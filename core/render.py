"""Renderiza los artefactos derivados del config (`sdd-configure`).

Dos documentos embeben datos del config y por eso se GENERAN (no se editan a
mano): `CONSTITUTION.md` (a partir de `principles`) y `specs/SPEC-000-naming.md`
(a partir de `naming`). El resto de las plantillas son estaticas y se copian con
sustitucion simple de `{{project.name}}` / `{{project.domain}}`.

Ademas, cuando el repo tiene su propia carpeta `templates/` (el caso del kit
dogfoodeando sobre si mismo, no el de un proyecto instalado), este script
sincroniza un puñado de documentos que existen duplicados entre `templates/`
(autoritativo) y la raiz del repo (`docs/`, `specs/SPEC-TEMPLATE.md`): SPEC-005
"desduplicar SSOTs". En un proyecto instalado con `sdd-init` no hay carpeta
`templates/`, asi que estas entradas son no-op.

Uso:
    python core/render.py [--check]

--check falla (exit 1) si algun artefacto generado o sincronizado esta
desactualizado; util para el pipeline (evita drift entre config/plantillas y
sus derivados).
"""

from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sdd_config import SddConfig, find_repo_root, load, write_text_lf  # noqa: E402

_TODAY = _dt.date.today().isoformat()


def render_constitution(cfg: SddConfig) -> str:
    """Genera CONSTITUTION.md desde el config (SPEC-010 FR-001..FR-003).

    El documento no es solo la lista de principios: incluye un preambulo que
    explica que ES una constitucion (y que no es), y una seccion Governance con
    el criterio de versionado y el procedimiento de enmienda. Sin eso, un equipo
    que recibe el archivo generado no sabe que hacer con el.
    """
    core = cfg.kit_paths["{{sdd.core}}"]
    version = cfg.constitution_version
    ratified = cfg.constitution_ratified or _TODAY
    amended = cfg.constitution_amended or _TODAY
    lines = [
        "# Constitución del proyecto",
        "",
        f"**Versión:** {version} | Ratificada: {ratified} | Última enmienda: {amended}",
        "",
        f"> Generado por `{core}/render.py` desde `.sdd/config.yaml`. La forma de cada",
        "> principio (invariante + Enforcement + Detalle) es lo que valida",
        f"> `{core}/check_constitution.py`. Para enmendar, editá el config y regenerá.",
        "",
        "## Preámbulo",
        "",
        "- **Qué es:** la lista curada de los principios no-negociables de *este*",
        "  proyecto. No es documentación de referencia ni el protocolo del asistente",
        "  (`AGENTS.md`): es lo que nunca cede.",
        "- **Cómo se usa:** se lee antes de diseñar una spec o encarar un cambio. Si",
        "  una spec o una decisión de implementación entra en conflicto con un",
        "  principio, **se ajusta la spec, no el principio**.",
        "- **Alcance:** cada principio declara un **invariante** estable y",
        "  autocontenido. El detalle operativo —que evoluciona— vive en el SSOT que",
        "  el principio referencia en `Detalle:`. La constitución nunca duplica ese",
        "  detalle: declara el invariante y apunta.",
        "",
        "## Principios",
        "",
    ]
    for p in cfg.principles:
        lines.append(f"### {p.id}. {p.title}")
        lines.append("")
        if p.invariant:
            lines.append(p.invariant)
            lines.append("")
        lines.append(f"- **Enforcement:** `{p.enforcement}`")
        lines.append(f"- **Detalle:** `{p.detail}`")
        lines.append("")
    lines += [
        "## Governance",
        "",
        "- **Versionado semver:** MAJOR remueve o redefine un principio; MINOR",
        "  agrega un principio o una sección; PATCH aclara la redacción sin cambiar",
        "  el invariante.",
        "- **Fase pre-1.0:** mientras el proyecto no alcance madurez sostenida la",
        "  serie es `0.y.z`: lo que tras `1.0.0` sería MAJOR o MINOR sube `y`; lo que",
        "  sería PATCH sube `z`.",
        "- **Precedencia:** un principio prevalece sobre cualquier spec o decisión de",
        "  implementación. El protocolo del asistente (`AGENTS.md`) referencia esta",
        "  constitución pero no la contiene: si se cambia de asistente, la",
        "  constitución sigue vigente.",
        "- **Procedimiento de enmienda:**",
        "  1. Editá `principles` (y `constitution.version`) en `.sdd/config.yaml`,",
        "     subiendo la versión según la regla de arriba y actualizando",
        "     `constitution.amended`.",
        f"  2. Regenerá este documento: `python {core}/render.py`.",
        "  3. Registrá el cambio en `historial/sdd.md` (qué principio, por qué).",
        "  4. Revisá los SSOTs que referencia el principio afectado.",
        f"  5. Verificá: `python {core}/check_constitution.py CONSTITUTION.md`.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_naming_spec(cfg: SddConfig) -> str:
    prohibited = cfg.naming_prohibited
    allowed = sorted(cfg.naming_allowed)
    relax = sorted(cfg.naming_relax_in_tests)
    core = cfg.kit_paths["{{sdd.core}}"]
    adapters = cfg.kit_paths["{{sdd.adapters}}"]
    lines = [
        "# SPEC-000: Nomenclatura agnóstica a tecnología",
        "",
        f"> Generado por `{core}/render.py` desde la sección `naming` de",
        "> `.sdd/config.yaml`. Editá el config, no este archivo.",
        "",
        "## Regla",
        "",
        "Ningún identificador de código (clase, función, variable, módulo) puede",
        "contener un token que nombre un proveedor, framework de UI, formato de",
        "almacenamiento/serialización o protocolo de autenticación. El código nombra",
        "*conceptos del dominio*, no *tecnologías*; los detalles de tecnología viven",
        "detrás de puertos, en la capa de adaptadores.",
        "",
        "## Tokens prohibidos",
        "",
    ]
    lines += [f"- `{t}`" for t in prohibited]
    lines += [
        "",
        "## Identificadores permitidos (excepciones)",
        "",
    ]
    lines += [f"- `{t}`" for t in allowed] or ["- (ninguno)"]
    lines += [
        "",
        "## Tokens relajados en tests",
        "",
        "En las carpetas de tests se toleran los siguientes tokens (los nombres de",
        "tests describen el escenario, no acoplan a tecnología):",
        "",
    ]
    lines += [f"- `{t}`" for t in relax] or ["- (ninguno)"]
    lines += [
        "",
        "## Enforcement",
        "",
        f"Automático vía `{adapters}/<language>/check_naming.py` (paso `naming` del",
        "pipeline). Ver `.sdd/config.yaml`.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_ci_workflow(cfg: SddConfig) -> str:
    """Genera el workflow de CI desde el config (SPEC-009 FR-005).

    Decision de diseno: el job **no enumera los pasos**, invoca el pipeline. El
    SSOT de que se corre es `pipeline.steps` del config; duplicar la lista en el
    YAML es justo el drift que se observo en el proyecto de referencia (su
    ci.yml y su pipeline_local.sh llevan meses desincronizados). Cambiar
    `pipeline.steps` cambia lo que corre CI sin tocar este archivo.

    Los `paths:` de disparo derivan de `dirs.source_roots` + carpetas de tests:
    un cambio que solo toca `docs/` o `specs/` no gasta una corrida de CI.
    """
    core = cfg.kit_paths["{{sdd.core}}"]
    watched = list(cfg.source_roots)
    for key in ("tests_unit", "tests_integration"):
        value = cfg.dirs.get(key)
        if value and value not in watched:
            watched.append(value)
    # El andamiaje se vigila siempre: en el kit ya esta entre los source_roots,
    # en un proyecto instalado vive aparte, bajo tools/sdd/.
    patterns: list[str] = []
    for candidate in [*watched, core]:
        pattern = f"{candidate}/**"
        if pattern not in patterns:
            patterns.append(pattern)
    patterns += [".sdd/config.yaml", ".github/workflows/ci.yml"]

    trigger = []
    for event, extra in (("push", ["    branches: [main]"]), ("pull_request", [])):
        trigger.append(f"  {event}:")
        trigger.extend(extra)
        trigger.append("    paths:")
        trigger.extend(f'      - "{p}"' for p in patterns)

    install = ["      - name: Instalar dependencias", "        run: |"]
    install.append("          python -m pip install --upgrade pip")
    install.append("          pip install pyyaml")
    if cfg.language == "python":
        install.append(
            "          if [ -f requirements-dev.txt ]; then "
            "pip install -r requirements-dev.txt; fi"
        )
        install.append(
            "          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi"
        )

    lines = [
        f"# Generado por `{core}/render.py` desde `.sdd/config.yaml`. No editar a mano:",
        "# los pasos que corre son los de `pipeline.steps`, no una lista propia.",
        f"name: ci ({cfg.name})",
        "",
        "on:",
        *trigger,
        "",
        "jobs:",
        "  pipeline:",
        "    runs-on: ubuntu-latest",
        "    steps:",
        "      - uses: actions/checkout@v4",
        "",
        "      - uses: actions/setup-python@v5",
        "        with:",
        '          python-version: "3.13"',
        "          cache: pip",
        "",
        *install,
        "",
        "      - name: Pipeline SDD",
        f"        run: python {core}/pipeline.py",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


_GENERATED = {
    "CONSTITUTION.md": render_constitution,
    "specs/SPEC-000-naming.md": render_naming_spec,
    ".github/workflows/ci.yml": render_ci_workflow,
}

# SPEC-005: pares (destino en la raiz del repo -> origen en templates/) que
# solo existen duplicados cuando el propio kit dogfoodea sobre si mismo (tiene
# carpeta templates/). `templates/` es el autoritativo; estos destinos NUNCA
# se editan a mano.
_SYNCED_FROM_TEMPLATES = {
    "docs/SDD-ENFORCEMENT.md": "docs/SDD-ENFORCEMENT.md",
    "docs/SKILLS-MULTITOOL.md": "docs/SKILLS-MULTITOOL.md",
    "docs/playbooks/analyze.md": "docs/playbooks/analyze.md",
    "docs/playbooks/clarify.md": "docs/playbooks/clarify.md",
    "docs/playbooks/sdd-spec.md": "docs/playbooks/sdd-spec.md",
    "docs/playbooks/sdd-doctor.md": "docs/playbooks/sdd-doctor.md",
    "docs/playbooks/sdd-configure.md": "docs/playbooks/sdd-configure.md",
    "specs/SPEC-TEMPLATE.md": "specs/SPEC-TEMPLATE.md",
}


def _sync_renderer(source_rel: str):
    def _render(cfg: SddConfig) -> str:
        text = (cfg.repo_root / "templates" / source_rel).read_text(encoding="utf-8")
        # En el kit los placeholders de ruta resuelven a `core/` y `adapters/`;
        # en un proyecto instalado los resuelve sdd_init (SPEC-010 FR-007).
        return cfg.resolve_kit_paths(text)

    return _render


def _generated_targets(repo_root: Path) -> dict[str, Any]:
    targets = dict(_GENERATED)
    if (repo_root / "templates").is_dir():
        for dst_rel, src_rel in _SYNCED_FROM_TEMPLATES.items():
            targets[dst_rel] = _sync_renderer(src_rel)
    return targets


def main(argv: list[str]) -> int:
    check = "--check" in argv
    repo_root = find_repo_root()
    cfg = load(repo_root)
    generated = _generated_targets(repo_root)

    drift: list[str] = []
    for rel, renderer in generated.items():
        target = repo_root / rel
        content = renderer(cfg)
        if check:
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            # Ignora la línea de fecha de enmienda para no marcar drift por el día.
            if _strip_dates(current) != _strip_dates(content):
                drift.append(rel)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            write_text_lf(target, content)
            print(f"  generado  {rel}")

    if check:
        if drift:
            print(
                "Artefactos derivados desincronizados (corre: python core/render.py):"
            )
            for d in drift:
                print(f"  x {d}")
            return 1
        print("Artefactos derivados: sincronizados.")
        return 0
    print(f"Renderizados {len(generated)} artefacto(s).")
    return 0


def _strip_dates(text: str) -> str:
    import re

    return re.sub(r"\d{4}-\d{2}-\d{2}", "DATE", text)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
