"""Tests del registro de specs de sdd_spec (SPEC-003 FR-003)."""

import sdd_spec

REGISTRY_CON_ROADMAP = """# Registro de specs — demo

## Specs vigentes

| ID | Título | Estado | Iteración | Formato | Archivo |
|----|--------|--------|-----------|---------|---------|
| SPEC-000 | Nomenclatura | active | 0 | casero | [SPEC-000-naming.md](SPEC-000-naming.md) |

## Roadmap / política de datos

- (pendiente)
"""

ROW = "| SPEC-001 | Nueva | draft | - | hibrido | [SPEC-001-nueva.md](SPEC-001-nueva.md) |"


def test_inserta_dentro_de_la_tabla_no_al_final_del_archivo():
    result = sdd_spec._insert_registry_row(REGISTRY_CON_ROADMAP, ROW)
    lines = result.splitlines()
    fila = lines.index(ROW)
    roadmap = lines.index("## Roadmap / política de datos")
    assert fila < roadmap
    # la fila queda contigua a la tabla (línea anterior también es de tabla)
    assert lines[fila - 1].startswith("| SPEC-000")


def test_sin_tabla_cae_a_append():
    result = sdd_spec._insert_registry_row("# Registro vacío\n", ROW)
    assert result.rstrip().endswith(ROW)


def test_slugify_normaliza():
    assert sdd_spec._slugify("Mi Capacidad Nueva!") == "mi-capacidad-nueva"
