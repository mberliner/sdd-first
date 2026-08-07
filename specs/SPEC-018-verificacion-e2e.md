# SPEC-018: Verificación de punta a punta del kit instalado

> **SSOT de la estrategia de verificación e2e del kit**: qué se prueba corriendo
> el producto instalado en un entorno real, dónde vive y por qué queda fuera del
> ciclo rápido. El detalle operativo (cómo se corre, cómo se agrega un escenario)
> vive en `tests/e2e/README.md`.
>
> Origen: los tres defectos que más costaron en las iteraciones 2 y 3 —el falso
> verde del pipeline (C-1/C-2/C-5), las skills que el instalador recomendaba y no
> existían ([[SPEC-016-skills-listas-tras-init]]) y el gate que bloqueaba el
> segundo commit de una misma spec (G-5, [[SPEC-017-gate-decision-spec-first]])—
> no los detectó ningún test unitario. Los tres salieron de correr el kit a mano,
> en una carpeta sin versionar, sin CI y sin aserciones.
>
> **Automatiza un criterio que ya existe:** [[SPEC-017-gate-decision-spec-first]]
> SC-004 exige verificar el ciclo spec-first "con commits reales en el kit y en un
> proyecto derivado instalado con `sdd-init`", hoy a mano. Esta spec no redefine
> ese criterio —SPEC-017 sigue siendo su SSOT— sino que lo ejecuta.
>
> **Fuera de esta spec, por eje distinto:** qué decide el gate
> ([[SPEC-017-gate-decision-spec-first]]), dónde se invoca
> ([[SPEC-015-wiring-apunta-al-codigo-real]]), qué afirma el derivado sobre sí
> mismo ([[SPEC-014-derivado-dice-la-verdad]]) y la suite unitaria del núcleo
> ([[SPEC-002-dogfooding-integro]] FR-003).

## User Story 1 (Priority P1) — las promesas al adoptante se verifican con el producto instalado

Como responsable del kit, quiero que cada promesa que el instalador le hace al
adoptante se verifique instalando el kit de verdad sobre un repositorio git real,
para que los defectos de integración se detecten en la suite y no en la primera
corrida de un usuario.

**Why this priority:** es el hueco que produjo los tres defectos citados. La suite
unitaria mide decisiones de funciones; ninguna función miente, lo que miente es el
conjunto instalado (un pipeline que reporta pasos que no midió, un mensaje que
recomienda una skill inexistente, un gate que bloquea el flujo que el propio
protocolo prescribe).

**Independent Test:** instalar el kit en una carpeta vacía con
`core/sdd_init.py` como subproceso, correr el pipeline del derivado y afirmar que
cada paso reportado OK **fue medido** —los omitidos dicen que se omitieron— y que
cada skill que el mensaje de próximos pasos nombra existe en los cuatro formatos.

## User Story 2 (Priority P1) — la verificación e2e no contamina el ciclo rápido

Como quien trabaja el kit todos los días, quiero que la suite e2e sea explícita y
esté aislada, para que `pytest` y `python core/pipeline.py` sigan siendo rápidos y
la suite e2e no deje residuos dentro del repositorio.

**Why this priority:** una suite lenta cableada al ciclo de cada commit se termina
salteando, y entonces no verifica nada. Además el riesgo es concreto: declarar la
carpeta como `dirs.tests_integration` la haría ejecutar dentro del paso `coverage`
del pipeline (`adapters/python/adapter.py` la incluye vía `_source_and_test_dirs`),
y un workspace resuelto dentro del árbol del kit quedaría gobernado por su propio
gate, porque la raíz SDD se busca subiendo por el sistema de archivos.

**Independent Test:** `pytest` a secas y `python core/pipeline.py` terminan sin
ejecutar ningún escenario e2e; tras correr `pytest tests/e2e`, `git status` está
limpio.

## Clarifications

### Session 2026-08-07

- Q: ¿Esto es una capacidad con spec o simplemente más tests de la suite? → A:
  spec. `tests/` está fuera de `dirs.source_roots`, así que mecánicamente el gate
  no lo exige, pero [[SPEC-012-suite-multiplataforma]] ya es precedente de una
  spec cuyo objeto es la suite, y lo que se agrega no son tests sueltos sino un
  nivel de verificación con estructura, contrato de entorno y job de CI propios.
- Q: ¿Integración, regresión o e2e? → A: e2e / aceptación. No verifica que las
  piezas internas encajen (integración) ni es una categoría por propósito
  (regresión es un porqué, no un alcance): verifica el producto instalado contra
  las promesas que le hace al adoptante. "Testbed" queda como nombre del entorno
  efímero que cada escenario crea, no de un directorio versionado.
- Q: ¿Se declara la carpeta como `dirs.tests_integration` para que el `ci.yml`
  generado la vigile? → A: no. Tiene un efecto no buscado y ningún beneficio real.
  El efecto: `_source_and_test_dirs` incluye esa clave y `step_coverage` le pasa
  las carpetas a pytest, así que `python core/pipeline.py` correría toda la suite
  e2e dentro del paso `coverage`. El no-beneficio: ese `ci.yml` invoca
  `core/pipeline.py`, que no corre e2e, de modo que el disparo extra gastaría una
  corrida sin ejecutar lo que cambió. Además `step_tests` solo corre `tests_unit`,
  con lo que quedarían medidos por un paso y ejecutados por ninguno.
- Q: ¿Y el hueco de `tests_integration` a medio cablear? → A: es real (clave de
  primera clase en el config y en los prefiltros de wiring, presente en
  `examples/config/config.yaml`, pero `sdd-init` no la siembra, `step_tests` no la
  corre y ninguna plantilla la prescribe) y es **cambio de producto** sobre `core/`
  y `adapters/`, con efecto en todos los derivados. Queda registrado en
  `docs/IDEAS.md` para spec propia; ver *Fuera de alcance*.
- Q: ¿Cómo se seleccionan los escenarios: marca de pytest o `testpaths`? → A: solo
  `testpaths`. `testpaths = ["tests/unit"]` ya los excluye de `pytest` a secas;
  agregar además una marca `e2e` sería un segundo mecanismo para el mismo filtro
  (Principio IV).
- Q: ¿Qué pasa si `pre-commit` no está disponible? → A: el escenario se omite con
  el motivo nombrado (qué faltó exactamente), no falla, para que la suite corra
  offline y en máquinas sin el entorno preparado. Con `SDD_E2E_STRICT` no vacía
  —que CI setea— esa omisión pasa a ser fallo, así el degradado no puede
  convertirse en un verde silencioso donde importa.
- Q: ¿El entorno se limpia al terminar o al empezar? → A: al empezar. Garantiza la
  regeneración total sin depender de que la corrida anterior haya terminado bien, y
  deja los artefactos en disco para inspeccionar un fallo.

## Acceptance Scenarios

### US1 — el producto instalado

- **Given** una carpeta vacía, **When** se instala con `sdd_init` como subproceso
  y se corre el pipeline del derivado, **Then** el veredicto distingue pasos
  medidos de pasos omitidos, y `sdd-doctor` reporta sano.
- **Given** un proyecto con historia git y código en una carpeta que no es la
  convencional, **When** se instala, **Then** se conservan los archivos del dueño,
  los `source_roots` detectados apuntan a esa carpeta y el gate la protege.
- **Given** un proyecto con `.pre-commit-config.yaml` y configuración de asistente
  propios, **When** se instala, **Then** el instalador avisa que los conservó y
  `sdd-doctor` sale distinto de 0 nombrando cada archivo que existe pero no invoca
  al gate.
- **Given** un derivado instalado, **When** se edita `.sdd/config.yaml` y se
  regenera, **Then** los artefactos derivados reflejan el cambio, `--check` no
  reporta drift y el pipeline detecta una violación sembrada según el config nuevo.
- **Given** un derivado con hooks instalados, **When** se recorren los tres
  escenarios de SPEC-017 US3 con commits reales, **Then** las decisiones son las
  que SPEC-017 especifica, incluido el escape hatch.

### US2 — aislamiento

- **Given** la suite e2e presente, **When** se corre `pytest` sin argumentos o
  `python core/pipeline.py`, **Then** no se ejecuta ningún escenario e2e.
- **Given** una corrida completa de `pytest tests/e2e`, **When** termina, **Then**
  `git status` no reporta archivos nuevos ni modificados.
- **Given** un `SDD_E2E_WORK` que resolvería dentro del árbol del kit, **When** se
  inicia la suite, **Then** aborta nombrando el conflicto, sin borrar nada.
- **Given** dos corridas consecutivas sin limpieza manual entre ellas, **When**
  terminan, **Then** el resultado es el mismo.
- **Given** un entorno sin `pre-commit` utilizable, **When** corre un escenario que
  lo requiere, **Then** se omite nombrando qué faltó; **When** además
  `SDD_E2E_STRICT` no está vacía, **Then** falla.

## Functional Requirements

### US1

- **FR-US1-001** MUST: existe una suite en `tests/e2e/` cuyos escenarios instalan
  el kit invocando `core/sdd_init.py` **como subproceso desde el clon del kit**,
  igual que un adoptante, sobre un repositorio git real creado por la propia suite.
- **FR-US1-002** MUST: las aserciones verifican **contenido** de la salida y de los
  archivos generados, no solo códigos de salida; un fallo muestra la salida
  completa del comando que lo produjo.
- **FR-US1-003** MUST: la suite cubre al menos instalación limpia, instalación
  sobre proyecto preexistente, wiring propio del dueño, reconfiguración vía
  `.sdd/config.yaml` y el ciclo spec-first con commits reales.
- **FR-US1-004** MUST: cada escenario nacido de un defecto reproducido nombra ese
  defecto en su docstring.
- **FR-US1-005** MUST: los escenarios que requieren `pre-commit` real se omiten con
  un motivo que nombra qué faltó cuando no está disponible, y fallan cuando
  `SDD_E2E_STRICT` tiene valor no vacío.

### US2

- **FR-US2-001** MUST: el workspace se resuelve fuera del árbol del kit (variable
  `SDD_E2E_WORK` o directorio temporal del sistema); si resolviera dentro, la suite
  aborta sin borrar nada.
- **FR-US2-002** MUST: el workspace se borra y recrea al **inicio** de la corrida,
  y cada escenario instala desde cero.
- **FR-US2-003** MUST: `tests/e2e/` no se declara en `.sdd/config.yaml` ni entra a
  `pipeline.steps`; `pytest` sin argumentos y `python core/pipeline.py` no ejecutan
  escenarios e2e.
- **FR-US2-004** MUST: la selección de escenarios tiene un solo mecanismo
  (`testpaths` de `pyproject.toml`), sin marca de pytest que duplique el filtro.
- **FR-US2-005** MUST: el disparo de e2e en CI vive en un workflow propio del kit
  escrito a mano, sin modificar `render_ci_workflow` —que produce el workflow
  universal que reciben los derivados—.
- **FR-US2-006** MUST: el testigo de proyecto preexistente tiene un solo SSOT,
  compartido por la suite unitaria y la e2e.

## Key Entities

- `tests/e2e/lib/` — harness: resolución y regeneración del entorno, ejecución de
  comandos del derivado, aserciones con mensajes útiles.
- `tests/e2e/escenarios/` — un archivo por escenario; su docstring dice qué promesa
  verifica y qué defecto lo originó.
- `tests/fixtures_proyecto.py` — SSOT del testigo de proyecto preexistente.
- `SDD_E2E_WORK` — override del workspace efímero.
- `SDD_E2E_STRICT` — convierte en fallo las omisiones por entorno incompleto.
- `.github/workflows/e2e.yml` — job propio del kit, escrito a mano.

## Success Criteria

- **SC-001** `pytest tests/e2e` corre verde en Windows, y dos corridas consecutivas
  sin limpieza manual entre ellas dan el mismo resultado.
- **SC-002** Tras una corrida completa, `git status` está limpio: ningún artefacto
  de la suite quedó dentro del repositorio.
- **SC-003** `pytest tests/unit` no recoge ningún escenario e2e y
  `python core/pipeline.py` sigue VERDE sin ejecutarlos.
- **SC-004** Los tres defectos que originan esta spec tienen cada uno un escenario
  que los detectaría si volvieran.
- **SC-005** El ciclo spec-first de SPEC-017 SC-004 se verifica en la suite y deja
  de depender de una corrida manual en una carpeta sin versionar.

## Assumptions

- El entorno de desarrollo tiene `git` disponible en el PATH. Sin `git` no hay
  escenario posible: el objeto de la verificación es el kit sobre un repositorio.
- `pre-commit` puede faltar o no poder construir su entorno (máquina sin red); por
  eso FR-US1-005. `git`, en cambio, no se degrada.
- La suite corre en el sistema de archivos local; no se cubre el caso de un
  workspace en unidad de red.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-US1-001 | tests/e2e/escenarios/test_instalacion_limpia.py |
| FR-US1-002 | tests/unit/test_e2e_entorno.py |
| FR-US1-003 | tests/unit/test_e2e_entorno.py |
| FR-US1-004 | tests/unit/test_e2e_entorno.py |
| FR-US1-005 | tests/unit/test_e2e_entorno.py |
| FR-US2-001 | tests/unit/test_e2e_entorno.py |
| FR-US2-002 | tests/unit/test_e2e_entorno.py |
| FR-US2-003 | tests/unit/test_e2e_aislamiento.py |
| FR-US2-004 | tests/unit/test_e2e_aislamiento.py |
| FR-US2-005 | tests/unit/test_e2e_aislamiento.py |
| FR-US2-006 | tests/unit/test_e2e_aislamiento.py |

## Fuera de alcance

- **Cerrar el hueco de `tests_integration` en el producto** (sembrarlo en
  `sdd-init`, ejecutarlo en `step_tests`, prescribirlo en `templates/`). Es cambio
  sobre `core/` y `adapters/` con efecto en todos los derivados: merece spec
  propia. Acá solo queda registrado en `docs/IDEAS.md`.
- Escenarios para otros lenguajes: los adaptadores `node`/`go` no existen todavía.
- La ruta de actualización del kit vendorizado (E-2 de `docs/IDEAS.md`).
- Verificar la experiencia dentro de cada asistente (que Claude Code u opencode
  efectivamente invoquen las skills): la suite verifica los archivos y el contrato,
  no el asistente.

## Historial

- 2026-08-07: creada (draft) y promovida a `active` en la iteración 4. Automatiza
  SPEC-017 SC-004 y convierte la campaña manual de usabilidad del derivado en
  suite versionada. Su primera corrida dejó V-1, V-2 y V-3 en `docs/IDEAS.md`.
