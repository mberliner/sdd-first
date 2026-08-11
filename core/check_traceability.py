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
4. Relacion entre specs (solo 'hibrido'): la seccion "Relacion con specs
   existentes" esta presente, sus referencias existen, cada campo directo tiene
   su reciproco del otro lado y una spec 'active' no se apoya en una no vigente.

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
_FR_DECL_LINE = re.compile(r"\*\*(FR-[A-Za-z0-9-]+)\*\*(.*)")
_FR_ANY = re.compile(r"\bFR-[A-Za-z0-9-]+\b")
_SC_ANY = re.compile(r"\bSC-[A-Za-z0-9-]+\b")
_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Referencia a un archivo de test: acepta prefijos comunes de varios ecosistemas.
# El lookbehind y el grupo de directorios previos capturan la ruta *entera*: sin
# ellos, de `src/tests/test_x.py` se extraia `tests/test_x.py` —el match arrancaba
# en la palabra `tests`— y la verificacion de existencia buscaba un archivo que
# no esta ahi. Rompia justo en el layout con los tests dentro de las carpetas de
# codigo, el que contempla SPEC-022 FR-US1-004.
_TEST_REF = re.compile(
    r"(?<![\w/.-])(?:[\w.-]+/)*(?:tests?|spec)/[\w./-]+\.(?:py|js|ts|go|rs|java|rb)"
)
_COVERAGE_HEADING = re.compile(r"(?i)^#+\s+.*coverage mapping")

# -- Relacion entre specs (SPEC-023 US2) ---------------------------------------
#
# La *lectura* de la seccion vive aca y en ningun otro lado (FR-US2-011): quien
# la escribe --`sdd_spec.py` al crear con --extends/--supersedes, `sdd_doctor.py`
# al inyectarla o cerrar reciprocos-- consume estos mismos parseadores desde
# `spec_relations.py`. Dos ideas de que es la seccion harian que el validador
# rechace lo que el creador escribe. El validador, en cambio, no escribe: un gate
# que modifica lo que valida deja de ser gate.
RELATION_HEADING = re.compile(r"(?i)^#+\s+.*relaci.n con specs existentes")

# Los tres pares simetricos, directo -> inverso (FR-US2-003). El tipo de la
# relacion se lee desde cualquiera de los dos lados, asi que una violacion puede
# nombrar el campo exacto que falta.
RELATION_PAIRS: tuple[tuple[str, str], ...] = (
    ("Extiende", "Extendida por"),
    ("Depende de", "Es dependencia de"),
    ("Supersede", "Superseded por"),
)
RELATION_FIELDS: tuple[str, ...] = tuple(f for par in RELATION_PAIRS for f in par)
RELATION_COUNTERPART: dict[str, str] = {
    **{directo: inverso for directo, inverso in RELATION_PAIRS},
    **{inverso: directo for directo, inverso in RELATION_PAIRS},
}

# Campo de prosa de la misma seccion: no declara un enlace, asi que no se valida
# como tal, pero el escritor necesita reconocerlo (`--rationale`, FR-US1-002).
RATIONALE_FIELD = "Por qué no cabe en una spec existente"

# Los dos campos que expresan apoyo en algo que tiene que seguir en pie: una spec
# 'active' no puede apuntarlos a una no vigente (FR-US2-007). `Supersede:` queda
# fuera --apuntar a una 'superseded' es el desenlace normal de reemplazarla-- y
# los tres inversos tambien.
RELATION_NEEDS_ACTIVE: frozenset[str] = frozenset({"Extiende", "Depende de"})

_KNOWN_FIELDS = {campo.lower(): campo for campo in (*RELATION_FIELDS, RATIONALE_FIELD)}
_RELATION_LABEL = re.compile(r"\*\*\s*([^*:]+?)\s*:?\s*\*\*(.*)")
_SPEC_REF = re.compile(r"\bSPEC-(\d+)\b")
# Marcadores de vacio (SPEC-FORMAT.md): las specs se escriben a mano y en
# consolas que no siempre producen el mismo caracter, asi que em dash, en dash,
# guion simple y campo sin valor son lo mismo.
EMPTY_MARKERS: frozenset[str] = frozenset({"", "—", "–", "-", "--"})


def canonical_field(raw: str) -> str | None:
    """Nombre canonico del campo, o `None` si la etiqueta no es de la seccion."""
    return _KNOWN_FIELDS.get(" ".join(raw.split()).lower())


def is_empty_value(raw: str) -> bool:
    return raw.strip() in EMPTY_MARKERS


def spec_id_of(name: str) -> str | None:
    """`SPEC-NNN` normalizado a tres digitos, desde un archivo o una referencia."""
    match = _SPEC_REF.search(name)
    return f"SPEC-{int(match.group(1)):03d}" if match else None


def iter_relation_fields(text: str):
    """Devuelve `(indice_de_linea, indice_de_celda, match)` por campo declarado.

    La seccion agrupa varios campos por linea separados por `|`, asi que la
    unidad de parseo es la celda y no la linea. Lo consume tanto el validador
    como el escritor, que necesita ademas las coordenadas para reemplazar.
    """
    inside = False
    for i, raw in enumerate(text.splitlines()):
        stripped = raw.strip()
        if RELATION_HEADING.match(stripped):
            inside = True
            continue
        if stripped.startswith("#"):
            inside = False
        if not inside:
            continue
        for j, celda in enumerate(raw.split("|")):
            match = _RELATION_LABEL.search(celda)
            if match and canonical_field(match.group(1)):
                yield i, j, match


def has_relation_section(text: str) -> bool:
    return any(RELATION_HEADING.match(line.strip()) for line in text.splitlines())


def parse_relations(text: str) -> dict[str, tuple[str, ...]] | None:
    """Los seis campos de enlace de la spec, o `None` si no tiene la seccion.

    Un campo ausente y un campo vacio son lo mismo: tupla vacia. La distincion
    que importa es "la spec no tiene la seccion" (violacion de FR-US2-004) vs
    "la tiene y no declara enlaces", que es el caso normal.
    """
    if not has_relation_section(text):
        return None
    relations: dict[str, tuple[str, ...]] = {campo: () for campo in RELATION_FIELDS}
    for _i, _j, match in iter_relation_fields(text):
        campo = canonical_field(match.group(1))
        if campo not in relations:
            continue  # el campo de prosa no declara enlaces
        refs = [f"SPEC-{int(n):03d}" for n in _SPEC_REF.findall(match.group(2))]
        relations[campo] = tuple(dict.fromkeys([*relations[campo], *refs]))
    return relations


# Keyword normativo con que arranca el cuerpo de un FR de la plantilla
# (`**FR-001** MUST: ...`): sin el, del placeholder no queda texto. El umbral
# separa eso de un requisito escrito, sin pretender juzgar su calidad.
_FR_KEYWORD = re.compile(r"(?i)^\s*(MUST|SHOULD|MAY)\s*:?")
_MIN_FR_CHARS = 1


def iter_fr_entries(text: str):
    """Devuelve `(fr_id, resto_de_la_linea)` para cada FR declarado en el texto."""
    for match in _FR_DECL_LINE.finditer(text):
        yield match.group(1), match.group(2)


def has_written_requirements(text: str, fr_id: str | None = None) -> bool:
    """True si la spec declara un FR con texto propio mas alla del keyword.

    Es la evidencia de que la spec precede al codigo (SPEC-017 FR-US3-001). Con
    `fr_id` la pregunta se acota a *ese* requisito, que es lo que necesita
    `sdd_spec.py --reuse` (SPEC-022 FR-US1-003): adoptar una spec no puede abrir
    el gate contra los FR viejos. La comparacion es por igualdad exacta del ID,
    nunca por substring: `FR-007` no satisface a `FR-US1-007` (FR-US1-007).

    Vive aca --y no en el gate, que fue su primer consumidor-- porque es parseo
    de spec: dos ideas de "que es un FR escrito" harian que `sdd_spec` acepte lo
    que `sdd_gate` rechaza (SPEC-022 FR-US1-005, Principio IV).
    """
    for declarado, rest in iter_fr_entries(text):
        if fr_id is not None and declarado != fr_id:
            continue
        cuerpo = _FR_KEYWORD.sub("", rest)
        if sum(c.isalnum() for c in cuerpo) >= _MIN_FR_CHARS:
            return True
    return False


def iter_coverage_entries(text: str):
    """Devuelve `(fr_id, rutas_de_test)` por cada fila del *Coverage mapping*.

    Liga cada requisito con los tests de su propia fila, que es lo que necesita
    `--reuse` para verificar la fila del FR nuevo (SPEC-022 FR-US1-004). La
    verificacion de cobertura de este mismo modulo consume la union de lo que
    esta funcion emite, para que haya un unico lector del formato.
    """
    for line in _coverage_section_text(text).splitlines():
        tests = tuple(dict.fromkeys(_TEST_REF.findall(line)))
        for fr in _FR_ANY.findall(line):
            yield fr, tests


class _RegistryRow:
    """Una fila de la tabla de specs vigentes de SPECS_REGISTRY.md."""

    def __init__(
        self,
        spec_id: str,
        estado: str,
        formato: str,
        archivo: str,
        titulo: str = "",
    ) -> None:
        self.spec_id = spec_id
        self.estado = estado
        self.formato = formato
        self.archivo = archivo  # basename del .md
        self.titulo = titulo  # columna Titulo, tal cual se escribio

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
        spec_id, titulo, estado, _iter, formato, archivo_cell = cells[:6]
        match = _LINK.search(archivo_cell)
        target = match.group(1) if match else archivo_cell
        rows.append(
            _RegistryRow(
                spec_id,
                estado.lower(),
                formato.lower(),
                Path(target).name,
                titulo,
            )
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
    declared = set(_FR_DECL.findall(text))
    covered = {fr for fr, _tests in iter_coverage_entries(text)}
    for fr in sorted(declared - covered):
        errors.append(f"{name}: {fr} declarado pero ausente del Coverage mapping.")
    # Los test refs se buscan sobre la seccion entera y no sobre las filas que
    # `iter_coverage_entries` liga a un FR: una referencia escrita en una linea
    # sin FR (una nota al pie de la tabla) tambien tiene que existir en disco.
    for test_ref in sorted(set(_TEST_REF.findall(_coverage_section_text(text)))):
        if not (repo_root / test_ref).exists():
            errors.append(
                f"{name}: test referenciado en Coverage mapping no existe: '{test_ref}'."
            )
    _check_fr_mentioned_in_tests(name, text, repo_root, errors)


# Vecinos que invalidan un match como token completo del ID (FR-002): no solo
# no-\w, porque `-` es no-\w y un `\b` de re dejaria pasar `FR-1` dentro de
# `FR-1-ALGO` (los IDs multi-HU usan `-` como separador interno).
_TOKEN_NEIGHBOR = "[A-Za-z0-9_-]"


def _fr_appears_as_token(fr_id: str, content: str) -> bool:
    pattern = re.compile(
        rf"(?<!{_TOKEN_NEIGHBOR}){re.escape(fr_id)}(?!{_TOKEN_NEIGHBOR})"
    )
    return pattern.search(content) is not None


def _read_test_text(path: Path) -> str:
    """Contenido del test, o cadena vacia si no se puede leer como texto (FR-001)."""
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def _check_fr_mentioned_in_tests(
    name: str, text: str, repo_root: Path, errors: list[str]
) -> None:
    cache: dict[str, str] = {}
    for fr, tests in iter_coverage_entries(text):
        if not tests:
            continue  # fila sin ruta de test: fuera de alcance (FR-001)
        found = False
        for test_ref in tests:
            if test_ref not in cache:
                cache[test_ref] = _read_test_text(repo_root / test_ref)
            if _fr_appears_as_token(fr, cache[test_ref]):
                found = True
                break
        if not found:
            errors.append(f"{name}: {fr} no aparece en {', '.join(tests)}.")


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


def _check_relations(
    rows: list[_RegistryRow], specs_dir: Path, errors: list[str]
) -> None:
    """Seccion presente, referencias reales, reciprocas y sin apoyo en no vigentes.

    Corre sobre el conjunto de specs y no spec por spec porque la reciprocidad
    (FR-US2-006) solo se puede juzgar mirando las dos puntas del enlace.
    """
    por_id: dict[str, _RegistryRow] = {}
    for row in rows:
        spec_id = spec_id_of(row.archivo)
        if spec_id:
            por_id[spec_id] = row
    en_disco: dict[str, Path] = {}
    for path in _spec_files(specs_dir):
        spec_id = spec_id_of(path.name)
        if spec_id:
            en_disco[spec_id] = path

    relaciones: dict[str, dict[str, tuple[str, ...]]] = {}
    for spec_id, path in sorted(en_disco.items()):
        row = por_id.get(spec_id)
        if row is None or not row.is_hybrid:
            continue  # las specs de otro formato no se validan contra la seccion
        parsed = parse_relations(path.read_text(encoding="utf-8"))
        if parsed is None:
            errors.append(
                f"{path.name}: falta la seccion 'Relacion con specs existentes', "
                "obligatoria en specs hibrido (ver docs/SPEC-FORMAT.md). Se "
                "inyecta con: sdd_doctor.py --fix"
            )
            continue
        relaciones[spec_id] = parsed

    for spec_id, parsed in sorted(relaciones.items()):
        nombre = en_disco[spec_id].name
        for campo, refs in parsed.items():
            for ref in refs:
                if ref not in por_id or ref not in en_disco:
                    errors.append(
                        f"{nombre}: '{campo}: {ref}' apunta a una spec que no "
                        "existe en disco o no esta en SPECS_REGISTRY.md."
                    )
                    continue
                if (
                    campo in RELATION_NEEDS_ACTIVE
                    and por_id[spec_id].estado == "active"
                    and por_id[ref].estado != "active"
                ):
                    errors.append(
                        f"{nombre}: spec 'active' con '{campo}: {ref}', que esta "
                        f"en estado '{por_id[ref].estado}'. Ambos campos expresan "
                        "apoyo en una spec que tiene que seguir vigente."
                    )
                otra = relaciones.get(ref)
                if otra is None:
                    continue  # spec no hibrida, o sin seccion: ya se reporto
                inverso = RELATION_COUNTERPART[campo]
                if spec_id not in otra[inverso]:
                    errors.append(
                        f"{nombre}: '{campo}: {ref}' sin enlace inverso: falta "
                        f"'{inverso}: {spec_id}' en {en_disco[ref].name}. Se "
                        "cierra con: sdd_doctor.py --fix"
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

    _check_relations(rows, specs_dir, errors)

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
