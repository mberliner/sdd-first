"""El catalogo de claves del config viaja con la instalacion (SPEC-013 FR-008/010).

K-2 de `docs/IDEAS.md`: la cabecera de `.sdd/config.yaml` remitia al catalogo
"en el kit, en examples/config/config.yaml" --un archivo que el derivado no
tiene--. Bajo la premisa vieja daba igual, porque siempre habia un clon del kit a
mano; bajo la nueva (el kit es desechable, README) es una referencia colgada en
el archivo que el dueno mas edita.
"""

from __future__ import annotations

from pathlib import Path

import sdd_init

KIT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = KIT_ROOT / "examples" / "config" / "config.yaml"


def test_el_catalogo_queda_instalado(tmp_path: Path):
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    assert (tmp_path / sdd_init.CONFIG_REFERENCE_RELPATH).exists()


def test_el_catalogo_se_instala_verbatim(tmp_path: Path):
    # Verbatim y no reescrito: el catalogo *es* ese YAML, su valor esta en los
    # comentarios junto a cada clave. Una version resumida seria una segunda
    # descripcion del mismo tema (Principio IV).
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    instalado = (tmp_path / sdd_init.CONFIG_REFERENCE_RELPATH).read_text(
        encoding="utf-8"
    )
    assert instalado == EXAMPLE.read_text(encoding="utf-8").replace("\r\n", "\n")


def test_la_cabecera_del_config_apunta_al_catalogo_instalado(tmp_path: Path):
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    cabecera = (tmp_path / ".sdd" / "config.yaml").read_text(encoding="utf-8")
    assert sdd_init.CONFIG_REFERENCE_RELPATH.as_posix() in cabecera
    # Y ya no manda a buscar el archivo dentro del clon del kit.
    assert "examples/config/config.yaml" not in cabecera


def test_el_catalogo_se_refresca_aunque_el_config_se_conserve(tmp_path: Path):
    # El config sembrado es del dueno (se conserva); el catalogo es artefacto del
    # kit y se reescribe, como tools/sdd/. Un catalogo viejo describiendo claves
    # de otra version del andamiaje es peor que no tenerlo.
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    config = tmp_path / ".sdd" / "config.yaml"
    config.write_text("# editado por el dueno\n", encoding="utf-8")
    catalogo = tmp_path / sdd_init.CONFIG_REFERENCE_RELPATH
    catalogo.write_text("# catalogo viejo\n", encoding="utf-8")

    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0

    assert config.read_text(encoding="utf-8") == "# editado por el dueno\n"
    assert catalogo.read_text(encoding="utf-8") != "# catalogo viejo\n"


def test_el_indice_nombra_el_catalogo(tmp_path: Path):
    # FR-010: 00-INDEX es donde el dueno busca cual es el SSOT de cada tema.
    assert sdd_init.main([str(tmp_path), "--language=none"]) == 0
    indice = (tmp_path / "00-INDEX.md").read_text(encoding="utf-8")
    assert sdd_init.CONFIG_REFERENCE_RELPATH.as_posix() in indice
