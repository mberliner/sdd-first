"""El config sembrado apunta al codigo real del destino (SPEC-003 FR-007).

Antes de esta spec, `sdd-init` copiaba los `dirs` del proyecto de referencia
(`src/domain`, `src/dashboard`, `tests/unit`). En un proyecto con otro layout eso
dejaba al gate y a los pasos de codigo apuntando a carpetas inexistentes: el
pipeline salia VERDE sin haber verificado nada y el gate permitia editar el
codigo real. Estos tests fijan la deteccion y su fallback.
"""

from __future__ import annotations

import sdd_init
from conftest import crear_proyecto_brownfield
from sdd_config import load


def _instalar(destino, language="python"):
    sdd_init.main([str(destino), f"--language={language}"])
    return load(destino)


def test_detecta_codigo_en_app_y_tests_en_tests(tmp_path):
    crear_proyecto_brownfield(tmp_path, layout="app")
    cfg = _instalar(tmp_path)
    assert cfg.source_roots == ["app"]
    assert cfg.dirs["tests_unit"] == "tests"


def test_no_hereda_las_rutas_del_proyecto_de_referencia(tmp_path):
    """Solo en YAML activo: el ejemplo comentado de `pipeline.coverage` cita
    `src/domain` como ilustracion de la sintaxis (SPEC-009) y no configura nada.
    """
    crear_proyecto_brownfield(tmp_path, layout="app")
    _instalar(tmp_path)
    activas = [
        linea
        for linea in (tmp_path / ".sdd" / "config.yaml")
        .read_text(encoding="utf-8")
        .splitlines()
        if linea.strip() and not linea.strip().startswith("#")
    ]
    for heredada in ("src/domain", "src/application", "src/dashboard"):
        assert not any(heredada in linea for linea in activas)


def test_prefiere_src_cuando_existe(tmp_path):
    crear_proyecto_brownfield(tmp_path, layout="src")
    cfg = _instalar(tmp_path)
    assert cfg.source_roots == ["src"]


def test_ignora_carpeta_sin_archivos_del_lenguaje(tmp_path):
    """Una carpeta `lib/` de assets no es la raiz de codigo."""
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "logo.png").write_bytes(b"\x89PNG")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("x = 1\n", encoding="utf-8")
    cfg = _instalar(tmp_path)
    assert cfg.source_roots == ["app"]


def test_directorio_vacio_deja_dirs_sin_declarar(tmp_path):
    """Greenfield: nada que detectar, y el default clasico se conserva."""
    cfg = _instalar(tmp_path)
    config = (tmp_path / ".sdd" / "config.yaml").read_text(encoding="utf-8")
    assert "TODO" in config
    assert "source_roots: [app]" not in config
    # Sin `dirs` declarado, sdd_config cae al default historico.
    assert cfg.source_roots == ["src"]


def test_language_none_no_declara_source_roots(tmp_path):
    """Sin adaptador que valide codigo, declarar la carpeta solo haria que el
    gate bloquee ediciones que ningun paso del pipeline mira."""
    crear_proyecto_brownfield(tmp_path, layout="app")
    cfg = _instalar(tmp_path, language="none")
    assert cfg.source_roots == ["src"]


def test_informa_el_layout_detectado_en_la_salida(tmp_path, capsys):
    """El dueno tiene que saber que se hizo una adivinanza para poder corregirla."""
    crear_proyecto_brownfield(tmp_path, layout="app")
    sdd_init.main([str(tmp_path), "--language=python"])
    salida = capsys.readouterr().out
    assert "Layout detectado" in salida
    assert "app/" in salida


def test_avisa_cuando_no_detecto_layout(tmp_path, capsys):
    sdd_init.main([str(tmp_path), "--language=python"])
    salida = capsys.readouterr().out
    assert "No se detecto carpeta de codigo" in salida
    assert "source_roots" in salida
