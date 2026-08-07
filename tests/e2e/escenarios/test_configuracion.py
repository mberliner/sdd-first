"""Reconfigurar el derivado: el config es el SSOT y todo lo derivado lo obedece.

Verifica la promesa central del kit —"cambiar `.sdd/config.yaml` cambia lo que
el pipeline verifica y lo que el gate protege"—: no alcanza con que `render.py`
reescriba archivos, tiene que cambiar el **veredicto** sobre el mismo codigo.
"""

from __future__ import annotations

from pathlib import Path

from ..lib import entorno
from ..lib.aserciones import archivo_dice, dice, espera_exit, no_dice

PALABRA = "planilla"


def _reconfigurar(destino: Path) -> None:
    """Declara la carpeta de codigo y una palabra excluida propia."""
    config = destino / ".sdd" / "config.yaml"
    texto = config.read_text(encoding="utf-8")
    texto = texto.replace("  # source_roots: [src]", "  source_roots: [nucleo]")
    texto = texto.replace("  prohibited:\n", f"  prohibited:\n    - {PALABRA}\n")
    config.write_text(texto, encoding="utf-8")


def _sembrar_violacion(destino: Path) -> None:
    nucleo = destino / "nucleo"
    nucleo.mkdir(exist_ok=True)
    (nucleo / "reporte.py").write_text(
        "def exportar_planilla(datos):\n    return datos\n", encoding="utf-8"
    )


def test_el_config_gobierna_los_artefactos_y_el_veredicto(derivado: Path) -> None:
    _sembrar_violacion(derivado)
    espera_exit(
        entorno.paso(derivado, "naming"),
        3,
        porque="antes de declarar dirs, `nucleo/` no la mira nadie",
    )

    _reconfigurar(derivado)

    espera_exit(entorno.herramienta(derivado, "render"))
    archivo_dice(derivado / "specs" / "SPEC-000-naming.md", PALABRA)
    archivo_dice(derivado / ".github" / "workflows" / "ci.yml", '- "nucleo/**"')
    espera_exit(
        entorno.herramienta(derivado, "render", "--check"),
        porque="recien regenerado, no puede haber drift",
    )

    # El veredicto sobre el mismo codigo cambia por el config y por nada mas.
    naming = entorno.paso(derivado, "naming")
    espera_exit(naming, 1, porque=f"'{PALABRA}' quedo declarada como palabra excluida")
    dice(naming, PALABRA, "reporte.py")


def test_el_gate_sigue_al_config_sin_tocar_el_wiring(derivado: Path) -> None:
    """Las tres capas derivan los roots del config (SPEC-015): cambiar el config alcanza."""
    espera_exit(
        entorno.herramienta(derivado, "sdd_gate", "nucleo/reporte.py"),
        0,
        porque="antes de declararla, `nucleo/` no es codigo fuente",
    )

    _reconfigurar(derivado)

    bloqueado = entorno.herramienta(derivado, "sdd_gate", "nucleo/reporte.py")
    espera_exit(bloqueado, 2, porque="ahora `nucleo/` esta declarada y no hay spec")
    no_dice(bloqueado, "src/")
