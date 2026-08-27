"""Tests del linter de nomenclatura del adaptador python (SPEC-002 FR-003).

Los tokens usados son ficticios ("acme", "gadget") para no introducir tokens
reales prohibidos en identificadores del propio kit.
"""

from pathlib import Path

import check_naming as cn
import pytest


def _check(tmp_path: Path, source: str, filename: str = "modulo.py", **kwargs):
    path = tmp_path / filename
    path.write_text(source, encoding="utf-8")
    defaults = {
        "prohibited": ("acme",),
        "allowed": frozenset(),
        "relax_tokens": frozenset(),
        "relax_format": False,
    }
    defaults.update(kwargs)
    return cn._violations_in_file(path, **defaults)


def test_detecta_token_en_funcion_y_variable(tmp_path):
    """SPEC-001 FR-005: naming via AST + palabras excluidas del config."""
    violations = _check(tmp_path, "def cliente_acme():\n    acme_url = 1\n")
    names = [v[2] for v in violations]
    assert names == ["cliente_acme", "acme_url"]


def test_detecta_token_en_nombre_de_archivo(tmp_path):
    violations = _check(tmp_path, "x = 1\n", filename="acme_client.py")
    assert violations and violations[0][2] == "acme_client.py"


def test_respeta_allowed_identifiers(tmp_path):
    violations = _check(tmp_path, "acme_url = 1\n", allowed=frozenset({"acme_url"}))
    assert violations == []


def test_relax_solo_aplica_a_tokens_relajados(tmp_path):
    source = "def parse_acme():\n    pass\n\ndef parse_gadget():\n    pass\n"
    violations = _check(
        tmp_path,
        source,
        prohibited=("acme", "gadget"),
        relax_tokens=frozenset({"acme"}),
        relax_format=True,
    )
    names = [v[2] for v in violations]
    assert names == ["parse_gadget"]


def test_detecta_token_en_nombre_de_directorio(tmp_path):
    """SPEC-001 FR-005: el linter tambien mira nombres de directorio."""
    d = tmp_path / "acme_adapter"
    d.mkdir()
    violations = cn._violations_in_dir(
        d,
        prohibited=("acme",),
        allowed=frozenset(),
        relax_tokens=frozenset(),
        relax_format=False,
    )
    assert violations and violations[0][2] == "acme_adapter"
    assert violations[0][3] == "acme"


def test_directorio_respeta_allowed(tmp_path):
    d = tmp_path / "acme_adapter"
    d.mkdir()
    violations = cn._violations_in_dir(
        d,
        prohibited=("acme",),
        allowed=frozenset({"acme_adapter"}),
        relax_tokens=frozenset(),
        relax_format=False,
    )
    assert violations == []


def test_directorio_relaja_tokens_declarados(tmp_path):
    d = tmp_path / "acme_adapter"
    d.mkdir()
    violations = cn._violations_in_dir(
        d,
        prohibited=("acme",),
        allowed=frozenset(),
        relax_tokens=frozenset({"acme"}),
        relax_format=True,
    )
    assert violations == []


def test_archivo_con_sintaxis_invalida_no_rompe(tmp_path):
    violations = _check(tmp_path, "def acme(:\n")
    assert violations == []


def test_comparacion_es_case_insensitive(tmp_path):
    violations = _check(tmp_path, "ClienteACME = object\n")
    assert violations and violations[0][3] == "acme"


def test_is_test_root_reconoce_dirs_del_config(tmp_path):
    # SPEC-003 FR-002: 'tests/unit' (basename 'unit') debe contar como tests.
    test_dirs = [(tmp_path / "tests" / "unit").resolve()]
    assert cn._is_test_root(tmp_path / "tests" / "unit", test_dirs)
    assert cn._is_test_root(tmp_path / "tests" / "unit" / "sub", test_dirs)
    assert not cn._is_test_root(tmp_path / "src", test_dirs)


def test_is_test_root_fallback_por_basename(tmp_path):
    assert cn._is_test_root(tmp_path / "tests", [])
    assert not cn._is_test_root(tmp_path / "src", [])


# -- nodos del AST que solo el visitor recolecta ---------------------------------


def test_detecta_token_en_clase_anotacion_y_async(tmp_path):
    source = (
        "class ClienteAcme:\n"
        "    pass\n"
        "\n"
        "async def traer_acme():\n"
        "    pass\n"
        "\n"
        "acme_total: int = 0\n"
    )
    names = [v[2] for v in _check(tmp_path, source)]
    assert names == ["ClienteAcme", "traer_acme", "acme_total"]


# -- main(): el entrypoint que corre el paso `naming` ---------------------------
#
# K-3: el modulo estaba en 59% con todo el CLI sin ejecutar.


def _repo(tmp_path, prohibited=("acme",), extra=""):
    (tmp_path / "CONSTITUTION.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    lista = "\n".join(f"    - {p}" for p in prohibited)
    (tmp_path / ".sdd" / "config.yaml").write_text(
        f"project:\n  name: demo\n  language: python\n\nnaming:\n  prohibited:\n{lista}\n{extra}",
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    return tmp_path


def test_main_sin_argumentos_devuelve_2(capsys):
    assert cn.main(["check_naming.py"]) == 2
    assert "Uso:" in capsys.readouterr().err


def test_main_con_root_inexistente_devuelve_2(tmp_path, capsys):
    assert cn.main(["check_naming.py", str(tmp_path / "nope")]) == 2
    assert "No existe" in capsys.readouterr().err


def test_main_sin_palabras_excluidas_no_verifica_nada(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path, prohibited=())
    (repo / "src" / "m.py").write_text("acme = 1\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    assert cn.main(["check_naming.py", "src"]) == 0
    assert "sin palabras excluidas" in capsys.readouterr().out


def test_main_verde_sin_violaciones(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    (repo / "src" / "m.py").write_text("cliente = 1\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    assert cn.main(["check_naming.py", "src"]) == 0


def test_main_rojo_reporta_ubicacion_y_total(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    (repo / "src" / "m.py").write_text(
        "def traer_acme():\n    pass\n", encoding="utf-8"
    )
    monkeypatch.chdir(repo)

    assert cn.main(["check_naming.py", "src"]) == 1

    err = capsys.readouterr().err
    assert "traer_acme" in err
    assert "'acme'" in err
    assert "Total: 1 violacion(es)" in err


def test_main_rojo_por_nombre_de_directorio(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    (repo / "src" / "acme_adapter").mkdir()
    (repo / "src" / "acme_adapter" / "m.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    assert cn.main(["check_naming.py", "src"]) == 1

    err = capsys.readouterr().err
    assert "acme_adapter" in err
    assert "'acme'" in err


def test_main_relaja_los_tokens_declarados_dentro_de_tests(tmp_path, monkeypatch):
    """SPEC-003 FR-002: `tests/unit` cuenta como tests aunque el basename sea `unit`."""
    repo = _repo(
        tmp_path,
        extra="  relax_in_tests:\n    - acme\n\ndirs:\n  tests_unit: tests/unit\n",
    )
    (repo / "tests" / "unit").mkdir(parents=True)
    (repo / "tests" / "unit" / "test_m.py").write_text("acme = 1\n", encoding="utf-8")
    (repo / "src" / "m.py").write_text("acme = 1\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    assert cn.main(["check_naming.py", "tests/unit"]) == 0
    assert cn.main(["check_naming.py", "src"]) == 1


# -- FR-008: un archivo ilegible degrada, no revienta --------------------------


def _archivo_latin1(tmp_path: Path, nombre: str = "legado.py") -> Path:
    """Un `.py` real que no decodifica como UTF-8 (bytes latin-1 crudos)."""
    path = tmp_path / nombre
    path.write_bytes("x = 'café'\n".encode("latin-1"))
    return path


def test_un_archivo_ilegible_no_propaga_la_excepcion_cruda(tmp_path):
    """SPEC-001 FR-008: sin guarda, esto era un UnicodeDecodeError sin contexto.

    El error se tipa (`_ArchivoIlegible`) en vez de devolver `[]` en silencio:
    `main` necesita distinguirlo para nombrarlo, y "no se pudo leer" no es lo
    mismo que "no tiene violaciones".
    """
    path = _archivo_latin1(tmp_path)
    with pytest.raises(cn._ArchivoIlegible) as exc:
        cn._violations_in_file(
            path,
            prohibited=("acme",),
            allowed=frozenset(),
            relax_tokens=frozenset(),
            relax_format=False,
        )
    assert "legado.py" in str(exc.value)


def test_un_archivo_ilegible_se_nombra_y_no_cuenta_como_violacion(
    tmp_path, monkeypatch, capsys
):
    """No se puede afirmar que cumple, y llamarlo violacion seria igual de falso."""
    _archivo_latin1(tmp_path)
    (tmp_path / "limpio.py").write_text("def ok():\n    pass\n", encoding="utf-8")
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  name: probe\nnaming:\n  prohibited: [acme]\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    cn.load.cache_clear()

    codigo = cn.main(["check_naming.py", str(tmp_path)])
    salida = capsys.readouterr()

    assert codigo == 0, "un archivo ilegible no es una violacion de nomenclatura"
    assert "legado.py" in salida.out + salida.err, (
        "el archivo que no se pudo verificar tiene que nombrarse: "
        f"out={salida.out!r} err={salida.err!r}"
    )
