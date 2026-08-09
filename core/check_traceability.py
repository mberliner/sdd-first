"""Verificador de trazabilidad spec<->codigo (nucleo minimo del kit).

Gate determinista de trazabilidad. Sobre el directorio de specs:

1. Estructura: cada spec en formato hibrido (segun el campo Formato del registro)
   tiene las secciones obligatorias de docs/SPEC-FORMAT.md (User Story con
   prioridad, Functional Requirements con FR-NNN, Success Criteria con SC-NNN,
   Coverage mapping).
2. Consistencia spec<->registro: toda spec en disco esta registrada en
   SPECS_REGISTRY.md con un Estado valido, y el registro no apunta a inexistentes.
3. Cobertura FR->test (solo specs 'active'): cada FR-NNN declarado aparece en el
   Coverage mapping, y toda referencia a un archivo de test dentro del Coverage
   mapping existe.

No juzga *adecuacion* (eso lo aportan las skills analyze/clarify y la revision
humana). Es agnostico de dominio y de lenguaje. Detalle en docs/SDD-ENFORCEMENT.md.

Uso:
    python core/check_traceability.py specs

Exit code 0 si todo OK, 1 si hay violaciones, 2 si error de argumentos.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

VALID_ESTADOS: frozenset[str] = frozenset(
    {"draft", "active", "superseded", "archived", "notas"}
)

# Una spec real es SPEC-<numero>-...; SPEC-TEMPLATE.md y otros no numerados se ignoran.
_SPEC_FILE = re.compile(r"^SPEC-\d+.*\.md$")


def _spec_files(specs_dir: Path) -> list[Path]:
    return sorted(p for p in specs_dir.glob("SPEC-*.md") if _SPEC_FILE.match(p.name))


_FR_DECL = re.compile(r"\*\*(FR-[A-Za-z0-9-]+)\*\*")
_FR_DECL_LINE = re.compile(r"\*\*FR-[A-Za-z0-9-]+\*\*(.*)")
_FR_ANY = re.compile(r"\bFR-[A-Za-z0-9-]+\b")
_SC_ANY = re.compile(r"\bSC-[A-Za-z0-9-]+\b")
_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Referencia a un archivo de test: acepta prefijos comunes de varios ecosistemas.
_TEST_REF = re.compile(r"(?:tests?|spec)/[\w./-]+\.(?:py|js|ts|go|rs|java|rb)")
_COVERAGE_HEADING = re.compile(r"(?i)^#+\s+.*coverage mapping")


def iter_fr_declarations(text: str):
    """Devuelve el resto de la linea para cada FR declarado en el texto."""
    for match in _FR_DECL_LINE.finditer(text):
        yield match.group(1)


class _RegistryRow:
    """Una fila de la tabla de specs vigentes de SPECS_REGISTRY.md."""

    def __init__(self, spec_id: str, estado: str, formato: str, archivo: str) -> None:
        self.spec_id = spec_id
        self.estado = estado
        self.formato = formato
        self.archivo = archivo  # basename del .md

    @property
    def is_hybrid(self) -> bool:
        return "brid" in self.formato  # tolera "hibrido"/"híbrido"


def _parse_registry(path: Path, errors: list[str]) -> list[_RegistryRow]:
    if not path.exists():
        errors.append(f"No existe el registro: {path}")
        return []

    rows: list[_RegistryRow] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        if cells[0] == "ID" or set(cells[0]) <= {"-", ":"}:
            continue
        spec_id, _titulo, estado, _iter, formato, archivo_cell = cells[:6]
        match = _LINK.search(archivo_cell)
        target = match.group(1) if match else archivo_cell
        rows.append(
            _RegistryRow(spec_id, estado.lower(), formato.lower(), Path(target).name)
        )
    return rows


def _coverage_section_text(text: str) -> str:
    """Concatena las lineas dentro de secciones 'Coverage mapping' (soporta multi-HU)."""
    out: list[str] = []
    inside = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if _COVERAGE_HEADING.match(stripped):
            inside = True
            continue
        if stripped.startswith("#"):
            inside = False
        if inside:
            out.append(raw)
    return "\n".join(out)


def _check_structure(name: str, text: str, errors: list[str]) -> None:
    if not re.search(r"(?im)^#+\s+.*User Story", text):
        errors.append(f"{name}: falta seccion 'User Story' (formato hibrido).")
    elif not re.search(r"(?i)priorit", text):
        errors.append(f"{name}: 'User Story' sin prioridad declarada.")
    if not re.search(r"(?im)^#+\s+.*Functional Requirements", text):
        errors.append(f"{name}: falta seccion 'Functional Requirements'.")
    if not _FR_ANY.search(text):
        errors.append(f"{name}: sin requisitos FR-NNN.")
    if not re.search(r"(?im)^#+\s+.*Success Criteria", text):
        errors.append(f"{name}: falta seccion 'Success Criteria'.")
    if not _SC_ANY.search(text):
        errors.append(f"{name}: sin criterios SC-NNN.")
    if not re.search(r"(?im)^#+\s+.*coverage mapping", text):
        errors.append(f"{name}: falta seccion 'Coverage mapping'.")


def _check_coverage(name: str, text: str, repo_root: Path, errors: list[str]) -> None:
    coverage = _coverage_section_text(text)
    declared = set(_FR_DECL.findall(text))
    covered = set(_FR_ANY.findall(coverage))
    for fr in sorted(declared - covered):
        errors.append(f"{name}: {fr} declarado pero ausente del Coverage mapping.")
    for test_ref in sorted(set(_TEST_REF.findall(coverage))):
        if not (repo_root / test_ref).exists():
            errors.append(
                f"{name}: test referenciado en Coverage mapping no existe: '{test_ref}'."
            )


def _check_consistency(
    rows: list[_RegistryRow], specs_dir: Path, errors: list[str]
) -> None:
    registry_specs = {
        r.archivo
        for r in rows
        if r.archivo.startswith("SPEC-") and r.archivo.endswith(".md")
    }
    disk_specs = {p.name for p in _spec_files(specs_dir)}
    for missing in sorted(disk_specs - registry_specs):
        errors.append(f"{missing}: archivo de spec no registrado en SPECS_REGISTRY.md.")
    for dangling in sorted(registry_specs - disk_specs):
        errors.append(
            f"SPECS_REGISTRY.md: entrada apunta a archivo inexistente '{dangling}'."
        )
    for row in rows:
        if row.estado and row.estado not in VALID_ESTADOS:
            errors.append(
                f"SPECS_REGISTRY.md: estado invalido '{row.estado}' en {row.spec_id}."
            )


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    if len(argv) < 2:
        print("Uso: check_traceability.py <specs_dir>", file=sys.stderr)
        return 2

    specs_dir = Path(argv[1])
    if not specs_dir.exists():
        print(f"No existe: {specs_dir}", file=sys.stderr)
        return 2

    repo_root = specs_dir.resolve().parent
    errors: list[str] = []

    rows = _parse_registry(specs_dir / "SPECS_REGISTRY.md", errors)
    _check_consistency(rows, specs_dir, errors)

    by_file = {r.archivo: r for r in rows}
    disk_specs = _spec_files(specs_dir)
    for spec_path in disk_specs:
        row = by_file.get(spec_path.name)
        if row is None or not row.is_hybrid:
            continue
        text = spec_path.read_text(encoding="utf-8")
        _check_structure(spec_path.name, text, errors)
        if row.estado == "active":
            _check_coverage(spec_path.name, text, repo_root, errors)

    if errors:
        print("Violaciones de trazabilidad:", file=sys.stderr)
        for err in errors:
            print(f"  x {err}", file=sys.stderr)
        print(
            f"\nTotal: {len(errors)} problema(s). Ver docs/SDD-ENFORCEMENT.md y docs/SPEC-FORMAT.md.",
            file=sys.stderr,
        )
        return 1

    print(f"Trazabilidad OK: {len(disk_specs)} spec(s) verificada(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
