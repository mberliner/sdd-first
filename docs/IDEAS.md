# Ideas pre-spec — sdd-first

> SSOT de ideas que todavía no son spec. Cuando una idea se promueve, se marca
> con un puntero `(ya con spec) → [[SPEC-NNN-slug]]` y su desarrollo pasa a la spec.
>
> Este documento ordena los hallazgos de la revisión crítica del 2026-07-02
> (código de `core/`+`adapters/`, plantillas, skills, dogfooding; bugs A-1..A-3
> reproducidos por ejecución en sandbox). Cada ítem tiene ID estable para
> referenciarlo desde specs y commits.

## Cómo leer las prioridades

| Prioridad | Criterio |
|-----------|----------|
| **P0** | El kit se contradice a sí mismo o el happy path de un usuario nuevo está roto. Bloquea la credibilidad del producto. |
| **P1** | Bug real o hueco de enforcement que un usuario va a pisar en las primeras semanas de uso. |
| **P2** | Deuda de diseño/duplicación que va a divergir con el tiempo; conviene pagarla antes de que crezca. |
| **P3** | Mejora de producto/pulido; deseable, no urgente. |

Agrupación sugerida en specs (una spec por iteración, en este orden):

1. **SPEC-002 — Dogfooding íntegro** → D-1, D-2, D-3, D-4 (P0).
2. **SPEC-003 — Happy path de instalación** → B-1, B-2, B-3, E-1 (P0/P1).
3. **SPEC-004 — Endurecer el gate y la trazabilidad** → G-1..G-5 (P1).
4. **SPEC-005 — Desduplicar SSOTs del kit** → R-1, R-2, R-3 (P2).
5. **SPEC-006 — Distribución y ciclo de vida** → E-2, E-3, E-4 (P2/P3).
6. **SPEC-007 — Onboarding del proyecto derivado** → E-1, E-7 (P2/P3).

---

## P0 — Dogfooding roto (el kit no cumple su propio protocolo)

> **(ya con spec) → [[SPEC-002-dogfooding-integro]]** — D-1..D-4 implementados
> el 2026-07-02 (pipeline 7/7 VERDE, doctor sano, 37 tests, SPEC-001 active).

- **D-1 · Cablear el gate spec-first en el propio kit.** El repo no tiene
  `.claude/settings.json`, `.pre-commit-config.yaml` ni `.sdd/current-spec`:
  el Principio III de la propia `CONSTITUTION.md` está declarado pero sin
  enforcement real (hoy se puede editar `core/` sin spec y nada bloquea).
  `sdd-doctor` sobre el kit sale con exit 1 y 4 problemas.
- **D-2 · Primeros tests del kit.** `AGENTS.md` exige "todo cambio de
  comportamiento requiere test en `tests/unit/`" y no existe ni un test.
  Sembrar `tests/unit/` cubriendo al menos `sdd_gate.decide`,
  `check_traceability`, `check_naming` y `sdd_config` (todo es lógica pura,
  fácil de testear), y agregar `tests` + `lint` a `pipeline.steps` del kit.
- **D-3 · Resolver `00-INDEX.md` del kit.** `sdd_doctor.py` lo exige
  incondicionalmente mientras `AGENTS.md` del kit dice que el README hace de
  índice. O el doctor parametriza sus artefactos requeridos (config), o el kit
  crea su propio índice. Hoy es imposible que el kit esté "sano" según su
  propia herramienta.
- **D-4 · Promover SPEC-001 a formato híbrido y estado `active`.** Todo el
  núcleo implementado vive bajo una spec `draft`/`casero` sin FRs ni Coverage
  mapping — el ciclo de vida que `docs/SPEC-FORMAT.md` documenta no se cumplió
  en el propio kit. Depende de D-2 (necesita tests que mapear).

## P0/P1 — Happy path de instalación roto (bugs reproducidos)

> **(ya con spec) → [[SPEC-003-install-happy-path]]** — B-1..B-4 implementados
> el 2026-07-02 (instalación fresca → VERDE, relax operativo, registro íntegro).

- **B-1 · `naming` falla en un proyecto recién instalado.**
  `adapters/python/adapter.py::step_naming` con cero targets existentes invoca
  `check_naming.py` sin argumentos → exit 2. Un proyecto sin código todavía
  (el estado exacto post-init) arranca en ROJO. Fix: si no hay targets,
  imprimir aviso y devolver 0.
- **B-2 · `relax_in_tests` nunca aplica con el layout por defecto.**
  `check_naming.py` relaja solo si `root.name in {"tests","test"}`, pero el
  adaptador pasa `tests/unit` (name = `unit`). Reproducido: `csv` relajado en
  config sigue reportando violación en `tests/unit/`. Fix: comparar contra los
  dirs de tests del config (o contra cualquier parte del path), no contra el
  basename.
- **B-3 · Pipeline sembrado asume toolchain no declarada.** El config de
  ejemplo declara los 10 pasos, pero ruff/mypy/bandit/pytest/import-linter no
  están instalados ni declarados (README promete "solo Python + pyyaml").
  Instalación fresca → ROJO 6/10, contradiciendo el historial ("install demo →
  VERDE"). Opciones: sembrar `pipeline.steps` mínimo (proceso + naming) y que
  `sdd-configure` ofrezca los pasos de tooling, o detectar tools ausentes y
  omitir con aviso (como hace `language: none`).
- **B-4 · `sdd_spec.py` rompe el registro instalado.** Agrega la fila al final
  del **archivo**, no de la tabla: con el registro plantilla (que tiene
  `## Roadmap` después de la tabla) la fila queda huérfana bajo el roadmap.
  Reproducido en sandbox. Fix: insertar la fila al final de la tabla de
  `## Specs vigentes` (buscar la última línea `|` contigua al header).

## P1 — Huecos de enforcement del gate y la trazabilidad

- **G-1 · Pre-commit hardcodea `files: '^(src|app|lib)/'`.**
  **(ya con spec) → [[SPEC-015-wiring-apunta-al-codigo-real]]** — implementado
  el 2026-08-05. Resultó más ancho de lo registrado: eran **tres** capas
  pre-filtrando por `src/`, no una (el `files:` de pre-commit, la rama
  fail-closed de `sdd_gate_hook.sh` y `isUnderSrc`/`resolveSrcPath` del plugin
  de opencode). En pre-commit el pre-filtro se eliminó (el gate ya decide); en
  las otras dos —que corren cuando Python no está disponible y no pueden
  consultar al gate— se derivan los roots de `.sdd/config.yaml` con un parseo
  mínimo por capa, atado a un test de paridad contra `SddConfig.source_roots`.
- **G-2 · El gate no verifica el estado de la spec.**
  **(ya con spec) → [[SPEC-006-gate-verifica-estado-spec]]** — implementado
  el 2026-08-01. `_spec_is_valid` hacía substring match de `spec_id` sobre el
  texto del registro: una spec `archived`/`superseded` (o mencionada en
  prosa del roadmap) desbloqueaba el gate igual que una `active`. Fix:
  parsea la fila (reusa `check_traceability._parse_registry`) y exige estado
  `draft`/`active`.
- **G-3 · Matcher del hook de Claude solo cubre `Edit|Write`.**
  **(ya con spec) → [[SPEC-015-wiring-apunta-al-codigo-real]]** — implementado
  el 2026-08-05: matcher `Edit|Write|MultiEdit|NotebookEdit` y el bypass por
  `Bash` documentado como límite conocido (corrimiento de capa: lo agarra
  pre-commit al commitear).
- **G-4 · `sdd-doctor` valida existencia, no contenido, del wiring.** Un
  `.claude/settings.json` cualquiera cuenta como "gate cableado". Fix: buscar
  la invocación de `sdd_gate.py` dentro del archivo.
  **(ya con spec) → [[SPEC-014-derivado-dice-la-verdad]]** FR-US1-002, con
  U-4..U-11.
- **G-5 · Criterio mtime del gate sin documentar ni escape hatch.**
  `git checkout`/`clone` renuevan mtimes y pueden des/bloquear espuriamente.
  Documentarlo como heurística en SDD-ENFORCEMENT y considerar una alternativa
  (hash de la spec registrado en `.sdd/current-spec`).
  **(resuelto) → [[SPEC-017-gate-decision-spec-first]]**, que va más lejos que lo
  planteado acá: el disparador fue el ciclo stash/restore del propio `pre-commit`
  (no solo `checkout`/`clone`), y el diagnóstico mostró que la mtime tampoco
  aportaba garantía —un `touch` la satisfacía—. Se eliminó el criterio en vez de
  documentarlo: el gate exige que la spec declarada tenga FR escritos. El hash en
  `.sdd/current-spec` se evaluó y descartó (mismo defecto en el flujo de varios
  commits por spec). Escape hatch: `SDD_GATE_BYPASS`.
- **G-6 · `check_traceability` no exige keyword en los FR.** SPEC-FORMAT
  declara obligatorio `MUST:/SHOULD:/MAY:` pero nada lo verifica. Chequeo de
  una línea; alinear doc y check en cualquier dirección.
- **G-7 · `sdd_spec.py` sobrescribe `.sdd/current-spec` completo.**
  Parcialmente resuelto → [[SPEC-004-enforcement-hardening]] FR-007
  (2026-08-01): ahora preserva el header de comentarios (el síntoma que
  dejaba el working tree sucio tras cada commit, vía `sdd_reset.py`). Sigue
  pendiente la semántica multi-spec en sí: crear una segunda spec todavía
  des-declara la primera sin aviso — falta definir append vs replace (con
  flag).
- **G-8 · `check_traceability` no verifica que los tests referencien el FR
  que dicen cubrir.** El Coverage mapping de una spec `hibrido` declara
  FR-NNN → archivo de test, pero nada valida que ese ID aparezca en el código
  o docstring del test (hoy alcanza con que el archivo exista). Extender
  `check_traceability.py` para grepear el ID del FR (`FR-NNN`) dentro del
  archivo de test mapeado en `tests/unit/`, y fallar si no aparece —
  trazabilidad requisito↔test auditable por máquina, no solo por convención.
- **G-9 · El reset post-commit de `.sdd/current-spec` nunca queda commiteado
  — el working tree SIEMPRE sale sucio tras un commit con spec declarada.**
  `core/sdd_reset.py` (hook `post-commit`, SPEC-004 FR-002) edita el archivo
  para dejar solo el header, pero no hace ningún `git add`/commit de ese
  cambio — es un hook post-commit, corre *después* de que el commit ya
  cerró. El criterio de aceptación de SPEC-004 dice textualmente "el working
  tree no queda sucio después del commit", pero el test que lo cubre
  (`test_ciclo_declarar_luego_reset_deja_solo_el_header`) solo verifica el
  *contenido* del archivo tras `sdd_reset.main()`, nunca el ciclo real con
  `git commit` de por medio — por eso el hueco pasó dos rondas de SPEC-004 sin
  detectarse. Reproducido en vivo durante SPEC-007 (2026-08-02): tras cerrar
  la spec, `git status` mostraba `.sdd/current-spec` modificado. Ya había
  pasado antes: el commit `1bc4881 "Restaura header de comentarios perdido"`
  de la sesión 2026-08-01 fue un commit manual de limpieza para el mismo
  síntoma. Opciones a evaluar: (a) que el hook post-commit haga su propio
  commit del reset (riesgo de encadenar/recursar hooks), (b) documentar el
  comportamiento como esperado y sumar el `git add .sdd/current-spec` al
  playbook de cierre de iteración, (c) repensar el mecanismo para no
  depender de tocar un archivo fuera del commit que lo origina.

## P2 — Duplicación de SSOT dentro del kit

> **(ya con spec) → [[SPEC-005-desduplicar-ssot]]** — R-1, R-2, R-3
> implementados el 2026-08-01 (pipeline 9/9 VERDE, doctor sano, 62 tests).

- **R-1 · `docs/` del kit duplica `templates/docs/` byte a byte.**
  `SDD-ENFORCEMENT.md` y los playbooks `analyze`/`clarify` existen dos veces y
  van a divergir en la primera edición — exactamente lo que "No duplicar SSOT"
  prohíbe. Opciones: que los docs del kit se generen desde templates (render
  con placeholders resueltos), o un check de sincronía en el pipeline (como el
  de skills).
- **R-2 · El template de spec existe dos veces.**
  `templates/specs/SPEC-TEMPLATE.md` (el que consume `sdd_spec.py`) y el
  bloque "Template copiable" de `docs/SPEC-FORMAT.md`. Dejar en SPEC-FORMAT
  una referencia al archivo.
- **R-3 · Defaults dispersos.** `"tests/unit"` repetido en `adapter.py`;
  `["src"]` como default en `sdd_config.py` y `sdd_gate.py`. Centralizar en
  `sdd_config`.

## P2 — Hallazgos de la implementación de SPEC-015 (2026-08-05)

- **R-4 · El wiring del kit es una copia manual de `templates/wiring/`.**
  `.pre-commit-config.yaml`, `.claude/settings.json` y `.claude/sdd_gate_hook.sh`
  del propio kit son copias de sus plantillas que difieren *solo* en el prefijo
  de rutas (`core/` vs `tools/sdd/core/`), pero nada las mantiene sincronizadas:
  cada arreglo del wiring hay que aplicarlo dos veces y el drift no lo detecta
  nadie. Es R-1 en otra superficie, y ya se pagó en SPEC-004 (FR-004 tuvo que
  tocar el par) y en SPEC-015 (tres pares). Fix: convertir las rutas literales
  de `templates/wiring/` en `{{sdd.core}}` y sumar los destinos a
  `_SYNCED_FROM_TEMPLATES` de `render.py`, que ya resuelve el placeholder para
  el kit y para el derivado. Lo caro es que `render.py` hoy sincroniza solo
  `.md`; habría que aceptar `.sh`/`.json`/`.yaml` respetando LF.
- **C-7 · `sdd_init.py` ignora en silencio los flags que no conoce, y el target
  es posicional.** `python core/sdd_init.py --target=/otro/lado --language=python`
  no instala en `/otro/lado`: instala en el **cwd**, porque `main` descarta todo
  lo que empieza con `--` y toma el target del primer argumento posicional.
  Reproducido en vivo durante SPEC-015: la corrida se instaló sobre el propio
  kit y hubo que limpiar a mano los artefactos que sembró (`tools/`,
  `.opencode/plugin/`, cinco `docs/*.md`). Misma clase que C-3 (`--language`
  frágil) pero con consecuencia peor: escribe archivos en el directorio
  equivocado sin una sola advertencia. Fix: validar los flags contra los
  conocidos y fallar con mensaje de uso ante cualquier otro.

## P1 — Hallazgos de la primera corrida de la suite e2e (2026-08-07)

Los tres salieron de escribir los escenarios de [[SPEC-018-verificacion-e2e]]:
ninguno lo veía la suite unitaria.

Los tres quedaron **resueltos el 2026-08-07**, en la misma iteración que los
encontró.

- **V-1 · `tests_integration` estaba cableada a medias.** Resuelto por
  [[SPEC-019-tests-integracion-ejecutados]]. Era clave de primera clase del config
  (`sdd_config.py`, `render.py:184`, los dos prefiltros de wiring) y figuraba en
  `examples/config/config.yaml`, pero `sdd-init` nunca la sembraba y **ningún paso
  la ejecutaba**: `step_tests` usaba solo `tests_unit`. El síntoma no era "esos
  tests no corren" sino que corrían **en el paso equivocado o en ninguno**, según
  una clave sin relación con ellos: con `pipeline.coverage` declarado,
  `step_coverage` los arrastraba —pasa todas las carpetas de test a pytest—, así
  que un test de integración roto pintaba `coverage` en rojo y se ejecutaba una
  vez por umbral; sin umbrales, no se ejecutaba nunca. Se cerró con un paso
  `integration` propio (el contrato define `tests` como suite unitaria, y fundirlos
  habría impuesto un ciclo único a todos los derivados) más el aviso de
  `sdd-doctor` cuando una carpeta declarada no la corre ningún paso.
- **V-2 · El aviso de `SDD_GATE_BYPASS` no le llegaba al operador.** Resuelto por
  [[SPEC-017-gate-decision-spec-first]] FR-US3-007. El gate imprime en stderr el
  motivo del bypass y el bloqueo que se saltea (FR-US3-004), pero en el flujo real
  corre como hook de `pre-commit`, que **descarta la salida de los hooks que
  pasan** y solo muestra `Passed` — justo el caso del bypass, donde el gate sale 0.
  La garantía existía a nivel unitario y se evaporaba de punta a punta. Se cerró
  con `verbose: true` en el hook `sdd-gate` de las dos copias del wiring, que no
  agrega ruido porque el gate no escribe nada cuando no hay nada que bloquear.
- **V-3 · Cambiar `project.domain` después de instalar no propagaba a ningún
  lado.** Resuelto por [[SPEC-014-derivado-dice-la-verdad]] FR-US2-006. `AGENTS.md`
  recibía el dominio por sustitución de `{{project.domain}}` **en la instalación**;
  `render.py` no lo regenera (en el derivado no hay `templates/`) y ningún
  artefacto derivado lo reflejaba. Se cerró eliminando la copia en vez de
  sincronizarla: el dominio lo declara `CONSTITUTION.md`, que sí es generado y sí
  lo vigila `render --check`; `AGENTS.md` y el `README.md` de plantilla remiten.
- **V-4 · La raíz de `tests/` no la mira ningún paso** (encontrado el 2026-08-09
  al implementar K-4, **abierto**). Las claves de `dirs` apuntan a subcarpetas
  (`tests_unit`, `tests_integration`, `tests_e2e`), así que la infraestructura
  compartida que vive en la raíz —`tests/conftest.py`,
  `tests/fixtures_proyecto.py`— queda fuera de `naming`/`lint`/`format`.
  `conftest.py` no lo lintaba nadie; `fixtures_proyecto.py` solo lo salvaba un
  paso a mano del workflow e2e. Es la familia de V-1: una carpeta que existe y
  ningún paso mira. Ojo con el fix fácil: declarar `tests/` a secas la solaparía
  con sus propias subcarpetas y los pasos las visitarían dos veces. Opciones:
  una clave `tests_root` que solo alimente los pasos estáticos, o que los pasos
  estáticos deriven la raíz común de las carpetas declaradas.

## P2 — Bugs y asperezas menores de código

- **C-1 · Paso desconocido cuenta como OK.** Resuelto de paso el 2026-08-05 al
  implementar [[SPEC-003-install-happy-path]] FR-009: el `continue` de un step no
  reconocido ahora decrementa `total`, igual que una omisión. Queda pendiente
  solo la parte de doc: `gate` no es paso de pipeline (decisión ya tomada en el
  historial) y el config de ejemplo y la doc de `adapter.py` lo insinúan.
- **C-2 · Mojibake en Windows.** `pipeline.py`, `sdd_doctor.py` y
  `sdd_init.py` imprimen `VERDE �` porque no hacen el
  `reconfigure(encoding="utf-8")` que sí hacen los `check_*`. Extraer un
  helper común en `sdd_config` y usarlo en todos los entrypoints.
- **C-3 · `sdd_init --language` frágil.** La forma `--language node` (espacio)
  se ignora en silencio; con `=` un lenguaje sin adaptador se acepta y el
  vendorizado se omite sin aviso. Validar contra los adaptadores existentes +
  `none` y fallar con mensaje claro.
- **C-4 · `_slugify` no translitera acentos** (`búsqueda` → `b-squeda`).
  Normalizar con NFKD antes de filtrar.
- **C-5 · Constitución con versión hardcodeada.** `render.py` fija `0.1.0` y
  fecha del día: la governance promete semver de enmiendas pero no hay campo
  en el config para bumpear. Agregar `constitution_version` (y fecha de
  ratificación) al config.
- **C-6 · Vestigios.** `_module_of(repo_root, …)` con parámetro sin usar
  (`gen_import_linter.py`); `_ = src` en `sdd_init._install_project_skills`;
  estado `notas` en `VALID_ESTADOS` sin convención documentada (¿vestigio del
  proyecto de referencia? decidir: documentar o eliminar).
- **C-8 · Los pasos de código están declarados dos veces.** `pipeline.CODE_STEPS`
  y el dispatcher `STEPS` del adaptador enumeran lo mismo por separado, y no hay
  nada que los ate: al agregar `integration` (SPEC-019) el paso quedó implementado
  y el pipeline lo reportó "paso desconocido", descontándolo del total sin ruido
  —la familia de C-1—. Lo tapa `tests/unit/test_adapter_integration.py`, que cruza
  las dos listas, pero la duplicación sigue. Fix: que el pipeline pregunte al
  adaptador qué pasos soporta, o que la lista salga de un SSOT en `sdd_config.py`.
  Ojo con el agnosticismo: `PROCESS_STEPS` es del núcleo y `CODE_STEPS` del
  lenguaje, así que no es un simple merge.
  **(cerrado el 2026-08-09)** → [[SPEC-005-desduplicar-ssot]] FR-006/FR-007.
  La premisa del "no es un simple merge" resultó ser el error: `CODE_STEPS` **no**
  es del lenguaje, es del contrato (`adapters/CONTRACT.md`) —lo que aporta el
  lenguaje es la implementación de cada paso—, así que vive en `sdd_config.py` y
  el pipeline lo importa. Preguntarle al adaptador se descartó: gasta un
  subproceso por corrida y vuelve el vocabulario dependiente del adaptador
  instalado. Apareció una duplicación hermana que la idea no registraba: la tupla
  `("tests_unit", "tests_integration")` repetida en cuatro módulos, que tapaba que
  los cuatro hacen preguntas **distintas** sobre la misma carpeta —por eso agregar
  una clase de test nueva no era un renglón—. Ahora `TEST_DIRS` declara la
  carpeta con sus propiedades y cada consumidor filtra por la suya.

## P2/P3 — Producto y distribución

> **(ya con spec) → [[SPEC-007-derived-project-onboarding]]** — E-1, E-7
> implementados el 2026-08-02 (pipeline 9/9 VERDE, doctor sano, 77 tests,
> instalación fresca verificada en `/tmp`).

- **E-1 · El proyecto instalado no recibe las skills `sdd-*`.** `sdd-init`
  instala solo `analyze`/`clarify`, pero README y playbooks instruyen "corré
  `sdd-configure`" / "usá `sdd-spec`" — que solo existen en el repo del kit.
  Instalar también `sdd-spec`, `sdd-doctor` y `sdd-configure` (con sus
  playbooks) en el destino, o reescribir la doc para que el flujo instalado
  sea vía CLI vendorizada.
  **(ya con spec) → [[SPEC-007-derived-project-onboarding]]** para las fuentes y
  **[[SPEC-016-skills-listas-tras-init]]** para lo que faltaba: copiar
  `.agents/skills/` no alcanzaba: sin los adaptadores generados
  (`.claude/skills/`, `.opencode/command/`), Claude Code y opencode seguían sin
  ver ninguna skill hasta que alguien corriera `gen_skill_adapters.py` a mano —
  el paso 3 del onboarding, dos pasos *después* de que el instalador recomendara
  usar `sdd-configure`. Resuelto sembrándolos desde `sdd-init`.
- **E-2 · Ruta de actualización del kit vendorizado.** `sdd-doctor` lee
  `kit_version` pero no la compara contra nada; actualizar `tools/sdd/` es
  `--force` manual sin diff. Diseñar `sdd-update` (comparar versión, mostrar
  qué cambia, regenerar).
- **E-3 · Packaging mínimo.** No hay `pyproject.toml`/`requirements` (pyyaml
  solo en prosa), no hay LICENSE (bloqueante para un kit que se copia en
  proyectos ajenos), no hay CI que corra el pipeline del kit.
- **E-4 · Enforcement de principios custom.** `ENFORCEMENT_STEP` en
  `check_constitution.py` es un mapa hardcodeado tool→paso: un enforcement
  propio (`mi_check.py`) no obtiene verificación de cableado ni error. Mover
  el mapeo al config (`enforcement: {tool, step}`).
  **(ya con spec) → [[SPEC-020-enforcement-declarado-en-config]]** — implementado
  el 2026-08-08. La forma final fue una clave `step` **por principio**, no un mapa
  de nivel superior (el principio es la unidad; un mapa aparte duplicaba SSOT
  dentro del config). Lo promovió K-3: al ir a declarar el principio de cobertura
  se vio que no obtendría verificación, y un enforcement decorativo en la
  constitución del propio kit era inaceptable. Se aprovechó el viaje para pagar la
  primera cuota de K-3: `check_constitution.py` de 0% a 99%.
- **E-5 · Ajustes de doc del README.** El claim de skills para "Cursor…" no
  tiene soporte real (hoy: `.agents/` + Claude + opencode); precisar. Aclarar
  qué tooling requieren los pasos de código del adaptador python.
- **E-6 · `templates/AGENTS.md` referencia rutas inexistentes en el destino**
  ("`python core/pipeline.py` (o el wrapper `tools/pipeline`)"): en un
  proyecto instalado es `tools/sdd/core/pipeline.py` y el wrapper no existe.
  Corregir la plantilla.
- **E-7 · El proyecto derivado no recibe un README humano ni un manual de
  skills.** `sdd_init.py` no instalaba ningún `README.md` (no estaba en
  `STATIC_DOCS`), pese a que `templates/AGENTS.md` ya asume su existencia
  ("no dupliques información entre `docs/`, `specs/` y README"). Resuelto:
  `templates/README.md` (solo producto derivado, sin explicar SDD) +
  `templates/docs/SDD-OPERACION.md` (catálogo humano de las skills SDD
  instaladas) sumados a `STATIC_DOCS`.

## P1 — Hallazgos de la segunda comparación con el proyecto de referencia

> Revisión del 2026-08-04 sobre `evaluador-flujo-intent`. Decisión tomada: los
> dos proyectos siguen **independientes** (migrar el evaluador al kit implicaría
> rehacer su andamiaje y no es el espíritu del SDD); lo que se porta es el
> *mecanismo*, generalizado. Comparando línea a línea, el núcleo del kit está
> **adelante** del evaluador en casi todo (`check_constitution` verifica contra
> `pipeline.steps` en vez de hardcodear `PIPELINE_TOOLS`; `sdd_gate`/`sdd_reset`
> centralizan `find_repo_root`); lo que faltaba era otra cosa.

- **F-1 · Umbrales de cobertura como paso del pipeline.**
  **(ya con spec) → [[SPEC-009-coverage-y-ci]]** — el evaluador exige `>=80%`
  global y `>=96%` en el dominio; el adaptador Python del kit no tenía paso
  `coverage`. Implementado como lista opcional `pipeline.coverage`
  (`[{paths, min}]`): ausente ⇒ se omite con aviso.
- **F-2 · Sin CI, ni propia ni instalable.**
  **(ya con spec) → [[SPEC-009-coverage-y-ci]]** — deuda E-3 parcial. Resuelto
  generando `.github/workflows/ci.yml` desde el config: los `paths:` derivan de
  `dirs.source_roots` y el job invoca el pipeline en vez de repetir los pasos.
  Nota de diseño: el evaluador **sí** duplica la lista y sus dos copias ya
  divergieron (11 pasos en `pipeline_local.sh` vs 10 en `ci.yml`, sin `hooks`
  ni `skills`); el kit evita ese drift por construcción.
- **F-3 · `gen_skill_adapters.py` sin ninguna documentación.**
  **(ya con spec) → [[SPEC-010-gobernanza-y-docs]]** — el mecanismo existía y
  estaba en el pipeline, pero quien recibía el kit veía carpetas con
  "NO EDITAR A MANO" y no sabía qué las generaba. Portado y generalizado desde
  `docs/SKILLS-MULTITOOL.md` del evaluador.
- **F-4 · La constitución generada era mucho más pobre que la de referencia.**
  **(ya con spec) → [[SPEC-010-gobernanza-y-docs]]** — faltaban el preámbulo
  (qué es / cómo se usa / alcance) y una Governance real (semver desglosado,
  procedimiento de enmienda). Arrastraba C-5: la versión estaba hardcodeada en
  `render.py`, así que el procedimiento de enmienda no tenía dónde bumpear.
  Resuelto con la sección `constitution` del config.
- **F-5 · E-6 era más ancho de lo registrado.**
  **(ya con spec) → [[SPEC-010-gobernanza-y-docs]]** — no era solo
  `templates/AGENTS.md`: ocho plantillas citaban `core/...`, que en un proyecto
  instalado es `tools/sdd/core/...`. Resuelto con placeholders `{{sdd.core}}` /
  `{{sdd.adapters}}` que `render.py` resuelve para el kit y `sdd_init.py` para
  el destino, más un test parametrizado que barre `templates/`.
- **F-6 · `.gitattributes` no forzaba LF en los `.sh` — el gate queda roto en
  un checkout de Windows.** `sh` no ejecuta un script con CRLF: falla con
  `\n: not found` y `Syntax error: word unexpected`, así que
  `.claude/sdd_gate_hook.sh` devuelve 2 para *todo* (incluido lo que debería
  permitir) o, peor, el hook se cuelga como fail-closed permanente. Se detectó
  porque los 4 tests de `test_sdd_gate_hook.py` fallaban en el clon actual.
  Corregido en `.gitattributes` (kit y plantilla), pero **el working tree ya
  convertido necesita renormalizarse a mano** (`git add --renormalize .`); la
  regla nueva solo evita que vuelva a pasar.
- **F-7 · Módulos del núcleo con 0% de cobertura.** Medido al fijar los
  umbrales de F-1: `check_constitution.py`, `gen_skill_adapters.py` y
  `sdd_doctor.py` no tienen ni un test directo (total del kit: 52%). El umbral
  se fijó en el piso actual como trinquete; subirlo requiere cubrirlos.

## P1/P2 — Hallazgos de la campaña de usabilidad del proyecto derivado

Del recorrido completo del README sobre proyectos testigo (2026-08-05): un
greenfield vacío y un proyecto Python con código previo en `app/`. Evidencia y
detalle de cada hallazgo en el informe de la campaña, fuera del repo. Lo que ya
se cerró: **U-1..U-3 → [[SPEC-003-install-happy-path]]** (reabierta) y
**U-4..U-11 + G-4 → [[SPEC-014-derivado-dice-la-verdad]]** (la otra mitad del
mismo problema: un derivado que reporta salud sin haberla medido, y que habla en
términos del kit en vez de los propios). Se tomaron en bloque en una sola spec
porque repartirlos entre specs viejas fragmentaba el invariante.

- **U-1 · El config sembrado heredaba el layout del proyecto de referencia**
  (`src/domain`, `tests/unit`), así que en cualquier otro layout `naming` y
  `tests` se omitían y el gate no protegía nada. *(ya con spec)*
- **U-2 · El README no nombraba `dirs`/`source_roots`** entre lo configurable,
  que es lo único que hace que el gate y los checks apunten al código. *(ya con
  spec)*
- **U-3 · Un paso omitido se contaba como paso OK** (`VERDE 8/8` con 4 pasos que
  no verificaron nada). *(ya con spec)*
- **U-4 · `sdd-init` conserva en silencio el wiring propio del proyecto.** Con
  un `.pre-commit-config.yaml` y un `.claude/settings.json` preexistentes, no
  queda ninguna capa de gate cableada y nadie avisa: la línea
  `(existe, se conserva)` se pierde entre 30 líneas de log. Verificado con un
  commit sobre `src/` que el gate debió bloquear y no bloqueó. *(ya con spec)*
- **U-5 · El mensaje de drift del doctor nombra artefactos fijos.** Dice
  "CONSTITUTION.md/SPEC-000 desincronizados" aunque lo que drifteó sea
  `ci.yml`. *(ya con spec)*
- **U-6 · `.sdd/current-spec` se instala con el placeholder `{{sdd.core}}` sin
  sustituir**: `_copy_text` sustituye por extensión y ese archivo no tiene. Es
  el primer archivo que se abre para entender el gate, y el test de rutas
  colgadas de SPEC-013 FR-004 no lo veía por el mismo motivo. *(ya con spec)*
- **U-7 · Los mensajes de drift citan rutas del kit** (`corre: python
  core/render.py`), inexistentes en un derivado, donde es `tools/sdd/core/`.
  Misma clase que SPEC-010 FR-007, en superficie de runtime. *(ya con spec)*
- **U-8 · El config sembrado conserva la cabecera del ejemplo**, que dice
  "copialo a `.sdd/config.yaml`" cuando ya *es* ese archivo, y nombra al
  proyecto de referencia. *(ya con spec)*
- **U-9 · El CI generado hardcodea `branches: [main]`.** Un proyecto en
  `master` o `develop` recibe un workflow que nunca dispara, mientras los
  `paths:` sí derivan del config. *(ya con spec)*
- **U-10 · El gate falla *abierto* si el `cwd` del payload no resuelve a una
  raíz con marcadores SDD**: `find_repo_root` devuelve ese directorio y la
  edición se permite en silencio. El wrapper de Claude está diseñado
  fail-closed; el núcleo detrás, no. *(ya con spec)*
- **U-11 · La salida de instalación no nombra ningún documento para leer.**
  `00-INDEX.md` es un buen índice y está instalado, pero nada invita a abrirlo;
  en un brownfield cuyo README propio se conservó, no había puerta de entrada. *(ya con spec)*

Ítems ya registrados que la campaña **reprodujo en un proyecto real**, con la
evidencia que les faltaba:

- **G-1** (pre-filtro `files:` hardcodeado): confirmado con `pkg/x.py`, que no
  matchea `^(src|app|lib)/` y nunca llega al gate. La rama fail-closed del hook
  de Claude tiene la misma limitación (su `case` solo cubre `src/`). El núcleo
  del gate sí lee `source_roots` correctamente.
- **G-4** (doctor valida existencia, no contenido): confirmado — reporta
  "Instalación SDD sana" sobre un `.pre-commit-config.yaml` con solo `ruff`. *(ya con spec)*
- **C-2** (mojibake en Windows): confirmado por bytes; con la salida redirigida
  `sys.stdout.encoding` es `cp1252` y el texto **no es UTF-8 válido**. Afecta al
  aviso clave de `sdd_spec.py` ("Editá la spec… ANTES de tocar código").
- **E-2** (ruta de actualización del kit vendorizado): confirmado que ningún
  documento del derivado lo explica, aunque `SDD-OPERACION` hable de "después de
  actualizar el kit".

## P1/P2 — Reevaluación kit vs derivado (2026-08-08)

> Salió de comparar el SDD del propio kit contra el que siembra `sdd-init`, y
> después filtrar esa lista con la premisa correcta: **el kit casi no tiene
> código de producto** (todo lo que tiene es código de palanca que se ejecuta
> dentro de N proyectos ajenos), mientras que el derivado **sí** es un proyecto
> de IT con desarrollo real. Con eso, la simetría kit↔derivado deja de ser el
> criterio: valen solo dos preguntas — *¿lo que el kit genera es correcto?* y
> *¿el derivado se sostiene solo, sin el clon del kit al lado?*
>
> Asimetrías que el filtro **descartó** como legítimas, para no volver a
> levantarlas: `tools/sdd/` fuera del gate del derivado (es infra vendorizada,
> no su producto); que el kit no tenga `ARCHITECTURE.md`/`SPEC-FORMAT.md` propios
> (no tiene capas ni producto, y su `00-INDEX` referencia el SSOT en
> `templates/`); que el kit no corra el paso `layers` (un contrato de capas sobre
> `core/`+`adapters/` sería ceremonial); principios mínimos sembrados, exenciones
> de `naming` y `AGENTS.md` divergente (todos son "el derivado elige lo suyo").

- **K-1 · El derivado nace sin el paso `render`, así que nada vigila el drift de
  lo generado.** `_SEEDED_STEPS` (`core/sdd_init.py`) no lo incluye; el kit sí lo
  corre. En un derivado `render --check` compara tres artefactos (`_GENERATED`,
  `render.py:256`): `CONSTITUTION.md`, `specs/SPEC-000-naming.md` y
  `.github/workflows/ci.yml` — el bloque `_SYNCED_FROM_TEMPLATES` es no-op ahí
  (no hay `templates/`). No lo cubre ningún otro paso: `check_constitution.py`
  parsea el **documento** y valida que sus referencias y su enforcement estén
  cableados, pero **nunca lo compara contra `principles:` del config**, así que
  el paso `constitution` sale verde sobre una constitución obsoleta. Hoy el único
  que ve el drift es `sdd-doctor`, que se corre a mano. Tres daños concretos:
  (a) `SPEC-000` es lo que lee el agente (paso 5 de `AGENTS.md`) mientras
  `check_naming.py` enforcea desde el config — divergen y el asistente sigue
  reglas que el linter ya no aplica; (b) la constitución queda congelada; (c) el
  `ci.yml` se genera desde `pipeline.steps` y `default_branch`, así que habilitar
  un paso deja **verde local ≠ verde en CI**, silencioso y cross-máquina. Fix:
  una línea en `_SEEDED_STEPS`, entre `skills` y `tests`. Es seguro: `--check`
  es lectura pura, stdlib, sin tooling (por eso va en la lista sembrada y no en
  `_OPTIONAL_STEPS`, cuyo criterio es "requiere tooling del proyecto"), y no
  introduce precondición nueva — el paso `constitution` ya exige haber corrido
  `render` (paso 2 de `_next_steps`, y así lo hace la e2e en
  `tests/e2e/conftest.py`). Encaja como FR de [[SPEC-014-derivado-dice-la-verdad]]:
  un derivado no puede afirmar que su constitución es la vigente si nada lo
  verifica.
  **(cerrado el 2026-08-09)** → [[SPEC-014-derivado-dice-la-verdad]] FR-US1-005,
  tal cual estaba planteado: una línea en `_SEEDED_STEPS`, entre `skills` y
  `tests`. Se descartó la alternativa de que `check_constitution.py` comparara
  contra `principles:` — sería una segunda implementación del criterio que
  `render --check` ya tiene, divergente por construcción (Principio IV).
- **K-2 · El catálogo de claves del config no viaja con el derivado.** La
  cabecera que siembra `_seed_header` remite a `examples/config/config.yaml`
  "en el kit" — un archivo que el derivado no tiene. Bajo la premisa vieja daba
  igual (siempre había un clon a mano); bajo la nueva, no: quien mantiene el
  derivado nunca ve el kit, y `.sdd/config.yaml` es justo el archivo que más va
  a editar. Fix: instalar el catálogo como `docs/CONFIG-REFERENCE.md` (o
  `.sdd/config.example.yaml`) y que la cabecera apunte ahí. Emparejado con K-6:
  si el kit es desechable, su documentación de referencia tiene que viajar.
  **(cerrado el 2026-08-09)** → [[SPEC-013-proyecto-derivado-coherente]] FR-008..010.
  Ninguna de las dos formas propuestas: se instala el **YAML verbatim** como
  `.sdd/config.reference.yaml`. Un `docs/CONFIG-REFERENCE.md` en prosa habría sido
  una segunda descripción de las mismas claves (Principio IV), y `config.example`
  invita a copiarlo, que es justo la instrucción que SPEC-014 FR-US2-004 sacó de
  la cabecera. De paso destapó por qué FR-004 estaba verde con esta referencia
  rota desde siempre: el test de rutas colgadas miraba solo los `.md` instalados,
  no `.sdd/config.yaml`.
- **K-3 · La cobertura del kit está mal calibrada — y es el punto de mayor
  palanca.** Medido el 2026-08-08: total **75%** contra un umbral declarado de
  **50** (el trinquete quedó 25 puntos por debajo del piso real y no protege
  nada), y el comentario del config que justifica ese 50 nombra módulos que hoy
  están en 74% y 85%. Lo grave es la distribución: `check_constitution.py` sigue
  en **0%** (97 stmts) siendo un gate que se ejecuta en **cada** proyecto
  instalado; después `sdd_spec.py` 44%, `adapters/python/adapter.py` 51%,
  `check_naming.py` 59%, `bootstrap_hooks.py` 59%, `gen_import_linter.py` 69%.
  Si el kit casi no tiene código propio, cada línea que sí tiene está
  multiplicada por N: el kit debe exigirse **más** que lo que reparte, no menos.
  **Objetivo: 90%** sobre `core`+`adapters`. Son ~247 stmts a cubrir sobre los
  409 sin cubrir hoy; conviene subir el umbral por escalones (75 → 85 → 90) para
  que el trinquete muerda desde la primera iteración, empezando por
  `check_constitution`. Supersede a F-7, que se conformaba con "fijar el piso".
  **(cerrado el 2026-08-08)** — 75% → **91%**, umbral 50 → 90. El invariante se
  declaró como **Principio V** de la constitución (enmienda 0.3.0 → 0.4.0), con
  enforcement `pytest-cov` + paso `coverage`, que es verificable recién desde
  [[SPEC-020-enforcement-declarado-en-config]]; el número quedó en su SSOT
  (`pipeline.coverage`), no en la constitución ni en una spec. La deuda era un
  patrón único: la suite cubría helpers y **nunca los `main()`** — los
  entrypoints que corren en un proyecto instalado. Destapó un bug real,
  [[SPEC-021-config-vacio-no-rompe]].
- **K-4 · La suite e2e tiene que ser un paso del pipeline local.** El dogfooding
  es estructuralmente incapaz de cubrir lo que el kit genera *para otros*: el
  config del kit ejercita rutas distintas de las sembradas — por ahí entró el bug
  de sintaxis INI de `gen_import_linter` (el kit no corre `layers`, ver el
  descarte de arriba), que solo apareció al correr la e2e. Para un proyecto
  generador, **el test de instalación es el nivel de test primario**, no un
  extra que se corre a mano ni solo en un workflow aparte. Fix: sumar un paso
  `e2e` al pipeline y a `pipeline.steps` del kit. La forma ya está resuelta por
  precedente: replicar lo que SPEC-019 hizo con `integration` (clave
  `dirs.tests_e2e` + paso propio en el adaptador + omisión con aviso si la
  carpeta no existe), lo que además lo deja disponible para cualquier derivado
  que tenga su propia e2e, sin acoplar el núcleo. Ojo con C-8: agregar un paso
  de código exige tocar `pipeline.CODE_STEPS` **y** el dispatcher del adaptador.
  Y con el costo: el paso es caro comparado con el resto, así que hay que decidir
  si va en el pipeline completo o detrás de un flag/orden (al final, después de
  `coverage`).
  **(cerrado el 2026-08-09)** → [[SPEC-018-verificacion-e2e]] US3
  (FR-US3-001..005), como reapertura: US2 ordenaba lo contrario y una spec nueva
  habría dejado dos SSOTs contradictorios sobre el mismo archivo. **El costo era
  un mito**: medido, 16,6 s contra los 17,2 s del pipeline entero (`coverage`
  solo tarda 9,2 s). El pipeline pasa a ~36 s. Nada de flag: un disparador
  opcional reproduce el "se termina salteando" que US2 temía, con otro nombre. Y
  "cableada al ciclo de cada commit" era falso desde el principio — en cada commit
  corren los hooks, el pipeline corre al cerrar iteración. El acople que US2 sí
  describía bien (la carpeta arrastrada a `coverage`) se cerró antes, en C-8:
  ahora `TEST_DIRS` declara si la carpeta entra a la medición, y la e2e no entra
  porque maneja el kit por subproceso y no aporta líneas medidas. Salió gratis:
  el paso de lint a mano de `e2e.yml` desaparece. Destapó **V-4**.
- **K-5 · El paso `coverage` se siembra sin umbrales, o sea inerte.** En el kit
  es una elección deliberada; en un proyecto de IT real con código creciendo, un
  paso que se omite con aviso en cada corrida enseña que el verde no significa
  nada — la misma familia que U-3 y C-1. Fix: que `sdd-configure` (o `sdd-init`,
  si ya hay tests) mida el piso real del proyecto y lo escriba como trinquete,
  en vez de dejar la clave comentada.
  **(cerrado el 2026-08-09)** → [[SPEC-009-coverage-y-ci]] US2 (FR-US2-001..007).
  `core/sdd_coverage_baseline.py` mide y escribe; la medición la hace el adaptador
  vía `coverage-baseline`, categoría nueva del contrato —una **consulta**: produce
  un dato en vez de validar, y por eso no entra a `STEPS` ni a
  `pipeline.CODE_STEPS`, evitando repetir C-8—. **No** lo hace `sdd-init`: correr
  la suite ajena durante la instalación es una sorpresa cara. **No** pisa umbrales
  ya declarados: informa medido vs declarado y avisa cuando el trinquete dejó de
  morder, que es el defecto que K-3 encontró en el propio kit.
- **K-6 · No está dicho en ninguna parte que el kit es desechable.** Es la
  propiedad de producto que ordena todo lo anterior: una vez instalado, el
  derivado **se sostiene solo** — el andamiaje vendorizado en `tools/sdd/`, las
  skills, las plantillas ya resueltas y los docs no requieren el clon del kit
  para nada del día a día. Nadie lo afirma: ni el README del kit, ni
  `templates/docs/SDD-OPERACION.md`, ni la salida de `sdd-init`. Sin esa
  afirmación, el usuario asume una dependencia permanente (y nosotros toleramos
  huecos como K-2, que solo se explican si el kit está siempre a mano). SSOT
  elegido: el `README.md` del kit, que es el autoritativo de "qué es el kit / uso"
  según `00-INDEX.md`. Matiz que hay que escribir con cuidado: la única razón
  legítima para volver al kit es **actualizar** el andamiaje, que es E-2
  (`sdd-update`) y hoy no existe.
  **(cerrado el 2026-08-09)** con la sección "El kit es desechable" del
  `README.md`. Se evaluó y **descartó** el reflejo que este ítem pedía del lado
  del derivado (una línea en `templates/docs/SDD-OPERACION.md`): quien corre
  `sdd-init` ya lo leyó en el README, y quien llega después al proyecto derivado
  nunca oye hablar del kit —las únicas dos menciones en las plantillas hablan de
  la copia vendorizada y de E-2, las dos correctas—. Declararlo ahí sería
  introducir una dependencia en la cabeza del lector solo para negarla. Lo que
  sí queda del razonamiento es K-2, que se sostiene solo: una referencia colgada
  es un hueco aunque el clon esté al lado.

## Descartado explícitamente del proyecto de referencia

No todo lo que tiene el evaluador tiene sentido en un kit agnóstico. Se
evaluó y se dejó afuera:

- `schema_drift_check.py`, `connection_check.py`, `e2e_probe.py`,
  `conversation_probe.py` — específicos de su dominio (validar un agente
  conversacional contra un schema versionado).
- Su principio "Evaluación determinista" — es un invariante de *producto*, no
  de método; un proyecto que lo quiera lo escribe en su propio config.
- Migrar el evaluador a consumir el kit — descartado por decisión de producto,
  no por viabilidad técnica.

## Técnicas (ideas sueltas, sin prioridad asignada)

- Render de `SPEC-000` genera secciones vacías ("Tokens relajados" sin ítems)
  que ensucian el doc; omitir secciones vacías.
- `check_naming` también podría chequear nombres de paquetes/directorios, no
  solo identificadores y stems de archivo.
- Adaptadores `node`/`go` (deuda ya registrada en historial y SPEC-001).
- `enforcement`/`detail` de un principio admiten un solo token: `render.py` los
  envuelve en un único code span y `check_constitution._is_path` valida
  existencia sobre él. Un principio con dos SSOTs de detalle (o con enforcement
  mixto tool + revisión) no se puede expresar. Aceptar listas sería cambio de
  núcleo (config + render + check) y necesita spec propia.
