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

- **G-1 · Pre-commit hardcodea `files: '^(src|app|lib)/'`.** El gate lee
  `dirs.source_roots` del config pero el wiring de pre-commit no: un proyecto
  con código en `core/` (como el propio kit) tiene ese gate muerto. Viola el
  principio "no hardcodear listas". Fix: generar la regex desde el config
  (render del wiring) o quitar `files:` y dejar que `sdd_gate` decida.
- **G-2 · El gate no verifica el estado de la spec.**
  **(ya con spec) → [[SPEC-006-gate-verifica-estado-spec]]** — implementado
  el 2026-08-01. `_spec_is_valid` hacía substring match de `spec_id` sobre el
  texto del registro: una spec `archived`/`superseded` (o mencionada en
  prosa del roadmap) desbloqueaba el gate igual que una `active`. Fix:
  parsea la fila (reusa `check_traceability._parse_registry`) y exige estado
  `draft`/`active`.
- **G-3 · Matcher del hook de Claude solo cubre `Edit|Write`.**
  `MultiEdit`, `NotebookEdit` y `Bash` (`echo > src/x.py`) lo evitan. Ampliar
  el matcher y documentar el bypass por Bash como límite conocido en
  `docs/SDD-ENFORCEMENT.md`.
- **G-4 · `sdd-doctor` valida existencia, no contenido, del wiring.** Un
  `.claude/settings.json` cualquiera cuenta como "gate cableado". Fix: buscar
  la invocación de `sdd_gate.py` dentro del archivo.
- **G-5 · Criterio mtime del gate sin documentar ni escape hatch.**
  `git checkout`/`clone` renuevan mtimes y pueden des/bloquear espuriamente.
  Documentarlo como heurística en SDD-ENFORCEMENT y considerar una alternativa
  (hash de la spec registrado en `.sdd/current-spec`).
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

## P2 — Bugs y asperezas menores de código

- **C-1 · Paso desconocido cuenta como OK.** `pipeline.py`: un step no
  reconocido (p. ej. `gate`, que la doc de `adapter.py` y del config de
  ejemplo listan como paso de proceso) hace `continue` sin decrementar
  `total` → "VERDE 5/5" con un paso que no corrió. Además, alinear la doc:
  `gate` no es paso de pipeline (decisión ya tomada en el historial).
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
