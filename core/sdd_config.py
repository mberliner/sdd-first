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

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - dependencia declarada
    raise SystemExit(
        "sdd-first requiere PyYAML para leer .sdd/config.yaml (pip install pyyaml)."
    ) from exc

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

# Prefijo de la linea con que un adaptador reporta la cobertura medida en la
# consulta `coverage-baseline` (SPEC-009 FR-US2-001). Igual que EXIT_OMITIDO,
# vive aca porque lo comparten los dos lados del contrato: el adaptador que la
# imprime y `core/sdd_coverage_baseline.py` que la lee.
COVERAGE_BASELINE_PREFIX = "SDD-COVERAGE-BASELINE"

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
    """Carga `.sdd/config.yaml` desde la raiz del proyecto (o la detecta)."""
    root = find_repo_root() if repo_root is None else Path(repo_root).resolve()
    config_path = root / CONFIG_RELPATH
    raw: dict[str, Any] = {}
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            raw = loaded
    return SddConfig(repo_root=root, raw=raw)
