"""Un principio sin enforcement ejecutado no deja el resumen en VERDE a secas.

SPEC-020 FR-US2-001/FR-US2-004/FR-US2-007. US1 cerro el hueco de la
*declaracion* (un `step` ausente de `pipeline.steps` es error); esto cubre el de
la *ejecucion*: un paso declarado que se omite en runtime deja el principio sin
verificar y el pipeline decia VERDE igual.

El pipeline no recalcula el cruce -- eso lo decide `check_constitution`, unico
dueno del criterio (Principio IV). Aca se verifica el canal (que publique los
pasos ejecutados) y la traduccion del codigo a un estado visible.
"""

from __future__ import annotations

import pipeline
import pytest
from sdd_config import EXIT_OMITIDO, EXIT_RESERVAS, PIPELINE_STEPS_RUN_ENV


@pytest.fixture
def proyecto(tmp_path):
    (tmp_path / ".sdd").mkdir()
    (tmp_path / "CONSTITUTION.md").write_text("# c\n", encoding="utf-8")
    return tmp_path


def _correr(monkeypatch, proyecto, steps, resultados, visto=None):
    """Corre el pipeline con `steps` y un resultado fijo por paso.

    `visto` recibe, si se pasa, el valor de la variable de entorno que el
    pipeline publica en cada paso de proceso: es el canal de FR-US2-001.
    """
    (proyecto / ".sdd" / "config.yaml").write_text(
        "project:\n  language: python\npipeline:\n  steps:\n"
        + "".join(f"    - {s}\n" for s in steps),
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline, "find_repo_root", lambda: proyecto)

    def _proceso(step, root, extra_env=None):
        if visto is not None:
            visto[step] = (extra_env or {}).get(PIPELINE_STEPS_RUN_ENV)
        return resultados[step]

    monkeypatch.setattr(pipeline, "_run_process_step", _proceso)
    monkeypatch.setattr(
        pipeline,
        "_run_code_step",
        lambda step, lang, root, extra_env=None: resultados[step],
    )
    return pipeline.main([])


def test_el_paso_recibe_los_pasos_ya_ejecutados(monkeypatch, proyecto):
    """FR-US2-001: ni los omitidos ni los pendientes entran en la lista."""
    visto: dict[str, str | None] = {}
    _correr(
        monkeypatch,
        proyecto,
        ["traceability", "naming", "tests", "constitution"],
        {"traceability": 0, "naming": EXIT_OMITIDO, "tests": 0, "constitution": 0},
        visto=visto,
    )
    recibido = (visto["constitution"] or "").split(",")
    assert "traceability" in recibido
    assert "tests" in recibido
    # Omitido: corrio el paso pero no verifico nada, asi que no cuenta.
    assert "naming" not in recibido
    # Pendiente: `constitution` se ve a si mismo como no ejecutado todavia.
    assert "constitution" not in recibido


def test_un_paso_fallado_cuenta_como_ejecutado(monkeypatch, proyecto):
    """FR-US2-001: fallar es haber corrido; el enforcement hizo su trabajo."""
    visto: dict[str, str | None] = {}
    _correr(
        monkeypatch,
        proyecto,
        ["naming", "constitution"],
        {"naming": 1, "constitution": 0},
        visto=visto,
    )
    assert "naming" in (visto["constitution"] or "").split(",")


def test_reservas_condicionan_el_verde_sin_cambiar_el_exit_code(
    monkeypatch, proyecto, capsys
):
    """FR-US2-004: el verde deja de ser incondicional, el exit code sigue 0."""
    codigo = _correr(
        monkeypatch,
        proyecto,
        ["naming", "constitution"],
        {"naming": EXIT_OMITIDO, "constitution": EXIT_RESERVAS},
    )
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "VERDE con reservas" in salida
    assert "Con reservas (1): constitution" in salida


def test_sin_reservas_el_verde_es_el_de_siempre(monkeypatch, proyecto, capsys):
    codigo = _correr(
        monkeypatch,
        proyecto,
        ["naming", "constitution"],
        {"naming": 0, "constitution": 0},
    )
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "VERDE — 2/2 pasos OK" in salida
    assert "reservas" not in salida


def test_el_paso_con_reservas_cuenta_como_ok(monkeypatch, proyecto, capsys):
    """Verifico lo suyo: la reserva no lo saca del conteo, a diferencia de OMITIDO."""
    _correr(
        monkeypatch,
        proyecto,
        ["naming", "constitution"],
        {"naming": EXIT_OMITIDO, "constitution": EXIT_RESERVAS},
    )
    salida = capsys.readouterr().out
    assert "1/1 pasos OK" in salida


def test_un_paso_de_codigo_no_puede_hacer_reservas(monkeypatch, proyecto, capsys):
    """El contrato de adaptador declara tres estados (adapters/CONTRACT.md).

    Un adaptador que devuelva el codigo de reservas no amplia el contrato por la
    ventana: cuenta como falla, como cualquier otro exit desconocido.
    """
    codigo = _correr(
        monkeypatch,
        proyecto,
        ["naming", "constitution"],
        {"naming": EXIT_RESERVAS, "constitution": 0},
    )
    salida = capsys.readouterr().out
    assert codigo == 1
    assert "[FALLO] naming" in salida
    assert "reservas" not in salida


def test_un_fallo_real_sigue_mandando_sobre_las_reservas(monkeypatch, proyecto, capsys):
    codigo = _correr(
        monkeypatch,
        proyecto,
        ["naming", "tests", "constitution"],
        {"naming": EXIT_OMITIDO, "tests": 1, "constitution": EXIT_RESERVAS},
    )
    salida = capsys.readouterr().out
    assert codigo == 1
    assert "ROJO" in salida
    assert "Con reservas (1): constitution" in salida
