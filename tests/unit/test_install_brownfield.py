"""Instalacion sobre un proyecto que ya tiene codigo (SPEC-003 SC-005/SC-006).

Es el escenario que la campana de usabilidad del 2026-08-05 encontro roto: el
kit instalado sobre un proyecto Python con codigo en `app/` reportaba VERDE 8/8
y "instalacion sana" mientras `naming` y `tests` se omitian, dos violaciones de
SPEC-000 quedaban sin detectar y el gate permitia commits sobre `app/`.

A diferencia de los tests unitarios de `_seed_dirs`, estos corren el pipeline y
el gate de verdad contra el proyecto instalado: es la unica forma de que el
falso verde no pueda volver por una pieza intermedia.
"""

from __future__ import annotations

import subprocess
import sys

import sdd_gate
import sdd_init
from conftest import crear_proyecto_brownfield

KIT_CORE = "tools/sdd/core"


def _instalar(destino):
    """Instala y deja el derivado como lo dejan los pasos 2 y 3 del README."""
    sdd_init.main([str(destino), "--language=python"])
    for script in ("render.py", "gen_skill_adapters.py"):
        subprocess.run(  # nosec B603 - script del propio kit recien vendorizado
            [sys.executable, f"{KIT_CORE}/{script}"],
            cwd=destino,
            check=True,
            capture_output=True,
        )
    return destino


def _pipeline(destino):
    """Corre el pipeline y devuelve (returncode, salida completa).

    Las dos corrientes se unen a proposito: los checks reportan las violaciones
    por stderr y el pipeline su resumen por stdout, y lo que se afirma aca es lo
    que el operador ve en su terminal.
    """
    resultado = subprocess.run(  # nosec B603 - script del propio kit
        [sys.executable, f"{KIT_CORE}/pipeline.py"],
        cwd=destino,
        capture_output=True,
        text=True,
    )
    return resultado.returncode, resultado.stdout + resultado.stderr


def test_naming_verifica_el_codigo_real_sin_editar_el_config(tmp_path):
    """SC-005: antes se omitia con 'sin carpetas de codigo todavia'."""
    proyecto = _instalar(crear_proyecto_brownfield(tmp_path, layout="app"))
    codigo, salida = _pipeline(proyecto)
    assert "[OMITIDO] naming" not in salida
    assert "cargar_pedidos_json" in salida
    assert "ClienteOpenaiResumen" in salida
    # El pipeline sale ROJO por el codigo del proyecto, no VERDE por no mirarlo.
    assert codigo == 1
    assert "[FALLO] naming" in salida


def test_el_resumen_no_cuenta_como_ok_lo_que_omitio(tmp_path):
    """FR-009 de punta a punta: los pasos sin tooling se declaran omitidos."""
    proyecto = _instalar(crear_proyecto_brownfield(tmp_path, layout="app"))
    _, salida = _pipeline(proyecto)
    assert "Omitidos (" in salida
    assert "no verificados" in salida


def test_el_gate_bloquea_el_codigo_real_del_proyecto(tmp_path):
    """SC-006: antes el gate solo protegia `src/`, que aca no existe."""
    proyecto = _instalar(crear_proyecto_brownfield(tmp_path, layout="app"))
    permitir, motivo = sdd_gate.decide(
        {"tool_input": {"file_path": "app/servicio.py"}}, proyecto
    )
    assert not permitir
    assert "spec" in motivo.lower()


def test_el_gate_no_bloquea_fuera_del_codigo(tmp_path):
    """Contraste: `src/` ya no es codigo fuente en este proyecto."""
    proyecto = _instalar(crear_proyecto_brownfield(tmp_path, layout="app"))
    permitir, _ = sdd_gate.decide(
        {"tool_input": {"file_path": "src/inexistente.py"}}, proyecto
    )
    assert permitir


def test_conserva_los_archivos_del_dueno(tmp_path):
    """La instalacion no pisa lo que el proyecto ya tenia."""
    proyecto = crear_proyecto_brownfield(tmp_path, layout="app")
    readme_previo = (proyecto / "README.md").read_text(encoding="utf-8")
    _instalar(proyecto)
    assert (proyecto / "README.md").read_text(encoding="utf-8") == readme_previo
