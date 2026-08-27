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

Declarado no es ejecutado (SPEC-020 US2): corriendo dentro de `core/pipeline.py`
tambien verifica que el paso de cada principio haya corrido de verdad, leyendo
los pasos ya ejecutados del canal que el pipeline publica. Un paso declarado
pero omitido en runtime -- sin tool, sin targets, sin umbrales -- deja el
principio sin verificar: no es un error de la constitucion, pero tampoco un
verde limpio. Por eso conviene declarar `constitution` DESPUES de los pasos que
enforzan principios; si corre antes, lo reporta en vez de callarlo.

Uso:
    python core/check_constitution.py CONSTITUTION.md

Exit codes: 0 todo OK, 1 referencia rota o version malformada, 4 principios sin
enforcement ejecutado en esta corrida (EXIT_RESERVAS).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd_config import (  # noqa: E402
    EXIT_RESERVAS,
    PIPELINE_STEPS_RUN_ENV,
    forzar_salida_utf8,
    load,
)

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
    """El token nombra un archivo: ruta explicita o basename con extension.

    Antes exigia `/` o punto inicial, y los enforcements se escriben como
    basename (`check_naming.py`): ninguno se verificaba, asi que renombrar o
    borrar un check no lo detectaba el gate que existe para eso (SPEC-001
    FR-010). La extension es lo que separa un archivo de un paquete
    (`pytest-cov`), sin necesidad de una lista de extensiones conocidas.
    """
    return "/" in token or token.startswith(".") or bool(PurePosixPath(token).suffix)


def _basenames_del_repo(repo_root: Path) -> set[str]:
    """Nombres de archivo presentes en el repo, para resolver un token sin ruta.

    Se saltean los directorios ocultos (`.git`, `.venv`) y los `__pycache__`:
    es una regla estructural, no una lista de nombres del dominio.
    """
    nombres: set[str] = set()
    pendientes = [repo_root]
    while pendientes:
        actual = pendientes.pop()
        try:
            entradas = list(actual.iterdir())
        except OSError:
            continue
        for entrada in entradas:
            if entrada.is_dir():
                if not entrada.name.startswith(".") and entrada.name != "__pycache__":
                    pendientes.append(entrada)
            else:
                nombres.add(entrada.name)
    return nombres


def _referencia_existe(token: str, repo_root: Path, basenames: set[str]) -> bool:
    if "/" in token or token.startswith("."):
        return (repo_root / token).exists()
    return token in basenames


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
    basenames = _basenames_del_repo(repo_root)
    for p in principles:
        tokens = [(t, "Detalle") for t in p.detalle]
        tokens += [(t, "Enforcement") for t in p.enforcement]

        if not p.detalle:
            errors.append(f"Principio '{p.title}' sin linea Detalle.")
        if not p.enforcement:
            errors.append(f"Principio '{p.title}' sin linea Enforcement.")

        for token, field in tokens:
            if _is_path(token) and not _referencia_existe(token, repo_root, basenames):
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


def _check_ejecucion(
    principles: list[_Principle],
    pipeline_steps: list[str],
    enforcement_steps: dict[str, str],
    reservas: list[str],
) -> None:
    """Principios cuyo paso de enforcement no llego a correr (SPEC-020 FR-US2-002).

    Complementa a `_check_references`, que verifica que el enforcement este
    *declarado*: un paso declarado pero omitido en runtime -- sin tool, sin
    targets, sin umbrales -- deja el principio sin verificar, y hasta esta
    historia el pipeline decia VERDE igual.

    Solo corre dentro de un pipeline: la lista de pasos ejecutados la publica
    `core/pipeline.py` (FR-US2-001). Sin la variable de entorno no hay nada que
    evaluar y el llamador no invoca esta funcion (FR-US2-005).
    """
    ejecutados = {s for s in os.environ[PIPELINE_STEPS_RUN_ENV].split(",") if s}
    # Frontera entre lo que quedo atras y lo que falta: la posicion del ultimo
    # paso ejecutado en el orden declarado. Un paso ausente antes de esa marca
    # se omitio; despues, todavia no le toco. Asi el mensaje es exacto tambien
    # cuando `constitution` corre en el medio, que es el caso que una
    # heuristica del tipo "¿ya corrio alguno?" contaba mal.
    ultimo = max(
        (i for i, s in enumerate(pipeline_steps) if s in ejecutados), default=-1
    )

    for p in principles:
        for token in p.enforcement:
            step = enforcement_steps.get(token.rsplit("/", 1)[-1])
            # Sin `step`, el enforcement no pasa por el pipeline (FR-004): no
            # hay paso que esperar. Sin cablear ya es error de _check_references,
            # y no hay que decirlo dos veces.
            if step is None or step not in pipeline_steps or step in ejecutados:
                continue
            # Distinguir el omitido del pendiente le dice al lector si le falta
            # tooling o si tiene `constitution` declarado demasiado temprano.
            motivo = (
                f"el paso '{step}' se omitio: no verifico nada"
                if pipeline_steps.index(step) < ultimo
                else f"el paso '{step}' todavia no se ejecuto en esta corrida"
            )
            reservas.append(f"Principio '{p.title}' ({token}): {motivo}.")


def main(argv: list[str]) -> int:
    forzar_salida_utf8()

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
    reservas: list[str] = []
    _check_version(version_line, errors)
    if not principles:
        errors.append("No se encontraron principios bajo '## Principios'.")
    _check_references(principles, repo_root, wired_steps, cfg.enforcement_steps, errors)
    # Solo dentro de un pipeline: sin el canal no hay corrida de la que hablar y
    # el check se comporta como antes de SPEC-020 US2 (FR-US2-005).
    if PIPELINE_STEPS_RUN_ENV in os.environ:
        _check_ejecucion(
            principles, cfg.pipeline_steps, cfg.enforcement_steps, reservas
        )

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

    if reservas:
        # No es violacion de integridad: la constitucion esta bien escrita y bien
        # cableada. Lo que falta es que el enforcement haya corrido, asi que el
        # paso no falla -- condiciona el verde (SPEC-020 FR-US2-003).
        print("\nPrincipios sin enforcement ejecutado en esta corrida:")
        for r in reservas:
            print(f"  ! {r}")
        print(
            f"\nTotal: {len(reservas)} principio(s) sin verificar. "
            "El paso no falla, pero el verde del pipeline queda con reservas."
        )
        return EXIT_RESERVAS

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
