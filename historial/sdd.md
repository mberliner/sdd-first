# Historial SDD — sdd-kit

## 2026-08-01 — SPEC-006: El gate verifica el estado de la spec declarada (G-2 de docs/IDEAS.md)

**Scope:** cerrar un bypass real del gate spec-first: `_spec_is_valid` en
`core/sdd_gate.py` validaba una spec declarada con `spec_id in
registry.read_text(...)` — un substring match sobre el texto crudo del
registro. Una spec `archived`/`superseded` (o solo mencionada en prosa, p. ej.
en un roadmap fuera de la tabla) desbloqueaba el gate igual que una `active`,
rompiendo la garantía central del kit ("no se edita código sin spec vigente").

**Hecho:**
- `core/sdd_gate.py`: `_spec_is_valid` reemplazada por `_registry_row` +
  `_spec_invalid_reason`, que parsean la fila real del registro (reusando
  `check_traceability._parse_registry`, sin duplicar el parser) y exigen
  `estado` en `{draft, active}`. El mensaje de bloqueo ahora distingue "no
  existe el archivo", "no está registrada" y "estado 'X' no vigente".
- Tests nuevos en `test_sdd_gate.py` (archived, superseded, mención solo en
  prosa, estado active) — suite: 66 tests.
- Verificado además con una instalación real vendorizada en `/tmp` (no solo
  tests unitarios): los tres escenarios (archived bloquea, active permite,
  mención en prosa bloquea) reproducen igual que en los tests.

**Deuda:** ninguna nueva; `docs/IDEAS.md` mantiene G-1 (pre-commit hardcodea
`files:`), G-3..G-8 y E-1..E-6 para specs futuras.

## 2026-08-01 — SPEC-005: Desduplicar SSOTs del kit (R-1, R-2, R-3 de docs/IDEAS.md)

**Scope:** eliminar la duplicación de archivos y defaults dentro del propio
repo que "No duplicar SSOT" prohíbe: `docs/` vs `templates/docs/`
(`SDD-ENFORCEMENT.md`, playbooks `analyze`/`clarify`), `specs/SPEC-TEMPLATE.md`
duplicado dos veces (archivo + embebido en prosa en `SPEC-FORMAT.md`), y los
literales `"src"`/`"tests/unit"` repetidos como fallback en `sdd_gate.py` y
`adapter.py`.

**Hecho:**
- `core/sdd_config.py`: nuevas constantes `DEFAULT_SOURCE_ROOT` (`"src"`) y
  `DEFAULT_TESTS_UNIT` (`"tests/unit"`); `sdd_gate.py` y
  `adapters/python/adapter.py` las importan en vez de repetir el literal.
- `templates/docs/SPEC-FORMAT.md`: la sección "Template copiable" ya no
  embebe el template completo — referencia `specs/SPEC-TEMPLATE.md` como
  único archivo fuente.
- `core/render.py`: además de generar `CONSTITUTION.md`/`SPEC-000-naming.md`
  desde el config, ahora sincroniza (copia byte a byte, `--check` detecta
  drift) `docs/SDD-ENFORCEMENT.md`, `docs/playbooks/analyze.md`,
  `docs/playbooks/clarify.md` y `specs/SPEC-TEMPLATE.md` desde `templates/`
  — pero solo cuando el repo tiene su propia carpeta `templates/` (el caso
  del kit dogfoodeando sobre sí mismo); en un proyecto instalado con
  `sdd-init` (sin `templates/`) estas entradas son no-op.
- `core/pipeline.py`: nuevo paso de proceso `render` (corre
  `render.py --check`), agregado a `PROCESS_STEPS` y a `pipeline.steps` en
  `.sdd/config.yaml` del kit — el drift entre `templates/` y sus copias ahora
  bloquea el pipeline como cualquier otro paso.
- Tests nuevos: `test_render.py`, `test_pipeline_render_step.py`,
  `test_spec_format_reference.py`, más una prueba en `test_sdd_config.py`
  que verifica que `sdd_gate` y `adapter` reusan la misma constante (no la
  repiten) — suite: 62 tests.

**Deuda:** ninguna nueva; `docs/IDEAS.md` mantiene registradas G-8 (idea del
usuario sobre trazabilidad FR→test), E-1/E-2/E-3 (skills en destino,
`sdd-update`, packaging) y G-7 (multi-spec en `current-spec`) para specs
futuras.

## 2026-08-01 — SPEC-004: Enforcement hardening (comparación con evaluador-flujo-intent)

**Scope:** cerrar dos huecos reales del gate spec-first descubiertos al
comparar con `evaluador-flujo-intent` (proyecto que corrió el gate más tiempo
en producción): `.sdd/current-spec` podía quedar vigente indefinidamente, y un
`git clone` nuevo no tenía los hooks git instalados hasta que alguien corría
`pre-commit install` a mano. De paso, mismo bug del `python` no encontrado que
ya se había resuelto para Claude Code/opencode (sesión anterior), sin resolver
en la capa `pre-commit`.

**Hecho:**
- `core/bootstrap_hooks.py` (nuevo): instala hooks `pre-commit`/`post-commit`
  si faltan, idempotente, no-op sin `.git/`. Wireado como paso `hooks` en
  `core/pipeline.py` (primero en `PROCESS_STEPS`) y en `_SEEDED_STEPS` de
  `sdd_init.py` (primer paso sembrado en proyectos nuevos).
- `core/sdd_reset.py` (nuevo): limpia `.sdd/current-spec` tras cada commit
  exitoso, dejando solo comentarios. Wireado como hook `sdd-reset`
  (`stages: [post-commit]`) en `.pre-commit-config.yaml` (kit) y
  `templates/wiring/.pre-commit-config.yaml` (plantilla instalada).
- `.pre-commit-config.yaml` y `templates/wiring/.pre-commit-config.yaml`:
  `language: system` → `language: python` (+ `additional_dependencies:
  [pyyaml]`) en los hooks locales — pre-commit gestiona su propio intérprete
  aislado, ya no depende de que el shell invocador tenga `python` en el PATH.
- `docs/SDD-ENFORCEMENT.md` (+ su copia en `templates/docs/`): documenta las
  tres piezas nuevas.
- Tests nuevos: `test_bootstrap_hooks.py`, `test_sdd_reset.py`,
  `test_pipeline_hooks_step.py`, `test_sdd_init_seeded_steps.py`,
  `test_sdd_gate_hook.py` (cubre `.claude/sdd_gate_hook.sh` y
  `templates/wiring/sdd_gate_hook.sh`, ramas normal y fail-closed) — suite:
  53 tests.
- Validado con `pre-commit run --all-files` real (no solo tests unitarios:
  crea el venv aislado, instala `pyyaml`, ambos hooks corren y pasan) y con
  instalación fresca vía `sdd_init.py` en directorio temporal.

**Deuda:**
- No se portaron los coverage gates (`--cov-fail-under`) ni el wiring de
  ruff/mypy como hooks de pre-commit — quedó fuera de alcance de este
  hardening (ver "Fuera de alcance" en SPEC-004).

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
