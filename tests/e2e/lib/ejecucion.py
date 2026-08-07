"""Ejecucion de comandos del proyecto derivado, con la salida capturada entera.

Los tests unitarios que levantan proyectos temporales ya usan este patron
(`tests/unit/test_sdd_init_skills.py`, `test_install_brownfield.py`); aca esta
centralizado porque la suite e2e lo hace en cada paso y porque un fallo tiene
que poder mostrar *que* imprimio el comando, no solo con que codigo salio
(SPEC-018 FR-US1-002).
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - la suite orquesta el propio kit
import sys
from dataclasses import dataclass
from pathlib import Path

TIMEOUT_DEFECTO = 300


@dataclass(frozen=True)
class Resultado:
    """Lo que dejo un comando: como salio y que dijo."""

    comando: list[str]
    cwd: Path
    exit: int
    salida: str

    @property
    def descripcion(self) -> str:
        return f"{' '.join(self.comando)}  (cwd={self.cwd})"

    def detalle(self) -> str:
        """Bloque para el mensaje de un assert fallido."""
        cuerpo = self.salida.rstrip() or "(sin salida)"
        return f"\n$ {self.descripcion}\nexit={self.exit}\n--- salida ---\n{cuerpo}\n"


def _entorno(overrides: dict[str, str] | None) -> dict[str, str]:
    """Entorno del hijo: el del proceso menos las variables SDD del kit.

    La suite corre *dentro* del repositorio del kit, cuyo entorno puede traer
    `SDD_GATE_BYPASS` u otras variables que cambiarian la decision del derivado
    sin que el escenario lo pida. Se limpian y cada escenario declara las que
    necesita.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("SDD_")}
    # Salida del hijo siempre en utf-8: sin esto Windows la emite en la
    # codificacion de consola y los mensajes con acentos llegan rotos.
    env["PYTHONIOENCODING"] = "utf-8"
    if overrides:
        env.update(overrides)
    return env


def correr(
    comando: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    timeout: int = TIMEOUT_DEFECTO,
) -> Resultado:
    """Corre `comando` en `cwd` y devuelve exit + salida (stdout y stderr juntos).

    Nunca levanta por codigo de salida: el codigo es el dato que el escenario
    va a afirmar. Un timeout si es fallo del harness y se reporta como tal.
    """
    try:
        proceso = subprocess.run(  # nosec B603 - comandos armados por la suite
            comando,
            cwd=str(cwd),
            env=_entorno(env),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        parcial = (exc.stdout or "") + (exc.stderr or "")
        return Resultado(comando, cwd, 124, f"{parcial}\n[timeout tras {timeout}s]")
    return Resultado(comando, cwd, proceso.returncode, proceso.stdout + proceso.stderr)


def correr_python(
    modulo_o_script: str | Path,
    cwd: Path,
    *args: str,
    env: dict[str, str] | None = None,
    timeout: int = TIMEOUT_DEFECTO,
) -> Resultado:
    """Corre un script con el mismo interprete que la suite."""
    return correr(
        [sys.executable, str(modulo_o_script), *args], cwd, env=env, timeout=timeout
    )
