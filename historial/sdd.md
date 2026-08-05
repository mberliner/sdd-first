# Historial SDD — sdd-first

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
