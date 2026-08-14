"""El aviso del gate sobrevive al transporte de pre-commit (SPEC-017 FR-US3-007).

Origen: V-2 de `docs/IDEAS.md`. FR-US3-004 exige que un bypass deje su motivo en
stderr, y los unitarios del gate lo verifican. Pero en el flujo real el gate corre
como hook de `pre-commit`, que **descarta la salida de los hooks que pasan**; con
`SDD_GATE_BYPASS` el gate sale exit 0, o sea que se tragaba justo el caso que el
requisito queria hacer visible.

Se verifica sobre la plantilla, que desde SPEC-005 FR-008 es el unico archivo:
el `.pre-commit-config.yaml` del kit se genera desde ella y `render --check`
vigila que no diverja. Verificar tambien la copia generada seria testear el
render dos veces, no el wiring.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

KIT_ROOT = Path(__file__).resolve().parents[2]

PRE_COMMIT = [
    KIT_ROOT / "templates" / "wiring" / ".pre-commit-config.yaml",
]


def _hook(ruta: Path, hook_id: str) -> dict:
    config = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    for repo in config["repos"]:
        for hook in repo["hooks"]:
            if hook["id"] == hook_id:
                return hook
    raise AssertionError(f"{ruta} no declara el hook '{hook_id}'")


@pytest.mark.parametrize("ruta", PRE_COMMIT, ids=lambda p: p.parent.name)
def test_el_hook_del_gate_muestra_su_salida_aunque_pase(ruta):
    """FR-US3-007: sin `verbose`, un bypass es indistinguible de un commit normal."""
    assert _hook(ruta, "sdd-gate").get("verbose") is True, (
        f"{ruta}: el hook sdd-gate necesita `verbose: true` o pre-commit se traga "
        "el aviso de SDD_GATE_BYPASS (solo muestra 'Passed')"
    )


@pytest.mark.parametrize("ruta", PRE_COMMIT, ids=lambda p: p.parent.name)
def test_los_demas_hooks_no_piden_verbose(ruta):
    """`verbose` se justifica por lo que el gate imprime al permitir; el resto no.

    Ponerlo en todos convertiria cada commit en un muro de texto y le quitaria al
    aviso del gate justamente lo que lo hace notorio.
    """
    for hook_id in ("sdd-traceability", "sdd-reset"):
        assert "verbose" not in _hook(ruta, hook_id)


def test_el_gate_no_escribe_nada_cuando_no_hay_nada_que_bloquear(tmp_path):
    """La premisa que hace barato a `verbose`: el camino feliz es mudo.

    Si el gate imprimiera en cada corrida, `verbose: true` llenaria de ruido todos
    los commits y el requisito habria que resolverlo de otra forma.
    """
    afuera = tmp_path / "suelto.py"
    afuera.write_text("x = 1\n", encoding="utf-8")

    proceso = subprocess.run(
        [sys.executable, str(KIT_ROOT / "core" / "sdd_gate.py"), str(afuera)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert proceso.returncode == 0
    assert proceso.stdout == ""
    assert proceso.stderr == ""
