# Enforcement del SDD

> SSOT del mecanismo de enforcement. Explica cómo el kit obliga a que el código
> derive de una spec, en tres capas complementarias.

## Las tres capas

1. **Gate de autoría (preventivo)** — `core/sdd_gate.py`. Se dispara *antes* de
   editar código fuente. Bloquea la edición si no hay una spec vigente declarada
   en `.sdd/current-spec` con requisitos escritos (criterio abajo).
   Multi-transporte:
   - `PreToolUse` de Claude Code (stdin JSON) — `.claude/settings.json`.
   - `PreToolUse` de Antigravity CLI (stdin JSON) — `.agents/hooks.json`.
   - `pre-commit` (argv) — `.pre-commit-config.yaml`.
   - plugin opencode (argv) — `.opencode/plugin/sdd-gate.js`.

   Contrato: exit 0 permite, exit 2 bloquea. Las carpetas consideradas "código
   fuente" se leen de `dirs.source_roots` en `.sdd/config.yaml`.

   **Ninguna capa hardcodea `src/`.** El hook de `pre-commit` no lleva
   pre-filtro `files:`: le pasa todos los archivos staged al gate, que decide.
   Las dos capas que sí pre-filtran —la rama fail-closed de
   `.claude/sdd_gate_hook.sh` (cuando no hay ningún intérprete Python capaz de
   correr el gate) y el plugin de opencode (que decide si vale la pena invocar
   a Python)— derivan las carpetas del mismo `.sdd/config.yaml` con un parseo
   mínimo propio, porque no pueden consultar al gate. Ese pre-filtro decide *si
   preguntar*, no *qué política aplicar*: el SSOT de la política sigue siendo
   `sdd_gate.decide`, y un test de paridad verifica que las tres derivaciones
   coincidan. Si cambiás `dirs`, las tres capas se enteran solas.

   **Antigravity no pre-filtra**: su adaptador (`.agents/agy_gate_hook.py`) es
   Python, así que le pregunta al gate por cada edición y no duplica la
   derivación. A cambio tiene una regla propia, porque el CLI es **fail-open**
   —un hook que falla o cuya salida no parsea deja pasar la edición—: el
   adaptador sale siempre con 0 y siempre imprime
   `{"decision": "allow"|"deny"}`, traduciendo cualquier excepción a `deny`. Y
   como sin intérprete no hay adaptador que corra, el `command` de
   `.agents/hooks.json` termina en `type agy_deny.json || cat agy_deny.json`:
   un deny total (no filtrado por `source_roots`) servido desde archivo, porque
   un `echo` no sobrevive al escapado de `cmd.exe`. Las rutas de ese comando son
   relativas a `.agents/`, que es el `cwd` con el que Antigravity lo invoca.

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
declaración de intención y exige, a **cada** spec listada:

1. que exista como `specs/<ID>.md`,
2. que figure como fila de `SPECS_REGISTRY.md` con estado `draft` o `active`,
3. que tenga **requisitos escritos**: al menos un `**FR-NNN**` con texto propio
   además del keyword. Los placeholders de `specs/SPEC-TEMPLATE.md` no cuentan,
   así que una spec recién creada no desbloquea nada hasta escribir los FR.

El criterio es de **contenido, no de marcas de tiempo**. El original comparaba la
mtime de la spec contra la de este archivo, y fallaba en las dos direcciones:
bloqueaba el flujo legítimo —trabajar una spec en varios commits, `git checkout`,
`clone`, y el propio ciclo stash/restore de `pre-commit`, que renueva mtimes— y no
detenía a nadie, porque un `touch` lo satisfacía. Consecuencia práctica: **para el
segundo commit de una misma spec alcanza con redeclararla**, sin volver a tocarla.

Que los requisitos sean *adecuados* al cambio en curso sigue siendo juicio de
`analyze`/`clarify` (ver "Límite: presencia, no adecuación").

**Escape hatch** (`SDD_GATE_BYPASS`): con un valor no vacío, el gate imprime el
bloqueo que correspondería, agrega el motivo del bypass y devuelve exit 0. Es la
alternativa acotada a `--no-verify`, que apaga *todo* el `pre-commit` —gate,
trazabilidad y reset— y deja al repositorio sin enforcement en vez de saltear un
caso puntual.

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

## Límite conocido: escritura por `Bash`

El hook `PreToolUse` de Claude Code cubre las tools de edición estructurada
(`Edit`, `Write`, `MultiEdit`, `NotebookEdit`), que son las que declaran qué
archivo tocan. **No cubre `Bash`**: un `echo ... > pkg/x.py` no declara
`file_path` en su payload y no dispara el gate. Interceptarlo exigiría parsear
la línea de comando, con falsos positivos garantizados.

No es un agujero abierto, es un corrimiento de capa: ese archivo igual queda
bajo el gate de `pre-commit` al commitear y bajo el pipeline al cerrar la
iteración. Lo que se pierde es la advertencia *en el momento*, no el
enforcement.

El mismo límite aplica a Antigravity, y ahí se lo vio en vivo: al recibir el
`deny`, el asistente intentó escribir el archivo con una tool de terminal.

## Límite: presencia, no adecuación

El enforcement automático garantiza que *existe* una spec y que su estructura y
cobertura son íntegras. Que la spec sea *correcta y suficiente* es responsabilidad
de `analyze`/`clarify` y de la revisión humana.
