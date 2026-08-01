"""Post-commit reset de .sdd/current-spec (gate spec-first, Principio III).

Limpia las specs declaradas tras cada commit exitoso, dejando solo el header
de comentarios. Fuerza declaracion explicita al inicio de la proxima iteracion,
evitando reutilizacion silenciosa de una spec de sesion anterior.

Wiring: hook post-commit en .pre-commit-config.yaml (stages: [post-commit]).
Requiere instalacion explicita: pre-commit install --hook-type post-commit
(automatizado por core/bootstrap_hooks.py). Ver docs/SDD-ENFORCEMENT.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sdd_config import find_repo_root  # noqa: E402


def main() -> int:
    repo_root = find_repo_root()
    path = repo_root / ".sdd" / "current-spec"
    if not path.exists():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    comments = [ln for ln in lines if ln.startswith("#")]
    path.write_text("\n".join(comments) + "\n", encoding="utf-8")
    print(
        "sdd-reset: .sdd/current-spec limpiado — declara una spec antes de editar codigo."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
