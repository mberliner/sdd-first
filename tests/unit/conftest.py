"""Hace importables los módulos del núcleo y del adaptador python en los tests."""

import os
import sys
from pathlib import Path

import pytest
from fixtures_proyecto import crear_proyecto_brownfield

__all__ = ["crear_proyecto_brownfield", "requiere_permisos_posix", "ejecutable_sh"]

KIT_ROOT = Path(__file__).resolve().parents[2]
for extra in (KIT_ROOT / "core", KIT_ROOT / "adapters" / "python"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

# NTFS no expresa los bits de ejecucion de POSIX: `Path.chmod(0o755)` corre sin
# error pero `st_mode` los reporta apagados. Los tests que verifican el *efecto*
# de un chmod se saltan ahi; el que verifica la *intencion* corre siempre
# (SPEC-012 FR-002/FR-004).
SOPORTA_PERMISOS_POSIX = os.name != "nt"

requiere_permisos_posix = pytest.mark.skipif(
    not SOPORTA_PERMISOS_POSIX,
    reason="el sistema de archivos no expresa los bits de ejecucion de POSIX",
)


def ejecutable_sh() -> str:
    """Resuelve el ejecutable sh, incluso en Windows si Git esta instalado."""
    import shutil

    sh = shutil.which("sh")
    if sh:
        return sh
    if os.name == "nt":
        # Buscar en ubicacion comun de Git Bash
        git_sh = Path(r"C:\Program Files\Git\bin\sh.exe")
        if git_sh.exists():
            return str(git_sh)
    return "/bin/sh"
