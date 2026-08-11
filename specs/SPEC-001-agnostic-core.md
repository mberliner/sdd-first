# SPEC-001: Núcleo agnóstico + adaptadores por lenguaje

> Promovida a formato híbrido en la iteración SPEC-002 (antes: casero/draft).
> Cubre el núcleo ya implementado del kit.

## User Story (Priority P1)

Como equipo que adopta SDD, quiero un núcleo de validadores agnóstico de
lenguaje y dominio, parametrizado por un único config, para instalar la misma
disciplina de specs en cualquier proyecto sin reescribir tooling.

**Why this priority:** es la capacidad fundacional del kit; todo lo demás
(skills, plantillas, gates) se apoya en esta separación núcleo/adaptador.

**Independent Test:** `python core/pipeline.py` corre los pasos declarados en
`.sdd/config.yaml`, delegando los de código al adaptador del lenguaje activo,
y sale VERDE/ROJO según el resultado agregado.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** [SPEC-024](SPEC-024-traza-fr-en-test.md) | **Es dependencia de:** [SPEC-022](SPEC-022-reusar-specs-existentes.md) | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

## Clarifications

### Session 2026-07-01
- Q: ¿Formato del config? → A: YAML (tooling parejo cross-ecosistema).
- Q: ¿Qué pasa con `language: none`? → A: los pasos de código se omiten con
  aviso (modo doc-solo: solo gates de proceso).
- Q: ¿El gate es un paso del pipeline? → A: no; se cablea por hooks
  (PreToolUse / pre-commit / plugin opencode) y lo verifica `sdd-doctor`.

## Acceptance Scenarios

- **Given** un config con `pipeline.steps` mixtos, **When** corre el pipeline,
  **Then** los pasos de proceso los ejecuta el núcleo y los de código se
  delegan a `adapters/<language>/adapter.py <step>`.
- **Given** un hook de cualquiera de los tres transportes, **When** invoca
  `core/sdd_gate.py`, **Then** obtiene la misma decisión y el contrato 0/2
  (escenarios de la política: [[SPEC-017-gate-decision-spec-first]]).
- **Given** una spec `hibrido`+`active` con un FR sin fila en el Coverage
  mapping, **When** corre `check_traceability`, **Then** reporta la violación.

## Functional Requirements

- **FR-001** MUST: toda parametrización (naming, dirs, capas, principios,
  pasos) se lee de `.sdd/config.yaml` vía `core/sdd_config.py`, con defaults
  tolerantes para configs parciales; nada de listas hardcodeadas en `core/`.
  "Tolerante" incluye el caso límite de la clave declarada pero vacía o
  malformada, que colapsa al mismo resultado que la clave ausente: su SSOT es
  [[SPEC-021-config-vacio-no-rompe]].
- **FR-002** MUST: `core/sdd_gate.py` decide sobre las ediciones de archivos
  bajo `dirs.source_roots` con el contrato exit 0 permite / exit 2 bloquea,
  agnóstico del asistente que lo invoque. La política —qué hace falta para
  autorizar una edición— es la de
  [[SPEC-017-gate-decision-spec-first]], su SSOT.
- **FR-003** MUST: `core/check_traceability.py` valida estructura de specs
  híbridas (User Story+prioridad, FR-NNN, SC-NNN, Coverage mapping),
  consistencia disco↔registro y cobertura FR→test en specs `active`.
- **FR-004** MUST: `core/check_constitution.py` valida que cada principio
  tenga Enforcement y Detalle con referencias existentes, y que el enforcement
  mapeado a un paso esté cableado en `pipeline.steps`.
- **FR-005** MUST: los validadores de código se delegan al adaptador según el
  contrato `adapters/CONTRACT.md` (`adapter.py <step>`, exit 0 = OK / 3 =
  omitido / otro = falla); el
  adaptador `python` implementa naming (AST + palabras excluidas del config), layers,
  lint, format, types, security y tests.
- **FR-006** MUST: `core/gen_skill_adapters.py` genera los adaptadores de
  skills de Claude y opencode desde el SSOT `.agents/skills/`, con `--check`
  de drift determinista.
- **FR-007** MUST: `core/render.py` genera `CONSTITUTION.md` y
  `specs/SPEC-000-naming.md` desde el config, con `--check` de drift.

## Key Entities

- `.sdd/config.yaml` — SSOT de parámetros (ver `examples/config/config.yaml`).
- `core/` — validadores de proceso + orquestador + generadores.
- `adapters/<language>/` — validadores de código por lenguaje.
- `.sdd/current-spec` — declaración de intención que consume el gate.

## Success Criteria

- **SC-001** El mismo `core/` corre sin modificación en el kit y en un
  proyecto instalado (vendorizado bajo `tools/sdd/`), cambiando solo el config.
- **SC-002** El gate corre con el mismo `core/` en el kit y en un derivado, y
  cada bloqueo llega a stderr con un motivo específico (los casos concretos los
  fija [[SPEC-017-gate-decision-spec-first]]).
- **SC-003** `check_traceability` reporta específicamente: sección faltante,
  FR sin cobertura, test inexistente, spec no registrada, entrada colgante y
  estado inválido.
- **SC-004** Los artefactos generados (skills, constitución, SPEC-000) no
  driftean: sus `--check` pasan tras regenerar, en Windows y Linux (LF).

## Assumptions

- Python 3.11+ y pyyaml disponibles donde corre el andamiaje (única
  dependencia del núcleo; las tools de los pasos de código son del proyecto).
- Adaptadores `node`/`go`: fuera de alcance (roadmap, ver historial).

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_sdd_config.py |
| FR-002 | tests/unit/test_sdd_gate.py |
| FR-003 | tests/unit/test_check_traceability.py |
| FR-004 | pipeline del kit (paso `constitution` en verde sobre CONSTITUTION.md generado) |
| FR-005 | tests/unit/test_check_naming.py (naming); resto de pasos: verificación manual vía pipeline |
| FR-006 | pipeline del kit (paso `skills` con `--check` en verde) |
| FR-007 | sdd-doctor (drift de render en verde) |

## Fuera de alcance

- Adaptadores `node`/`go` (solo contrato documentado).
- Juicio de *adecuación* de specs (lo aportan `analyze`/`clarify`).

## Historial

- 2026-07-01: creada (draft, formato casero) durante el bootstrap v0.1.0.
- 2026-07-02: promovida a hibrido/active con FRs, SC y Coverage mapping
  (SPEC-002 FR-006).
- 2026-08-05: FR-005 enmendado — el contrato de adaptador pasa de `exit 0/≠0` a
  tres estados (`0` OK, `3` omitido, otro falla). Lo exige SPEC-003 FR-009: con
  dos estados, un paso omitido era indistinguible de un paso verificado. El
  detalle del contrato vive en `adapters/CONTRACT.md` (SSOT).
- 2026-08-10: FR-001 enlazado a [[SPEC-021-config-vacio-no-rompe]]. No cambia el
  requisito: le da destino explícito al caso límite de la clave vacía, que
  quedaba descrito en dos specs sin referencia entre sí (Principio de SSOT único).
