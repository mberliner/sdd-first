"""Purga y recreacion de `tools/sdd/`, regeneracion en el destino, fallo sin lock.

SPEC-025 FR-US2-003, FR-US2-004, FR-US2-011.
"""

from __future__ import annotations

import sdd_config
import sdd_init
import sdd_lock
import sdd_update


def _instalar(tmp_path):
    sdd_init.main([str(tmp_path), "--language=python"])
    sdd_config.load.cache_clear()


def test_vendor_se_purga_y_recrea_borrando_residuos(tmp_path):
    """FR-US2-003: un módulo que ya no viene del kit desaparece porque el
    vendorizado se borra entero, no se parchea (a diferencia de
    `shutil.copytree(..., dirs_exist_ok=True)`, que sólo sobrescribe)."""
    _instalar(tmp_path)
    residuo = tmp_path / "tools" / "sdd" / "core" / "modulo_retirado_del_kit.py"
    residuo.write_text("# ya no viene del kit\n", encoding="utf-8")
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0
    assert not residuo.exists()
    assert (tmp_path / "tools" / "sdd" / "core" / "sdd_update.py").exists()


def test_aborta_si_el_kit_no_trae_el_adaptador_del_lenguaje(tmp_path, monkeypatch):
    """FR-US2-003/ANA-002: no deja al derivado sin adaptador."""
    _instalar(tmp_path)
    monkeypatch.setattr(sdd_update, "KIT_ROOT", tmp_path / "no-existe-como-kit")
    # KIT_ROOT sin templates/ tambien dispara el aborto de "no es un clon del kit"
    # (FR-US4-003): se verifica el mensaje de adaptador con un KIT_ROOT valido
    # pero sin el adaptador python.
    (tmp_path / "no-existe-como-kit" / "templates").mkdir(parents=True)
    (tmp_path / "no-existe-como-kit" / "adapters").mkdir(parents=True)
    exit_code = sdd_update.main([str(tmp_path)])
    assert exit_code == 1


def test_regeneracion_corre_el_render_py_ya_copiado_en_el_destino(tmp_path):
    """FR-US2-004: se ejecuta el `render.py` del destino (cwd=target), no el
    del clon -- si asi no fuera, el CONSTITUTION.md resultante citaria las
    rutas del kit en vez de `tools/sdd/core`."""
    _instalar(tmp_path)
    sdd_update.main([str(tmp_path), "--apply"])
    constitucion = (tmp_path / "CONSTITUTION.md").read_text(encoding="utf-8")
    assert "tools/sdd/core" in constitucion


def test_regeneracion_fallida_no_reescribe_el_lock(tmp_path, monkeypatch):
    """FR-US2-011: si `render.py`/`gen_skill_adapters.py` fallan con el vendor
    ya recreado, el lock NO se reescribe -- eso es lo que deja detectable la
    actualizacion a medio aplicar (FR-US1-005)."""
    _instalar(tmp_path)
    lock_antes = (tmp_path / sdd_lock.LOCK_RELPATH).read_text(encoding="utf-8")
    vendor_kit_original = sdd_init._vendor_kit

    def _vendor_kit_y_rompe_render(target, language, force):
        out = vendor_kit_original(target, language, force)
        core = target / "tools" / "sdd" / "core" / "render.py"
        core.write_text("import sys; sys.exit(1)\n", encoding="utf-8")
        return out

    monkeypatch.setattr(sdd_init, "_vendor_kit", _vendor_kit_y_rompe_render)
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 1
    lock_despues = (tmp_path / sdd_lock.LOCK_RELPATH).read_text(encoding="utf-8")
    assert lock_antes == lock_despues
