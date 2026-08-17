"""Tests de los pasos sembrados por sdd_init --'hooks' (SPEC-004 FR-005) y
'render' (SPEC-014 FR-US1-005)-- y del wiring ejecutable
(.claude/sdd_gate_hook.sh).

El wiring ejecutable se verifica en dos niveles porque NTFS no puede expresar
el resultado (SPEC-012): la *intencion* --que el instalador aplique chmod 0o755
a cada destino de `_EXECUTABLE_WIRING`-- corre en todas las plataformas; el
*efecto* sobre `st_mode`, solo donde el sistema de archivos lo soporta.
"""

from __future__ import annotations

from pathlib import Path

import sdd_init
from conftest import requiere_permisos_posix


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


def test_render_esta_en_los_pasos_sembrados_por_defecto():
    # SPEC-014 FR-US1-005: sin este paso nada vigila el drift de lo generado en
    # un derivado, y el pipeline reporta VERDE sobre una constitucion obsoleta.
    assert "render" in sdd_init._SEEDED_STEPS


def test_render_se_siembra_antes_de_los_pasos_de_codigo():
    # `render --check` es lectura pura: tiene que decidir antes de que la suite
    # del proyecto gaste tiempo, y antes de `coverage`, el mas caro.
    pasos = sdd_init._SEEDED_STEPS
    assert pasos.index("render") < pasos.index("tests")
    assert pasos.index("render") < pasos.index("coverage")


def test_seed_pipeline_steps_incluye_render():
    config_text = "pipeline:\n  steps:\n    - constitution\n    - tests\n"
    result = sdd_init._seed_pipeline_steps(config_text)
    assert "- render" in result


def test_main_aplica_chmod_al_wiring_ejecutable(tmp_path, monkeypatch):
    # FR-001: verifica la intencion, no el efecto, asi la proteccion sigue viva
    # en Windows (si alguien saca el chmod de sdd_init.py, esto falla ahi
    # tambien).
    aplicados: dict[Path, int] = {}
    original = Path.chmod

    def espia(self: Path, mode: int, **kwargs) -> None:
        aplicados[self] = mode
        original(self, mode, **kwargs)

    monkeypatch.setattr(Path, "chmod", espia)

    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0

    for destino in sdd_init._EXECUTABLE_WIRING:
        ruta = tmp_path / destino
        assert ruta.exists()
        assert aplicados.get(ruta) == 0o755, f"no se aplico chmod a {destino}"


@requiere_permisos_posix
def test_el_wiring_queda_ejecutable_en_disco(tmp_path):
    # FR-002: el efecto real, donde el sistema de archivos puede expresarlo.
    # SPEC-012 FR-003: el chmod sobre _EXECUTABLE_WIRING se conserva en sdd_init.
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    hook = tmp_path / ".claude" / "sdd_gate_hook.sh"
    assert hook.exists()
    assert hook.stat().st_mode & 0o111  # al menos algun bit de ejecucion


def test_constitution_se_siembra_despues_de_los_pasos_que_enforzan_principios():
    """SPEC-020 FR-US2-006: declarado no es ejecutado.

    El paso verifica que el enforcement de cada principio haya corrido, asi que
    tiene que correr despues de esos pasos. Sembrado segundo --como estaba--
    reportaba reservas por todos los principios en cada corrida, y ademas
    contradecia su propia precondicion documentada (`render` antes).
    """
    pasos = sdd_init._SEEDED_STEPS
    assert pasos.index("constitution") > pasos.index("render")
    assert pasos.index("constitution") > pasos.index("naming")
    assert pasos.index("constitution") > pasos.index("traceability")
    assert pasos.index("constitution") > pasos.index("coverage")


def test_seed_pipeline_steps_descarta_comentario_intercalado():
    """SPEC-004 FR-010: un comentario entre pasos del bloque original no corta
    el descarte a mitad de camino. `_seed_pipeline_steps` debe seguir
    descartando hasta la desindentacion real, no hasta la primera linea que no
    matchea '- '."""
    config_text = (
        "pipeline:\n"
        "  steps:\n"
        "    - constitution\n"
        "    # comentario intercalado\n"
        "    - tests\n"
        "    - coverage\n"
    )
    result = sdd_init._seed_pipeline_steps(config_text)
    pasos = [
        ln.strip()[2:] for ln in result.splitlines() if ln.strip().startswith("- ")
    ]
    assert pasos.count("tests") == 1
    assert pasos.count("coverage") == 1
    assert pasos.count("constitution") == 1


def test_e2e_se_siembra_despues_de_constitution():
    """`e2e` es el mas caro y va ultimo (SPEC-018 FR-US3-003), asi que la
    posicion de `constitution` no lo desplaza."""

    class _Layout:
        tests_integration = None
        tests_e2e = "tests/e2e"

    config_text = "pipeline:\n  steps:\n    - constitution\n"
    result = sdd_init._seed_pipeline_steps(config_text, _Layout())
    pasos = [
        ln.strip()[2:] for ln in result.splitlines() if ln.strip().startswith("- ")
    ]
    assert pasos.index("e2e") > pasos.index("constitution")
