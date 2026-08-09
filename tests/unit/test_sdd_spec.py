"""Tests de sdd_spec (SPEC-003 FR-003, SPEC-004 FR-007)."""

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


def test_declare_current_spec_preserva_comentarios(tmp_path):
    current = tmp_path / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER, encoding="utf-8")

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")

    text = current.read_text(encoding="utf-8")
    for line in CURRENT_SPEC_HEADER.splitlines():
        assert line in text
    assert "SPEC-005-demo" in text


def test_declare_current_spec_reemplaza_spec_previa_no_apila(tmp_path):
    current = tmp_path / "current-spec"
    current.write_text(CURRENT_SPEC_HEADER + "SPEC-004-vieja\n", encoding="utf-8")

    sdd_spec._declare_current_spec(current, "SPEC-005-demo")

    text = current.read_text(encoding="utf-8")
    assert "SPEC-004-vieja" not in text
    assert "SPEC-005-demo" in text


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
