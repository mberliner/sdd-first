"""El paso `integration` corre lo declarado y nada mas (SPEC-019 US1).

Origen: V-1 de `docs/IDEAS.md`. `dirs.tests_integration` era clave de primera
clase del config y ningun paso la ejecutaba: con `pipeline.coverage` declarado
esos tests corrian de rebote dentro de `coverage` (una vez por umbral, y su
fallo se reportaba como cobertura), y sin umbrales no corrian nunca.
"""

from __future__ import annotations

from pathlib import Path

import adapter
import pytest
from sdd_config import EXIT_OMITIDO, SddConfig

KIT_ROOT = Path(__file__).resolve().parents[2]


def _cfg(tmp_path: Path, dirs: dict) -> SddConfig:
    return SddConfig(repo_root=tmp_path, raw={"dirs": dirs})


@pytest.fixture
def corridas(monkeypatch):
    """Captura los comandos en vez de correrlos: interesa que y con que carpeta."""
    vistas: list[list[str]] = []
    monkeypatch.setattr(adapter, "_run", lambda cmd, cwd: vistas.append(cmd) or 0)
    return vistas


def test_corre_la_carpeta_declarada(tmp_path, corridas):
    """FR-US1-001: el paso ejecuta `dirs.tests_integration`."""
    (tmp_path / "pruebas" / "integracion").mkdir(parents=True)

    codigo = adapter.step_integration(
        tmp_path, _cfg(tmp_path, {"tests_integration": "pruebas/integracion"})
    )

    assert codigo == 0
    assert corridas and corridas[0][-3:] == ["pytest", "pruebas/integracion", "-q"]


def test_no_toca_la_carpeta_unitaria(tmp_path, corridas):
    """`tests` sigue siendo la suite unitaria: los pasos no se pisan."""
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "integration").mkdir(parents=True)
    dirs = {"tests_unit": "tests/unit", "tests_integration": "tests/integration"}

    adapter.step_integration(tmp_path, _cfg(tmp_path, dirs))
    adapter.step_tests(tmp_path, _cfg(tmp_path, dirs))

    assert [cmd[-2] for cmd in corridas] == ["tests/integration", "tests/unit"]


def test_sin_clave_declarada_se_omite(tmp_path, corridas):
    """FR-US1-003: no hereda el fallback a `tests/` de los pasos estaticos.

    Los pasos estaticos (naming, lint, format) ante la duda miran de mas y no
    rompen nada; ejecutar tests que el proyecto no declaro es adivinar con
    efectos.
    """
    (tmp_path / "tests").mkdir()

    codigo = adapter.step_integration(tmp_path, _cfg(tmp_path, {}))

    assert codigo == EXIT_OMITIDO
    assert corridas == []


def test_carpeta_declarada_pero_ausente_se_omite_nombrandola(
    tmp_path, capsys, corridas
):
    """FR-US1-002: el motivo nombra la carpeta, no un generico 'sin tests'."""
    codigo = adapter.step_integration(
        tmp_path, _cfg(tmp_path, {"tests_integration": "tests/integration"})
    )

    assert codigo == EXIT_OMITIDO
    assert "tests/integration" in capsys.readouterr().out
    assert corridas == []


def test_el_paso_esta_en_el_dispatcher():
    """FR-US1-001: `adapter.py integration` tiene que existir para el pipeline."""
    assert adapter.STEPS["integration"] is adapter.step_integration


# El cruce "el pipeline reconoce todos los pasos del adaptador" vivia aca porque
# las dos listas estaban separadas y nada las ataba. Con el SSOT unico de
# SPEC-005 FR-006 el cruce es general y bidireccional, y su lugar es
# `tests/unit/test_vocabulario_de_pasos.py`: repetirlo aca seria la duplicacion
# que esa spec vino a cerrar.


def test_el_contrato_documenta_el_paso_y_conserva_la_semantica_de_tests():
    """FR-US1-004: el SSOT del contrato es adapters/CONTRACT.md."""
    contrato = (KIT_ROOT / "adapters" / "CONTRACT.md").read_text(encoding="utf-8")

    assert "| `integration` |" in contrato
    assert "dirs.tests_integration" in contrato
    assert "unitarios" in contrato
