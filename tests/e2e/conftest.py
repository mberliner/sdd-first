"""Fixtures de la suite e2e: workspace, repositorio y derivado instalado.

Se corre con `pytest tests/e2e` y no con `pytest` a secas: `testpaths` en
`pyproject.toml` apunta solo a `tests/unit`, que es el unico mecanismo de
seleccion de la suite (SPEC-018 FR-US2-003/FR-US2-004).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from .lib import entorno
from .lib.aserciones import espera_exit, omitir_o_fallar


@pytest.fixture(scope="session")
def workspace() -> Path:
    """Workspace efimero, regenerado una vez al inicio de la corrida."""
    if not entorno.hay_git():
        pytest.fail("la suite e2e necesita `git` en el PATH")
    return entorno.rehacer()


@pytest.fixture
def destino(request: pytest.FixtureRequest, workspace: Path) -> Path:
    """Carpeta vacia propia del escenario, nombrada como el test."""
    nombre = re.sub(r"[^A-Za-z0-9_.-]", "_", request.node.name)
    return entorno.nuevo_destino(workspace, nombre)


@pytest.fixture
def repo(destino: Path) -> Path:
    """`destino` con un repositorio git inicializado y deterministico."""
    entorno.inicializar_git(destino)
    return destino


@pytest.fixture
def derivado(repo: Path) -> Path:
    """Proyecto con el kit instalado y los artefactos generados.

    Incluye `render.py` porque es el paso 2 del flujo que el propio instalador
    prescribe, y sin el ningun commit pasa: el registro de specs sembrado
    referencia `specs/SPEC-000-naming.md`, que genera `render`, y el hook de
    trazabilidad bloquea mientras falte.

    Los escenarios que verifican *que dice* el instalador llaman a
    `entorno.instalar` ellos mismos; este fixture es para los que necesitan un
    derivado listo como punto de partida.
    """
    espera_exit(entorno.instalar(repo), porque="instalacion base del escenario")
    espera_exit(entorno.herramienta(repo, "render"), porque="paso 2 del flujo")
    return repo


@pytest.fixture
def derivado_con_hooks(derivado: Path) -> Path:
    """Derivado con los hooks git cableados, o escenario omitido con motivo."""
    motivo = entorno.preparar_hooks(derivado)
    if motivo:
        omitir_o_fallar(motivo)
    return derivado
