"""Las skills quedan usables apenas termina la instalacion (SPEC-016).

Hasta SPEC-016 `sdd-init` copiaba solo las fuentes (`.agents/skills/`, que leen
Codex y Antigravity) y dejaba la generacion de los adaptadores como paso manual
numero 3. Efecto medido en una instalacion limpia: Claude Code y opencode no
veian **ninguna** skill SDD, incluida la `sdd-configure` que el propio
instalador recomienda correr en el paso 1.
"""

from __future__ import annotations

import subprocess
import sys

import gen_skill_adapters
import sdd_init


def _instalar(target, language: str = "none") -> None:
    assert sdd_init.main([str(target), f"--language={language}"]) == 0


def test_install_project_skills_no_calcula_ruta_de_playbook(tmp_path):
    # SPEC-016 FR-010: `src` (ruta al playbook) quedo muerta cuando el copiado
    # de playbooks paso a STATIC_DOCS; no debe calcularse ni descartarse.
    import inspect

    fuente = inspect.getsource(sdd_init._install_project_skills)
    assert "_ = src" not in fuente
    assert "playbooks" not in fuente
    out = sdd_init._install_project_skills(tmp_path, force=False)
    assert any("SKILL.md" in linea for linea in out)


def test_instala_los_adaptadores_de_las_dos_familias(tmp_path):
    # FR-002: sin estos archivos las skills no son descubribles.
    _instalar(tmp_path)
    for skill in sdd_init.PROJECT_SKILLS:
        assert (tmp_path / ".claude" / "skills" / skill / "SKILL.md").exists(), (
            f"falta el adaptador de Claude Code para {skill}"
        )
        assert (tmp_path / ".opencode" / "command" / f"{skill}.md").exists(), (
            f"falta el command de opencode para {skill}"
        )


def test_no_instala_la_skill_de_bootstrap(tmp_path):
    # `sdd-init` es de una sola vez y se corre desde el clon del kit (SPEC-007).
    _instalar(tmp_path)
    assert not (tmp_path / ".claude" / "skills" / "sdd-init").exists()
    assert not (tmp_path / ".opencode" / "command" / "sdd-init.md").exists()


def test_lo_sembrado_no_tiene_drift_contra_el_generador(tmp_path):
    """SC-002: el paso `skills` del pipeline verifica con `--check`.

    Se corre el generador real sobre el destino, como lo haria el pipeline
    instalado: si el instalador sembrara algo distinto, la instalacion fresca
    arrancaria en ROJO.
    """
    _instalar(tmp_path)
    resultado = subprocess.run(  # nosec B603 - script del propio kit vendorizado
        [
            sys.executable,
            str(tmp_path / "tools" / "sdd" / "core" / "gen_skill_adapters.py"),
            "--check",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_el_adaptador_generado_se_reescribe_sin_force(tmp_path):
    """FR-003: es artefacto generado, no un archivo del dueno del proyecto.

    Conservarlo dejaria el paso `skills` en ROJO desde la instalacion.
    """
    destino = tmp_path / ".claude" / "skills" / "analyze" / "SKILL.md"
    destino.parent.mkdir(parents=True)
    destino.write_text("editado a mano", encoding="utf-8")

    _instalar(tmp_path)

    assert destino.read_text(encoding="utf-8") != "editado a mano"
    assert "NO EDITAR A MANO" in destino.read_text(encoding="utf-8")


def test_la_fuente_de_la_skill_si_se_conserva(tmp_path):
    # FR-003: la idempotencia sigue valiendo para lo editable a mano.
    fuente = tmp_path / ".agents" / "skills" / "analyze" / "SKILL.md"
    fuente.parent.mkdir(parents=True)
    fuente.write_text("mi version", encoding="utf-8")

    _instalar(tmp_path)

    assert fuente.read_text(encoding="utf-8") == "mi version"


def test_un_fallo_del_generador_no_aborta_la_instalacion(tmp_path, monkeypatch, capsys):
    """FR-004: el andamiaje ya esta copiado; dejarlo a medias es peor.

    El aviso tiene que traer el comando para reintentar: sin adaptadores el
    asistente no tiene ninguna skill con la que resolverlo por su cuenta.
    """

    def _falla(_root, check=False):
        return gen_skill_adapters.Result(
            written=[], drift=[], problems=["analyze: falta el playbook SSOT"], skills=1
        )

    monkeypatch.setattr(gen_skill_adapters, "generate", _falla)
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0

    salida = capsys.readouterr().out
    assert "falta el playbook SSOT" in salida
    assert "gen_skill_adapters.py" in salida
    # Lo demas se instalo igual.
    assert (tmp_path / "CONSTITUTION.md").exists() or (tmp_path / "AGENTS.md").exists()
