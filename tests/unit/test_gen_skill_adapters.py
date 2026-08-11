"""El generador de adaptadores es invocable con una raiz explicita (SPEC-016 FR-001).

Antes la raiz salia solo de `find_repo_root()` sobre el `cwd`, asi que `sdd_init`
—que corre desde el clon del kit apuntando a otro directorio— no podia reusarlo
sin cambiar de directorio ni lanzar un subproceso. Estos tests fijan el contrato
de `generate()`: recibe la raiz, no imprime, y devuelve lo escrito, el drift y
los problemas de validacion para que cada llamador reporte a su manera.
"""

from __future__ import annotations

import gen_skill_adapters
import pytest

FUENTE = """---
name: {name}
description: Hace algo util.
allowed-tools: Read, Grep
---

Cuerpo de la skill.
"""


@pytest.fixture
def proyecto(tmp_path):
    """Raiz minima con una skill y su playbook (que `_validate` exige)."""

    def _crear(name: str = "demo", fuente: str | None = None):
        skill = tmp_path / ".agents" / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            fuente if fuente is not None else FUENTE.format(name=name),
            encoding="utf-8",
        )
        playbook = tmp_path / "docs" / "playbooks"
        playbook.mkdir(parents=True, exist_ok=True)
        (playbook / f"{name}.md").write_text("# Playbook", encoding="utf-8")
        return tmp_path

    return _crear


def test_genera_sobre_la_raiz_recibida_no_sobre_el_cwd(proyecto, tmp_path, monkeypatch):
    otro = tmp_path.parent / "cwd-distinto"
    otro.mkdir(exist_ok=True)
    monkeypatch.chdir(otro)
    raiz = proyecto()

    resultado = gen_skill_adapters.generate(raiz)

    assert (raiz / ".claude" / "skills" / "demo" / "SKILL.md").exists()
    assert (raiz / ".opencode" / "command" / "demo.md").exists()
    assert sorted(resultado.written) == [
        ".claude/skills/demo/SKILL.md",
        ".opencode/command/demo.md",
    ]
    assert resultado.skills == 1


def test_check_no_escribe_y_reporta_el_drift(proyecto):
    """SPEC-013 FR-007: el SKILL.md generado (p.ej. sdd-configure) queda sin drift."""
    raiz = proyecto()
    resultado = gen_skill_adapters.generate(raiz, check=True)

    assert resultado.written == []
    assert not (raiz / ".claude" / "skills" / "demo" / "SKILL.md").exists()
    assert len(resultado.drift) == 2

    gen_skill_adapters.generate(raiz)
    assert gen_skill_adapters.generate(raiz, check=True).drift == []


def test_una_fuente_invalida_se_reporta_sin_propagar_la_excepcion(proyecto):
    """El llamador decide que hacer: `main` sale 1, `sdd_init` avisa y sigue."""
    raiz = proyecto(fuente="sin frontmatter")
    resultado = gen_skill_adapters.generate(raiz)
    assert resultado.problems
    assert "frontmatter" in resultado.problems[0]


def test_un_playbook_faltante_es_un_problema_de_validacion(proyecto, tmp_path):
    raiz = proyecto()
    (raiz / "docs" / "playbooks" / "demo.md").unlink()
    resultado = gen_skill_adapters.generate(raiz)
    assert any("playbook" in p for p in resultado.problems)


def test_sin_carpeta_de_skills_no_hay_nada_que_generar(tmp_path):
    resultado = gen_skill_adapters.generate(tmp_path)
    assert resultado == gen_skill_adapters.Result(
        written=[], drift=[], problems=[], skills=0
    )
