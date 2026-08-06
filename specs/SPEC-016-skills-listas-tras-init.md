# SPEC-016-skills-listas-tras-init: Las skills quedan usables apenas termina sdd-init

> Origen: reporte de uso del 2026-08-06 — "en el README no figura `sdd-configure`
> en el derivado, sólo está en comentarios; y hay que implementar las skills para
> usar por parte de los asistentes luego de `sdd-init`". Verificado con una
> instalación limpia: tras `sdd_init.py` el destino tiene `.agents/skills/` pero
> **no** `.claude/skills/` ni `.opencode/command/`, así que Claude Code y opencode
> no ven ninguna skill SDD.

## User Story (Priority P0)

Como dueño de un proyecto recién instalado con sdd-first, quiero que las skills
SDD (`sdd-configure`, `sdd-doctor`, `sdd-spec`, `analyze`, `clarify`) estén
disponibles en mi asistente **apenas termina `sdd-init`**, y que el README las
nombre como parte del flujo y no dentro de un comentario, para poder pedirle a mi
asistente que configure el proyecto en vez de editar YAML a mano.

**Why this priority:** el propio instalador cierra diciendo *"Edita
`.sdd/config.yaml` … o corre la skill `sdd-configure`"*, y esa skill todavía no
existe para el asistente en ese momento: los adaptadores se generan recién en el
paso 3 (`gen_skill_adapters.py`), dos pasos después de que se la ofrece. El
primer consejo que da el kit al usuario nuevo es, literalmente, imposible de
seguir. Mismo problema en el README: `sdd-configure` aparece sólo como comentario
`#` dentro del bloque bash del paso 3, mientras los comandos visibles instruyen
editar el config a mano — de las cinco skills instaladas, ninguna se nombra como
paso ejecutable del onboarding.

**Independent Test:** en un destino limpio, correr únicamente
`python core/sdd_init.py <destino>` y verificar que existen
`<destino>/.claude/skills/sdd-configure/SKILL.md` y
`<destino>/.opencode/command/sdd-configure.md`, y que
`python tools/sdd/core/gen_skill_adapters.py --check` sale 0 sin haber corrido
nunca el generador a mano.

## Clarifications

### Session 2026-08-06
- Q: ¿generar los adaptadores dentro de `sdd-init`, o dejar el paso manual y sólo
  documentarlo mejor? → A: generarlos en `sdd-init`. Un paso manual necesario
  para que funcione lo que el propio instalador recomienda en el paso anterior no
  es documentación faltante, es un orden imposible. Además el paso 3 no aportaba
  ninguna decisión del usuario: siempre se corre igual, con los mismos insumos.
- Q: ¿qué pasa con la idempotencia — `sdd-init` no pisa archivos del proyecto? →
  A: los adaptadores son **artefactos generados** (llevan cabecera
  `NO EDITAR A MANO`) y el paso `skills` del pipeline los verifica con `--check`;
  conservar una versión ajena sería dejar el pipeline en ROJO desde la
  instalación. Se escriben siempre, como hace `render.py` con `CONSTITUTION.md`.
  Lo que sigue sin pisarse es la fuente (`.agents/skills/*/SKILL.md`).
- Q: ¿se elimina el paso 3 de la secuencia de cierre y del README? → A: sí como
  paso obligatorio del onboarding; el comando queda documentado en
  `SKILLS-MULTITOOL.md` (su SSOT) para cuando se agrega o edita una skill.
- Q: ¿el README del kit o el del derivado? → A: los dos, con roles distintos. El
  del kit (sección "Cómo se usa") promueve `sdd-configure` a paso numerado y
  visible; el del derivado (`templates/README.md`) sólo apunta a
  `docs/SDD-OPERACION.md`, que es el SSOT del catálogo de skills — no repite la
  lista.

## Acceptance Scenarios

- **Given** un directorio destino limpio, **When** se corre `sdd_init.py` y nada
  más, **Then** existen `.claude/skills/<skill>/SKILL.md` y
  `.opencode/command/<skill>.md` para las cinco skills de `PROJECT_SKILLS`, y no
  existe ninguna para `sdd-init` (que no se instala en el derivado).
- **Given** ese mismo destino, **When** se corre
  `python tools/sdd/core/gen_skill_adapters.py --check`, **Then** sale 0 (sin
  drift): lo que sembró el instalador es exactamente lo que genera el generador.
- **Given** un destino donde ya existe un `.claude/skills/analyze/SKILL.md` con
  contenido distinto, **When** se corre `sdd_init.py` sin `--force`, **Then** el
  adaptador se reescribe igual (es artefacto generado) y el log lo informa.
- **Given** la salida de cierre del instalador, **When** el operador la lee,
  **Then** la secuencia no incluye `gen_skill_adapters.py` como paso pendiente y
  sí dice que las skills quedaron disponibles y cuáles son.
- **Given** el `README.md` del kit, **When** se busca `sdd-configure`, **Then**
  aparece fuera de todo comentario `#`, como paso del onboarding, junto con la
  aclaración de que las skills quedan instaladas por `sdd-init`.
- **Given** el `README.md` instalado en el derivado, **When** su dueño lo lee,
  **Then** encuentra el puntero a `docs/SDD-OPERACION.md` para saber qué skills
  tiene y cuándo usar cada una.

## Functional Requirements

- **FR-001** MUST: `core/gen_skill_adapters.py` expone la generación como función
  invocable con una raíz explícita (`generate(repo_root, check=False)`), en vez de
  resolverla sólo desde el `cwd` en `main()`. `main()` pasa a ser una envoltura
  fina sobre ella, sin duplicar la lógica.
- **FR-002** MUST: `core/sdd_init.py` genera los adaptadores de skills en el
  destino al final de la instalación, para las skills de `PROJECT_SKILLS`, y lista
  cada archivo escrito en el log de instalación.
- **FR-003** MUST: la generación de FR-002 escribe siempre los adaptadores, con o
  sin `--force` (son artefactos generados y verificados por `--check`), sin tocar
  las fuentes `.agents/skills/*/SKILL.md`, que sí respetan la idempotencia.
- **FR-004** MUST: si la generación falla (fuente inválida, playbook faltante), la
  instalación **no** aborta: informa el problema en la salida y sigue, incluyendo
  el comando manual para reintentar. Un adaptador que no se pudo generar no puede
  dejar a medias un andamiaje ya copiado.
- **FR-005** MUST: `_next_steps` deja de listar `gen_skill_adapters.py` como paso
  pendiente y renumera la secuencia; a cambio informa que las skills quedaron
  disponibles y las nombra, indicando que el catálogo está en
  `docs/SDD-OPERACION.md`.
- **FR-006** MUST: `_next_steps` presenta `sdd-configure` como la vía recomendada
  del primer paso (configurar el proyecto), con la edición manual del config como
  alternativa.
- **FR-007** MUST: el `README.md` del kit nombra `sdd-configure` fuera de
  comentarios, como paso del onboarding del derivado, y enumera las skills que
  quedan instaladas y para qué sirve cada una a alto nivel.
- **FR-008** MUST: `templates/README.md` (el README que recibe el derivado)
  apunta a `docs/SDD-OPERACION.md` como catálogo de las skills SDD disponibles,
  sin duplicar la lista.
- **FR-009** MUST: `templates/docs/SKILLS-MULTITOOL.md` documenta que los
  adaptadores los siembra `sdd-init` y que `gen_skill_adapters.py` se corre a mano
  sólo al agregar o editar una skill.

## Key Entities

- `.agents/skills/<name>/SKILL.md` — fuente editable de cada skill, instalada por
  `sdd-init` de forma idempotente.
- `.claude/skills/<name>/SKILL.md` y `.opencode/command/<name>.md` — adaptadores
  **generados**; su SSOT es la fuente de arriba. Sin ellos, Claude Code y opencode
  no descubren ninguna skill SDD.
- `PROJECT_SKILLS` (`core/sdd_init.py`) — qué skills recibe un derivado. Excluye
  `sdd-init`, que es bootstrap de una sola vez.

## Success Criteria

- **SC-001** Una instalación limpia con un solo comando (`sdd_init.py`) deja las
  cinco skills descubribles por Claude Code y por opencode, verificado sobre el
  árbol de archivos y no sólo por el log.
- **SC-002** `gen_skill_adapters.py --check` sale 0 en un destino recién instalado
  sin haber corrido el generador a mano.
- **SC-003** `sdd-configure` aparece en el `README.md` del kit en al menos una
  línea que no empieza con `#` dentro de un bloque de código.
- **SC-004** El pipeline del kit sigue VERDE y `sdd-doctor` sigue reportando la
  instalación sana.

## Assumptions

- El destino recibe siempre los playbooks (`docs/playbooks/<name>.md`) antes de la
  generación: `STATIC_DOCS` se copia primero en `main()`, y `_validate` los exige.
- Los adaptadores generados son deterministas (LF forzado por `write_text_lf`), así
  que sembrarlos desde el instalador y regenerarlos después produce bytes idénticos.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_gen_skill_adapters.py |
| FR-002, FR-003 | tests/unit/test_sdd_init_skills.py |
| FR-004 | tests/unit/test_sdd_init_skills.py |
| FR-005, FR-006 | tests/unit/test_sdd_init_next_steps.py |
| FR-007 | tests/unit/test_readme_bootstrap.py |
| FR-008, FR-009 | tests/unit/test_derived_references.py |
| SC-002 | tests/unit/test_sdd_init_skills.py |

## Fuera de alcance

- Adaptadores para asistentes nuevos (Cursor, Aider, Gemini CLI): E-5 de
  `docs/IDEAS.md` sigue abierto y es una decisión de alcance del kit, no de
  onboarding.
- Instalar `sdd-init` como skill del derivado: sigue siendo bootstrap de una sola
  vez (decisión de SPEC-007).
- Que `sdd-configure` corra sin asistente (modo CLI no interactivo). Hoy es un
  playbook para un agente; convertirlo en script propio es otra spec.
- C-7 de `docs/IDEAS.md` (validación de flags de `sdd_init`), aunque toque el mismo
  `main()`.

## Historial

- 2026-08-06: creada (draft).
- 2026-08-06: implementada y pasada a `active`. `gen_skill_adapters.generate()`
  ahora recibe la raíz explícita y devuelve un `Result` (escritos / drift /
  problemas) en vez de imprimir, lo que permite que `sdd_init` lo reuse sin
  subproceso ni cambio de directorio. La secuencia de cierre bajó de cuatro pasos
  a tres y nombra las cinco skills; el README del kit ganó una sección propia para
  `sdd-configure` con la tabla de las skills instaladas. Verificado sobre una
  instalación limpia: los quince archivos de skill (5 fuentes + 5 adaptadores de
  Claude + 5 commands de opencode) quedan en su lugar con un solo comando,
  `gen_skill_adapters.py --check` sale 0 sin haber corrido el generador a mano,
  `sdd-doctor` reporta sano y el pipeline del derivado sale VERDE. Kit: 251 tests
  y pipeline 10/10 VERDE.
