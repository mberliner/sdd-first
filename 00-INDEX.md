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
7. `adapters/CONTRACT.md` — contrato de adaptador de lenguaje.
8. `docs/IDEAS.md` — backlog de ideas pre-spec.

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
| Fuente de skills | `.agents/skills/` (genera `.claude/` y `.opencode/`) |
| Playbooks de skills | `docs/playbooks/` |
| Plantillas instalables | `templates/` |
| Historial de iteraciones | `historial/sdd.md` |
| Ideas pre-spec | `docs/IDEAS.md` |
