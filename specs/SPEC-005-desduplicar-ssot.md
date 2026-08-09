# SPEC-005-desduplicar-ssot: Desduplicar SSOTs del kit (docs/templates, defaults)

> Origen: `docs/IDEAS.md` P2 "Duplicación de SSOT dentro del kit" (R-1, R-2,
> R-3), detectado en la revisión crítica del 2026-07-02.

## User Story (Priority P2)

Como mantenedor de sdd-first, quiero que los documentos y defaults que hoy
existen duplicados dentro del propio repo tengan un único archivo autoritativo
(el resto se genera o referencia), para que una edición futura no pueda dejar
`docs/` y `templates/docs/` (o dos constantes de código) divergiendo en
silencio — justo lo que el Principio "No duplicar SSOT" de `AGENTS.md`
prohíbe.

**Why this priority:** hoy no rompe nada en caliente (P2, no P0/P1), pero es
deuda que compone: cada edición manual a uno de los duplicados y no al otro
es un drift que nadie detecta hasta que alguien lee las dos versiones y no
coinciden.

**Independent Test:** correr `python core/render.py --check` sobre el propio
kit reporta drift si se edita a mano `docs/SDD-ENFORCEMENT.md`,
`docs/playbooks/analyze.md`, `docs/playbooks/clarify.md` o
`specs/SPEC-TEMPLATE.md` sin tocar su contraparte en `templates/`; el paso
`render` del pipeline falla en ese caso.

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
