# SPEC-007: README propio y manual de operación SDD en el proyecto derivado

> Copiá este archivo a `specs/SPEC-NNN-slug.md`, completá las secciones y
> registralo en `SPECS_REGISTRY.md`. La skill `sdd-spec` automatiza esto.

## User Story (Priority P1)

Como desarrollador que acaba de correr `sdd_init.py` sobre un proyecto nuevo,
quiero recibir un `README.md` propio del producto, un manual humano de cómo
operar SDD (`docs/SDD-OPERACION.md`), y las skills operativas completas
(`sdd-spec`, `sdd-doctor`, `sdd-configure`) — no solo `analyze`/`clarify` —
para poder trabajar con el kit sin tener que ir a leer el repo del kit.

**Why this priority:** bloquea el happy path de instalación (E-1, E-7 en
`docs/IDEAS.md`): hoy la documentación instalada instruye "corré
`sdd-configure`" / "usá `sdd-spec`" pero esas skills no existen en el destino,
y el proyecto derivado no tiene ni README ni manual de las herramientas SDD.

**Independent Test:** correr `sdd_init.py` sobre un directorio vacío y
verificar que aparecen `README.md`, `docs/SDD-OPERACION.md`, y las 5 skills
(`analyze`, `clarify`, `sdd-spec`, `sdd-doctor`, `sdd-configure`) bajo
`.agents/skills/`.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

## Clarifications

### Session 2026-08-02
- Q: ¿El README del derivado debe explicar el protocolo SDD? → A: No. Solo
  info del producto derivado (qué es, cómo se corre); un único link de salida
  a `AGENTS.md` y `docs/SDD-OPERACION.md` en una sección "Desarrollo".
- Q: ¿Cómo se llama el manual de operación? → A: `docs/SDD-OPERACION.md`
  (sigue la convención `SDD-<TEMA>.md` ya usada por `SDD-ENFORCEMENT.md`, no
  `SKILLS.md` que es ambiguo con las skills del asistente en general).
- Q: ¿Se instala también la skill `sdd-init`? → A: No, es bootstrap de una
  sola vez; fuera de alcance.

## Acceptance Scenarios

- **Given** un directorio vacío, **When** se corre
  `python core/sdd_init.py <target> --language none`, **Then** el target
  contiene `README.md`, `docs/SDD-OPERACION.md`, y
  `.agents/skills/{analyze,clarify,sdd-spec,sdd-doctor,sdd-configure}/SKILL.md`.
- **Given** un target donde `README.md` ya existe, **When** se corre
  `sdd_init.py` sin `--force`, **Then** el archivo existente se conserva
  (idempotencia, igual que el resto de `STATIC_DOCS`).
- **Given** el propio kit (que dogfoodea sobre sí mismo), **When** se corre
  `python core/render.py --check`, **Then** no reporta drift para los 3
  playbooks movidos a `templates/docs/playbooks/`.

## Functional Requirements

- **FR-001** MUST: `templates/README.md` existe, con placeholders
  `{{project.name}}` / `{{project.domain}}`, contenido 100% sobre el producto
  derivado (qué es, instalación, uso, tests — TODOs para completar), y una
  única sección "Desarrollo" con un link a `AGENTS.md` y
  `docs/SDD-OPERACION.md`, sin explicar el protocolo SDD.
- **FR-002** MUST: `templates/docs/SDD-OPERACION.md` existe: catálogo humano
  de las 5 skills instaladas (`analyze`, `clarify`, `sdd-spec`, `sdd-doctor`,
  `sdd-configure`) — qué hace cada una y cuándo invocarla.
- **FR-003** MUST: `core/sdd_init.py` instala `README.md` y
  `docs/SDD-OPERACION.md` (sumados a `STATIC_DOCS`) y las 3 skills
  restantes (sumadas a `PROJECT_SKILLS`), con sus playbooks
  (`sdd-spec.md`, `sdd-doctor.md`, `sdd-configure.md`) movidos a
  `templates/docs/playbooks/` como SSOT.
- **FR-004** MUST: los playbooks movidos siguen disponibles en el propio kit
  (`docs/playbooks/*.md`) generados desde `templates/` vía
  `_SYNCED_FROM_TEMPLATES` en `core/render.py` (patrón SPEC-005), no
  duplicados a mano.
- **FR-005** MUST: `templates/00-INDEX.md` referencia `docs/SDD-OPERACION.md`
  en la ruta de lectura y el mapa de SSOTs.
- **FR-006** MUST: `Path.write_text(..., newline="\n")` no es una llamada
  válida en ninguna versión de Python (el kwarg no existe); se reemplaza en
  `core/sdd_spec.py`, `core/render.py`, `core/gen_skill_adapters.py` y
  `core/sdd_init.py` por un helper `sdd_config.write_text_lf` que usa
  `Path.open(..., newline="\n")`. Bug preexistente que bloqueaba toda
  escritura nueva de estas herramientas (nunca se había ejercitado porque el
  kit siempre estaba en sync, sin drift que forzara una escritura real).

## Key Entities

- `templates/README.md`, `templates/docs/SDD-OPERACION.md` (nuevos).
- `templates/docs/playbooks/{sdd-spec,sdd-doctor,sdd-configure}.md` (movidos).
- `core/sdd_config.write_text_lf` (nuevo helper).

## Success Criteria

- **SC-001** Instalación fresca (`sdd_init.py` en target vacío) produce
  `README.md`, `docs/SDD-OPERACION.md` y las 5 skills bajo `.agents/skills/`.
- **SC-002** `python core/pipeline.py` sigue en VERDE tras el cambio.
- **SC-003** `python core/sdd_doctor.py` sano, sin drift de generados.
- **SC-004** `pytest tests/unit` verde, incluyendo tests nuevos para FR-003 y
  FR-006.

## Assumptions

- Los playbooks de `sdd-spec`/`sdd-doctor`/`sdd-configure` ya usan rutas
  vendorizadas (`tools/sdd/core/...`), verificado en el código: no requieren
  edición de contenido, solo reubicación.
- `core/gen_skill_adapters.py` generaliza por glob sobre
  `.agents/skills/*/SKILL.md`: no requiere cambios para las 3 skills nuevas.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_sdd_init.py |
| FR-002 | tests/unit/test_sdd_init.py |
| FR-003 | tests/unit/test_sdd_init.py |
| FR-004 | tests/unit/test_render.py |
| FR-005 | tests/unit/test_sdd_init.py |
| FR-006 | tests/unit/test_sdd_config.py |

## Fuera de alcance

- Instalar la skill `sdd-init` en el proyecto derivado.
- `sdd-update` / ruta de actualización del kit vendorizado (E-2, ya
  registrada aparte en `docs/IDEAS.md`).

## Historial

- 2026-08-02: creada (draft), registrada en SPECS_REGISTRY.md y declarada en
  `.sdd/current-spec`.
- 2026-08-02: implementada y promovida a `active` (pipeline 9/9 VERDE,
  sdd-doctor sano, 77 tests, instalación fresca verificada en `/tmp`).
