"""La suite e2e no se cuela en el ciclo rapido (SPEC-018 US2).

Estas aserciones son la contracara del riesgo concreto que la spec descarta:
declarar `tests/e2e` como `dirs.tests_integration` la haria correr dentro del
paso `coverage` del pipeline, porque `_source_and_test_dirs` del adaptador
incluye esa clave. Sin un test que lo fije, el proximo que edite el config
reintroduce el acople sin enterarse.
"""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest
from sdd_config import load

KIT_ROOT = Path(__file__).resolve().parents[2]
E2E = KIT_ROOT / "tests" / "e2e"


@pytest.fixture(scope="module")
def pyproject() -> dict:
    return tomllib.loads((KIT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_pytest_a_secas_no_recoge_los_escenarios(pyproject: dict) -> None:
    testpaths = pyproject["tool"]["pytest"]["ini_options"]["testpaths"]
    assert testpaths == ["tests/unit"], (
        "`testpaths` es el unico mecanismo de seleccion: ampliarlo mete los "
        "escenarios e2e en cada corrida de `pytest`"
    )


def test_la_seleccion_no_tiene_un_segundo_mecanismo(pyproject: dict) -> None:
    """Una marca `e2e` seria un filtro duplicado (Principio IV)."""
    marcas = pyproject["tool"]["pytest"]["ini_options"].get("markers", [])
    assert not any("e2e" in m for m in marcas), (
        f"`testpaths` ya excluye la suite; sobra la marca: {marcas}"
    )


def test_el_config_no_declara_la_carpeta_e2e() -> None:
    cfg = load(KIT_ROOT)
    declaradas = {k: v for k, v in cfg.dirs.items() if "e2e" in str(v)}
    assert not declaradas, (
        "declarar tests/e2e en `dirs` la arrastra a los pasos del adaptador "
        f"(naming/lint/format/coverage): {declaradas}"
    )
    assert "tests_integration" not in cfg.dirs


def test_el_pipeline_no_incluye_un_paso_e2e() -> None:
    cfg = load(KIT_ROOT)
    assert not [s for s in cfg.pipeline_steps if "e2e" in s]


def test_el_ci_generado_no_sabe_de_e2e() -> None:
    """El workflow universal que reciben los derivados no se contamina."""
    generado = (KIT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert "tests/e2e" not in generado


def test_el_workflow_e2e_es_propio_del_kit_y_escrito_a_mano() -> None:
    workflow = KIT_ROOT / ".github" / "workflows" / "e2e.yml"
    assert workflow.exists(), "falta el job propio de la suite e2e"
    texto = workflow.read_text(encoding="utf-8")
    assert "tests/e2e" in texto
    assert "SDD_E2E_STRICT" in texto, "en CI el degradado por entorno tiene que fallar"
    render = (KIT_ROOT / "core" / "render.py").read_text(encoding="utf-8")
    assert "e2e.yml" not in render, (
        "`render_ci_workflow` genera el workflow universal de los derivados: "
        "un job e2e del kit no puede salir de ahi"
    )


def test_el_testigo_brownfield_tiene_un_solo_ssot() -> None:
    # Partido para que este archivo no cuente como una definicion mas.
    marca = "def " + "crear_proyecto_brownfield"
    definiciones = [
        p.relative_to(KIT_ROOT).as_posix()
        for p in (KIT_ROOT / "tests").rglob("*.py")
        if marca in p.read_text(encoding="utf-8")
    ]
    assert definiciones == ["tests/fixtures_proyecto.py"], (
        f"el testigo se define en mas de un lugar: {definiciones}"
    )


FIXTURES_DEL_HARNESS = frozenset(
    {"workspace", "destino", "repo", "derivado", "derivado_con_hooks"}
)


def _es_fixture(funcion: ast.FunctionDef) -> bool:
    return any("fixture" in ast.unparse(d) for d in funcion.decorator_list)


def _fixtures_locales(modulo: ast.Module) -> dict[str, list[str]]:
    return {
        nodo.name: [a.arg for a in nodo.args.args]
        for nodo in modulo.body
        if isinstance(nodo, ast.FunctionDef) and _es_fixture(nodo)
    }


def _llega_al_harness(params: list[str], locales: dict[str, list[str]]) -> bool:
    """Recorre la cadena de fixtures hasta dar con una del harness."""
    pendientes, vistos = list(params), set()
    while pendientes:
        nombre = pendientes.pop()
        if nombre in FIXTURES_DEL_HARNESS:
            return True
        if nombre in vistos:
            continue
        vistos.add(nombre)
        pendientes.extend(locales.get(nombre, []))
    return False


def test_todo_escenario_parte_de_un_entorno_del_harness() -> None:
    """SPEC-018 FR-US1-007: la carpeta es infraestructura compartida.

    Otra spec puede agregar su escenario aca —`test_tests_de_integracion.py` es
    de [[SPEC-019]]— pero no puede armarse su propio entorno: el workspace
    efimero, su aislamiento del arbol del kit y el degradado por `pre-commit`
    ausente son contrato de esta spec. Cada test tiene que llegar, directo o a
    traves de un fixture propio, a uno de los fixtures del harness.
    """
    infractores: list[str] = []
    duplican: list[str] = []
    for archivo in sorted((E2E / "escenarios").glob("test_*.py")):
        modulo = ast.parse(archivo.read_text(encoding="utf-8"))
        locales = _fixtures_locales(modulo)
        duplican.extend(
            f"{archivo.name}::{n}" for n in locales if n in FIXTURES_DEL_HARNESS
        )
        for nodo in modulo.body:
            if not isinstance(nodo, ast.FunctionDef) or not nodo.name.startswith(
                "test_"
            ):
                continue
            params = [a.arg for a in nodo.args.args]
            if not _llega_al_harness(params, locales):
                infractores.append(f"{archivo.name}::{nodo.name}")

    assert not infractores, (
        f"no parten de un entorno del harness (se arman el suyo): {infractores}"
    )
    assert not duplican, f"redefinen un fixture del harness: {duplican}"


def test_solo_el_harness_conoce_la_ruta_del_kit() -> None:
    """Ningun escenario construye rutas contra el arbol del kit.

    `entorno.py` es el unico que puede: la usa para invocar `sdd_init` desde el
    clon y para verificar que el workspace no se solape con el repositorio.
    """
    infractores = [
        archivo.relative_to(E2E).as_posix()
        for archivo in E2E.rglob("*.py")
        if archivo.name != "entorno.py"
        and "KIT_ROOT" in archivo.read_text(encoding="utf-8")
    ]
    assert not infractores, f"construyen rutas dentro del kit: {infractores}"
