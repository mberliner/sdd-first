"""Crea una spec nueva y la deja lista para codear (respaldo de `sdd-spec`).

Genera `specs/SPEC-NNN-slug.md` desde la plantilla, agrega la fila al registro y
declara la spec en `.sdd/current-spec` (desbloqueando el gate spec-first).

Uso:
    python core/sdd_spec.py "<slug-o-titulo>" [--title "Título legible"]

El número NNN se asigna como el siguiente correlativo disponible en specs/.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sdd_config import find_repo_root  # noqa: E402


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
    current.write_text(
        "\n".join([*comments, spec_id]) + "\n", encoding="utf-8", newline="\n"
    )


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


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print('Uso: sdd_spec.py "<slug>" [--title "Título"]', file=sys.stderr)
        return 2
    title = None
    for a in argv:
        if a.startswith("--title="):
            title = a.split("=", 1)[1]
    slug = _slugify(args[0])
    title = title or args[0]

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
    spec_file.write_text(body, encoding="utf-8", newline="\n")
    print(f"Creada {spec_file}")

    # Registro: agrega una fila draft a la tabla de SPECS_REGISTRY.md.
    registry = specs_dir / "SPECS_REGISTRY.md"
    row = f"| SPEC-{number:03d} | {title} | draft | - | hibrido | [{spec_id}.md]({spec_id}.md) |"
    if registry.exists():
        text = registry.read_text(encoding="utf-8")
        registry.write_text(
            _insert_registry_row(text, row), encoding="utf-8", newline="\n"
        )
        print(f"Registrada en {registry}")

    # Declara la spec vigente para el gate.
    current = repo_root / ".sdd" / "current-spec"
    _declare_current_spec(current, spec_id)
    print(f"Declarada en {current}")
    print(
        "\nEditá la spec (agregá los FR) ANTES de tocar código: el gate exige que la "
        "spec sea modificada después de declararla."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
