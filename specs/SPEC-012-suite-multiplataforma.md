# SPEC-012: El pipeline del kit corre verde en Windows y POSIX

> Origen: deuda anotada al cerrar SPEC-011 el 2026-08-04. El pipeline del kit
> sale ROJO 8/10 en Windows por un test que asevera un permiso POSIX; en
> Linux/CI no se manifiesta.

## User Story (Priority P1)

Como desarrollador del kit trabajando en Windows, quiero que
`python core/pipeline.py` salga VERDE cuando el kit está sano, para poder usar
el semáforo como señal de mi trabajo en vez de tener que recordar cuál de los
fallos es "el de siempre".

**Why this priority:** un ROJO permanente e inevitable destruye el valor del
pipeline como gate — es exactamente el problema que el kit existe para
resolver, y lo tiene sobre sí mismo. Además contradice el Principio III: el
propio kit dogfoodea un enforcement que en su plataforma de desarrollo nunca
puede pasar.

**Independent Test:** `python core/pipeline.py` en Windows sale VERDE 10/10, y
la aserción sobre el wiring ejecutable sigue fallando si se elimina el `chmod`
de `sdd_init.py` (la protección no se pierde, cambia de forma).

## Clarifications

### Session 2026-08-04

- Q: ¿Por qué falla? → A: `Path.chmod(0o755)` no setea bits de ejecución en
  NTFS; Python los reporta siempre apagados. El instalador hace lo correcto y
  el test asevera un efecto que la plataforma no puede producir.
- Q: ¿Se quita el `chmod` de `sdd_init.py`? → A: no. En POSIX el bit es real y
  necesario: `.claude/sdd_gate_hook.sh` se invoca como ejecutable. El defecto
  está en el test, no en el instalador.
- Q: ¿Alcanza con un `skipif` en Windows? → A: no. Dejaría el wiring ejecutable
  sin cobertura alguna en la plataforma donde más se desarrolla. Se parte en
  dos aserciones: la **intención** (`chmod(0o755)` se invoca sobre los destinos
  de `_EXECUTABLE_WIRING`) se verifica en todas las plataformas; el **efecto**
  (bits en `st_mode`) solo donde el sistema de archivos puede expresarlo.
- Q: ¿El paso `coverage` también hay que arreglarlo? → A: no, falla en cascada
  del paso `tests`. Medido deseleccionando el test roto, da 55% ≥ 50%.

## Acceptance Scenarios

- **Given** un entorno Windows, **When** corre `python core/pipeline.py`,
  **Then** sale VERDE (antes: ROJO 8/10 por `tests` + `coverage`).
- **Given** cualquier plataforma, **When** se elimina el `chmod` de
  `sdd_init.py`, **Then** la suite falla — la protección del wiring ejecutable
  sigue viva.
- **Given** un entorno POSIX, **When** corre la suite, **Then** además se
  verifica el bit real en `st_mode` del hook instalado.

## Functional Requirements

- **FR-001** MUST: la suite verifica, en **todas** las plataformas, que
  `sdd_init.main` aplica permiso de ejecución (`chmod(0o755)`) a cada destino
  declarado en `_EXECUTABLE_WIRING`.
- **FR-002** MUST: la aserción sobre los bits de `st_mode` del archivo
  instalado se ejecuta solo donde el sistema de archivos los soporta, con la
  razón explicitada en el motivo del skip (no un skip mudo).
- **FR-003** MUST: `core/sdd_init.py` conserva el `chmod` sobre
  `_EXECUTABLE_WIRING` — el fix es del test, no del instalador.
- **FR-004** SHOULD: el criterio "esta plataforma expresa permisos POSIX" se
  declara una sola vez y de forma reutilizable, para que el próximo test con el
  mismo problema no re-derive la condición.

## Key Entities

- `tests/unit/test_sdd_init_seeded_steps.py` — el test defectuoso.
- `tests/unit/conftest.py` — sede del criterio compartido de FR-004.
- `core/sdd_init.py::_EXECUTABLE_WIRING` — contrato verificado; no se modifica.

## Success Criteria

- **SC-001** `python core/pipeline.py` en Windows → VERDE 10/10 (antes: ROJO
  8/10).
- **SC-002** Quitar el `chmod` de `sdd_init.py` hace fallar la suite en
  Windows (verificación manual de que FR-001 no es un test vacío).
- **SC-003** `pytest tests/unit` sin fallos ni errores en Windows.

## Assumptions

- El kit se desarrolla en Windows y se valida en CI Linux: ambas plataformas
  deben dar la misma señal, aunque una de las dos aserciones no aplique.
- No hay otros tests del kit que dependan de permisos POSIX (verificado: es el
  único uso de `st_mode` en la suite).

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_sdd_init_seeded_steps.py |
| FR-002 | tests/unit/test_sdd_init_seeded_steps.py |
| FR-003 | tests/unit/test_sdd_init_seeded_steps.py |
| FR-004 | tests/unit/conftest.py (consumido por el test anterior) |

## Fuera de alcance

- Cualquier otro fallo de plataforma que no sea el del wiring ejecutable.
- Matriz de CI multiplataforma (hoy corre solo Linux) — anotable en
  `docs/IDEAS.md`.

## Historial

- 2026-08-04: creada (draft), registrada en `SPECS_REGISTRY.md` y declarada en
  `.sdd/current-spec`.
- 2026-08-04: implementada y promovida a `active`. Pipeline VERDE 10/10 en
  Windows (SC-001), 139 passed + 1 skip justificado (SC-003). SC-002 verificado
  a mano: parcheando `sdd_init.py` para no aplicar el `chmod`, la suite falla
  en Windows con `no se aplico chmod a .claude/sdd_gate_hook.sh`.
