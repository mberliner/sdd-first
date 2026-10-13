# Playbook: clarify

Detecta subespecificación en una spec mediante un diálogo interactivo de **hasta 5 preguntas** dirigidas de baja fricción, y graba las decisiones directamente en la spec. Adaptado de `/speckit.clarify`.
**Edita únicamente el archivo de la spec (`specs/<SPEC-ID>.md`), nunca el código fuente ni los tests.**

## Entrada

Una `SPEC-ID` como argumento (ej. `SPEC-015`). Si viene vacío, usá la primera línea de
`.sdd/current-spec`.

## Procedimiento

1. **Escaneo de ambigüedad por taxonomía (10 dimensiones):**
   Cargá la spec y evaluá cada área como **Clara / Parcial / Ausente**:
   - **Alcance y comportamiento funcional:** Objetivos centrales, límites expresos fuera de alcance y roles/personas diferenciados.
   - **Modelo de dominio y datos:** Entidades, atributos, unicidad/identidad, estados y ciclo de vida.
   - **Flujo de interacción y UX:** Caminos críticos de usuario y estados de error/vacío/carga.
   - **Calidad no funcional:** Requisitos de latencia, escalabilidad, confiabilidad, observabilidad y seguridad/privacidad.
   - **Integración y dependencias externas:** Servicios/APIs externas, fallos esperados y formatos de intercambio.
   - **Casos de borde y manejo de fallos:** Escenarios negativos, límites de tasa (*rate limits*) y concurrencia.
   - **Restricciones y compromisos técnicos:** Decisiones de arquitectura, stack tecnológico o trade-offs explícitos.
   - **Consistencia terminológica:** Glosario canónico, términos descartados y eliminación de sinónimos confusos.
   - **Criterios de completitud y testabilidad:** Verificabilidad de criterios de aceptación y Definition of Done.
   - **Placeholders y lenguaje vago:** Marcas no resueltas (`TODO`, `???`) y adjetivos ambiguos (*"robusto"*, *"rápido"*) sin cuantificar.

2. **Cola priorizada de preguntas (máximo 5):**
   - Construí una cola ordenada por **Impacto × Incertidumbre**.
   - Solo incluí preguntas cuya respuesta afecte materialmente la arquitectura, el modelo de datos, la descomposición de tareas o los tests de aceptación.
   - Excluí preferencias cosméticas o detalles de implementación interna que no afecten la corrección funcional.
   - Si no hay ambigüedades críticas, reportá que la spec es sólida y sugerí proceder directamente sin preguntar.

3. **Estándar de calidad en la formulación:**
   - **Regla anti-etiqueta:** La pregunta DEBE ser una oración interrogativa gramatical completa que termine en `?`. Jamás uses una etiqueta o ID como pregunta (ej. `"Matriz de dispositivos (FR-023)"` es inválido).
   - **Contexto obligatorio ("Por qué importa"):** Inmediatamente después de la pregunta, agregá una sola oración concisa en lenguaje claro que explique qué riesgo técnico, de producto o de testing mitiga responder esto ahora.

4. **Ciclo interactivo de baja fricción (opción recomendada por defecto):**
   - Presentá **exactamente una pregunta por vez**.
   - **Formato con opciones discretas (preferido):**
     - Analizá las alternativas según las mejores prácticas y restricciones del proyecto.
     - Destacá prominentemente la **opción recomendada** con justificación breve:
       `**Recomendado:** Opción A - <motivo conciso>`
     - Presentá la tabla de opciones:

       | Opción | Descripción |
       |--------|-------------|
       | A | <descripción opción A> |
       | B | <descripción opción B> |
       | C | <descripción opción C> |
       | Corta | Otra respuesta breve (≤5 palabras) |

     - Instrucción: *"Podés responder con la letra (ej. 'A'), aceptar la recomendación diciendo 'sí' o 'recomendado', o proveer una respuesta corta."*
   - **Formato de respuesta breve puntual (sin opciones discretas):**
     - Proponé una **respuesta sugerida** fundamentada:
       `**Sugerido:** <valor propuesto> - <motivo conciso>`
     - Instrucción: *"Podés aceptar la sugerencia diciendo 'sí' o 'sugerido', o proveer tu propia respuesta (≤5 palabras)."*
   - Si el usuario dice "sí", "recomendado" o "sugerido", adoptá la opción sugerida.
   - Detené el ciclo si:
     - Se resolvieron todas las ambigüedades críticas.
     - El usuario señala fin (*"listo"*, *"basta"*, *"avanzar"*).
     - Se alcanza el cupo máximo de 5 preguntas.

5. **Integración y propagación directa en la Spec:**
   - Por cada respuesta acordada:
     - Asegurá la sección `## Clarifications` y agregá bajo `### Session YYYY-MM-DD` el registro:
       `- Q: <pregunta>? → A: <respuesta>`
     - **Propagá el cambio a la sección pertinente de la spec:**
       - *Funcional:* agregá o actualizá el `FR-NNN` y su fila en el Coverage mapping.
       - *Datos:* actualizá entidades, atributos o estados en el modelo de datos.
       - *No funcional:* convertí el adjetivo vago en métrica verificable bajo Success Criteria (`SC-NNN`).
       - *Casos de borde:* agregá el escenario a la sección de errores o casos límite.
     - **Eliminá contradicciones:** si la respuesta invalida una frase preliminar o ambigua previa, reemplazala directamente. No dejes texto obsoleto.
   - Guardá la spec atómicamente tras cada integración para evitar pérdida de contexto.

6. **Reporte de cierre:**
   - Total de preguntas realizadas y respondidas.
   - Secciones modificadas de la spec.
   - Resumen de cobertura: dimensiones resueltas vs. diferidas (si se agotó el cupo de 5).
   - Próximo paso recomendado: avanzar a la implementación / tests (`sdd-spec` / TDD) o revisar.

## Límites

- **Edita únicamente el archivo de la spec (`specs/<SPEC-ID>.md`).**
- No toques `src/`, `core/`, `tests/` ni ninguna carpeta de código de producción. Este playbook solo perfecciona la spec.
