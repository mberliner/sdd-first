# SPEC-003: Happy path de instalación

> Origen: ítems B-1..B-4 (P0/P1) de `docs/IDEAS.md`, reproducidos en sandbox
> el 2026-07-02. Un proyecto recién instalado con `sdd-init` debe arrancar con
> pipeline VERDE y las herramientas del kit no deben romper sus propios
> artefactos.

## User Story (Priority P1)

Como usuario nuevo del kit, quiero que la instalación recién sembrada corra el
pipeline en VERDE y que `sdd-spec` deje el registro bien formado, para confiar
en el kit desde el primer minuto en vez de arrancar depurándolo.

**Why this priority:** hoy una instalación fresca sale ROJO 6/10 y la primera
spec creada rompe la tabla del registro — es la primera impresión del kit.

**Independent Test:** `sdd-init` en un directorio vacío + render + gen +
pipeline → VERDE sin instalar tooling extra; `sdd_spec.py` en ese proyecto
agrega la fila dentro de la tabla del registro.

## Clarifications

### Session 2026-07-02
- Q: ¿Cómo evitar el ROJO por tooling ausente (B-3)? → A: doble medida: el
  config sembrado declara solo los pasos que funcionan out-of-the-box
  (proceso + naming + tests), y el adaptador python omite con aviso (exit 0)
  los pasos cuya tool no está instalada, imitando el trato de
  `language: none`. El config de ejemplo completo sigue mostrando los 10 pasos.
- Q (descubierto al verificar): el set mínimo sin `layers` hace fallar
  `check_constitution` (el principio II del ejemplo declara `lint-imports`
  como enforcement y exige el paso cableado). → A: `layers` se siembra
  igualmente; sin import-linter instalado, el adaptador lo omite con aviso.
- Q: ¿Relax de naming (B-2): por basename o por config? → A: por config: un
  target se considera "de tests" si su ruta está bajo alguno de los dirs de
  tests declarados (`tests_unit`, `tests_integration`), con fallback al
  basename `tests`/`test` para proyectos sin dirs declarados.

## Acceptance Scenarios

- **Given** un directorio vacío, **When** corre `sdd-init` + render + gen +
  pipeline, **Then** el pipeline sale VERDE (pasos de código sin targets o sin
  tool se omiten con aviso, no fallan).
- **Given** un proyecto con `csv` en `relax_in_tests` y tests en
  `tests/unit/`, **When** corre el paso `naming`, **Then** los identificadores
  con `csv` en tests no se reportan.
- **Given** el registro plantilla (con sección Roadmap después de la tabla),
  **When** `sdd_spec.py` registra una spec nueva, **Then** la fila queda
  dentro de la tabla de `## Specs vigentes`, antes del Roadmap.

## Functional Requirements

- **FR-001** MUST: `adapters/python/adapter.py` con cero targets existentes
  para un paso lo omite con aviso y exit 0 (no invoca la tool sin argumentos).
- **FR-002** MUST: la relajación de tokens en tests aplica a los directorios
  de tests declarados en el config (`dirs.tests_unit`/`tests_integration`),
  no solo a roots con basename `tests`/`test`.
- **FR-003** MUST: `sdd_spec.py` inserta la fila nueva al final de la tabla
  de `## Specs vigentes` del registro (última línea `|` contigua), no al final
  del archivo.
- **FR-004** MUST: los pasos de código cuya tool no está instalada se omiten
  con aviso y exit 0 en el adaptador python (paridad con `language: none`).
- **FR-005** MUST: el config sembrado por `sdd_init.py` declara solo pasos
  operativos out-of-the-box: constitution, traceability, naming, layers,
  skills, tests; los demás quedan comentados con instrucción de habilitarlos
  (`layers` se incluye porque el principio II del ejemplo lo exige cableado;
  sin import-linter se omite con aviso).
- **FR-006** SHOULD: el README aclara qué tooling requiere cada paso de
  código del adaptador python (ruff, mypy, bandit, pytest, import-linter).

## Key Entities

- `adapters/python/adapter.py` — omisión por targets/tool ausentes.
- `adapters/python/check_naming.py` — relax por dirs de tests del config.
- `core/sdd_spec.py` — inserción de fila en tabla.
- `core/sdd_init.py` — config sembrado con pasos operativos.

## Success Criteria

- **SC-001** Instalación fresca en sandbox → pipeline VERDE (antes: ROJO 6/10).
- **SC-002** Token relajado en `tests/unit/` no reporta violación (antes: 2
  violaciones con el config de ejemplo).
- **SC-003** Registro instalado sigue siendo una tabla markdown válida tras
  `sdd_spec.py` (fila dentro de la tabla).
- **SC-004** El kit sigue VERDE 7/7 (sin regresión de SPEC-002).

## Assumptions

- pytest sí se considera tooling base razonable para el paso `tests` (si no
  está, FR-004 lo omite con aviso).
- El config de ejemplo (`examples/config/config.yaml`) conserva los 10 pasos
  como referencia completa; solo cambia el sembrado por defecto.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_python_adapter.py |
| FR-002 | tests/unit/test_check_naming.py, tests/unit/test_python_adapter.py |
| FR-003 | tests/unit/test_sdd_spec.py |
| FR-004 | tests/unit/test_python_adapter.py |
| FR-005 | verificación manual: install sandbox → pipeline VERDE (SC-001) |
| FR-006 | verificación manual (README) |

## Fuera de alcance

- Endurecimiento del gate (G-1..G-7) → SPEC-004.
- Skills `sdd-*` en el proyecto instalado (E-1) → SPEC-006.

## Historial

- 2026-07-02: creada (draft) desde B-1..B-4 de `docs/IDEAS.md`.
