"""Qué skills SDD llegan al proyecto derivado, y cuál se queda del lado del kit.

SPEC-025 FR-US4-003: `sdd-update` necesita el clon del kit al lado (no solo
`tools/sdd/`), así que su skill y su playbook viven en el kit y no se
instalan en el derivado -- instalarla ahí prometería un comando que no puede
correr.
"""

from __future__ import annotations

from pathlib import Path

import sdd_init

KIT_ROOT = Path(__file__).resolve().parents[2]


def test_sdd_update_no_esta_en_project_skills():
    assert "sdd-update" not in sdd_init.PROJECT_SKILLS


def test_sdd_update_no_se_instala_en_el_derivado(tmp_path):
    sdd_init.main([str(tmp_path), "--language=python"])
    assert not (tmp_path / ".agents" / "skills" / "sdd-update").exists()
    assert not (tmp_path / ".claude" / "skills" / "sdd-update").exists()


def test_las_skills_de_proyecto_si_se_instalan(tmp_path):
    sdd_init.main([str(tmp_path), "--language=python"])
    for skill in sdd_init.PROJECT_SKILLS:
        assert (tmp_path / ".agents" / "skills" / skill / "SKILL.md").exists()


def test_sdd_update_vive_en_el_kit():
    assert (KIT_ROOT / ".agents" / "skills" / "sdd-update" / "SKILL.md").exists()
    assert (KIT_ROOT / "docs" / "playbooks" / "sdd-update.md").exists()
