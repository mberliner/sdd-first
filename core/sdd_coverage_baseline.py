"""Mide el piso de cobertura del proyecto y lo declara en el config.

SPEC-009 US2 (K-5 de `docs/IDEAS.md`): `sdd-init` siembra el paso `coverage` en
`pipeline.steps` pero no puede sembrar un umbral --no sabe cuanto cubre un
proyecto que todavia no existe--, asi que el paso se omite con aviso en cada
corrida. Un paso que nunca verifica nada ensena que el VERDE del pipeline es
ruido: la misma familia que U-3 y C-1.

Esta herramienta cierra el hueco midiendo el piso real y escribiendolo como
trinquete. El nucleo orquesta y decide la politica; la medicion es del adaptador
del lenguaje (consulta `coverage-baseline`, ver adapters/CONTRACT.md), porque
como se mide cobertura es especifico del ecosistema.

Politica (FR-US2-005): si `pipeline.coverage` ya esta declarado, NO se toca. Se
informa medido vs declarado y se avisa cuando el declarado quedo por debajo del
piso real --el trinquete dejo de morder, que es exactamente el defecto que K-3
encontro en el propio kit: umbral 50 con cobertura real 75--. Subir un umbral es
decision de politica, no algo que una corrida afortunada haga por su cuenta.

Uso:
    python core/sdd_coverage_baseline.py

Exit 0 si midio y escribio (o si no habia nada que escribir), 3 si no se pudo
medir (sin adaptador, sin tooling, sin codigo o sin tests todavia).
"""

from __future__ import annotations

import math
import subprocess  # nosec B404 - invoca el adaptador del propio proyecto
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT_ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from sdd_config import (  # noqa: E402
    CONFIG_RELPATH,
    COVERAGE_BASELINE_PREFIX,
    EXIT_OMITIDO,
    find_repo_root,
    load,
    script_hint,
    write_text_lf,
)


def _skip(reason: str) -> int:
    print(f"(omitido: {reason})")
    return EXIT_OMITIDO


def medir(repo_root: Path, language: str) -> tuple[float, list[str]] | None:
    """Corre la consulta `coverage-baseline` del adaptador activo.

    Devuelve (porcentaje, paths medidos) o None si no se pudo medir. La salida
    del adaptador se reemite tal cual: quien corre esto quiere ver la suite.
    """
    if language == "none":
        return None
    adapter = KIT_ROOT / "adapters" / language / "adapter.py"
    if not adapter.exists():
        return None
    proc = subprocess.run(  # nosec B603 - ruta construida desde el config, no input externo
        [sys.executable, str(adapter), "coverage-baseline"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        return None
    return parse_baseline(proc.stdout)


def parse_baseline(salida: str) -> tuple[float, list[str]] | None:
    """Lee la linea de contrato del adaptador (SPEC-009 FR-US2-001)."""
    for linea in salida.splitlines():
        if not linea.startswith(COVERAGE_BASELINE_PREFIX):
            continue
        partes = linea.split()
        if len(partes) != 3:
            continue
        try:
            porcentaje = float(partes[1])
        except ValueError:
            continue
        paths = [p for p in partes[2].split(",") if p]
        if paths:
            return porcentaje, paths
    return None


def escribir_umbral(texto: str, paths: list[str], minimo: int) -> str:
    """Agrega `coverage:` a la seccion `pipeline:` conservando el resto.

    Edicion por lineas y no reescritura del YAML (FR-US2-004): el config es un
    documento que su dueno edita a mano y sus comentarios son parte del
    contenido; volcarlo con un dumper los perderia todos.
    """
    lineas = texto.splitlines()
    inicio = next(
        (i for i, linea in enumerate(lineas) if linea.rstrip() == "pipeline:"), None
    )
    if inicio is None:
        raise ValueError("el config no tiene seccion 'pipeline:'")

    # Fin de la seccion: la proxima linea con contenido en columna 0.
    fin = len(lineas)
    for i in range(inicio + 1, len(lineas)):
        linea = lineas[i]
        if linea.strip() and not linea[0].isspace():
            fin = i
            break

    bloque = [
        "",
        "  # Piso de cobertura medido por core/sdd_coverage_baseline.py.",
        "  # Es un trinquete: subirlo exige cubrir mas, bajarlo es una decision",
        "  # que se toma a mano y se justifica.",
        "  coverage:",
        f"    - paths: [{', '.join(paths)}]",
        f"      min: {minimo}",
    ]
    # Se inserta despues del ultimo renglon con contenido de la seccion, para no
    # dejar el bloque colgando entre lineas en blanco.
    corte = fin
    while corte > inicio + 1 and not lineas[corte - 1].strip():
        corte -= 1
    nuevas = [*lineas[:corte], *bloque, *lineas[corte:]]
    return "\n".join(nuevas).rstrip() + "\n"


def main(argv: list[str]) -> int:
    _ = argv
    repo_root = find_repo_root()
    cfg = load(repo_root)
    config_path = repo_root / CONFIG_RELPATH
    if not config_path.exists():
        return _skip(f"falta {CONFIG_RELPATH} (¿corriste sdd-init?)")

    medicion = medir(repo_root, cfg.language)
    if medicion is None:
        return _skip(
            f"el adaptador de language={cfg.language} no pudo medir la cobertura"
        )
    porcentaje, paths = medicion
    # Hacia abajo: un piso con decimales que no se puede volver a alcanzar no es
    # un trinquete, es una trampa (FR-US2-003).
    minimo = math.floor(porcentaje)

    declarados = cfg.pipeline_coverage
    if declarados:
        print(f"\nCobertura medida: {porcentaje:.2f}% sobre {', '.join(paths)}")
        print("pipeline.coverage ya esta declarado; no se modifica:")
        for target in declarados:
            print(f"  - {', '.join(target.paths)}: min {target.minimum}")
        flojos = [t for t in declarados if t.minimum < minimo]
        if flojos:
            print(
                "\nAviso: el trinquete no esta mordiendo. Estos umbrales estan por"
                f" debajo del piso real ({minimo}%):"
            )
            for target in flojos:
                print(f"  x {', '.join(target.paths)}: min {target.minimum} < {minimo}")
            print(f"Subilos a mano en {CONFIG_RELPATH} si el piso vino para quedarse.")
        return 0

    texto = config_path.read_text(encoding="utf-8")
    try:
        nuevo = escribir_umbral(texto, paths, minimo)
    except ValueError as exc:
        return _skip(str(exc))
    write_text_lf(config_path, nuevo)
    print(f"\nCobertura medida: {porcentaje:.2f}% sobre {', '.join(paths)}")
    print(f"Umbral escrito en {CONFIG_RELPATH}: min {minimo}")
    print(
        "El paso 'coverage' pasa a verificar. Corré: python "
        f"{script_hint(HERE / 'pipeline.py', repo_root)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
