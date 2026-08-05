"""Instalador del andamiaje SDD en un proyecto (respaldo de la skill `sdd-init`).

Copia las plantillas del kit al proyecto destino, vendoriza el núcleo y el
adaptador de lenguaje bajo `tools/sdd/`, instala el wiring de los gates y siembra
`.sdd/config.yaml`. Es **idempotente**: por defecto no pisa archivos existentes
(usá --force para sobrescribir plantillas).

Uso:
    python core/sdd_init.py [<target_dir>] [--language python|none] [--force]

Al terminar imprime la secuencia para continuar (`_next_steps`), con el path
real del destino: esos comandos corren desde el proyecto instalado
(`tools/sdd/core/...`), no desde el clon del kit.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sdd_config import VENDOR_PREFIX, write_text_lf  # noqa: E402

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
    ("docs/SKILLS-MULTITOOL.md", "docs/SKILLS-MULTITOOL.md"),
    ("docs/DEVELOPMENT.md", "docs/DEVELOPMENT.md"),
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
    """Resuelve los placeholders de plantilla para el proyecto destino.

    Los de ruta (`{{sdd.core}}`, `{{sdd.adapters}}`) resuelven al andamiaje
    vendorizado, que es donde vive en un proyecto instalado — no en `core/`
    como en el repo del kit (SPEC-010 FR-007).
    """
    return (
        text.replace("{{project.name}}", name)
        .replace("{{project.domain}}", domain)
        .replace("{{sdd.core}}", f"{VENDOR_PREFIX}/core")
        .replace("{{sdd.adapters}}", f"{VENDOR_PREFIX}/adapters")
    )


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


def _write_config(
    target: Path, name: str, language: str, force: bool
) -> tuple[str, Layout | None]:
    """Siembra `.sdd/config.yaml`. Devuelve (linea de log, layout detectado)."""
    dst = target / ".sdd" / "config.yaml"
    if dst.exists() and not force:
        return f"  (existe, se conserva) {dst}", None
    example = (KIT_ROOT / "examples" / "config" / "config.yaml").read_text(
        encoding="utf-8"
    )
    example = example.replace("name: mi-proyecto", f"name: {name}")
    example = example.replace("language: python", f"language: {language}")
    example = _seed_pipeline_steps(example)
    example = _seed_principles(example)
    layout = _detect_layout(target, language)
    example = _seed_dirs(example, layout)
    dst.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(dst, example)
    return f"  sembrado {dst}", layout


# Pasos sembrados por defecto: solo los operativos out-of-the-box (SPEC-003
# FR-005). Los demás requieren tooling del proyecto y se habilitan a mano o
# con sdd-configure (el adaptador igual los omite con aviso si falta la tool).
# `layers` va sembrado aunque requiera import-linter: el principio II del
# config de ejemplo lo declara como enforcement y check_constitution exige el
# paso cableado; sin la tool, el adaptador lo omite con aviso.
# `coverage` va sembrado por visibilidad (SPEC-009 FR-002): sin umbrales
# declarados se omite con aviso, asi que no puede poner en ROJO una instalacion
# fresca, pero deja el paso a la vista para cuando la suite madure.
_SEEDED_STEPS = [
    "hooks",
    "constitution",
    "traceability",
    "naming",
    "layers",
    "skills",
    "tests",
    "coverage",
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


# Carpetas candidatas a raiz de codigo, en orden de preferencia. No es una lista
# de "layouts soportados" (el kit no acopla a ninguno): es el orden en que se
# busca para adivinar, y lo que se adivina queda escrito en el config, donde el
# dueno lo puede corregir. Ver SPEC-003 FR-007.
_SOURCE_CANDIDATES = ("src", "app", "lib", "pkg", "source", "internal")
_TEST_CANDIDATES = ("tests/unit", "tests", "test")

# Extension de los archivos que delatan codigo del lenguaje, por adaptador.
_LANGUAGE_GLOBS = {"python": "*.py"}


@dataclass(frozen=True)
class Layout:
    """Layout detectado en el destino: que carpetas tienen codigo y tests."""

    source_root: str | None
    tests_unit: str | None

    @property
    def detected(self) -> bool:
        return bool(self.source_root or self.tests_unit)


def _has_language_files(directory: Path, language: str) -> bool:
    glob = _LANGUAGE_GLOBS.get(language)
    if glob is None:
        return False
    return any(directory.rglob(glob))


def _detect_layout(target: Path, language: str) -> Layout:
    """Busca la carpeta de codigo y la de tests que el proyecto ya tiene.

    Con `language: none` no se detecta codigo: no hay adaptador que lo valide,
    asi que declarar un source_root solo serviria para que el gate bloquee
    ediciones que ningun paso del pipeline mira.
    """
    source_root = next(
        (
            name
            for name in _SOURCE_CANDIDATES
            if (target / name).is_dir() and _has_language_files(target / name, language)
        ),
        None,
    )
    tests_unit = next(
        (name for name in _TEST_CANDIDATES if (target / name).is_dir()), None
    )
    return Layout(source_root=source_root, tests_unit=tests_unit)


def _seed_dirs(config_text: str, layout: Layout) -> str:
    """Reemplaza el bloque `dirs:` del ejemplo por el del proyecto destino.

    El ejemplo trae las rutas del proyecto de referencia (`src/domain`,
    `src/dashboard`, `tests/unit`). Heredarlas en un proyecto con otro layout
    hacia que el gate y los pasos de codigo apuntaran a carpetas inexistentes y
    que el pipeline reportara VERDE sin haber mirado nada (SPEC-003 FR-007).

    Sin deteccion se siembra un bloque minimo con TODO: `source_roots` cae al
    default `src` (ver sdd_config.source_roots), que es lo que ya hacia.
    """
    if layout.source_root:
        cuerpo = [
            "  # Detectado por sdd-init desde la estructura del proyecto.",
            f"  source_roots: [{layout.source_root}]",
        ]
    else:
        cuerpo = [
            "  # TODO: declara las carpetas de codigo de tu proyecto. Mientras",
            "  # `source_roots` no este, el gate y los pasos de codigo asumen `src`.",
            "  # source_roots: [src]",
        ]
    if layout.tests_unit:
        cuerpo.append(f"  tests_unit: {layout.tests_unit}")
    else:
        cuerpo.append("  # tests_unit: tests/unit")
    cuerpo.append("  # Rutas de cada capa (las pregunta sdd-configure):")
    cuerpo.append("  # domain: <ruta>")

    lines = config_text.splitlines()
    out: list[str] = []
    in_dirs = False
    for line in lines:
        if line.strip() == "dirs:":
            out.append(line)
            out.extend(cuerpo)
            in_dirs = True
            continue
        if in_dirs:
            # El bloque termina en la primera linea de nivel superior.
            if line and not line[0].isspace():
                in_dirs = False
            else:
                continue
        out.append(line)
    return "\n".join(out).rstrip() + "\n"


# Marcador que separa el nucleo minimo de los principios opcionales dentro de
# `principles:` en el config de ejemplo. Se busca el marcador en vez de contar
# principios: la lista vive en el ejemplo (SSOT), no duplicada aca.
_OPTIONAL_PRINCIPLES_MARKER = "principios OPCIONALES"


def _seed_principles(config_text: str) -> str:
    """Comenta los principios opcionales del ejemplo (SPEC-013 FR-001).

    Un principio que el dueno del proyecto nunca eligio ensena que la
    constitucion es decorativa. Se siembra solo el nucleo minimo obligatorio;
    el resto queda a la vista pero inactivo, y `sdd-configure` los pregunta al
    configurar el derivado.
    """
    lines = config_text.splitlines()
    out: list[str] = []
    in_block = False
    base = ""  # indentacion del marcador: prefijo comun de lo comentado
    commenting = False
    for line in lines:
        stripped = line.strip()
        if stripped == "principles:":
            in_block = True
            out.append(line)
            continue
        if in_block and line and not line[0].isspace():
            in_block = commenting = False  # arranca otra clave de nivel superior
        if in_block and not commenting and _OPTIONAL_PRINCIPLES_MARKER in stripped:
            base = line[: len(line) - len(line.lstrip())]
            out.append(f"{base}# Principios OPCIONALES: descomenta los que apliquen a")
            out.append(f"{base}# tu proyecto (sdd-configure te los pregunta).")
            commenting = True
            continue
        if commenting:
            if stripped.startswith("#"):
                continue  # notas del ejemplo: las reemplaza el aviso de arriba
            if stripped:
                # Prefijo fijo + indentacion relativa: descomentar es borrar
                # `# ` de cada linea y el YAML sigue alineado.
                out.append(f"{base}# {line[len(base) :]}")
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


def _layout_notice(layout: Layout | None) -> list[str]:
    """Que se detecto del layout, o que falta declarar (SPEC-003 FR-007).

    Va en la salida y no solo en el config: el dueno tiene que poder confirmar o
    corregir la adivinanza, y para eso primero tiene que saber que se hizo una.
    """
    if layout is None:
        return []
    if layout.source_root:
        detectado = f"codigo en {layout.source_root}/"
        if layout.tests_unit:
            detectado += f", tests en {layout.tests_unit}/"
        return [
            f"  Layout detectado: {detectado}",
            "  Verificalo en .sdd/config.yaml (dirs.source_roots) antes de seguir:",
            "  de ahi salen las carpetas que el gate protege y que los checks miran.",
            "",
        ]
    return [
        "  No se detecto carpeta de codigo: .sdd/config.yaml quedo con `dirs` sin",
        "  declarar y el gate asume `src`. Si tu codigo va en otra carpeta,",
        "  declarala en dirs.source_roots (o corre sdd-configure).",
        "",
    ]


def _next_steps(target: Path, layout: Layout | None = None) -> str:
    """Secuencia para continuar, con el path real y sin los pasos ya cumplidos.

    El operador cierra la instalacion mirando esta salida, no el README: si el
    `cd` al destino no esta a la vista, los comandos `tools/sdd/...` que siguen
    no resuelven desde el clon del kit (SPEC-011 FR-009). Los pasos de
    preparacion ya satisfechos se omiten -- sugerir `git init` sobre un repo
    existente resta credibilidad al resto de la lista (FR-010).
    """
    lines = [f"\nListo. sdd-first instalado en {target}", ""]
    lines.extend(_layout_notice(layout))
    lines.extend(["Proximos pasos:", ""])

    prep: list[str] = []
    if target != Path.cwd():
        prep.append(f"  cd {target}")
    if not (target / ".git").exists():
        prep.append(
            "  git init                 # el gate en el commit necesita repo git"
        )
    if importlib.util.find_spec("pre_commit") is None:
        prep.append(
            "  pip install pre-commit   # para que el paso `hooks` cablee los hooks"
        )
    if prep:
        lines.extend(prep)
        lines.append("")

    lines.extend(
        [
            "  1. Edita .sdd/config.yaml (dominio, carpetas de codigo y tests,",
            "     palabras excluidas, capas) o corre la skill sdd-configure.",
            "  2. python tools/sdd/core/render.py"
            "               # CONSTITUTION.md + SPEC-000 + CI",
            "  3. python tools/sdd/core/gen_skill_adapters.py"
            "   # skills para tu asistente",
            "  4. python tools/sdd/core/pipeline.py"
            "             # verifica -> VERDE / ROJO",
            "",
            "Antes de editar codigo, crea la primera spec: el gate spec-first bloquea",
            "mientras .sdd/current-spec este vacio.",
            '  python tools/sdd/core/sdd_spec.py "<slug>" --title="<Titulo>"',
            "  (o pedile a tu asistente la skill sdd-spec)",
            "",
            "El andamiaje quedo vendorizado en tools/sdd/: el clon del kit ya es"
            " descartable.",
        ]
    )
    return "\n".join(lines)


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
    config_line, layout = _write_config(target, name, language, force)
    log.append(config_line)
    log.extend(_vendor_kit(target, language, force))
    log.extend(_install_project_skills(target, force))

    for line in log:
        print(line)

    print(_next_steps(target, layout))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
