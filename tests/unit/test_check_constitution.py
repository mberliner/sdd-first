"""Tests del Constitution Check (SPEC-020 FR-003/FR-004/FR-006, FR-US2-002/003/005).

El modulo estaba en 0% de cobertura pese a correr en el paso `constitution` de
todo proyecto instalado (deuda K-3 de docs/IDEAS.md). Se cubre aca, en la misma
iteracion que le saca el mapa de tools hardcodeado.
"""

import check_constitution as cc
from sdd_config import EXIT_RESERVAS, PIPELINE_STEPS_RUN_ENV

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
    """Deja en tmp_path un proyecto minimo: config, constitucion y lo que cita.

    "Lo que cita" son las **dos** referencias del principio, no solo el Detalle:
    desde SPEC-001 FR-010 el enforcement escrito como basename tambien se
    verifica contra los archivos del repo, asi que un fixture sin esos archivos
    dejo de representar un proyecto valido.
    """
    (tmp_path / ".sdd").mkdir(exist_ok=True)
    (tmp_path / ".sdd" / "config.yaml").write_text(config, encoding="utf-8")
    (tmp_path / "specs").mkdir(exist_ok=True)
    (tmp_path / "specs" / "SPEC-000-naming.md").write_text(
        "# naming\n", encoding="utf-8"
    )
    herramientas = tmp_path / "adapters" / "python"
    herramientas.mkdir(parents=True, exist_ok=True)
    for tool in ("check_naming.py", "mi_check.py", "sdd_gate.py"):
        (herramientas / tool).write_text("", encoding="utf-8")
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


def test_un_token_con_extension_si_se_valida_aunque_no_lleve_barra(tmp_path):
    """SPEC-001 FR-010: revierte la regla anterior, que miraba solo la barra.

    Estaba escrito que `check_naming.py` "es una tool, no un path" y por eso no
    se le exigia existir. La preocupacion era legitima --no exigirle existencia
    a algo que no es un archivo-- pero la barra dejaba fuera justo a los
    enforcements que SI son archivos: los del kit se escriben todos como
    basename, asi que la verificacion no corria para ninguno.
    """
    principio = cc._Principle("I. Demo")
    principio.enforcement = ["check_naming.py"]
    principio.detalle = ["algo"]
    errors: list[str] = []
    cc._check_references([principio], tmp_path, set(), {}, errors)
    assert any("referencia inexistente 'check_naming.py'" in e for e in errors)


def test_un_token_sin_extension_sigue_sin_validarse(tmp_path):
    """La extension separa un archivo de una tool (`pytest-cov`, `ruff`)."""
    principio = cc._Principle("V. Cobertura")
    principio.enforcement = ["pytest-cov"]
    principio.detalle = ["algo"]
    errors: list[str] = []
    cc._check_references([principio], tmp_path, set(), {}, errors)
    assert errors == []


def test_paso_declarado_y_no_cableado_es_error(tmp_path):
    principio = cc._Principle("I. Demo")
    principio.enforcement = ["check_naming.py"]
    principio.detalle = ["algo"]
    (tmp_path / "check_naming.py").write_text("", encoding="utf-8")
    errors: list[str] = []
    cc._check_references(
        [principio], tmp_path, {"traceability"}, {"check_naming.py": "naming"}, errors
    )
    joined = "\n".join(errors)
    assert "no esta activo" in joined
    # FR-003 exige los tres datos: sin el enforcement, el lector no sabe cual de
    # los tokens del principio es el que quedo sin paso.
    assert "'naming'" in joined
    assert "I. Demo" in joined
    assert "check_naming.py" in joined


def test_paso_declarado_y_cableado_pasa(tmp_path):
    principio = cc._Principle("I. Demo")
    principio.enforcement = ["check_naming.py"]
    principio.detalle = ["algo"]
    (tmp_path / "check_naming.py").write_text("", encoding="utf-8")
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
    (tmp_path / "sdd_gate.py").write_text("", encoding="utf-8")
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


# -- ejecucion del enforcement, no solo su declaracion (SPEC-020 US2) ----------
#
# FR-US2-002/003/005. US1 verifica que el paso este declarado en pipeline.steps;
# esto, que ademas haya corrido. El canal lo publica core/pipeline.py: sin la
# variable de entorno el check no evalua ejecucion y se comporta como antes.


def test_main_con_el_paso_ejecutado_sale_verde(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(PIPELINE_STEPS_RUN_ENV, "naming")
    destino = _proyecto(tmp_path)
    assert cc.main(["check_constitution.py", str(destino)]) == 0
    assert "sin enforcement ejecutado" not in capsys.readouterr().out


def test_main_reserva_cuando_el_paso_se_omitio(tmp_path, monkeypatch, capsys):
    """FR-US2-002: declarado y cableado, pero no verifico nada en la corrida."""
    config = CONFIG_OK.replace("    - naming\n", "    - naming\n    - tests\n")
    monkeypatch.setenv(PIPELINE_STEPS_RUN_ENV, "tests")
    destino = _proyecto(tmp_path, config=config)
    assert cc.main(["check_constitution.py", str(destino)]) == EXIT_RESERVAS
    salida = capsys.readouterr().out
    assert "Nomenclatura agnostica" in salida
    assert "check_naming.py" in salida
    assert "el paso 'naming' se omitio" in salida


def test_main_reserva_cuando_constitution_corre_demasiado_temprano(
    tmp_path, monkeypatch, capsys
):
    """FR-US2-002: nada ejecutado todavia -- el mensaje lo dice, no lo calla."""
    monkeypatch.setenv(PIPELINE_STEPS_RUN_ENV, "")
    destino = _proyecto(tmp_path)
    assert cc.main(["check_constitution.py", str(destino)]) == EXIT_RESERVAS
    salida = capsys.readouterr().out
    assert "Nomenclatura agnostica" in salida
    assert "check_naming.py" in salida
    assert "todavia no se ejecuto en esta corrida" in salida


def test_main_sin_la_variable_no_evalua_ejecucion(tmp_path, monkeypatch, capsys):
    """FR-US2-005: invocado suelto, el comportamiento es el previo a US2."""
    monkeypatch.delenv(PIPELINE_STEPS_RUN_ENV, raising=False)
    destino = _proyecto(tmp_path)
    assert cc.main(["check_constitution.py", str(destino)]) == 0


def test_un_principio_sin_step_no_genera_reserva(tmp_path, monkeypatch, capsys):
    """FR-004 sigue mandando: sin `step` no hay paso que esperar."""
    config = CONFIG_OK.replace("    step: naming\n", "")
    monkeypatch.setenv(PIPELINE_STEPS_RUN_ENV, "")
    destino = _proyecto(tmp_path, config=config)
    assert cc.main(["check_constitution.py", str(destino)]) == 0


def test_un_error_de_integridad_prevalece_sobre_la_reserva(
    tmp_path, monkeypatch, capsys
):
    """FR-US2-003: primero se arregla lo que esta mal escrito."""
    config = CONFIG_OK.replace("    - naming\n", "    - traceability\n")
    monkeypatch.setenv(PIPELINE_STEPS_RUN_ENV, "")
    destino = _proyecto(tmp_path, config=config)
    assert cc.main(["check_constitution.py", str(destino)]) == 1


# -- FR-010: los enforcements escritos como basename tambien se verifican ------

CONSTITUCION_CON_BASENAMES = """**Versión:** 1.0.0 | Ratificada: 2026-01-01 | Última enmienda: 2026-01-02

## Principios

### I. Test
- **Detalle:** `{detalle}`
- **Enforcement:** `{enforcement}`
"""


def _repo_con_constitucion(tmp_path, *, enforcement: str, detalle: str):
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  name: probe\npipeline:\n  steps: [naming]\n",
        encoding="utf-8",
    )
    constitucion = tmp_path / "CONSTITUTION.md"
    constitucion.write_text(
        CONSTITUCION_CON_BASENAMES.format(enforcement=enforcement, detalle=detalle),
        encoding="utf-8",
    )
    return constitucion


def test_un_enforcement_basename_inexistente_es_un_error(tmp_path, capsys):
    """SPEC-001 FR-010: renombrar un check tiene que romper el gate que lo cita.

    `_is_path` exigia `/` o `.` inicial, asi que `check_naming.py` --y todos los
    enforcements del kit, que se escriben como basename-- no se verificaban:
    la constitucion podia citar un archivo borrado y el paso salia verde.
    """
    constitucion = _repo_con_constitucion(
        tmp_path, enforcement="check_QUE_NO_EXISTE.py", detalle="NADA_TAMPOCO.md"
    )
    codigo = cc.main(["check_constitution.py", str(constitucion)])
    salida = capsys.readouterr()
    assert codigo == 1, salida.out + salida.err
    assert "check_QUE_NO_EXISTE.py" in salida.err
    assert "NADA_TAMPOCO.md" in salida.err


def test_un_enforcement_basename_existente_no_es_un_error(tmp_path, capsys):
    """Control: el basename se resuelve contra los archivos del repositorio."""
    (tmp_path / "herramientas").mkdir()
    (tmp_path / "herramientas" / "check_real.py").write_text("", encoding="utf-8")
    (tmp_path / "GUIA.md").write_text("", encoding="utf-8")
    constitucion = _repo_con_constitucion(
        tmp_path, enforcement="check_real.py", detalle="GUIA.md"
    )
    cc.main(["check_constitution.py", str(constitucion)])
    salida = capsys.readouterr()
    assert "inexistente" not in salida.err, salida.err


def test_un_token_sin_extension_no_se_verifica(tmp_path, capsys):
    """`pytest-cov` es un paquete, no un archivo: exigirle existencia seria falso."""
    constitucion = _repo_con_constitucion(
        tmp_path, enforcement="pytest-cov", detalle="GUIA.md"
    )
    (tmp_path / "GUIA.md").write_text("", encoding="utf-8")
    cc.main(["check_constitution.py", str(constitucion)])
    salida = capsys.readouterr()
    assert "pytest-cov" not in salida.err, salida.err
