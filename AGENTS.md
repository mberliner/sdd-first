# Protocolo SDD para asistentes IA — sdd-first

> **SSOT del protocolo del agente de este repositorio.** Fuente única
> cross-asistente: la leen directo los asistentes que buscan `AGENTS.md`
> (opencode, Cursor, Codex, Aider, Gemini CLI…). Claude Code la recibe vía
> `@AGENTS.md` en `CLAUDE.md`.
>
> Este es el kit dogfooding su propio SDD. El andamiaje que instalás en otros
> proyectos vive en `templates/` + `core/` + `adapters/`; acá lo usamos sobre
> nosotros mismos. Parámetros en `.sdd/config.yaml`.

> El dominio del proyecto lo declara `CONSTITUTION.md`, que se genera desde
> `project.domain` de `.sdd/config.yaml`. Acá no se repite: una copia escrita a
> mano quedaría congelada en el primer valor (SPEC-014 FR-US2-006).

## Antes de cualquier cambio

1. Leé `CONSTITUTION.md` (generado desde `.sdd/config.yaml`). Ningún cambio ni
   spec puede violar un principio; si hay conflicto, se ajusta la spec.
2. Leé `00-INDEX.md`... (en el kit, este README + `specs/SPECS_REGISTRY.md`).
3. Leé `specs/SPECS_REGISTRY.md` para saber qué specs están vigentes.
4. Identificá a qué spec corresponde el cambio. **Antes de crear una nueva,
   fijate si la capacidad ya cabe en una vigente**: se adopta con `sdd-spec
   --reuse`, y el triage del propio script avisa cuáles se solapan. El
   procedimiento completo —incluido dónde escribir el FR nuevo en la spec
   adoptada— vive en el playbook `sdd-spec`, que no se reproduce acá.
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
- Antes de escribir una regla, una cifra o una convención, buscá su SSOT en el
  mapa de `00-INDEX.md` y referencialo; si el tema todavía no tiene documento
  autoritativo, elegí uno y agregalo al mapa. Dentro de un mismo documento vale
  igual: si dos secciones necesitan el mismo detalle, declaralo una vez.

## Al cerrar una iteración

1. Corré `python core/pipeline.py` y asegurate de que esté verde.
2. Regenerá artefactos si tocaste config o skills: `python core/render.py` y
   `python core/gen_skill_adapters.py`.
3. Actualizá `specs/SPECS_REGISTRY.md` y agregá una entrada en `historial/sdd.md`.
4. El commit de cierre incluye el bloque `[SDD-Check]`.

## Qué NO hacer

- No hardcodear listas (palabras excluidas, capas, pasos) en `core/` o `adapters/`: van al
  config.
- No editar a mano `CONSTITUTION.md`, `specs/SPEC-000-naming.md` ni los
  adaptadores generados en `.claude/`/`.opencode/`/`.agents/` (los regenera el kit).
- No editar el wiring del kit (`.claude/settings.json`, `.claude/sdd_gate_hook.sh`,
  `.pre-commit-config.yaml`, `.gitattributes`, `.agents/*`, `.opencode/plugin/*`):
  se genera desde `templates/wiring/`. Editá la plantilla y corré
  `python core/render.py`.
- No sobrescribir a mano `.sdd/current-spec` para destrabar el gate. Siempre se debe usar `python tools/sdd/core/sdd_spec.py` para reusar una spec o crear una nueva. Ante la duda de qué spec aplicar, se debe consultar al usuario.
- No romper el contrato de adaptador ni el agnosticismo del núcleo.
- No duplicar SSOT.
