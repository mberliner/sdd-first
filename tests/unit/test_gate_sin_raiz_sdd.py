"""El gate no juzga contra una raiz inventada (SPEC-014 FR-US1-003).

Hallado durante la campana de usabilidad: `find_repo_root` devolvia el propio
`cwd` cuando no encontraba marcadores, con lo que `_is_source_path` no reconocia
nada como codigo fuente y la edicion se permitia en silencio.

La primera version de este arreglo denegaba toda edicion sin raiz resoluble, y
bloqueo en vivo la edicion de archivos de otras carpetas: el criterio no es el
`cwd` sino de que proyecto es el ARCHIVO. Estos tests fijan las dos mitades: la
raiz se busca tambien desde la ruta del archivo, y fuera de todo proyecto SDD no
hay protocolo que aplicar.
"""

from __future__ import annotations

import json

import sdd_gate
from sdd_config import find_repo_root, find_sdd_root


def _payload(cwd, file_path="app/servicio.py"):
    return {"tool_input": {"file_path": file_path}, "cwd": str(cwd)}


def test_find_sdd_root_devuelve_none_sin_marcadores(tmp_path):
    assert find_sdd_root(tmp_path) is None


def test_find_repo_root_sigue_siendo_tolerante(tmp_path):
    """El resto del andamiaje (pipeline, render, doctor) corre dentro del
    proyecto y su peor caso es reportar artefactos faltantes, no permitir."""
    assert find_repo_root(tmp_path) == tmp_path.resolve()


def _proyecto_sdd_sin_spec(tmp_path):
    """Proyecto SDD minimo con `app/` como codigo y ninguna spec declarada."""
    (tmp_path / ".sdd").mkdir(parents=True)
    (tmp_path / ".sdd" / "config.yaml").write_text(
        "project:\n  name: destino\ndirs:\n  source_roots: [app]\n",
        encoding="utf-8",
    )
    (tmp_path / ".sdd" / "current-spec").write_text("# vacio\n", encoding="utf-8")
    (tmp_path / "app").mkdir()
    return tmp_path


def test_bloquea_por_la_ruta_del_archivo_aunque_el_cwd_no_resuelva(
    tmp_path, monkeypatch, capsys
):
    """El caso que el fail-open dejaba pasar: el `cwd` es inutil pero el archivo
    pertenece a un proyecto SDD, y ese proyecto lo gobierna."""
    proyecto = _proyecto_sdd_sin_spec(tmp_path / "proyecto")
    payload = {
        "cwd": str(tmp_path / "otra-carpeta"),
        "tool_input": {"file_path": str(proyecto / "app" / "servicio.py")},
    }
    monkeypatch.setattr("sys.stdin", _Stdin(json.dumps(payload)))
    assert sdd_gate.main([]) == 2
    assert "no hay spec" in capsys.readouterr().err.lower()


def test_no_bloquea_fuera_de_todo_proyecto_sdd(tmp_path, monkeypatch):
    """Sin proyecto SDD no hay protocolo que aplicar: denegar seria ruido."""
    monkeypatch.setattr(
        "sys.stdin",
        _Stdin(json.dumps(_payload(tmp_path / "sin-sdd", str(tmp_path / "notas.md")))),
    )
    assert sdd_gate.main([]) == 0


def test_un_payload_sin_ruta_no_declara_edicion_y_pasa(tmp_path, monkeypatch):
    """No hay nada que juzgar: bloquear ahi seria ruido, no seguridad."""
    payload = {"cwd": str(tmp_path), "tool_input": {}}
    monkeypatch.setattr("sys.stdin", _Stdin(json.dumps(payload)))
    assert sdd_gate.main([]) == 0


class _Stdin:
    """stdin minimo: el gate solo llama isatty() y read()."""

    def __init__(self, contenido: str) -> None:
        self._contenido = contenido

    def isatty(self) -> bool:
        return False

    def read(self) -> str:
        return self._contenido
