"""SPEC-FORMAT.md referencia el template, no lo embebe (SPEC-005 FR-004)."""

from __future__ import annotations

from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[2]


def test_spec_format_no_embebe_el_template_completo():
    text = (KIT_ROOT / "templates" / "docs" / "SPEC-FORMAT.md").read_text(
        encoding="utf-8"
    )
    assert "```markdown" not in text
    assert "specs/SPEC-TEMPLATE.md" in text


def test_spec_template_sigue_siendo_un_unico_archivo_fuente():
    kit_copy = (KIT_ROOT / "specs" / "SPEC-TEMPLATE.md").read_text(encoding="utf-8")
    template_source = (KIT_ROOT / "templates" / "specs" / "SPEC-TEMPLATE.md").read_text(
        encoding="utf-8"
    )
    assert kit_copy == template_source


# -- SPEC-023: la seccion de relaciones y su SSOT -------------------------------

SPEC_FORMAT = KIT_ROOT / "templates" / "docs" / "SPEC-FORMAT.md"
CAMPOS = (
    "Extiende",
    "Supersede",
    "Depende de",
    "Extendida por",
    "Es dependencia de",
    "Superseded por",
)


def test_la_plantilla_trae_la_seccion_con_sus_seis_campos_vacios():
    """FR-US1-005: en las dos copias, que el test de arriba mantiene identicas."""
    for ruta in (
        KIT_ROOT / "templates" / "specs" / "SPEC-TEMPLATE.md",
        KIT_ROOT / "specs" / "SPEC-TEMPLATE.md",
    ):
        texto = ruta.read_text(encoding="utf-8")
        assert "## Relación con specs existentes" in texto
        for campo in CAMPOS:
            assert f"**{campo}:** —" in texto, f"{ruta.name} sin {campo}"


def test_spec_format_declara_la_seccion_obligatoria_y_su_gramatica():
    """FR-US2-001: SSOT del formato, incluidos los marcadores de vacio."""
    texto = SPEC_FORMAT.read_text(encoding="utf-8")
    assert "## Relación con specs existentes" in texto
    for campo in CAMPOS:
        assert campo in texto
    assert "hibrido" in texto
    # Los marcadores de vacio se declaran aca y en ningun otro documento.
    for marcador in ("em dash", "en dash", "guion simple"):
        assert marcador in texto


def test_spec_format_declara_cuando_corresponde_cada_campo():
    """FR-US2-002: sin criterio, el validador verifica forma sin significado."""
    texto = SPEC_FORMAT.read_text(encoding="utf-8")
    assert "no puede entregarse sin B implementada" in texto
    assert "sin reemplazarla" in texto
    # Lo que NO es depender, que es donde cada autor enlazaria distinto.
    assert "va en prosa" in texto


def test_ningun_otro_documento_reproduce_la_gramatica():
    """FR-US2-001, Principio IV: una sola copia normativa del detalle."""
    otros = [
        p for p in (KIT_ROOT / "templates" / "docs").rglob("*.md") if p != SPEC_FORMAT
    ]
    for doc in otros:
        texto = doc.read_text(encoding="utf-8")
        declarados = [campo for campo in CAMPOS if f"**{campo}:**" in texto]
        assert not declarados, f"{doc.name} reproduce la seccion: {declarados}"
