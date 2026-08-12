"""Indice invertido archivo -> specs, y triage de solape (SPEC-022 US2/US3).

Responde dos preguntas que hoy solo sabia contestar un humano leyendo el
registro: *que specs ya gobiernan este archivo* y *que specs vigentes se solapan
con esta capacidad*. Las usa `sdd_spec.py` antes de crear una spec (triage) y
`sdd_gate.py` cuando bloquea una edicion (aviso de reuso).

El indice se deriva de tres fuentes que ya viven en el repositorio, sin pedir
metadatos nuevos (FR-US2-001):

1. las rutas nombradas en la seccion *Key Entities* de cada spec vigente,
2. las rutas de test del *Coverage mapping*,
3. las citas `SPEC-NNN` escritas en el codigo y en los tests.

Se computa en memoria y bajo demanda: no hay artefacto generado que persistir ni
que pueda quedar desincronizado.

Deliberadamente no hay similitud semantica ni TF-IDF: sobre un puñado de specs
que comparten todo el vocabulario del dominio, la similitud lexica rankea ruido,
y los embeddings exigirian red o una dependencia pesada. Las citas ya escritas
son señal dura y determinista.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_traceability import (  # noqa: E402
    _parse_registry,
    iter_coverage_entries,
)
from sdd_config import DEFAULT_TESTS_UNIT, TriageConfig, load  # noqa: E402

# Estados cuyas specs gobiernan algo: una superseded o archived ya no reclama
# ningun archivo (FR-US2-003).
_ESTADOS_VIGENTES = frozenset({"draft", "active"})

_KEY_ENTITIES = re.compile(r"(?i)^#+\s+.*key entities")
_HEADING = re.compile(r"^#+\s")
_CITA_SPEC = re.compile(r"\bSPEC-(\d+)\b")

# Un token de *Key Entities* es ruta si trae directorio o si termina en una
# extension de archivo. La lista es de formatos, no de tecnologias: no acopla el
# kit a ningun proveedor ni UI (Principio I, SPEC-000).
_EXTENSIONES = (
    ".py", ".md", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini", ".txt",
    ".sh", ".ps1", ".js", ".ts", ".tsx", ".go", ".rs", ".java", ".rb", ".sql",
)  # fmt: skip

# Carpetas que nunca aportan senal y si mucho ruido y latencia al escaneo.
_IGNORADAS = frozenset(
    {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache",
     ".pytest_cache", ".ruff_cache", "dist", "build", ".tox"}
)  # fmt: skip

# Separadores de una entrada de *Key Entities*: la descripcion arranca en el
# guion largo y varias entidades en la misma linea se separan con el punto medio.
_CORTE_DESCRIPCION = "—"
_SEPARADOR_ENTIDADES = "·"


@dataclass(frozen=True)
class Candidata:
    """Una spec vigente que podria estar cubriendo ya la capacidad pedida."""

    spec_id: str
    titulo: str
    motivo: str
    por_archivo: bool

    def linea(self) -> str:
        return f"  {self.spec_id} — {self.titulo}\n      ({self.motivo})"


def sin_acentos(text: str) -> str:
    """Translitera diacriticos a ASCII (`búsqueda` -> `busqueda`).

    Publica porque es la unica normalizacion de texto del kit: la consume el
    triage de aca y el slug de `sdd_spec._slugify` (SPEC-003 FR-013). Dos
    criterios distintos para el mismo problema es lo que veta el Principio IV.
    """
    descompuesto = unicodedata.normalize("NFKD", text)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def palabras(text: str, config: TriageConfig) -> set[str]:
    """Palabras significativas de `text`, normalizadas para comparar.

    Se cortan acentos y mayusculas, y `-`/`_` cuentan como separadores de
    palabra a los dos lados de la comparacion (FR-US2-006): sin eso `sdd_spec`
    seria un token unico que ninguna palabra de un titulo alcanzaria.
    """
    crudas = re.split(r"[^a-z0-9]+", sin_acentos(text).lower())
    return {
        p for p in crudas if len(p) >= config.min_word_len and p not in config.stopwords
    }


def _es_ruta(token: str) -> bool:
    return "/" in token or token.lower().endswith(_EXTENSIONES)


def _limpiar(token: str) -> str:
    return token.strip().strip("`*_,;:()[]<>\"'").strip()


def _rutas_de_key_entities(text: str) -> list[str]:
    """Rutas nombradas en la seccion *Key Entities* de una spec (FR-US2-002).

    Cada entrada se corta en el guion de la descripcion y en el punto medio que
    separa varias; de lo que queda es ruta todo token con directorio o con
    extension conocida. Una entrada conceptual sin ruta ("Registro de specs
    vigentes") simplemente no aporta nada.
    """
    rutas: list[str] = []
    dentro = False
    for raw in text.splitlines():
        linea = raw.strip()
        if _KEY_ENTITIES.match(linea):
            dentro = True
            continue
        if _HEADING.match(linea):
            dentro = False
        if not dentro or not linea:
            continue
        cabeza = linea.lstrip("-*+ ").split(_CORTE_DESCRIPCION, 1)[0]
        for parte in cabeza.split(_SEPARADOR_ENTIDADES):
            for token in parte.split():
                limpio = _limpiar(token)
                if limpio and _es_ruta(limpio) and limpio not in rutas:
                    rutas.append(limpio)
    return rutas


def _por_basename(repo_root: Path) -> dict[str, list[str]]:
    """Mapa `nombre de archivo -> rutas reales` del repositorio."""
    out: dict[str, list[str]] = {}
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if any(parte in _IGNORADAS for parte in rel.parts):
            continue
        out.setdefault(path.name, []).append(rel.as_posix())
    return out


def _normalizar_ruta(ruta: str, repo_root: Path, basenames) -> str | None:
    """Ruta relativa al repo en forma posix, o None si es indeterminable.

    Un token con directorio se conserva **aunque el archivo todavia no exista**:
    una spec `draft` nombra en *Key Entities* los archivos que va a crear, y son
    justo los que el gate va a bloquear primero (FR-US2-003). Lo que se descarta
    es el token sin directorio que no resuelve por basename, o que resuelve a
    mas de un archivo: ahi no se sabe de que ruta se habla.
    """
    limpio = ruta.replace("\\", "/").lstrip("./")
    if not limpio:
        return None
    if "/" in limpio:
        return limpio
    candidatos = basenames.get(limpio, [])
    return candidatos[0] if len(candidatos) == 1 else None


def _rutas_citadas(repo_root: Path, config) -> dict[str, set[str]]:
    """Mapa `ruta -> numeros de spec citados` en el codigo y los tests."""
    carpetas = [*config.source_roots, config.dirs.get("tests_unit", DEFAULT_TESTS_UNIT)]
    out: dict[str, set[str]] = {}
    for carpeta in dict.fromkeys(carpetas):
        base = repo_root / carpeta
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or any(p in _IGNORADAS for p in path.parts):
                continue
            try:
                texto = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                # Una fuente ilegible reduce la cobertura del indice; nunca
                # provoca error (FR-US2-003).
                continue
            numeros = set(_CITA_SPEC.findall(texto))
            if numeros:
                out[path.relative_to(repo_root).as_posix()] = numeros
    return out


def build_index(repo_root: Path) -> dict[str, set[str]]:
    """Indice `ruta -> {SPEC-NNN-slug}` derivado del repositorio (FR-US2-001).

    Solo entran specs `draft` o `active`. Ninguna fuente ausente o ilegible
    rompe el calculo: el resultado es un indice mas pobre, no un error.
    """
    specs_dir = repo_root / "specs"
    rows = [
        row
        for row in _parse_registry(specs_dir / "SPECS_REGISTRY.md", [])
        if row.estado in _ESTADOS_VIGENTES
    ]
    basenames = _por_basename(repo_root)
    index: dict[str, set[str]] = {}

    def anotar(ruta: str | None, spec_id: str) -> None:
        if ruta:
            index.setdefault(ruta, set()).add(spec_id)

    por_numero: dict[str, str] = {}
    for row in rows:
        spec_id = Path(row.archivo).stem
        numero = spec_id.split("-")[1] if "-" in spec_id else ""
        if numero:
            por_numero[numero] = spec_id
        try:
            text = (specs_dir / row.archivo).read_text(encoding="utf-8")
        except OSError:
            continue
        for ruta in _rutas_de_key_entities(text):
            anotar(_normalizar_ruta(ruta, repo_root, basenames), spec_id)
        for _fr, tests in iter_coverage_entries(text):
            for ruta in tests:
                anotar(_normalizar_ruta(ruta, repo_root, basenames), spec_id)

    try:
        config = load(repo_root)
    except SystemExit:  # pragma: no cover - PyYAML ausente
        return index
    for ruta, numeros in _rutas_citadas(repo_root, config).items():
        for numero in numeros:
            if numero in por_numero:
                anotar(ruta, por_numero[numero])
    return index


def _titulos(repo_root: Path) -> dict[str, str]:
    """Mapa `SPEC-NNN-slug -> titulo` de las specs vigentes del registro."""
    rows = _parse_registry(repo_root / "specs" / "SPECS_REGISTRY.md", [])
    return {
        Path(row.archivo).stem: row.titulo
        for row in rows
        if row.estado in _ESTADOS_VIGENTES
    }


def specs_for_path(file_path: str, repo_root: Path) -> list[tuple[str, str]]:
    """`(spec_id, titulo)` de las specs que ya gobiernan `file_path` (FR-US3-001)."""
    index = build_index(repo_root)
    objetivo = _relativa(file_path, repo_root)
    if objetivo is None:
        return []
    titulos = _titulos(repo_root)
    return sorted(
        (spec_id, titulos.get(spec_id, "")) for spec_id in index.get(objetivo, ())
    )


def _relativa(file_path: str, repo_root: Path) -> str | None:
    candidato = Path(file_path)
    if not candidato.is_absolute():
        candidato = repo_root / candidato
    try:
        return candidato.resolve().relative_to(repo_root.resolve()).as_posix()
    except (ValueError, OSError):
        return None


def triage(
    titulo: str,
    repo_root: Path,
    *,
    touches: tuple[str, ...] = (),
    config: TriageConfig | None = None,
) -> list[Candidata]:
    """Specs vigentes que podrian estar cubriendo ya esta capacidad (US2).

    Lista candidatas con el motivo que las señalo; no decide. El juicio de si hay
    duplicacion lo aporta quien lee, y por eso las de archivo van primero: que
    una spec nombre el archivo es señal mas dura que compartir vocabulario.
    """
    if config is None:
        try:
            config = load(repo_root).triage
        except SystemExit:  # pragma: no cover - PyYAML ausente
            config = TriageConfig()
    index = build_index(repo_root)
    titulos = _titulos(repo_root)
    tokens = palabras(titulo, config)

    motivos_archivo: dict[str, list[str]] = {}

    def señalar(ruta: str, por: str) -> None:
        for spec_id in index.get(ruta, ()):
            motivos_archivo.setdefault(spec_id, []).append(por)

    for ruta in touches:
        objetivo = _relativa(ruta, repo_root)
        if objetivo is not None:
            señalar(objetivo, f"ya gobierna {objetivo}")

    # Sin `--touches` el triage por archivo igual corre: las mismas palabras del
    # titulo se buscan en el *stem* del nombre de archivo de cada ruta indexada,
    # no en la ruta completa --si no, cualquier segmento de directorio del
    # dominio ("specs/") volveria candidata a media docena de specs (FR-US2-005).
    for ruta in index:
        stem = Path(ruta).stem
        comunes = tokens & palabras(stem, config)
        for palabra in sorted(comunes):
            señalar(ruta, f"'{palabra}' aparece en {ruta}")

    candidatas = [
        Candidata(
            spec_id=spec_id,
            titulo=titulos.get(spec_id, ""),
            motivo="; ".join(dict.fromkeys(motivos)),
            por_archivo=True,
        )
        for spec_id, motivos in motivos_archivo.items()
    ]

    ya = {c.spec_id for c in candidatas}
    for spec_id, texto in titulos.items():
        if spec_id in ya:
            continue
        comunes = tokens & palabras(texto, config)
        if len(comunes) >= config.min_matches:
            candidatas.append(
                Candidata(
                    spec_id=spec_id,
                    titulo=texto,
                    motivo=f"comparte {', '.join(sorted(comunes))} con su titulo",
                    por_archivo=False,
                )
            )

    # Las de archivo primero: es la señal fuerte, y quien lee la lista decide con
    # lo mejor arriba (FR-US2-007).
    return sorted(candidatas, key=lambda c: (not c.por_archivo, c.spec_id))
