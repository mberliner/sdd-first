# SPEC-022-reusar-specs-existentes: Antes de crear una spec, reusar la existente que ya cubre la capacidad

## User Story 1 (Priority P1) — adoptar una spec existente en vez de crear otra

Como creador de specs, quiero que al arrancar una funcionalidad nueva el kit me
deje **adoptar una spec vigente en lugar de crear otra**, para que la capacidad
viva en un único documento (Principio IV) y no se multipliquen specs solapadas.

**Why this priority:** es el camino que hoy no existe. `sdd_spec.py` solo sabe
crear; reusar una spec implica editar `.sdd/current-spec` a mano, así que en la
práctica se crea una spec nueva siempre.

**Independent Test:** `python core/sdd_spec.py --reuse SPEC-021 --fr FR-004` no
crea ningún archivo ni fila de registro y deja `SPEC-021-...` declarada en
`.sdd/current-spec` si FR-004 ya está escrito en esa spec; si no lo está, aborta
indicando dónde escribirlo.

## User Story 2 (Priority P2) — el triage avisa qué spec ya cubre la capacidad

Como creador de specs, quiero que crear una spec que se solapa con una vigente
—por título o porque gobierna los mismos archivos— exija resolver explícitamente
el solape, para que la decisión de duplicar quede escrita y auditable en vez de
ser un descuido.

**Why this priority:** es la red de seguridad, no el camino. Con la US1 sola el
reuso ya funciona cuando el asistente sigue el playbook; el triage existe para
cuando no lo sigue. Vale menos que el camino que protege.

**Independent Test:** crear una spec cuyo título comparte palabras significativas
con una vigente, o que declara tocar un archivo ya gobernado por otra spec,
aborta con código ≠ 0, lista las candidatas y no escribe nada en disco.

## User Story 3 (Priority P3) — el gate dice qué specs ya gobiernan el archivo

Como quien está por editar código sin spec declarada, quiero que el gate me diga
**qué specs ya gobiernan ese archivo**, para decidir si reuso una en vez de crear
otra en el momento exacto en que la pregunta importa.

**Why this priority:** es el punto donde la señal es más dura —el archivo
concreto ya se conoce— pero llega última por dependencia: sin `--reuse` el aviso
no tendría salida que ofrecer, y sin el índice de la US2 no tendría qué nombrar.
Baja por dependencia, no por valor.

**Independent Test:** un `sdd_gate.py core/sdd_spec.py` que bloquea por falta de
spec vigente imprime en el motivo los IDs de las specs que ya nombran ese archivo
y sugiere `sdd_spec.py --reuse SPEC-NNN --fr FR-NNN`.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** [SPEC-001](SPEC-001-agnostic-core.md), [SPEC-017](SPEC-017-gate-decision-spec-first.md)
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** SPEC-003 especifica el happy path de
  creación de una spec y SPEC-017 qué decide bloquear el gate; ninguna de las dos
  gobierna la decisión previa —reusar o crear—. La US3 toca `sdd_gate.py` pero no
  cambia *qué* se bloquea (SSOT de SPEC-017): solo enriquece el motivo del
  bloqueo con información de reuso. Declarar y validar la relación entre specs es
  una capacidad distinta y vive en
  [SPEC-023](SPEC-023-relacion-entre-specs.md), hermana de esta: nacieron del
  mismo corte y se referencian, pero **ninguna depende de la otra para
  entregarse**, así que no se enlazan con `Depende de:` —hacerlo encadenaría el
  paso a `active` de una al de la otra sin necesidad técnica. Por el mismo
  criterio (SPEC-023 FR-US2-002) tampoco se enlazan SPEC-005 —de la que solo se
  cita el invariante de plantilla— ni SPEC-016, que comparte terreno pero no
  condiciona esta entrega.

## Clarifications

### Session 2026-08-10

- Q: ¿Qué pasa con la prueba del test rojo (necesidad funcional)? → A: Se deja
  para una iteración posterior: es valioso pero toca el ciclo draft→active, se
  mide antes de cablear.
- Q: ¿El triage compara solo títulos, o también el contenido (User Story /
  Independent Test) de cada spec? → A: Títulos **y** archivos gobernados (índice
  invertido). El índice de ámbitos extraído del cuerpo queda en `docs/IDEAS.md`
  como idea pre-spec.
- Q: ¿El script decide por sí solo si hay duplicación? → A: No. Lista candidatas
  con su puntaje y exige una decisión explícita; es red de seguridad, no árbitro.
- Q: Si `--reuse` adopta una spec `active`, sus FR viejos ya satisfacen al gate:
  ¿no queda el gate abierto sin haber escrito nada? → A: Sí, y por eso `--reuse`
  exige `--fr FR-NNN` y verifica que ese requisito ya esté escrito en la spec
  adoptada antes de declararla (FR-US1-003). Reusar no puede costar menos
  evidencia que crear; el criterio es el mismo de SPEC-017 FR-US3-001 y se aplica
  al FR nuevo, no a los viejos.
- Q: Adoptar una spec `active` y escribirle un FR deja rojo a
  `check_traceability` (FR sin fila en *Coverage mapping*) hasta que exista el
  test. ¿Se tolera ese rojo como "algo pendiente", al estilo TDD? → A: No, porque
  no es el mismo rojo. El de los tests no bloquea commits (los tests corren en el
  pipeline); el de trazabilidad sí, porque `sdd-traceability` está en el
  pre-commit con `always_run`, así que impediría hasta commitear el test rojo.
  El ciclo rojo→verde se consigue igual: `--reuse` exige que el FR nuevo traiga
  su fila de *Coverage mapping* y que el archivo de test exista, y **el test
  puede —y se espera que— falle**. Eso es el rojo de TDD, no un test previo.
- Q: ¿Y en un proyecto cuyos tests caen dentro de `dirs.source_roots`? Ahí no se
  puede crear el test sin spec declarada ni declarar sin el test. → A: en ese
  layout `--reuse` exige la fila de *Coverage mapping* pero tolera que el archivo
  todavía no exista: se abre el gate, se crea el test y recién entonces se
  commitea, sin pasar nunca por un commit en rojo (FR-US1-004).
- Q: ¿La exigencia de fila y test también rige al adoptar una spec `draft`? → A:
  No. `check_traceability` no exige *Coverage mapping* sobre `draft`, así que ahí
  el costo no evitaría ningún rojo y haría que adoptar saliera más caro que
  crear —el sesgo que esta spec existe para eliminar—. Sobre `draft` basta el FR
  escrito.
- Q: ¿`sdd_spec.py` verifica que ese test efectivamente falle? → A: No en esta
  iteración: exigiría ejecutar la suite desde el script. Queda en *Fuera de
  alcance* junto con el resto de la prueba de "test rojo".
- Q: ¿Dónde aterriza el FR nuevo dentro de la spec adoptada? → A: en la User
  Story cuyo alcance cubre la capacidad, con el ID que corresponda a esa historia
  (`FR-USk-NNN` en specs multi-HU, `FR-NNN` en las de una sola). Si ninguna la
  cubre, se agrega una US nueva a la spec adoptada —con su prioridad y su
  *Independent Test*— y el FR nace ahí. Así cada FR sigue perteneciendo a un
  corte vertical y la spec receptora no se degrada con cada adopción.
- Q: ¿Qué forma de ID acepta `--fr`, y cómo se compara? → A: cualquiera con la
  forma `FR-[A-Za-z0-9-]+`, el mismo patrón que ya usan `check_traceability` y el
  gate; el script no impone convención. La comparación contra la spec es por
  igualdad exacta del ID declarado, nunca por substring: pasar `FR-007` no
  satisface a un requisito declarado como `FR-US1-007`.
- Q: `--touches` es opcional; si nadie lo pasa, el índice invertido nunca se usa.
  ¿Cómo se activa sin depender de que alguien se acuerde? → A: el triage deduce
  las rutas del propio título: las mismas palabras significativas que compara
  contra los títulos del registro se buscan en el **nombre de archivo** de las
  rutas del índice. Determinista, sin git, sin mtime y sin estado persistente.
  `--touches` queda como afinamiento explícito.
- Q: ¿Por qué no inferirlas de git, de la fecha de modificación o de un rastro
  que deje el gate? → A: git ataría el kit a un VCS concreto; la mtime ya fue
  descartada en SPEC-017 (checkout, clone y stash la renuevan, un `touch` la
  falsea); un rastro del gate agregaría estado persistente que envejece. El
  título ya está en la mano del script.
- Q: Deducir del título con el vocabulario del propio dominio, ¿no vuelve
  candidata a media docena de specs? ("specs" aparece en casi toda ruta del kit)
  → A: por eso el match es contra el **stem** del archivo —no contra cualquier
  segmento de la ruta— y el kit siembra `specs.triage.stopwords` con su propio
  vocabulario (`spec`, `sdd`), que cada derivado ajusta al suyo.
- Q: ¿Cómo se extraen las rutas de *Key Entities*, si cada spec las escribe
  distinto? → A: es ruta todo token que contenga `/` o termine en una extensión
  de archivo conocida, cortando la entrada en el `—` de la descripción y en el
  `·` que separa varias. Un token sin directorio (`sdd_spec.py`) se resuelve por
  basename contra los archivos reales del repositorio; si no resuelve o resuelve
  a más de uno, se descarta. Una entrada conceptual sin ruta ("Registro de specs
  vigentes") no aporta nada al índice.
- Q: Si `--reuse` recibe solo el número (`SPEC-021`), ¿cómo se resuelve el ID
  completo: buscando en `specs/` o en el registro? → A: en el registro, que es el
  SSOT de las specs vigentes; un glob sobre `specs/` encontraría también archivos
  sin registrar. Y lo que se escribe en `.sdd/current-spec` es siempre el ID
  completo: `sdd_gate` compara la declaración contra el nombre de archivo de la
  fila, así que declarar el número pelado haría que el gate rechazara la spec
  recién adoptada (FR-US1-002).
- Q: ¿Cómo lee `sdd_spec.py` el *Coverage mapping* para verificar la fila del FR?
  → A: reutilizando el parseo de `check_traceability.py`, no con un lector
  propio. Dos parseadores del mismo formato divergen y el script terminaría
  aceptando lo que el validador rechaza; `sdd_gate.py` ya importa de ese módulo
  (FR-US1-005).
- Q: ¿`spec` matchea el stem `sdd_spec`? → A: sí, porque la normalización trata
  `-` y `_` como separadores antes de tokenizar, a ambos lados de la comparación
  (FR-US2-006). Sin eso el stem sería un token único e inalcanzable.
- Q: ¿Por qué el índice invertido y no similitud semántica (TF-IDF/embeddings)?
  → A: Sobre ~20 specs que comparten todo el vocabulario del dominio, la
  similitud léxica rankea ruido; los embeddings exigirían red o una dependencia
  pesada, rompiendo el agnosticismo y el trabajo offline del kit. Las citas
  `SPEC-NNN` ya escritas en código y tests son señal dura y determinista.
- Q: La spec llegó a 31 FR y 4 historias, el doble que la más grande del repo.
  → A: se parte en dos por coherencia de historia, sin dividir ninguna US:
  decidir-y-adoptar queda acá; declarar-y-verificar la relación entre specs se va
  a [SPEC-023](SPEC-023-relacion-entre-specs.md). El corte no parte ninguna
  funcionalidad: el único roce era `--new --rationale`, que pasa entero a
  SPEC-023 junto con la sección donde escribe.

## Acceptance Scenarios

### US1 — adopción de una spec existente

- **Given** una capacidad que cabe en una spec vigente y su FR nuevo ya escrito
  **When** se corre `sdd_spec.py --reuse SPEC-NNN --fr FR-0XX` **Then** no se
  crea archivo ni fila y la spec existente queda declarada como vigente.
- **Given** `--reuse SPEC-NNN --fr FR-0XX` con el FR todavía sin escribir en la
  spec adoptada **When** se ejecuta **Then** aborta con código ≠ 0, no declara
  nada e indica dónde escribir el requisito.
- **Given** `--reuse` sobre una spec `superseded`/`archived`/inexistente **When**
  se ejecuta **Then** aborta con código ≠ 0 y no toca `.sdd/current-spec`.
- **Given** una spec adoptada `active` y el FR nuevo sin fila en el *Coverage
  mapping* **When** se corre `--reuse` **Then** aborta con código ≠ 0 y
  `check_traceability` nunca llega a ponerse rojo.
- **Given** una spec adoptada `draft` y el FR escrito sin fila de Coverage
  **When** se corre `--reuse` **Then** la spec queda declarada: sobre `draft` el
  validador no exige mapping y adoptar no cuesta más que crear.
- **Given** el FR, su fila y un test que **falla** **When** se corre `--reuse`
  **Then** la spec queda declarada: el rojo del test no impide adoptar ni
  commitear.
- **Given** un proyecto cuyos tests caen dentro de `dirs.source_roots` y el
  archivo de test todavía no existe **When** se corre `--reuse` **Then** la spec
  queda declarada igual, para que el gate abierto permita crearlo.

### US2 — triage

- **Given** un título que colisiona con una spec `active` o `draft` **When** se
  llama a `sdd-spec` sin bandera resolutoria **Then** lista las candidatas y
  aborta sin escribir nada.
- **Given** `--touches core/sdd_gate.py` **When** se crea una spec **Then** se
  listan como candidatas las specs que ya gobiernan ese archivo.
- **Given** un título cuyas palabras coinciden con el stem de un archivo del
  índice y ninguna `--touches` **When** se crea una spec **Then** el triage por
  archivo igual señala las specs de ese archivo.
- **Given** una palabra del título que figura en `specs.triage.stopwords`
  **When** corre el triage **Then** no genera candidatas por sí sola.

### US3 — aviso de reuso en el gate

- **Given** una edición de código sin spec declarada **When** el gate bloquea
  **Then** el motivo nombra las specs que ya gobiernan el archivo.
- **Given** una spec `draft` que nombra `core/nuevo.py` en *Key Entities* y ese
  archivo todavía no existe **When** el gate bloquea su creación **Then** el
  motivo nombra esa spec y sugiere `--reuse`.
- **Given** un archivo sin specs asociadas **When** el gate bloquea **Then** el
  mensaje es el actual, sin añadido y con el mismo código de salida.

## Functional Requirements

### US1 — adoptar sin crear (`core/sdd_spec.py`)

- **FR-US1-001** MUST: `--reuse SPEC-NNN[-slug]` no crea archivo de spec ni fila
  de registro: verifica que la spec exista en disco y esté `active` o `draft` en
  el registro y la declara en `.sdd/current-spec`. Si la spec no existe o su
  estado no es vigente, aborta con código ≠ 0 sin tocar nada.
- **FR-US1-002** MUST: cuando se pasa solo el número (`SPEC-021`), el ID completo
  se resuelve desde `SPECS_REGISTRY.md` —SSOT de las specs vigentes— y no por
  pattern matching sobre `specs/`, que devolvería también archivos sin registrar.
  Lo que se escribe en `.sdd/current-spec` es siempre el ID completo
  `SPEC-NNN-slug`: `sdd_gate` compara la declaración contra el nombre de archivo
  del registro, así que declarar el número pelado haría que el gate rechazara la
  spec que se acaba de adoptar. Si el número no resuelve a exactamente una fila,
  aborta nombrando las candidatas.
- **FR-US1-003** MUST: `--reuse` exige `--fr FR-NNN` —el identificador del
  requisito que la capacidad nueva agrega a la spec adoptada— y **solo declara la
  spec si ese FR ya está escrito en ella** con el criterio de contenido de
  SPEC-017 FR-US3-001 (declaración `**FR-NNN**` con texto propio más allá de la
  keyword). Si el FR no existe todavía, aborta con código ≠ 0, sin declarar nada,
  e imprime dónde escribirlo y con qué forma. Adoptar una spec no puede ser más
  barato que crearla: en ambos caminos el gate se abre contra un requisito
  escrito antes del código, nunca contra los FR viejos (Principio III).
- **FR-US1-004** MUST: cuando la spec adoptada está `active`, `--reuse` exige
  además que el FR indicado tenga su fila en el *Coverage mapping*; sin ella,
  aborta. Sobre `draft` no lo exige: `check_traceability` no valida el mapping en
  ese estado, así que pedirlo solo encarecería adoptar frente a crear. El archivo
  de test referenciado debe existir, **salvo** que su ruta caiga dentro de
  `dirs.source_roots`: en ese layout el gate impediría crearlo antes de declarar
  la spec, así que se tolera su ausencia y se avisa en la salida.
- **FR-US1-005** MUST: `sdd_spec.py` **reutiliza** el parseo de
  `check_traceability.py` para leer el *Coverage mapping* y las declaraciones de
  FR, en vez de escribir su propio lector de esas tablas. Dos parseadores del
  mismo formato divergen y harían que el script acepte lo que el validador
  rechaza; `sdd_gate.py` ya sienta el precedente importando `_parse_registry` e
  `iter_fr_declarations` de ese módulo (Principio IV).
- **FR-US1-006** MUST: `sdd_spec.py` no ejecuta la suite: exige que el test
  exista, no que pase. Un test rojo es el estado esperado al adoptar la spec y el
  punto de partida del ciclo rojo→implementación→verde.
- **FR-US1-007** MUST: `--fr` acepta cualquier identificador con la forma
  `FR-[A-Za-z0-9-]+` —el mismo patrón que ya usan `check_traceability` y
  `sdd_gate`— y lo compara contra los IDs declarados en la spec por igualdad
  exacta, nunca por substring.
- **FR-US1-008** MUST: `templates/docs/playbooks/sdd-spec.md` declara dónde
  escribir el FR nuevo en la spec adoptada: en la User Story cuyo alcance cubre
  la capacidad, con el ID de esa historia; si ninguna la cubre, se agrega una US
  nueva —con prioridad e *Independent Test*— y el FR nace ahí, junto con su fila
  de *Coverage mapping* y su test. La regla la aplica quien escribe, no el
  script: `sdd_spec.py` verifica que el FR exista, no dónde está.

### US2 — triage (`core/sdd_spec.py`, config, playbook)

- **FR-US2-001** MUST: el kit deriva un índice `archivo → [SPEC-NNN]` de tres
  fuentes ya presentes en el repositorio, sin metadatos nuevos: (a) las rutas
  nombradas en la sección *Key Entities* de cada spec, (b) las rutas de test del
  *Coverage mapping*, y (c) las citas `SPEC-NNN` que aparecen en los archivos de
  `dirs.source_roots` y `dirs.tests_unit`. El índice se computa en memoria bajo
  demanda; no se persiste ningún artefacto generado.
- **FR-US2-002** MUST: de *Key Entities* se toma como ruta todo token que
  contenga `/` o termine en una extensión de archivo conocida, cortando la
  entrada en el `—` de la descripción y en el `·` que separa varias. Un token sin
  directorio se resuelve por basename contra los archivos del repositorio y se
  descarta si no resuelve o resuelve a más de uno; una entrada conceptual sin
  ruta no aporta al índice.
- **FR-US2-003** MUST: el índice solo considera specs en estado `active` o
  `draft`, y **conserva las rutas con directorio explícito aunque todavía no
  existan en disco**: una spec `draft` nombra en *Key Entities* los archivos que
  va a crear, y son precisamente los que el gate va a bloquear primero —sin ellos
  FR-US3-001 quedaría ciego en el caso más frecuente, el archivo nuevo—. La misma
  tolerancia rige sobre las rutas de test del *Coverage mapping*, coherente con
  FR-US1-004, que ya admite el archivo de test ausente. Lo que se descarta son los
  tokens sin directorio que no resuelven por basename (FR-US2-002): son
  indeterminables, no proyectados. Una fuente ilegible o ausente reduce la
  cobertura del índice pero nunca provoca error.
- **FR-US2-004** MUST: `sdd_spec.py` acepta `--touches <ruta>` (repetible). Toda
  spec que el índice asocie a alguna de esas rutas es candidata, indicando en la
  salida qué archivo la señaló.
- **FR-US2-005** MUST: sin `--touches`, el triage por archivo igual corre: las
  palabras significativas del título —las mismas que normaliza y filtra
  FR-US2-006— se comparan contra el **stem** del nombre de archivo de cada ruta
  del índice, no contra la ruta completa, y toda spec asociada a una coincidencia
  es candidata. La salida indica qué palabra señaló qué ruta. Ninguna de las dos
  vías depende de un VCS, de la fecha de modificación de los archivos ni de
  estado persistente entre corridas.
- **FR-US2-006** MUST: además, `sdd_spec.py` compara el título pedido contra la
  columna *Título* de las specs `active` o `draft` de `SPECS_REGISTRY.md`. La
  comparación normaliza acentos y mayúsculas y **trata `-` y `_` como separadores
  de palabra** antes de tokenizar, tanto en el texto como en los stems de archivo
  de FR-US2-005: sin eso, `sdd_spec` sería un token único que ninguna palabra de
  un título alcanzaría. Descarta las palabras de
  `specs.triage.stopwords` y las más cortas que `specs.triage.min_word_len`, y
  marca candidata a toda spec que comparta al menos `specs.triage.min_matches`
  palabras. Los tres parámetros viven en `.sdd/config.yaml` con defaults en el
  kit; ninguna lista ni umbral se hardcodea en `core/` (Principio I, SPEC-001).
- **FR-US2-007** MUST: las candidatas se imprimen ordenadas con las de archivo
  primero —señal más fuerte que la léxica—, cada una con su ID, título completo y
  el motivo que la señaló (archivo o palabras coincidentes).
- **FR-US2-008** MUST: al haber candidatas, `sdd_spec.py` aborta con código ≠ 0
  salvo que se pase una bandera resolutoria: `--reuse` (FR-US1-001), `--new
  --rationale="<texto>"`, o las de enlace que declara
  [SPEC-023](SPEC-023-relacion-entre-specs.md).
- **FR-US2-009** MUST: la sección `specs.triage` de `.sdd/config.yaml` declarada
  pero vacía, o ausente, cae a los defaults del kit sin romper el pipeline
  (invariante de SPEC-021). El default de `stopwords` del propio kit incluye el
  vocabulario de su dominio (`spec`, `specs`, `sdd`), que de otro modo volvería
  candidata a casi toda spec.
- **FR-US2-010** MUST: `examples/config/config.yaml` —el catálogo de claves que
  `sdd_init` instala verbatim en cada derivado (SPEC-013 FR-008/FR-010)— declara
  `specs.triage` con sus tres claves, sus defaults y el comentario que explica
  para qué sirven, incluida la advertencia de sembrar `stopwords` con el
  vocabulario del propio dominio.
- **FR-US2-011** MUST: `templates/docs/playbooks/sdd-spec.md` documenta el
  procedimiento previo a crear: (1) leer `SPECS_REGISTRY.md` y correr el triage
  —que deduce las rutas del título y admite `--touches` para afinar—, (2)
  proponer al usuario reusar o crear, con la spec candidata nombrada, y (3)
  ejecutar `sdd_spec.py` con la bandera resolutoria que corresponda. `AGENTS.md`
  (SSOT del protocolo) referencia el playbook en su paso 4, sin duplicarlo.

### US3 — aviso de reuso en el gate (`core/sdd_gate.py`)

- **FR-US3-001** MUST: cuando el gate bloquea una edición por falta de spec
  vigente declarada, el motivo incluye los IDs y títulos de las specs que el
  índice asocia al archivo que se intentaba editar, y sugiere resolverlo con
  `sdd_spec.py --reuse SPEC-NNN --fr FR-NNN` o crear una spec nueva.
- **FR-US3-002** MUST: el índice se computa **solo** en el camino de bloqueo,
  nunca cuando el gate permite la edición: el gate corre en cada `PreToolUse` y
  no puede pagar un escaneo del repositorio por edición permitida. El indexador
  se expone como dependencia inyectable para que un test pueda verificar que no
  se invoca en el camino permitido.
- **FR-US3-003** MUST: si el índice queda vacío o su cómputo falla, el gate emite
  el mensaje de bloqueo actual sin el añadido y con el mismo código de salida. El
  aviso es informativo: no cambia qué se bloquea (SSOT de la política: SPEC-017).

## Key Entities

- `core/sdd_spec.py` — `--reuse`, `--fr`, `--touches`, triage.
- `core/sdd_gate.py` — aviso de reuso en el motivo del bloqueo.
- `core/sdd_config.py` — lectura de `specs.triage` con defaults.
- `specs/SPECS_REGISTRY.md` — fuente de títulos y estados del triage.
- `examples/config/config.yaml` — catálogo de claves que viaja al derivado.
- `templates/docs/playbooks/sdd-spec.md` — SSOT del procedimiento.

## Success Criteria

- **SC-001** `sdd_spec.py --reuse SPEC-NNN --fr FR-0XX` deja el repositorio sin
  archivos ni filas nuevas y con esa spec declarada en `.sdd/current-spec`, y
  **solo** si FR-0XX ya está escrito en ella; sobre una spec no vigente,
  inexistente, sin `--fr`, o con el FR aún sin escribir, aborta sin efectos.
- **SC-002** Tras `--reuse` con el FR ausente, `sdd_gate.decide` sobre un archivo
  de `dirs.source_roots` devuelve bloqueo; tras escribir el FR y reintentar,
  devuelve permiso. Adoptar nunca habilita el gate con menos evidencia que crear.
- **SC-003** Adoptar una spec `active` y commitear el paso intermedio es posible:
  con el FR, su fila y un test que falla, `check_traceability` pasa y el
  pre-commit no bloquea. En ningún layout de `dirs.source_roots` el flujo queda
  bloqueado contra sí mismo.
- **SC-004** Un solape detectado —por título o por archivo— sin bandera
  resolutoria aborta con código ≠ 0 y el árbol de trabajo queda idéntico a antes
  de la ejecución.
- **SC-005** Dadas dos specs de las que solo una nombra el archivo consultado, el
  triage por archivo devuelve exactamente esa; y un título compuesto solo de
  palabras de `stopwords` no produce candidatas por archivo.
- **SC-006** El bloqueo del gate sobre un archivo gobernado por specs nombra esas
  specs; sobre un archivo sin specs asociadas, el mensaje es el actual y el
  código de salida no cambia en ningún caso.
- **SC-007** El playbook `sdd-spec` describe el triage, el requisito de `--fr` y
  dónde escribir el FR en la spec adoptada; `AGENTS.md` lo referencia sin
  reproducirlo.
- **SC-008** Un derivado recién instalado encuentra `specs.triage` documentada en
  el catálogo de config que recibe, no solo en el kit.

## Assumptions

- Las citas `SPEC-NNN` en código y tests son suficientemente sistemáticas en un
  proyecto SDD como para alimentar el índice; donde falten, el triage por título
  sigue operando y el resultado es una candidata menos, no un falso positivo.
- El juicio final de solape lo aporta el asistente leyendo el registro; el script
  no incorpora LLM ni similitud semántica.
- El registro es la fuente de verdad de estados; una spec ausente del registro ya
  la detecta la verificación de consistencia preexistente.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-US1-001 | tests/unit/test_sdd_spec_reuse.py |
| FR-US1-002 | tests/unit/test_sdd_spec_reuse.py |
| FR-US1-003 | tests/unit/test_sdd_spec_reuse.py |
| FR-US1-004 | tests/unit/test_sdd_spec_reuse.py |
| FR-US1-005 | tests/unit/test_check_traceability.py |
| FR-US1-006 | tests/unit/test_sdd_spec_reuse.py |
| FR-US1-007 | tests/unit/test_sdd_spec_reuse.py |
| FR-US1-008 | tests/unit/test_template_paths.py |
| FR-US2-001 | tests/unit/test_sdd_spec.py |
| FR-US2-002 | tests/unit/test_sdd_spec.py |
| FR-US2-003 | tests/unit/test_sdd_spec.py |
| FR-US2-004 | tests/unit/test_sdd_spec.py |
| FR-US2-005 | tests/unit/test_sdd_spec.py |
| FR-US2-006 | tests/unit/test_sdd_spec.py |
| FR-US2-007 | tests/unit/test_sdd_spec.py |
| FR-US2-008 | tests/unit/test_sdd_spec.py |
| FR-US2-009 | tests/unit/test_sdd_config.py |
| FR-US2-010 | tests/unit/test_example_config.py |
| FR-US2-011 | tests/unit/test_template_paths.py |
| FR-US3-001 | tests/unit/test_sdd_gate.py |
| FR-US3-002 | tests/unit/test_sdd_gate.py |
| FR-US3-003 | tests/unit/test_sdd_gate.py |

## Fuera de alcance

- Declarar y validar la relación entre specs (`--extends`, `--supersedes`, la
  sección "Relación con specs existentes" y su validación): es
  [SPEC-023](SPEC-023-relacion-entre-specs.md).
- Índice generado de los ámbitos (User Story / Independent Test) de cada spec
  para un triage semántico: queda en `docs/IDEAS.md` hasta tener spec propia.
- Similitud léxica o semántica sobre el cuerpo de las specs (TF-IDF, embeddings).
- Persistir el índice invertido como artefacto generado del pipeline.
- Verificar que el test declarado **falle** antes de implementar: exigiría
  ejecutar la suite desde `sdd_spec.py`. Esta spec exige que el test exista
  (FR-US1-004), no que esté rojo.

## Historial

- 2026-08-10: creada (draft).
- 2026-08-10: FR-006 movido a SPEC-023; FR-010 eliminado por redundante.
- 2026-08-10: reescrita tras análisis. Se agrega `--reuse` (adoptar una spec
  existente sin crear otra) como US1; se declara la gramática de la sección de
  relaciones y su SSOT; se exige atomicidad; se excluyen de la migración las
  specs generadas; se corrige el Coverage mapping, que apuntaba a
  `tests/unit/test_docs.py` (no existe). Registrada en `SPECS_REGISTRY.md`.
- 2026-08-10: se agrega el índice invertido archivo→spec como señal primaria del
  triage y el aviso de reuso en el gate. Se agrega dependencia de SPEC-017.
- 2026-08-10: resueltos los hallazgos A1/A2/A4 de `analyze` (gate abierto sin
  evidencia nueva, degradación prematura al superseder, clave de config que no
  viajaba al derivado).
- 2026-08-10: repriorizadas las historias. Tres P1 no priorizaban nada.
- 2026-08-10: FR renumerados a `FR-USk-NNN` y agrupados por historia, siguiendo
  la convención multi-HU del repo (SPEC-014, SPEC-017).
- 2026-08-10: primera sesión `clarify`: el rojo de trazabilidad al adoptar una
  spec `active`, dónde aterriza el FR nuevo, deducción de rutas sin git y
  extracción de rutas de *Key Entities*.
- 2026-08-10: segunda sesión `clarify` y **partición**. (1) En un layout con los
  tests dentro de `source_roots`, `--reuse` se bloqueaba contra sí mismo: ahora
  tolera el archivo de test ausente en ese caso (FR-US1-004). (2) La exigencia de
  fila de Coverage se limita a specs `active`: sobre `draft` el validador no la
  pide y cobrarla haría que adoptar saliera más caro que crear. (3) El triage por
  título compara contra el *stem* del archivo y el kit siembra `stopwords` con su
  propio vocabulario, para no volver candidata a casi toda spec (FR-US2-005/009).
  (4) `--fr` compara por igualdad exacta (FR-US1-007). (5) La spec se parte en
  dos por coherencia de historia, sin dividir ninguna US: declarar y validar la
  relación entre specs pasa a
  [SPEC-023](SPEC-023-relacion-entre-specs.md). Cierra C1..C8.
- 2026-08-10: resuelto D1 de `analyze`. El par `Es dependencia de` / `Depende de`
  entre esta spec y SPEC-023 estaba invertido —quien referencia a la otra es esta,
  no al revés— pero tampoco corresponde invertirlo: ninguna necesita a la otra
  para entregarse, y el enlace duro obligaría a que ambas pasen a `active` juntas.
  Se quita el enlace y la relación queda declarada en prosa. La deuda de
  recíprocos que este campo destapó (D2) la asume la migración de SPEC-023.
- 2026-08-10: se aplica el criterio semántico que declara SPEC-023 FR-US2-002
  (`Depende de:` es dependencia de entrega, no cita ni vecindad): quedan SPEC-001
  y SPEC-017, y bajan a prosa SPEC-005 y SPEC-016. Se agrega el campo
  `Extendida por:`, que completa el tercer par simétrico.
- 2026-08-10: revisión externa. Se declara cómo se resuelve `SPEC-NNN` al ID
  completo y por qué `.sdd/current-spec` lo necesita entero (FR-US1-002); que el
  parseo del *Coverage mapping* se reutiliza de `check_traceability.py` en vez de
  duplicarse (FR-US1-005); y que la normalización trata `-` y `_` como
  separadores a ambos lados de la comparación (FR-US2-006). Se descartó tratar
  como hallazgo que los tests del *Coverage mapping* aún no cubran estos FR: es
  el estado normal de una spec `draft` y el ciclo ya lo especifican FR-US1-004 y
  FR-US1-006.
- 2026-08-10: segunda revisión externa. El índice descartaba las rutas que no
  existen en disco, lo que dejaba ciego a FR-US3-001 justo en el caso más
  frecuente: el archivo **nuevo** que una spec `draft` nombra en *Key Entities* y
  que el gate va a bloquear primero. La inconsistencia además era interna —
  FR-US1-004 ya tolera el archivo de test ausente—. Ahora se conservan las rutas
  con directorio explícito aunque no existan, y el descarte se limita a los
  tokens sin directorio que no resuelven por basename, que son indeterminables y
  no proyectados (FR-US2-003). Se prefiere el falso positivo visible —una
  candidata de más en una lista que el humano lee— al falso negativo silencioso,
  coherente con el triage como red de seguridad y no como árbitro.
