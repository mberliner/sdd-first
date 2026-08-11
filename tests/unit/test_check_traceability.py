"""Tests del verificador de trazabilidad (SPEC-002 FR-003/FR-006)."""

import check_traceability as ct

HYBRID_OK = """# SPEC-001: Demo

## User Story (Priority P1)

Como rol, quiero capacidad para beneficio.

## Functional Requirements

- **FR-001** MUST: algo verificable.

## Success Criteria

- **SC-001** binario.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_x.py |
"""


def test_estructura_completa_sin_errores():
    errors: list[str] = []
    ct._check_structure("SPEC-001.md", HYBRID_OK, errors)
    assert errors == []


def test_estructura_detecta_secciones_faltantes():
    errors: list[str] = []
    ct._check_structure("SPEC-001.md", "# SPEC-001: vacia\n", errors)
    joined = "\n".join(errors)
    assert "User Story" in joined
    assert "Functional Requirements" in joined
    assert "Success Criteria" in joined
    assert "Coverage mapping" in joined


def test_coverage_detecta_fr_sin_mapear(tmp_path):
    text = HYBRID_OK.replace(
        "- **FR-001** MUST: algo verificable.",
        "- **FR-001** MUST: algo verificable.\n- **FR-002** MUST: sin mapear.",
    )
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_x.py").write_text("", encoding="utf-8")
    errors: list[str] = []
    ct._check_coverage("SPEC-001.md", text, tmp_path, errors)
    assert any("FR-002" in e for e in errors)


def test_coverage_detecta_test_inexistente(tmp_path):
    errors: list[str] = []
    ct._check_coverage("SPEC-001.md", HYBRID_OK, tmp_path, errors)
    assert any("test_x.py" in e for e in errors)


def test_consistencia_detecta_spec_no_registrada_y_dangling(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "SPEC-001-a.md").write_text("# a\n", encoding="utf-8")
    rows = [ct._RegistryRow("SPEC-002", "draft", "casero", "SPEC-002-b.md")]
    errors: list[str] = []
    ct._check_consistency(rows, specs, errors)
    joined = "\n".join(errors)
    assert "SPEC-001-a.md" in joined  # en disco, no registrada
    assert "SPEC-002-b.md" in joined  # registrada, no en disco


def test_consistencia_detecta_estado_invalido(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    rows = [ct._RegistryRow("SPEC-001", "vigente", "casero", "SPEC-001-a.md")]
    (specs / "SPEC-001-a.md").write_text("# a\n", encoding="utf-8")
    errors: list[str] = []
    ct._check_consistency(rows, specs, errors)
    assert any("estado invalido" in e for e in errors)


def test_parse_registry_extrae_filas(tmp_path):
    registry = tmp_path / "SPECS_REGISTRY.md"
    registry.write_text(
        "| ID | Título | Estado | Iteración | Formato | Archivo |\n"
        "|----|--------|--------|-----------|---------|---------|\n"
        "| SPEC-001 | Demo | active | 0 | hibrido | [SPEC-001-a.md](SPEC-001-a.md) |\n",
        encoding="utf-8",
    )
    errors: list[str] = []
    rows = ct._parse_registry(registry, errors)
    assert errors == []
    assert len(rows) == 1
    assert rows[0].estado == "active"
    assert rows[0].is_hybrid
    assert rows[0].archivo == "SPEC-001-a.md"


def test_parse_registry_conserva_el_titulo(tmp_path):
    """SPEC-022 FR-US2-006: el triage compara contra la columna Titulo."""
    registry = tmp_path / "SPECS_REGISTRY.md"
    registry.write_text(
        "| ID | Título | Estado | Iteración | Formato | Archivo |\n"
        "|----|--------|--------|-----------|---------|---------|\n"
        "| SPEC-001 | Gate spec-first | active | 0 | hibrido "
        "| [SPEC-001-a.md](SPEC-001-a.md) |\n",
        encoding="utf-8",
    )
    rows = ct._parse_registry(registry, [])
    assert rows[0].titulo == "Gate spec-first"


def test_iter_coverage_entries_liga_cada_fr_con_sus_tests():
    """SPEC-022 FR-US1-004/005: un unico lector del *Coverage mapping*."""
    text = (
        "## Coverage mapping\n\n"
        "| Requisito | Cubierto por |\n"
        "|-----------|--------------|\n"
        "| FR-001 | tests/unit/test_a.py |\n"
        "| FR-US2-003 | tests/unit/test_b.py |\n"
        "\n## Otra seccion\n\n| FR-999 | tests/unit/test_fuera.py |\n"
    )
    entries = dict(ct.iter_coverage_entries(text))
    assert entries["FR-001"] == ("tests/unit/test_a.py",)
    assert entries["FR-US2-003"] == ("tests/unit/test_b.py",)
    # Lo que esta fuera de la seccion no es parte del mapping.
    assert "FR-999" not in entries


def test_test_ref_captura_la_ruta_entera_no_desde_la_palabra_tests(tmp_path):
    """El match arrancaba en `tests`, perdiendo el prefijo `src/`.

    Con los tests dentro de las carpetas de codigo —el layout que contempla
    SPEC-022 FR-US1-004— la verificacion de existencia buscaba la ruta
    equivocada y reportaba un test faltante que si estaba.
    """
    (tmp_path / "src" / "tests").mkdir(parents=True)
    (tmp_path / "src" / "tests" / "test_a.py").write_text("", encoding="utf-8")
    text = (
        "## Coverage mapping\n\n| FR-001 | src/tests/test_a.py |\n\n"
        "## Functional Requirements\n\n- **FR-001** MUST: algo.\n"
    )

    errors: list[str] = []
    ct._check_coverage("SPEC-001-a.md", text, tmp_path, errors)

    assert errors == []


def test_spec_files_ignora_template(tmp_path):
    (tmp_path / "SPEC-TEMPLATE.md").write_text("", encoding="utf-8")
    (tmp_path / "SPEC-001-a.md").write_text("", encoding="utf-8")
    files = ct._spec_files(tmp_path)
    assert [p.name for p in files] == ["SPEC-001-a.md"]
