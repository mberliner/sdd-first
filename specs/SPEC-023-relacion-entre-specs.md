# SPEC-023-relacion-entre-specs: La relación entre specs se declara al crearlas y se verifica sola

## User Story 1 (Priority P1) — crear una spec enlazada a la que extiende o reemplaza

Como creador de specs, quiero que al crear una spec que extiende o reemplaza a
otra el enlace quede escrito **en los dos documentos**, para que la relación no
dependa de que alguien se acuerde de anotarla del otro lado.

**Why this priority:** es el momento en que la información existe y es barata de
escribir. Anotada después, no se anota.

**Independent Test:** `sdd_spec.py "titulo" --extends SPEC-021` crea la spec
nueva con `Extiende: SPEC-021` y agrega `Extendida por: <la nueva>` en SPEC-021;
si no puede escribir el recíproco, aborta sin crear nada.

## User Story 2 (Priority P2) — los enlaces declarados se verifican solos

Como mantenedor del SDD, quiero que `check_traceability.py` valide la sección de
relaciones, para que los enlaces sean reales, recíprocos y no apunten a specs no
vigentes.

**Why this priority:** un enlace escrito a mano y nunca verificado envejece; pero
primero tiene que existir la sección que se valida (US1).

**Independent Test:** una spec híbrida sin la sección, con una referencia a una
spec inexistente, sin enlace inverso, o `active` dependiendo de una `draft`,
falla `check_traceability.py` con código 1.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** [SPEC-022](SPEC-022-reusar-specs-existentes.md)
  gobierna la decisión previa —reusar una spec o crear otra— y su triage ofrece
  estas banderas como salida, pero declarar y verificar la relación entre dos
  specs es una capacidad separable: se implementa, se testea y se entrega sin
  tocar el reuso. Se separó de SPEC-022 cuando esa spec llegó a 31 requisitos,
  cortando por historia completa y sin partir ninguna. Son hermanas, no
  dependientes: **ninguna necesita a la otra para entregarse**, así que no se
  enlazan con `Depende de:`. Enlazarlas obligaría a que ambas pasen a `active`
  juntas (FR-US2-007), un encadenamiento sin fundamento técnico.

## Clarifications

### Session 2026-08-10

- Q: ¿`--supersedes` degrada la spec vieja al crear la nueva? → A: No. La nueva
  nace `draft`; degradar en ese momento dejaría la capacidad sin spec vigente y
  rompería a toda spec `active` que dependa de ella. La transición ocurre al
  cerrar la iteración, cuando la nueva pasa a `active` (FR-US1-003).
- Q: ¿Dónde vive la gramática de la sección? → A: en
  `templates/docs/SPEC-FORMAT.md`, SSOT del formato de spec según `00-INDEX.md`.
  Los requisitos de esta spec la exigen por referencia y no la reproducen: dos
  copias normativas del mismo detalle es justo lo que prohíbe el Principio IV.
- Q: ¿Qué se considera "vacío" en un campo de la sección? → A: el em dash `—`, el
  en dash `–`, el guion simple `-` o el campo sin valor. Las specs se escriben a
  mano y en consolas que no siempre producen el mismo carácter; tratarlos
  distinto convertiría un detalle tipográfico en una violación.
- Q: ¿Las specs `casero` también se migran? → A: No. `SPEC-000-naming.md` la
  genera `core/render.py` desde el config: agregarle la sección a mano
  reaparecería como drift en el paso `render` del pipeline. La validación de la
  sección corre solo sobre specs `hibrido`: que una `casero` la tenga o no le es
  indiferente.
- Q: ¿Cuándo corresponde `Depende de:` y cuándo basta mencionar la otra spec en
  prosa? → A: `Depende de: B` significa que **esta spec no puede entregarse sin B
  implementada**; por eso FR-US2-007 encadena los estados. Citar un invariante de
  B, compartir archivos con B o haberse diseñado junto a B no es depender: va en
  prosa. `Extiende: B` es ampliar el alcance de B sin reemplazarla, con B
  vigente. El criterio vive en `SPEC-FORMAT.md` junto con la gramática, y explica
  por qué SPEC-022 y esta no se enlazan pese a ser hermanas.
- Q: `Es dependencia de:` era el inverso de `Extiende:` y de `Depende de:` a la
  vez. ¿Se deja ambiguo? → A: No. Se agrega `Extendida por:` y los campos quedan
  en tres pares simétricos, así el grafo es tipado en ambas direcciones y el
  validador puede nombrar el campo que falta. Agregar un campo cuesta poco antes
  de migrar 22 specs y mucho después.
- Q: Hay `--extends` y `--supersedes`, ¿por qué no un `--depends`? → A: porque
  las dos primeras **resuelven el triage** de SPEC-022 —son respuestas a "esta
  capacidad se solapa con otra"— y se saben en el momento de crear. `Depende de:`
  casi nunca: se descubre escribiendo los FR, cuando `sdd_spec.py` ya terminó.
  Una bandera que casi siempre llegaría vacía no evitaría el olvido del
  recíproco; lo que sí lo evita es poder cerrarlos después (FR-US2-011).
- Q: ¿Qué ejecuta la migración de FR-US2-008/009: un script suelto, una bandera
  del validador? → A: `core/sdd_doctor.py`, que ya es la herramienta que
  diagnostica y autorepara, con la lógica de parseo viviendo en
  `check_traceability.py` para no duplicar parseadores. El validador no escribe:
  un gate que modifica lo que valida deja de ser gate.
- Q: ¿Es una migración de una sola vez? → A: No. La misma operación cierra los
  recíprocos de un `Depende de:` escrito a mano hoy o dentro de un año; la
  migración inicial es su primera corrida, no su único uso.
- Q: ¿A qué estados puede apuntar `Supersede:` en una spec `active`? → A: a
  cualquiera, y muy especialmente a `superseded`: reemplazar una spec y dejarla
  no vigente es exactamente el final feliz de esa relación. La restricción de
  FR-US2-007 aplica solo a `Depende de:` y `Extiende:`, que expresan apoyo en
  algo que tiene que seguir en pie.
- Q: ¿Quién implementa `--new --rationale`, esta spec o SPEC-022? → A: `--new`
  resuelve el triage y pertenece a SPEC-022; `--rationale` escribe en la sección
  de relaciones y pertenece acá. Con SPEC-022 sola, `--new` crea la spec igual y
  `--rationale` avisa que todavía no hay sección donde escribir.

## Acceptance Scenarios

### US1 — creación con enlace

- **Given** `--extends SPEC-NNN` **When** se crea la spec **Then** la nueva
  declara `Extiende: SPEC-NNN`, SPEC-NNN declara `Extendida por:` la nueva, y las
  dos pasan `check_traceability`.
- **Given** `--supersedes SPEC-NNN` **When** se crea la spec **Then** SPEC-NNN
  conserva su estado hasta que la nueva pase a `active`.
- **Given** `--supersedes SPEC-NNN` con una spec `active` que depende de SPEC-NNN
  **When** se ejecuta **Then** aborta con código ≠ 0 antes de escribir nada.
- **Given** una spec referenciada que no tiene la sección donde escribir el
  recíproco **When** se ejecuta **Then** aborta sin crear archivo, sin fila de
  registro y sin tocar `.sdd/current-spec`.
- **Given** `--extends SPEC-A --extends SPEC-B --supersedes SPEC-C` **When** se
  crea la spec **Then** la nueva declara las tres referencias en los campos que
  les corresponden y las tres referenciadas reciben su recíproco.
- **Given** varias referencias donde una sola es inválida —inexistente, no
  vigente o sin sección— **When** se ejecuta **Then** aborta con código ≠ 0 sin
  haber escrito el recíproco de ninguna de las válidas.
- **Given** `--extends SPEC-A --supersedes SPEC-A` **When** se ejecuta **Then**
  aborta con código ≠ 0 antes de escribir nada.

### US2 — validación

- **Given** una spec híbrida sin la sección **When** corre `check_traceability`
  **Then** falla nombrando la spec.
- **Given** `Depende de: SPEC-X` sin `Es dependencia de:` del otro lado **When**
  corre `check_traceability` **Then** falla nombrando la spec y el campo ausente.
- **Given** `Extiende: SPEC-X` cuyo recíproco en SPEC-X es `Es dependencia de:`
  en vez de `Extendida por:` **When** corre `check_traceability` **Then** falla:
  el par tiene que ser el que corresponde al tipo de relación.
- **Given** una spec `active` con `Depende de:` hacia una `draft` **When** corre
  `check_traceability` **Then** falla; con `Es dependencia de:` hacia la misma
  `draft`, pasa.
- **Given** una spec `casero` generada por `render.py` sin la sección **When**
  corre el pipeline **Then** pasa, y el paso `render` no reporta drift.
- **Given** el repositorio migrado **When** corre `check_traceability` con la
  reciprocidad activa **Then** pasa sin violaciones: todo campo directo
  preexistente tiene del otro lado el inverso que le corresponde.
- **Given** un `Depende de:` escrito a mano sin su recíproco **When** se corre
  `sdd_doctor` **Then** el recíproco queda escrito y `check_traceability` pasa,
  sin importar cuánto haya pasado desde la migración inicial.
- **Given** una spec `hibrido` creada a mano sin la sección después de la
  migración **When** se corre `sdd_doctor` **Then** la sección queda inyectada
  con sus campos vacíos y `check_traceability` pasa.
- **Given** una spec `active` con `Supersede:` hacia una `superseded` **When**
  corre `check_traceability` **Then** pasa: la restricción de estado no alcanza a
  ese campo.

## Functional Requirements

### US1 — enlaces al crear (`core/sdd_spec.py`, plantilla)

- **FR-US1-001** MUST: `--extends SPEC-NNN` y `--supersedes SPEC-NNN` crean la
  spec nueva y escriben la relación en **ambos** sentidos: el campo
  correspondiente en la spec nueva y su recíproco (`Extendida por:` /
  `Superseded por:`) en la referenciada. Ambas banderas son **repetibles** y
  combinables entre sí —una spec puede nacer extendiendo a dos y reemplazando a
  una tercera—; cada aparición agrega una referencia al campo que le
  corresponde. Apuntar la **misma** `SPEC-NNN` con las dos banderas aborta con
  código ≠ 0: extenderla y reemplazarla a la vez es contradictorio.
- **FR-US1-002** MUST: `--rationale="<texto>"` inserta el texto en *Por qué no
  cabe en una spec existente* de la spec nueva. La bandera `--new` que resuelve
  el triage pertenece a SPEC-022 y crea la spec con o sin esta; sin la sección de
  relaciones implementada, `--rationale` avisa que no hay dónde escribir y no
  aborta la creación.
- **FR-US1-003** MUST: `--supersedes` **no** cambia el estado de la spec
  referenciada al crear: la nueva nace `draft` y degradar la vieja en ese momento
  dejaría la capacidad sin spec vigente y a toda spec `active` que dependa de
  ella violando FR-US2-007. El paso a `superseded` ocurre en el cierre de
  iteración, junto con el paso de la nueva a `active`, y lo documenta el playbook
  (FR-US1-007).
- **FR-US1-004** MUST: la creación es atómica. `sdd_spec.py` valida todo lo que
  necesita sobre **cada una** de las referencias recibidas (existencia de la spec
  referenciada, estado vigente, presencia de la sección donde va a escribir el
  recíproco, ausencia del conflicto de FR-US1-001 y —para `--supersedes`— que
  ninguna spec `active` dependa de la referenciada) **antes** de escribir el
  primer byte; que una sola referencia falle aborta la ejecución entera;
  si alguna validación falla, aborta con código ≠ 0 dejando specs, registro y
  `.sdd/current-spec` sin modificar.
- **FR-US1-005** MUST: `templates/specs/SPEC-TEMPLATE.md` incluye la sección
  "Relación con specs existentes" con sus seis campos vacíos, y
  `specs/SPEC-TEMPLATE.md` se mantiene byte a byte idéntica (invariante de
  SPEC-005 FR-004).
- **FR-US1-006** MUST: cuando esa plantilla existe, `sdd_spec.py` rellena los
  campos dentro de ella en vez de construir una sección propia; el cuerpo mínimo
  sin plantilla —comportamiento preexistente— la incluye con todos los campos
  vacíos.
- **FR-US1-007** MUST: `templates/docs/playbooks/sdd-spec.md` documenta cuándo
  usar `--extends` y `--supersedes` —con el criterio de FR-US2-002— y que la spec
  reemplazada pasa a `superseded` al cerrar la iteración, no al crear la nueva.

### US2 — formato y validación (`core/check_traceability.py`)

- **FR-US2-001** MUST: `templates/docs/SPEC-FORMAT.md` —SSOT del formato de spec
  según `00-INDEX.md`— declara la sección "Relación con specs existentes" como
  obligatoria en specs `hibrido` y define su gramática: los campos, el formato de
  sus valores y los marcadores de vacío. Ningún otro documento la reproduce.
- **FR-US2-002** MUST: `SPEC-FORMAT.md` declara además **cuándo** corresponde
  cada campo, no solo cómo se escribe: `Depende de: B` cuando la spec no puede
  entregarse sin B implementada —de ahí que FR-US2-007 encadene los estados—;
  `Extiende: B` cuando amplía el alcance de B sin reemplazarla; `Supersede: B`
  cuando la reemplaza. Citar un invariante de B, compartir archivos con B o
  haberse diseñado junto a B **no** es depender: va en prosa. Sin este criterio
  el validador verificaría forma sin significado y cada autor enlazaría distinto.
- **FR-US2-003** MUST: los campos forman tres pares simétricos —`Extiende:` ↔
  `Extendida por:`, `Depende de:` ↔ `Es dependencia de:`, `Supersede:` ↔
  `Superseded por:`— de modo que el tipo de la relación se lee desde cualquiera
  de los dos lados y una violación puede nombrar el campo exacto que falta.
- **FR-US2-004** MUST: `check_traceability.py` exige esa sección en toda spec
  `hibrido` e implementa la gramática declarada en `SPEC-FORMAT.md`, incluidos
  sus marcadores de vacío. Las specs de otro formato no se validan contra ella,
  tengan o no la sección.
- **FR-US2-005** MUST: `check_traceability.py` valida que toda spec referenciada
  en esos campos exista como archivo en disco y como fila del registro; una
  referencia colgada es violación.
- **FR-US2-006** MUST: `check_traceability.py` exige reciprocidad en los tres
  pares de FR-US2-003: cada campo directo declarado en A requiere su recíproco en
  B, y la falta del enlace inverso es violación que nombra la spec y el campo
  ausente.
- **FR-US2-007** MUST: en una spec `active`, `check_traceability.py` rechaza
  `Depende de:` o `Extiende:` apuntando a specs en estado no vigente (`draft`,
  `superseded`, `archived`, `notas`): ambos expresan apoyo en algo que tiene que
  seguir en pie. `Supersede:` queda **fuera de la restricción** —apuntar a una
  spec `superseded` es el desenlace normal de reemplazarla—, igual que los tres
  campos inversos (`Extendida por:`, `Es dependencia de:`, `Superseded por:`),
  que pueden apuntar a cualquier estado.
- **FR-US2-008** MUST: `core/sdd_doctor.py` —dueño de las dos operaciones, según
  FR-US2-011— inyecta la sección con sus campos vacíos en las specs `hibrido` que
  no la tengan, o con las relaciones ya escritas en su cuerpo cuando las haya, de
  modo que el pipeline siga verde. Las specs `casero` y las
  generadas por `core/render.py` quedan **fuera**: agregarles la sección a mano
  produciría drift en el paso `render`.
- **FR-US2-009** MUST: la migración **cierra los recíprocos que ya existen**, no
  solo agrega campos vacíos: por cada campo directo declarado en A, la spec B
  recibe el inverso que le corresponde según FR-US2-003. Al escribirse este
  requisito hay cinco enlaces sin su vuelta —SPEC-001, SPEC-005, SPEC-016 y
  SPEC-017 desde SPEC-022, y SPEC-005 desde SPEC-023—, así que sin este paso
  FR-US2-006 nacería fallando sobre specs `active` que nadie tocó.
- **FR-US2-010** MUST: la migración aplica el criterio de FR-US2-002 a los
  enlaces preexistentes: los que no son dependencia de entrega se bajan a prosa
  en vez de arrastrarse como campos. El `Depende de: SPEC-005` de esta spec es el
  primer caso —cita el invariante de plantilla de SPEC-005, no la necesita
  implementada— y se resuelve en la misma migración.
- **FR-US2-011** MUST: quien ejecuta **la inyección de la sección ausente
  (FR-US2-008) y el cierre de recíprocos (FR-US2-009)** es
  `core/sdd_doctor.py` —la herramienta que ya diagnostica y autorepara—, con la
  lógica de lectura de la sección viviendo en `check_traceability.py` para no
  duplicar parseadores. El validador no escribe: un gate que modifica lo que
  valida deja de ser gate. Ambas operaciones son **repetibles**, no un paso único
  de migración: cierran igual los recíprocos de un `Depende de:` escrito a mano
  hoy o dentro de un año, e inyectan la sección en una spec `hibrido` creada a
  mano después de la migración; la migración inicial es su primera corrida. Por eso no hace
  falta una bandera `--depends` en la creación: la dependencia se descubre
  escribiendo los FR, cuando `sdd_spec.py` ya terminó.

## Key Entities

- `core/sdd_spec.py` — `--extends`, `--supersedes`, `--rationale`.
- `core/check_traceability.py` — validación de la sección de relaciones.
- `core/sdd_doctor.py` — cierre repetible de recíprocos.
- `templates/specs/SPEC-TEMPLATE.md` — la sección en la plantilla.
- `templates/docs/SPEC-FORMAT.md` — SSOT de la gramática.
- `templates/docs/playbooks/sdd-spec.md` — cuándo usar cada bandera.

## Success Criteria

- **SC-001** `--extends` y `--supersedes` dejan ambas specs enlazadas en los dos
  sentidos y el registro coherente, en un estado que pasa `check_traceability.py`.
- **SC-002** `--supersedes` no altera el estado de la spec referenciada ni deja
  huérfana a ninguna spec `active` que dependa de ella.
- **SC-003** Un fallo de validación previa deja el árbol de trabajo idéntico a
  antes de la ejecución: sin spec nueva, sin fila y sin declaración.
- **SC-004** `check_traceability.py` rechaza, con mensaje que nombra la spec y el
  campo: sección ausente, referencia inexistente, enlace inverso ausente y
  dependencia `active` → estado no vigente.
- **SC-005** Todas las specs `hibrido` vigentes tienen la sección tras la
  migración y el pipeline sigue verde, sin drift en el paso `render`.
- **SC-006** La gramática de la sección **y el criterio de cuándo usar cada
  campo** aparecen completos en un único documento del repositorio.
- **SC-007** Activar la reciprocidad sobre el repositorio migrado no produce
  ninguna violación: la migración cerró las vueltas de los enlaces preexistentes
  en vez de dejarlas como deuda que estrena el validador.
- **SC-008** Leyendo solo el lado inverso de una relación se distingue si la otra
  spec la extiende, depende de ella o la reemplaza.
- **SC-009** Una sección ausente y un recíproco faltante se resuelven corriendo
  `sdd_doctor`, sin edición manual y sin importar si son parte de la migración
  inicial o de una spec escrita meses después.

## Assumptions

- El registro es la fuente de verdad de estados; una spec ausente del registro ya
  la detecta la verificación de consistencia preexistente.
- Las relaciones son pocas por spec: la validación recorre todas las specs sin
  necesidad de índices ni caché.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-US1-001 | tests/unit/test_sdd_spec.py |
| FR-US1-002 | tests/unit/test_sdd_spec.py |
| FR-US1-003 | tests/unit/test_sdd_spec.py |
| FR-US1-004 | tests/unit/test_sdd_spec.py |
| FR-US1-005 | tests/unit/test_spec_format_reference.py |
| FR-US1-006 | tests/unit/test_sdd_spec.py |
| FR-US1-007 | tests/unit/test_template_paths.py |
| FR-US2-001 | tests/unit/test_spec_format_reference.py |
| FR-US2-002 | tests/unit/test_spec_format_reference.py |
| FR-US2-003 | tests/unit/test_check_traceability.py |
| FR-US2-004 | tests/unit/test_check_traceability.py |
| FR-US2-005 | tests/unit/test_check_traceability.py |
| FR-US2-006 | tests/unit/test_check_traceability.py |
| FR-US2-007 | tests/unit/test_check_traceability.py |
| FR-US2-008 | tests/unit/test_check_traceability.py, tests/unit/test_sdd_doctor_wiring.py |
| FR-US2-009 | tests/unit/test_check_traceability.py, tests/unit/test_sdd_doctor_wiring.py |
| FR-US2-010 | tests/unit/test_check_traceability.py |
| FR-US2-011 | tests/unit/test_check_traceability.py, tests/unit/test_sdd_doctor_wiring.py |

## Fuera de alcance

- El triage que decide si conviene reusar o crear, y `--reuse`: es
  [SPEC-022](SPEC-022-reusar-specs-existentes.md).
- Relaciones más allá de las tres declaradas —extender, depender, reemplazar; seis
  campos contando sus inversos (FR-US2-003)— (p. ej. "conflicto con", "duplica
  parcialmente"): el vocabulario se amplía cuando aparezca el caso, no antes.

## Historial

- 2026-08-11: implementada y pasada a `active` (iteración 9). La escritura de la
  sección vive en `core/spec_relations.py` —nuevo— y la lectura en
  `check_traceability.py`, como exige FR-US2-011. La migración cubrió las 22
  specs `hibrido` y cerró los recíprocos que SPEC-022 dejó abiertos; de paso se
  declaró el primer `Supersede:` real del repositorio (SPEC-017 → SPEC-006), que
  ejercita la excepción de estado de FR-US2-007 sobre datos verdaderos.
- 2026-08-10: creada (draft) al partir SPEC-022, que había llegado a 31
  requisitos. El corte respeta historias completas: acá vienen las banderas de
  enlace (`--extends`, `--supersedes`, `--rationale`), la sección en la plantilla
  y toda la validación de relaciones; en SPEC-022 quedan `--reuse`, el triage y
  el aviso del gate. La gramática pasa a exigirse por referencia a
  `SPEC-FORMAT.md` en vez de reproducirse (hallazgo C1 de `analyze`), se declaran
  los marcadores de vacío tolerados y se agregan los escenarios de reciprocidad,
  estado no vigente y specs generadas.
- 2026-08-10: resueltos D1 y D2 de `analyze`. D1: se quita el enlace
  `Depende de: SPEC-022`. La dependencia estaba invertida —ningún requisito de
  esta spec necesita el reuso— y enlazarlas en cualquier dirección encadenaría el
  paso a `active` de una al de la otra sin motivo técnico; la relación es de
  hermanas y queda en prosa. D2: la migración pasa a cerrar los recíprocos
  preexistentes, porque con cinco enlaces sin vuelta la reciprocidad habría
  nacido fallando sobre specs `active` intactas.
- 2026-08-10: sesión `clarify`. (1) Se declara la **semántica** de los campos, no
  solo su gramática: `Depende de:` es dependencia de entrega, y citar un
  invariante o compartir archivos va en prosa (FR-US2-002). Aplicado a esta misma
  spec: se quita `Depende de: SPEC-005`, que solo citaba su invariante de
  plantilla. (2) Se agrega `Extendida por:` y los campos quedan en tres pares
  simétricos, para que el grafo sea tipado en ambos sentidos (FR-US2-003).
  (3) `--new` queda en SPEC-022 y `--rationale` acá (FR-US1-002). (4) FR-US2-004
  deja de reproducir los marcadores de vacío que SPEC-FORMAT declara (hallazgo E1)
  y se parte FR-US1-004 en plantilla y relleno, que tenían cobertura distinta.
- 2026-08-10: revisión externa. Se declara **quién ejecuta** el cierre de
  recíprocos —`sdd_doctor`, que ya autorepara, con el parseo en
  `check_traceability`— y que la operación es repetible, no un paso único de
  migración (FR-US2-011, SC-009). Eso responde de paso por qué no hay `--depends`:
  la dependencia se descubre escribiendo los FR, no al crear la spec, y el
  recíproco se cierra después. Se declara además que `Supersede:` queda fuera de
  la restricción de estado —apuntar a una `superseded` es su desenlace normal—,
  que antes solo estaba implícito por omisión (FR-US2-007). Se descartó tratar
  como hallazgo que los tests aún no cubran estos FR: es el estado normal de una
  spec `draft`.
- 2026-08-10: segunda revisión externa. Aceptados dos hallazgos y uno propio.
  (1) Se declara la **aridad** de las banderas: son repetibles y combinables, y
  apuntar la misma spec con `--extends` y `--supersedes` aborta; la atomicidad de
  FR-US1-004 pasa a cubrir el conjunto entero de referencias, no una sola.
  (2) FR-US2-008 estaba en pasiva y sin sujeto: la inyección de la sección
  ausente es de `sdd_doctor`, igual que el cierre de recíprocos, y también es
  repetible —una spec `hibrido` escrita a mano después de la migración nacería
  sin sección—. (3) *Fuera de alcance* decía "las cinco relaciones declaradas",
  cifra anterior a `Extendida por:`: son tres relaciones en seis campos
  (FR-US2-003). Rechazados dos: que el `Coverage mapping` no tenga aún
  aserciones —ya descartado arriba, y su remediación es seguir el ciclo de vida
  tal cual está— y que FR-US2-002/003 dupliquen `SPEC-FORMAT.md` violando el
  Principio IV: un requisito que exige que ese documento declare algo tiene que
  decir **qué**, o es inverificable y SC-006 no se puede evaluar. La poda
  legítima ya se hizo con los marcadores de vacío (hallazgo E1); el riesgo de
  drift restante se ataja con `test_spec_format_reference.py`, no borrando los
  requisitos.
