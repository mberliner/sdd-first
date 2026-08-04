"""Hace importables los módulos del núcleo y del adaptador python en los tests."""

import os
import sys
from pathlib import Path

import pytest

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
