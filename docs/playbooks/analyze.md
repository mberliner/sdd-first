# Playbook: analyze

Análisis **read-only** de adecuación de una spec (capa semántica del enforcement).
Adaptado de `/speckit.analyze`. **No modifica archivos.**

## Entrada

Una `SPEC-ID` como argumento. Si viene vacío, usá la primera línea de
`.sdd/current-spec`.

## Procedimiento

1. **Carga de contexto (revelación progresiva):**
   - Spec objetivo (`specs/<SPEC-ID>.md`): Functional Requirements (`FR-NNN`),
     Success Criteria (`SC-NNN`), User Stories y Coverage mapping.
   - Restricciones gobernantes: `CONSTITUTION.md` y `specs/SPECS_REGISTRY.md`.
   - Estándar de formato: `docs/SPEC-FORMAT.md`.
   - Código de verificación: tests referenciados en el Coverage mapping de la spec.

2. **Pasadas de detección (heurísticas de calidad):**
   - **Conflicto constitucional:** Cualquier requisito o decisión técnica que
     contradiga o diluya un principio de `CONSTITUTION.md`. Severidad obligatoria: `CRITICAL`.
   - **Cobertura semántica:** Requisitos declarados (`FR-NNN`) cuyos tests asociados
     en el Coverage mapping solo comprueban existencia formal/superficial o no
     validan el comportamiento real prometido.
   - **Ambigüedad:**
     - Adjetivos o atributos vagos sin criterios de aceptación medibles
       (ej. *"rápido"*, *"escalable"*, *"seguro"*, *"intuitivo"*, *"robusto"*, *"limpio"*).
     - Placeholders o marcas no resueltas (`TODO`, `TKTK`, `???`, `<placeholder>`).
     - Requisitos o criterios de aceptación interpretables de más de una forma.
   - **Subespecificación:**
     - Comportamiento implícito no declarado: errores/fallos, límites de datos,
       concurrencia, idempotencia o unicidad.
     - Requisitos con verbos transitivos sin objeto definido o sin resultado observable.
     - Referencias a componentes, entidades de datos o APIs no definidos en la spec ni en el sistema.
     - Criterios de éxito (`SC-NNN`): separar métricas de negocio post-lanzamiento
       (ej. *"aumentar adopción un 20%"*) de criterios técnicos verificables en la iteración.
   - **Inconsistencia y deriva terminológica:**
     - Contradicciones internas o con otras specs vigentes en `specs/SPECS_REGISTRY.md`.
     - *Terminology drift*: un mismo concepto del dominio nombrado de múltiples formas
       a lo largo del documento.

3. **Asignación de severidad:**
   - **CRITICAL:** Conflicto con la constitución o requisito central sin cobertura que
     bloquea la funcionalidad base.
   - **HIGH:** Conflicto directo entre requisitos, ambigüedad en seguridad/rendimiento o
     criterio de aceptación no testeable.
   - **MEDIUM:** Deriva terminológica, caso de borde subespecificado o cobertura semántica
     incompleta.
   - **LOW:** Mejoras de redacción o redundancia menor que no afecta la implementación.

## Eficiencia de tokens y límites

- Enfocate en hallazgos accionables de alta señal; evitá reportar trivialidades de estilo.
- Limitá la tabla a los **top 30 hallazgos** más relevantes. Si hay excedente, agrupalo
  en un resumen de desborde al pie.
- Asigná IDs estables prefijados con la inicial de la categoría:
  - `C` para Constitucional (`C1`, `C2`...)
  - `S` para Cobertura Semántica (`S1`, `S2`...)
  - `A` para Ambigüedad (`A1`, `A2`...)
  - `U` para Subespecificación (`U1`, `U2`...)
  - `I` para Inconsistencia (`I1`, `I2`...)

## Salida

Reportá en formato Markdown en la consola/sesión (sin escribir archivos):

1. **Tabla de hallazgos:**
   `ID | Categoría | Severidad | Ubicación | Resumen | Recomendación`
2. **Métricas de cierre:**
   Conteo de hallazgos por severidad (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) y total evaluado.
3. **Bloque "Próximos Pasos":**
   - Si existen hallazgos `CRITICAL`: advertir expresamente **no** iniciar la implementación
     ni desbloquear el gate hasta corregir la spec o resolver el conflicto constitucional.
   - Si solo hay `LOW` / `MEDIUM`: indicar que se puede proceder a la implementación
     (o invocar `clarify` si se desea pulir antes).
4. **Oferta de remediación:**
   Preguntar al usuario: *"¿Deseás que proponga sugerencias concretas de redacción para mitigar los hallazgos principales?"*
   (sin aplicar cambios automáticamente, manteniendo la propiedad estrictamente read-only).
