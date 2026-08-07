"""Instalacion sobre un proyecto que ya existe: no romper nada y apuntar al codigo real.

Defectos que este escenario detectaria si volvieran:

- **Gate apuntando a una carpeta inventada** (G-1/G-3,
  [[SPEC-015-wiring-apunta-al-codigo-real]]): el wiring protegia `src/` aunque
  el codigo del proyecto viviera en otro lado, asi que el gate no bloqueaba nada.
- **CI que nunca dispara** ([[SPEC-014-derivado-dice-la-verdad]] FR-US2-005): el
  workflow generado hardcodeaba `main` y en un repositorio con otra rama no
  corria jamas.
"""

from __future__ import annotations

from pathlib import Path

from fixtures_proyecto import crear_proyecto_brownfield

from ..lib import entorno
from ..lib.aserciones import archivo_dice, dice, espera_exit

RAMA = "produccion"


def test_instalacion_sobre_proyecto_existente(destino: Path) -> None:
    crear_proyecto_brownfield(destino, layout="app")
    entorno.inicializar_git(destino, rama=RAMA)
    espera_exit(entorno.commitear(destino, "estado previo del proyecto"))

    instalacion = espera_exit(entorno.instalar(destino))
    dice(instalacion, "Layout detectado: codigo en app/")

    # Lo del dueno sigue siendo del dueno.
    archivo_dice(destino / "README.md", "README del dueno del proyecto.")
    archivo_dice(destino / ".gitignore", "__pycache__/")
    archivo_dice(destino / "app" / "servicio.py", "ClienteOpenaiResumen")

    # El config apunta al codigo real, no al `src` del default.
    archivo_dice(destino / ".sdd" / "config.yaml", "source_roots: [app]")

    # Y el gate protege esa carpeta, no otra.
    bloqueado = entorno.herramienta(destino, "sdd_gate", "app/servicio.py")
    espera_exit(bloqueado, 2, porque="sin spec declarada, editar app/ se bloquea")
    espera_exit(
        entorno.herramienta(destino, "sdd_gate", "docs/ARCHITECTURE.md"),
        0,
        porque="docs/ no es codigo fuente",
    )


def test_el_ci_generado_dispara_en_la_rama_real(destino: Path) -> None:
    crear_proyecto_brownfield(destino, layout="app")
    entorno.inicializar_git(destino, rama=RAMA)
    espera_exit(entorno.commitear(destino, "estado previo del proyecto"))
    espera_exit(entorno.instalar(destino))
    espera_exit(entorno.herramienta(destino, "render"))

    archivo_dice(
        destino / ".github" / "workflows" / "ci.yml",
        f"branches: [{RAMA}]",
        '- "app/**"',
    )


def test_el_paso_naming_mira_la_carpeta_detectada(destino: Path) -> None:
    """El senuelo sembrado en `app/` tiene que aparecer: si no, nadie lo miro."""
    crear_proyecto_brownfield(destino, layout="app")
    entorno.inicializar_git(destino, rama=RAMA)
    espera_exit(entorno.instalar(destino))

    naming = entorno.paso(destino, "naming")
    espera_exit(naming, 1, porque="app/servicio.py tiene una palabra excluida")
    dice(naming, "openai", "servicio.py")
