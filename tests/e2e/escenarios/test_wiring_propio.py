"""Proyecto con wiring propio: el kit conserva lo que hay y lo dice en voz alta.

Defecto que este escenario detectaria si volviera (G-4,
[[SPEC-014-derivado-dice-la-verdad]]): `sdd-doctor` verificaba que los archivos
de wiring **existieran**, no que invocaran al gate. Con el
`.pre-commit-config.yaml` y el `settings.json` del dueno intactos —sin una sola
capa de enforcement activa— reportaba "Instalacion SDD sana" y salia exit 0.
"""

from __future__ import annotations

from pathlib import Path

from fixtures_proyecto import crear_proyecto_brownfield

from ..lib import entorno
from ..lib.aserciones import dice, espera_exit, no_dice


def test_el_wiring_del_dueno_se_conserva_y_el_doctor_no_miente(destino: Path) -> None:
    crear_proyecto_brownfield(destino, layout="app", con_wiring=True)
    entorno.inicializar_git(destino)

    instalacion = espera_exit(entorno.instalar(destino))
    dice(instalacion, "(existe, se conserva)")
    # El aviso no puede quedar sepultado entre las treinta lineas del log, y
    # tiene que nombrar cada archivo conservado con lo que deberia invocar.
    dice(
        instalacion,
        "ATENCION: se conservo el wiring que ya tenias",
        ".claude/settings.json (deberia invocar sdd_gate_hook.sh)",
        ".pre-commit-config.yaml (deberia invocar sdd_gate.py)",
    )

    # Se regenera primero para que los unicos problemas que queden sean los del
    # wiring: si el doctor los tapara con drift, la asercion no probaria nada.
    espera_exit(entorno.herramienta(destino, "render"))

    salud = entorno.herramienta(destino, "sdd_doctor")
    espera_exit(salud, 1, porque="ninguna capa del gate esta cableada")
    no_dice(salud, "Instalación SDD sana")
    dice(
        salud,
        "Gate no cableado: .claude/settings.json existe pero no invoca sdd_gate_hook.sh",
        "Gate no cableado: .pre-commit-config.yaml existe pero no invoca sdd_gate.py",
        "Total: 2 problema(s)",
    )
