"""Las plantillas no hardcodean rutas del kit (SPEC-010 FR-005/FR-007/FR-008).

Un proyecto instalado recibe el andamiaje bajo `tools/sdd/`, no en `core/`.
Antes, las plantillas citaban `python core/pipeline.py`: el usuario copiaba el
comando del documento que el kit le había instalado y no funcionaba (ítem E-6
de `docs/IDEAS.md`, más ancho de lo registrado). Ahora escriben
`{{sdd.core}}` y cada consumidor lo resuelve.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from sdd_config import kit_path_tokens

KIT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = KIT_ROOT / "templates"

# Modulos del andamiaje: si una plantilla los cita con el prefijo `core/` o
# `adapters/` pelado, en el proyecto instalado esa ruta no existe.
_RUTA_PELADA = re.compile(
    r"(?<![\w/.{])(core|adapters)/[\w/]+\.py",
)


def _plantillas() -> list[Path]:
    return sorted(
        p
        for p in TEMPLATES.rglob("*")
        if p.is_file() and (p.suffix in {".md", ".yaml", ".yml", ".json", ".js"})
    )


@pytest.mark.parametrize("plantilla", _plantillas(), ids=lambda p: p.name)
def test_plantilla_no_hardcodea_rutas_del_andamiaje(plantilla: Path):
    encontradas = _RUTA_PELADA.findall(plantilla.read_text(encoding="utf-8"))
    assert not encontradas, (
        f"{plantilla.relative_to(TEMPLATES)} cita rutas del kit sin placeholder; "
        "usá {{sdd.core}} / {{sdd.adapters}}"
    )


def test_los_placeholders_resuelven_distinto_segun_el_repo(tmp_path):
    instalado = kit_path_tokens(tmp_path)
    (tmp_path / "templates").mkdir()
    kit = kit_path_tokens(tmp_path)

    assert instalado["{{sdd.core}}"] == "tools/sdd/core"
    assert kit["{{sdd.core}}"] == "core"


def test_docs_nuevos_existen_como_plantilla():
    # FR-005/FR-006: SSOT del mecanismo de skills y setup local del derivado.
    assert (TEMPLATES / "docs" / "SKILLS-MULTITOOL.md").exists()
    assert (TEMPLATES / "docs" / "DEVELOPMENT.md").exists()


def test_docs_nuevos_estan_en_el_indice_del_derivado():
    # FR-008: un documento que no está en el índice es un SSOT invisible.
    indice = (TEMPLATES / "00-INDEX.md").read_text(encoding="utf-8")
    assert "SKILLS-MULTITOOL.md" in indice
    assert "DEVELOPMENT.md" in indice


def test_docs_nuevos_estan_en_el_indice_del_kit():
    indice = (KIT_ROOT / "00-INDEX.md").read_text(encoding="utf-8")
    assert "SKILLS-MULTITOOL.md" in indice


# -- SPEC-022: el playbook es el SSOT del procedimiento de decidir-y-adoptar ----

PLAYBOOK_SPEC = TEMPLATES / "docs" / "playbooks" / "sdd-spec.md"


def test_playbook_documenta_el_triage_y_la_bandera_touches():
    """FR-US2-011: leer el registro, correr el triage, proponer, resolver."""
    texto = PLAYBOOK_SPEC.read_text(encoding="utf-8")
    assert "SPECS_REGISTRY.md" in texto
    assert "--touches" in texto
    assert "--new --rationale" in texto or "--rationale" in texto


def test_playbook_documenta_reuse_y_su_exigencia_de_fr():
    """FR-US1-008 / FR-US2-011: adoptar es un camino de primera clase."""
    texto = PLAYBOOK_SPEC.read_text(encoding="utf-8")
    assert "--reuse SPEC-NNN --fr FR-NNN" in texto


def test_playbook_dice_donde_aterriza_el_fr_en_la_spec_adoptada():
    """FR-US1-008: en la User Story que cubre la capacidad, o en una nueva."""
    texto = PLAYBOOK_SPEC.read_text(encoding="utf-8")
    assert "User Story" in texto
    assert "Independent Test" in texto
    assert "Coverage mapping" in texto


def test_agents_referencia_el_playbook_sin_reproducirlo():
    """FR-US2-011: SSOT único; AGENTS.md apunta, no duplica."""
    texto = (KIT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "sdd-spec" in texto and "--reuse" in texto
    # El detalle vive en el playbook: AGENTS.md no repite el procedimiento.
    assert "--touches" not in texto
