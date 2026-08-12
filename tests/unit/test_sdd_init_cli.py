"""Tests de la linea de comandos de sdd_init (SPEC-003 FR-012).

El instalador escribe ~40 archivos: un flag mal leido no es un detalle de
ergonomia, es escribir en el directorio equivocado. Estos tests cubren las tres
formas en que `main` aceptaba en silencio algo distinto de lo pedido (C-7 y C-3
de docs/IDEAS.md).
"""

from __future__ import annotations

import pytest
import sdd_init


def _instalado(target) -> bool:
    return (target / "tools" / "sdd" / "core" / "sdd_gate.py").exists()


# --- destino explicito (C-7) -------------------------------------------------


def test_target_con_igual_instala_ahi_y_no_en_el_cwd(tmp_path, monkeypatch):
    """FR-012: `--target=<dir>` era descartado y el destino caia al cwd."""
    destino = tmp_path / "destino"
    destino.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)

    assert sdd_init.main([f"--target={destino}", "--language=none"]) == 0

    assert _instalado(destino)
    assert not _instalado(cwd)
    assert list(cwd.iterdir()) == []


def test_target_con_espacio_instala_ahi(tmp_path, monkeypatch):
    """FR-012: la forma separada por espacio vale lo mismo que con `=`."""
    destino = tmp_path / "destino"
    destino.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)

    assert sdd_init.main(["--target", str(destino), "--language", "none"]) == 0

    assert _instalado(destino)
    assert list(cwd.iterdir()) == []


def test_target_y_posicional_en_conflicto_abortan(tmp_path):
    """FR-012: dos destinos distintos es ambiguo; se aborta en vez de elegir."""
    uno = tmp_path / "uno"
    uno.mkdir()
    otro = tmp_path / "otro"
    otro.mkdir()

    with pytest.raises(SystemExit) as exc:
        sdd_init.main([str(uno), f"--target={otro}", "--language=none"])

    assert exc.value.code != 0
    assert not _instalado(uno)
    assert not _instalado(otro)


def test_target_y_posicional_coincidentes_no_abortan(tmp_path):
    """FR-012: repetir el mismo destino no es un conflicto."""
    argv = [str(tmp_path), f"--target={tmp_path}", "--language=none"]
    assert sdd_init.main(argv) == 0
    assert _instalado(tmp_path)


# --- flags desconocidos (C-7) ------------------------------------------------


@pytest.mark.parametrize("flag", ["--dry-run", "--languaje=python", "--verbose"])
def test_flag_desconocido_aborta_sin_escribir_nada(tmp_path, flag):
    """FR-012: se descartaba en silencio; ahora sale con el uso y exit != 0."""
    with pytest.raises(SystemExit) as exc:
        sdd_init.main([str(tmp_path), flag])

    assert exc.value.code != 0
    assert list(tmp_path.iterdir()) == []


def test_el_error_de_uso_nombra_el_flag_y_la_forma_correcta(tmp_path, capsys):
    """FR-012: el mensaje tiene que servir para corregir la invocacion."""
    with pytest.raises(SystemExit):
        sdd_init.main([str(tmp_path), "--dry-run"])

    salida = capsys.readouterr()
    texto = salida.out + salida.err
    assert "--dry-run" in texto
    assert "--language" in texto and "--target" in texto


# --- lenguaje validado contra los adaptadores en disco (C-3) -----------------


def test_language_sin_adaptador_aborta(tmp_path):
    """FR-012: `--language=node` sembraba el config sin vendorizar adaptador."""
    with pytest.raises(SystemExit) as exc:
        sdd_init.main([str(tmp_path), "--language=node"])

    assert exc.value.code != 0
    assert list(tmp_path.iterdir()) == []


def test_language_con_espacio_no_cae_a_python_en_silencio(tmp_path):
    """FR-012: `--language none` (con espacio) instalaba python callado."""
    assert sdd_init.main([str(tmp_path), "--language", "none"]) == 0

    config = (tmp_path / ".sdd" / "config.yaml").read_text(encoding="utf-8")
    assert "language: none" in config
    assert not (tmp_path / "tools" / "sdd" / "adapters" / "python").exists()


def test_language_sin_valor_aborta(tmp_path):
    """FR-012: `--language` colgado al final tomaba python por default."""
    with pytest.raises(SystemExit) as exc:
        sdd_init.main([str(tmp_path), "--language"])

    assert exc.value.code != 0
    assert list(tmp_path.iterdir()) == []


def test_lenguajes_validos_salen_del_disco_no_de_una_lista(tmp_path):
    """FR-012: el catalogo es el contenido de adapters/, no una constante.

    Un segundo SSOT del catalogo de adaptadores se desincroniza el dia que
    aparezca `adapters/node/` (Principio IV).
    """
    validos = sdd_init.lenguajes_soportados()

    en_disco = {
        d.name for d in (sdd_init.KIT_ROOT / "adapters").iterdir() if d.is_dir()
    }
    assert validos == en_disco | {"none"}
