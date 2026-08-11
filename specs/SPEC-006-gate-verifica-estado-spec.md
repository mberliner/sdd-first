# SPEC-006-gate-verifica-estado-spec: El gate verifica el estado (draft/active) de la spec declarada

> **`superseded` por [[SPEC-017-gate-decision-spec-first]] (2026-08-06).** La
> política de decisión del gate tiene un solo SSOT y es esa spec, que absorbe
> esta entera (US2). Lo de acá se conserva como registro de por qué existió el
> requisito, no como fuente autoritativa: no leas este documento para saber qué
> decide el gate hoy.
>
> Origen: `docs/IDEAS.md` P1 "Huecos de enforcement del gate y la
> trazabilidad", ítem G-2, detectado en la revisión crítica del 2026-07-02.

## User Story (Priority P1)

Como mantenedor de un proyecto con sdd-first, quiero que el gate spec-first
rechace una spec declarada en `.sdd/current-spec` cuyo estado en
`SPECS_REGISTRY.md` sea `archived`/`superseded`/`notas` (o que ni siquiera
esté registrada como fila), para que declarar una spec cerrada no sirva como
llave universal para editar código sin una spec realmente vigente.

**Why this priority:** es P1 porque rompe la garantía central del Principio
de gate ("no se edita código sin spec vigente"): hoy `_spec_is_valid` en
`core/sdd_gate.py` hace `spec_id in registry.read_text(...)` — un substring
match sobre el texto crudo del registro. Cualquier mención del ID en
`SPECS_REGISTRY.md` (la fila con estado `archived`, o el link de esa fila,
incluso texto suelto en un roadmap) desbloquea el gate igual que una spec
`active`. Es un bypass silencioso del enforcement que el propio kit vende
como su valor central.

**Independent Test:** con una spec `archived` en el registro (y su archivo en
`specs/`), declararla en `.sdd/current-spec` y editar un archivo bajo
`dirs.source_roots` — el gate debe bloquear. Con la misma spec en estado
`active`, el gate debe permitir (dado que además fue tocada después de
declararse, regla ya existente).

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** [SPEC-017](SPEC-017-gate-decision-spec-first.md)
- **Por qué no cabe en una spec existente:** —

## Clarifications

### Session 2026-08-01
- Q: ¿reimplementar el parseo de filas del registro en `sdd_gate.py` o
  reusar el de `check_traceability.py`? → A: reusar — `check_traceability.py`
  ya tiene `_parse_registry`/`_RegistryRow` (parsea ID, estado, formato,
  archivo desde la tabla markdown); duplicarlo en `sdd_gate.py` violaría el
  mismo principio "No duplicar SSOT" que motivó SPEC-005. `sdd_gate.py`
  importa esas funciones desde `check_traceability` (ambos viven en `core/`,
  mismo mecanismo de import ya usado para `sdd_config`).
- Q: ¿qué estados dejan pasar el gate? → A: `draft` y `active` — los mismos
  dos estados que ya trata como "editable" el resto del kit (p. ej.
  `check_traceability` exige Coverage mapping solo en `active`, pero `draft`
  es el estado normal mientras se está codeando la spec recién creada por
  `sdd_spec.py`).
- Q: ¿la fila se matchea por el ID corto (`SPEC-006`) o por el archivo
  completo (`SPEC-006-gate-verifica-estado-spec.md`)? → A: por archivo —
  `.sdd/current-spec` declara el slug completo (`SPEC-NNN-slug`, sin `.md`);
  la columna `ID` del registro solo tiene el número corto (`SPEC-006`), pero
  la columna `Archivo` tiene el link con el slug completo. Matchear
  `row.archivo == f"{declared}.md"`.

## Acceptance Scenarios

- **Given** `SPECS_REGISTRY.md` con una fila `SPEC-009-vieja` en estado
  `archived`, **When** `.sdd/current-spec` declara `SPEC-009-vieja` y se edita
  un archivo bajo `dirs.source_roots`, **Then** el gate bloquea (exit 2 /
  `decide()` devuelve `False`) con un motivo que menciona el estado inválido.
- **Given** la misma fila pero en estado `active` (y la spec editada después
  de declararse), **When** se edita código, **Then** el gate permite.
- **Given** un ID declarado en `.sdd/current-spec` que no aparece como
  `Archivo` de ninguna fila del registro (solo mencionado en prosa, p. ej. en
  un roadmap fuera de la tabla), **When** se edita código, **Then** el gate
  bloquea (mismo comportamiento que "spec inexistente" hoy).
- **Given** un registro con una fila en estado `draft` recién creada por
  `sdd_spec.py`, **When** se declara y se edita esa spec (tras el paso
  obligatorio de editarla primero), **Then** el gate permite — no rompe el
  flujo normal de `sdd-spec`.

## Functional Requirements

- **FR-001** MUST: `core/sdd_gate.py::_spec_is_valid` reemplaza el substring
  match por un parseo real de `SPECS_REGISTRY.md` (reusando
  `check_traceability._parse_registry`), matcheando la fila cuyo `archivo`
  sea `f"{spec_id}.md"`.
- **FR-002** MUST: una spec declarada solo es válida si la fila matcheada
  tiene `estado` en `{"draft", "active"}` (case-insensitive); cualquier otro
  estado (`archived`, `superseded`, `notas`) o ausencia de fila hace que
  `_spec_is_valid` devuelva `False`.
- **FR-003** MUST: el motivo de bloqueo que `decide()` devuelve cuando la
  spec es inválida por estado (no por inexistencia) es distinguible en el
  mensaje (menciona el estado encontrado), para que el usuario entienda que
  la spec existe pero no está vigente — no solo "no existe".

## Key Entities

- **Fila de registro válida**: `_RegistryRow` con `archivo` matcheado y
  `estado` en `{draft, active}`.

## Success Criteria

- **SC-001** Una spec `archived`/`superseded`/`notas` declarada en
  `.sdd/current-spec` no desbloquea la edición de código fuente.
- **SC-002** El comportamiento existente (spec `draft`/`active` tocada
  después de declararse desbloquea el gate) no tiene regresión.

## Assumptions

- El formato de fila de `SPECS_REGISTRY.md` (columnas `ID | Título | Estado |
  Iteración | Formato | Archivo`) es el mismo que ya parsea
  `check_traceability.py`; no hay variantes de formato entre proyectos
  instalados (`sdd_init.py` siempre siembra el mismo template de registro).

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_sdd_gate.py |
| FR-002 | tests/unit/test_sdd_gate.py |
| FR-003 | tests/unit/test_sdd_gate.py |

## Fuera de alcance

- G-1 (pre-commit hardcodea `files:`), G-3 (matcher del hook de Claude), G-4
  (doctor valida contenido del wiring), G-5 (heurística de mtime), G-6/G-8
  (trazabilidad FR→test) y G-7 (multi-spec en `current-spec`) quedan
  registrados en `docs/IDEAS.md`, fuera de esta spec.

## Historial

- 2026-08-01: creada (draft).
- 2026-08-01: implementada y promovida a `active`. `core/sdd_gate.py` reemplaza
  el substring match sobre `SPECS_REGISTRY.md` por un parseo real de la fila
  (reusando `check_traceability._parse_registry`), exigiendo estado
  `draft`/`active`. Verificado con tests unitarios (11 casos en
  `test_sdd_gate.py`) y con una instalación real vendorizada en `/tmp`:
  spec `archived` bloquea, spec `active` permite, ID mencionado solo en
  prosa (no en tabla) bloquea — el bypass original ya no reproduce. Pipeline
  9/9 VERDE, doctor sano, 66 tests.
