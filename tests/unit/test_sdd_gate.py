"""Tests de la lógica de decisión del gate spec-first.

SPEC-017 US1 (bloqueo sin declaración) y US2 (la spec declarada tiene que
existir, estar registrada como fila y tener estado vigente). La evidencia por
contenido (US3) vive en `test_gate_evidencia_contenido.py`.
"""

from pathlib import Path

import sdd_gate

# Cuerpo mínimo que cuenta como "spec con requisitos escritos" (FR-US3-001).
SPEC_CON_FR = "# spec\n\n- **FR-001** MUST: el gate hace algo verificable.\n"


def _make_repo(tmp_path: Path) -> Path:
    (tmp_path / ".sdd").mkdir()
    (tmp_path / "specs").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  name: demo\ndirs:\n  source_roots: [src]\n",
        encoding="utf-8",
    )
    (tmp_path / "specs" / "SPECS_REGISTRY.md").write_text(
        "| ID | Título | Estado | Iteración | Formato | Archivo |\n"
        "|----|--------|--------|-----------|---------|---------|\n"
        "| SPEC-001 | Demo | draft | - | casero | [SPEC-001-demo.md](SPEC-001-demo.md) |\n",
        encoding="utf-8",
    )
    return tmp_path


def _declare(repo: Path, spec_id: str, *, cuerpo: str = SPEC_CON_FR) -> None:
    (repo / "specs" / f"{spec_id}.md").write_text(cuerpo, encoding="utf-8")
    (repo / ".sdd" / "current-spec").write_text(f"{spec_id}\n", encoding="utf-8")


def _payload(path: str) -> dict:
    return {"tool_input": {"file_path": path}}


def test_permite_rutas_fuera_del_codigo_fuente(tmp_path):
    """SPEC-017 FR-US1-001: ruta fuera de dirs.source_roots, se permite sin mas."""
    repo = _make_repo(tmp_path)
    allow, _ = sdd_gate.decide(_payload(str(repo / "docs" / "x.md")), repo)
    assert allow


def test_bloquea_sin_spec_declarada(tmp_path):
    """SPEC-017 FR-US1-002: sin spec en .sdd/current-spec, bloquea nombrando la via."""
    repo = _make_repo(tmp_path)
    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)
    assert not allow
    assert "spec" in reason.lower()


def test_bloquea_spec_declarada_inexistente(tmp_path):
    repo = _make_repo(tmp_path)
    (repo / ".sdd" / "current-spec").write_text("SPEC-999-nada\n", encoding="utf-8")
    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)
    assert not allow
    assert "SPEC-999-nada" in reason


def test_permite_con_spec_declarada_y_con_requisitos(tmp_path):
    """SPEC-001 FR-002 / SPEC-002 FR-002: el gate gobierna de hecho src/ con spec declarada."""
    repo = _make_repo(tmp_path)
    _declare(repo, "SPEC-001-demo")
    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)
    assert allow, reason


def test_ruta_relativa_se_resuelve_contra_repo_root(tmp_path):
    repo = _make_repo(tmp_path)
    allow, _ = sdd_gate.decide(_payload("src/a.py"), repo)
    assert not allow


def test_payload_sin_ruta_permite(tmp_path):
    repo = _make_repo(tmp_path)
    allow, _ = sdd_gate.decide({"tool_input": {}}, repo)
    assert allow


def _set_registry_estado(repo: Path, spec_id: str, estado: str) -> None:
    (repo / "specs" / "SPECS_REGISTRY.md").write_text(
        "| ID | Título | Estado | Iteración | Formato | Archivo |\n"
        "|----|--------|--------|-----------|---------|---------|\n"
        f"| SPEC-001 | Demo | {estado} | - | casero | [{spec_id}.md]({spec_id}.md) |\n",
        encoding="utf-8",
    )


def test_bloquea_spec_archivada_aunque_registrada(tmp_path):
    """SPEC-017 FR-US2-002: una fila 'archived' no desbloquea el gate."""
    repo = _make_repo(tmp_path)
    _set_registry_estado(repo, "SPEC-001-demo", "archived")
    _declare(repo, "SPEC-001-demo")

    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)

    assert not allow
    assert "archived" in reason


def test_bloquea_spec_superseded(tmp_path):
    repo = _make_repo(tmp_path)
    _set_registry_estado(repo, "SPEC-001-demo", "superseded")
    _declare(repo, "SPEC-001-demo")

    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)

    assert not allow
    assert "superseded" in reason


def test_bloquea_spec_mencionada_solo_en_prosa_no_en_tabla(tmp_path):
    """FR-US2-001: un substring match dejaba pasar esto (bug real del kit)."""
    repo = _make_repo(tmp_path)
    (repo / "specs" / "SPECS_REGISTRY.md").write_text(
        "| ID | Título | Estado | Iteración | Formato | Archivo |\n"
        "|----|--------|--------|-----------|---------|---------|\n"
        "| SPEC-001 | Demo | draft | - | casero | [SPEC-001-demo.md](SPEC-001-demo.md) |\n"
        "\n## Roadmap\n\n- Pendiente: SPEC-002-fantasma en el futuro.\n",
        encoding="utf-8",
    )
    _declare(repo, "SPEC-002-fantasma")

    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)

    assert not allow
    assert "SPEC-002-fantasma" in reason


def test_permite_spec_con_estado_active(tmp_path):
    repo = _make_repo(tmp_path)
    _set_registry_estado(repo, "SPEC-001-demo", "active")
    _declare(repo, "SPEC-001-demo")

    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)

    assert allow, reason


# -- SPEC-022 US3: el motivo del bloqueo dice que specs ya gobiernan el archivo --


def test_bloqueo_nombra_las_specs_que_gobiernan_el_archivo(tmp_path):
    """FR-US3-001: el aviso llega en el momento en que la pregunta importa."""
    repo = _make_repo(tmp_path)

    def indexador(file_path, repo_root):
        return [("SPEC-001-demo", "Demo")]

    allow, motivo = sdd_gate.decide(_payload("src/a.py"), repo, indexador=indexador)

    assert not allow
    assert "SPEC-001-demo: Demo" in motivo
    assert "--reuse" in motivo


def test_el_indice_no_se_computa_cuando_el_gate_permite(tmp_path):
    """FR-US3-002: el gate corre en cada PreToolUse; no puede escanear el repo."""
    repo = _make_repo(tmp_path)
    _declare(repo, "SPEC-001-demo")
    llamadas = []

    def indexador(file_path, repo_root):
        llamadas.append(file_path)
        return []

    allow, _motivo = sdd_gate.decide(_payload("src/a.py"), repo, indexador=indexador)

    assert allow
    assert llamadas == []


def test_sin_specs_asociadas_el_mensaje_es_el_de_siempre(tmp_path):
    """FR-US3-003: el aviso es informativo; no cambia qué se bloquea."""
    repo = _make_repo(tmp_path)

    _allow, con_indice = sdd_gate.decide(
        _payload("src/a.py"), repo, indexador=lambda *_: []
    )
    _allow2, sin_indice = sdd_gate.decide(_payload("src/a.py"), repo)

    assert "Specs que ya gobiernan" not in con_indice
    assert con_indice == sin_indice


def test_un_indexador_que_falla_no_altera_el_bloqueo(tmp_path):
    """FR-US3-003: el mismo mensaje y el mismo código de salida."""
    repo = _make_repo(tmp_path)

    def roto(file_path, repo_root):
        raise RuntimeError("indice roto")

    allow, motivo = sdd_gate.decide(_payload("src/a.py"), repo, indexador=roto)
    _allow, esperado = sdd_gate.decide(
        _payload("src/a.py"), repo, indexador=lambda *_: []
    )

    assert not allow
    assert motivo == esperado


def test_el_aviso_tambien_acompana_al_bloqueo_por_spec_invalida(tmp_path):
    """FR-US3-001: declarar una spec cerrada tampoco te deja sin salida."""
    repo = _make_repo(tmp_path)
    (repo / ".sdd" / "current-spec").write_text("SPEC-404-fantasma\n", encoding="utf-8")

    allow, motivo = sdd_gate.decide(
        _payload("src/a.py"), repo, indexador=lambda *_: [("SPEC-001-demo", "Demo")]
    )

    assert not allow
    assert "SPEC-001-demo" in motivo


def test_el_gate_real_nombra_la_spec_de_un_archivo_que_todavia_no_existe(tmp_path):
    """FR-US3-001 + FR-US2-003, sin indexador inyectado.

    Es el caso mas frecuente: una spec `draft` nombra en *Key Entities* el
    archivo que va a crear, y ese archivo nuevo es justo el que el gate bloquea
    primero. Si el indice descartara las rutas inexistentes, el aviso estaria
    ciego donde mas se necesita.
    """
    repo = _make_repo(tmp_path)
    (repo / "specs" / "SPEC-001-demo.md").write_text(
        "# demo\n\n## Key Entities\n\n- `src/nuevo.py` — lo que voy a crear\n",
        encoding="utf-8",
    )

    allow, motivo = sdd_gate.decide(_payload("src/nuevo.py"), repo)

    assert not allow
    assert "SPEC-001-demo: Demo" in motivo
    assert not (repo / "src" / "nuevo.py").exists()
