"""Chequeo de salud de la instalación SDD (respaldo de la skill `sdd-doctor`).

Verifica que el andamiaje esté sano: config presente y parseable, artefactos
clave existentes, gates cableados, sin drift de artefactos generados, y versión
del kit registrada. Reporta; con --fix ejecuta las regeneraciones seguras.

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
from sdd_config import find_repo_root, load  # noqa: E402

REQUIRED = [
    "CONSTITUTION.md",
    "AGENTS.md",
    "00-INDEX.md",
    "specs/SPECS_REGISTRY.md",
    "specs/SPEC-000-naming.md",
    ".sdd/config.yaml",
    ".sdd/current-spec",
]

GATE_WIRING = [".claude/settings.json", ".pre-commit-config.yaml"]


def _run(cmd: list[str], cwd: Path) -> int:
    return subprocess.call(cmd, cwd=str(cwd))  # nosec B603 - comandos fijos


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

    # 3. Gates cableados.
    for rel in GATE_WIRING:
        if not (repo_root / rel).exists():
            problems.append(f"Gate no cableado: falta {rel}")

    # 4. Drift de artefactos generados.
    core = repo_root / "tools" / "sdd" / "core"
    if not core.exists():
        core = HERE  # ejecución desde el propio kit
    render = core / "render.py"
    gen = core / "gen_skill_adapters.py"
    if render.exists():
        rc = _run([sys.executable, str(render), "--check"], repo_root)
        if rc != 0:
            if fix:
                _run([sys.executable, str(render)], repo_root)
                notes.append("render: regenerado (--fix).")
            else:
                problems.append(
                    "CONSTITUTION.md/SPEC-000 desincronizados del config (render)."
                )
    if gen.exists():
        rc = _run([sys.executable, str(gen), "--check"], repo_root)
        if rc != 0:
            if fix:
                _run([sys.executable, str(gen)], repo_root)
                notes.append("skills: regeneradas (--fix).")
            else:
                problems.append(
                    "Adaptadores de skills desincronizados (gen_skill_adapters)."
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
