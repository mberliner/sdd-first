"""El wiring del kit se genera desde `templates/wiring/` (SPEC-005 FR-008..FR-013).

Hasta esta spec, cada archivo de `templates/wiring/` que el kit tambien instala
sobre si mismo existia dos veces y nada los mantenia juntos: el arreglo habia
que escribirlo en los dos lados y el drift no lo detectaba nadie. Paso de
verdad -- `.claude/sdd_gate_hook.sh` conservo durante una spec entera un bloque
`IS_ANTIGRAVITY` que su plantilla ya no tenia.

Estos tests cubren las dos mitades del cierre:
- que el par no pueda divergir (el destino se genera, `render --check` lo vigila);
- que un archivo de wiring nuevo no pueda volver a quedar huerfano (todo destino
  del catalogo esta clasificado, con motivo si se excluye).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import render
import sdd_catalog
from sdd_config import load

KIT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = KIT_ROOT / "templates"

WIRING_DIR = TEMPLATES / "wiring"

# SC-008: como resuelve cada plantilla donde vive el andamiaje. No se uniforma la
# tecnica -- se exige que ninguna quede valida en un solo layout. La regla se
# barre sobre la carpeta entera y esta es la lista de EXCEPCIONES: los archivos
# que prueban los dos layouts en runtime, con el motivo. Enumerar en cambio los
# que deben usar el placeholder dejaria fuera del control a cada archivo nuevo.
RUTA_POR_DETECCION = {
    "sdd_gate_hook.sh": (
        "resuelve el interprete y el gate en runtime: tiene que decidir sin que "
        "nadie sustituya nada, incluso copiado suelto"
    ),
    "agy_gate_hook.py": (
        "importa el nucleo probando ambos layouts en sys.path; corre con el cwd "
        "en .agents/, no en la raiz"
    ),
}

# Placeholders que `_sync_renderer` resuelve (FR-011). Los de proyecto los
# resuelve `sdd-init` al instalar: en el kit llegarian crudos al destino.
PLACEHOLDERS_ADMITIDOS = frozenset({"{{sdd.core}}", "{{sdd.adapters}}"})


def _plantillas_de_wiring() -> list[Path]:
    return sorted(p for p in WIRING_DIR.rglob("*") if p.is_file())


def _destinos_wiring() -> list[str]:
    return [dst for _src, dst in sdd_catalog.WIRING]


def test_todo_destino_de_wiring_esta_clasificado():
    """FR-009: sincronizado o excluido con motivo; no hay tercera opcion.

    Es la guarda que faltaba: sin esto, sumar `wiring/loquesea.json` al catalogo
    y copiarlo a mano al kit reintroduce el par sin que nada avise.
    """
    sin_clasificar = [
        dst
        for dst in _destinos_wiring()
        if dst not in render._SYNCED_FROM_TEMPLATES
        and dst not in sdd_catalog.WIRING_NO_SINCRONIZADO
    ]
    assert not sin_clasificar, (
        f"destinos de wiring sin clasificar: {sin_clasificar}. Sumalos al sync de "
        "render.py o declara el motivo en sdd_catalog.WIRING_NO_SINCRONIZADO."
    )


def test_las_excepciones_declaran_motivo_y_existen_en_el_catalogo():
    destinos = set(_destinos_wiring())
    for dst, motivo in sdd_catalog.WIRING_NO_SINCRONIZADO.items():
        assert dst in destinos, f"{dst} no es un destino del catalogo de wiring"
        assert motivo.strip(), f"{dst} se excluye del sync sin motivo escrito"
        assert dst not in render._SYNCED_FROM_TEMPLATES, (
            f"{dst} esta excluido y sincronizado a la vez"
        )


def test_el_wiring_esperado_esta_sincronizado():
    """FR-008: los ocho destinos que el kit instala sobre si mismo."""
    esperados = {
        ".claude/settings.json",
        ".claude/sdd_gate_hook.sh",
        ".pre-commit-config.yaml",
        ".gitattributes",
        ".agents/hooks.json",
        ".agents/agy_gate_hook.py",
        ".agents/agy_deny.json",
        ".opencode/plugin/sdd-gate.js",
    }
    assert esperados <= set(render._SYNCED_FROM_TEMPLATES)


@pytest.mark.parametrize("dst", sorted(sdd_catalog.WIRING_NO_SINCRONIZADO))
def test_las_excepciones_no_se_generan(dst):
    """El motivo tiene que ser real: `.gitignore` y `current-spec` son del dueño."""
    assert dst not in render._generated_targets(KIT_ROOT)


def test_el_wiring_del_kit_no_tiene_drift():
    """El par vive sincronizado ahora mismo, no solo en teoria."""
    cfg = load(KIT_ROOT)
    targets = render._generated_targets(KIT_ROOT)
    for dst in _destinos_wiring():
        if dst not in targets:
            continue
        actual = (KIT_ROOT / dst).read_text(encoding="utf-8")
        assert actual == targets[dst](cfg), (
            f"{dst} difiere de su plantilla: corre `python core/render.py`"
        )


def test_render_escribe_lf_aunque_la_plantilla_tenga_crlf(tmp_path, monkeypatch):
    """FR-010, primera mitad: lo que *escribe* el render, sin git de por medio.

    `sh` no ejecuta un script con CRLF, y el gate es un script. Este test no
    depende del checkout: siembra plantillas con CRLF y mira los bytes que
    quedaron en disco.
    """
    for src_rel in render._SYNCED_FROM_TEMPLATES.values():
        origen = tmp_path / "templates" / src_rel
        origen.parent.mkdir(parents=True, exist_ok=True)
        origen.write_bytes(b"una linea\r\notra linea\r\n")
    monkeypatch.chdir(tmp_path)
    render.load.cache_clear()

    render.main([])

    for dst in render._SYNCED_FROM_TEMPLATES:
        assert b"\r\n" not in (tmp_path / dst).read_bytes(), f"{dst} quedo con CRLF"


def test_el_checkout_conserva_el_lf_del_wiring():
    """FR-010, segunda mitad: lo que sostiene `.gitattributes`.

    El render escribe LF, pero `* text=auto` devolveria estos archivos en CRLF
    en un checkout de Windows -- distintos de lo que el render acaba de escribir.
    Por eso cada uno se declara `eol=lf`. Se verifica el efecto (los bytes del
    arbol de trabajo) y no la linea del archivo: es la regla la que importa,
    no como esta escrita.
    """
    for dst in _destinos_wiring():
        if dst not in render._SYNCED_FROM_TEMPLATES:
            continue
        assert b"\r\n" not in (KIT_ROOT / dst).read_bytes(), (
            f"{dst} llego con CRLF: revisa su regla `eol=lf` en .gitattributes"
        )


# Las formas de *apuntar* al andamiaje vendorizado: la ruta hasta un archivo
# concreto del nucleo, o la ruta armada por partes (`path.join(root, "tools",
# "sdd", "core")`, `Path / "tools" / "sdd" / "core"`). Nombrar `tools/sdd/core/`
# en prosa no molesta: lo que deja el archivo roto del otro lado es usarlo.
_VENDOR_LITERAL = (
    r"tools[/\\]sdd[/\\]core[/\\]\w+\.py",
    r'"tools"\s*,\s*"sdd"\s*,\s*"core"',
    r'"tools"\s*/\s*"sdd"\s*/\s*"core"',
)


# Ruta al nucleo del KIT escrita pelada (`core/sdd_gate.py`): rompe al derivado,
# donde esa carpeta no existe. Mismo criterio que test_template_paths.py, que
# barre el resto de `templates/` pero no llega a `.sh` ni a `.py`.
_KIT_LITERAL = (r"(?<![\w/.{])(core|adapters)/[\w/]+\.py",)


@pytest.mark.parametrize("plantilla", _plantillas_de_wiring(), ids=lambda p: p.name)
def test_ninguna_plantilla_de_wiring_vale_en_un_solo_layout(plantilla):
    """SC-008 por barrido de la carpeta, no contra una lista escrita a mano.

    Una lista dejaria a cada archivo nuevo fuera del control -- la misma omision
    que FR-009 existe para impedir del lado del sync.
    """
    texto = plantilla.read_text(encoding="utf-8")
    if plantilla.name in RUTA_POR_DETECCION:
        pytest.skip(
            f"resuelve el layout en runtime: {RUTA_POR_DETECCION[plantilla.name]}"
        )
    for patron in (*_VENDOR_LITERAL, *_KIT_LITERAL):
        assert not re.search(patron, texto), (
            f"{plantilla.name} hardcodea un layout del andamiaje ({patron}); "
            "usa {{sdd.core}} o declaralo en RUTA_POR_DETECCION con su motivo"
        )


@pytest.mark.parametrize("nombre", sorted(RUTA_POR_DETECCION))
def test_las_plantillas_con_deteccion_prueban_los_dos_layouts(nombre):
    """La alternativa legitima al placeholder: resolver el layout en runtime.

    No alcanza con nombrar el layout del derivado: si el archivo no prueba
    tambien el del kit, la copia sincronizada queda rota de este lado.
    """
    texto = (WIRING_DIR / nombre).read_text(encoding="utf-8")
    assert any(re.search(p, texto) for p in _VENDOR_LITERAL), (
        f"{nombre} no contempla el andamiaje vendorizado"
    )
    # Se borran las menciones al layout del derivado para que su `core` final no
    # cuente como si fuera el del kit.
    resto = re.sub("|".join(_VENDOR_LITERAL), "", texto)
    assert re.search(r"""["'/]core["'/]""", resto), (
        f"{nombre} no contempla el layout del kit (core/)"
    )


def test_las_excepciones_de_ruta_existen_y_declaran_motivo():
    """Si un archivo se renombra o se va, su excepcion no puede quedar colgada."""
    for nombre, motivo in RUTA_POR_DETECCION.items():
        assert (WIRING_DIR / nombre).exists(), f"{nombre} ya no esta en el wiring"
        assert motivo.strip(), f"{nombre} se exceptua sin motivo escrito"


@pytest.mark.parametrize("plantilla", _plantillas_de_wiring(), ids=lambda p: p.name)
def test_el_wiring_solo_usa_placeholders_que_el_sync_resuelve(plantilla):
    """FR-011: `{{project.name}}` en el wiring llegaria crudo al kit.

    `_sync_renderer` resuelve solo los de ruta; los de proyecto los resuelve
    `sdd-init` al instalar, asi que el derivado no notaria nada y el kit se
    quedaria con el placeholder a la vista.
    """
    usados = set(re.findall(r"\{\{[\w.]+\}\}", plantilla.read_text(encoding="utf-8")))
    assert usados <= PLACEHOLDERS_ADMITIDOS, (
        f"{plantilla.name} usa placeholders que el sync no resuelve: "
        f"{sorted(usados - PLACEHOLDERS_ADMITIDOS)}"
    )


def test_el_plugin_de_opencode_del_kit_apunta_a_un_gate_que_existe():
    """El modo de falla del plugin es callarse: si el gate no esta, no bloquea.

    `tool.execute.before` hace `return` cuando el archivo no existe, asi que un
    placeholder mal resuelto no da error -- deja el gate apagado, que es
    exactamente lo que este wiring vino a evitar.
    """
    texto = (KIT_ROOT / ".opencode" / "plugin" / "sdd-gate.js").read_text(
        encoding="utf-8"
    )
    declaracion = re.search(r"const GATE_REL = \[(.*?)\]", texto, re.S)
    assert declaracion, "el plugin ya no declara GATE_REL: revisa este test"
    partes = re.findall(r'"([^"]+)"', declaracion.group(1))
    gate = KIT_ROOT.joinpath(*[p for parte in partes for p in parte.split("/")])
    assert gate.is_file(), f"el plugin apunta a {gate}, que no existe en el kit"


@pytest.mark.parametrize("dst", sorted(sdd_catalog.EXECUTABLE_WIRING))
def test_render_no_degrada_los_permisos_del_wiring_ejecutable(dst, tmp_path):
    """Regenerar el hook no puede dejarlo con menos permisos que instalarlo.

    `sdd_init` y `sdd_update` le ponen 0o755; `render.py` es el tercer escritor
    del mismo archivo. En Windows el bit no se expresa, asi que ahi se verifica
    la intencion (que el destino este en la lista) y no el efecto.
    """
    assert dst in render._SYNCED_FROM_TEMPLATES, (
        f"{dst} es ejecutable pero no lo escribe el render: revisa la lista"
    )
    if os.name == "nt":
        pytest.skip("NTFS no expresa los bits de ejecucion de POSIX")
    destino = KIT_ROOT / dst
    assert destino.stat().st_mode & 0o111, f"{dst} perdio el bit de ejecucion"


@pytest.mark.parametrize("dst", sorted(sdd_catalog.EXECUTABLE_WIRING))
def test_el_bit_de_ejecucion_del_wiring_viaja_en_el_indice(dst):
    """FR-013: el permiso tiene que sobrevivir a un clon, no solo al render.

    `render.py` le devuelve el bit al escribir (FR-012), pero el pipeline corre
    `render --check`, que no escribe: en un checkout fresco el archivo llega con
    el modo que declare el indice. Mientras ese modo fue `100644`, la garantia
    de FR-012 existia solo en la copia donde alguien habia corrido el render en
    modo escritura, y se perdia en el primer checkout o stash/restore. Es la
    misma forma que FR-010 con el LF: lo que escribe el render y lo que entrega
    el checkout son dos puntos distintos, y ninguno alcanza solo.
    """
    if shutil.which("git") is None or not (KIT_ROOT / ".git").exists():
        pytest.skip("sin checkout de git no hay indice donde declarar el modo")
    salida = subprocess.run(
        ["git", "ls-files", "-s", "--", dst],
        cwd=KIT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    modo = salida.split(" ", 1)[0] if salida.strip() else "(ausente del indice)"
    assert modo == "100755", (
        f"{dst} figura en el indice como {modo}: un clon fresco lo entrega sin "
        "permiso de ejecucion. Se corrige con "
        f"`git update-index --chmod=+x {dst}`, no con un chmod suelto "
        "(un chmod no viaja, y con core.fileMode=false git ni lo ve)."
    )


def test_sync_resuelve_el_placeholder_segun_el_layout(tmp_path):
    """El mismo archivo apunta a `core/` en el kit y a `tools/sdd/core/` afuera."""
    (tmp_path / "templates" / "wiring").mkdir(parents=True)
    (tmp_path / "templates" / "wiring" / "ejemplo.yaml").write_text(
        "entry: python {{sdd.core}}/sdd_gate.py\n", encoding="utf-8"
    )
    cfg = load(tmp_path)
    texto = render._sync_renderer("wiring/ejemplo.yaml")(cfg)
    assert texto == "entry: python core/sdd_gate.py\n"
