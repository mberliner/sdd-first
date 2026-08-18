"""Tests de sdd_spec (SPEC-003 FR-003, SPEC-004 FR-007).

El camino de adopcion (`--reuse`, SPEC-022 US1) vive en test_sdd_spec_reuse.py.
"""

import sdd_spec

CURRENT_SPEC_HEADER = (
    "# Spec(s) vigente(s): una por línea, formato SPEC-NNN-slug.\n"
    "# El gate spec-first (core/sdd_gate.py) exige que al menos una spec listada aquí\n"
    "# exista, esté registrada y haya sido editada DESPUÉS de este archivo.\n"
    "# Vacío = ninguna edición de código fuente permitida.\n"
)

REGISTRY_CON_ROADMAP = """# Registro de specs — demo

## Specs vigentes

| ID | Título | Estado | Iteración | Formato | Archivo |
|----|--------|--------|-----------|---------|---------|
| SPEC-000 | Nomenclatura | active | 0 | casero | [SPEC-000-naming.md](SPEC-000-naming.md) |

## Roadmap / política de datos

- (pendiente)
"""

ROW = "| SPEC-001 | Nueva | draft | - | hibrido | [SPEC-001-nueva.md](SPEC-001-nueva.md) |"


def test_inserta_dentro_de_la_tabla_no_al_final_del_archivo():
    result = sdd_spec._insert_registry_row(REGISTRY_CON_ROADMAP, ROW)
    lines = result.splitlines()
    fila = lines.index(ROW)
    roadmap = lines.index("## Roadmap / política de datos")
    assert fila < roadmap
    # la fila queda contigua a la tabla (línea anterior también es de tabla)
    assert lines[fila - 1].startswith("| SPEC-000")


def test_sin_tabla_cae_a_append():
    result = sdd_spec._insert_registry_row("# Registro vacío\n", ROW)
    assert result.rstrip().endswith(ROW)


def test_slugify_normaliza():
    assert sdd_spec._slugify("Mi Capacidad Nueva!") == "mi-capacidad-nueva"


def test_slugify_translitera_acentos(tmp_path):
    """SPEC-003 FR-013: los diacriticos se transliteran, no se descartan.

    Antes cada acento abria un hueco en el slug (`busqueda` -> `b-squeda`), asi
    que el archivo y el ID de la spec no eran los que el titulo pedia.
    """
    assert sdd_spec._slugify("Búsqueda semántica") == "busqueda-semantica"
    assert sdd_spec._slugify("Integración con ñandú") == "integracion-con-nandu"


def test_slugify_usa_la_transliteracion_del_triage():
    """SPEC-003 FR-013: una sola normalizacion de texto en el kit (Principio IV)."""
    import spec_index

    assert sdd_spec._slugify("Búsqueda") == spec_index.sin_acentos("Búsqueda").lower()


def test_declare_current_spec_preserva_comentarios(tmp_path):
    current = tmp_path / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER, encoding="utf-8")

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")

    text = current.read_text(encoding="utf-8")
    for line in CURRENT_SPEC_HEADER.splitlines():
        assert line in text
    assert "SPEC-005-demo" in text


def test_declare_current_spec_acumula_sin_perder_la_previa(tmp_path):
    """SPEC-004 FR-011: la declaracion es acumulativa dentro de la iteracion.

    Invierte el criterio original de FR-007 ("agrega o reemplaza"): reemplazar
    des-declaraba en silencio la spec anterior, y como una spec recien creada
    nace sin FR escritos, el gate pasaba a bloquear tambien las ediciones que
    esa anterior ya autorizaba (docs/IDEAS.md G-7).
    """
    current = tmp_path / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER + "SPEC-004-vieja\n", encoding="utf-8")

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")

    declaradas = sdd_spec._specs_declaradas(current)
    assert declaradas == ["SPEC-004-vieja", "SPEC-005-demo"]
    for line in CURRENT_SPEC_HEADER.splitlines():
        assert line in current.read_text(encoding="utf-8")


def test_declare_current_spec_no_duplica_una_ya_declarada(tmp_path):
    """FR-011: re-declarar no agrega una segunda linea ni reordena (SC-008)."""
    current = tmp_path / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER, encoding="utf-8")

    sdd_spec._declare_current_spec(current, "SPEC-004-vieja")
    sdd_spec._declare_current_spec(current, "SPEC-005-demo")
    sdd_spec._declare_current_spec(current, "SPEC-004-vieja")

    assert sdd_spec._specs_declaradas(current) == [
        "SPEC-004-vieja",
        "SPEC-005-demo",
    ]


def test_clear_current_spec_deja_el_archivo_igual_al_header(tmp_path):
    """FR-011: `--clear` retira las declaraciones y conserva los comentarios."""
    current = tmp_path / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER, encoding="utf-8")
    sdd_spec._declare_current_spec(current, "SPEC-004-vieja")
    sdd_spec._declare_current_spec(current, "SPEC-005-demo")

    sdd_spec._clear_current_spec(current)

    assert current.read_text(encoding="utf-8") == CURRENT_SPEC_HEADER
    assert sdd_spec._specs_declaradas(current) == []


def test_declare_current_spec_sin_archivo_previo_no_falla(tmp_path):
    current = tmp_path / "current-spec"

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")

    assert current.read_text(encoding="utf-8") == "SPEC-005-demo\n"


def test_ciclo_declarar_luego_reset_deja_solo_el_header(tmp_path, monkeypatch):
    """SPEC-004 SC-004: tras declarar->commit->reset, queda igual al header."""
    import sdd_reset

    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    current = tmp_path / ".sdd" / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER, encoding="utf-8")
    monkeypatch.setattr(sdd_reset, "find_repo_root", lambda: tmp_path)

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")
    assert sdd_reset.main() == 0

    assert current.read_text(encoding="utf-8") == CURRENT_SPEC_HEADER


def test_ciclo_con_dos_specs_declaradas_tambien_vuelve_al_header(tmp_path, monkeypatch):
    """SPEC-004 SC-008: el conjunto acumulado no degrada SC-004.

    El reset acota el alcance de FR-011 a la iteracion en curso: por eso la
    acumulacion no crece sin limite.
    """
    import sdd_reset

    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    current = tmp_path / ".sdd" / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER, encoding="utf-8")
    monkeypatch.setattr(sdd_reset, "find_repo_root", lambda: tmp_path)

    sdd_spec._declare_current_spec(current, "SPEC-004-una")
    sdd_spec._declare_current_spec(current, "SPEC-005-otra")
    assert sdd_reset.main() == 0

    assert current.read_text(encoding="utf-8") == CURRENT_SPEC_HEADER


# -- main(): el flujo completo de crear una spec --------------------------------
#
# K-3: el modulo estaba en 44% porque la suite cubria los helpers y nunca el
# entrypoint, que es lo que corre la skill `sdd-spec`.


def _repo(tmp_path, con_template=True, con_registro=True):
    """Proyecto minimo donde `find_repo_root` ancla y `main` puede escribir."""
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "current-spec").write_text(
        CURRENT_SPEC_HEADER, encoding="utf-8"
    )
    specs = tmp_path / "specs"
    specs.mkdir()
    if con_template:
        (specs / "SPEC-TEMPLATE.md").write_text(
            "# SPEC-NNN: <título agnóstico>\n\n## Functional Requirements\n",
            encoding="utf-8",
        )
    if con_registro:
        (specs / "SPECS_REGISTRY.md").write_text(REGISTRY_CON_ROADMAP, encoding="utf-8")
    return tmp_path


def test_main_crear_una_segunda_spec_no_desdeclara_la_primera(
    tmp_path, monkeypatch, capsys
):
    """SPEC-004 FR-011/SC-008 por el entrypoint, que es lo que corre la skill.

    Antes, crear la segunda spec dejaba declarada solo a esa; como nace sin FR
    escritos, el gate bloqueaba tambien lo que la primera ya autorizaba.
    """
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["primera"]) == 0
    assert sdd_spec.main(["segunda"]) == 0

    current = repo / ".sdd" / "current-spec"
    assert sdd_spec._specs_declaradas(current) == [
        "SPEC-001-primera",
        "SPEC-002-segunda",
    ]
    # El conjunto resultante se imprime: la acumulacion no es silenciosa.
    assert "SPEC-001-primera, SPEC-002-segunda" in capsys.readouterr().out


def test_main_clear_retira_las_declaraciones(tmp_path, monkeypatch, capsys):
    """FR-011: `--clear` es la via explicita para des-declarar sin commitear."""
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)
    assert sdd_spec.main(["primera"]) == 0

    assert sdd_spec.main(["--clear"]) == 0

    current = repo / ".sdd" / "current-spec"
    assert current.read_text(encoding="utf-8") == CURRENT_SPEC_HEADER
    assert "Sin specs declaradas" in capsys.readouterr().out


def test_main_clear_con_slug_reemplaza(tmp_path, monkeypatch):
    """FR-011: `--clear` + declaracion da el reemplazo explicito."""
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)
    assert sdd_spec.main(["primera"]) == 0

    assert sdd_spec.main(["segunda", "--clear"]) == 0

    assert sdd_spec._specs_declaradas(repo / ".sdd" / "current-spec") == [
        "SPEC-002-segunda"
    ]


def test_main_sin_argumentos_devuelve_2(capsys):
    assert sdd_spec.main([]) == 2
    assert "Uso:" in capsys.readouterr().err


def test_main_solo_con_flags_devuelve_2(capsys):
    """Los `--flag` no cuentan como slug: sin posicional no hay spec que crear."""
    assert sdd_spec.main(["--title=Algo"]) == 2


def test_main_crea_registra_y_declara(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["Mi Capacidad Nueva", "--title=Título legible"]) == 0

    spec = repo / "specs" / "SPEC-001-mi-capacidad-nueva.md"
    assert spec.exists()
    # El título del flag reemplaza el placeholder de la plantilla.
    assert "SPEC-001-mi-capacidad-nueva: Título legible" in spec.read_text(
        encoding="utf-8"
    )
    registro = (repo / "specs" / "SPECS_REGISTRY.md").read_text(encoding="utf-8")
    assert "| SPEC-001 | Título legible | draft |" in registro
    # La fila entra en la tabla, no debajo del roadmap (SPEC-003 FR-003).
    lineas = registro.splitlines()
    assert lineas.index("## Roadmap / política de datos") > next(
        i for i, line in enumerate(lineas) if "SPEC-001" in line
    )
    assert "SPEC-001-mi-capacidad-nueva" in (repo / ".sdd" / "current-spec").read_text(
        encoding="utf-8"
    )
    assert "ANTES de tocar código" in capsys.readouterr().out


def test_main_numera_correlativo_desde_las_specs_existentes(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    (repo / "specs" / "SPEC-007-vieja.md").write_text("# vieja\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["nueva"]) == 0

    assert (repo / "specs" / "SPEC-008-nueva.md").exists()


def test_main_sin_titulo_usa_el_argumento(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["mi-slug"]) == 0

    assert "| SPEC-001 | mi-slug | draft |" in (
        repo / "specs" / "SPECS_REGISTRY.md"
    ).read_text(encoding="utf-8")


def test_main_sin_plantilla_escribe_un_cuerpo_minimo(tmp_path, monkeypatch):
    repo = _repo(tmp_path, con_template=False)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["nueva"]) == 0

    texto = (repo / "specs" / "SPEC-001-nueva.md").read_text(encoding="utf-8")
    assert "SPEC-001-nueva" in texto
    assert "SPEC-FORMAT" in texto


def test_main_sin_registro_no_falla(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path, con_registro=False)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["nueva"]) == 0
    assert "Registrada" not in capsys.readouterr().out


def test_main_no_pisa_una_spec_existente(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    (repo / "specs" / "SPEC-001-nueva.md").write_text("# mia\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    # El correlativo daria 002, asi que se fuerza la colision creando la 001 y
    # pidiendo el mismo slug: el numero siguiente ya existe solo si hay hueco.
    assert sdd_spec.main(["nueva"]) == 0
    assert (repo / "specs" / "SPEC-002-nueva.md").exists()
    assert (repo / "specs" / "SPEC-001-nueva.md").read_text(
        encoding="utf-8"
    ) == "# mia\n"


# -- SPEC-022 US2: el triage de solape, antes de crear ---------------------------


def _repo_con_vigente(
    tmp_path, titulo="Gate spec-first", entities="`core/gate.py` — x"
):
    repo = _repo(tmp_path)
    archivo = "SPEC-010-vigente.md"
    (repo / "specs" / archivo).write_text(
        f"# {archivo}\n\n## Key Entities\n\n- {entities}\n", encoding="utf-8"
    )
    registro = (repo / "specs" / "SPECS_REGISTRY.md").read_text(encoding="utf-8")
    fila = f"| SPEC-010 | {titulo} | draft | - | hibrido | [{archivo}]({archivo}) |"
    (repo / "specs" / "SPECS_REGISTRY.md").write_text(
        sdd_spec._insert_registry_row(registro, fila), encoding="utf-8"
    )
    return repo


def test_triage_por_titulo_aborta_sin_escribir_nada(tmp_path, monkeypatch, capsys):
    """FR-US2-008 / SC-004: el arbol queda idéntico a antes de la ejecucion."""
    repo = _repo_con_vigente(tmp_path, titulo="Gate decision spec-first")
    monkeypatch.chdir(repo)
    antes = sorted(p.name for p in (repo / "specs").iterdir())
    registro_antes = (repo / "specs" / "SPECS_REGISTRY.md").read_text(encoding="utf-8")

    assert sdd_spec.main(["gate decision nuevo"]) != 0

    err = capsys.readouterr().err
    assert "SPEC-010-vigente" in err and "--reuse" in err
    assert sorted(p.name for p in (repo / "specs").iterdir()) == antes
    assert (repo / "specs" / "SPECS_REGISTRY.md").read_text(
        encoding="utf-8"
    ) == registro_antes


def test_triage_por_touches_lista_la_spec_del_archivo(tmp_path, monkeypatch, capsys):
    """FR-US2-004: la salida indica qué archivo señaló a la candidata."""
    repo = _repo_con_vigente(tmp_path, titulo="Sin nada en comun")
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["otra capacidad", "--touches", "core/gate.py"]) != 0

    err = capsys.readouterr().err
    assert "SPEC-010-vigente" in err
    assert "core/gate.py" in err


def test_new_con_rationale_crea_igual(tmp_path, monkeypatch, capsys):
    """FR-US2-008: la bandera resolutoria deja pasar y la decision queda escrita."""
    repo = _repo_con_vigente(tmp_path, titulo="Gate decision spec-first")
    monkeypatch.chdir(repo)

    assert (
        sdd_spec.main(
            ["gate decision nuevo", "--new", "--rationale=es otra capa del gate"]
        )
        == 0
    )

    assert (repo / "specs" / "SPEC-011-gate-decision-nuevo.md").exists()
    assert "SPEC-010-vigente" in capsys.readouterr().out


def test_new_sin_rationale_devuelve_2(tmp_path, monkeypatch, capsys):
    """FR-US2-008: sin el texto, `--new` seria un 'dale' que no deja rastro."""
    repo = _repo_con_vigente(tmp_path)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["lo que sea", "--new"]) == 2

    assert "--rationale" in capsys.readouterr().err


def test_rationale_sin_new_devuelve_2(tmp_path, monkeypatch):
    repo = _repo_con_vigente(tmp_path)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["lo que sea", "--rationale=porque si"]) == 2


def test_sin_solape_crea_sin_pedir_nada(tmp_path, monkeypatch):
    """El triage no estorba cuando no hay candidatas: es red, no peaje."""
    repo = _repo_con_vigente(tmp_path, titulo="Cobertura minima por capa")
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["exportar reportes a disco"]) == 0
    assert (repo / "specs" / "SPEC-011-exportar-reportes-a-disco.md").exists()


# -- SPEC-023 US1: crear una spec enlazada a la que extiende o reemplaza ---------

SECCION = (
    "## Relación con specs existentes\n"
    "\n"
    "- **Extiende:** — | **Supersede:** — | **Depende de:** —\n"
    "- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —\n"
    "- **Por qué no cabe en una spec existente:** —\n"
)


def _agregar_spec(repo, numero, titulo="Capacidad vieja", estado="active", cuerpo=None):
    """Registra una spec vigente con la seccion de relaciones ya presente."""
    archivo = f"SPEC-{numero:03d}-vieja-{numero}.md"
    (repo / "specs" / archivo).write_text(
        cuerpo
        if cuerpo is not None
        else f"# SPEC-{numero:03d}\n\n{SECCION}\n## Functional Requirements\n",
        encoding="utf-8",
    )
    registro = (repo / "specs" / "SPECS_REGISTRY.md").read_text(encoding="utf-8")
    fila = (
        f"| SPEC-{numero:03d} | {titulo} | {estado} | - | hibrido "
        f"| [{archivo}]({archivo}) |"
    )
    (repo / "specs" / "SPECS_REGISTRY.md").write_text(
        sdd_spec._insert_registry_row(registro, fila), encoding="utf-8"
    )
    return archivo


def _estado_del_arbol(repo):
    return (
        sorted(p.name for p in (repo / "specs").iterdir()),
        (repo / "specs" / "SPECS_REGISTRY.md").read_text(encoding="utf-8"),
        (repo / ".sdd" / "current-spec").read_text(encoding="utf-8"),
    )


def test_extends_escribe_la_relacion_en_los_dos_documentos(tmp_path, monkeypatch):
    """FR-US1-001: el enlace no depende de que alguien lo anote del otro lado."""
    repo = _repo(tmp_path)
    archivo = _agregar_spec(repo, 10)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["capacidad ampliada", "--extends", "SPEC-010"]) == 0

    nueva = (repo / "specs" / "SPEC-011-capacidad-ampliada.md").read_text(
        encoding="utf-8"
    )
    assert "**Extiende:** [SPEC-010]" in nueva
    vieja = (repo / "specs" / archivo).read_text(encoding="utf-8")
    assert "**Extendida por:** [SPEC-011](SPEC-011-capacidad-ampliada.md)" in vieja


def test_supersedes_no_toca_el_estado_de_la_spec_reemplazada(tmp_path, monkeypatch):
    """FR-US1-003: la nueva nace draft; la vieja se degrada al cerrar, no ahora."""
    repo = _repo(tmp_path)
    _agregar_spec(repo, 10)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["capacidad nueva", "--supersedes", "SPEC-010"]) == 0

    registro = (repo / "specs" / "SPECS_REGISTRY.md").read_text(encoding="utf-8")
    assert "| SPEC-010 | Capacidad vieja | active |" in registro
    assert "| SPEC-011 | capacidad nueva | draft |" in registro


def test_supersedes_aborta_si_una_active_se_apoya_en_la_referenciada(
    tmp_path, monkeypatch, capsys
):
    """FR-US1-004: reemplazarla dejaria a esa otra apoyada en una no vigente."""
    repo = _repo(tmp_path)
    _agregar_spec(repo, 10)
    _agregar_spec(
        repo,
        12,
        cuerpo="# SPEC-012\n\n"
        + SECCION.replace("**Depende de:** —", "**Depende de:** [SPEC-010](x.md)"),
    )
    monkeypatch.chdir(repo)
    antes = _estado_del_arbol(repo)

    assert sdd_spec.main(["capacidad nueva", "--supersedes", "SPEC-010"]) != 0

    assert "SPEC-012" in capsys.readouterr().err
    assert _estado_del_arbol(repo) == antes


def test_referencia_sin_la_seccion_aborta_sin_crear_nada(tmp_path, monkeypatch, capsys):
    """FR-US1-004: sin sección no hay dónde escribir el recíproco."""
    repo = _repo(tmp_path)
    _agregar_spec(repo, 10, cuerpo="# SPEC-010\n\n## Functional Requirements\n")
    monkeypatch.chdir(repo)
    antes = _estado_del_arbol(repo)

    assert sdd_spec.main(["capacidad nueva", "--extends", "SPEC-010"]) != 0

    assert "Relacion con specs existentes" in capsys.readouterr().err
    assert _estado_del_arbol(repo) == antes


def test_extender_y_reemplazar_la_misma_spec_es_contradictorio(
    tmp_path, monkeypatch, capsys
):
    """FR-US1-001."""
    repo = _repo(tmp_path)
    _agregar_spec(repo, 10)
    monkeypatch.chdir(repo)
    antes = _estado_del_arbol(repo)

    assert (
        sdd_spec.main(
            ["capacidad nueva", "--extends", "SPEC-010", "--supersedes", "SPEC-010"]
        )
        != 0
    )

    assert "contradictorio" in capsys.readouterr().err
    assert _estado_del_arbol(repo) == antes


def test_varias_referencias_se_escriben_todas_en_su_campo(tmp_path, monkeypatch):
    """FR-US1-001: las banderas son repetibles y combinables entre si."""
    repo = _repo(tmp_path)
    for numero in (10, 11, 12):
        _agregar_spec(repo, numero)
    monkeypatch.chdir(repo)

    assert (
        sdd_spec.main(
            [
                "capacidad nueva",
                "--extends",
                "SPEC-010",
                "--extends",
                "SPEC-011",
                "--supersedes",
                "SPEC-012",
            ]
        )
        == 0
    )

    nueva = (repo / "specs" / "SPEC-013-capacidad-nueva.md").read_text(encoding="utf-8")
    assert "**Extiende:** [SPEC-010]" in nueva and "[SPEC-011]" in nueva
    assert "**Supersede:** [SPEC-012]" in nueva
    for numero, campo in (
        (10, "Extendida por"),
        (11, "Extendida por"),
        (12, "Superseded por"),
    ):
        vieja = (repo / "specs" / f"SPEC-{numero:03d}-vieja-{numero}.md").read_text(
            encoding="utf-8"
        )
        assert f"**{campo}:** [SPEC-013]" in vieja


def test_una_referencia_invalida_aborta_el_conjunto_entero(
    tmp_path, monkeypatch, capsys
):
    """FR-US1-004: la validacion corre sobre todas antes de escribir un byte."""
    repo = _repo(tmp_path)
    archivo = _agregar_spec(repo, 10)
    monkeypatch.chdir(repo)
    antes = _estado_del_arbol(repo)

    assert (
        sdd_spec.main(
            ["capacidad nueva", "--extends", "SPEC-010", "--extends", "SPEC-099"]
        )
        != 0
    )

    assert "SPEC-099" in capsys.readouterr().err
    assert _estado_del_arbol(repo) == antes
    # Ni siquiera el reciproco de la referencia valida quedo escrito.
    assert "SPEC-011" not in (repo / "specs" / archivo).read_text(encoding="utf-8")


def test_el_relleno_va_dentro_de_la_seccion_de_la_plantilla(tmp_path, monkeypatch):
    """FR-US1-006: no se construye una seccion propia si la plantilla la trae."""
    repo = _repo(tmp_path)
    (repo / "specs" / "SPEC-TEMPLATE.md").write_text(
        f"# SPEC-NNN: <título agnóstico>\n\n{SECCION}\n## Functional Requirements\n",
        encoding="utf-8",
    )
    _agregar_spec(repo, 10)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["capacidad nueva", "--extends", "SPEC-010"]) == 0

    nueva = (repo / "specs" / "SPEC-011-capacidad-nueva.md").read_text(encoding="utf-8")
    assert nueva.count("## Relación con specs existentes") == 1


def test_sin_plantilla_el_cuerpo_minimo_trae_la_seccion_vacia(tmp_path, monkeypatch):
    """FR-US1-006: el comportamiento preexistente tambien la incluye."""
    repo = _repo(tmp_path, con_template=False)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["nueva"]) == 0

    texto = (repo / "specs" / "SPEC-001-nueva.md").read_text(encoding="utf-8")
    assert "## Relación con specs existentes" in texto
    assert "**Extiende:** —" in texto


def test_rationale_aterriza_en_el_campo_de_la_seccion(tmp_path, monkeypatch):
    """FR-US1-002: el motivo se escribe donde se lo va a buscar."""
    repo = _repo(tmp_path)
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["nueva", "--new", "--rationale=es otro corte vertical"]) == 0

    texto = (repo / "specs" / "SPEC-001-nueva.md").read_text(encoding="utf-8")
    assert "**Por qué no cabe en una spec existente:** es otro corte vertical" in texto
