"""Catálogo de artefactos que instala el kit, con su clase de propiedad.

SSOT único, compartido por `sdd_init.py` (instalación y `--force`) y
`sdd_update.py` (actualización) — SPEC-025 FR-US2-001. Antes `STATIC_DOCS` y
`WIRING` vivían en `sdd_init.py`; se mudan acá para que un mismo listado sirva
a los dos consumidores sin que `sdd_init` y este módulo se importen en
círculo (`sdd_init` pasa a importar de acá, no al revés).

Clases:
    vendor    — del kit, se purga y recrea entero (`tools/sdd/`) o se
                reescribe siempre (`.sdd/config.reference.yaml`). El dueño
                nunca lo edita con expectativa de que sobreviva.
    plantilla — del kit, adoptable por el dueño. Se pisa si está intacta
                (coincide con el lock) y se reporta como conflicto si no.
    semilla   — se crea solo si falta y nunca se actualiza ni se pisa.

Los artefactos `generado` (CONSTITUTION.md, SPEC-000, ci.yml) no se enumeran
acá: su SSOT es `render.py._GENERATED`, y listarlos de nuevo sería la
duplicación que esta clase existe para evitar (FR-US2-001).
"""

from __future__ import annotations

from enum import Enum


class Clase(Enum):
    VENDOR = "vendor"
    PLANTILLA = "plantilla"
    SEMILLA = "semilla"


# Plantillas estáticas: (origen relativo a templates/, destino relativo a target).
STATIC_DOCS: list[tuple[str, str]] = [
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
WIRING: list[tuple[str, str]] = [
    ("wiring/claude-settings.json", ".claude/settings.json"),
    ("wiring/sdd_gate_hook.sh", ".claude/sdd_gate_hook.sh"),
    ("wiring/.pre-commit-config.yaml", ".pre-commit-config.yaml"),
    ("wiring/opencode-sdd-gate.js", ".opencode/plugin/sdd-gate.js"),
    ("wiring/.gitattributes", ".gitattributes"),
    ("wiring/.gitignore", ".gitignore"),
    ("wiring/hooks.json", ".agents/hooks.json"),
    ("wiring/agy_gate_hook.py", ".agents/agy_gate_hook.py"),
    ("wiring/agy_deny.json", ".agents/agy_deny.json"),
    ("wiring/current-spec", ".sdd/current-spec"),
]

# Wiring que necesita quedar con permiso de ejecucion tras copiarse/actualizarse.
EXECUTABLE_WIRING: frozenset[str] = frozenset({".claude/sdd_gate_hook.sh"})

# Sufijo del testigo que deja una `plantilla` en conflicto (SPEC-025 ANA-006):
# va al final para no cambiar la extension del original, y es propio (no
# ".new" generico) para que sea inequivoco y grepeable de donde salio.
KIT_NEW_SUFFIX = ".kit-new"

# Semilla: se crea si falta, nunca se actualiza. `.gitignore` lleva la
# excepción declarada de SPEC-004 FR-009 (se le agrega una línea puntual sin
# pisar el resto); eso lo maneja `_copy_text`/`ensure_gitignore_current_spec`,
# no esta clasificación.
SEMILLA_DESTINOS: frozenset[str] = frozenset(
    {
        "specs/SPECS_REGISTRY.md",
        "historial/sdd.md",
        ".gitignore",
        ".sdd/current-spec",
        ".sdd/config.yaml",
    }
)

# Vendor fuera de `tools/sdd/` (que se purga y recrea aparte, no por archivo):
# el catálogo de claves del config, que SPEC-013 FR-008 ya manda reescribir
# siempre.
VENDOR_DESTINOS: frozenset[str] = frozenset({".sdd/config.reference.yaml"})


def clase_de(dst_rel: str) -> Clase:
    """Clase de propiedad de un destino relativo al proyecto instalado."""
    rel = dst_rel.replace("\\", "/")
    if rel in SEMILLA_DESTINOS:
        return Clase.SEMILLA
    if rel in VENDOR_DESTINOS:
        return Clase.VENDOR
    return Clase.PLANTILLA


def catalogo_plantillas() -> list[tuple[str, str]]:
    """`(origen relativo a templates/, destino relativo al target)` del catálogo."""
    return [*STATIC_DOCS, *WIRING]


def decidir_plantilla(
    existe_en_disco: bool,
    hash_disco: str | None,
    hash_kit: str,
    hash_lock: str | None,
) -> str:
    """Decisión de conflicto para una `plantilla`, sin I/O (SPEC-025 FR-US2-005/006/012).

    Única función de decisión, compartida por `sdd-init --force` y
    `sdd-update`: evita que las dos rutas de escritura del kit diverjan sobre
    cuándo se puede pisar un archivo (ANA-002).

    Devuelve uno de:
        "nuevo"       — no está en disco y el lock no lo tenía: alta.
        "eliminada"   — no está en disco pero el lock sí lo tenía: el dueño lo
                         borró a propósito, no se reinstala.
        "sin_cambios" — está en disco y ya coincide con lo que el kit entrega
                         ahora (independiente de si hay lock).
        "actualizar"  — está en disco, coincide con el lock (intacta) y el kit
                         trae contenido distinto: se pisa sin preguntar.
        "conflicto"   — todo lo demás: está en disco y no hay lock (no se
                         puede afirmar que esté intacta), o difiere del lock
                         (el dueño la editó).
    """
    if not existe_en_disco:
        return "eliminada" if hash_lock is not None else "nuevo"
    if hash_disco == hash_kit:
        return "sin_cambios"
    if hash_lock is not None and hash_disco == hash_lock:
        return "actualizar"
    return "conflicto"
