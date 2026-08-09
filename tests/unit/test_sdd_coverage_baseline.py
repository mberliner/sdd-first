"""core/sdd_coverage_baseline.py — el piso medido (SPEC-009 FR-US2-003..005).

Lo que se fija aca es la politica, que es lo que el nucleo aporta sobre la
medicion del adaptador: redondear hacia abajo, no pisar lo ya declarado, y no
perder los comentarios del config al escribir.
"""

from __future__ import annotations

from pathlib import Path

import sdd_coverage_baseline as baseline
from sdd_config import COVERAGE_BASELINE_PREFIX, EXIT_OMITIDO, load

CONFIG_BASE = """\
project:
  name: demo
  language: python

dirs:
  source_roots: [src]
  tests_unit: tests/unit

pipeline:
  # Este comentario tiene que sobrevivir a la escritura.
  steps:
    - tests
    - coverage

principles: []
"""


def _proyecto(tmp_path: Path, config: str = CONFIG_BASE) -> Path:
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text(config, encoding="utf-8")
    load.cache_clear()  # `load` esta cacheado por raiz: el test reescribe el config
    return tmp_path


def _releer(repo: Path):
    load.cache_clear()
    return load(repo)


def _con_medicion(monkeypatch, tmp_path, porcentaje: float, paths=("src",)):
    monkeypatch.setattr(baseline, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(baseline, "medir", lambda root, lang: (porcentaje, list(paths)))


# --- parseo de la linea de contrato -----------------------------------------


def test_parse_baseline_lee_la_linea():
    salida = f"ruido\n{COVERAGE_BASELINE_PREFIX} 84.90 core,adapters\nmas ruido"
    assert baseline.parse_baseline(salida) == (84.90, ["core", "adapters"])


def test_parse_baseline_ignora_lineas_malformadas():
    assert baseline.parse_baseline(f"{COVERAGE_BASELINE_PREFIX} 84.90") is None
    assert baseline.parse_baseline(f"{COVERAGE_BASELINE_PREFIX} x y") is None
    assert baseline.parse_baseline(f"{COVERAGE_BASELINE_PREFIX} 84.9 ,") is None
    assert baseline.parse_baseline("sin la linea") is None


# --- escritura ---------------------------------------------------------------


def test_escribe_el_piso_redondeado_hacia_abajo(tmp_path, monkeypatch):
    repo = _proyecto(tmp_path)
    _con_medicion(monkeypatch, repo, 84.90)

    assert baseline.main([]) == 0

    cfg = _releer(repo)
    assert [(list(t.paths), t.minimum) for t in cfg.pipeline_coverage] == [
        (["src"], 84)
    ]


def test_la_escritura_conserva_los_comentarios(tmp_path, monkeypatch):
    repo = _proyecto(tmp_path)
    _con_medicion(monkeypatch, repo, 91.0)

    assert baseline.main([]) == 0

    texto = (repo / ".sdd" / "config.yaml").read_text(encoding="utf-8")
    assert "# Este comentario tiene que sobrevivir a la escritura." in texto
    assert "principles: []" in texto  # la seccion siguiente sigue entera


def test_el_paso_coverage_deja_de_omitirse(tmp_path, monkeypatch):
    # SC-005: el efecto observable es que el paso pasa a verificar.
    repo = _proyecto(tmp_path)
    _con_medicion(monkeypatch, repo, 77.7)
    assert not _releer(repo).pipeline_coverage  # inerte antes

    baseline.main([])

    assert _releer(repo).pipeline_coverage  # verifica despues


def test_varios_paths_medidos_entran_en_una_entrada(tmp_path, monkeypatch):
    repo = _proyecto(tmp_path)
    _con_medicion(monkeypatch, repo, 60.2, paths=("core", "adapters"))

    baseline.main([])

    (target,) = _releer(repo).pipeline_coverage
    assert list(target.paths) == ["core", "adapters"]
    assert target.minimum == 60


# --- trinquete: no pisar lo declarado ---------------------------------------


def test_no_toca_un_umbral_ya_declarado(tmp_path, monkeypatch, capsys):
    config = CONFIG_BASE.replace(
        "principles: []",
        "  coverage:\n    - paths: [src]\n      min: 95\n\nprinciples: []",
    )
    repo = _proyecto(tmp_path, config)
    antes = (repo / ".sdd" / "config.yaml").read_text(encoding="utf-8")
    _con_medicion(monkeypatch, repo, 99.0)

    assert baseline.main([]) == 0

    assert (repo / ".sdd" / "config.yaml").read_text(encoding="utf-8") == antes
    assert "no se modifica" in capsys.readouterr().out


def test_avisa_cuando_el_trinquete_dejo_de_morder(tmp_path, monkeypatch, capsys):
    # El defecto que K-3 encontro en el propio kit: umbral 50 con cobertura 75.
    config = CONFIG_BASE.replace(
        "principles: []",
        "  coverage:\n    - paths: [src]\n      min: 50\n\nprinciples: []",
    )
    repo = _proyecto(tmp_path, config)
    _con_medicion(monkeypatch, repo, 75.0)

    assert baseline.main([]) == 0

    salida = capsys.readouterr().out
    assert "no esta mordiendo" in salida
    assert "min 50 < 75" in salida


def test_no_avisa_cuando_el_umbral_esta_al_dia(tmp_path, monkeypatch, capsys):
    config = CONFIG_BASE.replace(
        "principles: []",
        "  coverage:\n    - paths: [src]\n      min: 90\n\nprinciples: []",
    )
    repo = _proyecto(tmp_path, config)
    _con_medicion(monkeypatch, repo, 90.4)

    assert baseline.main([]) == 0
    assert "no esta mordiendo" not in capsys.readouterr().out


# --- omisiones ---------------------------------------------------------------


def test_se_omite_sin_config(tmp_path, monkeypatch):
    monkeypatch.setattr(baseline, "find_repo_root", lambda: tmp_path)
    assert baseline.main([]) == EXIT_OMITIDO


def test_se_omite_si_el_adaptador_no_pudo_medir(tmp_path, monkeypatch):
    repo = _proyecto(tmp_path)
    monkeypatch.setattr(baseline, "find_repo_root", lambda: repo)
    monkeypatch.setattr(baseline, "medir", lambda root, lang: None)
    assert baseline.main([]) == EXIT_OMITIDO


def test_se_omite_sin_seccion_pipeline(tmp_path, monkeypatch):
    repo = _proyecto(tmp_path, "project:\n  name: demo\n  language: python\n")
    _con_medicion(monkeypatch, repo, 50.0)
    assert baseline.main([]) == EXIT_OMITIDO


# --- medir(): el puente con el adaptador ------------------------------------


def test_medir_omite_language_none(tmp_path):
    assert baseline.medir(tmp_path, "none") is None


def test_medir_omite_lenguaje_sin_adaptador(tmp_path):
    assert baseline.medir(tmp_path, "cobol") is None


def test_medir_devuelve_none_si_el_adaptador_falla(tmp_path, monkeypatch):
    class _Proc:
        returncode = 3
        stdout = "(omitido: sin carpetas de tests todavia)\n"
        stderr = ""

    monkeypatch.setattr(baseline.subprocess, "run", lambda *a, **k: _Proc())
    assert baseline.medir(tmp_path, "python") is None


def test_medir_parsea_la_salida_del_adaptador(tmp_path, monkeypatch, capsys):
    class _Proc:
        returncode = 0
        stdout = f"corriendo pytest...\n{COVERAGE_BASELINE_PREFIX} 42.00 src\n"
        stderr = ""

    monkeypatch.setattr(baseline.subprocess, "run", lambda *a, **k: _Proc())
    assert baseline.medir(tmp_path, "python") == (42.0, ["src"])
    # La salida del adaptador se reemite: quien corre esto quiere ver la suite.
    assert "corriendo pytest" in capsys.readouterr().out
