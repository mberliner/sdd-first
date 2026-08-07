"""Ninguna carpeta de tests declarada queda sin ejecutor (SPEC-019 US2).

Que el ciclo rapido incluya o no los tests de integracion es decision del
proyecto —el paso es opcional en `pipeline.steps`—, pero la omision no puede ser
silenciosa: es exactamente el defecto que esta spec corrige (V-1), y sin este
aviso un paso opcional lo reintroduce.
"""

from __future__ import annotations

from pathlib import Path

import sdd_doctor
from sdd_config import TEST_DIR_STEP, SddConfig


def _cfg(dirs: dict, steps: list[str]) -> SddConfig:
    return SddConfig(
        repo_root=Path("."), raw={"dirs": dirs, "pipeline": {"steps": steps}}
    )


def test_carpeta_declarada_sin_su_paso_es_problema():
    """FR-US2-001: el mensaje nombra la clave, la carpeta y el paso que falta."""
    problemas = sdd_doctor._tests_sin_ejecutor(
        _cfg({"tests_integration": "tests/integration"}, ["naming", "tests"])
    )

    assert len(problemas) == 1
    assert "dirs.tests_integration" in problemas[0]
    assert "tests/integration" in problemas[0]
    assert "'integration'" in problemas[0]


def test_con_el_paso_declarado_no_hay_problema():
    assert (
        sdd_doctor._tests_sin_ejecutor(
            _cfg({"tests_integration": "tests/integration"}, ["tests", "integration"])
        )
        == []
    )


def test_sin_la_clave_no_hay_nada_huerfano():
    """Un proyecto que no declara la carpeta no tiene por que ver el aviso."""
    assert (
        sdd_doctor._tests_sin_ejecutor(_cfg({"tests_unit": "tests/unit"}, ["tests"]))
        == []
    )


def test_tambien_cubre_la_carpeta_unitaria():
    """El invariante es por carpeta declarada, no una regla ad-hoc de integracion."""
    problemas = sdd_doctor._tests_sin_ejecutor(
        _cfg({"tests_unit": "tests/unit"}, ["naming"])
    )

    assert len(problemas) == 1
    assert "dirs.tests_unit" in problemas[0]


def test_la_correspondencia_carpeta_paso_tiene_un_solo_ssot():
    """FR-US2-002: el doctor no guarda su propia copia del mapa."""
    assert TEST_DIR_STEP == {"tests_unit": "tests", "tests_integration": "integration"}

    fuente = Path(sdd_doctor.__file__).read_text(encoding="utf-8")
    assert "TEST_DIR_STEP" in fuente
    for paso in TEST_DIR_STEP.values():
        assert f'"{paso}"' not in fuente, (
            f"sdd_doctor.py nombra el paso '{paso}' a mano: sale de TEST_DIR_STEP"
        )
