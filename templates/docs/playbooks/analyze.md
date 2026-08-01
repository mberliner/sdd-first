# Playbook: analyze

Análisis **read-only** de adecuación de una spec (capa semántica del enforcement).
Adaptado de `/speckit.analyze`. **No modifica archivos.**

## Entrada

Una `SPEC-ID` como argumento. Si viene vacío, usá la primera línea de
`.sdd/current-spec`.

## Procedimiento

1. Cargá el contexto: la spec objetivo, `specs/SPECS_REGISTRY.md`,
   `CONSTITUTION.md`, `docs/SPEC-FORMAT.md` y los tests referenciados en el
   Coverage mapping de la spec.
2. Detectá y clasificá hallazgos en estas categorías:
   - **Conflicto constitucional** → siempre severidad CRITICAL.
   - **Cobertura semántica** — requisitos sin test que los verifique de verdad
     (más allá de la presencia en el Coverage mapping).
   - **Ambigüedad** — FR/SC interpretables de más de una forma.
   - **Subespecificación** — comportamiento implícito no declarado (ej. unicidad,
     concurrencia, errores).
   - **Inconsistencia** — contradicciones internas o con otras specs/registro.
3. Asigná severidad: CRITICAL / HIGH / MEDIUM / LOW.

## Salida

Una tabla Markdown con columnas: `ID | Categoría | Severidad | Ubicación |
Resumen | Recomendación`, seguida de un cierre con métricas (conteo por
severidad). No escribas en ningún archivo.
