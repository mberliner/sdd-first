"""El derivado solo declara los principios que su dueno eligio (SPEC-013 FR-001).

Antes se sembraba el catalogo completo del ejemplo, incluidos los opcionales:
la constitucion de un proyecto recien creado declaraba principios que nadie
eligio (datasets, SSOT), y el playbook de `sdd-configure` -- que manda partir
del nucleo minimo y *preguntar* los opcionales -- quedaba contradicho por el
sembrado.
"""

from __future__ import annotations

import re

import sdd_init
import yaml


def _config_sembrado(tmp_path) -> dict:
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    return yaml.safe_load(
        (tmp_path / ".sdd" / "config.yaml").read_text(encoding="utf-8")
    )


def test_siembra_solo_el_nucleo_minimo(tmp_path):
    principios = _config_sembrado(tmp_path)["principles"]
    assert [p["id"] for p in principios] == ["I", "II", "III", "IV"]


def test_los_opcionales_quedan_comentados_y_a_la_vista(tmp_path):
    sdd_init.main([str(tmp_path), "--language=none"])
    texto = (tmp_path / ".sdd" / "config.yaml").read_text(encoding="utf-8")
    assert "# Principios OPCIONALES: descomenta" in texto
    # Siguen legibles para poder elegirlos, pero inactivos.
    assert "#   title: Datos no versionados" in texto
    assert "#   title: SSOT unico por tema" in texto


def test_descomentar_los_opcionales_produce_yaml_valido(tmp_path):
    # El sembrado usa prefijo fijo + indentacion relativa: descomentar es
    # borrar `# ` de cada linea y el YAML tiene que seguir alineado. Si no,
    # el dueno que acepta un principio se lleva un config roto.
    sdd_init.main([str(tmp_path), "--language=none"])
    dst = tmp_path / ".sdd" / "config.yaml"

    dato_comentado = re.compile(r"^(\s*)# (- id:|  \w+:)")
    reactivado = "\n".join(
        dato_comentado.sub(r"\1\2", linea)
        for linea in dst.read_text(encoding="utf-8").splitlines()
    )

    ids = [p["id"] for p in yaml.safe_load(reactivado)["principles"]]
    assert ids == ["I", "II", "III", "IV", "V", "VI"]
