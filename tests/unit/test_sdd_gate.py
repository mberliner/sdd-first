"""Tests de la lógica de decisión del gate spec-first.

SPEC-002 FR-002/FR-003 (declaración + edición posterior) y SPEC-006
FR-001/FR-002/FR-003 (el gate verifica el estado de la spec, no solo su
existencia por substring).
"""

import os
import time
from pathlib import Path

import sdd_gate


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


def _declare(repo: Path, spec_id: str, *, touch_spec_after: bool) -> None:
    spec_file = repo / "specs" / f"{spec_id}.md"
    current = repo / ".sdd" / "current-spec"
    if touch_spec_after:
        current.write_text(f"{spec_id}\n", encoding="utf-8")
        spec_file.write_text("# spec\n", encoding="utf-8")
        later = time.time() + 5
        os.utime(spec_file, (later, later))
    else:
        spec_file.write_text("# spec\n", encoding="utf-8")
        current.write_text(f"{spec_id}\n", encoding="utf-8")
        later = time.time() + 5
        os.utime(current, (later, later))


def _payload(path: str) -> dict:
    return {"tool_input": {"file_path": path}}


def test_permite_rutas_fuera_del_codigo_fuente(tmp_path):
    repo = _make_repo(tmp_path)
    allow, _ = sdd_gate.decide(_payload(str(repo / "docs" / "x.md")), repo)
    assert allow


def test_bloquea_sin_spec_declarada(tmp_path):
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


def test_bloquea_spec_no_editada_despues_de_declarar(tmp_path):
    repo = _make_repo(tmp_path)
    _declare(repo, "SPEC-001-demo", touch_spec_after=False)
    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)
    assert not allow
    assert "editada" in reason


def test_permite_con_spec_declarada_y_editada(tmp_path):
    repo = _make_repo(tmp_path)
    _declare(repo, "SPEC-001-demo", touch_spec_after=True)
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
    """SPEC-006 FR-002: una fila 'archived' ya no desbloquea el gate."""
    repo = _make_repo(tmp_path)
    _set_registry_estado(repo, "SPEC-001-demo", "archived")
    _declare(repo, "SPEC-001-demo", touch_spec_after=True)

    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)

    assert not allow
    assert "archived" in reason


def test_bloquea_spec_superseded(tmp_path):
    repo = _make_repo(tmp_path)
    _set_registry_estado(repo, "SPEC-001-demo", "superseded")
    _declare(repo, "SPEC-001-demo", touch_spec_after=True)

    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)

    assert not allow
    assert "superseded" in reason


def test_bloquea_spec_mencionada_solo_en_prosa_no_en_tabla(tmp_path):
    """Antes de SPEC-006, un substring match dejaba pasar esto (bug real)."""
    repo = _make_repo(tmp_path)
    (repo / "specs" / "SPECS_REGISTRY.md").write_text(
        "| ID | Título | Estado | Iteración | Formato | Archivo |\n"
        "|----|--------|--------|-----------|---------|---------|\n"
        "| SPEC-001 | Demo | draft | - | casero | [SPEC-001-demo.md](SPEC-001-demo.md) |\n"
        "\n## Roadmap\n\n- Pendiente: SPEC-002-fantasma en el futuro.\n",
        encoding="utf-8",
    )
    _declare(repo, "SPEC-002-fantasma", touch_spec_after=True)

    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)

    assert not allow
    assert "SPEC-002-fantasma" in reason


def test_permite_spec_con_estado_active(tmp_path):
    repo = _make_repo(tmp_path)
    _set_registry_estado(repo, "SPEC-001-demo", "active")
    _declare(repo, "SPEC-001-demo", touch_spec_after=True)

    allow, reason = sdd_gate.decide(_payload(str(repo / "src" / "a.py")), repo)

    assert allow, reason
