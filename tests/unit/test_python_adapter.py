"""Tests del dispatcher del adaptador python (SPEC-003 FR-001/FR-002/FR-004)."""

from pathlib import Path

import adapter
import pytest
from sdd_config import SddConfig


def _cfg(tmp_path: Path, raw: dict) -> SddConfig:
    return SddConfig(repo_root=tmp_path, raw=raw)


@pytest.fixture(autouse=True)
def sin_subprocesos(monkeypatch):
    """Ningún test de esta suite debe llegar a invocar una tool real."""

    def _explota(cmd, cwd):
        raise AssertionError(f"no debía ejecutarse: {cmd}")

    monkeypatch.setattr(adapter, "_run", _explota)


def test_naming_sin_targets_se_omite_con_exit_0(tmp_path):
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain", "tests_unit": "tests/unit"}})
    assert adapter.step_naming(tmp_path, cfg) == 0


def test_lint_sin_tool_se_omite_con_exit_0(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: False)
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain"}})
    assert adapter.step_lint(tmp_path, cfg) == 0


def test_tests_sin_carpeta_se_omite_con_exit_0(tmp_path):
    cfg = _cfg(tmp_path, {"dirs": {"tests_unit": "tests/unit"}})
    assert adapter.step_tests(tmp_path, cfg) == 0


def test_layers_sin_lint_imports_se_omite_con_exit_0(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter.shutil, "which", lambda name: None)
    cfg = _cfg(tmp_path, {})
    assert adapter.step_layers(tmp_path, cfg) == 0


def test_con_targets_y_tool_si_se_ejecuta(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(adapter, "_run", lambda cmd, cwd: llamadas.append(cmd) or 0)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain"}})
    assert adapter.step_lint(tmp_path, cfg) == 0
    assert llamadas and "ruff" in llamadas[0]
