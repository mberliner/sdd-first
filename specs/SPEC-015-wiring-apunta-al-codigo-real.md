# SPEC-015-wiring-apunta-al-codigo-real: El wiring del gate apunta al codigo real, en toda superficie que el kit soporta

> Origen: G-1 y G-3 de `docs/IDEAS.md`, reproducidos en un proyecto real por la
> campaña de usabilidad del 2026-08-05 (testigo con código en `pkg/`, que no
> matchea `^(src|app|lib)/` y nunca llega al gate). Las tres specs que los
> mencionaron —SPEC-003, SPEC-006 y SPEC-014— los declararon explícitamente
> fuera de alcance; esta los toma.

## User Story (Priority P0)

Como mantenedor de un proyecto instalado con sdd-first cuyo código **no** vive
en `src/`, quiero que todas las capas de wiring del gate (pre-commit, hook de
Claude Code, plugin de opencode) reconozcan como código fuente lo que declara
`dirs.source_roots` de mi config, para que el gate spec-first proteja mi código
real en vez de una carpeta de ejemplo que ni existe en mi repo.

**Why this priority:** el gate es el Principio de enforcement central del kit y
`sdd_gate.py` ya lee `source_roots` correctamente — pero **ninguna de las tres
capas que lo invocan lo hace**: todas pre-filtran contra `src/` (o
`^(src|app|lib)/`) hardcodeado. El efecto medido en la campaña es un derivado
que reporta el gate cableado y sano mientras deja pasar cualquier commit sobre
su código. Es la misma clase de falso positivo que cerró SPEC-014, en la única
superficie que quedó sin cubrir, y además viola el "No hardcodear listas" del
propio `AGENTS.md`.

**Independent Test:** en un proyecto instalado cuyo `dirs.source_roots` es
`[pkg]`, un `git commit` que toca `pkg/x.py` sin spec vigente es **bloqueado**
por pre-commit; y con Python inaccesible, la rama fail-closed del hook de Claude
también bloquea una edición de `pkg/x.py` (hoy ambas la permiten).


## User Story 2: Soporte para asistentes IA (Antigravity)

Como mantenedor de un proyecto instalado con sdd-first, quiero que el soporte para Antigravity CLI quede unificado con el de Claude Code y con las capas de enforcement, para tener el mismo nivel de proteccion sin tener que duplicar logica de hooks.

**Why this priority:** Antigravity CLI soporta pre-tool hooks via `.agents/hooks.json`, lo que permite replicar la contencion exacta del gate antes de editar. Expandir el soporte asegura que proyectos usando Antigravity tengan el mismo enforcement que los de Claude.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

## Clarifications

### Session 2026-08-05
- Q: ¿cómo obtienen los `source_roots` las capas que pre-filtran **sin poder
  invocar el gate** (rama fail-closed de `sdd_gate_hook.sh` y el plugin de
  opencode)? → A: leyendo `.sdd/config.yaml` desde el propio hook con un parser
  mínimo (builtins de `sh`; `fs` + regex en JS). Descartado inyectar la lista al
  instalar vía placeholder (crea una copia que driftea si los `source_roots`
  cambian después) y descartado el fail-closed total sin pre-filtro (deja un
  checkout sin Python inutilizable para editar, cuando hoy se permite fuera de
  los roots justamente para que sea reparable).
- Q: ¿y en pre-commit, donde Python **sí** está disponible? → A: ahí no se
  parsea nada: se elimina el pre-filtro `files:`. `sdd_gate.decide` ya devuelve
  "permitir" para toda ruta que no sea código fuente (`_is_source_path`), así
  que el filtro es redundante y su única función hoy es equivocarse. Cero drift
  por construcción, que es mejor que sincronizar una copia.
- Q: si el pre-filtro de las capas sin Python duplica la regla de derivación de
  `source_roots`, ¿no es duplicar SSOT? → A: es una aproximación deliberada y
  acotada (decide *si preguntar*, no *qué política aplicar* — el SSOT de la
  política sigue siendo `sdd_gate.py`), y la duplicación se ata con un test de
  paridad que compara la salida del parser de cada capa contra
  `SddConfig.source_roots` sobre los mismos configs.
- Q: ¿se amplía el matcher del hook de Claude a `Bash`? → A: no. El payload de
  `Bash` no declara `file_path`; interceptarlo exige parsear la línea de comando
  y es una superficie distinta. Se amplía a las tools de edición estructurada y
  el bypass por `Bash` queda documentado como límite conocido, con pre-commit
  como backstop.

## Acceptance Scenarios

- **Given** un proyecto instalado con `dirs.source_roots: [pkg]` y sin spec
  vigente declarada, **When** se commitea un cambio en `pkg/x.py`, **Then**
  el hook `sdd-gate` de pre-commit corre sobre ese archivo y bloquea el commit.
- **Given** ese mismo proyecto, **When** se commitea un cambio en `README.md`,
  **Then** el gate corre pero permite el commit (no es código fuente).
- **Given** un proyecto con `dirs.source_roots: [pkg]` y ningún intérprete
  Python ejecutable, **When** Claude Code intenta editar `pkg/x.py`, **Then**
  `sdd_gate_hook.sh` bloquea (exit 2) por su rama fail-closed; **y** si la
  edición es sobre `docs/nota.md`, la permite (exit 0).
- **Given** un `.sdd/config.yaml` sin `dirs.source_roots` explícito pero con
  `dirs.domain: pkg/domain`, **When** el pre-filtro de cualquier capa deriva los
  roots, **Then** obtiene `pkg` — el mismo valor que `SddConfig.source_roots`.
- **Given** un proyecto sin `.sdd/config.yaml` legible, **When** la rama
  fail-closed pre-filtra, **Then** cae al default `src` sin romperse.
- **Given** el hook `PreToolUse` de Claude Code, **When** la edición llega por
  `MultiEdit` o `NotebookEdit` en vez de `Edit`/`Write`, **Then** el gate se
  ejecuta igual.

## Functional Requirements

- **FR-001** MUST: `.pre-commit-config.yaml` (del kit) y
  `templates/wiring/.pre-commit-config.yaml` (plantilla instalada) no declaran
  `files:` en el hook `sdd-gate`: todos los archivos staged se pasan al gate y
  `sdd_gate._is_source_path` decide cuáles son código fuente según
  `dirs.source_roots`.
- **FR-002** MUST: `templates/wiring/sdd_gate_hook.sh` y
  `.claude/sdd_gate_hook.sh` derivan las carpetas de código de
  `.sdd/config.yaml` en su rama fail-closed, en vez del `case *'"src/'*` fijo.
  El parseo usa solo builtins POSIX (`while read`, `case`, `printf`) —sin
  comandos externos, para que un PATH roto no pueda tumbar la rama fail-closed—
  y cae al default `src` si el config no existe o no declara nada.
- **FR-003** MUST: `templates/wiring/opencode-sdd-gate.js` y
  `.opencode/plugin/sdd-gate.js` reemplazan `isUnderSrc`/`resolveSrcPath`
  hardcodeados a `src/` por la misma derivación desde `.sdd/config.yaml`
  (`fs` + regex, sin dependencias), con el mismo default.
- **FR-004** MUST: la derivación de FR-002/FR-003 replica la regla de
  `SddConfig.source_roots`: si existe `dirs.source_roots` (lista en bloque o
  inline) esa es la lista; si no, el primer componente de cada valor de `dirs:`
  excluyendo `tests_unit`/`tests_integration`/`source_roots`; si no hay nada,
  `src`.
- **FR-005** MUST: existe un test de paridad que, para un conjunto de configs
  representativos (roots explícitos inline y en bloque, roots implícitos,
  `dirs:` vacío, config ausente), compara la lista derivada por cada pre-filtro
  contra `SddConfig.source_roots` y falla ante cualquier divergencia. El caso
  del plugin JS se omite con aviso si no hay `node` disponible.
- **FR-006** MUST: `templates/wiring/claude-settings.json` y
  `.claude/settings.json` usan el matcher `Edit|Write|MultiEdit|NotebookEdit`
  en el hook `PreToolUse`.
- **FR-007** MUST: `docs/SDD-ENFORCEMENT.md` (SSOT del enforcement, sincronizado
  desde `templates/docs/`) documenta que el pre-filtro de cada capa deriva de
  `dirs.source_roots`, y registra el bypass por `Bash` (`echo > pkg/x.py`) como
  límite conocido del hook de Claude, con pre-commit y el pipeline como
  backstop.


- **FR-US2-001** MUST: `sdd_init` debe instalar el wiring de Antigravity en proyectos derivados. El archivo `templates/wiring/hooks.json` debe agregarse a la constante `_WIRING` en `core/sdd_init.py` (copiándolo a `.agents/hooks.json`).
- **FR-US2-002** MUST: La ruta del script del gate en `hooks.json` debe ser `CLAUDE_PROJECT_DIR=$(pwd) sh .claude/sdd_gate_hook.sh`, apuntando a la ubicación real donde `sdd_init` deposita el hook unificado.
- **FR-US2-003** MUST: El soporte de Antigravity en `core/sdd_gate.py` (extraer `toolCall.args.TargetFile`) y `sdd_gate_hook.sh` (emitir JSON `{"decision": "allow"|"deny"}` al stdout) debe estar cubierto por tests en `tests/unit/`.
- **FR-US2-004** MUST: El hook de shell debe ejecutar `cd "$ROOT" || exit 1` antes de la lógica principal para que el fallback de `find_sdd_root` (CWD) resuelva correctamente en Antigravity, que provee rutas relativas sin el context-dir en el payload.
- **FR-US2-005** MUST: `sdd_doctor` debe conocer `.agents/hooks.json` en `GATE_WIRING` dentro de `core/sdd_config.py` para reportar que está cableado en la instalación.

## Key Entities

- `dirs.source_roots` (`.sdd/config.yaml`) — SSOT de qué es código fuente para
  el enforcement. Ya lo leían `sdd_gate.py` y los checks del adaptador; ahora
  también las tres capas de wiring.
- Pre-filtro — decisión barata y local de *si vale la pena consultar al gate*.
  No es la política spec-first (SSOT: `sdd_gate.decide`); puede ser conservador,
  nunca laxo.

## Success Criteria

- **SC-001** En un proyecto instalado con el código fuera de `src/`, un commit
  sin spec vigente que toca ese código es bloqueado por pre-commit — verificado
  sobre un testigo real, no solo por test unitario.
- **SC-002** Ninguna de las tres capas de wiring (kit y plantilla) contiene la
  cadena `src` como carpeta de código hardcodeada; `grep` sobre
  `templates/wiring/` y el wiring del kit no encuentra `^(src|app|lib)/` ni
  `case *'"src/'*` ni `isUnderSrc`.
- **SC-003** El test de paridad de FR-005 pasa en verde para los cinco casos de
  config declarados.
- **SC-004** El pipeline del kit sigue VERDE y `sdd-doctor` sigue reportando el
  wiring cableado tras el cambio (el doctor verifica que cada archivo invoque al
  gate, SPEC-014 FR-US1-002 — quitar `files:` no debe romper esa detección).

## Assumptions

- `pre-commit` pasando todos los archivos staged al gate tiene costo
  despreciable: es un único proceso Python por commit y `_is_source_path` es
  comparación de rutas en memoria.
- `sh` está disponible para el test de paridad del hook (Git Bash en Windows,
  shell POSIX en el resto); `node` puede no estarlo y ese caso se omite.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_wiring_prefiltros.py |
| FR-002 | tests/unit/test_sdd_gate_hook.py |
| FR-003 | tests/unit/test_wiring_prefiltros.py |
| FR-004, FR-005 | tests/unit/test_prefilter_source_roots.py |
| FR-006 | tests/unit/test_wiring_prefiltros.py |
| FR-007 | tests/unit/test_wiring_prefiltros.py |
| FR-US2-001 | tests/unit/test_wiring_prefiltros.py |
| FR-US2-002 | tests/unit/test_wiring_prefiltros.py |
| FR-US2-003 | tests/unit/test_sdd_gate.py, tests/unit/test_sdd_gate_hook.py |
| FR-US2-004 | tests/unit/test_sdd_gate_hook.py |
| FR-US2-005 | tests/unit/test_wiring_prefiltros.py |
| SC-002 | tests/unit/test_wiring_prefiltros.py |

## Fuera de alcance

- Interceptar `Bash` en el hook de Claude Code (payload sin `file_path`; exige
  parsear la línea de comando). Queda documentado como límite conocido por
  FR-007.
- Sincronizar el wiring del kit desde `templates/wiring/` con `render.py`. Los
  hooks shell se unificaron y ahora son byte-idénticos (US2 resuelve dinámicamente
  la ruta del script), pero la automatización de la copia queda diferida. Se
  registra como idea nueva en `docs/IDEAS.md` en vez de ampliar esta spec.
- El resto de los ítems `G-*` abiertos (G-5..G-9).

## Historial

- 2026-08-05: creada (draft), tomando G-1 y G-3 de `docs/IDEAS.md`.
- 2026-08-05: implementada y pasada a `active`. G-1 resultó ser tres capas, no
  una. Se eliminó el `files:` de ambos `.pre-commit-config.yaml`; se agregó
  `sdd_source_roots()` (POSIX sh, sin comandos externos) a los dos
  `sdd_gate_hook.sh` y `sourceRoots()` (sin dependencias) al plugin de opencode;
  matcher ampliado en ambos `settings.json`; `SDD-ENFORCEMENT.md` documenta el
  pre-filtro y el límite de `Bash`. Un bug encontrado al testear: un config con
  CRLF dejaba el `\r` pegado al último root y ningún patrón matcheaba —
  resuelto con `${_l%[[:cntrl:]]}`, y `config_con_crlf` es ahora uno de los
  siete casos del test de paridad. Verificado con 232 tests (21 de paridad,
  16 de wiring, 8 del hook), pipeline 10/10 VERDE, `sdd-doctor` sano, y un
  testigo real con el código en `pkg/`: el commit sin spec quedó **bloqueado**
  y un `NOTA.md` en la misma raíz commiteó sin fricción.
- 2026-08-09: agregada User Story 2 para unificar el soporte de Antigravity CLI
  y Claude Code. Los hooks shell ahora emiten JSON o texto según el payload y son
  idénticos entre el kit y las plantillas.
