"""Indice invertido archivo->spec y triage de solape (SPEC-022 US2)."""

import spec_index
from sdd_config import TriageConfig

CONFIG_TRIAGE = TriageConfig(stopwords=frozenset({"spec", "specs", "sdd"}))


def _repo(tmp_path, *filas):
    """Repo con registro y specs. `filas`: (num, titulo, estado, cuerpo)."""
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    specs = tmp_path / "specs"
    specs.mkdir()
    tabla = [
        "| ID | Título | Estado | Iteración | Formato | Archivo |",
        "|----|--------|--------|-----------|---------|---------|",
    ]
    for num, titulo, estado, cuerpo in filas:
        archivo = f"SPEC-{num}-{titulo.lower().replace(' ', '-')}.md"
        tabla.append(
            f"| SPEC-{num} | {titulo} | {estado} | - | hibrido "
            f"| [{archivo}]({archivo}) |"
        )
        (specs / archivo).write_text(cuerpo, encoding="utf-8")
    (specs / "SPECS_REGISTRY.md").write_text("\n".join(tabla) + "\n", encoding="utf-8")
    return tmp_path


def _cuerpo(entities=(), coverage=""):
    lineas = ["# Spec demo", "", "## Key Entities", ""]
    lineas += [f"- {e}" for e in entities]
    lineas += ["", "## Coverage mapping", "", coverage]
    return "\n".join(lineas) + "\n"


# -- el indice ------------------------------------------------------------------


def test_indice_toma_las_rutas_de_key_entities(tmp_path):
    """FR-US2-001/002: la ruta sale del token, la descripcion se descarta."""
    repo = _repo(
        tmp_path,
        ("021", "Gate", "draft", _cuerpo(["`core/sdd_gate.py` — el interlock"])),
    )

    index = spec_index.build_index(repo)

    assert index["core/sdd_gate.py"] == {"SPEC-021-gate"}


def test_indice_separa_varias_entidades_en_una_linea(tmp_path):
    """FR-US2-002: el punto medio separa entradas dentro de la misma linea."""
    repo = _repo(
        tmp_path,
        ("021", "Gate", "draft", _cuerpo(["`core/a.py` · `core/b.py` — dos cosas"])),
    )

    index = spec_index.build_index(repo)

    assert index["core/a.py"] == {"SPEC-021-gate"}
    assert index["core/b.py"] == {"SPEC-021-gate"}


def test_indice_ignora_las_entradas_conceptuales_sin_ruta(tmp_path):
    """FR-US2-002: "Registro de specs vigentes" no aporta ninguna ruta."""
    repo = _repo(
        tmp_path,
        ("021", "Gate", "draft", _cuerpo(["Registro de specs vigentes — concepto"])),
    )

    assert spec_index.build_index(repo) == {}


def test_indice_resuelve_un_token_sin_directorio_por_basename(tmp_path):
    """FR-US2-002: `sdd_spec.py` a secas se resuelve contra los archivos reales."""
    repo = _repo(
        tmp_path, ("021", "Gate", "draft", _cuerpo(["`sdd_spec.py` — la CLI"]))
    )
    (repo / "core").mkdir()
    (repo / "core" / "sdd_spec.py").write_text("", encoding="utf-8")

    assert spec_index.build_index(repo)["core/sdd_spec.py"] == {"SPEC-021-gate"}


def test_indice_descarta_un_basename_ambiguo(tmp_path):
    """FR-US2-002: si resuelve a mas de un archivo, no se sabe de cual se habla."""
    repo = _repo(tmp_path, ("021", "Gate", "draft", _cuerpo(["`adapter.py` — cual?"])))
    for carpeta in ("uno", "dos"):
        (repo / carpeta).mkdir()
        (repo / carpeta / "adapter.py").write_text("", encoding="utf-8")

    assert spec_index.build_index(repo) == {}


def test_indice_conserva_las_rutas_que_todavia_no_existen(tmp_path):
    """FR-US2-003: una spec draft nombra lo que va a crear, y es lo que el gate
    bloquea primero. Descartarlo dejaria ciego al aviso de reuso."""
    repo = _repo(
        tmp_path,
        ("021", "Gate", "draft", _cuerpo(["`core/todavia_no_existe.py` — futuro"])),
    )

    assert spec_index.build_index(repo)["core/todavia_no_existe.py"] == {
        "SPEC-021-gate"
    }


def test_indice_toma_los_tests_del_coverage_mapping(tmp_path):
    """FR-US2-001: segunda fuente."""
    repo = _repo(
        tmp_path,
        ("021", "Gate", "draft", _cuerpo(coverage="| FR-001 | tests/unit/test_g.py |")),
    )

    assert spec_index.build_index(repo)["tests/unit/test_g.py"] == {"SPEC-021-gate"}


def test_indice_toma_las_citas_del_codigo(tmp_path):
    """FR-US2-001: tercera fuente, la señal mas dura de todas."""
    repo = _repo(tmp_path, ("021", "Gate", "draft", _cuerpo()))
    (repo / ".sdd").mkdir()
    (repo / ".sdd" / "config.yaml").write_text(
        "dirs:\n  source_roots: [core]\n  tests_unit: tests/unit\n", encoding="utf-8"
    )
    (repo / "core").mkdir()
    (repo / "core" / "citador.py").write_text(
        "# implementa SPEC-021 FR-003\n", encoding="utf-8"
    )

    assert spec_index.build_index(repo)["core/citador.py"] == {"SPEC-021-gate"}


def test_indice_ignora_las_specs_no_vigentes(tmp_path):
    """FR-US2-003: una superseded ya no gobierna nada."""
    repo = _repo(
        tmp_path,
        ("021", "Vieja", "superseded", _cuerpo(["`core/a.py` — de la vieja"])),
    )

    assert spec_index.build_index(repo) == {}


def test_indice_sin_registro_no_rompe(tmp_path):
    """FR-US2-003: una fuente ausente reduce la cobertura, nunca da error."""
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")

    assert spec_index.build_index(tmp_path) == {}


def test_specs_for_path_devuelve_id_y_titulo(tmp_path):
    """FR-US3-001: lo que el gate necesita nombrar."""
    repo = _repo(
        tmp_path, ("021", "Gate", "draft", _cuerpo(["`core/sdd_gate.py` — el gate"]))
    )

    assert spec_index.specs_for_path("core/sdd_gate.py", repo) == [
        ("SPEC-021-gate", "Gate")
    ]


def test_specs_for_path_sin_specs_asociadas_devuelve_vacio(tmp_path):
    repo = _repo(tmp_path, ("021", "Gate", "draft", _cuerpo()))

    assert spec_index.specs_for_path("core/otro.py", repo) == []


# -- normalizacion ---------------------------------------------------------------


def test_palabras_trata_guiones_y_underscores_como_separadores():
    """FR-US2-006: sin esto `sdd_spec` seria un token inalcanzable."""
    assert "spec" in spec_index.palabras("sdd_spec", TriageConfig())
    assert "reusar" in spec_index.palabras("reusar-specs", TriageConfig())


def test_palabras_normaliza_acentos_y_mayusculas():
    assert spec_index.palabras("Relación", TriageConfig()) == {"relacion"}


def test_palabras_descarta_stopwords_y_palabras_cortas():
    config = TriageConfig(stopwords=frozenset({"spec"}), min_word_len=4)
    assert spec_index.palabras("spec de gate", config) == {"gate"}


# -- el triage --------------------------------------------------------------------


def test_triage_por_titulo_marca_la_spec_que_comparte_palabras(tmp_path):
    """FR-US2-006: al menos `min_matches` palabras significativas en comun."""
    repo = _repo(tmp_path, ("021", "Reusar specs existentes", "draft", _cuerpo()))

    candidatas = spec_index.triage(
        "reusar specs existentes en el kit", repo, config=CONFIG_TRIAGE
    )

    assert [c.spec_id for c in candidatas] == ["SPEC-021-reusar-specs-existentes"]
    assert not candidatas[0].por_archivo


def test_triage_por_titulo_no_marca_con_una_sola_palabra(tmp_path):
    repo = _repo(tmp_path, ("021", "Reusar specs existentes", "draft", _cuerpo()))

    assert spec_index.triage("reusar plantillas", repo, config=CONFIG_TRIAGE) == []


def test_triage_con_touches_marca_la_spec_del_archivo(tmp_path):
    """FR-US2-004: la salida indica que archivo la señalo."""
    repo = _repo(
        tmp_path, ("021", "Gate", "draft", _cuerpo(["`core/sdd_gate.py` — el gate"]))
    )

    candidatas = spec_index.triage(
        "otra cosa", repo, touches=("core/sdd_gate.py",), config=CONFIG_TRIAGE
    )

    assert [c.spec_id for c in candidatas] == ["SPEC-021-gate"]
    assert candidatas[0].por_archivo
    assert "core/sdd_gate.py" in candidatas[0].motivo


def test_triage_sin_touches_deduce_las_rutas_del_titulo(tmp_path):
    """FR-US2-005: las palabras del titulo se buscan en el *stem* del archivo."""
    repo = _repo(
        tmp_path, ("021", "Otra", "draft", _cuerpo(["`core/sdd_gate.py` — el gate"]))
    )

    candidatas = spec_index.triage(
        "aviso del gate al bloquear", repo, config=CONFIG_TRIAGE
    )

    assert [c.spec_id for c in candidatas] == ["SPEC-021-otra"]
    assert candidatas[0].por_archivo


def test_triage_matchea_contra_el_stem_no_contra_la_ruta(tmp_path):
    """FR-US2-005: 'specs' aparece en casi toda ruta del kit y no debe señalar."""
    repo = _repo(
        tmp_path, ("021", "Otra", "draft", _cuerpo(["`specs/SPEC-000-naming.md` — x"]))
    )

    # Sin stopwords siquiera: lo que evita el falso positivo es comparar contra
    # el stem `SPEC-000-naming` y no contra el segmento de directorio `specs/`.
    candidatas = spec_index.triage(
        "registro de specs", repo, config=TriageConfig(stopwords=frozenset())
    )

    assert candidatas == []


def test_triage_ignora_las_stopwords_del_dominio(tmp_path):
    """FR-US2-009: un titulo de puro vocabulario del dominio no produce nada."""
    repo = _repo(
        tmp_path, ("021", "Gate spec-first", "draft", _cuerpo(["`core/spec.py` — x"]))
    )

    assert spec_index.triage("spec sdd specs", repo, config=CONFIG_TRIAGE) == []


def test_triage_pone_las_de_archivo_primero(tmp_path):
    """FR-US2-007: la señal de archivo es mas fuerte que la lexica."""
    repo = _repo(
        tmp_path,
        ("021", "Aviso de reuso", "draft", _cuerpo()),
        ("022", "Otra", "draft", _cuerpo(["`core/reuso.py` — x"])),
    )

    candidatas = spec_index.triage("aviso de reuso", repo, config=CONFIG_TRIAGE)

    assert [c.por_archivo for c in candidatas] == [True, False]
    assert candidatas[0].spec_id == "SPEC-022-otra"


def test_triage_no_duplica_una_spec_señalada_por_ambas_vias(tmp_path):
    repo = _repo(
        tmp_path, ("021", "Aviso de reuso", "draft", _cuerpo(["`core/reuso.py` — x"]))
    )

    candidatas = spec_index.triage("aviso de reuso", repo, config=CONFIG_TRIAGE)

    assert len(candidatas) == 1
    assert candidatas[0].por_archivo
