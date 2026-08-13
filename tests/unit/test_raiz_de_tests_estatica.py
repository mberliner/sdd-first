"""Los pasos estaticos alcanzan la raiz de `tests/` (SPEC-019 US4).

Origen: V-4 de `docs/IDEAS.md`. Las claves de `dirs` apuntan a subcarpetas
(`tests_unit`, `tests_integration`, `tests_e2e`), asi que la infraestructura
compartida que vive en la raiz --`tests/conftest.py`, `tests/fixtures_proyecto.py`--
quedaba fuera de `naming`/`lint`/`format`: una carpeta que existe, que se edita
seguido y que ningun paso verificaba.

Es el caso simetrico del que abrio la spec: US2 avisa sobre carpetas
*declaradas* sin ejecutor, y la raiz de `tests/` no esta declarada en ninguna
clave, asi que ese aviso no puede verla.
"""

from __future__ import annotations

from pathlib import Path

import adapter
import check_naming
import pytest
from sdd_config import SddConfig, colapsar_a_raiz_comun


def _cfg(tmp_path: Path, dirs: dict) -> SddConfig:
    return SddConfig(repo_root=tmp_path, raw={"dirs": dirs})


def test_fr_us4_001_la_raiz_comun_reemplaza_a_las_subcarpetas():
    """FR-US4-001: los pasos estaticos reciben la raiz, no solo las subcarpetas.

    Es lo que pone a `tests/conftest.py` dentro del alcance: no vive en ninguna
    subcarpeta declarada, asi que solo lo alcanza quien mire la raiz.
    """
    assert colapsar_a_raiz_comun(["tests/unit", "tests/integration"]) == ["tests"]


def test_fr_us4_002_ninguna_carpeta_se_visita_dos_veces():
    """FR-US4-002: la raiz derivada no convive con las carpetas que contiene.

    El solape no es un detalle de performance: ruff lintaria dos veces y
    `check_naming` reportaria cada violacion duplicada en la salida que lee el
    operador.
    """
    resultado = colapsar_a_raiz_comun(["tests/unit", "tests/integration"])
    assert "tests/unit" not in resultado
    assert "tests/integration" not in resultado
    assert len(resultado) == len(set(resultado))


def test_fr_us4_003_arboles_distintos_no_colapsan_a_la_raiz_del_repo():
    """FR-US4-003: la guarda. Sin ancestro propio, se devuelve lo declarado.

    Barrer el repo entero porque el layout es inusual seria mucho peor que el
    agujero que se esta tapando.
    """
    declaradas = ["pruebas/unit", "e2e"]
    assert colapsar_a_raiz_comun(declaradas) == declaradas


@pytest.mark.parametrize(
    "declaradas",
    [
        [],
        ["tests/unit"],
        ["tests"],
    ],
)
def test_fr_us4_003_casos_borde_no_ensanchan_el_alcance(declaradas):
    """FR-US4-003: una sola carpeta (o ninguna) no gana alcance por derivacion.

    Con `tests/unit` como unica carpeta declarada su ancestro es `tests`, pero
    subir ahi visitaria carpetas hermanas que el proyecto nunca declaro. La
    derivacion colapsa lo declarado; no lo ensancha.
    """
    assert colapsar_a_raiz_comun(declaradas) == declaradas


def test_fr_us4_004_la_relajacion_en_tests_sigue_aplicando_bajo_la_raiz(tmp_path):
    """FR-US4-004: pasar `tests/` en vez de `tests/unit` no des-relaja tokens.

    `relax_in_tests` ya se rompio una vez por comparar contra el basename
    equivocado (B-2 de `docs/IDEAS.md`): con `tests/unit` el `name` era `unit` y
    la relajacion no aplicaba nunca. El cambio de blanco vuelve a mover ese
    basename, asi que el riesgo es el mismo.

    Se ejercita con `pruebas/` a proposito: con `tests/` la relajacion la salva
    el fallback del basename de `_is_test_root`, que es una casualidad del
    nombre y no la garantia que este FR pide.
    """
    raiz = tmp_path / "pruebas"
    (raiz / "unit").mkdir(parents=True)
    declaradas = [(raiz / "unit").resolve()]

    assert check_naming._is_test_root(raiz / "unit", declaradas), (
        "la carpeta declarada misma tiene que seguir relajada"
    )
    assert check_naming._is_test_root(raiz, declaradas), (
        "la raiz que contiene a la carpeta declarada tambien: es el blanco que "
        "reciben los pasos estaticos desde FR-US4-001"
    )
    assert not check_naming._is_test_root(tmp_path / "src", declaradas), (
        "el codigo de produccion no gana relajacion por esto"
    )


def test_fr_us4_005_los_pasos_que_ejecutan_tests_no_reciben_la_raiz(tmp_path):
    """FR-US4-005: `tests` sigue corriendo `dirs.tests_unit`, no `tests/`.

    Ejecutar la raiz le haria correr al paso `tests` la suite de integracion:
    el defecto original de esta spec, al reves.
    """
    cfg = _cfg(
        tmp_path, {"tests_unit": "tests/unit", "tests_integration": "tests/integration"}
    )
    assert adapter._test_dirs(cfg) == ["tests/unit", "tests/integration"]


def test_fr_us4_006_el_criterio_vive_una_sola_vez_en_sdd_config():
    """FR-US4-006: el adaptador consume la derivacion, no la reimplementa.

    Mismo invariante que FR-US2-002: la correspondencia carpeta<->paso se
    declara una vez en `core/sdd_config.py`.
    """
    fuente = Path(adapter.__file__).read_text(encoding="utf-8")
    assert "colapsar_a_raiz_comun" in fuente
