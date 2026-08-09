"""Los vocabularios del kit tienen un solo SSOT (SPEC-005 FR-006/FR-007).

C-8 de `docs/IDEAS.md`: `pipeline.CODE_STEPS` y el dispatcher `STEPS` del
adaptador enumeraban lo mismo por separado y nada los ataba. Al agregar
`integration` (SPEC-019) el paso quedo implementado y el pipeline lo reporto
"paso desconocido", descontandolo del total sin ruido --la familia del falso
verde--. La duplicacion hermana era la tupla `("tests_unit",
"tests_integration")` repetida en cuatro modulos con criterios distintos.

Estos tests son la atadura: cruzan cada vocabulario contra sus consumidores, en
las dos direcciones, para que la proxima divergencia sea roja y no silenciosa.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pipeline
import pytest
from sdd_config import CODE_STEPS, TEST_DIRS, declared_test_dirs

KIT_ROOT = Path(__file__).resolve().parents[2]
ADAPTERS = KIT_ROOT / "adapters"


def _adapter_steps(language: str) -> set[str]:
    """Claves del dispatcher `STEPS`, leidas del fuente sin importar el modulo.

    Se parsea en vez de importar para que el test valga sobre cualquier adaptador
    del kit, incluidos los que traigan dependencias que este entorno no tenga.
    """
    fuente = (ADAPTERS / language / "adapter.py").read_text(encoding="utf-8")
    for nodo in ast.walk(ast.parse(fuente)):
        if not isinstance(nodo, ast.Assign):
            continue
        destinos = [t.id for t in nodo.targets if isinstance(t, ast.Name)]
        if "STEPS" in destinos and isinstance(nodo.value, ast.Dict):
            return {
                k.value
                for k in nodo.value.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            }
    raise AssertionError(f"el adaptador {language} no declara un dict STEPS")


def _lenguajes() -> list[str]:
    return sorted(d.name for d in ADAPTERS.iterdir() if (d / "adapter.py").exists())


# --- FR-006: el vocabulario de pasos de codigo ---------------------------------


def test_el_pipeline_no_tiene_lista_propia_de_pasos_de_codigo() -> None:
    """Importa el vocabulario del nucleo; no lo repite como literal."""
    assert pipeline.CODE_STEPS is CODE_STEPS
    fuente = (KIT_ROOT / "core" / "pipeline.py").read_text(encoding="utf-8")
    asignaciones = [
        nodo
        for nodo in ast.walk(ast.parse(fuente))
        if isinstance(nodo, ast.Assign)
        and any(t.id == "CODE_STEPS" for t in nodo.targets if isinstance(t, ast.Name))
    ]
    assert not asignaciones, (
        "core/pipeline.py vuelve a declarar CODE_STEPS: el SSOT es sdd_config"
    )


@pytest.mark.parametrize("language", _lenguajes())
def test_todo_paso_implementado_esta_declarado(language: str) -> None:
    """Direccion que rompio con `integration`: implementado pero desconocido."""
    sobrantes = _adapter_steps(language) - set(CODE_STEPS)
    assert not sobrantes, (
        f"el adaptador {language} implementa pasos que el contrato no declara "
        f"{sorted(sobrantes)}: el pipeline los reportaria 'paso desconocido' y "
        "los descontaria del total sin fallar"
    )


@pytest.mark.parametrize("language", _lenguajes())
def test_todo_paso_declarado_esta_implementado(language: str) -> None:
    """La otra direccion: un paso del contrato que nadie corre.

    Declararlo en `pipeline.steps` daria un fallo confuso del adaptador en vez de
    la omision con aviso que el contrato promete.
    """
    faltantes = set(CODE_STEPS) - _adapter_steps(language)
    assert not faltantes, (
        f"el adaptador {language} no implementa {sorted(faltantes)}, "
        "declarados en CODE_STEPS"
    )


def test_los_pasos_de_proceso_y_de_codigo_no_se_pisan() -> None:
    """Un nombre en los dos lados haria que gane el orden del `if`, no el config."""
    assert not pipeline.PROCESS_STEPS & set(CODE_STEPS)


# --- FR-007: las carpetas de tests ---------------------------------------------


def test_ningun_consumidor_enumera_las_claves_de_tests_por_su_cuenta() -> None:
    """La tupla literal repetida en cuatro modulos no vuelve.

    Se busca la *enumeracion* (dos o mas claves juntas en un literal), no la
    mencion: que `step_integration` nombre `tests_integration` es correcto --es
    la implementacion de ese paso-- y no tiene con que desincronizarse. Lo que
    duplicaba el SSOT era la coleccion.
    """
    claves = set(TEST_DIRS)
    culpables: list[str] = []
    for modulo in sorted((KIT_ROOT / "core").rglob("*.py")) + sorted(
        (KIT_ROOT / "adapters").rglob("*.py")
    ):
        if modulo.name == "sdd_config.py":
            continue  # el SSOT
        arbol = ast.parse(modulo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Tuple | ast.List | ast.Set):
                continue
            literales = {
                e.value
                for e in nodo.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            }
            if len(literales & claves) > 1:
                culpables.append(
                    f"{modulo.relative_to(KIT_ROOT).as_posix()}:{nodo.lineno}"
                )
    assert not culpables, (
        "enumeran claves de carpetas de tests en vez de derivarlas de "
        "sdd_config.TEST_DIRS: " + ", ".join(culpables)
    )


def test_cada_carpeta_declara_que_paso_la_ejecuta() -> None:
    """SPEC-019 FR-US2-002 sigue valiendo: ninguna carpeta sin ejecutor."""
    for clave, meta in TEST_DIRS.items():
        assert meta.step in CODE_STEPS, (
            f"dirs.{clave} dice ejecutarse en '{meta.step}', que no es un paso"
        )


def test_las_claves_conservan_el_orden_de_declaracion() -> None:
    """El orden es visible: son los `paths:` del CI y los blancos de los linters."""
    assert declared_test_dirs() == tuple(TEST_DIRS)
