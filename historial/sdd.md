# Historial SDD — sdd-first

## 2026-08-17 — SPEC-003 FR-015: `_vendor_kit` no copia `__pycache__`/`*.pyc`

**Scope:** `core/sdd_init.py` (`_vendor_kit`), `specs/SPEC-003-install-happy-path.md`
(FR-015, Coverage mapping).

**Qué cambió:** `_vendor_kit` copiaba `core/` y `adapters/<lang>/` al derivado
con `shutil.copytree(..., dirs_exist_ok=True)` sin filtro, así que si el clon
del kit tenía bytecode compilado en disco (típico tras correr los tests),
`sdd-init` y `sdd-update` —que reusa la misma función (`sdd_update.py:440`)—
vendorizaban `__pycache__/*.pyc` tal cual dentro de `tools/sdd/`: binarios
atados a una versión de CPython específica, no reproducibles, ajenos al
contenido real del kit. Se agregó
`ignore=shutil.ignore_patterns("__pycache__", "*.pyc")` a los dos `copytree`.

**Cobertura:** verificación manual (instalación real con `core/__pycache__/`
poblado → destino sin rastro de caché); sin test automatizado por decisión
explícita del usuario al pedir el fix.

```
[SDD-Check]
- Specs leídas: SPEC-003-install-happy-path (adoptada, FR-015 nuevo)
- Includes/excludes verificados: core/sdd_init.py::_vendor_kit
- Verificación: python core/pipeline.py → VERDE (11/11); sdd-init a target
  temporal con __pycache__ presente en el kit → sin __pycache__/*.pyc en
  tools/sdd/
```

## 2026-08-17 — X-2: `check_naming` también verifica nombres de directorio

**Scope:** `adapters/python/check_naming.py`, `tests/unit/test_check_naming.py`,
`specs/SPEC-001-agnostic-core.md` (FR-005 enmendado, sin FR nuevo),
`specs/SPECS_REGISTRY.md` (iteración de SPEC-001), `docs/IDEAS.md`,
`docs/IDEAS-CERRADAS.md`.

**Qué cambió:** el linter de nomenclatura agnóstica solo caminaba
identificadores AST (clase/función/variable/anotación) y el stem del archivo;
un directorio como `flask_adapter/` pasaba verde pese a violar la misma regla
que `SPEC-000-naming.md` declara para "módulo". Se agregó
`_violations_in_dir` y se la conectó en `main()` junto al recorrido de
archivos existente, reusando `prohibited`/`allowed`/`relax_in_tests` del
config sin cambios en `core/`.

**Triage de reuso:** `sdd_spec.py` marcó 6 specs vigentes con solape
(SPEC-000, SPEC-001, SPEC-002, SPEC-003, SPEC-019, SPEC-021, todas tocando
`check_naming.py` o su test por motivos distintos). Se adoptó **SPEC-001**
porque su FR-005 ya describía textualmente el linter de naming del adaptador
python — se amplió el texto del FR (no se creó uno nuevo), con precedente de
enmienda análoga en 2026-08-05 (contrato de exit codes).

**Alcance en derivados:** `adapters/<language>/` se vendoriza completo tanto
en la instalación (`sdd_init.py:158-160`) como en la actualización
(`sdd_update.py:435`), así que el chequeo llega a todo derivado sin tocar
`core/`. No es retroactivo: aplica sobre los directorios que el derivado ya
tenga o cree de ahí en más dentro de sus `dirs.source_roots`.

```
[SDD-Check]
- Specs leídas: SPEC-001-agnostic-core (adoptada, FR-005 enmendado)
- Includes/excludes verificados: adapters/python/check_naming.py + tests/unit
- Verificación: python core/pipeline.py → VERDE (11/11)
```

## 2026-08-17 — Correcciones de docs/IDEAS.md: X-1, X-4, C-1, E-5

**Scope:** `core/render.py`, `specs/SPEC-005-desduplicar-ssot.md` (FR-014,
Coverage mapping), `tests/unit/test_render.py`, `specs/SPEC-000-naming.md`
(regenerado), `specs/SPECS_REGISTRY.md` (iteración de SPEC-005),
`examples/config/config.yaml`, `README.md`, `docs/IDEAS.md`,
`docs/IDEAS-CERRADAS.md`.

**Qué cambió:** cuatro ítems del backlog abierto, cada uno en su propio
commit, priorizando reusar la spec origen de la funcionalidad tocada antes
que crear una nueva:
- **X-1 → SPEC-005 FR-014 (único con cambio de comportamiento, requirió
  spec):** `render_naming_spec` emitía un placeholder `- (ninguno)` bajo un
  header sin contenido real cuando `naming_allowed`/`naming_relax_in_tests`
  estaban vacías en el config. Se reusó SPEC-005 (ya gobierna `render.py` y
  trata `SPEC-000-naming.md` como archivo sincronizado) en vez de crear spec
  nueva; se agregó FR-014, su fila en el Coverage mapping y 2 tests nuevos en
  `tests/unit/test_render.py` (no había cobertura previa de
  `render_naming_spec`). Se corrigieron las dos secciones que podían quedar
  vacías, no solo la que citaba el ítem original.
- **X-4 → cerrado sin spec, por revisión de código:** la marca
  `.sdd-e2e-workspace` de `tests/e2e/lib/entorno.py:rehacer()` ya se escribe
  inmediatamente tras el `mkdir` desde el commit `3ad7b82` (2026-08-08),
  anterior al registro del ítem. La descripción no correspondía al estado
  real del código; se cerró como obsoleta, sin tocar código.
- **C-1 (resto) → doc, sin spec (no cambia comportamiento):**
  `examples/config/config.yaml` seguía listando `gate` como paso de proceso
  del pipeline, contradiciendo la línea vecina y la decisión ya tomada de que
  el gate se cablea vía hooks.
- **E-5 → doc, sin spec:** el README prometía soporte a "Cursor" sin
  respaldo real; se corrigió por Antigravity (sí documentado como consumidor
  de `.agents/skills/`). La mitad del ítem sobre tooling del adaptador python
  ya estaba resuelta, sin que quedara registrado el cierre.

**Decisiones de diseño:**
- **Solo X-1 pasó por `sdd-spec`**, porque es el único de los cuatro que
  cambia la salida de una herramienta del kit; los otros tres son ediciones
  de doc/config de ejemplo sin efecto en el comportamiento verificado por el
  pipeline, así que no requieren declarar spec (AGENTS.md exige spec para
  "cambio de comportamiento", no para cualquier edición de texto).
- **Commits independientes por ítem** (no uno solo de "correcciones de
  IDEAS.md"), para que cada cambio sea revisable y revertible por separado.

**SSOTs afectados:** SPEC-005 (iteración 4→5 en `SPECS_REGISTRY.md`),
`docs/IDEAS.md`/`docs/IDEAS-CERRADAS.md` (los cuatro ítems movidos con su
post-mortem).

```
[SDD-Check]
- Specs leídas: SPEC-005-desduplicar-ssot (FR-014)
- Includes/excludes verificados: core/render.py, examples/config/config.yaml, README.md; C-1/E-5/X-4 evaluados como fuera de alcance de sdd-spec (sin cambio de comportamiento)
- SSOTs afectados: SPEC-005 + SPECS_REGISTRY.md (iteración) + docs/IDEAS.md + docs/IDEAS-CERRADAS.md
- Verificación: .venv/bin/python core/pipeline.py → VERDE (11/11)
```

## 2026-08-17 — C-9/C-6 de docs/IDEAS.md: bug de parser y tres vestigios de código

**Scope:** `specs/SPEC-004-enforcement-hardening.md` (FR-010, SC-007),
`specs/SPEC-003-install-happy-path.md` (FR-014), `specs/SPEC-016-skills-listas-tras-init.md`
(FR-010), `specs/SPEC-017-gate-decision-spec-first.md` (FR-US2-004),
`specs/SPEC-023-relacion-entre-specs.md` (prosa), `core/sdd_init.py`,
`adapters/python/gen_import_linter.py`, `core/check_traceability.py`,
`specs/SPECS_REGISTRY.md`, `templates/specs/SPECS_REGISTRY.md`.

**Qué cambió:** cuatro fixes independientes, cada uno reusando la spec que ya
gobernaba el archivo tocado (sin spec "de higiene" genérica):
- **C-9 → SPEC-004 FR-010:** `sdd_init._seed_pipeline_steps` cortaba el
  descarte del bloque `steps:` original en la primera línea que no empezaba
  con `"- "`; un comentario intercalado entre pasos dejaba sobrevivir (y
  duplicarse) los pasos siguientes. Fix: descarta por indentación, no por
  forma de línea.
- **C-6a → SPEC-003 FR-014:** `gen_import_linter._module_of` recibía
  `repo_root` sin usarlo desde el commit inicial. Eliminado.
- **C-6b → SPEC-016 FR-010:** `sdd_init._install_project_skills` calculaba
  `src` (ruta a un playbook) y la descartaba con `_ = src` — dead code desde
  que el copiado de playbooks pasó a `STATIC_DOCS`. Eliminado.
- **C-6c → SPEC-017 FR-US2-004:** `check_traceability.VALID_ESTADOS` incluía
  `notas`, un estado sin fila que lo usara ni semántica documentada, mientras
  `SPECS_REGISTRY.md` mantenía su propia enumeración de estados en prosa. Se
  fija `VALID_ESTADOS` como origen único (el registro lo cita como fuente) y
  se retira `notas`; de paso se corrigió una mención stale del mismo estado en
  SPEC-023 FR-US2-007 (prosa, sin cambio de comportamiento).

**Decisiones de diseño:**
- **Ningún fix creó spec nueva.** El triage de `sdd_spec.py` sobre archivos
  compartidos (`sdd_init.py`, `check_traceability.py`) devuelve ruido —14+
  candidatas por coincidencia de archivo, no de capacidad—, así que la regla
  aplicada fue "por funcionalidad": cada vestigio se rastreó hasta la spec que
  ya declara la función que lo contiene (SPEC-004 ya tenía FR-005 sobre
  `_SEEDED_STEPS`; SPEC-003 ya tenía FR-010 sobre este mismo archivo de
  `gen_import_linter`; SPEC-016 ya gobierna `_install_project_skills`;
  SPEC-017 ya declara la semántica de estados en FR-US2-002).
- **Se evaluó y se descartó agregar la regla `ARG` (flake8-unused-arguments)
  de ruff al `select` global** como prevención automática del vestigio de
  C-6a: `ruff check --select ARG` sobre `core/adapters/tests` reporta **121**
  violaciones preexistentes, la enorme mayoría firmas de fixtures/mocks de
  test que no usan todos sus parámetros a propósito (patrón idiomático de
  mocking). Habilitarla exige triar esas 121 líneas primero — alcance muy por
  encima de este cierre. Queda para una spec propia si se decide perseguir.
- **`_ = src` no lo detectó el linter porque para eso existe el patrón**: `F841`
  (ya activo) marca variables sin usar, y `_ = x` es exactamente la forma de
  silenciarlo sin borrar el código muerto. La prevención ahí no es una regla
  nueva — es no repetir el patrón.

**SSOTs afectados:** las cuatro specs listadas arriba, `SPECS_REGISTRY.md`
(iteración de cada una), `templates/specs/SPECS_REGISTRY.md` (misma prosa de
Convenciones, actualizada en paralelo — no hay sync automático entre ambos).

```
[SDD-Check]
- Specs leídas: SPEC-004-enforcement-hardening (FR-010), SPEC-003-install-happy-path (FR-014), SPEC-016-skills-listas-tras-init (FR-010), SPEC-017-gate-decision-spec-first (FR-US2-004)
- Includes/excludes verificados: core/sdd_init.py, adapters/python/gen_import_linter.py, core/check_traceability.py; regla ARG evaluada y descartada (fuera de alcance)
- SSOTs afectados: las 4 specs + SPECS_REGISTRY.md (iteración) + templates/specs/SPECS_REGISTRY.md + SPEC-023 (prosa)
- Verificación: .venv/bin/python core/pipeline.py → VERDE (11/11)
```

## 2026-08-16 — SPEC-005 FR-013: el bit de ejecución del wiring viaja en el índice

**Scope:** `specs/SPEC-005-desduplicar-ssot.md` (FR-013, SC-009),
`tests/unit/test_wiring_sincronizado.py`, el modo de
`.claude/sdd_gate_hook.sh` en el índice de git.

**Qué cambió:** `test_render_no_degrada_los_permisos_del_wiring_ejecutable`
(FR-012, de la iteración anterior) estaba en rojo. El bit de ejecución de
`.claude/sdd_gate_hook.sh` **nunca estuvo en el índice**: el archivo figura como
`100644` desde que nació (`e365aa6`, 2026-08-01), así que cualquier clon o
checkout lo materializa sin `+x`. Ahora el índice lo declara `100755` y un test
nuevo lo verifica ahí, no en el disco.

**Decisiones de diseño:**
- **El test mira el índice, no la copia de trabajo.** FR-012 puso el chmod en
  `render.py`, pero solo en la rama que **escribe**, y el pipeline corre
  `render --check`, que no escribe. Por eso el test de disco pasaba en la copia
  donde alguien acababa de correr el render y volvía a fallar tras el primer
  checkout o stash/restore de `pre-commit`: afirmaba una propiedad local a una
  máquina y a un momento. El disco es propiedad de una copia; el índice es lo
  que viaja.
- **Es la misma forma que FR-010, aplicada a otro atributo.** El LF ya se
  sostenía en dos puntos declarados —`render.py` lo escribe y `.gitattributes`
  hace que el checkout lo entregue así— justamente porque ninguno alcanza solo.
  FR-012 había hecho una sola mitad de ese par para el permiso; FR-013 escribe
  la otra.
- **Se arregla con `git update-index --chmod=+x`, no con un `chmod`.** Este clon
  tiene `core.fileMode = false`, así que un chmod suelto es invisible para git y
  no se hubiera commiteado nunca — que es parte de por qué el modo se quedó en
  `100644` quince días sin que nadie lo notara. El mensaje de fallo del test lo
  dice explícito para que el próximo no pierda el rato.
- **`templates/wiring/sdd_gate_hook.sh` sigue en `100644`, a propósito.** La
  plantilla no se ejecuta desde `templates/`, y el destino instalado en un
  derivado lo chmodea `sdd_init` (`sdd_init.py:869`). `EXECUTABLE_WIRING` declara
  destinos, no plantillas, y el alcance del FR es el índice **del kit**: el de un
  proyecto derivado es de su dueño.
- **No se tocó `render.py`.** El chmod de FR-012 sigue siendo correcto y
  necesario para el flujo de escritura; lo que faltaba estaba afuera del código.

**SSOTs afectados:** `specs/SPEC-005-desduplicar-ssot.md`,
`specs/SPECS_REGISTRY.md`, `docs/PATRONES.md` (patrón 6, evidencia nueva).

```
[SDD-Check]
- Specs leídas: SPEC-005-desduplicar-ssot (FR-010, FR-012, FR-013), SPEC-000-naming
- Includes/excludes verificados: wiring ejecutable del kit + tests/unit; plantillas y derivados fuera de alcance
- SSOTs afectados: SPEC-005, SPECS_REGISTRY.md, docs/PATRONES.md
- Verificación: .venv/bin/python core/pipeline.py → VERDE (11/11); 774 tests
```

## 2026-08-14 — SPEC-005 FR-008/FR-009: el wiring del kit deja de ser una copia

**Scope:** `specs/SPEC-005-desduplicar-ssot.md` (Clarifications 2026-08-14,
4 escenarios, FR-008/FR-009, SC-007/SC-008), `core/sdd_catalog.py`
(`WIRING_NO_SINCRONIZADO`, `wiring_sincronizado()`), `core/render.py`,
`templates/wiring/.pre-commit-config.yaml`,
`templates/wiring/opencode-sdd-gate.js`, `templates/wiring/.gitattributes`,
el wiring del propio kit (regenerado), `.opencode/plugin/sdd-gate.js` (nuevo),
`AGENTS.md`, `00-INDEX.md`, `tests/unit/test_wiring_sincronizado.py` (nuevo),
`tests/unit/test_render.py`.

**Qué cambió:** cada archivo de `templates/wiring/` que el kit se instala a sí
mismo existía dos veces y nada los mantenía juntos (R-4). Ahora el de la raíz se
genera con `render.py`, igual que los docs de FR-001: el arreglo se escribe una
vez, en la plantilla.

**Decisiones de diseño:**
- **La lista de destinos no se escribe en `render.py`.** Sale de
  `sdd_catalog.WIRING` menos `WIRING_NO_SINCRONIZADO`, un dict destino → motivo.
  Enumerarla a mano reintroducía el mismo drift un nivel más arriba: el séptimo
  archivo de wiring habría quedado huérfano igual que el primero. Un test exige
  que todo destino del catálogo esté de uno de los dos lados.
- **No se uniformó cómo cada archivo ubica el núcleo.** `.pre-commit-config.yaml`
  y el plugin de opencode hardcodeaban `tools/sdd/core` —válido en un solo
  layout— y pasan a `{{sdd.core}}`; el hook `sh` y `agy_gate_hook.py` ya prueban
  ambos en runtime y se sincronizan tal cual. Lo que la spec exige es un solo
  archivo, no una sola técnica.
- **`.gitignore` y `.sdd/current-spec` quedan fuera, con motivo escrito.** El
  primero es semilla (el kit ignora cosas propias); el segundo es estado de
  sesión que se reescribe en cada commit.
- **Lo "caro" del ítem no existía.** `_sync_renderer` ya leía texto, resolvía
  placeholders y escribía con `write_text_lf`: la extensión (`.sh`/`.json`/
  `.yaml`/`.js`) nunca entró en la decisión. Sí hizo falta declarar esos
  destinos `eol=lf` en `.gitattributes`: con `* text=auto`, un checkout en
  Windows los dejaba en CRLF, distintos de lo que el render acababa de escribir.

**Evidencia de que el drift era real, no teórico:** `.claude/sdd_gate_hook.sh`
arrastraba las 37 líneas del bloque `IS_ANTIGRAVITY` que su plantilla perdió en
`fc95761`, cuando el soporte de Antigravity se mudó a `.agents/agy_gate_hook.py`.
Rama inalcanzable —a ese `.sh` solo lo invoca Claude Code, que decide por exit
code— y sobrevivió una spec entera. El sync la borró sin que nadie la buscara.

**Deuda:** el kit pasó a tener instalado `.opencode/plugin/sdd-gate.js`, que le
pedía a sus derivados sin usarlo él: el gate spec-first ahora también corre en
sesiones de opencode sobre el kit.

**SSOTs afectados:** `core/sdd_catalog.py` (clasificación del wiring),
`templates/wiring/` (autoritativo del wiring), `AGENTS.md` y `00-INDEX.md`
(el wiring de la raíz no se edita a mano).

## 2026-08-13 — SPEC-015 US2: el gate de Antigravity pasa de decorativo a real

**Scope:** `specs/SPEC-015-wiring-apunta-al-codigo-real.md` (Clarifications
2026-08-13, escenarios de US2, FR-US2-002/-003/-004 reescritos, FR-US2-006/-007
nuevos, SC-005, Independent Test), `templates/wiring/agy_gate_hook.py` (nuevo),
`templates/wiring/agy_deny.json` (nuevo), `templates/wiring/hooks.json`,
`templates/wiring/sdd_gate_hook.sh`, `core/sdd_gate.py`, `core/sdd_catalog.py`,
`core/sdd_config.py`, `templates/docs/SDD-ENFORCEMENT.md` (+ derivado),
`.agents/` (las tres piezas, dogfooding), `tests/unit/test_sdd_gate_hook.py`,
`tests/unit/test_wiring_prefiltros.py`, `tests/unit/test_sdd_gate.py`.

**Qué cambió:** el soporte de Antigravity era una rama dentro del hook `sh` de
Claude Code y **nunca bloqueó nada**. Ahora es un adaptador propio,
`.agents/agy_gate_hook.py`, que traduce el payload del CLI y delega en
`sdd_gate.main`. El núcleo dejó de conocer `toolCall.args.TargetFile` y el hook
`sh` volvió a ser sólo de Claude Code.

**Decisiones de diseño:**
- **Un adaptador Python, no una tercera copia del pre-filtro.** Bash y JS
  duplican el parseo de `source_roots` porque no pueden invocar Python; acá
  Python está por definición, así que el adaptador pregunta al gate y no duplica
  regla ninguna. Delega en `main`, no en `decide`, para heredar el escape hatch
  y la resolución de raíz.
- **Medir antes de diseñar.** Los supuestos heredados del hook de Claude Code
  eran tres, y los tres falsos: Antigravity es **fail-open** (un hook que falla
  deja pasar la edición), invoca con el `cwd` en **`.agents/`** (así que
  `python .agents/agy_gate_hook.py` nunca resolvía), y no admite un `echo` como
  fail-closed (en `cmd.exe` las comillas le llegan escapadas y muere en
  `protojson`). El experimento y su evidencia:
  `sdd-testbed/agy-hook-probe/HALLAZGOS.md`.
- **Fail-closed total para esta capa.** `type agy_deny.json || cat agy_deny.json`
  bloquea todo cuando falta el intérprete, incluidos archivos que no son código.
  Contradice a propósito el "descartado el fail-closed total" de la Clarification
  del 2026-08-05: aquel argumento era un checkout irreparable, y acá el alcance
  es un asistente concreto — el proyecto se sigue editando con cualquier otro.
- **Los tests corren el adaptador desde `.agents/`**, que es como lo corre el
  CLI. Correrlo desde la raíz era lo que mantenía la suite verde con el gate
  apagado.

**Deuda:**
- SC-005 (testigo real conducido por `agy`) se verifica a mano; no hay e2e
  automatizado que maneje el CLI.
- El bypass por terminal quedó documentado como límite conocido, igual que el de
  `Bash` en Claude Code: el asistente, al ser bloqueado, intentó escribir el
  archivo con un comando de shell.

**SSOTs afectados:** `docs/SDD-ENFORCEMENT.md` (capa de Antigravity),
`specs/SPEC-015` (política del wiring), `core/sdd_catalog.py` (qué instala el kit).

## 2026-08-12 — SPEC-020 US2: un principio sin enforcement ejecutado no deja el pipeline en VERDE a secas

**Scope:** `specs/SPEC-020-enforcement-declarado-en-config.md` (nueva US2,
FR-US2-001..007, título ampliado), `core/sdd_config.py` (`EXIT_RESERVAS`,
`PIPELINE_STEPS_RUN_ENV`), `core/check_constitution.py` (`_check_ejecucion`),
`core/pipeline.py` (canal + cuarto estado), `core/sdd_init.py` (`_SEEDED_STEPS`),
`.sdd/config.yaml` y `examples/config/config.yaml` (orden de `constitution`),
`adapters/CONTRACT.md`, `tests/unit/test_pipeline_enforcement_ejecutado.py`
(nuevo), `tests/unit/test_check_constitution.py`,
`tests/unit/test_sdd_init_seeded_steps.py`, `tests/unit/test_pipeline_omitidos.py`,
`tests/e2e/escenarios/test_instalacion_limpia.py`, `docs/IDEAS.md`.

**Qué cambió:** cierra **"Omitido no es VERDE"** de `docs/IDEAS.md`. US1 verificaba
que el enforcement de cada principio estuviera *declarado* en `pipeline.steps`;
faltaba que hubiera *corrido*. Un paso declarado pero omitido en runtime —sin
tool, sin targets, sin umbrales— dejaba el principio sin verificar y el pipeline
decía VERDE igual. Ahora `check_constitution` recibe los pasos ya ejecutados de la
corrida y reporta los principios que quedaron sin enforzar; el resumen pasa a
decir "VERDE con reservas" sin cambiar el exit code.

**Decisiones de diseño:**
- **La idea, tal como estaba escrita, era irrealizable.** Pedía que
  `check_constitution` leyera el reporte de omitidos, pero el paso corría segundo
  y los pasos que enforzan principios cuarto y décimo: cuando el check corría no
  había reporte. Se movió el paso y se le abrió un canal (variable de entorno con
  los pasos ejecutados), mismo patrón y mismo degradado que
  `PIPELINE_COVERAGE_CACHE_ENV` entre `tests` y `coverage`.
- **En el check, no en el resumen del pipeline.** Se evaluó cruzar `omitidos` ×
  `enforcement_steps` en `pipeline.py` —tiene los dos datos y no depende del
  orden— y se descartó para que el mensaje hable en lenguaje de principios y
  aparezca junto al listado que el lector ya está mirando. El costo aceptado es
  el canal y la dependencia del orden, que se compensa abajo.
- **Un exit code dedicado, no un segundo cruce.** El pipeline traduce
  `EXIT_RESERVAS` a un estado visible pero **no recalcula** el criterio: dos
  implementaciones del mismo criterio divergen por construcción (Principio IV).
- **Ni ROJO ni `strict` por principio.** ROJO rompe frontalmente SPEC-003 FR-001
  —una instalación fresca volvería a arrancar en rojo—; una clave `strict`
  nacería en `false` para no romper derivados, o sea inerte (K-5). El verde
  condicionado muerde sin reabrir nada.
- **La posición del paso es derivable, no una constante.** Es "después del último
  paso de `enforcement_steps`"; para el kit cae penúltima (antes de `e2e`) porque
  el Principio V se enforza con `coverage`. Se conserva así la mitad del tiempo
  de feedback.
- **El degradado dice la verdad en los dos órdenes.** El criterio es "el paso no
  se ejecutó todavía", que cubre igual al omitido y al pendiente, así que un
  derivado que declare `constitution` primero recibe el aviso en vez de recuperar
  el hueco en silencio. La garantía no queda colgada de un orden que nada
  verifica —la familia V-1/C-8.
- **El cuarto estado no toca el contrato de adaptador.** `EXIT_RESERVAS` vale
  solo para pasos de proceso; de un adaptador cuenta como falla, así que
  `adapters/CONTRACT.md` sigue declarando tres estados y es cierto.

**Hallazgos:** (a) el orden sembrado ya contradecía su propia precondición
escrita: `sdd_init.py` documenta que "el paso `constitution` ya exige haber
corrido `render`" y lo sembraba cinco posiciones antes —el arreglo se sostiene
solo, sin esta US2—. (b) No era un caso de borde sino **el** caso: en una
instalación fresca se omiten los dos pasos que enforzan principios, así que el
primer VERDE de todo derivado se emitía con el 100% de sus principios sin
enforzar; la e2e de instalación limpia lo confirma y ahora lo afirma. (c)
Apareció **C-9**, registrado como idea: `_seed_pipeline_steps` corta el bloque
`steps:` en la primera línea que no es un ítem, así que un comentario intercalado
duplica los pasos que siguen —se descubrió porque el derivado nacía con
`constitution` dos veces—.

**Verificación:** `python core/pipeline.py` VERDE 11/11, 745 tests unitarios +
19 e2e en verde, `sdd-doctor` sano.

## 2026-08-12 — SPEC-019 US4: la raíz de `tests/` entra al alcance de los pasos estáticos

**Scope:** `specs/SPEC-019-tests-integracion-ejecutados.md` (nueva US4,
FR-US4-001..006), `core/sdd_config.py` (`colapsar_a_raiz_comun`),
`adapters/python/adapter.py` (`_source_and_test_dirs` la consume),
`adapters/python/check_naming.py` (`_is_test_root` bidireccional),
`tests/unit/test_raiz_de_tests_estatica.py` (nuevo),
`tests/unit/test_adapter_e2e.py`, `docs/IDEAS.md`.

**Qué cambió:** cierra **V-4** de `docs/IDEAS.md`. Las claves de `dirs` apuntan
a subcarpetas (`tests/unit`, `tests/e2e`), así que la infraestructura compartida
que vive en la raíz —`tests/conftest.py`, `tests/fixtures_proyecto.py`— no caía
dentro de ninguna y no la miraba `naming`, `lint` ni `format`. Desde ahora los
pasos estáticos reciben la raíz que contiene a las carpetas declaradas, derivada
de lo ya declarado en vez de pedida como clave nueva.

**Decisiones de diseño:**
- **Derivar la raíz, no declararla.** Se evaluó una clave `tests_root` y se
  descartó: es superficie de config que hay que sembrar, documentar y que el
  adoptante tiene que descubrir —la lección que US3 de esta misma spec dejó
  escrita para `tests_integration`—, y la raíz ya es derivable. No hay dato nuevo
  que pedirle al proyecto, solo una pregunta que nadie hacía.
- **Colapsar, no sumar.** Pasar `tests` junto a `tests/unit` deja al paso
  visitando la subcarpeta dos veces y duplicando cada violación en la salida que
  lee el operador (FR-US4-002).
- **Guarda contra la raíz del repo.** Con carpetas en árboles distintos
  (`pruebas/unit` y `e2e`) el único ancestro común es el repo entero; ahí no se
  colapsa nada. Con una sola carpeta declarada tampoco: subir a su ancestro
  ensancharía el alcance a hermanas que el proyecto nunca declaró.
- **Reapertura y no spec nueva.** SPEC-019 ya se declara SSOT de qué carpeta mira
  cada paso; una spec aparte dejaba dos SSOTs sobre el mismo contrato.

**Hallazgo:** el FR sobre `relax_in_tests` (FR-US4-004) se escribió como
precaución por B-2 y encontró un defecto **ya presente**:
`check_naming._is_test_root` miraba la relación en una sola dirección (¿el root
está *dentro* de una carpeta declarada?), así que la raíz derivada no calificaba
y solo la salvaba el fallback del basename `{"tests","test"}`. En este kit
funcionaba de casualidad —la carpeta se llama `tests`—; un proyecto con
`pruebas/unit` habría perdido la relajación en silencio. La relación ahora vale
en las dos direcciones.

**Costo lateral:** un test de [[SPEC-018-verificacion-e2e]] afirmaba el literal
`tests/e2e` en la invocación de `lint`. Se reescribió para afirmar el *alcance*
(la carpeta queda cubierta por `tests`, que la contiene): exigir el literal es
pedir exactamente el doble barrido que FR-US4-002 prohíbe. El invariante que
protegía —declarar la carpeta sirve para que los pasos estáticos la miren— queda
intacto.

**Deuda arrastrada:** el ítem #1 con el que V-4 se había agrupado ("omitido no es
VERDE": `check_constitution` no lee el reporte de omitidos del pipeline, así que
un principio cuyo paso de enforcement se omite en runtime deja la constitución en
verde) queda **abierto** en `docs/IDEAS.md`, sin spec.

```
[SDD-Check]
- Specs leídas: SPEC-019-tests-integracion-ejecutados, SPEC-018-verificacion-e2e,
  SPEC-003-install-happy-path (FR-002, relajación en tests)
- Includes/excludes verificados: core/sdd_config.py + adapters/python/adapter.py
  + adapters/python/check_naming.py + tests/unit; adapters/CONTRACT.md sin cambio
  (no especifica los blancos de los pasos estáticos, solo qué verifica cada uno)
- SSOTs afectados: SPEC-019-tests-integracion-ejecutados.md,
  specs/SPECS_REGISTRY.md (iteración 5), docs/IDEAS.md (V-4 cerrado; G-8, E-3,
  C-5, E-6 y F-7 anotados con el cierre que ya tenían sin registrar)
- Verificación: python core/pipeline.py → VERDE (11/11); 729 passed + 2 skipped
  en la suite unitaria
```

## 2026-08-12 — SPEC-009 US3: una corrida de pytest sirve para `tests` y `coverage`

**Scope:** `specs/SPEC-009-coverage-y-ci.md` (nueva US3, FR-US3-001..005),
`adapters/CONTRACT.md` (nota del mecanismo opcional), `core/sdd_config.py`
(`PIPELINE_COVERAGE_CACHE_ENV`), `core/pipeline.py` (cache temporal por
corrida), `adapters/python/adapter.py` (`step_tests` instrumenta y escribe,
`step_coverage` lee antes de correr pytest), `tests/unit/test_sdd_config.py`,
`tests/unit/test_python_adapter.py`, `tests/unit/test_pipeline_coverage_step.py`,
`tests/unit/test_pipeline_omitidos.py`, `tests/unit/test_pipeline_coverage_cache.py`
(nuevo).

**Qué cambió:** medido en el propio kit, la suite unitaria plana tarda ~74s y
la misma suite instrumentada con `--cov` ~141s; el pipeline pagaba las dos
corridas en secuencia (~215s) porque `tests` y `coverage` ejecutaban pytest
cada uno por su cuenta sobre exactamente las mismas carpetas. Ahora, dentro de
una corrida de `core/pipeline.py`, `tests` instrumenta su propia corrida con
`--cov` y deja el reporte en un archivo temporal (ruta en
`SDD_PIPELINE_COVERAGE_CACHE`); `coverage` lo lee y evalúa los umbrales
agregando cobertura por `paths` desde ese reporte, sin volver a invocar
pytest. Verificado en el propio pipeline: el tramo tests+coverage bajó de
~215s a ~150s (~30%).

**Decisiones de diseño:**
- **No se fusionan los pasos.** `tests` y `coverage` siguen siendo dos pasos
  nombrados con su propio veredicto: fusionarlos reintroduce el defecto que
  [[SPEC-019-tests-integracion-ejecutados]] corrigió (un test roto pintando
  `coverage` en rojo) y rompe el invariante de `sdd_doctor._tests_sin_ejecutor`
  (`dirs.tests_unit` tiene que tener *su propio* paso ejecutor). Lo que se
  comparte es la ejecución de pytest subyacente, no el resultado.
  Se evaluó primero sacar `tests` de `pipeline.steps` (config-only, cero
  cambios de código) y se descartó por esa misma razón.
- **Handshake por variable de entorno, no por contrato nuevo por paso.**
  `core/pipeline.py` crea un temporal por invocación y lo expone en
  `SDD_PIPELINE_COVERAGE_CACHE`; sin la variable (paso invocado suelto, como
  exige `adapters/CONTRACT.md`) cada paso corre exactamente como antes. Es
  opcional para los adaptadores `node`/`go` (roadmap).
- **La instrumentación solo se activa si `coverage` mide exactamente lo que
  `tests` ejecuta.** Si el proyecto también declara `tests_integration`
  medida, `tests` (que solo corre `dirs.tests_unit` por contrato) dejaría un
  reporte incompleto; en ese caso se omite la instrumentación y `coverage`
  cae sola a su loop de pytest por target, sin resultado incorrecto.
- El cache se borra siempre al terminar `core/pipeline.py` (haya fallado o
  no): un reporte que ningún paso llegó a leer no es un problema.

```
[SDD-Check]
- Specs leídas: SPEC-009-coverage-y-ci, SPEC-019-tests-integracion-ejecutados
- Includes/excludes verificados: core/pipeline.py + core/sdd_config.py +
  adapters/python/adapter.py + adapters/CONTRACT.md + tests/unit
- SSOTs afectados: SPEC-009-coverage-y-ci.md, adapters/CONTRACT.md,
  specs/SPECS_REGISTRY.md (iteración 7)
- Verificación: python core/pipeline.py → VERDE (11/11), tramo tests+coverage
  ~150s (antes ~215s); "cobertura evaluada desde el reporte de 'tests' (sin
  correr pytest de nuevo)" confirmado en la salida
```

## 2026-08-12 — SPEC-025: el andamiaje instalado se puede actualizar sin perder lo propio

**Scope:** `specs/SPEC-025-actualizar-kit-en-derivados.md` (30 FR, US1..US4,
`active`), `core/sdd_catalog.py` y `core/sdd_lock.py` (nuevos),
`core/sdd_update.py` (nuevo comando), `core/sdd_init.py`, `core/sdd_doctor.py`,
`core/sdd_config.py` (`KIT_VERSION`), `CHANGELOG.md` (nuevo),
`.agents/skills/sdd-update/`, `docs/playbooks/sdd-update.md`, `README.md`,
`templates/docs/SDD-OPERACION.md`, `00-INDEX.md` y `templates/00-INDEX.md`, 13
archivos de test nuevos en `tests/unit/` y
`tests/e2e/escenarios/test_actualizacion_kit.py`.

**Qué cambió:** promueve E-2 de `docs/IDEAS.md`. Antes de esta spec no había
forma segura de traer arreglos del kit a un proyecto ya instalado:
`project.kit_version` era una constante copiada del ejemplo (siempre
`"0.1.0"`, nunca comparada), y la única ruta de "actualización",
`sdd-init --force`, **borraba** `specs/SPECS_REGISTRY.md` y
`historial/sdd.md`.

- **US1 — registro:** `KIT_VERSION` vendorizado (`sdd_config.py`) y
  `.sdd/kit.lock`, un manifiesto JSON determinista que `sdd-init` escribe al
  terminar: versión, valores de sustitución usados, `sha256` por `plantilla`
  **tal como la entrega el kit** (nunca el contenido del disco — es lo que
  evita que una plantilla en conflicto se dé por intacta y se pise en
  silencio en la actualización siguiente) y presencia de cada `semilla`.
- **US2 — actualización:** `core/sdd_update.py`, simétrico a `sdd-init`,
  corrido desde el clon del kit apuntando al derivado. Purga y recrea
  `tools/sdd/`, pisa las plantillas intactas, deja las editadas sin tocar con
  la versión del kit en `<archivo>.kit-new`, propaga altas y bajas del
  catálogo, y reescribe el lock solo si todo salió bien. `sdd-init --force`
  pasa a respetar el mismo catálogo de clases (`core/sdd_catalog.py`:
  vendor/plantilla/semilla) — deja de borrar el registro y el historial, y
  aplica la misma política de conflicto sobre las plantillas.
- **US3 — el plan:** por defecto `sdd-update` solo muestra qué cambiaría (sin
  escribir); `--apply` lo aplica, `--diff` muestra el contenido.
- **US4 — changelog:** `CHANGELOG.md` con una entrada por `KIT_VERSION`, que
  el plan cita entre la versión instalada y la del kit.

**Decisiones de diseño:**
- El lock nunca lee el disco para decidir su propio contenido: `build_lock`
  arma cada hash desde `templates/` con los placeholders resueltos. Es lo que
  hace que el caso brownfield y el de un conflicto sin resolver registren la
  línea base correcta sin necesitar una rama especial.
- `sdd_catalog.decidir_plantilla` es la única función de decisión de
  conflicto, compartida por `sdd-init --force` y `sdd-update`: evita que las
  dos rutas de escritura del kit terminen aplicando criterios distintos.
- `STATIC_DOCS`/`WIRING` se mudaron de `sdd_init.py` a `sdd_catalog.py` (con
  `sdd_init` reexportándolos) para que el catálogo sea el único SSOT que
  ambos comandos consultan, sin import circular.
- Al escribir el `--force` sobre `.sdd/config.yaml`, se encontró un bug
  colateral: `sdd-init` sustituía las plantillas con un `domain` hardcodeado
  distinto del que terminaba escrito en `.sdd/config.yaml`, así que el lock
  registraba una sustitución que nunca coincidía con la del config real. Se
  corrigió leyendo `name`/`domain` del config recién escrito (mismo criterio
  que ya usa `sdd-update`, FR-US2-010), en vez de un literal aparte.
- `sdd-init --force` sobre un wiring propio del brownfield ya no puede
  "silenciar" el aviso pisándolo: sin lock que lo avale como intacto, sigue
  en conflicto (`tests/unit/test_sdd_init_wiring_conservado.py` se actualizó
  para reflejarlo).

## 2026-08-12 — SPEC-003 + SPEC-012: las herramientas del kit no fallan en silencio

**Scope:** `specs/SPEC-003-install-happy-path.md` (FR-012/FR-013, SC-008/SC-009),
`specs/SPEC-012-suite-multiplataforma.md` (FR-005/FR-006, SC-004/SC-005),
`core/sdd_init.py`, `core/sdd_spec.py`, `core/spec_index.py`,
`core/sdd_config.py`, los 15 entrypoints de `core/` y `adapters/python/`,
`tests/unit/test_sdd_init_cli.py`, `tests/unit/test_salida_utf8.py`,
`tests/unit/test_sdd_spec.py`.

**Qué cambió:** C-7, C-3, C-4 y C-2 de `docs/IDEAS.md`, elegidos juntos porque
comparten un modo de falla: una herramienta del kit hace algo distinto de lo que
se le pidió y lo reporta como éxito.

- **FR-012** (C-7 + C-3): `sdd_init.main` partía `argv` en "empieza con `--`" y
  "el resto", y de los flags leía solo `--force`/`--language`. `--target=<dir>`
  caía en el descarte y el destino terminaba siendo el **cwd**: ~40 archivos en
  el directorio equivocado, con la instalación informando éxito (pasó en vivo el
  2026-08-05 durante SPEC-015). Ahora `_parse_argv` valida todo antes de escribir
  nada. El catálogo de `--language` se deriva de `adapters/` en disco.
- **FR-013** (C-4): `_slugify` filtraba sobre el título crudo, así que cada
  acento abría un hueco (`búsqueda` → `b-squeda`) y ese era el nombre del archivo
  y el ID de la spec. No se escribió normalización nueva: `spec_index` ya
  transliteraba con NFKD para el triage, o sea que el kit tenía dos criterios y
  el defecto estaba en el que no lo hacía.
- **FR-005** (C-2): en Windows la salida cae a `cp1252` cuando no es una consola
  UTF-8 y todo el texto acentuado sale ilegible. Eran **2 de 15** entrypoints los
  que hacían `reconfigure`, y los 2 con el bloque copiado. Ahora
  `sdd_config.forzar_salida_utf8` es el único lugar que sabe cómo se fuerza, y lo
  sostiene un barrido que falla nombrando al entrypoint que se olvide.

**Decisiones de diseño:**
- Los tres ítems se **repartieron entre specs vigentes** en vez de abrir una spec
  nueva que los uniera: el invariante común ("la CLI no falla en silencio")
  describe bien el trabajo, pero cada fix pertenece a un invariante ya declarado
  —el happy path de instalación y la paridad Windows/POSIX—, y una spec nueva
  habría solapado con las dos.
- El *Fuera de alcance* de SPEC-012 decía "cualquier otro fallo de plataforma que
  no sea el del wiring ejecutable". Se **enmendó** en vez de esquivarlo: estaba
  escrito para no arrastrar problemas sin diagnóstico, no para vetar la
  codificación de la salida, que es paridad Windows/POSIX de manual.
- Se descartó migrar `sdd_init` a `argparse`: el parseo a mano es deliberado (el
  módulo se vendoriza y se ejecuta suelto) y movería la superficie de los
  mensajes de uso que la e2e y el README ya citan.

**Hallazgo destapado al verificar (FR-006):** darle el helper a
`check_traceability` —el único entrypoint que no importaba `sdd_config`— rompió
el hook de pre-commit con "requiere PyYAML": el módulo abortaba **al importarse**
y los hooks corren en un venv sin dependencias. La dependencia se reclama ahora
en `load()`, que es lo único que lee el YAML. No fue una concesión al fix:
`sdd_gate._source_roots` y `spec_index` ya capturaban ese `SystemExit` alrededor
de `load()` para degradar, o sea que el contrato que el resto del kit asumía era
este y el import lo cumplía por accidente.

**SSOTs afectados:** ninguno nuevo. `spec_index.sin_acentos` pasa a ser el SSOT
de la transliteración (antes privado) y `sdd_config.forzar_salida_utf8` el de la
codificación de salida; los dos ya vivían en el módulo que corresponde.

**Deuda anotada:** ninguna nueva. Del tier propuesto en esta sesión quedan
abiertos "omitido no es VERDE", V-4 (la raíz de `tests/` no la mira ningún paso),
R-4 (el wiring del kit es copia manual de `templates/wiring/`) y E-2
(`sdd-update`).

```
[SDD-Check]
- Specs leídas: SPEC-000-naming, SPEC-003-install-happy-path, SPEC-012-suite-multiplataforma, SPEC-022-reusar-specs-existentes, SPEC-024-traza-fr-en-test
- Includes/excludes verificados: core/ + adapters/python + tests/unit; templates/ y tests/e2e sin cambios (el fix no toca lo que se siembra, salvo el core vendorizado)
- SSOTs afectados: specs/SPEC-003-install-happy-path.md, specs/SPEC-012-suite-multiplataforma.md, docs/IDEAS.md (C-2/C-3/C-4/C-7 cerrados)
- Verificación: python core/pipeline.py → VERDE (11/11); pytest tests/unit → 626 passed, 2 skipped; mojibake del triage verificado a mano antes/después
```

## 2026-08-11 — SPEC-004 (reabierta, G-9): `.sdd/current-spec` deja de versionarse

**Scope:** `specs/SPEC-004-enforcement-hardening.md` (FR-008/SC-005),
`core/sdd_config.py`, `core/sdd_doctor.py`, `.gitignore`,
`templates/wiring/.gitignore`, `tests/unit/test_current_spec_no_versionado.py`,
`tests/e2e/escenarios/test_ciclo_spec_first.py`.

**Qué cambió:** G-9 de `docs/IDEAS.md` — el reset post-commit (`sdd_reset.py`,
FR-002) edita `.sdd/current-spec` *después* de que el commit ya cerró, así que
ese cambio nunca queda commiteado y el working tree salía sucio tras todo
commit con spec declarada. En vez de reconciliar el reset con el commit que lo
origina (arriesga recursión de hooks, o un antipatrón de `git add` manual), se
repensó el mecanismo: `.sdd/current-spec` es estado de sesión local (el gate
solo lee su contenido en disco; la trazabilidad real vive en
`SPECS_REGISTRY.md` + `FR-NNN` grepeado en los tests, nunca en este archivo),
así que se sacó del control de versiones (`.gitignore` en el kit y en la
plantilla del wiring; `git rm --cached`).

Eso rompía a `sdd-doctor`, que tenía el archivo en `REQUIRED` (chequeo de mera
existencia): un `git clone` fresco saldría en rojo por "artefacto faltante" —
la misma clase de contradicción que D-1/D-3/G-4 señalaron en otras
superficies. Se sacó de `REQUIRED` y se agregó `sdd_config.seed_current_spec`,
que siembra el header si falta (nunca pisa uno existente): usa
`templates/wiring/current-spec` cuando hay `templates/` (el kit) y
`CURRENT_SPEC_FALLBACK_HEADER` — mismo texto embebido, con `{{sdd.core}}`
resuelto a `tools/sdd/core` — cuando no la hay (proyecto derivado, donde
`templates/` nunca se vendoriza). Un test de paridad
(`test_fallback_header_coincide_con_la_plantilla_del_kit`) evita que las dos
copias diverjan en silencio, mismo patrón que la duplicación inevitable de
`source_roots` entre capas (G-1).

**SSOTs afectados:** ninguno nuevo; `templates/wiring/current-spec` sigue
siendo el header canónico, `sdd_config.CURRENT_SPEC_FALLBACK_HEADER` es su
copia de emergencia atada por test.

**Hallazgos de `analyze` corregidos antes de cerrar (mismo día):** FR-008
decía "reemplaza FR-002/FR-007" mientras ambos seguían `MUST` con tests
propios (ANA-01, HIGH) — reformulado a "complementa": el reset y la
preservación de comentarios siguen haciendo falta dentro de una sesión,
tenga o no versionado el archivo. `git rm --cached` no aclaraba si era un
paso automatizado o manual (ANA-02, MEDIUM) — se documentó como manual y de
una sola vez, sobre el archivo ya trackeado. SC-004 y SC-005 se pisaban
hablando los dos de `git status` (ANA-03, LOW) — SC-004 quedó acotado a la
preservación byte a byte del contenido. Una segunda pasada de `analyze`
encontró que SC-005 — "no aparece en `git status`" — no tenía ningún test
que corriera git de verdad (ANA-04, HIGH): el test unitario solo probaba
`seed_current_spec`, y el e2e existente verificaba el *contenido* del
archivo tras el reset, nunca `git status`. Se agregó la aserción
`git status --porcelain` sobre `current-spec` en
`test_escenario_2_misma_spec_en_varios_commits` (entorno con git y hooks
reales). También se cubrió que ambos `.gitignore` contuvieran de verdad la
línea (ANA-05, MEDIUM) y se completaron el *Independent Test* y *Key
Entities* de la spec, que no nombraban el alcance de FR-008 (ANA-06/ANA-07).

Una tercera pasada de `analyze` encontró el hueco más importante (ANA-08,
HIGH): FR-008 prometía que `.gitignore` ignoraba `.sdd/current-spec` "de
forma permanente y automática", pero `sdd_init.py` **conserva sin tocar**
cualquier `.gitignore` ya presente en el target vía `_copy_text` — el caso
realista, porque casi todo proyecto (brownfield, o greenfield con `git init`
que ya generó uno) tiene `.gitignore` antes de correr `sdd-init`. La línea
nunca se agregaba y FR-008 quedaba neutralizado por la vía de instalación,
sin que `sdd-doctor` lo detectara (`.gitignore` no estaba en `GATE_WIRING`,
lo único auditado por contenido). Misma familia que U-4/G-4. Se agregó
**FR-009/SC-006**: `sdd_config.ensure_gitignore_current_spec` suma la línea a
un `.gitignore` existente sin pisar el resto (mismo criterio que
`sdd_spec.py` con `.sdd/current-spec`: preservar y sumar, no reemplazar);
`_copy_text` de `sdd_init.py` la invoca en la rama "existe, se conserva"; y
`sdd_doctor.py` verifica por contenido que el `.gitignore` del proyecto la
incluya, reportando problema si falta el archivo o la línea.

Una cuarta pasada de `analyze` encontró que el fix de FR-009 solo estaba
probado llamando directo a `sdd_init._copy_text` (unidad interna), no por la
ruta real de instalación —`sdd_init.py` como subproceso, como ya hace la
suite e2e para FR-008— así que una regresión en `main()` no la detectaría
nadie (ANA-09, MEDIUM). Se agregó
`tests/e2e/escenarios/test_instalacion_brownfield_gitignore.py`, que corre
`entorno.instalar` (subproceso real) sobre un `.gitignore` propio
preexistente. De paso, dos correcciones de texto: SC-006 tenía un error de
concordancia verbal ("...dejar ese .gitignore...", ANA-10, LOW) y *Key
Entities* no mencionaba `.gitignore` pese al comportamiento que FR-009 le
agrega (ANA-11, LOW).

**Verificación:** `python core/pipeline.py` → VERDE (11/11); simulado un clon
fresco (borrando `.sdd/current-spec` del kit) y `sdd-doctor` lo sembró
correctamente con `core/sdd_gate.py` (ruta del kit) y siguió reportando
"Instalación SDD sana"; `tests/e2e/escenarios/test_ciclo_spec_first.py` → 4/4
verde con la aserción de `git status` nueva; instalación simulada a mano en
`/tmp` sobre un target con `.gitignore` propio (`node_modules/`, `*.log`):
`sdd-init` conservó ambas líneas y agregó `.sdd/current-spec`, con el aviso
"se agregó .sdd/current-spec" en el log;
`test_instalacion_brownfield_gitignore.py` → verde, ejercitando el mismo
camino vía subproceso real de `sdd_init.py`.

## 2026-08-11 — SPEC-024: el Coverage mapping verifica que el FR aparezca en el test, no solo que el archivo exista

**Scope:** `specs/SPEC-024-traza-fr-en-test.md`, `core/check_traceability.py`,
`tests/unit/test_check_traceability.py` y el backfill sobre los tests de las
specs `active`+`hibrido` vigentes que quedaban en rojo.

**Qué cambió:** una fila del *Coverage mapping* quedaba "verde" si el archivo
de test referenciado existía, sin importar si mencionaba el FR que decía
cubrir (hallazgo G-8 de `docs/IDEAS.md`). `check_traceability.py` ahora
verifica, por cada fila con al menos una ruta de test, que el ID del FR
aparezca como token completo (no substring) en el contenido de al menos uno
de los archivos referenciados. Vecinos alfanuméricos, `_` y `-` invalidan el
match — no alcanza con `\b` de `re`, porque `-` es no-`\w` y dejaría pasar
`FR-1` dentro de `FR-1-ALGO` (los IDs multi-HU del propio kit usan `-` como
separador). Un archivo no decodificable como texto cuenta como "no lo
contiene", sin abortar el check.

**Migración:** de las 217 filas medidas el 2026-08-11 sobre las 21 specs
`active`+`hibrido`, 30 fallaban. El backfill agregó el ID como comentario o
docstring de una línea en la función de test que ya ejercía ese
comportamiento; donde no existía cobertura real (SPEC-009 FR-004:
`pipeline_coverage`; SPEC-015 FR-US2-001/002/004/005: wiring de Antigravity)
se escribieron tests nuevos mínimos — la señal que SPEC-024 está diseñada
para sacar a la luz.

**Hallazgo colateral:** SPEC-009 FR-006 describía un instalador que copiaba
`ci.yml` como plantilla estática con `--force`; el mecanismo real es que
`render.py` lo genera siempre como artefacto derivado (igual que
`CONSTITUTION.md`), sin idempotencia porque no hay contenido de usuario que
proteger. FR-006 se enmendó y su Coverage mapping pasó de
`tests/unit/test_sdd_init.py` a `tests/unit/test_render.py`.

**SSOTs afectados:** ninguno nuevo; `core/check_traceability.py` sigue siendo
el único lector del *Coverage mapping* (FR-002/Key Entities de SPEC-022).

## 2026-08-11 — SPEC-023: la relación entre specs se declara al crearlas y se verifica sola

**Scope:** `specs/SPEC-023-relacion-entre-specs.md`, `core/spec_relations.py`
(nuevo), `core/check_traceability.py`, `core/sdd_spec.py`, `core/sdd_doctor.py`,
`templates/docs/SPEC-FORMAT.md`, `templates/docs/playbooks/sdd-spec.md`,
`templates/specs/SPEC-TEMPLATE.md` + `specs/SPEC-TEMPLATE.md`, las 22 specs
`hibrido` del repositorio (migración), `tests/unit/test_check_traceability.py`,
`tests/unit/test_sdd_spec.py`, `tests/unit/test_sdd_doctor_wiring.py`,
`tests/unit/test_spec_format_reference.py`, `tests/unit/test_template_paths.py`.

**Qué cambió:** la relación entre dos specs vivía en prosa, se anotaba de un solo
lado y nadie la verificaba. Ahora es una sección obligatoria con tres pares
simétricos de campos —`Extiende:`↔`Extendida por:`, `Depende de:`↔`Es dependencia
de:`, `Supersede:`↔`Superseded por:`— y tres piezas que la sostienen:

- **`sdd-spec --extends SPEC-NNN` / `--supersedes SPEC-NNN`** escriben el enlace
  en **los dos** documentos en el momento en que la información existe y es
  barata de anotar. Son repetibles y combinables; apuntar la misma spec con las
  dos aborta. La creación es atómica: todo lo que hay que verificar sobre cada
  referencia corre antes del primer byte, así que un fallo deja el árbol idéntico
  —sin spec, sin fila y sin `.sdd/current-spec` tocado—. `--rationale` aterriza
  ahora en el campo de prosa de la sección, que es donde se lo va a buscar.
- **`check_traceability.py`** exige la sección en specs `hibrido` y valida que
  las referencias existan, que cada campo directo tenga su recíproco del tipo
  correcto y que una spec `active` no se apoye en una no vigente.
- **`sdd_doctor.py --fix`** inyecta la sección ausente y cierra los recíprocos.

**Decisiones:**
- **`--supersedes` no degrada la spec vieja al crear.** La nueva nace `draft`:
  degradarla ahí dejaría la capacidad sin spec vigente y a toda `active` que se
  apoye en ella violando la restricción de estado. El cambio ocurre al cerrar la
  iteración. Por eso mismo se aborta si alguna `active` cuelga de la referenciada.
- **`Supersede:` queda fuera de la restricción de estado.** Apuntar a una
  `superseded` es el desenlace normal de reemplazarla, no una violación. El
  primer caso real es SPEC-017 → SPEC-006, que se declaró en esta migración.
- **Quien escribe no es el validador.** Un gate que modifica lo que valida deja
  de ser gate: la lectura de la sección vive en `check_traceability.py` —un solo
  parseador, o el validador rechazaría lo que el creador escribe— y la escritura
  en `core/spec_relations.py`, que consumen `sdd_spec` y `sdd_doctor`.
- **La reparación es repetible, no una migración de una vez.** La misma operación
  cierra el recíproco de un `Depende de:` escrito a mano hoy o dentro de un año, e
  inyecta la sección en una spec `hibrido` creada a mano después; la migración
  inicial fue su primera corrida.
- **No hay `--depends`.** `--extends`/`--supersedes` resuelven el triage de
  SPEC-022 y se saben al crear; la dependencia se descubre escribiendo los FR,
  cuando `sdd_spec.py` ya terminó. Una bandera que casi siempre llegaría vacía no
  evitaría el olvido del recíproco: lo que sí lo evita es poder cerrarlo después.
- **Las specs `casero` quedan fuera.** `SPEC-000-naming.md` la genera
  `core/render.py`: agregarle la sección a mano reaparecería como drift.
- Declarar `--extends`/`--supersedes` **resuelve el triage** igual que `--new`:
  deja el solape escrito en los dos documentos, que es más de lo que el triage
  pide.

**Migración:** las 22 specs `hibrido` recibieron la sección y se cerraron los
recíprocos preexistentes que SPEC-022 dejó abiertos (SPEC-001 y SPEC-017 reciben
`Es dependencia de:`). Sin ese paso la reciprocidad habría nacido fallando sobre
specs `active` que nadie tocó.

**Deuda declarada:** el vocabulario se queda en tres relaciones; "conflicto con"
o "duplica parcialmente" se agregan cuando aparezca el caso, no antes.

**SSOTs afectados:** `templates/docs/SPEC-FORMAT.md` (gramática de la sección
**y** criterio de cuándo usar cada campo, en un único documento),
`templates/docs/playbooks/sdd-spec.md` (cuándo usar cada bandera y cuándo pasa a
`superseded` la spec reemplazada), `specs/SPECS_REGISTRY.md`.

## 2026-08-10 — SPEC-022: antes de crear una spec, reusar la que ya cubre la capacidad

**Scope:** `specs/SPEC-022-reusar-specs-existentes.md`, `core/spec_index.py`
(nuevo), `core/sdd_spec.py`, `core/sdd_gate.py`, `core/check_traceability.py`,
`core/sdd_config.py`, `.sdd/config.yaml`, `examples/config/config.yaml`,
`templates/docs/playbooks/sdd-spec.md`, `AGENTS.md`,
`tests/unit/test_spec_index.py` y `tests/unit/test_sdd_spec_reuse.py` (nuevos),
`tests/unit/test_sdd_spec.py`, `tests/unit/test_sdd_gate.py`,
`tests/unit/test_sdd_config.py`, `tests/unit/test_check_traceability.py`,
`tests/unit/test_example_config.py`, `tests/unit/test_template_paths.py`.

**Qué cambió:** el kit sólo sabía *crear* specs. Reusar una vigente exigía
editar `.sdd/current-spec` a mano, así que en la práctica se creaba una spec
nueva siempre y las capacidades quedaban repartidas en documentos que se pisan.
Ahora hay tres piezas:

- **`sdd-spec --reuse SPEC-NNN --fr FR-NNN`** declara una spec existente sin
  crear archivo ni fila, y sólo si ese requisito ya está escrito en ella:
  adoptar no puede abrir el gate con menos evidencia que crear. Sobre una spec
  `active` exige además la fila de *Coverage mapping*, porque sin ella
  `check_traceability` —que corre en el pre-commit con `always_run`— quedaría
  rojo y bloquearía hasta el commit del test.
- **Triage de solape** (`core/spec_index.py`): antes de crear, se listan las
  specs vigentes que podrían cubrir ya la capacidad, por título o porque ya
  gobiernan los archivos a tocar. Al haberlas, aborta sin escribir nada y exige
  resolver el solape con `--reuse` o dejarlo escrito con `--new --rationale`.
- **Aviso de reuso en el gate**: cuando bloquea por falta de spec declarada, el
  motivo nombra las specs que ya gobiernan ese archivo. Es el punto donde la
  señal es más dura, porque el archivo concreto ya se conoce.

**Decisiones:**
- El índice se deriva de tres fuentes que ya viven en el repositorio (rutas de
  *Key Entities*, tests del *Coverage mapping*, citas `SPEC-NNN` en el código),
  se computa en memoria y no se persiste: un artefacto generado más es un
  artefacto que puede quedar desincronizado.
- Nada de similitud semántica: sobre specs que comparten todo el vocabulario del
  dominio, la léxica rankea ruido, y los embeddings romperían el agnosticismo y
  el trabajo offline. Las citas ya escritas son señal dura y determinista.
- El índice conserva las rutas que una spec `draft` todavía no creó. Son
  precisamente las que el gate bloquea primero, y descartarlas dejaba ciego al
  aviso en su caso más frecuente.
- `specs.triage` vive en el config con defaults **neutros** en el loader: el
  vocabulario del dominio lo siembra cada proyecto, el kit incluido. Hardcodear
  `spec`/`sdd` en `core/` es justo la lista que el Principio I manda al config.

**Hallazgo de paso:** `_TEST_REF` de `check_traceability` no estaba anclada y de
`src/tests/test_x.py` extraía `tests/test_x.py`, así que la verificación de
existencia buscaba donde no era. Rompía justo en el layout con los tests dentro
de las carpetas de código, el que FR-US1-004 contempla.

**Deuda declarada:** el triage por título deducido del stem no hace stemming, así
que `existentes` no alcanza a `existente`; se compensa con `--touches`. La
relación entre specs (`--extends`, `--supersedes`) es SPEC-023, todavía `draft`:
`--new --rationale` acepta y exige el texto, pero quien lo escribe en la sección
de relaciones es esa spec.

**SSOTs afectados:** `templates/docs/playbooks/sdd-spec.md` (procedimiento),
`AGENTS.md` (paso 4, referencia sin duplicar), `.sdd/config.yaml` y
`examples/config/config.yaml` (parámetros del triage).

## 2026-08-09 — Soporte para Antigravity CLI unificado (Iteración 7)

**Scope:** `specs/SPEC-015-wiring-apunta-al-codigo-real.md` (ampliada con User Story 2),
`templates/wiring/sdd_gate_hook.sh`, `.claude/sdd_gate_hook.sh`,
`templates/wiring/hooks.json` (nuevo), `.agents/hooks.json` (wiring),
`core/sdd_gate.py`, `core/sdd_init.py`, `core/sdd_config.py`,
`tests/unit/test_sdd_gate_hook.py`, `tests/unit/test_sdd_gate.py`.

**Qué cambió:** Se agregó soporte completo para Antigravity CLI al gate, procesando su formato de payload (`toolCall.args.TargetFile`) y emitiendo JSON por `stdout`. El wiring de Antigravity (`hooks.json`) ahora se instala en los repositorios derivados de forma análoga a `.claude/settings.json`, y el doctor verifica su existencia. Los scripts de pre-filtro shell se unificaron para ambos asistentes (eliminando dependencias de herramientas externas como `tr` y arreglando el mensaje de `fail-closed` para que expanda correctamente la ruta del script del gate a reportar). Se expandió `SPEC-015` para declarar este soporte, cubriendo Antigravity bajo la misma iteración del "wiring".

## 2026-08-09 — K-4: la suite e2e entra al pipeline

**Scope:** `specs/SPEC-018-verificacion-e2e.md` (reabierta, iteración 5),
`specs/SPEC-019-tests-integracion-ejecutados.md` (nota de reversión),
`core/sdd_config.py`, `core/sdd_init.py`, `adapters/python/adapter.py`,
`adapters/CONTRACT.md`, `.sdd/config.yaml`, `examples/config/config.yaml`,
`.github/workflows/e2e.yml`, `tests/unit/test_adapter_e2e.py` (nuevo),
`tests/unit/test_e2e_aislamiento.py`, `tests/unit/test_sdd_init_seeded_config.py`,
`tests/unit/test_sdd_doctor_tests_huerfanos.py`.

**Qué cambió:** el adaptador expone un paso `e2e` que corre `dirs.tests_e2e`, el
kit declara la clave y el paso (último), y `sdd-init` los siembra cuando detecta
la carpeta en el destino. El pipeline pasa de 10 a 11 pasos.

**Se revirtió una decisión, no se la esquivó.** SPEC-018 US2 prohibía justamente
esto (FR-US2-003, SC-003). Abrir una spec nueva habría dejado dos SSOTs
contradictorios sobre el mismo archivo, así que va como enmienda de la spec dueña,
con la revisión escrita en sus Clarifications y las dos mitades del argumento
original marcadas como falsas en el propio FR:

- **El costo nunca se había medido.** Medido: e2e 16,6 s, pipeline entero 17,2 s,
  `coverage` 9,2 s, `tests` 7,3 s. La e2e es 1,8× el paso más caro que ya existía,
  no un orden de magnitud. El ciclo pasa de ~17 s a ~36 s.
- **"Cableada al ciclo de cada commit" era falso.** En cada commit corren los
  hooks; el pipeline corre al cerrar iteración — que es exactamente cuando se
  quiere saber si el producto instalado todavía funciona.

**Sin flag.** Un disparador opcional reproduce el modo de falla que US2 temía
("se termina salteando") con otro nombre, y le devuelve al kit un VERDE que no
miró su nivel de test primario. Último por costo, no por importancia.

**Lo que US2 sí describía bien** era el acople: declarar la carpeta la arrastraba
a la corrida de `coverage`. Se cerró antes, en C-8: `TEST_DIRS` declara si la
carpeta entra a la medición, y `tests_e2e` no entra —no por preferencia, sino
porque los escenarios manejan el kit por subproceso y no aportan una sola línea
medida en proceso—. Verificado: el paso `coverage` no menciona `tests/e2e`, y
romper un escenario pinta el paso `e2e` en rojo (exit 1).

**Salió gratis:** el paso "Lint de la suite" escrito a mano en `e2e.yml`
desaparece; con la carpeta en `dirs`, la cubren `naming`/`lint`/`format` desde el
config.

**Hallazgo, registrado y no arreglado de contrabando (V-4):** al sacar ese paso
apareció que la raíz de `tests/` no la mira ningún paso — las claves apuntan a
subcarpetas, así que `tests/conftest.py` **nunca estuvo lintado** y
`tests/fixtures_proyecto.py` solo lo salvaba ese paso a mano. Queda un lint
acotado en el workflow y la idea abierta en `docs/IDEAS.md`: el fix pide decidir
entre una clave `tests_root` o derivar la raíz común, y eso es otra iteración.

**Verificación:** pipeline VERDE 11/11 (36 s), 454 unitarios + 17 e2e,
`sdd-doctor` sano.

```
[SDD-Check]
- Specs leídas: SPEC-018-verificacion-e2e, SPEC-019, SPEC-005
- SSOTs afectados: SPEC-018 (US2 enmendada, US3 nueva), .sdd/config.yaml, adapters/CONTRACT.md
- Verificación: python core/pipeline.py → VERDE (11/11); 454 unitarios; e2e 17; sdd-doctor sano
```

## 2026-08-09 — C-8: un solo SSOT para los vocabularios del kit

**Scope:** `specs/SPEC-005-desduplicar-ssot.md` (reabierta, iteración 2),
`core/sdd_config.py`, `core/pipeline.py`, `core/render.py`, `core/sdd_doctor.py`,
`adapters/python/adapter.py`, `adapters/python/check_naming.py`,
`adapters/CONTRACT.md`, `tests/unit/test_vocabulario_de_pasos.py` (nuevo),
`tests/unit/test_sdd_doctor_tests_huerfanos.py`,
`tests/unit/test_adapter_integration.py`.

**Qué cambió:** los dos vocabularios que el kit tenía escritos dos veces pasan a
tener un SSOT en `core/sdd_config.py`. `CODE_STEPS` (qué pasos reserva el
contrato) lo importa `core/pipeline.py`; `TEST_DIRS` (qué carpetas de tests
existen y qué paso ejecuta cada una) reemplaza a `TEST_DIR_STEP` y a las cuatro
tuplas `("tests_unit", "tests_integration")` sueltas.

**Por qué ahora:** es prerequisito de K-4. Sin separar "carpeta que los pasos
estáticos miran" de "carpeta que un paso ejecuta", declarar `tests/e2e` en el
config la arrastraba a la corrida de `coverage` — el acople exacto que SPEC-018
US2 nombra como razón para dejar la e2e afuera.

**Decisiones:**

- **`CODE_STEPS` es del núcleo, no del lenguaje.** La idea original suponía lo
  contrario ("no es un simple merge") y por eso quedó trabada. Lo que reserva los
  nombres es el contrato (`adapters/CONTRACT.md`); el lenguaje aporta la
  *implementación* de cada paso.
- **No se le pregunta al adaptador qué soporta.** Gasta un subproceso por corrida
  y, peor, haría que un nombre mal escrito en `pipeline.steps` fuera válido o no
  según el adaptador instalado.
- **El cruce es bidireccional.** La dirección que ya falló (implementado y no
  declarado → "paso desconocido" descontado del total en silencio) y la inversa
  (declarado y no implementado → fallo confuso en vez de la omisión que el
  contrato promete). Verificado por mutación: romper cada lado pinta la suite.

**Lo que la duplicación tapaba:** los cuatro módulos que repetían la tupla no
hacían la misma pregunta. El adaptador la usaba para dos cosas distintas —blancos
estáticos de `naming`/`lint`/`format` vs carpetas que `coverage` le pasa a pytest
para ejecutar—, `check_naming` para relajar reglas, `render` para los `paths:` de
CI y `sdd_doctor` para cruzar contra `pipeline.steps`. Una lista plana obligaba a
que toda carpeta respondiera igual a las cinco: por eso agregar una clase de test
nueva no era un renglón sino una revisión de cuatro criterios.

**Se borró un test:** `test_el_pipeline_reconoce_todos_los_pasos_del_adaptador`
era el parche de C-8 ("las dos listas viven separadas, así que se cruzan acá").
Con un SSOT único, mantenerlo sería la duplicación que la spec vino a cerrar.

**Hallazgo lateral:** la función se llamaba `test_dir_keys` y pytest la
recolectaba como test al importarla. Renombrada a `declared_test_dirs`.

**Verificación:** pipeline VERDE 10/10, 440 unitarios + 1 skip.

```
[SDD-Check]
- Specs leídas: SPEC-005-desduplicar-ssot, SPEC-019, SPEC-018
- SSOTs afectados: core/sdd_config.py (CODE_STEPS, TEST_DIRS), adapters/CONTRACT.md
- Verificación: python core/pipeline.py → VERDE (10/10); 440 unitarios; sdd-doctor sano
```

## 2026-08-09 — K-2: el catálogo de claves del config viaja con la instalación

**Scope:** `specs/SPEC-013-proyecto-derivado-coherente.md` (reabierta, iteración
6), `core/sdd_init.py`, `templates/00-INDEX.md`,
`tests/unit/test_catalogo_config_viaja.py` (nuevo),
`tests/unit/test_derived_references.py`.

**Qué cambió:** `sdd-init` instala el catálogo de claves —`examples/config/
config.yaml`, verbatim— como `.sdd/config.reference.yaml` del destino, y la
cabecera sembrada remite ahí en vez de a "el kit, en `examples/config/
config.yaml`". Era una referencia colgada en el archivo que el dueño más edita,
que solo se sostenía asumiendo que siempre hay un clon del kit a mano.

**Por qué ahora:** la premisa cambió. El README declara que el kit es desechable
(K-6), así que todo lo que el derivado necesite tiene que viajar con la
instalación. Un catálogo que solo existe en el repo del kit es un hueco.

**Decisiones:**

- **El YAML verbatim, no un `docs/CONFIG-REFERENCE.md`.** El catálogo *es* ese
  archivo: su valor está en los comentarios junto a cada clave. Reexplicarlas en
  prosa sería una segunda descripción del mismo tema, divergente por construcción
  (Principio IV). Copiar el archivo del kit al derivado no duplica un SSOT dentro
  de un repo: es la misma vendorización que ya hace `tools/sdd/`.
- **`config.reference.yaml`, no `config.example.yaml`.** "Example" invita a
  copiarlo, que es la instrucción absurda que SPEC-014 FR-US2-004 sacó de la
  cabecera sembrada.
- **Se reescribe en cada instalación.** El config es del dueño y se conserva; el
  catálogo es artefacto del kit. Uno viejo, describiendo claves de otra versión
  del andamiaje, es peor que no tenerlo.

**El test que no veía nada:** `test_derived_references.py` auditaba rutas colgadas
solo sobre los `.md` instalados. Por eso FR-004 estaba verde con esta referencia
rota desde siempre. Ahora la auditoría alcanza también a `.sdd/config.yaml`
(FR-009). Límite conocido, heredado: solo se auditan rutas en backticks — la
convención del kit para "ruta que el lector puede seguir".

**Verificación:** pipeline VERDE 10/10, 434 unitarios + 17 e2e.

**[SDD-Check]** SPEC-013 · FR-008, FR-009, FR-010 · SC-007 · pipeline VERDE 10/10

## 2026-08-09 — K-5: el paso `coverage` sembrado deja de nacer inerte

**Scope:** `specs/SPEC-009-coverage-y-ci.md` (reabierta con US2, iteración 6),
`core/sdd_coverage_baseline.py` (nuevo), `adapters/python/adapter.py`,
`core/sdd_config.py`, `core/sdd_doctor.py`, `adapters/CONTRACT.md`,
`examples/config/config.yaml`, `templates/docs/playbooks/sdd-configure.md`, y
cuatro archivos de test.

**El problema:** `sdd-init` siembra `coverage` en `pipeline.steps` pero no puede
sembrar un umbral —no sabe cuánto cubre un proyecto que todavía no existe—, así
que el paso se omite con aviso en **cada** corrida. En el kit fue una elección
deliberada mientras no hubo suite; en un proyecto real es deuda que nadie paga,
porque nadie sabe qué número poner. Un paso que nunca verifica nada enseña que el
VERDE es ruido: la familia de U-3 y C-1.

**La solución:** el kit sí sabe medirlo. `core/sdd_coverage_baseline.py` mide el
piso real y lo escribe como trinquete. Reparto de responsabilidades: la medición
es del adaptador (consulta `coverage-baseline`, contrato en
`adapters/CONTRACT.md`), porque medir cobertura es específico del ecosistema; el
núcleo orquesta y aplica la política.

**Decisiones:**

- **No lo mide `sdd-init`.** Medir es correr la suite del proyecto destino:
  arbitrariamente lenta, con efectos posibles, y sobre un brownfield que el
  instalador acaba de tocar. Un instalador que ejecuta los tests ajenos sin
  pedirlo es una sorpresa cara. Va como comando, que el playbook de
  `sdd-configure` ofrece y el catálogo del config nombra.
- **No pisa un umbral ya declarado.** Informa medido vs declarado y avisa si el
  declarado quedó **por debajo** del piso real —el trinquete dejó de morder, que
  es exactamente el defecto que K-3 encontró en el propio kit: umbral 50 con
  cobertura 75—. Subir un umbral es decisión de política, no algo que una corrida
  afortunada haga a espaldas de quien lo declaró.
- **Redondeo hacia abajo.** Un piso con decimales que no se puede volver a
  alcanzar no es un trinquete.
- **Escritura por líneas, no volcado de YAML.** El config es un documento que su
  dueño edita a mano; un dumper le borraría todos los comentarios.
- **`sdd-doctor` lo informa como nota, no como problema.** Un proyecto recién
  instalado sin suite todavía es sano; un doctor que sale 1 sobre una instalación
  fresca reintroduce el falso negativo que SPEC-014 cerró del otro lado.
- **La consulta no es un paso.** Produce un dato, no valida, así que va en un
  dispatcher `QUERIES` aparte y **no** en `STEPS` ni en `pipeline.CODE_STEPS`.
  Meterla ahí habría repetido C-8: dos listas de pasos que divergen en silencio.
  Hay un test que fija ese límite.

**Verificación:** pipeline VERDE 10/10, 434 unitarios + 17 e2e, cobertura del kit
92% (umbral 90, Principio V). La integración real —el núcleo invocando al
adaptador por subproceso y parseando su línea— se ejercitó corriendo la
herramienta sobre el propio kit, que tomó la rama de "ya declarado".

**Deuda:** sin escenario e2e propio. El testigo de instalación no tiene suite,
así que la consulta se omitiría; cubrirlo pide un testigo con tests, que es
trabajo de la infraestructura e2e (SPEC-018), no de esta spec.

**[SDD-Check]** SPEC-009 · FR-US2-001..007 · SC-005, SC-006 · pipeline VERDE 10/10

## 2026-08-09 — K-1: el derivado nace vigilando el drift de lo generado

**Scope:** `specs/SPEC-014-derivado-dice-la-verdad.md` (reabierta, iteración 6),
`core/sdd_init.py`, `tests/unit/test_sdd_init_seeded_steps.py`.

**Qué cambió:** `_SEEDED_STEPS` siembra el paso `render`, entre `skills` y
`tests`. Es una línea, pero cierra un falso verde estructural del derivado: nada
comparaba los artefactos generados contra el config. `check_constitution.py`
parsea el **documento** y valida que sus referencias y su enforcement estén
cableados, pero nunca lo contrasta con `principles:`, así que el paso
`constitution` salía OK sobre una constitución obsoleta. El único que veía el
drift era `sdd-doctor`, que se corre a mano.

**Los tres daños que pasaban en silencio:** (a) el agente lee
`specs/SPEC-000-naming.md` (paso 5 de `AGENTS.md`) mientras `check_naming.py`
enforcea desde el config — divergen y el asistente sigue reglas que el linter ya
no aplica; (b) la constitución queda congelada en el primer valor; (c) el
`ci.yml` se genera desde `pipeline.steps` y `default_branch`, así que habilitar un
paso dejaba **verde local ≠ verde en CI**, silencioso y cross-máquina.

**Por qué en SPEC-014 y no en una spec nueva:** es la HU-1 textual de esa spec
—*ningún reporte de salud sin medición*—, la misma clase que G-4 (`sdd-doctor`
validando existencia y no contenido del wiring). Abrir spec propia habría
fragmentado el invariante.

**Por qué sembrado y no opcional:** el criterio de `_OPTIONAL_STEPS` es "requiere
tooling del proyecto" (`lint`, `format`, `types`, `security`). `render --check` es
lectura pura sobre el config y los artefactos. Y no agrega precondición: el paso
`constitution`, ya sembrado, exige que `CONSTITUTION.md` exista, y eso lo produce
`render` — el paso 2 del flujo que imprime el propio instalador, antes del paso 3
(`pipeline.py`).

**Descartado:** hacer que `check_constitution.py` compare contra `principles:`.
Sería una segunda implementación del criterio que `render --check` ya tiene,
divergente por construcción (Principio IV). El paso existía; lo que faltaba era
sembrarlo.

**Verificación:** pipeline VERDE 10/10, 397 unitarios + 17 e2e en verde.

**[SDD-Check]** SPEC-014 · FR-US1-005 · SC-008 · pipeline VERDE 10/10

## 2026-08-08 — K-3 cerrado: Principio V y cobertura al 90% (con SPEC-021 de yapa)

**Scope:** `.sdd/config.yaml` (Principio V, `constitution.version` 0.3.0 → 0.4.0,
umbral 80 → 90), `CONSTITUTION.md` (regenerado), `core/sdd_config.py`,
`specs/SPEC-021-config-vacio-no-rompe.md` (nueva), y tests de `sdd_spec`,
`check_naming`, el adaptador python y `bootstrap_hooks`.

**Qué cambió:** se declaró el **Principio V** — el kit no tiene código de
producto, todo lo que contiene es código de palanca que corre dentro de proyectos
ajenos, así que su cobertura se mantiene por encima del piso que le pide a un
derivado y el umbral **solo sube**. Enforcement `pytest-cov` / paso `coverage`,
detalle `.sdd/config.yaml`. Es la primera vez que se usa el mecanismo de SPEC-020:
se verificó sacando `coverage` de `pipeline.steps` y confirmando que la
constitución sale ROJO nombrando el principio. Con el mapa hardcodeado de antes,
ese principio habría pasado en silencio.

Enmienda de constitución, no cambio de código: la versión sube a **0.4.0** (MINOR
pre-1.0 = agrega un principio) y `amended` a 2026-08-08.

**Cobertura:** 81% → **91%**, umbral 80 → 90.

| Módulo | Antes | Ahora |
|--------|-------|-------|
| `core/sdd_spec.py` | 44% | 96% |
| `adapters/python/check_naming.py` | 59% | 99% |
| `adapters/python/adapter.py` | 51% | 98% |
| `core/bootstrap_hooks.py` | 59% | 97% |

**El patrón que explicaba la deuda:** la suite cubría helpers y **nunca los
`main()`**. Todos los bloques sin ejecutar eran entrypoints — justo lo que corre
en la línea de comandos de un proyecto instalado. En el adaptador la asimetría
era más fina: estaban cubiertas las omisiones (la mitad interesante de SPEC-003)
y casi ninguna rama donde el paso sí ejecuta la tool.

**Lo que destapó (SPEC-021):** cubrir `check_naming.main()` reventó con
`TypeError: 'NoneType' object is not iterable`. Un `naming.prohibited:` sin ítems
—YAML lo carga como `None`, y vaciar la lista es la forma natural de desactivar
la regla sin borrar la clave— abortaba el paso `naming` con un traceback,
tapando el mensaje "sin palabras excluidas (nada que verificar)" que el propio
consumidor ya tenía escrito. Eran las tres propiedades de `naming`, las únicas
del loader que iteraban un `.get(clave, [])` sin verificar el tipo; el resto ya
guardaba. La regla estaba declarada desde antes en el docstring de
`pipeline_coverage` ("un typo no debe volver ilegible el proyecto"): esta spec la
extiende a las claves que se la saltaban, con la guarda en un helper único para
que una lista nueva la herede.

Confirma la hipótesis con la que se encaró K-3: cubrir un módulo nunca ejecutado
destapa defectos, no solo sube un número.

**Estado:** pipeline 10/10 VERDE, 394 tests + 1 skip, doctor sano.

## 2026-08-08 — SPEC-020: el enforcement de un principio lo declara el config

**Scope:** `core/sdd_config.py` (`Principle.step`, `enforcement_steps`),
`core/check_constitution.py` (se elimina `ENFORCEMENT_STEP`), `.sdd/config.yaml`,
`examples/config/config.yaml`, `tests/unit/test_check_constitution.py` (nuevo),
`tests/unit/test_sdd_config.py`, `tests/unit/test_example_config.py`.

**Qué cambió:** el mapa tool→paso que usaba el Constitution Check para verificar
que el enforcement de un principio esté cableado era un `dict` hardcodeado con
cuatro entradas en `core/check_constitution.py`. Ahora cada principio declara su
`step` en `.sdd/config.yaml` y el check resuelve contra `cfg.enforcement_steps`.
El núcleo dejó de nombrar tools. Un principio propio (`enforcement: mi_check.py`
+ `step: mi-paso`) obtiene exactamente la misma verificación que los del kit.

**Cómo apareció:** yendo a declarar el principio de cobertura de K-3 (el kit se
exige más que lo que reparte). Al escribirlo se vio que no obtendría
verificación: `ENFORCEMENT_STEP.get(name)` devuelve `None` para cualquier tool
fuera del mapa y el check **pasa en silencio**. Habría sido un enforcement
decorativo en la constitución del propio kit — el fallo que el kit existe para
evitar. Estaba registrado como E-4 en `docs/IDEAS.md` desde la primera revisión
crítica; lo que cambió es que dejó de ser deuda abstracta y pasó a ser
prerrequisito.

**Decisión de diseño:** `step` va **dentro de cada principio**, no como un mapa
de nivel superior. Un mapa aparte partiría en dos lugares la descripción de un
mismo principio y sería duplicación de SSOT dentro del config: el principio es la
unidad. Un principio **sin** `step` no verifica cableado y no es error — es cómo
se declara un enforcement que el pipeline no activa: el gate (Principio III) va
por hooks y lo verifica `sdd-doctor`, el SSOT único (Principio IV) es convención
de `AGENTS.md`. Esa distinción vivía en un comentario de código; ahora es
explícita en el config. Fuera de alcance: renderizar el paso en
`CONSTITUTION.md` (la línea `Enforcement:` se parsea con `_BACKTICK.findall`, así
que un segundo token se leería como otro enforcement).

**Cobertura (K-3):** `check_constitution.py` pasó de **0% a 99%** — 96 stmts que
nunca se habían ejecutado, en un módulo que corre en el paso `constitution` de
*todo* proyecto instalado. Total del kit: 75% → **81%**, y el umbral de
`pipeline.coverage` subió de 50 (25 puntos por debajo del piso real: no protegía
nada) a **80**. Objetivo declarado 90%; falta cubrir `sdd_spec` (44%), el
adaptador python (51%) y `check_naming` (59%).

**Estado:** pipeline 10/10 VERDE, 352 tests + 1 skip. `CONSTITUTION.md` no
cambió: `step` no se renderiza, así que la enmienda no fue tal y la versión de la
constitución sigue en 0.3.0.

## 2026-08-08 — SPEC-003 (FR-010/FR-011): el paso `layers` nunca se había ejecutado

**Scope:** `adapters/python/gen_import_linter.py`, `adapters/python/adapter.py`
(`step_layers`), `tests/unit/test_gen_import_linter.py` (nuevo),
`tests/unit/test_python_adapter.py`, `specs/SPEC-003-install-happy-path.md`
(reapertura, iteración 4).

**Qué cambió:** dos defectos encadenados que dejaban ROJO el primer pipeline de
todo proyecto derivado con `import-linter` instalado.

1. `gen_import_linter.py` emitía `[[importlinter:contract]]` —sintaxis TOML de
   array-of-tables— dentro de un `.importlinter`, que import-linter lee como INI
   con `configparser`. `lint-imports` abortaba con `section '' already exists`.
   Ahora emite `[importlinter:contract:<capa>]`, una sección por capa, que es lo
   que el lector real consume.
2. Con el archivo ya legible, la instalación fresca **seguía** ROJO:
   `lint-imports` importa el paquete raíz para construir el grafo y en greenfield
   no existe (`Could not find package 'src'`). `step_layers` era el único paso de
   código sin la guardia de targets de FR-001 — `naming`, `lint`, `format` y
   `types` ya omitían con exit 3 en ese caso. Ahora también omite, y además
   cuando el config no declara `layers`.

**Cómo aparecieron:** corriendo la suite e2e de SPEC-018 con `.venv/bin` en el
PATH. Hasta ese momento `lint-imports` no estaba en el PATH de quien corría, así
que el paso se omitía y los 17 escenarios pasaban en verde.

**Por qué nadie los vio antes:** por dos ausencias que se tapaban entre sí. La
única cobertura del generador era su propio `--check`, que compara el archivo
contra lo que el generador produce —coincide siempre, sea válido o no—; y el kit
no declara `layers` en sus `pipeline.steps`, así que su propio pipeline nunca
ejecutó `lint-imports`. De ahí la regla nueva (FR-010), que es la lección
generalizable: **lo que un adaptador genera para una tool externa se verifica con
el parser de esa tool**, no con una comparación contra el generador.

**Decisiones:** el destino sigue siendo `.importlinter` y no el `pyproject.toml`
del adoptante (es suyo, el kit no lo toca). El test end-to-end nuevo corre
`lint-imports` de verdad sobre un paquete de tres capas: es el único lugar donde
el archivo generado se somete al ejecutable, porque tras FR-011 los escenarios
e2e greenfield omiten el paso por diseño. Verificado además que una violación
real de capas rompe el contrato (no es un verde vacío).

```
[SDD-Check]
- Specs leídas: SPEC-003-install-happy-path, SPEC-013, SPEC-018, SPEC-000-naming
- Includes/excludes verificados: adapters/python + tests/unit; el kit no cablea `layers` (sin cambio)
- SSOTs afectados: specs/SPEC-003-install-happy-path.md, specs/SPECS_REGISTRY.md
- Verificación: python core/pipeline.py → VERDE (10/10); pytest tests/e2e → 17 passed con lint-imports en PATH
```

## 2026-08-08 — SPEC-018 (FR-US1-006/007, FR-US2-007/008/009): la suite e2e se verifica a sí misma

**Scope:** `tests/e2e/lib/entorno.py`, `tests/e2e/README.md`,
`tests/unit/test_e2e_entorno.py`, `tests/unit/test_e2e_aislamiento.py`,
`.github/workflows/e2e.yml`, `tests/unit/test_sdd_gate_hook.py`,
`specs/SPEC-018-verificacion-e2e.md` (sesión de clarify).

**Qué cambió:**
- El workspace efímero solo se borra si no existe, está vacío o lleva la marca
  `.sdd-e2e-workspace` que siembra la propia suite. Un `SDD_E2E_WORK` mal tipeado
  ya no puede borrar una carpeta ajena: aborta sin tocar nada.
- Guardias estructurales (AST) sobre `tests/e2e/escenarios/`: cada escenario
  afirma contenido y no solo códigos de salida, su docstring nombra el defecto
  que lo originó, y todos parten de un fixture del harness en vez de armarse su
  propio entorno.
- El workflow e2e fija la matriz Linux+Windows y verifica al terminar que
  `git status --porcelain` esté vacío.
- `test_sdd_gate_hook.py`: los tests fail-closed dejan de depender del `.venv`
  del clon (pasaban en CI y fallaban en la máquina de quien desarrolla, que es
  al revés de lo útil).

**Decisiones:** `tests/e2e/` es infraestructura compartida del kit, no propiedad
de SPEC-018: otra spec puede agregar su escenario, pero no su propio entorno.

```
[SDD-Check]
- Specs leídas: SPEC-018-verificacion-e2e, SPEC-012, SPEC-019, SPEC-004, SPEC-015
- Includes/excludes verificados: tests/e2e + tests/unit + workflow e2e; core/ y adapters/ sin tocar
- SSOTs afectados: specs/SPEC-018-verificacion-e2e.md
- Verificación: python core/pipeline.py → VERDE (10/10); pytest tests/e2e → 17 passed
```

## 2026-08-07 — SPEC-013 (FR-007): forzar la lectura del playbook en Codex/Antigravity

**Scope:** `specs/SPEC-013-proyecto-derivado-coherente.md` (iteración 4),
`.agents/skills/sdd-configure/SKILL.md` (SSOT del wrapper), adaptadores
regenerados (`.claude/skills/sdd-configure/SKILL.md`,
`.opencode/command/sdd-configure.md`), `specs/SPECS_REGISTRY.md`.

**Qué cambió:** el wrapper que leen Codex y Antigravity directo (sin pasar por
`gen_skill_adapters.py`) pasó de mencionar el playbook de forma pasiva ("Leé y
seguí el playbook...") a exigir explícitamente abrirlo y leerlo completo antes
de preguntar nada, sin resumir de memoria.

**Por qué:** probado en la práctica con Claude Code y Antigravity corriendo el
mismo `sdd-configure` (FR-006, iteración anterior): Claude Code mostró el
preámbulo explicativo nuevo, Antigravity no — pese a que ambos leen exactamente
el mismo `docs/playbooks/sdd-configure.md`, sin drift. La causa no era el
contenido sino el comportamiento del asistente: Claude Code fuerza la carga
del archivo referenciado por su mecanismo nativo de skills; Antigravity no
tiene garantía equivalente y puede correr la skill sin abrir el playbook. Es
lo único accionable desde el contenido del kit — no hay forma de replicar
desde acá el mecanismo de carga forzada de Claude Code.

**Decisiones:** se reforzó el wrapper en vez de duplicar el contenido del
playbook ahí (rompería el SSOT). No hay garantía de que todo asistente
obedezca una instrucción más imperativa, pero es la palanca disponible.
Pipeline VERDE 10/10, 310 tests + 1 skip.

## 2026-08-07 — SPEC-013 (FR-006): preámbulo explicativo en el wizard de sdd-configure

**Scope:** `specs/SPEC-013-proyecto-derivado-coherente.md` (reabierta, iteración 3),
`templates/docs/playbooks/sdd-configure.md` (SSOT), `docs/playbooks/sdd-configure.md`
(sincronizado vía `render.py`), `specs/SPECS_REGISTRY.md`.

**Qué cambió:** cada pregunta del wizard de `sdd-configure` (nombre/dominio,
lenguaje, `naming.prohibited`, `principles`, `layers`, `dirs`, `pipeline.steps`)
ahora tiene, antes de preguntarse, una explicación en lenguaje simple de qué es
ese campo, para qué sirve y qué efecto concreto tiene responderlo.

**Por qué:** quien corre `sdd-configure` puede estar arrancando el proyecto y no
conocer el vocabulario de SDD — no hay razón para asumir que sabe qué es una
"palabra excluida" o un "principio opcional" antes de que se le pregunte por
ellos. Mismo problema de fondo que motivó SPEC-013 (comprensión real, no
heredada en silencio), aplicado al propio wizard.

**Decisiones:** se reabrió SPEC-013 en vez de crear una spec nueva — mismo tema,
mismo archivo que ya tocaba FR-005. Solo cambió texto del playbook, sin lógica
nueva. Pipeline VERDE 10/10, 310 tests + 1 skip.

## 2026-08-07 — SPEC-019 + enmiendas a SPEC-014/017: cerrar lo que encontró la suite e2e

**Scope:** `specs/SPEC-019-...` (nueva), `specs/SPEC-014-...` (FR-US2-006, SC-007),
`specs/SPEC-017-...` (FR-US3-007), `adapters/CONTRACT.md`,
`adapters/python/adapter.py`, `core/pipeline.py`, `core/sdd_config.py`,
`core/sdd_doctor.py`, `core/sdd_init.py`, `core/render.py`, `AGENTS.md` y
`templates/` (AGENTS, README, wiring), `.pre-commit-config.yaml`,
`examples/config/config.yaml`, tests unitarios y e2e, `docs/IDEAS.md`.

**Qué cambió:** los tres hallazgos de la primera corrida de la suite e2e (V-1..V-3)
quedaron cerrados en la iteración siguiente a la que los encontró.

- **V-1 → SPEC-019.** Paso `integration` en el adaptador, que ejecuta
  `dirs.tests_integration` y nada más; `sdd-doctor` reporta toda carpeta de tests
  declarada que ningún paso de `pipeline.steps` corre; `sdd-init` detecta la
  carpeta, la siembra y siembra el paso.
- **V-2 → SPEC-017 FR-US3-007.** `verbose: true` en el hook `sdd-gate` de las dos
  copias del wiring: el aviso del escape hatch ahora llega a quien commitea.
- **V-3 → SPEC-014 FR-US2-006.** El dominio lo declara `CONSTITUTION.md`, que se
  regenera; `AGENTS.md` y el README de plantilla remiten en vez de copiarlo.

**Por qué:** los tres eran promesas que se cumplían por partes y se rompían en el
producto instalado — un requisito verificado en unitarios cuyo aviso el transporte
descartaba, una clave del config que nadie ejecutaba, un dato del proyecto
congelado en el momento de la instalación. Es la clase de defecto que motivó
SPEC-018, y la primera vez que el kit los encuentra sin campaña manual.

**Decisiones:**
- **Un paso `integration` propio y no `tests` corriendo todo.** Era la opción de
  una línea, y se descartó: `adapters/CONTRACT.md` define `tests` como suite
  unitaria, así que `step_tests` no se había olvidado de la clave. Reescribir esa
  definición le impondría a todos los derivados el ciclo único que SPEC-018 acababa
  de rechazar para el kit. El paso opcional conserva la distinción rápido/lento y
  **amplía** el contrato en vez de redefinirlo.
- **El paso opcional exige el aviso.** Dejar el paso a criterio del proyecto
  reintroduce el agujero silencioso que la spec corrige, salvo que alguien lo mire:
  por eso US2 y el mapa `TEST_DIR_STEP` como SSOT de qué paso corre qué carpeta.
- **El dominio se elimina, no se sincroniza.** Regenerar `AGENTS.md` en el derivado
  exigiría vendorizar plantillas a cada proyecto: más superficie instalada para
  sostener una copia que conviene no tener. El artefacto que ya se regenera es
  `CONSTITUTION.md`, y el protocolo ya manda leerlo antes de cualquier cambio.
- **El kit no declara `tests_integration`.** No tiene esa carpeta y sus e2e siguen
  fuera del pipeline (SPEC-018). El dogfooding del paso nuevo se hace donde
  corresponde: un escenario e2e sobre un derivado que sí separa sus dos suites.
- **Enmendar SPEC-014/017 en vez de abrir specs nuevas.** V-2 es la garantía de
  FR-US3-004 perdida en el transporte y V-3 es literalmente el invariante de la
  HU-2 de SPEC-014 (*el derivado no afirma nada que no sea cierto de sí mismo*).
  Specs nuevas habrían duplicado el SSOT de dos políticas vigentes.

**Hallazgos:** al agregar el paso, el pipeline lo reportó *"paso desconocido"* y lo
descontó del total sin ruido: `pipeline.CODE_STEPS` y el dispatcher del adaptador
enumeran los pasos por separado y nada los ata (**C-8**, familia de C-1). Queda un
test que cruza las dos listas; la duplicación sigue anotada.

**Deuda:** C-8. La precisión sobre V-1 quedó registrada: el síntoma no era "esos
tests no corren" sino que corrían dentro de `coverage` —y su fallo se reportaba
como cobertura— cuando había umbrales declarados, y en ningún lado cuando no.

**Verificación:** pipeline VERDE 10/10 (los mismos pasos que antes), 310 passed +
1 skip en `tests/unit`, 17 en `tests/e2e`, `render --check` sincronizado,
`sdd-doctor` sano.

**SSOTs afectados:** `adapters/CONTRACT.md` (contrato de pasos),
`core/sdd_config.py` (`TEST_DIR_STEP`), `CONSTITUTION.md` (dominio del proyecto),
`specs/SPEC-017` (política del gate), `specs/SPEC-014` (verdad del derivado),
`specs/SPEC-019` (contrato de los pasos de test).

```
[SDD-Check]
- Specs leídas: SPEC-014, SPEC-017, SPEC-018, SPEC-019, SPEC-003, SPEC-009
- Includes/excludes verificados: el kit no declara dirs.tests_integration y no
  gana el paso `integration`; tests/e2e sigue fuera de testpaths y del pipeline
- SSOTs afectados: adapters/CONTRACT.md, core/sdd_config.py (TEST_DIR_STEP),
  CONSTITUTION.md (dominio), SPEC-014, SPEC-017, SPEC-019
```

## 2026-08-07 — SPEC-018: el kit se verifica instalado, no solo por partes

**Scope:** `tests/e2e/` (harness + 5 escenarios + README), `tests/conftest.py` y
`tests/fixtures_proyecto.py` (nuevos), `tests/unit/conftest.py`,
`tests/unit/test_e2e_entorno.py` y `test_e2e_aislamiento.py` (nuevos),
`.github/workflows/e2e.yml` (escrito a mano), `specs/SPEC-018-...`, `00-INDEX.md`,
`docs/IDEAS.md`.

**Qué cambió:** la campaña manual de usabilidad del derivado —que vivía en una
carpeta sin versionar, sin CI y sin aserciones— pasó a ser una suite e2e
versionada. Cada escenario instala el kit de verdad (`core/sdd_init.py` como
subproceso sobre un repositorio git nuevo) en un workspace efímero fuera del
árbol del kit, y afirma **contenido**, no solo códigos de salida. `pytest
tests/e2e -q`: 12 tests, ~35 s.

**Por qué:** los tres defectos que más costaron en las iteraciones 2 y 3 —falso
verde del pipeline, skills que el instalador recomendaba y no existían, gate que
bloqueaba el segundo commit de una misma spec— no los detectó ningún test
unitario. Ninguna función mentía: mentía el conjunto instalado.

**Decisiones:**
- **Spec propia y no "unos tests más".** `tests/` está fuera de `source_roots`, así
  que el gate no lo exigía, pero SPEC-012 ya es precedente de una spec sobre la
  suite, y lo que se agrega es un nivel de verificación con contrato de entorno y
  CI propios. SPEC-018 automatiza además el SC-004 de SPEC-017, que hasta ahora
  pedía una corrida manual.
- **No declarar `tests/e2e` como `dirs.tests_integration`.** Era la idea inicial,
  para que el `ci.yml` generado la vigilara. Se descartó al verificarlo en código:
  `_source_and_test_dirs` incluye esa clave y `step_coverage` le pasa las carpetas
  a pytest, así que `core/pipeline.py` habría corrido toda la suite e2e dentro del
  paso `coverage`; y el beneficio no existía, porque ese workflow invoca al
  pipeline, que no corre e2e. Fijado con `tests/unit/test_e2e_aislamiento.py` para
  que nadie lo reintroduzca sin enterarse.
- **Un solo mecanismo de selección.** Se descartó registrar una marca `e2e`:
  `testpaths = ["tests/unit"]` ya los excluye y dos filtros para lo mismo violan el
  Principio IV.
- **Degradado explícito en vez de dependencia dura.** Sin `pre-commit` utilizable
  los escenarios de commits reales se omiten **nombrando qué faltó**; con
  `SDD_E2E_STRICT` (que CI setea) la misma condición es fallo.
- **Workflow e2e escrito a mano.** `render_ci_workflow` produce el job universal
  que reciben los derivados; un job específico del kit no puede salir de ahí.
- **El informe de la campaña manual no se importa.** Su continuidad son los
  escenarios, que citan en sus docstrings los defectos que lo originaron.

**Hallazgos de la primera corrida** (anotados como V-1..V-3 en `docs/IDEAS.md`):
`tests_integration` está cableada a medias y el paso `tests` nunca la ejecuta; el
aviso de `SDD_GATE_BYPASS` no le llega al operador porque `pre-commit` se traga la
salida de los hooks que pasan; y cambiar `project.domain` después de instalar no
propaga a ningún artefacto del derivado.

**Deuda:** V-1 necesita spec propia (es cambio de producto sobre `core/` y
`adapters/`) y quedó fuera del alcance de SPEC-018. Los escenarios de otros
lenguajes esperan a que existan los adaptadores.

**SSOTs afectados:** `tests/e2e/README.md` (estrategia de verificación e2e, fila
nueva en `00-INDEX.md`), `specs/SPEC-018-verificacion-e2e.md`,
`specs/SPECS_REGISTRY.md`, `docs/IDEAS.md`.

```
[SDD-Check]
- Specs leídas: SPEC-018-verificacion-e2e, SPEC-017-gate-decision-spec-first,
  SPEC-016-skills-listas-tras-init, SPEC-015-wiring-apunta-al-codigo-real,
  SPEC-014-derivado-dice-la-verdad, SPEC-012-suite-multiplataforma
- Includes/excludes verificados: pipeline VERDE 10/10; 286 tests unitarios + 1
  skip; `pytest tests/e2e` 12/12 en dos corridas consecutivas sin limpieza manual,
  la segunda con SDD_E2E_STRICT=1; `git status` sin residuos tras correrla;
  `render.py --check` sin drift; `sdd-doctor` exit 0
- SSOTs afectados: tests/e2e/README.md, SPEC-018, SPECS_REGISTRY.md, 00-INDEX.md,
  IDEAS.md
```

## 2026-08-06 — SPEC-017: el gate valida contenido de la spec, no marcas de tiempo

**Scope:** `core/sdd_gate.py`, `core/sdd_spec.py`, `templates/wiring/current-spec`,
`templates/docs/SDD-ENFORCEMENT.md` (+ copia sincronizada), `specs/SPEC-017-...`,
enmiendas a SPEC-001/SPEC-002, SPEC-006 a `superseded`, `docs/IDEAS.md`,
`tests/unit/test_gate_evidencia_contenido.py` (nuevo) y `test_sdd_gate.py`.

**Qué cambió:** el gate dejó de comparar la mtime de la spec contra la de
`.sdd/current-spec`. Ahora exige, a **cada** spec declarada, que exista, esté
registrada con estado vigente y **tenga requisitos escritos** (al menos un FR con
texto propio además del keyword; los placeholders de la plantilla no cuentan). Se
agregó el escape hatch `SDD_GATE_BYPASS`, que permite pero imprime el bloqueo que
se saltea junto con el motivo.

**Por qué:** G-5, disparado al cerrar SPEC-016. El ciclo stash/restore del propio
`pre-commit` renueva la mtime de los archivos no staged, así que `.sdd/current-spec`
quedaba más nuevo que la spec y el gate afirmaba que la spec "no fue editada
después de declararla" en pleno commit legítimo. El diagnóstico mostró que el
criterio fallaba en las dos direcciones: bloqueaba el flujo legítimo (varios
commits por spec, checkout, clone) y no detenía a nadie, porque un `touch` lo
satisfacía. Fricción alta, garantía nula.

**Decisiones:**
- **Eliminar el criterio en vez de documentarlo como heurística** (que era lo que
  proponía G-5). La mtime es un proxy de "el contenido cambió"; ninguna tolerancia
  arregla que se mida la señal equivocada.
- **Contenido y no git.** Se evaluó usar `HEAD`/índice como evidencia: resuelve el
  falso positivo pero agrega subproceso, requisito de repositorio y comportamiento
  distinto en worktrees, sin garantía extra (una spec vacía commiteada pasaría).
- **Hash de la spec en `.sdd/current-spec` descartado.** Reproduce el mismo defecto
  en el flujo de varios commits por spec: la spec ya está escrita, el hash no
  cambia, el gate bloquea.
- **Endurecimiento multi-spec.** El criterio viejo se conformaba con que *alguna*
  spec declarada estuviera tocada; ahora se exige a todas.
- **Spec nueva como SSOT de la política, no enmienda.** La política estaba repartida
  entre SPEC-001 FR-002, SPEC-002 FR-002 y SPEC-006 entera. SPEC-017 las absorbe:
  SPEC-001/SPEC-002 delegan sin describir el criterio y SPEC-006 pasa a `superseded`.

**Deuda:** correlacionar el archivo editado con la spec que lo cubre (declarar una
spec completa habilita cualquier archivo bajo `source_roots`) y G-6 (el keyword de
los FR no se verifica en trazabilidad), ambos anotados en la spec.

**SSOTs afectados:** `docs/SDD-ENFORCEMENT.md` (política del gate, vía
`templates/`), `specs/SPEC-017-gate-decision-spec-first.md` (decisión del gate),
`specs/SPECS_REGISTRY.md`, `docs/IDEAS.md`.

```
[SDD-Check]
- Specs leídas: SPEC-017-gate-decision-spec-first, SPEC-001-agnostic-core,
  SPEC-002-dogfooding-integro, SPEC-006-gate-verifica-estado-spec
- Includes/excludes verificados: pipeline VERDE 10/10; 262 tests OK; los tres
  escenarios (spec simple, misma spec en varios commits, dos specs con commit al
  final) verificados con commits reales en el kit y en un derivado instalado
- SSOTs afectados: docs/SDD-ENFORCEMENT.md, SPEC-017, SPECS_REGISTRY.md, IDEAS.md
```

## 2026-08-06 — SPEC-016: las skills quedan usables apenas termina sdd-init

**Scope:** `core/gen_skill_adapters.py`, `core/sdd_init.py`, `README.md`,
`templates/README.md`, `templates/docs/SKILLS-MULTITOOL.md` (+ su copia
sincronizada), `specs/SPEC-016-...`, y 5 archivos de test (2 nuevos).

**Qué cambió:** un derivado recién instalado tenía `.agents/skills/` —que leen
Codex y Antigravity— pero ni `.claude/skills/` ni `.opencode/command/`: para
Claude Code y opencode **no existía ninguna skill SDD**. Los adaptadores se
generaban recién en el paso 3 del onboarding, dos pasos después de que el propio
instalador recomendara *"corré la skill `sdd-configure`"*. Ahora `sdd-init` los
siembra: al terminar la instalación las cinco skills están disponibles en los
cuatro formatos, sin ningún paso manual.

En el README pasaba lo mismo en superficie de documentación: `sdd-configure`
aparecía sólo como comentario `#` dentro del bloque bash, mientras los comandos
visibles instruían editar el YAML a mano. Ahora tiene sección propia (paso 3) con
la tabla de las cinco skills instaladas y para qué sirve cada una, y el README que
recibe el derivado apunta a `docs/SDD-OPERACION.md` como catálogo.

**Por qué:** el primer consejo que el kit le daba a un usuario nuevo era, en
sentido literal, imposible de seguir. Misma clase que U-4/U-11 de SPEC-014 —el
derivado afirmando algo que no es cierto sobre sí mismo— en la superficie del
onboarding.

**Decisiones:**
- **Generar en `sdd-init` en vez de sólo documentar mejor el paso 3.** El paso no
  aportaba ninguna decisión del usuario: siempre se corre igual, con los mismos
  insumos. Un paso manual necesario para que funcione lo que el paso anterior
  recomienda no es documentación faltante, es un orden imposible.
- **Los adaptadores se escriben siempre, aun sin `--force`.** Son artefactos
  generados (cabecera `NO EDITAR A MANO`) y el paso `skills` los verifica con
  `--check`; conservar una versión ajena dejaría la instalación fresca en ROJO.
  La idempotencia sigue valiendo para la fuente `.agents/skills/`.
- **`generate(repo_root, check)` devuelve un `Result` en vez de imprimir.** Es lo
  que permite reusar el generador desde `sdd_init` —que corre en el clon del kit
  apuntando a otro directorio— sin subproceso ni `chdir`, y que cada llamador
  reporte a su manera. `main()` quedó como envoltura fina.
- **Un fallo del generador no aborta la instalación.** El andamiaje ya está
  copiado; dejarlo a medias es peor que un derivado sin adaptadores, que se
  resuelve con un comando (que el aviso incluye).

**Deuda:** E-5 de `docs/IDEAS.md` sigue abierto (adaptadores para Cursor, Aider,
Gemini CLI). `sdd-configure` sigue siendo un playbook para un agente, sin modo CLI
no interactivo.

**SSOTs afectados:** `README.md` (onboarding del operador),
`templates/docs/SKILLS-MULTITOOL.md` (mecanismo de skills), `docs/SDD-OPERACION.md`
(catálogo, sin cambios: se lo referencia desde dos lugares más).

```
[SDD-Check]
- Specs leídas: SPEC-016-skills-listas-tras-init, SPEC-007-derived-project-onboarding, SPEC-011-operator-bootstrap
- Includes/excludes verificados: core/ + README + templates/; fuera de alcance E-5, C-7, sdd-init como skill del derivado
- SSOTs afectados: README.md, templates/README.md, templates/docs/SKILLS-MULTITOOL.md
- Verificación: python core/pipeline.py → VERDE (10/10), 251 tests; instalación limpia → 15 archivos de skill, `gen_skill_adapters.py --check` exit 0, sdd-doctor sano, pipeline del derivado VERDE
```

## 2026-08-05 — SPEC-015: el wiring del gate apunta al código real del proyecto

**Scope:** `.pre-commit-config.yaml` y `templates/wiring/.pre-commit-config.yaml`,
`.claude/settings.json` y `templates/wiring/claude-settings.json`,
`.claude/sdd_gate_hook.sh` y `templates/wiring/sdd_gate_hook.sh`,
`templates/wiring/opencode-sdd-gate.js`, `templates/docs/SDD-ENFORCEMENT.md`
(+ su copia sincronizada), `specs/SPEC-015-...`, `docs/IDEAS.md`, y 3 archivos
de test (2 nuevos). Ni `core/` ni `adapters/` cambiaron: el gate ya leía bien el
config — el problema estaba entero en las capas que lo invocan.

**Qué cambió:** G-1 y G-3 de `docs/IDEAS.md`. El gate spec-first leía
`dirs.source_roots` desde SPEC-001, pero **ninguna** de las tres capas de wiring
lo hacía: todas pre-filtraban por `src/` (o `^(src|app|lib)/`) hardcodeado, así
que un proyecto con el código en `pkg/` tenía las tres muertas. Ahora:
- **pre-commit** no pre-filtra: sin `files:`, todos los staged van al gate y el
  gate decide (`_is_source_path` ya devolvía "permitir" fuera del código).
- **`sdd_gate_hook.sh`** (rama fail-closed) y el **plugin de opencode** derivan
  los roots de `.sdd/config.yaml` con un parseo mínimo propio — no pueden
  consultar al gate, que es justo lo que no está disponible cuando corren.
- El matcher de Claude Code cubre `Edit|Write|MultiEdit|NotebookEdit`.

**Por qué:** la campaña de usabilidad ya lo había reproducido (`pkg/x.py` no
matchea `^(src|app|lib)/` y nunca llega al gate). Es el mismo falso positivo que
cerró SPEC-014 en la última superficie que quedaba: un derivado que reporta el
gate cableado y sano mientras deja pasar todos los commits sobre su código.

**Decisiones:**
- **Eliminar el pre-filtro de pre-commit en vez de generarlo desde el config.**
  Renderizar la regex habría sincronizado una copia; quitarla elimina la copia.
  Además el `.pre-commit-config.yaml` instalado recibe hooks del adaptador de
  lenguaje, y volverlo generado obligaría a pisarlos.
- **Parsear el config en las capas sin Python, no inyectar la lista al
  instalar.** Un placeholder sustituido por `sdd_init` habría driftado en cuanto
  el usuario cambiara `dirs`. Se descartó también el fail-closed total (deja un
  checkout sin Python inutilizable para editar).
- **La duplicación se acepta pero se ata.** Tres derivaciones de la misma regla
  (Python autoritativo, sh, JS) con un test de paridad sobre siete configs
  representativos. El pre-filtro decide *si preguntar*, no *qué política
  aplicar*: puede ser conservador, nunca laxo.
- **`Bash` queda fuera del hook de Claude**, documentado como límite conocido:
  su payload no declara `file_path`. No es un agujero, es un corrimiento de
  capa — pre-commit lo agarra al commitear.

**Bug encontrado al testear:** un `.sdd/config.yaml` con CRLF (lo normal si lo
escribió una herramienta de Windows) dejaba el `\r` pegado al último root, y
ningún patrón matcheaba: el fail-closed permitía todo, en silencio. Resuelto con
`${_l%[[:cntrl:]]}` —clase POSIX en vez de un CR literal invisible o un
subshell— y `config_con_crlf` es uno de los siete casos de paridad.

**Deuda registrada:** `R-4` (el wiring del kit es copia manual de
`templates/wiring/`; esta spec tuvo que editar tres pares a mano) y `C-7`
(`sdd_init.py` ignora en silencio los flags desconocidos y toma el target
posicional: `--target=X` instala en el cwd — reproducido en vivo sobre el propio
kit durante esta iteración).

```
[SDD-Check]
- Specs leídas: SPEC-000-naming, SPEC-001-agnostic-core, SPEC-004-enforcement-hardening, SPEC-014-derivado-dice-la-verdad, SPEC-015-wiring-apunta-al-codigo-real
- Includes/excludes verificados: wiring (kit + plantilla) + docs de enforcement + tests; core/ y adapters/ sin cambios; sincronizar el wiring del kit desde templates queda fuera (R-4)
- SSOTs afectados: templates/docs/SDD-ENFORCEMENT.md (pre-filtro y límite de Bash), docs/IDEAS.md (G-1, G-3, R-4, C-7), specs/SPECS_REGISTRY.md
- Verificación: python core/pipeline.py → VERDE (10/10); python core/sdd_doctor.py → exit 0; 232 tests + 1 skip; testigo real con código en pkg/: commit sin spec BLOQUEADO, commit fuera del código permitido
```

## 2026-08-05 — SPEC-014: el proyecto derivado deja de afirmar cosas que no son ciertas de sí mismo

**Scope:** `core/sdd_config.py` (`find_sdd_root`, `GATE_WIRING`, `script_hint`,
`default_branch`), `core/sdd_gate.py`, `core/sdd_doctor.py`, `core/sdd_init.py`,
`core/render.py`, `core/gen_skill_adapters.py`,
`templates/docs/SDD-ENFORCEMENT.md`, `examples/config/config.yaml`,
`specs/SPEC-014-derivado-dice-la-verdad.md`, `docs/IDEAS.md`, y 5 archivos de
test (4 nuevos).

**Qué cambió:** la segunda mitad de los hallazgos de la campaña de usabilidad
(U-4..U-11 y G-4 de `docs/IDEAS.md`), tomados en bloque en una spec nueva con
**dos historias de usuario** — la primera del kit que usa el formato `FR-USk-NNN`
que `docs/SPEC-FORMAT.md` ya contemplaba.

HU-1, enforcement: `sdd-init` avisa cuando conservó wiring de gate preexistente y
dice cómo resolverlo (FR-US1-001); `sdd-doctor` verifica el **contenido** del
wiring y no solo su existencia (FR-US1-002, el viejo G-4); el gate **falla
cerrado** cuando no puede ubicar una raíz con marcadores SDD (FR-US1-003); la
instalación nombra `00-INDEX.md` como puerta de entrada (FR-US1-004).

HU-2, claridad: todo archivo instalado queda sin placeholders crudos
(FR-US2-001); los mensajes de drift citan la ruta real del script y los
artefactos que efectivamente driftearon (FR-US2-002/FR-US2-003); el config
sembrado lleva cabecera del proyecto destino (FR-US2-004); el CI dispara en la
rama real (FR-US2-005).

**Por qué:** el testigo con wiring propio preexistente terminaba con **cero**
capas de enforcement activas y `sdd-doctor` respondiendo "Instalación SDD sana".
Un falso positivo de seguridad es peor que no tener la herramienta: sustituye la
verificación por una creencia. Lo demás es la misma clase de daño en menor
escala: un `{{sdd.core}}` sin sustituir en `.sdd/current-spec` —el primer archivo
que se abre para entender el gate—, un "corre: python core/render.py" inexistente
en un derivado, un CI que nunca dispara porque la rama es `master`.

**Decisiones:**
- **Dos HU en una spec** en vez de dos specs: comparten el invariante de fondo
  (el derivado no afirma nada que no sea cierto de sí mismo) y el contexto de la
  campaña, pero tienen prioridad y criterio de aceptación distintos, así que
  cada una conserva su *Independent Test*.
- **`GATE_WIRING` como mapa `archivo → invocación esperada` en `sdd_config.py`.**
  La lista de archivos ya vivía en `sdd_doctor.py` y el aviso nuevo de
  `sdd_init.py` habría sido una segunda copia; el mapa es el SSOT de qué cablea
  el gate y de cómo se reconoce que está puesto (principio VI).
- **`find_sdd_root` nueva, `find_repo_root` intacta.** Solo el gate necesita la
  resolución estricta; `pipeline`, `render` y `doctor` corren dentro del proyecto
  y su peor caso es reportar artefactos faltantes. Partir la función en dos evita
  que el endurecimiento del gate se filtre a scripts donde sería ruido.
- **El gate resuelve la raíz por el `cwd` y, si falla, por la ruta del archivo.**
  FR-US1-003 se implementó primero como "sin raíz resoluble, denegar", y eso
  bloqueó en vivo la edición de un `.md` de otra carpeta y del propio kit (el
  `cwd` del asistente había quedado fuera del repo). Lo que decide si hay
  protocolo que aplicar no es desde dónde se invoca al gate sino de qué proyecto
  es el archivo. Con el criterio corregido el fail-open queda igual de cerrado
  —verificado: `cwd` inútil + archivo del testigo ⇒ exit 2— sin el falso
  positivo. La spec quedó enmendada el mismo día, con el hallazgo en sus
  Clarifications.
- **La rama del CI sale del config, no de git en cada render.** Detectarla al
  renderizar haría que el artefacto generado dependiera del estado del repo y
  `--check` dejaría de ser determinista. `sdd-init` la siembra; el default
  sigue siendo `main`.
- **`sdd-init` no sobrescribe el wiring propio**: avisa. La idempotencia es
  deliberada; lo que faltaba era hacer visible la consecuencia.
- La sustitución de placeholders pasa a aplicarse a **todo** lo que se copia. El
  criterio por extensión era la causa raíz de U-6 y volvería a fallar con
  cualquier archivo nuevo sin sufijo.

**Verificación:** pipeline del kit VERDE 10/10, 192 passed + 1 skip (26 tests
nuevos). En el testigo `brownfield-wiring` (proyecto con `app/`, rama `master` y
wiring propio), donde antes salía "Instalación SDD sana": la instalación avisa y
nombra los dos archivos conservados, `sdd-doctor` sale 1 con "existe pero no
invoca sdd_gate.py", el pipeline sale ROJO por las violaciones reales de naming,
`.sdd/current-spec` cita `tools/sdd/core/sdd_gate.py` resuelto y el `ci.yml`
dispara en `master`. El fail-closed del gate verificado con un payload cuyo `cwd`
no resuelve: exit 2.

**Deuda:** G-1 (el pre-filtro `files:` de pre-commit sigue siendo
`^(src|app|lib)/` fijo, así que un proyecto con código en `pkg/` no llega al
gate en el commit), C-2 (mojibake con stdout redirigido en Windows) y E-2 (ruta
de actualización del kit vendorizado) siguen abiertos en `docs/IDEAS.md`.


## 2026-08-05 — SPEC-003 (reabierta) + SPEC-001: el pipeline deja de reportar verde sin haber medido

**Scope:** `core/sdd_init.py` (`_detect_layout`, `_seed_dirs`, `_layout_notice`),
`core/pipeline.py`, `core/sdd_config.py` (`EXIT_OMITIDO`, guarda de `dirs`),
`core/bootstrap_hooks.py`, `adapters/python/adapter.py`, `adapters/CONTRACT.md`,
`README.md`, `templates/docs/playbooks/sdd-configure.md` (y su generado),
`specs/SPEC-003-install-happy-path.md`, `specs/SPEC-001-agnostic-core.md`,
`docs/IDEAS.md`, `tests/unit/conftest.py` y 5 archivos de test.

**Qué cambió:** tres FR nuevos en SPEC-003 (FR-007 sembrado de `dirs` según el
layout real, FR-008 el README nombra `dirs`/`source_roots`, FR-009 un paso
omitido no se cuenta como paso OK) y la enmienda de FR-001/FR-004 y SC-001 de la
misma spec. El contrato de adaptador pasa de dos estados a tres —`0` OK, `3`
omitido, otro falla— lo que obligó a enmendar SPEC-001 FR-005.

**Por qué:** una campaña de usabilidad recorrió el README completo sobre
proyectos testigo, uno vacío y uno con código previo en `app/`. En el segundo, el
kit reportaba `VERDE 8/8` y "instalación sana" mientras `naming` y `tests` se
omitían con el aviso "sin carpetas de codigo todavia", dos violaciones de
SPEC-000 quedaban sin detectar y un commit sobre `app/servicio.py` sin spec
editada pasaba sin bloqueo. Las dos causas eran decisiones de SPEC-003: el
sembrado heredaba los `dirs` del proyecto de referencia y la omisión con exit 0
hacía indistinguible "no medí" de "medí y pasó".

**Decisiones:**
- Se **reabrió** SPEC-003 en vez de abrir una spec nueva: una spec nueva habría
  dejado FR-001/FR-004 falsos sin marca, y el registro solo expresa `superseded`
  a nivel de spec entera. Precedente: SPEC-004 reabierta el 2026-08-01.
- El estado OMITIDO se transporta por exit code y no por un marcador en stdout:
  el pipeline usa `subprocess.call` y deja la salida de los checks en streaming;
  parsearla obligaría a capturarla y reemitirla.
- La omisión sigue existiendo: una instalación fresca no debe arrancar en ROJO
  por tooling que todavía no tiene. Lo que cambia es que no se cuenta como
  verificada. Greenfield pasa de `VERDE 8/8` a `VERDE 4/4 pasos OK` +
  `Omitidos (4, no verificados)`.
- `layers` **no** se siembra según el layout: las capas no se infieren de la
  estructura de carpetas y el principio II las respalda. Lo pregunta
  `sdd-configure`.
- El layout detectado se informa en la salida de instalación, no solo en el
  config: el dueño tiene que poder corregir la adivinanza, y para eso primero
  tiene que saber que se hizo una.
- El helper `crear_proyecto_brownfield` vive en `conftest.py` y no como fixture
  versionado: bajo `tests/`, los `test_*.py` de un fixture los recogería la
  propia suite (`testpaths = ["tests/unit"]`).

**Verificación:** kit VERDE 10/10, 166 tests + 1 skip. Greenfield reinstalado de
cero sigue VERDE con los omitidos a la vista (sin regresión de SC-001).
Brownfield con `app/` sale ROJO por sus 2 violaciones reales sin editar el config
a mano (SC-005), y el gate bloquea `app/servicio.py` por argv y por el hook de
Claude (SC-006).

**Deuda:** los 11 hallazgos restantes de la campaña quedaron en `docs/IDEAS.md`
como U-4..U-11, con SPEC-014 (avisos de wiring conservado y doctor por
contenido, junto con G-4) y SPEC-013/SPEC-009 como destinos propuestos. La
campaña además reprodujo con evidencia G-1, G-4, C-2 y E-2, ya registrados, y
cerró de paso C-1.

## 2026-08-05 — SPEC-000: "token" pasa a llamarse "palabra excluida"

**Scope:** `core/render.py` (plantilla de `SPEC-000-naming.md`),
`specs/SPEC-000-naming.md` (regenerado), `adapters/python/check_naming.py`,
`adapters/CONTRACT.md`, `README.md`, `core/sdd_init.py`, `AGENTS.md`,
`templates/AGENTS.md`, `docs/playbooks/sdd-configure.md` (y su template),
`.agents/skills/sdd-configure/SKILL.md` (y adaptadores generados),
`templates/docs/SDD-OPERACION.md`, `.sdd/config.yaml`,
`examples/config/config.yaml`, `specs/SPEC-001-agnostic-core.md`,
`specs/SPEC-002-dogfooding-integro.md`.

**Qué cambió:** el kit usaba "token" para referirse a los fragmentos de
identificadores de código vetados por `naming.prohibited` (SPEC-000). Se
reemplazó por "palabra excluida" en toda la documentación y los mensajes
user-facing; la clave interna `naming.prohibited` de `.sdd/config.yaml` no se
tocó.

**Por qué:** "token" ya tiene un significado establecido y distinto en el
contexto de LLMs (con el que este kit convive todo el tiempo, al ser
consumido por asistentes de IA). Reusar la palabra para dos conceptos no
relacionados generaba ambigüedad al leer la documentación.

**Decisiones:**
- El cambio es de terminología, no de comportamiento: `naming.prohibited`
  sigue siendo la clave del config; solo cambia cómo se la nombra en prosa.
- `specs/SPEC-000-naming.md` es generado por `render.py`; se editó el
  generador y se regeneró, no se tocó el artefacto a mano en el resultado
  final.

## 2026-08-05 — Enmienda constitucional: Principio IV "SSOT único por tema"

**Scope:** `.sdd/config.yaml` (`principles`, `constitution`), `CONSTITUTION.md`
(regenerado), `AGENTS.md`, `examples/config/config.yaml`.

**Qué cambió:** el kit predicaba "no duplicar SSOT" en su `AGENTS.md` y lo
ofrecía como principio elegible a sus derivados (VI del catálogo), pero no lo
declaraba en su propia constitución. Pasa a ser el Principio IV de sdd-first.
Versión de la constitución: 0.2.0 → 0.3.0 (MINOR pre-1.0: agrega un principio).

**Por qué:** es el invariante que más veces se invocó como justificación en las
specs previas (SPEC-005 desduplicar SSOTs, SPEC-013 la lista vive en un solo
lugar) sin estar escrito donde manda. Un principio que se usa para decidir y no
figura en la constitución erosiona el valor del documento.

**Decisiones:**
- El invariante cubre las dos mitades del problema: entre documentos (una pieza
  normativa vive en un SSOT, el resto referencia) y **dentro** de un documento
  (un detalle compartido por varias secciones se declara una vez). La segunda no
  estaba enunciada en ningún lado y es la que más se viola en la práctica.
- `Enforcement: AGENTS.md` — es revisión editorial, no una tool. Se le agregó a
  `AGENTS.md` el paso operativo (consultar el mapa de SSOTs de `00-INDEX.md`
  antes de escribir una regla nueva) para que el enforcement tenga contenido.
  `check_constitution` no exige paso de pipeline: `AGENTS.md` no está en
  `ENFORCEMENT_STEP`.
- `Detalle: 00-INDEX.md` — ahí vive el mapa de qué documento es SSOT de qué
  tema. La constitución declara el invariante y apunta; no lista los SSOTs.
- El catálogo (`examples/config/config.yaml`, principio VI) recibió el mismo
  invariante, y su `enforcement` pasó de `docs/playbooks/analyze.md` a
  `AGENTS.md`: el playbook `analyze` es spec-scoped y ninguna de sus cinco
  categorías detecta duplicación de SSOT, así que apuntaba a un documento que no
  contenía la regla que decía enforzar.

**Deuda:** `enforcement`/`detail` admiten un solo token (render.py los envuelve
en un único code span y `check_constitution._is_path` valida existencia sobre
él). Un principio con dos SSOTs de detalle no se puede expresar hoy; si hace
falta, es cambio de núcleo y necesita spec propia. Anotado en `docs/IDEAS.md`.

## 2026-08-04 — SPEC-013: el derivado solo declara lo que eligió y lo que tiene

**Scope:** qué recibe un proyecto recién derivado en su `CONSTITUTION.md` y en
sus docs.

**Hallazgos (auditados sobre instalaciones reales, no sobre las plantillas):**

1. El config sembrado copiaba el catálogo completo de principios, opcionales
   incluidos: la constitución de un proyecto nuevo declaraba "Datos no
   versionados" y "SSOT único por tema" sin que nadie los eligiera. Peor: el
   playbook de `sdd-configure` ya mandaba "partí del núcleo mínimo y preguntá
   qué opcionales agregar" — el sembrado contradecía a la skill.
2. `docs/ARCHITECTURE.md` citaba `{{sdd.adapters}}/python/gen_import_linter.py`,
   que con `--language none` no existe: no se vendoriza ningún adaptador.
3. Con `language: none` los principios I y II declaran enforcements que la
   instalación no puede ejecutar. `check_constitution` no lo detecta porque
   `check_naming.py` y `lint-imports` no son rutas.

**Por qué importa:** un principio que el dueño no eligió, o cuyo enforcement no
puede correr, enseña que la constitución es decorativa. Si el primer contacto
con ella es "esto no aplica a mi proyecto", deja de leerse — y es el artefacto
central del kit.

**Decisiones:**
- Se recorta el **sembrado**, no el ejemplo: `examples/config/config.yaml`
  sigue siendo el catálogo de referencia con los seis principios, igual que
  conserva los 10 pasos de pipeline aunque se siembren 8 (SPEC-003 FR-005).
- `_seed_principles` busca el marcador "principios OPCIONALES" del ejemplo en
  vez de contar cuatro: la lista vive en un solo lugar (Principio VI). El
  acoplamiento al texto del comentario es deliberado y quedó anclado con un
  test — sin él, reescribir ese comentario habría desactivado el recorte en
  silencio.
- Los opcionales se comentan con prefijo fijo e indentación relativa, así
  descomentar es borrar `# ` y el YAML sigue alineado; hay un test que lo
  descomenta y valida el parseo.
- `ARCHITECTURE.md` describe el mecanismo (el adaptador del lenguaje traduce
  `layers` a contratos de imports) en vez de citar un archivo que puede no
  estar. El doc de capas se instala con cualquier lenguaje.
- Para el hallazgo 3, que no da para automatizar: `sdd-configure` avisa al
  ofrecer un principio cuyo enforcement esta instalación no puede ejecutar.

**Anti-regresión:** `test_derived_references.py` instala de verdad en los dos
lenguajes, corre `render.py` (sin eso, SPEC-000 y el CI generado aparecen como
rutas rotas) y falla si algún doc instalado cita un archivo ausente.
`check_constitution` ya cubría las líneas de la constitución; nada cubría el
resto de los documentos.

**SSOTs afectados:** `templates/docs/ARCHITECTURE.md`,
`templates/docs/playbooks/sdd-configure.md`.

```
[SDD-Check]
- Specs leídas: SPEC-013-proyecto-derivado-coherente, SPEC-003, SPEC-010,
  CONSTITUTION.md
- Includes/excludes verificados: core/sdd_init.py (_seed_principles) +
  templates/docs/{ARCHITECTURE.md,playbooks/sdd-configure.md} + 3 tests
- SSOTs afectados: plantillas de docs; examples/config/config.yaml intacto
- Verificación: constitución fresca con 4 principios (antes 6); cero rutas
  colgadas en `none` y `python`; pipelines VERDE (derivado none 4/4, derivado
  python 8/8, kit 10/10); 147 passed + 1 skipped
```

## 2026-08-04 — SPEC-012: el pipeline del kit corre verde en Windows

**Scope:** la deuda que dejó SPEC-011. `python core/pipeline.py` salía ROJO
8/10 en Windows de forma permanente e inevitable.

**Causa:** `Path.chmod(0o755)` corre sin error en NTFS pero `st_mode` reporta
los bits de ejecución apagados. `test_main_instala_y_marca_ejecutable`
aseveraba un efecto que la plataforma no puede producir. El paso `coverage`
caía en cascada del paso `tests` (medido aparte daba 55% ≥ 50%).

**Por qué importaba más de lo que parece:** un ROJO permanente destruye el
valor del pipeline como señal — el desarrollador aprende a ignorarlo y a
recordar "cuál es el fallo de siempre". Es exactamente el problema que el kit
existe para resolver, y lo tenía sobre sí mismo, en contra del Principio III.

**Decisiones:**
- El `chmod` de `sdd_init.py` **no** se toca: en POSIX el bit es real y
  necesario (`.claude/sdd_gate_hook.sh` se invoca como ejecutable). El defecto
  era del test.
- Se descartó el `skipif` pelado: habría dejado el wiring ejecutable sin
  cobertura alguna en la plataforma donde más se desarrolla. En su lugar, la
  aserción se parte en dos niveles — la **intención** (que el instalador
  aplique `chmod(0o755)` a cada destino de `_EXECUTABLE_WIRING`, espiando
  `Path.chmod`) corre en todas las plataformas; el **efecto** sobre `st_mode`
  solo donde el filesystem lo expresa.
- El criterio de plataforma vive en `conftest.py` como marca reutilizable
  (`requiere_permisos_posix`), con motivo explícito: el próximo test con el
  mismo problema no tiene que re-derivarlo, y un skip mudo no enseña nada a
  quien lee la salida.

**Verificación del test, no solo del código:** se parcheó `sdd_init.py` para
omitir el `chmod` y se confirmó que la suite **falla en Windows**. Sin ese
paso, FR-001 podía ser un test que no protege nada.

**SSOTs afectados:** ninguno (solo la suite de tests).

```
[SDD-Check]
- Specs leídas: SPEC-012-suite-multiplataforma, SPEC-004, CONSTITUTION.md
- Includes/excludes verificados: tests/unit/{conftest,test_sdd_init_seeded_steps}.py
- SSOTs afectados: ninguno; core/sdd_init.py sin cambios (FR-003)
- Verificación: python core/pipeline.py → VERDE 10/10 en Windows (antes ROJO
  8/10); 139 passed + 1 skipped; SC-002 verificado parcheando el chmod
```

## 2026-08-04 — SPEC-011: bootstrap reproducible en el README del kit

**Scope:** el `README.md` de la raíz, único punto de entrada del operador que
clona el kit para sembrar un proyecto derivado.

**Hallazgo:** la sección "Cómo se usa" arrancaba a mitad de camino. Un operador
que la seguía literalmente no llegaba: faltaba el `git clone`, faltaba
`pip install pyyaml` —bloqueante desde el primer comando, porque `sdd_config`
importa `yaml` a nivel módulo y sale con `SystemExit`—, y el cambio de
directorio entre los comandos del kit (`core/…`) y los del destino
(`tools/sdd/core/…`) era implícito. A eso se sumaban tres cosas que el operador
solo podía descubrir leyendo el código: que `sdd-init` **no** se instala en el
derivado (bootstrap de una sola vez, decidido en SPEC-007), que el clon queda
descartable tras la vendorización, y que el gate bloquea toda edición hasta
crear la primera spec.

**Por qué una spec propia:** SPEC-003 cubrió el happy path *técnico* de
instalación (que el pipeline fresco salga VERDE) y SPEC-007 le dio README y
manual al *proyecto derivado*. El onboarding del operador **del kit** no tenía
dueño — un hueco de gobernanza, no de comportamiento.

**Decisiones:**
- El comportamiento de instalación no cambia (`sdd_init.py` ya crea el destino y
  ya es idempotente); lo que fallaba era la comunicación, en sus **dos** caras:
  el README y el mensaje de cierre del instalador. El operador termina mirando
  esa salida, no el README, y ahí también faltaba el `cd` al destino —sin el
  cual los `tools/sdd/...` que seguían no resuelven desde el clon— y la primera
  spec. El mensaje ahora imprime el path real y **omite los pasos ya
  satisfechos** (`git init` si ya es repo, `pip install pre-commit` si ya está
  importable): un paso innecesario resta credibilidad al que sí hace falta.
- No se revierte la decisión de SPEC-007 sobre `sdd-init`: el bootstrap
  circular se resuelve explicándolo en el README, no instalando la skill.
- El README no es artefacto generado, así que la protección contra drift es un
  test (`test_readme_bootstrap.py`), que además verifica que cada script del
  kit citado exista en disco — mismo rol que `test_template_paths.py` cumple
  para las plantillas.
- `pre-commit install` no se documenta a mano: el paso `hooks` ya lo hace. Lo
  que se documenta son sus dos precondiciones (repo git + `pre-commit`
  instalado), porque sin ellas el bloqueo en el commit queda inactivo en
  silencio.

**Deuda detectada, no tocada:**
- `test_sdd_init_seeded_steps.py::test_main_instala_y_marca_ejecutable` falla
  en Windows: `Path.chmod(0o755)` no setea bits de ejecución en NTFS. Es
  **preexistente** (verificado sobre HEAD limpio) y ajeno a esta spec; el
  pipeline del kit queda ROJO 8/10 en Windows por eso y por `coverage` en
  cascada. En Linux/CI no se manifiesta. Requiere su propia spec.

**SSOTs afectados:** `README.md` y el mensaje de cierre de `core/sdd_init.py`.

```
[SDD-Check]
- Specs leídas: SPEC-011-operator-bootstrap, SPEC-003, SPEC-007, CONSTITUTION.md
- Includes/excludes verificados: README.md + core/sdd_init.py (_next_steps) +
  tests/unit/{test_readme_bootstrap,test_sdd_init_next_steps}.py
- SSOTs afectados: README.md (onboarding del operador del kit); sdd_init.py
  imprime la misma secuencia, resuelta al destino real
- Verificación: bootstrap end-to-end en sandbox siguiendo README y mensaje del
  instalador → pipeline VERDE 8/8; pytest 138 passed (1 fallo preexistente de
  Windows, ajeno); coverage 55% ≥ 50%; ruff check + format limpios
```

## 2026-08-04 — SPEC-009 + SPEC-010: segunda cosecha del proyecto de referencia (coverage, CI, gobernanza, rutas)

**Scope:** comparación sistemática con `evaluador-flujo-intent` (la primera
fue SPEC-004) para decidir qué coordinar entre ambos. **Decisión de producto
del usuario: los proyectos siguen independientes** — migrar el evaluador a
consumir el kit implicaría rehacer su andamiaje entero y no es el espíritu del
SDD. Lo que se porta es el *mecanismo*, generalizado y parametrizado.

**Hallazgo que orientó todo:** línea a línea, el núcleo del kit está
**adelante** del evaluador (`check_constitution` verifica el cableado contra
`pipeline.steps` en vez de hardcodear `PIPELINE_TOOLS`; `sdd_gate`/`sdd_reset`
centralizan `find_repo_root` en `sdd_config`). Lo que le faltaba al kit no era
lógica de validación sino **capas de verificación y de explicación**. De ahí
las dos specs: 009 es comportamiento de pipeline, 010 es gobernanza y docs.

**SPEC-009 (coverage + CI):**

1. Paso `coverage` en el adaptador Python, con umbrales **opcionales** por
   target: `pipeline.coverage: [{paths, min}]`. Varias entradas porque el
   patrón útil del evaluador es "el dominio se exige más que el resto" y
   `--cov-fail-under` es un umbral único por corrida (de ahí una invocación de
   pytest por entrada). Ausente, sin `pytest-cov`, sin carpeta de tests o con
   el target todavía inexistente ⇒ se omite con aviso: una instalación fresca
   no puede salir ROJO por una métrica que aún no tiene sentido medir
   (SPEC-003 FR-001).
2. `.github/workflows/ci.yml` **generado** por `render.py` desde el config, no
   una plantilla copiada. Los `paths:` de disparo derivan de
   `dirs.source_roots` + carpetas de tests (un cambio que solo toca `docs/` no
   gasta una corrida) y el job **invoca el pipeline en vez de enumerar los
   pasos**. Esto último es una corrección deliberada al modelo del evaluador,
   donde la lista está duplicada y las dos copias ya divergieron: su
   `pipeline_local.sh` corre 11 pasos y su `ci.yml` 10, sin `hooks` ni
   `skills`. Al ser artefacto generado, entra al `render --check` del pipeline
   y no puede driftear.
3. `requirements-dev.txt` del kit (deuda E-3 parcial): sin él, la CI generada
   omitía todos los pasos de código "con aviso" y habría sido verde vacío.

**SPEC-010 (gobernanza y docs):**

4. `CONSTITUTION.md` generada ahora incluye **Preámbulo** (qué es, cómo se usa,
   alcance: invariante + puntero, nunca duplicar el detalle) y **Governance**
   real (semver desglosado por MAJOR/MINOR/PATCH, fase pre-1.0, procedimiento
   de enmienda en 5 pasos, precedencia). Arrastraba C-5: la versión estaba
   hardcodeada en `render.py`, así que prometer un procedimiento de enmienda
   era incoherente — ahora sale de `constitution.{version,ratified,amended}`
   del config, con defaults retrocompatibles.
5. `docs/SKILLS-MULTITOOL.md`: el mecanismo de `gen_skill_adapters.py` existía
   y estaba en el pipeline, pero **no estaba documentado en ninguna parte**.
   Quien recibía el kit veía carpetas marcadas "NO EDITAR A MANO" sin saber
   qué las generaba ni cómo agregar una skill propia.
6. `docs/DEVELOPMENT.md` para el proyecto derivado (setup, comandos, tooling
   opcional por paso, umbrales de cobertura).
7. Principio opcional "SSOT único por tema" al catálogo de
   `examples/config/config.yaml` — el kit lo predicaba en su `AGENTS.md` pero
   no lo ofrecía como principio configurable. Va con enforcement editorial
   (`docs/playbooks/analyze.md`), que `check_constitution` no exige cablear
   como paso.

**Bug E-6, más ancho de lo registrado:** no era solo `templates/AGENTS.md`.
Ocho plantillas citaban `core/...`, que en un proyecto instalado es
`tools/sdd/core/...`: el usuario copiaba el comando del `CONTRIBUTING.md` que
el propio kit le había instalado y no funcionaba. La causa es estructural —
un mismo documento sirve a dos layouts. Resuelto con placeholders
`{{sdd.core}}` / `{{sdd.adapters}}` (mismo mecanismo que `{{project.name}}`),
que `render.py` resuelve a `core`/`adapters` al sincronizar hacia la raíz del
kit y `sdd_init.py` a `tools/sdd/...` al instalar. Un test parametrizado barre
`templates/` y falla ante cualquier ruta pelada nueva.

**Bug nuevo encontrado de paso (F-6, fuera de las dos specs):**
`.gitattributes` no forzaba LF en los `.sh`. `sh` no ejecuta un script con
CRLF (falla con `\n: not found` / `Syntax error: word unexpected`), así que en
un checkout de Windows **el hook del gate spec-first está roto en silencio**:
devuelve 2 para todo, incluido lo que debería permitir. Se detectó porque los
4 tests de `test_sdd_gate_hook.py` fallaban en el clon actual (y siguen
fallando: el working tree ya está convertido). Regla agregada al
`.gitattributes` del kit y de la plantilla; **el árbol existente necesita
`git add --renormalize .` a mano**, la regla solo evita la repetición.

**Decisiones:** (a) los umbrales de cobertura son opcionales y se siembran
comentados, no obligatorios — coherente con SPEC-003; (b) la CI invoca el
pipeline en vez de duplicar pasos, corrigiendo el modelo de referencia; (c)
los umbrales del propio kit se fijaron en el **piso medido** (50%) como
trinquete, no en un ideal.

**Deuda arrastrada:** F-7 — `check_constitution.py`, `gen_skill_adapters.py` y
`sdd_doctor.py` están en 0% de cobertura (total del kit: 52%); subir el umbral
exige cubrirlos primero. Sigue abierta la ruta de actualización del kit
vendorizado (E-2): los proyectos ya instalados no reciben los placeholders
nuevos automáticamente. Y los 4 tests del hook seguirán en rojo hasta la
renormalización de fin de línea.

**[SDD-Check] — 2026-08-04**
- Specs leídas: SPEC-009-coverage-y-ci, SPEC-010-gobernanza-y-docs, SPEC-003
  (happy path, criterio de omisión con aviso), SPEC-005 (sync docs/templates),
  SPEC-007, CONSTITUTION.md, docs/IDEAS.md (C-5, E-3, E-5, E-6).
- Includes/excludes verificados: núcleo sigue agnóstico (los umbrales y los
  `paths:` de CI salen del config, nada hardcodeado); lo específico de Python
  quedó en `adapters/python/adapter.py`; naming agnóstico en los
  identificadores nuevos (`CoverageTarget`, `kit_path_tokens`,
  `render_ci_workflow`); descartado explícitamente lo específico del dominio
  del evaluador (`schema_drift_check`, `connection_check`, `e2e_probe`).
- SSOTs afectados: `.sdd/config.yaml`, `examples/config/config.yaml`,
  `core/{sdd_config,render,pipeline,sdd_init}.py`,
  `adapters/python/adapter.py`, `templates/` (8 documentos + wiring),
  `templates/docs/{SKILLS-MULTITOOL,DEVELOPMENT}.md`, `00-INDEX.md` (kit y
  plantilla), `README.md`, `.gitattributes`, `docs/IDEAS.md`,
  `specs/SPECS_REGISTRY.md`, `historial/sdd.md`.

---

## 2026-08-02 — SPEC-007: README propio y manual de operación SDD en el proyecto derivado (E-1, E-7 de docs/IDEAS.md)

**Scope:** cerrar dos huecos del happy path de instalación: el proyecto
derivado solo recibía las skills `analyze`/`clarify` (E-1) y no recibía ni
`README.md` ni un manual humano de las herramientas SDD (E-7). Decisión de
diseño: el README del derivado habla solo del producto (nunca de SDD); el
manual de operación de SDD vive aparte, en `docs/SDD-OPERACION.md`.

**Bloqueante encontrado y resuelto primero:** `Path.write_text(...,
newline="\n")` no es una llamada válida en ninguna versión de Python (el
kwarg no existe en `write_text`, solo en `Path.open`) — bug preexistente en
`sdd_spec.py`, `render.py`, `gen_skill_adapters.py`, `sdd_init.py` y
`adapters/python/gen_import_linter.py` que nunca se había disparado porque el
kit siempre estaba en sync (sin drift que forzara una escritura real).
Bloqueaba por completo la creación de esta misma spec. Fix: helper
`sdd_config.write_text_lf` (vía `Path.open(newline="\n")`) usado en los 5
puntos.

**Hecho:**
- `templates/README.md` (nuevo): producto derivado, placeholders `{{project.name}}`/
  `{{project.domain}}`, sección final "Desarrollo" con un único link a
  `AGENTS.md` y `docs/SDD-OPERACION.md` — sin explicar el protocolo SDD.
- `templates/docs/SDD-OPERACION.md` (nuevo): catálogo humano de las 5 skills
  SDD instaladas (qué hace cada una, cuándo invocarla).
- `templates/docs/playbooks/{sdd-spec,sdd-doctor,sdd-configure}.md`: movidos
  desde `docs/playbooks/` (pasan a ser SSOT en `templates/`); las copias del
  propio kit ahora se generan vía `_SYNCED_FROM_TEMPLATES` en `render.py`
  (patrón SPEC-005), no se editan a mano.
- `core/sdd_init.py`: `STATIC_DOCS` suma `README.md`, `docs/SDD-OPERACION.md`
  y los 3 playbooks movidos; `PROJECT_SKILLS` suma `sdd-spec`, `sdd-doctor`,
  `sdd-configure` (no `sdd-init`, bootstrap de una sola vez).
- Tests nuevos: `test_sdd_init.py` (instalación completa, idempotencia del
  README, README sin detalle de SDD), `test_render.py` (sync de los 3
  playbooks nuevos), `test_sdd_config.py` (`write_text_lf`) — suite: 77
  tests.
- Verificado con instalación fresca en `/tmp`: `sdd_init.py` → `render.py` →
  `gen_skill_adapters.py` → `sdd_doctor.py` sano, 5 skills generadas para
  Claude y opencode.
- `docs/IDEAS.md`: E-1 y E-7 marcados con puntero a esta spec.

**Deuda:** ninguna nueva. Sigue pendiente `sdd-init` como skill instalable
(fuera de alcance, ver SPEC-007 "Fuera de alcance") y `sdd-update` (E-2).

## 2026-08-01 — SPEC-004 (reabierta): sdd_spec.py preserva el header de current-spec (G-7 de docs/IDEAS.md)

**Scope:** al usar `sdd_spec.py` en la práctica (durante esta misma sesión,
para SPEC-006), se notó que `.sdd/current-spec` quedaba modificado en el
working tree después de cada commit exitoso, pese a que `sdd_reset.py`
(SPEC-004 FR-002) corría bien. Causa: `sdd_spec.py::main` pisaba el archivo
entero con `f"{spec_id}\n"`, destruyendo el header de comentarios de la
plantilla *antes* de que hubiera un commit — `sdd_reset.py` filtra líneas `#`
post-commit, pero no había ninguna que filtrar, así que el resultado nunca
coincidía con lo committeado. SPEC-004 ya declaraba esta garantía como FR-002/
SC-002 (con un test que la ejercitaba solo de forma aislada, sembrando el
archivo a mano); se reabrió esa spec en vez de crear una nueva, porque el
invariante roto es el mismo que ya gobierna.

**Hecho:**
- `core/sdd_spec.py`: nueva `_declare_current_spec` que preserva las líneas
  `#` existentes y solo agrega/reemplaza la línea del spec-id (antes pisaba
  todo el archivo).
- SPEC-004 suma FR-007, dos Acceptance Scenarios y SC-004 (el ciclo real
  declarar→commit→reset deja el archivo byte a byte igual al header de
  `templates/wiring/current-spec`).
- Tests nuevos en `test_sdd_spec.py` (preserva comentarios, reemplaza sin
  apilar, sin archivo previo no falla, ciclo real declarar→reset) — suite:
  70 tests. Verificado además con una instalación fresca en `/tmp`
  (`sdd_init.py` → `sdd_spec.py` → `sdd_reset.py`): diff vacío contra el
  header de la plantilla.
- `docs/IDEAS.md`: G-7 marcado como parcialmente resuelto — la semántica
  multi-spec (append vs replace) sigue pendiente, separada de este fix.

**Deuda:** ninguna nueva.

## 2026-08-01 — SPEC-006: El gate verifica el estado de la spec declarada (G-2 de docs/IDEAS.md)

**Scope:** cerrar un bypass real del gate spec-first: `_spec_is_valid` en
`core/sdd_gate.py` validaba una spec declarada con `spec_id in
registry.read_text(...)` — un substring match sobre el texto crudo del
registro. Una spec `archived`/`superseded` (o solo mencionada en prosa, p. ej.
en un roadmap fuera de la tabla) desbloqueaba el gate igual que una `active`,
rompiendo la garantía central del kit ("no se edita código sin spec vigente").

**Hecho:**
- `core/sdd_gate.py`: `_spec_is_valid` reemplazada por `_registry_row` +
  `_spec_invalid_reason`, que parsean la fila real del registro (reusando
  `check_traceability._parse_registry`, sin duplicar el parser) y exigen
  `estado` en `{draft, active}`. El mensaje de bloqueo ahora distingue "no
  existe el archivo", "no está registrada" y "estado 'X' no vigente".
- Tests nuevos en `test_sdd_gate.py` (archived, superseded, mención solo en
  prosa, estado active) — suite: 66 tests.
- Verificado además con una instalación real vendorizada en `/tmp` (no solo
  tests unitarios): los tres escenarios (archived bloquea, active permite,
  mención en prosa bloquea) reproducen igual que en los tests.

**Deuda:** ninguna nueva; `docs/IDEAS.md` mantiene G-1 (pre-commit hardcodea
`files:`), G-3..G-8 y E-1..E-6 para specs futuras.

## 2026-08-01 — SPEC-005: Desduplicar SSOTs del kit (R-1, R-2, R-3 de docs/IDEAS.md)

**Scope:** eliminar la duplicación de archivos y defaults dentro del propio
repo que "No duplicar SSOT" prohíbe: `docs/` vs `templates/docs/`
(`SDD-ENFORCEMENT.md`, playbooks `analyze`/`clarify`), `specs/SPEC-TEMPLATE.md`
duplicado dos veces (archivo + embebido en prosa en `SPEC-FORMAT.md`), y los
literales `"src"`/`"tests/unit"` repetidos como fallback en `sdd_gate.py` y
`adapter.py`.

**Hecho:**
- `core/sdd_config.py`: nuevas constantes `DEFAULT_SOURCE_ROOT` (`"src"`) y
  `DEFAULT_TESTS_UNIT` (`"tests/unit"`); `sdd_gate.py` y
  `adapters/python/adapter.py` las importan en vez de repetir el literal.
- `templates/docs/SPEC-FORMAT.md`: la sección "Template copiable" ya no
  embebe el template completo — referencia `specs/SPEC-TEMPLATE.md` como
  único archivo fuente.
- `core/render.py`: además de generar `CONSTITUTION.md`/`SPEC-000-naming.md`
  desde el config, ahora sincroniza (copia byte a byte, `--check` detecta
  drift) `docs/SDD-ENFORCEMENT.md`, `docs/playbooks/analyze.md`,
  `docs/playbooks/clarify.md` y `specs/SPEC-TEMPLATE.md` desde `templates/`
  — pero solo cuando el repo tiene su propia carpeta `templates/` (el caso
  del kit dogfoodeando sobre sí mismo); en un proyecto instalado con
  `sdd-init` (sin `templates/`) estas entradas son no-op.
- `core/pipeline.py`: nuevo paso de proceso `render` (corre
  `render.py --check`), agregado a `PROCESS_STEPS` y a `pipeline.steps` en
  `.sdd/config.yaml` del kit — el drift entre `templates/` y sus copias ahora
  bloquea el pipeline como cualquier otro paso.
- Tests nuevos: `test_render.py`, `test_pipeline_render_step.py`,
  `test_spec_format_reference.py`, más una prueba en `test_sdd_config.py`
  que verifica que `sdd_gate` y `adapter` reusan la misma constante (no la
  repiten) — suite: 62 tests.

**Deuda:** ninguna nueva; `docs/IDEAS.md` mantiene registradas G-8 (idea del
usuario sobre trazabilidad FR→test), E-1/E-2/E-3 (skills en destino,
`sdd-update`, packaging) y G-7 (multi-spec en `current-spec`) para specs
futuras.

## 2026-08-01 — SPEC-004: Enforcement hardening (comparación con evaluador-flujo-intent)

**Scope:** cerrar dos huecos reales del gate spec-first descubiertos al
comparar con `evaluador-flujo-intent` (proyecto que corrió el gate más tiempo
en producción): `.sdd/current-spec` podía quedar vigente indefinidamente, y un
`git clone` nuevo no tenía los hooks git instalados hasta que alguien corría
`pre-commit install` a mano. De paso, mismo bug del `python` no encontrado que
ya se había resuelto para Claude Code/opencode (sesión anterior), sin resolver
en la capa `pre-commit`.

**Hecho:**
- `core/bootstrap_hooks.py` (nuevo): instala hooks `pre-commit`/`post-commit`
  si faltan, idempotente, no-op sin `.git/`. Wireado como paso `hooks` en
  `core/pipeline.py` (primero en `PROCESS_STEPS`) y en `_SEEDED_STEPS` de
  `sdd_init.py` (primer paso sembrado en proyectos nuevos).
- `core/sdd_reset.py` (nuevo): limpia `.sdd/current-spec` tras cada commit
  exitoso, dejando solo comentarios. Wireado como hook `sdd-reset`
  (`stages: [post-commit]`) en `.pre-commit-config.yaml` (kit) y
  `templates/wiring/.pre-commit-config.yaml` (plantilla instalada).
- `.pre-commit-config.yaml` y `templates/wiring/.pre-commit-config.yaml`:
  `language: system` → `language: python` (+ `additional_dependencies:
  [pyyaml]`) en los hooks locales — pre-commit gestiona su propio intérprete
  aislado, ya no depende de que el shell invocador tenga `python` en el PATH.
- `docs/SDD-ENFORCEMENT.md` (+ su copia en `templates/docs/`): documenta las
  tres piezas nuevas.
- Tests nuevos: `test_bootstrap_hooks.py`, `test_sdd_reset.py`,
  `test_pipeline_hooks_step.py`, `test_sdd_init_seeded_steps.py`,
  `test_sdd_gate_hook.py` (cubre `.claude/sdd_gate_hook.sh` y
  `templates/wiring/sdd_gate_hook.sh`, ramas normal y fail-closed) — suite:
  53 tests.
- Validado con `pre-commit run --all-files` real (no solo tests unitarios:
  crea el venv aislado, instala `pyyaml`, ambos hooks corren y pasan) y con
  instalación fresca vía `sdd_init.py` en directorio temporal.

**Deuda:**
- No se portaron los coverage gates (`--cov-fail-under`) ni el wiring de
  ruff/mypy como hooks de pre-commit — quedó fuera de alcance de este
  hardening (ver "Fuera de alcance" en SPEC-004).

## 2026-07-02 — SPEC-003: Happy path de instalación (B-1..B-4 de docs/IDEAS.md)

**Scope:** una instalación fresca con `sdd-init` arranca con pipeline VERDE y
las herramientas del kit no rompen sus propios artefactos.

**Hecho:**
- `adapters/python/adapter.py`: pasos sin targets o sin tool instalada
  (ruff/mypy/bandit/pytest/import-linter) se omiten con aviso y exit 0, en vez
  de fallar (antes: instalación fresca → ROJO 6/10; ahora → VERDE).
- `check_naming.py`: la relajación de tokens en tests aplica a los dirs de
  tests del config (`tests_unit`/`tests_integration`), con fallback al
  basename; antes `relax_in_tests` era inoperante con el layout `tests/unit`.
- `sdd_spec.py`: la fila nueva se inserta al final de la tabla de specs, no
  al final del archivo (antes quedaba huérfana después de `## Roadmap` en el
  registro plantilla). Fila con ID simplificado `SPEC-NNN`.
- `sdd_init.py`: el config sembrado declara solo pasos operativos
  out-of-the-box (constitution, traceability, naming, layers, skills, tests);
  el resto queda comentado. `layers` va incluido porque el principio II del
  ejemplo lo exige cableado (descubierto al verificar: sembrar el mínimo sin
  `layers` hacía fallar `check_constitution`).
- README: nota de qué tooling requiere cada paso de código y la semántica de
  omisión con aviso.
- Tests nuevos: `test_python_adapter.py`, `test_sdd_spec.py`, `_is_test_root`
  en `test_check_naming.py` (suite: 37 tests).

**Deuda:**
- El resto del backlog (`G-*`, `R-*`, `C-*`, `E-*`) sigue en `docs/IDEAS.md`.

```
[SDD-Check]
- Specs leídas: SPEC-001-agnostic-core, SPEC-002-dogfooding-integro, SPEC-003-install-happy-path
- Includes/excludes verificados: adapter/check_naming/sdd_spec/sdd_init + README; gate (G-*) fuera de alcance
- SSOTs afectados: specs/SPECS_REGISTRY.md, README.md, examples (sembrado, no el ejemplo)
- Verificación: pytest 37/37; pipeline kit → VERDE (7/7); doctor → exit 0; sandbox fresco → VERDE (6/6), relax OK, fila en tabla OK
```

## 2026-07-02 — SPEC-002: Dogfooding íntegro (D-1..D-4 de docs/IDEAS.md)

**Scope:** el kit pasa a cumplir su propio protocolo: gate cableado, primera
suite de tests, doctor en verde, SPEC-001 promovida.

**Hecho:**
- Gate spec-first cableado en el propio kit: `.claude/settings.json`
  (PreToolUse → `core/sdd_gate.py`), `.pre-commit-config.yaml`
  (`^(core|adapters)/`), `.sdd/current-spec`, `.gitattributes`.
- `tests/unit/` (27 tests): `sdd_gate.decide`, `check_traceability`,
  `check_naming`, `sdd_config`. Pipeline del kit ampliado con `lint`,
  `format`, `tests` (7 pasos, VERDE).
- `00-INDEX.md` del kit creado (el doctor lo exigía; queda como idea
  parametrizar los requeridos del doctor).
- `specs/SPEC-TEMPLATE.md` copiado al kit (antes `sdd_spec.py` caía al
  fallback TODO — gap descubierto durante esta iteración).
- SPEC-001 promovida a `hibrido`/`active` con FRs, SC y Coverage mapping.
- `ruff format` aplicado a `core/` y `adapters/` (mecánico, sin cambio de
  comportamiento) para habilitar el paso `format`.

**Deuda:**
- Pasos `types`/`security` del kit (mypy --strict y bandit) — diferidos.
- El resto del backlog priorizado vive en `docs/IDEAS.md`.

```
[SDD-Check]
- Specs leídas: SPEC-000-naming, SPEC-001-agnostic-core, SPEC-002-dogfooding-integro
- Includes/excludes verificados: wiring + tests/unit + 00-INDEX + SPEC-001; types/security fuera de alcance
- SSOTs afectados: .sdd/config.yaml (pipeline.steps), specs/SPECS_REGISTRY.md, 00-INDEX.md (nuevo)
- Verificación: python core/pipeline.py → VERDE (7/7); python core/sdd_doctor.py → exit 0
```

## 2026-07-01 — Bootstrap del kit (v0.1.0)

**Scope:** extracción y generalización del andamiaje SDD del proyecto de
referencia (evaluador-flujo-intent) hacia un kit universal, agnóstico y
personalizable.

**Decisiones tomadas:**
- Config único en YAML (`.sdd/config.yaml`) como SSOT de parámetros; los
  validadores dejan de tener listas hardcoded.
- Separación núcleo agnóstico (`core/`) vs adaptadores por lenguaje
  (`adapters/`). Contrato de adaptador `adapter.py <step>`.
- Núcleo mínimo obligatorio: nomenclatura, capas, trazabilidad, gate spec-first.
- Skills con responsabilidades separadas: `sdd-init` (instala), `sdd-configure`
  (wizard + config), `sdd-doctor` (salud/drift), `sdd-spec` (crea spec + gate);
  `analyze`/`clarify` portados.
- Pipeline reescrito como orquestador Python multiplataforma (reemplaza al .sh).
- `sdd_gate.py` lee las carpetas de código de `dirs.source_roots`.
- El gate no es un paso de pipeline: se cablea por hooks y lo verifica
  `sdd-doctor`.

**Deuda arrastrada:**
- Adaptadores `node`/`go`: sólo contrato documentado, sin implementar.
- Coverage mapping FR→nodo-de-test estricto: diferido (celdas en prosa).
- `render.py` cubre CONSTITUTION.md y SPEC-000; el resto de plantillas se copian
  con sustitución simple.

**SSOTs afectados:** todos (bootstrap).

```
[SDD-Check]
- Specs leídas: SPEC-000-naming, SPEC-001-agnostic-core
- Includes/excludes verificados: core/ + adapters/python + templates + skills
- SSOTs afectados: CONSTITUTION.md (generado), AGENTS.md, specs/, docs/, .sdd/config.yaml
- Verificación: python core/pipeline.py → VERDE (4/4); install demo python/none → VERDE; gate/anti-drift OK
```
