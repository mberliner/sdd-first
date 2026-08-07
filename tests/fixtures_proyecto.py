"""Testigos de proyecto que usan las suites unitaria y e2e.

SSOT unico del proyecto preexistente (Principio IV): la suite unitaria lo usa
para verificar decisiones de `sdd_init`, la e2e para instalar el kit encima y
recorrer el ciclo completo. Vive en `tests/` y no en una de las dos suites para
que ninguna dependa de la otra.
"""

from pathlib import Path


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
