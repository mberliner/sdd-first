"""Tests de bootstrap_hooks (SPEC-004 FR-001)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import bootstrap_hooks
from sdd_config import EXIT_OMITIDO


def _make_repo(tmp_path: Path) -> Path:
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    return tmp_path


def test_sin_git_se_omite(tmp_path, monkeypatch, capsys):
    """Sin repo git la capa git no queda cableada: omitido, no OK (SPEC-003 FR-009)."""
    repo = _make_repo(tmp_path)
    monkeypatch.setattr(bootstrap_hooks, "find_repo_root", lambda: repo)
    assert bootstrap_hooks.main() == EXIT_OMITIDO
    assert "omitido" in capsys.readouterr().out


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


# K-3: faltaba `_hooks_dir` (la resolucion real via git) y la rama que instala.


def test_hooks_dir_resuelve_ruta_relativa_contra_el_repo(tmp_path, monkeypatch):
    """git devuelve `.git/hooks` relativo; el helper lo ancla en el repo."""

    class _Resultado:
        returncode = 0
        stdout = ".git/hooks\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado())
    assert bootstrap_hooks._hooks_dir(tmp_path) == tmp_path / ".git" / "hooks"


def test_hooks_dir_respeta_una_ruta_absoluta(tmp_path, monkeypatch):
    """Con worktrees o core.hooksPath, git responde absoluto."""
    absoluta = tmp_path / "otro" / "hooks"

    class _Resultado:
        returncode = 0
        stdout = f"{absoluta}\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado())
    assert bootstrap_hooks._hooks_dir(tmp_path) == absoluta


def test_hooks_dir_devuelve_none_si_git_falla(tmp_path, monkeypatch):
    class _Resultado:
        returncode = 128
        stdout = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado())
    assert bootstrap_hooks._hooks_dir(tmp_path) is None


def test_hooks_faltantes_se_instalan(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path)
    (repo / ".git").mkdir()
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir()
    monkeypatch.setattr(bootstrap_hooks, "find_repo_root", lambda: repo)
    monkeypatch.setattr(bootstrap_hooks, "_hooks_dir", lambda _root: hooks_dir)

    comandos = []

    class _Resultado:
        returncode = 0

    monkeypatch.setattr(
        subprocess, "run", lambda cmd, **k: comandos.append(cmd) or _Resultado()
    )

    assert bootstrap_hooks.main() == 0
    assert comandos[0][-4:] == [
        "--hook-type",
        "pre-commit",
        "--hook-type",
        "post-commit",
    ]
    assert "faltan pre-commit, post-commit" in capsys.readouterr().out


def test_sin_el_paquete_pre_commit_falla_con_instruccion(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path)
    (repo / ".git").mkdir()
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir()
    monkeypatch.setattr(bootstrap_hooks, "find_repo_root", lambda: repo)
    monkeypatch.setattr(bootstrap_hooks, "_hooks_dir", lambda _root: hooks_dir)

    import builtins

    real_import = builtins.__import__

    def _sin_pre_commit(name, *args, **kwargs):
        if name == "pre_commit":
            raise ImportError("no module named pre_commit")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _sin_pre_commit)

    assert bootstrap_hooks.main() == 1
    assert "pip install pre-commit" in capsys.readouterr().err
