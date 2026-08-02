"""Tests del sync docs/templates (SPEC-005 FR-001, FR-002)."""

from __future__ import annotations

from pathlib import Path

import render


def _make_repo(tmp_path: Path) -> Path:
    (tmp_path / "templates" / "docs" / "playbooks").mkdir(parents=True)
    (tmp_path / "templates" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "playbooks").mkdir(parents=True)
    (tmp_path / "specs").mkdir(parents=True)
    (tmp_path / "templates" / "docs" / "SDD-ENFORCEMENT.md").write_text(
        "contenido autoritativo\n", encoding="utf-8"
    )
    (tmp_path / "templates" / "docs" / "playbooks" / "analyze.md").write_text(
        "analyze\n", encoding="utf-8"
    )
    (tmp_path / "templates" / "docs" / "playbooks" / "clarify.md").write_text(
        "clarify\n", encoding="utf-8"
    )
    for name in ("sdd-spec", "sdd-doctor", "sdd-configure"):
        (tmp_path / "templates" / "docs" / "playbooks" / f"{name}.md").write_text(
            f"{name}\n", encoding="utf-8"
        )
    (tmp_path / "templates" / "specs" / "SPEC-TEMPLATE.md").write_text(
        "template\n", encoding="utf-8"
    )
    return tmp_path


def test_generated_targets_incluye_sync_solo_si_hay_templates(tmp_path):
    repo_con_templates = _make_repo(tmp_path)
    targets = render._generated_targets(repo_con_templates)
    assert "docs/SDD-ENFORCEMENT.md" in targets
    assert "specs/SPEC-TEMPLATE.md" in targets


def test_sync_incluye_los_3_playbooks_operativos():
    # SPEC-007 FR-004: sdd-spec/sdd-doctor/sdd-configure se sincronizan desde
    # templates/ igual que analyze/clarify (patron SPEC-005), no se duplican
    # a mano en docs/playbooks/ del propio kit.
    for name in ("sdd-spec", "sdd-doctor", "sdd-configure"):
        assert f"docs/playbooks/{name}.md" in render._SYNCED_FROM_TEMPLATES


def test_generated_targets_es_noop_sin_carpeta_templates(tmp_path):
    # Proyecto instalado con sdd-init: no tiene templates/ propia.
    targets = render._generated_targets(tmp_path)
    assert "docs/SDD-ENFORCEMENT.md" not in targets
    assert set(targets) == set(render._GENERATED)


def test_sync_copia_byte_a_byte_desde_templates(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    monkeypatch.chdir(repo)
    render.load.cache_clear()

    render.main([])

    assert (repo / "docs" / "SDD-ENFORCEMENT.md").read_text(
        encoding="utf-8"
    ) == "contenido autoritativo\n"
    assert (repo / "specs" / "SPEC-TEMPLATE.md").read_text(
        encoding="utf-8"
    ) == "template\n"


def test_check_detecta_drift_en_archivo_sincronizado(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path)
    monkeypatch.chdir(repo)
    render.load.cache_clear()
    render.main([])  # sincroniza primero

    (repo / "docs" / "SDD-ENFORCEMENT.md").write_text(
        "editado a mano, sin tocar templates/\n", encoding="utf-8"
    )

    code = render.main(["--check"])

    assert code == 1
    out = capsys.readouterr().out
    assert "docs/SDD-ENFORCEMENT.md" in out
