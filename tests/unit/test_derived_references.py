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


def test_ningun_archivo_instalado_queda_con_placeholders(tmp_path):
    """SPEC-014 FR-US2-001. `.sdd/current-spec` se instalaba con `{{sdd.core}}`
    crudo porque la sustitucion dependia de la extension y ese archivo no tiene.
    Es el primer archivo que se abre para entender el gate, y el test de rutas
    colgadas de arriba tampoco lo veia (no es `.md`).
    """
    assert sdd_init.main([str(tmp_path), "--language=python"]) == 0
    crudos = [
        p.relative_to(tmp_path).as_posix()
        for p in sorted(tmp_path.rglob("*"))
        if p.is_file()
        and not any(x in p.as_posix() for x in ("tools/sdd", "__pycache__"))
        and "{{" in p.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not crudos, "placeholders sin resolver en: " + "; ".join(crudos)


def test_el_readme_del_derivado_apunta_al_catalogo_de_skills(tmp_path):
    """SPEC-016 FR-008.

    El README es la puerta de entrada del proyecto y no decia que el asistente
    tuviera skills instaladas. La lista no se repite aca: su SSOT es
    `docs/SDD-OPERACION.md`.
    """
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    texto = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "docs/SDD-OPERACION.md" in texto
    assert "skills" in texto.lower()


def test_skills_multitool_aclara_que_los_adaptadores_ya_estan(tmp_path):
    # FR-009: el comando queda para agregar o editar una skill, no para arrancar.
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    texto = (tmp_path / "docs" / "SKILLS-MULTITOOL.md").read_text(encoding="utf-8")
    assert "sdd-init" in texto
    assert "gen_skill_adapters.py" in texto


def test_architecture_no_depende_del_adaptador_python(tmp_path):
    # FR-003: el doc de capas se instala con cualquier lenguaje, asi que no
    # puede citar un archivo que solo existe con `--language python`.
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    texto = (tmp_path / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "gen_import_linter.py" not in texto
    assert "layers" in texto  # sigue explicando de donde sale la matriz
