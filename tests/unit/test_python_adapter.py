"""Tests del dispatcher del adaptador python (SPEC-003 FR-001/FR-002/FR-004)."""

from pathlib import Path

import adapter
import pytest
from sdd_config import EXIT_OMITIDO, SddConfig


def _cfg(tmp_path: Path, raw: dict) -> SddConfig:
    return SddConfig(repo_root=tmp_path, raw=raw)


@pytest.fixture(autouse=True)
def sin_subprocesos(monkeypatch):
    """Ningún test de esta suite debe llegar a invocar una tool real."""

    def _explota(cmd, cwd):
        raise AssertionError(f"no debía ejecutarse: {cmd}")

    monkeypatch.setattr(adapter, "_run", _explota)


def test_naming_sin_targets_se_omite_con_exit_omitido(tmp_path):
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain", "tests_unit": "tests/unit"}})
    assert adapter.step_naming(tmp_path, cfg) == EXIT_OMITIDO


def test_lint_sin_tool_se_omite_con_exit_omitido(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: False)
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain"}})
    assert adapter.step_lint(tmp_path, cfg) == EXIT_OMITIDO


def test_tests_sin_carpeta_se_omite_con_exit_omitido(tmp_path):
    cfg = _cfg(tmp_path, {"dirs": {"tests_unit": "tests/unit"}})
    assert adapter.step_tests(tmp_path, cfg) == EXIT_OMITIDO


def test_layers_sin_lint_imports_se_omite_con_exit_omitido(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter.shutil, "which", lambda name: None)
    cfg = _cfg(tmp_path, {})
    assert adapter.step_layers(tmp_path, cfg) == EXIT_OMITIDO


def test_layers_sin_el_paquete_raiz_en_disco_se_omite(tmp_path, monkeypatch):
    """SPEC-003 FR-011: era el unico paso de codigo sin guardia de targets.

    Con la tool instalada y `layers` sembrado —el estado de toda instalacion
    fresca— `lint-imports` abortaba con "Could not find package 'src'" y la
    instalacion salia ROJO en su primer pipeline.
    """
    monkeypatch.setattr(adapter.shutil, "which", lambda name: "/usr/bin/lint-imports")
    cfg = _cfg(tmp_path, {"layers": {"domain": [], "application": ["domain"]}})
    assert adapter.step_layers(tmp_path, cfg) == EXIT_OMITIDO


def test_layers_sin_capas_declaradas_se_omite(tmp_path, monkeypatch):
    """Sin `layers` no hay contrato que verificar: omitir, no correr en vacio."""
    monkeypatch.setattr(adapter.shutil, "which", lambda name: "/usr/bin/lint-imports")
    (tmp_path / "src").mkdir()
    assert adapter.step_layers(tmp_path, _cfg(tmp_path, {})) == EXIT_OMITIDO


def test_layers_con_capas_y_paquete_raiz_si_se_ejecuta(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(adapter, "_run", lambda cmd, cwd: llamadas.append(cmd) or 0)
    monkeypatch.setattr(adapter.shutil, "which", lambda name: "/usr/bin/lint-imports")
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"layers": {"domain": [], "application": ["domain"]}})
    assert adapter.step_layers(tmp_path, cfg) == 0
    assert llamadas[-1] == ["lint-imports"]


def test_con_targets_y_tool_si_se_ejecuta(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(adapter, "_run", lambda cmd, cwd: llamadas.append(cmd) or 0)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain"}})
    assert adapter.step_lint(tmp_path, cfg) == 0
    assert llamadas and "ruff" in llamadas[0]


# -- pasos que llegan a ejecutar la tool ----------------------------------------
#
# K-3: el adaptador estaba en 51%. La suite cubria las omisiones (la mitad
# interesante de SPEC-003) y casi ninguna rama donde el paso si corre.


def _grabador(monkeypatch, code=0):
    llamadas: list[list[str]] = []

    def _fake(cmd, cwd):
        llamadas.append(cmd)
        return code

    monkeypatch.setattr(adapter, "_run", _fake)
    return llamadas


def test_naming_con_targets_invoca_check_naming(tmp_path, monkeypatch):
    llamadas = _grabador(monkeypatch)
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"dirs": {"domain": "src/domain"}})
    assert adapter.step_naming(tmp_path, cfg) == 0
    assert "check_naming.py" in llamadas[0][1]


def test_format_con_targets_corre_ruff_en_modo_check(tmp_path, monkeypatch):
    llamadas = _grabador(monkeypatch)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "src").mkdir()
    assert adapter.step_format(tmp_path, _cfg(tmp_path, {})) == 0
    assert "--check" in llamadas[0]


def test_types_corre_mypy_strict(tmp_path, monkeypatch):
    llamadas = _grabador(monkeypatch)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "src").mkdir()
    assert adapter.step_types(tmp_path, _cfg(tmp_path, {})) == 0
    assert "--strict" in llamadas[0]


def test_security_corre_bandit(tmp_path, monkeypatch):
    llamadas = _grabador(monkeypatch)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "src").mkdir()
    assert adapter.step_security(tmp_path, _cfg(tmp_path, {})) == 0
    assert "bandit" in llamadas[0]


def test_types_y_security_sin_tool_se_omiten(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: False)
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {})
    assert adapter.step_types(tmp_path, cfg) == EXIT_OMITIDO
    assert adapter.step_security(tmp_path, cfg) == EXIT_OMITIDO


def test_types_y_security_sin_carpetas_se_omiten(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    cfg = _cfg(tmp_path, {})
    assert adapter.step_types(tmp_path, cfg) == EXIT_OMITIDO
    assert adapter.step_security(tmp_path, cfg) == EXIT_OMITIDO


def test_format_sin_tool_se_omite(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: False)
    (tmp_path / "src").mkdir()
    assert adapter.step_format(tmp_path, _cfg(tmp_path, {})) == EXIT_OMITIDO


def test_lint_y_format_sin_carpetas_se_omiten(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    cfg = _cfg(tmp_path, {})
    assert adapter.step_lint(tmp_path, cfg) == EXIT_OMITIDO
    assert adapter.step_format(tmp_path, cfg) == EXIT_OMITIDO


def test_tests_con_carpeta_corre_pytest(tmp_path, monkeypatch):
    llamadas = _grabador(monkeypatch)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    cfg = _cfg(tmp_path, {"dirs": {"tests_unit": "tests/unit"}})
    assert adapter.step_tests(tmp_path, cfg) == 0
    assert "tests/unit" in llamadas[0]


def test_tests_sin_pytest_se_omite(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: False)
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    cfg = _cfg(tmp_path, {"dirs": {"tests_unit": "tests/unit"}})
    assert adapter.step_tests(tmp_path, cfg) == EXIT_OMITIDO


def test_layers_falla_si_falla_el_generador(tmp_path, monkeypatch):
    """Si gen_import_linter no pudo escribir, no tiene sentido correr la tool."""
    llamadas = _grabador(monkeypatch, code=1)
    monkeypatch.setattr(adapter.shutil, "which", lambda name: "/usr/bin/lint-imports")
    (tmp_path / "src").mkdir()
    cfg = _cfg(tmp_path, {"layers": {"domain": []}})
    assert adapter.step_layers(tmp_path, cfg) == 1
    assert len(llamadas) == 1  # no llego a lint-imports


# -- step_coverage: el cuerpo, no solo sus omisiones ----------------------------


def _cfg_coverage(tmp_path, minimo=80, paths=("core",)):
    return _cfg(
        tmp_path,
        {
            "dirs": {"tests_unit": "tests/unit"},
            "pipeline": {"coverage": [{"paths": list(paths), "min": minimo}]},
        },
    )


def test_coverage_mide_cada_target_declarado(tmp_path, monkeypatch):
    llamadas = _grabador(monkeypatch)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "core").mkdir()
    assert adapter.step_coverage(tmp_path, _cfg_coverage(tmp_path)) == 0
    assert "--cov=core" in llamadas[0]
    assert "--cov-fail-under=80" in llamadas[0]


def test_coverage_falla_nombrando_el_target_incumplido(tmp_path, monkeypatch, capsys):
    _grabador(monkeypatch, code=1)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "core").mkdir()
    assert adapter.step_coverage(tmp_path, _cfg_coverage(tmp_path, minimo=95)) == 1
    assert "core (< 95%)" in capsys.readouterr().out


def test_coverage_omite_un_target_que_no_existe_todavia(tmp_path, monkeypatch, capsys):
    _grabador(monkeypatch)
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    cfg = _cfg_coverage(tmp_path, paths=("no-existe",))
    assert adapter.step_coverage(tmp_path, cfg) == EXIT_OMITIDO
    assert "no existe todavia" in capsys.readouterr().out


def test_coverage_sin_umbrales_o_sin_tool_o_sin_tests_se_omite(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: True)
    assert adapter.step_coverage(tmp_path, _cfg(tmp_path, {})) == EXIT_OMITIDO

    # con umbrales pero sin carpeta de tests
    assert adapter.step_coverage(tmp_path, _cfg_coverage(tmp_path)) == EXIT_OMITIDO

    # con umbrales y tests, pero sin pytest
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    monkeypatch.setattr(adapter, "_module_available", lambda m: False)
    assert adapter.step_coverage(tmp_path, _cfg_coverage(tmp_path)) == EXIT_OMITIDO


def test_coverage_sin_pytest_cov_se_omite(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "_module_available", lambda m: m != "pytest_cov")
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    assert adapter.step_coverage(tmp_path, _cfg_coverage(tmp_path)) == EXIT_OMITIDO


# -- main(): el dispatcher ------------------------------------------------------


def test_main_sin_paso_o_con_paso_desconocido_devuelve_2(capsys):
    assert adapter.main([]) == 2
    assert adapter.main(["inventado"]) == 2
    assert "Uso: adapter.py" in capsys.readouterr().err


def test_main_delega_en_el_paso_pedido(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  name: demo\n", encoding="utf-8"
    )
    assert adapter.main(["naming"]) == EXIT_OMITIDO  # sin carpetas: omite


def test_run_ejecuta_el_comando_de_verdad(tmp_path, monkeypatch, capsys):
    """`_run` es el unico punto que toca subprocess; el resto de la suite lo mockea."""
    monkeypatch.undo()
    assert adapter._run([__import__("sys").executable, "-c", "pass"], tmp_path) == 0
    assert "$ " in capsys.readouterr().out
