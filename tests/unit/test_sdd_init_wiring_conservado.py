"""La instalacion avisa cuando el gate puede no haber quedado cableado.

SPEC-014 FR-US1-001 y FR-US1-004. En el proyecto testigo de la campana de
usabilidad (2026-08-05), instalar sobre un repo que ya tenia
`.pre-commit-config.yaml` y `.claude/settings.json` propios dejo CERO capas de
enforcement activas. `sdd-init` los conserva por diseno, pero la unica senal era
una linea `(existe, se conserva)` perdida entre treinta lineas de log.
"""

from __future__ import annotations

import sdd_init
from conftest import crear_proyecto_brownfield


def test_avisa_y_nombra_cada_archivo_conservado(tmp_path, capsys):
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=True)
    sdd_init.main([str(tmp_path), "--language=python"])
    salida = capsys.readouterr().out
    assert "ATENCION" in salida
    assert ".pre-commit-config.yaml" in salida
    assert ".claude/settings.json" in salida


def test_el_aviso_da_las_dos_salidas_concretas(tmp_path, capsys):
    """Avisar sin decir que hacer solo mueve el problema."""
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=True)
    sdd_init.main([str(tmp_path), "--language=python"])
    salida = capsys.readouterr().out
    assert "templates/wiring/" in salida
    assert "--force" in salida
    assert "sdd_doctor.py" in salida


def test_sin_wiring_previo_no_hay_aviso(tmp_path, capsys):
    """El aviso tiene que ser raro para que se lea cuando aparece."""
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=False)
    sdd_init.main([str(tmp_path), "--language=python"])
    assert "ATENCION" not in capsys.readouterr().out


def test_con_force_no_avisa_porque_lo_piso(tmp_path, capsys):
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=True)
    sdd_init.main([str(tmp_path), "--language=python", "--force"])
    assert "ATENCION" not in capsys.readouterr().out


def test_nombra_el_indice_como_puerta_de_entrada(tmp_path, capsys):
    """FR-US1-004: en un brownfield el README propio se conserva, asi que sin
    esto la instalacion no deja ninguna puerta de entrada a lo instalado."""
    crear_proyecto_brownfield(tmp_path, layout="app")
    sdd_init.main([str(tmp_path), "--language=python"])
    assert "00-INDEX.md" in capsys.readouterr().out
