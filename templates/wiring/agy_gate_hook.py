"""Transporte del SDD gate para Antigravity CLI (hook PreToolUse).

Adapta el payload JSON de Antigravity al nucleo agnostico y delega la decision
en `sdd_gate.main` (SSOT de la politica spec-first, vendorizado por sdd-init).
El nucleo no conoce el esquema `toolCall.args.TargetFile`: esa traduccion vive
aca (SPEC-015 FR-US2-003).

A diferencia del hook de Claude Code —que decide por exit code— Antigravity
**solo** respeta un JSON `{"decision": "allow"|"deny", "reason": "..."}` por
stdout. Todo lo demas (exit != 0, stdout vacio, stdout no parseable, comando que
no arranca) lo registra como `pre-tool hook failed` y **ejecuta la edicion igual**:
es fail-OPEN, medido en el testbed el 2026-08-13. De ahi dos reglas:

1. Este script sale SIEMPRE con codigo 0 y SIEMPRE imprime un JSON valido.
   Cualquier excepcion se traduce a `deny` (fail-closed), nunca se propaga.
2. La rama "no hay Python" no puede resolverse aca —si el interprete falta, este
   archivo no corre—: la cubre `.agents/agy_deny.json` via el `||` del comando
   en `.agents/hooks.json`.

Antigravity invoca el hook con el **cwd en `.agents/`**, no en la raiz del
proyecto (tambien medido). Por eso el comando del hook nombra los archivos
relativos a esa carpeta, y aca la raiz se deriva de `__file__` y se aplica con
`os.chdir` antes de decidir (FR-US2-004): las rutas relativas del payload son
del proyecto, no de `.agents/`.

Ver docs/SDD-ENFORCEMENT.md. Wiring: .agents/hooks.json.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
from pathlib import Path

# JSON que Antigravity espera cuando la edicion no se permite.
_DENY = "deny"
_ALLOW = "allow"


def _responder(decision: str, reason: str = "") -> None:
    """Emite el veredicto y termina. Siempre exit 0: ver regla 1 del modulo."""
    salida: dict[str, str] = {"decision": decision}
    if reason:
        salida["reason"] = reason
    print(json.dumps(salida))
    sys.exit(0)


def main() -> None:
    try:
        # La raiz sale del propio script (`.agents/agy_gate_hook.py`), nunca del
        # cwd, que Antigravity deja en `.agents/`.
        repo_root = Path(__file__).resolve().parent.parent
        os.chdir(repo_root)

        # En el kit el nucleo es `core/`; en un proyecto derivado, vendorizado
        # en `tools/sdd/core/`.
        for candidato in (repo_root / "tools" / "sdd" / "core", repo_root / "core"):
            if candidato.exists():
                sys.path.insert(0, str(candidato))
                break

        import sdd_gate

        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        args = payload.get("toolCall", {}).get("args", {})
        file_path = str(args.get("TargetFile", ""))

        # Transporte argv del gate: pasa por `main`, no por `decide`, para
        # heredar el escape hatch SDD_GATE_BYPASS y la resolucion de raiz
        # (SPEC-017 FR-US3-004). Su stderr es el motivo del bloqueo; su stdout
        # se descarta para no contaminar el JSON de respuesta.
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            exit_code = sdd_gate.main([file_path] if file_path else [])
    except Exception as exc:  # noqa: BLE001 - cualquier fallo bloquea (regla 1)
        _responder(_DENY, f"sdd-gate: el gate no pudo decidir ({exc!r}).")
    else:
        if exit_code == 0:
            _responder(_ALLOW)
        _responder(_DENY, err.getvalue().strip())


if __name__ == "__main__":
    main()
