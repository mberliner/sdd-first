"""Dispatcher del adaptador de lenguaje Python.

Contrato de adaptador (ver adapters/CONTRACT.md): expone los pasos de validacion
de codigo que el pipeline delega al lenguaje activo. Cada paso corre una tool del
ecosistema Python y respeta el contrato de tres estados:
exit 0 = OK / exit 3 = omitido (no se pudo verificar) / otro = falla.

    python adapters/python/adapter.py <step>

Pasos: naming | layers | lint | format | types | security | tests | integration |
coverage | e2e
Consultas (producen un dato, no validan): coverage-baseline

El pipeline agnostico (core/pipeline.py) invoca `adapter.py <step>` para cada paso
de codigo declarado en pipeline.steps. Los pasos de proceso (constitution,
traceability, skills) los corre el nucleo directamente, no el adaptador.

Omisiones con aviso (exit 3 = EXIT_OMITIDO), para que una instalacion fresca no
arranque en ROJO sin por eso hacer pasar por verificado lo que no se miro
(SPEC-003 FR-001/FR-004/FR-009):
  - paso sin targets existentes (proyecto todavia sin codigo);
  - paso cuya tool no esta instalada (ruff/mypy/bandit/pytest/import-linter);
  - paso `coverage` sin umbrales declarados en el config (SPEC-009 FR-002):
    los umbrales son opcionales por diseno.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess  # nosec B404 - orquesta linters del proyecto, sin input externo
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "core"))
from sdd_config import (  # noqa: E402
    COVERAGE_BASELINE_PREFIX,
    DEFAULT_TESTS_UNIT,
    EXIT_OMITIDO,
    PIPELINE_COVERAGE_CACHE_ENV,
    CoverageTarget,
    colapsar_a_raiz_comun,
    declared_test_dirs,
    find_repo_root,
    forzar_salida_utf8,
    load,
)


def _run(cmd: list[str], cwd: Path) -> int:
    print(f"    $ {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(cwd))  # nosec B603 - comandos fijos del adaptador


def _module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _skip(reason: str) -> int:
    print(f"    (omitido: {reason})")
    return EXIT_OMITIDO


def _test_dirs(cfg, *, solo_medidas: bool = False) -> list[str]:  # type: ignore[no-untyped-def]
    """Carpetas de tests declaradas, derivadas del SSOT (SPEC-005 FR-007).

    `solo_medidas` separa las dos preguntas: los pasos estaticos miran **todas**
    las carpetas de test, mientras que `coverage` se las pasa a pytest para
    ejecutarlas, y ahi una suite que maneja el producto por subproceso se
    correria de nuevo sin medir una linea (SPEC-018 FR-US3-002).
    """
    return [
        cfg.dirs[k]
        for k in declared_test_dirs(solo_medidas=solo_medidas)
        if k in cfg.dirs
    ] or ["tests"]


def _source_and_test_dirs(cfg) -> tuple[list[str], list[str]]:  # type: ignore[no-untyped-def]
    """Blancos de los pasos estaticos: codigo mas las carpetas de tests.

    Las carpetas de test se colapsan a la raiz que las contiene (SPEC-019
    FR-US4-001): asi entra al alcance la infraestructura compartida que vive
    ahi y no dentro de ninguna subcarpeta declarada. El criterio --y su guarda--
    es de `sdd_config`, no de este adaptador (FR-US4-006).
    """
    return cfg.source_roots, colapsar_a_raiz_comun(_test_dirs(cfg))


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
    if not cfg.layers:
        return _skip("sin capas declaradas en 'layers' del config, paso 'layers'")
    # `lint-imports` importa el paquete raiz para construir el grafo: sin la
    # carpeta en disco aborta ("Could not find package"). Es el mismo caso que
    # los demas pasos de codigo resuelven omitiendo (SPEC-003 FR-001/FR-011).
    root_package = cfg.source_roots[0] if cfg.source_roots else "src"
    if not (repo_root / root_package).exists():
        return _skip(
            f"sin carpetas de codigo todavia (falta '{root_package}/'), paso 'layers'"
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


def _coverage_source_paths(repo_root: Path, cfg) -> list[str]:  # type: ignore[no-untyped-def]
    """Union de `paths` de todos los targets de `pipeline.coverage` que existen."""
    todos = sorted({p for target in cfg.pipeline_coverage for p in target.paths})
    return _existing_targets(repo_root, todos)


def step_tests(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    if not _module_available("pytest"):
        return _skip("tool 'pytest' no instalada (pip install pytest), paso 'tests'")
    unit = cfg.dirs.get("tests_unit", DEFAULT_TESTS_UNIT)
    if not (repo_root / unit).exists():
        return _skip(f"sin carpeta de tests '{unit}' todavia, paso 'tests'")

    # SPEC-009 FR-US3-003: dentro de una corrida de core/pipeline.py con
    # umbrales declarados, instrumenta esta misma corrida con --cov y deja el
    # reporte para que el paso `coverage` lo lea, en vez de correr pytest de
    # nuevo. Solo cuando las carpetas que `coverage` mide son exactamente la
    # unitaria: si hay `tests_integration` medida, esta corrida no la
    # ejecutaria (el paso `tests` solo corre `dirs.tests_unit`, por contrato)
    # y el reporte quedaria incompleto, asi que se omite la instrumentacion y
    # `coverage` cae solo a su loop de siempre. Sin variable de entorno (paso
    # invocado suelto), sin umbrales o sin pytest-cov, corre igual que
    # siempre: el exit code es solo el resultado de los tests, nunca depende
    # de la cobertura.
    cache = os.environ.get(PIPELINE_COVERAGE_CACHE_ENV)
    medidas = _existing_targets(repo_root, _test_dirs(cfg, solo_medidas=True))
    if (
        cache
        and cfg.pipeline_coverage
        and medidas == [unit]
        and _module_available("pytest_cov")
    ):
        src = _coverage_source_paths(repo_root, cfg)
        if src:
            return _run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    unit,
                    *(f"--cov={p}" for p in src),
                    f"--cov-report=json:{cache}",
                    "-q",
                ],
                repo_root,
            )
    return _run([sys.executable, "-m", "pytest", unit, "-q"], repo_root)


def _run_declared_suite(repo_root: Path, cfg, clave: str, paso: str) -> int:  # type: ignore[no-untyped-def]
    """Ejecuta la carpeta que declara `dirs.<clave>`, o se omite nombrando que falta.

    Sin fallback a `tests/`: ejecutar una carpeta que el proyecto no declaro es
    adivinar con efectos, a diferencia de los pasos estaticos, que ante la duda
    miran de mas y no rompen nada (SPEC-019 FR-US1-003).
    """
    carpeta = cfg.dirs.get(clave)
    if not carpeta:
        return _skip(f"sin 'dirs.{clave}' declarada en el config, paso '{paso}'")
    if not _module_available("pytest"):
        return _skip(f"tool 'pytest' no instalada (pip install pytest), paso '{paso}'")
    if not (repo_root / carpeta).exists():
        return _skip(f"sin carpeta de tests '{carpeta}' todavia, paso '{paso}'")
    return _run([sys.executable, "-m", "pytest", carpeta, "-q"], repo_root)


def step_integration(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    """Ejecuta `dirs.tests_integration` (SPEC-019 FR-US1-001..FR-US1-003).

    Paso aparte de `tests` a proposito: el contrato define `tests` como la suite
    unitaria, y fundirlos le impondria a todo derivado un ciclo unico.
    """
    return _run_declared_suite(repo_root, cfg, "tests_integration", "integration")


def step_e2e(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    """Ejecuta `dirs.tests_e2e` (SPEC-018 FR-US3-001).

    Para un proyecto generador este es el nivel de test *primario*: el unico que
    ejercita lo que el producto hace para otros, que es distinto de lo que hace
    sobre si mismo. Va declarado ultimo en `pipeline.steps` por costo, no por
    importancia.
    """
    return _run_declared_suite(repo_root, cfg, "tests_e2e", "e2e")


def _cached_coverage_report(repo_root: Path) -> dict[str, Any] | None:
    """Reporte que dejo el paso `tests` en la misma corrida de pipeline, si hay.

    None cuando no hay corrida compartida que leer: sin variable de entorno
    (paso invocado suelto), sin archivo (tests no lo escribio, p.ej. porque
    tests_integration tambien esta medida) o con un archivo no parseable. En
    los tres casos el llamador cae al loop de pytest por target (SPEC-009
    FR-US3-004).
    """
    cache = os.environ.get(PIPELINE_COVERAGE_CACHE_ENV)
    if not cache:
        return None
    path = Path(cache)
    if not path.exists():
        return None
    try:
        datos: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return datos if isinstance(datos, dict) else None


def _coverage_percent_from_report(
    files: dict[str, Any], paths: list[str]
) -> float | None:
    """Cobertura agregada de los archivos del reporte bajo alguno de `paths`.

    None si ningun archivo del reporte cae bajo esos paths: el reporte no
    instrumento ese target (p. ej. una corrida anterior con otros umbrales) y
    no hay que confiar en el.
    """
    prefixes = [Path(p).as_posix() for p in paths]
    covered = statements = 0
    matched = False
    for filekey, data in files.items():
        key = Path(filekey).as_posix()
        if any(key == prefix or key.startswith(f"{prefix}/") for prefix in prefixes):
            matched = True
            summary = data["summary"]
            covered += summary["covered_lines"]
            statements += summary["num_statements"]
    if not matched:
        return None
    return 100.0 if statements == 0 else covered / statements * 100


def _evaluate_coverage_from_cache(
    report: dict[str, Any], targets: list[CoverageTarget], repo_root: Path
) -> int | None:
    files = report.get("files")
    if not isinstance(files, dict):
        return None

    failed: list[str] = []
    measured = 0
    for target in targets:
        paths = _existing_targets(repo_root, list(target.paths))
        if not paths:
            print(f"    (omitido: {'/'.join(target.paths)} no existe todavia)")
            continue
        pct = _coverage_percent_from_report(files, paths)
        if pct is None:
            return None  # reporte incompleto para este target: no confiar en el cache
        measured += 1
        if pct < target.minimum:
            failed.append(
                f"{', '.join(paths)} (< {target.minimum}%, medido {pct:.2f}%)"
            )

    if not measured:
        return _skip("ningun target de cobertura existe todavia, paso 'coverage'")
    if failed:
        print(
            "    cobertura por debajo del umbral en (reporte compartido con 'tests'):"
        )
        for f in failed:
            print(f"      x {f}")
        return 1
    print(
        "    cobertura evaluada desde el reporte de 'tests' (sin correr pytest de nuevo)."
    )
    return 0


def step_coverage(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    """Verifica los umbrales de cobertura declarados (SPEC-009 FR-001/FR-002).

    Cada entrada de `pipeline.coverage` mide sus `paths` juntas contra su
    `min`. Dentro de una corrida de `core/pipeline.py`, si el paso `tests` dejo
    un reporte compartido (SPEC-009 FR-US3-003/004), este paso evalua los
    umbrales leyendolo en vez de correr pytest. Sin ese reporte -invocacion
    suelta, o `tests` no pudo instrumentar la corrida- cae al mecanismo de
    siempre: una invocacion de pytest por entrada, porque `--cov-fail-under`
    es un umbral unico por corrida y dos exigencias distintas (p. ej. 80%
    global y 96% en el dominio) no entran en la misma.
    """
    targets = cfg.pipeline_coverage
    if not targets:
        return _skip(
            "sin umbrales declarados en pipeline.coverage del config, paso 'coverage'"
        )
    if not _module_available("pytest"):
        return _skip("tool 'pytest' no instalada (pip install pytest), paso 'coverage'")
    if not _module_available("pytest_cov"):
        return _skip(
            "tool 'pytest-cov' no instalada (pip install pytest-cov), paso 'coverage'"
        )

    test_dirs = _existing_targets(repo_root, _test_dirs(cfg, solo_medidas=True))
    if not test_dirs:
        return _skip("sin carpetas de tests todavia, paso 'coverage'")

    report = _cached_coverage_report(repo_root)
    if report is not None:
        cached_result = _evaluate_coverage_from_cache(report, targets, repo_root)
        if cached_result is not None:
            return cached_result

    failed: list[str] = []
    measured = 0
    for target in targets:
        paths = _existing_targets(repo_root, list(target.paths))
        if not paths:
            print(f"    (omitido: {'/'.join(target.paths)} no existe todavia)")
            continue
        measured += 1
        code = _run(
            [
                sys.executable,
                "-m",
                "pytest",
                *test_dirs,
                *(f"--cov={p}" for p in paths),
                "--cov-report=term-missing",
                f"--cov-fail-under={target.minimum}",
                "-q",
            ],
            repo_root,
        )
        if code != 0:
            failed.append(f"{', '.join(paths)} (< {target.minimum}%)")

    if not measured:
        return _skip("ningun target de cobertura existe todavia, paso 'coverage'")
    if failed:
        print("    cobertura por debajo del umbral en:")
        for f in failed:
            print(f"      x {f}")
        return 1
    return 0


def query_coverage_baseline(repo_root: Path, cfg) -> int:  # type: ignore[no-untyped-def]
    """Mide la cobertura real del codigo y la imprime (SPEC-009 FR-US2-001).

    No es un paso de pipeline: no valida nada, produce un dato para que
    `core/sdd_coverage_baseline.py` escriba el primer umbral de un proyecto que
    todavia no tiene ninguno. Por eso vive en QUERIES y no en STEPS.

    Contrato de salida (adapters/CONTRACT.md): una linea
    `SDD-COVERAGE-BASELINE <porcentaje> <paths separados por coma>`.
    """
    if not _module_available("pytest"):
        return _skip("tool 'pytest' no instalada (pip install pytest)")
    if not _module_available("pytest_cov"):
        return _skip("tool 'pytest-cov' no instalada (pip install pytest-cov)")

    src_dirs = _existing_targets(repo_root, cfg.source_roots)
    test_dirs = _existing_targets(repo_root, _test_dirs(cfg, solo_medidas=True))
    if not src_dirs:
        return _skip("sin carpetas de codigo todavia")
    if not test_dirs:
        return _skip("sin carpetas de tests todavia")

    with tempfile.TemporaryDirectory() as tmp:
        reporte = Path(tmp) / "coverage.json"
        # Un exit != 0 aca puede ser "la suite esta roja", que no invalida la
        # medicion: lo que decide es si hubo reporte.
        _run(
            [
                sys.executable,
                "-m",
                "pytest",
                *test_dirs,
                *(f"--cov={d}" for d in src_dirs),
                f"--cov-report=json:{reporte}",
                "-q",
            ],
            repo_root,
        )
        if not reporte.exists():
            return _skip("pytest no produjo reporte de cobertura")
        try:
            datos = json.loads(reporte.read_text(encoding="utf-8"))
            porcentaje = float(datos["totals"]["percent_covered"])
        except (OSError, ValueError, KeyError) as exc:
            return _skip(f"reporte de cobertura ilegible ({exc})")

    print(f"{COVERAGE_BASELINE_PREFIX} {porcentaje:.2f} {','.join(src_dirs)}")
    return 0


STEPS = {
    "naming": step_naming,
    "layers": step_layers,
    "lint": step_lint,
    "format": step_format,
    "types": step_types,
    "security": step_security,
    "tests": step_tests,
    "integration": step_integration,
    "coverage": step_coverage,
    "e2e": step_e2e,
}

# Consultas: verbos que producen un dato en vez de validar. No son pasos de
# pipeline y no deben entrar a `CODE_STEPS` (SPEC-009 FR-US2-001).
QUERIES = {
    "coverage-baseline": query_coverage_baseline,
}


def main(argv: list[str]) -> int:
    verbos = {**STEPS, **QUERIES}
    if len(argv) != 1 or argv[0] not in verbos:
        print(f"Uso: adapter.py <{' | '.join(verbos)}>", file=sys.stderr)
        return 2
    repo_root = find_repo_root()
    cfg = load(repo_root)
    return verbos[argv[0]](repo_root, cfg)


if __name__ == "__main__":
    forzar_salida_utf8()
    raise SystemExit(main(sys.argv[1:]))
