"""La salida de los entrypoints es UTF-8 en cualquier plataforma (SPEC-012 FR-005).

En Windows `sys.stdout` cae a `cp1252` cuando no es una consola UTF-8, asi que
todo texto acentuado del kit sale ilegible (`VERDE �`) o revienta. El fix es un
helper unico; lo que lo sostiene es el barrido de entrypoints de la ultima
prueba, que falla si alguno se olvida de invocarlo (C-2 de docs/IDEAS.md).
"""

from __future__ import annotations

import ast
import os
import subprocess  # nosec B404 - invoca entrypoints del propio kit
import sys
from pathlib import Path

import pytest
import sdd_config

KIT_ROOT = Path(__file__).resolve().parents[2]

# Modulos que se ejecutan como script: los unicos que escriben en una terminal.
ENTRYPOINTS = sorted(
    [p for p in (KIT_ROOT / "core").glob("*.py")]
    + [p for p in (KIT_ROOT / "adapters" / "python").glob("*.py")]
)


def _tiene_bloque_main(path: Path) -> bool:
    arbol = ast.parse(path.read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if not isinstance(nodo, ast.If):
            continue
        if "__main__" in ast.dump(nodo.test):
            return True
    return False


def _invoca_helper(path: Path) -> bool:
    return "forzar_salida_utf8" in path.read_text(encoding="utf-8")


class _StreamFalso:
    """Stream con `reconfigure`, como el `sys.stdout` real de un script."""

    def __init__(self) -> None:
        self.encoding_pedido: str | None = None

    def reconfigure(self, *, encoding: str) -> None:
        self.encoding_pedido = encoding


class _StreamSinReconfigure:
    """Stream sin `reconfigure`: lo que instala pytest al capturar la salida."""


def test_helper_fuerza_utf8_en_los_dos_streams(monkeypatch):
    """SPEC-012 FR-005: stdout y stderr, no solo stdout."""
    out, err = _StreamFalso(), _StreamFalso()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)

    sdd_config.forzar_salida_utf8()

    assert out.encoding_pedido == "utf-8"
    assert err.encoding_pedido == "utf-8"


def test_helper_tolera_un_stream_sin_reconfigure(monkeypatch):
    """SPEC-012 FR-005: bajo pytest los streams no exponen reconfigure.

    Si el helper se cayera ahi, todo entrypoint que lo invoque seria intesteable.
    """
    monkeypatch.setattr(sys, "stdout", _StreamSinReconfigure())
    monkeypatch.setattr(sys, "stderr", _StreamSinReconfigure())

    sdd_config.forzar_salida_utf8()  # no debe lanzar


def test_salida_real_es_utf8_con_la_codificacion_del_entorno_en_cp1252(tmp_path):
    """SPEC-012 FR-005 (SC-004): el caso reproducido, de punta a punta.

    `PYTHONIOENCODING=cp1252` reproduce en cualquier plataforma lo que Windows
    hace solo al redirigir la salida. Sin el helper, la 'i' con tilde de
    `sdd_spec.py` se emite como el byte 0xED (cp1252) y el texto no es UTF-8.
    """
    env = dict(os.environ, PYTHONIOENCODING="cp1252")
    proc = subprocess.run(  # nosec B603 - script del propio kit, sin shell
        [sys.executable, str(KIT_ROOT / "core" / "sdd_spec.py")],
        capture_output=True,
        env=env,
        cwd=str(tmp_path),
    )

    crudo = proc.stdout + proc.stderr
    assert crudo, "el entrypoint no imprimio nada: el caso dejo de ser observable"
    texto = crudo.decode("utf-8")  # falla si salio en cp1252
    assert "Título" in texto


@pytest.mark.parametrize(
    "path", [p for p in ENTRYPOINTS if _tiene_bloque_main(p)], ids=lambda p: p.name
)
def test_cada_entrypoint_invoca_el_helper(path):
    """SPEC-012 FR-005 (SC-005): la garantia no depende de acordarse.

    Era 2 de 15, y los 2 con el bloque de `reconfigure` copiado.
    """
    assert _invoca_helper(path), (
        f"{path.relative_to(KIT_ROOT)} se ejecuta como script y no llama a "
        "sdd_config.forzar_salida_utf8(): su salida acentuada sale ilegible "
        "donde la codificacion del sistema no es UTF-8"
    )


def test_importar_sdd_config_no_exige_pyyaml(tmp_path):
    """SPEC-012 FR-006: los hooks corren en un venv sin dependencias.

    `check_traceability.py` importa `sdd_config` desde FR-005 para usar el
    helper; si el modulo abortara al importarse sin PyYAML, el hook de
    pre-commit se caeria con "requiere PyYAML" en vez de verificar nada.
    """
    script = tmp_path / "sin_yaml.py"
    script.write_text(
        "import sys\n"
        "sys.modules['yaml'] = None\n"  # simula ModuleNotFoundError al importar
        f"sys.path.insert(0, {str(KIT_ROOT / 'core')!r})\n"
        "import importlib\n"
        "for m in list(sys.modules):\n"
        "    if m.startswith('sdd_config'):\n"
        "        del sys.modules[m]\n"
        "import sdd_config\n"
        "print(sdd_config.forzar_salida_utf8 is not None)\n",
        encoding="utf-8",
    )
    proc = subprocess.run(  # nosec B603 - script generado por el test
        [sys.executable, str(script)], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "requiere PyYAML" not in (proc.stdout + proc.stderr)


def test_load_sin_pyyaml_reporta_la_dependencia(monkeypatch):
    """SPEC-012 FR-006: el mensaje no se pierde, se mueve a quien lee el YAML."""
    monkeypatch.setattr(sdd_config, "yaml", None)
    sdd_config.load.cache_clear()

    with pytest.raises(SystemExit, match="PyYAML"):
        sdd_config.load(KIT_ROOT)

    sdd_config.load.cache_clear()


def test_el_bloque_de_reconfigure_no_quedo_duplicado():
    """SPEC-012 FR-005: un solo lugar que sepa como se fuerza la codificacion."""
    con_reconfigure = [
        p.relative_to(KIT_ROOT).as_posix()
        for p in ENTRYPOINTS
        if "reconfigure" in p.read_text(encoding="utf-8")
    ]
    assert con_reconfigure == ["core/sdd_config.py"]
