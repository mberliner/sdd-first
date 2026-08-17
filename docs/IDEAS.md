# Ideas pre-spec — sdd-first

> SSOT del **backlog abierto** del kit: ideas que todavía no son spec. Lo ya
> cerrado —con su post-mortem, que es donde vive la mayor parte del
> conocimiento— está en [`IDEAS-CERRADAS.md`](IDEAS-CERRADAS.md), y los patrones
> que se repiten entre esos cierres, destilados, en [`PATRONES.md`](PATRONES.md).
>
> Una idea se promueve con `sdd-spec` (triage de reutilización primero: puede
> caber en una spec vigente). Al cerrarla, se mueve el ítem a
> `IDEAS-CERRADAS.md` con el puntero `**(cerrado el AAAA-MM-DD)** → [[SPEC-NNN-slug]]`
> y el post-mortem de lo que la implementación encontró y la idea no registraba.

## Cómo se lee este documento

### IDs

Cada ítem tiene un ID estable `<letra>-<número>` y **los IDs no se renumeran ni
se reciclan**: los citan las specs, el historial y hasta comentarios de código
(`adapters/python/check_naming.py` cita B-2). La letra identifica la **tanda**
que encontró el ítem, no su tema:

| Letra | Tanda de origen |
|-------|-----------------|
| B | Happy path de instalación (2026-07-02) |
| C | Bugs y asperezas menores de código (varias tandas) |
| D | Revisión crítica de dogfooding (2026-07-02) |
| E | Producto y distribución |
| F | Segunda comparación con el proyecto de referencia (2026-08-04) |
| G | Huecos de enforcement del gate y la trazabilidad |
| K | Reevaluación kit vs derivado (2026-08-08) |
| R | Duplicación de SSOT dentro del kit |
| T | Abarcabilidad de una spec (2026-08-15) |
| U | Campaña de usabilidad del proyecto derivado (2026-08-05) |
| V | Primera corrida de la suite e2e (2026-08-07) |
| X | Ideas sueltas, sin tanda |

Una tanda nueva toma la próxima letra libre; una idea suelta entra como `X-N`.

### Estados

| Estado | Significado |
|--------|-------------|
| `abierta` | Nadie la tomó todavía. |
| `parcial` | Una spec cerró una parte; el resto sigue acá, descrito en el propio ítem. |
| `cerrada` | Implementada. Se mueve a [`IDEAS-CERRADAS.md`](IDEAS-CERRADAS.md) con su post-mortem. |
| `superseded` | Otro ítem la reencuadró y la reemplaza (ej.: F-7 → K-3). |
| `descartada` | Se evaluó y se dejó afuera. Va al índice de descartes, con el motivo. |

### Prioridades

La prioridad de un ítem se declara **solo** en la tabla del backlog: los títulos
de sección agrupan por tanda, no por prioridad, para que recalibrar un ítem no
obligue a moverlo de lugar.

| Prioridad | Criterio |
|-----------|----------|
| **P0** | El kit se contradice a sí mismo o el happy path de un usuario nuevo está roto. Bloquea la credibilidad del producto. |
| **P1** | Bug real o hueco de enforcement que un usuario va a pisar en las primeras semanas de uso. |
| **P2** | Deuda de diseño/duplicación que va a divergir con el tiempo; conviene pagarla antes de que crezca. |
| **P3** | Mejora de producto/pulido; deseable, no urgente. |
| **—** | Sin triage: la idea está registrada pero nadie la evaluó todavía. No es "menos que P3", es "sin medir". |

---

## Backlog abierto

La tanda de cada ítem no es una columna: la dice la letra del ID (tabla de
arriba).

| ID | Prio | Ítem | Estado |
|----|------|------|--------|
| T-1 | P1 | No existe métrica de abarcabilidad de una spec | abierta |
| G-6 | P1 | `check_traceability` no exige keyword en los FR | abierta |
| G-7 | P1 | `sdd_spec.py` sobrescribe `.sdd/current-spec` completo | parcial |
| X-2 | — | `check_naming` no mira nombres de paquetes/directorios | abierta |
| X-3 | — | Adaptadores `node`/`go` | abierta |
| X-5 | — | `enforcement`/`detail` de un principio admiten un solo token | abierta |
| X-6 | — | El Coverage mapping mapea archivos, no casos | abierta |
| X-7 | — | Índice de ámbitos de las specs | abierta |
| X-9 | P2 | Nada verifica la consistencia del propio backlog | abierta |

---

## Abarcabilidad de una spec (tanda T)

> Salió de preguntarse si el registro necesitaba un mecanismo de **cierre** de
> specs (24 de 25 en `active`). La premisa se cayó en el primer cruce y el debate
> derivó a lo que sí importa: **cuánto trabajo puede tener una spec abierto a la
> vez sin exceder lo que un asistente sostiene con precisión.** Queda un solo
> ítem, T-1, porque las cuatro conclusiones son una sola cadena: si se separan,
> cada mitad vuelve a levantar la que la refuta.

- **T-1 · No existe métrica de abarcabilidad de una spec, y el primer intento de
  fijarla salió mal por un motivo instructivo: se calibró contra un dataset sin
  etiquetas.** La cadena completa, en orden, con lo que cada eslabón refuta:

  **(a) La spec es viva; "cerrar" no es el modelo.** El estado terminal ya existe
  (`archived`/`superseded`) y su criterio es *dejó de ser verdad*, no *el trabajo
  terminó*. Lo que cierra es la **iteración** (entrada en `historial/sdd.md` +
  `[SDD-Check]`), y la columna `Iteración` del registro es el contador de
  reaperturas. El riesgo de "spec vieja vigente para siempre" ya lo resolvió
  [[SPEC-004-enforcement-hardening]] en la **declaración** —`.sdd/current-spec`
  es estado de sesión y se resetea—, no en la spec. Descartado: cualquier estado
  nuevo tipo `implemented`/`done`.

  **(b) Toda métrica de *stock* clasifica mal, y castiga justo la reapertura que
  el modelo quiere.** Medido el 2026-08-15: por FR totales los que se pasan son
  SPEC-022 (22 FR) y SPEC-018 (21), las dos sanas y construidas en 8 y 5
  iteraciones; SPEC-004 lleva **11 iteraciones y 9 FR**, o sea que reusar bien
  *reduce* el tamaño por iteración. Un tope sobre el acumulado premia con una
  partición forzada al que mejor reusa. También se cayó **"una spec = una US"**
  (INVEST, spec-kit): SPEC-019 tiene **4 US y está sana**; el conteo de US es
  stock igual. La única métrica que aislaba el caso raro era de **flujo** —FR por
  iteración: mediana 3,0 · p75 4,3 · máximo sano 7,0 · SPEC-025 en 29—.

  **(c) Pero llamar "no sana" a SPEC-025 era infundado, y la métrica de salud
  correcta invierte el ranking.** *Outlier* no es *defectuosa*: lo único medido
  era tamaño. El único indicio de rework es débil y ambiguo (8 sesiones de
  Clarifications y 7 pasadas de `analyze` contra un máximo de 4 en el resto — se
  lee igual como diligencia proporcional al alcance). Y con la métrica que sí
  importaría, **fuga de defectos** (lo que una pasada posterior encontró que la
  iteración debió cubrir), SPEC-025 va por la iteración 1 y no registra ninguna,
  mientras que la peor puntuada sería **SPEC-004 con 11 reaperturas**, cuyos
  post-mortems dicen textualmente "una tercera pasada encontró…", "una cuarta
  pasada encontró…". Conclusión incómoda y central: **hoy no hay métrica de salud
  para ninguna spec**; todo lo demás son proxies de tamaño y de esfuerzo. El
  umbral "máximo 6 FR pendientes" que este debate llegó a proponer era un umbral
  **no supervisado presentado como empírico**.

  **(d) El límite real es la ventana del asistente — pero no la del documento.**
  La versión ingenua se cae sola: SPEC-025 pesa **~19.600 tokens** (el resto,
  entre 250 y 8.000), o sea que *entra* en cualquier ventana moderna. Lo que ata
  es el **conjunto de trabajo co-residente** que el lote pendiente obliga a tener
  a la vez: spec + `CONSTITUTION.md` + `AGENTS.md` + registro + el código que
  toca + los tests del Coverage mapping + la salida del pipeline cuando falla. La
  spec es una fracción del presupuesto, no el presupuesto. De ahí, tres
  consecuencias de diseño: la unidad es el **presupuesto en tokens**, no el
  conteo de FR, y **es computable con lo que el kit ya tiene** (el Coverage
  mapping da FR→tests, `dirs.source_roots` da el código); el límite es **por
  asistente**, así que nace en `.sdd/config.yaml` y jamás en `core/` —un derivado
  con un modelo de ventana chica necesita lotes chicos sin tocar el núcleo—; y se
  expresa como fracción de la ventana **utilizable**, no de la nominal, porque la
  degradación empieza bastante antes del techo. Límite honesto de la métrica: el
  conjunto calculado es una **cota inferior**, no incluye lo que el asistente lee
  explorando.

  **Sobre las buenas prácticas de origen:** sobrevive la **forma** de la ley
  (lote chico, procesador acotado, degradación al crecer la carga — Reinertsen,
  la "S" de INVEST, el límite por sesión de revisión), y **no** sus constantes:
  las ~200-400 LOC y los ~60 min de la guía de revisión están calibrados a
  fatiga y atención sostenida, que un asistente no tiene. Importar esos números
  sería repetir el error de (c). El método correcto ya está en el kit: **K-3** —
  medís tu piso real y ponés el trinquete ahí.

  **Convergencia que abarata todo:** la unidad de las dos cosas es la misma, el
  **FR pendiente** (escrito, sin fila en el Coverage mapping). Sirve para el lote
  (¿cuánto hay abierto?) y también para una idea hermana que salió del mismo
  debate: **que el gate abra por FR pendiente y no por spec** — hoy
  [[SPEC-017-gate-decision-spec-first]] exige que la spec declarada tenga FR
  escritos, y eso lo satisfacen FR de la iteración 1 para siempre, así que se
  puede `--reuse` una spec vieja, no escribir un solo FR y codear igual. Un
  mecanismo, dos invariantes. Punto espinoso de esa hermana: en TDD el test se
  escribe antes que el código, así que "saldado" no puede ser "existe un test"
  sino "está escrita la fila del mapping" — declarativo, y hay que decidir si
  alcanza.

  **Consecuencia que disuelve el planteo original:** si la unidad es el lote,
  **el límite no parte la spec, parte la iteración**. Se pueden escribir 29 FR;
  lo que no se puede es implementarlos de una. La spec sigue viva y entera, sin
  descendencia artificial. Por eso el enforcement, si algún día se cablea, va en
  el **gate** y no en la escritura: bloquear que se escriba un FR es censurar el
  documento; bloquear editar código con un lote sobredimensionado pendiente es el
  principio de flujo aplicado. Un aviso perpetuo está descartado por precedente
  propio (U-3, C-1, K-5: el aviso que suena siempre enseña que el verde no
  significa nada).

  **La calibración se fue a `sdd-research` (2026-08-16), y este ítem queda
  esperándola.** Medir el corpus, etiquetar la fuga de defectos y decidir si
  existe un umbral se cierra con **evidencia**, no con una edición: es una
  pregunta de investigación y su lugar es el backlog de ese repositorio
  (prioridad alta #15), que además ya tiene el instrumental que hace falta
  —preregistro, piso de ruido antes de reportar una brecha, y el anti-patrón de
  la variable de salida que es artefacto del propio tratamiento, que es
  exactamente el riesgo de etiquetar leyendo nuestros post-mortems—. Allá viven
  el diseño y el resultado; acá no se reproducen.

  Lo que sigue siendo del kit es la **consecuencia**: si el experimento da
  señal, lo que se implementa es una clave de presupuesto en `.sdd/config.yaml`
  y un reporte en `sdd-doctor`; si no da señal, este ítem se cierra como
  descartado con el puntero al resultado. En cualquiera de los dos casos hace
  falta spec, y el triage de [[SPEC-022-reusar-specs-existentes]] tiene que
  decidir antes si cabe en SPEC-017 (es su misma pregunta: qué autoriza una
  edición) o si el presupuesto de contexto es capacidad nueva.

  Un dato del prototipo exploratorio que sí es del kit y conviene no perder: el
  **FR pendiente** (escrito, sin fila en el Coverage mapping) da **0 en las 26
  specs**, porque el flujo escribe la fila en la misma iteración. La unidad
  existe solo *durante* la iteración — sirve para el gate de la idea hermana,
  pero no hay lote que medir mirando el árbol en reposo.

## Huecos de enforcement del gate y la trazabilidad (tanda G)

- **G-6 · `check_traceability` no exige keyword en los FR.** SPEC-FORMAT
  declara obligatorio `MUST:/SHOULD:/MAY:` pero nada lo verifica. Chequeo de
  una línea; alinear doc y check en cualquier dirección.
  **(revisado el 2026-08-14, sigue abierto)** El keyword hoy sí se *parsea*,
  pero para lo contrario de lo que la idea pide: `_FR_KEYWORD`
  (`core/check_traceability.py:171`) lo **elimina** del cuerpo para medir si al
  FR le queda texto propio, que es la evidencia de spec-antes-que-código de
  [[SPEC-017-gate-decision-spec-first]] FR-US3-001. Un FR sin keyword pasa
  igual: `sub` no quita nada y el cuerpo entero cuenta como texto escrito. O
  sea que el ítem no está a medio hacer — el mecanismo que lo parece resuelve
  otra pregunta. Sigue faltando elegir la dirección, y no es gratis en ninguna
  de las dos: endurecer el check obliga a barrer las specs `active` y migrar en
  la misma iteración las que queden en rojo (precedente de
  [[SPEC-024-traza-fr-en-test]], que prohíbe la lista de exenciones); aflojar
  `templates/docs/SPEC-FORMAT.md` deja `sdd_spec.py:309` sembrando el formato
  y `sdd_gate.py:227` citándolo en el mensaje de bloqueo.
- **G-7 · `sdd_spec.py` sobrescribe `.sdd/current-spec` completo.**
  Parcialmente resuelto → [[SPEC-004-enforcement-hardening]] FR-007
  (2026-08-01): ahora preserva el header de comentarios (el síntoma que
  dejaba el working tree sucio tras cada commit, vía `sdd_reset.py`). Sigue
  pendiente la semántica multi-spec en sí: crear una segunda spec todavía
  des-declara la primera sin aviso — falta definir append vs replace (con
  flag).

## Ideas sueltas (tanda X)

- **X-2 ·** `check_naming` también podría chequear nombres de paquetes/directorios, no
  solo identificadores y stems de archivo.
- **X-3 ·** Adaptadores `node`/`go` (deuda ya registrada en historial y SPEC-001).
- **X-5 ·** `enforcement`/`detail` de un principio admiten un solo token: `render.py` los
  envuelve en un único code span y `check_constitution._is_path` valida
  existencia sobre él. Un principio con dos SSOTs de detalle (o con enforcement
  mixto tool + revisión) no se puede expresar. Aceptar listas sería cambio de
  núcleo (config + render + check) y necesita spec propia.
- **X-6 · El Coverage mapping mapea archivos, no casos**. `check_traceability` da por
  cubierto un FR cuando el archivo de test referenciado existe, sin mirar si
  contiene alguna aserción sobre ese requisito. Un FR nuevo que reusa un archivo
  ya presente por otros FR nace verde. Cubrirlo de verdad exigiría convención de
  nombres de test o parsear la suite; medir antes de cablear.
- **X-7 · Índice de ámbitos de las specs**. Generar un índice (User Story +
  *Independent Test* de cada spec) para que el triage de reutilización sea
  semántico y no dependa solo del título. Sale de SPEC-022, que compara títulos:
  el solape real suele vivir en los FR. Necesita spec propia porque implica un
  extractor y un artefacto generado más en el pipeline.
- **X-9 · Nada verifica la consistencia del propio backlog.** Un ítem puede
  declararse cerrado apuntando a una spec que no existe, que no está en
  `SPECS_REGISTRY.md` o que quedó `archived`, y nadie se entera: hoy el estado y
  el puntero son prosa. Es el patrón 5 de [`PATRONES.md`](PATRONES.md) aplicado a
  este archivo. Fix candidato: un check que cruce las tres tablas —backlog
  abierto, "qué idea terminó en qué spec" y el registro— y falle si un ID
  aparece en las dos primeras, si un puntero `[[SPEC-NNN-slug]]` no resuelve a
  una fila del registro, o si un ID se recicla. Al promoverlo, triage con
  [[SPEC-022-reusar-specs-existentes]]: la pregunta se parece a la de
  `check_traceability` (consistencia disco↔registro) y puede caber ahí en vez de
  ser capacidad nueva. Ojo con el alcance: el kit **no** instala este archivo en
  los derivados, así que el check es del propio kit y no debería nacer en
  `core/` sin decidir antes si el backlog es un artefacto SDD o algo nuestro.

## Índice de descartes

Decisiones que se evaluaron y se dejaron afuera, con el puntero a dónde está
escrito el motivo. Existe para no re-litigarlas: el razonamiento no se reproduce
acá.

### Del proyecto de referencia

No todo lo que tiene el evaluador tiene sentido en un kit agnóstico. Se
evaluó y se dejó afuera:

- `schema_drift_check.py`, `connection_check.py`, `e2e_probe.py`,
  `conversation_probe.py` — específicos de su dominio (validar un agente
  conversacional contra un schema versionado).
- Su principio "Evaluación determinista" — es un invariante de *producto*, no
  de método; un proyecto que lo quiera lo escribe en su propio config.
- Migrar el evaluador a consumir el kit — descartado por decisión de producto,
  no por viabilidad técnica.

### De diseño, salidas de una idea o de su implementación

| Descarte | Motivo escrito en |
|----------|-------------------|
| Un estado `implemented`/`done` para specs | T-1 (a) |
| Un tope de FR acumulados por spec, y "una spec = una US" | T-1 (b) |
| Importar las constantes de la industria (~200-400 LOC, ~60 min de revisión) | T-1 |
| Un aviso perpetuo de lote sobredimensionado | T-1, por precedente de U-3 · C-1 · K-5 |
| Registrar el hash de la spec en `.sdd/current-spec` | G-5 → [[SPEC-017-gate-decision-spec-first]] |
| Migrar `sdd_init` a `argparse` | C-7 → [[SPEC-003-install-happy-path]] |
| Preguntarle al adaptador qué pasos soporta | C-8 → [[SPEC-005-desduplicar-ssot]] |
| Una clave `tests_root` explícita en el config | V-4 → [[SPEC-019-tests-integracion-ejecutados]] |
| Un `docs/CONFIG-REFERENCE.md` en prosa, y `config.example.yaml` | K-2 → [[SPEC-013-proyecto-derivado-coherente]] |
| Que `sdd-init` mida la cobertura del proyecto durante la instalación | K-5 → [[SPEC-009-coverage-y-ci]] |
| Que `check_constitution` compare contra `principles:` del config | K-1 → [[SPEC-014-derivado-dice-la-verdad]] |
| Declarar "el kit es desechable" también del lado del derivado | K-6 |
| Una clave `strict` por principio, y el ROJO por principio no enforzado | X-8 → [[SPEC-020-enforcement-declarado-en-config]] |
| Una lista de exenciones para las specs que un check nuevo pone en rojo | G-8 → [[SPEC-024-traza-fr-en-test]] (lo prohíbe `AGENTS.md`) |
| Las asimetrías kit↔derivado que son legítimas | encabezado de la tanda K, en [`IDEAS-CERRADAS.md`](IDEAS-CERRADAS.md) |
