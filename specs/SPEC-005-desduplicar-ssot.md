# SPEC-005-desduplicar-ssot: Desduplicar SSOTs del kit (docs/templates, defaults, wiring)

> Origen: `docs/IDEAS.md` P2 "Duplicación de SSOT dentro del kit" (R-1, R-2,
> R-3), detectado en la revisión crítica del 2026-07-02; ampliada después con
> C-8 (vocabularios de código repetidos) y R-4 (el wiring del kit como copia
> manual de `templates/wiring/`).

## User Story (Priority P2)

Como mantenedor de sdd-first, quiero que los documentos, defaults y archivos de
wiring que hoy existen duplicados dentro del propio repo tengan un único archivo
autoritativo (el resto se genera o referencia), para que una edición futura no
pueda dejar `docs/` y `templates/docs/`, el wiring de la raíz y
`templates/wiring/`, o dos constantes de código, divergiendo en silencio — justo
lo que el Principio "No duplicar SSOT" de `AGENTS.md` prohíbe.

**Why this priority:** hoy no rompe nada en caliente (P2, no P0/P1), pero es
deuda que compone: cada edición manual a uno de los duplicados y no al otro
es un drift que nadie detecta hasta que alguien lee las dos versiones y no
coinciden.

**Independent Test:** correr `python core/render.py --check` sobre el propio
kit reporta drift si se edita a mano cualquiera de sus copias sincronizadas
—`docs/SDD-ENFORCEMENT.md`, `docs/playbooks/analyze.md`,
`docs/playbooks/clarify.md`, `specs/SPEC-TEMPLATE.md` o un archivo de wiring
como `.claude/sdd_gate_hook.sh`— sin tocar su contraparte en `templates/`; el
paso `render` del pipeline falla en ese caso.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

## Clarifications

### Session 2026-08-01
- Q: ¿cuál de las dos copias es la autoritativa, `docs/` o `templates/`? → A:
  `templates/` — es lo que `sdd_init.py` ya copia a proyectos instalados
  (`STATIC_DOCS`); `docs/` del kit es la copia dogfooded de esas mismas
  plantillas sobre sí mismo (sin placeholders en los 4 archivos afectados, se
  verificó con `grep "{{"` → 0 matches).
- Q: ¿los proyectos instalados con `sdd-init` heredan el nuevo paso `render`
  con las entradas de sync? → A: sí (el `core/` completo se vendoriza), pero
  las entradas de sync son no-op ahí: no tienen `templates/` en su repo, así
  que `render.py` las omite si `(repo_root / "templates")` no existe.

### Session 2026-08-09 (C-8)

- Q: ¿La duplicación de listas de código entra en esta spec o pide una nueva? →
  A: entra. FR-005 ya trata exactamente este caso —un default declarado como
  literal en varios módulos— y su Independent Test es sobre `core/sdd_config.py`.
  Lo que cambia es la clase de dato duplicado: antes un valor, ahora un
  vocabulario (qué pasos existen, qué carpetas de test existen).
- Q: ¿El pipeline le pregunta al adaptador qué pasos soporta, o la lista sale del
  núcleo? → A: del núcleo. Preguntarle al adaptador gasta un subproceso por
  corrida y, peor, vuelve el vocabulario dependiente del lenguaje: un nombre de
  paso mal escrito en `pipeline.steps` sería "soportado" o no según el adaptador
  instalado, cuando lo que decide es el contrato (`adapters/CONTRACT.md`). El
  contrato es del núcleo; lo que es del lenguaje es la *implementación* de cada
  paso. Así que `CODE_STEPS` vive en `core/sdd_config.py` y un test cruza el
  dispatcher del adaptador contra él en las dos direcciones.
- Q: ¿Alcanza con mover la tupla `("tests_unit", "tests_integration")` a una
  constante y que los cuatro consumidores la importen? → A: no, y esto es lo que
  la duplicación tapaba: los cuatro no hacen la misma pregunta. El adaptador la
  usa para dos cosas distintas (blancos estáticos de `naming`/`lint`/`format` vs
  carpetas que `coverage` le pasa a pytest para **ejecutar**), `check_naming` para
  relajar reglas, `render` para los `paths:` de CI y `sdd_doctor` para cruzar
  contra `pipeline.steps`. Una lista plana obliga a que toda carpeta de test
  responda igual a las cinco preguntas, que es justo lo que impide agregar una
  clase de test nueva. El SSOT declara la carpeta **con sus propiedades**, y cada
  consumidor filtra por la que le toca.
- Q: ¿Por qué `TEST_DIR_STEP` no alcanzaba si ya era SSOT? → A: era SSOT de una
  sola de las cinco preguntas (qué paso la corre) y las otras cuatro siguieron
  con su literal. Se generaliza en vez de sumarle una constante hermana, que
  reintroduciría el mismo drift un nivel más arriba.

### Session 2026-08-14 (R-4)

- Q: ¿El wiring duplicado (`templates/wiring/` ↔ la copia instalada en el propio
  kit) entra acá o pide una spec nueva? → A: entra. Es la misma clase de
  duplicación que FR-001 —dos archivos con el mismo contenido y ningún mecanismo
  que los mantenga juntos— sobre otra superficie. Lo único distinto es que un
  par difiere por el layout del andamiaje (`core/` en el kit,
  `tools/sdd/core/` en el derivado), y para eso ya existe `{{sdd.core}}`.
- Q: ¿Hay evidencia de que el drift ocurre, o es teórico? → A: ocurrió y nadie lo
  detectó. En `fc95761` la plantilla `sdd_gate_hook.sh` perdió las 37 líneas del
  bloque `IS_ANTIGRAVITY` (el soporte de Antigravity se mudó a
  `agy_gate_hook.py`), pero `.claude/sdd_gate_hook.sh` del kit no se tocó: quedó
  cargando una rama muerta que ninguna plantilla tiene. El par también se pagó
  doble en SPEC-004 (FR-004) y dos veces en SPEC-015.
- Q: ¿`render.py` necesita aprender a escribir `.sh`/`.json`/`.yaml`/`.js`? → A:
  no. `_sync_renderer` ya lee texto plano, resuelve los placeholders de ruta y
  escribe con `write_text_lf`; la extensión nunca entró en la decisión. Lo que
  faltaba era **la lista de destinos**, no el mecanismo.
- Q: ¿Cómo resuelve cada archivo dónde vive el núcleo? → A: por el medio que ya
  usa, sin uniformar: `.pre-commit-config.yaml` y el plugin de opencode pasan a
  `{{sdd.core}}` (hoy hardcodean una de las dos rutas); `sdd_gate_hook.sh` y
  `agy_gate_hook.py` conservan su detección dinámica (prueban ambos layouts en
  runtime), que ya los hace válidos en los dos lados. Lo que esta spec exige es
  que haya **un solo archivo**, no una única técnica para ubicar el núcleo.
- Q: ¿Qué pasa con los destinos de wiring que el kit no tiene o que le son
  propios? → A: se clasifican explícitamente al lado del catálogo, con el motivo.
  `.gitignore` queda fuera (el kit ignora cosas que un derivado no tiene por qué
  heredar, y el catálogo ya lo trata como `semilla`) y `.sdd/current-spec`
  también (es estado de sesión, no un artefacto). `.opencode/plugin/sdd-gate.js`
  entra: el kit no lo tenía instalado y pasa a tenerlo, con lo que el gate de
  opencode deja de ser lo único que el kit le pide a sus derivados sin usarlo él.

## Acceptance Scenarios

- **Given** el kit con `docs/SDD-ENFORCEMENT.md` editado a mano y
  `templates/docs/SDD-ENFORCEMENT.md` sin tocar, **When** corre
  `python core/render.py --check`, **Then** reporta drift y sale con exit 1.
- **Given** el kit sincronizado, **When** corre `python core/render.py`,
  **Then** `docs/SDD-ENFORCEMENT.md`, `docs/playbooks/analyze.md`,
  `docs/playbooks/clarify.md` y `specs/SPEC-TEMPLATE.md` quedan
  byte-idénticos a sus fuentes en `templates/`.
- **Given** un proyecto instalado vía `sdd-init` (sin carpeta `templates/`),
  **When** corre `python tools/sdd/core/render.py --check`, **Then** no falla
  por las entradas de sync (se omiten silenciosamente) — solo verifica
  `CONSTITUTION.md`/`SPEC-000-naming.md` como hoy.
- **Given** `.sdd/config.yaml` del kit con el paso `render` en `pipeline.steps`,
  **When** corre `python core/pipeline.py`, **Then** el paso `render` corre
  `render.py --check` y cuenta como paso del pipeline (verde/rojo real).
- **Given** `templates/docs/SPEC-FORMAT.md`, **When** se lee la sección
  "Template copiable", **Then** referencia `specs/SPEC-TEMPLATE.md` en vez de
  embeber una copia del contenido del template.
- **Given** `core/sdd_config.py`, `core/sdd_gate.py`,
  `adapters/python/adapter.py` y `adapters/python/check_naming.py`, **When**
  se busca el default `"src"` (source_roots) y `"tests/unit"` (tests_unit),
  **Then** ambos existen una sola vez en `core/sdd_config.py` y el resto de
  los módulos los importa (no los repite como literal).
- **Given** un paso de código implementado en el dispatcher del adaptador pero
  ausente de `CODE_STEPS`, o al revés, **When** corre la suite unitaria,
  **Then** falla nombrando el paso que sobra o falta de cada lado.
- **Given** `core/pipeline.py`, **When** se busca la enumeración de pasos de
  código, **Then** no hay literal propio: importa el vocabulario de
  `core/sdd_config.py`.
- **Given** el kit con `.claude/sdd_gate_hook.sh` (o cualquier otro destino de
  wiring sincronizado) editado a mano y su plantilla sin tocar, **When** corre
  `python core/render.py --check`, **Then** reporta drift y sale con exit 1.
- **Given** `templates/wiring/.pre-commit-config.yaml` con `{{sdd.core}}`,
  **When** corre `python core/render.py` sobre el kit, **Then**
  `.pre-commit-config.yaml` de la raíz queda con `python core/sdd_gate.py`; y
  **When** `sdd-init` lo instala en un derivado, **Then** queda con
  `python tools/sdd/core/sdd_gate.py`.
- **Given** una plantilla de wiring con finales de línea CRLF, **When**
  `render.py` la sincroniza, **Then** el destino queda escrito con LF; y
  **Given** ese destino ya versionado, **When** se lo saca en un checkout de
  Windows, **Then** sigue en LF porque `.gitattributes` lo declara `eol=lf`.
- **Given** una plantilla de `templates/wiring/` que usa `{{project.name}}`,
  **When** corre la suite unitaria, **Then** falla: el sync no resuelve ese
  placeholder y lo dejaría crudo en el destino del kit.
- **Given** el `.opencode/plugin/sdd-gate.js` instalado en el kit, **When** se
  resuelve la ruta del gate que declara, **Then** ese archivo existe — si no,
  el plugin no falla: se calla y deja el gate apagado.
- **Given** `.claude/sdd_gate_hook.sh` regenerado por `render.py` en un sistema
  POSIX, **When** se miran sus permisos, **Then** conserva el bit de ejecución
  que le deja `sdd-init`.
- **Given** un destino nuevo agregado a `sdd_catalog.WIRING`, **When** corre la
  suite unitaria sin que ese destino se haya clasificado (sincronizado o
  excluido con motivo), **Then** falla nombrándolo.
- **Given** una clave de carpeta de test declarada en el SSOT, **When** se
  consultan los cinco consumidores (blancos estáticos del adaptador, corrida de
  cobertura, relajación de `check_naming`, `paths:` del CI generado y cruce de
  `sdd-doctor`), **Then** cada uno la deriva de ese SSOT filtrando por la
  propiedad que le corresponde, sin repetir la tupla de claves.

## Functional Requirements

- **FR-001** MUST: `core/render.py` sincroniza (copia byte a byte) desde
  `templates/` hacia el árbol del propio repo los 4 archivos duplicados:
  `docs/SDD-ENFORCEMENT.md`, `docs/playbooks/analyze.md`,
  `docs/playbooks/clarify.md`, `specs/SPEC-TEMPLATE.md`; con `--check` falla
  (exit 1) si alguno está desincronizado, igual que ya hace con
  `CONSTITUTION.md`/`SPEC-000-naming.md`.
- **FR-002** MUST: las entradas de sync de FR-001 son no-op (no leen ni
  escriben nada, no cuentan como drift) cuando el repo no tiene carpeta
  `templates/` en su raíz — así `render.py` vendorizado en un proyecto
  instalado no falla por archivos que ese proyecto nunca tuvo.
- **FR-003** MUST: `core/pipeline.py` agrega el paso de proceso `render`
  (corre `render.py --check`) a `PROCESS_STEPS`, y `.sdd/config.yaml` del kit
  lo declara en `pipeline.steps` para que el drift bloquee el pipeline local
  como cualquier otro paso.
- **FR-004** MUST: `templates/docs/SPEC-FORMAT.md` reemplaza el bloque
  "Template copiable" (contenido embebido) por una referencia a
  `specs/SPEC-TEMPLATE.md` como único archivo con el template real.
- **FR-005** SHOULD: los defaults `"src"` (fallback de `source_roots`) y
  `"tests/unit"` (fallback de `tests_unit`) quedan declarados una sola vez
  como constantes en `core/sdd_config.py`, e importados desde `core/sdd_gate.py`
  y `adapters/python/adapter.py` en vez de repetidos como literal.
- **FR-006** MUST: el vocabulario de pasos de código del contrato de adaptador
  está declarado una sola vez, en `core/sdd_config.py`. `core/pipeline.py` lo
  importa en vez de repetirlo, y un test cruza ese vocabulario contra el
  dispatcher del adaptador en **las dos direcciones**: un paso implementado y no
  declarado (el pipeline lo reporta "paso desconocido" y lo descuenta del total
  sin ruido, C-8) y un paso declarado y no implementado fallan la suite.
- **FR-007** MUST: las claves de carpetas de test de `dirs` están declaradas una
  sola vez, con las propiedades que distinguen a cada una: qué paso de pipeline
  la ejecuta y si entra a la corrida de cobertura. Los consumidores derivan de
  ese SSOT —blancos estáticos y corrida de cobertura del adaptador, relajación de
  reglas de `check_naming`, `paths:` del workflow que genera `render.py` y cruce
  de `sdd-doctor` contra `pipeline.steps`— y ninguno enumera las claves por su
  cuenta.

- **FR-008** MUST: los archivos de `templates/wiring/` que el kit también
  instala sobre sí mismo se sincronizan con el mismo mecanismo de FR-001
  (`templates/` autoritativo, destino nunca editado a mano, `--check` falla ante
  drift), resolviendo los placeholders de ruta según el layout. Alcanza a
  `.claude/settings.json`, `.claude/sdd_gate_hook.sh`, `.pre-commit-config.yaml`,
  `.gitattributes`, `.agents/hooks.json`, `.agents/agy_gate_hook.py`,
  `.agents/agy_deny.json` y `.opencode/plugin/sdd-gate.js`.
- **FR-010** MUST: el LF de esos destinos se sostiene en dos puntos, porque
  ninguno alcanza solo: `render.py` **escribe** LF aunque la plantilla tenga
  CRLF, y `.gitattributes` los declara `eol=lf` para que el **checkout** no los
  vuelva a CRLF (`* text=auto` lo haría en Windows, dejándolos distintos de lo
  que el render acaba de escribir, y `sh` no ejecuta un script con CRLF).
- **FR-011** MUST: una plantilla de `templates/wiring/` solo puede usar
  placeholders de ruta (`{{sdd.core}}`, `{{sdd.adapters}}`). Son los únicos que
  el sync resuelve: los de proyecto (`{{project.*}}`) los resuelve `sdd-init` al
  instalar, así que en el kit llegarían crudos al destino generado.
- **FR-012** MUST: al regenerar un destino declarado en
  `sdd_catalog.EXECUTABLE_WIRING`, `render.py` le deja el mismo permiso de
  ejecución que le dejaría `sdd-init`. `render.py` pasa a ser el tercer escritor
  de ese archivo y no puede degradar lo que los otros dos garantizan.
- **FR-013** MUST: el permiso de ejecución de los destinos de
  `sdd_catalog.EXECUTABLE_WIRING` se sostiene en **dos** puntos, porque ninguno
  alcanza solo — misma forma que FR-010 con el LF: `render.py` lo escribe
  (FR-012) y el **índice de git** lo declara (modo `100755`), para que un clon o
  un checkout fresco entregue el archivo ya ejecutable. Sin la segunda mitad, la
  garantía de FR-012 solo existe en la copia de trabajo donde alguien corrió el
  render en modo escritura, y se pierde en el primer checkout. El test que la
  cubre verifica el **índice**, no solo el disco: el disco es propiedad de una
  copia, el índice es lo que viaja.
- **FR-009** MUST: la clasificación de cada destino de `sdd_catalog.WIRING`
  —sincronizado con el kit, o excluido con su motivo— es explícita y vive junto
  al catálogo; `render.py` la deriva de ahí en vez de repetir la lista, y un test
  falla si un destino nuevo del catálogo no está clasificado de ninguno de los
  dos lados.
- **FR-014** MUST: `render_naming_spec` (el generador de `SPEC-000-naming.md`)
  omite por completo una sección de la lista —header, párrafo introductorio y
  bullets— cuando la lista que la alimenta (`naming_allowed` o
  `naming_relax_in_tests`) está vacía, en vez de emitir un placeholder
  `- (ninguno)` bajo un header sin contenido real. `SPEC-000-naming.md` es un
  archivo sincronizado (Key Entities): su única fuente de verdad es
  `.sdd/config.yaml`, y un header sin ítems no aporta información — ensucia el
  doc con estructura vacía en vez de reflejar fielmente el config.

## Key Entities

- **Archivo autoritativo**: el que un humano edita a mano (`templates/...`).
- **Archivo sincronizado**: el que `render.py` genera/verifica, nunca se edita
  a mano (`docs/...`, `specs/SPEC-TEMPLATE.md` en la raíz del kit).
- **Vocabulario de pasos** (`CODE_STEPS` en `core/sdd_config.py`): qué nombres de
  paso reserva el contrato para el adaptador. Es del núcleo, no del lenguaje: el
  lenguaje aporta la implementación de cada paso, no la lista.
- **Declaración de carpetas de test** (`TEST_DIRS` en `core/sdd_config.py`): por
  cada clave de `dirs`, qué paso la ejecuta y si entra a la medición de
  cobertura. Reemplaza a `TEST_DIR_STEP`, que cubría solo la primera pregunta.

- **Wiring sincronizado**: destino del catálogo (`sdd_catalog.WIRING`) que el kit
  instala sobre sí mismo y que `render.py` regenera desde su plantilla. Mismo
  contrato que "archivo sincronizado", pero el par no siempre es byte-idéntico:
  los placeholders de ruta resuelven distinto en el kit y en el derivado.
- **Excepción de wiring** (`WIRING_NO_SINCRONIZADO` en `core/sdd_catalog.py`):
  destino que el kit tiene con contenido legítimamente propio, con el motivo
  escrito. Existe para que "no está sincronizado" sea una decisión registrada y
  no un olvido.

## Success Criteria

- **SC-001** `python core/render.py --check` detecta drift introducido a mano
  en cualquiera de los 4 archivos sincronizados.
- **SC-002** El pipeline del kit (`python core/pipeline.py`) incluye `render`
  entre sus pasos y sale ROJO si hay drift.
- **SC-003** `grep -c '"src"' core/sdd_gate.py` y el equivalente de
  `"tests/unit"` en `adapters/python/adapter.py` bajan a cero literales
  propios (referencian la constante de `sdd_config`).
- **SC-004** `templates/docs/SPEC-FORMAT.md` ya no contiene el bloque
  markdown completo del template (verificable: el archivo baja de tamaño y
  el bloque ` ```markdown ` de la sección desaparece).
- **SC-005** Agregar un paso al dispatcher del adaptador sin declararlo en el
  vocabulario del núcleo (o al revés) pinta la suite en rojo, en vez de terminar
  como un "paso desconocido" que el pipeline descuenta del total en silencio.
- **SC-006** Agregar una clase de carpeta de test nueva se hace declarándola una
  vez con sus propiedades; ningún consumidor necesita editar una tupla propia, y
  ninguna carpeta queda arrastrada a un paso que no le corresponde por el solo
  hecho de estar declarada.

- **SC-007** Un arreglo del wiring se escribe **una sola vez** (en
  `templates/wiring/`) y llega al kit por `render.py`: `git diff` tras editar la
  plantilla y correr el render toca los dos archivos, y `--check` sale en rojo si
  solo se tocó uno. Verificable sobre el drift que motivó esto: el bloque
  `IS_ANTIGRAVITY` sobreviviente en `.claude/sdd_gate_hook.sh` desaparece al
  sincronizar, sin que nadie tenga que ir a buscarlo.
- **SC-008** **Ningún** archivo de `templates/wiring/` —los de hoy y los que se
  agreguen— contiene una ruta literal al andamiaje válida en un solo layout: o
  es `{{sdd.core}}`, o el archivo prueba ambos en runtime y está declarado como
  tal. Se verifica por barrido de la carpeta, no contra una lista escrita a
  mano: una lista sería la misma omisión que FR-009 existe para impedir.
- **SC-009** Un clon fresco del kit entrega `.claude/sdd_gate_hook.sh` ejecutable
  sin correr nada: `git ls-files -s .claude/sdd_gate_hook.sh` muestra `100755`.
  Antes mostraba `100644` y el bit solo aparecía tras un `render.py` en modo
  escritura, así que el test que lo afirmaba pasaba o fallaba según qué había
  corrido antes en esa copia de trabajo.

## Assumptions

- Los 4 archivos de FR-001 no tienen placeholders `{{project.*}}` (verificado
  por `grep`); si en el futuro alguno los necesita, sale de este mecanismo de
  copia literal y pasa a necesitar sustitución (fuera de alcance acá).
- No se toca `docs/IDEAS.md` como par de `templates/docs/IDEAS.md`: ese par
  es intencionalmente distinto (uno es el backlog real del kit, el otro es un
  esqueleto vacío para proyectos instalados) — no es duplicación, es plantilla
  con placeholder de contenido, no de sintaxis `{{}}`.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_render.py |
| FR-002 | tests/unit/test_render.py |
| FR-003 | tests/unit/test_pipeline_render_step.py |
| FR-004 | tests/unit/test_spec_format_reference.py |
| FR-005 | tests/unit/test_sdd_config.py |
| FR-006 | tests/unit/test_vocabulario_de_pasos.py |
| FR-007 | tests/unit/test_vocabulario_de_pasos.py |
| FR-008 | tests/unit/test_wiring_sincronizado.py; tests/unit/test_derived_references.py (el lado derivado: el placeholder resuelto al instalar) |
| FR-009 | tests/unit/test_wiring_sincronizado.py |
| FR-010 | tests/unit/test_wiring_sincronizado.py |
| FR-011 | tests/unit/test_wiring_sincronizado.py |
| FR-012 | tests/unit/test_wiring_sincronizado.py |
| FR-013 | tests/unit/test_wiring_sincronizado.py |
| FR-014 | tests/unit/test_render.py |

## Fuera de alcance

- R-2 tal como lo planteaba `docs/IDEAS.md` original también mencionaba
  `docs/SPEC-FORMAT.md` como posible duplicado propio del kit; se verificó
  que no existe tal copia (el kit referencia directo
  `templates/docs/SPEC-FORMAT.md` desde `00-INDEX.md`) — no hay nada que
  desduplicar ahí más allá del FR-004.
- G-6/G-8 (keyword `MUST/SHOULD/MAY` y trazabilidad FR→test) quedan fuera:
  son mejoras de `check_traceability.py`, no de duplicación de SSOT.
- E-1/E-2/E-3 (skills en destino, `sdd-update`, packaging) y G-7 (multi-spec
  en `current-spec`) quedan registrados en `docs/IDEAS.md`, fuera de esta
  spec.

## Historial

- 2026-08-01: creada (draft).
- 2026-08-01: implementada y promovida a `active`. `core/sdd_config.py` gana
  `DEFAULT_SOURCE_ROOT`/`DEFAULT_TESTS_UNIT`, reusados por `sdd_gate.py` y
  `adapters/python/adapter.py`; `templates/docs/SPEC-FORMAT.md` referencia
  `specs/SPEC-TEMPLATE.md` en vez de embeberlo; `core/render.py` sincroniza
  `docs/SDD-ENFORCEMENT.md`, `docs/playbooks/{analyze,clarify}.md` y
  `specs/SPEC-TEMPLATE.md` desde `templates/` (no-op sin carpeta `templates/`);
  `core/pipeline.py` suma el paso `render` (`render.py --check`), declarado en
  `.sdd/config.yaml`. Pipeline 9/9 VERDE, `sdd-doctor` sano, 62 tests.
- 2026-08-09: reabierta por C-8 de `docs/IDEAS.md`. FR-006/FR-007 extienden lo
  que FR-005 hizo con dos defaults a los dos vocabularios que el kit tenía
  repetidos: los pasos de código (`pipeline.CODE_STEPS` vs el dispatcher del
  adaptador, que ya se habían desincronizado al agregar `integration` en
  [[SPEC-019-tests-integracion-ejecutados]]) y las claves de carpetas de test
  (cuatro literales `("tests_unit", "tests_integration")` con criterios
  distintos). Prerequisito de [[SPEC-018-verificacion-e2e]] US3: sin separar
  "blancos estáticos" de "carpetas que se ejecutan", declarar `tests/e2e` la
  arrastraba a la corrida de cobertura.
- 2026-08-14: reabierta por R-4 de `docs/IDEAS.md`. FR-008..FR-011 llevan el
  mecanismo de FR-001 al wiring: los ocho destinos que el kit instala sobre sí
  mismo se generan desde `templates/wiring/`, y la lista sale de
  `sdd_catalog.WIRING` menos las excepciones declaradas. El par ya había
  divergido —`.claude/sdd_gate_hook.sh` conservaba el bloque `IS_ANTIGRAVITY`
  que la plantilla perdió en `fc95761`— y el sync lo borró solo. `{{sdd.core}}`
  se aplicó donde había una ruta válida en un solo layout
  (`.pre-commit-config.yaml`, plugin de opencode); el hook `sh` y el de
  Antigravity ya probaban ambos en runtime. El kit pasa a tener instalado
  `.opencode/plugin/sdd-gate.js`. El `/analyze` posterior agregó FR-010 (el LF
  se sostiene en render **y** en `.gitattributes`, con un test por mitad),
  FR-011 (el wiring solo admite placeholders de ruta) y convirtió la
  verificación de SC-008 en un barrido de la carpeta: la lista de cuatro
  archivos que tenía era la misma omisión que FR-009 existe para impedir.
  Después cerró los hallazgos menores: FR-012 (render era el único de los tres
  escritores del hook que no le devolvía el bit de ejecución), un test de que
  el plugin de opencode del kit apunta a un gate que existe —su modo de falla
  es callarse— y la baja de la duplicación en `test_wiring_prefiltros.py` y
  `test_wiring_precommit_verbose.py`, que seguían recorriendo el par kit +
  plantilla como si fueran dos archivos.
