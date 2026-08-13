# SPEC-020-enforcement-declarado-en-config: El enforcement de un principio se declara en el config y se verifica que haya corrido

> Origen: **E-4** de `docs/IDEAS.md`, promovido al intentar declarar el principio
> de cobertura de **K-3** (misma revisión del 2026-08-08). Al ir a escribirlo se
> vio que un principio nuevo *no obtendría verificación de cableado*: el mapa
> tool→paso vive hardcodeado en `core/check_constitution.py` y lo que no está en
> él pasa en silencio. Declarar el principio sobre esa base habría producido un
> enforcement decorativo en la constitución del propio kit — el fallo que el kit
> existe para evitar.

## User Story 1 (Priority P1) — el enforcement declarado se verifica contra el config

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

## User Story 2 (Priority P1) — declarado no es ejecutado: un principio sin enforcement corrido no deja verde a la constitución

> Origen: **"Omitido no es VERDE"** de `docs/IDEAS.md` (Técnicas), que esta misma
> spec abrió como idea en su Assumption al cerrar US1. Reapertura y no spec
> nueva: el invariante es el mismo de US1 —un principio no puede tener
> enforcement decorativo— y esta spec ya es su SSOT; una spec aparte dejaría dos
> documentos respondiendo quién verifica que un principio se enforce de verdad.

Como dueño de un proyecto con SDD instalado, quiero que el pipeline me diga
cuando un principio quedó sin enforcement **ejecutado** en la corrida, para que
el verde no signifique "se verificó" cuando el paso que lo enforza se omitió por
falta de tool, de targets o de umbrales.

**Why this priority:** US1 cerró el hueco de la *declaración* (un `step` que no
está en `pipeline.steps` es error), pero dejó abierto el de la *ejecución*: un
paso declarado que se omite en runtime deja el principio sin verificar y el
pipeline en VERDE. No es un caso de borde: en una instalación fresca los pasos
que enforzan los principios del kit (`naming`, `coverage`) se omiten los dos —
sin carpetas de código y sin umbrales declarados—, así que el primer VERDE de
todo proyecto nuevo se emite con el 100% de sus principios sin enforzar.

**Independent Test:** correr el pipeline con el paso que enforza un principio
omitido hace que el resumen final deje de decir VERDE a secas y nombre el
principio y el paso; el exit code sigue siendo 0. Con ese paso ejecutado, el
resumen vuelve a ser VERDE sin reservas.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

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

### Session 2026-08-12 (US2)

- Q: ¿la detección vive en `check_constitution.py` o en el resumen de
  `core/pipeline.py`? → A: en **`check_constitution.py`**. El mensaje habla en
  lenguaje de principios y aparece junto al listado de principios, que es donde
  el lector lo busca; el orquestador no pasa a saber de constitución. Se evaluó
  el cruce en el resumen —el pipeline ya tiene los omitidos y el mapa
  `enforcement_steps`— y se descartó por eso, aceptando a cambio el costo de
  mover el paso y de abrir un canal de vuelta.
- Q: ¿cómo se entera el check de lo que pasó en la corrida, si es un subproceso
  que hoy recibe un solo argumento? → A: por variable de entorno con los pasos ya
  **ejecutados**, mismo patrón y mismo degradado que
  `PIPELINE_COVERAGE_CACHE_ENV` entre `tests` y `coverage` (SPEC-009
  FR-US3-002): sin la variable —check invocado suelto— el comportamiento es el
  de siempre.
- Q: ¿ejecutados o terminados OK? → A: **ejecutados**, incluyendo los que
  fallaron. Un paso que falla sí corrió su enforcement y de hecho detectó algo;
  el pipeline ya está en ROJO por él, y sumar "principio sin enforcement" sería
  decir algo falso encima de un error real.
- Q: ¿aviso, error, o configurable por principio? → A: **ni error ni
  configurable**. Error rompe frontalmente SPEC-003 FR-001 —la instalación fresca
  volvería a arrancar en ROJO, que es exactamente lo que esa spec existe para
  evitar—, y una clave `strict` por principio nacería en `false` para no romper
  derivados, o sea inerte: el defecto que K-5 nombra. Queda un tercer estado:
  el check sale con un código dedicado y el resumen del pipeline deja de decir
  VERDE a secas, sin cambiar el exit code.
- Q: ¿por qué un código de salida nuevo y no que el pipeline haga su propio
  cruce? → A: porque el criterio tiene que existir **una sola vez**. Con el
  código dedicado, `check_constitution` decide y el pipeline solo traduce a un
  estado visible; si el pipeline recalculara el cruce para su resumen habría dos
  implementaciones del mismo criterio, divergentes por construcción (Principio
  IV).
- Q: ¿dónde queda `constitution` en `pipeline.steps`? → A: después del último
  paso que enforza algún principio. No es una constante: es derivable de
  `enforcement_steps`, y para el kit hoy da **entre `coverage` y `e2e`**, porque
  el Principio V se enforza con `coverage`. Se conserva así la mitad del tiempo
  de feedback (`e2e` son ~17 s de los ~36 s del pipeline, medido en K-4).
- Q: ¿y si un proyecto no mueve el paso? → A: el check lo ve, porque el criterio
  es "el paso todavía no se ejecutó en esta corrida", que cubre igual al omitido
  y al pendiente. Un `constitution` declarado primero reporta reservas por todos
  sus principios, nombrando que corrió antes de tiempo. El degradado es honesto
  en vez de silencioso, y es lo que evita que la garantía dependa de un orden que
  nada verifica —la familia V-1/C-8.

## Acceptance Scenarios

### US1 — declaración

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

### US2 — ejecución

- **Given** un pipeline donde el paso `naming` se omitió (sin carpetas de
  código) y `constitution` corre después, **When** termina la corrida, **Then**
  el resumen no dice VERDE a secas, nombra el Principio I y el paso `naming`
  como no ejecutado, y el exit code es 0.
- **Given** el mismo pipeline con `naming` ejecutado, **When** termina la
  corrida, **Then** el resumen dice VERDE sin reservas.
- **Given** un paso de enforcement que **falló**, **When** termina la corrida,
  **Then** el pipeline sale ROJO por ese paso y el principio **no** se reporta
  sin enforcement: se ejecutó.
- **Given** `check_constitution.py` invocado suelto, sin la variable de entorno,
  **When** corre, **Then** no evalúa ejecución y su comportamiento es idéntico
  al previo a esta historia.
- **Given** un proyecto que declara `constitution` antes de sus pasos de
  enforcement, **When** corre el pipeline, **Then** los principios se reportan
  con reservas nombrando que el paso todavía no se ejecutó en esa corrida.
- **Given** un principio sin `step` (III y IV del kit), **When** corre el
  pipeline, **Then** no se reporta ninguna reserva por él: no hay paso que
  esperar.

## Functional Requirements

### US1

- **FR-001** MUST: cada entrada de `principles` en `.sdd/config.yaml` admite una
  clave opcional `step`, que nombra el paso de `pipeline.steps` que activa su
  enforcement.
- **FR-002** MUST: `core/sdd_config.py` expone el dato tipado: `Principle.step` y
  un mapa derivado `enforcement_steps` (token de enforcement → paso), donde el
  token es el basename del valor de `enforcement`. Si dos basenames colisionan,
  se levanta un `ValueError` considerándolo un error de configuración. Ningún
  consumidor parsea el YAML crudo ni recompone el mapa por su cuenta.
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

### US2

- **FR-US2-001** MUST: `core/pipeline.py` publica a los pasos de proceso qué
  pasos de la corrida ya se **ejecutaron** —los que corrieron, hayan pasado o
  fallado; ni los omitidos ni los todavía pendientes— mediante una variable de
  entorno cuyo nombre se declara en `core/sdd_config.py`, junto a
  `PIPELINE_COVERAGE_CACHE_ENV` y por el mismo motivo: la comparten los dos lados
  del canal.
- **FR-US2-002** MUST: `check_constitution.py`, con esa variable presente,
  reporta cada principio cuyo `step` declarado no figura entre los pasos
  ejecutados, nombrando principio, enforcement y paso, y distinguiendo en el
  mensaje el paso omitido del que todavía no corrió en esa corrida.
- **FR-US2-003** MUST: ese reporte no es un error de integridad. El check sale
  con un código dedicado, declarado en `core/sdd_config.py` junto a
  `EXIT_OMITIDO`; un error de US1 sigue prevaleciendo sobre él.
- **FR-US2-004** MUST: `core/pipeline.py` traduce ese código a un cuarto estado
  visible: el paso cuenta como OK —verificó lo suyo— pero el resumen final deja
  de decir VERDE a secas y nombra el paso con reservas. El exit code del pipeline
  sigue siendo 0. El pipeline no recalcula el cruce: solo traduce el código.
- **FR-US2-005** MUST: sin la variable de entorno, `check_constitution.py` no
  evalúa ejecución y no puede devolver el código nuevo — el comportamiento del
  check invocado suelto es el previo a esta historia.
- **FR-US2-006** MUST: `pipeline.steps` de `.sdd/config.yaml`,
  `examples/config/config.yaml` y `_SEEDED_STEPS` de `core/sdd_init.py` declaran
  `constitution` después del último paso que enforza un principio y después de
  `render`, cuya precondición el orden sembrado hoy viola.
- **FR-US2-007** MUST: `tests/unit/` cubre el ciclo completo por el resumen del
  pipeline —paso de enforcement omitido, ejecutado y fallado—, el degradado sin
  variable de entorno, el principio sin `step` y el orden sembrado.

## Key Entities

- **Principio** — unidad de la constitución. Declara invariante, qué lo enforcea
  (`enforcement`), dónde está su detalle (`detail`) y, si el pipeline lo activa,
  con qué paso (`step`).
- **Mapa de enforcement** — proyección `token → paso` derivada de los principios;
  no es una clave del config ni una lista en el código.
- **Paso ejecutado** — el que corrió en la corrida, con cualquier resultado. Se
  opone al omitido (no se pudo verificar) y al pendiente (declarado después de
  `constitution`). Es lo que decide si un principio tuvo enforcement real.
- **Reserva** — principio con `step` declarado y cableado cuyo paso no se
  ejecutó. No es un error de integridad de la constitución: es un verde que no
  puede afirmar lo que afirma.

## Success Criteria

- **SC-001** `grep -c "check_naming\|lint-imports" core/check_constitution.py`
  da 0: no queda ninguna tool nombrada en el núcleo.
- **SC-002** Un principio custom con paso no cableado hace ROJO el paso
  `constitution` del pipeline.
- **SC-003** `check_constitution.py` deja de estar en 0% de cobertura.
- **SC-004** El pipeline del kit sigue VERDE y `CONSTITUTION.md` no cambia
  (el documento generado es idéntico: `step` no se renderiza).
- **SC-US2-005** Con `naming` omitido, la última línea del pipeline no contiene
  `VERDE —` a secas y sí el nombre del Principio I; `echo $?` da 0.
- **SC-US2-006** El pipeline completo del kit sigue VERDE **sin reservas**: los
  tres principios con `step` (`naming`, `traceability`, `coverage`) se ejecutan
  antes de `constitution` en el orden nuevo.
- **SC-US2-007** Una instalación fresca sigue sin arrancar en ROJO: exit 0 con
  reservas por los principios que todavía no puede enforzar (SPEC-003 FR-001
  intacto).

## Assumptions

- El criterio de US2 es "se ejecutó", no "pasó". Un enforcement que corre y
  detecta una violación cumplió su función; el pipeline ya reporta ese ROJO por
  su propio paso.
- El orden de `pipeline.steps` lo declara cada proyecto y esta spec no lo impone:
  lo siembra bien y reporta con reservas cuando está mal. Un proyecto que declare
  `constitution` primero recibe el aviso en cada corrida, que es correcto —
  describe lo que efectivamente pasó— y se apaga moviendo el paso.
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
| FR-US2-001 | tests/unit/test_pipeline_enforcement_ejecutado.py |
| FR-US2-002 | tests/unit/test_check_constitution.py |
| FR-US2-003 | tests/unit/test_check_constitution.py |
| FR-US2-004 | tests/unit/test_pipeline_enforcement_ejecutado.py |
| FR-US2-005 | tests/unit/test_check_constitution.py |
| FR-US2-006 | tests/unit/test_sdd_init_seeded_steps.py, tests/unit/test_example_config.py |
| FR-US2-007 | tests/unit/test_pipeline_enforcement_ejecutado.py |

## Fuera de alcance

- Renderizar el paso en `CONSTITUTION.md` (cambiaría el contrato de parseo de la
  línea `Enforcement:`).
- Que `check_constitution` lea los principios del config en vez del documento.
- Declarar el principio de cobertura de K-3 y subir el umbral al 90%: es el paso
  siguiente, habilitado por esta spec.
- `enforcement`/`detail` con múltiples tokens (idea suelta ya registrada en
  `docs/IDEAS.md`).
- **(US2)** Partir `check_constitution` en dos momentos —verificaciones estáticas
  temprano, verificación de ejecución al final— para conservar el fallo barato
  bajo `--fail-fast`. Es la única pérdida real de mover el paso: sin
  `--fail-fast` el pipeline corre entero igual y el error aparece a los ~19 s en
  vez de a los ~2 s, sobre un documento que solo cambia al enmendar un principio.
  Complejidad (dos invocaciones del mismo check, conteo de pasos ensuciado) para
  un caso que casi no ocurre.
- **(US2)** Hacer que `sdd-doctor` prediga las omisiones. No puede: no ejecuta el
  pipeline, así que tendría que duplicar la lógica de omisión de cada paso del
  adaptador.
- **(US2)** Una clave `strict` por principio que convierta la reserva en error.

## Historial

- 2026-08-08: creada (draft) desde E-4, como prerrequisito de K-3.
- 2026-08-08: implementada y promovida a `active` (iteración 5). `check_constitution.py`
  pasó de 0% a 99% de cobertura; el total del kit de 75% a 81% y el umbral de
  `pipeline.coverage` de 50 a 80. `CONSTITUTION.md` no cambió, como exigía SC-004.
- 2026-08-12: reabierta con **US2** desde la idea "Omitido no es VERDE", que esta
  misma spec había abierto en sus Assumptions al cerrar US1. Cubre el hueco
  complementario: US1 verifica que el enforcement esté *declarado*, US2 que se
  haya *ejecutado*.
