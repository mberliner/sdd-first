"""Lo generado para una tool externa lo lee esa tool (SPEC-003 FR-010).

El generador de `.importlinter` estuvo emitiendo `[[importlinter:contract]]`
—sintaxis TOML de array-of-tables— dentro de un archivo que import-linter lee
como INI, asi que todo derivado con capas nacia con un `.importlinter` que
`lint-imports` no podia parsear (`section '' already exists`) y su pipeline
salia ROJO en el paso `layers`.

Lo que faltaba no era generar bien: era **leer lo generado con el parser real**.
El unico chequeo que existia era `--check`, que compara el archivo con lo que el
propio generador produce y por eso coincide sea valido o no. De ahi que estos
tests parseen: con el lector de import-linter si esta instalado, y siempre con
`configparser`, que es lo que ese lector usa por dentro.
"""

from __future__ import annotations

import configparser
import os
import shutil
import subprocess  # nosec B404 - corre la tool real sobre lo generado
import sys
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT_ROOT / "adapters" / "python"))
import gen_import_linter  # noqa: E402

CONFIG = """
project:
  name: demo
  language: python
dirs:
  source_roots: [src]
  domain: src/domain
  application: src/application
  infrastructure: src/infrastructure
layers:
  domain: []
  application: [domain]
  infrastructure: [domain, application]
"""


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text(CONFIG, encoding="utf-8")
    return tmp_path


@pytest.fixture
def generado(proyecto: Path) -> str:
    return gen_import_linter.render(proyecto)


def _parseado(texto: str) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read_string(texto)  # el fallo original moria aca
    return parser


def test_module_of_no_declara_parametro_sin_usar() -> None:
    # SPEC-003 FR-014: `repo_root` estaba en la firma sin usarse (docs/IDEAS.md
    # C-6); ruff --select ARG lo marcaria si volviera.
    import inspect

    assert list(inspect.signature(gen_import_linter._module_of).parameters) == [
        "layer_path"
    ]
    assert gen_import_linter._module_of("src/domain") == "src.domain"


def test_lo_generado_es_ini_parseable(generado: str) -> None:
    secciones = _parseado(generado).sections()
    assert "importlinter" in secciones, (
        "sin la seccion raiz, import-linter ignora el archivo entero"
    )


def test_hay_un_contrato_por_capa_con_prohibidos(generado: str) -> None:
    """`infrastructure` tiene permitido todo lo demas: no genera contrato."""
    parser = _parseado(generado)
    contratos = [s for s in parser.sections() if s.startswith("importlinter:")]
    assert contratos == [
        "importlinter:contract:domain",
        "importlinter:contract:application",
    ]


def test_cada_contrato_trae_lo_que_import_linter_le_exige(generado: str) -> None:
    parser = _parseado(generado)
    seccion = parser["importlinter:contract:application"]
    assert seccion["type"] == "forbidden"
    assert seccion["name"]
    assert seccion["source_modules"].split() == ["src.application"]
    assert seccion["forbidden_modules"].split() == ["src.infrastructure"]


def test_import_linter_construye_sus_contratos_desde_el_archivo(generado: str) -> None:
    """La prueba de fuego: el lector real, no una imitacion nuestra.

    Se omite si import-linter no esta instalado —el paso `layers` tambien se
    omite en ese caso (FR-004)— pero entonces los tests de arriba siguen
    cubriendo el formato con el mismo `configparser` que usa el lector.
    """
    lector = pytest.importorskip(
        "importlinter.adapters.user_options",
        reason="import-linter no instalado; el paso layers tampoco correria",
    )
    parser = _parseado(generado)
    opciones = lector.IniFileUserOptionReader()._build_from_config(parser)

    assert opciones.session_options["root_package"] == "src"
    assert [c["id"] for c in opciones.contracts_options] == [
        "domain",
        "application",
    ]
    assert all(c["type"] == "forbidden" for c in opciones.contracts_options)


def test_el_archivo_escrito_es_el_que_se_verifica(
    proyecto: Path, generado: str
) -> None:
    """`--check` sin este test solo compara el generador consigo mismo."""
    (proyecto / ".importlinter").write_text(generado, encoding="utf-8")
    assert _parseado((proyecto / ".importlinter").read_text(encoding="utf-8"))


def test_lint_imports_corre_de_punta_a_punta_sobre_lo_generado(
    proyecto: Path, generado: str
) -> None:
    """El paso `layers` completo, sobre un paquete de verdad.

    Los escenarios e2e no llegan aca: una instalacion fresca no tiene paquete
    raiz, asi que el paso se omite (FR-011). Este es el unico lugar donde el
    archivo generado se somete al ejecutable real.
    """
    if shutil.which("lint-imports") is None:
        pytest.skip("lint-imports no instalado; el paso layers tampoco correria")

    for capa in ("domain", "application", "infrastructure"):
        paquete = proyecto / "src" / capa
        paquete.mkdir(parents=True)
        (paquete / "__init__.py").write_text("", encoding="utf-8")
    (proyecto / "src" / "__init__.py").write_text("", encoding="utf-8")
    # Respeta las capas: infrastructure puede importar domain, no al reves.
    (proyecto / "src" / "infrastructure" / "repo.py").write_text(
        "from src.domain import modelo\n", encoding="utf-8"
    )
    (proyecto / "src" / "domain" / "modelo.py").write_text("", encoding="utf-8")
    (proyecto / ".importlinter").write_text(generado, encoding="utf-8")

    res = subprocess.run(  # nosec B603 B607 - comando fijo, cwd controlado
        ["lint-imports"],
        cwd=proyecto,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(proyecto)},
    )
    assert res.returncode == 0, (
        f"lint-imports rechazo lo generado:\n{res.stdout}{res.stderr}"
    )
    assert "Contracts: 2 kept, 0 broken" in res.stdout, res.stdout
