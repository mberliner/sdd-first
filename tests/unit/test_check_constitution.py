"""Tests del Constitution Check (SPEC-020 FR-003/FR-004/FR-006).

El modulo estaba en 0% de cobertura pese a correr en el paso `constitution` de
todo proyecto instalado (deuda K-3 de docs/IDEAS.md). Se cubre aca, en la misma
iteracion que le saca el mapa de tools hardcodeado.
"""

import check_constitution as cc

CONSTITUTION_OK = """# Constitución del proyecto

**Versión:** 0.1.0 | Ratificada: 2026-01-01 | Última enmienda: 2026-01-02

## Principios

### I. Nomenclatura agnostica

Ningun identificador nombra un proveedor.

- **Enforcement:** `check_naming.py`
- **Detalle:** `specs/SPEC-000-naming.md`

## Governance

- Lo de siempre.
"""

CONFIG_OK = """project:
  name: demo
  language: python

principles:
  - id: I
    title: Nomenclatura agnostica
    enforcement: check_naming.py
    step: naming
    detail: specs/SPEC-000-naming.md

pipeline:
  steps:
    - naming
"""


def _proyecto(tmp_path, constitution=CONSTITUTION_OK, config=CONFIG_OK):
    """Deja en tmp_path un proyecto minimo: config, constitucion y el SSOT citado."""
    (tmp_path / ".sdd").mkdir(exist_ok=True)
    (tmp_path / ".sdd" / "config.yaml").write_text(config, encoding="utf-8")
    (tmp_path / "specs").mkdir(exist_ok=True)
    (tmp_path / "specs" / "SPEC-000-naming.md").write_text(
        "# naming\n", encoding="utf-8"
    )
    destino = tmp_path / "CONSTITUTION.md"
    destino.write_text(constitution, encoding="utf-8")
    return destino


# -- parseo del documento ------------------------------------------------------


def test_parse_extrae_version_principios_y_referencias():
    version, principles = cc._parse(CONSTITUTION_OK)
    assert version is not None and "0.1.0" in version
    assert [p.title for p in principles] == ["I. Nomenclatura agnostica"]
    assert principles[0].enforcement == ["check_naming.py"]
    assert principles[0].detalle == ["specs/SPEC-000-naming.md"]


def test_parse_ignora_lo_que_esta_fuera_de_principios():
    """Un `###` bajo Governance no es un principio."""
    texto = CONSTITUTION_OK + "\n### No soy un principio\n\n- **Enforcement:** `x.py`\n"
    _, principles = cc._parse(texto)
    assert len(principles) == 1


# -- linea de version ----------------------------------------------------------


def test_version_ausente_es_error():
    errors: list[str] = []
    cc._check_version(None, errors)
    assert any("Falta la linea de version" in e for e in errors)


def test_version_sin_semver_es_error():
    errors: list[str] = []
    cc._check_version("**Versión:** uno | Ratificada: 2026-01-01 | 2026-01-02", errors)
    assert any("semver" in e for e in errors)


def test_version_sin_las_dos_fechas_es_error():
    errors: list[str] = []
    cc._check_version("**Versión:** 0.1.0 | Ratificada: 2026-01-01", errors)
    assert any("Ratificada" in e for e in errors)


# -- referencias y cableado ----------------------------------------------------


def test_principio_sin_enforcement_ni_detalle_es_error(tmp_path):
    principio = cc._Principle("I. Pelado")
    errors: list[str] = []
    cc._check_references([principio], tmp_path, set(), {}, errors)
    joined = "\n".join(errors)
    assert "sin linea Detalle" in joined
    assert "sin linea Enforcement" in joined


def test_referencia_a_ruta_inexistente_es_error(tmp_path):
    principio = cc._Principle("I. Demo")
    principio.enforcement = ["check_naming.py"]
    principio.detalle = ["docs/NO-EXISTE.md"]
    errors: list[str] = []
    cc._check_references([principio], tmp_path, set(), {}, errors)
    assert any("referencia inexistente 'docs/NO-EXISTE.md'" in e for e in errors)


def test_token_sin_barra_no_se_valida_como_ruta(tmp_path):
    """`check_naming.py` es una tool, no un path: no se exige que exista."""
    principio = cc._Principle("I. Demo")
    principio.enforcement = ["check_naming.py"]
    principio.detalle = ["algo"]
    errors: list[str] = []
    cc._check_references([principio], tmp_path, set(), {}, errors)
    assert errors == []


def test_paso_declarado_y_no_cableado_es_error(tmp_path):
    principio = cc._Principle("I. Demo")
    principio.enforcement = ["check_naming.py"]
    principio.detalle = ["algo"]
    errors: list[str] = []
    cc._check_references(
        [principio], tmp_path, {"traceability"}, {"check_naming.py": "naming"}, errors
    )
    joined = "\n".join(errors)
    assert "no esta activo" in joined
    assert "'naming'" in joined
    assert "I. Demo" in joined


def test_paso_declarado_y_cableado_pasa(tmp_path):
    principio = cc._Principle("I. Demo")
    principio.enforcement = ["check_naming.py"]
    principio.detalle = ["algo"]
    errors: list[str] = []
    cc._check_references(
        [principio], tmp_path, {"naming"}, {"check_naming.py": "naming"}, errors
    )
    assert errors == []


def test_enforcement_sin_step_declarado_no_verifica_cableado(tmp_path):
    """FR-004: sdd_gate.py se cablea via hooks; no se le exige paso de pipeline."""
    principio = cc._Principle("III. Gate")
    principio.enforcement = ["sdd_gate.py"]
    principio.detalle = ["algo"]
    errors: list[str] = []
    cc._check_references([principio], tmp_path, set(), {}, errors)
    assert errors == []


def test_el_mapa_resuelve_por_basename(tmp_path):
    """En la constitucion el enforcement se escribe con ruta; el mapa usa la tool."""
    principio = cc._Principle("I. Demo")
    principio.enforcement = ["adapters/python/check_naming.py"]
    principio.detalle = ["algo"]
    (tmp_path / "adapters" / "python").mkdir(parents=True)
    (tmp_path / "adapters" / "python" / "check_naming.py").write_text(
        "", encoding="utf-8"
    )
    errors: list[str] = []
    cc._check_references(
        [principio], tmp_path, set(), {"check_naming.py": "naming"}, errors
    )
    assert any("falta el paso 'naming'" in e for e in errors)


# -- main() --------------------------------------------------------------------


def test_main_sin_argumento_devuelve_2(capsys):
    assert cc.main(["check_constitution.py"]) == 2


def test_main_con_archivo_inexistente_devuelve_2(tmp_path, capsys):
    assert cc.main(["check_constitution.py", str(tmp_path / "nope.md")]) == 2


def test_main_verde_sobre_proyecto_coherente(tmp_path, capsys):
    destino = _proyecto(tmp_path)
    assert cc.main(["check_constitution.py", str(destino)]) == 0
    salida = capsys.readouterr().out
    assert "1 principio(s) activo(s)" in salida


def test_main_rojo_cuando_el_paso_del_principio_no_esta_cableado(tmp_path, capsys):
    """El caso que E-4 no cubria: el config manda, no un mapa en el codigo."""
    config = CONFIG_OK.replace("    - naming\n", "    - traceability\n")
    destino = _proyecto(tmp_path, config=config)
    assert cc.main(["check_constitution.py", str(destino)]) == 1
    assert "falta el paso 'naming'" in capsys.readouterr().err


def test_main_verifica_el_cableado_de_un_enforcement_propio(tmp_path, capsys):
    """FR-003: una tool que el kit no conoce obtiene la misma verificacion."""
    config = CONFIG_OK.replace(
        "    enforcement: check_naming.py\n    step: naming\n",
        "    enforcement: mi_check.py\n    step: mi-paso\n",
    )
    constitution = CONSTITUTION_OK.replace("`check_naming.py`", "`mi_check.py`")
    destino = _proyecto(tmp_path, constitution=constitution, config=config)
    assert cc.main(["check_constitution.py", str(destino)]) == 1
    assert "falta el paso 'mi-paso'" in capsys.readouterr().err


def test_main_rojo_sin_principios(tmp_path, capsys):
    constitution = "# Constitución\n\n**Versión:** 0.1.0 | 2026-01-01 | 2026-01-02\n"
    destino = _proyecto(tmp_path, constitution=constitution)
    assert cc.main(["check_constitution.py", str(destino)]) == 1
    assert "No se encontraron principios" in capsys.readouterr().err
