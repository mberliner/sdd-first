"""Tests de bootstrap_hooks (SPEC-004 FR-001)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import bootstrap_hooks


def _make_repo(tmp_path: Path) -> Path:
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    return tmp_path


def test_sin_git_es_no_op(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path)
    monkeypatch.setattr(bootstrap_hooks, "find_repo_root", lambda: repo)
    assert bootstrap_hooks.main() == 0
    assert "no-op" in capsys.readouterr().out


def test_hooks_ya_instalados_no_toca_nada(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path)
    (repo / ".git").mkdir()
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")
    (hooks_dir / "post-commit").write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setattr(bootstrap_hooks, "find_repo_root", lambda: repo)
    monkeypatch.setattr(bootstrap_hooks, "_hooks_dir", lambda _root: hooks_dir)

    called = []
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: called.append((a, k)) or None
    )

    assert bootstrap_hooks.main() == 0
    assert not called
    assert "sin cambios" in capsys.readouterr().out


def test_git_sin_hooks_dir_resoluble_falla(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    (repo / ".git").mkdir()
    monkeypatch.setattr(bootstrap_hooks, "find_repo_root", lambda: repo)
    monkeypatch.setattr(bootstrap_hooks, "_hooks_dir", lambda _root: None)
    assert bootstrap_hooks.main() == 1
