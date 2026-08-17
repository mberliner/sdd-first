# Registro de specs — sdd-first

> SSOT de specs vigentes del propio kit. `core/check_traceability.py` valida la
> consistencia disco↔registro.

## Convenciones

- **ID:** `SPEC-NNN-slug`.
- **Estados:** `draft` · `active` · `superseded` · `archived` (origen único:
  `core/check_traceability.VALID_ESTADOS` — SPEC-017 FR-US2-004).
- **Formato:** `hibrido` o `casero`. Solo `hibrido` + `active` exige Coverage mapping.

## Specs vigentes

| ID | Título | Estado | Iteración | Formato | Archivo |
|----|--------|--------|-----------|---------|---------|
| SPEC-000 | Nomenclatura agnóstica | active | 1 | casero | [SPEC-000-naming.md](SPEC-000-naming.md) |
| SPEC-001 | Núcleo agnóstico + adaptadores | active | 1 | hibrido | [SPEC-001-agnostic-core.md](SPEC-001-agnostic-core.md) |
| SPEC-002 | Dogfooding íntegro del kit | active | 1 | hibrido | [SPEC-002-dogfooding-integro.md](SPEC-002-dogfooding-integro.md) |
| SPEC-003 | Happy path de instalación | active | 5 | hibrido | [SPEC-003-install-happy-path.md](SPEC-003-install-happy-path.md) |
| SPEC-004 | Enforcement hardening (bootstrap hooks, reset post-commit, pre-commit robusto) | active | 12 | hibrido | [SPEC-004-enforcement-hardening.md](SPEC-004-enforcement-hardening.md) |
| SPEC-005 | Desduplicar SSOTs del kit (docs/templates, defaults, wiring) | active | 5 | hibrido | [SPEC-005-desduplicar-ssot.md](SPEC-005-desduplicar-ssot.md) |
| SPEC-006 | El gate verifica el estado (draft/active) de la spec declarada | superseded | 1 | hibrido | [SPEC-006-gate-verifica-estado-spec.md](SPEC-006-gate-verifica-estado-spec.md) |
| SPEC-007 | README propio y manual de operación SDD en el proyecto derivado | active | 1 | hibrido | [SPEC-007-derived-project-onboarding.md](SPEC-007-derived-project-onboarding.md) |
| SPEC-008 | Renombrar mensajes internos sdd-kit a sdd-first | draft | - | hibrido | [SPEC-008-rename-sdd-first.md](SPEC-008-rename-sdd-first.md) |
| SPEC-009 | Paso `coverage` con umbrales opcionales y plantilla de CI derivada del config | active | 7 | hibrido | [SPEC-009-coverage-y-ci.md](SPEC-009-coverage-y-ci.md) |
| SPEC-010 | Constitución con preámbulo y governance, principio de SSOT y rutas correctas en plantillas | active | 2 | hibrido | [SPEC-010-gobernanza-y-docs.md](SPEC-010-gobernanza-y-docs.md) |
| SPEC-011 | Onboarding del operador del kit: bootstrap reproducible en el README | active | 2 | hibrido | [SPEC-011-operator-bootstrap.md](SPEC-011-operator-bootstrap.md) |
| SPEC-012 | El pipeline del kit corre verde en Windows y POSIX | active | 2 | hibrido | [SPEC-012-suite-multiplataforma.md](SPEC-012-suite-multiplataforma.md) |
| SPEC-013 | Proyecto derivado coherente: principios elegidos y referencias disponibles | active | 6 | hibrido | [SPEC-013-proyecto-derivado-coherente.md](SPEC-013-proyecto-derivado-coherente.md) |
| SPEC-014 | El proyecto derivado dice la verdad sobre sí mismo (wiring, rutas, rama) | active | 6 | hibrido | [SPEC-014-derivado-dice-la-verdad.md](SPEC-014-derivado-dice-la-verdad.md) |
| SPEC-015 | El wiring del gate apunta al código real, en toda superficie que el kit soporta | active | 7 | hibrido | [SPEC-015-wiring-apunta-al-codigo-real.md](SPEC-015-wiring-apunta-al-codigo-real.md) |
| SPEC-016 | Las skills quedan usables apenas termina sdd-init | active | 4 | hibrido | [SPEC-016-skills-listas-tras-init.md](SPEC-016-skills-listas-tras-init.md) |
| SPEC-017 | Gate spec-first: qué decide bloquear una edición de código | active | 4 | hibrido | [SPEC-017-gate-decision-spec-first.md](SPEC-017-gate-decision-spec-first.md) |
| SPEC-018 | Verificación de punta a punta del kit instalado | active | 5 | hibrido | [SPEC-018-verificacion-e2e.md](SPEC-018-verificacion-e2e.md) |
| SPEC-019 | Los tests declarados se ejecutan o el proyecto se entera | active | 5 | hibrido | [SPEC-019-tests-integracion-ejecutados.md](SPEC-019-tests-integracion-ejecutados.md) |
| SPEC-020 | El enforcement de un principio se declara en el config y se verifica que haya corrido | active | 11 | hibrido | [SPEC-020-enforcement-declarado-en-config.md](SPEC-020-enforcement-declarado-en-config.md) |
| SPEC-021 | Una clave del config declarada pero vacía no rompe el pipeline | active | 5 | hibrido | [SPEC-021-config-vacio-no-rompe.md](SPEC-021-config-vacio-no-rompe.md) |
| SPEC-022 | Antes de crear una spec, reusar la existente que ya cubre la capacidad | active | 8 | hibrido | [SPEC-022-reusar-specs-existentes.md](SPEC-022-reusar-specs-existentes.md) |
| SPEC-023 | La relación entre specs se declara al crearlas y se verifica sola | active | 9 | hibrido | [SPEC-023-relacion-entre-specs.md](SPEC-023-relacion-entre-specs.md) |
| SPEC-024 | El Coverage mapping verifica que el FR referenciado aparezca en el test, no solo que el archivo exista | active | 10 | hibrido | [SPEC-024-traza-fr-en-test.md](SPEC-024-traza-fr-en-test.md) |
| SPEC-025 | El andamiaje instalado se puede actualizar sin perder lo propio | active | 1 | hibrido | [SPEC-025-actualizar-kit-en-derivados.md](SPEC-025-actualizar-kit-en-derivados.md) |
