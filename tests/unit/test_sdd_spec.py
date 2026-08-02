"""Tests de sdd_spec (SPEC-003 FR-003, SPEC-004 FR-007)."""

import sdd_spec

CURRENT_SPEC_HEADER = (
    "# Spec(s) vigente(s): una por línea, formato SPEC-NNN-slug.\n"
    "# El gate spec-first (core/sdd_gate.py) exige que al menos una spec listada aquí\n"
    "# exista, esté registrada y haya sido editada DESPUÉS de este archivo.\n"
    "# Vacío = ninguna edición de código fuente permitida.\n"
)

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


def test_declare_current_spec_preserva_comentarios(tmp_path):
    current = tmp_path / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER, encoding="utf-8")

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")

    text = current.read_text(encoding="utf-8")
    for line in CURRENT_SPEC_HEADER.splitlines():
        assert line in text
    assert "SPEC-005-demo" in text


def test_declare_current_spec_reemplaza_spec_previa_no_apila(tmp_path):
    current = tmp_path / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER + "SPEC-004-vieja\n", encoding="utf-8")

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")

    text = current.read_text(encoding="utf-8")
    assert "SPEC-004-vieja" not in text
    assert "SPEC-005-demo" in text


def test_declare_current_spec_sin_archivo_previo_no_falla(tmp_path):
    current = tmp_path / "current-spec"

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")

    assert current.read_text(encoding="utf-8") == "SPEC-005-demo\n"


def test_ciclo_declarar_luego_reset_deja_solo_el_header(tmp_path, monkeypatch):
    """SPEC-004 SC-004: tras declarar->commit->reset, queda igual al header."""
    import sdd_reset

    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    current = tmp_path / ".sdd" / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER, encoding="utf-8")
    monkeypatch.setattr(sdd_reset, "find_repo_root", lambda: tmp_path)

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")
    assert sdd_reset.main() == 0

    assert current.read_text(encoding="utf-8") == CURRENT_SPEC_HEADER
