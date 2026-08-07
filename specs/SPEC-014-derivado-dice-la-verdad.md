# SPEC-014: El proyecto derivado dice la verdad sobre sí mismo

> Origen: campaña de usabilidad del proyecto derivado del 2026-08-05 (U-4..U-11 y
> G-4 de `docs/IDEAS.md`). SPEC-003 (reabierta) cerró la mitad del problema: el
> pipeline dejó de contar como OK lo que no midió. Esta spec cierra la otra
> mitad, que tiene dos caras distintas y por eso lleva dos historias de usuario.

## User Story 1 (Priority P1) — ningún reporte de salud sin medición

Como dueño de un proyecto donde acabo de instalar el kit, quiero que ninguna
salida me diga que la instalación está sana mientras haya capas de enforcement
sin cablear, para poder confiar en que un "sano" significa protegido.

**Why this priority:** en el testigo con wiring propio preexistente
(`.pre-commit-config.yaml` con solo `ruff`, `.claude/settings.json` propio) el
resultado fue **cero** capas de gate activas y `sdd-doctor` reportando
"Instalación SDD sana". Un commit que debía bloquearse se aceptó. Un falso
positivo de seguridad es peor que no tener la herramienta: sustituye la
verificación por una creencia.

**Independent Test:** instalar sobre un proyecto que ya tiene
`.pre-commit-config.yaml` y `.claude/settings.json` propios; la salida de
instalación nombra los archivos conservados y advierte que el gate puede no estar
cableado, y `sdd-doctor` sale con exit 1 señalando cada archivo que existe pero no
invoca al gate.

## User Story 2 (Priority P2) — el derivado habla en sus propios términos

Como asistente o dueño que abre los artefactos de un proyecto derivado, quiero que
cada mensaje y cada archivo instalado se refiera a las rutas, ramas y artefactos
**de ese proyecto**, para no seguir instrucciones que solo son válidas en el repo
del kit.

**Why this priority:** no rompe el enforcement, pero es la clase de detalle que
enseña que el andamiaje es ajeno: un `{{sdd.core}}` sin sustituir en el primer
archivo que se abre para entender el gate, un "corre: python core/render.py" que
no existe en el derivado, un CI que nunca dispara porque la rama es `develop`.
Cada uno cuesta minutos y confianza.

**Independent Test:** instalar en un proyecto cuya rama por defecto no es `main`;
ningún archivo instalado contiene la cadena `{{`, los mensajes de drift citan
rutas que existen en el destino, y el `ci.yml` generado dispara en la rama real.

## Clarifications

### Session 2026-08-05

- Q: ¿Por qué dos HU en una spec y no dos specs? → A: las dos caras salen del
  mismo recorrido y comparten el mismo invariante de fondo (*el derivado no
  afirma nada que no sea cierto de sí mismo*), pero tienen prioridad y criterio
  de aceptación distintos: una es enforcement, la otra es claridad. Separarlas en
  dos specs duplicaría el contexto de la campaña; fundirlas en una sola HU haría
  que su *Independent Test* no fuera verificable de una vez.
  `docs/SPEC-FORMAT.md` ya contempla el caso (`FR-USk-NNN`); es la primera spec
  del kit que lo usa.
- Q: ¿`sdd-init` debería sobrescribir el wiring propio? → A: no. La
  idempotencia y el "no pisar lo del dueño" son deliberados (SPEC-003). Lo que
  falta no es sobrescribir sino **avisar**, con la instrucción concreta para
  resolverlo (`--force` o cablear a mano).
- Q: ¿Cómo reconoce `sdd-doctor` que un wiring "cablea el gate"? → A: por la
  invocación que debe contener, declarada en un único mapa
  `GATE_WIRING` en `core/sdd_config.py`. Hoy la lista de archivos vive duplicada
  en `sdd_doctor.py` y el aviso nuevo de `sdd_init.py` necesitaría una tercera
  copia: el mapa es el SSOT de *qué es wiring de gate y cómo se reconoce que está
  puesto* (principio IV).
- Q: ¿El gate debería fallar cerrado si no encuentra raíz SDD? → A: no como
  se implementó primero. `find_repo_root` devolvía el directorio de partida
  cuando no hallaba marcadores, así que `_is_source_path` no reconocía nada como
  código y la edición pasaba en silencio: eso hay que cerrarlo. Pero denegar
  **toda** edición sin raíz resoluble es demasiado ancho, y se comprobó en el
  acto: con el hook instalado y un `cwd` apuntando fuera del repo, quedó
  bloqueada la edición de un `.md` de otra carpeta y también la del propio kit.
  El criterio correcto no es el `cwd` sino **de qué proyecto es el archivo**: se
  resuelve la raíz desde el `cwd` y, si falla, desde la ruta del archivo. Sin
  raíz por ninguno de los dos caminos no existe el proyecto SDD cuyo protocolo
  se estaría violando. Se conserva `find_repo_root` con su fallback (lo usan
  `pipeline`, `render`, `doctor`, donde fallar cerrado no aplica) y se agrega
  `find_sdd_root()`, que devuelve `None` cuando no hay marcador.
- Q: ¿Y el fail-closed del wrapper de Claude Code, entonces? → A: sigue siendo
  correcto ahí: si el *wrapper* no puede invocar al gate (falta Python, falta el
  script), bloquea. Lo que no corresponde es que el gate deniegue ediciones de
  archivos que no pertenecen a ningún proyecto SDD.
- Q: ¿De dónde sale la rama del CI? → A: de `project.default_branch` en el
  config, que `sdd-init` siembra con la rama real del destino cuando git puede
  informarla. Detectarla en cada `render` haría que el artefacto generado
  dependiera del estado de git y no del config, rompiendo el `--check`.
- Q: ¿Y los docstrings que citan `core/x.py`? → A: fuera de alcance. El alcance
  son los mensajes de **runtime**, que es lo que el operador copia y pega. Los
  docstrings se leen en el archivo, cuya ruta ya es visible.

### Session 2026-08-07

- Q: `AGENTS.md` afirma el dominio del proyecto, pero cambiar `project.domain`
  después de instalar no lo actualiza. ¿Se regenera `AGENTS.md`? → A: no. El
  dominio llega ahí por sustitución de `{{project.domain}}` **en la instalación**,
  y `render.py` no puede regenerarlo porque el derivado no tiene `templates/`.
  Regenerarlo exigiría vendorizar plantillas a cada proyecto: más superficie
  instalada para sostener una copia que conviene no tener.
- Q: ¿Entonces cómo se arregla? → A: eliminando la copia, no sincronizándola. El
  dominio pasa a declararse en `CONSTITUTION.md`, que **sí** es artefacto generado,
  sí existe en el derivado y sí lo vigila `render --check`; `AGENTS.md` remite. Un
  solo lugar lo afirma, y ese lugar deriva del config (principio IV).
- Q: ¿No se pierde el dominio para el asistente, que lee `AGENTS.md`? → A: no: el
  paso 1 del protocolo ya lo manda a leer `CONSTITUTION.md` antes de cualquier
  cambio. Pasa a encontrarlo ahí, actualizado, en vez de leer en `AGENTS.md` una
  afirmación que puede tener meses.
- Q: ¿Por qué en esta spec y no en una nueva? → A: es exactamente el invariante de
  la HU-2 —*el derivado no afirma nada que no sea cierto de sí mismo*— con el
  mismo origen que U-4..U-11. Lo encontró la suite e2e (**V-3** de
  `docs/IDEAS.md`), no una campaña manual, pero el defecto es de la misma clase.

## Acceptance Scenarios

- **Given** un proyecto con `.pre-commit-config.yaml` y `.claude/settings.json`
  propios, **When** se corre `sdd-init`, **Then** la salida final nombra esos dos
  archivos como conservados y advierte que el gate puede no estar cableado.
- **Given** ese mismo proyecto ya instalado, **When** se corre `sdd-doctor`,
  **Then** sale con exit 1 y reporta, por archivo, que existe pero no invoca al
  gate.
- **Given** un payload cuyo `cwd` no resuelve a ninguna raíz con marcadores SDD
  pero cuyo `file_path` está dentro de un proyecto SDD, **When** llega al gate,
  **Then** se juzga con la raíz del archivo y se bloquea si no hay spec vigente.
- **Given** un payload donde ni el `cwd` ni el `file_path` caen en un proyecto
  SDD, **When** llega al gate, **Then** se permite: no hay protocolo que aplicar.
- **Given** una instalación fresca, **When** se listan los archivos instalados,
  **Then** ninguno contiene un placeholder `{{...}}` sin resolver.
- **Given** un derivado con drift de artefactos generados, **When** se corre
  `sdd-doctor`, **Then** el problema nombra los archivos desincronizados y cita
  la ruta real del script que los regenera.
- **Given** un proyecto cuya rama por defecto es `develop`, **When** se instala y
  se corre `render.py`, **Then** el `ci.yml` generado dispara en `develop`.
- **Given** un derivado instalado, **When** se cambia `project.domain` en el
  config y se corre `render.py`, **Then** `CONSTITUTION.md` refleja el dominio
  nuevo y ningún otro artefacto instalado afirma el viejo; **When** se cambia sin
  regenerar, **Then** `render --check` reporta el drift.

## Functional Requirements — HU-1 (enforcement)

- **FR-US1-001** MUST: `core/sdd_init.py` avisa al cerrar cuando conservó wiring
  de gate preexistente. El aviso nombra cada archivo, dice que el gate puede no
  estar cableado y da las dos salidas (`--force` para pisarlo, o cablear a mano
  comparando con `templates/wiring/`). Va en la salida final, no en el log de 30
  líneas donde hoy se pierde la línea `(existe, se conserva)`.
- **FR-US1-002** MUST: `core/sdd_doctor.py` verifica el **contenido** del wiring
  de gate, no solo su existencia: cada archivo de `GATE_WIRING` debe contener la
  invocación declarada para él. Un archivo presente que no la contiene es un
  problema reportado por separado de la ausencia del archivo.
- **FR-US1-003** MUST: `core/sdd_gate.py` no juzga contra una raíz inventada.
  Resuelve la raíz desde el `cwd` del payload y, si ahí no hay marcadores SDD,
  **desde la ruta del archivo que se va a editar**. Si la edición cae dentro de
  un proyecto SDD, ese proyecto la gobierna aunque el `cwd` sea inútil; si no cae
  en ninguno, no hay spec que exigir y se permite. `core/sdd_config.py` expone
  `find_sdd_root(start) -> Path | None` (marcador encontrado o nada) y
  `find_repo_root` queda como el envoltorio tolerante que ya usaban el resto de
  los scripts. *(Enmendado el 2026-08-05 tras el hallazgo de abajo: la primera
  redacción denegaba toda edición sin raíz resoluble.)*
- **FR-US1-004** SHOULD: la salida de instalación nombra `00-INDEX.md` como
  puerta de entrada a la documentación instalada.

## Functional Requirements — HU-2 (claridad)

- **FR-US2-001** MUST: todo archivo de texto que `sdd-init` instala queda con los
  placeholders resueltos. La sustitución deja de depender de la extensión del
  archivo — el criterio que dejaba `.sdd/current-spec` con `{{sdd.core}}` crudo
  por no tener sufijo.
- **FR-US2-002** MUST: los mensajes de drift de `core/render.py`,
  `core/gen_skill_adapters.py` y `core/sdd_doctor.py` citan la ruta real del
  script que corresponde correr, resuelta desde la ubicación del propio módulo
  (`core/` en el kit, `tools/sdd/core/` en un derivado).
- **FR-US2-003** MUST: el problema de drift que reporta `sdd-doctor` nombra los
  artefactos desincronizados en vez de una lista fija de nombres. Hoy dice
  "CONSTITUTION.md/SPEC-000 desincronizados" aunque lo que drifteó sea `ci.yml`.
- **FR-US2-004** SHOULD: el `.sdd/config.yaml` sembrado lleva una cabecera propia
  del proyecto destino, en vez de la del catálogo de referencia, que manda
  copiarlo a `.sdd/config.yaml` cuando ya *es* ese archivo y nombra al proyecto de
  referencia. `examples/config/config.yaml` conserva la suya: sigue siendo el
  catálogo.
- **FR-US2-005** SHOULD: el `ci.yml` generado dispara en la rama por defecto real
  del proyecto, leída de `project.default_branch` del config. `sdd-init` la
  siembra con lo que informe git en el destino; sin dato, `main`.
- **FR-US2-006** MUST: el dominio del proyecto lo afirma **un solo artefacto**, y
  es generado: `CONSTITUTION.md` lo declara desde `project.domain`. Ninguna
  plantilla instalada guarda una copia sustituida en la instalación, que quedaría
  congelada al primer valor. `render --check` detecta el drift como con cualquier
  otro artefacto generado.

## Success Criteria

- **SC-001**: sobre un proyecto con wiring propio, ninguna salida del kit afirma
  que la instalación está sana: `sdd-doctor` sale 1 y la instalación advierte.
- **SC-002**: un payload sin raíz SDD resoluble es denegado por el gate (exit 2),
  con motivo legible.
- **SC-003**: ningún archivo instalado por `sdd-init` contiene `{{`.
- **SC-004**: los mensajes de drift de los tres scripts, corridos desde un
  derivado, citan rutas que existen en ese derivado.
- **SC-005**: instalado sobre un repo en rama `develop`, el `ci.yml` generado
  dispara en `develop`; en un repo sin git, en `main`.
- **SC-006**: el pipeline del kit sigue VERDE y la suite pasa completa.
- **SC-007**: cambiar `project.domain` en un derivado ya instalado y regenerar
  deja el dominio nuevo en `CONSTITUTION.md`; ningún archivo instalado conserva el
  viejo.

## Key Entities

- **`GATE_WIRING`** (`core/sdd_config.py`): mapa `archivo → invocación esperada`.
  SSOT de qué archivos cablean el gate y de cómo se reconoce que lo hacen.
  Consumido por `sdd_doctor` (verificación) y `sdd_init` (aviso).
- **`find_sdd_root`** (`core/sdd_config.py`): resolución estricta de la raíz.
  `None` = no hay proyecto SDD acá, y quien pregunta decide qué hacer con eso.
- **`project.default_branch`** (`.sdd/config.yaml`): rama de disparo del CI.
  Opcional; sin ella se asume `main`.

## Coverage mapping

| Requisito | Cubierto por |
| --- | --- |
| FR-US1-001 | `tests/unit/test_sdd_init_wiring_conservado.py` |
| FR-US1-002 | `tests/unit/test_sdd_doctor_wiring.py` |
| FR-US1-003 | `tests/unit/test_gate_sin_raiz_sdd.py` |
| FR-US1-004 | `tests/unit/test_sdd_init_wiring_conservado.py` |
| FR-US2-001 | `tests/unit/test_derived_references.py` |
| FR-US2-002 | `tests/unit/test_mensajes_de_drift.py` |
| FR-US2-003 | `tests/unit/test_sdd_doctor_wiring.py` |
| FR-US2-004 | `tests/unit/test_sdd_init_seeded_config.py` |
| FR-US2-005 | `tests/unit/test_render.py`, `tests/unit/test_sdd_init_seeded_config.py` |
| FR-US2-006 | `tests/unit/test_render.py`, `tests/e2e/escenarios/test_configuracion.py` |

## Fuera de alcance

- Derivar el pre-filtro `files:` de `.pre-commit-config.yaml` desde
  `source_roots` → G-1 de `docs/IDEAS.md`.
- Mojibake de la salida en Windows con stdout redirigido → C-2 de
  `docs/IDEAS.md`.
- Ruta de actualización del kit vendorizado → E-2 de `docs/IDEAS.md`.
- Docstrings de uso que citan `core/x.py` (ver Clarifications).
- Sobrescribir el wiring propio del proyecto: `sdd-init` avisa, no decide.

## Historial

- 2026-08-05: creada (draft), registrada en `SPECS_REGISTRY.md` y declarada en
  `.sdd/current-spec`. Primera spec multi-HU del kit.
- 2026-08-05: implementada y promovida a `active`. Pipeline VERDE 10/10, 191
  passed + 1 skip. Verificada además sobre el testigo con wiring propio de la
  campaña: instalación que avisa, doctor en exit 1 nombrando cada archivo sin
  cablear, `ci.yml` disparando en `master` y gate resolviendo la raíz.
- 2026-08-07 (iteración 4): FR-US2-006 y SC-007. La suite e2e mostró que
  `project.domain` quedaba congelado en `AGENTS.md` desde la instalación (V-3);
  el dominio pasa a declararse en `CONSTITUTION.md`, que sí se regenera.
- 2026-08-05: FR-US1-003 enmendado el mismo día. La primera implementación
  denegaba toda edición cuyo `cwd` no resolviera a una raíz SDD, y bloqueó en
  vivo la edición de un archivo de otra carpeta y del propio kit. La raíz ahora
  se busca también desde la ruta del archivo, y solo se permite cuando la
  edición no pertenece a ningún proyecto SDD.
