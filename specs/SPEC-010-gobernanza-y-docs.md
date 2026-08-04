# SPEC-010-gobernanza-y-docs: Constitución con preámbulo y governance completa, principio de SSOT y rutas correctas en las plantillas

> Origen: comparación con el proyecto de referencia `evaluador-flujo-intent`
> (2026-08-04), hermana de SPEC-009. Cubre lo que en esa comparación resultó
> ser documentación y gobernanza (no comportamiento de pipeline), más un bug
> de rutas detectado de paso: E-6 de `docs/IDEAS.md` es más ancho de lo que se
> creía y afecta a casi todas las plantillas, no solo a `templates/AGENTS.md`.

## User Story (Priority P2)

Como desarrollador de un proyecto recién instalado con sdd-first, quiero que
la constitución generada explique qué es y cómo se enmienda, y que todos los
comandos que aparecen en la documentación instalada sean ejecutables tal como
están escritos, para no tener que ir a leer el repo del kit para entender ni
para corregir cada ruta a mano.

**Why this priority:** P2 y no P1 porque nada se rompe en caliente. Pero es
deuda que compone en dos direcciones: la constitución que el kit genera es
tan escueta que un equipo no sabe qué hacer con ella (y el propio kit
predica un principio de SSOT que no ofrece como principio configurable), y las
rutas rotas son la primera fricción real de un usuario nuevo — copia el
comando del `CONTRIBUTING.md` que el kit le instaló y no funciona.

**Independent Test:** `sdd-init` sobre un directorio vacío + `render.py`
produce un `CONSTITUTION.md` con Preámbulo y procedimiento de enmienda, y
ningún archivo instalado contiene la cadena `core/` apuntando al kit (todas
dicen `tools/sdd/core/`), mientras el propio kit conserva `core/`.

## Clarifications

### Session 2026-08-04

- Q: ¿cómo se resuelve que la misma plantilla sirva al kit (`core/`) y al
  proyecto derivado (`tools/sdd/core/`)? → A: con un placeholder nuevo,
  `{{sdd.core}}` / `{{sdd.adapters}}`, del mismo mecanismo que
  `{{project.name}}`. `core/render.py` lo resuelve a `core` al sincronizar
  las plantillas hacia la raíz del kit (SPEC-005); `core/sdd_init.py` lo
  resuelve a `tools/sdd/core` al instalar. Una sola fuente, dos resoluciones.
- Q: ¿la versión de la constitución sigue hardcodeada en `render.py`? → A:
  no; pasa al config (`constitution.version` / `ratified` / `amended`). Es el
  ítem C-5 de `docs/IDEAS.md`, que entra acá porque la sección Governance que
  se agrega promete un procedimiento de enmienda con bump de versión y sería
  incoherente prometerlo sin campo dónde bumpear.
- Q: ¿"SSOT único por tema" se vuelve principio obligatorio del núcleo? → A:
  no. Los cuatro principios del núcleo mínimo no cambian; este se agrega al
  catálogo **opcional** de `examples/config/config.yaml`, como ya está
  "Datos no versionados". Su enforcement es editorial (code review +
  `analyze`), no una tool: `check_constitution.py` no exige paso de pipeline
  para enforcements que no están en `ENFORCEMENT_STEP`, así que no rompe.
- Q: ¿por qué documentar `gen_skill_adapters.py` recién ahora? → A: el
  mecanismo existe y está en el pipeline (`skills --check`), pero no hay
  ningún documento que lo explique — quien recibe el kit ve carpetas
  generadas con "NO EDITAR A MANO" y no sabe qué las genera ni cómo agregar
  una skill propia.

## Acceptance Scenarios

- **Given** un config con `constitution.version: 0.3.0`, **When** corre
  `render.py`, **Then** `CONSTITUTION.md` muestra esa versión y
  `check_constitution.py` la valida como semver.
- **Given** el config sin sección `constitution`, **When** corre `render.py`,
  **Then** usa los defaults (`0.1.0`, fecha de hoy) sin fallar —
  retrocompatible con los configs ya instalados.
- **Given** un proyecto instalado, **When** se lee cualquier documento de
  `docs/` o `AGENTS.md`, **Then** los comandos citados apuntan a
  `tools/sdd/core/...` y se ejecutan sin editarlos.
- **Given** el propio kit, **When** corre `render.py --check`, **Then** los
  documentos sincronizados desde `templates/` conservan `core/...` y no hay
  drift.
- **Given** un equipo que quiere el principio de SSOT, **When** lo copia del
  config de ejemplo, **Then** `check_constitution.py` pasa sin exigir un paso
  de pipeline para él.

## Functional Requirements

- **FR-001** MUST: `core/render.py` emite en `CONSTITUTION.md` una sección
  **Preámbulo** que declara qué es la constitución (lista curada de
  invariantes no-negociables), cómo se usa (leer antes de diseñar; ante
  conflicto se ajusta la spec, no el principio) y su alcance (cada principio
  declara un invariante estable y apunta al SSOT del detalle operativo, sin
  duplicarlo).
- **FR-002** MUST: la sección **Governance** generada incluye el criterio
  semver desglosado (qué es MAJOR, MINOR y PATCH para un principio), la regla
  de fase pre-1.0, el procedimiento de enmienda enumerado y la regla de
  precedencia sobre specs y decisiones de implementación.
- **FR-003** MUST: la versión y las fechas de la constitución se leen de
  `.sdd/config.yaml` (`constitution.version`, `constitution.ratified`,
  `constitution.amended`), con defaults que preservan el comportamiento
  actual si la sección no existe.
- **FR-004** MUST: `examples/config/config.yaml` incluye, en el bloque de
  principios opcionales, "SSOT único por tema" con su invariante, enforcement
  editorial y detalle.
- **FR-005** MUST: existe `templates/docs/SKILLS-MULTITOOL.md` — SSOT del
  mecanismo de skills multi-asistente: tabla de asistentes soportados y sus
  rutas, modelo de capas playbook→SKILL.md→adaptadores generados, campos del
  frontmatter (incluidos los `opencode-*`), y por qué se generan archivos
  reales en vez de symlinks. Se sincroniza a `docs/` del kit por el mecanismo
  de SPEC-005 y se instala en el proyecto derivado.
- **FR-006** MUST: existe `templates/docs/DEVELOPMENT.md` (setup local y
  comandos clave del proyecto derivado) y `sdd-init` lo instala.
- **FR-007** MUST: las plantillas usan los placeholders `{{sdd.core}}` y
  `{{sdd.adapters}}` en lugar de las rutas literales `core/` y `adapters/`.
  `core/sdd_init.py` los resuelve a `tools/sdd/core` y `tools/sdd/adapters`;
  `core/render.py` los resuelve a `core` y `adapters` al sincronizar hacia la
  raíz del kit.
- **FR-008** MUST: `00-INDEX.md` del kit y `templates/00-INDEX.md` registran
  los documentos nuevos en el mapa de SSOTs.
- **FR-009** SHOULD: el `README.md` del kit precisa qué asistentes tienen
  soporte real de skills (`.agents/` + Claude + opencode), corrigiendo el
  claim genérico sobre "Cursor…" (ítem E-5 de `docs/IDEAS.md`).

## Key Entities

- **Placeholder de ruta del kit** (`{{sdd.core}}`, `{{sdd.adapters}}`) —
  resuelve la única diferencia estructural entre el kit y un proyecto
  instalado: dónde vive el andamiaje.
- **Catálogo de principios opcionales** — bloque del config de ejemplo del
  que un proyecto elige; distinto del núcleo mínimo obligatorio.

## Success Criteria

- **SC-001** `grep -rn "core/" ` sobre un proyecto recién instalado no
  devuelve ninguna ruta del kit sin el prefijo `tools/sdd/`.
- **SC-002** `render.py --check` sobre el propio kit pasa: la resolución del
  placeholder es determinista y no introduce drift.
- **SC-003** La constitución generada pasa `check_constitution.py` con la
  sección Preámbulo presente (el parser sigue reconociendo `## Principios` y
  la línea de versión).
- **SC-004** Un config sin sección `constitution` sigue rindiendo el mismo
  documento que antes de este cambio, salvo las secciones nuevas.

## Assumptions

- El parser de `check_constitution.py` recorre secciones `## `, así que
  agregar `## Preámbulo` antes de `## Principios` no lo altera.
- Los proyectos ya instalados con versiones previas del kit no se migran
  automáticamente; la ruta de actualización del kit vendorizado sigue siendo
  deuda abierta (E-2 en `docs/IDEAS.md`).

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_render.py |
| FR-002 | tests/unit/test_render.py |
| FR-003 | tests/unit/test_render.py |
| FR-004 | tests/unit/test_example_config.py |
| FR-005 | tests/unit/test_template_paths.py |
| FR-006 | tests/unit/test_sdd_init.py |
| FR-007 | tests/unit/test_template_paths.py |
| FR-008 | tests/unit/test_template_paths.py |
| FR-009 | revisión editorial (README del kit) |

## Fuera de alcance

- Migrar proyectos ya instalados a los placeholders nuevos (ruta de
  actualización = E-2, deuda abierta).
- Convertir "SSOT único por tema" en principio obligatorio del núcleo.
- Migrar `evaluador-flujo-intent` a consumir el kit: decisión tomada de
  mantener los proyectos independientes.

## Historial

- 2026-08-04: creada (draft) a partir de la comparación con
  `evaluador-flujo-intent`.
