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

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

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

### Session 2026-08-12

- Q: ¿Por qué entra el mojibake (C-2 de `docs/IDEAS.md`) en una spec cuyo
  alcance era el wiring ejecutable? → A: porque el invariante de esta spec es la
  paridad Windows/POSIX del kit, y el mojibake es el otro caso donde Windows
  degrada la señal: `sys.stdout` cae a `cp1252` cuando la salida no es una
  consola UTF-8, y todo texto acentuado sale ilegible o revienta con
  `UnicodeEncodeError`. Se enmienda el *Fuera de alcance*, que estaba escrito
  para no arrastrar problemas de plataforma sin diagnóstico, no para vetarlos.
- Q: ¿Qué tan real es? → A: se reprodujo en esta misma sesión: el triage de
  `sdd_spec.py` imprimió `SPEC-000-naming � Nomenclatura agn�stica` con la
  salida redirigida. La campaña de usabilidad ya lo había confirmado por bytes
  (`docs/IDEAS.md`, C-2 en la lista de reproducidos): con `stdout` redirigido,
  `sys.stdout.encoding` es `cp1252` y lo emitido **no es UTF-8 válido**. Afecta
  al aviso más importante del kit —el de `sdd_spec.py`: "Editá la spec ANTES de
  tocar código"— y a todo `_next_steps` de la instalación.
- Q: ¿Se arregla en cada entrypoint o de una vez? → A: de una vez. Hoy dos
  módulos (`check_constitution.py`, `check_traceability.py`) repiten el mismo
  bloque de `reconfigure` y los otros trece no lo tienen; copiarlo trece veces
  más sería la duplicación del Principio IV con forma de fix. El helper vive en
  `core/sdd_config.py`, que es donde ya viven `write_text_lf` y los defaults
  compartidos.
- Q (descubierto al verificar): `check_traceability.py` no importaba
  `sdd_config`, y al hacerlo para usar el helper el hook de pre-commit se cayó
  con "requiere PyYAML": el módulo abortaba **al importarse** si falta la
  dependencia, y los hooks corren en un venv sin ella. → A: el chequeo se mueve
  a `load()`, que es quien de verdad lee el YAML. Importar `sdd_config` da
  acceso a helpers de stdlib (`forzar_salida_utf8`, `find_repo_root`,
  `write_text_lf`) que no necesitan PyYAML para nada. No es una concesión al
  fix: `sdd_gate._source_roots` y `spec_index` ya capturaban ese `SystemExit`
  alrededor de `load()` para degradar, o sea que el contrato que asumía el resto
  del kit era este, y el import lo cumplía por accidente.
- Q: ¿Alcanza con un helper que nadie obligue a llamar? → A: no — sería el
  patrón que K-3 encontró en la cobertura: un mecanismo correcto que los
  entrypoints nuevos no adoptan. El test barre los módulos con bloque
  `__main__` y exige que cada uno lo invoque, así que un entrypoint futuro que
  se olvide sale en rojo.

## Acceptance Scenarios

- **Given** un entorno Windows, **When** corre `python core/pipeline.py`,
  **Then** sale VERDE (antes: ROJO 8/10 por `tests` + `coverage`).
- **Given** cualquier plataforma, **When** se elimina el `chmod` de
  `sdd_init.py`, **Then** la suite falla — la protección del wiring ejecutable
  sigue viva.
- **Given** un entorno POSIX, **When** corre la suite, **Then** además se
  verifica el bit real en `st_mode` del hook instalado.
- **Given** un entorno cuya codificación de salida no es UTF-8 (Windows con la
  salida redirigida, `PYTHONIOENCODING=cp1252`), **When** un entrypoint del kit
  imprime texto acentuado, **Then** lo emitido es UTF-8 válido y legible (antes:
  `VERDE �`, `agn�stica`).
- **Given** un entrypoint nuevo que se olvida de forzar la codificación,
  **When** corre la suite, **Then** falla nombrando el módulo.

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
- **FR-005** MUST: todo entrypoint del kit —cada módulo de `core/` y de
  `adapters/<lang>/` con bloque `__main__`— fuerza la codificación UTF-8 de
  `stdout` y `stderr` al arrancar, invocando un helper único de
  `core/sdd_config.py`. El helper es tolerante: si el stream no expone
  `reconfigure` (redirigido a un buffer, capturado por la suite), no falla. Un
  test barre los entrypoints y falla nombrando al que no lo invoque, para que la
  garantía no dependa de acordarse.
- **FR-006** MUST: importar `core/sdd_config.py` no exige PyYAML; la dependencia
  se reclama en `load()`, que es lo único que lee el YAML. Un entrypoint que
  solo usa sus helpers de stdlib —el caso de los hooks de pre-commit, que corren
  en un venv sin dependencias— tiene que poder importarlo sin abortar.

## Key Entities

- `tests/unit/test_sdd_init_seeded_steps.py` — el test defectuoso.
- `tests/unit/conftest.py` — sede del criterio compartido de FR-004.
- `core/sdd_init.py::_EXECUTABLE_WIRING` — contrato verificado; no se modifica.
- `core/sdd_config.py::forzar_salida_utf8` — helper único de FR-005; reemplaza
  el bloque repetido en `check_constitution.py` y `check_traceability.py`.

## Success Criteria

- **SC-001** `python core/pipeline.py` en Windows → VERDE 10/10 (antes: ROJO
  8/10).
- **SC-002** Quitar el `chmod` de `sdd_init.py` hace fallar la suite en
  Windows (verificación manual de que FR-001 no es un test vacío).
- **SC-003** `pytest tests/unit` sin fallos ni errores en Windows.
- **SC-004** Un entrypoint invocado con `PYTHONIOENCODING=cp1252` y la salida
  redirigida emite bytes UTF-8 válidos (antes: `cp1252`, con los acentos
  reemplazados por `?`/`�` o un `UnicodeEncodeError`).
- **SC-005** Los 15 entrypoints de `core/` y `adapters/python/` invocan el
  helper (antes: 2 de 15, con el bloque copiado).

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
| FR-005 | tests/unit/test_salida_utf8.py |
| FR-006 | tests/unit/test_salida_utf8.py |

## Fuera de alcance

- Matriz de CI multiplataforma (hoy corre solo Linux) — anotable en
  `docs/IDEAS.md`.
- *(Hasta 2026-08-12: "cualquier otro fallo de plataforma que no sea el del
  wiring ejecutable". Enmendado al incorporar FR-005: el alcance es la paridad
  Windows/POSIX del kit, y la codificación de la salida es parte de ella. Lo que
  sigue fuera es un fallo de plataforma sin diagnóstico ni reproducción.)*

## Historial

- 2026-08-04: creada (draft), registrada en `SPECS_REGISTRY.md` y declarada en
  `.sdd/current-spec`.
- 2026-08-04: implementada y promovida a `active`. Pipeline VERDE 10/10 en
  Windows (SC-001), 139 passed + 1 skip justificado (SC-003). SC-002 verificado
  a mano: parcheando `sdd_init.py` para no aplicar el `chmod`, la suite falla
  en Windows con `no se aplico chmod a .claude/sdd_gate_hook.sh`.
- 2026-08-12: **ampliada** (FR-005, SC-004/SC-005; enmienda del *Fuera de
  alcance*) con C-2 de `docs/IDEAS.md`, el otro modo en que Windows degrada la
  señal del kit: la salida cae a `cp1252` y el texto acentuado se vuelve
  ilegible. Estaba reproducido por bytes desde la campaña de usabilidad y volvió
  a aparecer en esta sesión, en el triage de `sdd_spec.py`.
