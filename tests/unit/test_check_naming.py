"""Tests del linter de nomenclatura del adaptador python (SPEC-002 FR-003).

Los tokens usados son ficticios ("acme", "gadget") para no introducir tokens
reales prohibidos en identificadores del propio kit.
"""

from pathlib import Path

import check_naming as cn


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
