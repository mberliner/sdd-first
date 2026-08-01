"""Dispatcher del adaptador de lenguaje Python.

Contrato de adaptador (ver adapters/CONTRACT.md): expone los pasos de validacion
de codigo que el pipeline delega al lenguaje activo. Cada paso corre una tool del
ecosistema Python y respeta el contrato exit 0 = OK / exit != 0 = falla.

    python adapters/python/adapter.py <step>

Pasos: naming | layers | lint | format | types | security | tests

El pipeline agnostico (core/pipeline.py) invoca `adapter.py <step>` para cada paso
de codigo declarado en pipeline.steps. Los pasos de proceso (constitution,
traceability, skills) los corre el nucleo directamente, no el adaptador.

Omisiones con aviso (exit 0), para que una instalacion fresca no arranque en
ROJO (SPEC-003 FR-001/FR-004):
  - paso sin targets existentes (proyecto todavia sin codigo);
  - paso cuya tool no esta instalada (ruff/mypy/bandit/pytest/import-linter).
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess  # nosec B404 - orquesta linters del proyecto, sin input externo
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "core"))
from sdd_config import find_repo_root, load  # noqa: E402


def _run(cmd: list[str], cwd: Path) -> int:
    print(f"    $ {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(cwd))  # nosec B603 - comandos fijos del adaptador


def _module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _skip(reason: str) -> int:
    print(f"    (omitido: {reason})")
    return 0


def _source_and_test_dirs(cfg) -> tuple[list[str], list[str]]:  # type: ignore[no-untyped-def]
    src = cfg.source_roots
    tests = [
        cfg.dirs[k] for k in ("tests_unit", "tests_integration") if k in cfg.dirs
    ] or ["tests"]
    return src, tests


def _existing_targets(repo_root: Path, dirs: list[str]) -> list[str]:
    return [d for d in dirs if (repo_root / d).exists()]


def step_naming(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    src, tests = _source_and_test_dirs(cfg)
    targets = _existing_targets(repo_root, [*src, *tests])
    if not targets:
        return _skip("sin carpetas de codigo todavia, paso 'naming'")
    return _run([sys.executable, str(HERE / "check_naming.py"), *targets], repo_root)


def step_layers(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    if shutil.which("lint-imports") is None:
        return _skip(
            "tool 'lint-imports' no instalada (pip install import-linter), paso 'layers'"
        )
    # Regenera .importlinter desde config y corre lint-imports.
    gen = _run([sys.executable, str(HERE / "gen_import_linter.py")], repo_root)
    if gen != 0:
        return gen
    return _run(["lint-imports"], repo_root)


def step_lint(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    if not _module_available("ruff"):
        return _skip("tool 'ruff' no instalada (pip install ruff), paso 'lint'")
    src, tests = _source_and_test_dirs(cfg)
    targets = _existing_targets(repo_root, [*src, *tests])
    if not targets:
        return _skip("sin carpetas de codigo todavia, paso 'lint'")
    return _run([sys.executable, "-m", "ruff", "check", *targets], repo_root)


def step_format(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    if not _module_available("ruff"):
        return _skip("tool 'ruff' no instalada (pip install ruff), paso 'format'")
    src, tests = _source_and_test_dirs(cfg)
    targets = _existing_targets(repo_root, [*src, *tests])
    if not targets:
        return _skip("sin carpetas de codigo todavia, paso 'format'")
    return _run(
        [sys.executable, "-m", "ruff", "format", "--check", *targets], repo_root
    )


def step_types(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    if not _module_available("mypy"):
        return _skip("tool 'mypy' no instalada (pip install mypy), paso 'types'")
    src = _existing_targets(repo_root, cfg.source_roots)
    if not src:
        return _skip("sin carpetas de codigo todavia, paso 'types'")
    return _run([sys.executable, "-m", "mypy", "--strict", *src], repo_root)


def step_security(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    if not _module_available("bandit"):
        return _skip("tool 'bandit' no instalada (pip install bandit), paso 'security'")
    src = _existing_targets(repo_root, cfg.source_roots)
    if not src:
        return _skip("sin carpetas de codigo todavia, paso 'security'")
    return _run([sys.executable, "-m", "bandit", "-r", *src, "-q"], repo_root)


def step_tests(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    if not _module_available("pytest"):
        return _skip("tool 'pytest' no instalada (pip install pytest), paso 'tests'")
    unit = cfg.dirs.get("tests_unit", "tests/unit")
    if not (repo_root / unit).exists():
        return _skip(f"sin carpeta de tests '{unit}' todavia, paso 'tests'")
    return _run([sys.executable, "-m", "pytest", unit, "-q"], repo_root)


STEPS = {
    "naming": step_naming,
    "layers": step_layers,
    "lint": step_lint,
    "format": step_format,
    "types": step_types,
    "security": step_security,
    "tests": step_tests,
}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in STEPS:
        print(f"Uso: adapter.py <{' | '.join(STEPS)}>", file=sys.stderr)
        return 2
    repo_root = find_repo_root()
    cfg = load(repo_root)
    return STEPS[argv[0]](repo_root, cfg)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
