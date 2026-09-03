"""Actualiza el andamiaje SDD vendorizado en un proyecto derivado, sin perder
lo que el dueño escribió o adaptó (SPEC-025, respaldo de la skill `sdd-update`).

Se corre **desde un clon del kit** apuntando al derivado — simétrico a
`sdd-init`, nunca al revés: la copia vendorizada del derivado aborta si se la
invoca (no tiene `templates/` al lado).

Por defecto solo muestra el plan (qué cambiaría) sin escribir un solo byte;
`--apply` lo aplica. `--diff` agrega el contenido de cada cambio.

Uso:
    python core/sdd_update.py [<target_dir>] [--target=<dir>] [--apply] [--diff]
"""

from __future__ import annotations

import difflib
import re
import shutil
import subprocess  # nosec B404 - corre el andamiaje del propio kit/destino
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sdd_catalog  # noqa: E402
import sdd_init  # noqa: E402
import sdd_lock  # noqa: E402
from sdd_config import (  # noqa: E402
    KIT_VERSION,
    VENDOR_PREFIX,
    forzar_salida_utf8,
    hash_bytes,
    is_kit_repo,
    load,
    write_text_lf,
)

KIT_ROOT = sdd_init.KIT_ROOT
USAGE = (
    "Uso: python core/sdd_update.py [<target_dir>] [--target=<dir>] [--apply] [--diff]"
)

_LABELS = {
    "sin_cambios": "sin cambios",
    "actualizar": "actualizar",
    "conflicto": "conflicto",
    "nuevo": "nuevo",
}


@dataclass
class Entrada:
    dst_rel: str
    decision: str
    contenido_kit: str | None = None
    contenido_disco: str | None = None


@dataclass
class Plan:
    plantillas: list[Entrada] = field(default_factory=list)
    retiradas: list[Entrada] = field(default_factory=list)
    semillas_nuevas: list[tuple[str, str]] = field(default_factory=list)  # (src, dst)
    borradas_por_dueno: list[str] = field(default_factory=list)
    kit_new_presentes: list[str] = field(default_factory=list)
    claves_config_faltantes: list[str] = field(default_factory=list)
    gitignore_faltantes: list[str] = field(default_factory=list)
    substitutions_cambiaron: bool = False

    def hay_cambios(self) -> bool:
        return bool(
            self.semillas_nuevas
            or self.borradas_por_dueno is None  # nunca True; documenta intencion
            or any(e.decision != "sin_cambios" for e in self.plantillas)
            or self.retiradas
        )


# -- construccion del plan --------------------------------------------------


def _claves_yaml(text: str) -> set[str]:
    """Rutas punteadas de las claves de un YAML simple (sin listas ni anclas).

    No es un parser de YAML: alcanza para comparar "que claves trae la
    referencia nueva que el config del dueño no tiene" (FR-US3-004), que es
    una lectura informativa, no una validación de esquema.
    """
    claves: set[str] = set()
    pila: list[tuple[int, str]] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or line.strip().startswith("-"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            continue
        clave = stripped.split(":", 1)[0].strip().strip('"').strip("'")
        if not clave or not re.match(r"^[A-Za-z_][\w]*$", clave):
            continue
        while pila and pila[-1][0] >= indent:
            pila.pop()
        ruta = ".".join([*(k for _, k in pila), clave])
        claves.add(ruta)
        pila.append((indent, clave))
    return claves


def construir_plan(
    kit_root: Path, target: Path, cfg, lock: sdd_lock.Lock | None
) -> Plan:
    plan = Plan()
    # La fecha con la que el kit resuelve sus plantillas es la de la
    # instalacion, no la de hoy (SPEC-014 FR-US2-009): comparar contra el lock
    # exige resolver con los mismos valores con los que se hasheo.
    today = (lock.substitutions.get("today") if lock else None) or sdd_init.hoy()
    catalogo = sdd_catalog.catalogo_plantillas()
    catalogo_dst = {dst for _src, dst in catalogo}

    for src_rel, dst_rel in catalogo:
        clase = sdd_catalog.clase_de(dst_rel)
        contenido_kit = sdd_init._substitute(
            (kit_root / "templates" / src_rel).read_text(encoding="utf-8"),
            cfg.name,
            cfg.domain,
            today,
        )
        if clase == sdd_catalog.Clase.SEMILLA:
            if not (target / dst_rel).exists():
                plan.semillas_nuevas.append((src_rel, dst_rel))
            continue
        if clase != sdd_catalog.Clase.PLANTILLA:
            continue
        hash_kit = hash_bytes(contenido_kit.encode("utf-8"))
        dst = target / dst_rel
        existe = dst.exists()
        contenido_disco = dst.read_text(encoding="utf-8") if existe else None
        hash_disco = hash_bytes(contenido_disco.encode("utf-8")) if existe else None
        hash_lock = lock.plantillas.get(dst_rel) if lock else None
        decision = sdd_catalog.decidir_plantilla(
            existe, hash_disco, hash_kit, hash_lock
        )
        if decision == "eliminada":
            plan.borradas_por_dueno.append(dst_rel)
            continue
        plan.plantillas.append(
            Entrada(dst_rel, decision, contenido_kit, contenido_disco)
        )

    if lock:
        for dst_rel, hash_lock_val in sorted(lock.plantillas.items()):
            if dst_rel in catalogo_dst:
                continue
            dst = target / dst_rel
            if not dst.exists():
                continue
            hash_disco = hash_bytes(dst.read_bytes())
            decision = (
                "retirada_eliminar"
                if hash_disco == hash_lock_val
                else "retirada_conflicto"
            )
            plan.retiradas.append(Entrada(dst_rel, decision))

    plan.kit_new_presentes = sorted(
        str(p.relative_to(target)).replace("\\", "/")
        for p in target.rglob(f"*{sdd_catalog.KIT_NEW_SUFFIX}")
    )

    referencia_nueva = (kit_root / "examples" / "config" / "config.yaml").read_text(
        encoding="utf-8"
    )
    config_dueno_path = target / ".sdd" / "config.yaml"
    config_dueno = (
        config_dueno_path.read_text(encoding="utf-8")
        if config_dueno_path.exists()
        else ""
    )
    plan.claves_config_faltantes = sorted(
        _claves_yaml(referencia_nueva) - _claves_yaml(config_dueno)
    )

    gitignore_kit = (kit_root / "templates" / "wiring" / ".gitignore").read_text(
        encoding="utf-8"
    )
    gitignore_dueno_path = target / ".gitignore"
    gitignore_dueno = (
        gitignore_dueno_path.read_text(encoding="utf-8")
        if gitignore_dueno_path.exists()
        else ""
    )
    lineas_kit = {
        s
        for s in (linea.strip() for linea in gitignore_kit.splitlines())
        if s and not s.startswith("#")
    }
    lineas_dueno = {linea.strip() for linea in gitignore_dueno.splitlines()}
    plan.gitignore_faltantes = sorted(lineas_kit - lineas_dueno)

    if lock and lock.substitutions:
        # Solo los valores del proyecto: la fecha del lock cambia con el
        # calendario y avisar por ella seria el mismo ruido que FR-US2-008
        # elimina, mudado de lugar (SPEC-014 FR-US2-009).
        actuales = {"project.name": cfg.name, "project.domain": cfg.domain}
        del_lock = {k: v for k, v in lock.substitutions.items() if k in actuales}
        plan.substitutions_cambiaron = del_lock != actuales

    return plan


# -- impresion ----------------------------------------------------------------


def _imprimir_diff(entrada: Entrada) -> None:
    antes = (entrada.contenido_disco or "").splitlines(keepends=True)
    despues = (entrada.contenido_kit or "").splitlines(keepends=True)
    diff = difflib.unified_diff(
        antes,
        despues,
        fromfile=f"{entrada.dst_rel} (disco)",
        tofile=f"{entrada.dst_rel} (kit)",
    )
    texto = "".join(diff)
    if texto:
        print(texto)


def imprimir_plan(plan: Plan, *, diff: bool) -> None:
    categorias: dict[str, list[str]] = {
        "sin cambios": [],
        "actualizar": [],
        "conflicto": [],
        "nuevo": [],
        "eliminado": [],
        "regenerar": [],
    }
    for e in plan.plantillas:
        categorias[_LABELS[e.decision]].append(e.dst_rel)
    for e in plan.retiradas:
        if e.decision == "retirada_eliminar":
            categorias["eliminado"].append(f"{e.dst_rel} (retirada del kit)")
        else:
            categorias["conflicto"].append(f"{e.dst_rel} (retirada del kit, editada)")
    for _src, dst in plan.semillas_nuevas:
        categorias["nuevo"].append(dst)
    categorias["regenerar"].append("tools/sdd/ (vendor: purga y recrea)")
    categorias["actualizar"].append(".sdd/config.reference.yaml (vendor)")
    categorias["regenerar"].append(
        "artefactos generados (render.py + gen_skill_adapters.py, tras el vendor)"
    )

    print("== Plan de actualización ==")
    resumen = ", ".join(f"{k}: {len(v)}" for k, v in categorias.items())
    print(f"  {resumen}")
    for etiqueta, items in categorias.items():
        if not items:
            continue
        print(f"\n  {etiqueta}:")
        for item in sorted(items):
            print(f"    - {item}")

    if plan.borradas_por_dueno:
        print("\n  Borradas por el dueño (no se reinstalan):")
        for rel in sorted(plan.borradas_por_dueno):
            print(f"    - {rel}")

    if plan.kit_new_presentes:
        print("\n  .kit-new de una corrida anterior (conflictos sin resolver):")
        for rel in plan.kit_new_presentes:
            print(f"    - {rel}")

    if plan.claves_config_faltantes:
        print("\n  Claves nuevas en config.reference.yaml que tu config no tiene:")
        for clave in plan.claves_config_faltantes:
            print(f"    - {clave}")

    if plan.gitignore_faltantes:
        print("\n  Líneas del .gitignore del kit que el tuyo no tiene:")
        for linea in plan.gitignore_faltantes:
            print(f"    - {linea}")

    if plan.substitutions_cambiaron:
        print(
            "\n  Los valores de sustitución (nombre/dominio) cambiaron desde la "
            "instalación: por eso se reescriben las plantillas intactas, aunque "
            "ninguna esté en conflicto."
        )

    if diff:
        print("\n== Diferencias ==")
        for e in plan.plantillas:
            if e.decision in ("actualizar", "conflicto", "nuevo"):
                _imprimir_diff(e)


# -- changelog ------------------------------------------------------------


_CHANGELOG_HEADING = re.compile(r"^##\s+([0-9][\w.\-]*)")


def leer_changelog(kit_root: Path) -> dict[str, str]:
    path = kit_root / "CHANGELOG.md"
    if not path.exists():
        return {}
    entradas: dict[str, str] = {}
    version_actual: str | None = None
    buffer: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _CHANGELOG_HEADING.match(line)
        if m:
            if version_actual is not None:
                entradas[version_actual] = "\n".join(buffer).strip()
            version_actual = m.group(1)
            buffer = []
            continue
        if version_actual is not None:
            buffer.append(line)
    if version_actual is not None:
        entradas[version_actual] = "\n".join(buffer).strip()
    return entradas


def _version_tuple(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(p) for p in v.split("."))
    except ValueError:
        return (0,)


def seleccionar_changelog(
    entradas: dict[str, str], version_instalada: str | None, version_kit: str
) -> tuple[list[str], str | None]:
    """FR-US4-002: qué entradas citar y por qué, sin I/O (testable sin CHANGELOG.md).

    Devuelve `(versiones_a_mostrar, motivo)`. `motivo` no es `None` solo
    cuando se cae al changelog completo: sin lock, o con una versión instalada
    que el changelog no registra."""
    if version_instalada is None:
        return sorted(
            entradas, key=_version_tuple
        ), "no hay lock: se desconoce la versión instalada."
    if version_instalada not in entradas:
        return (
            sorted(entradas, key=_version_tuple),
            f"la versión instalada ('{version_instalada}') no figura en el changelog.",
        )
    base = _version_tuple(version_instalada)
    tope = _version_tuple(version_kit)
    a_mostrar = [
        v
        for v in sorted(entradas, key=_version_tuple)
        if base < _version_tuple(v) <= tope
    ]
    return a_mostrar, None


def imprimir_changelog(kit_root: Path, lock: sdd_lock.Lock | None) -> None:
    entradas = leer_changelog(kit_root)
    if not entradas:
        return
    version_instalada = lock.kit_version if lock else None
    a_mostrar, motivo = seleccionar_changelog(entradas, version_instalada, KIT_VERSION)

    print("\n== Changelog ==")
    if motivo:
        print(f"  (mostrando el changelog completo: {motivo})")
    if not a_mostrar:
        print("  Sin cambios de versión que citar.")
        return
    requieren_accion = []
    for v in a_mostrar:
        texto = entradas[v]
        print(f"\n  ## {v}")
        for line in texto.splitlines():
            print(f"  {line}")
        if "Acción requerida" in texto:
            requieren_accion.append(v)
    if requieren_accion:
        print("\n  ATENCIÓN — versiones con cambios que exigen acción del dueño:")
        for v in requieren_accion:
            print(f"    - {v}")


# -- aplicacion -------------------------------------------------------------


def _doctor_problems(target: Path) -> list[str]:
    doctor = target / VENDOR_PREFIX / "core" / "sdd_doctor.py"
    if not doctor.exists():
        return []
    result = subprocess.run(  # nosec B603 - script del propio andamiaje
        [sys.executable, str(doctor)], cwd=str(target), capture_output=True, text=True
    )
    salida = result.stdout
    return [
        line.strip()[2:].strip()
        for line in salida.splitlines()
        if line.strip().startswith("x ")
    ]


def aplicar_plantillas(target: Path, kit_root: Path, plan: Plan) -> None:
    for e in plan.plantillas:
        dst = target / e.dst_rel
        kit_new = target / (e.dst_rel + sdd_catalog.KIT_NEW_SUFFIX)
        if e.decision in ("nuevo", "actualizar"):
            dst.parent.mkdir(parents=True, exist_ok=True)
            write_text_lf(dst, e.contenido_kit or "")
            if e.dst_rel in sdd_init._EXECUTABLE_WIRING:
                dst.chmod(0o755)
            if kit_new.exists():
                kit_new.unlink()
        elif e.decision == "conflicto":
            kit_new.parent.mkdir(parents=True, exist_ok=True)
            write_text_lf(kit_new, e.contenido_kit or "")
        elif e.decision == "sin_cambios" and kit_new.exists():
            kit_new.unlink()

    for e in plan.retiradas:
        if e.decision == "retirada_eliminar":
            (target / e.dst_rel).unlink(missing_ok=True)

    for src_rel, dst_rel in plan.semillas_nuevas:
        contenido = sdd_init._substitute(
            (kit_root / "templates" / src_rel).read_text(encoding="utf-8"),
            "",
            "",
            sdd_init.hoy(),
        )
        # Las semillas no llevan placeholders de nombre/dominio (son
        # `SPECS_REGISTRY.md`, `historial/sdd.md`, `.gitignore`,
        # `.sdd/current-spec`): se resuelven igual por si alguna lo tuviera.
        # La fecha si: `historial/sdd.md` abre con `{{today}}`, y una semilla
        # sembrada hoy se fecha hoy, no el dia de la instalacion original.
        dst = target / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        write_text_lf(dst, contenido)


def aplicar_plan(kit_root: Path, target: Path, cfg, plan: Plan) -> tuple[bool, str]:
    """Aplica el plan. Devuelve `(ok, motivo_si_fallo)`."""
    if cfg.language != "none":
        src_adapter = kit_root / "adapters" / cfg.language
        if not src_adapter.is_dir():
            return False, f"el kit nuevo no trae el adaptador de '{cfg.language}'."

    shutil.rmtree(target / "tools" / "sdd", ignore_errors=True)
    sdd_init._vendor_kit(target, cfg.language, force=True)

    aplicar_plantillas(target, kit_root, plan)
    sdd_init._install_config_reference(target)

    core = target / VENDOR_PREFIX / "core"
    for script in ("render.py", "gen_skill_adapters.py"):
        result = subprocess.run(  # nosec B603 - script recien copiado al destino
            [sys.executable, str(core / script)],
            cwd=str(target),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            return False, (
                f"{script} falló regenerando en el destino. El andamiaje ya quedó "
                f"en la versión nueva; el lock NO se reescribió. Reintentá con: "
                f"python {VENDOR_PREFIX}/core/{script} (desde {target})"
            )
    return True, ""


# -- CLI ----------------------------------------------------------------------


@dataclass
class Opciones:
    target: Path
    apply: bool
    diff: bool


def _abortar(motivo: str) -> None:
    print(f"ERROR: {motivo}\n{USAGE}", file=sys.stderr)
    raise SystemExit(2)


def _parse_argv(argv: list[str]) -> Opciones:
    """Parseo estricto: lo que no se reconoce aborta (SPEC-025 FR-US3-005),
    mismo criterio que `sdd_init._parse_argv` (SPEC-003 FR-012)."""
    posicional: str | None = None
    target_flag: str | None = None
    apply_ = False
    diff = False

    resto = list(argv)
    while resto:
        arg = resto.pop(0)
        if not arg.startswith("--"):
            if posicional is not None:
                _abortar(f"destino repetido: '{posicional}' y '{arg}'")
            posicional = arg
            continue
        nombre, sep, valor = arg.partition("=")
        if nombre == "--apply":
            if sep:
                _abortar("--apply no lleva valor")
            apply_ = True
        elif nombre == "--diff":
            if sep:
                _abortar("--diff no lleva valor")
            diff = True
        elif nombre == "--target":
            if not sep:
                if not resto or resto[0].startswith("--"):
                    _abortar(f"{nombre} necesita un valor")
                valor = resto.pop(0)
            if not valor:
                _abortar(f"{nombre} necesita un valor")
            target_flag = valor
        else:
            _abortar(f"flag desconocido: {nombre}")

    if posicional is not None and target_flag is not None:
        if Path(posicional).resolve() != Path(target_flag).resolve():
            _abortar(f"dos destinos distintos: '{posicional}' y '{target_flag}'")
    elegido = target_flag if target_flag is not None else posicional
    target = Path(elegido).resolve() if elegido else Path.cwd()
    return Opciones(target=target, apply=apply_, diff=diff)


def main(argv: list[str]) -> int:
    opciones = _parse_argv(argv)
    target = opciones.target

    if not is_kit_repo(KIT_ROOT):
        print(
            "ERROR: sdd-update se corre desde un CLON DEL KIT (con templates/ al "
            "lado), no desde la copia vendorizada de un derivado. Cloná sdd-first "
            f"y corré: python core/sdd_update.py --target={target}",
            file=sys.stderr,
        )
        return 1

    if not (target / ".sdd" / "config.yaml").exists():
        print(
            f"ERROR: {target} no parece tener sdd-first instalado (falta "
            ".sdd/config.yaml). Usá sdd-init para instalarlo primero.",
            file=sys.stderr,
        )
        return 1

    if is_kit_repo(target):
        print(
            f"ERROR: {target} es el repo del propio kit; no hay nada que "
            "actualizar ahí (purgar tools/sdd/ no significa nada).",
            file=sys.stderr,
        )
        return 1

    try:
        import yaml  # noqa: PLC0415 - mismo diferido que sdd_config.load()

        yaml.safe_load((target / ".sdd" / "config.yaml").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - el motivo se le muestra al operador
        print(f"ERROR: {target}/.sdd/config.yaml no parsea: {exc}", file=sys.stderr)
        return 1
    try:
        cfg = load(target)
    except SystemExit as exc:
        print(
            f"ERROR: no se pudo leer {target}/.sdd/config.yaml: {exc}", file=sys.stderr
        )
        return 1

    try:
        lock = sdd_lock.load_lock(target)
    except sdd_lock.LockIlegible as exc:
        print(
            f"ERROR: {exc}\nSi es un conflicto de merge sin resolver, arreglalo. "
            "Si preferís correr en modo degradado (ninguna plantilla se pisa), "
            "borrá .sdd/kit.lock y volvé a correr sdd-update.",
            file=sys.stderr,
        )
        return 1

    if lock is not None and _version_tuple(lock.kit_version) > _version_tuple(
        KIT_VERSION
    ):
        print(
            f"ERROR: la versión instalada ('{lock.kit_version}') es posterior a la "
            f"del kit ('{KIT_VERSION}'). Este clon del kit está atrasado.",
            file=sys.stderr,
        )
        return 1

    if cfg.language != "none" and not (KIT_ROOT / "adapters" / cfg.language).is_dir():
        print(
            f"ERROR: el kit nuevo no trae el adaptador de '{cfg.language}'. "
            "Actualizar dejaría el derivado sin adaptador de lenguaje.",
            file=sys.stderr,
        )
        return 1

    plan = construir_plan(KIT_ROOT, target, cfg, lock)
    print(f"sdd-update sobre {target}")
    imprimir_plan(plan, diff=opciones.diff)
    imprimir_changelog(KIT_ROOT, lock)

    if not opciones.apply:
        print(
            "\n(plan únicamente: no se escribió nada. Corré con --apply para aplicarlo.)"
        )
        return 0

    print("\n== Aplicando ==")
    doctor_antes = _doctor_problems(target)
    ok, motivo = aplicar_plan(KIT_ROOT, target, cfg, plan)
    if not ok:
        print(f"ERROR: {motivo}", file=sys.stderr)
        return 1

    sdd_lock.write_lock(
        target,
        sdd_lock.build_lock(KIT_ROOT, target, cfg.name, cfg.domain, sdd_init.hoy()),
    )
    print(f"  lock reescrito: {target / sdd_lock.LOCK_RELPATH}")

    doctor_despues = _doctor_problems(target)
    delta = [p for p in doctor_despues if p not in doctor_antes]
    if delta:
        print("\nsdd-doctor reporta problemas nuevos tras actualizar:")
        for p in delta:
            print(f"  x {p}")
        return 1

    print("\nActualización aplicada. sdd-doctor no reporta problemas nuevos.")
    return 0


if __name__ == "__main__":
    forzar_salida_utf8()
    raise SystemExit(main(sys.argv[1:]))
