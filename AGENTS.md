# Protocolo SDD para asistentes IA — sdd-kit

> **SSOT del protocolo del agente de este repositorio.** Fuente única
> cross-asistente: la leen directo los asistentes que buscan `AGENTS.md`
> (opencode, Cursor, Codex, Aider, Gemini CLI…). Claude Code la recibe vía
> `@AGENTS.md` en `CLAUDE.md`.
>
> Este es el kit dogfooding su propio SDD. El andamiaje que instalás en otros
> proyectos vive en `templates/` + `core/` + `adapters/`; acá lo usamos sobre
> nosotros mismos. Parámetros en `.sdd/config.yaml`.

Dominio: andamiaje SDD universal, agnóstico y personalizable para otros proyectos.

## Antes de cualquier cambio

1. Leé `CONSTITUTION.md` (generado desde `.sdd/config.yaml`). Ningún cambio ni
   spec puede violar un principio; si hay conflicto, se ajusta la spec.
2. Leé `00-INDEX.md`... (en el kit, este README + `specs/SPECS_REGISTRY.md`).
3. Leé `specs/SPECS_REGISTRY.md` para saber qué specs están vigentes.
4. Identificá a qué spec corresponde el cambio. Si no hay, creala con `sdd-spec`
   (o a mano) antes de tocar `core/` o `adapters/`.
5. Aplicá la nomenclatura agnóstica (`specs/SPEC-000-naming.md`): el kit maneja
   formatos (yaml/json) por diseño, pero no acopla a proveedores/UI concretos.

## Durante el cambio

- El núcleo (`core/`) debe seguir siendo agnóstico de lenguaje y de dominio: toda
  parametrización va a `.sdd/config.yaml`, nunca hardcodeada.
- Lo específico de un lenguaje va en `adapters/<language>/` respetando
  `adapters/CONTRACT.md`.
- Las plantillas de `templates/` usan placeholders `{{project.name}}` /
  `{{project.domain}}`; los docs derivados del config (`CONSTITUTION.md`,
  `SPEC-000`) se generan con `core/render.py`, no se editan a mano.
- Todo cambio de comportamiento requiere test en `tests/unit/`.

## Al cerrar una iteración

1. Corré `python core/pipeline.py` y asegurate de que esté verde.
2. Regenerá artefactos si tocaste config o skills: `python core/render.py` y
   `python core/gen_skill_adapters.py`.
3. Actualizá `specs/SPECS_REGISTRY.md` y agregá una entrada en `historial/sdd.md`.
4. El commit de cierre incluye el bloque `[SDD-Check]`.

## Qué NO hacer

- No hardcodear listas (tokens, capas, pasos) en `core/` o `adapters/`: van al
  config.
- No editar a mano `CONSTITUTION.md`, `specs/SPEC-000-naming.md` ni los
  adaptadores generados en `.claude/`/`.opencode/` (los regenera el kit).
- No romper el contrato de adaptador ni el agnosticismo del núcleo.
- No duplicar SSOT.
