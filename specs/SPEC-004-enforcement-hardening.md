# SPEC-004-enforcement-hardening: Enforcement hardening — bootstrap de hooks, reset post-commit y pre-commit robusto

> Origen: comparación con el proyecto de referencia `evaluador-flujo-intent`
> (2026-08-01), que corrió más tiempo el gate spec-first en producción y
> endureció capas que sdd-first todavía no tiene.

## User Story (Priority P1)

Como mantenedor de un proyecto instalado con sdd-first, quiero que la capa git
del enforcement (hooks pre-commit/post-commit) se instale sola y que la spec
vigente se limpie automáticamente después de cada commit, para que el gate
spec-first no dependa de que alguien recuerde instalar hooks a mano ni de que
una spec vieja quede "vigente" para siempre por descuido.

**Why this priority:** hoy `.sdd/current-spec` puede quedar declarado
indefinidamente (nadie lo resetea), y los hooks git de un `git clone` nuevo no
están instalados hasta que alguien corre `pre-commit install` a mano — dos
huecos reales que dejan pasar código sin spec vigente real.

**Independent Test:** en un repo limpio (o recién instalado con `sdd-init`),
correr el pipeline instala los hooks git si faltan; un commit exitoso deja
`.sdd/current-spec` con solo comentarios y **sin aparecer en `git status`**
(está ignorado, FR-008); un `git clone` fresco sin el archivo lo recupera vía
`sdd-doctor`; el hook `sdd-gate` de pre-commit sigue bloqueando aunque
`python` no esté en el PATH (solo `python3`).

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

## Clarifications

### Session 2026-08-01
- Q: ¿el fix de `.pre-commit-config.yaml` aplica solo al kit o también a
  proyectos instalados? → A: a ambos — se corrige `.pre-commit-config.yaml`
  del propio kit y `templates/wiring/.pre-commit-config.yaml` (lo que
  `sdd_init.py` copia a proyectos nuevos).
- Q: ¿`bootstrap_hooks.py` y `sdd_reset.py` van a `core/` o a `tools/`? → A:
  `core/`, porque `sdd_init.py` vendoriza todo `core/` en
  `tools/sdd/core/` de cada proyecto instalado (`_vendor_kit`); ponerlos ahí
  los distribuye gratis a los derivados sin tocar la lista `WIRING`.

### Session 2026-08-11 (reabierta, G-9)

- Q: ¿nueva spec o se reabre SPEC-004? → A: se reabre — G-9
  (`docs/IDEAS.md`) es el mismo invariante que SC-004 ya declara ("git status
  no lo marca modificado") y que sigue incumplido: `sdd_reset.py` (FR-002)
  edita el archivo *después* de que el commit ya cerró, así que ese cambio
  nunca queda commiteado y el working tree sale sucio tras todo commit con
  spec declarada.
- Q: ¿reconciliar el reset con el commit (hook que commitea, o exigir `git add`
  manual) o repensar el mecanismo? → A: repensar — `.sdd/current-spec` es
  estado de sesión local (el gate solo lee su contenido en disco, nunca su
  historial de git; la trazabilidad real vive en `SPECS_REGISTRY.md` +
  `FR-NNN` grepeado en los tests, no en este archivo). Que un hook post-commit
  haga su propio commit arriesga recursión y ensucia el historial con commits
  vacíos de "reset"; exigir `git add .sdd/current-spec` a mano es el
  antipatrón que el propio protocolo prohíbe (automatización que depende de
  memoria humana). Sacarlo de git resuelve la contradicción de raíz.
- Q: ¿alcanza con el `.gitignore`? → A: no — `core/sdd_doctor.py` tiene
  `.sdd/current-spec` en `REQUIRED` (chequeo de existencia). Sin sembrarlo, un
  `git clone` fresco (del kit o de un derivado ya instalado) sale con el
  doctor en rojo por "artefacto faltante" — la misma clase de contradicción
  que D-1/D-3/G-4 ya señalaron en otras superficies. FR-008 lo resuelve
  sacándolo de `REQUIRED` y sembrándolo si falta.
- Q (hallazgos de `analyze`, ANA-01): FR-008 decía "reemplaza FR-002/FR-007
  como mecanismo" mientras ambos siguen `MUST` con tests propios — ¿se
  deprecan o el texto está mal? → A: el texto estaba mal. FR-002/FR-007 siguen
  vigentes: limpian y preservan el *contenido* del archivo dentro de una
  sesión de trabajo, algo necesario tenga o no versionado. Lo único que
  cambia con FR-008 es que ese contenido ya no viaja por git. Reformulado a
  "complementa".
- Q (ANA-02): "se destrackea con `git rm --cached`" — ¿es un paso
  automatizado (algún script) o manual? Los tests no lo ejercitan. → A: es
  manual y de una sola vez, sobre el archivo ya trackeado del kit al cerrar
  esta iteración; no es comportamiento de ningún script porque no hay nada
  que automatizar para repos que nacen después de este FR (el `.gitignore`
  evita que vuelvan a trackearlo). Aclarado en el texto del FR; no aplica
  cobertura de test porque no es lógica del andamiaje.
- Q (ANA-03): SC-004 decía "`git status` no lo marca modificado", que
  SC-005 ya cubre (y de forma más fuerte: ni siquiera aparece). → A: se acotó
  SC-004 a la preservación byte a byte de la estructura del archivo tras el
  reset, sin mencionar git; SC-005 es el único SC que habla de `git status`.
- Q (ANA-04, HIGH): SC-005 afirma que el archivo no aparece en `git status`
  tras el ciclo completo, pero el test mapeado no corría git — solo probaba
  `seed_current_spec` y la ausencia en `REQUIRED`. → A: hueco real. Se agregó
  una aserción en `test_escenario_2_misma_spec_en_varios_commits`
  (`tests/e2e/escenarios/test_ciclo_spec_first.py`, entorno con git real y
  hooks reales) que corre `git status --porcelain` tras el primer commit y
  confirma que "current-spec" no aparece en la salida.
- Q (ANA-05, MEDIUM): nada verificaba que `.gitignore` (kit) y
  `templates/wiring/.gitignore` contuvieran de verdad la línea
  `.sdd/current-spec`. → A: se agregaron dos tests unitarios de paridad
  (`test_gitignore_del_kit_ignora_current_spec`,
  `test_gitignore_de_la_plantilla_de_wiring_ignora_current_spec`) en
  `tests/unit/test_current_spec_no_versionado.py`.
- Q (ANA-06, MEDIUM): el *Independent Test* de la User Story no mencionaba el
  alcance de FR-008. → A: ampliado para nombrar que el commit no deja rastro
  en `git status` y que `sdd-doctor` recupera el header en un clon fresco.
- Q (ANA-07, LOW): *Key Entities* no reflejaba que el ciclo de
  `.sdd/current-spec` ocurre fuera de git desde FR-008. → A: agregada la
  cláusula correspondiente.
- Q (ANA-08, HIGH, segunda pasada de `analyze`): FR-008 promete que
  `.gitignore` "de forma permanente y automática" evita volver a trackear
  `.sdd/current-spec`, pero `sdd_init.py` conserva sin tocar cualquier
  `.gitignore` preexistente en el target — el caso realista (casi todo
  proyecto ya tiene uno) — así que la línea nunca se agregaba y FR-008 quedaba
  neutralizado por la vía de instalación, sin que `sdd-doctor` lo detectara
  (`.gitignore` no estaba en `GATE_WIRING`, lo único que el doctor audita por
  contenido). Misma familia que U-4/G-4 de `docs/IDEAS.md`. → A: se agregó
  FR-009/SC-006 — `sdd_init.py` ahora **agrega** la línea a un `.gitignore`
  existente que no la tenga (sin pisar el resto, mismo criterio que
  `sdd_spec.py` con `.sdd/current-spec`), y `sdd-doctor` verifica por
  contenido que el `.gitignore` del proyecto la incluya, reportándolo si
  falta.
- Q (ANA-09, MEDIUM, tercera pasada de `analyze`): el único test de FR-009
  llamaba directo a `sdd_init._copy_text`, no a la ruta real de instalación
  (`sdd_init.py` como subproceso, como ya hace la suite e2e para FR-008) —
  una regresión en `main()` no la detectaría. → A: se agregó
  `tests/e2e/escenarios/test_instalacion_brownfield_gitignore.py`, que corre
  `entorno.instalar` (subproceso real) sobre un `.gitignore` propio
  preexistente y confirma que se conserva y se le agrega la línea.
- Q (ANA-10, LOW): SC-006 tenía un error de concordancia verbal ("...propio
  dejar ese .gitignore..."). → A: corregido a "deja".
- Q (ANA-11, LOW): *Key Entities* no mencionaba `.gitignore` pese al
  comportamiento que le agrega FR-009. → A: agregada la entrada
  correspondiente.

### Session 2026-08-01 (reabierta)
- Q: tras un commit real, `.sdd/current-spec` no quedaba con "solo
  comentarios" (SC-002) sino casi vacío, distinto del header committeado —
  working tree sucio después de todo commit. ¿Por qué el test de FR-002 no lo
  detectó? → A: `test_sdd_reset.py` siembra el archivo a mano ya con el header
  puesto; nunca ejercita el camino real `sdd_spec.py` (declara) → commit →
  `sdd_reset.py` (limpia). `sdd_spec.py::main` pisa el archivo entero con
  `f"{spec_id}\n"` (línea ~101), destruyendo el header de comentarios *antes*
  de que `sdd_reset.py` tenga algo que preservar — el filtro `startswith("#")`
  no tiene nada que filtrar. Es el mismo bug ya anotado como G-7 en
  `docs/IDEAS.md`, visto ahora desde el ángulo de esta spec.
- Q: ¿nueva spec o se reabre SPEC-004? → A: se reabre — el invariante roto
  (SC-002/FR-002) es literalmente el que esta spec ya declara como propio;
  las specs son vivas (`AGENTS.md`).

## Acceptance Scenarios

- **Given** un repo con `.git/` y sin hooks instalados, **When** corre
  `core/pipeline.py`, **Then** el paso `hooks` instala `pre-commit` y
  `post-commit` sin tocar hooks ya instalados, y no falla si no hay `.git/`
  (no-op con aviso).
- **Given** un commit exitoso con `SPEC-004-enforcement-hardening` declarada
  en `.sdd/current-spec`, **When** corre el hook post-commit `sdd-reset`,
  **Then** `.sdd/current-spec` queda con solo las líneas de comentario (`#`).
- **Given** un shell sin el binario `python` en el PATH (solo `python3`),
  **When** `pre-commit` corre el hook local `sdd-gate` sobre un archivo bajo
  `core/`, **Then** el hook igual se ejecuta y decide (bloquea o permite)
  porque `language: python` deja que `pre-commit` resuelva su propio
  intérprete en vez de depender del `python` del shell invocador.
- **Given** `.sdd/current-spec` con el header de comentarios de la plantilla,
  **When** `sdd_spec.py` declara una spec nueva, **Then** el archivo conserva
  las líneas `#` y solo agrega/reemplaza la línea del spec-id — no pisa el
  archivo entero.
- **Given** ese mismo flujo (`sdd_spec.py` declara → se edita la spec → se
  commitea), **When** corre el hook post-commit `sdd-reset`, **Then**
  `.sdd/current-spec` queda **byte a byte igual** al header de
  `templates/wiring/current-spec` (SC-004; que el working tree no quede
  sucio lo cubre el escenario siguiente, vía SC-005).
- **Given** `.sdd/current-spec` bajo `.gitignore`, **When** se declara una
  spec, se edita, se commitea y corre `sdd-reset`, **Then** `git status` no
  reporta el archivo en absoluto (ni modificado ni sin trackear pendiente de
  commit) — no solo "sin diff" como en el escenario anterior.
- **Given** un `git clone` fresco sin `.sdd/current-spec` en disco, **When**
  corre `core/sdd_doctor.py` (con o sin `--fix`), **Then** no lo reporta como
  artefacto faltante y lo siembra con el header de
  `templates/wiring/current-spec` si no existe.
- **Given** un target con un `.gitignore` propio ya existente (sin la línea
  `.sdd/current-spec`), **When** corre `sdd-init`, **Then** el `.gitignore`
  resultante conserva su contenido original **y además** incluye
  `.sdd/current-spec`.
- **Given** un proyecto instalado cuyo `.gitignore` no incluye
  `.sdd/current-spec` (por ejemplo, editado a mano después de instalar),
  **When** corre `core/sdd_doctor.py`, **Then** lo reporta como problema,
  igual que reporta un gate no cableado por contenido.
- **Given** un ejemplo de config con un comentario intercalado entre pasos
  dentro del bloque `steps:` original, **When** `sdd_init._seed_pipeline_steps`
  lo procesa, **Then** el resultado trae el set sembrado una sola vez — ningún
  paso del bloque original (ni antes ni después del comentario) sobrevive.

## Functional Requirements

- **FR-001** MUST: `core/bootstrap_hooks.py` instala los hooks
  `pre-commit`/`post-commit` si faltan (vía `sys.executable -m pre_commit
  install --hook-type ... --hook-type ...`), sin tocar los ya instalados; es
  no-op con aviso si no hay `.git/`; falla con instrucción accionable si
  falta el paquete `pre-commit`.
- **FR-002** MUST: `core/sdd_reset.py` limpia `.sdd/current-spec` dejando solo
  las líneas que empiezan con `#`, buscando la raíz del repo igual que
  `sdd_gate.py`/`sdd_config.py`.
- **FR-003** MUST: `core/pipeline.py` corre `bootstrap_hooks` como paso
  `hooks`, agregado a `PROCESS_STEPS`, antes de los demás pasos declarados en
  `.sdd/config.yaml`.
- **FR-004** MUST: `.pre-commit-config.yaml` (del propio kit) y
  `templates/wiring/.pre-commit-config.yaml` (plantilla instalada) usan
  `language: python` (con `additional_dependencies: [pyyaml]` donde el script
  importe `sdd_config`) en vez de `language: system` para los hooks locales
  `sdd-gate`/`sdd-gate` y `sdd-traceability`, y agregan el hook `sdd-reset`
  (`stages: [post-commit]`, `always_run: true`, `pass_filenames: false`).
- **FR-005** MUST: `core/sdd_init.py` agrega `hooks` al set de pasos
  sembrados por defecto (`_SEEDED_STEPS`) para que proyectos nuevos lo tengan
  activo sin configuración manual.
- **FR-006** MUST: `.claude/sdd_gate_hook.sh` (del propio kit) y
  `templates/wiring/sdd_gate_hook.sh` (plantilla) tienen test que cubre la
  rama fail-closed (sin intérprete Python disponible) y la rama normal
  (con `python3` disponible, gate corre y decide).
- **FR-007** MUST: `core/sdd_spec.py` preserva las líneas de comentario (`#`)
  ya presentes en `.sdd/current-spec` al declarar una spec nueva; solo agrega
  la línea del spec-id, nunca pisa el archivo entero. Cierra el
  hueco por el que `sdd_reset.py` (FR-002) no tenía comentarios que preservar
  tras un ciclo real declarar→commitear→reset. *(La cláusula original decía
  «agrega o reemplaza»; FR-011 retiró el reemplazo implícito.)*
- **FR-008** MUST: `.sdd/current-spec` deja de estar bajo control de versiones
  — es un puntero de sesión local, no un artefacto del repo. `.gitignore` del
  kit y `templates/wiring/.gitignore` lo ignoran de forma permanente y
  automática (ningún commit futuro puede volver a trackearlo por descuido).
  El destrackeo del archivo ya versionado (`git rm --cached .sdd/current-spec`)
  es, en cambio, una acción **manual y de una sola vez**, ejecutada al cerrar
  esta iteración sobre el repo del kit — no un paso de ningún script, porque
  solo aplica a un archivo que ya estaba en el índice; un repo que nace con
  este FR ya implementado nunca llega a trackearlo. `core/sdd_doctor.py` deja
  de exigirlo en `REQUIRED` (ya no es un artefacto instalado que deba
  persistir) y, en su lugar, lo siembra con el header de
  `templates/wiring/current-spec` si falta — tanto en el chequeo normal como
  en `--fix` — para que un `git clone` fresco (del kit o de un derivado ya
  instalado) recupere el header sin paso manual. Esto **complementa** a
  FR-002/FR-007, no los reemplaza: ambos siguen vigentes para la higiene del
  contenido del archivo dentro de una misma sesión de trabajo (limpiar la
  spec declarada tras cada commit, preservar el header al declarar una
  nueva) — lo único que cambia es que ese contenido ya no viaja por git.
- **FR-009** MUST: la garantía de FR-008 no depende de que `.gitignore` del
  proyecto derivado sea uno nuevo. `core/sdd_init.py` copia `.gitignore` vía
  `WIRING`, cuyo `_copy_text` conserva sin tocar cualquier archivo ya
  presente en el destino — el caso realista, porque casi todo proyecto
  (brownfield, o greenfield con `git init` que ya generó un `.gitignore` por
  defecto) tiene uno antes de correr `sdd-init`. Si la instalación se limitara
  a conservar, la línea `.sdd/current-spec` nunca se agregaría y FR-008
  quedaría neutralizado por la vía de instalación. Por eso `sdd_init.py`
  **agrega** la línea a un `.gitignore` existente que no la tenga (append, sin
  pisar el resto del archivo — mismo criterio que `sdd_spec.py` ya aplica a
  `.sdd/current-spec`: preservar lo existente, sumar solo lo que falta), y
  `core/sdd_doctor.py` verifica por **contenido** (no solo existencia) que el
  `.gitignore` del proyecto instalado incluya esa línea, reportándolo como
  problema si no — mismo patrón que `_gate_wiring_problems` (FR-US1-002 de
  SPEC-014), que ya audita otros archivos de wiring por contenido y no solo
  por presencia.
- **FR-010** MUST: `core/sdd_init._seed_pipeline_steps` descarta el bloque
  `steps:` original comparando la indentación de cada línea contra la de
  `steps:`, no cortando en la primera línea que no matchea `"- "`. Un
  comentario intercalado entre los pasos del ejemplo (mismo o mayor nivel de
  indentación que los ítems) tiene que descartarse igual que un ítem; hoy corta
  el descarte a mitad de camino y los pasos que siguen al comentario se
  duplican en el config sembrado (docs/IDEAS.md C-9).
- **FR-011** MUST: la declaración de specs en `.sdd/current-spec` es
  **acumulativa dentro de la iteración**. `core/sdd_spec.py` conserva las specs
  ya declaradas al declarar otra —creándola o adoptándola con `--reuse`—, sin
  duplicar una ya presente ni reordenar las anteriores, e imprime el conjunto
  vigente resultante en ambos caminos. `--clear` retira las declaraciones
  dejando solo los comentarios; combinado con una declaración da el reemplazo
  explícito que antes ocurría solo. Cierra el hueco por el que crear una spec a
  mitad de iteración des-declaraba en silencio la anterior (docs/IDEAS.md G-7).
  **No** levanta el bloqueo transitorio: mientras la spec nueva no tenga FR
  escritos el gate sigue rechazando toda edición, porque exige las tres
  condiciones a cada spec declarada. Lo que cambia es que la anterior no se
  pierde, así que al escribir esos FR la autorización vuelve sola, sin
  re-declararla. El conjunto no crece sin límite: `sdd_reset.py`
  (FR-002) lo limpia tras cada commit, así que su alcance es exactamente la
  iteración en curso.

## Key Entities

- `.sdd/current-spec` — archivo de declaración de spec vigente; tiene ciclo de
  vida completo: declarar → editar → commitear → reset. Desde FR-008 ese
  ciclo entero ocurre fuera de git (`.gitignore`): no es un artefacto
  versionado, es estado de sesión local que `sdd-doctor` siembra si falta.
- Hooks git (`pre-commit`, `post-commit`) — instalados vía el paquete
  `pre-commit`, gestionados por `bootstrap_hooks.py`.
- `.gitignore` (kit y proyecto derivado) — desde FR-009 su contenido se
  audita (no solo su existencia): `sdd-init` le agrega la línea de
  `.sdd/current-spec` si lo conserva sin tenerla, y `sdd-doctor` reporta
  problema si falta.

## Success Criteria

- **SC-001** Un `git clone` nuevo del kit (o de un proyecto instalado con
  `sdd-init`) queda con los hooks git instalados a más tardar en su primer
  `core/pipeline.py`, sin paso manual.
- **SC-002** Tras cualquier commit exitoso con hooks instalados,
  `.sdd/current-spec` no contiene IDs de spec (solo comentarios).
- **SC-003** El hook `sdd-gate` de `pre-commit` sigue bloqueando/permitiendo
  correctamente en un entorno donde el binario `python` no existe (solo
  `python3`).
- **SC-004** Tras el ciclo real `sdd_spec.py` declara → se edita la spec → se
  commitea → corre `sdd-reset`, `.sdd/current-spec` queda **byte a byte
  idéntico** al header de la plantilla — la estructura del archivo (líneas de
  comentario preservadas, sin ID de spec residual) sobrevive el ciclo
  completo, independientemente de si el archivo está o no bajo control de
  versiones (eso lo cubre SC-005).
- **SC-005** `.sdd/current-spec` no aparece en `git status` bajo ninguna
  circunstancia del ciclo declarar→editar→commitear→reset (está ignorado, no
  solo "limpio" — a diferencia de SC-004, acá no hay diff que comparar porque
  git no lo trackea), y un `git clone` fresco recupera el header sin paso
  manual.
- **SC-006** Instalar con `sdd-init` sobre un target que ya tiene `.gitignore`
  propio deja ese `.gitignore` con `.sdd/current-spec` incluido, sin perder
  ninguna línea original; `sdd-doctor` sobre un proyecto instalado detecta y
  reporta si esa línea falta.
- **SC-007** `_seed_pipeline_steps` produce el set sembrado una sola vez
  incluso cuando el bloque `steps:` original del ejemplo trae un comentario
  intercalado entre pasos: ningún paso del bloque descartado sobrevive en el
  resultado.
- **SC-008** En un proyecto instalado, crear SPEC-A, escribir su FR y crear
  después SPEC-B deja las dos declaradas en `.sdd/current-spec` (en ese orden,
  una por línea); el gate bloquea mientras SPEC-B no tenga FR —nombrando a
  SPEC-B, no a las dos— y vuelve a autorizar en cuanto SPEC-B los tiene, **sin
  re-declarar SPEC-A**. Re-declarar SPEC-A no agrega una segunda línea;
  `--clear` deja el archivo idéntico al header; y el ciclo completo declarar A →
  declarar B → commitear → `sdd-reset` sigue dejando el archivo byte a byte igual
  al header (SC-004 no se degrada con el conjunto).

## Assumptions

- Los proyectos instalados con `sdd-init --language=python` tienen (o pueden
  instalar) el paquete `pre-commit` como dependencia de desarrollo — igual
  que ya asume `.pre-commit-config.yaml` hoy.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_bootstrap_hooks.py |
| FR-002 | tests/unit/test_sdd_reset.py |
| FR-003 | tests/unit/test_pipeline_hooks_step.py |
| FR-004 | inspección manual de `.pre-commit-config.yaml` y `templates/wiring/.pre-commit-config.yaml` (no hay runner de pre-commit en CI del kit) |
| FR-005 | tests/unit/test_sdd_init_seeded_steps.py |
| FR-006 | tests/unit/test_sdd_gate_hook.py |
| FR-007, SC-004 | tests/unit/test_sdd_spec.py |
| FR-008, SC-005 | tests/unit/test_current_spec_no_versionado.py, tests/e2e/escenarios/test_ciclo_spec_first.py |
| FR-009, SC-006 | tests/unit/test_current_spec_no_versionado.py, tests/e2e/escenarios/test_instalacion_brownfield_gitignore.py |
| FR-010, SC-007 | tests/unit/test_sdd_init_seeded_steps.py |
| FR-011, SC-008 | tests/unit/test_sdd_spec.py, tests/e2e/escenarios/test_ciclo_spec_first.py |

## Fuera de alcance

- Coverage gates (`--cov-fail-under`) del pipeline de `evaluador-flujo-intent`
  — específicos de la madurez de testing de ese proyecto, no del kit.
- Wiring de `ruff`/`mypy` como hooks de `pre-commit` (hoy solo corren vía
  `core/pipeline.py` / el adaptador) — fuera de alcance de este hardening.

## Historial

- 2026-08-01: creada (draft), a partir de la comparación con
  `evaluador-flujo-intent`.
- 2026-08-01: implementada y pasada a `active`. `core/bootstrap_hooks.py`,
  `core/sdd_reset.py`, paso `hooks` en `core/pipeline.py` y `_SEEDED_STEPS`,
  `.pre-commit-config.yaml` (kit y plantilla) con `language: python` +
  hook `sdd-reset`. Validado con `pre-commit run --all-files` real (crea su
  venv aislado, instala `pyyaml`, ambos hooks pasan) y con instalación fresca
  vía `sdd_init.py` en directorio temporal.
- 2026-08-01: reabierta y cerrada de nuevo (FR-007/SC-004). Tras usar
  `sdd_spec.py` en la práctica se detectó que `.sdd/current-spec` quedaba
  sucio después de todo commit: `sdd_spec.py` pisaba el archivo entero al
  declarar, destruyendo el header de comentarios que `sdd_reset.py` (FR-002)
  necesitaba preservar. `sdd_spec.py::_declare_current_spec` ahora conserva
  las líneas `#` existentes. Verificado con 4 tests nuevos en
  `test_sdd_spec.py` (incluye el ciclo real declarar→reset) y con una
  instalación fresca en `/tmp`: el archivo queda byte a byte igual al header
  de `templates/wiring/current-spec` tras el ciclo completo. Relacionado con
  G-7 de `docs/IDEAS.md` (parcialmente resuelto entonces — la semántica
  multi-spec la cerró FR-011 el 2026-08-17). Pipeline 9/9 VERDE, 70 tests.
- 2026-08-11: reabierta y cerrada de nuevo (G-9, FR-008/FR-009). El reset
  post-commit (FR-002) editaba `.sdd/current-spec` *después* de que el commit
  ya cerrara, así que ese cambio nunca quedaba commiteado y el working tree
  salía sucio tras todo commit con spec declarada — invariante roto de
  SC-004/SC-005 desde que existían. Se repensó el mecanismo en vez de
  reconciliar el reset con el commit: `.sdd/current-spec` pasó a ser estado
  de sesión local no versionado (`.gitignore`, `git rm --cached`), con
  `sdd_config.seed_current_spec` sembrando el header en un clon fresco y
  `core/sdd_doctor.py` dejando de exigirlo en `REQUIRED` (FR-008). Cuatro
  rondas de `analyze` sobre esta misma reapertura encontraron y cerraron
  ocho hallazgos más (ANA-01..ANA-11 salvo huecos numéricos): el más
  importante, que `sdd_init.py` conserva sin tocar cualquier `.gitignore`
  preexistente en el target —el caso realista—, así que la línea nunca se
  agregaba y FR-008 quedaba neutralizado por la vía de instalación; se cerró
  con FR-009 (`sdd_config.ensure_gitignore_current_spec`, que agrega la línea
  sin pisar el resto, y una auditoría por contenido en `sdd-doctor`). Cada
  hallazgo quedó documentado en *Clarifications* con su corrección. Verificado
  con `pipeline.py` → VERDE 11/11, `check_traceability.py` OK, una instalación
  simulada en `/tmp` sobre un `.gitignore` propio y el escenario e2e
  `test_instalacion_brownfield_gitignore.py`.
- 2026-08-17: **reabierta** (FR-010/SC-007) por C-9 de `docs/IDEAS.md`.
  `_seed_pipeline_steps` cortaba el descarte del bloque `steps:` original en la
  primera línea que no empezaba con `"- "`, así que un comentario intercalado
  entre pasos dejaba sobrevivir (y duplicarse) los pasos que venían después del
  comentario. Fix: descarta comparando indentación contra la de `steps:`, no
  por forma de línea. Test nuevo reproduce el caso (rojo confirmado antes del
  fix). Pipeline VERDE 11/11.
- 2026-08-17: **reabierta** (FR-011/SC-008) por G-7 de `docs/IDEAS.md`, que
  cierra. La declaración de specs pasó de reemplazo a **acumulación dentro de la
  iteración**, con `--clear` como vía explícita para retirarla. Enmienda la
  cláusula «agrega o reemplaza» de FR-007: reemplazar des-declaraba en silencio
  la spec anterior y, como una spec recién creada nace sin FR escritos, el gate
  pasaba a bloquear también las ediciones que esa anterior ya autorizaba. El
  triage de reutilización devolvió 7 candidatas por archivo compartido (ruido
  conocido); se aplicó la regla por funcionalidad del precedente de C-9/C-6 y
  ganó esta spec, cuya User Story es el ciclo de vida de `.sdd/current-spec` y
  cuyo FR-007 es literalmente `_declare_current_spec`. La capacidad multi-spec ya
  existía en el formato (header), en el lector (`sdd_gate._declared_specs`, que
  valida cada spec en AND) y en la doc: faltaba solo el escritor, así que ninguna
  vía sancionada podía producirla. Se descartó la alternativa "replace + aviso"
  con la evidencia del propio historial —las iteraciones del 2026-08-17 (C-9/C-6,
  cuatro specs con FR) y del 2026-08-12 (SPEC-003 + SPEC-012) editan código
  gateado bajo varias specs en un solo commit, y son buena práctica de SPEC-022,
  no deslices—. Seis tests unitarios nuevos y un escenario e2e (todos en rojo
  confirmado antes del fix), incluido el ciclo con dos specs que verifica que
  SC-004 no se degrada. El e2e existía en una forma que no probaba nada de esto:
  llegaba al estado multi-spec escribiendo `.sdd/current-spec` a mano, la vía que
  `AGENTS.md` prohíbe; el escenario nuevo declara solo con `sdd_spec.py` como
  subproceso en el derivado (precedente ANA-09: probar el helper interno no
  prueba la ruta que corre el usuario). Esa prueba en un proyecto instalado
  corrigió un overclaim de la primera redacción: FR-011 **no** levanta el bloqueo
  transitorio de la spec sin FR. Pipeline VERDE 11/11.
