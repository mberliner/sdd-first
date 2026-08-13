"""Un paso omitido no se cuenta como un paso OK (SPEC-003 FR-009).

`_skip` del adaptador devolvia 0 para que una instalacion fresca no arrancara en
ROJO. El efecto colateral: `VERDE 8/8` en un proyecto donde 4 pasos no habian
mirado nada. El estado OMITIDO separa "no se pudo verificar" de "verifique y
paso", sin volver a poner en ROJO lo que no corresponde.
"""

from __future__ import annotations

import pipeline
import pytest
from sdd_config import EXIT_OMITIDO


@pytest.fixture
def proyecto(tmp_path):
    (tmp_path / ".sdd").mkdir()
    (tmp_path / "CONSTITUTION.md").write_text("# c\n", encoding="utf-8")
    return tmp_path


def _correr(monkeypatch, proyecto, steps, resultados):
    """Corre el pipeline con `steps` y un resultado fijo por paso."""
    (proyecto / ".sdd" / "config.yaml").write_text(
        "project:\n  language: python\npipeline:\n  steps:\n"
        + "".join(f"    - {s}\n" for s in steps),
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline, "find_repo_root", lambda: proyecto)
    monkeypatch.setattr(
        pipeline,
        "_run_process_step",
        lambda step, root, extra_env=None: resultados[step],
    )
    monkeypatch.setattr(
        pipeline,
        "_run_code_step",
        lambda step, lang, root, extra_env=None: resultados[step],
    )
    return pipeline.main([])


def test_omitido_no_suma_al_total_ni_a_los_ok(monkeypatch, proyecto, capsys):
    codigo = _correr(
        monkeypatch,
        proyecto,
        ["constitution", "naming", "tests"],
        {"constitution": 0, "naming": EXIT_OMITIDO, "tests": EXIT_OMITIDO},
    )
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "[OMITIDO] naming" in salida
    assert "[OMITIDO] tests" in salida
    # Un solo paso verifico algo: el total lo refleja en vez de decir 3/3.
    assert "VERDE — 1/1 pasos OK" in salida


def test_el_resumen_nombra_los_pasos_omitidos(monkeypatch, proyecto, capsys):
    _correr(
        monkeypatch,
        proyecto,
        ["constitution", "naming"],
        {"constitution": 0, "naming": EXIT_OMITIDO},
    )
    salida = capsys.readouterr().out
    assert "Omitidos (1, no verificados): naming" in salida


def test_los_omitidos_se_ven_tambien_en_rojo(monkeypatch, proyecto, capsys):
    codigo = _correr(
        monkeypatch,
        proyecto,
        ["constitution", "naming", "tests"],
        {"constitution": 0, "naming": 1, "tests": EXIT_OMITIDO},
    )
    salida = capsys.readouterr().out
    assert codigo == 1
    assert "ROJO — 1/2 OK, 1 fallo(s)" in salida
    assert "Omitidos (1, no verificados): tests" in salida


def test_todo_omitido_no_es_verde_enganoso(monkeypatch, proyecto, capsys):
    """Cero pasos verificados: sale 0/0, no VERDE 2/2."""
    codigo = _correr(
        monkeypatch,
        proyecto,
        ["naming", "tests"],
        {"naming": EXIT_OMITIDO, "tests": EXIT_OMITIDO},
    )
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "VERDE — 0/0 pasos OK" in salida
    assert "Omitidos (2, no verificados): naming, tests" in salida


def test_fallo_sigue_siendo_fallo(monkeypatch, proyecto, capsys):
    codigo = _correr(monkeypatch, proyecto, ["constitution"], {"constitution": 1})
    salida = capsys.readouterr().out
    assert codigo == 1
    assert "[FALLO] constitution" in salida
    assert "Omitidos" not in salida
