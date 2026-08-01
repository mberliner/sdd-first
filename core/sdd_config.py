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
    layers:    {capa: [capas_que_puede_importar]}
    pipeline:  steps[]

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
        "sdd-kit requiere PyYAML para leer .sdd/config.yaml (pip install pyyaml)."
    ) from exc

CONFIG_RELPATH = Path(".sdd") / "config.yaml"

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


@dataclass(frozen=True)
class Principle:
    id: str
    title: str
    invariant: str = ""
    enforcement: str = ""
    detail: str = ""


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
        return roots or ["src"]

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

    # -- pipeline --------------------------------------------------------------
    @property
    def pipeline_steps(self) -> list[str]:
        value = self.raw.get("pipeline", {})
        steps = value.get("steps") if isinstance(value, dict) else None
        return [str(x) for x in steps] if isinstance(steps, list) else []


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
