"""`.sdd/kit.lock`: escritura determinista y linea base del kit, no del disco.

SPEC-025 FR-US1-002, FR-US1-003, FR-US2-008.
"""

from __future__ import annotations

import json
from pathlib import Path

import sdd_config
import sdd_init
import sdd_lock

KIT_ROOT = Path(__file__).resolve().parents[2]


def test_hash_bytes_es_sha256():
    assert sdd_lock.hash_bytes(b"hola") == sdd_config.hash_bytes(b"hola")
    import hashlib

    assert sdd_lock.hash_bytes(b"hola") == hashlib.sha256(b"hola").hexdigest()


def test_build_lock_registra_version_algoritmo_sustituciones_y_hashes(tmp_path):
    """FR-US1-002: instalar en carpeta vacia deja un lock con la version real,
    los valores de sustitucion usados y un hash por plantilla instalada."""
    sdd_init.main([str(tmp_path), "--language=python"])
    lock = sdd_lock.load_lock(tmp_path)
    assert lock is not None
    assert lock.kit_version == sdd_config.KIT_VERSION
    assert lock.algorithm == "sha256"
    assert lock.substitutions["project.name"]
    assert "AGENTS.md" in lock.plantillas
    assert "specs/SPECS_REGISTRY.md" in lock.semillas
    assert ".sdd/current-spec" in lock.semillas
    assert ".sdd/config.yaml" in lock.semillas


def test_lock_deja_de_coincidir_solo_para_el_archivo_editado(tmp_path):
    """FR-US1-002 (Acceptance Scenarios US1): editar un documento hace que el
    lock deje de coincidir para ese archivo y siga coincidiendo para el resto."""
    sdd_init.main([str(tmp_path), "--language=python"])
    lock = sdd_lock.load_lock(tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        (tmp_path / "AGENTS.md").read_text(encoding="utf-8") + "\nEDITADO\n",
        encoding="utf-8",
    )
    hash_agents = sdd_config.hash_bytes((tmp_path / "AGENTS.md").read_bytes())
    hash_readme = sdd_config.hash_bytes((tmp_path / "README.md").read_bytes())
    assert hash_agents != lock.plantillas["AGENTS.md"]
    assert hash_readme == lock.plantillas["README.md"]


def test_lock_es_json_determinista_byte_a_byte(tmp_path):
    """FR-US1-002: JSON con claves ordenadas; dos instalaciones equivalentes
    (mismo nombre de proyecto) producen el mismo archivo."""
    destino_a = tmp_path / "contenedor-a" / "mismo-nombre"
    destino_b = tmp_path / "contenedor-b" / "mismo-nombre"
    sdd_init.main([str(destino_a), "--language=python"])
    sdd_init.main([str(destino_b), "--language=python"])
    texto_a = (destino_a / sdd_lock.LOCK_RELPATH).read_text(encoding="utf-8")
    texto_b = (destino_b / sdd_lock.LOCK_RELPATH).read_text(encoding="utf-8")
    assert texto_a == texto_b
    crudo = json.loads(texto_a)
    assert list(crudo.keys()) == sorted(crudo.keys())


def test_kit_lock_no_esta_en_gitignore_plantilla():
    """FR-US1-003: el lock se versiona -- distinto de `.sdd/current-spec`."""
    texto = (KIT_ROOT / "templates" / "wiring" / ".gitignore").read_text(
        encoding="utf-8"
    )
    assert "kit.lock" not in texto


def test_brownfield_registra_el_hash_del_kit_no_el_del_dueno(tmp_path):
    """FR-US2-008/ANA-001: un archivo preexistente que sdd-init conserva entra
    al lock con el hash de lo que el kit entrega, no con el del disco -- si no,
    la primera actualizacion lo daria por intacto y lo pisaria en silencio."""
    tmp_path.mkdir(exist_ok=True)
    propio = "# Mi AGENTS.md propio, nada que ver con el del kit\n"
    (tmp_path / "AGENTS.md").write_text(propio, encoding="utf-8")
    sdd_init.main([str(tmp_path), "--language=python"])
    lock = sdd_lock.load_lock(tmp_path)
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == propio
    assert lock.plantillas["AGENTS.md"] != sdd_config.hash_bytes(propio.encode("utf-8"))


def test_load_lock_ausente_devuelve_none(tmp_path):
    assert sdd_lock.load_lock(tmp_path) is None


def test_load_lock_ilegible_levanta_lockilegible(tmp_path):
    (tmp_path / ".sdd").mkdir(parents=True)
    (tmp_path / ".sdd" / "kit.lock").write_text("{esto no es json", encoding="utf-8")
    try:
        sdd_lock.load_lock(tmp_path)
    except sdd_lock.LockIlegible:
        pass
    else:  # pragma: no cover - documenta la expectativa
        raise AssertionError("se esperaba LockIlegible")


def test_load_lock_sin_claves_minimas_levanta_lockilegible(tmp_path):
    (tmp_path / ".sdd").mkdir(parents=True)
    (tmp_path / ".sdd" / "kit.lock").write_text(
        json.dumps({"foo": "bar"}), encoding="utf-8"
    )
    try:
        sdd_lock.load_lock(tmp_path)
    except sdd_lock.LockIlegible:
        pass
    else:  # pragma: no cover
        raise AssertionError("se esperaba LockIlegible")
