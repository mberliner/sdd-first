# Índice de documentación — sdd-first

> Navegación y mapa de SSOTs del propio kit (dogfooding). Evita duplicación:
> cada tema tiene un único archivo autoritativo.

## Ruta de lectura recomendada

1. `README.md` — qué es el kit y cómo se usa.
2. `CONSTITUTION.md` — principios (generado desde `.sdd/config.yaml`).
3. `AGENTS.md` — protocolo del agente (SSOT cross-asistente).
4. `specs/SPECS_REGISTRY.md` — specs vigentes del kit.
5. `specs/SPEC-000-naming.md` — nomenclatura agnóstica (generado).
6. `docs/SDD-ENFORCEMENT.md` — cómo se obliga el SDD.
7. `docs/SKILLS-MULTITOOL.md` — cómo una skill sirve a varios asistentes.
8. `adapters/CONTRACT.md` — contrato de adaptador de lenguaje.
9. `docs/IDEAS.md` — backlog de ideas pre-spec (abiertas).
10. `docs/PATRONES.md` — clases de defecto que ya se repitieron en el kit.

## Mapa de SSOTs

| Tema | Archivo autoritativo |
|------|----------------------|
| Qué es el kit / uso | `README.md` |
| Principios / constitución | `CONSTITUTION.md` (← `.sdd/config.yaml`) |
| Parámetros del kit | `.sdd/config.yaml` |
| Protocolo del agente | `AGENTS.md` (Claude lo recibe vía `CLAUDE.md`) |
| Specs vigentes | `specs/SPECS_REGISTRY.md` |
| Nomenclatura | `specs/SPEC-000-naming.md` (← `.sdd/config.yaml`) |
| Formato de spec | `templates/docs/SPEC-FORMAT.md` |
| Enforcement | `docs/SDD-ENFORCEMENT.md` |
| Contrato de adaptadores | `adapters/CONTRACT.md` |
| Mecanismo de skills multi-asistente | `docs/SKILLS-MULTITOOL.md` |
| Verificación e2e del kit instalado | `tests/e2e/README.md` (requisitos: `specs/SPEC-018-verificacion-e2e.md`) |
| Workflow de CI | `.github/workflows/ci.yml` (← `.sdd/config.yaml`, generado) |
| Fuente de skills | `.agents/skills/` (genera `.claude/` y `.opencode/`) |
| Wiring de los gates (hooks, pre-commit, plugin) | `templates/wiring/` (el del propio kit se genera desde ahí con `core/render.py`) |
| Playbooks de skills | `docs/playbooks/` |
| Plantillas instalables | `templates/` |
| Historial de iteraciones | `historial/sdd.md` |
| Ideas pre-spec abiertas (backlog, IDs, estados, descartes) | `docs/IDEAS.md` |
| Ideas cerradas y su post-mortem | `docs/IDEAS-CERRADAS.md` |
| Patrones recurrentes de defecto | `docs/PATRONES.md` |
| Historial de versiones del kit | `CHANGELOG.md` |
| Clases de propiedad de cada artefacto instalado | `core/sdd_catalog.py` |
| Manifiesto de instalación de un derivado | `.sdd/kit.lock` (formato en `core/sdd_lock.py`) |
