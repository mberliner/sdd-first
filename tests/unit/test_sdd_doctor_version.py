"""`sdd-doctor` lee la version instalada del lock, no del config.

SPEC-025 FR-US1-005.
"""

from __future__ import annotations

import json
import subprocess
import sys

import sdd_config
import sdd_doctor
import sdd_init
import sdd_lock


def _instalar(tmp_path):
    """Instala y regenera lo derivado: sin `render.py`, `sdd-doctor` ya sale en
    rojo por `CONSTITUTION.md` faltante -- independiente de esta spec."""
    sdd_init.main([str(tmp_path), "--language=python"])
    sdd_config.load.cache_clear()
    subprocess.run(
        [sys.executable, str(tmp_path / "tools" / "sdd" / "core" / "render.py")],
        cwd=str(tmp_path),
        check=True,
    )


def test_reporta_version_del_lock_como_nota_no_como_problema(
    tmp_path, capsys, monkeypatch
):
    _instalar(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = sdd_doctor.main([])
    salida = capsys.readouterr().out
    assert exit_code == 0
    assert f"kit_version instalada: {sdd_config.KIT_VERSION}" in salida


def test_lock_ausente_es_nota_no_problema(tmp_path, capsys, monkeypatch):
    _instalar(tmp_path)
    (tmp_path / sdd_lock.LOCK_RELPATH).unlink()
    monkeypatch.chdir(tmp_path)
    exit_code = sdd_doctor.main([])
    salida = capsys.readouterr().out
    assert exit_code == 0
    assert "sin lock" in salida


def test_version_del_lock_desincronizada_de_la_vendorizada_es_problema(
    tmp_path, capsys, monkeypatch
):
    """FR-US1-005: `.sdd/kit.lock` con una version distinta de la vendorizada
    es una actualizacion a medio aplicar."""
    _instalar(tmp_path)
    lock_path = tmp_path / sdd_lock.LOCK_RELPATH
    crudo = json.loads(lock_path.read_text(encoding="utf-8"))
    crudo["kit_version"] = "0.0.1"
    lock_path.write_text(json.dumps(crudo), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    exit_code = sdd_doctor.main([])
    salida = capsys.readouterr().out
    assert exit_code == 1
    assert "medio aplicar" in salida


def test_lock_ilegible_es_problema(tmp_path, capsys, monkeypatch):
    _instalar(tmp_path)
    (tmp_path / sdd_lock.LOCK_RELPATH).write_text("{no json", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    exit_code = sdd_doctor.main([])
    salida = capsys.readouterr().out
    assert exit_code == 1
    assert "ilegible" in salida
