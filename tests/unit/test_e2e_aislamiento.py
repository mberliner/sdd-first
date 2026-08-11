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
from sdd_config import TEST_DIRS, declared_test_dirs, load

KIT_ROOT = Path(__file__).resolve().parents[2]
E2E = KIT_ROOT / "tests" / "e2e"


@pytest.fixture(scope="module")
def pyproject() -> dict:
    return tomllib.loads((KIT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_pytest_a_secas_no_recoge_los_escenarios(pyproject: dict) -> None:
    """SPEC-018 FR-US2-003: pytest sin argumentos no recoge ningun escenario e2e."""
    testpaths = pyproject["tool"]["pytest"]["ini_options"]["testpaths"]
    assert testpaths == ["tests/unit"], (
        "`testpaths` es el unico mecanismo de seleccion: ampliarlo mete los "
        "escenarios e2e en cada corrida de `pytest`"
    )


def test_la_seleccion_no_tiene_un_segundo_mecanismo(pyproject: dict) -> None:
    """SPEC-018 FR-US2-004. Una marca `e2e` seria un filtro duplicado (Principio IV)."""
    marcas = pyproject["tool"]["pytest"]["ini_options"].get("markers", [])
    assert not any("e2e" in m for m in marcas), (
        f"`testpaths` ya excluye la suite; sobra la marca: {marcas}"
    )


def test_el_config_declara_la_carpeta_e2e_pero_no_como_integracion() -> None:
    """SPEC-018 FR-US3-003. Enmienda de 2026-08-09: la carpeta ahora se declara.

    Lo que sigue prohibido es declararla bajo `tests_integration`, que es lo que
    la arrastraria a la corrida de `coverage`: esa clave si esta marcada como
    medida. La carpeta e2e tiene clave propia, con `medida=False`.
    """
    cfg = load(KIT_ROOT)
    assert cfg.dirs.get("tests_e2e") == "tests/e2e"
    assert "tests_integration" not in cfg.dirs


def test_la_carpeta_e2e_no_entra_a_la_corrida_de_cobertura() -> None:
    """FR-US3-002: el acople que US2 nombraba, ahora impedido por propiedad.

    Antes lo sostenia la *ausencia* de la clave en el config --frágil: cualquiera
    que la declarara reintroducia el acople sin enterarse--. Ahora lo sostiene
    `TEST_DIRS`, que es el SSOT (SPEC-005 FR-007).
    """
    assert TEST_DIRS["tests_e2e"].medida is False
    assert "tests_e2e" not in declared_test_dirs(solo_medidas=True)
    assert "tests_e2e" in declared_test_dirs()


def test_el_pipeline_incluye_el_paso_e2e_ultimo() -> None:
    """FR-US3-003: sin flag, y ultimo para que un fallo barato aparezca antes."""
    cfg = load(KIT_ROOT)
    assert "e2e" in cfg.pipeline_steps
    assert cfg.pipeline_steps[-1] == "e2e"
    assert cfg.pipeline_steps.index("coverage") < cfg.pipeline_steps.index("e2e")


def test_el_generador_de_ci_no_sabe_de_e2e() -> None:
    """FR-US2-005: el workflow universal no se contamina con el caso del kit.

    Se afirma sobre el *generador*, no sobre el `ci.yml` del kit: ese ahora
    menciona `tests/e2e` legitimamente, porque sale de `dirs` como cualquier otra
    carpeta declarada. Lo que no puede pasar es que `render_ci_workflow` tenga una
    rama para la e2e.
    """
    fuente = (KIT_ROOT / "core" / "render.py").read_text(encoding="utf-8")
    assert "e2e" not in fuente


@pytest.fixture(scope="module")
def workflow_e2e() -> str:
    workflow = KIT_ROOT / ".github" / "workflows" / "e2e.yml"
    assert workflow.exists(), "falta el job propio de la suite e2e"
    return workflow.read_text(encoding="utf-8")


def test_el_workflow_e2e_es_propio_del_kit_y_escrito_a_mano(workflow_e2e: str) -> None:
    texto = workflow_e2e
    assert "tests/e2e" in texto
    assert "SDD_E2E_STRICT" in texto, "en CI el degradado por entorno tiene que fallar"
    render = (KIT_ROOT / "core" / "render.py").read_text(encoding="utf-8")
    assert "e2e.yml" not in render, (
        "`render_ci_workflow` genera el workflow universal de los derivados: "
        "un job e2e del kit no puede salir de ahi"
    )


def test_el_workflow_corre_en_las_dos_plataformas(workflow_e2e: str) -> None:
    """SC-001 se apoya en Windows: sacarlo del matrix lo dejaba sin enforcement.

    El criterio multiplataforma es de [[SPEC-012-suite-multiplataforma]]; aca
    solo se fija que la suite e2e lo respete (FR-US2-008).
    """
    faltan = [
        so for so in ("ubuntu-latest", "windows-latest") if so not in workflow_e2e
    ]
    assert not faltan, f"la matriz del job e2e no cubre: {faltan}"


def test_el_workflow_no_linta_la_suite_por_su_cuenta(workflow_e2e: str) -> None:
    """FR-US3-005: con la carpeta declarada en `dirs`, la cubre el paso `lint`.

    Lo que el workflow sigue lintando es la raiz de `tests/`, que ninguna clave
    alcanza (V-4 de docs/IDEAS.md): eso no es duplicacion, es el unico lugar que
    la mira hoy.
    """
    assert "ruff check tests/e2e" not in workflow_e2e, (
        "el workflow linta la suite por su cuenta y el paso `lint` del pipeline "
        "tambien: es la duplicacion que FR-US3-005 cierra"
    )


def test_el_workflow_verifica_que_no_quedo_residuo(workflow_e2e: str) -> None:
    """FR-US2-009: SC-002 deja de depender de que alguien mire `git status`."""
    assert "git status --porcelain" in workflow_e2e, (
        "nada verifica que la corrida no haya dejado archivos en el repositorio"
    )


def test_el_testigo_brownfield_tiene_un_solo_ssot() -> None:
    # SPEC-018 FR-US2-006: el testigo de proyecto preexistente tiene un solo SSOT.
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
