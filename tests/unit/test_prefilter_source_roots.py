"""Paridad de los pre-filtros de wiring con el config (SPEC-015 FR-004, FR-005).

Las capas que deciden *si preguntarle al gate* sin poder invocarlo —la rama
fail-closed de `sdd_gate_hook.sh` y el plugin de opencode— derivan las carpetas
de codigo de `.sdd/config.yaml` por su cuenta, cada una en su lenguaje y sin
parser YAML. Esa duplicacion deliberada solo es sostenible si esta atada: para
cada config representativo, los tres derivadores (Python autoritativo, sh, JS)
tienen que coincidir exactamente.

El caso JS se omite si no hay `node` en el entorno.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import ejecutable_sh

KIT_ROOT = Path(__file__).resolve().parents[2]
HOOK_SH = KIT_ROOT / "templates" / "wiring" / "sdd_gate_hook.sh"
PLUGIN_JS = KIT_ROOT / "templates" / "wiring" / "opencode-sdd-gate.js"

sys.path.insert(0, str(KIT_ROOT / "core"))
from sdd_config import declared_test_dirs, load  # noqa: E402

# Bloque `dirs:` que declara TODAS las carpetas de tests que el kit conoce
# (SPEC-015 FR-010). Se arma desde `declared_test_dirs()` a proposito: escrito a
# mano, este caso envejece igual que envejecio FR-004. Cuando SPEC-018 sumo
# `tests_e2e` nadie lo agrego a las tres derivaciones, las tres coincidieron en
# devolver `tests` como carpeta de codigo, y el test las dio por parejas porque
# ninguno de sus configs la declaraba. Asi, sumar una clase de test nueva a
# TEST_DIRS pone esto en rojo hasta que las tres capas la reconozcan.
_DIRS_CON_TODAS_LAS_CARPETAS_DE_TESTS = "dirs:\n  domain: src/domain\n" + "".join(
    f"  {clave}: tests/{clave.removeprefix('tests_')}\n"
    for clave in declared_test_dirs()
)

# nombre -> (contenido de .sdd/config.yaml o None si no debe existir, esperado)
CONFIGS: dict[str, tuple[str | None, list[str]]] = {
    # `src`, nunca `tests`: el gate protege el codigo y deja escribir los tests
    # (FR-009). Derivar `tests` aca impide el rojo de TDD en cualquier derivado
    # que declare e2e sin `source_roots` explicito.
    "toda_carpeta_de_tests_declarada": (
        _DIRS_CON_TODAS_LAS_CARPETAS_DE_TESTS,
        ["src"],
    ),
    "explicito_inline": (
        "project:\n  name: x\ndirs:\n"
        "  source_roots: [pkg, cmd]\n  tests_unit: tests/unit\n",
        ["pkg", "cmd"],
    ),
    "explicito_en_bloque": (
        "dirs:\n  source_roots:\n    - pkg\n    - cmd   # con comentario\n"
        "naming:\n  prohibited: [foo]\n",
        ["pkg", "cmd"],
    ),
    "implicito_desde_capas": (
        "dirs:\n  domain: src/domain\n  ui: src/ui\n  adapters: lib/adapters\n"
        "  tests_unit: tests/unit\n  tests_integration: tests/integration\n",
        ["src", "lib"],
    ),
    "dirs_todo_comentado": ("dirs:\n  # todo comentado\nnaming: {}\n", ["src"]),
    "sin_config": (None, ["src"]),
    "valores_con_comillas": (
        "dirs:\n  domain: \"app/domain\"\n  ui: 'app/ui'\n  tests_unit: tests/unit\n",
        ["app"],
    ),
    "config_con_crlf": (
        "dirs:\r\n  source_roots: [pkg]\r\n  tests_unit: tests/unit\r\n",
        ["pkg"],
    ),
}


@pytest.fixture(params=sorted(CONFIGS))
def caso(request, tmp_path):
    cuerpo, esperado = CONFIGS[request.param]
    if cuerpo is not None:
        (tmp_path / ".sdd").mkdir()
        # newline="": el contenido manda, para poder sembrar CRLF a proposito.
        (tmp_path / ".sdd" / "config.yaml").write_text(
            cuerpo, encoding="utf-8", newline=""
        )
    return tmp_path, esperado


def _roots_sh(root: Path) -> list[str]:
    sh = ejecutable_sh()
    res = subprocess.run(
        [sh, str(HOOK_SH), "--source-roots", str(root)],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.split()


def _roots_js(root: Path) -> list[str]:
    codigo = (
        f"import {{ sourceRoots }} from {json.dumps(PLUGIN_JS.as_uri())};\n"
        f"console.log(sourceRoots({json.dumps(str(root))}).join(' '));\n"
    )
    res = subprocess.run(
        [shutil.which("node") or "node", "--input-type=module", "-e", codigo],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.split()


def test_python_es_el_autoritativo(caso):
    root, esperado = caso
    assert load(root).source_roots == esperado


def test_prefiltro_sh_coincide_con_el_config(caso):
    root, esperado = caso
    assert _roots_sh(root) == esperado


def test_prefiltro_js_coincide_con_el_config(caso):
    if shutil.which("node") is None:
        pytest.skip("node ausente: no se puede verificar el pre-filtro de opencode")
    root, esperado = caso
    assert _roots_js(root) == esperado
