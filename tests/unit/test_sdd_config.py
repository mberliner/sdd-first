"""Tests del loader de configuración (SPEC-002 FR-003, SPEC-005 FR-005)."""

from pathlib import Path

from sdd_config import (
    DEFAULT_SOURCE_ROOT,
    DEFAULT_TESTS_UNIT,
    DEFAULT_TRIAGE_MIN_MATCHES,
    DEFAULT_TRIAGE_MIN_WORD_LEN,
    SddConfig,
    write_text_lf,
)


def _cfg(raw: dict) -> SddConfig:
    return SddConfig(repo_root=Path("."), raw=raw)


def test_write_text_lf_escribe_utf8_con_fin_de_linea_lf(tmp_path):
    # SPEC-007 FR-006: Path.write_text no admite newline= en ninguna version de
    # Python; este helper via Path.open es el reemplazo correcto.
    target = tmp_path / "out.md"
    write_text_lf(target, "línea 1\nlínea 2\n")
    raw = target.read_bytes()
    assert raw == "línea 1\nlínea 2\n".encode()
    assert b"\r\n" not in raw


def test_defaults_con_config_vacio():
    cfg = _cfg({})
    assert cfg.language == "none"
    assert cfg.source_roots == [DEFAULT_SOURCE_ROOT]
    assert cfg.naming_prohibited == ()
    assert cfg.principles == []
    assert cfg.pipeline_steps == []


def test_source_roots_explicitos_tienen_prioridad():
    cfg = _cfg(
        {"dirs": {"domain": "nucleo/dominio", "source_roots": ["nucleo", "extras"]}}
    )
    assert cfg.source_roots == ["nucleo", "extras"]


def test_source_roots_derivados_de_capas_sin_tests():
    cfg = _cfg(
        {
            "dirs": {
                "domain": "src/domain",
                "adapters": "src/adapters",
                "tests_unit": "tests/unit",
            }
        }
    )
    assert cfg.source_roots == ["src"]


def test_naming_normaliza_a_minusculas():
    cfg = _cfg({"naming": {"prohibited": ["Acme", "GADGET"]}})
    assert cfg.naming_prohibited == ("acme", "gadget")


# SPEC-021: una clave declarada pero vacia se comporta como ausente. YAML carga
# `prohibited:` sin items como None, y vaciar la lista es la forma natural de
# desactivar la regla sin borrar la clave.


def test_naming_con_claves_vacias_equivale_a_ausentes():
    vacio = _cfg(
        {
            "naming": {
                "prohibited": None,
                "allowed_identifiers": None,
                "relax_in_tests": None,
            }
        }
    )
    ausente = _cfg({})
    assert vacio.naming_prohibited == ausente.naming_prohibited == ()
    assert vacio.naming_allowed == ausente.naming_allowed == frozenset()
    assert vacio.naming_relax_in_tests == ausente.naming_relax_in_tests == frozenset()


def test_naming_con_escalar_en_vez_de_lista_no_rompe():
    cfg = _cfg({"naming": {"prohibited": "acme"}})
    assert cfg.naming_prohibited == ()


def test_naming_acepta_tupla_ademas_de_lista():
    cfg = _cfg({"naming": {"prohibited": ("Acme",)}})
    assert cfg.naming_prohibited == ("acme",)


def test_principles_ignora_entradas_no_dict():
    cfg = _cfg({"principles": [{"id": "I", "title": "T"}, "basura", None]})
    assert len(cfg.principles) == 1
    assert cfg.principles[0].id == "I"


# SPEC-020: el paso que activa el enforcement lo declara el principio, no un
# mapa hardcodeado en check_constitution.


def test_principle_step_es_opcional_y_default_vacio():
    cfg = _cfg({"principles": [{"id": "I", "title": "T", "enforcement": "x.py"}]})
    assert cfg.principles[0].step == ""


def test_enforcement_steps_mapea_tool_a_paso():
    cfg = _cfg(
        {
            "principles": [
                {
                    "id": "I",
                    "title": "T",
                    "enforcement": "check_naming.py",
                    "step": "naming",
                },
            ]
        }
    )
    assert cfg.enforcement_steps == {"check_naming.py": "naming"}


def test_enforcement_steps_usa_el_basename_de_la_ruta():
    cfg = _cfg(
        {
            "principles": [
                {
                    "id": "I",
                    "title": "T",
                    "enforcement": "adapters/python/check_naming.py",
                    "step": "naming",
                },
            ]
        }
    )
    assert cfg.enforcement_steps == {"check_naming.py": "naming"}


def test_enforcement_steps_ignora_principio_sin_step_o_sin_enforcement():
    cfg = _cfg(
        {
            "principles": [
                {"id": "I", "title": "Hooks", "enforcement": "sdd_gate.py"},
                {"id": "II", "title": "Convencion", "step": "naming"},
            ]
        }
    )
    assert cfg.enforcement_steps == {}


def test_enforcement_steps_falla_ante_colision_de_nombres():
    import pytest

    cfg = _cfg(
        {
            "principles": [
                {
                    "id": "I",
                    "title": "C1",
                    "enforcement": "core/check_naming.py",
                    "step": "naming",
                },
                {
                    "id": "II",
                    "title": "C2",
                    "enforcement": "adapters/python/check_naming.py",
                    "step": "naming",
                },
            ]
        }
    )
    with pytest.raises(ValueError, match="Colisión de enforcement: 'check_naming.py'"):
        _ = cfg.enforcement_steps


def test_triage_ausente_cae_a_los_defaults():
    """SPEC-022 FR-US2-009: la seccion es opcional."""
    triage = _cfg({}).triage
    assert triage.stopwords == frozenset()
    assert triage.min_word_len == DEFAULT_TRIAGE_MIN_WORD_LEN
    assert triage.min_matches == DEFAULT_TRIAGE_MIN_MATCHES


def test_triage_declarado_pero_vacio_cae_a_los_defaults():
    """SPEC-022 FR-US2-009: invariante de SPEC-021, `triage:` sin claves es None."""
    triage = _cfg({"specs": {"triage": None}}).triage
    assert triage.min_matches == DEFAULT_TRIAGE_MIN_MATCHES
    assert triage.stopwords == frozenset()


def test_triage_con_umbral_malformado_cae_al_default():
    """Un typo en un umbral no puede volver ilegible el proyecto."""
    triage = _cfg(
        {"specs": {"triage": {"min_matches": "dos", "min_word_len": 0}}}
    ).triage
    assert triage.min_matches == DEFAULT_TRIAGE_MIN_MATCHES
    assert triage.min_word_len == DEFAULT_TRIAGE_MIN_WORD_LEN


def test_triage_lee_las_stopwords_declaradas():
    triage = _cfg({"specs": {"triage": {"stopwords": ["Spec", "SDD"]}}}).triage
    assert triage.stopwords == frozenset({"spec", "sdd"})


def test_el_kit_siembra_sus_propias_stopwords_de_dominio():
    """SPEC-022 FR-US2-009: sin esto el triage marcaria candidata a casi toda spec.

    El default del loader es neutro a proposito (Principio I: el vocabulario del
    dominio va al config, no a `core/`); quien lo puebla es cada proyecto, y el
    kit no es la excepcion.
    """
    import yaml

    raw = yaml.safe_load(
        (Path(__file__).resolve().parents[2] / ".sdd" / "config.yaml").read_text(
            encoding="utf-8"
        )
    )
    stopwords = SddConfig(repo_root=Path("."), raw=raw).triage.stopwords
    assert {"spec", "specs", "sdd"} <= stopwords


def test_layers_tolera_listas_nulas():
    cfg = _cfg({"layers": {"domain": None, "app": ["domain"]}})
    assert cfg.layers == {"domain": [], "app": ["domain"]}


def test_defaults_source_root_y_tests_unit_son_las_constantes_compartidas():
    """SPEC-005 FR-005: un único literal, reusado por sdd_gate y el adaptador."""
    import adapter
    import sdd_gate

    assert sdd_gate.DEFAULT_SOURCE_ROOT is DEFAULT_SOURCE_ROOT
    assert adapter.DEFAULT_TESTS_UNIT is DEFAULT_TESTS_UNIT
    assert DEFAULT_SOURCE_ROOT == "src"
    assert DEFAULT_TESTS_UNIT == "tests/unit"
