# Registro de specs — sdd-first

> SSOT de specs vigentes del propio kit. `core/check_traceability.py` valida la
> consistencia disco↔registro.

## Convenciones

- **ID:** `SPEC-NNN-slug`.
- **Estados:** `draft` · `active` · `superseded` · `archived` · `notas`.
- **Formato:** `hibrido` o `casero`. Solo `hibrido` + `active` exige Coverage mapping.

## Specs vigentes

| ID | Título | Estado | Iteración | Formato | Archivo |
|----|--------|--------|-----------|---------|---------|
| SPEC-000 | Nomenclatura agnóstica | active | 1 | casero | [SPEC-000-naming.md](SPEC-000-naming.md) |
| SPEC-001 | Núcleo agnóstico + adaptadores | active | 1 | hibrido | [SPEC-001-agnostic-core.md](SPEC-001-agnostic-core.md) |
| SPEC-002 | Dogfooding íntegro del kit | active | 1 | hibrido | [SPEC-002-dogfooding-integro.md](SPEC-002-dogfooding-integro.md) |
| SPEC-003 | Happy path de instalación | active | 1 | hibrido | [SPEC-003-install-happy-path.md](SPEC-003-install-happy-path.md) |
| SPEC-004 | Enforcement hardening (bootstrap hooks, reset post-commit, pre-commit robusto) | active | 1 | hibrido | [SPEC-004-enforcement-hardening.md](SPEC-004-enforcement-hardening.md) |
| SPEC-005 | Desduplicar SSOTs del kit (docs/templates, defaults) | active | 1 | hibrido | [SPEC-005-desduplicar-ssot.md](SPEC-005-desduplicar-ssot.md) |
| SPEC-006 | El gate verifica el estado (draft/active) de la spec declarada | active | 1 | hibrido | [SPEC-006-gate-verifica-estado-spec.md](SPEC-006-gate-verifica-estado-spec.md) |
| SPEC-007 | README propio y manual de operación SDD en el proyecto derivado | active | 1 | hibrido | [SPEC-007-derived-project-onboarding.md](SPEC-007-derived-project-onboarding.md) |
| SPEC-008 | Renombrar mensajes internos sdd-kit a sdd-first | draft | - | hibrido | [SPEC-008-rename-sdd-first.md](SPEC-008-rename-sdd-first.md) |
| SPEC-009 | Paso `coverage` con umbrales opcionales y plantilla de CI derivada del config | active | 2 | hibrido | [SPEC-009-coverage-y-ci.md](SPEC-009-coverage-y-ci.md) |
| SPEC-010 | Constitución con preámbulo y governance, principio de SSOT y rutas correctas en plantillas | active | 2 | hibrido | [SPEC-010-gobernanza-y-docs.md](SPEC-010-gobernanza-y-docs.md) |
| SPEC-011 | Onboarding del operador del kit: bootstrap reproducible en el README | active | 2 | hibrido | [SPEC-011-operator-bootstrap.md](SPEC-011-operator-bootstrap.md) |
| SPEC-012 | El pipeline del kit corre verde en Windows y POSIX | active | 2 | hibrido | [SPEC-012-suite-multiplataforma.md](SPEC-012-suite-multiplataforma.md) |
| SPEC-013 | Proyecto derivado coherente: principios elegidos y referencias disponibles | active | 2 | hibrido | [SPEC-013-proyecto-derivado-coherente.md](SPEC-013-proyecto-derivado-coherente.md) |
