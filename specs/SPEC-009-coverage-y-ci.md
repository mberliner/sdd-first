# SPEC-009-coverage-y-ci: Paso `coverage` con umbrales opcionales y plantilla de CI derivada del config

> Origen: comparación con el proyecto de referencia `evaluador-flujo-intent`
> (2026-08-04), igual que SPEC-004. El evaluador corre hace meses dos capas de
> verificación que el kit todavía no ofrece: umbrales de cobertura como paso
> duro del pipeline, y un workflow de CI que espeja el pipeline local sin los
> gates de documentación. Los proyectos siguen independientes (no se migra el
> evaluador al kit); lo que se porta es el **mecanismo**, generalizado.

## User Story (Priority P1)

Como mantenedor de un proyecto instalado con sdd-first, quiero declarar
umbrales de cobertura en el config y recibir un workflow de CI ya cableado a
mi pipeline, para que la verificación no dependa de que cada quien recuerde
correr el pipeline local antes de pushear.

**Why this priority:** el kit vende "un pipeline local que te dice VERDE o
ROJO", pero hoy ese VERDE no dice nada sobre cobertura y nada lo vuelve a
correr en el servidor. Un proyecto instalado con sdd-first tiene menos
enforcement que el proyecto de referencia del que salió el kit.

**Independent Test:** en un proyecto con `pipeline.coverage` declarado,
`python core/pipeline.py` incluye el paso `coverage` y falla si algún target
está por debajo de su umbral; sin esa clave (o sin `pytest-cov` instalado) el
paso se omite con aviso y el pipeline sigue VERDE. `sdd-init` sobre un
directorio vacío deja un `.github/workflows/ci.yml` cuyos `paths:` y pasos
derivan del config, no de una lista fija.

## Clarifications

### Session 2026-08-04

- Q: ¿un umbral global o varios por target? → A: varios. El patrón útil del
  proyecto de referencia es "el dominio exige más que el resto"
  (`>=80%` global, `>=96%` en `src/domain`); un umbral único no lo expresa.
- Q: ¿el umbral es obligatorio? → A: no. Va **opcional en las plantillas**:
  `sdd-init` lo siembra comentado en `.sdd/config.yaml` y el paso se omite con
  aviso si la clave no está. Un proyecto recién instalado no puede arrancar en
  ROJO por una métrica que todavía no tiene sentido medir (SPEC-003 FR-001).
- Q: ¿la plantilla de CI asume GitHub Actions y Python? → A: el formato de
  archivo sí (GitHub Actions es el destino concreto), pero su **contenido** se
  deriva del config: los `paths:` salen de `dirs.source_roots`, los pasos de
  `pipeline.steps`. Un proyecto `language: none` obtiene solo los pasos de
  gobernanza. Otros proveedores de CI: fuera de alcance, mismo criterio que
  los adaptadores `node`/`go`.
- Q: ¿la CI corre el pipeline entero o pasos sueltos? → A: corre
  `core/pipeline.py`, no una lista duplicada de comandos. Duplicar la lista es
  exactamente el drift que el proyecto de referencia tiene hoy entre
  `pipeline_local.sh` y `ci.yml` (11 pasos vs 10, y `hooks`/`skills` ausentes
  en CI). El SSOT de los pasos es `pipeline.steps`.

## Acceptance Scenarios

- **Given** un config sin la clave `pipeline.coverage`, **When** corre el paso
  `coverage`, **Then** imprime el aviso de omisión y devuelve 0.
- **Given** un config con `pipeline.coverage` pero sin `pytest-cov`
  instalado, **When** corre el paso, **Then** se omite con aviso y devuelve 0.
- **Given** `pipeline.coverage: [{paths: [core], min: 80}]` y una suite que
  cubre el 60%, **When** corre el paso, **Then** devuelve != 0 y el pipeline
  sale ROJO nombrando el target incumplido.
- **Given** dos targets con umbrales distintos, **When** corre el paso,
  **Then** se evalúan ambos y falla si cualquiera incumple.
- **Given** un target declarado que no existe en disco, **When** corre el
  paso, **Then** ese target se omite con aviso sin fallar (proyecto que
  todavía no creó esa carpeta).
- **Given** `sdd-init --language=none`, **When** se instala, **Then** el
  `ci.yml` generado no contiene pasos de código ni instalación de tooling de
  lenguaje.

## Functional Requirements

- **FR-001** MUST: `adapters/python/adapter.py` expone el paso `coverage`,
  que lee los umbrales de `pipeline.coverage` del config: una lista de
  entradas `{paths: [...], min: N}`. Cada entrada se verifica con
  `pytest --cov=<path> ... --cov-fail-under=N` sobre las carpetas de tests
  declaradas en `dirs`.
- **FR-002** MUST: el paso se omite con aviso y exit 0 cuando (a) la clave
  `pipeline.coverage` no está declarada o está vacía, (b) `pytest` o
  `pytest-cov` no están instalados, o (c) no existe la carpeta de tests. Un
  proyecto recién instalado nunca sale ROJO por este paso.
- **FR-003** MUST: `core/pipeline.py` reconoce `coverage` como paso de código
  y lo delega al adaptador del lenguaje activo; con `language: none` se omite
  como el resto de los pasos de código.
- **FR-004** MUST: `core/sdd_config.py` expone la lectura tipada de los
  umbrales (`pipeline_coverage`), con default vacío y tolerancia a entradas
  malformadas — ningún consumidor parsea el YAML crudo.
- **FR-005** MUST: existe `templates/wiring/ci.yml`, plantilla de workflow
  cuyo contenido se resuelve desde `.sdd/config.yaml`: los `paths:` de
  disparo derivan de `dirs.source_roots` más las carpetas de tests, y el job
  invoca `python tools/sdd/core/pipeline.py` en vez de repetir la lista de
  pasos.
- **FR-006** MUST: `core/sdd_init.py` instala esa plantilla como
  `.github/workflows/ci.yml` en el proyecto destino, respetando la
  idempotencia del instalador (no pisa un workflow existente sin `--force`).
- **FR-007** SHOULD: el propio kit tiene su `.github/workflows/ci.yml`
  generado por el mismo mecanismo (deuda E-3 de `docs/IDEAS.md`), de modo que
  el dogfooding cubra también esta capa.

## Key Entities

- **Umbral de cobertura** — par `{paths, min}`: una o más carpetas medidas
  juntas contra un porcentaje mínimo. Varias entradas expresan exigencias
  distintas por capa.
- **Workflow de CI derivado** — artefacto generado desde el config, no
  editado a mano; su SSOT de pasos es `pipeline.steps`.

## Success Criteria

- **SC-001** Una instalación fresca (`sdd-init` en directorio vacío) sigue
  saliendo VERDE sin instalar tooling extra, con el paso `coverage` presente
  en el config comentado y omitido en la corrida.
- **SC-002** Declarar dos umbrales distintos y romper solo uno hace ROJO el
  pipeline identificando cuál.
- **SC-003** El `ci.yml` de un proyecto `language: none` no menciona ninguna
  tool de lenguaje.
- **SC-004** Los pasos que corre la CI no están enumerados en el workflow:
  cambiar `pipeline.steps` cambia lo que corre CI sin editar el YAML.

## Assumptions

- El adaptador Python usa `pytest-cov`; medir cobertura en otros lenguajes es
  responsabilidad de sus adaptadores (contrato en `adapters/CONTRACT.md`).
- GitHub Actions es el único proveedor de CI con plantilla. Otros proveedores
  quedan como roadmap, igual que `node`/`go`.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_python_adapter.py |
| FR-002 | tests/unit/test_python_adapter.py |
| FR-003 | tests/unit/test_pipeline_coverage_step.py |
| FR-004 | tests/unit/test_sdd_config.py |
| FR-005 | tests/unit/test_render.py |
| FR-006 | tests/unit/test_sdd_init.py |
| FR-007 | pipeline del kit (workflow presente y generado sin drift) |

## Fuera de alcance

- Proveedores de CI distintos de GitHub Actions.
- Cobertura para adaptadores `node`/`go` (no existen todavía).
- Publicar reportes de cobertura a servicios externos.

## Historial

- 2026-08-04: creada (draft) a partir de la comparación con
  `evaluador-flujo-intent`.
