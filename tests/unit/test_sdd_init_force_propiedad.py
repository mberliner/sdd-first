"""`sdd-init --force` respeta el catálogo de clases de propiedad.

SPEC-025 FR-US2-013.
"""

from __future__ import annotations

import sdd_config
import sdd_init


def _instalar(tmp_path):
    sdd_init.main([str(tmp_path), "--language=python"])
    sdd_config.load.cache_clear()


def test_force_no_borra_registro_ni_historial(tmp_path):
    _instalar(tmp_path)
    registro = tmp_path / "specs" / "SPECS_REGISTRY.md"
    historial = tmp_path / "historial" / "sdd.md"
    registro.write_text(
        registro.read_text(encoding="utf-8") + "| propia |\n", encoding="utf-8"
    )
    historial.write_text(
        historial.read_text(encoding="utf-8") + "\npropio\n", encoding="utf-8"
    )
    sdd_init.main([str(tmp_path), "--language=python", "--force"])
    assert "propia" in registro.read_text(encoding="utf-8")
    assert "propio" in historial.read_text(encoding="utf-8")


def test_force_no_pisa_plantilla_editada_deja_kit_new(tmp_path):
    _instalar(tmp_path)
    original = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(original + "\nEDITADO\n", encoding="utf-8")
    sdd_init.main([str(tmp_path), "--language=python", "--force"])
    assert (tmp_path / "AGENTS.md").read_text(
        encoding="utf-8"
    ) == original + "\nEDITADO\n"
    assert (tmp_path / "AGENTS.md.kit-new").exists()


def test_force_pisa_plantilla_intacta(tmp_path, capsys):
    """Una plantilla que el dueño nunca tocó no genera conflicto con --force:
    se reescribe (o queda sin cambios) sin dejar `.kit-new`."""
    _instalar(tmp_path)
    readme = tmp_path / "README.md"
    contenido_original = readme.read_text(encoding="utf-8")
    sdd_init.main([str(tmp_path), "--language=python", "--force"])
    salida = capsys.readouterr().out
    assert readme.read_text(encoding="utf-8") == contenido_original
    assert not (tmp_path / "README.md.kit-new").exists()
    assert "CONFLICTO (editado): " + str(readme) not in salida


def test_force_no_borra_config_yaml(tmp_path):
    _instalar(tmp_path)
    config = tmp_path / ".sdd" / "config.yaml"
    texto = config.read_text(encoding="utf-8") + "\n# nota propia\n"
    config.write_text(texto, encoding="utf-8")
    sdd_init.main([str(tmp_path), "--language=python", "--force"])
    assert "# nota propia" in config.read_text(encoding="utf-8")


def test_force_sin_lock_no_pisa_nada_y_lo_dice(tmp_path, capsys):
    """FR-US2-013/ANA-023: sin lock, --force no pisa una plantilla editada
    presente, y la salida lo explica -- sin lock no se puede afirmar que esa
    edición sea segura de pisar."""
    _instalar(tmp_path)
    (tmp_path / ".sdd" / "kit.lock").unlink()
    original = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(original + "\nEDITADO\n", encoding="utf-8")
    sdd_init.main([str(tmp_path), "--language=python", "--force"])
    salida = capsys.readouterr().out
    assert (tmp_path / "AGENTS.md").read_text(
        encoding="utf-8"
    ) == original + "\nEDITADO\n"
    assert "CONFLICTO" in salida
