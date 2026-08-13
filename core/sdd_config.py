"""Loader del SSOT de parametrizacion del proyecto (`.sdd/config.yaml`).

Todo el andamiaje SDD (validadores de proceso en `core/` y adaptadores de
lenguaje en `adapters/`) lee sus parametros de aqui, en vez de tener listas
hardcoded. Esto es lo que hace al kit agnostico: el mismo codigo sirve a
cualquier proyecto cambiando solo el config.

Esquema (ver examples/config/config.yaml para un ejemplo completo):

    project:   name, domain, language, default_branch
    dirs:      domain, application, adapters, ui, tests_unit, source_roots
    naming:    prohibited[], allowed_identifiers[], relax_in_tests[]
    principles: [{id, title, invariant, enforcement, detail}]
    constitution: version, ratified, amended
    layers:    {capa: [capas_que_puede_importar]}
    pipeline:  steps[], coverage[{paths[], min}]

El loader no valida semantica (eso lo hacen los checks); solo carga y expone
accesos tipados con defaults razonables para que un config parcial no rompa.
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - se reporta al usar load()
    yaml = None  # type: ignore[assignment]

_SIN_PYYAML = (
    "sdd-first requiere PyYAML para leer .sdd/config.yaml (pip install pyyaml)."
)

CONFIG_RELPATH = Path(".sdd") / "config.yaml"

# Defaults compartidos cuando el config no declara la carpeta explicitamente.
DEFAULT_SOURCE_ROOT = "src"
DEFAULT_TESTS_UNIT = "tests/unit"
DEFAULT_CONSTITUTION_VERSION = "0.1.0"
DEFAULT_BRANCH = "main"

# Defaults del triage de solape entre specs (SPEC-022 FR-US2-006/009). Son
# estructurales y neutros a proposito: el vocabulario que hay que ignorar
# depende del dominio, asi que `stopwords` nace vacia y cada proyecto --el kit
# incluido-- siembra la suya en `.sdd/config.yaml`. Hardcodear aca las palabras
# del dominio del kit seria la clase de lista que el Principio I manda al config.
DEFAULT_TRIAGE_MIN_WORD_LEN = 4
DEFAULT_TRIAGE_MIN_MATCHES = 2

# Tercer estado del contrato de adaptador (SPEC-003 FR-009, SPEC-001 FR-005):
# el paso no se pudo verificar (sin targets, sin tool, sin umbrales) y eso NO es
# ni un pase ni una falla. Vive aca porque lo comparten los dos lados del
# contrato: `core/pipeline.py` que agrega y `adapters/*/adapter.py` que reporta.
# Contrato completo en adapters/CONTRACT.md.
EXIT_OMITIDO = 3

# Cuarto estado, este solo de los pasos de proceso (SPEC-020 FR-US2-003): el
# paso verifico lo suyo, pero algo que su verificacion presupone no ocurrio en
# la corrida, asi que su verde no puede afirmar todo lo que afirmaria. Hoy lo
# usa `check_constitution.py` para un principio cuyo paso de enforcement no se
# ejecuto. No es falla -- no pone el pipeline en ROJO ni cambia su exit code --
# ni omision -- el paso si corrio y cuenta entre los OK.
EXIT_RESERVAS = 4

# Prefijo de la linea con que un adaptador reporta la cobertura medida en la
# consulta `coverage-baseline` (SPEC-009 FR-US2-001). Igual que EXIT_OMITIDO,
# vive aca porque lo comparten los dos lados del contrato: el adaptador que la
# imprime y `core/sdd_coverage_baseline.py` que la lee.
COVERAGE_BASELINE_PREFIX = "SDD-COVERAGE-BASELINE"

# Variable de entorno con la ruta de un reporte de cobertura compartido entre
# los pasos `tests` y `coverage` de una misma corrida de `core/pipeline.py`
# (SPEC-009 FR-US3-001). `core/pipeline.py` la crea una vez por invocacion y la
# pasa a los pasos de codigo; el adaptador la usa para correr pytest
# instrumentado una sola vez en `tests` y evaluar los umbrales de `coverage`
# leyendo ese reporte en vez de correr pytest de nuevo. Sin la variable (paso
# invocado suelto, fuera de un pipeline completo) cada paso corre pytest por su
# cuenta, como siempre. Vive aca porque la comparten `core/pipeline.py` y el
# adaptador, los dos lados del contrato.
PIPELINE_COVERAGE_CACHE_ENV = "SDD_PIPELINE_COVERAGE_CACHE"

# Variable de entorno con los pasos que ya se EJECUTARON en la corrida en curso
# de `core/pipeline.py`, separados por coma (SPEC-020 FR-US2-001). Ejecutado es
# "corrio, con cualquier resultado": no entran los omitidos (no verificaron
# nada) ni los todavia pendientes (declarados despues). La consume
# `check_constitution.py` para saber si el paso que enforza cada principio
# llego a correr; sin la variable -- check invocado suelto -- no evalua
# ejecucion. Mismo patron y mismo degradado que PIPELINE_COVERAGE_CACHE_ENV, y
# vive aca por el mismo motivo: la comparten los dos lados del canal.
PIPELINE_STEPS_RUN_ENV = "SDD_PIPELINE_STEPS_RUN"

# Marcadores que identifican la raiz de un proyecto con SDD instalado.
_ROOT_MARKERS = (
    CONFIG_RELPATH,
    Path("CONSTITUTION.md"),
    Path("specs") / "SPECS_REGISTRY.md",
)


def find_sdd_root(start: Path | None = None) -> Path | None:
    """Raiz del proyecto SDD que contiene a `start`, o None si no hay ninguna.

    Resolucion estricta: quien pregunta decide que hacer con el None. La usa el
    gate, que ante una raiz irresoluble debe fallar CERRADO (SPEC-014 FR-US1-003)
    en vez de operar sobre un directorio cualquiera.
    """
    origin = (start or Path.cwd()).resolve()
    for directory in (origin, *origin.parents):
        if any((directory / marker).exists() for marker in _ROOT_MARKERS):
            return directory
    return None


def find_repo_root(start: Path | None = None) -> Path:
    """Sube desde `start` hasta encontrar un proyecto con SDD instalado.

    Variante tolerante: sin marcadores devuelve el propio punto de partida. Es
    lo que necesitan `pipeline`, `render` y `doctor` (corren *dentro* del
    proyecto y su peor caso es reportar que faltan artefactos), no el gate.
    """
    return find_sdd_root(start) or (start or Path.cwd()).resolve()


# Wiring que cablea el gate, y la invocacion que delata que esta puesto de
# verdad (SPEC-014 FR-US1-002). SSOT unico: `sdd_doctor` lo verifica y
# `sdd_init` avisa cuando conserva alguno preexistente del proyecto. Un archivo
# con el nombre correcto no prueba nada -- el testigo de la campana traia un
# `.pre-commit-config.yaml` propio con solo `ruff` y el doctor lo daba por bueno.
GATE_WIRING = {
    ".claude/settings.json": "sdd_gate_hook.sh",
    ".agents/hooks.json": "sdd_gate_hook.sh",
    ".pre-commit-config.yaml": "sdd_gate.py",
}


# Vocabulario de pasos de codigo del contrato de adaptador (SPEC-005 FR-006).
# Vive en el nucleo y no en el adaptador porque es el *contrato*
# (adapters/CONTRACT.md) el que reserva estos nombres: lo que aporta el lenguaje
# es la implementacion de cada paso, no la lista. `core/pipeline.py` lo importa y
# un unitario lo cruza contra el dispatcher del adaptador en las dos direcciones.
# Sin esa atadura, un paso implementado y no declarado queda como "paso
# desconocido" que el pipeline descuenta del total sin ruido (C-8 de IDEAS: le
# paso a `integration` al nacer).
CODE_STEPS = (
    "naming",
    "layers",
    "lint",
    "format",
    "types",
    "security",
    "tests",
    "integration",
    "coverage",
    "e2e",
)


@dataclass(frozen=True)
class TestDir:
    """Que es y como se trata una carpeta de tests declarada en `dirs`."""

    step: str
    """Paso de `pipeline.steps` que la ejecuta (SPEC-019 FR-US2-002)."""

    medida: bool = True
    """Si entra a la corrida del paso `coverage` (SPEC-018 FR-US3-002).

    False para las suites que manejan el producto **por subproceso**: no aportan
    una sola linea medida en proceso, asi que incluirlas en la corrida de
    cobertura solo las volveria a ejecutar. No es una preferencia sobre que
    merece medirse: es que ahi no hay nada que medir.
    """


# SSOT de las carpetas de tests que el kit conoce (SPEC-005 FR-007). Antes esto
# era `TEST_DIR_STEP`, que respondia una sola de las preguntas, y las otras cuatro
# quedaban como tuplas `("tests_unit", "tests_integration")` repetidas en el
# adaptador, `check_naming`, `render` y este modulo. La lista plana obligaba a que
# toda carpeta respondiera igual a todas las preguntas: por eso agregar una clase
# nueva de test no era un renglon sino una revision de cuatro criterios.
TEST_DIRS = {
    "tests_unit": TestDir(step="tests"),
    "tests_integration": TestDir(step="integration"),
    "tests_e2e": TestDir(step="e2e", medida=False),
}


def declared_test_dirs(*, solo_medidas: bool = False) -> tuple[str, ...]:
    """Claves de `dirs` que declaran carpetas de tests, en orden de declaracion.

    Con `solo_medidas`, unicamente las que entran a la corrida de cobertura: es
    la distincion entre "carpeta que los pasos estaticos miran" --ante la duda
    miran de mas y no rompen nada-- y "carpeta que un paso ejecuta".
    """
    return tuple(
        clave for clave, meta in TEST_DIRS.items() if not solo_medidas or meta.medida
    )


def colapsar_a_raiz_comun(dirs: Sequence[str]) -> list[str]:
    """Reemplaza las carpetas dadas por la raiz que las contiene a todas.

    Blancos de los pasos **estaticos** (SPEC-019 FR-US4-001): las claves de
    `dirs` apuntan a subcarpetas (`tests/unit`, `tests/integration`), asi que la
    infraestructura compartida que vive en la raiz --`conftest.py`, fixtures,
    helpers-- no caia dentro de ninguna y no la miraba ningun paso.

    Colapsar en vez de sumar la raiz: pasar `tests` junto a `tests/unit` deja al
    paso visitando la subcarpeta dos veces, y cada violacion se reportaria
    duplicada en la salida que lee el operador (FR-US4-002).

    Se devuelve `dirs` sin tocar cuando no hay una raiz *propia* que colapsar
    (FR-US4-003): con una sola carpeta, subir a su ancestro ensancharia el
    alcance a carpetas hermanas que el proyecto nunca declaro; con carpetas en
    arboles distintos (`pruebas/unit` y `e2e`) el unico ancestro comun es el
    repo entero, y barrerlo porque el layout es inusual seria peor que el
    agujero que esto tapa.

    No aplica a los pasos que **ejecutan** tests: darles la raiz le haria correr
    al paso `tests` la suite de integracion (FR-US4-005), que es el defecto que
    abrio esta spec, al reves.
    """
    if len(dirs) < 2:
        return list(dirs)
    partes = [PurePosixPath(d.replace("\\", "/")).parts for d in dirs]
    comun: list[str] = []
    # strict=False a proposito: las rutas tienen profundidades distintas y lo
    # que se busca es el prefijo comun, asi que cortar en la mas corta es el
    # comportamiento correcto, no un descuido.
    for tramo in zip(*partes, strict=False):
        if len(set(tramo)) != 1:
            break
        comun.append(tramo[0])
    if not comun:
        return list(dirs)
    raiz = "/".join(comun)
    # La raiz coincide con una carpeta declarada: ya las contiene a todas y no
    # hay nada que colapsar mas alla de deduplicar.
    return [raiz]


def script_hint(module_file: str | Path, repo_root: Path) -> str:
    """Ruta invocable de un script del andamiaje, relativa a la raiz del repo.

    Los mensajes de runtime que dicen "corre: python core/render.py" son falsos
    en un derivado, donde el andamiaje vive en `tools/sdd/core/`. Sale de la
    ubicacion real del modulo en vez del config: es exacta por construccion
    (SPEC-014 FR-US2-002).
    """
    path = Path(module_file).resolve()
    try:
        return path.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        # El andamiaje corre desde fuera del repo (kit clonado aparte): el
        # nombre del script solo es lo mejor que se puede afirmar con certeza.
        return path.name


# Prefijo bajo el que `sdd-init` vendoriza el andamiaje en un proyecto derivado.
VENDOR_PREFIX = "tools/sdd"

# Versión del propio andamiaje (SPEC-025 FR-US1-001). Viaja vendorizada bajo
# `{{sdd.core}}`: un derivado puede afirmar qué versión tiene sin el clon del
# kit al lado. Independiente de `constitution_version`: son dos líneas de
# versionado distintas (andamiaje vs. principios) que no tiene sentido atar.
# Cada versión publicada necesita su entrada en `CHANGELOG.md`
# (tests/unit/test_changelog.py lo exige).
KIT_VERSION = "0.1.0"


def is_kit_repo(repo_root: Path) -> bool:
    """True si `repo_root` es el repo del kit (no un proyecto instalado).

    El kit se distingue por tener la carpeta `templates/`: un proyecto
    instalado con `sdd-init` recibe los documentos ya resueltos, nunca las
    plantillas. Es la misma senal que usa `render.py` para decidir si
    sincroniza los docs duplicados (SPEC-005).
    """
    return (repo_root / "templates").is_dir()


def kit_path_tokens(repo_root: Path) -> dict[str, str]:
    """Resolucion de los placeholders de ruta del andamiaje (SPEC-010 FR-007).

    La unica diferencia estructural entre el kit y un proyecto instalado es
    donde vive el andamiaje: en el kit es `core/` y `adapters/`; en el destino,
    `tools/sdd/core/` y `tools/sdd/adapters/`. Las plantillas escriben
    `{{sdd.core}}` / `{{sdd.adapters}}` y cada consumidor resuelve lo suyo, en
    vez de mantener dos copias del mismo documento.
    """
    if is_kit_repo(repo_root):
        return {"{{sdd.core}}": "core", "{{sdd.adapters}}": "adapters"}
    return {
        "{{sdd.core}}": f"{VENDOR_PREFIX}/core",
        "{{sdd.adapters}}": f"{VENDOR_PREFIX}/adapters",
    }


# Fallback del header de `.sdd/current-spec` para cuando no hay `templates/`
# (proyecto derivado): mismo texto que `templates/wiring/current-spec`, con
# `{{sdd.core}}` como placeholder de `.format(core=...)`. Un test de paridad
# (tests/unit/test_current_spec_no_versionado.py) evita que diverjan en
# silencio -- mismo patron que la duplicacion inevitable de `source_roots`
# entre capas (docs/IDEAS.md G-1).
CURRENT_SPEC_FALLBACK_HEADER = (
    "# Spec(s) vigente(s): una por línea, formato SPEC-NNN-slug.\n"
    "# El gate spec-first ({core}/sdd_gate.py) exige que cada spec listada aquí\n"
    "# exista, esté registrada con estado vigente y tenga sus requisitos (FR) escritos.\n"
    "# Vacío = ninguna edición de código fuente permitida.\n"
)


def seed_current_spec(repo_root: Path) -> bool:
    """Siembra `.sdd/current-spec` con el header si falta (SPEC-004 FR-008).

    El archivo dejo de versionarse -- es estado de sesion local, no un
    artefacto instalado -- asi que un `git clone` fresco no lo trae. No pisa
    un archivo ya existente (podria tener una spec declarada). Devuelve True
    si lo creo.
    """
    path = repo_root / ".sdd" / "current-spec"
    if path.exists():
        return False
    core_token = kit_path_tokens(repo_root)["{{sdd.core}}"]
    template = repo_root / "templates" / "wiring" / "current-spec"
    if template.exists():
        text = template.read_text(encoding="utf-8").replace("{{sdd.core}}", core_token)
    else:
        text = CURRENT_SPEC_FALLBACK_HEADER.format(core=core_token)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(path, text)
    return True


# Linea que `.gitignore` debe tener para que `.sdd/current-spec` (estado de
# sesion local, SPEC-004 FR-008) nunca vuelva a trackearse.
GITIGNORE_CURRENT_SPEC_LINE = ".sdd/current-spec"


def _gitignore_lines(text: str) -> set[str]:
    return {line.strip() for line in text.splitlines()}


def gitignore_has_current_spec_line(gitignore_path: Path) -> bool:
    """True si `gitignore_path` ya tiene la linea que ignora `.sdd/current-spec`."""
    if not gitignore_path.exists():
        return False
    text = gitignore_path.read_text(encoding="utf-8")
    return GITIGNORE_CURRENT_SPEC_LINE in _gitignore_lines(text)


def ensure_gitignore_current_spec(gitignore_path: Path) -> bool:
    """Agrega la linea de `.sdd/current-spec` a un `.gitignore` que no la tenga
    (SPEC-004 FR-009), sin pisar el resto del archivo.

    `sdd_init.py` conserva sin tocar cualquier `.gitignore` ya presente en el
    target -- el caso realista, porque casi todo proyecto ya tiene uno. Sin
    este paso esa conservacion neutralizaria FR-008: la linea nunca se
    agregaria y `.sdd/current-spec` volveria a trackearse. No crea el archivo
    si no existe (eso lo cubre la copia normal de `WIRING` en una instalacion
    fresca). Devuelve True si modifico el archivo.
    """
    if not gitignore_path.exists():
        return False
    if gitignore_has_current_spec_line(gitignore_path):
        return False
    text = gitignore_path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    text += (
        "\n# Puntero de sesion local del gate spec-first (SPEC-004 FR-008/FR-009):\n"
        f"{GITIGNORE_CURRENT_SPEC_LINE}\n"
    )
    write_text_lf(gitignore_path, text)
    return True


def forzar_salida_utf8() -> None:
    """Emite `stdout`/`stderr` en UTF-8 sea cual sea la codificacion del sistema.

    En Windows, un proceso cuya salida no es una consola UTF-8 cae a `cp1252`:
    todo el texto acentuado del kit sale ilegible (`VERDE �`, `agn�stica`) o
    aborta con `UnicodeEncodeError`. Lo llama cada entrypoint al arrancar
    (SPEC-012 FR-005); el test lo verifica por barrido, no por convencion.

    Tolera streams sin `reconfigure` (los que instala pytest al capturar la
    salida, o un stream ya envuelto): ahi no hay codificacion que forzar.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def hash_bytes(data: bytes) -> str:
    """`sha256` hexdigest de `data`. Vive acá (y no en `sdd_lock`) porque lo usan
    `sdd_init` y `sdd_lock` por igual, y `sdd_lock` ya importa a `sdd_init` para
    reusar `_substitute` -- ponerlo del otro lado crearia un ciclo."""
    return hashlib.sha256(data).hexdigest()  # nosec B324 - integridad, no criptografía


def write_text_lf(path: Path, text: str) -> None:
    """Escribe `text` en UTF-8 forzando fin de linea LF (determinismo en
    Windows). `Path.write_text` no admite `newline=`; solo `Path.open` lo
    admite."""
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


@dataclass(frozen=True)
class Principle:
    """Un principio de la constitucion (SPEC-020 FR-001).

    `step` es opcional y nombra el paso de `pipeline.steps` que activa su
    enforcement. Sin `step`, el cableado no se verifica contra el pipeline: es la
    forma de declarar un enforcement que corre por otra via (hooks, convencion).
    """

    id: str
    title: str
    invariant: str = ""
    enforcement: str = ""
    detail: str = ""
    step: str = ""


def _entero(valor: Any, default: int) -> int:
    """`valor` como entero positivo, o `default` si no lo es.

    Un umbral con typo no puede volver ilegible el proyecto: mismo criterio que
    `pipeline_coverage` con sus entradas malformadas.
    """
    try:
        entero = int(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return entero if entero > 0 else default


@dataclass(frozen=True)
class TriageConfig:
    """Parametros del triage de solape entre specs (SPEC-022 FR-US2-006).

    `stopwords` son las palabras que no señalan solape por si solas --el
    vocabulario que todo titulo del dominio comparte--; `min_word_len` descarta
    las cortas; `min_matches` es cuantas palabras tienen que coincidir para
    marcar candidata a una spec.
    """

    stopwords: frozenset[str] = frozenset()
    min_word_len: int = DEFAULT_TRIAGE_MIN_WORD_LEN
    min_matches: int = DEFAULT_TRIAGE_MIN_MATCHES


@dataclass(frozen=True)
class CoverageTarget:
    """Umbral de cobertura para un conjunto de carpetas (SPEC-009 FR-001).

    `paths` se miden juntas contra `minimum`. Varias entradas expresan
    exigencias distintas por capa (p. ej. dominio mas estricto que el resto).
    """

    paths: tuple[str, ...]
    minimum: int


@dataclass(frozen=True)
class SddConfig:
    """Vista tipada de `.sdd/config.yaml`, con defaults tolerantes."""

    repo_root: Path
    raw: dict[str, Any] = field(default_factory=dict)

    # -- project ---------------------------------------------------------------
    @property
    def name(self) -> str:
        return str(self._project.get("name", self.repo_root.name))

    @property
    def domain(self) -> str:
        return str(self._project.get("domain", ""))

    @property
    def language(self) -> str:
        return str(self._project.get("language", "none")).lower()

    @property
    def default_branch(self) -> str:
        """Rama en la que dispara el CI generado (SPEC-014 FR-US2-005)."""
        return str(self._project.get("default_branch") or DEFAULT_BRANCH)

    @property
    def _project(self) -> dict[str, Any]:
        value = self.raw.get("project", {})
        return value if isinstance(value, dict) else {}

    # -- dirs ------------------------------------------------------------------
    @property
    def dirs(self) -> dict[str, str]:
        value = self.raw.get("dirs", {})
        return (
            {str(k): str(v) for k, v in value.items()}
            if isinstance(value, dict)
            else {}
        )

    @property
    def source_roots(self) -> list[str]:
        """Carpetas que el gate spec-first considera 'codigo fuente'.

        Por defecto: la union de las capas declaradas en `dirs` (sin tests) o,
        si se declara explicitamente `dirs.source_roots`, esa lista.
        """
        # `or {}`: un `dirs:` presente pero sin claves (todo comentado, como lo
        # siembra sdd-init sin layout detectado) parsea a None, no a dict.
        explicit = (self.raw.get("dirs") or {}).get("source_roots")
        if isinstance(explicit, list) and explicit:
            return [str(x) for x in explicit]
        roots: list[str] = []
        for key, path in self.dirs.items():
            if key in {"tests_unit", "tests_integration", "source_roots"}:
                continue
            top = Path(path).parts[0] if path else path
            if top and top not in roots:
                roots.append(top)
        return roots or [DEFAULT_SOURCE_ROOT]

    # -- naming ----------------------------------------------------------------
    def _naming_list(self, key: str) -> list[Any]:
        """Lista del bloque `naming`, tolerante a clave vacia o malformada.

        SPEC-021 FR-001/FR-003: `prohibited:` sin items lo carga YAML como `None`
        —la forma natural de desactivar la regla sin borrar la clave— y iterarlo
        reventaba el paso `naming` con un TypeError, tapando el aviso de "nada
        que verificar" que el propio consumidor ya tenia escrito. Ausente, vacia
        y malformada colapsan al mismo resultado. La guarda vive aca y no
        repetida en cada propiedad para que una lista nueva la herede.
        """
        value = self._naming.get(key)
        return list(value) if isinstance(value, (list, tuple)) else []

    @property
    def naming_prohibited(self) -> tuple[str, ...]:
        return tuple(str(x).lower() for x in self._naming_list("prohibited"))

    @property
    def naming_allowed(self) -> frozenset[str]:
        return frozenset(str(x) for x in self._naming_list("allowed_identifiers"))

    @property
    def naming_relax_in_tests(self) -> frozenset[str]:
        return frozenset(str(x).lower() for x in self._naming_list("relax_in_tests"))

    @property
    def _naming(self) -> dict[str, Any]:
        value = self.raw.get("naming", {})
        return value if isinstance(value, dict) else {}

    # -- principles ------------------------------------------------------------
    @property
    def principles(self) -> list[Principle]:
        out: list[Principle] = []
        for item in self.raw.get("principles", []) or []:
            if not isinstance(item, dict):
                continue
            out.append(
                Principle(
                    id=str(item.get("id", "")),
                    title=str(item.get("title", "")),
                    invariant=str(item.get("invariant", "")),
                    enforcement=str(item.get("enforcement", "")),
                    detail=str(item.get("detail", "")),
                    step=str(item.get("step", "")),
                )
            )
        return out

    @property
    def enforcement_steps(self) -> dict[str, str]:
        """Mapa token de enforcement -> paso que lo activa (SPEC-020 FR-002).

        La clave es el basename del `enforcement` del principio, porque en la
        constitucion se escribe con ruta (`adapters/python/check_naming.py`) y
        aca interesa la tool. Antes esto era un dict hardcodeado en
        `check_constitution.py`, con el efecto de que un principio propio no
        obtenia verificacion de cableado (E-4 de docs/IDEAS.md).
        """
        out: dict[str, str] = {}
        for p in self.principles:
            if not p.enforcement or not p.step:
                continue
            basename = p.enforcement.rsplit("/", 1)[-1]
            if basename in out:
                raise ValueError(
                    f"Colisión de enforcement: '{basename}' está declarado "
                    "más de una vez en principles."
                )
            out[basename] = p.step
        return out

    # -- specs -----------------------------------------------------------------
    @property
    def triage(self) -> TriageConfig:
        """Parametros de `specs.triage`, con defaults tolerantes.

        La seccion ausente, declarada vacia o malformada cae a los defaults sin
        romper nada (SPEC-022 FR-US2-009, invariante de SPEC-021): `triage:` sin
        claves lo carga YAML como `None`.
        """
        raw = self.raw.get("specs")
        specs = raw if isinstance(raw, dict) else {}
        triage = specs.get("triage")
        triage = triage if isinstance(triage, dict) else {}
        palabras = triage.get("stopwords")
        stopwords = (
            frozenset(str(x).lower() for x in palabras)
            if isinstance(palabras, (list, tuple))
            else frozenset()
        )
        return TriageConfig(
            stopwords=stopwords,
            min_word_len=_entero(
                triage.get("min_word_len"), DEFAULT_TRIAGE_MIN_WORD_LEN
            ),
            min_matches=_entero(triage.get("min_matches"), DEFAULT_TRIAGE_MIN_MATCHES),
        )

    # -- layers ----------------------------------------------------------------
    @property
    def layers(self) -> dict[str, list[str]]:
        value = self.raw.get("layers", {})
        if not isinstance(value, dict):
            return {}
        return {str(k): [str(x) for x in (v or [])] for k, v in value.items()}

    # -- rutas del andamiaje ---------------------------------------------------
    @property
    def kit_paths(self) -> dict[str, str]:
        """Placeholders de ruta ya resueltos para este repo (SPEC-010 FR-007)."""
        return kit_path_tokens(self.repo_root)

    def resolve_kit_paths(self, text: str) -> str:
        """Sustituye `{{sdd.core}}` / `{{sdd.adapters}}` en `text`."""
        for token, value in self.kit_paths.items():
            text = text.replace(token, value)
        return text

    # -- constitution ----------------------------------------------------------
    @property
    def constitution_version(self) -> str:
        return str(self._constitution.get("version", DEFAULT_CONSTITUTION_VERSION))

    @property
    def constitution_ratified(self) -> str:
        """Fecha de ratificacion; vacio => el renderer usa la fecha de hoy."""
        return str(self._constitution.get("ratified", "") or "")

    @property
    def constitution_amended(self) -> str:
        """Fecha de ultima enmienda; vacio => el renderer usa la fecha de hoy."""
        return str(self._constitution.get("amended", "") or "")

    @property
    def _constitution(self) -> dict[str, Any]:
        value = self.raw.get("constitution", {})
        return value if isinstance(value, dict) else {}

    # -- pipeline --------------------------------------------------------------
    @property
    def pipeline_steps(self) -> list[str]:
        value = self._pipeline.get("steps")
        return [str(x) for x in value] if isinstance(value, list) else []

    @property
    def pipeline_coverage(self) -> list[CoverageTarget]:
        """Umbrales de cobertura declarados (SPEC-009 FR-004).

        Opcional por diseno: ausente o vacio => el paso `coverage` se omite con
        aviso. Las entradas malformadas (sin `paths` o sin `min` numerico) se
        descartan en silencio en vez de romper el pipeline: el config es un
        SSOT editado a mano y un typo no debe volver ilegible el proyecto.
        """
        raw = self._pipeline.get("coverage")
        if not isinstance(raw, list):
            return []
        out: list[CoverageTarget] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            paths = item.get("paths")
            if isinstance(paths, str):
                paths = [paths]
            if not isinstance(paths, list) or not paths:
                continue
            try:
                minimum = int(item.get("min"))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            out.append(
                CoverageTarget(paths=tuple(str(p) for p in paths), minimum=minimum)
            )
        return out

    @property
    def _pipeline(self) -> dict[str, Any]:
        value = self.raw.get("pipeline", {})
        return value if isinstance(value, dict) else {}


@lru_cache(maxsize=8)
def load(repo_root: Path | None = None) -> SddConfig:
    """Carga `.sdd/config.yaml` desde la raiz del proyecto (o la detecta).

    PyYAML se exige aca y no al importar el modulo: importarlo es lo que hace
    todo entrypoint para acceder a los helpers de stdlib (`forzar_salida_utf8`,
    `find_repo_root`, `write_text_lf`), y varios corren en entornos sin
    dependencias -- los hooks de pre-commit, sin ir mas lejos. Que solo falle
    quien de verdad necesita leer el config es ademas lo que ya asumian
    `sdd_gate._source_roots` y `spec_index`, que capturan este SystemExit para
    degradar en vez de romperse.
    """
    if yaml is None:
        raise SystemExit(_SIN_PYYAML)
    root = find_repo_root() if repo_root is None else Path(repo_root).resolve()
    config_path = root / CONFIG_RELPATH
    raw: dict[str, Any] = {}
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            raw = loaded
    return SddConfig(repo_root=root, raw=raw)
