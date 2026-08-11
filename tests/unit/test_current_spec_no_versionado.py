"""Tests de FR-008 (SPEC-004): .sdd/current-spec deja de ser artefacto requerido
y se siembra solo si falta, en vez de exigirse versionado en git."""

from __future__ import annotations

from pathlib import Path

import sdd_config
import sdd_doctor
import sdd_init


def _make_kit_repo(tmp_path: Path) -> Path:
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "00-INDEX.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "SPECS_REGISTRY.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "specs" / "SPEC-000-naming.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  name: demo\n", encoding="utf-8"
    )
    (tmp_path / "templates" / "wiring").mkdir(parents=True)
    (tmp_path / "templates" / "wiring" / "current-spec").write_text(
        "# header ({{sdd.core}}/sdd_gate.py)\n", encoding="utf-8"
    )
    (tmp_path / ".gitignore").write_text(".sdd/current-spec\n", encoding="utf-8")
    return tmp_path


def test_current_spec_no_esta_en_required():
    assert ".sdd/current-spec" not in sdd_doctor.REQUIRED


def test_seed_current_spec_lo_crea_desde_la_plantilla_del_kit(tmp_path):
    repo = _make_kit_repo(tmp_path)
    current = repo / ".sdd" / "current-spec"
    assert not current.exists()

    assert sdd_config.seed_current_spec(repo) is True

    text = current.read_text(encoding="utf-8")
    assert text == "# header (core/sdd_gate.py)\n"


def test_seed_current_spec_no_pisa_uno_existente(tmp_path):
    repo = _make_kit_repo(tmp_path)
    current = repo / ".sdd" / "current-spec"
    current.write_text("SPEC-001-demo\n", encoding="utf-8")

    assert sdd_config.seed_current_spec(repo) is False

    assert current.read_text(encoding="utf-8") == "SPEC-001-demo\n"


def test_seed_current_spec_en_derivado_usa_el_fallback_con_prefijo_vendorizado(
    tmp_path,
):
    """Sin templates/ (proyecto derivado), usa CURRENT_SPEC_FALLBACK_HEADER con
    {{sdd.core}} resuelto a tools/sdd/core (SPEC-010 FR-007)."""
    repo = tmp_path
    (repo / ".sdd").mkdir()

    assert sdd_config.seed_current_spec(repo) is True

    text = (repo / ".sdd" / "current-spec").read_text(encoding="utf-8")
    assert "tools/sdd/core/sdd_gate.py" in text
    assert "{{sdd.core}}" not in text


def test_fallback_header_coincide_con_la_plantilla_del_kit(tmp_path):
    """Test de paridad (patron ya usado para G-1): el fallback embebido en
    sdd_config.py no puede divergir en silencio de la plantilla real del kit."""
    repo_kit = sdd_config.find_repo_root()
    plantilla = (repo_kit / "templates" / "wiring" / "current-spec").read_text(
        encoding="utf-8"
    )
    fallback = sdd_config.CURRENT_SPEC_FALLBACK_HEADER.format(core="{{sdd.core}}")
    assert fallback == plantilla


def test_gitignore_del_kit_ignora_current_spec():
    repo_kit = sdd_config.find_repo_root()
    texto = (repo_kit / ".gitignore").read_text(encoding="utf-8")
    assert ".sdd/current-spec" in texto


def test_gitignore_de_la_plantilla_de_wiring_ignora_current_spec():
    repo_kit = sdd_config.find_repo_root()
    texto = (repo_kit / "templates" / "wiring" / ".gitignore").read_text(
        encoding="utf-8"
    )
    assert ".sdd/current-spec" in texto


def test_doctor_siembra_current_spec_faltante_y_no_lo_reporta_como_problema(
    tmp_path, monkeypatch, capsys
):
    repo = _make_kit_repo(tmp_path)
    monkeypatch.setattr(sdd_doctor, "find_repo_root", lambda: repo)
    monkeypatch.chdir(repo)

    sdd_doctor.main([])

    salida = capsys.readouterr().out
    assert (repo / ".sdd" / "current-spec").exists()
    assert "Falta artefacto requerido: .sdd/current-spec" not in salida


# --- FR-009/SC-006: el .gitignore conservado por sdd-init tiene que sumar la
# linea de .sdd/current-spec, y sdd-doctor tiene que auditarlo por contenido. ---


def test_ensure_gitignore_current_spec_agrega_la_linea_sin_pisar_el_resto(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("__pycache__/\n*.pyc\n", encoding="utf-8")

    assert sdd_config.ensure_gitignore_current_spec(gitignore) is True

    texto = gitignore.read_text(encoding="utf-8")
    assert "__pycache__/" in texto
    assert "*.pyc" in texto
    assert ".sdd/current-spec" in texto


def test_ensure_gitignore_current_spec_es_idempotente_si_ya_la_tiene(tmp_path):
    gitignore = tmp_path / ".gitignore"
    original = "__pycache__/\n.sdd/current-spec\n"
    gitignore.write_text(original, encoding="utf-8")

    assert sdd_config.ensure_gitignore_current_spec(gitignore) is False
    assert gitignore.read_text(encoding="utf-8") == original


def test_ensure_gitignore_current_spec_no_crea_archivo_si_no_existe(tmp_path):
    gitignore = tmp_path / ".gitignore"
    assert sdd_config.ensure_gitignore_current_spec(gitignore) is False
    assert not gitignore.exists()


def test_sdd_init_agrega_la_linea_a_un_gitignore_propio_conservado(tmp_path):
    """FR-009: sdd-init conserva un .gitignore preexistente (comportamiento de
    _copy_text para todo WIRING), pero para .gitignore ademas suma la linea
    que le falte -- si no, FR-008 quedaria neutralizado en el caso realista."""
    destino = tmp_path / "proyecto"
    destino.mkdir()
    gitignore = destino / ".gitignore"
    gitignore.write_text("node_modules/\n", encoding="utf-8")

    mensaje = sdd_init._copy_text(
        sdd_init.TEMPLATES / "wiring" / ".gitignore",
        gitignore,
        "demo",
        "dominio",
        force=False,
    )

    texto = gitignore.read_text(encoding="utf-8")
    assert "node_modules/" in texto
    assert ".sdd/current-spec" in texto
    assert "se conserva" in mensaje
    assert ".sdd/current-spec" in mensaje


def test_doctor_reporta_gitignore_sin_la_linea_de_current_spec(
    tmp_path, monkeypatch, capsys
):
    repo = _make_kit_repo(tmp_path)
    (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    monkeypatch.setattr(sdd_doctor, "find_repo_root", lambda: repo)
    monkeypatch.chdir(repo)

    exit_code = sdd_doctor.main([])

    salida = capsys.readouterr().out
    assert exit_code == 1
    assert ".gitignore no ignora .sdd/current-spec" in salida


def test_doctor_reporta_gitignore_faltante(tmp_path, monkeypatch, capsys):
    repo = _make_kit_repo(tmp_path)
    (repo / ".gitignore").unlink()
    monkeypatch.setattr(sdd_doctor, "find_repo_root", lambda: repo)
    monkeypatch.chdir(repo)

    exit_code = sdd_doctor.main([])

    salida = capsys.readouterr().out
    assert exit_code == 1
    assert "Falta .gitignore" in salida


def test_doctor_no_reporta_problema_con_gitignore_sano(tmp_path, monkeypatch, capsys):
    repo = _make_kit_repo(tmp_path)
    monkeypatch.setattr(sdd_doctor, "find_repo_root", lambda: repo)
    monkeypatch.chdir(repo)

    sdd_doctor.main([])

    salida = capsys.readouterr().out
    assert "gitignore" not in salida.lower()
