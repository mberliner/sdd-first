"""Interlock de autoria spec-first (nucleo minimo del kit, Principio de gate).

Gate de enforcement *anterior* a que el codigo exista: bloquea la edicion/commit
de codigo fuente si no hay una spec vigente declarada en `.sdd/current-spec` (y
editada despues de declararla). La logica de decision (`decide`) es agnostica de
asistente; el modulo acepta tres transportes de entrada:

1. **argv**: `python core/sdd_gate.py src/a.py` — usado por pre-commit y hooks
   que pasan rutas como argumentos.
2. **env**: `SDD_GATE_FILE=src/a.py python core/sdd_gate.py`.
3. **stdin JSON**: protocolo `PreToolUse` de Claude Code.

Contrato de salida: exit 0 = permitir, exit 2 = bloquear (motivo en stderr).

A diferencia del original hardcodeado a `src/`, este lee las carpetas de codigo
fuente de `dirs.source_roots` en `.sdd/config.yaml` (via core.sdd_config), de
modo que sirve a proyectos con cualquier layout.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd_config import find_repo_root, load  # noqa: E402


def _source_roots(repo_root: Path) -> list[str]:
    try:
        return load(repo_root).source_roots
    except SystemExit:
        # PyYAML ausente: degradar al default clasico en vez de romper el gate.
        return ["src"]


def _is_source_path(file_path: str, repo_root: Path) -> bool:
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    try:
        rel = candidate.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    if not rel.parts:
        return False
    roots = _source_roots(repo_root)
    for root in roots:
        parts = Path(root).parts
        if rel.parts[: len(parts)] == parts:
            return True
    return False


def _declared_specs(repo_root: Path) -> list[str]:
    path = repo_root / ".sdd" / "current-spec"
    if not path.exists():
        return []
    specs: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            specs.append(line)
    return specs


def _spec_is_valid(spec_id: str, repo_root: Path) -> bool:
    spec_file = repo_root / "specs" / f"{spec_id}.md"
    if not spec_file.exists():
        return False
    registry = repo_root / "specs" / "SPECS_REGISTRY.md"
    if not registry.exists():
        return False
    return spec_id in registry.read_text(encoding="utf-8")


def _any_spec_touched_after_declaration(declared: list[str], repo_root: Path) -> bool:
    """True si al menos una spec declarada fue editada despues de .sdd/current-spec."""
    decl_path = repo_root / ".sdd" / "current-spec"
    if not decl_path.exists():
        return False
    decl_mtime = decl_path.stat().st_mtime
    for spec_id in declared:
        spec_file = repo_root / "specs" / f"{spec_id}.md"
        if spec_file.exists() and spec_file.stat().st_mtime > decl_mtime:
            return True
    return False


def decide(payload: dict[str, object], repo_root: Path) -> tuple[bool, str]:
    """Devuelve (permitir, motivo). Motivo solo es relevante cuando se bloquea."""
    tool_input = payload.get("tool_input")
    tinput = tool_input if isinstance(tool_input, dict) else {}
    raw_path = tinput.get("file_path") or tinput.get("path") or ""
    file_path = str(raw_path)
    if not file_path or not _is_source_path(file_path, repo_root):
        return True, ""

    declared = _declared_specs(repo_root)
    if not declared:
        return False, (
            "Edicion de codigo fuente bloqueada (gate spec-first): no hay spec "
            "vigente declarada. Declara la SPEC-NNN en .sdd/current-spec (o creala "
            "con sdd-spec). Ver docs/SDD-ENFORCEMENT.md."
        )
    invalid = [s for s in declared if not _spec_is_valid(s, repo_root)]
    if invalid:
        return False, (
            "Edicion de codigo fuente bloqueada (gate spec-first): spec(s) "
            f"declarada(s) invalida(s): {', '.join(invalid)}. Deben existir en "
            "specs/ y estar registradas en SPECS_REGISTRY.md."
        )
    if not _any_spec_touched_after_declaration(declared, repo_root):
        return False, (
            "Edicion de codigo fuente bloqueada (gate spec-first): la(s) spec(s) "
            f"declarada(s) ({', '.join(declared)}) no fueron editadas despues de "
            "declararlas en .sdd/current-spec. Edita la spec primero (agrega/actualiza "
            "el FR) y luego edita el codigo."
        )
    return True, ""


def _payloads_from_paths(paths: list[str], cwd: str) -> list[dict[str, object]]:
    return [{"tool_input": {"file_path": p}, "cwd": cwd} for p in paths]


def _payloads_from_stdin() -> list[dict[str, object]]:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    return [payload] if isinstance(payload, dict) else [{}]


def _repo_root_for(payload: dict[str, object]) -> Path:
    cwd = payload.get("cwd")
    start = Path(str(cwd)) if isinstance(cwd, str) and cwd else None
    return find_repo_root(start)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    cwd = os.getcwd()

    env_file = os.environ.get("SDD_GATE_FILE")
    if args:
        payloads = _payloads_from_paths(args, cwd)
    elif env_file:
        payloads = _payloads_from_paths([env_file], cwd)
    elif sys.stdin.isatty():
        return 0
    else:
        payloads = _payloads_from_stdin()

    reasons: list[str] = []
    for payload in payloads:
        allow, reason = decide(payload, _repo_root_for(payload))
        if not allow and reason:
            reasons.append(reason)
    if reasons:
        print("\n".join(reasons), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
