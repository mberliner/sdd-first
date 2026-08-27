"""Tests del verificador de trazabilidad (SPEC-002 FR-003/FR-006)."""

from pathlib import Path

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


def test_valid_estados_no_incluye_notas():
    # SPEC-017 FR-US2-004: `notas` no tiene semantica documentada ni fila que lo
    # use; VALID_ESTADOS es el origen unico y no lo declara.
    assert "notas" not in ct.VALID_ESTADOS
    assert ct.VALID_ESTADOS == frozenset({"draft", "active", "superseded", "archived"})


def test_registry_estados_documentados_coinciden_con_valid_estados():
    # SPEC-017 FR-US2-004: SPECS_REGISTRY.md cita VALID_ESTADOS como origen,
    # no mantiene una enumeracion propia que pueda divergir.
    repo_root = Path(__file__).resolve().parents[2]
    texto = (repo_root / "specs" / "SPECS_REGISTRY.md").read_text(encoding="utf-8")
    for estado in ct.VALID_ESTADOS:
        assert f"`{estado}`" in texto
    assert "`notas`" not in texto


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
    """SPEC-022 FR-US1-004 / FR-US1-005: un unico lector del *Coverage mapping*."""
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
    (tmp_path / "src" / "tests" / "test_a.py").write_text(
        "# cubre FR-001\n", encoding="utf-8"
    )
    text = (
        "## Coverage mapping\n\n| FR-001 | src/tests/test_a.py |\n\n"
        "## Functional Requirements\n\n- **FR-001** MUST: algo.\n"
    )

    errors: list[str] = []
    ct._check_coverage("SPEC-001-a.md", text, tmp_path, errors)

    assert errors == []


# -- SPEC-024: el FR referenciado tiene que aparecer en el test -----------------


def test_fr_ausente_del_test_reporta_violacion(tmp_path):
    """FR-001: archivo existe pero no menciona el FR que dice cubrir."""
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_x.py").write_text(
        "# no menciona ningun requisito\n", encoding="utf-8"
    )
    errors: list[str] = []
    ct._check_coverage("SPEC-001.md", HYBRID_OK, tmp_path, errors)
    assert any("FR-001" in e and "no aparece" in e for e in errors)


def test_fr_presente_en_docstring_no_reporta_violacion(tmp_path):
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_x.py").write_text(
        'def test_algo():\n    """Cubre FR-001."""\n', encoding="utf-8"
    )
    errors: list[str] = []
    ct._check_coverage("SPEC-001.md", HYBRID_OK, tmp_path, errors)
    assert not any("no aparece" in e for e in errors)


def test_fr_en_al_menos_uno_de_varios_tests_alcanza(tmp_path):
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_a.py").write_text("nada", encoding="utf-8")
    (tmp_path / "tests" / "unit" / "test_b.py").write_text("FR-001", encoding="utf-8")
    text = (
        "## Coverage mapping\n\n"
        "| FR-001 | tests/unit/test_a.py tests/unit/test_b.py |\n"
    )
    errors: list[str] = []
    ct._check_coverage("SPEC-001.md", text, tmp_path, errors)
    assert not any("no aparece" in e for e in errors)


def test_fila_sin_ruta_de_test_no_evalua_esta_regla(tmp_path):
    text = "## Coverage mapping\n\n| FR-001 | (sin test aun) |\n"
    errors: list[str] = []
    ct._check_coverage("SPEC-001.md", text, tmp_path, errors)
    assert not any("no aparece" in e for e in errors)


def test_fr_1_no_se_satisface_con_fr_10(tmp_path):
    """FR-002: match de token completo, no substring."""
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_y.py").write_text("FR-10", encoding="utf-8")
    text = "## Coverage mapping\n\n| FR-1 | tests/unit/test_y.py |\n"
    errors: list[str] = []
    ct._check_coverage("SPEC-001.md", text, tmp_path, errors)
    assert any("FR-1" in e and "no aparece" in e for e in errors)


def test_fr_1_no_se_satisface_con_fr_1_algo(tmp_path):
    """FR-002: `-` cuenta como vecino que invalida el match, pese a ser no-\\w."""
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_y.py").write_text(
        "FR-1-ALGO", encoding="utf-8"
    )
    text = "## Coverage mapping\n\n| FR-1 | tests/unit/test_y.py |\n"
    errors: list[str] = []
    ct._check_coverage("SPEC-001.md", text, tmp_path, errors)
    assert any("FR-1" in e and "no aparece" in e for e in errors)


def test_test_no_decodificable_cuenta_como_sin_mencion(tmp_path):
    """FR-001: binario/encoding inesperado no aborta el check."""
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_x.py").write_bytes(b"\xff\xfe\x00\x01")
    errors: list[str] = []
    ct._check_coverage("SPEC-001.md", HYBRID_OK, tmp_path, errors)
    assert any("FR-001" in e and "no aparece" in e for e in errors)


# -- SPEC-023 US2: la relacion entre specs se verifica sola ---------------------

_CAMPOS_VACIOS = {
    "Extiende": "—",
    "Supersede": "—",
    "Depende de": "—",
    "Extendida por": "—",
    "Es dependencia de": "—",
    "Superseded por": "—",
}


def _seccion(**campos) -> str:
    """La seccion con los valores pedidos; el resto de los campos, vacios."""
    valores = {**_CAMPOS_VACIOS, **campos}

    def celda(campo: str) -> str:
        return f"**{campo}:** {valores[campo]}"

    return (
        "## Relación con specs existentes\n\n"
        f"- {celda('Extiende')} | {celda('Supersede')} | {celda('Depende de')}\n"
        f"- {celda('Extendida por')} | {celda('Es dependencia de')} "
        f"| {celda('Superseded por')}\n"
        "- **Por qué no cabe en una spec existente:** —\n"
    )


def _repo_specs(tmp_path, specs):
    """`specs` = {spec_id: (estado, formato, seccion_o_None)} -> (rows, specs_dir)."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(exist_ok=True)
    rows = []
    for spec_id, (estado, formato, seccion) in specs.items():
        archivo = f"{spec_id}-x.md"
        cuerpo = f"# {spec_id}\n\n" + (seccion or "")
        (specs_dir / archivo).write_text(cuerpo, encoding="utf-8")
        rows.append(ct._RegistryRow(spec_id, estado, formato, archivo))
    return rows, specs_dir


def test_pares_simetricos_se_leen_desde_los_dos_lados():
    """FR-US2-003: el tipo de la relacion se lee desde cualquiera de las puntas."""
    for directo, inverso in ct.RELATION_PAIRS:
        assert ct.RELATION_COUNTERPART[directo] == inverso
        assert ct.RELATION_COUNTERPART[inverso] == directo
    assert len(ct.RELATION_FIELDS) == 6


def test_marcadores_de_vacio_son_todos_equivalentes():
    """FR-US2-004: em dash, en dash, guion simple y campo sin valor son lo mismo."""
    for marcador in ("—", "–", "-", ""):
        texto = "# SPEC-001\n\n" + _seccion(Extiende=marcador)
        assert ct.parse_relations(texto)["Extiende"] == ()


def test_sin_seccion_el_parseo_lo_distingue_de_la_seccion_vacia():
    """FR-US2-008/011: el doctor decide inyectar leyendo esto, no reparseando."""
    assert ct.parse_relations("# SPEC-001\n\n## Clarifications\n") is None
    assert ct.parse_relations("# SPEC-001\n\n" + _seccion()) is not None


def test_spec_hibrida_sin_la_seccion_falla_nombrandola(tmp_path):
    """FR-US2-004."""
    rows, specs_dir = _repo_specs(tmp_path, {"SPEC-001": ("draft", "hibrido", None)})
    errors: list[str] = []
    ct._check_relations(rows, specs_dir, errors)
    assert any("SPEC-001-x.md" in e and "Relacion con specs" in e for e in errors)


def test_spec_casero_sin_la_seccion_no_se_valida(tmp_path):
    """FR-US2-004: las generadas por render.py quedan fuera o habria drift."""
    rows, specs_dir = _repo_specs(tmp_path, {"SPEC-000": ("active", "casero", None)})
    errors: list[str] = []
    ct._check_relations(rows, specs_dir, errors)
    assert errors == []


def test_referencia_a_spec_inexistente_es_violacion(tmp_path):
    """FR-US2-005: un enlace colgado."""
    rows, specs_dir = _repo_specs(
        tmp_path,
        {"SPEC-001": ("draft", "hibrido", _seccion(**{"Depende de": "SPEC-099"}))},
    )
    errors: list[str] = []
    ct._check_relations(rows, specs_dir, errors)
    assert any("SPEC-099" in e for e in errors)


def test_falta_el_enlace_inverso_nombra_spec_y_campo(tmp_path):
    """FR-US2-006: la violacion dice qué campo falta y dónde."""
    rows, specs_dir = _repo_specs(
        tmp_path,
        {
            "SPEC-001": ("draft", "hibrido", _seccion(**{"Depende de": "SPEC-002"})),
            "SPEC-002": ("draft", "hibrido", _seccion()),
        },
    )
    errors: list[str] = []
    ct._check_relations(rows, specs_dir, errors)
    assert any(
        "SPEC-001-x.md" in e and "Es dependencia de" in e and "SPEC-002-x.md" in e
        for e in errors
    )


def test_reciproco_del_tipo_equivocado_no_alcanza(tmp_path):
    """FR-US2-003/006: el par tiene que ser el que corresponde a la relacion."""
    rows, specs_dir = _repo_specs(
        tmp_path,
        {
            "SPEC-001": ("draft", "hibrido", _seccion(Extiende="SPEC-002")),
            # El inverso de `Extiende` es `Extendida por`, no `Es dependencia de`.
            "SPEC-002": (
                "draft",
                "hibrido",
                _seccion(**{"Es dependencia de": "SPEC-001"}),
            ),
        },
    )
    errors: list[str] = []
    ct._check_relations(rows, specs_dir, errors)
    assert any("Extendida por" in e for e in errors)


def test_active_apoyada_en_draft_falla_pero_el_inverso_pasa(tmp_path):
    """FR-US2-007: `Depende de` exige vigencia; `Es dependencia de` no."""
    directa = {
        "SPEC-001": ("active", "hibrido", _seccion(**{"Depende de": "SPEC-002"})),
        "SPEC-002": ("draft", "hibrido", _seccion(**{"Es dependencia de": "SPEC-001"})),
    }
    errors: list[str] = []
    rows, specs_dir = _repo_specs(tmp_path, directa)
    ct._check_relations(rows, specs_dir, errors)
    assert any("SPEC-001-x.md" in e and "draft" in e for e in errors)

    # Misma pareja, mirada desde el lado inverso: la 'active' no se apoya en nada.
    inversa = {
        "SPEC-001": (
            "active",
            "hibrido",
            _seccion(**{"Es dependencia de": "SPEC-002"}),
        ),
        "SPEC-002": ("draft", "hibrido", _seccion(**{"Depende de": "SPEC-001"})),
    }
    errors = []
    rows, specs_dir = _repo_specs(tmp_path, inversa)
    ct._check_relations(rows, specs_dir, errors)
    assert errors == []


def test_supersede_hacia_una_superseded_es_el_desenlace_normal(tmp_path):
    """FR-US2-007: la restriccion de estado no alcanza a `Supersede:`."""
    rows, specs_dir = _repo_specs(
        tmp_path,
        {
            "SPEC-001": ("active", "hibrido", _seccion(Supersede="SPEC-002")),
            "SPEC-002": (
                "superseded",
                "hibrido",
                _seccion(**{"Superseded por": "SPEC-001"}),
            ),
        },
    )
    errors: list[str] = []
    ct._check_relations(rows, specs_dir, errors)
    assert errors == []


def test_el_repositorio_migrado_no_tiene_ninguna_violacion():
    """FR-US2-009 / FR-US2-010, SC-007: la migracion cerro las vueltas preexistentes.

    Activar la reciprocidad sobre specs `active` que nadie toco no puede
    estrenar el validador en rojo.
    """
    from pathlib import Path

    specs_dir = Path(__file__).resolve().parents[2] / "specs"
    rows = ct._parse_registry(specs_dir / "SPECS_REGISTRY.md", [])
    errors: list[str] = []
    ct._check_relations(rows, specs_dir, errors)
    assert errors == []


def test_spec_files_ignora_template(tmp_path):
    (tmp_path / "SPEC-TEMPLATE.md").write_text("", encoding="utf-8")
    (tmp_path / "SPEC-001-a.md").write_text("", encoding="utf-8")
    files = ct._spec_files(tmp_path)
    assert [p.name for p in files] == ["SPEC-001-a.md"]


# -- FR-009: el mismo criterio de "que es una spec" en los dos lados -----------


def _registro(filas: str) -> str:
    return (
        "| ID | Título | Estado | Iteración | Formato | Archivo |\n"
        "|----|--------|--------|-----------|---------|---------|\n" + filas
    )


def test_una_fila_a_spec_no_numerada_no_se_reporta_como_inexistente(tmp_path):
    """SPEC-001 FR-009: el archivo esta en disco; decir lo contrario es falso.

    El lado del disco ignora las specs no numeradas (`_SPEC_FILE` lo documenta);
    el lado del registro las aceptaba, y de la asimetria salia un mensaje que
    manda a buscar un archivo que esta ahi.
    """
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "SPECS_REGISTRY.md").write_text(
        _registro(
            "| SPEC-TEMPLATE | Plantilla | archived | - | casero | "
            "[SPEC-TEMPLATE.md](SPEC-TEMPLATE.md) |\n"
        ),
        encoding="utf-8",
    )
    (specs / "SPEC-TEMPLATE.md").write_text("# plantilla\n", encoding="utf-8")

    errores: list[str] = []
    filas = ct._parse_registry(specs / "SPECS_REGISTRY.md", errores)
    ct._check_consistency(filas, specs, errores)

    assert not any("inexistente" in e for e in errores), errores


def test_una_fila_a_spec_numerada_ausente_si_se_reporta(tmp_path):
    """Contraste de control: la simetria no puede apagar la deteccion real."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "SPECS_REGISTRY.md").write_text(
        _registro(
            "| SPEC-042 | Fantasma | active | - | hibrido | "
            "[SPEC-042-fantasma.md](SPEC-042-fantasma.md) |\n"
        ),
        encoding="utf-8",
    )

    errores: list[str] = []
    filas = ct._parse_registry(specs / "SPECS_REGISTRY.md", errores)
    ct._check_consistency(filas, specs, errores)

    assert any("SPEC-042-fantasma.md" in e and "inexistente" in e for e in errores), (
        errores
    )
