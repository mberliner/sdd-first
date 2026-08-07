"""Los tests de integracion declarados se ejecutan (SPEC-019 SC-001..SC-004).

Es el dogfooding del paso `integration`, que se hace aca y no en el pipeline del
kit: el kit no tiene `tests/integration` y sus e2e siguen fuera del pipeline por
decision de [[SPEC-018-verificacion-e2e]].

Defecto que este escenario detectaria si volviera (V-1): `dirs.tests_integration`
era clave del config que ningun paso ejecutaba. Con umbrales de cobertura
declarados esos tests corrian de rebote dentro de `coverage` —y su fallo se
reportaba como cobertura—; sin umbrales, no corrian nunca.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ..lib import entorno
from ..lib.aserciones import dice, espera_exit, no_dice

CARPETA = "tests/integration"

PASA = "def test_el_saldo_se_informa():\n    assert 1 + 1 == 2\n"
FALLA = "def test_el_saldo_se_informa():\n    assert 1 + 1 == 3\n"


def _sembrar_proyecto(destino: Path) -> None:
    """Codigo, suite unitaria y suite de integracion, antes de instalar."""
    (destino / "src").mkdir(parents=True, exist_ok=True)
    (destino / "src" / "cuentas.py").write_text(
        "def saldo(cuenta):\n    return cuenta\n", encoding="utf-8"
    )
    (destino / "tests" / "unit").mkdir(parents=True, exist_ok=True)
    (destino / "tests" / "unit" / "test_cuentas.py").write_text(
        "def test_saldo():\n    assert True\n", encoding="utf-8"
    )
    (destino / CARPETA).mkdir(parents=True, exist_ok=True)
    (destino / CARPETA / "test_flujo.py").write_text(PASA, encoding="utf-8")


@pytest.fixture
def con_integracion(repo: Path) -> Path:
    """Derivado instalado sobre un proyecto que ya separa sus dos suites."""
    _sembrar_proyecto(repo)
    espera_exit(entorno.instalar(repo), porque="instalacion base del escenario")
    espera_exit(entorno.herramienta(repo, "render"), porque="paso 2 del flujo")
    return repo


def test_la_instalacion_declara_la_carpeta_y_la_corre(con_integracion: Path) -> None:
    """SC-004: sin intervencion manual, la carpeta queda declarada y ejecutada."""
    config = (con_integracion / ".sdd" / "config.yaml").read_text(encoding="utf-8")
    assert f"tests_integration: {CARPETA}" in config, (
        f"sdd-init no declaro la carpeta detectada:\n{config}"
    )

    corrida = entorno.paso(con_integracion, "integration")
    espera_exit(corrida, porque="la carpeta existe y sus tests pasan")
    dice(corrida, CARPETA)


def test_el_veredicto_del_pipeline_lo_cuenta_como_paso_medido(
    con_integracion: Path,
) -> None:
    """SC-001: no alcanza con que corra; el pipeline tiene que contarlo."""
    resultado = entorno.pipeline(con_integracion)

    dice(resultado, "--- integration ---", "[OK]    integration")
    no_dice(resultado, "[OMITIDO] integration")


def test_un_test_de_integracion_roto_pinta_su_propio_paso(
    con_integracion: Path,
) -> None:
    """SC-002: antes el fallo aparecia como `coverage` y mandaba a buscar umbrales."""
    (con_integracion / CARPETA / "test_flujo.py").write_text(FALLA, encoding="utf-8")

    corrida = entorno.paso(con_integracion, "integration")
    assert corrida.exit not in (0, 3), (
        f"un test roto no puede pasar ni omitirse{corrida.detalle()}"
    )
    dice(corrida, "test_el_saldo_se_informa")


def test_declarar_la_carpeta_sin_el_paso_lo_reporta_el_doctor(
    con_integracion: Path,
) -> None:
    """SC-003: la decision es del proyecto, pero la omision no puede ser muda."""
    config = con_integracion / ".sdd" / "config.yaml"
    texto = config.read_text(encoding="utf-8")
    config.write_text(texto.replace("    - integration\n", ""), encoding="utf-8")

    doctor = entorno.herramienta(con_integracion, "sdd_doctor")
    espera_exit(doctor, 1, porque="hay tests declarados que no corre nadie")
    dice(doctor, "dirs.tests_integration", CARPETA, "'integration'")
