# SPEC-009-coverage-y-ci: Paso `coverage` con umbrales opcionales y plantilla de CI derivada del config

> **SSOT del paso `coverage`**: qué mide, cuándo se omite y cómo llega un umbral
> al config de un proyecto. La cifra concreta de cada proyecto vive en su
> `pipeline.coverage`, no acá.

> Origen: comparación con el proyecto de referencia `evaluador-flujo-intent`
> (2026-08-04), igual que SPEC-004. El evaluador corre hace meses dos capas de
> verificación que el kit todavía no ofrece: umbrales de cobertura como paso
> duro del pipeline, y un workflow de CI que espeja el pipeline local sin los
> gates de documentación. Los proyectos siguen independientes (no se migra el
> evaluador al kit); lo que se porta es el **mecanismo**, generalizado.

## User Story 1 (Priority P1) — el umbral declarado se verifica

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

## User Story 2 (Priority P2) — el paso sembrado no nace inerte

Como dueño de un proyecto donde acabo de instalar el kit, quiero que el paso
`coverage` que recibo sembrado mida algo desde el primer día, para que el VERDE
del pipeline no me enseñe que un paso puede omitirse en cada corrida sin
consecuencia.

**Why this priority:** la US1 dejó el umbral opcional con buen motivo —una
instalación fresca no puede arrancar en ROJO por una métrica que todavía no tiene
sentido medir (FR-002)—, pero el paso **sí** se siembra en `pipeline.steps`. El
resultado es un paso que se omite con aviso en cada corrida: la misma familia de
U-3 (un paso omitido contado como OK) y C-1 (un paso desconocido contado como OK),
donde el verde se vuelve ruido. En el kit la clave vacía fue una elección
deliberada mientras no hubo suite; en un proyecto de IT real con código creciendo
es deuda que nadie paga, porque nadie sabe qué número poner. El kit sí sabe:
puede medirlo.

**Why P2 y no P1:** no rompe nada en caliente ni produce un falso verde —el paso
omitido se informa aparte y no cuenta como OK (SPEC-003 FR-009)—. Lo que degrada
es el hábito.

**Independent Test:** en un proyecto con suite y sin `pipeline.coverage`, correr
la herramienta de piso deja el config con un umbral igual a la cobertura real
medida (redondeada hacia abajo), y el paso `coverage` pasa a verificar en vez de
omitirse. Corrida sobre un proyecto que ya declara umbrales, no los toca.

## User Story 3 (Priority P2) — una corrida sirve para los dos pasos

Como mantenedor del propio kit (u otro proyecto con `pipeline.coverage`
declarado sobre las mismas carpetas que mide `tests`), quiero que el pipeline
completo no pague dos veces el costo de la suite —una vez sin instrumentar
para `tests`, otra instrumentada para `coverage`—, para que declarar umbrales
de cobertura no duplique el tiempo del ciclo rápido sin ganar nada a cambio.

**Why this priority:** medido en el propio kit (2026-08-12), la suite plana
tarda ~74s y la misma suite instrumentada con `--cov` tarda ~141s; correr las
dos en secuencia (~215s) para terminar evaluando exactamente la misma
ejecución dos veces es tiempo que no compra una verificación adicional. No es
P1 porque no cambia ningún resultado ni corrige un falso verde: es una
optimización de costo sobre un mecanismo que ya es correcto.

**Why this diseño y no fusionar los pasos:** fusionar `tests` y `coverage` en
un solo paso de `pipeline.steps` reintroduce el defecto que
[[SPEC-019-tests-integracion-ejecutados]] corrigió —un fallo de test se
reportaría bajo el nombre `coverage`, no `tests`— y rompe el invariante de
`sdd_doctor._tests_sin_ejecutor` (SPEC-019 FR-US2-001), que exige que
`dirs.tests_unit` tenga *su propio* paso ejecutor. Los dos pasos siguen
existiendo, nombrados y con su propio veredicto; lo que se comparte es la
**ejecución** subyacente, no el resultado.

**Independent Test:** con `pipeline.coverage` declarado y `pytest-cov`
instalado, correr `python core/pipeline.py` invoca pytest instrumentado con
`--cov` una sola vez (en el paso `tests`); el paso `coverage` que sigue no
vuelve a invocar pytest, evalúa los umbrales leyendo el reporte que dejó
`tests`, y un test roto sigue pintando `tests` en rojo (no `coverage`).
Invocado suelto (`python adapters/python/adapter.py coverage`, sin pasar por
`core/pipeline.py`), el paso `coverage` sigue corriendo pytest por su cuenta,
igual que hoy: el mecanismo es una optimización de la corrida completa, no un
cambio del contrato por paso.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

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

### Session 2026-08-09 (K-5)

- Q: ¿quién mide el piso, `sdd-init` durante la instalación? → A: no. Medir es
  correr la suite del proyecto destino: arbitrariamente lenta, con efectos
  posibles, y sobre un brownfield que el instalador acaba de tocar. Un instalador
  que ejecuta los tests ajenos sin pedirlo es una sorpresa cara. Va como comando
  propio, que el operador (o su asistente vía `sdd-configure`) corre cuando
  quiere, y que el instalador nombra.
- Q: ¿y si el proyecto ya declara `pipeline.coverage`? → A: no se toca. La
  herramienta informa medido vs declarado y avisa si el declarado quedó **por
  debajo** del piso real —el trinquete perdió el mordisco, que es exactamente el
  defecto que K-3 encontró en el propio kit: umbral 50 con cobertura real 75—.
  Subir un umbral es decisión de política, no algo que una corrida afortunada
  deba hacer por su cuenta y a espaldas de quien lo declaró.
- Q: medir cobertura es específico del lenguaje. ¿Va en el núcleo? → A: no. La
  medición es del adaptador; el núcleo orquesta, decide dónde escribir y aplica
  la política del trinquete. Como no es un paso de pipeline (no valida nada,
  produce un dato), no entra a `STEPS` del adaptador: sería un paso más para
  `pipeline.CODE_STEPS` sin nada que verificar. Va en un dispatcher aparte de
  consultas, con su propio contrato de salida documentado en
  `adapters/CONTRACT.md`.
- Q: ¿por qué no lo reporta `sdd-doctor` como problema? → A: porque un proyecto
  recién instalado sin tests todavía es sano, y un `sdd-doctor` que sale 1 sobre
  una instalación fresca reintroduce el falso negativo que SPEC-014 cerró del otro
  lado. Va como nota, no como problema.
- Q: ¿por qué la numeración de FR no se unifica? → A: los `FR-001..FR-007` de la
  US1 están referenciados desde el historial, desde commits y desde comentarios de
  código. Renumerarlos dejaría esas referencias colgadas para ganar simetría
  cosmética. La US2 estrena el prefijo `FR-US2-NNN`.

### Session 2026-08-12

- Q: ¿cómo se comparte una ejecución entre dos pasos que corren como
  subprocesos separados (`adapter.py tests`, después `adapter.py coverage`),
  si el contrato de adaptador exige que cada paso sea invocable suelto con un
  único argumento? → A: una variable de entorno, no un cambio del contrato por
  paso. `core/pipeline.py` crea un archivo temporal por corrida y expone su
  ruta en `SDD_PIPELINE_COVERAGE_CACHE` a los pasos de código que invoca. El
  paso `tests`, si la variable está seteada y hay umbrales declarados, escribe
  ahí el reporte de cobertura de su propia corrida (sin `--cov-fail-under`: su
  exit code sigue siendo solo el resultado de los tests). El paso `coverage`,
  si la variable apunta a un archivo que existe, lo lee en vez de correr
  pytest. Sin la variable —paso invocado suelto— cada uno se comporta como
  hoy: es un atajo opcional, no un requisito nuevo del contrato.
- Q: ¿y si `tests` corre pero `coverage` no está en `pipeline.steps` de ese
  proyecto, o corre con `--fail-fast` y el pipeline se detiene antes? → A: el
  archivo temporal lo limpia `core/pipeline.py` al terminar (haya fallado o
  no); un reporte que nadie leyó no es un problema, es trabajo que ya se hizo
  gratis por si acaso el siguiente paso lo necesitaba.
- Q: ¿el reporte cacheado puede quedar desactualizado entre los dos pasos? →
  A: no hay ventana: es el mismo proceso de `core/pipeline.py`, el archivo lo
  crea vacío al arrancar y el paso `tests` lo escribe antes de que el paso
  `coverage` corra. No hay reintento ni corridas en paralelo que lo hagan
  obsoleto dentro de una misma invocación.

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

### US3 — ejecución compartida

- **Given** `pipeline.coverage` declarado y `pytest-cov` instalado, **When**
  corre `core/pipeline.py`, **Then** pytest se invoca instrumentado con
  `--cov` una sola vez (dentro del paso `tests`, que deja el reporte en
  `SDD_PIPELINE_COVERAGE_CACHE`) y el paso `coverage` evalúa los umbrales
  leyendo ese reporte, sin invocar pytest de nuevo.
- **Given** ese mismo escenario con un test roto, **When** corre el pipeline,
  **Then** el paso `tests` sale en rojo por el test, no el paso `coverage`.
- **Given** el paso `coverage` invocado suelto (`python
  adapters/python/adapter.py coverage`, sin pasar por `core/pipeline.py`),
  **When** corre, **Then** evalúa los umbrales corriendo pytest por su cuenta,
  igual que sin esta optimización.

### US2 — el piso medido

- **Given** un proyecto con suite y sin `pipeline.coverage`, **When** se corre la
  herramienta de piso, **Then** el config queda con una entrada cuyos `paths` son
  las carpetas de código medidas y cuyo `min` es la cobertura real redondeada
  hacia abajo, y el paso `coverage` pasa a verificar en vez de omitirse.
- **Given** un proyecto que ya declara `pipeline.coverage`, **When** se corre la
  herramienta, **Then** el config no se modifica y la salida informa medido vs
  declarado.
- **Given** ese mismo proyecto con un umbral declarado por debajo del piso real,
  **When** se corre la herramienta, **Then** además avisa que el trinquete no
  está mordiendo y con qué valor lo estaría.
- **Given** un proyecto sin `pytest-cov`, o sin carpetas de tests, o sin código
  todavía, **When** se corre la herramienta, **Then** se omite con aviso y no
  escribe nada.
- **Given** un config con `coverage` en `pipeline.steps` pero sin umbrales,
  **When** se corre `sdd-doctor`, **Then** lo informa como nota —no como
  problema— nombrando la herramienta que lo resuelve.
- **Given** un config con comentarios, **When** la herramienta escribe el umbral,
  **Then** los comentarios preexistentes sobreviven.

## Functional Requirements — US1 (el umbral declarado se verifica)

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
- **FR-006** MUST: `.github/workflows/ci.yml` es un artefacto derivado más de
  `core/render.py` (`_GENERATED`), igual que `CONSTITUTION.md` o `SPEC-000`: no
  lo instala `sdd_init.py` como copia estática, lo escribe `render.py` a partir
  del config y se regenera siempre, sin idempotencia ni `--force` — es un
  archivo que "nunca se edita a mano", así que no hay contenido de usuario que
  proteger. *(Enmendado el 2026-08-11: la versión original describía un
  instalador que copiaba una plantilla estática con `--force`; el mecanismo
  real es el de FR-005, no uno separado en `sdd_init.py`.)*
- **FR-007** SHOULD: el propio kit tiene su `.github/workflows/ci.yml`
  generado por el mismo mecanismo (deuda E-3 de `docs/IDEAS.md`), de modo que
  el dogfooding cubra también esta capa.

## Functional Requirements — US2 (el paso sembrado no nace inerte)

- **FR-US2-001** MUST: el adaptador del lenguaje expone la consulta
  `coverage-baseline`, que mide la cobertura real de las carpetas de código sobre
  las carpetas de tests declaradas y la imprime en una línea con formato fijo
  (`SDD-COVERAGE-BASELINE <porcentaje> <paths separados por coma>`). No es un paso
  de pipeline: no valida nada, produce un dato, y por eso no entra al dispatcher
  `STEPS` ni a `pipeline.CODE_STEPS`. Se omite (exit 3) sin tooling, sin carpetas
  de tests o sin código.
- **FR-US2-002** MUST: `adapters/CONTRACT.md` documenta la consulta como parte del
  contrato: nombre, formato de salida y estados de salida. Un adaptador `node`/`go`
  implementa lo mismo o no la ofrece; el núcleo no asume Python.
- **FR-US2-003** MUST: `core/sdd_coverage_baseline.py` orquesta: invoca la consulta
  del adaptador activo, redondea **hacia abajo** el porcentaje —un piso medido con
  decimales que no se puede volver a alcanzar no es un trinquete— y escribe la
  entrada en `pipeline.coverage` de `.sdd/config.yaml`. Sin adaptador para el
  lenguaje activo, se omite con aviso.
- **FR-US2-004** MUST: la escritura preserva el resto del archivo, comentarios
  incluidos. El config es un documento que su dueño edita a mano; una reescritura
  que pierda sus comentarios es un cambio destructivo.
- **FR-US2-005** MUST: si `pipeline.coverage` ya está declarado, la herramienta no
  lo modifica. Informa medido vs declarado y, cuando el umbral declarado quedó por
  debajo del piso real, avisa que el trinquete no está mordiendo y con qué valor
  lo estaría.
- **FR-US2-006** SHOULD: `core/sdd_doctor.py` informa como **nota** —no como
  problema— cuando `coverage` está en `pipeline.steps` sin umbrales declarados, y
  nombra la herramienta que lo resuelve con la ruta real del derivado.
- **FR-US2-007** SHOULD: el playbook de `sdd-configure` y el comentario de
  `pipeline.coverage` del catálogo de config nombran la herramienta, en vez de
  decir solamente "descomentar cuando la suite esté madura".

## Functional Requirements — US3 (una corrida sirve para los dos pasos)

- **FR-US3-001** MUST: `core/sdd_config.py` expone `PIPELINE_COVERAGE_CACHE_ENV`,
  el nombre de la variable de entorno que comunica la ruta del reporte
  compartido entre `core/pipeline.py` y el adaptador. SSOT único, igual que
  `EXIT_OMITIDO` y `COVERAGE_BASELINE_PREFIX`.
- **FR-US3-002** MUST: `core/pipeline.py` crea un archivo temporal por
  invocación, expone su ruta en esa variable a los pasos de código que
  ejecuta, y lo borra al terminar (con o sin fallos).
- **FR-US3-003** MUST: el paso `tests` del adaptador Python, cuando la
  variable está seteada, hay `pipeline.coverage` con targets existentes y
  `pytest-cov` está instalado, corre pytest una sola vez sobre `dirs.tests_unit`
  con `--cov` de la unión de los `paths` declarados y
  `--cov-report=json:<ruta>`, sin `--cov-fail-under`: el exit code del paso
  sigue siendo únicamente el resultado de los tests. Sin esas condiciones,
  corre como hoy (FR de US1, sin tocar).
- **FR-US3-004** MUST: el paso `coverage`, cuando la variable apunta a un
  archivo JSON legible, evalúa cada target agregando `covered_lines` y
  `num_statements` de los archivos del reporte cuyo path cae bajo alguno de
  sus `paths`, y compara el porcentaje resultante contra `minimum` — sin
  invocar pytest. Sin variable, sin archivo, o con un archivo no parseable,
  cae al comportamiento de FR-001 (una corrida de pytest por target).
- **FR-US3-005** MUST: el mecanismo es interno a la corrida de
  `core/pipeline.py`. Invocado suelto (`python adapters/python/adapter.py
  coverage`), sin la variable de entorno, el paso se comporta exactamente
  como antes de esta User Story.

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
- **SC-005** En un proyecto con suite y sin umbrales, una corrida de la
  herramienta de piso deja el paso `coverage` verificando: la corrida siguiente
  del pipeline lo cuenta entre los pasos medidos, no entre los omitidos.
- **SC-006** La herramienta no baja ni pisa un umbral ya declarado, y el config
  conserva sus comentarios después de escribir.

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
| FR-006 | tests/unit/test_render.py |
| FR-007 | pipeline del kit (workflow presente y generado sin drift) |
| FR-US2-001 | tests/unit/test_adapter_coverage_baseline.py |
| FR-US2-002 | tests/unit/test_adapter_coverage_baseline.py |
| FR-US2-003 | tests/unit/test_sdd_coverage_baseline.py |
| FR-US2-004 | tests/unit/test_sdd_coverage_baseline.py |
| FR-US2-005 | tests/unit/test_sdd_coverage_baseline.py |
| FR-US2-006 | tests/unit/test_sdd_doctor_coverage_inerte.py |
| FR-US2-007 | tests/unit/test_example_config.py |
| FR-US3-001 | tests/unit/test_sdd_config.py |
| FR-US3-002 | tests/unit/test_pipeline_coverage_cache.py |
| FR-US3-003 | tests/unit/test_python_adapter.py |
| FR-US3-004 | tests/unit/test_python_adapter.py |
| FR-US3-005 | tests/unit/test_python_adapter.py |

## Fuera de alcance

- Proveedores de CI distintos de GitHub Actions.
- Cobertura para adaptadores `node`/`go` (no existen todavía).
- Publicar reportes de cobertura a servicios externos.

## Historial

- 2026-08-04: creada (draft) a partir de la comparación con
  `evaluador-flujo-intent`.
- 2026-08-09: reabierta con la US2 (K-5 de `docs/IDEAS.md`): el paso sembrado sin
  umbrales se omitía en cada corrida. La US1 queda intacta —el umbral sigue siendo
  opcional—; lo que se agrega es la forma de conseguir el primero.
- 2026-08-11: FR-006 enmendado (hallazgo de [[SPEC-024-traza-fr-en-test]] al
  verificar que el FR referenciado aparece en el test, no solo que el archivo
  exista): describía un instalador que copiaba `ci.yml` como plantilla estática
  con `--force`; el mecanismo real es que `render.py` lo genera siempre como
  artefacto derivado, igual que `CONSTITUTION.md`. Coverage mapping actualizado
  de `test_sdd_init.py` a `test_render.py`.
- 2026-08-12: agregada la US3. Medido en el propio kit: suite plana ~74s,
  misma suite instrumentada con `--cov` ~141s; el pipeline pagaba las dos
  corridas en secuencia (~215s) para un resultado que una sola corrida
  instrumentada ya da. `tests` y `coverage` siguen siendo pasos separados y
  nombrados (no se toca la decisión de [[SPEC-019-tests-integracion-ejecutados]]);
  lo que se comparte es la ejecución de pytest subyacente, vía
  `SDD_PIPELINE_COVERAGE_CACHE`.
