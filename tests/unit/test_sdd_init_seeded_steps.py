"""Tests del paso 'hooks' sembrado por sdd_init (SPEC-004 FR-005) y del wiring
ejecutable (.claude/sdd_gate_hook.sh)."""

from __future__ import annotations

import sdd_init


def test_hooks_esta_en_los_pasos_sembrados_por_defecto():
    assert "hooks" in sdd_init._SEEDED_STEPS
    # Primero: bootstrap_hooks debe correr antes que constitution/traceability.
    assert sdd_init._SEEDED_STEPS[0] == "hooks"


def test_sdd_gate_hook_sh_esta_en_el_wiring_ejecutable():
    assert ".claude/sdd_gate_hook.sh" in sdd_init._EXECUTABLE_WIRING


def test_seed_pipeline_steps_incluye_hooks():
    config_text = "pipeline:\n  steps:\n    - constitution\n    - tests\n"
    result = sdd_init._seed_pipeline_steps(config_text)
    assert "- hooks" in result


def test_main_instala_y_marca_ejecutable(tmp_path):
    code = sdd_init.main([str(tmp_path), "--language=none"])
    assert code == 0
    hook = tmp_path / ".claude" / "sdd_gate_hook.sh"
    assert hook.exists()
    assert hook.stat().st_mode & 0o111  # al menos algun bit de ejecucion
