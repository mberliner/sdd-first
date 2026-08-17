"""Instalador del andamiaje SDD en un proyecto (respaldo de la skill `sdd-init`).

Copia las plantillas del kit al proyecto destino, vendoriza el núcleo y el
adaptador de lenguaje bajo `tools/sdd/`, instala el wiring de los gates y siembra
`.sdd/config.yaml`. Es **idempotente**: por defecto no pisa archivos existentes
(usá --force para sobrescribir plantillas).

Uso:
    python core/sdd_init.py [<target_dir>] [--target=<dir>]
                            [--language=<lang>] [--force]

El destino se pasa como posicional o con `--target`; sin ninguno de los dos es
el directorio actual. `--language` se valida contra los adaptadores que existen
en `adapters/` (mas `none`). Cualquier otro flag aborta antes de escribir nada
(SPEC-003 FR-012): el instalador toca ~40 archivos y una invocacion mal leida
los deja en el directorio equivocado.

Al terminar imprime la secuencia para continuar (`_next_steps`), con el path
real del destino: esos comandos corren desde el proyecto instalado
(`tools/sdd/core/...`), no desde el clon del kit.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess  # nosec B404 - solo consulta la rama actual del destino
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_skill_adapters  # noqa: E402
import sdd_catalog  # noqa: E402
from sdd_catalog import KIT_NEW_SUFFIX, Clase  # noqa: E402
from sdd_config import (  # noqa: E402
    GATE_WIRING,
    VENDOR_PREFIX,
    ensure_gitignore_current_spec,
    forzar_salida_utf8,
    hash_bytes,
    write_text_lf,
)

if TYPE_CHECKING:  # evita el ciclo sdd_init <-> sdd_lock en tiempo de import
    from sdd_lock import Lock

KIT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = KIT_ROOT / "templates"

# Catalogo de claves del config: SSOT en el kit, instalado en el destino para
# que la cabecera del config sembrado pueda apuntarle (SPEC-013 FR-008).
EXAMPLE_CONFIG = KIT_ROOT / "examples" / "config" / "config.yaml"
CONFIG_REFERENCE_RELPATH = Path(".sdd") / "config.reference.yaml"

# Catálogo de artefactos (plantillas estáticas + wiring), con su clase de
# propiedad: SSOT único en `sdd_catalog.py`, compartido con `sdd_update.py`
# (SPEC-025 FR-US2-001). No se copian acá para no duplicar la lista.
STATIC_DOCS = sdd_catalog.STATIC_DOCS
WIRING = sdd_catalog.WIRING

# Wiring que necesita quedar con permiso de ejecucion tras copiarse.
_EXECUTABLE_WIRING = sdd_catalog.EXECUTABLE_WIRING

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
    import datetime as _dt

    today = _dt.date.today().isoformat()
    return (
        text.replace("{{project.name}}", name)
        .replace("{{project.domain}}", domain)
        .replace("{{sdd.core}}", f"{VENDOR_PREFIX}/core")
        .replace("{{sdd.adapters}}", f"{VENDOR_PREFIX}/adapters")
        .replace("YYYY-MM-DD", today)
    )


def _copy_text(
    src: Path,
    dst: Path,
    name: str,
    domain: str,
    force: bool,
    *,
    dst_rel: str = "",
    lock: Lock | None = None,
) -> str:
    """Instala una plantilla, respetando su clase de propiedad (SPEC-025 FR-US2-013).

    `dst_rel` (ruta relativa al target, forma posix) es la clave del catálogo:
    decide la clase con `sdd_catalog.clase_de` y, si es `plantilla` y
    `force=True`, la política de conflicto (`decidir_plantilla`) contra el
    lock existente en vez de pisar a ciegas.
    """
    text = _substitute(src.read_text(encoding="utf-8"), name, domain)
    clase = sdd_catalog.clase_de(dst_rel) if dst_rel else Clase.PLANTILLA

    if dst.exists():
        if clase == Clase.SEMILLA or not force:
            if dst.name == ".gitignore" and ensure_gitignore_current_spec(dst):
                return (
                    f"  (existe, se conserva) {dst} -- se agrego .sdd/current-spec "
                    "(SPEC-004 FR-009)"
                )
            return f"  (existe, se conserva) {dst}"
        # PLANTILLA + force: no se pisa a ciegas (FR-US2-013). Se decide contra
        # el lock existente, con el mismo criterio que `sdd-update`.
        hash_kit = hash_bytes(text.encode("utf-8"))
        hash_disco = hash_bytes(dst.read_bytes())
        hash_lock = lock.plantillas.get(dst_rel) if lock else None
        decision = sdd_catalog.decidir_plantilla(True, hash_disco, hash_kit, hash_lock)
        if decision == "sin_cambios":
            return f"  (sin cambios) {dst}"
        if decision == "actualizar":
            write_text_lf(dst, text)
            return f"  actualizado {dst}"
        # "conflicto": se conserva y se deja la version del kit al lado.
        kit_new = dst.with_name(dst.name + KIT_NEW_SUFFIX)
        write_text_lf(kit_new, text)
        return (
            f"  CONFLICTO (editado): {dst} -- se conservo tu version; la del kit "
            f"queda en {kit_new}"
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    # Se sustituye en TODO lo que se copia: son todas plantillas de texto. El
    # criterio anterior era la extension, y `.sdd/current-spec` -- el primer
    # archivo que se abre para entender el gate -- no tiene, asi que se instalaba
    # con `{{sdd.core}}` crudo (SPEC-014 FR-US2-001).
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


def _install_config_reference(target: Path) -> str:
    """Instala el catalogo de claves del config en el destino (SPEC-013 FR-008).

    La cabecera del config sembrado remite al catalogo, que hasta ahora vivia
    solo en el kit (`examples/config/config.yaml`): una referencia colgada en el
    archivo que el dueno mas edita, y que solo se sostenia asumiendo que siempre
    hay un clon del kit a mano. No la hay: el kit es desechable.

    Se copia verbatim porque el catalogo *es* ese YAML --su valor esta en los
    comentarios junto a cada clave--, y se reescribe siempre porque es artefacto
    del kit, no del dueno: un catalogo viejo describiendo claves de una version
    anterior del andamiaje es peor que no tenerlo.
    """
    dst = target / CONFIG_REFERENCE_RELPATH
    dst.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(dst, EXAMPLE_CONFIG.read_text(encoding="utf-8"))
    return f"  instalado {dst}"


def _write_config(
    target: Path, name: str, language: str, force: bool
) -> tuple[str, Layout | None]:
    """Siembra `.sdd/config.yaml`. Devuelve (linea de log, layout detectado).

    Es `semilla` (SPEC-025 FR-US2-002): ni siquiera `--force` lo pisa (ANA-014)
    -- es el archivo que el dueno mas edita, y `--force` fuerza la
    reinstalacion del andamiaje, no la destruccion de lo que el dueno escribio.
    """
    dst = target / ".sdd" / "config.yaml"
    if dst.exists():
        return f"  (existe, se conserva) {dst}", None
    example = EXAMPLE_CONFIG.read_text(encoding="utf-8")
    example = _seed_header(example, name)
    example = example.replace("name: mi-proyecto", f"name: {name}")
    example = example.replace("language: python", f"language: {language}")

    import datetime as _dt

    today = _dt.date.today().isoformat()
    example = example.replace("ratified: 2026-01-01", f"ratified: {today}")
    example = example.replace("amended: 2026-01-01", f"amended: {today}")

    example = _seed_default_branch(example, target)
    layout = _detect_layout(target, language)
    example = _seed_pipeline_steps(example, layout)
    example = _seed_principles(example)
    example = _seed_dirs(example, layout)
    dst.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(dst, example)
    return f"  sembrado {dst}", layout


def _seed_header(config_text: str, name: str) -> str:
    """Cambia la cabecera del catalogo por una del proyecto (FR-US2-004).

    El ejemplo se presenta como catalogo de referencia y manda "copialo a
    .sdd/config.yaml", instruccion absurda en el archivo que ya *es* ese destino,
    y nombra al proyecto de referencia del kit. El catalogo conserva la suya: lo
    que cambia es el sembrado.
    """
    cuerpo = config_text.splitlines()
    inicio = next(
        (
            i
            for i, line in enumerate(cuerpo)
            if line.strip() and not line.startswith("#")
        ),
        0,
    )
    cabecera = [
        f"# .sdd/config.yaml — SSOT de parametrizacion de {name}.",
        "#",
        "# Todo el andamiaje SDD lee sus parametros de aca: cambiar este archivo",
        "# cambia lo que el pipeline verifica y lo que el gate protege. Tras",
        "# editarlo, regenera los derivados con `render.py` (CONSTITUTION.md,",
        "# SPEC-000, CI). El catalogo completo de claves, con su documentacion,",
        f"# esta al lado: `{CONFIG_REFERENCE_RELPATH.as_posix()}`.",
        "",
    ]
    return "\n".join([*cabecera, *cuerpo[inicio:]]).rstrip() + "\n"


def _git_default_branch(target: Path) -> str | None:
    """Rama actual del destino segun git, o None si no hay repo ni rama."""
    result = subprocess.run(  # nosec B603 B607 - comando fijo, sin input de usuario
        ["git", "-C", str(target), "branch", "--show-current"],
        capture_output=True,
        text=True,
    )
    rama = result.stdout.strip()
    return rama or None


def _seed_default_branch(config_text: str, target: Path) -> str:
    """Declara `project.default_branch` con la rama real del destino (FR-US2-005).

    Sin dato no se declara nada: el default del loader es `main`, que es lo que
    el CI hardcodeaba hasta ahora.
    """
    rama = _git_default_branch(target)
    if rama is None:
        return config_text
    out: list[str] = []
    for line in config_text.splitlines():
        out.append(line)
        if line.strip().startswith("name:"):
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}default_branch: {rama}   # rama de disparo del CI")
    return "\n".join(out).rstrip() + "\n"


# Pasos sembrados por defecto: solo los operativos out-of-the-box (SPEC-003
# FR-005). Los demás requieren tooling del proyecto y se habilitan a mano o
# con sdd-configure (el adaptador igual los omite con aviso si falta la tool).
# `layers` va sembrado aunque requiera import-linter: el principio II del
# config de ejemplo lo declara como enforcement y check_constitution exige el
# paso cableado; sin la tool, el adaptador lo omite con aviso.
# `coverage` va sembrado por visibilidad (SPEC-009 FR-002): sin umbrales
# declarados se omite con aviso, asi que no puede poner en ROJO una instalacion
# fresca, pero deja el paso a la vista para cuando la suite madure.
# `render` va sembrado porque es lo unico que vigila el drift de los artefactos
# generados en un derivado (SPEC-014 FR-US1-005): sin el, el pipeline reporta
# VERDE sobre una CONSTITUTION.md, un SPEC-000 o un ci.yml que ya no derivan del
# config. Es lectura pura, no requiere tooling del proyecto, y no agrega
# precondicion: el paso `constitution` ya exige haber corrido `render`.
# `constitution` va ANTEPENULTIMO --despues de `render`, su precondicion, y
# despues de los pasos que enforzan principios-- porque tambien verifica que
# cada enforcement haya corrido y no solo que este declarado (SPEC-020
# FR-US2-006). Sembrarlo segundo, como estaba, contradecia esa precondicion ya
# escrita arriba y dejaba al paso reportando reservas en cada corrida.
_SEEDED_STEPS = [
    "hooks",
    "traceability",
    "naming",
    "layers",
    "skills",
    "render",
    "tests",
    "coverage",
    "constitution",
]
_OPTIONAL_STEPS = ["lint", "format", "types", "security"]


def _seed_pipeline_steps(config_text: str, layout: Layout | None = None) -> str:
    """Reemplaza la lista `steps:` del ejemplo por el set mínimo operativo.

    El paso `integration` se siembra solo si el destino tiene carpeta de tests de
    integración (SPEC-019 FR-US3-002): sembrarlo siempre lo dejaría omitiéndose en
    cada corrida de todo proyecto que no la use, y no sembrarlo cuando la carpeta
    existe haría nacer la instalación con tests declarados que no corre nadie.
    """
    pasos = list(_SEEDED_STEPS)
    if layout is not None and layout.tests_integration:
        pasos.insert(pasos.index("tests") + 1, "integration")
    # `e2e` va ultimo por costo: un fallo barato tiene que aparecer antes
    # (SPEC-018 FR-US3-003).
    if layout is not None and layout.tests_e2e:
        pasos.append("e2e")
    lines = config_text.splitlines()
    out: list[str] = []
    in_steps = False
    steps_indent = 0
    replaced = False
    for line in lines:
        stripped = line.strip()
        if in_steps:
            if not stripped:
                continue  # linea en blanco del bloque original: se descarta
            linea_indent = len(line) - len(line.lstrip())
            if linea_indent > steps_indent:
                continue  # descarta items y comentarios del bloque original
            in_steps = False
        if stripped == "steps:" and not replaced:
            out.append(line)
            steps_indent = len(line) - len(line.lstrip())
            indent = line[: len(line) - len(line.lstrip())] + "  "
            out.extend(f"{indent}- {s}" for s in pasos)
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
_INTEGRATION_CANDIDATES = ("tests/integration", "tests/integracion")
_E2E_CANDIDATES = ("tests/e2e", "tests/end-to-end", "e2e")

# Extension de los archivos que delatan codigo del lenguaje, por adaptador.
_LANGUAGE_GLOBS = {"python": "*.py"}


@dataclass(frozen=True)
class Layout:
    """Layout detectado en el destino: que carpetas tienen codigo y tests."""

    source_root: str | None
    tests_unit: str | None
    tests_integration: str | None = None
    tests_e2e: str | None = None

    @property
    def detected(self) -> bool:
        return bool(
            self.source_root
            or self.tests_unit
            or self.tests_integration
            or self.tests_e2e
        )


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
    tests_integration = next(
        (name for name in _INTEGRATION_CANDIDATES if (target / name).is_dir()), None
    )
    tests_e2e = next(
        (name for name in _E2E_CANDIDATES if (target / name).is_dir()), None
    )
    # Si la carpeta unitaria detectada ya contiene a la de integracion (layout
    # `tests/` plano), declararlas por separado haria correr los mismos tests dos
    # veces: manda la unitaria, que es la que se detecto.
    if (
        tests_integration
        and tests_unit
        and tests_integration.startswith(f"{tests_unit}/")
    ):
        tests_integration = None
    if tests_e2e and tests_unit and tests_e2e.startswith(f"{tests_unit}/"):
        tests_e2e = None
    return Layout(
        source_root=source_root,
        tests_unit=tests_unit,
        tests_integration=tests_integration,
        tests_e2e=tests_e2e,
    )


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
    # La carpeta de integracion la corre el paso `integration`; declararla sin
    # ese paso deja tests que no ejecuta nadie, y eso lo reporta sdd-doctor
    # (SPEC-019 FR-US3-001).
    if layout.tests_integration:
        cuerpo.append(f"  tests_integration: {layout.tests_integration}")
    else:
        cuerpo.append("  # tests_integration: tests/integration  # paso 'integration'")
    if layout.tests_e2e:
        cuerpo.append(f"  tests_e2e: {layout.tests_e2e}")
    else:
        cuerpo.append("  # tests_e2e: tests/e2e  # paso 'e2e'")
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
        # SKILL.md fuente: lo tomamos de .agents/skills del kit.
        skill_src = KIT_ROOT / ".agents" / "skills" / skill / "SKILL.md"
        if skill_src.exists():
            dst = target / ".agents" / "skills" / skill / "SKILL.md"
            if not dst.exists() or force:
                dst.parent.mkdir(parents=True, exist_ok=True)
                write_text_lf(dst, skill_src.read_text(encoding="utf-8"))
                out.append(f"  instalado {dst}")
    return out


def _generate_skill_adapters(target: Path) -> list[str]:
    """Siembra los adaptadores que hacen descubribles las skills (FR-002).

    Sin esto, un destino recien instalado tiene `.agents/skills/` (que leen Codex
    y Antigravity) pero ni `.claude/skills/` ni `.opencode/command/`: Claude Code
    y opencode no ven ninguna skill SDD. Y el paso siguiente que el propio
    instalador recomienda —"corre la skill sdd-configure"— es imposible de seguir.

    Se escriben siempre, con o sin `--force`: son artefactos generados, con
    cabecera `NO EDITAR A MANO`, que el paso `skills` del pipeline verifica con
    `--check` (FR-003). La fuente `.agents/skills/` sigue siendo idempotente.

    Un fallo aca no aborta la instalacion (FR-004): el andamiaje ya esta copiado
    y dejarlo a medias es peor que un derivado sin adaptadores, que se resuelve
    con un comando.
    """
    try:
        result = gen_skill_adapters.generate(target)
    except OSError as exc:  # pragma: no cover - E/S del destino
        return _skill_adapters_fallo([str(exc)])
    if result.problems:
        return _skill_adapters_fallo(result.problems)
    return [f"  generado {target / Path(rel)}" for rel in result.written]


def _skill_adapters_fallo(problemas: list[str]) -> list[str]:
    return [
        "  ATENCION: no se pudieron generar los adaptadores de skills; tu",
        "  asistente puede no ver las skills SDD. Motivo:",
        *(f"    - {p}" for p in problemas),
        f"  Reintenta con: python {VENDOR_PREFIX}/core/gen_skill_adapters.py",
    ]


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
        if layout.tests_integration:
            detectado += f", integracion en {layout.tests_integration}/"
        if layout.tests_e2e:
            detectado += f", e2e en {layout.tests_e2e}/"
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


def _gate_wiring_conservado(target: Path) -> list[str]:
    """Archivos de wiring del gate que no cablean la invocacion esperada
    (FR-US1-001), consultado DESPUES de copiar.

    Antes se consultaba antes de copiar y `force=True` devolvia `[]` a ciegas
    (asumiendo que todo se pisaba). Con la politica de conflicto de
    FR-US2-013, un `--force` sin lock (o sobre una plantilla editada) puede
    conservar el wiring igual, asi que el chequeo real es sobre lo que quedo
    en disco, con el mismo criterio de contenido que usa `sdd_doctor`.
    """
    conservado = []
    for rel, invocacion in GATE_WIRING.items():
        path = target / rel
        if not path.exists() or invocacion not in path.read_text(encoding="utf-8"):
            conservado.append(rel)
    return conservado


def _wiring_notice(conservado: list[str]) -> list[str]:
    """Aviso destacado cuando el gate puede haber quedado sin cablear.

    La linea `(existe, se conserva)` del log se pierde entre treinta lineas de
    instalacion. En el proyecto testigo de la campana eso significo CERO capas de
    enforcement activas, con el doctor reportando "instalacion sana" y un commit
    que debia bloquearse aceptado (SPEC-014 FR-US1-001).
    """
    if not conservado:
        return []
    lineas = [
        "  ATENCION: se conservo el wiring que ya tenias, asi que el gate",
        "  spec-first puede no estar cableado:",
    ]
    lineas += [
        f"    - {rel} (deberia invocar {GATE_WIRING[rel]})" for rel in conservado
    ]
    lineas += [
        "  Resolvelo de una de estas dos formas:",
        "    - fusionalo a mano comparando con templates/wiring/ del kit, o",
        "    - reinstala con --force: si esta intacto lo pisa; si lo editaste,",
        "      deja la version del kit en <archivo>.kit-new para fusionar a mano.",
        "  Verificalo con: python tools/sdd/core/sdd_doctor.py",
        "",
    ]
    return lineas


def _next_steps(
    target: Path,
    layout: Layout | None = None,
    wiring_conservado: list[str] | None = None,
) -> str:
    """Secuencia para continuar, con el path real y sin los pasos ya cumplidos.

    El operador cierra la instalacion mirando esta salida, no el README: si el
    `cd` al destino no esta a la vista, los comandos `tools/sdd/...` que siguen
    no resuelven desde el clon del kit (SPEC-011 FR-009). Los pasos de
    preparacion ya satisfechos se omiten -- sugerir `git init` sobre un repo
    existente resta credibilidad al resto de la lista (FR-010).
    """
    lines = [f"\nListo. sdd-first instalado en {target}", ""]
    lines.extend(_wiring_notice(wiring_conservado or []))
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
            "  1. Pedile a tu asistente la skill sdd-configure (wizard sobre",
            "     .sdd/config.yaml), o edita el archivo a mano: dominio, carpetas",
            "     de codigo y tests, palabras excluidas, capas.",
            "  2. python tools/sdd/core/render.py"
            "               # CONSTITUTION.md + SPEC-000 + CI",
            "  3. python tools/sdd/core/pipeline.py"
            "             # verifica -> VERDE / ROJO",
            "",
            "Tu asistente ya tiene las skills SDD instaladas y listas para usar:",
            f"  {', '.join(PROJECT_SKILLS)}",
            "Que hace cada una y cuando usarla: docs/SDD-OPERACION.md.",
            "",
            "Para entender que quedo instalado, abri 00-INDEX.md: es el mapa de los",
            "documentos y de que archivo es el SSOT de cada tema.",
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


USAGE = (
    "Uso: python core/sdd_init.py [<target_dir>] [--target=<dir>]"
    " [--language=<lang>] [--force]"
)


def lenguajes_soportados() -> set[str]:
    """Lenguajes que `--language` acepta: los adaptadores en disco, mas `none`.

    El catalogo es el contenido de `adapters/`, no una lista escrita aparte: una
    constante seria un segundo SSOT que se desincroniza en cuanto se agregue un
    adaptador (SPEC-003 FR-012, Principio IV).
    """
    adapters = KIT_ROOT / "adapters"
    en_disco = (
        {d.name for d in adapters.iterdir() if d.is_dir()}
        if adapters.is_dir()
        else set()
    )
    return en_disco | {"none"}


def _abortar(motivo: str) -> None:
    """Sale sin escribir nada. El instalador toca ~40 archivos: ante una
    invocacion que no entendemos, no hay opcion segura que no sea no empezar."""
    print(f"ERROR: {motivo}\n{USAGE}", file=sys.stderr)
    raise SystemExit(2)


@dataclass
class Opciones:
    target: Path
    language: str
    force: bool


def _parse_argv(argv: list[str]) -> Opciones:
    """Parseo estricto: lo que no se reconoce aborta (SPEC-003 FR-012).

    Antes `main` partia argv en "empieza con --" y "el resto", miraba solo
    `--force`/`--language` y descartaba todo lo demas. `--target=<dir>` caia en
    ese descarte y el destino terminaba siendo el cwd, en silencio.
    """
    posicional: str | None = None
    target_flag: str | None = None
    language: str | None = None
    force = False

    resto = list(argv)
    while resto:
        arg = resto.pop(0)
        if not arg.startswith("--"):
            if posicional is not None:
                _abortar(f"destino repetido: '{posicional}' y '{arg}'")
            posicional = arg
            continue

        nombre, sep, valor = arg.partition("=")
        if nombre == "--force":
            if sep:
                _abortar("--force no lleva valor")
            force = True
        elif nombre in ("--target", "--language"):
            if not sep:
                if not resto or resto[0].startswith("--"):
                    _abortar(f"{nombre} necesita un valor")
                valor = resto.pop(0)
            if not valor:
                _abortar(f"{nombre} necesita un valor")
            if nombre == "--target":
                target_flag = valor
            else:
                language = valor
        else:
            _abortar(f"flag desconocido: {nombre}")

    if language is None:
        language = "python"
    elif language not in lenguajes_soportados():
        disponibles = ", ".join(sorted(lenguajes_soportados()))
        _abortar(f"lenguaje sin adaptador: '{language}'. Disponibles: {disponibles}")

    if posicional is not None and target_flag is not None:
        if Path(posicional).resolve() != Path(target_flag).resolve():
            _abortar(f"dos destinos distintos: '{posicional}' y '{target_flag}'")
    elegido = target_flag if target_flag is not None else posicional
    target = Path(elegido).resolve() if elegido else Path.cwd()

    return Opciones(target=target, language=language, force=force)


def main(argv: list[str]) -> int:
    import sdd_lock  # import tardio: sdd_lock importa sdd_init, evita el ciclo
    from sdd_config import load  # noqa: PLC0415 - mismo import tardio, evita ciclo

    opciones = _parse_argv(argv)
    force = opciones.force
    language = opciones.language
    target = opciones.target

    # Lock de una instalacion previa (si la hay): solo se usa para decidir
    # conflicto en un --force sobre plantillas editadas (FR-US2-013). Ilegible
    # se trata como ausente aca -- ese requisito estricto es de `sdd-update`.
    try:
        existing_lock = sdd_lock.load_lock(target)
    except sdd_lock.LockIlegible:
        existing_lock = None

    print(f"Instalando sdd-first en {target} (language={language})")

    # `.sdd/config.yaml` se escribe primero: `name`/`domain` para sustituir el
    # resto de las plantillas se leen de ahi (mismo criterio que `sdd-update`,
    # FR-US2-010), no de un literal aparte que podia divergir del config
    # sembrado -- y en un `--force` sobre un config ya editado, refleja lo que
    # el dueno declaro de verdad.
    config_line, layout = _write_config(target, target.name, language, force)
    load.cache_clear()
    cfg = load(target)
    name = cfg.name
    domain = cfg.domain

    log: list[str] = []
    for src_rel, dst_rel in STATIC_DOCS:
        log.append(
            _copy_text(
                TEMPLATES / src_rel,
                target / dst_rel,
                name,
                domain,
                force,
                dst_rel=dst_rel,
                lock=existing_lock,
            )
        )
    for src_rel, dst_rel in WIRING:
        log.append(
            _copy_text(
                TEMPLATES / src_rel,
                target / dst_rel,
                name,
                domain,
                force,
                dst_rel=dst_rel,
                lock=existing_lock,
            )
        )
        if dst_rel in _EXECUTABLE_WIRING and (target / dst_rel).exists():
            (target / dst_rel).chmod(0o755)
    wiring_conservado = _gate_wiring_conservado(target)
    log.append(config_line)
    log.append(_install_config_reference(target))
    log.extend(_vendor_kit(target, language, force))
    log.extend(_install_project_skills(target, force))
    log.extend(_generate_skill_adapters(target))

    for line in log:
        print(line)

    # Toda instalacion (incluida --force) deja lock: es lo que le permite a
    # una actualizacion futura afirmar que hubo instalacion (SPEC-025 FR-US1-002).
    sdd_lock.write_lock(target, sdd_lock.build_lock(KIT_ROOT, target, name, domain))

    print(_next_steps(target, layout, wiring_conservado))
    return 0


if __name__ == "__main__":
    forzar_salida_utf8()
    raise SystemExit(main(sys.argv[1:]))
