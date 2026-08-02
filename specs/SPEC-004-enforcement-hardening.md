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
`.sdd/current-spec` con solo comentarios; el hook `sdd-gate` de pre-commit
sigue bloqueando aunque `python` no esté en el PATH (solo `python3`).

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
  `templates/wiring/current-spec` — el working tree no queda sucio después
  del commit.

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
  o reemplaza la línea del spec-id, nunca pisa el archivo entero. Cierra el
  hueco por el que `sdd_reset.py` (FR-002) no tenía comentarios que preservar
  tras un ciclo real declarar→commitear→reset.

## Key Entities

- `.sdd/current-spec` — archivo de declaración de spec vigente; ahora tiene
  ciclo de vida completo: declarar → editar → commitear → reset.
- Hooks git (`pre-commit`, `post-commit`) — instalados vía el paquete
  `pre-commit`, gestionados por `bootstrap_hooks.py`.

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
  commitea → corre `sdd-reset`, `.sdd/current-spec` queda idéntico al header
  de la plantilla — `git status` no lo marca modificado.

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
  G-7 de `docs/IDEAS.md` (parcialmente resuelto — la semántica multi-spec
  sigue pendiente). Pipeline 9/9 VERDE, 70 tests.
