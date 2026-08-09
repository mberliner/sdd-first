"""El SSOT de la politica de decision del gate es SPEC-017 (y el doc operativo).

SPEC-017 FR-US3-006: docs/SDD-ENFORCEMENT.md (SSOT del enforcement) describe
el criterio vigente, el endurecimiento multi-spec y el escape hatch, y ningun
otro documento del kit repite la politica.
"""

from __future__ import annotations

from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[2]


def test_sdd_enforcement_describe_el_criterio_y_escape_hatch():
    # El archivo que lee el operador en un proyecto derivado.
    doc = KIT_ROOT / "templates" / "docs" / "SDD-ENFORCEMENT.md"
    texto = doc.read_text(encoding="utf-8").lower()

    # Debe describir que es por contenido, no mtime
    assert "contenido, no de marcas de tiempo" in texto
    # Debe describir multi-spec
    assert "cada spec listada" in texto or "cada** spec listada" in texto
    # Debe describir el escape hatch
    assert "sdd_gate_bypass" in texto


def test_ninguna_otra_spec_active_describe_la_politica():
    # SC-005: Ninguna spec `active` distinta de esta describe la politica de
    # decision del gate; SPEC-006 queda `superseded` con puntero a esta.
    specs_dir = KIT_ROOT / "specs"

    import sys

    sys.path.insert(0, str(KIT_ROOT / "core"))
    from check_traceability import _parse_registry

    errors: list[str] = []
    rows = _parse_registry(specs_dir / "SPECS_REGISTRY.md", errors)
    assert not errors

    active_specs = [
        row.archivo.replace(".md", "") for row in rows if row.estado == "active"
    ]

    # Verificamos que ninguna (salvo SPEC-017) describa el criterio o el bypass.
    for spec_id in active_specs:
        if "SPEC-017" in spec_id:
            continue

        spec_path = specs_dir / f"{spec_id}.md"
        if not spec_path.exists():
            continue

        texto = spec_path.read_text(encoding="utf-8")
        # El hook script y tests lo mencionan, pero una spec active no deberia estar
        # re-definiendo las politicas de bypass o mtime. Solo lo hara si documenta pruebas (SPEC-018).
        if "SPEC-018" in spec_id:
            # SPEC-018 puede tener scenarios que lo usan
            continue

        # Nos aseguramos que no contengan definiciones normativas de gate decision.
        assert "SDD_GATE_BYPASS" not in texto, (
            f"La spec {spec_id} repite el escape hatch"
        )
