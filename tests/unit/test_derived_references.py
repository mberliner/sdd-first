"""Un derivado no cita archivos que no tiene (SPEC-013 FR-003/FR-004).

`check_constitution` ya verifica las referencias de las lineas Detalle/
Enforcement, pero nada cubria el resto de los documentos instalados. Asi se
coló que `docs/ARCHITECTURE.md` citara el generador de contratos del adaptador
python: con `--language none` no se vendoriza ningun adaptador y la ruta
quedaba colgada.

El test instala de verdad en los dos lenguajes soportados en vez de leer las
plantillas: lo que importa es lo que el dueno del proyecto encuentra en disco.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import sdd_init

# Rutas de archivo citadas en backticks. Solo con separador: un nombre pelado
# (`render.py`) es una mencion, no una ruta que el lector pueda seguir.
_RUTA = re.compile(r"`([\w./-]+/[\w./-]+\.(?:py|md|json|yaml|yml|sh|js))`")

# Placeholders documentales: nombran la forma de una ruta, no un archivo.
_PLACEHOLDERS = {"specs/SPEC-NNN-slug.md"}

# Andamiaje interno: se verifica aparte y tiene su propia estructura.
_EXCLUIDOS = ("tools/sdd", ".agents", ".claude", ".opencode")


def _docs_instalados(target: Path) -> list[Path]:
    return [
        md
        for md in sorted(target.rglob("*.md"))
        if not any(x in md.as_posix() for x in _EXCLUIDOS)
    ]


def _bootstrap(target: Path, language: str) -> None:
    """Instala y renderiza: el estado que el dueno ve tras seguir el README.

    Sin el render, SPEC-000 y el workflow de CI todavia no existen y el test
    los reportaria como referencias rotas.
    """
    assert sdd_init.main([str(target), f"--language={language}"]) == 0
    subprocess.run(  # nosec B603 - script del propio kit recien instalado
        [sys.executable, str(target / "tools" / "sdd" / "core" / "render.py")],
        cwd=target,
        check=True,
        capture_output=True,
    )


@pytest.mark.parametrize("language", ["python", "none"])
def test_ningun_doc_instalado_cita_una_ruta_inexistente(tmp_path, language):
    _bootstrap(tmp_path, language)

    colgadas: list[str] = []
    for md in _docs_instalados(tmp_path):
        for m in _RUTA.finditer(md.read_text(encoding="utf-8")):
            ruta = m.group(1)
            if ruta in _PLACEHOLDERS:
                continue
            if not (tmp_path / ruta).exists():
                colgadas.append(f"{md.relative_to(tmp_path).as_posix()} -> {ruta}")

    assert not colgadas, "rutas citadas que el derivado no tiene: " + "; ".join(
        colgadas
    )


def test_architecture_no_depende_del_adaptador_python(tmp_path):
    # FR-003: el doc de capas se instala con cualquier lenguaje, asi que no
    # puede citar un archivo que solo existe con `--language python`.
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    texto = (tmp_path / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "gen_import_linter.py" not in texto
    assert "layers" in texto  # sigue explicando de donde sale la matriz
