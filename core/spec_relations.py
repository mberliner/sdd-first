"""Escritura de la seccion "Relacion con specs existentes" (SPEC-023).

La *lectura* de la seccion vive en `check_traceability.py` y de ahi se consume
(FR-US2-011): el validador no escribe --un gate que modifica lo que valida deja
de ser gate-- pero tampoco puede haber dos ideas de que es la seccion, o el
validador rechazaria lo que el creador escribe. Aca vive lo que la modifica, que
usan `sdd_spec.py` (al crear con `--extends`/`--supersedes`/`--rationale`) y
`sdd_doctor.py` (al inyectar la seccion ausente y cerrar reciprocos).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_traceability import (  # noqa: E402
    RATIONALE_FIELD,
    RELATION_FIELDS,
    canonical_field,
    has_relation_section,
    is_empty_value,
    iter_relation_fields,
)

SECTION_TITLE = "Relación con specs existentes"

# La seccion se inyecta despues de las User Stories: se ancla en la primera de
# las secciones que siempre vienen despues. Se elige la que aparezca *antes* en
# el documento, no la primera de esta lista, porque no toda spec tiene las tres.
_ANCHORS = re.compile(
    r"(?i)^#+\s+(clarifications|acceptance scenarios|functional requirements)\b"
)


def empty_section() -> str:
    """El bloque con los seis campos vacios, tal como lo declara SPEC-FORMAT.md."""
    return (
        f"## {SECTION_TITLE}\n"
        "\n"
        "- **Extiende:** — | **Supersede:** — | **Depende de:** —\n"
        "- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —\n"
        f"- **{RATIONALE_FIELD}:** —\n"
    )


def link(spec_id: str, archivo: str) -> str:
    """Referencia en la forma que usa el resto del registro: `[SPEC-NNN](archivo)`."""
    return f"[{spec_id}]({archivo})"


def inject_section(text: str) -> str:
    """Devuelve `text` con la seccion vacia insertada (o tal cual si ya la tiene)."""
    if has_relation_section(text):
        return text
    lines = text.splitlines()
    bloque = empty_section().splitlines()
    destino = next(
        (i for i, line in enumerate(lines) if _ANCHORS.match(line.strip())),
        None,
    )
    if destino is None:
        cuerpo = [*lines, "", *bloque]
    else:
        cuerpo = [*lines[:destino], *bloque, "", *lines[destino:]]
    return "\n".join(cuerpo).rstrip() + "\n"


def _rewrite_field(text: str, campo: str, nuevo_valor) -> str | None:  # type: ignore[no-untyped-def]
    """Reemplaza el valor de `campo` por `nuevo_valor(valor_actual)`.

    Devuelve `None` si la seccion no declara ese campo: el llamador decide si eso
    es un aborto (crear con `--extends`) o un problema a reportar (el doctor).
    """
    lines = text.splitlines()
    for i, j, match in iter_relation_fields(text):
        if canonical_field(match.group(1)) != campo:
            continue
        celdas = lines[i].split("|")
        celda = celdas[j]
        valor = nuevo_valor(match.group(2).strip())
        if valor is None:
            return text
        cabeza = celda[: match.start(2)]
        cola = celda[len(celda.rstrip()) :]
        celdas[j] = f"{cabeza} {valor}{cola}"
        lines[i] = "|".join(celdas)
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return None


def add_reference(text: str, campo: str, referencia: str) -> str | None:
    """Agrega `referencia` al campo, respetando lo que ya haya declarado.

    Un campo puede llevar varias referencias --una spec puede extender a dos--,
    asi que el valor previo se conserva y la nueva se apenda. Si la spec ya esta
    referenciada en ese campo, el texto vuelve intacto: la operacion es
    repetible (FR-US2-011) y correrla dos veces no duplica el enlace.
    """
    if campo not in RELATION_FIELDS:
        raise ValueError(f"'{campo}' no es un campo de enlace de la seccion.")
    objetivo = re.search(r"\bSPEC-\d+\b", referencia)

    def nuevo(valor: str) -> str | None:
        if objetivo and objetivo.group(0) in valor:
            return None
        return referencia if is_empty_value(valor) else f"{valor}, {referencia}"

    return _rewrite_field(text, campo, nuevo)


def set_rationale(text: str, texto: str) -> str | None:
    """Escribe el motivo por el que la capacidad no cabe en una spec existente."""
    return _rewrite_field(text, RATIONALE_FIELD, lambda _valor: texto)
