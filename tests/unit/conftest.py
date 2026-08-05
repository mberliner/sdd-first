"""Hace importables los módulos del núcleo y del adaptador python en los tests."""

import os
import sys
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
for extra in (KIT_ROOT / "core", KIT_ROOT / "adapters" / "python"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

# NTFS no expresa los bits de ejecucion de POSIX: `Path.chmod(0o755)` corre sin
# error pero `st_mode` los reporta apagados. Los tests que verifican el *efecto*
# de un chmod se saltan ahi; el que verifica la *intencion* corre siempre
# (SPEC-012 FR-002/FR-004).
SOPORTA_PERMISOS_POSIX = os.name != "nt"

requiere_permisos_posix = pytest.mark.skipif(
    not SOPORTA_PERMISOS_POSIX,
    reason="el sistema de archivos no expresa los bits de ejecucion de POSIX",
)


def crear_proyecto_brownfield(
    tmp_path: Path,
    layout: str = "app",
    con_wiring: bool = False,
) -> Path:
    """Proyecto Python preexistente, el estado 'antes' de un adoptante real.

    Codigo en `<layout>/` (no en `src/`, para que el layout heredado del ejemplo
    no acierte por casualidad), tests en `tests/`, y archivos propios que
    `sdd-init` tiene que respetar. `con_wiring` agrega un
    `.pre-commit-config.yaml` y un `.claude/settings.json` del usuario.

    Se construye en codigo y no como fixture versionado a proposito: bajo
    `tests/` cualquier `test_*.py` de un fixture lo recogeria la propia suite
    (`testpaths = ["tests/unit"]` en pyproject.toml).
    """
    codigo = tmp_path / layout
    (codigo / "dominio").mkdir(parents=True)
    (codigo / "dominio" / "modelo.py").write_text(
        "class Pedido:\n    def __init__(self, monto):\n        self.monto = monto\n",
        encoding="utf-8",
    )
    # Dos identificadores con palabras excluidas del config de ejemplo: si el
    # paso `naming` mira esta carpeta, tiene que encontrarlos.
    (codigo / "servicio.py").write_text(
        "import json\n\n\n"
        "def cargar_pedidos_json(ruta):\n"
        "    return json.loads(ruta)\n\n\n"
        "class ClienteOpenaiResumen:\n"
        "    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_modelo.py").write_text(
        "def test_placeholder():\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / "README.md").write_text(
        "# proyecto-preexistente\n\nREADME del dueno del proyecto.\n", encoding="utf-8"
    )
    (tmp_path / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")

    if con_wiring:
        (tmp_path / ".pre-commit-config.yaml").write_text(
            "repos:\n  - repo: local\n    hooks: []\n", encoding="utf-8"
        )
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "settings.json").write_text(
            '{"permissions": {"allow": []}}\n', encoding="utf-8"
        )
    return tmp_path
