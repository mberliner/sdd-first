"""El config de ejemplo es la semilla de todo proyecto nuevo.

`sdd_init._write_config` lo copia a `.sdd/config.yaml` del destino, así que un
error acá se propaga a cada instalación. Cubre SPEC-010 FR-004 (catálogo de
principios opcionales) y SPEC-009 FR-001 (umbrales sembrados comentados).
"""

from __future__ import annotations

from pathlib import Path

import yaml

KIT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = KIT_ROOT / "examples" / "config" / "config.yaml"


def _cargado() -> dict:
    return yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))


def test_el_ejemplo_es_yaml_valido():
    assert isinstance(_cargado(), dict)


def test_incluye_el_principio_opcional_de_ssot_unico():
    # FR-004: el kit predicaba "no duplicar SSOT" en su AGENTS.md pero no lo
    # ofrecía como principio elegible.
    titulos = [p["title"] for p in _cargado()["principles"]]
    assert "SSOT unico por tema" in titulos


def test_los_principios_opcionales_van_despues_del_nucleo_minimo():
    titulos = [p["title"] for p in _cargado()["principles"]]
    nucleo = [
        "Nomenclatura agnostica a tecnologia",
        "Capas limpias con dependencia unidireccional",
        "Trazabilidad spec-codigo",
        "Gate spec-first",
    ]
    assert titulos[: len(nucleo)] == nucleo


def test_todo_principio_declara_invariante_enforcement_y_detalle():
    for p in _cargado()["principles"]:
        assert p.get("invariant"), p
        assert p.get("enforcement"), p
        assert p.get("detail"), p


def test_declara_la_seccion_constitution_con_semver():
    # SPEC-010 FR-003: el procedimiento de enmienda necesita dónde bumpear.
    constitution = _cargado()["constitution"]
    assert constitution["version"].count(".") == 2


def test_el_paso_coverage_esta_declarado():
    assert "coverage" in _cargado()["pipeline"]["steps"]


def test_los_umbrales_de_cobertura_vienen_comentados():
    # SPEC-009 FR-002: el umbral es opcional; sembrarlo activo haría que una
    # instalación fresca midiera cobertura de un proyecto todavía vacío.
    assert _cargado()["pipeline"].get("coverage") is None
    assert "# coverage:" in EXAMPLE.read_text(encoding="utf-8")
