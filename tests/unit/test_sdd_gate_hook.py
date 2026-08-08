"""Tests de los hooks shell del gate (SPEC-004 FR-006, SPEC-015 FR-002).

Cubre la rama normal (con python3 disponible, el gate corre y decide) y la
rama fail-closed (sin ningun interprete) para ambos scripts:
- .claude/sdd_gate_hook.sh (del propio kit)
- templates/wiring/sdd_gate_hook.sh (plantilla instalada)

Desde SPEC-015 la rama fail-closed ya no bloquea `src/` fijo: deriva las
carpetas de codigo de `dirs` en `.sdd/config.yaml`, asi que un proyecto con el
codigo en `pkg/` queda protegido y `src/` —que no declara— no.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
KIT_HOOK = KIT_ROOT / ".claude" / "sdd_gate_hook.sh"
TEMPLATE_HOOK = KIT_ROOT / "templates" / "wiring" / "sdd_gate_hook.sh"


def _seed_config(root: Path, cuerpo: str) -> Path:
    (root / ".sdd").mkdir(parents=True, exist_ok=True)
    (root / ".sdd" / "config.yaml").write_text(cuerpo, encoding="utf-8")
    return root


def _run_hook(
    script: Path, project_dir: Path, file_path: str, *, path: str | None
) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_input": {"file_path": file_path}})
    env = {"CLAUDE_PROJECT_DIR": str(project_dir)}
    if path is not None:
        env["PATH"] = path
    sh = shutil.which("sh") or "/bin/sh"
    return subprocess.run(
        [sh, str(script)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_dir),
    )


def test_kit_hook_normal_corre_el_gate_y_bloquea_sin_spec(tmp_path):
    real_path = shutil.os.environ.get("PATH", "")  # PATH real: encuentra python3
    res = _run_hook(KIT_HOOK, KIT_ROOT, "core/foo.py", path=real_path)
    # El gate del propio kit corre de verdad; el resultado depende de si hay
    # spec vigente declarada, pero NO debe ser el mensaje fail-closed.
    assert "no se encontro un interprete" not in res.stderr


@pytest.fixture
def kit_sin_venv(tmp_path):
    """Raiz con el config **real** del kit y sin `.venv`.

    La rama fail-closed empieza probando `$ROOT/.venv/bin/python`, asi que
    contra la raiz real del clon era inalcanzable en cuanto el proyecto tenia
    entorno virtual: el hook encontraba interprete y decidia normalmente. Estos
    tests pasaban en CI (que instala global) y fallaban en la maquina de quien
    desarrolla, que es justo al reves de lo util. Copiar el config preserva lo
    que interesa —los roots que declara el kit— sin depender del clon.
    """
    raiz = tmp_path / "kit"
    (raiz / ".sdd").mkdir(parents=True)
    shutil.copy(KIT_ROOT / ".sdd" / "config.yaml", raiz / ".sdd" / "config.yaml")
    return raiz


def test_kit_hook_fail_closed_bloquea_bajo_los_roots_del_kit(kit_sin_venv):
    # El config del kit declara [core, adapters].
    res = _run_hook(KIT_HOOK, kit_sin_venv, "core/foo.py", path="/nonexistent")
    assert res.returncode == 2, res.stderr
    assert "no se encontro un interprete" in res.stderr


def test_kit_hook_fail_closed_permite_fuera_de_los_roots(kit_sin_venv):
    res = _run_hook(KIT_HOOK, kit_sin_venv, "README.md", path="/nonexistent")
    assert res.returncode == 0, res.stderr


def test_template_hook_fail_closed_bloquea_el_root_declarado(tmp_path):
    """El corazon de SPEC-015: protege `pkg/` porque el config lo declara."""
    _seed_config(tmp_path, "dirs:\n  source_roots: [pkg]\n")
    res = _run_hook(TEMPLATE_HOOK, tmp_path, "pkg/foo.py", path="/nonexistent")
    assert res.returncode == 2
    assert "pkg/" in res.stderr


def test_template_hook_fail_closed_ignora_src_si_no_esta_declarado(tmp_path):
    """Y `src/` deja de ser especial: no esta en el config de este proyecto."""
    _seed_config(tmp_path, "dirs:\n  source_roots: [pkg]\n")
    res = _run_hook(TEMPLATE_HOOK, tmp_path, "src/foo.py", path="/nonexistent")
    assert res.returncode == 0


def test_template_hook_fail_closed_usa_roots_implicitos(tmp_path):
    """Sin `source_roots` explicito, derivan de las capas declaradas en `dirs`."""
    _seed_config(tmp_path, "dirs:\n  domain: app/domain\n  tests_unit: tests/unit\n")
    res = _run_hook(TEMPLATE_HOOK, tmp_path, "app/domain/x.py", path="/nonexistent")
    assert res.returncode == 2
    assert "app/" in res.stderr


def test_template_hook_fail_closed_sin_config_cae_al_default_src(tmp_path):
    res = _run_hook(TEMPLATE_HOOK, tmp_path, "src/foo.py", path="/nonexistent")
    assert res.returncode == 2
    assert "no se encontro un interprete" in res.stderr


def test_template_hook_fail_closed_permite_fuera_de_los_roots(tmp_path):
    _seed_config(tmp_path, "dirs:\n  source_roots: [pkg]\n")
    res = _run_hook(TEMPLATE_HOOK, tmp_path, "README.md", path="/nonexistent")
    assert res.returncode == 0
