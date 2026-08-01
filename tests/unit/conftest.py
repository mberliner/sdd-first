"""Hace importables los módulos del núcleo y del adaptador python en los tests."""

import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[2]
for extra in (KIT_ROOT / "core", KIT_ROOT / "adapters" / "python"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))
