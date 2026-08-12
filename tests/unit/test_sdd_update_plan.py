"""El plan de `sdd-update`: sin --apply no escribe nada, clasifica, --diff.

SPEC-025 FR-US3-001, FR-US3-002, FR-US3-003, FR-US3-004, FR-US3-005, FR-US3-006.
"""

from __future__ import annotations

import sdd_config
import sdd_init
import sdd_update


def _instalar(tmp_path):
    sdd_init.main([str(tmp_path), "--language=python"])
    sdd_config.load.cache_clear()


def _snapshot(tmp_path):
    return {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_sin_apply_el_arbol_queda_byte_a_byte_identico(tmp_path):
    """FR-US3-001: incluido el lock."""
    _instalar(tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        (tmp_path / "AGENTS.md").read_text(encoding="utf-8") + "\nEDITADO\n",
        encoding="utf-8",
    )
    antes = _snapshot(tmp_path)
    exit_code = sdd_update.main([str(tmp_path)])
    assert exit_code == 0
    assert _snapshot(tmp_path) == antes


def test_plan_clasifica_y_resume_por_categoria(tmp_path, capsys):
    """FR-US3-002: vocabulario cerrado y conteo por categoria."""
    _instalar(tmp_path)
    (tmp_path / "AGENTS.md").write_text("editado\n", encoding="utf-8")
    sdd_update.main([str(tmp_path)])
    salida = capsys.readouterr().out
    assert "sin cambios:" in salida
    assert "conflicto:" in salida
    assert "AGENTS.md" in salida


def test_kit_new_presentes_se_listan(tmp_path, capsys):
    """FR-US3-002: un `.kit-new` de una corrida anterior aparece en el plan."""
    _instalar(tmp_path)
    (tmp_path / "AGENTS.md.kit-new").write_text("residuo\n", encoding="utf-8")
    sdd_update.main([str(tmp_path)])
    salida = capsys.readouterr().out
    assert "AGENTS.md.kit-new" in salida


def test_diff_muestra_contenido_no_solo_nombres(tmp_path, capsys):
    """FR-US3-003."""
    _instalar(tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        "contenido completamente distinto\n", encoding="utf-8"
    )
    sdd_update.main([str(tmp_path), "--diff"])
    salida = capsys.readouterr().out
    assert "+++ " in salida or "--- " in salida


def test_diff_es_valido_junto_con_apply(tmp_path):
    """FR-US3-003/US3-041: --diff no es un modo, es compatible con --apply."""
    _instalar(tmp_path)
    exit_code = sdd_update.main([str(tmp_path), "--diff", "--apply"])
    assert exit_code == 0


def test_claves_de_config_reference_faltantes_se_nombran_sin_reescribir(tmp_path):
    """FR-US3-004."""
    _instalar(tmp_path)
    config_path = tmp_path / ".sdd" / "config.yaml"
    antes = config_path.read_text(encoding="utf-8")
    plan = sdd_update.construir_plan(
        sdd_update.KIT_ROOT,
        tmp_path,
        sdd_config.load(tmp_path),
        __import__("sdd_lock").load_lock(tmp_path),
    )
    assert plan.claves_config_faltantes  # el config sembrado no declara todo
    assert config_path.read_text(encoding="utf-8") == antes


def test_gitignore_faltante_se_nombra_sin_tocar(tmp_path):
    """FR-US3-004."""
    _instalar(tmp_path)
    gitignore = tmp_path / ".gitignore"
    texto = gitignore.read_text(encoding="utf-8").replace("*.kit-new\n", "")
    gitignore.write_text(texto, encoding="utf-8")
    antes = gitignore.read_text(encoding="utf-8")
    plan = sdd_update.construir_plan(
        sdd_update.KIT_ROOT,
        tmp_path,
        sdd_config.load(tmp_path),
        __import__("sdd_lock").load_lock(tmp_path),
    )
    assert "*.kit-new" in plan.gitignore_faltantes
    assert gitignore.read_text(encoding="utf-8") == antes


def test_flag_desconocido_aborta_con_uso(tmp_path):
    try:
        sdd_update.main([str(tmp_path), "--no-existe"])
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover
        raise AssertionError("se esperaba SystemExit")


def test_dos_destinos_distintos_abortan(tmp_path):
    try:
        sdd_update.main([str(tmp_path), f"--target={tmp_path.parent}"])
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover
        raise AssertionError("se esperaba SystemExit")


def test_destino_sin_andamiaje_instalado_aborta(tmp_path):
    exit_code = sdd_update.main([str(tmp_path)])
    assert exit_code == 1


def test_destino_es_el_propio_kit_aborta():
    exit_code = sdd_update.main([str(sdd_update.KIT_ROOT)])
    assert exit_code == 1


def test_derivado_sin_ningun_cambio_lo_dice_y_no_propone_nada(tmp_path):
    """FR-US2-014/US3: el veredicto es por contenido, no por version. El unico
    "actualizar" es `.sdd/config.reference.yaml`, que es `vendor` y se
    reescribe siempre por diseño (SPEC-013 FR-008) -- no una plantilla con
    trabajo pendiente."""
    _instalar(tmp_path)
    plan = sdd_update.construir_plan(
        sdd_update.KIT_ROOT,
        tmp_path,
        sdd_config.load(tmp_path),
        __import__("sdd_lock").load_lock(tmp_path),
    )
    assert all(e.decision == "sin_cambios" for e in plan.plantillas)
    assert not plan.retiradas
    assert not plan.semillas_nuevas


def test_plan_cita_el_changelog_entre_la_version_instalada_y_la_del_kit(
    tmp_path, capsys
):
    """FR-US4-002: cita las entradas estrictamente posteriores a la instalada
    y hasta la del kit inclusive (instalado == KIT_VERSION: nada que citar)."""
    _instalar(tmp_path)
    sdd_update.main([str(tmp_path)])
    salida = capsys.readouterr().out
    assert "== Changelog ==" in salida
    assert "Sin cambios de versión que citar." in salida

    entradas = {"0.1.0": "primera", "0.2.0": "segunda", "0.3.0": "tercera"}
    a_mostrar, motivo = sdd_update.seleccionar_changelog(entradas, "0.1.0", "0.3.0")
    assert a_mostrar == ["0.2.0", "0.3.0"]
    assert motivo is None


def test_plan_sin_lock_cita_el_changelog_completo_y_dice_por_que(tmp_path, capsys):
    """FR-US4-002: sin version instalada conocida, cita todo y declara el motivo."""
    _instalar(tmp_path)
    (tmp_path / ".sdd" / "kit.lock").unlink()
    sdd_update.main([str(tmp_path)])
    salida = capsys.readouterr().out
    assert "mostrando el changelog completo" in salida


def test_lock_ilegible_aborta_sin_degradar_y_ofrece_borrarlo(tmp_path, capsys):
    """FR-US3-006/ANA-029."""
    _instalar(tmp_path)
    (tmp_path / ".sdd" / "kit.lock").write_text("{esto no es json", encoding="utf-8")
    exit_code = sdd_update.main([str(tmp_path)])
    salida = capsys.readouterr().err
    assert exit_code == 1
    assert "borrá" in salida.lower() or "borra" in salida.lower()


def test_config_yaml_no_parsea_aborta_antes_de_tocar_nada(tmp_path):
    """FR-US3-006."""
    _instalar(tmp_path)
    config_path = tmp_path / ".sdd" / "config.yaml"
    roto = "project:\n  name: [sin cerrar\n"
    config_path.write_text(roto, encoding="utf-8")
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 1
    assert config_path.read_text(encoding="utf-8") == roto  # sdd-update no lo tocó
