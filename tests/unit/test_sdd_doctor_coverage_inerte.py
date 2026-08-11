"""El paso `coverage` sin umbrales se informa como nota (SPEC-009 FR-US2-006).

Nota y no problema: un proyecto recien instalado que todavia no tiene suite es
sano, y un doctor que sale 1 sobre una instalacion fresca reintroduce el falso
negativo que SPEC-014 cerro del otro lado. El silencio tampoco sirve --un paso
que se omite en cada corrida ensena que el VERDE es ruido (K-5)--, asi que la
nota tiene que nombrar la herramienta que lo resuelve.
"""

from __future__ import annotations

from pathlib import Path

import sdd_doctor


class _Cfg:
    def __init__(self, steps: list[str], coverage: list) -> None:
        self.pipeline_steps = steps
        self.pipeline_coverage = coverage
        self.raw: dict = {}
        self.language = "python"


def test_avisa_cuando_coverage_no_tiene_umbrales(tmp_path: Path):
    notas = sdd_doctor._coverage_inerte(_Cfg(["tests", "coverage"], []), tmp_path)
    assert len(notas) == 1
    assert "sdd_coverage_baseline.py" in notas[0]


def test_callado_cuando_hay_umbrales(tmp_path: Path):
    cfg = _Cfg(["coverage"], [object()])
    assert sdd_doctor._coverage_inerte(cfg, tmp_path) == []


def test_callado_cuando_el_paso_no_esta_declarado(tmp_path: Path):
    # Un proyecto que decidio no correr `coverage` no tiene nada que arreglar.
    assert sdd_doctor._coverage_inerte(_Cfg(["tests"], []), tmp_path) == []


def test_es_nota_y_no_problema(tmp_path: Path, monkeypatch, capsys):
    # El invariante que importa: un derivado con el paso inerte sigue saliendo 0.
    monkeypatch.setattr(sdd_doctor, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sdd_doctor, "REQUIRED", [])
    monkeypatch.setattr(sdd_doctor, "_gate_wiring_problems", lambda root: [])
    monkeypatch.setattr(sdd_doctor, "_tests_sin_ejecutor", lambda cfg: [])
    # El drift de generados se mide contra el kit real; acá no es lo que se prueba.
    monkeypatch.setattr(sdd_doctor, "_drift", lambda script, root: None)
    monkeypatch.setattr(sdd_doctor, "load", lambda root: _Cfg(["coverage"], []))
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text("project: {}\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".sdd/current-spec\n", encoding="utf-8")

    assert sdd_doctor.main([]) == 0
    salida = capsys.readouterr().out
    assert "sdd_coverage_baseline.py" in salida
    assert "Problemas:" not in salida
