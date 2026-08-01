# Historial SDD — sdd-kit

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
