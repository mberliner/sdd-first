# SPEC-024-traza-fr-en-test: El Coverage mapping verifica que el FR referenciado aparezca en el test, no solo que el archivo exista

## User Story (Priority P2)

Como mantenedor del kit, quiero que `check_traceability` detecte cuando una
fila del *Coverage mapping* apunta a un archivo de test que existe pero no
menciona el FR que dice cubrir, para que un requisito no pueda quedar "verde"
sobre un test que en realidad prueba otra cosa.

**Why this priority:** cierra un hueco de enforcement (G-8 en
`docs/IDEAS.md`), no un bug del happy path ni una capacidad nueva de
producto; el kit sigue funcionando sin esto, pero la garantía de trazabilidad
que promete es más débil de lo que parece.

**Independent Test:** con una spec `active`+`hibrido` cuyo *Coverage mapping*
mapea `FR-999` a un archivo de test que existe pero no contiene el ID
`FR-999` en ningún lado, `python core/check_traceability.py specs` reporta la
violación y sale con exit 1.

## Relación con specs existentes

- **Extiende:** [SPEC-001](SPEC-001-agnostic-core.md) | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** SPEC-001 FR-003 declara que
  `check_traceability.py` valida "cobertura FR→test en specs active" como
  afirmación mínima de existencia (el archivo referenciado existe). Es el
  mismo patrón que ya se usó dos veces en el historial de SPEC-001 (FR-002 →
  [[SPEC-017-gate-decision-spec-first]], FR-001 →
  [[SPEC-021-config-vacio-no-rompe]]): cuando un FR de SPEC-001 acumula
  matiz semántico real, se saca a una spec propia enlazada en vez de inflar
  el FR existente, para que SPEC-001 se mantenga como índice liviano de "esto
  existe" y no una bolsa sin centro.

## Clarifications

### Session 2026-08-11
- Q: ¿Qué significa "el FR aparece en el test" — grep de substring o match
  exacto? → A: match de token completo sobre el ID exacto, no el operador
  `in` de Python sobre substrings: un `in` ingenuo haría que `FR-1`
  "aparezca" dentro de `FR-10`. **Ojo:** tampoco alcanza `\bFR-ID\b` de `re`
  tal cual — `-` es un carácter no-`\w`, así que ese `\b` se satisface en la
  transición `1`→`-` y deja pasar `FR-1` como falso positivo dentro de
  `FR-1-ALGO` (estructura real, dado que los IDs multi-HU usan `-` como
  separador). El criterio correcto excluye alfanumérico, `_` y `-` como
  vecinos, no solo no-`\w` (ver FR-002). `_FR_ANY` no se reusa tal cual —esa
  regex extrae *cualquier* FR mencionado, no busca uno específico—; lo que se
  reusa es la idea de anclar el ID como token, no el patrón literal.
- Q: ¿Y si una fila mapea el FR a varios archivos de test a la vez (como
  SPEC-018 FR-US1-001, con cinco archivos e2e)? → A: alcanza con que el FR
  aparezca en **al menos uno** de los archivos referenciados en esa fila, no
  en todos.
- Q: ¿Filas del Coverage mapping sin ninguna ruta de test referenciada? →
  A: fuera de alcance de este check: ya las cubre (o no) la verificación
  existente de `declared - covered` de SPEC-001 FR-003; este check no evalúa
  nada si no hay una ruta de test contra la cual grepear.
- Q: ¿Qué pasa con las filas que hoy fallarían sobre specs `active` ya
  existentes? → A: no es un FR del checker —es trabajo de migración—, así que
  se corrige como parte del cierre de esta iteración (ver Historial), sin
  bandera de excepción ni lista de specs eximidas: el propio `AGENTS.md` del
  kit prohíbe hardcodear ese tipo de listas, y una exención permanente sería
  una segunda fuente de verdad sobre "qué specs cumplen". El criterio de
  aceptación es SC-002 (pipeline verde al cerrar), no un conteo fijo de
  filas: el número medido (30 sobre 217, el 2026-08-11) es una fotografía del
  momento de escribir esta spec, no una lista cerrada.

## Acceptance Scenarios

- **Given** una spec `active`+`hibrido` con una fila `| FR-042 | tests/unit/test_x.py |`
  donde `test_x.py` existe pero no contiene el ID `FR-042`, **When** corre
  `check_traceability.py specs`, **Then** reporta una violación específica
  ("FR-042 no aparece en tests/unit/test_x.py") y sale con exit 1.
- **Given** la misma fila pero con `test_x.py` conteniendo `FR-042` en el
  nombre de una función o en un docstring, **When** corre el check, **Then**
  no reporta violación por esta regla.
- **Given** una fila que mapea un FR a varios archivos de test, **When** al
  menos uno de ellos contiene el ID del FR, **Then** no reporta violación
  (no se exige que todos lo mencionen).
- **Given** una fila sin ninguna ruta de test reconocible, **When** corre el
  check, **Then** esta regla no se evalúa sobre esa fila (queda a cargo de la
  verificación de FR huérfano ya existente).
- **Given** una fila `| FR-1 | tests/unit/test_y.py |` donde `test_y.py`
  contiene `FR-10` pero no `FR-1` como token completo, **When** corre el
  check, **Then** reporta violación (el match de token completo no deja que
  `FR-1` quede satisfecho por `FR-10`).
- **Given** la misma fila `| FR-1 | tests/unit/test_y.py |` pero `test_y.py`
  contiene `FR-1-ALGO` (un ID distinto, con `-` como separador) y no `FR-1`
  aislado, **When** corre el check, **Then** reporta violación: un `\b` de
  `re` sin más recaudos dejaría pasar este caso como falso positivo porque
  `-` es no-`\w`, así que el criterio de FR-002 lo excluye explícitamente.
- **Given** las filas de Coverage mapping que fallaban al momento de escribir
  esta spec (30 sobre 217, medidas el 2026-08-11), **When** se aplica el
  backfill de este cambio, **Then** `check_traceability.py specs` sale en
  verde sobre las specs `active`+`hibrido` vigentes al cerrar la iteración.

## Functional Requirements

- **FR-001** MUST: `check_traceability.py` verifica, para cada fila del
  *Coverage mapping* de una spec `active`+`hibrido` que tenga al menos una
  ruta de test, que el ID exacto del FR de esa fila aparezca como texto en el
  contenido de al menos uno de los archivos de test referenciados; si ninguno
  lo contiene, reporta una violación nombrando el FR y el/los archivo(s)
  evaluados. Un archivo referenciado que no se pueda decodificar como texto
  (encoding inesperado o binario) se trata como si no contuviera el ID —no
  aborta el check— y cuenta para la violación igual que un archivo sin la
  mención.
- **FR-002** MUST: el matching trata el ID como token completo: una
  ocurrencia solo cuenta si el carácter inmediatamente anterior y el
  inmediatamente posterior (cuando existen) no son alfanuméricos, `_` ni `-`.
  Esto excluye tanto los falsos positivos por sufijo (`FR-1` dentro de
  `FR-10`) como por prefijo con separador (`FR-1` dentro de `FR-1-ALGO`, un
  caso real dado que los IDs multi-HU del propio kit usan `-` como separador
  interno: `\bFR-1\b` de `re` no alcanza, porque `-` es no-`\w` y satisface
  el límite `\b` en esa transición). `FR-007` tampoco se satisface con
  `FR-US1-007` presente en el archivo, ni viceversa.

## Key Entities

- `core/check_traceability.py::_check_coverage` — función existente que se
  extiende con la verificación nueva.
- `core/check_traceability.py::iter_coverage_entries` — ya devuelve
  `(fr_id, rutas_de_test)` por fila; es la fuente de datos que reusa esta
  verificación, sin un segundo parseo del formato.

## Success Criteria

- **SC-001** `check_traceability.py specs` reporta en rojo cualquier fila del
  Coverage mapping de una spec `active`+`hibrido` cuyo FR no aparezca en
  ninguno de los archivos de test que declara cubrirlo.
- **SC-002** El pipeline del kit (`python core/pipeline.py`) sigue en verde
  tras el backfill, sobre las specs `active`+`hibrido` vigentes al cerrar la
  iteración.

## Assumptions

- El check sigue siendo determinista y sin dependencias nuevas: el criterio
  de vecinos no-alfanuméricos/`_`/`-` de FR-002 sobre el contenido ya leído
  del archivo, sin AST ni parseo de la suite de test.
- No se verifica que exista una aserción real sobre el requisito (eso queda
  registrado como idea separada, sin spec, en `docs/IDEAS.md`: "Coverage
  mapping mapea archivos, no casos").

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_check_traceability.py |
| FR-002 | tests/unit/test_check_traceability.py |

## Fuera de alcance

- Verificar que el test contenga una aserción real sobre el FR, más allá de
  mencionarlo (idea suelta en `docs/IDEAS.md`, sin spec).
- Filas del Coverage mapping sin ninguna ruta de test referenciada: las
  cubre la verificación de FR huérfano ya existente en SPEC-001 FR-003.

## Historial

- 2026-08-11: creada (draft), extiende SPEC-001. Origen: hallazgo G-8 de
  `docs/IDEAS.md`, medido sobre las 21 specs `active`+`hibrido` del kit
  (217 filas, 175 OK, 30 a corregir, 12 no evaluables). El backfill de esas
  30 filas es trabajo de migración del cierre de esta iteración —no un FR—:
  agregar el ID del FR al docstring o nombre de la función de test
  correspondiente en cada una, verificado por SC-002.
