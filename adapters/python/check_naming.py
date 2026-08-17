"""Adaptador Python: linter de nomenclatura agnostica.

Verifica el principio de nomenclatura agnostica: ningun identificador de Python
en las carpetas de codigo puede contener palabras excluidas que referencien
proveedor, framework UI, formato de almacenamiento o protocolo de auth.

A diferencia del original hardcodeado, la lista de palabras excluidas, los
identificadores permitidos y las palabras relajadas en tests se leen de
`.sdd/config.yaml` (seccion `naming`), de modo que cada proyecto define su
propio vocabulario.

Uso:
    python adapters/python/check_naming.py <root> [<root> ...]

Exit code 0 si todo OK, 1 si hay violaciones, 2 error de argumentos.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from sdd_config import (  # noqa: E402
    declared_test_dirs,
    find_repo_root,
    forzar_salida_utf8,
    load,
)


class _NameCollector(ast.NodeVisitor):
    """Recolecta nombres de clases, funciones, variables y anotaciones."""

    def __init__(self) -> None:
        self.names: list[tuple[str, int]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.names.append((node.name, node.lineno))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.names.append((node.name, node.lineno))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.names.append((node.name, node.lineno))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.names.append((target.id, node.lineno))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.names.append((node.target.id, node.lineno))
        self.generic_visit(node)


def _violations_in_file(
    path: Path,
    *,
    prohibited: tuple[str, ...],
    allowed: frozenset[str],
    relax_tokens: frozenset[str],
    relax_format: bool,
) -> list[tuple[Path, int, str, str]]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    collector = _NameCollector()
    collector.visit(tree)

    violations: list[tuple[Path, int, str, str]] = []
    for name, lineno in collector.names:
        if name in allowed:
            continue
        lowered = name.lower()
        for token in prohibited:
            if relax_format and token in relax_tokens:
                continue
            if token in lowered:
                violations.append((path, lineno, name, token))
                break

    stem_lowered = path.stem.lower()
    for token in prohibited:
        if relax_format and token in relax_tokens:
            continue
        if token in stem_lowered:
            violations.append((path, 0, path.name, token))
            break

    return violations


def _violations_in_dir(
    path: Path,
    *,
    prohibited: tuple[str, ...],
    allowed: frozenset[str],
    relax_tokens: frozenset[str],
    relax_format: bool,
) -> list[tuple[Path, int, str, str]]:
    name = path.name
    if name in allowed:
        return []

    lowered = name.lower()
    for token in prohibited:
        if relax_format and token in relax_tokens:
            continue
        if token in lowered:
            return [(path, 0, path.name, token)]
    return []


def _test_dirs(cfg, repo_root: Path) -> list[Path]:  # type: ignore[no-untyped-def]
    """Directorios de tests declarados en el config, resueltos a rutas absolutas."""
    return [
        (repo_root / cfg.dirs[key]).resolve()
        for key in declared_test_dirs()
        if key in cfg.dirs
    ]


def _is_test_root(root: Path, test_dirs: list[Path]) -> bool:
    """True si `root` es un dir de tests del config, o lo contiene (SPEC-003 FR-002).

    La relacion vale en las **dos** direcciones (SPEC-019 FR-US4-004). Desde que
    los pasos estaticos reciben la raiz que contiene a las carpetas declaradas
    --`tests`, no `tests/unit`--, mirar solo hacia abajo perdia la relajacion:
    `tests` no es relativo a `tests/unit`. Aca lo tapaba el fallback del
    basename, que no es la garantia sino una casualidad del nombre: un proyecto
    con `pruebas/unit` habria dejado de relajar sin que nada lo dijera. Es el
    mismo defecto que B-2 (`docs/IDEAS.md`), que ya se pago una vez comparando
    contra el basename equivocado.

    Fallback para proyectos sin dirs de tests declarados: basename tests/test.
    """
    resolved = root.resolve()
    for test_dir in test_dirs:
        if (
            resolved == test_dir
            or resolved.is_relative_to(test_dir)
            or test_dir.is_relative_to(resolved)
        ):
            return True
    return root.name in {"tests", "test"}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Uso: check_naming.py <root> [<root> ...]", file=sys.stderr)
        return 2

    roots = [Path(a) for a in argv[1:]]
    for root in roots:
        if not root.exists():
            print(f"No existe: {root}", file=sys.stderr)
            return 2

    repo_root = find_repo_root()
    cfg = load(repo_root)
    prohibited = cfg.naming_prohibited
    allowed = cfg.naming_allowed
    relax_tokens = cfg.naming_relax_in_tests
    if not prohibited:
        print(
            "naming: sin palabras excluidas en .sdd/config.yaml (nada que verificar)."
        )
        return 0

    test_dirs = _test_dirs(cfg, repo_root)
    all_violations: list[tuple[Path, int, str, str]] = []
    for root in roots:
        relax = _is_test_root(root, test_dirs)
        for path in root.rglob("*.py"):
            all_violations.extend(
                _violations_in_file(
                    path,
                    prohibited=prohibited,
                    allowed=allowed,
                    relax_tokens=relax_tokens,
                    relax_format=relax,
                )
            )
        for path in root.rglob("*"):
            if path.is_dir():
                all_violations.extend(
                    _violations_in_dir(
                        path,
                        prohibited=prohibited,
                        allowed=allowed,
                        relax_tokens=relax_tokens,
                        relax_format=relax,
                    )
                )

    if not all_violations:
        return 0

    print("Violaciones de nomenclatura agnostica:", file=sys.stderr)
    for path, lineno, name, token in all_violations:
        loc = f"{path}:{lineno}" if lineno else str(path)
        print(
            f"  {loc}  identificador '{name}' contiene palabra excluida '{token}'",
            file=sys.stderr,
        )
    print(
        f"\nTotal: {len(all_violations)} violacion(es). "
        f"Ver specs/SPEC-000-naming.md y la seccion naming de .sdd/config.yaml.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    forzar_salida_utf8()
    sys.exit(main(sys.argv))
