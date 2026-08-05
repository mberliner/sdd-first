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

   La raíz del proyecto se busca por marcadores (`.sdd/config.yaml`,
   `CONSTITUTION.md`, `specs/SPECS_REGISTRY.md`) subiendo desde el `cwd` y, si
   ahí no aparece ninguno, desde la ruta del archivo que se va a editar. Lo que
   determina si hay protocolo que aplicar es **de qué proyecto es el archivo**:
   una edición dentro de un proyecto SDD queda gobernada por ese proyecto aunque
   el `cwd` del asistente apunte a otra parte, y una edición que no cae en ningún
   proyecto SDD se permite.

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

**Reset post-commit** (`core/sdd_reset.py`, hook `sdd-reset` en
`.pre-commit-config.yaml`, `stages: [post-commit]`): tras cada commit exitoso
limpia `.sdd/current-spec` dejando solo las líneas de comentario (`#`). Fuerza
declaración explícita al inicio de cada iteración en vez de dejar una spec
vieja "vigente" indefinidamente por descuido.

**Bootstrap automático de hooks git** (`core/bootstrap_hooks.py`, paso `hooks`
del pipeline, primero en `pipeline.steps`): git no instala hooks al clonar (por
diseño, seguridad), así que `pre-commit install --hook-type pre-commit
--hook-type post-commit` requiere un paso explícito. `bootstrap_hooks.py` lo
automatiza: verifica si ya están instalados (no toca los existentes), los
instala si faltan, es no-op con aviso sin `.git/`, y falla con instrucción
accionable si falta el paquete `pre-commit`. Como el protocolo obliga a correr
el pipeline al cerrar cada iteración, un clon nuevo queda reparado a más
tardar en su primer `core/pipeline.py` — antes del primer commit.

**`language: python`, no `system`, en los hooks locales de `pre-commit`**: los
hooks `sdd-gate`/`sdd-traceability`/`sdd-reset` usan `language: python` en vez
de `system`. Con `system`, pre-commit invoca el `python` que esté en el PATH
del shell que dispara el commit — el mismo problema que resolvió
`.claude/sdd_gate_hook.sh` para Claude Code, sin resolver a nivel git. Con
`language: python`, pre-commit gestiona su propio entorno aislado con un
intérprete que él mismo resuelve, así el hook corre igual en un sistema donde
solo existe `python3` (sin `python` en el PATH).

## Límite: presencia, no adecuación

El enforcement automático garantiza que *existe* una spec y que su estructura y
cobertura son íntegras. Que la spec sea *correcta y suficiente* es responsabilidad
de `analyze`/`clarify` y de la revisión humana.
