"""Docs y SSOTs de la ruta de actualización nombrados donde corresponde.

SPEC-025 FR-US4-004.
"""

from __future__ import annotations

from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[2]


def test_readme_nombra_sdd_update_donde_dice_desechable():
    texto = (KIT_ROOT / "README.md").read_text(encoding="utf-8")
    seccion = texto.split("## El kit es desechable", 1)[1]
    assert "sdd_update.py" in seccion


def test_sdd_operacion_explica_el_mecanismo():
    texto = (KIT_ROOT / "templates" / "docs" / "SDD-OPERACION.md").read_text(
        encoding="utf-8"
    )
    assert "sdd-update" in texto
    assert "clon del kit" in texto
    assert ".sdd/kit.lock" in texto


def test_00_index_del_kit_lista_los_tres_ssot_nuevos():
    texto = (KIT_ROOT / "00-INDEX.md").read_text(encoding="utf-8")
    assert "CHANGELOG.md" in texto
    assert "sdd_catalog.py" in texto
    assert "kit.lock" in texto


def test_00_index_de_la_plantilla_lista_los_ssot_del_derivado():
    texto = (KIT_ROOT / "templates" / "00-INDEX.md").read_text(encoding="utf-8")
    assert "sdd_catalog.py" in texto
    assert "kit.lock" in texto
