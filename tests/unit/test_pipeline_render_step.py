"""Test del paso 'render' del pipeline (SPEC-005 FR-003)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pipeline


def test_render_es_paso_de_proceso():
    assert "render" in pipeline.PROCESS_STEPS


def test_render_invoca_render_py_con_check(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        subprocess, "call", lambda cmd, cwd=None: calls.append(cmd) or 0
    )

    code = pipeline._run_process_step("render", tmp_path)

    assert code == 0
    assert len(calls) == 1
    cmd = calls[0]
    assert cmd[0] == pipeline.sys.executable
    assert Path(cmd[1]).name == "render.py"
    assert "--check" in cmd
