# SPEC-005-desduplicar-ssot: Desduplicar SSOTs del kit (docs/templates, defaults)

> Origen: `docs/IDEAS.md` P2 "Duplicación de SSOT dentro del kit" (R-1, R-2,
> R-3), detectado en la revisión crítica del 2026-07-02.

## User Story (Priority P2)

Como mantenedor de sdd-kit, quiero que los documentos y defaults que hoy
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

## Key Entities

- **Archivo autoritativo**: el que un humano edita a mano (`templates/...`).
- **Archivo sincronizado**: el que `render.py` genera/verifica, nunca se edita
  a mano (`docs/...`, `specs/SPEC-TEMPLATE.md` en la raíz del kit).

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
