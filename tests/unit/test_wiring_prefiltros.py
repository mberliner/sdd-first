"""El wiring instalado no hardcodea carpetas de codigo (SPEC-015).

Cubre FR-001 (pre-commit sin `files:`), FR-003 (plugin de opencode derivando
del config), FR-006 (matcher de Claude Code sobre todas las tools de edicion),
FR-007 (la doc lo explica) y SC-002 (ningun rastro de los pre-filtros viejos).

Se verifica sobre `templates/wiring/`, que desde SPEC-005 FR-008 es el unico
archivo de cada pieza: el wiring del kit se genera desde ahi y `render --check`
vigila que no diverja. Antes esto recorria el par kit + plantilla porque las dos
copias podian desincronizarse -- y se desincronizaron; ahora repetir cada caso
sobre el destino generado verificaria el render, no el wiring.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = KIT_ROOT / "templates"

PRE_COMMIT = [TEMPLATES / "wiring" / ".pre-commit-config.yaml"]
SETTINGS = [TEMPLATES / "wiring" / "claude-settings.json"]
HOOKS_SH = [TEMPLATES / "wiring" / "sdd_gate_hook.sh"]
HOOKS_JSON = [TEMPLATES / "wiring" / "hooks.json"]
AGY_HOOK_PY = [TEMPLATES / "wiring" / "agy_gate_hook.py"]
AGY_DENY_JSON = [TEMPLATES / "wiring" / "agy_deny.json"]
PLUGIN_JS = TEMPLATES / "wiring" / "opencode-sdd-gate.js"
DOCS = [TEMPLATES / "docs" / "SDD-ENFORCEMENT.md"]

# Pre-filtros hardcodeados que esta spec elimina (SC-002).
PATRONES_VIEJOS = ("^(src|app|lib)/", "isUnderSrc", "resolveSrcPath", "*'\"src/'*")


@pytest.mark.parametrize("ruta", PRE_COMMIT, ids=lambda p: p.parent.name)
def test_pre_commit_no_prefiltra_el_hook_del_gate(ruta):
    """FR-001: sin `files:`, todos los staged van al gate y el gate decide."""
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    inicio = next(i for i, linea in enumerate(lineas) if "id: sdd-gate" in linea)
    resto = enumerate(lineas[inicio + 1 :], inicio + 1)
    fin = next((i for i, linea in resto if "- id: " in linea), len(lineas))
    bloque = lineas[inicio:fin]
    assert not [x for x in bloque if x.strip().startswith("files:")], (
        f"{ruta} volvio a pre-filtrar el hook sdd-gate: seria una segunda copia "
        "de dirs.source_roots"
    )
    assert any("pass_filenames: true" in x for x in bloque)


@pytest.mark.parametrize("ruta", SETTINGS, ids=lambda p: p.parent.name)
def test_matcher_cubre_las_tools_de_edicion(ruta):
    """FR-006: MultiEdit y NotebookEdit tambien escriben archivos."""
    hooks = json.loads(ruta.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    matchers = {h["matcher"] for h in hooks}
    assert len(matchers) == 1
    tools = set(matchers.pop().split("|"))
    assert {"Edit", "Write", "MultiEdit", "NotebookEdit"} <= tools


@pytest.mark.parametrize("ruta", HOOKS_SH, ids=lambda p: p.parent.name)
def test_hook_sh_deriva_los_roots_del_config(ruta):
    """FR-002: la rama fail-closed consulta el config, no una carpeta fija."""
    texto = ruta.read_text(encoding="utf-8")
    assert "sdd_source_roots" in texto
    assert ".sdd/config.yaml" in texto


def test_plugin_opencode_deriva_los_roots_del_config():
    """FR-003: idem para la capa de opencode, que pre-filtra en cada escritura."""
    texto = PLUGIN_JS.read_text(encoding="utf-8")
    assert "export const sourceRoots" in texto
    assert ".sdd" in texto and "config.yaml" in texto


@pytest.mark.parametrize(
    "ruta", PRE_COMMIT + SETTINGS + HOOKS_SH + [PLUGIN_JS], ids=lambda p: str(p.name)
)
def test_sin_rastros_de_los_prefiltros_hardcodeados(ruta):
    """SC-002: ninguna capa vuelve a decidir por una carpeta de ejemplo."""
    texto = ruta.read_text(encoding="utf-8")
    presentes = [p for p in PATRONES_VIEJOS if p in texto]
    assert not presentes, f"{ruta} conserva pre-filtros hardcodeados: {presentes}"


@pytest.mark.parametrize("ruta", DOCS, ids=lambda p: p.parent.name)
def test_la_doc_explica_el_prefiltro_y_el_limite_de_bash(ruta):
    """FR-007: el adoptante tiene que poder leer por que Bash no dispara el gate."""
    texto = ruta.read_text(encoding="utf-8")
    assert "Bash" in texto
    assert "pre-filtro" in texto.lower()
    assert "dirs.source_roots" in texto


@pytest.mark.parametrize("ruta", HOOKS_JSON, ids=lambda p: p.parent.name)
def test_hooks_json_encadena_las_cuatro_ramas(ruta):
    """SPEC-015 FR-US2-002: adaptador (python3, python) y fail-closed (type, cat).

    Las rutas van relativas a `.agents/`, que es el `cwd` con el que Antigravity
    invoca el hook: con `.agents/agy_gate_hook.py` resolvia a `.agents/.agents/`
    y —siendo el CLI fail-open— el gate quedaba apagado en silencio.
    """
    comando = json.loads(ruta.read_text(encoding="utf-8"))["sdd-gate"]["PreToolUse"][0][
        "hooks"
    ][0]["command"]
    assert comando.split(" || ") == [
        "python3 agy_gate_hook.py",
        "python agy_gate_hook.py",
        "type agy_deny.json",
        "cat agy_deny.json",
    ]


@pytest.mark.parametrize("ruta", AGY_HOOK_PY, ids=lambda p: p.parent.name)
def test_agy_hook_py_se_reubica_en_la_raiz_y_delega_en_el_gate(ruta):
    """SPEC-015 FR-US2-004: la raiz sale de `__file__`, no del cwd de Antigravity."""
    texto = ruta.read_text(encoding="utf-8")
    assert "os.chdir(repo_root)" in texto
    assert "Path(__file__).resolve().parent.parent" in texto
    # `main`, no `decide`: por ahi pasa el escape hatch SDD_GATE_BYPASS.
    assert "sdd_gate.main(" in texto


@pytest.mark.parametrize("ruta", AGY_DENY_JSON, ids=lambda p: p.parent.name)
def test_agy_deny_json_es_un_deny_bien_formado(ruta):
    """SPEC-015 FR-US2-007: el fail-closed sin interprete se sirve desde archivo.

    Un `echo` no sirve: en `cmd.exe` las comillas llegan escapadas y Antigravity
    descarta la respuesta (`protojson: syntax error`), volviendo a fail-open.
    """
    data = json.loads(ruta.read_text(encoding="utf-8"))
    assert data["decision"] == "deny"
    assert "Python" in data["reason"]


def test_el_catalogo_instala_el_wiring_de_antigravity():
    """SPEC-015 FR-US2-001: sdd_init deposita las tres piezas en `.agents/`.

    Las tres o ninguna: el adaptador sin `hooks.json` no lo invoca nadie, y
    `hooks.json` sin `agy_deny.json` deja la rama fail-closed sin qué imprimir.
    """
    import sdd_catalog

    destinos = {destino for _, destino in sdd_catalog.WIRING}
    assert {
        ".agents/hooks.json",
        ".agents/agy_gate_hook.py",
        ".agents/agy_deny.json",
    } <= destinos


def test_gate_wiring_conoce_hooks_json():
    """SPEC-015 FR-US2-005: sdd_doctor reporta .agents/hooks.json como cableado."""
    import sdd_config

    assert ".agents/hooks.json" in sdd_config.GATE_WIRING
