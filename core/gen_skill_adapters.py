"""Generador de adaptadores de skills multi-asistente (nucleo del kit).

SSOT: cada skill se escribe una sola vez en `.agents/skills/<name>/SKILL.md`.
Ese formato (carpeta + SKILL.md con frontmatter `name` + `description`) lo leen
directo Codex y Antigravity, con auto-descubrimiento por `description`.

Desde esa fuente este script genera los adaptadores que divergen:

  - `.claude/skills/<name>/SKILL.md`  (Claude usa ademas `allowed-tools`).
  - `.opencode/command/<name>.md`     (invocacion explicita `/name`).

No se usan symlinks: archivos reales committeados, identicos en Windows y Linux.
Siempre se escribe con `\\n` para que `--check` sea determinista (ver .gitattributes).

A diferencia del original (que fijaba REPO_ROOT a partir de tools/), este detecta
la raiz del proyecto, para funcionar igual en el kit y en un proyecto instalado.

Uso:
    python core/gen_skill_adapters.py            # escribe los adaptadores
    python core/gen_skill_adapters.py --check    # falla si hay drift (CI/pipeline)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd_config import find_repo_root, script_hint, write_text_lf  # noqa: E402

PLAYBOOK_TEMPLATE = "docs/playbooks/{name}.md"

GENERATED_MARKER = (
    "<!-- GENERADO por core/gen_skill_adapters.py desde "
    ".agents/skills/{name}/SKILL.md — NO EDITAR A MANO -->"
)

GENERATOR_ONLY_KEYS: frozenset[str] = frozenset(
    {"opencode-description", "opencode-constraint"}
)


@dataclass(frozen=True)
class Skill:
    name: str
    frontmatter: dict[str, str]
    body: str

    @property
    def description(self) -> str:
        return self.frontmatter.get("description", "").strip()

    @property
    def opencode_description(self) -> str:
        return self.frontmatter.get("opencode-description", self.description).strip()

    @property
    def opencode_constraint(self) -> str:
        return self.frontmatter.get("opencode-constraint", "").strip()


def parse_skill(source: Path) -> Skill:
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{source}: falta frontmatter (primera linea debe ser '---')")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{source}: frontmatter sin cierre '---'") from exc

    frontmatter: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        if ":" not in raw:
            raise ValueError(f"{source}: linea de frontmatter sin ':' -> {raw!r}")
        key, value = raw.split(":", 1)
        frontmatter[key.strip()] = _unquote(value.strip())

    body = "\n".join(lines[end + 1 :]).strip("\n")
    name = frontmatter.get("name", source.parent.name).strip()
    if "description" not in frontmatter:
        raise ValueError(f"{source}: frontmatter sin 'description' (obligatorio)")
    return Skill(name=name, frontmatter=frontmatter, body=body)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _needs_quote(value: str) -> bool:
    return value.startswith((" ", '"', "'")) or value.endswith(" ")


def render_claude(skill: Skill) -> str:
    keys = [
        k for k in ("name", "description", "allowed-tools") if k in skill.frontmatter
    ]
    fm = "\n".join(f"{k}: {skill.frontmatter[k]}" for k in keys)
    marker = GENERATED_MARKER.format(name=skill.name)
    return f"---\n{fm}\n---\n\n{marker}\n\n{skill.body}\n"


def render_opencode(skill: Skill) -> str:
    desc = skill.opencode_description
    desc_line = (
        f'description: "{desc}"' if _needs_quote(desc) else f"description: {desc}"
    )
    marker = GENERATED_MARKER.format(name=skill.name)
    playbook = PLAYBOOK_TEMPLATE.format(name=skill.name)
    lines = [
        f"---\n{desc_line}\n---",
        "",
        marker,
        "",
        f"Leé y seguí el playbook `{playbook}` (SSOT del procedimiento).",
        "Spec objetivo: `$ARGUMENTS` (si está vacío, usá la primera de `.sdd/current-spec`).",
    ]
    if skill.opencode_constraint:
        lines.append(skill.opencode_constraint)
    return "\n".join(lines) + "\n"


def _validate(skill: Skill, repo_root: Path) -> list[str]:
    errors: list[str] = []
    playbook = repo_root / PLAYBOOK_TEMPLATE.format(name=skill.name)
    if not playbook.exists():
        errors.append(
            f"{skill.name}: falta el playbook SSOT {playbook.relative_to(repo_root)}"
        )
    unknown = set(skill.frontmatter) - {
        "name",
        "description",
        "allowed-tools",
        *GENERATOR_ONLY_KEYS,
    }
    if unknown:
        errors.append(
            f"{skill.name}: claves de frontmatter no reconocidas: {sorted(unknown)}"
        )
    return errors


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(path, content)


def _check(path: Path, content: str) -> bool:
    if not path.exists():
        return False
    return path.read_text(encoding="utf-8") == content


@dataclass(frozen=True)
class Result:
    """Resultado de una corrida del generador sobre una raiz concreta.

    `written` son las rutas relativas escritas (vacia en modo `--check`);
    `drift`, las que no coinciden con lo generado; `problems`, los errores de
    validacion de las fuentes. Devolverlo en vez de imprimir permite que
    `sdd_init` siembre los adaptadores del destino y reporte en su propio log
    (SPEC-016 FR-001).
    """

    written: list[str]
    drift: list[str]
    problems: list[str]
    skills: int


def generate(repo_root: Path, check: bool = False) -> Result:
    """Genera (o verifica) los adaptadores de skills bajo `repo_root`.

    La raiz es explicita: `main()` la resuelve desde el `cwd`, pero `sdd_init`
    corre desde el clon del kit y necesita apuntar al proyecto destino.
    """
    source_dir = repo_root / ".agents" / "skills"
    claude_dir = repo_root / ".claude" / "skills"
    opencode_dir = repo_root / ".opencode" / "command"

    if not source_dir.is_dir():
        return Result(written=[], drift=[], problems=[], skills=0)

    sources = sorted(source_dir.glob("*/SKILL.md"))
    written: list[str] = []
    drift: list[str] = []
    problems: list[str] = []

    for source in sources:
        try:
            skill = parse_skill(source)
        except ValueError as exc:
            problems.append(str(exc))
            continue
        problems.extend(_validate(skill, repo_root))

        targets = {
            claude_dir / skill.name / "SKILL.md": render_claude(skill),
            opencode_dir / f"{skill.name}.md": render_opencode(skill),
        }
        for target, content in targets.items():
            rel = target.relative_to(repo_root).as_posix()
            if check:
                if not _check(target, content):
                    drift.append(rel)
            else:
                _write(target, content)
                written.append(rel)

    return Result(written=written, drift=drift, problems=problems, skills=len(sources))


def main(argv: list[str]) -> int:
    check_mode = "--check" in argv
    repo_root = find_repo_root()
    source_dir = repo_root / ".agents" / "skills"

    if not source_dir.is_dir():
        print(f"No existe {source_dir.relative_to(repo_root)}; nada que generar.")
        return 0

    result = generate(repo_root, check=check_mode)
    if result.skills == 0:
        print(f"Sin skills en {source_dir.relative_to(repo_root)}.")
        return 0

    for rel in result.written:
        print(f"  generado  {rel}")

    if result.problems:
        print("\nProblemas de validacion:")
        for p in result.problems:
            print(f"  x {p}")
        return 1

    if check_mode:
        if result.drift:
            hint = script_hint(__file__, repo_root)
            print(f"Adaptadores desincronizados (corre: python {hint}):")
            for d in result.drift:
                print(f"  x {d}")
            return 1
        print(f"Adaptadores de skills: sincronizados ({result.skills} skill(s)).")
        return 0

    print(f"Adaptadores generados para {result.skills} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
