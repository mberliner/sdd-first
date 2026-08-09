"""Chequeo de salud de la instalación SDD (respaldo de la skill `sdd-doctor`).

Verifica que el andamiaje esté sano: config presente y parseable, artefactos
clave existentes, gates cableados **de verdad** (el archivo existe y contiene la
invocación al gate, no solo el nombre correcto), sin drift de artefactos
generados, y versión del kit registrada. Reporta; con --fix ejecuta las
regeneraciones seguras.

Uso:
    python core/sdd_doctor.py [--fix]

Exit 0 si todo OK, 1 si hay problemas.
"""

from __future__ import annotations

import subprocess  # nosec B404 - corre checks del propio proyecto
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sdd_config import (  # noqa: E402
    GATE_WIRING,
    TEST_DIR_STEP,
    find_repo_root,
    load,
    script_hint,
)

REQUIRED = [
    "CONSTITUTION.md",
    "AGENTS.md",
    "00-INDEX.md",
    "specs/SPECS_REGISTRY.md",
    "specs/SPEC-000-naming.md",
    ".sdd/config.yaml",
    ".sdd/current-spec",
]


def _run(cmd: list[str], cwd: Path) -> int:
    return subprocess.call(cmd, cwd=str(cwd))  # nosec B603 - comandos fijos


def _drift(script: Path, repo_root: Path) -> list[str] | None:
    """Corre `<script> --check` y devuelve los artefactos desincronizados.

    `None` = sin drift. Lista (posiblemente vacía) = el check falló; se capturan
    las líneas `x <archivo>` que ya imprimen `render.py` y
    `gen_skill_adapters.py` para poder nombrar en el reporte lo que drifteó
    (FR-US2-003) en vez de una lista fija de artefactos.
    """
    result = subprocess.run(  # nosec B603 - script del propio andamiaje
        [sys.executable, str(script), "--check"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return None
    salida = f"{result.stdout}\n{result.stderr}"
    print(salida.rstrip())
    return [
        line.strip()[2:].strip()
        for line in salida.splitlines()
        if line.strip().startswith("x ")
    ]


def _gate_wiring_problems(repo_root: Path) -> list[str]:
    """Verifica que el wiring de gate exista Y cablee el gate (FR-US1-002).

    Un archivo con el nombre correcto no prueba nada: el proyecto pudo tener su
    propio `.pre-commit-config.yaml` (que `sdd-init` conserva por diseno) y
    entonces no hay ninguna capa de enforcement activa. Reportar "sana" en ese
    caso es peor que no tener la herramienta.
    """
    problems: list[str] = []
    for rel, invocacion in GATE_WIRING.items():
        path = repo_root / rel
        if not path.exists():
            problems.append(f"Gate no cableado: falta {rel}")
            continue
        try:
            contenido = path.read_text(encoding="utf-8")
        except OSError as exc:
            problems.append(f"Gate no verificable: no se pudo leer {rel} ({exc}).")
            continue
        if invocacion not in contenido:
            problems.append(
                f"Gate no cableado: {rel} existe pero no invoca {invocacion} "
                "(¿es el wiring propio del proyecto? compara con templates/wiring/)."
            )
    return problems


def _tests_sin_ejecutor(cfg) -> list[str]:  # type: ignore[no-untyped-def]
    """Carpetas de tests declaradas que ningun paso del pipeline corre (SPEC-019).

    Que el ciclo rapido incluya o no los tests de integracion es decision del
    proyecto —por eso el paso es opcional en `pipeline.steps`—, pero la omision
    no puede ser silenciosa: `dirs.tests_integration` existe como clave desde
    siempre y durante todo ese tiempo nadie ejecuto lo que declaraba (V-1).
    """
    declarados = set(cfg.pipeline_steps)
    problemas: list[str] = []
    for clave, paso in TEST_DIR_STEP.items():
        carpeta = cfg.dirs.get(clave)
        if carpeta and paso not in declarados:
            problemas.append(
                f"Tests declarados que no corre nadie: dirs.{clave} = {carpeta}, "
                f"pero '{paso}' no esta en pipeline.steps de .sdd/config.yaml."
            )
    return problemas


def _coverage_inerte(cfg, repo_root: Path) -> list[str]:  # type: ignore[no-untyped-def]
    """Paso `coverage` declarado sin umbrales: se omite en cada corrida.

    Nota y no problema (SPEC-009 FR-US2-006): un proyecto recien instalado que
    todavia no tiene suite es sano, y un doctor que sale 1 sobre una instalacion
    fresca reintroduce el falso negativo que SPEC-014 cerro del otro lado. Pero
    el silencio tampoco sirve: un paso que nunca verifica nada ensena que el
    VERDE es ruido (K-5 de docs/IDEAS.md).
    """
    if "coverage" not in cfg.pipeline_steps or cfg.pipeline_coverage:
        return []
    script = HERE / "sdd_coverage_baseline.py"
    return [
        "paso 'coverage' declarado sin umbrales en pipeline.coverage: se omite en "
        f"cada corrida. Medí el piso real con: python {script_hint(script, repo_root)}"
    ]


def main(argv: list[str]) -> int:
    fix = "--fix" in argv
    repo_root = find_repo_root()
    problems: list[str] = []
    notes: list[str] = []

    # 1. Config parseable + versión del kit.
    cfg = load(repo_root)
    if not (repo_root / ".sdd" / "config.yaml").exists():
        problems.append("Falta .sdd/config.yaml (¿corriste sdd-init?).")
    else:
        kit_version = cfg.raw.get("project", {}).get("kit_version")
        notes.append(f"kit_version: {kit_version or '(no declarada)'}")
        notes.append(f"language: {cfg.language}")

    # 2. Artefactos requeridos.
    for rel in REQUIRED:
        if not (repo_root / rel).exists():
            problems.append(f"Falta artefacto requerido: {rel}")

    # 3. Gates cableados (existen y cablean el gate).
    problems.extend(_gate_wiring_problems(repo_root))

    # 3b. Carpetas de tests declaradas sin paso que las ejecute.
    problems.extend(_tests_sin_ejecutor(cfg))

    # 3c. Paso `coverage` sin umbrales: nota, no problema.
    notes.extend(_coverage_inerte(cfg, repo_root))

    # 4. Drift de artefactos generados.
    core = repo_root / "tools" / "sdd" / "core"
    if not core.exists():
        core = HERE  # ejecución desde el propio kit
    for script_name, etiqueta in (
        ("render.py", "Artefactos derivados del config"),
        ("gen_skill_adapters.py", "Adaptadores de skills"),
    ):
        script = core / script_name
        if not script.exists():
            continue
        desincronizados = _drift(script, repo_root)
        if desincronizados is None:
            continue
        if fix:
            _run([sys.executable, str(script)], repo_root)
            notes.append(f"{script_name}: regenerado (--fix).")
            continue
        # El mensaje nombra lo que drifteó, no una lista fija de artefactos
        # (FR-US2-003), y cita la ruta real del script (FR-US2-002).
        detalle = ", ".join(desincronizados) if desincronizados else "(ver salida)"
        problems.append(
            f"{etiqueta} desincronizados: {detalle} — corré: python "
            f"{script_hint(script, repo_root)}"
        )

    print("== sdd-doctor ==")
    for n in notes:
        print(f"  - {n}")
    if problems:
        print("\nProblemas:")
        for p in problems:
            print(f"  x {p}")
        print(
            f"\nTotal: {len(problems)} problema(s). Corré con --fix para autoreparar drift."
        )
        return 1
    print("\nInstalación SDD sana.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
