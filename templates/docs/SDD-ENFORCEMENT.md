# Enforcement del SDD

> SSOT del mecanismo de enforcement. Explica cómo el kit obliga a que el código
> derive de una spec, en tres capas complementarias.

## Las tres capas

1. **Gate de autoría (preventivo)** — `core/sdd_gate.py`. Se dispara *antes* de
   editar código fuente. Bloquea la edición si no hay una spec vigente declarada
   en `.sdd/current-spec` y editada *después* de declararla. Multi-transporte:
   - `PreToolUse` de Claude Code (stdin JSON) — `.claude/settings.json`.
   - `pre-commit` (argv) — `.pre-commit-config.yaml`.
   - plugin opencode (argv) — `.opencode/plugin/sdd-gate.js`.

   Contrato: exit 0 permite, exit 2 bloquea. Las carpetas consideradas "código
   fuente" se leen de `dirs.source_roots` en `.sdd/config.yaml`.

2. **Backstop determinista** — `core/check_traceability.py` en el pipeline.
   Verifica *estructura* (secciones obligatorias), *consistencia* disco↔registro
   y *cobertura* FR→test en specs `active`. No juzga adecuación.

3. **Capa semántica** — las skills `analyze` y `clarify`. Aportan el juicio de
   *adecuación* (¿la spec describe BIEN el cambio?) que los scripts deterministas
   no dan. `analyze` es read-only; `clarify` hace ≤5 preguntas y graba respuestas
   en la spec.

## `.sdd/current-spec`

Archivo de una línea por spec vigente (SPEC-NNN-slug). El gate lo usa como
declaración de intención: comparás la mtime de la spec contra la de este archivo
para forzar el flujo **declarar → editar la spec → editar el código**.

## Límite: presencia, no adecuación

El enforcement automático garantiza que *existe* una spec y que su estructura y
cobertura son íntegras. Que la spec sea *correcta y suficiente* es responsabilidad
de `analyze`/`clarify` y de la revisión humana.
