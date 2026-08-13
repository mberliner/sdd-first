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

Un paso puede terminar en cuatro estados: OK, FALLO, OMITIDO (SPEC-003 FR-009) y
OK CON RESERVAS (SPEC-020 FR-US2-004). Omitido es "no se pudo verificar" -- sin
targets, sin tool, sin umbrales, sin repo git -- y no se cuenta entre los pasos
OK: contarlo hacia parecer verificado lo que nadie miro. Con reservas es
"verifique lo mio, pero algo que presupongo no paso en esta corrida": cuenta
entre los OK y condiciona el verde del resumen, sin cambiar el exit code. El
resumen final informa las dos cosas.

Uso:
    python core/pipeline.py [--fail-fast]
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - orquesta checks del propio proyecto
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT_ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from sdd_config import (  # noqa: E402
    CODE_STEPS,
    EXIT_OMITIDO,
    EXIT_RESERVAS,
    PIPELINE_COVERAGE_CACHE_ENV,
    PIPELINE_STEPS_RUN_ENV,
    find_repo_root,
    forzar_salida_utf8,
    load,
)

PROCESS_STEPS = {"hooks", "constitution", "traceability", "skills", "render"}


def _run(cmd: list[str], cwd: Path, extra_env: dict[str, str] | None = None) -> int:
    if extra_env:
        return subprocess.call(  # nosec B603 - comandos fijos del pipeline
            cmd, cwd=str(cwd), env={**os.environ, **extra_env}
        )
    return subprocess.call(cmd, cwd=str(cwd))  # nosec B603 - comandos fijos del pipeline


def _run_process_step(
    step: str, repo_root: Path, extra_env: dict[str, str] | None = None
) -> int:
    if step == "hooks":
        return _run([sys.executable, str(HERE / "bootstrap_hooks.py")], repo_root)
    if step == "constitution":
        # Recibe el canal con los pasos ya ejecutados (SPEC-020 FR-US2-001):
        # es lo unico que le permite distinguir un enforcement declarado de uno
        # que efectivamente corrio.
        return _run(
            [sys.executable, str(HERE / "check_constitution.py"), "CONSTITUTION.md"],
            repo_root,
            extra_env,
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


def _run_code_step(
    step: str,
    language: str,
    repo_root: Path,
    extra_env: dict[str, str] | None = None,
) -> int:
    if language == "none":
        print(f"    (omitido: language=none, paso de codigo '{step}')")
        return EXIT_OMITIDO
    adapter = KIT_ROOT / "adapters" / language / "adapter.py"
    if not adapter.exists():
        print(f"    (omitido: sin adaptador para language={language}: {adapter})")
        return EXIT_OMITIDO
    return _run([sys.executable, str(adapter), step], repo_root, extra_env)


def main(argv: list[str]) -> int:
    fail_fast = "--fail-fast" in argv
    repo_root = find_repo_root()
    cfg = load(repo_root)
    steps = cfg.pipeline_steps or ["constitution", "traceability"]
    language = cfg.language

    # Cache de un solo uso para que `tests` y `coverage` compartan una unica
    # corrida de pytest instrumentada en vez de correrla cada uno por su
    # cuenta (SPEC-009 FR-US3-002). Vive fuera del repo y se borra siempre al
    # terminar: un reporte que ningun paso llego a leer no es un problema.
    cache_dir = Path(tempfile.mkdtemp(prefix="sdd-pipeline-"))
    extra_env = {PIPELINE_COVERAGE_CACHE_ENV: str(cache_dir / "coverage.json")}
    try:
        failed: list[str] = []
        omitidos: list[str] = []
        con_reservas: list[str] = []
        ejecutados: list[str] = []
        total = 0
        for step in steps:
            total += 1
            print(f"\n--- {step} ---")
            # Los pasos ya ejecutados viajan a los de proceso (SPEC-020
            # FR-US2-001). Se arma por paso, no una vez: lo que importa es el
            # estado al llegar a este punto de la corrida.
            paso_env = {**extra_env, PIPELINE_STEPS_RUN_ENV: ",".join(ejecutados)}
            es_proceso = step in PROCESS_STEPS
            if es_proceso:
                code = _run_process_step(step, repo_root, paso_env)
            elif step in CODE_STEPS:
                code = _run_code_step(step, language, repo_root, paso_env)
            else:
                print(f"    (paso desconocido: {step})")
                total -= 1
                continue

            if code == EXIT_OMITIDO:
                # No verificado: no suma a los OK ni al total (SPEC-003 FR-009).
                # Tampoco cuenta como ejecutado: corrio, pero no miro nada.
                total -= 1
                omitidos.append(step)
                print(f"[OMITIDO] {step}")
            elif code == EXIT_RESERVAS and es_proceso:
                # Verifico lo suyo, asi que cuenta entre los OK, pero algo que
                # presupone no paso en esta corrida (SPEC-020 FR-US2-004). El
                # detalle lo imprimio el propio paso: aca solo se traduce el
                # codigo, sin recalcular ningun criterio.
                #
                # Solo de pasos de proceso: el contrato de adaptador declara tres
                # estados (adapters/CONTRACT.md) y un paso de codigo no tiene de
                # que hacer reservas, asi que ese exit code suyo es una falla.
                ejecutados.append(step)
                con_reservas.append(step)
                print(f"[OK*]   {step} (con reservas)")
            elif code == 0:
                ejecutados.append(step)
                print(f"[OK]    {step}")
            else:
                ejecutados.append(step)
                failed.append(step)
                print(f"[FALLO] {step}")
                if fail_fast:
                    print("Pipeline detenido por --fail-fast.")
                    return 1

        print("\n" + "=" * 50)
        ok = total - len(failed)
        if not failed:
            # El verde deja de ser incondicional cuando algun paso no pudo
            # afirmar todo lo suyo (SPEC-020 FR-US2-004).
            estado = "VERDE con reservas" if con_reservas else "VERDE"
            print(f"Pipeline local: {estado} — {ok}/{total} pasos OK")
        else:
            print(f"Pipeline local: ROJO — {ok}/{total} OK, {len(failed)} fallo(s):")
            for f in failed:
                print(f"  x {f}")
        if omitidos:
            # Visible en verde y en rojo: son los pasos que NADIE verifico.
            print(f"Omitidos ({len(omitidos)}, no verificados): {', '.join(omitidos)}")
        if con_reservas:
            print(f"Con reservas ({len(con_reservas)}): {', '.join(con_reservas)}")
        return 1 if failed else 0
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


if __name__ == "__main__":
    forzar_salida_utf8()
    raise SystemExit(main(sys.argv[1:]))
