"""Loader del SSOT de parametrizacion del proyecto (`.sdd/config.yaml`).

Todo el andamiaje SDD (validadores de proceso en `core/` y adaptadores de
lenguaje en `adapters/`) lee sus parametros de aqui, en vez de tener listas
hardcoded. Esto es lo que hace al kit agnostico: el mismo codigo sirve a
cualquier proyecto cambiando solo el config.

Esquema (ver examples/config/config.yaml para un ejemplo completo):

    project:   name, domain, language
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

# Marcadores que identifican la raiz de un proyecto con SDD instalado.
_ROOT_MARKERS = (
    CONFIG_RELPATH,
    Path("CONSTITUTION.md"),
    Path("specs") / "SPECS_REGISTRY.md",
)


def find_repo_root(start: Path | None = None) -> Path:
    """Sube desde `start` hasta encontrar un proyecto con SDD instalado."""
    origin = (start or Path.cwd()).resolve()
    for directory in (origin, *origin.parents):
        if any((directory / marker).exists() for marker in _ROOT_MARKERS):
            return directory
    return origin


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
    id: str
    title: str
    invariant: str = ""
    enforcement: str = ""
    detail: str = ""


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
        explicit = self.raw.get("dirs", {}).get("source_roots")
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
    @property
    def naming_prohibited(self) -> tuple[str, ...]:
        return tuple(str(x).lower() for x in self._naming.get("prohibited", []))

    @property
    def naming_allowed(self) -> frozenset[str]:
        return frozenset(str(x) for x in self._naming.get("allowed_identifiers", []))

    @property
    def naming_relax_in_tests(self) -> frozenset[str]:
        return frozenset(str(x).lower() for x in self._naming.get("relax_in_tests", []))

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
                )
            )
        return out

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
