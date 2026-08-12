"""`sdd-doctor` antes y después: decide por delta, no por el estado absoluto.

SPEC-025 FR-US2-009.
"""

from __future__ import annotations

import sdd_config
import sdd_init
import sdd_update


def _instalar(tmp_path):
    sdd_init.main([str(tmp_path), "--language=python"])
    sdd_config.load.cache_clear()


def test_problema_preexistente_no_pone_en_rojo_una_actualizacion_correcta(tmp_path):
    """FR-US2-009: un `.gitignore` sin la linea de current-spec ya estaba roto
    antes de actualizar -- no es responsabilidad de sdd-update."""
    _instalar(tmp_path)
    gitignore = tmp_path / ".gitignore"
    texto = gitignore.read_text(encoding="utf-8")
    gitignore.write_text(texto.replace(".sdd/current-spec\n", ""), encoding="utf-8")
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 0


def test_problema_nuevo_introducido_por_la_actualizacion_pone_en_rojo(
    tmp_path, monkeypatch
):
    """FR-US2-009: si algo que antes estaba sano deja de estarlo, es
    responsabilidad de la actualizacion."""
    _instalar(tmp_path)

    llamadas = {"n": 0}
    original = sdd_update._doctor_problems

    def _fake(target):
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            return []
        return [*original(target), "problema inventado por el test"]

    monkeypatch.setattr(sdd_update, "_doctor_problems", _fake)
    exit_code = sdd_update.main([str(tmp_path), "--apply"])
    assert exit_code == 1
