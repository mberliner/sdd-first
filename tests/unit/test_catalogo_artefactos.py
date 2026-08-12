"""Catálogo de clases de propiedad: SSOT único para instalación y actualización.

SPEC-025 FR-US2-001, FR-US2-002.
"""

from __future__ import annotations

import sdd_catalog


def test_catalogo_plantillas_es_static_docs_mas_wiring():
    """FR-US2-001: no se duplica la lista, se reexporta."""
    assert sdd_catalog.catalogo_plantillas() == [
        *sdd_catalog.STATIC_DOCS,
        *sdd_catalog.WIRING,
    ]


def test_semillas_declaradas_por_fr_us2_002():
    assert sdd_catalog.SEMILLA_DESTINOS == {
        "specs/SPECS_REGISTRY.md",
        "historial/sdd.md",
        ".gitignore",
        ".sdd/current-spec",
        ".sdd/config.yaml",
    }


def test_clase_de_semillas():
    for destino in sdd_catalog.SEMILLA_DESTINOS:
        assert sdd_catalog.clase_de(destino) == sdd_catalog.Clase.SEMILLA


def test_config_reference_es_vendor_pese_a_vivir_fuera_de_tools_sdd():
    """FR-US2-002/ANA-035: la clase describe autoridad, no ubicacion."""
    assert (
        sdd_catalog.clase_de(".sdd/config.reference.yaml") == sdd_catalog.Clase.VENDOR
    )


def test_resto_del_catalogo_es_plantilla():
    for _src, dst in sdd_catalog.catalogo_plantillas():
        if dst in sdd_catalog.SEMILLA_DESTINOS:
            continue
        assert sdd_catalog.clase_de(dst) == sdd_catalog.Clase.PLANTILLA


def test_generado_no_se_enumera_en_el_catalogo():
    """FR-US2-001: CONSTITUTION.md/SPEC-000/ci.yml son SSOT de render.py."""
    destinos = {dst for _src, dst in sdd_catalog.catalogo_plantillas()}
    assert "CONSTITUTION.md" not in destinos
    assert "specs/SPEC-000-naming.md" not in destinos
    assert ".github/workflows/ci.yml" not in destinos


def test_decidir_plantilla_tabla_de_decision():
    """FR-US2-005/006/012: cubre exhaustivamente los casos declarados."""
    decidir = sdd_catalog.decidir_plantilla
    assert decidir(False, None, "hk", None) == "nuevo"
    assert decidir(False, None, "hk", "hl") == "eliminada"
    assert decidir(True, "hk", "hk", None) == "sin_cambios"
    assert decidir(True, "hk", "hk", "hl-distinto") == "sin_cambios"
    assert decidir(True, "hl", "hk-nuevo", "hl") == "actualizar"
    assert decidir(True, "editado", "hk", None) == "conflicto"
    assert decidir(True, "editado", "hk", "hl-distinto") == "conflicto"
