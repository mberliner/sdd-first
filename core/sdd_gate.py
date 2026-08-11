"""Interlock de autoria spec-first (nucleo minimo del kit, Principio de gate).

Gate de enforcement *anterior* a que el codigo exista: bloquea la edicion/commit
de codigo fuente si no hay una spec vigente declarada en `.sdd/current-spec` con
requisitos escritos (SPEC-017, SSOT de la politica). La logica de decision
(`decide`) es agnostica de asistente; el modulo acepta tres transportes:

1. **argv**: `python core/sdd_gate.py src/a.py` — usado por pre-commit y hooks
   que pasan rutas como argumentos.
2. **stdin JSON**: protocolo `PreToolUse` de Claude Code.

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
from check_traceability import _parse_registry, has_written_requirements  # noqa: E402
from sdd_config import DEFAULT_SOURCE_ROOT, find_sdd_root, load  # noqa: E402

# Estados de SPECS_REGISTRY.md que dejan pasar el gate (SPEC-017 FR-US2-002).
_VALID_ESTADOS = frozenset({"draft", "active"})

# Escape hatch acotado al gate (SPEC-017 FR-US3-004). La alternativa historica
# era `--no-verify`, que ademas apaga trazabilidad y reset post-commit.
_BYPASS_ENV = "SDD_GATE_BYPASS"


def _source_roots(repo_root: Path) -> list[str]:
    try:
        return load(repo_root).source_roots
    except SystemExit:
        # PyYAML ausente: degradar al default clasico en vez de romper el gate.
        return [DEFAULT_SOURCE_ROOT]


def is_source_path(file_path: str, repo_root: Path) -> bool:
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


def _registry_row(spec_id: str, repo_root: Path):  # type: ignore[no-untyped-def]
    """Fila de SPECS_REGISTRY.md cuyo Archivo matchea `spec_id`, o None."""
    registry = repo_root / "specs" / "SPECS_REGISTRY.md"
    if not registry.exists():
        return None
    errors: list[str] = []
    for row in _parse_registry(registry, errors):
        if row.archivo == f"{spec_id}.md":
            return row
    return None


def _spec_invalid_reason(spec_id: str, repo_root: Path) -> str | None:
    """None si `spec_id` esta vigente (draft/active); si no, el motivo del rechazo.

    SPEC-017 FR-US2-001: parseo real de la fila y su estado, no substring-match
    sobre el texto crudo del registro (bypasseable con specs archived o
    superseded mencionadas en prosa).
    """
    spec_file = repo_root / "specs" / f"{spec_id}.md"
    if not spec_file.exists():
        return "no existe el archivo de spec"
    row = _registry_row(spec_id, repo_root)
    if row is None:
        return "no esta registrada en SPECS_REGISTRY.md"
    if row.estado not in _VALID_ESTADOS:
        return f"estado '{row.estado}' no vigente (debe ser draft o active)"
    return None


def _has_written_requirements(spec_file: Path) -> bool:
    """True si la spec declara al menos un FR con texto propio.

    Evidencia de que la spec precede al codigo (SPEC-017 FR-US3-001). Sustituye
    al criterio anterior, que comparaba la mtime de la spec contra la de
    `.sdd/current-spec`: la mtime es un proxy del contenido que renuevan
    checkout, clone y el ciclo stash/restore de pre-commit —bloqueando el flujo
    legitimo de varios commits por spec— y que un `touch` satisface —no
    deteniendo a quien quiera saltearlo—. El contenido es determinista, no
    necesita git y da la misma respuesta en cualquier maquina.

    El criterio de "FR escrito" lo aporta `check_traceability`, no este modulo:
    `sdd_spec.py --reuse` lo aplica al FR que adopta y tiene que dar el mismo
    veredicto que el gate (SPEC-022 FR-US1-005).
    """
    try:
        text = spec_file.read_text(encoding="utf-8")
    except OSError:
        return False
    return has_written_requirements(text)


def _specs_sin_requisitos(declared: list[str], repo_root: Path) -> list[str]:
    """Specs declaradas que todavia no tienen requisitos escritos.

    Se evalua cada una (FR-US3-002): el criterio anterior se conformaba con que
    *alguna* estuviera tocada, asi que declarar dos specs y escribir una
    habilitaba las dos.
    """
    return [
        spec_id
        for spec_id in declared
        if not _has_written_requirements(repo_root / "specs" / f"{spec_id}.md")
    ]


def _declared_file_path(payload: dict[str, object]) -> str:
    """Ruta que el payload declara editar ("" si no declara ninguna)."""
    tool_input = payload.get("tool_input")
    tinput = tool_input if isinstance(tool_input, dict) else {}
    if tinput:
        return str(tinput.get("file_path") or tinput.get("path") or "")

    # Antigravity hook format (PreToolUse)
    tool_call = payload.get("toolCall")
    if isinstance(tool_call, dict):
        args = tool_call.get("args")
        if isinstance(args, dict):
            return str(args.get("TargetFile") or "")

    return ""


def _aviso_de_reuso(file_path: str, repo_root: Path, indexador) -> str:  # type: ignore[no-untyped-def]
    """Que specs ya gobiernan este archivo, para poder reusar una (FR-US3-001).

    Es el momento exacto en que la pregunta importa: el archivo concreto ya se
    conoce. Puramente informativo -- no cambia *que* se bloquea, cuyo SSOT es
    SPEC-017 -- asi que un indice vacio o un fallo al computarlo devuelven vacio
    y el bloqueo sale con su mensaje de siempre (FR-US3-003).
    """
    try:
        if indexador is None:
            import spec_index

            indexador = spec_index.specs_for_path
        specs = indexador(file_path, repo_root)
    except Exception:
        return ""
    if not specs:
        return ""
    detalle = "; ".join(f"{spec_id} ({titulo})" for spec_id, titulo in specs)
    return (
        f"\nEspecs que ya gobiernan '{file_path}': {detalle}. Si la capacidad "
        "cabe en alguna, escribi ahi el requisito nuevo y adoptala con "
        "sdd_spec.py --reuse SPEC-NNN --fr FR-NNN, en vez de crear otra spec."
    )


def decide(
    payload: dict[str, object],
    repo_root: Path,
    *,
    indexador=None,  # type: ignore[no-untyped-def]
) -> tuple[bool, str]:
    """Devuelve (permitir, motivo). Motivo solo es relevante cuando se bloquea.

    `indexador` existe para inyectarlo desde los tests: el gate corre en cada
    `PreToolUse` y no puede pagar un escaneo del repositorio por edicion
    permitida, asi que el indice se computa **solo** en el camino de bloqueo
    (FR-US3-002).
    """
    file_path = _declared_file_path(payload)
    if not file_path or not is_source_path(file_path, repo_root):
        return True, ""

    declared = _declared_specs(repo_root)
    if not declared:
        return False, (
            "Edicion de codigo fuente bloqueada (gate spec-first): no hay spec "
            "vigente declarada. Declara la SPEC-NNN en .sdd/current-spec (o creala "
            "con sdd-spec). Ver docs/SDD-ENFORCEMENT.md."
            + _aviso_de_reuso(file_path, repo_root, indexador)
        )
    invalid = {
        s: reason
        for s in declared
        for reason in [_spec_invalid_reason(s, repo_root)]
        if reason is not None
    }
    if invalid:
        detalle = "; ".join(f"{s} ({reason})" for s, reason in invalid.items())
        return False, (
            "Edicion de codigo fuente bloqueada (gate spec-first): spec(s) "
            f"declarada(s) invalida(s) — {detalle}. Deben existir en specs/ y "
            "estar registradas en SPECS_REGISTRY.md con estado draft o active."
            + _aviso_de_reuso(file_path, repo_root, indexador)
        )
    sin_requisitos = _specs_sin_requisitos(declared, repo_root)
    if sin_requisitos:
        return False, (
            "Edicion de codigo fuente bloqueada (gate spec-first): la(s) spec(s) "
            f"declarada(s) ({', '.join(sin_requisitos)}) no tiene(n) requisitos "
            "escritos. Escribi los FR (**FR-NNN** MUST: ...) antes de tocar codigo. "
            "Ver docs/SDD-ENFORCEMENT.md."
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


def _repo_root_for(payload: dict[str, object]) -> Path | None:
    """Raiz SDD que gobierna este payload, o None si la edicion no cae en ninguna.

    Se prueba el `cwd` y despues la ruta del archivo. Antes se usaba solo el
    `cwd` via `find_repo_root`, que ante la falta de marcadores devolvia ese
    mismo directorio: `is_source_path` no reconocia nada como codigo y la
    edicion pasaba en silencio (SPEC-014 FR-US1-003). Lo que decide si hay
    protocolo que aplicar no es desde donde se invoca al gate sino **de que
    proyecto es el archivo**; el `cwd` es solo la pista mas barata.
    """
    for candidato in (payload.get("cwd"), _declared_file_path(payload)):
        if not isinstance(candidato, str) or not candidato:
            continue
        root = find_sdd_root(Path(candidato))
        if root is not None:
            return root
    return None


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    cwd = os.getcwd()

    if args:
        payloads = _payloads_from_paths(args, cwd)
    elif sys.stdin.isatty():
        return 0
    else:
        payloads = _payloads_from_stdin()

    reasons: list[str] = []
    for payload in payloads:
        repo_root = _repo_root_for(payload)
        if repo_root is None:
            # La edicion no pertenece a ningun proyecto SDD: no hay spec que
            # exigir ni config que consultar (SPEC-014 FR-US1-003).
            continue
        allow, reason = decide(payload, repo_root)
        if not allow and reason:
            reasons.append(reason)
    if not reasons:
        return 0

    # Se imprime siempre lo que se estaria bloqueando: un bypass silencioso es
    # indistinguible de un gate que no corre (SPEC-017 FR-US3-004).
    print("\n".join(reasons), file=sys.stderr)
    bypass = os.environ.get(_BYPASS_ENV, "").strip()
    if bypass:
        print(
            f"{_BYPASS_ENV} activo - se permite igual. Motivo: {bypass}",
            file=sys.stderr,
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
