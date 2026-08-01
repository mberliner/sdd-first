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
from sdd_config import SddConfig, find_repo_root, load  # noqa: E402

_TODAY = _dt.date.today().isoformat()


def render_constitution(cfg: SddConfig) -> str:
    lines = [
        "# Constitución del proyecto",
        "",
        f"**Versión:** 0.1.0 | Ratificada: {_TODAY} | Última enmienda: {_TODAY}",
        "",
        "> Generado por `core/render.py` desde `.sdd/config.yaml`. La forma de cada",
        "> principio (invariante + Enforcement + Detalle) es lo que valida",
        "> `core/check_constitution.py`. Para enmendar, editá el config y regenerá.",
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
        "- **Versionado:** semver. Fase pre-1.0 (serie `0.y.z`): los principios",
        "  pueden cambiar entre minors sin ruptura formal.",
        "- **Precedencia:** ningún cambio ni spec puede violar un principio. Si una",
        "  spec entra en conflicto, se ajusta la spec, no el principio.",
        "- **Enmienda:** editá `principles` en `.sdd/config.yaml`, regenerá con",
        "  `python core/render.py`, y verificá con `python core/check_constitution.py",
        "  CONSTITUTION.md`.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_naming_spec(cfg: SddConfig) -> str:
    prohibited = cfg.naming_prohibited
    allowed = sorted(cfg.naming_allowed)
    relax = sorted(cfg.naming_relax_in_tests)
    lines = [
        "# SPEC-000: Nomenclatura agnóstica a tecnología",
        "",
        "> Generado por `core/render.py` desde la sección `naming` de",
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
        "Automático vía `adapters/<language>/check_naming.py` (paso `naming` del",
        "pipeline). Ver `.sdd/config.yaml`.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


_GENERATED = {
    "CONSTITUTION.md": render_constitution,
    "specs/SPEC-000-naming.md": render_naming_spec,
}

# SPEC-005: pares (destino en la raiz del repo -> origen en templates/) que
# solo existen duplicados cuando el propio kit dogfoodea sobre si mismo (tiene
# carpeta templates/). `templates/` es el autoritativo; estos destinos NUNCA
# se editan a mano.
_SYNCED_FROM_TEMPLATES = {
    "docs/SDD-ENFORCEMENT.md": "docs/SDD-ENFORCEMENT.md",
    "docs/playbooks/analyze.md": "docs/playbooks/analyze.md",
    "docs/playbooks/clarify.md": "docs/playbooks/clarify.md",
    "specs/SPEC-TEMPLATE.md": "specs/SPEC-TEMPLATE.md",
}


def _sync_renderer(source_rel: str):
    def _render(cfg: SddConfig) -> str:
        return (cfg.repo_root / "templates" / source_rel).read_text(encoding="utf-8")

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
            target.write_text(content, encoding="utf-8", newline="\n")
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
