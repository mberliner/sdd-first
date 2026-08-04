"""El mensaje de cierre del instalador es ejecutable (SPEC-011 FR-009..FR-011).

El operador termina la instalacion mirando esta salida, no el README. Antes
listaba comandos `tools/sdd/...` sin el `cd` al destino: copiados tal cual desde
el clon del kit, no resuelven. Estos tests fijan que la secuencia este completa
y que no incluya pasos que el destino ya cumple.
"""

from __future__ import annotations

import sdd_init


def test_incluye_el_cd_con_el_path_real_antes_de_los_comandos(tmp_path):
    # FR-009: el path tiene que ser el del destino, no un placeholder.
    salida = sdd_init._next_steps(tmp_path)
    posicion_cd = salida.find(f"cd {tmp_path}")
    posicion_comando = salida.find("python tools/sdd/core/")
    assert posicion_cd != -1, "falta el cd al destino con su path real"
    assert posicion_cd < posicion_comando, (
        "el cd debe preceder al primer comando tools/sdd/..."
    )


def test_incluye_los_cuatro_pasos_de_configuracion(tmp_path):
    salida = sdd_init._next_steps(tmp_path)
    for comando in ("render.py", "gen_skill_adapters.py", "pipeline.py"):
        assert f"python tools/sdd/core/{comando}" in salida
    assert ".sdd/config.yaml" in salida


def test_avisa_del_gate_y_de_la_primera_spec(tmp_path):
    # FR-009: sin esto el operador choca contra el gate sin saber por que.
    salida = sdd_init._next_steps(tmp_path)
    assert "sdd_spec.py" in salida
    assert ".sdd/current-spec" in salida


def test_aclara_que_el_clon_del_kit_es_descartable(tmp_path):
    # FR-011.
    salida = sdd_init._next_steps(tmp_path)
    assert "tools/sdd/" in salida
    assert "descartable" in salida


def test_omite_git_init_si_el_destino_ya_es_repo(tmp_path):
    # FR-010: sugerir un paso ya cumplido resta credibilidad al resto.
    assert "git init" in sdd_init._next_steps(tmp_path)
    (tmp_path / ".git").mkdir()
    assert "git init" not in sdd_init._next_steps(tmp_path)


def test_omite_el_cd_si_el_destino_es_el_cwd(tmp_path, monkeypatch):
    # FR-010.
    monkeypatch.chdir(tmp_path)
    salida = sdd_init._next_steps(tmp_path)
    assert f"cd {tmp_path}" not in salida
    # El resto de la secuencia sigue completo.
    assert "python tools/sdd/core/pipeline.py" in salida


def test_omite_la_instalacion_de_pre_commit_si_ya_esta_disponible(
    tmp_path, monkeypatch
):
    # FR-010: `pre_commit` es dependencia de desarrollo del kit, asi que en esta
    # suite esta importable; forzamos ambos casos para no depender del entorno.
    monkeypatch.setattr(sdd_init.importlib.util, "find_spec", lambda _n: object())
    assert "pip install pre-commit" not in sdd_init._next_steps(tmp_path)

    monkeypatch.setattr(sdd_init.importlib.util, "find_spec", lambda _n: None)
    assert "pip install pre-commit" in sdd_init._next_steps(tmp_path)
