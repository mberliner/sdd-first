"""KIT_VERSION vendorizado y `project.kit_version` fuera del catálogo.

SPEC-025 FR-US1-001, FR-US1-004.
"""

from __future__ import annotations

from pathlib import Path

import sdd_config

KIT_ROOT = Path(__file__).resolve().parents[2]


def test_kit_version_es_una_constante_semver_en_sdd_config():
    """FR-US1-001: vive en `core/sdd_config.py`, junto a las demas constantes
    del nucleo, y nace en 0.1.0."""
    assert sdd_config.KIT_VERSION == "0.1.0"
    partes = sdd_config.KIT_VERSION.split(".")
    assert len(partes) == 3
    assert all(p.isdigit() for p in partes)


def test_kit_version_es_independiente_de_constitution_version():
    """FR-US1-001: dos lineas de versionado distintas, no atadas."""
    cfg = sdd_config.SddConfig(
        repo_root=KIT_ROOT, raw={"constitution": {"version": "9.9.9"}}
    )
    assert cfg.constitution_version == "9.9.9"
    assert sdd_config.KIT_VERSION != cfg.constitution_version


def test_project_kit_version_no_esta_en_el_config_de_ejemplo():
    """FR-US1-004: era una constante copiada del ejemplo, nunca comparada
    contra nada; se elimina del catalogo de claves."""
    texto = (KIT_ROOT / "examples" / "config" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "kit_version" not in texto


def test_project_kit_version_no_esta_en_el_config_del_propio_kit():
    """FR-US1-004: el kit dogfoodea su propio andamiaje (SPEC-002)."""
    texto = (KIT_ROOT / ".sdd" / "config.yaml").read_text(encoding="utf-8")
    assert "kit_version" not in texto
