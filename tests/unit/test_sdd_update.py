"""CLI de `sdd-update`, aborto por versión posterior, placeholders y version
como veredicto.

SPEC-025 FR-US2-007, FR-US2-010, FR-US2-014, FR-US4-003.
"""

from __future__ import annotations

import json

import sdd_config
import sdd_init
import sdd_lock
import sdd_update


def _instalar(tmp_path):
    sdd_init.main([str(tmp_path), "--language=python"])
    sdd_config.load.cache_clear()


def test_aborta_si_la_version_instalada_es_posterior_a_la_del_kit(tmp_path, capsys):
    """FR-US2-007: aborta sin escribir, nombrando ambas versiones."""
    _instalar(tmp_path)
    lock_path = tmp_path / sdd_lock.LOCK_RELPATH
    crudo = json.loads(lock_path.read_text(encoding="utf-8"))
    crudo["kit_version"] = "99.0.0"
    lock_path.write_text(json.dumps(crudo), encoding="utf-8")
    antes = lock_path.read_text(encoding="utf-8")
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    salida = capsys.readouterr().err
    assert exit_code == 1
    assert "99.0.0" in salida and sdd_config.KIT_VERSION in salida
    assert lock_path.read_text(encoding="utf-8") == antes


def test_placeholders_se_resuelven_con_el_config_del_destino(tmp_path):
    """FR-US2-010: mismo helper que la instalacion (`sdd_init._substitute`),
    con los valores que declara `.sdd/config.yaml` del destino."""
    _instalar(tmp_path)
    config_path = tmp_path / ".sdd" / "config.yaml"
    texto = config_path.read_text(encoding="utf-8")
    texto = texto.replace(f"name: {tmp_path.name}", "name: otro-nombre")
    config_path.write_text(texto, encoding="utf-8")
    sdd_config.load.cache_clear()
    plan = sdd_update.construir_plan(
        sdd_update.KIT_ROOT,
        tmp_path,
        sdd_config.load(tmp_path),
        sdd_lock.load_lock(tmp_path),
    )
    entrada = next(e for e in plan.plantillas if e.dst_rel == "README.md")
    assert "otro-nombre" in (entrada.contenido_kit or "")


def test_version_igual_pero_contenido_distinto_igual_propone_cambios(tmp_path):
    """FR-US2-014: la version no decide si hay trabajo -- lo decide el
    contenido. Version instalada == KIT_VERSION, contenido difiere: se
    actualiza igual."""
    _instalar(tmp_path)
    (tmp_path / "README.md").write_text("cambiado a mano\n", encoding="utf-8")
    plan = sdd_update.construir_plan(
        sdd_update.KIT_ROOT,
        tmp_path,
        sdd_config.load(tmp_path),
        sdd_lock.load_lock(tmp_path),
    )
    readme = next(e for e in plan.plantillas if e.dst_rel == "README.md")
    assert readme.decision == "conflicto"


def test_version_igual_y_sin_diferencias_no_propone_nada(tmp_path):
    """FR-US2-014: version igual y contenido identico -> nada que aplicar."""
    _instalar(tmp_path)
    plan = sdd_update.construir_plan(
        sdd_update.KIT_ROOT,
        tmp_path,
        sdd_config.load(tmp_path),
        sdd_lock.load_lock(tmp_path),
    )
    assert all(e.decision == "sin_cambios" for e in plan.plantillas)


def test_cli_flags_desconocidos_abortan_sin_escribir(tmp_path, capsys):
    _instalar(tmp_path)
    try:
        sdd_update.main([str(tmp_path), "--flag-inventado"])
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover
        raise AssertionError("se esperaba SystemExit")


def test_aborta_si_se_corre_desde_el_vendorizado(tmp_path, monkeypatch):
    """FR-US4-003: el vendorizado del derivado no tiene templates/ al lado."""
    _instalar(tmp_path)
    vendorizado = tmp_path / "tools" / "sdd"
    monkeypatch.setattr(sdd_update, "KIT_ROOT", vendorizado)
    exit_code = sdd_update.main([str(tmp_path)])
    assert exit_code == 1
