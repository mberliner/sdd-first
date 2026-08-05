"""El wiring instalado no hardcodea carpetas de codigo (SPEC-015).

Cubre FR-001 (pre-commit sin `files:`), FR-003 (plugin de opencode derivando
del config), FR-006 (matcher de Claude Code sobre todas las tools de edicion),
FR-007 (la doc lo explica) y SC-002 (ningun rastro de los pre-filtros viejos).

Se verifica sobre el par kit + plantilla: el kit dogfoodea su propio wiring y
los arreglos tienen que llegar a las dos copias, que es justo lo que fallaba.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = KIT_ROOT / "templates"

PRE_COMMIT = [
    KIT_ROOT / ".pre-commit-config.yaml",
    TEMPLATES / "wiring" / ".pre-commit-config.yaml",
]
SETTINGS = [
    KIT_ROOT / ".claude" / "settings.json",
    TEMPLATES / "wiring" / "claude-settings.json",
]
HOOKS_SH = [
    KIT_ROOT / ".claude" / "sdd_gate_hook.sh",
    TEMPLATES / "wiring" / "sdd_gate_hook.sh",
]
PLUGIN_JS = TEMPLATES / "wiring" / "opencode-sdd-gate.js"
DOCS = [
    KIT_ROOT / "docs" / "SDD-ENFORCEMENT.md",
    TEMPLATES / "docs" / "SDD-ENFORCEMENT.md",
]

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
