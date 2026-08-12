"""`sdd-update` sobre un derivado real: no pisa lo editado, deja `.kit-new`.

SPEC-025 US2/US3, FR-US2-009. Defecto que este escenario detectaria si
volviera: la única ruta de actualización existente antes de esta spec
(`sdd-init --force`) pisaba/borraba lo que el dueño había escrito
(`specs/SPECS_REGISTRY.md`, `historial/sdd.md`, plantillas editadas) sin
avisar. Esta capacidad no se puede afirmar con unitarios solos porque su
objeto es un proyecto instalado que "envejeció" (una plantilla editada a
mano, un registro con filas propias) y un comando que se corre **desde el
clon del kit**, apuntando a él — la e2e es la única que ejercita esa ruta de
verdad (subprocess real, no un import).
"""

from __future__ import annotations

from pathlib import Path

from ..lib import entorno
from ..lib.aserciones import archivo_dice, dice, espera_exit

RAMA = "main"


def test_actualizar_no_pisa_lo_editado_y_deja_kit_new(destino: Path) -> None:
    entorno.inicializar_git(destino, rama=RAMA)
    espera_exit(entorno.instalar(destino))
    espera_exit(entorno.herramienta(destino, "render"))
    espera_exit(entorno.commitear(destino, "instalacion inicial"))

    # El dueño adapta una plantilla y agrega una fila propia al registro.
    agents = destino / "AGENTS.md"
    original_agents = agents.read_text(encoding="utf-8")
    agents.write_text(
        original_agents + "\n## Nota propia del equipo\n", encoding="utf-8"
    )
    registro = destino / "specs" / "SPECS_REGISTRY.md"
    original_registro = registro.read_text(encoding="utf-8")
    registro.write_text(
        original_registro + "\n<!-- fila propia -->\n", encoding="utf-8"
    )

    plan = espera_exit(entorno.actualizar(destino))
    dice(plan, "conflicto:", "AGENTS.md")

    aplicado = espera_exit(entorno.actualizar(destino, "--apply"))
    dice(aplicado, "Actualización aplicada")

    # Lo editado no se pisó, y quedó la version del kit al lado.
    archivo_dice(agents, "## Nota propia del equipo")
    assert (destino / "AGENTS.md.kit-new").exists()

    # El registro con la fila propia, intacto: es `semilla`.
    archivo_dice(registro, "<!-- fila propia -->")

    # Un archivo no tocado no genera conflicto ni ruido.
    dice(plan, "README.md")

    # El lock quedó reescrito con la versión vigente del kit.
    lock = destino / ".sdd" / "kit.lock"
    assert lock.exists()

    # sdd-doctor sobre el resultado no reporta problemas nuevos.
    doctor = espera_exit(entorno.herramienta(destino, "sdd_doctor"))
    dice(doctor, "kit_version instalada")
