"""El config sembrado habla del proyecto destino (SPEC-014 FR-US2-004/FR-US2-005).

`examples/config/config.yaml` es el catalogo de referencia del kit y se sigue
copiando como base, pero su cabecera manda "copialo a .sdd/config.yaml" — una
instruccion absurda en el archivo que ya *es* ese destino — y nombra al proyecto
de referencia. La rama de disparo del CI tenia el mismo problema al reves: se
hardcodeaba `main` sin mirar el destino.
"""

from __future__ import annotations

import subprocess

import sdd_init
from sdd_config import load


def _config(destino) -> str:
    return (destino / ".sdd" / "config.yaml").read_text(encoding="utf-8")


def test_la_cabecera_nombra_al_proyecto_y_no_al_de_referencia(tmp_path):
    destino = tmp_path / "mi-app"
    destino.mkdir()
    sdd_init.main([str(destino), "--language=python"])
    texto = _config(destino)
    assert "SSOT de parametrizacion de mi-app" in texto
    assert "evaluador-flujo-intent" not in texto
    assert "Copialo a" not in texto


def test_el_catalogo_conserva_su_cabecera():
    """Lo que cambia es el sembrado, no el ejemplo: sigue siendo el catalogo."""
    from pathlib import Path

    ejemplo = (
        Path(__file__).resolve().parents[2] / "examples" / "config" / "config.yaml"
    ).read_text(encoding="utf-8")
    assert "Copialo a" in ejemplo


def test_siembra_la_rama_real_del_destino(tmp_path):
    subprocess.run(["git", "init", "-b", "develop", str(tmp_path)], check=True)
    sdd_init.main([str(tmp_path), "--language=python"])
    assert load(tmp_path).default_branch == "develop"


def test_sin_repo_git_no_declara_rama_y_asume_main(tmp_path):
    """El catalogo trae la clave comentada como documentacion, asi que se mira
    solo el YAML activo: sin git no se declara nada y el default es `main`."""
    sdd_init.main([str(tmp_path), "--language=python"])
    activas = [
        linea
        for linea in _config(tmp_path).splitlines()
        if linea.strip() and not linea.strip().startswith("#")
    ]
    assert not any("default_branch" in linea for linea in activas)
    assert load(tmp_path).default_branch == "main"
