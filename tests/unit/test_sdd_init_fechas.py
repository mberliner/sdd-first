"""La fecha se sustituye por marcador, no por el literal `YYYY-MM-DD`.

SPEC-014 FR-US2-008, FR-US2-009.
"""

from __future__ import annotations

from pathlib import Path

import sdd_catalog
import sdd_init
import sdd_lock
from sdd_config import hash_bytes

KIT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = KIT_ROOT / "templates"


def _plantillas_del_catalogo() -> list[tuple[str, str]]:
    return [
        (src, dst)
        for src, dst in sdd_catalog.catalogo_plantillas()
        if sdd_catalog.clase_de(dst) == sdd_catalog.Clase.PLANTILLA
    ]


def test_plantillas_instaladas_conservan_el_placeholder_de_fecha(tmp_path):
    """FR-US2-008: lo que el dueno va a usar despues sigue diciendo YYYY-MM-DD.

    `SPEC-TEMPLATE.md` se copia cada vez que se crea una spec y `clarify.md` le
    dicta al asistente bajo que encabezado grabar la sesion: si la instalacion
    les cuece su fecha, toda spec futura nace fechada el dia de la instalacion.
    """
    sdd_init.main([str(tmp_path), "--language=none"])

    plantilla = (tmp_path / "specs" / "SPEC-TEMPLATE.md").read_text(encoding="utf-8")
    assert "### Session YYYY-MM-DD" in plantilla
    assert "- YYYY-MM-DD: creada (draft)." in plantilla

    clarify = (tmp_path / "docs" / "playbooks" / "clarify.md").read_text(
        encoding="utf-8"
    )
    assert "### Session YYYY-MM-DD" in clarify


def test_historial_sembrado_lleva_la_fecha_real(tmp_path):
    """FR-US2-008: el marcador `{{today}}` se resuelve donde si corresponde."""
    import datetime as _dt

    sdd_init.main([str(tmp_path), "--language=none"])
    historial = (tmp_path / "historial" / "sdd.md").read_text(encoding="utf-8")
    assert _dt.date.today().isoformat() in historial
    assert "{{today}}" not in historial


def test_ninguna_plantilla_del_catalogo_cambia_de_hash_con_el_dia():
    """FR-US2-008: hash estable en el tiempo.

    Es la regresion que cierra la clase de bug: si una plantilla resuelve
    distinto segun el dia, `sdd-update` la clasifica `actualizar` —intacta
    respecto del lock, distinta de lo que el kit entrega hoy— y la reescribe
    sola en cada corrida hecha otro dia.
    """
    distintos = []
    for src_rel, dst_rel in _plantillas_del_catalogo():
        crudo = (TEMPLATES / src_rel).read_text(encoding="utf-8")
        hashes = {
            hash_bytes(
                sdd_init._substitute(crudo, "demo", "un dominio", fecha).encode("utf-8")
            )
            for fecha in ("2026-01-01", "2026-06-15")
        }
        if len(hashes) > 1:
            distintos.append(dst_rel)
    assert distintos == []


def test_substitute_no_toca_el_literal_de_fecha():
    """FR-US2-008: solo el marcador se sustituye."""
    texto = "### Session YYYY-MM-DD y {{today}}"
    resuelto = sdd_init._substitute(texto, "demo", "dominio", "2026-01-01")
    assert resuelto == "### Session YYYY-MM-DD y 2026-01-01"


def test_lock_registra_la_fecha_usada(tmp_path):
    """FR-US2-009: la fecha queda en el lock, como cualquier otra sustitucion."""
    sdd_init.main([str(tmp_path), "--language=none"])
    lock = sdd_lock.load_lock(tmp_path)
    assert lock is not None
    import datetime as _dt

    assert lock.substitutions["today"] == _dt.date.today().isoformat()


def test_la_fecha_del_lock_no_dispara_el_aviso_de_sustituciones_cambiadas(tmp_path):
    """FR-US2-009: el aviso mira nombre y dominio, no el calendario."""
    import sdd_config
    import sdd_update

    sdd_init.main([str(tmp_path), "--language=none"])
    lock = sdd_lock.load_lock(tmp_path)
    assert lock is not None
    lock.substitutions["today"] = "1999-12-31"

    sdd_config.load.cache_clear()
    cfg = sdd_config.load(tmp_path)
    plan = sdd_update.construir_plan(KIT_ROOT, tmp_path, cfg, lock)
    assert plan.substitutions_cambiaron is False
