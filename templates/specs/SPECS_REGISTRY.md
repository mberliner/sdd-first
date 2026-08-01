# Registro de specs — {{project.name}}

> SSOT de specs vigentes. Toda spec en `specs/` debe estar acá con un Estado
> válido. `core/check_traceability.py` valida la consistencia disco↔registro.

## Convenciones

- **ID:** `SPEC-NNN-slug` (número correlativo + slug agnóstico).
- **Estados:** `draft` · `active` · `superseded` · `archived` · `notas`.
- **Formato:** `hibrido` (secciones de `docs/SPEC-FORMAT.md`) o `casero`.
  Solo las specs `hibrido` en estado `active` exigen Coverage mapping FR→test.
- Enlaces entre specs con `[[SPEC-NNN-slug]]`.

## Specs vigentes

| ID | Título | Estado | Iteración | Formato | Archivo |
|----|--------|--------|-----------|---------|---------|
| SPEC-000 | Nomenclatura agnóstica | active | 0 | casero | [SPEC-000-naming.md](SPEC-000-naming.md) |

## Roadmap / política de datos

- (Agregá acá el roadmap de specs y la política de datos del proyecto.)
