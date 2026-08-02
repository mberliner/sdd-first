"""Instalador del andamiaje SDD en un proyecto (respaldo de la skill `sdd-init`).

Copia las plantillas del kit al proyecto destino, vendoriza el núcleo y el
adaptador de lenguaje bajo `tools/sdd/`, instala el wiring de los gates y siembra
`.sdd/config.yaml`. Es **idempotente**: por defecto no pisa archivos existentes
(usá --force para sobrescribir plantillas).

Uso:
    python core/sdd_init.py [<target_dir>] [--language python|none] [--force]

Después de instalar, corré `python core/render.py` y `sdd-configure` para
personalizar, y `python tools/sdd/core/pipeline.py` para verificar.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sdd_config import write_text_lf  # noqa: E402

KIT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = KIT_ROOT / "templates"

# Plantillas estáticas: (origen relativo a templates/, destino relativo a target).
STATIC_DOCS = [
    ("AGENTS.md", "AGENTS.md"),
    ("CLAUDE.md", "CLAUDE.md"),
    ("00-INDEX.md", "00-INDEX.md"),
    ("README.md", "README.md"),
    ("docs/ARCHITECTURE.md", "docs/ARCHITECTURE.md"),
    ("docs/CONTRIBUTING.md", "docs/CONTRIBUTING.md"),
    ("docs/SPEC-FORMAT.md", "docs/SPEC-FORMAT.md"),
    ("docs/SDD-ENFORCEMENT.md", "docs/SDD-ENFORCEMENT.md"),
    ("docs/SDD-OPERACION.md", "docs/SDD-OPERACION.md"),
    ("docs/IDEAS.md", "docs/IDEAS.md"),
    ("docs/playbooks/analyze.md", "docs/playbooks/analyze.md"),
    ("docs/playbooks/clarify.md", "docs/playbooks/clarify.md"),
    ("docs/playbooks/sdd-spec.md", "docs/playbooks/sdd-spec.md"),
    ("docs/playbooks/sdd-doctor.md", "docs/playbooks/sdd-doctor.md"),
    ("docs/playbooks/sdd-configure.md", "docs/playbooks/sdd-configure.md"),
    ("specs/SPECS_REGISTRY.md", "specs/SPECS_REGISTRY.md"),
    ("specs/SPEC-TEMPLATE.md", "specs/SPEC-TEMPLATE.md"),
    ("historial/sdd.md", "historial/sdd.md"),
]

# Wiring: (origen en templates/wiring, destino en target).
WIRING = [
    ("wiring/claude-settings.json", ".claude/settings.json"),
    ("wiring/sdd_gate_hook.sh", ".claude/sdd_gate_hook.sh"),
    ("wiring/.pre-commit-config.yaml", ".pre-commit-config.yaml"),
    ("wiring/opencode-sdd-gate.js", ".opencode/plugin/sdd-gate.js"),
    ("wiring/.gitattributes", ".gitattributes"),
    ("wiring/.gitignore", ".gitignore"),
    ("wiring/current-spec", ".sdd/current-spec"),
]

# Wiring que necesita quedar con permiso de ejecucion tras copiarse.
_EXECUTABLE_WIRING = {".claude/sdd_gate_hook.sh"}

# Skills de proyecto que se instalan en el destino (fuente para el generador).
# No incluye "sdd-init": es bootstrap de una sola vez, no una skill operativa
# del día a día del proyecto ya instalado.
PROJECT_SKILLS = ["analyze", "clarify", "sdd-spec", "sdd-doctor", "sdd-configure"]


def _substitute(text: str, name: str, domain: str) -> str:
    return text.replace("{{project.name}}", name).replace("{{project.domain}}", domain)


def _copy_text(src: Path, dst: Path, name: str, domain: str, force: bool) -> str:
    if dst.exists() and not force:
        return f"  (existe, se conserva) {dst}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8")
    if src.suffix in {".md", ".json", ".yaml", ".yml", ".js"}:
        text = _substitute(text, name, domain)
    write_text_lf(dst, text)
    return f"  instalado {dst}"


def _vendor_kit(target: Path, language: str, force: bool) -> list[str]:
    """Copia core/ y el adaptador del lenguaje bajo tools/sdd/."""
    out: list[str] = []
    dst_core = target / "tools" / "sdd" / "core"
    if dst_core.exists() and not force:
        out.append(f"  (existe, se conserva) {dst_core}")
    else:
        shutil.copytree(KIT_ROOT / "core", dst_core, dirs_exist_ok=True)
        out.append(f"  vendorizado {dst_core}")
    if language != "none":
        src_adapter = KIT_ROOT / "adapters" / language
        if src_adapter.is_dir():
            dst_adapter = target / "tools" / "sdd" / "adapters" / language
            shutil.copytree(src_adapter, dst_adapter, dirs_exist_ok=True)
            out.append(f"  vendorizado {dst_adapter}")
    return out


def _write_config(target: Path, name: str, language: str, force: bool) -> str:
    dst = target / ".sdd" / "config.yaml"
    if dst.exists() and not force:
        return f"  (existe, se conserva) {dst}"
    example = (KIT_ROOT / "examples" / "config" / "config.yaml").read_text(
        encoding="utf-8"
    )
    example = example.replace("name: mi-proyecto", f"name: {name}")
    example = example.replace("language: python", f"language: {language}")
    example = _seed_pipeline_steps(example)
    dst.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(dst, example)
    return f"  sembrado {dst}"


# Pasos sembrados por defecto: solo los operativos out-of-the-box (SPEC-003
# FR-005). Los demás requieren tooling del proyecto y se habilitan a mano o
# con sdd-configure (el adaptador igual los omite con aviso si falta la tool).
# `layers` va sembrado aunque requiera import-linter: el principio II del
# config de ejemplo lo declara como enforcement y check_constitution exige el
# paso cableado; sin la tool, el adaptador lo omite con aviso.
_SEEDED_STEPS = [
    "hooks",
    "constitution",
    "traceability",
    "naming",
    "layers",
    "skills",
    "tests",
]
_OPTIONAL_STEPS = ["lint", "format", "types", "security"]


def _seed_pipeline_steps(config_text: str) -> str:
    """Reemplaza la lista `steps:` del ejemplo por el set mínimo operativo."""
    lines = config_text.splitlines()
    out: list[str] = []
    in_steps = False
    replaced = False
    for line in lines:
        stripped = line.strip()
        if in_steps:
            if stripped.startswith("- "):
                continue  # descarta los pasos del ejemplo
            in_steps = False
        if stripped == "steps:" and not replaced:
            out.append(line)
            indent = line[: len(line) - len(line.lstrip())] + "  "
            out.extend(f"{indent}- {s}" for s in _SEEDED_STEPS)
            out.append(f"{indent}# Habilitá según el tooling del proyecto:")
            out.extend(f"{indent}# - {s}" for s in _OPTIONAL_STEPS)
            in_steps = True
            replaced = True
            continue
        out.append(line)
    return "\n".join(out).rstrip() + "\n"


def _install_project_skills(target: Path, force: bool) -> list[str]:
    out: list[str] = []
    for skill in PROJECT_SKILLS:
        src = TEMPLATES / "docs" / "playbooks" / f"{skill}.md"
        # SKILL.md fuente: lo tomamos de .agents/skills del kit.
        skill_src = KIT_ROOT / ".agents" / "skills" / skill / "SKILL.md"
        if skill_src.exists():
            dst = target / ".agents" / "skills" / skill / "SKILL.md"
            if not dst.exists() or force:
                dst.parent.mkdir(parents=True, exist_ok=True)
                write_text_lf(dst, skill_src.read_text(encoding="utf-8"))
                out.append(f"  instalado {dst}")
        _ = src  # el playbook ya se copió en STATIC_DOCS
    return out


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    flags = [a for a in argv if a.startswith("--")]
    force = "--force" in flags
    language = "python"
    for f in flags:
        if f.startswith("--language"):
            language = f.split("=", 1)[1] if "=" in f else "python"

    target = Path(args[0]).resolve() if args else Path.cwd()
    name = target.name
    domain = "TODO: describir el dominio"

    print(f"Instalando sdd-first en {target} (language={language})")
    log: list[str] = []
    for src_rel, dst_rel in STATIC_DOCS:
        log.append(
            _copy_text(TEMPLATES / src_rel, target / dst_rel, name, domain, force)
        )
    for src_rel, dst_rel in WIRING:
        log.append(
            _copy_text(TEMPLATES / src_rel, target / dst_rel, name, domain, force)
        )
        if dst_rel in _EXECUTABLE_WIRING:
            (target / dst_rel).chmod(0o755)
    log.append(_write_config(target, name, language, force))
    log.extend(_vendor_kit(target, language, force))
    log.extend(_install_project_skills(target, force))

    for line in log:
        print(line)

    print(
        "\nListo. Próximos pasos:\n"
        "  1. Editá .sdd/config.yaml (o corré sdd-configure).\n"
        "  2. python tools/sdd/core/render.py       # genera CONSTITUTION.md y SPEC-000\n"
        "  3. python tools/sdd/core/gen_skill_adapters.py   # genera skills\n"
        "  4. python tools/sdd/core/pipeline.py     # verifica"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
