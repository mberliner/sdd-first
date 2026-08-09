"""Consulta `coverage-baseline` del adaptador Python (SPEC-009 FR-US2-001/002).

La consulta produce un dato, no valida: por eso vive en QUERIES y no en STEPS.
Ese limite es lo que estos tests fijan --si alguien la mueve a STEPS, el pipeline
la tomaria por un paso de codigo y `pipeline.CODE_STEPS` divergiria en silencio,
que es el defecto C-8 de docs/IDEAS.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import adapter
import pipeline
from sdd_config import COVERAGE_BASELINE_PREFIX, EXIT_OMITIDO

CONTRATO = Path(__file__).resolve().parents[2] / "adapters" / "CONTRACT.md"


class _Cfg:
    def __init__(self, source_roots: list[str], dirs: dict[str, str]) -> None:
        self.source_roots = source_roots
        self.dirs = dirs


def test_coverage_baseline_es_consulta_y_no_paso():
    assert "coverage-baseline" in adapter.QUERIES
    assert "coverage-baseline" not in adapter.STEPS
    assert "coverage-baseline" not in pipeline.CODE_STEPS
    assert "coverage-baseline" not in pipeline.PROCESS_STEPS


def test_el_contrato_documenta_la_consulta():
    # FR-US2-002: un adaptador node/go tiene que poder implementarla sin leer
    # el codigo del adaptador python.
    texto = CONTRATO.read_text(encoding="utf-8")
    assert "coverage-baseline" in texto
    assert COVERAGE_BASELINE_PREFIX in texto


def test_se_omite_sin_codigo(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda mod: True)
    cfg = _Cfg(["src"], {"tests_unit": "tests/unit"})
    assert adapter.query_coverage_baseline(tmp_path, cfg) == EXIT_OMITIDO


def test_se_omite_sin_tests(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda mod: True)
    (tmp_path / "src").mkdir()
    cfg = _Cfg(["src"], {"tests_unit": "tests/unit"})
    assert adapter.query_coverage_baseline(tmp_path, cfg) == EXIT_OMITIDO


def test_se_omite_sin_pytest_cov(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda mod: mod != "pytest_cov")
    assert adapter.query_coverage_baseline(tmp_path, _Cfg([], {})) == EXIT_OMITIDO


def test_se_omite_si_pytest_no_deja_reporte(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(adapter, "_module_available", lambda mod: True)
    monkeypatch.setattr(adapter, "_run", lambda cmd, cwd: 0)  # no escribe nada
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    cfg = _Cfg(["src"], {"tests_unit": "tests/unit"})
    assert adapter.query_coverage_baseline(tmp_path, cfg) == EXIT_OMITIDO
    assert "reporte" in capsys.readouterr().out


def test_imprime_la_linea_de_contrato(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(adapter, "_module_available", lambda mod: True)

    def falso_pytest(cmd: list[str], cwd: Path) -> int:
        destino = next(
            c.split(":", 1)[1] for c in cmd if c.startswith("--cov-report=json:")
        )
        Path(destino).write_text(
            json.dumps({"totals": {"percent_covered": 73.456}}), encoding="utf-8"
        )
        return 0

    monkeypatch.setattr(adapter, "_run", falso_pytest)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    cfg = _Cfg(["src"], {"tests_unit": "tests/unit"})

    assert adapter.query_coverage_baseline(tmp_path, cfg) == 0
    salida = capsys.readouterr().out
    assert f"{COVERAGE_BASELINE_PREFIX} 73.46 src" in salida


def test_suite_roja_no_invalida_la_medicion(tmp_path, monkeypatch, capsys):
    # Medir no es verificar: un proyecto con la suite en rojo igual tiene un
    # piso de cobertura, y negarselo lo dejaria sin poder declarar el primero.
    monkeypatch.setattr(adapter, "_module_available", lambda mod: True)

    def pytest_rojo(cmd: list[str], cwd: Path) -> int:
        destino = next(
            c.split(":", 1)[1] for c in cmd if c.startswith("--cov-report=json:")
        )
        Path(destino).write_text(
            json.dumps({"totals": {"percent_covered": 12.0}}), encoding="utf-8"
        )
        return 1

    monkeypatch.setattr(adapter, "_run", pytest_rojo)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    cfg = _Cfg(["src"], {"tests_unit": "tests/unit"})

    assert adapter.query_coverage_baseline(tmp_path, cfg) == 0
    assert f"{COVERAGE_BASELINE_PREFIX} 12.00 src" in capsys.readouterr().out


def test_reporte_ilegible_se_omite(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda mod: True)

    def basura(cmd: list[str], cwd: Path) -> int:
        destino = next(
            c.split(":", 1)[1] for c in cmd if c.startswith("--cov-report=json:")
        )
        Path(destino).write_text("{}", encoding="utf-8")
        return 0

    monkeypatch.setattr(adapter, "_run", basura)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    cfg = _Cfg(["src"], {"tests_unit": "tests/unit"})
    assert adapter.query_coverage_baseline(tmp_path, cfg) == EXIT_OMITIDO


def test_main_acepta_la_consulta_y_rechaza_lo_desconocido(capsys):
    assert adapter.main(["no-existe"]) == 2
    assert "coverage-baseline" in capsys.readouterr().err


def test_main_despacha_consultas(monkeypatch, tmp_path):
    llamadas: list[str] = []

    def espia(root, cfg) -> int:
        llamadas.append("ok")
        return 0

    monkeypatch.setitem(adapter.QUERIES, "coverage-baseline", espia)
    monkeypatch.setattr(adapter, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(adapter, "load", lambda root: _Cfg([], {}))
    assert adapter.main(["coverage-baseline"]) == 0
    assert llamadas == ["ok"]
