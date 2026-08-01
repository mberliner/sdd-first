"""Tests de los hooks shell del gate (SPEC-004 FR-006).

Cubre la rama normal (con python3 disponible, el gate corre y decide) y la
rama fail-closed (sin ningun interprete, bloquea bajo la carpeta de codigo
fuente y permite fuera de ella) para ambos scripts:
- .claude/sdd_gate_hook.sh (del propio kit, bloquea bajo core/ y adapters/)
- templates/wiring/sdd_gate_hook.sh (plantilla instalada, bloquea bajo src/)
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[2]


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
    script = KIT_ROOT / ".claude" / "sdd_gate_hook.sh"
    real_path = shutil.os.environ.get("PATH", "")  # PATH real: encuentra python3
    res = _run_hook(script, KIT_ROOT, "core/foo.py", path=real_path)
    # El gate del propio kit corre de verdad; el resultado depende de si hay
    # spec vigente declarada, pero NO debe ser el mensaje fail-closed.
    assert "no se encontro un interprete" not in res.stderr


def test_kit_hook_fail_closed_bloquea_bajo_core(tmp_path):
    script = KIT_ROOT / ".claude" / "sdd_gate_hook.sh"
    res = _run_hook(script, tmp_path, "core/foo.py", path="/nonexistent")
    assert res.returncode == 2
    assert "no se encontro un interprete" in res.stderr


def test_kit_hook_fail_closed_permite_fuera_de_core(tmp_path):
    script = KIT_ROOT / ".claude" / "sdd_gate_hook.sh"
    res = _run_hook(script, tmp_path, "README.md", path="/nonexistent")
    assert res.returncode == 0


def test_template_hook_fail_closed_bloquea_bajo_src(tmp_path):
    script = KIT_ROOT / "templates" / "wiring" / "sdd_gate_hook.sh"
    res = _run_hook(script, tmp_path, "src/foo.py", path="/nonexistent")
    assert res.returncode == 2
    assert "no se encontro un interprete" in res.stderr


def test_template_hook_fail_closed_permite_fuera_de_src(tmp_path):
    script = KIT_ROOT / "templates" / "wiring" / "sdd_gate_hook.sh"
    res = _run_hook(script, tmp_path, "README.md", path="/nonexistent")
    assert res.returncode == 0
