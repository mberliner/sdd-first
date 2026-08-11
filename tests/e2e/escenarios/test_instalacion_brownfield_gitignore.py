"""Instalar sobre un target que ya tiene `.gitignore` propio (SPEC-004 FR-009).

`sdd-init` conserva sin tocar cualquier archivo de `WIRING` que ya exista en
el destino -- el caso realista, porque casi todo proyecto (brownfield, o
greenfield con `git init` que ya genero un `.gitignore` por defecto) tiene uno
antes de correr `sdd-init`. Sin este escenario, el fix de FR-009 solo estaba
probado llamando directo a `sdd_init._copy_text` (unidad interna); esto
ejercita la ruta real -- `sdd_init.py` como subproceso, igual que un
adoptante -- que es la que podria romperse por una regresion en `main()`
(orden de pasos, parseo de argv) sin que la unitaria lo note (ANA-09).
"""

from __future__ import annotations

from pathlib import Path

from ..lib import entorno
from ..lib.aserciones import archivo_dice, espera_exit


def test_instalacion_conserva_el_gitignore_propio_y_le_agrega_current_spec(
    repo: Path,
) -> None:
    gitignore = repo / ".gitignore"
    gitignore.write_text("node_modules/\n*.log\n", encoding="utf-8")

    espera_exit(entorno.instalar(repo))

    texto = archivo_dice(gitignore, "node_modules/", "*.log", ".sdd/current-spec")
    assert texto.startswith("node_modules/\n*.log\n"), (
        f"sdd-init no debio reordenar ni pisar el contenido original:\n{texto}"
    )
