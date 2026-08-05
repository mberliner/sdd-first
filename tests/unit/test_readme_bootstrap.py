"""El README publica un bootstrap ejecutable de punta a punta (SPEC-011).

El `README.md` de la raiz es el unico punto de entrada del operador que clona el
kit para sembrar un proyecto derivado. Antes arrancaba a mitad de camino: sin
`git clone`, sin `pip install pyyaml` (bloqueante: `sdd_config` aborta si falta)
y con un cambio de directorio implicito entre los comandos del kit y los del
destino. Estos tests fijan los pasos que no pueden faltar y, sobre todo, evitan
que un rename en `core/` deje el bloque de comandos apuntando al vacio -- mismo
rol que `test_template_paths.py` cumple para las plantillas.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
README = KIT_ROOT / "README.md"

# Scripts del andamiaje citados en el README, con o sin el prefijo vendorizado
# (`tools/sdd/core/render.py` en el destino es `core/render.py` en el kit).
_SCRIPT = re.compile(r"(?:tools/sdd/)?((?:core|adapters)/[\w/]+\.py)")


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


def _scripts_citados(texto: str) -> set[str]:
    return {m.group(1) for m in _SCRIPT.finditer(texto)}


def test_todos_los_scripts_citados_existen(readme: str):
    # FR-007: el README no se regenera, asi que el unico anclaje contra el drift
    # es este test.
    citados = _scripts_citados(readme)
    assert citados, "el README dejo de citar scripts del andamiaje"
    faltantes = sorted(s for s in citados if not (KIT_ROOT / s).exists())
    assert not faltantes, f"el README cita scripts inexistentes: {faltantes}"


def test_documenta_como_obtener_el_kit(readme: str):
    # FR-001: sin esto la secuencia arranca en un cwd que el operador no tiene.
    assert "git clone" in readme
    assert "sdd-first.git" in readme


def test_documenta_la_dependencia_bloqueante(readme: str):
    # FR-002: sdd_config.py hace `import yaml` a nivel modulo y sale con
    # SystemExit; sin el comando, el operador choca en el primer paso.
    assert "pip install pyyaml" in readme


def test_el_cambio_de_directorio_al_destino_es_explicito(readme: str):
    # FR-003: los comandos `tools/sdd/...` solo existen en el proyecto destino.
    posicion_cd = readme.find("cd /ruta/a/mi-proyecto")
    # Solo comandos ejecutables: la prosa puede nombrar la ruta vendorizada
    # antes, justamente para explicar por que hace falta el cd.
    posicion_comando = readme.find("python tools/sdd/core/")
    assert posicion_cd != -1, "falta el cd al proyecto destino"
    assert posicion_comando != -1, "falta la ruta vendorizada"
    assert posicion_cd < posicion_comando, (
        "el cd al destino debe preceder al primer comando tools/sdd/..."
    )


def test_aclara_el_bootstrap_de_una_sola_vez(readme: str):
    # FR-004: `sdd-init` no se instala en el derivado (decidido en SPEC-007) y
    # el clon queda descartable tras la vendorizacion.
    assert "no** se" in readme and "sdd-init" in readme
    assert "descartable" in readme


def test_documenta_las_precondiciones_de_la_capa_git(readme: str):
    # FR-005: el paso `hooks` necesita repo git + pre-commit; sin eso el bloqueo
    # en el commit queda inactivo en silencio.
    assert "git init" in readme
    assert "pip install pre-commit" in readme


def test_avisa_que_el_gate_exige_la_primera_spec(readme: str):
    # FR-006: con `.sdd/current-spec` vacio el gate bloquea toda edicion.
    assert ".sdd/current-spec" in readme
    assert "sdd-spec" in readme


def test_enumera_los_valores_de_language(readme: str):
    # FR-008.
    assert "--language" in readme
    assert "`python` (default)" in readme
    assert "`none`" in readme


def test_nombra_las_carpetas_de_codigo_entre_lo_configurable(readme: str):
    """SPEC-003 FR-008 (no el FR-008 de SPEC-011, que es el de `--language`).

    El README enumeraba que editar del config y omitia `dirs`/`source_roots`, que
    es lo unico que hace que el gate y los pasos de codigo apunten al codigo del
    proyecto. Sin eso, el pipeline puede salir VERDE sin haber verificado nada.
    """
    assert "source_roots" in readme
    assert "dirs" in readme
