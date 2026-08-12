"""`core/pipeline.py` crea y limpia el cache compartido tests/coverage
(SPEC-009 FR-US3-002).

El cache es un archivo temporal por corrida cuya ruta se expone en
`PIPELINE_COVERAGE_CACHE_ENV` a los pasos de código; el paso `tests` lo llena
y el paso `coverage` lo lee (adapters/python/adapter.py), sin correr pytest
dos veces. Este archivo cubre solo la parte que le toca a `core/pipeline.py`:
que la variable exista con una ruta real durante la corrida y que no quede
nada en disco al terminar.
"""

from __future__ import annotations

from pathlib import Path

import pipeline
import pytest
from sdd_config import PIPELINE_COVERAGE_CACHE_ENV


@pytest.fixture
def proyecto(tmp_path):
    (tmp_path / ".sdd").mkdir()
    (tmp_path / "CONSTITUTION.md").write_text("# c\n", encoding="utf-8")
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  language: python\npipeline:\n  steps:\n    - tests\n",
        encoding="utf-8",
    )
    return tmp_path


def test_los_pasos_de_codigo_reciben_la_ruta_del_cache(monkeypatch, proyecto):
    vistos: list[dict[str, str] | None] = []

    monkeypatch.setattr(pipeline, "find_repo_root", lambda: proyecto)
    monkeypatch.setattr(
        pipeline,
        "_run_code_step",
        lambda step, lang, root, extra_env=None: vistos.append(extra_env) or 0,
    )

    pipeline.main([])

    assert len(vistos) == 1
    extra_env = vistos[0]
    assert extra_env is not None
    ruta = extra_env[PIPELINE_COVERAGE_CACHE_ENV]
    assert ruta.endswith("coverage.json")


def test_el_cache_se_borra_al_terminar_la_corrida(monkeypatch, proyecto):
    rutas: list[Path] = []

    def _fake(step, lang, root, extra_env=None):
        # simula lo que hace `tests`: escribe algo en la ruta que recibio.
        ruta = Path(extra_env[PIPELINE_COVERAGE_CACHE_ENV])
        ruta.write_text("{}", encoding="utf-8")
        rutas.append(ruta)
        return 0

    monkeypatch.setattr(pipeline, "find_repo_root", lambda: proyecto)
    monkeypatch.setattr(pipeline, "_run_code_step", _fake)

    pipeline.main([])

    assert rutas and not rutas[0].exists()
    assert not rutas[0].parent.exists()


def test_el_cache_se_borra_incluso_si_un_paso_falla(monkeypatch, proyecto):
    rutas: list[Path] = []

    def _fake(step, lang, root, extra_env=None):
        ruta = Path(extra_env[PIPELINE_COVERAGE_CACHE_ENV])
        ruta.write_text("{}", encoding="utf-8")
        rutas.append(ruta)
        return 1

    monkeypatch.setattr(pipeline, "find_repo_root", lambda: proyecto)
    monkeypatch.setattr(pipeline, "_run_code_step", _fake)

    assert pipeline.main([]) == 1
    assert rutas and not rutas[0].parent.exists()
