# Protocolo SDD para asistentes IA — {{project.name}}

> **SSOT del protocolo del agente.** Fuente única cross-asistente: la leen
> directo los asistentes que buscan `AGENTS.md` (opencode, Cursor, Codex, Aider,
> Gemini CLI…). Claude Code la recibe vía `@AGENTS.md` en `CLAUDE.md`.
>
> Andamiaje provisto por **sdd-kit**. Parámetros del proyecto en `.sdd/config.yaml`.

Dominio: {{project.domain}}

Cuando trabajes en este proyecto, seguí este protocolo:

## Antes de cualquier cambio

1. Leé `CONSTITUTION.md`. Ningún cambio ni spec nueva puede violar un principio;
   si una spec entra en conflicto, se ajusta la spec, no el principio.
2. Leé `00-INDEX.md` para orientarte en la estructura y los SSOTs.
3. Leé `specs/SPECS_REGISTRY.md` para saber qué specs están vigentes.
4. Identificá a qué spec(s) corresponde el cambio. Si no hay spec, creala antes de
   codear (usá la skill `sdd-spec`).
5. Leé `specs/SPEC-000-naming.md` y aplicá la nomenclatura agnóstica en todo
   identificador nuevo.
6. Leé `docs/ARCHITECTURE.md` para respetar las capas declaradas en `.sdd/config.yaml`.

## Durante el cambio

- Actualizá la spec si el comportamiento implementado difiere de lo especificado
  (las specs son vivas).
- Mantené el SSOT único por tema: no dupliques información entre `docs/`, `specs/`
  y README.
- Todo cambio que toque comportamiento requiere test correspondiente.

## Al cerrar una iteración

1. Corré `python core/pipeline.py` (o el wrapper `tools/pipeline`) y asegurate de
   que esté verde.
2. Actualizá `specs/SPECS_REGISTRY.md` con el estado de las specs.
3. Agregá una entrada en `historial/sdd.md` (fecha, scope, decisiones, deuda).
4. El commit de cierre incluye el bloque `[SDD-Check]`:

```
[SDD-Check]
- Specs leídas: SPEC-NNN-x, SPEC-NNN-y
- Includes/excludes verificados: ...
- SSOTs afectados: ...
```

## Qué NO hacer

- No introducir identificadores con tokens prohibidos (ver `SPEC-000-naming.md` y
  la sección `naming` de `.sdd/config.yaml`).
- No mergear con specs desactualizadas.
- No agregar dependencias sin justificación.
- No duplicar SSOT.
