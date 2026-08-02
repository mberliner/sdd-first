# Constitución del proyecto

**Versión:** 0.1.0 | Ratificada: 2026-08-02 | Última enmienda: 2026-08-02

> Generado por `core/render.py` desde `.sdd/config.yaml`. La forma de cada
> principio (invariante + Enforcement + Detalle) es lo que valida
> `core/check_constitution.py`. Para enmendar, editá el config y regenerá.

## Principios

### I. Nomenclatura agnostica a tecnologia

Ningun identificador del kit acopla a un proveedor o UI concretos.

- **Enforcement:** `check_naming.py`
- **Detalle:** `specs/SPEC-000-naming.md`

### II. Trazabilidad spec-codigo

Toda capacidad del kit tiene spec registrada antes de implementar.

- **Enforcement:** `check_traceability.py`
- **Detalle:** `specs/SPECS_REGISTRY.md`

### III. Gate spec-first

No se edita el nucleo del kit sin una spec vigente declarada.

- **Enforcement:** `sdd_gate.py`
- **Detalle:** `docs/SDD-ENFORCEMENT.md`

## Governance

- **Versionado:** semver. Fase pre-1.0 (serie `0.y.z`): los principios
  pueden cambiar entre minors sin ruptura formal.
- **Precedencia:** ningún cambio ni spec puede violar un principio. Si una
  spec entra en conflicto, se ajusta la spec, no el principio.
- **Enmienda:** editá `principles` en `.sdd/config.yaml`, regenerá con
  `python core/render.py`, y verificá con `python core/check_constitution.py
  CONSTITUTION.md`.
