"""`.sdd/kit.lock`: manifiesto de lo que el kit entregó en una instalación.

SPEC-025 FR-US1-002/003. El lock es la línea base contra la que se mide toda
edición posterior — **no** una foto del disco: `build_lock` arma su contenido
leyendo únicamente las plantillas del kit (`templates/`, con los placeholders
resueltos), nunca el proyecto instalado. Eso es lo que hace que una
instalación brownfield o un conflicto sin resolver registren el hash de lo que
el kit entrega, no el del archivo del dueño — si registrara el del disco, la
actualización siguiente daría esa plantilla por intacta y la pisaría en
silencio (el daño que esta spec existe para impedir).

Formato JSON determinista (claves ordenadas, indentación fija): lo maneja la
biblioteca estándar sin depender de `pyyaml`, nadie lo edita a mano, y la
escritura determinista acota el diff de una actualización a los archivos que
cambiaron.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sdd_catalog  # noqa: E402
import sdd_init  # noqa: E402
from sdd_config import KIT_VERSION, hash_bytes, write_text_lf  # noqa: E402

LOCK_RELPATH = Path(".sdd") / "kit.lock"
ALGORITHM = "sha256"

_REQUIRED_KEYS = ("kit_version", "algorithm", "plantillas", "semillas")


class LockIlegible(Exception):
    """`.sdd/kit.lock` existe pero no se pudo interpretar (SPEC-025 FR-US3-006).

    No degrada a "sin lock": el archivo se versiona, así que uno roto suele ser
    un conflicto de merge sin resolver, y tratarlo como ausente le haría perder
    al proyecto su línea base sin que nadie se entere.
    """


@dataclass(frozen=True)
class Lock:
    kit_version: str
    algorithm: str
    substitutions: dict[str, str] = field(default_factory=dict)
    plantillas: dict[str, str] = field(default_factory=dict)
    semillas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "kit_version": self.kit_version,
            "algorithm": self.algorithm,
            "substitutions": dict(self.substitutions),
            "plantillas": dict(self.plantillas),
            "semillas": list(self.semillas),
        }


def write_lock(target: Path, lock: Lock) -> None:
    """Escribe el lock como JSON determinista (claves ordenadas, indent=2)."""
    path = target / LOCK_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(lock.to_dict(), sort_keys=True, indent=2, ensure_ascii=False)
    write_text_lf(path, texto + "\n")


def load_lock(target: Path) -> Lock | None:
    """Lee `.sdd/kit.lock`, o `None` si no existe.

    Levanta `LockIlegible` si el archivo existe pero no es JSON válido o le
    faltan las claves mínimas — eso no degrada a "sin lock" (FR-US3-006).
    """
    path = target / LOCK_RELPATH
    if not path.exists():
        return None
    try:
        texto = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LockIlegible(f"no se pudo leer {path}: {exc}") from exc
    try:
        crudo = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise LockIlegible(f"{path} no es JSON válido: {exc}") from exc
    if not isinstance(crudo, dict) or not all(k in crudo for k in _REQUIRED_KEYS):
        faltantes = (
            ", ".join(k for k in _REQUIRED_KEYS if k not in crudo)
            if isinstance(crudo, dict)
            else "(no es un objeto)"
        )
        raise LockIlegible(f"{path} no tiene las claves mínimas: {faltantes}")
    return Lock(
        kit_version=str(crudo["kit_version"]),
        algorithm=str(crudo["algorithm"]),
        substitutions={
            str(k): str(v) for k, v in (crudo.get("substitutions") or {}).items()
        },
        plantillas={str(k): str(v) for k, v in (crudo.get("plantillas") or {}).items()},
        semillas=[str(x) for x in (crudo.get("semillas") or [])],
    )


def build_lock(kit_root: Path, target: Path, name: str, domain: str) -> Lock:
    """Arma el lock desde lo que el kit entrega ahora — nunca desde el disco.

    Por cada `plantilla` del catálogo, hashea `templates/<src>` con los
    placeholders resueltos (`name`/`domain`): es la línea base del kit, no una
    foto de lo que quedó instalado. Para `semilla`, sí mira `target`: qué de
    `SEMILLA_DESTINOS` ya existe ahí (solo se registra presencia, nunca hash —
    una semilla no se actualiza, así que nadie compararía ese hash).
    """
    templates = kit_root / "templates"
    plantillas: dict[str, str] = {}
    for src_rel, dst_rel in sdd_catalog.catalogo_plantillas():
        if sdd_catalog.clase_de(dst_rel) != sdd_catalog.Clase.PLANTILLA:
            continue
        texto = sdd_init._substitute(
            (templates / src_rel).read_text(encoding="utf-8"), name, domain
        )
        plantillas[Path(dst_rel).as_posix()] = hash_bytes(texto.encode("utf-8"))
    semillas = sorted(
        dst_rel
        for dst_rel in sdd_catalog.SEMILLA_DESTINOS
        if (target / dst_rel).exists()
    )
    return Lock(
        kit_version=KIT_VERSION,
        algorithm=ALGORITHM,
        substitutions={"project.name": name, "project.domain": domain},
        plantillas=plantillas,
        semillas=semillas,
    )
