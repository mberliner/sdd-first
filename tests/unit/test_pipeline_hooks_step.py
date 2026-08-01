"""Test del paso 'hooks' del pipeline (SPEC-004 FR-003)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pipeline


def test_hooks_es_paso_de_proceso():
    assert "hooks" in pipeline.PROCESS_STEPS


def test_hooks_invoca_bootstrap_hooks_py(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        subprocess, "call", lambda cmd, cwd=None: calls.append(cmd) or 0
    )

    code = pipeline._run_process_step("hooks", tmp_path)

    assert code == 0
    assert len(calls) == 1
    cmd = calls[0]
    assert cmd[0] == pipeline.sys.executable
    assert Path(cmd[1]).name == "bootstrap_hooks.py"
