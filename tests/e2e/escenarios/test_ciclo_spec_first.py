"""El ciclo spec-first con commits reales, hooks reales y reset post-commit.

Automatiza [[SPEC-017-gate-decision-spec-first]] SC-004, que hasta ahora exigia
recorrer estos tres escenarios a mano en una carpeta sin versionar.

Defecto que este escenario detectaria si volviera (G-5): el criterio del gate
comparaba la **mtime** de la spec contra la de `.sdd/current-spec`. Eso hacia
imposible el segundo commit de una misma spec sin un `touch` ceremonial —el
escenario 2 de aca— y a la vez no detenia a nadie, porque una linea en blanco lo
satisfacia.
"""

from __future__ import annotations

from pathlib import Path

from ..lib import entorno
from ..lib.aserciones import dice, espera_exit, no_dice

CABECERA_DECLARACION = (
    "# Spec(s) vigente(s): una por linea, formato SPEC-NNN-slug.\n"
    "# Lo escribe la suite e2e; el reset post-commit lo limpia.\n"
)


def _declarar(destino: Path, *spec_ids: str) -> None:
    """Reescribe `.sdd/current-spec` con las specs indicadas (o ninguna)."""
    lineas = CABECERA_DECLARACION + "".join(f"{s}\n" for s in spec_ids)
    (destino / ".sdd" / "current-spec").write_text(lineas, encoding="utf-8")


def _declaradas(destino: Path) -> list[str]:
    texto = (destino / ".sdd" / "current-spec").read_text(encoding="utf-8")
    return [
        linea.strip()
        for linea in texto.splitlines()
        if linea.strip() and not linea.lstrip().startswith("#")
    ]


def _crear_spec(destino: Path, slug: str, titulo: str) -> Path:
    espera_exit(entorno.herramienta(destino, "sdd_spec", slug, f"--title={titulo}"))
    specs = sorted(destino.glob(f"specs/SPEC-*-{slug}.md"))
    assert specs, f"sdd_spec no dejo el archivo de la spec '{slug}'"
    return specs[0]


def _escribir_requisitos(spec: Path, requisito: str) -> None:
    """Convierte los placeholders de la plantilla en un FR de verdad."""
    texto = spec.read_text(encoding="utf-8")
    marcador = "- **FR-001** MUST: ..."
    assert marcador in texto, f"la plantilla de {spec.name} cambio de placeholder"
    spec.write_text(
        texto.replace(marcador, f"- **FR-001** MUST: {requisito}"), encoding="utf-8"
    )


def _escribir_codigo(destino: Path, cuerpo: str) -> None:
    modulo = destino / "src" / "modulo.py"
    modulo.parent.mkdir(exist_ok=True)
    modulo.write_text(cuerpo, encoding="utf-8")


def test_escenario_1_spec_recien_creada_no_habilita(derivado_con_hooks: Path) -> None:
    destino = derivado_con_hooks
    spec = _crear_spec(destino, "capacidad-uno", "Capacidad uno")
    _escribir_codigo(destino, "def saldo(cuenta):\n    return cuenta\n")

    bloqueado = entorno.commitear(destino, "feat: capacidad uno")
    assert bloqueado.exit != 0, f"el commit no debio pasar{bloqueado.detalle()}"
    dice(bloqueado, spec.stem, "no tiene(n) requisitos")

    _escribir_requisitos(spec, "el modulo expone el saldo de una cuenta.")
    espera_exit(
        entorno.commitear(destino, "feat: capacidad uno"),
        porque="con los FR escritos el gate habilita",
    )


def test_escenario_2_misma_spec_en_varios_commits(derivado_con_hooks: Path) -> None:
    """Sin tocar la spec entre commits: es el flujo que el protocolo prescribe."""
    destino = derivado_con_hooks
    spec = _crear_spec(destino, "capacidad-uno", "Capacidad uno")
    _escribir_requisitos(spec, "el modulo expone el saldo de una cuenta.")
    _escribir_codigo(destino, "def saldo(cuenta):\n    return cuenta\n")
    espera_exit(entorno.commitear(destino, "feat: primera parte"))

    # El reset post-commit dejo la declaracion vacia.
    assert _declaradas(destino) == [], (
        "el reset post-commit no limpio .sdd/current-spec: "
        f"quedo {_declaradas(destino)}"
    )

    # SPEC-004 FR-008/SC-005: el archivo esta ignorado, no solo "limpio" -- no
    # debe aparecer en absoluto en git status tras el ciclo declarar->commit->reset.
    no_dice(
        espera_exit(entorno.git(destino, "status", "--porcelain")),
        "current-spec",
    )

    _declarar(destino, spec.stem)
    _escribir_codigo(destino, "def saldo(cuenta):\n    return cuenta * 2\n")
    espera_exit(
        entorno.commitear(destino, "feat: segunda parte"),
        porque="redeclarar la spec sin modificarla tiene que alcanzar",
    )


def test_escenario_3_dos_specs_con_commit_al_final(derivado_con_hooks: Path) -> None:
    destino = derivado_con_hooks
    una = _crear_spec(destino, "capacidad-uno", "Capacidad uno")
    _escribir_requisitos(una, "el modulo expone el saldo de una cuenta.")
    otra = _crear_spec(destino, "capacidad-dos", "Capacidad dos")

    _declarar(destino, una.stem, otra.stem)
    _escribir_codigo(destino, "def saldo(cuenta):\n    return cuenta\n")

    bloqueado = entorno.commitear(destino, "feat: dos capacidades")
    assert bloqueado.exit != 0, f"el commit no debio pasar{bloqueado.detalle()}"
    dice(bloqueado, otra.stem, "no tiene(n) requisitos")
    assert una.stem not in bloqueado.salida.split("no tiene(n) requisitos")[0][-200:], (
        f"el motivo tendria que nombrar solo la spec incompleta{bloqueado.detalle()}"
    )

    _escribir_requisitos(otra, "el modulo informa el limite de una cuenta.")
    _declarar(destino, una.stem, otra.stem)
    espera_exit(entorno.commitear(destino, "feat: dos capacidades"))


def test_el_escape_hatch_permite_y_deja_rastro(derivado_con_hooks: Path) -> None:
    """`SDD_GATE_BYPASS` es la salida acotada; `--no-verify` apagaria todo.

    El rastro se exige en los dos planos: sobre el gate (FR-US3-004) y sobre la
    salida del commit (FR-US3-007). El segundo es el que fallaba: `pre-commit`
    descarta la salida de los hooks que pasan, y el gate pasa —imprimiendo el
    aviso— justo cuando el bypass saltea un bloqueo, asi que el operador veia un
    `Passed` mudo. Lo destapa `verbose: true` en el wiring (V-2 de IDEAS).
    """
    destino = derivado_con_hooks
    _declarar(destino)
    _escribir_codigo(destino, "def saldo(cuenta):\n    return cuenta\n")

    aviso = entorno.correr_gate(
        destino, "src/modulo.py", env={"SDD_GATE_BYPASS": "hotfix de produccion"}
    )
    espera_exit(aviso, porque="el bypass con motivo permite")
    dice(aviso, "SDD_GATE_BYPASS activo", "hotfix de produccion")

    sin_motivo = entorno.commitear(
        destino, "fix: sin spec", env={"SDD_GATE_BYPASS": ""}
    )
    assert sin_motivo.exit != 0, (
        f"un bypass vacio no habilita nada{sin_motivo.detalle()}"
    )

    commit = entorno.commitear(
        destino, "fix: sin spec", env={"SDD_GATE_BYPASS": "hotfix de produccion"}
    )
    espera_exit(commit, porque="con motivo, el commit sin spec declarada pasa")
    dice(commit, "SDD_GATE_BYPASS activo", "hotfix de produccion")
