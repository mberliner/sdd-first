"""Tests del loader de configuración (SPEC-002 FR-003, SPEC-005 FR-005)."""

from pathlib import Path

from sdd_config import DEFAULT_SOURCE_ROOT, DEFAULT_TESTS_UNIT, SddConfig


def _cfg(raw: dict) -> SddConfig:
    return SddConfig(repo_root=Path("."), raw=raw)


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


def test_principles_ignora_entradas_no_dict():
    cfg = _cfg({"principles": [{"id": "I", "title": "T"}, "basura", None]})
    assert len(cfg.principles) == 1
    assert cfg.principles[0].id == "I"


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
