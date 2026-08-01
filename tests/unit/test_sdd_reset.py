"""Tests de sdd_reset (SPEC-004 FR-002)."""

from __future__ import annotations

from pathlib import Path

import sdd_reset


def _make_repo(tmp_path: Path) -> Path:
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    return tmp_path


def test_limpia_specs_declaradas_deja_solo_comentarios(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    current = repo / ".sdd" / "current-spec"
    current.write_text(
        "# comentario de header\nSPEC-001-demo\nSPEC-002-otra\n", encoding="utf-8"
    )
    monkeypatch.setattr(sdd_reset, "find_repo_root", lambda: repo)

    assert sdd_reset.main() == 0

    text = current.read_text(encoding="utf-8")
    assert "SPEC-001-demo" not in text
    assert "SPEC-002-otra" not in text
    assert "# comentario de header" in text


def test_sin_archivo_current_spec_no_falla(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    monkeypatch.setattr(sdd_reset, "find_repo_root", lambda: repo)
    assert sdd_reset.main() == 0
