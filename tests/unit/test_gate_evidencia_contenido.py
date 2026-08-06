"""La evidencia spec-first es el contenido de la spec, no su mtime (SPEC-017 US3).

El criterio anterior comparaba la mtime de la spec contra la de
`.sdd/current-spec`. Fallaba en las dos direcciones a la vez: bloqueaba el flujo
legítimo (varios commits por spec, `git checkout`, y el ciclo stash/restore del
propio `pre-commit`, que renueva mtimes) y no detenía a nadie, porque un `touch`
sobre la spec lo satisfacía sin escribir una palabra.

Los tres escenarios de aceptación de la spec están cubiertos acá:
spec simple, misma spec en varios commits, y dos specs con commit al final.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import sdd_gate

PLANTILLA_FR = (
    "## Functional Requirements\n\n- **FR-001** MUST: ...\n- **FR-002** SHOULD: ...\n"
)
CON_FR = (
    "## Functional Requirements\n\n"
    "- **FR-001** MUST: el gate exige requisitos escritos en la spec declarada.\n"
)


def _repo(tmp_path: Path, specs: dict[str, str]) -> Path:
    """Raíz con una fila `draft` por spec y el cuerpo que se le pase."""
    (tmp_path / ".sdd").mkdir()
    (tmp_path / "specs").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  name: demo\ndirs:\n  source_roots: [src]\n", encoding="utf-8"
    )
    filas = "".join(
        f"| {spec_id.split('-')[0]}-{spec_id.split('-')[1]} | Demo | draft | - "
        f"| hibrido | [{spec_id}.md]({spec_id}.md) |\n"
        for spec_id in specs
    )
    (tmp_path / "specs" / "SPECS_REGISTRY.md").write_text(
        "| ID | Título | Estado | Iteración | Formato | Archivo |\n"
        "|----|--------|--------|-----------|---------|---------|\n" + filas,
        encoding="utf-8",
    )
    for spec_id, cuerpo in specs.items():
        (tmp_path / "specs" / f"{spec_id}.md").write_text(cuerpo, encoding="utf-8")
    return tmp_path


def _declarar(repo: Path, *specs: str) -> None:
    (repo / ".sdd" / "current-spec").write_text(
        "# header\n" + "".join(f"{s}\n" for s in specs), encoding="utf-8"
    )


def _decide(repo: Path):
    return sdd_gate.decide({"tool_input": {"file_path": "src/a.py"}}, repo)


def _reset_post_commit(repo: Path) -> None:
    """Lo que hace `sdd_reset` tras cada commit: deja solo los comentarios."""
    current = repo / ".sdd" / "current-spec"
    lineas = current.read_text(encoding="utf-8").splitlines()
    current.write_text(
        "\n".join(ln for ln in lineas if ln.startswith("#")) + "\n", encoding="utf-8"
    )


# --- Escenario 1: spec simple -------------------------------------------------


def test_la_plantilla_recien_creada_no_desbloquea(tmp_path):
    """FR-US3-001: `sdd_spec.py` deja placeholders; eso no es una spec escrita."""
    repo = _repo(tmp_path, {"SPEC-001-demo": PLANTILLA_FR})
    _declarar(repo, "SPEC-001-demo")

    allow, reason = _decide(repo)

    assert not allow
    assert "SPEC-001-demo" in reason


def test_el_motivo_pide_escribir_los_fr_y_no_reeditar_la_spec(tmp_path):
    """FR-US3-003: el motivo viejo mandaba a 'editar la spec después de declararla'.

    Con la spec ya escrita eso era instrucción imposible de cumplir: el operador
    terminaba haciendo `touch` para engañar al criterio.
    """
    repo = _repo(tmp_path, {"SPEC-001-demo": PLANTILLA_FR})
    _declarar(repo, "SPEC-001-demo")

    _, reason = _decide(repo)

    assert "FR" in reason
    assert "despues de declararla" not in reason.lower()


def test_con_los_fr_escritos_desbloquea(tmp_path):
    repo = _repo(tmp_path, {"SPEC-001-demo": PLANTILLA_FR})
    _declarar(repo, "SPEC-001-demo")
    (repo / "specs" / "SPEC-001-demo.md").write_text(CON_FR, encoding="utf-8")

    allow, reason = _decide(repo)

    assert allow, reason


def test_la_decision_no_depende_del_orden_de_las_mtimes(tmp_path):
    """SC-001: el mismo estado decide igual con las mtimes en cualquier orden."""
    repo = _repo(tmp_path, {"SPEC-001-demo": CON_FR})
    _declarar(repo, "SPEC-001-demo")
    spec = repo / "specs" / "SPEC-001-demo.md"
    current = repo / ".sdd" / "current-spec"

    for mas_nuevo in (spec, current):
        futuro = time.time() + 60
        os.utime(mas_nuevo, (futuro, futuro))
        allow, reason = _decide(repo)
        assert allow, f"bloqueó con {mas_nuevo.name} más nuevo: {reason}"


# --- Escenario 2: misma spec, varios commits ---------------------------------


def test_varios_commits_de_la_misma_spec_sin_volver_a_tocarla(tmp_path):
    """SC-002: el caso que el criterio mtime volvía imposible sin ceremonia.

    Tras cada commit el hook `sdd-reset` limpia la declaración; redeclarar la
    misma spec —ya escrita y sin cambios— tiene que alcanzar.
    """
    repo = _repo(tmp_path, {"SPEC-001-demo": CON_FR})
    spec = repo / "specs" / "SPEC-001-demo.md"
    contenido_original = spec.read_text(encoding="utf-8")

    for _ in range(3):
        _declarar(repo, "SPEC-001-demo")
        allow, reason = _decide(repo)
        assert allow, reason
        _reset_post_commit(repo)
        # Sin declaración vigente no se puede seguir editando: el reset cumple.
        assert not _decide(repo)[0]

    assert spec.read_text(encoding="utf-8") == contenido_original


def test_el_stash_de_pre_commit_ya_no_bloquea(tmp_path):
    """Reproducción del incidente al cerrar SPEC-016.

    `pre-commit` guarda y restaura los archivos no staged, y al restaurarlos
    renueva su mtime: `.sdd/current-spec` quedaba más nuevo que la spec y el
    gate concluía que la spec no se había editado, en pleno commit legítimo.
    """
    repo = _repo(tmp_path, {"SPEC-001-demo": CON_FR})
    _declarar(repo, "SPEC-001-demo")
    futuro = time.time() + 60
    os.utime(repo / ".sdd" / "current-spec", (futuro, futuro))

    allow, reason = _decide(repo)

    assert allow, reason


# --- Escenario 3: dos specs, commit al final ---------------------------------


def test_dos_specs_completas_desbloquean(tmp_path):
    repo = _repo(tmp_path, {"SPEC-001-demo": CON_FR, "SPEC-002-otra": CON_FR})
    _declarar(repo, "SPEC-001-demo", "SPEC-002-otra")

    allow, reason = _decide(repo)

    assert allow, reason


def test_una_spec_incompleta_bloquea_aunque_la_otra_este_escrita(tmp_path):
    """FR-US3-002: endurecimiento respecto del criterio viejo.

    Antes bastaba con que *alguna* spec declarada estuviera tocada, así que
    declarar dos y escribir una habilitaba las dos.
    """
    repo = _repo(tmp_path, {"SPEC-001-demo": CON_FR, "SPEC-002-otra": PLANTILLA_FR})
    _declarar(repo, "SPEC-001-demo", "SPEC-002-otra")

    allow, reason = _decide(repo)

    assert not allow
    assert "SPEC-002-otra" in reason
    assert "SPEC-001-demo" not in reason, "el motivo debe señalar solo la incompleta"


def test_todas_las_declaradas_se_validan_contra_el_registro(tmp_path):
    """FR-US2-003: la validez también se exige a cada una, no a la primera."""
    repo = _repo(tmp_path, {"SPEC-001-demo": CON_FR})
    _declarar(repo, "SPEC-001-demo", "SPEC-404-fantasma")

    allow, reason = _decide(repo)

    assert not allow
    assert "SPEC-404-fantasma" in reason


# --- Escape hatch y textos al operador ---------------------------------------


def test_el_bypass_permite_pero_deja_rastro(tmp_path, monkeypatch, capsys):
    """FR-US3-004: alternativa acotada a `--no-verify`, que apaga todo el pre-commit."""
    repo = _repo(tmp_path, {"SPEC-001-demo": PLANTILLA_FR})
    _declarar(repo, "SPEC-001-demo")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("SDD_GATE_BYPASS", "rescate de un repo a medio migrar")

    assert sdd_gate.main(["src/a.py"]) == 0

    err = capsys.readouterr().err
    assert "rescate de un repo a medio migrar" in err
    assert "bloqueada" in err, "el bypass tiene que mostrar lo que se saltea"


def test_el_bypass_vacio_no_habilita(tmp_path, monkeypatch):
    repo = _repo(tmp_path, {"SPEC-001-demo": PLANTILLA_FR})
    _declarar(repo, "SPEC-001-demo")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("SDD_GATE_BYPASS", "   ")

    assert sdd_gate.main(["src/a.py"]) == 2


def test_los_textos_al_operador_hablan_del_contenido(tmp_path):
    """FR-US3-005: el mensaje de `sdd_spec` y el header de la plantilla."""
    raiz = Path(__file__).resolve().parents[2]
    fuente = (raiz / "core" / "sdd_spec.py").read_text(encoding="utf-8")
    header = (raiz / "templates" / "wiring" / "current-spec").read_text(
        encoding="utf-8"
    )

    for texto in (fuente, header):
        assert "DESPUÉS" not in texto
        assert "después de declararla" not in texto
    assert "requisitos escritos" in fuente or "los FR" in fuente
    assert "requisitos" in header
