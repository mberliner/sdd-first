"""Tests del render: sync docs/templates (SPEC-005 FR-001, FR-002), constitucion
enriquecida y metadatos configurables (SPEC-010 FR-001..FR-003, FR-007) y
workflow de CI derivado del config (SPEC-009 FR-005)."""

from __future__ import annotations

from pathlib import Path

import render
import sdd_catalog
from sdd_config import SddConfig


def _make_repo(tmp_path: Path) -> Path:
    (tmp_path / "templates" / "docs" / "playbooks").mkdir(parents=True)
    (tmp_path / "templates" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "playbooks").mkdir(parents=True)
    (tmp_path / "specs").mkdir(parents=True)
    (tmp_path / "templates" / "docs" / "SDD-ENFORCEMENT.md").write_text(
        "contenido autoritativo\n", encoding="utf-8"
    )
    (tmp_path / "templates" / "docs" / "SKILLS-MULTITOOL.md").write_text(
        "skills multi-asistente\n", encoding="utf-8"
    )
    (tmp_path / "templates" / "docs" / "playbooks" / "analyze.md").write_text(
        "analyze\n", encoding="utf-8"
    )
    (tmp_path / "templates" / "docs" / "playbooks" / "clarify.md").write_text(
        "clarify\n", encoding="utf-8"
    )
    for name in ("sdd-spec", "sdd-doctor", "sdd-configure"):
        (tmp_path / "templates" / "docs" / "playbooks" / f"{name}.md").write_text(
            f"{name}\n", encoding="utf-8"
        )
    (tmp_path / "templates" / "specs" / "SPEC-TEMPLATE.md").write_text(
        "template\n", encoding="utf-8"
    )
    # El wiring tambien se sincroniza (SPEC-005 FR-008). Se siembra desde el
    # catalogo y no con una lista propia: sumar un archivo de wiring no deberia
    # obligar a tocar este fixture.
    for src_rel in sdd_catalog.wiring_sincronizado().values():
        origen = tmp_path / "templates" / src_rel
        origen.parent.mkdir(parents=True, exist_ok=True)
        origen.write_text(f"wiring {Path(src_rel).name}\n", encoding="utf-8")
    return tmp_path


def test_generated_targets_incluye_sync_solo_si_hay_templates(tmp_path):
    repo_con_templates = _make_repo(tmp_path)
    targets = render._generated_targets(repo_con_templates)
    assert "docs/SDD-ENFORCEMENT.md" in targets
    assert "specs/SPEC-TEMPLATE.md" in targets


def test_sync_incluye_los_3_playbooks_operativos():
    # SPEC-007 FR-004: sdd-spec/sdd-doctor/sdd-configure se sincronizan desde
    # templates/ igual que analyze/clarify (patron SPEC-005), no se duplican
    # a mano en docs/playbooks/ del propio kit.
    # SPEC-013 FR-006: el playbook de sdd-configure.md (con su preambulo
    # explicativo por pregunta) esta sincronizado sin drift, igual que el resto.
    for name in ("sdd-spec", "sdd-doctor", "sdd-configure"):
        assert f"docs/playbooks/{name}.md" in render._SYNCED_FROM_TEMPLATES


def test_generated_targets_es_noop_sin_carpeta_templates(tmp_path):
    # Proyecto instalado con sdd-init: no tiene templates/ propia.
    # SPEC-009 FR-006 (enmendado): .github/workflows/ci.yml es un artefacto
    # derivado mas de `render.py`, no algo que instale `sdd_init.py`.
    targets = render._generated_targets(tmp_path)
    assert "docs/SDD-ENFORCEMENT.md" not in targets
    assert ".github/workflows/ci.yml" in render._GENERATED
    assert set(targets) == set(render._GENERATED)


def test_sync_copia_byte_a_byte_desde_templates(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    monkeypatch.chdir(repo)
    render.load.cache_clear()

    render.main([])

    assert (repo / "docs" / "SDD-ENFORCEMENT.md").read_text(
        encoding="utf-8"
    ) == "contenido autoritativo\n"
    assert (repo / "specs" / "SPEC-TEMPLATE.md").read_text(
        encoding="utf-8"
    ) == "template\n"


def test_check_detecta_drift_en_archivo_sincronizado(tmp_path, monkeypatch, capsys):
    repo = _make_repo(tmp_path)
    monkeypatch.chdir(repo)
    render.load.cache_clear()
    render.main([])  # sincroniza primero

    (repo / "docs" / "SDD-ENFORCEMENT.md").write_text(
        "editado a mano, sin tocar templates/\n", encoding="utf-8"
    )

    code = render.main(["--check"])

    assert code == 1
    out = capsys.readouterr().out
    assert "docs/SDD-ENFORCEMENT.md" in out


# --- SPEC-010: constitucion con preambulo, governance y metadatos del config ---


def _cfg(tmp_path: Path, raw: dict) -> SddConfig:
    return SddConfig(repo_root=tmp_path, raw=raw)


_PRINCIPIO = {
    "principles": [
        {
            "id": "I",
            "title": "Un principio",
            "invariant": "Algo que no cede.",
            "enforcement": "check_naming.py",
            "detail": "specs/SPEC-000-naming.md",
        }
    ]
}


def test_constitucion_incluye_preambulo_y_governance(tmp_path):
    # FR-001/FR-002: el documento explica que ES una constitucion y como se
    # enmienda; sin eso, quien lo recibe no sabe que hacer con el.
    text = render.render_constitution(_cfg(tmp_path, _PRINCIPIO))

    assert "## Preámbulo" in text
    assert "se ajusta la spec, no el principio" in text
    assert "## Governance" in text
    assert "MAJOR" in text and "MINOR" in text and "PATCH" in text
    assert "Procedimiento de enmienda" in text


def test_constitucion_declara_el_dominio_del_config(tmp_path):
    # SPEC-014 FR-US2-006: el dominio lo afirma un artefacto generado, para que
    # cambiarlo en el config y regenerar alcance para actualizarlo (V-3).
    raw = dict(_PRINCIPIO, project={"name": "cobranzas", "domain": "gestion de mora"})
    text = render.render_constitution(_cfg(tmp_path, raw))

    assert "**Proyecto:** cobranzas | **Dominio:** gestion de mora" in text

    raw["project"]["domain"] = "gestion de mora temprana"
    assert "gestion de mora temprana" in render.render_constitution(_cfg(tmp_path, raw))


def test_constitucion_sin_dominio_declarado_lo_dice(tmp_path):
    # Callar el dato dejaria al lector sin saber si falta o si nadie lo declaro.
    text = render.render_constitution(_cfg(tmp_path, dict(_PRINCIPIO)))

    assert "**Dominio:** sin declarar" in text
    assert "`project.domain`" in text


def test_ninguna_plantilla_instalable_congela_el_dominio():
    # FR-US2-006: `sdd-init` sustituye {{project.domain}} una sola vez, en la
    # instalacion. Una plantilla que lo use deja en el derivado una copia que
    # ningun render puede actualizar despues (el derivado no tiene templates/).
    templates = Path(__file__).resolve().parents[2] / "templates"
    culpables = [
        ruta.relative_to(templates).as_posix()
        for ruta in templates.rglob("*")
        if ruta.is_file() and "{{project.domain}}" in ruta.read_text(encoding="utf-8")
    ]

    assert culpables == [], (
        f"estas plantillas congelan el dominio en la instalacion: {culpables}"
    )


def test_constitucion_toma_version_y_fechas_del_config(tmp_path):
    # FR-003: antes estaban hardcodeadas en render.py (ítem C-5 de IDEAS).
    raw = dict(
        _PRINCIPIO,
        constitution={
            "version": "0.7.1",
            "ratified": "2020-01-02",
            "amended": "2021-03-04",
        },
    )
    text = render.render_constitution(_cfg(tmp_path, raw))

    assert (
        "**Versión:** 0.7.1 | Ratificada: 2020-01-02 | Última enmienda: 2021-03-04"
        in text
    )


def test_constitucion_sin_seccion_constitution_usa_defaults(tmp_path):
    # FR-003: retrocompatible con los configs ya instalados.
    text = render.render_constitution(_cfg(tmp_path, _PRINCIPIO))

    assert "**Versión:** 0.1.0" in text


def test_constitucion_apunta_al_andamiaje_vendorizado_en_proyecto_instalado(tmp_path):
    # FR-007: sin templates/ el repo es un proyecto instalado -> tools/sdd/core.
    text = render.render_constitution(_cfg(tmp_path, _PRINCIPIO))

    assert "tools/sdd/core/render.py" in text
    assert "`core/render.py`" not in text


def test_constitucion_apunta_a_core_en_el_kit(tmp_path):
    # ...y con templates/ es el propio kit, donde el andamiaje vive en core/.
    (tmp_path / "templates").mkdir()
    text = render.render_constitution(_cfg(tmp_path, _PRINCIPIO))

    assert "`core/render.py`" in text
    assert "tools/sdd" not in text


def test_sync_resuelve_los_placeholders_de_ruta(tmp_path, monkeypatch):
    # FR-007: una sola plantilla sirve al kit y al proyecto instalado.
    repo = _make_repo(tmp_path)
    (repo / "templates" / "docs" / "SDD-ENFORCEMENT.md").write_text(
        "Corré `python {{sdd.core}}/pipeline.py`.\n", encoding="utf-8"
    )
    monkeypatch.chdir(repo)
    render.load.cache_clear()

    render.main([])

    text = (repo / "docs" / "SDD-ENFORCEMENT.md").read_text(encoding="utf-8")
    assert "python core/pipeline.py" in text
    assert "{{sdd.core}}" not in text


# --- SPEC-009 FR-005: workflow de CI derivado del config ----------------------


def test_ci_invoca_el_pipeline_y_no_enumera_los_pasos(tmp_path):
    raw = {
        "project": {"name": "demo", "language": "python"},
        "pipeline": {"steps": ["constitution", "traceability", "lint", "tests"]},
    }
    text = render.render_ci_workflow(_cfg(tmp_path, raw))

    assert "python tools/sdd/core/pipeline.py" in text
    # El SSOT de los pasos es pipeline.steps: el YAML no los repite.
    assert "ruff" not in text
    assert "traceability" not in text


def test_ci_deriva_los_paths_de_disparo_del_config(tmp_path):
    raw = {
        "project": {"name": "demo", "language": "python"},
        "dirs": {"source_roots": ["src"], "tests_unit": "tests/unit"},
        "pipeline": {"steps": ["tests"]},
    }
    text = render.render_ci_workflow(_cfg(tmp_path, raw))

    assert '- "src/**"' in text
    assert '- "tests/unit/**"' in text
    assert '- ".sdd/config.yaml"' in text
    # Cambios que solo tocan documentacion no gastan una corrida.
    assert "docs/**" not in text


def test_ci_no_duplica_patrones(tmp_path):
    # En el kit, el andamiaje ya esta entre los source_roots.
    (tmp_path / "templates").mkdir()
    raw = {
        "project": {"name": "kit"},
        "dirs": {"source_roots": ["core", "adapters"]},
        "pipeline": {"steps": ["tests"]},
    }
    text = render.render_ci_workflow(_cfg(tmp_path, raw))

    assert text.count('- "core/**"') == 2  # una vez por evento (push, PR)


def test_ci_dispara_en_la_rama_declarada(tmp_path):
    """SPEC-014 FR-US2-005: `branches: [main]` fijo le daba a un proyecto en
    `develop` un workflow que nunca dispara."""
    raw = {"project": {"name": "demo", "default_branch": "develop"}}
    text = render.render_ci_workflow(_cfg(tmp_path, raw))

    assert "branches: [develop]" in text


def test_ci_sin_rama_declarada_asume_main(tmp_path):
    raw = {"project": {"name": "demo"}}
    text = render.render_ci_workflow(_cfg(tmp_path, raw))

    assert "branches: [main]" in text


def test_ci_de_proyecto_sin_lenguaje_no_instala_tooling(tmp_path):
    raw = {"project": {"name": "docs-only", "language": "none"}}
    text = render.render_ci_workflow(_cfg(tmp_path, raw))

    assert "requirements-dev.txt" not in text
    assert "pip install pyyaml" in text
