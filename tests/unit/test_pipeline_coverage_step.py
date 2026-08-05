"""El pipeline reconoce `coverage` como paso de código (SPEC-009 FR-003).

Un paso no reconocido por `pipeline.py` hace `continue` sin correr nada (ítem
C-1 de `docs/IDEAS.md`): declararlo en el config y que el pipeline lo ignore en
silencio sería peor que no tenerlo.
"""

from __future__ import annotations

import pipeline
from sdd_config import EXIT_OMITIDO


def test_coverage_es_paso_de_codigo():
    assert "coverage" in pipeline.CODE_STEPS
    assert "coverage" not in pipeline.PROCESS_STEPS


def test_coverage_se_delega_al_adaptador_del_lenguaje(tmp_path, monkeypatch):
    invocaciones = []

    def _fake_run(cmd, cwd):
        invocaciones.append(cmd)
        return 0

    monkeypatch.setattr(pipeline, "_run", _fake_run)

    assert pipeline._run_code_step("coverage", "python", tmp_path) == 0
    assert invocaciones and invocaciones[0][-1] == "coverage"
    assert "adapter.py" in invocaciones[0][-2]


def test_coverage_se_omite_con_language_none(tmp_path, monkeypatch):
    monkeypatch.setattr(
        pipeline, "_run", lambda cmd, cwd: pytest_fail("no debía ejecutarse")
    )
    assert pipeline._run_code_step("coverage", "none", tmp_path) == EXIT_OMITIDO


def pytest_fail(msg):  # pragma: no cover - helper de aserción
    raise AssertionError(msg)
