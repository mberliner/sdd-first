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
