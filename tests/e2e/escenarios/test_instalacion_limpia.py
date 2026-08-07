"""Instalacion en una carpeta vacia: lo que el kit promete apenas termina.

Defectos que este escenario detectaria si volvieran:

- **Falso verde del pipeline** (C-1/C-2/C-5): el veredicto reportaba `VERDE 8/8`
  contando como OK pasos que nunca midio. Aca se afirma que la suma de pasos
  medidos y omitidos cierra contra las secciones realmente ejecutadas.
- **Skills invisibles** ([[SPEC-016-skills-listas-tras-init]]): el mensaje final
  recomendaba `sdd-configure`, una skill que no existia para ningun asistente.
  Aca se afirma que cada skill nombrada esta en los cuatro formatos.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..lib import entorno
from ..lib.aserciones import archivo_dice, dice, espera_exit, existen

SKILLS = ("analyze", "clarify", "sdd-spec", "sdd-doctor", "sdd-configure")

FORMATOS = (
    ".agents/skills/{s}/SKILL.md",  # fuente
    ".claude/skills/{s}/SKILL.md",
    ".opencode/command/{s}.md",
    "docs/playbooks/{s}.md",
)


def test_instalacion_limpia_deja_el_proyecto_operativo(repo: Path) -> None:
    instalacion = espera_exit(entorno.instalar(repo))

    dice(instalacion, "Listo. sdd-first instalado en", f"cd {repo}")
    existen(
        repo,
        "00-INDEX.md",
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        ".sdd/config.yaml",
        ".sdd/current-spec",
        ".pre-commit-config.yaml",
        ".claude/settings.json",
        ".claude/sdd_gate_hook.sh",
        ".opencode/plugin/sdd-gate.js",
        "specs/SPECS_REGISTRY.md",
        "historial/sdd.md",
        "tools/sdd/core/pipeline.py",
        "tools/sdd/adapters/python/adapter.py",
    )

    # Cada skill que el mensaje final nombra tiene que existir de verdad, en
    # los cuatro formatos que el kit dice instalar.
    dice(instalacion, *SKILLS)
    existen(repo, *(f.format(s=s) for s in SKILLS for f in FORMATOS))

    espera_exit(entorno.herramienta(repo, "render"))
    existen(
        repo, "CONSTITUTION.md", "specs/SPEC-000-naming.md", ".github/workflows/ci.yml"
    )
    espera_exit(
        entorno.herramienta(repo, "render", "--check"),
        porque="recien generado, no puede haber drift",
    )

    veredicto = espera_exit(entorno.pipeline(repo))
    _veredicto_sin_pasos_inventados(veredicto)

    salud = espera_exit(entorno.herramienta(repo, "sdd_doctor"))
    dice(salud, "Instalación SDD sana")


def _veredicto_sin_pasos_inventados(res) -> None:  # type: ignore[no-untyped-def]
    """Cada paso ejecutado se reporta medido u omitido, y el resumen los cuenta.

    El falso verde original salia justamente de que el resumen contaba pasos
    que el pipeline nunca habia corrido.
    """
    secciones = re.findall(r"^--- (\S+) ---$", res.salida, flags=re.MULTILINE)
    medidos = res.salida.count("[OK]")
    omitidos = res.salida.count("[OMITIDO]")
    fallidos = res.salida.count("[FALLO]")
    assert secciones, f"el pipeline no reporto ningun paso{res.detalle()}"
    assert medidos + omitidos + fallidos == len(secciones), (
        f"{len(secciones)} pasos ejecutados pero {medidos} OK + {omitidos} omitidos"
        f" + {fallidos} fallidos reportados{res.detalle()}"
    )
    dice(res, "VERDE", f"{medidos}/{medidos} pasos OK")
    if omitidos:
        dice(res, f"Omitidos ({omitidos}, no verificados)")


def test_el_config_sembrado_es_el_ssot_del_proyecto(repo: Path) -> None:
    """El nombre del proyecto sale del destino, no de un valor hardcodeado."""
    espera_exit(entorno.instalar(repo))
    archivo_dice(repo / ".sdd" / "config.yaml", f"name: {repo.name}")
