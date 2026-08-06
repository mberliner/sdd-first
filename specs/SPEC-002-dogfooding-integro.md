# SPEC-002: Dogfooding íntegro del kit

> Origen: ítems D-1..D-4 (P0) de `docs/IDEAS.md` (revisión crítica 2026-07-02).
> El kit debe cumplir su propio protocolo: gate cableado, tests propios,
> doctor en verde y SPEC-001 promovida al ciclo de vida documentado.

## User Story (Priority P1)

Como mantenedor de sdd-first, quiero que el kit cumpla íntegramente su propio
protocolo SDD (gate activo, tests, doctor sano, specs con ciclo de vida real)
para que el dogfooding sea creíble y cada regla que el kit impone a otros
proyectos esté demostrada sobre sí mismo.

**Why this priority:** la credibilidad del kit ES el dogfooding; hoy
`sdd-doctor` sale en rojo sobre el propio kit y el Principio III (gate
spec-first) está declarado pero sin enforcement.

**Independent Test:** `python core/sdd_doctor.py` exit 0 y
`python core/pipeline.py` VERDE con los pasos `tests` y `lint` incluidos.

## Clarifications

### Session 2026-07-02
- Q: ¿`00-INDEX.md` se crea en el kit o se parametriza el doctor? → A: se crea
  el índice del kit (menos invasivo; parametrizar los requeridos del doctor
  queda como idea en `docs/IDEAS.md`).
- Q: ¿Qué pasos de código se agregan al pipeline del kit? → A: `lint`,
  `format` y `tests` (ruff y pytest disponibles); `types`/`security` quedan
  como deuda (mypy --strict y bandit requieren trabajo de tipado aparte).

## Acceptance Scenarios

- **Given** el repo del kit sin spec vigente declarada, **When** un asistente
  intenta editar `core/`, **Then** el hook PreToolUse de `.claude/settings.json`
  ejecuta `sdd_gate.py` y bloquea con exit 2.
- **Given** el kit recién clonado con pytest y ruff instalados, **When** corre
  `python core/pipeline.py`, **Then** termina VERDE incluyendo `lint`,
  `format` y `tests`.
- **Given** el kit sano, **When** corre `python core/sdd_doctor.py`, **Then**
  exit 0 sin problemas.

## Functional Requirements

- **FR-001** MUST: el gate spec-first queda cableado en el propio kit vía
  `.claude/settings.json` (PreToolUse → `core/sdd_gate.py`) y
  `.pre-commit-config.yaml` (rutas `core/` y `adapters/`).
- **FR-002** MUST: existe `.sdd/current-spec` en el kit y el gate gobierna de
  hecho las ediciones de `core/` y `adapters/` — el kit se somete a su propio
  protocolo, con la política de [[SPEC-017-gate-decision-spec-first]].
- **FR-003** MUST: existe `tests/unit/` con tests de la lógica de decisión del
  núcleo: `sdd_gate.decide`, `check_traceability` (estructura, consistencia,
  coverage), `check_naming` (palabras excluidas, allowed, relax) y `sdd_config`
  (defaults, source_roots).
- **FR-004** MUST: `pipeline.steps` del kit incluye `lint`, `format` y
  `tests`, y el pipeline completo corre VERDE.
- **FR-005** MUST: existe `00-INDEX.md` del kit y `sdd-doctor` sale exit 0.
- **FR-006** MUST: SPEC-001 se promueve a formato `hibrido` y estado `active`,
  con FRs, SC y Coverage mapping hacia los tests de FR-003.
- **FR-007** SHOULD: el kit tiene `.gitattributes` forzando LF en artefactos
  generados (mismo wiring que instala en otros proyectos) y una copia local
  de `specs/SPEC-TEMPLATE.md` (hoy `sdd_spec.py` cae al fallback TODO porque
  la plantilla solo existe en `templates/`).

## Key Entities

- `.claude/settings.json`, `.pre-commit-config.yaml`, `.sdd/current-spec` —
  wiring del gate en el propio kit.
- `tests/unit/` — primera suite del kit.
- `00-INDEX.md` — índice de SSOTs del kit.
- `SPEC-001-agnostic-core.md` — spec promovida.

## Success Criteria

- **SC-001** `python core/sdd_doctor.py` → exit 0.
- **SC-002** `python core/pipeline.py` → VERDE con ≥7 pasos (constitution,
  traceability, naming, lint, format, skills, tests).
- **SC-003** `sdd_gate.py core/x.py` responde según la política vigente también
  cuando el proyecto gobernado es el propio kit (cubierto por test).
- **SC-004** SPEC-001 figura `active`/`hibrido` en el registro y pasa
  `check_traceability` (estructura + coverage).

## Assumptions

- pytest y ruff están disponibles en el entorno de desarrollo del kit (son
  dependencias de desarrollo, no del kit instalado; el config de otros
  proyectos no se ve afectado).
- Los pasos `types`/`security` del kit quedan fuera de alcance (deuda
  registrada en historial).

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_sdd_gate.py + verificación manual del wiring (sdd-doctor) |
| FR-002 | tests/unit/test_sdd_gate.py |
| FR-003 | tests/unit/test_sdd_gate.py, tests/unit/test_check_traceability.py, tests/unit/test_check_naming.py, tests/unit/test_sdd_config.py |
| FR-004 | pipeline VERDE (SC-002) |
| FR-005 | sdd-doctor exit 0 (SC-001) |
| FR-006 | tests/unit/test_check_traceability.py (valida el formato que SPEC-001 cumple) + SC-004 |
| FR-007 | verificación manual (git check-attr, sdd_spec usa la plantilla) |

## Fuera de alcance

- Bugs del happy path de instalación (B-1..B-4) → SPEC-003.
- Pasos `types`/`security` en el pipeline del kit.
- Parametrizar los artefactos requeridos de `sdd_doctor`.

## Historial

- 2026-07-02: creada (draft) desde D-1..D-4 de `docs/IDEAS.md`.
