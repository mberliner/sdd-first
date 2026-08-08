"""Tests del dispatcher del adaptador python (SPEC-003 FR-001/FR-002/FR-004)."""

from pathlib import Path

import adapter
import pytest
from sdd_config import EXIT_OMITIDO, SddConfig


def _cfg(tmp_path: Path, raw: dict) -> SddConfig:
    return SddConfig(repo_root=tmp_path, raw=raw)


@pytest.fixture(autouse=True)
def sin_subprocesos(monkeypatch):
    """Ningún test de esta suite debe llegar a invocar una tool real."""

    def _explota(cmd, cwd):
        raise AssertionError(f"no debía ejecutarse: {cmd}")

    monkeypatch.setattr(adapter, "_run", _explota)


def test_naming_sin_targets_se_omite_con_exit_omitido(tmp_path):
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain", "tests_unit": "tests/unit"}})
    assert adapter.step_naming(tmp_path, cfg) == EXIT_OMITIDO


def test_lint_sin_tool_se_omite_con_exit_omitido(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: False)
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain"}})
    assert adapter.step_lint(tmp_path, cfg) == EXIT_OMITIDO


def test_tests_sin_carpeta_se_omite_con_exit_omitido(tmp_path):
    cfg = _cfg(tmp_path, {"dirs": {"tests_unit": "tests/unit"}})
    assert adapter.step_tests(tmp_path, cfg) == EXIT_OMITIDO


def test_layers_sin_lint_imports_se_omite_con_exit_omitido(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter.shutil, "which", lambda name: None)
    cfg = _cfg(tmp_path, {})
    assert adapter.step_layers(tmp_path, cfg) == EXIT_OMITIDO


def test_layers_sin_el_paquete_raiz_en_disco_se_omite(tmp_path, monkeypatch):
    """SPEC-003 FR-011: era el unico paso de codigo sin guardia de targets.

    Con la tool instalada y `layers` sembrado —el estado de toda instalacion
    fresca— `lint-imports` abortaba con "Could not find package 'src'" y la
    instalacion salia ROJO en su primer pipeline.
    """
    monkeypatch.setattr(adapter.shutil, "which", lambda name: "/usr/bin/lint-imports")
    cfg = _cfg(tmp_path, {"layers": {"domain": [], "application": ["domain"]}})
    assert adapter.step_layers(tmp_path, cfg) == EXIT_OMITIDO


def test_layers_sin_capas_declaradas_se_omite(tmp_path, monkeypatch):
    """Sin `layers` no hay contrato que verificar: omitir, no correr en vacio."""
    monkeypatch.setattr(adapter.shutil, "which", lambda name: "/usr/bin/lint-imports")
    (tmp_path / "src").mkdir()
    assert adapter.step_layers(tmp_path, _cfg(tmp_path, {})) == EXIT_OMITIDO


def test_layers_con_capas_y_paquete_raiz_si_se_ejecuta(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(adapter, "_run", lambda cmd, cwd: llamadas.append(cmd) or 0)
    monkeypatch.setattr(adapter.shutil, "which", lambda name: "/usr/bin/lint-imports")
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"layers": {"domain": [], "application": ["domain"]}})
    assert adapter.step_layers(tmp_path, cfg) == 0
    assert llamadas[-1] == ["lint-imports"]


def test_con_targets_y_tool_si_se_ejecuta(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(adapter, "_run", lambda cmd, cwd: llamadas.append(cmd) or 0)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain"}})
    assert adapter.step_lint(tmp_path, cfg) == 0
    assert llamadas and "ruff" in llamadas[0]
