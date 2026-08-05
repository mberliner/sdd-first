"""El doctor no da por bueno un wiring que no cablea el gate.

SPEC-014 FR-US1-002 (antes G-4 de `docs/IDEAS.md`) y FR-US2-003. La campana de
usabilidad reprodujo el falso positivo completo: un `.pre-commit-config.yaml`
propio con solo `ruff` y un `.claude/settings.json` propio, y `sdd-doctor`
respondiendo "Instalacion SDD sana" sobre un proyecto sin ninguna capa de gate.
"""

from __future__ import annotations

import sdd_doctor
import sdd_init
from conftest import crear_proyecto_brownfield


def _correr_doctor(destino, monkeypatch, capsys) -> tuple[int, str]:
    """El doctor resuelve la raiz desde el cwd: hay que estar en el destino."""
    monkeypatch.chdir(destino)
    codigo = sdd_doctor.main([])
    return codigo, capsys.readouterr().out


def test_wiring_propio_del_proyecto_es_un_problema(tmp_path, monkeypatch, capsys):
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=True)
    sdd_init.main([str(tmp_path), "--language=python"])
    codigo, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    assert codigo == 1
    assert "no invoca sdd_gate.py" in salida
    assert "no invoca sdd_gate_hook.sh" in salida
    assert "Instalación SDD sana" not in salida


def test_wiring_del_kit_no_es_un_problema(tmp_path, monkeypatch, capsys):
    """Contraste de control: mismo proyecto, wiring instalado por el kit."""
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=False)
    sdd_init.main([str(tmp_path), "--language=python"])
    _, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    assert "no invoca" not in salida


def test_falta_de_archivo_se_reporta_distinto_de_contenido_ajeno(
    tmp_path, monkeypatch, capsys
):
    """Ausencia y presencia-sin-cablear son dos problemas distintos: el primero
    lo arregla reinstalar, el segundo hay que fusionarlo a mano."""
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=False)
    sdd_init.main([str(tmp_path), "--language=python"])
    (tmp_path / ".pre-commit-config.yaml").unlink()
    _, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    assert "falta .pre-commit-config.yaml" in salida


def test_el_drift_nombra_el_artefacto_desincronizado(tmp_path, monkeypatch, capsys):
    """FR-US2-003: recien instalado y sin correr render, lo que falta es
    CONSTITUTION.md — el mensaje tiene que decirlo en vez de citar una lista fija.
    """
    crear_proyecto_brownfield(tmp_path, layout="app")
    sdd_init.main([str(tmp_path), "--language=python"])
    _, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    problemas = [line for line in salida.splitlines() if "desincronizados:" in line]
    assert problemas, salida
    assert any("CONSTITUTION.md" in line for line in problemas)


def test_el_drift_cita_la_ruta_vendorizada_del_script(tmp_path, monkeypatch, capsys):
    """FR-US2-002: en un derivado el script vive en tools/sdd/core/, no en core/."""
    crear_proyecto_brownfield(tmp_path, layout="app")
    sdd_init.main([str(tmp_path), "--language=python"])
    _, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    assert "python tools/sdd/core/render.py" in salida
