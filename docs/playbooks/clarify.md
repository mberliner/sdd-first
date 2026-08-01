# Playbook: clarify

Detecta subespecificación en una spec y hace **hasta 5 preguntas** dirigidas,
grabando las respuestas en la propia spec. Adaptado de `/speckit.clarify`.
**Edita la spec, nunca el código fuente.**

## Entrada

Una `SPEC-ID` como argumento. Si viene vacío, usá la primera línea de
`.sdd/current-spec`.

## Procedimiento

1. Escaneá la spec por taxonomía de ambigüedad (alcance, datos, errores,
   concurrencia, seguridad, rendimiento, UX…). Marcá cada área como
   **Clara / Parcial / Ausente**.
2. Construí una cola de preguntas priorizada por **Impacto × Incertidumbre**.
   Máximo 5.
3. Preguntá **una por vez** (usá `AskUserQuestion` si el asistente lo ofrece).
   Esperá la respuesta antes de la siguiente.
4. Integrá cada respuesta:
   - Grabala en `## Clarifications / ### Session YYYY-MM-DD` de la spec.
   - Si la respuesta convierte un requisito implícito en explícito, agregá el
     `FR-NNN` correspondiente (y su fila en el Coverage mapping si aplica).
5. Al terminar, resumí qué quedó clarificado y qué sigue pendiente.

## Límite

No toques `src/` ni ninguna carpeta de código. Este playbook solo mejora la spec.
