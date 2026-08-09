# SPEC-020-enforcement-declarado-en-config: El enforcement de un principio se declara en el config, no en un mapa hardcodeado

> Origen: **E-4** de `docs/IDEAS.md`, promovido al intentar declarar el principio
> de cobertura de **K-3** (misma revisión del 2026-08-08). Al ir a escribirlo se
> vio que un principio nuevo *no obtendría verificación de cableado*: el mapa
> tool→paso vive hardcodeado en `core/check_constitution.py` y lo que no está en
> él pasa en silencio. Declarar el principio sobre esa base habría producido un
> enforcement decorativo en la constitución del propio kit — el fallo que el kit
> existe para evitar.

## User Story (Priority P1)

Como dueño de un proyecto con SDD instalado, quiero declarar en el config qué
paso del pipeline activa el enforcement de cada principio, para que la
constitución verifique el cableado de **mis** principios y no solo el de los
cuatro que el kit trae de fábrica.

**Why this priority:** el Constitution Check es la única garantía de que un
principio no es decorativo. Hoy esa garantía cubre exactamente cuatro tools
conocidas (`check_naming.py`, `lint-imports`, `check_traceability.py`,
`check_constitution.py`); cualquier otro enforcement —el de un principio propio,
o uno nuevo del kit— obtiene `ENFORCEMENT_STEP.get(name) is None` y **no se
verifica nada, sin aviso**. Es además una lista hardcodeada en `core/`, que es
justo lo que `AGENTS.md` prohíbe.

**Independent Test:** declarar un principio cuyo `enforcement` es una tool
arbitraria y cuyo `step` no está en `pipeline.steps` hace fallar
`check_constitution.py` nombrando el principio y el paso faltante; agregando el
paso al config, pasa.

## Clarifications

### Session 2026-08-08

- Q: ¿el mapa va como clave suelta de nivel superior (`enforcement: {tool: paso}`)
  o dentro de cada principio? → A: **dentro de cada principio**, como clave
  `step:` opcional. Un mapa aparte partiría en dos lugares la descripción de un
  mismo principio (qué lo enforcea acá, con qué paso allá) y sería duplicación de
  SSOT dentro del config: el principio es la unidad.
- Q: ¿`check_constitution` pasa a leer los principios del config en vez del
  documento? → A: no. Sigue parseando `CONSTITUTION.md` —el punto del check es
  validar el documento que la gente lee, no el config— y usa el config solo para
  resolver token→paso. Cambiar la fuente de los principios sería otra spec.
- Q: ¿qué pasa con un principio sin `step`? → A: no se verifica cableado y no es
  error. Es el caso real de dos de los cuatro principios del kit: el gate
  (Principio III) se cablea vía hooks y lo verifica `sdd-doctor`, no el pipeline;
  el SSOT único (Principio IV) se sostiene por convención en `AGENTS.md`. Hoy esa
  distinción vive en un comentario de código; pasa a ser explícita en el config.
- Q: ¿el paso se muestra en `CONSTITUTION.md`? → A: no, fuera de alcance. La
  línea `Enforcement:` se parsea con `_BACKTICK.findall`, así que un segundo
  token entre backticks se leería como otro enforcement. Tocar ese contrato de
  parseo no aporta a este invariante.
- Q: ¿por qué entra acá la cobertura de `check_constitution.py`? → A: porque el
  módulo está en **0%** (97 stmts) y esta spec lo modifica. Escribir el cambio sin
  tests sobre un módulo nunca ejecutado es exactamente la deuda K-3; se paga en el
  mismo viaje, con un cambio de comportamiento que los justifica.

## Acceptance Scenarios

- **Given** un principio con `enforcement: mi_check.py` y `step: mi-paso`, y
  `pipeline.steps` sin `mi-paso`, **When** corre `check_constitution.py`,
  **Then** sale 1 y el error nombra el principio, el enforcement y el paso
  faltante.
- **Given** el mismo principio con `mi-paso` presente en `pipeline.steps`,
  **When** corre el check, **Then** sale 0.
- **Given** un principio sin clave `step` (enforcement por hooks o por
  convención), **When** corre el check, **Then** no se verifica cableado y no se
  reporta error por ese motivo.
- **Given** el config del kit, **When** corre el check, **Then** los principios I
  y II verifican sus pasos (`naming`, `traceability`) igual que antes del cambio
  — la migración no afloja ninguna verificación existente.
- **Given** un principio cuyo `Detalle` o `Enforcement` referencia una ruta
  inexistente, **When** corre el check, **Then** sigue fallando por referencia
  rota (comportamiento previo intacto).

## Functional Requirements

- **FR-001** MUST: cada entrada de `principles` en `.sdd/config.yaml` admite una
  clave opcional `step`, que nombra el paso de `pipeline.steps` que activa su
  enforcement.
- **FR-002** MUST: `core/sdd_config.py` expone el dato tipado: `Principle.step` y
  un mapa derivado `enforcement_steps` (token de enforcement → paso), donde el
  token es el basename del valor de `enforcement`. Ningún consumidor parsea el
  YAML crudo ni recompone el mapa por su cuenta.
- **FR-003** MUST: `core/check_constitution.py` no contiene ninguna lista de
  tools ni de pasos: resuelve token→paso contra `enforcement_steps` del config.
  Un principio con `step` declarado y ausente de `pipeline.steps` es error, con
  mensaje que nombra principio, enforcement y paso.
- **FR-004** MUST: un principio sin `step` no produce error ni verificación de
  cableado — es la forma de declarar un enforcement que el pipeline no activa
  (hooks, convención). El motivo se documenta en el config, no en el código.
- **FR-005** MUST: `.sdd/config.yaml` del kit y `examples/config/config.yaml`
  declaran `step` en los principios cuyo enforcement es un paso del pipeline, de
  modo que la verificación existente se conserve tras eliminar el mapa.
- **FR-006** MUST: `tests/unit/test_check_constitution.py` cubre el módulo de
  forma directa: versión ausente/malformada, documento sin principios, principio
  sin `Enforcement`/`Detalle`, referencia rota, paso declarado y no cableado,
  paso cableado, principio sin `step`, y los códigos de salida de uso
  (sin argumento, archivo inexistente).

## Key Entities

- **Principio** — unidad de la constitución. Declara invariante, qué lo enforcea
  (`enforcement`), dónde está su detalle (`detail`) y, si el pipeline lo activa,
  con qué paso (`step`).
- **Mapa de enforcement** — proyección `token → paso` derivada de los principios;
  no es una clave del config ni una lista en el código.

## Success Criteria

- **SC-001** `grep -c "check_naming\|lint-imports" core/check_constitution.py`
  da 0: no queda ninguna tool nombrada en el núcleo.
- **SC-002** Un principio custom con paso no cableado hace ROJO el paso
  `constitution` del pipeline.
- **SC-003** `check_constitution.py` deja de estar en 0% de cobertura.
- **SC-004** El pipeline del kit sigue VERDE y `CONSTITUTION.md` no cambia
  (el documento generado es idéntico: `step` no se renderiza).

## Assumptions

- El nombre del paso no se valida contra un catálogo cerrado: los pasos de código
  los define cada adaptador, así que un `step` inventado se reporta como "falta
  el paso X en pipeline.steps", que es visible aunque sea un typo — preferible a
  no verificar nada.
- La fuente de los principios para el check sigue siendo `CONSTITUTION.md`.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_sdd_config.py |
| FR-002 | tests/unit/test_sdd_config.py |
| FR-003 | tests/unit/test_check_constitution.py |
| FR-004 | tests/unit/test_check_constitution.py |
| FR-005 | tests/unit/test_example_config.py |
| FR-006 | tests/unit/test_check_constitution.py |

## Fuera de alcance

- Renderizar el paso en `CONSTITUTION.md` (cambiaría el contrato de parseo de la
  línea `Enforcement:`).
- Que `check_constitution` lea los principios del config en vez del documento.
- Declarar el principio de cobertura de K-3 y subir el umbral al 90%: es el paso
  siguiente, habilitado por esta spec.
- `enforcement`/`detail` con múltiples tokens (idea suelta ya registrada en
  `docs/IDEAS.md`).

## Historial

- 2026-08-08: creada (draft) desde E-4, como prerrequisito de K-3.
- 2026-08-08: implementada y promovida a `active` (iteración 5). `check_constitution.py`
  pasó de 0% a 99% de cobertura; el total del kit de 75% a 81% y el umbral de
  `pipeline.coverage` de 50 a 80. `CONSTITUTION.md` no cambió, como exigía SC-004.
