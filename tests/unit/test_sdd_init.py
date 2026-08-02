"""Tests de la instalacion completa de sdd_init (SPEC-007 FR-001..FR-003)."""

from __future__ import annotations

import sdd_init


def test_project_skills_incluye_las_5_skills_operativas():
    # sdd-init es bootstrap de una sola vez: no viaja al proyecto derivado.
    assert set(sdd_init.PROJECT_SKILLS) == {
        "analyze",
        "clarify",
        "sdd-spec",
        "sdd-doctor",
        "sdd-configure",
    }
    assert "sdd-init" not in sdd_init.PROJECT_SKILLS


def test_static_docs_incluye_readme_y_manual_de_operacion():
    destinos = {dst for _src, dst in sdd_init.STATIC_DOCS}
    assert "README.md" in destinos
    assert "docs/SDD-OPERACION.md" in destinos
    assert "docs/playbooks/sdd-spec.md" in destinos
    assert "docs/playbooks/sdd-doctor.md" in destinos
    assert "docs/playbooks/sdd-configure.md" in destinos


def test_main_instala_readme_manual_y_skills_completas(tmp_path):
    code = sdd_init.main([str(tmp_path), "--language=none"])
    assert code == 0

    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "docs" / "SDD-OPERACION.md").exists()

    for skill in ("analyze", "clarify", "sdd-spec", "sdd-doctor", "sdd-configure"):
        assert (tmp_path / ".agents" / "skills" / skill / "SKILL.md").exists()


def test_readme_no_menciona_el_protocolo_sdd_en_detalle(tmp_path):
    # El README es del producto derivado; SDD solo aparece como un link de
    # salida, no explicado ahi (esa explicacion vive en SDD-OPERACION.md).
    sdd_init.main([str(tmp_path), "--language=none"])
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "docs/SDD-OPERACION.md" in readme
    assert "gate spec-first" not in readme.lower()


def test_main_no_pisa_readme_existente_sin_force(tmp_path):
    (tmp_path / "README.md").write_text("contenido del usuario\n", encoding="utf-8")
    sdd_init.main([str(tmp_path), "--language=none"])
    assert (tmp_path / "README.md").read_text(
        encoding="utf-8"
    ) == "contenido del usuario\n"
