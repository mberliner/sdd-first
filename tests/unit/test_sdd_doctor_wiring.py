"""El doctor no da por bueno un wiring que no cablea el gate.

SPEC-014 FR-US1-002 (antes G-4 de `docs/IDEAS.md`) y FR-US2-003. La campana de
usabilidad reprodujo el falso positivo completo: un `.pre-commit-config.yaml`
propio con solo `ruff` y un `.claude/settings.json` propio, y `sdd-doctor`
respondiendo "Instalacion SDD sana" sobre un proyecto sin ninguna capa de gate.
"""

from __future__ import annotations

import sdd_doctor
import sdd_init
from conftest import crear_proyecto_brownfield


def _correr_doctor(destino, monkeypatch, capsys) -> tuple[int, str]:
    """El doctor resuelve la raiz desde el cwd: hay que estar en el destino."""
    monkeypatch.chdir(destino)
    codigo = sdd_doctor.main([])
    return codigo, capsys.readouterr().out


def test_wiring_propio_del_proyecto_es_un_problema(tmp_path, monkeypatch, capsys):
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=True)
    sdd_init.main([str(tmp_path), "--language=python"])
    codigo, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    assert codigo == 1
    assert "no invoca sdd_gate.py" in salida
    assert "no invoca sdd_gate_hook.sh" in salida
    assert "Instalación SDD sana" not in salida


def test_wiring_del_kit_no_es_un_problema(tmp_path, monkeypatch, capsys):
    """Contraste de control: mismo proyecto, wiring instalado por el kit."""
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=False)
    sdd_init.main([str(tmp_path), "--language=python"])
    _, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    assert "no invoca" not in salida


def test_falta_de_archivo_se_reporta_distinto_de_contenido_ajeno(
    tmp_path, monkeypatch, capsys
):
    """Ausencia y presencia-sin-cablear son dos problemas distintos: el primero
    lo arregla reinstalar, el segundo hay que fusionarlo a mano."""
    crear_proyecto_brownfield(tmp_path, layout="app", con_wiring=False)
    sdd_init.main([str(tmp_path), "--language=python"])
    (tmp_path / ".pre-commit-config.yaml").unlink()
    _, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    assert "falta .pre-commit-config.yaml" in salida


def test_el_drift_nombra_el_artefacto_desincronizado(tmp_path, monkeypatch, capsys):
    """FR-US2-003: recien instalado y sin correr render, lo que falta es
    CONSTITUTION.md — el mensaje tiene que decirlo en vez de citar una lista fija.
    """
    crear_proyecto_brownfield(tmp_path, layout="app")
    sdd_init.main([str(tmp_path), "--language=python"])
    _, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    problemas = [line for line in salida.splitlines() if "desincronizados:" in line]
    assert problemas, salida
    assert any("CONSTITUTION.md" in line for line in problemas)


def test_el_drift_cita_la_ruta_vendorizada_del_script(tmp_path, monkeypatch, capsys):
    """FR-US2-002: en un derivado el script vive en tools/sdd/core/, no en core/."""
    crear_proyecto_brownfield(tmp_path, layout="app")
    sdd_init.main([str(tmp_path), "--language=python"])
    _, salida = _correr_doctor(tmp_path, monkeypatch, capsys)
    assert "python tools/sdd/core/render.py" in salida


# -- SPEC-023 US2: el doctor repara la seccion de relaciones --------------------
#
# La inyeccion de la seccion ausente (FR-US2-008) y el cierre de reciprocos
# (FR-US2-009) son de aca, no del validador: un gate que modifica lo que valida
# deja de ser gate (FR-US2-011). Ambas son repetibles, no un paso unico de
# migracion.

import check_traceability as ct  # noqa: E402
from test_check_traceability import _seccion  # noqa: E402


def _repo_de_specs(tmp_path, specs) -> None:
    """`specs` = {SPEC-NNN: (formato, cuerpo)} + su registro."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    filas = [
        "| ID | Título | Estado | Iteración | Formato | Archivo |",
        "|----|--------|--------|-----------|---------|---------|",
    ]
    for spec_id, (formato, cuerpo) in specs.items():
        archivo = f"{spec_id}-x.md"
        (specs_dir / archivo).write_text(cuerpo, encoding="utf-8")
        filas.append(
            f"| {spec_id} | Demo | draft | - | {formato} | [{archivo}]({archivo}) |"
        )
    (specs_dir / "SPECS_REGISTRY.md").write_text("\n".join(filas) + "\n", "utf-8")


def test_inyecta_la_seccion_ausente_y_deja_pasar_al_validador(tmp_path):
    """FR-US2-008: tambien en una spec hibrida escrita a mano post-migracion."""
    _repo_de_specs(
        tmp_path,
        {
            "SPEC-001": ("hibrido", "# SPEC-001\n\n## Clarifications\n\n- nada\n"),
            "SPEC-002": ("casero", "# SPEC-002\n\ngenerada por render.py\n"),
        },
    )

    problemas = sdd_doctor._relaciones_problemas(tmp_path, fix=False)
    assert any("SPEC-001-x.md" in p for p in problemas)
    assert not any("SPEC-002-x.md" in p for p in problemas)  # casero queda fuera

    assert sdd_doctor._relaciones_problemas(tmp_path, fix=True) == []

    texto = (tmp_path / "specs" / "SPEC-001-x.md").read_text(encoding="utf-8")
    assert ct.parse_relations(texto) == {campo: () for campo in ct.RELATION_FIELDS}
    # La seccion entra antes de la primera seccion posterior a las User Stories.
    assert texto.index("Relación con specs") < texto.index("## Clarifications")
    # La casero no se toca: agregarle la seccion produciria drift en `render`.
    assert "Relación con specs" not in (tmp_path / "specs" / "SPEC-002-x.md").read_text(
        encoding="utf-8"
    )


def test_cierra_el_reciproco_de_un_enlace_escrito_a_mano(tmp_path):
    """FR-US2-009/011: sirve igual hoy que dentro de un anio, y es idempotente."""
    _repo_de_specs(
        tmp_path,
        {
            "SPEC-001": (
                "hibrido",
                "# SPEC-001\n\n" + _seccion(**{"Depende de": "SPEC-002"}),
            ),
            "SPEC-002": ("hibrido", "# SPEC-002\n\n" + _seccion()),
        },
    )

    problemas = sdd_doctor._relaciones_problemas(tmp_path, fix=False)
    assert any("Es dependencia de" in p and "SPEC-002-x.md" in p for p in problemas)

    assert sdd_doctor._relaciones_problemas(tmp_path, fix=True) == []

    destino = tmp_path / "specs" / "SPEC-002-x.md"
    escrito = destino.read_text(encoding="utf-8")
    assert "**Es dependencia de:** [SPEC-001](SPEC-001-x.md)" in escrito
    # Repetible: una segunda corrida no encuentra nada que hacer ni duplica.
    assert sdd_doctor._relaciones_problemas(tmp_path, fix=True) == []
    assert destino.read_text(encoding="utf-8") == escrito


def test_una_spec_sin_seccion_recibe_la_vuelta_en_la_misma_corrida(tmp_path):
    """FR-US2-008/009: inyectar y cerrar son una sola operacion de reparacion."""
    _repo_de_specs(
        tmp_path,
        {
            "SPEC-001": ("hibrido", "# SPEC-001\n\n" + _seccion(Extiende="SPEC-002")),
            "SPEC-002": ("hibrido", "# SPEC-002\n\n## Clarifications\n"),
        },
    )

    assert sdd_doctor._relaciones_problemas(tmp_path, fix=True) == []

    escrito = (tmp_path / "specs" / "SPEC-002-x.md").read_text(encoding="utf-8")
    assert "**Extendida por:** [SPEC-001](SPEC-001-x.md)" in escrito


# -- FR-US1-006: se verifica la estructura, no el texto crudo ------------------

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

# Wiring *inerte* que menciona la invocacion donde no ejecuta nada. Es el caso
# que el `in` sobre el archivo entero daba por bueno: un comentario alcanza para
# satisfacerlo, incluso uno que dice lo contrario de lo que el chequeo afirma.
WIRING_INERTE = {
    ".pre-commit-config.yaml": (
        "# Este proyecto NO usa sdd_gate.py: se saco el hook a proposito.\n"
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: ruff\n"
        "        name: ruff\n"
        "        entry: ruff check\n"
        "        language: system\n"
    ),
    ".claude/settings.json": '{"hooks": {"PreToolUse": []}, "_nota": "sin sdd_gate_hook.sh"}',
    ".agents/hooks.json": '{"sdd-gate": {"PreToolUse": []}, "_nota": "agy_gate_hook.py"}',
    ".opencode/plugin/sdd-gate.js": "// sdd_gate.py — plugin vaciado a proposito\n",
}


def _proyecto_con_wiring(tmp_path: Path, contenidos: dict[str, str]) -> Path:
    (tmp_path / ".sdd").mkdir(parents=True)
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  name: probe\ndirs:\n  source_roots: [src]\n", encoding="utf-8"
    )
    for rel, cuerpo in contenidos.items():
        destino = tmp_path / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(cuerpo, encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("rel", sorted(WIRING_INERTE))
def test_una_mencion_sin_ejecucion_no_cuenta_como_cableado(tmp_path, rel):
    """FR-US1-006: la invocacion tiene que estar donde algo la ejecuta."""
    repo = _proyecto_con_wiring(tmp_path, WIRING_INERTE)
    problemas = sdd_doctor._gate_wiring_problems(repo)
    assert any(rel in p for p in problemas), (
        f"{rel} menciona la invocacion pero no la ejecuta, y el doctor lo dio "
        f"por cableado. Problemas reportados: {problemas}"
    )


def test_el_plugin_de_opencode_esta_bajo_control(tmp_path):
    """FR-US1-006: sdd-init lo instala siempre, asi que su ausencia es un problema."""
    contenidos = dict(WIRING_INERTE)
    del contenidos[".opencode/plugin/sdd-gate.js"]
    repo = _proyecto_con_wiring(tmp_path, contenidos)
    problemas = sdd_doctor._gate_wiring_problems(repo)
    assert any("sdd-gate.js" in p for p in problemas), problemas


def test_un_wiring_que_no_parsea_es_un_problema(tmp_path):
    """Un JSON roto no puede contar como pase: no se pudo verificar nada."""
    contenidos = dict(WIRING_INERTE)
    contenidos[".claude/settings.json"] = "{ esto no es JSON sdd_gate_hook.sh"
    repo = _proyecto_con_wiring(tmp_path, contenidos)
    problemas = sdd_doctor._gate_wiring_problems(repo)
    assert any("settings.json" in p for p in problemas), problemas
