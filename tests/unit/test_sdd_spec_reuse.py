"""Adoptar una spec existente en vez de crear otra (SPEC-022 US1).

El camino de creacion —el que ya existia— se prueba en test_sdd_spec.py.
"""

import sdd_spec
from test_sdd_spec import CURRENT_SPEC_HEADER


def _repo_con_specs(tmp_path, *filas):
    """Repo minimo con un registro a medida. `filas`: (num, titulo, estado, cuerpo)."""
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "current-spec").write_text(
        CURRENT_SPEC_HEADER, encoding="utf-8"
    )
    specs = tmp_path / "specs"
    specs.mkdir()
    tabla = [
        "# Registro — demo",
        "",
        "| ID | Título | Estado | Iteración | Formato | Archivo |",
        "|----|--------|--------|-----------|---------|---------|",
    ]
    for num, titulo, estado, cuerpo in filas:
        slug = titulo.lower().replace(" ", "-")
        archivo = f"SPEC-{num}-{slug}.md"
        tabla.append(
            f"| SPEC-{num} | {titulo} | {estado} | - | hibrido "
            f"| [{archivo}]({archivo}) |"
        )
        (specs / archivo).write_text(cuerpo, encoding="utf-8")
    (specs / "SPECS_REGISTRY.md").write_text("\n".join(tabla) + "\n", encoding="utf-8")
    return tmp_path


def _cuerpo(fr="FR-001", texto="MUST: el kit hace algo verificable.", coverage=""):
    return (
        "# Spec demo\n\n## Functional Requirements\n\n"
        f"- **{fr}** {texto}\n\n"
        "## Coverage mapping\n\n"
        "| Requisito | Cubierto por |\n|-----------|--------------|\n" + coverage
    )


def _declaradas(repo):
    texto = (repo / ".sdd" / "current-spec").read_text(encoding="utf-8")
    return [ln for ln in texto.splitlines() if ln and not ln.startswith("#")]


def test_reuse_declara_sin_crear_archivo_ni_fila(tmp_path, monkeypatch, capsys):
    """FR-US1-001: adoptar no crea spec ni fila; solo declara la existente."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo()))
    monkeypatch.chdir(repo)
    antes = sorted(p.name for p in (repo / "specs").iterdir())
    registro_antes = (repo / "specs" / "SPECS_REGISTRY.md").read_text(encoding="utf-8")

    assert sdd_spec.main(["--reuse", "SPEC-021-vieja", "--fr", "FR-001"]) == 0

    assert sorted(p.name for p in (repo / "specs").iterdir()) == antes
    assert (repo / "specs" / "SPECS_REGISTRY.md").read_text(
        encoding="utf-8"
    ) == registro_antes
    assert _declaradas(repo) == ["SPEC-021-vieja"]
    assert "no se creo spec nueva" in capsys.readouterr().out


def test_reuse_por_numero_declara_el_id_completo(tmp_path, monkeypatch):
    """FR-US1-002: el gate compara contra el nombre de archivo del registro."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo()))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-001"]) == 0

    assert _declaradas(repo) == ["SPEC-021-vieja"]


def test_reuse_por_numero_ambiguo_aborta_nombrando_candidatas(
    tmp_path, monkeypatch, capsys
):
    """FR-US1-002: sin resolucion univoca no se adivina."""
    repo = _repo_con_specs(
        tmp_path,
        ("021", "Vieja", "draft", _cuerpo()),
        ("021", "Otra", "draft", _cuerpo()),
    )
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-001"]) != 0

    err = capsys.readouterr().err
    assert "SPEC-021-vieja" in err and "SPEC-021-otra" in err
    assert _declaradas(repo) == []


def test_reuse_sin_el_fr_escrito_aborta_y_no_declara(tmp_path, monkeypatch, capsys):
    """FR-US1-003: adoptar no puede abrir el gate contra los FR viejos."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo()))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-009"]) != 0

    err = capsys.readouterr().err
    assert "FR-009" in err and "**FR-009** MUST:" in err
    assert _declaradas(repo) == []


def test_reuse_con_fr_placeholder_sin_texto_propio_aborta(tmp_path, monkeypatch):
    """FR-US1-003: mismo criterio de contenido que el gate (SPEC-017 FR-US3-001)."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo(texto="MUST:")))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-001"]) != 0
    assert _declaradas(repo) == []


def test_reuse_compara_el_fr_por_igualdad_exacta_no_por_substring(
    tmp_path, monkeypatch
):
    """FR-US1-007: FR-007 no satisface a un requisito declarado FR-US1-007."""
    repo = _repo_con_specs(
        tmp_path, ("021", "Vieja", "draft", _cuerpo(fr="FR-US1-007"))
    )
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-007"]) != 0
    assert _declaradas(repo) == []
    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-US1-007"]) == 0
    assert _declaradas(repo) == ["SPEC-021-vieja"]


def test_reuse_sobre_spec_no_vigente_aborta(tmp_path, monkeypatch, capsys):
    """FR-US1-001: superseded/archived no son adoptables."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "superseded", _cuerpo()))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-001"]) != 0

    assert "superseded" in capsys.readouterr().err
    assert _declaradas(repo) == []


def test_reuse_sobre_spec_no_registrada_aborta(tmp_path, monkeypatch, capsys):
    """FR-US1-002: el SSOT de las vigentes es el registro, no el glob de specs/."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo()))
    (repo / "specs" / "SPEC-099-suelta.md").write_text(_cuerpo(), encoding="utf-8")
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-099", "--fr", "FR-001"]) != 0

    assert "SPECS_REGISTRY" in capsys.readouterr().err
    assert _declaradas(repo) == []


def test_reuse_sobre_active_exige_fila_de_coverage(tmp_path, monkeypatch, capsys):
    """FR-US1-004: sin fila, check_traceability queda rojo y bloquea hasta el test."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "active", _cuerpo()))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-001"]) != 0

    assert "Coverage mapping" in capsys.readouterr().err
    assert _declaradas(repo) == []


def test_reuse_sobre_draft_no_exige_fila_de_coverage(tmp_path, monkeypatch):
    """FR-US1-004: sobre draft el validador no la pide; cobrarla encarece adoptar."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo()))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-001"]) == 0
    assert _declaradas(repo) == ["SPEC-021-vieja"]


def test_reuse_sobre_active_con_fila_y_test_rojo_declara(tmp_path, monkeypatch):
    """FR-US1-006: se exige que el test exista, no que pase."""
    cuerpo = _cuerpo(coverage="| FR-001 | tests/unit/test_algo.py |\n")
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "active", cuerpo))
    (repo / "tests" / "unit").mkdir(parents=True)
    (repo / "tests" / "unit" / "test_algo.py").write_text(
        "def test_rojo():\n    assert False\n", encoding="utf-8"
    )
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-001"]) == 0
    assert _declaradas(repo) == ["SPEC-021-vieja"]


def test_reuse_sobre_active_con_test_inexistente_aborta(tmp_path, monkeypatch, capsys):
    """FR-US1-004: el test referenciado tiene que existir (fuera de source_roots)."""
    cuerpo = _cuerpo(coverage="| FR-001 | tests/unit/test_algo.py |\n")
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "active", cuerpo))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-001"]) != 0

    assert "test_algo.py" in capsys.readouterr().err
    assert _declaradas(repo) == []


def test_reuse_tolera_el_test_ausente_si_cae_en_source_roots(
    tmp_path, monkeypatch, capsys
):
    """FR-US1-004: en ese layout el gate impediria crearlo antes de declarar."""
    cuerpo = _cuerpo(coverage="| FR-001 | src/tests/test_algo.py |\n")
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "active", cuerpo))
    (repo / ".sdd" / "config.yaml").write_text(
        "dirs:\n  source_roots: [src]\n", encoding="utf-8"
    )
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "FR-001"]) == 0

    assert "todavia no existe" in capsys.readouterr().out
    assert _declaradas(repo) == ["SPEC-021-vieja"]


def test_reuse_sin_fr_devuelve_2(tmp_path, monkeypatch, capsys):
    """FR-US1-003: `--reuse` exige `--fr`."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo()))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021"]) == 2

    assert "--fr" in capsys.readouterr().err
    assert _declaradas(repo) == []


def test_fr_sin_reuse_devuelve_2(tmp_path, monkeypatch):
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo()))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["nueva", "--fr", "FR-001"]) == 2


def test_reuse_con_slug_posicional_devuelve_2(tmp_path, monkeypatch):
    """Adoptar y crear son caminos excluyentes: el slug delata la confusion."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo()))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["nueva", "--reuse", "SPEC-021", "--fr", "FR-001"]) == 2


def test_fr_con_forma_invalida_devuelve_2(tmp_path, monkeypatch, capsys):
    """FR-US1-007: se acepta cualquier FR-[A-Za-z0-9-]+, pero tiene que serlo."""
    repo = _repo_con_specs(tmp_path, ("021", "Vieja", "draft", _cuerpo()))
    monkeypatch.chdir(repo)

    assert sdd_spec.main(["--reuse", "SPEC-021", "--fr", "001"]) == 2

    assert "FR-" in capsys.readouterr().err
    assert _declaradas(repo) == []
