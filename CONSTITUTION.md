# Constitución del proyecto

**Proyecto:** sdd-first | **Dominio:** andamiaje SDD universal, agnostico y personalizable para otros proyectos

**Versión:** 0.3.0 | Ratificada: 2026-08-02 | Última enmienda: 2026-08-05

> Generado por `core/render.py` desde `.sdd/config.yaml`. La forma de cada
> principio (invariante + Enforcement + Detalle) es lo que valida
> `core/check_constitution.py`. Para enmendar, editá el config y regenerá.

## Preámbulo

- **Qué es:** la lista curada de los principios no-negociables de *este*
  proyecto. No es documentación de referencia ni el protocolo del asistente
  (`AGENTS.md`): es lo que nunca cede.
- **Cómo se usa:** se lee antes de diseñar una spec o encarar un cambio. Si
  una spec o una decisión de implementación entra en conflicto con un
  principio, **se ajusta la spec, no el principio**.
- **Alcance:** cada principio declara un **invariante** estable y
  autocontenido. El detalle operativo —que evoluciona— vive en el SSOT que
  el principio referencia en `Detalle:`. La constitución nunca duplica ese
  detalle: declara el invariante y apunta.

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

### IV. SSOT unico por tema

Toda pieza de informacion normativa —regla, definicion, cifra, tabla, convencion— vive en exactamente un documento, su SSOT; cualquier otro que la necesite la referencia, nunca la reproduce. El mismo invariante rige dentro de un documento: un detalle compartido por varias secciones se declara una vez y las secciones lo referencian.

- **Enforcement:** `AGENTS.md`
- **Detalle:** `00-INDEX.md`

## Governance

- **Versionado semver:** MAJOR remueve o redefine un principio; MINOR
  agrega un principio o una sección; PATCH aclara la redacción sin cambiar
  el invariante.
- **Fase pre-1.0:** mientras el proyecto no alcance madurez sostenida la
  serie es `0.y.z`: lo que tras `1.0.0` sería MAJOR o MINOR sube `y`; lo que
  sería PATCH sube `z`.
- **Precedencia:** un principio prevalece sobre cualquier spec o decisión de
  implementación. El protocolo del asistente (`AGENTS.md`) referencia esta
  constitución pero no la contiene: si se cambia de asistente, la
  constitución sigue vigente.
- **Procedimiento de enmienda:**
  1. Editá `principles` (y `constitution.version`) en `.sdd/config.yaml`,
     subiendo la versión según la regla de arriba y actualizando
     `constitution.amended`.
  2. Regenerá este documento: `python core/render.py`.
  3. Registrá el cambio en `historial/sdd.md` (qué principio, por qué).
  4. Revisá los SSOTs que referencia el principio afectado.
  5. Verificá: `python core/check_constitution.py CONSTITUTION.md`.
