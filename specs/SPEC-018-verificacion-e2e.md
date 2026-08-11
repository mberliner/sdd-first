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
esté aislada, para que `pytest` siga siendo rápido y la suite e2e no deje residuos
dentro del repositorio.

**Why this priority:** el riesgo es concreto: declarar la carpeta como
`dirs.tests_integration` la haría ejecutar dentro del paso `coverage` del pipeline
(`adapters/python/adapter.py` la incluye vía `_source_and_test_dirs`), y un
workspace resuelto dentro del árbol del kit quedaría gobernado por su propio gate,
porque la raíz SDD se busca subiendo por el sistema de archivos.

> **Enmendada el 2026-08-09 (US3).** Esta US también prohibía el paso `e2e` en
> `pipeline.steps`, con el argumento de que "una suite lenta cableada al ciclo de
> cada commit se termina salteando". Las dos mitades resultaron falsas y la
> prohibición se levantó: ver la sesión de Clarifications de esa fecha y US3. Lo
> que sigue vigente y sin cambios es el aislamiento propiamente dicho: `pytest` a
> secas no recoge escenarios, el workspace vive fuera del árbol del kit y la
> corrida no deja residuo.

**Independent Test:** `pytest` a secas termina sin ejecutar ningún escenario e2e;
tras correr `pytest tests/e2e`, `git status` está limpio.

## User Story 3 (Priority P1) — el nivel de test primario del generador corre en el ciclo

Como responsable del kit, quiero que la suite e2e sea un paso del pipeline local,
para que el nivel de verificación que **más defectos reales encuentra** en un
proyecto generador deje de depender de que alguien se acuerde de correrla a mano.

**Why this priority:** el dogfooding es estructuralmente incapaz de cubrir lo que
el kit genera *para otros*. El config del kit ejercita rutas distintas de las que
siembra `sdd-init`: por ahí entró el bug de sintaxis INI de `gen_import_linter`
—el kit no corre `layers`— que ningún unitario vio y solo apareció al correr la
e2e. Para un generador, el test de instalación no es un extra: es el nivel
primario, y dejarlo fuera del pipeline es la misma clase de falso verde que el
kit persigue en todo lo demás (un VERDE que no miró lo que más importa).

**Independent Test:** `python core/pipeline.py` sobre el kit ejecuta los
escenarios e2e como un paso más, y romper un escenario pinta el paso `e2e` en
rojo; el paso `coverage` sigue sin ejecutarlos.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

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

### Session 2026-08-08

- Q: El workspace se borra entero al inicio y lo único que lo protege es no
  solaparse con el árbol del kit; un `SDD_E2E_WORK` mal tipeado borraría datos
  ajenos sin aviso. ¿Qué se exige antes de borrar? → A: marca propia o vacío. Se
  borra solo si la ruta no existe, está vacía, o lleva la marca que siembra la
  propia suite; un directorio preexistente sin marca aborta nombrando el
  conflicto, igual que el solape con el kit (FR-US2-007). No se restringe la ruta
  al temp del sistema: apuntar el workspace a un disco elegido es útil en Windows
  y para inspeccionar artefactos.
- Q: `tests/e2e/escenarios/` ya aloja un escenario de otra spec
  ([[SPEC-019-tests-integracion-ejecutados]]). ¿De quién es la carpeta? → A: es
  infraestructura compartida del kit. Cualquier spec puede agregar un escenario y
  lo mapea en **su propio** Coverage mapping; SPEC-018 mantiene el contrato del
  harness y sigue exigiendo solo los cinco escenarios fundacionales de FR-US1-003
  (FR-US1-007). Duplicar el inventario acá obligaría a tocar esta spec cada vez
  que otra agrega un escenario (Principio IV).
- Q: FR-US1-002 y FR-US1-004 son reglas sobre la propia suite, pero se verifican
  con tests más baratos que lo enunciado (que `detalle()` imprima la salida, que
  exista un docstring). ¿Se sostienen? → A: con una guardia estructural sobre
  `escenarios/`, al estilo de la que ya impide construir rutas contra el kit
  (FR-US1-006). Los dos siguen siendo MUST y pasan a ser verificables.
- Q: SC-001 exige verde en Windows y SC-002 `git status` limpio, y ninguno se
  mide. → A: se cierran los dos en el workflow propio: la matriz Linux + Windows
  queda fijada por un unitario (FR-US2-008) y un paso final exige
  `git status --porcelain` vacío (FR-US2-009). SC-001 no reenuncia el criterio
  multiplataforma: su SSOT es [[SPEC-012-suite-multiplataforma]].
- Q: ¿Qué entra al Coverage mapping: los escenarios o el unitario que verifica que
  existan? → A: los escenarios reales cubren FR-US1-001 y FR-US1-003; el unitario
  de completitud queda listado junto a ellos como guardia de que ninguno
  desaparezca, no como cobertura principal.

### Session 2026-08-09 (K-4) — se reabre la exclusión del ciclo rápido

- Q: US2 ordena lo contrario a lo que pide K-4. ¿Spec nueva? → A: no: dos SSOTs
  contradictorios sobre el mismo archivo (Principio IV). Va como enmienda de esta
  spec, que es la dueña de la decisión, con la revisión escrita acá y no
  disimulada.
- Q: El argumento de US2 era el costo. ¿Se midió? → A: nunca, y esa es la falla
  de la decisión original. Medido ahora: la suite e2e completa tarda **16,6 s**
  (17 escenarios) contra **17,2 s** del pipeline entero; el paso más caro que ya
  existe, `coverage`, tarda 9,2 s y `tests` 7,3 s. La e2e es 1,8× el paso más
  caro, no un orden de magnitud: el ciclo pasa de ~17 s a ~34 s. "Suite lenta" no
  describe este caso.
- Q: ¿Y "cableada al ciclo de cada commit"? → A: era falso desde el principio. En
  cada commit corren los hooks (`sdd-gate`, `sdd-traceability`, `sdd-reset`); el
  pipeline se corre al cerrar una iteración, que es exactamente el momento en que
  se quiere saber si el producto instalado todavía funciona.
- Q: ¿Detrás de un flag, o al final y siempre? → A: siempre, declarado último.
  Un flag reproduce el modo de falla que US2 temía —"se termina salteando"— nada
  más que con otro disparador, y le devuelve al kit un VERDE que no miró su nivel
  de test primario. Al final por orden de costo, para que un fallo barato aparezca
  antes.
- Q: ¿Se replica el precedente de `integration` (clave `dirs.tests_e2e` + paso
  propio)? → A: sí, pero la clave sola no alcanzaba: `_source_and_test_dirs` la
  arrastraba a la corrida de `coverage` —el acople que esta misma US nombra—. Se
  resolvió antes, en [[SPEC-005-desduplicar-ssot]] FR-007: la carpeta se declara
  con la propiedad de si entra o no a la medición. Aquí `tests_e2e` entra a los
  pasos estáticos y no a la medición.
- Q: ¿Por qué la e2e no entra a la medición de cobertura? → A: no es una
  preferencia. Los escenarios manejan el kit **por subproceso**, así que no
  aportan una sola línea medida en proceso: incluirla solo duplicaría su costo
  dentro de `coverage`, corriéndola dos veces por corrida del pipeline.
- Q: ¿Qué pasa con el `ci.yml` generado, que ahora hereda el paso? → A: en el kit
  el job de `ci.yml` pasa a correr la e2e en Linux, solapándose con la pata Linux
  de `e2e.yml`. Es duplicación real y se acepta a ojos abiertos: son ~17 s de
  runner, y evitarla exigiría que `render_ci_workflow` supiera del caso del kit,
  que es justo lo que FR-US2-005 prohíbe. `e2e.yml` sigue siendo el SSOT de la
  corrida e2e en CI: aporta Windows y `SDD_E2E_STRICT`, que el pipeline no setea.
- Q: ¿Y el paso "Lint de la suite" escrito a mano en `e2e.yml`? → A: desaparece.
  Existía precisamente porque la carpeta no estaba declarada en `dirs`; ahora
  `lint`/`format`/`naming` la cubren desde el config, que es su SSOT.
- Q: ¿Se siembra `tests_e2e` en un derivado? → A: sí, con detección, como
  `tests_integration` ([[SPEC-019-tests-integracion-ejecutados]] FR-US3-001). Una
  clave de primera clase que `sdd-init` nunca siembra es el hueco que produjo V-1;
  repetirlo con una clave nueva sería reintroducir el defecto a sabiendas.
- Q: ¿No hay recursión: el pipeline corre la e2e, que instala un kit y corre el
  pipeline del derivado? → A: no. El config sembrado no declara `tests_e2e` salvo
  detección, y ningún escenario copia el config del kit al derivado: `sdd-init`
  siembra uno nuevo.

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

- **Given** la suite e2e presente, **When** se corre `pytest` sin argumentos,
  **Then** no se ejecuta ningún escenario e2e.
- **Given** una corrida completa de `pytest tests/e2e`, **When** termina, **Then**
  `git status` no reporta archivos nuevos ni modificados.
- **Given** un `SDD_E2E_WORK` que resolvería dentro del árbol del kit, **When** se
  inicia la suite, **Then** aborta nombrando el conflicto, sin borrar nada.
- **Given** un `SDD_E2E_WORK` que apunta a un directorio con contenido que no dejó
  la suite, **When** se inicia, **Then** aborta nombrando el conflicto y el
  directorio queda intacto; **Given** el mismo directorio ya marcado por una
  corrida anterior, **When** se inicia, **Then** se regenera sin preguntar.
- **Given** dos corridas consecutivas sin limpieza manual entre ellas, **When**
  terminan, **Then** el resultado es el mismo.
- **Given** un entorno sin `pre-commit` utilizable, **When** corre un escenario que
  lo requiere, **Then** se omite nombrando qué faltó; **When** además
  `SDD_E2E_STRICT` no está vacía, **Then** falla.

### US3 — el paso `e2e`

- **Given** el kit con `dirs.tests_e2e` declarada y `e2e` en `pipeline.steps`,
  **When** corre `python core/pipeline.py`, **Then** los escenarios se ejecutan
  como un paso medido, y romper uno pinta el paso `e2e` en rojo.
- **Given** el mismo kit, **When** corre el paso `coverage`, **Then** no ejecuta
  ningún escenario e2e: la carpeta está declarada pero no entra a la medición.
- **Given** un proyecto sin `dirs.tests_e2e` declarada, **When** corre el paso
  `e2e`, **Then** se omite nombrando la clave que falta, sin adivinar carpetas.
- **Given** un proyecto con una carpeta de e2e propia, **When** se instala con
  `sdd-init`, **Then** el config sembrado la declara y `e2e` queda en
  `pipeline.steps`, de modo que `sdd-doctor` no reporta tests sin ejecutor.
- **Given** `.github/workflows/e2e.yml`, **When** se lo lee, **Then** ya no linta
  `tests/e2e` por su cuenta: lo cubre el paso `lint` del pipeline desde el config.

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
- **FR-US1-006** MUST: una guardia estructural recorre `tests/e2e/escenarios/` y
  verifica mecánicamente FR-US1-002 y FR-US1-004: cada archivo usa al menos una
  aserción de contenido, y su docstring de módulo nombra la promesa que verifica
  y —cuando nació de un defecto reproducido— el identificador de ese defecto.
- **FR-US1-007** MUST: `tests/e2e/` es infraestructura compartida del kit: otra
  spec puede agregar un escenario y lo mapea en su propio Coverage mapping. Esta
  spec es SSOT del contrato del harness (workspace, fixtures, aserciones,
  aislamiento) y no del inventario de escenarios ajenos.

### US2

- **FR-US2-001** MUST: el workspace se resuelve fuera del árbol del kit (variable
  `SDD_E2E_WORK` o directorio temporal del sistema); si resolviera dentro, la suite
  aborta sin borrar nada.
- **FR-US2-002** MUST: el workspace se borra y recrea al **inicio** de la corrida,
  y cada escenario instala desde cero.
- **FR-US2-003** MUST: `pytest` sin argumentos no recoge ningún escenario e2e.
  *(Enmendado el 2026-08-09: decía además que `tests/e2e/` no se declara en el
  config ni entra a `pipeline.steps`, y que `python core/pipeline.py` no los
  ejecuta. Lo revierte US3; el criterio de aislamiento que queda es el de
  `pytest` a secas, que sigue siendo el ciclo rápido de verdad.)*
- **FR-US2-004** MUST: la selección de escenarios tiene un solo mecanismo
  (`testpaths` de `pyproject.toml`), sin marca de pytest que duplique el filtro.
- **FR-US2-005** MUST: el disparo de e2e en CI vive en un workflow propio del kit
  escrito a mano, sin modificar `render_ci_workflow` —que produce el workflow
  universal que reciben los derivados—.
- **FR-US2-006** MUST: el testigo de proyecto preexistente tiene un solo SSOT,
  compartido por la suite unitaria y la e2e.
- **FR-US2-007** MUST: el workspace se borra solo si la ruta no existe, está vacía
  o lleva la marca que siembra la propia suite; un directorio preexistente sin
  marca aborta nombrando el conflicto, **sin borrar nada**.
- **FR-US2-008** MUST: el workflow e2e del kit corre en Linux y Windows, y esa
  matriz queda fijada por un test, no solo por el archivo.
- **FR-US2-009** MUST: el workflow e2e verifica al terminar la corrida que
  `git status --porcelain` esté vacío.

### US3

- **FR-US3-001** MUST: el adaptador expone un paso `e2e` que ejecuta los tests de
  `dirs.tests_e2e`. Es un paso distinto de `tests` y de `integration`, y no
  adivina carpetas: sin la clave declarada se omite nombrándola, igual que
  `integration` ([[SPEC-019-tests-integracion-ejecutados]] FR-US1-003).
- **FR-US3-002** MUST: `dirs.tests_e2e` entra a los pasos estáticos
  (`naming`/`lint`/`format`) y **no** a la corrida del paso `coverage`. La razón
  es factual, no de preferencia: los escenarios manejan el producto por
  subproceso y no aportan líneas medidas en proceso, así que incluirla solo los
  correría de nuevo. Lo sostiene la propiedad declarada en
  [[SPEC-005-desduplicar-ssot]] FR-007, no la ausencia de la clave en el config.
- **FR-US3-003** MUST: el `.sdd/config.yaml` del kit declara `dirs.tests_e2e` y
  `e2e` en `pipeline.steps`, **último**, después de `coverage`. Sin flag ni
  invocación aparte: un disparador opcional reintroduce el "se termina salteando"
  con otro nombre.
- **FR-US3-004** MUST: `sdd-init` detecta una carpeta de e2e en el destino y, si
  la encuentra, la siembra en `dirs.tests_e2e` **y** agrega `e2e` a
  `pipeline.steps`; sin detección no declara ninguna de las dos. Una clave de
  primera clase que el instalador nunca siembra es el hueco de V-1.
- **FR-US3-005** MUST: `.github/workflows/e2e.yml` deja de lintar `tests/e2e/` por
  su cuenta: con la carpeta declarada en `dirs`, los pasos `naming`/`lint`/
  `format` la cubren desde el config, que es su SSOT. Lo que el workflow puede
  conservar es el lint de la infraestructura compartida de la raíz de `tests/`
  (`conftest.py`, `fixtures_proyecto.py`), que ninguna clave de `dirs` alcanza:
  ese hueco es preexistente y ajeno a esta spec (V-4 de `docs/IDEAS.md`).

## Key Entities

- `tests/e2e/lib/` — harness: resolución y regeneración del entorno, ejecución de
  comandos del derivado, aserciones con mensajes útiles.
- `tests/e2e/escenarios/` — un archivo por escenario; su docstring dice qué promesa
  verifica y qué defecto lo originó.
- `tests/fixtures_proyecto.py` — SSOT del testigo de proyecto preexistente.
- `SDD_E2E_WORK` — override del workspace efímero.
- Marca del workspace — archivo que la suite siembra en la raíz del workspace y
  que autoriza a borrarlo en la corrida siguiente (FR-US2-007).
- `SDD_E2E_STRICT` — convierte en fallo las omisiones por entorno incompleto.
- `.github/workflows/e2e.yml` — job propio del kit, escrito a mano.

## Success Criteria

- **SC-001** `pytest tests/e2e` corre verde en las plataformas que exige
  [[SPEC-012-suite-multiplataforma]] —su SSOT—, y dos corridas consecutivas sin
  limpieza manual entre ellas dan el mismo resultado.
- **SC-002** Tras una corrida completa, `git status` está limpio: ningún artefacto
  de la suite quedó dentro del repositorio, y el propio workflow lo verifica.
- **SC-003** `pytest tests/unit` no recoge ningún escenario e2e. *(Enmendado el
  2026-08-09: exigía además que `python core/pipeline.py` siguiera VERDE **sin
  ejecutarlos**; ahora los ejecuta como el paso `e2e`, ver SC-006.)*
- **SC-004** Los tres defectos que originan esta spec tienen cada uno un escenario
  que los detectaría si volvieran.
- **SC-005** El ciclo spec-first de SPEC-017 SC-004 se verifica en la suite y deja
  de depender de una corrida manual en una carpeta sin versionar.
- **SC-006** `python core/pipeline.py` sobre el kit ejecuta los escenarios e2e
  como paso propio y sale ROJO si uno falla; el paso `coverage` de esa misma
  corrida no los ejecuta (una sola pasada de la suite por pipeline).
- **SC-007** Un derivado cuya carpeta de e2e se detectó al instalar nace con la
  clave declarada y el paso en `pipeline.steps`, de modo que `sdd-doctor` no
  reporta tests declarados sin ejecutor.

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
| FR-US1-001 | tests/e2e/escenarios/test_instalacion_limpia.py, tests/e2e/escenarios/test_instalacion_brownfield.py, tests/e2e/escenarios/test_wiring_propio.py, tests/e2e/escenarios/test_configuracion.py, tests/e2e/escenarios/test_ciclo_spec_first.py |
| FR-US1-002 | tests/unit/test_e2e_entorno.py |
| FR-US1-003 | tests/e2e/escenarios/test_instalacion_limpia.py, tests/e2e/escenarios/test_instalacion_brownfield.py, tests/e2e/escenarios/test_wiring_propio.py, tests/e2e/escenarios/test_configuracion.py, tests/e2e/escenarios/test_ciclo_spec_first.py; guardia de completitud: tests/unit/test_e2e_entorno.py |
| FR-US1-004 | tests/unit/test_e2e_entorno.py |
| FR-US1-005 | tests/unit/test_e2e_entorno.py |
| FR-US1-006 | tests/unit/test_e2e_entorno.py |
| FR-US1-007 | tests/unit/test_e2e_aislamiento.py |
| FR-US2-001 | tests/unit/test_e2e_entorno.py |
| FR-US2-002 | tests/unit/test_e2e_entorno.py |
| FR-US2-003 | tests/unit/test_e2e_aislamiento.py |
| FR-US2-004 | tests/unit/test_e2e_aislamiento.py |
| FR-US2-005 | tests/unit/test_e2e_aislamiento.py |
| FR-US2-006 | tests/unit/test_e2e_aislamiento.py |
| FR-US2-007 | tests/unit/test_e2e_entorno.py |
| FR-US2-008 | tests/unit/test_e2e_aislamiento.py |
| FR-US2-009 | tests/unit/test_e2e_aislamiento.py |
| FR-US3-001 | tests/unit/test_adapter_e2e.py |
| FR-US3-002 | tests/unit/test_adapter_e2e.py, tests/unit/test_e2e_aislamiento.py |
| FR-US3-003 | tests/unit/test_e2e_aislamiento.py |
| FR-US3-004 | tests/unit/test_sdd_init_seeded_config.py |
| FR-US3-005 | tests/unit/test_e2e_aislamiento.py |

## Fuera de alcance

- **Cerrar el hueco de `tests_integration` en el producto** (sembrarlo en
  `sdd-init`, ejecutarlo en `step_tests`, prescribirlo en `templates/`). Es cambio
  sobre `core/` y `adapters/` con efecto en todos los derivados, y tiene spec
  propia: [[SPEC-019-tests-integracion-ejecutados]]. Su escenario e2e vive en esta
  carpeta y lo mapea esa spec (FR-US1-007).
- Escenarios para otros lenguajes: los adaptadores `node`/`go` no existen todavía.
- La ruta de actualización del kit vendorizado (E-2 de `docs/IDEAS.md`).
- Verificar la experiencia dentro de cada asistente (que Claude Code u opencode
  efectivamente invoquen las skills): la suite verifica los archivos y el contrato,
  no el asistente.

## Historial

- 2026-08-07: creada (draft) y promovida a `active` en la iteración 4. Automatiza
  SPEC-017 SC-004 y convierte la campaña manual de usabilidad del derivado en
  suite versionada. Su primera corrida dejó V-1, V-2 y V-3 en `docs/IDEAS.md`.
- 2026-08-08: `/clarify` agrega FR-US1-006/007 y FR-US2-007/008/009 —guardia
  estructural de los escenarios, carpeta como infraestructura compartida, marca
  del workspace antes de borrar, matriz del workflow y verificación de residuo—.
  Implementados el mismo día: marca `.sdd-e2e-workspace` en `tests/e2e/lib/entorno.py`,
  guardias estructurales en los dos unitarios del harness, y matriz + paso de
  residuo afirmados sobre `.github/workflows/e2e.yml`.
- 2026-08-09: reabierta por K-4 de `docs/IDEAS.md`. US3 revierte la prohibición
  del paso `e2e` que US2 imponía (FR-US2-003, SC-003): la premisa de costo nunca
  se había medido y resultó falsa —16,6 s contra los 17,2 s del pipeline entero—,
  y "cableada al ciclo de cada commit" describía algo que no pasaba (el pipeline
  corre al cerrar iteración, no en cada commit). El acople que sí era real —la
  carpeta arrastrada a `coverage`— se resolvió antes en
  [[SPEC-005-desduplicar-ssot]] FR-007, declarando la propiedad en vez de omitir
  la clave. El aislamiento de `pytest` a secas, el workspace y el residuo quedan
  intactos.
