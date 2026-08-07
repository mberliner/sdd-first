# SPEC-019: Los tests declarados se ejecutan o el proyecto se entera

> Origen: **V-1** de `docs/IDEAS.md`, hallado al escribir los escenarios de
> [[SPEC-018-verificacion-e2e]], que declaró el arreglo fuera de alcance por ser
> cambio de producto sobre `core/` y `adapters/`.
>
> `dirs.tests_integration` es clave de primera clase del config —la leen
> `sdd_config.py`, `render.py` (paths del CI), los dos prefiltros de wiring y
> `check_naming.py`, y figura en `examples/config/config.yaml`— pero ningún paso
> del pipeline la ejecuta. El síntoma no es "esos tests no corren": es que corren
> **en el paso equivocado, o en ninguno**, según una clave sin relación con ellos.
> Con `pipeline.coverage` declarado, `step_coverage` los arrastra (pasa todas las
> carpetas de test a pytest), así que un test de integración roto pinta `coverage`
> en rojo y se ejecuta una vez por cada umbral declarado; sin umbrales, no se
> ejecutan nunca. En los dos casos el paso `tests` —el que dice correr los
> tests— los ignora.
>
> **SSOT del contrato de los pasos de test del pipeline.** El contrato de
> adaptador sigue siendo [[adapters/CONTRACT.md]]; esta spec define qué pasos de
> test existen y qué carpeta corre cada uno.

## User Story 1 (Priority P1) — el pipeline ejecuta los tests de integración declarados

Como dueño de un proyecto que separa tests unitarios de tests de integración,
quiero un paso de pipeline que ejecute los de integración, para que declarar la
carpeta en el config alcance para que se corran y para que su fallo se reporte
como lo que es.

**Why this priority:** hoy la única forma de que corran es un efecto colateral de
`coverage`, que ni los nombra. El equipo que ve `coverage` en rojo busca un
umbral y encuentra un test roto.

**Independent Test:** en un proyecto con `dirs.tests_integration` declarada y la
carpeta poblada, correr el pipeline ejecuta esos tests, el veredicto los cuenta
como paso medido, y romper uno pinta el paso `integration` en rojo.

## User Story 2 (Priority P1) — ninguna carpeta de tests declarada queda sin ejecutor

Como dueño del proyecto, quiero que el kit me avise si declaré una carpeta de
tests que ningún paso de `pipeline.steps` ejecuta, para que la separación entre
ciclo rápido y ciclo lento sea una decisión mía y no un olvido silencioso.

**Why this priority:** es el requisito que impide que el arreglo repita el defecto
que corrige. Dejar el paso a criterio del proyecto —que es lo correcto, porque
`pipeline.steps` es config— reintroduce el agujero salvo que alguien lo mire.

**Independent Test:** con `dirs.tests_integration` declarada y el paso
`integration` ausente de `pipeline.steps`, `sdd-doctor` sale con exit 1 nombrando
la clave, la carpeta y el paso que falta; con el paso presente, sale 0.

## User Story 3 (Priority P2) — el adoptante recibe la clave sembrada

Como quien acaba de instalar el kit sobre un proyecto que ya tiene
`tests/integration`, quiero que el config sembrado la declare, para no descubrir
la clave leyendo el código del kit.

**Why this priority:** `sdd-init` ya detecta la carpeta de código y la de tests
unitarios y las siembra (SPEC-003 FR-007). Que la de integración sea la única que
el adoptante tiene que descubrir por su cuenta es lo que mantuvo el hueco
invisible tanto tiempo.

**Independent Test:** instalar sobre un proyecto con `tests/unit` y
`tests/integration`; el `.sdd/config.yaml` sembrado declara las dos y el mensaje
de layout detectado las nombra.

## Clarifications

### Session 2026-08-07

- Q: ¿No alcanza con que `step_tests` corra todas las carpetas declaradas, como
  ya hacen `naming`, `lint`, `format` y `coverage` vía `_source_and_test_dirs`?
  → A: es la opción más simple y se descartó. `adapters/CONTRACT.md` define el
  paso `tests` como "suite de tests unitarios": `step_tests` no se olvidó de la
  clave, el contrato dice que no le corresponde. Reescribir esa definición le
  impondría a todos los derivados un ciclo único, justo lo contrario de lo que
  [[SPEC-018-verificacion-e2e]] decidió para el kit al dejar los e2e fuera del
  pipeline. Un paso propio conserva la distinción rápido/lento y **amplía** el
  contrato en vez de redefinirlo.
- Q: Pero un paso propio se puede omitir del config y el agujero vuelve. → A:
  por eso US2. La decisión de qué corre en el ciclo rápido es del proyecto; lo
  que no puede pasar es que la omisión sea silenciosa. `sdd-doctor` cruza las
  carpetas de test declaradas contra los pasos que las ejecutan.
- Q: ¿El paso hereda el fallback de `_source_and_test_dirs` (que cae a `tests`
  cuando no hay nada declarado)? → A: no. Ese fallback existe para los pasos
  estáticos, que ante la duda miran de más y no rompen nada. Ejecutar tests que
  el proyecto no declaró es adivinar con efectos: sin `dirs.tests_integration`,
  el paso se omite.
- Q: ¿Se agrega el paso al `pipeline.steps` del propio kit? → A: no: el kit no
  tiene `tests/integration` y sus e2e siguen fuera del pipeline por decisión de
  SPEC-018 (`tests/unit/test_e2e_aislamiento.py` lo fija). El dogfooding del paso
  nuevo se hace donde corresponde, sobre un derivado, en la suite e2e.
- Q: ¿Qué pasa con los derivados ya instalados que declaran la clave? → A: no
  ganan el paso solo: su `pipeline.steps` ya está escrito y el kit no reescribe
  configs ajenos (SPEC-003). Se enteran por el aviso de US2, que es exactamente
  el comportamiento buscado.

## Acceptance Scenarios

### US1 — ejecución

- **Given** un proyecto con `dirs.tests_integration` declarada y la carpeta
  poblada, **When** corre el paso `integration`, **Then** ejecuta los tests de esa
  carpeta y devuelve 0 si pasan.
- **Given** el mismo proyecto con un test de integración roto, **When** corre el
  pipeline, **Then** el paso `integration` sale en rojo y lo nombra.
- **Given** un proyecto sin `dirs.tests_integration` declarada, **When** corre el
  paso, **Then** se omite (exit 3) diciendo que no hay carpeta declarada.
- **Given** la clave declarada apuntando a una carpeta que no existe, **When**
  corre el paso, **Then** se omite nombrando la carpeta ausente.

### US2 — coherencia entre config y pasos

- **Given** `dirs.tests_integration` declarada y `integration` ausente de
  `pipeline.steps`, **When** corre `sdd-doctor`, **Then** sale 1 con un problema
  que nombra la clave, la carpeta y el paso faltante.
- **Given** la misma clave con el paso presente, **When** corre `sdd-doctor`,
  **Then** no reporta ese problema.
- **Given** un proyecto sin la clave declarada, **When** corre `sdd-doctor`,
  **Then** no reporta ese problema (no hay nada huérfano).

### US3 — siembra

- **Given** un proyecto con `tests/unit` y `tests/integration`, **When** se corre
  `sdd-init`, **Then** el config sembrado declara ambas y el paso `integration`
  queda en `pipeline.steps`.
- **Given** un proyecto sin carpeta de integración, **When** se corre `sdd-init`,
  **Then** el config la deja comentada como pista, igual que hoy con `tests_unit`.

## Functional Requirements

### US1

- **FR-US1-001** MUST: el adaptador expone un paso `integration` que ejecuta los
  tests de `dirs.tests_integration`. Es un paso distinto de `tests`, que conserva
  su semántica de suite unitaria.
- **FR-US1-002** MUST: el paso se omite con el contrato del adaptador (exit 3) y
  un motivo que nombre la causa cuando la clave no está declarada, cuando la
  carpeta no existe, o cuando falta la herramienta de tests.
- **FR-US1-003** MUST: el paso no adivina carpetas. Sin `dirs.tests_integration`
  declarada no hay default: no hereda el fallback a `tests` de los pasos
  estáticos.
- **FR-US1-004** MUST: `adapters/CONTRACT.md` —SSOT del contrato de adaptador—
  documenta el paso nuevo y mantiene la definición de `tests` como suite unitaria.

### US2

- **FR-US2-001** MUST: `core/sdd_doctor.py` reporta como problema toda carpeta de
  tests declarada en `dirs` que ningún paso de `pipeline.steps` ejecute. El
  mensaje nombra la clave, la carpeta y el paso que la ejecutaría.
- **FR-US2-002** MUST: la correspondencia `clave de tests → paso que la ejecuta`
  se declara **una sola vez** en `core/sdd_config.py` y la consumen el doctor y
  quien la necesite después. Ni el adaptador ni el doctor guardan su propia copia.

### US3

- **FR-US3-001** SHOULD: `sdd-init` detecta la carpeta de tests de integración del
  destino y la siembra en `dirs.tests_integration`; sin detección la deja
  comentada, como ya hace con `tests_unit`.
- **FR-US3-002** SHOULD: cuando la siembra, el paso `integration` queda en el
  `pipeline.steps` sembrado, para que la instalación no nazca con el problema que
  US2 reporta.
- **FR-US3-003** SHOULD: el mensaje de layout detectado de `sdd-init` nombra la
  carpeta de integración cuando la encontró.

## Key Entities

- **`TEST_DIR_STEP`** (`core/sdd_config.py`): mapa `clave de dirs → paso que la
  ejecuta`. SSOT de qué carpeta corre cada paso; lo consume `sdd_doctor`.
- **Paso `integration`** (`adapters/<language>/adapter.py`): ejecutor de
  `dirs.tests_integration`, opcional en `pipeline.steps`.
- **`dirs.tests_integration`** (`.sdd/config.yaml`): carpeta de tests de
  integración del proyecto. Opcional; sin ella el paso se omite.

## Success Criteria

- **SC-001** En un derivado con `tests/integration` poblada y el paso declarado,
  el pipeline ejecuta esos tests y los cuenta como paso medido.
- **SC-002** Un test de integración roto pinta el paso `integration` en rojo, no
  `coverage`.
- **SC-003** Declarar la carpeta sin declarar el paso hace que `sdd-doctor` salga
  1 nombrando los tres datos; declarar ambos lo deja en 0.
- **SC-004** Instalar sobre un proyecto con `tests/integration` deja un config que
  la declara y un pipeline que la corre, sin intervención manual.
- **SC-005** El pipeline del kit sigue VERDE con la misma cantidad de pasos: el
  kit no declara la clave y no gana el paso.

## Assumptions

- El adaptador de Python es el único que existe; el paso se define en el contrato
  para todos, se implementa donde haya adaptador.
- Qué es "de integración" lo decide el proyecto al declarar la carpeta. El kit no
  clasifica tests, solo ejecuta lo declarado.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-US1-001 | `tests/unit/test_adapter_integration.py` |
| FR-US1-002 | `tests/unit/test_adapter_integration.py` |
| FR-US1-003 | `tests/unit/test_adapter_integration.py` |
| FR-US1-004 | `tests/unit/test_adapter_integration.py` |
| FR-US2-001 | `tests/unit/test_sdd_doctor_tests_huerfanos.py` |
| FR-US2-002 | `tests/unit/test_sdd_doctor_tests_huerfanos.py` |
| FR-US3-001 | `tests/unit/test_sdd_init_seeded_config.py` |
| FR-US3-002 | `tests/unit/test_sdd_init_seeded_config.py` |
| FR-US3-003 | `tests/unit/test_sdd_init_seeded_config.py` |
| SC-001..SC-004 | `tests/e2e/escenarios/test_tests_de_integracion.py` |

## Fuera de alcance

- **Reclasificar qué corre `coverage`.** Sigue midiendo sobre todas las carpetas
  de test declaradas: es lo correcto para una medición de cobertura, y cambiarlo
  bajaría los números de cualquier proyecto que ya la declare.
- **Migrar configs de derivados ya instalados.** El kit avisa, no reescribe
  (ver Clarifications).
- **Un paso e2e en el pipeline.** SPEC-018 decidió lo contrario para el kit; que
  un derivado quiera declarar su carpeta e2e como `tests_integration` es decisión
  suya, y con esta spec al menos se entera de si corre o no.
- Adaptadores de otros lenguajes (no existen).

## Historial

- 2026-08-07: creada (draft) en la iteración 4. Cierra V-1.
- 2026-08-07: implementada y promovida a `active`. Pipeline VERDE 10/10 —los
  mismos pasos que antes: el kit no declara la clave—, 310 passed + 1 skip en la
  suite unitaria y 17 en la e2e. El paso nuevo se dogfoodea en
  `tests/e2e/escenarios/test_tests_de_integracion.py`, sobre un derivado que sí
  separa sus dos suites. Hallazgo lateral: `pipeline.CODE_STEPS` y el dispatcher
  del adaptador enumeran los pasos por separado y nada los ata (C-8 de IDEAS).
