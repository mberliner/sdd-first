# SPEC-017: Gate spec-first: qué decide bloquear una edición de código

> **SSOT de la política de decisión del gate** (`core/sdd_gate.decide`): qué
> hace falta para que una edición de código fuente esté autorizada. Absorbe
> SPEC-006 (que pasa a `superseded`) y el criterio que SPEC-001 FR-002
> enumeraba, para que la política tenga un solo documento autoritativo.
>
> Origen: **G-5** de `docs/IDEAS.md` ("criterio mtime del gate sin documentar ni
> escape hatch"), deuda que SPEC-006 declaró explícitamente fuera de alcance, más
> el incidente reproducido al cerrar SPEC-016 (ver Clarifications).
>
> **Fuera de esta spec, por eje distinto** (*dónde se invoca* el gate, no *qué
> decide*): el wiring de las tres capas y su pre-filtro
> ([[SPEC-015-wiring-apunta-al-codigo-real]]), la resolución de la raíz del
> proyecto ([[SPEC-014-derivado-dice-la-verdad]] FR-US1-003), y el bootstrap de
> hooks + reset post-commit ([[SPEC-004-enforcement-hardening]]). Sí es de acá,
> en cambio, que el aviso del gate **llegue** a quien commitea: es la garantía
> del escape hatch, no la configuración de a qué archivos se aplica.

## User Story 1 (Priority P1) — ninguna edición de código sin spec declarada

Como dueño de un proyecto con el kit instalado, quiero que editar código sin
haber declarado una spec vigente quede bloqueado con un motivo accionable, para
que el protocolo spec-first sea una propiedad del repositorio y no una promesa.

**Why this priority:** es la razón de existir del gate. Sin esta capa el resto
del andamiaje (trazabilidad, pipeline) solo verifica *a posteriori*.

**Independent Test:** con `.sdd/current-spec` sin ninguna spec, invocar el gate
sobre un archivo bajo `dirs.source_roots` sale exit 2 nombrando qué hacer; sobre
un archivo fuera de esas carpetas sale exit 0.

## User Story 2 (Priority P1) — la spec declarada tiene que estar viva

Como responsable del proceso, quiero que solo una spec **existente, registrada y
en estado vigente** desbloquee la edición, para que declarar una spec archivada,
inexistente o apenas mencionada en prosa no alcance para saltear el gate.

**Why this priority:** una declaración que no se verifica convierte al gate en un
trámite. El bug real que originó SPEC-006: el match por substring sobre el texto
crudo del registro dejaba pasar una spec `archived` nombrada en la sección
Roadmap.

**Independent Test:** declarar una spec con fila `archived` en el registro y
editar código sale exit 2 nombrando el estado; la misma fila en `active`, permite.

## User Story 3 (Priority P1) — la evidencia spec-first sobrevive al flujo real

Como quien trabaja una spec en varios commits, quiero que el gate reconozca que
la spec ya está escrita sin obligarme a modificarla de nuevo en cada commit, para
que el enforcement no me empuje a ediciones ceremoniales que no verifican nada.

**Why this priority:** el criterio anterior comparaba la **mtime** de la spec
contra la de `.sdd/current-spec`. Eso produce dos fallas simultáneas y opuestas:
bloquea el flujo legítimo (varios commits por spec, checkout, clone, y el propio
ciclo stash/restore de `pre-commit`, que renueva mtimes) y **no detiene** al que
quiera saltearlo, porque un `touch` o una línea en blanco lo satisfacen. Fricción
alta, garantía nula.

**Independent Test:** con la spec ya commiteada y sin modificarla, redeclararla
tras el reset post-commit habilita el commit siguiente; y una spec declarada que
solo tiene los placeholders de la plantilla bloquea.

## Clarifications

### Session 2026-08-06

- Q: ¿Por qué una spec nueva y no enmendar SPEC-001/SPEC-006? → A: por SSOT. El
  cambio no es un detalle de implementación sino la política de decisión completa,
  que hoy está repartida entre SPEC-001 FR-002 (criterio), SPEC-002 FR-002 (flujo)
  y SPEC-006 (estado). Una spec nueva que las absorba deja **un** documento
  autoritativo; las viejas quedan delegando o `superseded`, sin rastro duplicado
  del mecanismo.
- Q: ¿Alcanza con corregir la heurística de mtime (tolerancias, ignorar el
  stash)? → A: no. La mtime es un proxy de "el contenido cambió" y la tocan
  checkout, clone, stash, restore, copias y sincronizaciones; git no la versiona.
  Cualquier parche sigue midiendo la señal equivocada.
- Q: ¿Usar git como evidencia (spec en `HEAD` o con cambios en el índice)? → A:
  evaluado y descartado. Resuelve el falso positivo pero agrega un subproceso, un
  requisito de repositorio y comportamiento distinto en worktrees, y **no aporta
  garantía extra** sobre el criterio de contenido: una spec vacía commiteada
  pasaría igual. El criterio se queda en el contenido, que es determinista, no
  necesita git y da la misma respuesta en cualquier máquina.
- Q: Entonces, ¿qué se pierde respecto de la mtime? → A: la pretensión de forzar
  "editá la spec **en esta sesión**". Era pretensión y no garantía (un `touch`
  vacío la cumplía). Lo que se conserva y ahora sí se verifica es que la spec
  declarada tenga requisitos escritos: la plantilla recién creada no habilita.
- Q: ¿Qué cuenta como "contenido"? → A: al menos un FR **declarado** con la
  marca del formato (`FR-NNN` en negrita) y texto propio además del keyword
  `MUST:/SHOULD:/MAY:`. Los placeholders de `specs/SPEC-TEMPLATE.md`
  (un `FR-001` en negrita seguido de `MUST: ...`) no cuentan. Reusa el reconocimiento de FR de
  `check_traceability`, sin duplicar la expresión regular.
- Q: ¿Y si hay varias specs declaradas? → A: se exige a **todas**. El criterio
  viejo se conformaba con que *alguna* estuviera tocada: declarar dos specs y
  escribir una habilitaba las dos. Es un endurecimiento, no una regresión.
- Q: ¿Escape hatch? → A: `SDD_GATE_BYPASS=<motivo>`, con motivo no vacío y aviso
  siempre en stderr. Hoy la única salida es `--no-verify`, que apaga *todo* el
  pre-commit (gate, trazabilidad y reset): el operador que la aprende deja de
  tener enforcement en vez de saltearse un caso. G-5 pide explícitamente el
  escape hatch además de la documentación.

### Session 2026-08-07

- Q: FR-US3-004 exige el aviso en stderr y los tests unitarios lo verifican, pero
  al commitear no aparece. ¿Dónde se pierde? → A: en el transporte. En el flujo
  real el gate corre como hook de `pre-commit`, que **descarta la salida de los
  hooks que pasan** y muestra solo `Passed`. Con el bypass el gate sale exit 0,
  o sea que pre-commit se traga justo el caso que el requisito quería hacer
  visible: un bypass queda indistinguible de un commit normal. La garantía existía
  a nivel unitario y se evaporaba de punta a punta (**V-2** de `docs/IDEAS.md`,
  hallada al escribir los escenarios de [[SPEC-018-verificacion-e2e]]).
- Q: ¿`verbose: true` en el hook no llena de ruido cada commit? → A: no. El gate
  imprime **solo** cuando hay algo que bloquear (`sdd_gate.main` retorna 0 sin
  escribir nada si no hay motivos), así que el único caso en que un hook que pasa
  tiene salida es exactamente el bypass. `verbose` no agrega texto al camino
  feliz: destapa el que ya se estaba escribiendo.
- Q: ¿Y la alternativa de que el gate deje el rastro en un archivo? → A:
  descartada. Agrega un artefacto y un ciclo de vida (quién lo limpia, si se
  commitea) para que el operador se entere **después** de que el commit ya se
  hizo. El aviso sirve en el momento de decidir, no en la auditoría posterior.

## Acceptance Scenarios

### US1 — bloqueo sin declaración

- **Given** `.sdd/current-spec` sin ninguna línea de spec, **When** el gate
  recibe un archivo bajo `dirs.source_roots`, **Then** bloquea (exit 2) e indica
  declarar la spec o crearla con `sdd-spec`.
- **Given** el mismo estado, **When** el archivo está fuera de
  `dirs.source_roots` o el payload no declara ruta, **Then** permite (exit 0).

### US2 — validez de la declaración

- **Given** una spec declarada que no existe en `specs/`, **When** se edita
  código, **Then** bloquea nombrando el ID declarado.
- **Given** una spec cuyo ID solo aparece en prosa del registro (no como fila de
  la tabla), **When** se edita código, **Then** bloquea.
- **Given** una fila en estado `archived` o `superseded`, **When** se edita
  código, **Then** bloquea nombrando el estado; con `draft` o `active`, permite.

### US3 — evidencia por contenido

- **Escenario 1 (spec simple).** **Given** una spec recién creada con
  `sdd_spec.py` (solo placeholders de la plantilla) y declarada, **When** se
  edita código, **Then** bloquea pidiendo escribir los FR; **When** se escriben
  los FR, **Then** permite, sin importar el orden de las marcas de tiempo.
- **Escenario 2 (misma spec, varios commits).** **Given** una spec con FR ya
  commiteada y `.sdd/current-spec` limpiado por el reset post-commit, **When** se
  la redeclara **sin modificarla**, **Then** permite editar y commitear.
- **Escenario 3 (dos specs, commit al final).** **Given** dos specs declaradas
  con FR escritos, **When** se edita código de ambas y se commitea al final,
  **Then** permite; **Given** que una de las dos solo tiene placeholders,
  **Then** bloquea nombrando esa spec, aunque la otra esté completa.
- **Given** cualquiera de los escenarios anteriores, **When** se renuevan las
  mtimes de la spec y de `.sdd/current-spec` en cualquier orden, **Then** la
  decisión no cambia.
- **Given** una decisión de bloqueo, **When** el entorno trae
  `SDD_GATE_BYPASS=<motivo>`, **Then** permite y deja el motivo en stderr; con la
  variable vacía o ausente, bloquea igual.
- **Given** un repositorio con los hooks del kit instalados, **When** se commitea
  código con `SDD_GATE_BYPASS=<motivo>`, **Then** la salida del commit muestra el
  motivo y el bloqueo salteado, y no solo `Passed`.

## Functional Requirements

### US1

- **FR-US1-001** MUST: `sdd_gate.decide` permite toda edición cuyo payload no
  declare ruta o cuya ruta no caiga bajo `dirs.source_roots` del config.
- **FR-US1-002** MUST: sin ninguna spec declarada en `.sdd/current-spec`, bloquea
  con un motivo que nombra el archivo de declaración y la vía para crear la spec.
- **FR-US1-003** MUST: el contrato de salida es exit 0 permite / exit 2 bloquea,
  con los motivos en stderr, para los dos transportes (argv, stdin JSON) y sin
  depender del asistente que lo invoque.

### US2

- **FR-US2-001** MUST: cada spec declarada debe existir como `specs/<ID>.md` y
  aparecer como **fila** de la tabla de `SPECS_REGISTRY.md`, parseada con el
  mismo lector que `check_traceability`, nunca por coincidencia de substring.
- **FR-US2-002** MUST: solo los estados `draft` y `active` habilitan; cualquier
  otro bloquea nombrando el estado encontrado.
- **FR-US2-003** MUST: la validez se exige a **todas** las specs declaradas; el
  motivo enumera cada una con su causa.

### US3

- **FR-US3-001** MUST: la evidencia de que la spec precede al código es su
  **contenido**: al menos un FR declarado con la marca del formato y texto propio
  además del keyword. Ningún criterio del gate puede depender de marcas de tiempo
  del sistema de archivos.
- **FR-US3-002** MUST: el criterio de contenido se exige a **todas** las specs
  declaradas, y el motivo nombra las que no lo cumplen.
- **FR-US3-003** MUST: el motivo de bloqueo por contenido explica que la spec no
  tiene requisitos escritos e indica escribir los FR, sin sugerir "editar la spec
  después de declararla".
- **FR-US3-004** MUST: `SDD_GATE_BYPASS` con valor no vacío convierte cualquier
  bloqueo en permiso, imprimiendo en stderr el motivo del bypass junto con el
  bloqueo que se saltea; vacía o ausente no altera la decisión.
- **FR-US3-005** MUST: los textos que describen el criterio al operador —mensaje
  final de `core/sdd_spec.py` y header de `templates/wiring/current-spec`— hablan
  del contenido de la spec, no de editarla después de declararla.
- **FR-US3-006** MUST: `docs/SDD-ENFORCEMENT.md` (SSOT del enforcement) describe
  el criterio vigente, el endurecimiento multi-spec y el escape hatch, y ningún
  otro documento del kit repite la política.
- **FR-US3-007** MUST: el wiring de `pre-commit` que el kit instala entrega al
  operador la salida del hook del gate **aunque el hook pase**, para que el aviso
  de FR-US3-004 sobreviva al transporte. El wiring del propio kit cumple lo mismo.

## Key Entities

- `core/sdd_gate.py` — implementación de la política; `decide()` es su SSOT
  ejecutable.
- `.sdd/current-spec` — declaración de intención: qué spec(s) gobiernan la
  edición en curso.
- `specs/SPECS_REGISTRY.md` — fuente de existencia y estado de cada spec.
- `SDD_GATE_BYPASS` — escape hatch acotado al gate, alternativa a apagar todo el
  `pre-commit` con `--no-verify`.

## Success Criteria

- **SC-001** Una spec recién creada por `sdd_spec.py` y declarada **no** habilita
  la edición; con los FR escritos, sí — y la decisión es la misma cualquiera sea
  el orden de las mtimes.
- **SC-002** Trabajar una misma spec en varios commits no requiere modificarla ni
  tocarla entre commits: basta redeclararla tras el reset post-commit.
- **SC-003** Con dos specs declaradas, la incompleta bloquea aunque la otra esté
  completa, y el motivo la nombra.
- **SC-004** Los tres escenarios se verifican de punta a punta con commits reales
  en el kit **y** en un proyecto derivado instalado con `sdd-init`.
- **SC-005** Ninguna spec `active` distinta de esta describe la política de
  decisión del gate; SPEC-006 queda `superseded` con puntero a esta.

## Assumptions

- El formato de FR (`FR-NNN` en negrita + `KEYWORD: texto`) es el de `docs/SPEC-FORMAT.md`;
  las specs `casero` no se ven afectadas porque el gate mira el mismo marcador que
  ya usa `check_traceability`.
- Que un FR escrito sea *adecuado* al cambio en curso sigue siendo juicio de
  `analyze`/`clarify` y de la revisión humana (límite conocido, sin cambio).

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-US1-001 | tests/unit/test_sdd_gate.py |
| FR-US1-002 | tests/unit/test_sdd_gate.py |
| FR-US1-003 | tests/unit/test_sdd_gate_hook.py |
| FR-US2-001 | tests/unit/test_sdd_gate.py |
| FR-US2-002 | tests/unit/test_sdd_gate.py |
| FR-US2-003 | tests/unit/test_gate_evidencia_contenido.py |
| FR-US3-001 | tests/unit/test_gate_evidencia_contenido.py |
| FR-US3-002 | tests/unit/test_gate_evidencia_contenido.py |
| FR-US3-003 | tests/unit/test_gate_evidencia_contenido.py |
| FR-US3-004 | tests/unit/test_gate_evidencia_contenido.py |
| FR-US3-005 | tests/unit/test_gate_evidencia_contenido.py |
| FR-US3-006 | tests/unit/test_sdd_enforcement_ssot.py |
| FR-US3-007 | tests/unit/test_wiring_precommit_verbose.py, tests/e2e/escenarios/test_ciclo_spec_first.py |

## Fuera de alcance

- **Correlacionar el archivo editado con la spec que lo cubre.** Declarar una
  spec vigente y completa habilita cualquier archivo bajo `dirs.source_roots`.
  Exigiría leer el Coverage mapping y mapear código↔requisito; queda como idea.
- **G-6** (`check_traceability` no exige el keyword `MUST:/SHOULD:/MAY:` en los
  FR). Comparte el parser con FR-US3-001 y conviene resolverlo cerca, pero es
  trazabilidad, no gate.
- Adecuación semántica de la spec al cambio (capa `analyze`/`clarify`).
- El wiring, la resolución de raíz y el ciclo de hooks: ver el encabezado.

## Historial

- 2026-08-06: creada (draft) y promovida a `active` en la iteración 3. Absorbe
  SPEC-006 y el criterio que enumeraba SPEC-001 FR-002; cierra G-5.
- 2026-08-07 (iteración 4): FR-US3-007. La suite e2e mostró que el aviso del
  escape hatch no sobrevivía al transporte de `pre-commit` (V-2); el requisito
  extiende la garantía de FR-US3-004 hasta el operador.
