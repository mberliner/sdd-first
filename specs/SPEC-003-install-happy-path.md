# SPEC-003: Happy path de instalación

> Origen: ítems B-1..B-4 (P0/P1) de `docs/IDEAS.md`, reproducidos en sandbox
> el 2026-07-02. Un proyecto recién instalado con `sdd-init` debe arrancar con
> pipeline VERDE y las herramientas del kit no deben romper sus propios
> artefactos.

## User Story (Priority P1)

Como usuario nuevo del kit, quiero que la instalación recién sembrada corra el
pipeline en VERDE y que `sdd-spec` deje el registro bien formado, para confiar
en el kit desde el primer minuto en vez de arrancar depurándolo.

**Why this priority:** hoy una instalación fresca sale ROJO 6/10 y la primera
spec creada rompe la tabla del registro — es la primera impresión del kit.

**Independent Test:** `sdd-init` en un directorio vacío + render + gen +
pipeline → VERDE sin instalar tooling extra; `sdd_spec.py` en ese proyecto
agrega la fila dentro de la tabla del registro. Y sobre un proyecto que **ya
tiene código**: el pipeline mide ese código (no lo omite) y el resumen
distingue los pasos que verificaron algo de los que se omitieron.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

## Clarifications

### Session 2026-07-02
- Q: ¿Cómo evitar el ROJO por tooling ausente (B-3)? → A: doble medida: el
  config sembrado declara solo los pasos que funcionan out-of-the-box
  (proceso + naming + tests), y el adaptador python omite con aviso (exit 0)
  los pasos cuya tool no está instalada, imitando el trato de
  `language: none`. El config de ejemplo completo sigue mostrando los 10 pasos.
- Q (descubierto al verificar): el set mínimo sin `layers` hace fallar
  `check_constitution` (el principio II del ejemplo declara `lint-imports`
  como enforcement y exige el paso cableado). → A: `layers` se siembra
  igualmente; sin import-linter instalado, el adaptador lo omite con aviso.
- Q: ¿Relax de naming (B-2): por basename o por config? → A: por config: un
  target se considera "de tests" si su ruta está bajo alguno de los dirs de
  tests declarados (`tests_unit`, `tests_integration`), con fallback al
  basename `tests`/`test` para proyectos sin dirs declarados.

### Session 2026-08-05 (reapertura)

- Q: ¿Por qué se reabre? → A: la campaña de usabilidad instaló el kit en un
  proyecto Python real con código en `app/`. Resultado: pipeline VERDE 8/8 con
  `naming` y `tests` omitidos, dos violaciones de SPEC-000 sin detectar y el
  gate permitiendo commits sobre `app/`. Dos decisiones de esta spec lo causan:
  el sembrado de `dirs` (hermano del de FR-005, nunca hecho) y la omisión con
  exit 0 de FR-001/FR-004.
- Q: ¿Se arregla omitiendo menos, o reportando mejor? → A: reportando mejor. La
  omisión sigue siendo correcta —una instalación fresca no puede arrancar en
  ROJO por tooling que todavía no tiene—; lo que estaba mal es que un paso
  omitido se cuente como un paso OK. Se introduce un tercer estado en el
  contrato de adaptador (exit 3), y el pipeline lo imprime y lo tabula aparte.
- Q: ¿Por qué exit 3 y no un marcador en stdout? → A: el pipeline invoca al
  adaptador con `subprocess.call` y deja su salida en streaming; parsear stdout
  obligaría a capturarla y reemitirla. El exit code es el canal que el contrato
  ya usa. Obliga a enmendar `adapters/CONTRACT.md` y SPEC-001 FR-005.
- Q: ¿Y si el proyecto no tiene código todavía? → A: `dirs` se siembra mínimo,
  con un TODO. `sdd_config.source_roots` cae a `src` cuando `dirs` no declara
  capas, así que el gate conserva su default y greenfield no cambia.
- Q: ¿Se siembra también `layers` según el layout detectado? → A: no, fuera de
  alcance. Las capas no se pueden inferir de la estructura de carpetas y el
  principio II las respalda; `sdd-configure` es quien las pregunta.
  `gen_import_linter` ya cae a `<source_root>/<capa>` cuando `dirs` no declara
  la capa, así que el comportamiento no empeora respecto de hoy.

### Session 2026-08-08 (reapertura)

- Q: ¿Por qué se reabre otra vez? → A: la suite e2e de SPEC-018, corrida con
  `lint-imports` en el PATH, mostró que una instalación fresca sale **ROJO** en
  el paso `layers`: `.importlinter` se generaba con `[[importlinter:contract]]`
  (sintaxis TOML de array-of-tables) dentro de un archivo que import-linter lee
  como INI con `configparser`. Los corchetes dobles no son un nombre de sección
  válido y, repetidos por cada contrato, revientan con `section '' already
  exists`. Es una violación directa de SC-001, viva desde que existe el
  generador.
- Q: ¿Por qué ningún test lo vio? → A: por dos ausencias que se tapaban entre
  sí. El generador solo se verificaba por *drift* (`--check` compara el archivo
  con lo que el propio generador produce: siempre coincide, sea válido o no), y
  el kit no declara `layers` en sus `pipeline.steps`, así que su pipeline nunca
  ejecuta `lint-imports`. La regla que faltaba no es "generar bien": es que
  **alguien lea lo generado con el parser real**.
- Q: ¿Se arregla emitiendo TOML en `pyproject.toml` en vez de INI? → A: no. El
  archivo `.importlinter` sigue siendo el destino (no toca el `pyproject.toml`
  del proyecto adoptante, que es suyo); lo que cambia es la sintaxis, a la
  sección INI por contrato que import-linter documenta:
  `[importlinter:contract:<capa>]`.
- Q: ¿El paso `layers` debería fallar si `lint-imports` no está? → A: no, sigue
  vigente FR-004 (omitir con aviso y exit 3). Lo que no puede pasar es que
  *estando* instalado, el archivo que le damos sea ilegible.
- Q (descubierto al verificar el fix): con el `.importlinter` ya legible, la
  instalación fresca **seguía** ROJO: `lint-imports` importa el paquete raíz
  para construir el grafo y en greenfield no existe (`Could not find package
  'src'`). → A: `step_layers` era el único paso de código sin la guardia de
  targets de FR-001 —sus hermanos (`naming`, `lint`, `format`, `types`) ya
  omiten cuando no hay carpetas—; se le agrega (FR-011). Dos defectos
  encadenados con la misma raíz: el paso nunca se había ejecutado de verdad.

## Acceptance Scenarios

- **Given** un directorio vacío, **When** corre `sdd-init` + render + gen +
  pipeline, **Then** el pipeline sale VERDE (pasos de código sin targets o sin
  tool se omiten con aviso, no fallan).
- **Given** un proyecto con `csv` en `relax_in_tests` y tests en
  `tests/unit/`, **When** corre el paso `naming`, **Then** los identificadores
  con `csv` en tests no se reportan.
- **Given** el registro plantilla (con sección Roadmap después de la tabla),
  **When** `sdd_spec.py` registra una spec nueva, **Then** la fila queda
  dentro de la tabla de `## Specs vigentes`, antes del Roadmap.
- **Given** un proyecto con código en `app/` y tests en `tests/`, **When** corre
  `sdd-init`, **Then** el `.sdd/config.yaml` sembrado declara
  `source_roots: [app]` y `tests_unit: tests`, y la instalación informa qué
  layout detectó.
- **Given** ese mismo proyecto, **When** corre el pipeline sin editar el config a
  mano, **Then** el paso `naming` verifica `app/` y reporta sus violaciones (el
  pipeline sale ROJO por el código, no VERDE por no haber mirado).
- **Given** un paso que el adaptador omite (sin targets, sin tool o sin umbrales),
  **When** el pipeline lo agrega, **Then** lo imprime como `[OMITIDO]`, no lo
  cuenta entre los pasos OK y el resumen final informa cuántos se omitieron.
- **Given** una instalación fresca con `import-linter` instalado, **When** corre
  el paso `layers`, **Then** `lint-imports` lee el `.importlinter` generado y
  evalúa los contratos (no aborta al parsear el archivo).

## Functional Requirements

- **FR-001** MUST: `adapters/python/adapter.py` con cero targets existentes
  para un paso lo omite con aviso y **exit 3** (`EXIT_OMITIDO`), sin invocar la
  tool sin argumentos. *(Enmendado el 2026-08-05: antes exit 0, indistinguible
  de un pase real — ver FR-009.)*
- **FR-002** MUST: la relajación de tokens en tests aplica a los directorios
  de tests declarados en el config (`dirs.tests_unit`/`tests_integration`),
  no solo a roots con basename `tests`/`test`.
- **FR-003** MUST: `sdd_spec.py` inserta la fila nueva al final de la tabla
  de `## Specs vigentes` del registro (última línea `|` contigua), no al final
  del archivo.
- **FR-004** MUST: los pasos de código cuya tool no está instalada se omiten
  con aviso y **exit 3** en el adaptador python (paridad con `language: none`).
  *(Enmendado el 2026-08-05, ver FR-009.)*
- **FR-005** MUST: el config sembrado por `sdd_init.py` declara solo pasos
  operativos out-of-the-box: constitution, traceability, naming, layers,
  skills, tests; los demás quedan comentados con instrucción de habilitarlos
  (`layers` se incluye porque el principio II del ejemplo lo exige cableado;
  sin import-linter se omite con aviso).
- **FR-006** SHOULD: el README aclara qué tooling requiere cada paso de
  código del adaptador python (ruff, mypy, bandit, pytest, import-linter).
- **FR-007** MUST: `core/sdd_init.py` siembra `dirs` según el layout real del
  destino: detecta la carpeta de código (primera de `src`, `app`, `lib`, `pkg`,
  `source`, `internal` que exista y contenga archivos del lenguaje) y la de
  tests (`tests/unit`, si no `tests`), y declara `source_roots` y `tests_unit`
  en consecuencia. Sin detección —o con `--language none`— siembra un `dirs`
  mínimo con un TODO, **sin** las rutas de capas del proyecto de referencia.
- **FR-008** MUST: el `README.md` y el playbook de `sdd-configure` nombran
  `dirs` y `source_roots` entre los parámetros a ajustar; son los que hacen que
  el gate y los pasos de código apunten al código del proyecto.
- **FR-009** MUST: un paso omitido es distinguible de un paso OK. El contrato de
  adaptador gana un tercer estado (`EXIT_OMITIDO = 3` en `core/sdd_config.py`,
  documentado en `adapters/CONTRACT.md`); `core/pipeline.py` lo imprime como
  `[OMITIDO]`, lo excluye del conteo de pasos OK e informa el total de omitidos
  en la línea de cierre. Aplica también al paso de proceso `hooks` cuando no hay
  repositorio git.
- **FR-010** MUST: lo que genera un adaptador para una tool externa tiene que
  ser legible **por esa tool**, y un test lo verifica con su parser, no con una
  comparación contra el propio generador. En concreto:
  `adapters/python/gen_import_linter.py` emite un `.importlinter` en sintaxis
  INI —`[importlinter]` y una sección `[importlinter:contract:<capa>]` por
  contrato— y un test unitario lo parsea con el lector de import-linter (o, si
  no está instalado, con `configparser`, que es lo que ese lector usa) y
  comprueba que aparezcan todos los contratos declarados por `layers`. Un
  chequeo de drift (`--check`) no cuenta como cobertura: compara el generador
  consigo mismo.
- **FR-011** MUST: `step_layers` aplica la misma guardia de targets que el
  resto de los pasos de código (FR-001): con `lint-imports` instalado pero sin
  capas declaradas en `layers`, o sin el paquete raíz (`source_roots[0]`) en
  disco, omite con aviso y exit 3 en vez de dejar que la tool aborte. Era el
  único paso de código sin esa guardia.

## Key Entities

- `adapters/python/adapter.py` — omisión por targets/tool ausentes.
- `adapters/python/check_naming.py` — relax por dirs de tests del config.
- `core/sdd_spec.py` — inserción de fila en tabla.
- `core/sdd_init.py` — config sembrado con pasos operativos y, desde la
  reapertura, `_seed_dirs` (detección de layout).
- `core/sdd_config.py::EXIT_OMITIDO` — tercer estado del contrato de adaptador.
- `core/pipeline.py` — agregación con `[OMITIDO]` y conteo aparte.
- `core/bootstrap_hooks.py` — el no-op sin git se reporta como omitido.
- `adapters/CONTRACT.md` — contrato de exit codes (0 / 3 / otro).
- `adapters/python/gen_import_linter.py` — traducción de `layers` a contratos;
  desde FR-010, en la sintaxis INI que import-linter realmente lee.

## Success Criteria

- **SC-001** Instalación fresca en sandbox → pipeline VERDE (antes: ROJO 6/10),
  y el resumen declara cuántos pasos se omitieron en vez de contarlos como OK
  (antes: `VERDE 8/8` con 4 pasos que no verificaron nada).
- **SC-002** Token relajado en `tests/unit/` no reporta violación (antes: 2
  violaciones con el config de ejemplo).
- **SC-003** Registro instalado sigue siendo una tabla markdown válida tras
  `sdd_spec.py` (fila dentro de la tabla).
- **SC-004** El kit sigue VERDE 7/7 (sin regresión de SPEC-002).
- **SC-005** Instalación sobre un proyecto con código en `app/`: el paso `naming`
  lo verifica sin editar el config a mano (antes: omitido con el aviso "sin
  carpetas de codigo todavia", 2 violaciones sin detectar).
- **SC-006** El gate bloquea la edición del código real de ese proyecto tras la
  instalación (antes: permitía commits sobre `app/`, bloqueaba solo `src/`).
- **SC-007** Instalación fresca **con `import-linter` instalado**: el paso
  `layers` corre y el pipeline sigue VERDE (antes: ROJO 4/5, `lint-imports`
  abortaba con `While reading from '<string>' : section '' already exists`
  sobre el `.importlinter` recién generado).

## Assumptions

- pytest sí se considera tooling base razonable para el paso `tests` (si no
  está, FR-004 lo omite con aviso).
- El config de ejemplo (`examples/config/config.yaml`) conserva los 10 pasos
  como referencia completa; solo cambia el sembrado por defecto.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_python_adapter.py |
| FR-002 | tests/unit/test_check_naming.py, tests/unit/test_python_adapter.py |
| FR-003 | tests/unit/test_sdd_spec.py |
| FR-004 | tests/unit/test_python_adapter.py |
| FR-005 | verificación manual: install sandbox → pipeline VERDE (SC-001) |
| FR-006 | verificación manual (README) |
| FR-007 | tests/unit/test_sdd_init_seeded_dirs.py, tests/unit/test_install_brownfield.py |
| FR-008 | tests/unit/test_readme_bootstrap.py |
| FR-009 | tests/unit/test_pipeline_omitidos.py, tests/unit/test_python_adapter.py, tests/unit/test_bootstrap_hooks.py, tests/unit/test_install_brownfield.py |
| FR-010 | tests/unit/test_gen_import_linter.py |
| FR-011 | tests/unit/test_python_adapter.py |

## Fuera de alcance

- Endurecimiento del gate (G-1..G-7) → SPEC-004.
- Skills `sdd-*` en el proyecto instalado (E-1) → SPEC-006.
- Sembrar `layers` según el layout detectado: las capas no se infieren de la
  estructura de carpetas (ver Clarifications de la reapertura).
- Que la instalación diga la verdad sobre lo que dejó cableado y hable en
  términos del derivado → U-4..U-11 y G-4 de `docs/IDEAS.md`, reservados en
  bloque para SPEC-014.
- Derivar el pre-filtro `files:` de `.pre-commit-config.yaml` desde
  `source_roots` (hoy es `^(src|app|lib)/` fijo) → G-1 de `docs/IDEAS.md`.

## Historial

- 2026-07-02: creada (draft) desde B-1..B-4 de `docs/IDEAS.md`.
- 2026-08-05: **reabierta** (FR-007..FR-009, SC-005/SC-006; enmienda de
  FR-001/FR-004 y de SC-001). La campaña de usabilidad del proyecto derivado
  (`sdd-testbed/INFORME.md`, hallazgos C1/C2/C5) mostró que el happy path solo
  se cumplía en un directorio vacío: instalado sobre un proyecto Python con
  código en `app/`, el pipeline salía VERDE 8/8 con `naming` y `tests` omitidos,
  dos violaciones de SPEC-000 sin detectar y el gate permitiendo commits sobre
  `app/`. Causa: el config sembrado heredaba el layout del proyecto de
  referencia (`src/domain`, `tests/unit`) y la omisión con exit 0 de FR-001/FR-004
  hacía indistinguible "no medí" de "medí y pasó". Ítems U-1..U-3 de
  `docs/IDEAS.md`; cierra de paso C-1 (paso desconocido contado como OK).
  Verificado: greenfield sigue VERDE y ahora declara `4/4 pasos OK` + `Omitidos
  (4)` en vez de `VERDE 8/8`; brownfield con `app/` sale ROJO por sus 2
  violaciones reales y el gate bloquea `app/servicio.py` en las tres capas, sin
  editar el config a mano. 166 tests + 1 skip, kit VERDE 10/10.
