"""El paso `e2e` corre lo declarado y no se mezcla con la cobertura (SPEC-018 US3).

K-4 de `docs/IDEAS.md`: la suite e2e es el nivel de test *primario* de un
proyecto generador --el unico que ejercita lo que el kit hace **para otros**, que
es distinto de lo que hace sobre si mismo-- y hasta ahora corria solo a mano o en
un workflow aparte. SPEC-018 US2 lo prohibia con un argumento de costo que nunca
se habia medido: 16,6 s contra los 17,2 s del pipeline entero.

El riesgo que US2 si nombraba bien era el acople con `coverage`, y se cierra por
propiedad declarada (`TEST_DIRS[...].medida`), no por omitir la clave del config.
"""

from __future__ import annotations

from pathlib import Path

import adapter
import pytest
from sdd_config import EXIT_OMITIDO, SddConfig

KIT_ROOT = Path(__file__).resolve().parents[2]


def _cfg(tmp_path: Path, dirs: dict, **extra) -> SddConfig:
    return SddConfig(repo_root=tmp_path, raw={"dirs": dirs, **extra})


@pytest.fixture
def corridas(monkeypatch):
    """Captura los comandos en vez de correrlos: interesa que y con que carpeta."""
    vistas: list[list[str]] = []
    monkeypatch.setattr(adapter, "_run", lambda cmd, cwd: vistas.append(cmd) or 0)
    return vistas


def test_corre_la_carpeta_declarada(tmp_path, corridas):
    """FR-US3-001: el paso ejecuta `dirs.tests_e2e`."""
    (tmp_path / "pruebas" / "punta-a-punta").mkdir(parents=True)

    codigo = adapter.step_e2e(
        tmp_path, _cfg(tmp_path, {"tests_e2e": "pruebas/punta-a-punta"})
    )

    assert codigo == 0
    assert corridas and corridas[0][-3:] == ["pytest", "pruebas/punta-a-punta", "-q"]


def test_sin_la_clave_declarada_se_omite(tmp_path, corridas, capsys):
    """FR-US3-001: no adivina carpetas, ni siquiera `tests/e2e`.

    Ejecutar una carpeta que el proyecto no declaro es adivinar **con efectos**,
    a diferencia de los pasos estaticos.
    """
    (tmp_path / "tests" / "e2e").mkdir(parents=True)

    codigo = adapter.step_e2e(tmp_path, _cfg(tmp_path, {"tests_unit": "tests/unit"}))

    assert codigo == EXIT_OMITIDO
    assert "tests_e2e" in capsys.readouterr().out
    assert corridas == []


def test_declarada_pero_sin_carpeta_todavia_se_omite(tmp_path, corridas, capsys):
    """Un derivado que declara la clave antes de escribir su primer escenario."""
    codigo = adapter.step_e2e(tmp_path, _cfg(tmp_path, {"tests_e2e": "tests/e2e"}))

    assert codigo == EXIT_OMITIDO
    assert "tests/e2e" in capsys.readouterr().out
    assert corridas == []


def test_no_toca_la_carpeta_unitaria_ni_la_de_integracion(tmp_path, corridas):
    """Los tres pasos son distintos: fundirlos impondria un ciclo unico."""
    for sub in ("unit", "integration", "e2e"):
        (tmp_path / "tests" / sub).mkdir(parents=True)
    cfg = _cfg(
        tmp_path,
        {
            "tests_unit": "tests/unit",
            "tests_integration": "tests/integration",
            "tests_e2e": "tests/e2e",
        },
    )

    adapter.step_e2e(tmp_path, cfg)

    assert corridas[0][-2] == "tests/e2e"


def test_la_cobertura_no_ejecuta_la_suite_e2e(tmp_path, corridas):
    """FR-US3-002: el acople que dejo `integration` corriendo dentro de `coverage`.

    Es el defecto de V-1 con otra carpeta: `step_coverage` le pasa a pytest todas
    las carpetas de test declaradas, asi que la e2e correria una vez por umbral
    --sin aportar una sola linea medida, porque maneja el kit por subproceso--.
    """
    (tmp_path / "src").mkdir()
    for sub in ("unit", "e2e"):
        (tmp_path / "tests" / sub).mkdir(parents=True)
    cfg = _cfg(
        tmp_path,
        {"tests_unit": "tests/unit", "tests_e2e": "tests/e2e", "source_roots": ["src"]},
        pipeline={"coverage": [{"paths": ["src"], "min": 50}]},
    )

    adapter.step_coverage(tmp_path, cfg)

    assert corridas, "el paso no llego a invocar pytest"
    invocacion = corridas[0]
    assert "tests/unit" in invocacion
    assert "tests/e2e" not in invocacion, (
        "`coverage` esta ejecutando la suite e2e: es el acople de V-1 con otra "
        "carpeta, y ademas la correria una vez por umbral"
    )


def test_los_pasos_estaticos_si_miran_la_suite_e2e(tmp_path, corridas):
    """La otra mitad de FR-US3-002: declararla tiene que servir para algo.

    Antes de K-4 el lint de `tests/e2e` era un paso a mano del workflow, porque
    la carpeta no estaba en `dirs`. Ahora sale del config, que es su SSOT.

    Lo que se afirma es el **alcance**, no la forma del argumento: desde
    SPEC-019 FR-US4-001 los pasos estaticos reciben la raiz que contiene a las
    carpetas declaradas, asi que la suite queda cubierta por `tests` en vez de
    nombrada una por una. Pedir el literal `tests/e2e` seria pedir justo el
    doble barrido que FR-US4-002 prohibe.
    """
    (tmp_path / "src").mkdir()
    for sub in ("unit", "e2e"):
        (tmp_path / "tests" / sub).mkdir(parents=True)
    cfg = _cfg(
        tmp_path,
        {"tests_unit": "tests/unit", "tests_e2e": "tests/e2e", "source_roots": ["src"]},
    )

    adapter.step_lint(tmp_path, cfg)

    blancos = [Path(a) for a in corridas[0] if not a.startswith("-")]
    assert any(
        b == Path("tests/e2e") or Path("tests/e2e").is_relative_to(b) for b in blancos
    ), f"la suite e2e quedo fuera del alcance del paso: {corridas[0]}"


def test_el_contrato_documenta_el_paso():
    """El SSOT del contrato es adapters/CONTRACT.md."""
    contrato = (KIT_ROOT / "adapters" / "CONTRACT.md").read_text(encoding="utf-8")

    assert "| `e2e` |" in contrato
    assert "dirs.tests_e2e" in contrato
