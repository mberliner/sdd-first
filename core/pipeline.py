"""Orquestador del pipeline local SDD (nucleo del kit, multiplataforma).

Reemplaza al pipeline_local.sh especifico: corre los pasos declarados en
`pipeline.steps` de .sdd/config.yaml, en orden. Cada paso es:

  - de PROCESO (agnostico de lenguaje): lo ejecuta el nucleo directamente
    (constitution, traceability, skills, render).
  - de CODIGO (especifico de lenguaje): lo delega al adaptador del lenguaje
    activo (`adapters/<language>/adapter.py <step>`): naming, layers, lint,
    format, types, security, tests, coverage.

Con `language: none`, los pasos de codigo se omiten con aviso (modo doc-solo:
quedan activos solo los gates de proceso). Contrato: exit 0 si todos los pasos
pasan; 1 si alguno falla (sigue corriendo salvo --fail-fast).

Un paso puede terminar en tres estados (SPEC-003 FR-009): OK, FALLO u OMITIDO.
Omitido es "no se pudo verificar" -- sin targets, sin tool, sin umbrales, sin
repo git -- y no se cuenta entre los pasos OK: contarlo hacia parecer verificado
lo que nadie miro. El resumen final informa cuantos se omitieron.

Uso:
    python core/pipeline.py [--fail-fast]
"""

from __future__ import annotations

import subprocess  # nosec B404 - orquesta checks del propio proyecto
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT_ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from sdd_config import (  # noqa: E402
    CODE_STEPS,
    EXIT_OMITIDO,
    find_repo_root,
    forzar_salida_utf8,
    load,
)

PROCESS_STEPS = {"hooks", "constitution", "traceability", "skills", "render"}


def _run(cmd: list[str], cwd: Path) -> int:
    return subprocess.call(cmd, cwd=str(cwd))  # nosec B603 - comandos fijos del pipeline


def _run_process_step(step: str, repo_root: Path) -> int:
    if step == "hooks":
        return _run([sys.executable, str(HERE / "bootstrap_hooks.py")], repo_root)
    if step == "constitution":
        return _run(
            [sys.executable, str(HERE / "check_constitution.py"), "CONSTITUTION.md"],
            repo_root,
        )
    if step == "traceability":
        return _run(
            [sys.executable, str(HERE / "check_traceability.py"), "specs"], repo_root
        )
    if step == "skills":
        return _run(
            [sys.executable, str(HERE / "gen_skill_adapters.py"), "--check"], repo_root
        )
    if step == "render":
        return _run([sys.executable, str(HERE / "render.py"), "--check"], repo_root)
    print(f"    (paso de proceso desconocido: {step})")
    return 0


def _run_code_step(step: str, language: str, repo_root: Path) -> int:
    if language == "none":
        print(f"    (omitido: language=none, paso de codigo '{step}')")
        return EXIT_OMITIDO
    adapter = KIT_ROOT / "adapters" / language / "adapter.py"
    if not adapter.exists():
        print(f"    (omitido: sin adaptador para language={language}: {adapter})")
        return EXIT_OMITIDO
    return _run([sys.executable, str(adapter), step], repo_root)


def main(argv: list[str]) -> int:
    fail_fast = "--fail-fast" in argv
    repo_root = find_repo_root()
    cfg = load(repo_root)
    steps = cfg.pipeline_steps or ["constitution", "traceability"]
    language = cfg.language

    failed: list[str] = []
    omitidos: list[str] = []
    total = 0
    for step in steps:
        total += 1
        print(f"\n--- {step} ---")
        if step in PROCESS_STEPS:
            code = _run_process_step(step, repo_root)
        elif step in CODE_STEPS:
            code = _run_code_step(step, language, repo_root)
        else:
            print(f"    (paso desconocido: {step})")
            total -= 1
            continue

        if code == EXIT_OMITIDO:
            # No verificado: no suma a los OK ni al total (SPEC-003 FR-009).
            total -= 1
            omitidos.append(step)
            print(f"[OMITIDO] {step}")
        elif code == 0:
            print(f"[OK]    {step}")
        else:
            failed.append(step)
            print(f"[FALLO] {step}")
            if fail_fast:
                print("Pipeline detenido por --fail-fast.")
                return 1

    print("\n" + "=" * 50)
    ok = total - len(failed)
    if not failed:
        print(f"Pipeline local: VERDE — {ok}/{total} pasos OK")
    else:
        print(f"Pipeline local: ROJO — {ok}/{total} OK, {len(failed)} fallo(s):")
        for f in failed:
            print(f"  x {f}")
    if omitidos:
        # Visible en verde y en rojo: son los pasos que NADIE verifico.
        print(f"Omitidos ({len(omitidos)}, no verificados): {', '.join(omitidos)}")
    return 1 if failed else 0


if __name__ == "__main__":
    forzar_salida_utf8()
    raise SystemExit(main(sys.argv[1:]))
