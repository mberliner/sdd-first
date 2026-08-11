"""Crea una spec nueva y la deja lista para codear (respaldo de `sdd-spec`).

Genera `specs/SPEC-NNN-slug.md` desde la plantilla, agrega la fila al registro y
declara la spec en `.sdd/current-spec` (desbloqueando el gate spec-first).

Uso:
    python core/sdd_spec.py "<slug-o-titulo>" [--title "Título legible"]

El número NNN se asigna como el siguiente correlativo disponible en specs/.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_traceability import (  # noqa: E402
    _parse_registry,
    has_written_requirements,
    iter_coverage_entries,
)
from sdd_config import find_repo_root, write_text_lf  # noqa: E402
from sdd_gate import is_source_path  # noqa: E402

_USO = (
    'Uso: sdd_spec.py "<slug>" [--title "Título"]\n'
    "     sdd_spec.py --reuse SPEC-NNN --fr FR-NNN"
)

# Estados del registro sobre los que se puede adoptar una spec: los mismos que
# el gate acepta como vigentes (SPEC-017 FR-US2-002). Adoptar una spec que el
# gate no aceptaria dejaria el trabajo declarado contra un documento cerrado.
_ESTADOS_VIGENTES = frozenset({"draft", "active"})

# Forma de un identificador de requisito. Es el patron de check_traceability y
# del gate: el script no impone convencion sobre como se numeran las historias
# (SPEC-022 FR-US1-007).
_FR_ID = re.compile(r"^FR-[A-Za-z0-9-]+$")


class _ArgError(Exception):
    """Argumentos invalidos, con el mensaje que argparse habria impreso."""


class _Parser(argparse.ArgumentParser):
    """ArgumentParser que informa el error en vez de matar el proceso.

    `sdd_spec.main` es invocable como funcion (la skill y los tests la llaman
    directo), asi que el `SystemExit` que argparse lanza por su cuenta seria un
    efecto colateral sorpresivo: el contrato del modulo es devolver el codigo.
    """

    def error(self, message: str):  # type: ignore[override]
        raise _ArgError(message)


def _build_parser() -> _Parser:
    parser = _Parser(prog="sdd_spec.py", add_help=False)
    parser.add_argument("slug", nargs="?")
    parser.add_argument("--title", default=None)
    parser.add_argument("--reuse", default=None, metavar="SPEC-NNN")
    parser.add_argument("--fr", default=None, metavar="FR-NNN")
    return parser


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "spec"


def _next_number(specs_dir: Path) -> int:
    nums = [
        int(m.group(1))
        for p in specs_dir.glob("SPEC-*.md")
        if (m := re.match(r"SPEC-(\d+)", p.name))
    ]
    return (max(nums) + 1) if nums else 1


def _declare_current_spec(current: Path, spec_id: str) -> None:
    """Declara `spec_id` preservando las líneas de comentario ya presentes.

    SPEC-004 FR-007: antes esto pisaba el archivo entero, destruyendo el
    header de `templates/wiring/current-spec`; `sdd_reset.py` (FR-002) filtra
    comentarios post-commit, pero sin header no había nada que preservar y el
    working tree quedaba sucio tras cada commit.
    """
    comments: list[str] = []
    if current.exists():
        comments = [
            ln
            for ln in current.read_text(encoding="utf-8").splitlines()
            if ln.startswith("#")
        ]
    current.parent.mkdir(exist_ok=True)
    write_text_lf(current, "\n".join([*comments, spec_id]) + "\n")


def _insert_registry_row(text: str, row: str) -> str:
    """Inserta `row` al final de la tabla de specs, no al final del archivo.

    El registro plantilla tiene secciones después de la tabla (p. ej. Roadmap);
    apenderla al archivo dejaba la fila fuera de la tabla (SPEC-003 FR-003).
    La tabla objetivo es el primer bloque contiguo de líneas `|` del documento.
    """
    lines = text.splitlines()
    last_row_index = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("|"):
            last_row_index = i
        elif last_row_index is not None:
            break  # fin del primer bloque de tabla
    if last_row_index is None:
        return text.rstrip() + "\n" + row + "\n"
    lines.insert(last_row_index + 1, row)
    return "\n".join(lines).rstrip() + "\n"


def _registry_rows(repo_root: Path):  # type: ignore[no-untyped-def]
    errors: list[str] = []
    return _parse_registry(repo_root / "specs" / "SPECS_REGISTRY.md", errors), errors


def _resolve_registry_row(token: str, rows):  # type: ignore[no-untyped-def]
    """Fila del registro que `token` designa, o `(None, motivo)`.

    El ID se resuelve contra `SPECS_REGISTRY.md` —SSOT de las specs vigentes— y
    no por glob sobre `specs/`, que devolveria tambien archivos sin registrar
    (SPEC-022 FR-US1-002). Se acepta tanto el ID completo como el numero pelado;
    lo segundo solo si designa a una sola fila.
    """
    token = token.strip().removesuffix(".md")
    exactas = [r for r in rows if Path(r.archivo).stem == token]
    if len(exactas) == 1:
        return exactas[0], ""
    prefijo = [r for r in rows if Path(r.archivo).stem.startswith(f"{token}-")]
    if len(prefijo) == 1:
        return prefijo[0], ""
    if not prefijo:
        return None, (
            f"'{token}' no figura en specs/SPECS_REGISTRY.md. Solo se puede "
            "adoptar una spec registrada."
        )
    candidatas = ", ".join(sorted(Path(r.archivo).stem for r in prefijo))
    return None, (
        f"'{token}' resuelve a mas de una spec ({candidatas}). Pasa el ID completo."
    )


def _coverage_tests(text: str, fr_id: str) -> tuple[bool, list[str]]:
    """`(tiene_fila, rutas_de_test)` del FR en el *Coverage mapping* de la spec."""
    tiene_fila = False
    rutas: list[str] = []
    for fr, tests in iter_coverage_entries(text):
        if fr != fr_id:
            continue
        tiene_fila = True
        rutas.extend(t for t in tests if t not in rutas)
    return tiene_fila, rutas


def _falta_coverage(text: str, fr_id: str, repo_root: Path) -> tuple[str, list[str]]:
    """`(motivo_de_aborto, avisos)` de la exigencia de mapping sobre una spec `active`.

    Adoptar una spec `active` y escribirle un FR deja rojo a `check_traceability`
    —que corre en el pre-commit con `always_run`— hasta que exista la fila. Ese
    rojo bloquearia incluso el commit del test rojo, asi que se exige por
    adelantado (SPEC-022 FR-US1-004). Es el unico rojo que se adelanta: que el
    test *falle* es el estado esperado y el script no ejecuta la suite
    (FR-US1-006).
    """
    tiene_fila, rutas = _coverage_tests(text, fr_id)
    if not tiene_fila:
        return (
            f"{fr_id} no tiene fila en el *Coverage mapping* de la spec. Sobre una "
            "spec 'active' la fila es obligatoria: sin ella check_traceability "
            "queda rojo y el pre-commit no deja commitear ni el test.",
            [],
        )
    avisos: list[str] = []
    faltantes = [ruta for ruta in rutas if not (repo_root / ruta).exists()]
    for ruta in faltantes:
        if is_source_path(ruta, repo_root):
            # El test cae dentro de `dirs.source_roots`: exigirlo aca cerraria el
            # flujo contra si mismo, porque el gate impide crearlo antes de tener
            # la spec declarada. Se declara igual y se avisa (FR-US1-004).
            avisos.append(
                f"El test '{ruta}' todavia no existe. Cae dentro de "
                "dirs.source_roots, asi que se declara la spec igual: creralo "
                "ahora que el gate esta abierto, antes de commitear."
            )
        else:
            return (
                f"El test '{ruta}' referenciado por {fr_id} en el *Coverage "
                "mapping* no existe. Crealo (puede —y se espera que— falle) "
                "antes de adoptar la spec.",
                [],
            )
    if not rutas:
        avisos.append(
            f"La fila de {fr_id} en el *Coverage mapping* no nombra ningun archivo "
            "de test. check_traceability no lo exige, pero el FR queda sin cubrir."
        )
    return "", avisos


def _reuse(spec_token: str, fr_id: str, repo_root: Path) -> int:
    """Adopta una spec vigente en vez de crear otra (SPEC-022 US1).

    No escribe nada hasta haber verificado todo: un abort deja el arbol de
    trabajo identico a como estaba.
    """
    if not _FR_ID.match(fr_id):
        print(
            f"--fr '{fr_id}' no tiene la forma FR-NNN (se acepta cualquier "
            "identificador FR-[A-Za-z0-9-]+, p. ej. FR-007 o FR-US1-007).",
            file=sys.stderr,
        )
        return 2

    rows, errores_registro = _registry_rows(repo_root)
    if errores_registro and not rows:
        print("; ".join(errores_registro), file=sys.stderr)
        return 1
    row, motivo = _resolve_registry_row(spec_token, rows)
    if row is None:
        print(motivo, file=sys.stderr)
        return 1

    spec_id = Path(row.archivo).stem
    spec_file = repo_root / "specs" / row.archivo
    if not spec_file.exists():
        print(
            f"{spec_id} esta en el registro pero su archivo no existe: {spec_file}.",
            file=sys.stderr,
        )
        return 1
    if row.estado not in _ESTADOS_VIGENTES:
        print(
            f"{spec_id} esta en estado '{row.estado}': solo se puede adoptar una "
            "spec vigente (draft o active).",
            file=sys.stderr,
        )
        return 1

    text = spec_file.read_text(encoding="utf-8")
    if not has_written_requirements(text, fr_id):
        print(
            f"{fr_id} todavia no esta escrito en {row.archivo}. Escribilo primero, "
            "en la User Story cuyo alcance cubre la capacidad y con el ID de esa "
            "historia; si ninguna la cubre, agrega una User Story nueva —con "
            "prioridad e Independent Test— y que el requisito nazca ahi. Forma: "
            f"**{fr_id}** MUST: <lo que la capacidad debe cumplir>. Adoptar una "
            "spec no puede abrir el gate con menos evidencia que crearla.",
            file=sys.stderr,
        )
        return 1

    avisos: list[str] = []
    if row.estado == "active":
        motivo_coverage, avisos = _falta_coverage(text, fr_id, repo_root)
        if motivo_coverage:
            print(motivo_coverage, file=sys.stderr)
            return 1

    current = repo_root / ".sdd" / "current-spec"
    _declare_current_spec(current, spec_id)
    print(f"Adoptada {row.archivo} ({row.estado}) para {fr_id}: no se creo spec nueva.")
    print(f"Declarada en {current}")
    for aviso in avisos:
        print(f"Aviso: {aviso}")
    return 0


def main(argv: list[str]) -> int:
    try:
        ns = _build_parser().parse_args(argv)
    except _ArgError as exc:
        print(f"{_USO}\n{exc}", file=sys.stderr)
        return 2

    if ns.reuse:
        if ns.slug:
            print(
                f"{_USO}\n--reuse adopta una spec existente: no lleva slug "
                "posicional (no se crea ninguna).",
                file=sys.stderr,
            )
            return 2
        if not ns.fr:
            print(
                "--reuse exige --fr FR-NNN: el requisito que la capacidad nueva "
                "agrega a la spec adoptada. Sin el, el gate quedaria abierto "
                "contra los FR viejos, con menos evidencia que al crear una spec.",
                file=sys.stderr,
            )
            return 2
        return _reuse(ns.reuse, ns.fr, find_repo_root())

    if ns.fr:
        print("--fr solo tiene sentido junto a --reuse.", file=sys.stderr)
        return 2
    if not ns.slug:
        print(_USO, file=sys.stderr)
        return 2
    slug = _slugify(ns.slug)
    title = ns.title or ns.slug

    repo_root = find_repo_root()
    specs_dir = repo_root / "specs"
    specs_dir.mkdir(exist_ok=True)
    number = _next_number(specs_dir)
    spec_id = f"SPEC-{number:03d}-{slug}"
    spec_file = specs_dir / f"{spec_id}.md"
    if spec_file.exists():
        print(f"Ya existe: {spec_file}", file=sys.stderr)
        return 1

    template_path = specs_dir / "SPEC-TEMPLATE.md"
    if template_path.exists():
        body = template_path.read_text(encoding="utf-8")
        body = body.replace("SPEC-NNN: <título agnóstico>", f"{spec_id}: {title}")
    else:
        body = f"# {spec_id}: {title}\n\n(TODO: completar según docs/SPEC-FORMAT.md)\n"
    write_text_lf(spec_file, body)
    print(f"Creada {spec_file}")

    # Registro: agrega una fila draft a la tabla de SPECS_REGISTRY.md.
    registry = specs_dir / "SPECS_REGISTRY.md"
    row = f"| SPEC-{number:03d} | {title} | draft | - | hibrido | [{spec_id}.md]({spec_id}.md) |"
    if registry.exists():
        text = registry.read_text(encoding="utf-8")
        write_text_lf(registry, _insert_registry_row(text, row))
        print(f"Registrada en {registry}")

    # Declara la spec vigente para el gate.
    current = repo_root / ".sdd" / "current-spec"
    _declare_current_spec(current, spec_id)
    print(f"Declarada en {current}")
    print(
        "\nEscribí los FR de la spec ANTES de tocar código: el gate exige que la "
        "spec declarada tenga requisitos escritos (los placeholders de la "
        "plantilla no cuentan)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
