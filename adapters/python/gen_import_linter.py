"""Genera un archivo `.importlinter` desde `layers` de .sdd/config.yaml.

import-linter (lint-imports) codifica las capas Clean como "contratos forbidden":
una capa no puede importar de las capas que NO estan en su lista de permitidos.
Este generador traduce el mapa declarativo `layers` del config a esos contratos,
de modo que el proyecto no mantiene la matriz de imports a mano.

Uso:
    python adapters/python/gen_import_linter.py           # escribe .importlinter
    python adapters/python/gen_import_linter.py --check   # falla si hay drift
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from sdd_config import find_repo_root, load, write_text_lf  # noqa: E402


def _module_of(repo_root: Path, layer_path: str) -> str:
    """Convierte 'src/domain' en el modulo importable 'src.domain'."""
    return ".".join(Path(layer_path).parts)


def render(repo_root: Path) -> str:
    cfg = load(repo_root)
    layers = cfg.layers
    dirs = cfg.dirs
    root_package = cfg.source_roots[0] if cfg.source_roots else "src"

    lines: list[str] = [
        "[importlinter]",
        f"root_package = {root_package}",
        "",
    ]
    for layer, allowed in layers.items():
        layer_path = dirs.get(layer, f"{root_package}/{layer}")
        source_mod = _module_of(repo_root, layer_path)
        # forbidden = todas las capas que NO son este ni sus permitidos.
        forbidden = [
            other for other in layers if other != layer and other not in allowed
        ]
        if not forbidden:
            continue
        lines.append("[[importlinter:contract]]")
        lines.append(f"name = {layer} no depende de {', '.join(forbidden)}")
        lines.append("type = forbidden")
        lines.append(f"source_modules =\n    {source_mod}")
        forbidden_mods = "\n    ".join(
            _module_of(repo_root, dirs.get(o, f"{root_package}/{o}")) for o in forbidden
        )
        lines.append(f"forbidden_modules =\n    {forbidden_mods}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    repo_root = find_repo_root()
    target = repo_root / ".importlinter"
    content = render(repo_root)
    if "--check" in argv:
        if target.exists() and target.read_text(encoding="utf-8") == content:
            print(".importlinter sincronizado con layers de config.yaml.")
            return 0
        print(
            ".importlinter desincronizado (corre: python adapters/python/gen_import_linter.py)."
        )
        return 1
    write_text_lf(target, content)
    print(f"Generado {target.name} desde layers de config.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
