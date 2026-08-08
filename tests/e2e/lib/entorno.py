"""Entorno efimero de la suite e2e: donde vive, como se regenera, que instala.

Cada escenario trabaja sobre un proyecto real —repositorio git, kit instalado
con `sdd_init` como subproceso, hooks cableados— creado desde cero bajo un
workspace que la suite borra y recrea al **inicio** de la corrida (SPEC-018
FR-US2-002): asi la regeneracion no depende de que la corrida anterior haya
terminado bien, y los artefactos quedan en disco para inspeccionar un fallo.

El workspace **nunca** puede caer dentro del arbol del kit ni contenerlo
(FR-US2-001): `find_sdd_root` resuelve la raiz SDD subiendo por el sistema de
archivos, asi que un destino bajo el kit quedaria gobernado por el gate del kit
en vez del suyo; y un workspace que contenga al kit seria borrado entero por
`rehacer()`.

Fuera del kit el borrado tampoco es incondicional (FR-US2-007): solo se borra lo
que la suite dejo. Un `SDD_E2E_WORK` mal tipeado apunta a una carpeta cualquiera
del disco, y `rehacer()` la borraria entera; por eso la suite siembra una marca
al crear el workspace y se niega a borrar un directorio con contenido que no la
tenga.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess  # nosec B404 - la suite orquesta git y el propio kit
import sys
import tempfile
from pathlib import Path

from .ejecucion import Resultado, correr, correr_python

KIT_ROOT = Path(__file__).resolve().parents[3]
VAR_WORKSPACE = "SDD_E2E_WORK"
NOMBRE_WORKSPACE = "sdd-e2e"
MARCA = ".sdd-e2e-workspace"
TEXTO_MARCA = (
    "Workspace efimero de la suite e2e de sdd-first.\n"
    "Esta marca autoriza a la suite a borrar esta carpeta entera al inicio de la\n"
    "corrida siguiente. Si borras la marca, la suite se niega a tocar la carpeta.\n"
)
VENDOR = "tools/sdd"
RAMA_DEFECTO = "main"

# `pre-commit install` puede construir su entorno la primera vez, y los commits
# con hooks corren el pipeline del derivado: margen mas ancho que el default.
TIMEOUT_HOOKS = 600


class WorkspaceInvalido(RuntimeError):
    """El workspace pedido se solapa con el arbol del kit."""


def raiz_de_trabajo() -> Path:
    """Resuelve el workspace y verifica que no se solape con el kit."""
    crudo = os.environ.get(VAR_WORKSPACE, "").strip()
    raiz = (
        Path(crudo).expanduser().resolve()
        if crudo
        else Path(tempfile.gettempdir()).resolve() / NOMBRE_WORKSPACE
    )
    verificar_fuera_del_kit(raiz)
    return raiz


def verificar_fuera_del_kit(raiz: Path) -> None:
    """Aborta si `raiz` esta dentro del kit, es el kit, o lo contiene."""
    if raiz == KIT_ROOT:
        raise WorkspaceInvalido(
            f"el workspace e2e es la raiz del kit ({KIT_ROOT}); "
            f"eleji otro con {VAR_WORKSPACE}"
        )
    if KIT_ROOT in raiz.parents:
        raise WorkspaceInvalido(
            f"el workspace e2e ({raiz}) cae dentro del kit ({KIT_ROOT}): "
            "el gate del kit gobernaria los proyectos de prueba"
        )
    if raiz in KIT_ROOT.parents:
        raise WorkspaceInvalido(
            f"el workspace e2e ({raiz}) contiene al kit ({KIT_ROOT}): "
            "regenerarlo borraria el repositorio"
        )


def verificar_borrable(raiz: Path) -> None:
    """Aborta si `raiz` tiene contenido que no dejo la suite (FR-US2-007).

    Se borra lo que no existe, lo que esta vacio y lo que lleva la marca. Todo
    lo demas es de otro: la suite se detiene antes de tocarlo.
    """
    if not raiz.exists():
        return
    if not raiz.is_dir():
        raise WorkspaceInvalido(f"el workspace e2e ({raiz}) no es un directorio")
    if (raiz / MARCA).exists() or not any(raiz.iterdir()):
        return
    raise WorkspaceInvalido(
        f"el workspace e2e ({raiz}) ya tiene contenido y no lleva la marca "
        f"{MARCA}: no lo dejo esta suite y regenerarlo lo borraria entero. "
        f"Eleji una carpeta vacia o inexistente con {VAR_WORKSPACE}."
    )


def _forzar_escritura(func, path, _exc):  # type: ignore[no-untyped-def]
    """Reintento de borrado para los archivos de solo lectura de `.git`."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def borrar(ruta: Path) -> None:
    """Borra un arbol, incluidos los archivos de solo lectura que deja git."""
    if not ruta.exists():
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(ruta, onexc=_forzar_escritura)
    else:  # pragma: no cover - rama para interpretes viejos
        shutil.rmtree(ruta, onerror=_forzar_escritura)


def rehacer(raiz: Path | None = None) -> Path:
    """Deja el workspace vacio, existente y marcado. Se llama una vez por corrida."""
    raiz = raiz or raiz_de_trabajo()
    verificar_fuera_del_kit(raiz)
    verificar_borrable(raiz)
    borrar(raiz)
    raiz.mkdir(parents=True)
    (raiz / MARCA).write_text(TEXTO_MARCA, encoding="utf-8")
    return raiz


def nuevo_destino(raiz: Path, nombre: str) -> Path:
    """Carpeta limpia para un escenario, dentro del workspace."""
    destino = raiz / nombre
    borrar(destino)
    destino.mkdir(parents=True)
    return destino


def instalar(destino: Path, language: str = "python", *extra: str) -> Resultado:
    """Instala el kit en `destino` como lo haria un adoptante.

    Invoca `core/sdd_init.py` **como subproceso desde el clon del kit**
    (FR-US1-001) y no importando el modulo: lo que se verifica es el producto
    tal como se ejecuta, incluido lo que imprime.
    """
    destino.mkdir(parents=True, exist_ok=True)
    return correr_python(
        KIT_ROOT / "core" / "sdd_init.py",
        KIT_ROOT,
        str(destino),
        f"--language={language}",
        *extra,
    )


def git(destino: Path, *args: str, timeout: int = 120) -> Resultado:
    return correr(["git", *args], destino, timeout=timeout)


def inicializar_git(destino: Path, rama: str = RAMA_DEFECTO) -> None:
    """Repositorio git usable y deterministico para un escenario.

    La identidad y la firma se fijan **locales al repositorio**: la suite no
    puede depender de la configuracion global de quien la corra, ni dejarla
    tocada. La rama se fuerza para que `sdd_init` siembre siempre el mismo
    `default_branch` (SPEC-014 FR-US2-005).
    """
    correr(["git", "-c", f"init.defaultBranch={rama}", "init"], destino, timeout=120)
    for clave, valor in (
        ("user.email", "e2e@sdd-first.invalid"),
        ("user.name", "Suite e2e"),
        ("commit.gpgsign", "false"),
        ("core.autocrlf", "false"),
    ):
        git(destino, "config", clave, valor)


def commitear(destino: Path, mensaje: str, *, env: dict[str, str] | None = None):
    """`git add -A` + `git commit`, con los hooks que haya instalados."""
    git(destino, "add", "-A")
    return correr(
        ["git", "commit", "-m", mensaje],
        destino,
        env=env,
        timeout=TIMEOUT_HOOKS,
    )


def preparar_hooks(destino: Path) -> str | None:
    """Cablea los hooks git con el propio paso del kit (`bootstrap_hooks`).

    Devuelve `None` si quedaron instalados, o el motivo por el que no se pudo
    —falta `pre-commit`, o su entorno no se pudo construir— para que el
    escenario decida omitirse o fallar segun `SDD_E2E_STRICT`.
    """
    res = correr_python(
        Path(VENDOR) / "core" / "bootstrap_hooks.py", destino, timeout=TIMEOUT_HOOKS
    )
    if res.exit == 0:
        return None
    return (
        f"no se pudieron cablear los hooks de pre-commit en el derivado{res.detalle()}"
    )


def pipeline(destino: Path, *args: str) -> Resultado:
    return correr_python(
        Path(VENDOR) / "core" / "pipeline.py", destino, *args, timeout=TIMEOUT_HOOKS
    )


def herramienta(destino: Path, nombre: str, *args: str) -> Resultado:
    """Corre un script del kit vendorizado en el derivado (`tools/sdd/core/<nombre>.py`)."""
    return correr_python(Path(VENDOR) / "core" / f"{nombre}.py", destino, *args)


def correr_gate(
    destino: Path, *rutas: str, env: dict[str, str] | None = None
) -> Resultado:
    """Invoca el gate del derivado sobre rutas concretas, con env propio."""
    return correr_python(
        Path(VENDOR) / "core" / "sdd_gate.py", destino, *rutas, env=env
    )


def paso(destino: Path, nombre: str, language: str = "python") -> Resultado:
    """Corre un paso del adaptador de lenguaje, como lo invoca el pipeline.

    Se prefiere sobre llamar al checker con una ruta explicita: asi el escenario
    verifica tambien que el paso derive sus carpetas del config, que es la
    promesa que interesa.
    """
    return correr_python(
        Path(VENDOR) / "adapters" / language / "adapter.py",
        destino,
        nombre,
        timeout=TIMEOUT_HOOKS,
    )


def hay_git() -> bool:
    """`git` disponible: sin el no hay escenario posible (SPEC-018, Assumptions)."""
    return shutil.which("git") is not None


def hay_pre_commit() -> bool:
    """El paquete `pre_commit` importable con el interprete de la suite."""
    res = subprocess.run(  # nosec B603 - comando fijo
        [sys.executable, "-c", "import pre_commit"],
        capture_output=True,
    )
    return res.returncode == 0
