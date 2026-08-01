"""Orquestador del pipeline local SDD (nucleo del kit, multiplataforma).

Reemplaza al pipeline_local.sh especifico: corre los pasos declarados en
`pipeline.steps` de .sdd/config.yaml, en orden. Cada paso es:

  - de PROCESO (agnostico de lenguaje): lo ejecuta el nucleo directamente
    (constitution, traceability, skills).
  - de CODIGO (especifico de lenguaje): lo delega al adaptador del lenguaje
    activo (`adapters/<language>/adapter.py <step>`): naming, layers, lint,
    format, types, security, tests.

Con `language: none`, los pasos de codigo se omiten con aviso (modo doc-solo:
quedan activos solo los gates de proceso). Contrato: exit 0 si todos los pasos
pasan; 1 si alguno falla (sigue corriendo salvo --fail-fast).

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
from sdd_config import find_repo_root, load  # noqa: E402

PROCESS_STEPS = {"constitution", "traceability", "skills"}
CODE_STEPS = {"naming", "layers", "lint", "format", "types", "security", "tests"}


def _run(cmd: list[str], cwd: Path) -> int:
    return subprocess.call(cmd, cwd=str(cwd))  # nosec B603 - comandos fijos del pipeline


def _run_process_step(step: str, repo_root: Path) -> int:
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
    print(f"    (paso de proceso desconocido: {step})")
    return 0


def _run_code_step(step: str, language: str, repo_root: Path) -> int | None:
    if language == "none":
        print(f"    (omitido: language=none, paso de codigo '{step}')")
        return None
    adapter = KIT_ROOT / "adapters" / language / "adapter.py"
    if not adapter.exists():
        print(f"    (sin adaptador para language={language}: {adapter})")
        return None
    return _run([sys.executable, str(adapter), step], repo_root)


def main(argv: list[str]) -> int:
    fail_fast = "--fail-fast" in argv
    repo_root = find_repo_root()
    cfg = load(repo_root)
    steps = cfg.pipeline_steps or ["constitution", "traceability"]
    language = cfg.language

    failed: list[str] = []
    total = 0
    for step in steps:
        total += 1
        print(f"\n--- {step} ---")
        if step in PROCESS_STEPS:
            code = _run_process_step(step, repo_root)
        elif step in CODE_STEPS:
            code = _run_code_step(step, language, repo_root)
            if code is None:  # omitido: no cuenta como paso
                total -= 1
                continue
        else:
            print(f"    (paso desconocido: {step})")
            continue

        if code == 0:
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
        return 0
    print(f"Pipeline local: ROJO — {ok}/{total} OK, {len(failed)} fallo(s):")
    for f in failed:
        print(f"  x {f}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
