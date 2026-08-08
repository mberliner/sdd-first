"""Unitarios del harness e2e: el que verifica al kit tambien se verifica.

Cubren lo que un escenario e2e no puede cubrir sin destruir algo: que el
workspace nunca se solape con el arbol del kit (SPEC-018 FR-US2-001), que solo
se borre lo que dejo la suite (FR-US2-007), que se regenere igual dos veces
seguidas (FR-US2-002) y que el degradado por entorno incompleto no se vuelva un
verde silencioso (FR-US1-005).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from e2e.lib import entorno
from e2e.lib.aserciones import VAR_ESTRICTO, omitir_o_fallar
from e2e.lib.ejecucion import Resultado

ESCENARIOS = entorno.KIT_ROOT / "tests" / "e2e" / "escenarios"


# --- El workspace nunca se solapa con el kit (FR-US2-001) ---


@pytest.mark.parametrize(
    "candidato",
    [
        pytest.param(entorno.KIT_ROOT, id="la_raiz_del_kit"),
        pytest.param(entorno.KIT_ROOT / "tests" / "tmp", id="dentro_del_kit"),
        pytest.param(entorno.KIT_ROOT.parent, id="contiene_al_kit"),
    ],
)
def test_workspace_solapado_con_el_kit_aborta(candidato: Path) -> None:
    with pytest.raises(entorno.WorkspaceInvalido):
        entorno.verificar_fuera_del_kit(candidato)


def test_workspace_por_defecto_cae_fuera_del_kit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(entorno.VAR_WORKSPACE, raising=False)
    raiz = entorno.raiz_de_trabajo()
    assert entorno.KIT_ROOT not in raiz.parents
    assert raiz != entorno.KIT_ROOT


def test_la_variable_de_entorno_manda(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(entorno.VAR_WORKSPACE, str(tmp_path / "propio"))
    assert entorno.raiz_de_trabajo() == (tmp_path / "propio").resolve()


def test_la_variable_de_entorno_tambien_se_verifica(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(entorno.VAR_WORKSPACE, str(entorno.KIT_ROOT / "tmp-e2e"))
    with pytest.raises(entorno.WorkspaceInvalido):
        entorno.raiz_de_trabajo()


# --- Regeneracion total (FR-US2-002) ---


def test_rehacer_deja_el_workspace_vacio_y_es_repetible(tmp_path: Path) -> None:
    raiz = entorno.rehacer(tmp_path / "work")
    (raiz / "residuo.txt").write_text("de la corrida anterior", encoding="utf-8")

    segunda = entorno.rehacer(raiz)
    assert [p.name for p in segunda.iterdir()] == [entorno.MARCA], (
        "dos corridas seguidas no parten de lo mismo"
    )

    (segunda / "otro-residuo.txt").write_text("de esta corrida", encoding="utf-8")
    tercera = entorno.rehacer(raiz)
    assert [p.name for p in tercera.iterdir()] == [entorno.MARCA]


# --- Solo se borra lo que la suite dejo (FR-US2-007) ---


def test_una_carpeta_ajena_con_contenido_no_se_borra(tmp_path: Path) -> None:
    ajena = tmp_path / "proyectos"
    ajena.mkdir()
    (ajena / "tesis.txt").write_text("trabajo de otro", encoding="utf-8")

    with pytest.raises(entorno.WorkspaceInvalido) as excinfo:
        entorno.rehacer(ajena)

    assert entorno.MARCA in str(excinfo.value)
    assert (ajena / "tesis.txt").exists(), "aborto pero igual borro algo"


def test_una_carpeta_vacia_o_inexistente_si_se_usa(tmp_path: Path) -> None:
    vacia = tmp_path / "vacia"
    vacia.mkdir()
    assert entorno.rehacer(vacia) == vacia
    assert entorno.rehacer(tmp_path / "todavia-no-existe").exists()


def test_la_marca_de_la_corrida_anterior_autoriza_el_borrado(tmp_path: Path) -> None:
    raiz = entorno.rehacer(tmp_path / "work")
    (raiz / "derivado").mkdir()
    assert (raiz / entorno.MARCA).exists(), "rehacer no sembro la marca"

    entorno.rehacer(raiz)
    assert not (raiz / "derivado").exists()


def test_sin_la_marca_la_corrida_siguiente_ya_no_borra(tmp_path: Path) -> None:
    """Borrar la marca a mano es la forma de proteger un workspace."""
    raiz = entorno.rehacer(tmp_path / "work")
    (raiz / "derivado").mkdir()
    (raiz / entorno.MARCA).unlink()

    with pytest.raises(entorno.WorkspaceInvalido):
        entorno.rehacer(raiz)
    assert (raiz / "derivado").exists()


def test_un_archivo_donde_va_el_workspace_aborta(tmp_path: Path) -> None:
    archivo = tmp_path / "no-soy-carpeta"
    archivo.write_text("x", encoding="utf-8")
    with pytest.raises(entorno.WorkspaceInvalido):
        entorno.rehacer(archivo)


def test_borrar_vence_a_los_archivos_de_solo_lectura(tmp_path: Path) -> None:
    """Los objetos de `.git` quedan sin permiso de escritura en Windows."""
    raiz = tmp_path / "repo"
    (raiz / "objetos").mkdir(parents=True)
    archivo = raiz / "objetos" / "blob"
    archivo.write_text("contenido", encoding="utf-8")
    archivo.chmod(0o444)

    entorno.borrar(raiz)
    assert not raiz.exists()


def test_nuevo_destino_parte_siempre_limpio(tmp_path: Path) -> None:
    raiz = entorno.rehacer(tmp_path / "work")
    primero = entorno.nuevo_destino(raiz, "escenario")
    (primero / "sucio.txt").write_text("x", encoding="utf-8")

    segundo = entorno.nuevo_destino(raiz, "escenario")
    assert segundo == primero
    assert list(segundo.iterdir()) == []


# --- Degradado por entorno incompleto (FR-US1-005) ---


def test_sin_modo_estricto_la_falta_de_entorno_omite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(VAR_ESTRICTO, raising=False)
    with pytest.raises(pytest.skip.Exception) as excinfo:
        omitir_o_fallar("falta pre-commit")
    assert "falta pre-commit" in str(excinfo.value)


def test_en_modo_estricto_la_misma_falta_es_fallo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(VAR_ESTRICTO, "1")
    with pytest.raises(pytest.fail.Exception) as excinfo:
        omitir_o_fallar("falta pre-commit")
    assert "falta pre-commit" in str(excinfo.value)


def test_el_modo_estricto_ignora_el_valor_vacio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(VAR_ESTRICTO, "   ")
    with pytest.raises(pytest.skip.Exception):
        omitir_o_fallar("falta pre-commit")


# --- Un fallo tiene que mostrar la salida (FR-US1-002) ---


def test_el_detalle_de_un_resultado_trae_la_salida_completa(tmp_path: Path) -> None:
    res = Resultado(["cmd", "--flag"], tmp_path, 2, "linea uno\nlinea dos\n")
    detalle = res.detalle()
    assert "cmd --flag" in detalle
    assert "exit=2" in detalle
    assert "linea uno" in detalle and "linea dos" in detalle


def test_el_detalle_de_un_comando_mudo_lo_dice(tmp_path: Path) -> None:
    assert "(sin salida)" in Resultado(["cmd"], tmp_path, 0, "").detalle()


# --- Los escenarios declaran que verifican (FR-US1-003/FR-US1-004) ---


def test_cada_escenario_documenta_el_defecto_que_lo_origino() -> None:
    archivos = sorted(ESCENARIOS.glob("test_*.py"))
    assert len(archivos) >= 5, (
        "faltan escenarios de los que declara SPEC-018 FR-US1-003"
    )
    sin_docstring = [
        f.name
        for f in archivos
        if not re.match(r'^"""', f.read_text(encoding="utf-8").lstrip())
    ]
    assert not sin_docstring, f"escenarios sin docstring: {sin_docstring}"


def test_la_suite_cubre_los_cinco_escenarios_declarados() -> None:
    esperados = {
        "test_instalacion_limpia.py",
        "test_instalacion_brownfield.py",
        "test_wiring_propio.py",
        "test_configuracion.py",
        "test_ciclo_spec_first.py",
    }
    presentes = {f.name for f in ESCENARIOS.glob("test_*.py")}
    assert esperados <= presentes, f"faltan: {sorted(esperados - presentes)}"
