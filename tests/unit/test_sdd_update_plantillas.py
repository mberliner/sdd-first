"""Política de conflicto sobre `plantilla`: qué se pisa, qué se conserva.

SPEC-025 FR-US2-005, FR-US2-006, FR-US2-008, FR-US2-012.
"""

from __future__ import annotations

import sdd_catalog
import sdd_config
import sdd_init
import sdd_lock
import sdd_update
from conftest import requiere_permisos_posix


def _instalar(tmp_path):
    sdd_init.main([str(tmp_path), "--language=python"])
    sdd_config.load.cache_clear()


def test_editada_no_se_pisa_y_deja_kit_new(tmp_path):
    """FR-US2-005: una plantilla que el dueño editó nunca se pisa; la version
    del kit queda en `<archivo>.kit-new`."""
    _instalar(tmp_path)
    original = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(original + "\nEDITADO\n", encoding="utf-8")
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0
    assert (tmp_path / "AGENTS.md").read_text(
        encoding="utf-8"
    ) == original + "\nEDITADO\n"
    assert (tmp_path / "AGENTS.md.kit-new").exists()


def test_intacta_se_pisa_sin_preguntar_si_el_kit_cambio(tmp_path):
    """FR-US2-005: una plantilla intacta se actualiza sin intervención."""
    _instalar(tmp_path)
    lock_path = tmp_path / sdd_lock.LOCK_RELPATH
    import json

    crudo = json.loads(lock_path.read_text(encoding="utf-8"))
    crudo["plantillas"]["README.md"] = "0" * 64  # simula que el kit trae otra version
    lock_path.write_text(json.dumps(crudo), encoding="utf-8")
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0
    assert not (tmp_path / "README.md.kit-new").exists()


def test_sin_lock_ninguna_plantilla_presente_se_pisa(tmp_path):
    """FR-US2-006: modo degradado -- sin lock, todo lo presente es conflicto."""
    _instalar(tmp_path)
    (tmp_path / sdd_lock.LOCK_RELPATH).unlink()
    original = (tmp_path / "README.md").read_text(encoding="utf-8")
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == original
    assert (tmp_path / sdd_lock.LOCK_RELPATH).exists(), "queda lock escrito al terminar"


def test_plantilla_ausente_que_el_lock_tenia_no_se_reinstala(tmp_path):
    """FR-US2-005: el dueño la borró a propósito; sdd-update no la repone."""
    _instalar(tmp_path)
    (tmp_path / "docs" / "DEVELOPMENT.md").unlink()
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0
    assert not (tmp_path / "docs" / "DEVELOPMENT.md").exists()


def test_alta_del_catalogo_en_ruta_libre_se_instala_y_entra_al_lock(
    tmp_path, monkeypatch
):
    """FR-US2-012: una plantilla nueva del kit (ruta libre) es alta."""
    _instalar(tmp_path)
    nueva = ("docs/DEVELOPMENT.md", "docs/NUEVA-CAPACIDAD.md")
    monkeypatch.setattr(sdd_catalog, "STATIC_DOCS", [*sdd_catalog.STATIC_DOCS, nueva])
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0
    assert (tmp_path / "docs" / "NUEVA-CAPACIDAD.md").exists()
    lock = sdd_lock.load_lock(tmp_path)
    assert "docs/NUEVA-CAPACIDAD.md" in lock.plantillas


def test_alta_del_catalogo_en_ruta_ocupada_es_conflicto(tmp_path, monkeypatch):
    """FR-US2-012/ANA-043: si el dueño ya tiene un archivo propio ahi, no se
    pisa -- es conflicto, no alta."""
    _instalar(tmp_path)
    (tmp_path / "docs" / "OCUPADA.md").write_text("mio\n", encoding="utf-8")
    nueva = ("docs/DEVELOPMENT.md", "docs/OCUPADA.md")
    monkeypatch.setattr(sdd_catalog, "STATIC_DOCS", [*sdd_catalog.STATIC_DOCS, nueva])
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0
    assert (tmp_path / "docs" / "OCUPADA.md").read_text(encoding="utf-8") == "mio\n"
    assert (tmp_path / "docs" / "OCUPADA.md.kit-new").exists()


def test_baja_del_catalogo_intacta_se_elimina(tmp_path, monkeypatch):
    """FR-US2-012: una plantilla que el kit ya no trae, y que coincide con el
    lock, se elimina."""
    _instalar(tmp_path)
    retirados = [e for e in sdd_catalog.STATIC_DOCS if e[1] != "docs/DEVELOPMENT.md"]
    monkeypatch.setattr(sdd_catalog, "STATIC_DOCS", retirados)
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0
    assert not (tmp_path / "docs" / "DEVELOPMENT.md").exists()


def test_baja_del_catalogo_editada_se_conserva_y_reporta(tmp_path, monkeypatch, capsys):
    """FR-US2-012: si la plantilla retirada fue editada, se conserva."""
    _instalar(tmp_path)
    (tmp_path / "docs" / "DEVELOPMENT.md").write_text("mio\n", encoding="utf-8")
    retirados = [e for e in sdd_catalog.STATIC_DOCS if e[1] != "docs/DEVELOPMENT.md"]
    monkeypatch.setattr(sdd_catalog, "STATIC_DOCS", retirados)
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0
    assert (tmp_path / "docs" / "DEVELOPMENT.md").read_text(encoding="utf-8") == "mio\n"


@requiere_permisos_posix
def test_ejecutable_reaplica_bit_y_kit_new_nunca_lo_lleva(tmp_path):
    """FR-US2-005: el bit +x se reaplica al escribir; el `.kit-new` no lo lleva."""
    _instalar(tmp_path)
    hook = tmp_path / ".claude" / "sdd_gate_hook.sh"
    hook.chmod(0o644)
    contenido = hook.read_text(encoding="utf-8")
    hook.write_text(contenido + "\n# editado\n", encoding="utf-8")
    sdd_update.main([str(tmp_path), "--apply"])
    kit_new = tmp_path / ".claude" / "sdd_gate_hook.sh.kit-new"
    assert kit_new.exists()
    assert not (kit_new.stat().st_mode & 0o111)


def test_kit_new_se_borra_cuando_el_conflicto_se_resuelve_adoptando_el_kit(tmp_path):
    """FR-US2-005: al resolver adoptando la version del kit, el `.kit-new`
    sobra en la corrida siguiente."""
    _instalar(tmp_path)
    original = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(original + "\nEDITADO\n", encoding="utf-8")
    sdd_update.main([str(tmp_path), "--apply"])
    assert (tmp_path / "AGENTS.md.kit-new").exists()
    # El dueño adopta la version del kit.
    (tmp_path / "AGENTS.md").write_text(original, encoding="utf-8")
    sdd_config.load.cache_clear()
    sdd_update.main([str(tmp_path), "--apply"])
    assert not (tmp_path / "AGENTS.md.kit-new").exists()
