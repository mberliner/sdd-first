"""Verificador de integridad de la constitucion (nucleo del kit).

Implementa el Constitution Check: confirma que cada principio referencia SSOTs
que existen, que su enforcement automatico esta efectivamente activo en el
pipeline declarado (`pipeline.steps` de .sdd/config.yaml), y que la linea de
version esta bien formada. Imprime los principios para darles visibilidad.

A diferencia del original (que hardcodeaba PIPELINE_TOOLS y buscaba en un
pipeline_local.sh fijo), aqui el cableado se verifica contra los pasos
declarados en el config, de modo que es agnostico del layout y del lenguaje.

Que tool corresponde a que paso tambien sale del config: cada principio declara
su `step` (SPEC-020). Este modulo no conoce ninguna tool por nombre, asi que un
principio propio obtiene la misma verificacion que los del kit.

Uso:
    python core/check_constitution.py CONSTITUTION.md

Exit code 0 si todo OK, 1 si hay referencia rota o version malformada.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd_config import load  # noqa: E402

_BACKTICK = re.compile(r"`([^`]+)`")
_SEMVER = re.compile(r"\b\d+\.\d+\.\d+\b")
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


class _Principle:
    def __init__(self, title: str) -> None:
        self.title = title
        self.enforcement: list[str] = []
        self.detalle: list[str] = []


def _parse(text: str) -> tuple[str | None, list[_Principle]]:
    version_line: str | None = None
    principles: list[_Principle] = []
    section: str | None = None
    current: _Principle | None = None

    for raw in text.splitlines():
        line = raw.strip()

        if version_line is None and line.startswith("**Versión:**"):
            version_line = line

        if line.startswith("## "):
            section = line[3:].strip().lower()
            current = None
            continue

        if section == "principios":
            if line.startswith("### "):
                current = _Principle(line[4:].strip())
                principles.append(current)
            elif current is not None and line.startswith("- **Enforcement:**"):
                current.enforcement.extend(_BACKTICK.findall(line))
            elif current is not None and line.startswith("- **Detalle:**"):
                current.detalle.extend(_BACKTICK.findall(line))

    return version_line, principles


def _is_path(token: str) -> bool:
    return "/" in token or token.startswith(".")


def _check_version(version_line: str | None, errors: list[str]) -> None:
    if version_line is None:
        errors.append("Falta la linea de version (**Versión:** X.Y.Z | ...).")
        return
    if not _SEMVER.search(version_line):
        errors.append(f"Version sin semver valido: {version_line!r}")
    if len(_ISO_DATE.findall(version_line)) < 2:
        errors.append(
            f"Version debe incluir Ratificada y Última enmienda (YYYY-MM-DD): {version_line!r}"
        )


def _check_references(
    principles: list[_Principle],
    repo_root: Path,
    wired_steps: set[str],
    enforcement_steps: dict[str, str],
    errors: list[str],
) -> None:
    for p in principles:
        tokens = [(t, "Detalle") for t in p.detalle]
        tokens += [(t, "Enforcement") for t in p.enforcement]

        if not p.detalle:
            errors.append(f"Principio '{p.title}' sin linea Detalle.")
        if not p.enforcement:
            errors.append(f"Principio '{p.title}' sin linea Enforcement.")

        for token, field in tokens:
            if _is_path(token) and not (repo_root / token).exists():
                errors.append(
                    f"Principio '{p.title}' {field}: referencia inexistente '{token}'."
                )

        for token in p.enforcement:
            name = token.rsplit("/", 1)[-1]
            # Sin `step` declarado en el config no se verifica cableado: el
            # enforcement corre por otra via (hooks, convencion) y exigirle un
            # paso de pipeline seria falso (SPEC-020 FR-004).
            step = enforcement_steps.get(name)
            if step is not None and step not in wired_steps:
                errors.append(
                    f"Principio '{p.title}' Enforcement '{token}' no esta activo: "
                    f"falta el paso '{step}' en pipeline.steps de .sdd/config.yaml."
                )


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    if len(argv) < 2:
        print("Uso: check_constitution.py <CONSTITUTION.md>", file=sys.stderr)
        return 2

    constitution = Path(argv[1])
    if not constitution.exists():
        print(f"No existe: {constitution}", file=sys.stderr)
        return 2

    repo_root = constitution.resolve().parent
    text = constitution.read_text(encoding="utf-8")
    version_line, principles = _parse(text)

    cfg = load(repo_root)
    wired_steps = set(cfg.pipeline_steps)

    errors: list[str] = []
    _check_version(version_line, errors)
    if not principles:
        errors.append("No se encontraron principios bajo '## Principios'.")
    _check_references(principles, repo_root, wired_steps, cfg.enforcement_steps, errors)

    print(f"Constitucion: {len(principles)} principio(s) activo(s)")
    for p in principles:
        print(f"  - {p.title}")

    if errors:
        print("\nViolaciones de integridad de la constitucion:", file=sys.stderr)
        for e in errors:
            print(f"  x {e}", file=sys.stderr)
        print(
            f"\nTotal: {len(errors)} problema(s). Ver CONSTITUTION.md (seccion Governance).",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
