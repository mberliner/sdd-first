"""Aserciones sobre resultados de comandos, con el mensaje que hace falta.

Regla de la suite (SPEC-018 FR-US1-002): las expectativas miran **contenido**,
no solo codigos de salida. El peor hallazgo de la campana manual fue un
`sdd-doctor` que decia "Instalacion SDD sana" con cero capas de gate activas y
salia exit 0: un `assert res.exit == 0` lo habria dado por bueno.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from .ejecucion import Resultado

VAR_ESTRICTO = "SDD_E2E_STRICT"


def espera_exit(res: Resultado, esperado: int = 0, *, porque: str = "") -> Resultado:
    """Afirma el codigo de salida mostrando la salida completa si falla."""
    if res.exit != esperado:
        motivo = f" ({porque})" if porque else ""
        pytest.fail(
            f"se esperaba exit {esperado} y salio {res.exit}{motivo}{res.detalle()}"
        )
    return res


def dice(res: Resultado, *fragmentos: str) -> Resultado:
    """Afirma que la salida contiene cada fragmento."""
    faltantes = [f for f in fragmentos if f not in res.salida]
    if faltantes:
        listado = "\n".join(f"  - {f!r}" for f in faltantes)
        pytest.fail(f"la salida no dice:\n{listado}{res.detalle()}")
    return res


def no_dice(res: Resultado, *fragmentos: str) -> Resultado:
    """Afirma que la salida no contiene ninguno de los fragmentos."""
    presentes = [f for f in fragmentos if f in res.salida]
    if presentes:
        listado = "\n".join(f"  - {f!r}" for f in presentes)
        pytest.fail(f"la salida dice lo que no debia:\n{listado}{res.detalle()}")
    return res


def archivo_dice(ruta: Path, *fragmentos: str) -> str:
    """Afirma que un archivo existe y contiene cada fragmento."""
    if not ruta.exists():
        pytest.fail(f"falta el archivo {ruta}")
    texto = ruta.read_text(encoding="utf-8")
    faltantes = [f for f in fragmentos if f not in texto]
    if faltantes:
        listado = "\n".join(f"  - {f!r}" for f in faltantes)
        pytest.fail(f"{ruta} no dice:\n{listado}\n--- contenido ---\n{texto}\n")
    return texto


def existen(raiz: Path, *rutas: str) -> None:
    """Afirma que cada ruta relativa existe bajo `raiz`, listando las que no."""
    faltantes = [r for r in rutas if not (raiz / r).exists()]
    if faltantes:
        listado = "\n".join(f"  - {r}" for r in faltantes)
        pytest.fail(f"faltan archivos bajo {raiz}:\n{listado}")


def modo_estricto() -> bool:
    """`SDD_E2E_STRICT` no vacia convierte las omisiones por entorno en fallos."""
    return bool(os.environ.get(VAR_ESTRICTO, "").strip())


def omitir_o_fallar(motivo: str) -> None:
    """Degradado por entorno incompleto (SPEC-018 FR-US1-005).

    Sin la herramienta el escenario se omite **nombrando que falto**, para que
    la suite corra offline y en maquinas sin el entorno preparado. En CI, que
    setea `SDD_E2E_STRICT`, la misma condicion es fallo: el degradado no puede
    convertirse en un verde silencioso justo donde importa.
    """
    if modo_estricto():
        pytest.fail(f"{motivo} (con {VAR_ESTRICTO} la omision es fallo)")
    pytest.skip(motivo)
