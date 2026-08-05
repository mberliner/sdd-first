"""Los mensajes de drift citan rutas del proyecto, no del kit (FR-US2-002).

`render.py` y `gen_skill_adapters.py` decian "corre: python core/render.py". En un
proyecto derivado esa ruta no existe: el andamiaje vive en `tools/sdd/core/`. La
pista sale de la ubicacion real del modulo, asi que es exacta por construccion en
los dos casos.
"""

from __future__ import annotations

from pathlib import Path

from sdd_config import VENDOR_PREFIX, script_hint

KIT_ROOT = Path(__file__).resolve().parents[2]


def test_en_el_kit_la_pista_es_la_ruta_del_kit():
    hint = script_hint(KIT_ROOT / "core" / "render.py", KIT_ROOT)
    assert hint == "core/render.py"


def test_en_un_derivado_la_pista_es_la_ruta_vendorizada(tmp_path):
    script = tmp_path / VENDOR_PREFIX / "core" / "render.py"
    script.parent.mkdir(parents=True)
    script.touch()
    assert script_hint(script, tmp_path) == f"{VENDOR_PREFIX}/core/render.py"


def test_script_fuera_del_repo_degrada_al_nombre(tmp_path):
    """Kit clonado aparte del proyecto: el nombre es lo unico afirmable."""
    otro = tmp_path / "kit-aparte"
    otro.mkdir()
    (otro / "render.py").touch()
    assert script_hint(otro / "render.py", tmp_path / "proyecto") == "render.py"


def test_el_mensaje_real_de_render_usa_la_pista(tmp_path, monkeypatch, capsys):
    """No solo el helper: el mensaje que ve el operador. Se fuerza drift contra
    un proyecto donde los artefactos generados todavia no existen; el kit corre
    desde fuera de ese proyecto, asi que la pista degrada al nombre del script.
    """
    import render

    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  name: destino\n  language: python\n", encoding="utf-8"
    )
    monkeypatch.setattr(render, "find_repo_root", lambda: tmp_path)
    assert render.main(["--check"]) == 1
    assert "corre: python render.py" in capsys.readouterr().out
