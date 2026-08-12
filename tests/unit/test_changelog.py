"""`CHANGELOG.md` trae una entrada para la `KIT_VERSION` vigente.

SPEC-025 FR-US4-001.
"""

from __future__ import annotations

from pathlib import Path

import sdd_config
import sdd_update

KIT_ROOT = Path(__file__).resolve().parents[2]


def test_changelog_existe():
    assert (KIT_ROOT / "CHANGELOG.md").exists()


def test_kit_version_vigente_tiene_entrada():
    entradas = sdd_update.leer_changelog(KIT_ROOT)
    assert sdd_config.KIT_VERSION in entradas
    assert entradas[sdd_config.KIT_VERSION].strip()
