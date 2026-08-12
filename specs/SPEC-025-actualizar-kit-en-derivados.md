# SPEC-025-actualizar-kit-en-derivados: El andamiaje instalado se puede actualizar sin perder lo propio

> **SSOT de la ruta de actualización del andamiaje vendorizado**: qué registra la
> instalación, qué se puede pisar al actualizar y qué no, y qué ve el operador
> antes de que se escriba nada. Origen: E-2 de `docs/IDEAS.md`, abierto desde la
> primera revisión crítica y reproducido en la campaña de usabilidad ("ningún
> documento del derivado lo explica").
>
> **El kit es un generador de un solo disparo.** Cada arreglo del andamiaje se
> queda en el kit y no llega a ningún derivado ya instalado: el mojibake de
> Windows ([[SPEC-012-suite-multiplataforma]]), el wiring que pre-filtraba por
> `src/` ([[SPEC-015-wiring-apunta-al-codigo-real]]), el gate que se rompía en el
> ciclo stash/restore de `pre-commit`
> ([[SPEC-017-gate-decision-spec-first]]) y el config vacío que tumbaba el
> pipeline ([[SPEC-021-config-vacio-no-rompe]]). Un proyecto instalado antes de
> esas iteraciones convive con los cuatro y su única salida documentada,
> `sdd-init --force`, además de no mostrar nada, le borra
> `specs/SPECS_REGISTRY.md` y `historial/sdd.md`.
>
> **Cierra el hueco que deja [[SPEC-013-proyecto-derivado-coherente]] y el
> README del kit:** "el kit es desechable, la única razón legítima para volver a
> él es actualizar el andamiaje" (K-6) es hoy una promesa sin mecanismo.
>
> **Fuera de esta spec, por eje distinto:** la instalación inicial
> ([[SPEC-003-install-happy-path]]), la coherencia de lo instalado en un momento
> dado ([[SPEC-013-proyecto-derivado-coherente]],
> [[SPEC-014-derivado-dice-la-verdad]]) y la distribución del kit como paquete
> (E-3 de `docs/IDEAS.md`).

## User Story 1 (Priority P1) — el derivado registra qué versión tiene y cómo quedó

Como quien mantiene un proyecto derivado, quiero que la instalación deje
registrado qué versión del andamiaje instaló y con qué contenido exacto, para
poder saber después si estoy atrasado y qué archivos toqué yo.

**Why this priority:** es la precondición de todo lo demás y hoy no existe.
`project.kit_version` no mide nada: `sdd_init._write_config` copia
`examples/config/config.yaml` y solo reescribe `name`, `language`,
`default_branch`, `steps`, `principles` y `dirs` — la línea
`kit_version: "0.1.0"` viaja literal, así que **todo derivado, de cualquier
fecha, declara 0.1.0**. No es que `sdd-doctor` "no la compare contra nada": no
hay nada que comparar, porque el kit no declara su propia versión en ninguna
parte. Y sin saber si un archivo sigue como se instaló, la única política de
actualización posible es pisar todo o no pisar nada.

**Independent Test:** instalar en una carpeta vacía y afirmar que
`.sdd/kit.lock` declara la versión real del kit, un hash por cada `plantilla`
instalada que coincide con el contenido en disco y la presencia de cada
`semilla`; editar un documento y afirmar que el lock ya no coincide para ese
archivo y sí para el resto.

## User Story 2 (Priority P1) — actualizar sin perder lo propio

Como dueño de un proyecto derivado, quiero traer las mejoras del andamiaje sin
perder lo que escribí ni lo que adapté, para que actualizar no sea una decisión
entre quedarme con bugs conocidos o rehacer mi proyecto.

**Why this priority:** es la capacidad ausente, y su falta no es neutral: lo que
hoy existe en su lugar destruye datos. `STATIC_DOCS` incluye
`specs/SPECS_REGISTRY.md` y `historial/sdd.md`, y `WIRING` incluye `.gitignore` y
`.pre-commit-config.yaml`; un `sdd-init --force` sobre un proyecto con meses de
uso borra el registro de specs y el historial de iteraciones — el corazón del
método que el kit vende. La distinción que falta no es técnica sino de
**propiedad**: `tools/sdd/` es del kit, `CONSTITUTION.md` es derivado del config,
`AGENTS.md` es una plantilla que el dueño pudo adaptar, y `specs/` es suyo y de
nadie más.

**Independent Test:** sobre un derivado instalado con una versión anterior, con
un documento de plantilla editado a mano y un registro de specs con filas
propias, correr la actualización y afirmar que el andamiaje vendorizado quedó en
la versión nueva, los artefactos generados regenerados, el registro y el
historial **intactos**, y el documento editado no pisado sino reportado como
conflicto.

## User Story 3 (Priority P1) — ver qué va a cambiar antes de que cambie

Como operador que actualiza, quiero ver el plan completo antes de que se escriba
nada, para decidir con evidencia en vez de correr un comando y auditar el
destrozo después.

**Why this priority:** la actualización es un evento **raro** —cada varios meses,
sobre un proyecto que quien la corre probablemente no instaló—, así que no puede
apoyarse en que el operador recuerde qué archivos adaptó. Es además la mitad
explícita de E-2 ("actualizar es `--force` manual **sin diff**"). Y es el mismo
invariante que el kit ya aplica en todo lo demás: `render.py --check` y
`gen_skill_adapters.py --check` muestran el drift sin escribir, y
`sdd_init._abortar` no escribe nada ante una invocación que no entiende
([[SPEC-003-install-happy-path]] FR-012).

**Independent Test:** correr la actualización sin `--apply` sobre un derivado
atrasado y afirmar que el árbol queda byte a byte idéntico (incluido el lock) y
que la salida clasifica cada artefacto afectado; repetir con `--diff` y afirmar
que muestra el contenido del cambio.

## User Story 4 (Priority P2) — saber qué trae la versión nueva

Como quien decide si actualizar, quiero leer qué cambió entre mi versión y la
nueva en términos de capacidades, para juzgar si me conviene ahora y qué mirar
después de aplicar.

**Why this priority:** un plan que lista cuarenta archivos responde "qué se
toca", no "qué gano ni qué riesgo corro". Es P2 porque US1..US3 ya hacen la
actualización posible y segura; esto la hace decidible. Sin esto, además, la
versión del kit sería un número sin significado: nada obliga a bumpearlo ni dice
qué significa el bump.

**Independent Test:** con un `CHANGELOG.md` que declara dos versiones entre la
instalada y la del kit, el plan cita esas dos entradas y ninguna otra.

## Relación con specs existentes

- **Extiende:** [SPEC-003](SPEC-003-install-happy-path.md), [SPEC-014](SPEC-014-derivado-dice-la-verdad.md) | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** ninguna spec vigente gobierna el
  ciclo de vida **posterior** a la instalación. El triage marcó 18 candidatas
  solo por compartir `core/sdd_init.py` y `core/sdd_config.py`, que son módulos
  centrales que casi toda spec toca —compartir archivos no es una relación
  declarable—. El eje propio es el paso del tiempo, y trae entidades nuevas
  (versión del kit, manifiesto de instalación, clases de propiedad de cada
  artefacto) y un comando nuevo. Ahora bien, una ruta de actualización sin
  registro de qué se instaló es imposible, así que la spec **amplía** dos
  vigentes en vez de rozarlas: extiende [SPEC-003](SPEC-003-install-happy-path.md)
  —`sdd-init` pasa a escribir el lock, deja de sembrar `project.kit_version` y
  `--force` deja de destruir lo que es del dueño— y
  [SPEC-014](SPEC-014-derivado-dice-la-verdad.md), cuyo aviso de wiring conservado
  cambia el remedio que recomienda. [[SPEC-013-proyecto-derivado-coherente]] no se
  toca: gobierna la coherencia de lo instalado en un momento dado, que sigue
  valiendo igual antes y después de actualizar.

## Clarifications

### Session 2026-08-12

- Q: ¿No alcanza con arreglar `sdd-doctor` para que compare `kit_version`, que es
  como está escrito E-2? → A: no, porque `kit_version` es una constante copiada
  del ejemplo: siempre dice `0.1.0`. Compararla contra el kit reportaría que
  **todo** derivado está atrasado, incluido uno instalado hace cinco minutos. El
  registro tiene que escribirlo la instalación, no el catálogo de claves.
- Q: ¿Por qué un archivo nuevo y no la clave del config? → A: el config es del
  dueño y es editable; un registro de instalación que el dueño puede tocar deja
  de ser registro. Y hay una sola verdad posible sobre qué versión se instaló, así
  que la clave `project.kit_version` **se elimina** del catálogo y del sembrado en
  vez de quedar como copia informativa (Principio IV).
- Q: ¿Por qué hashes y no preguntarle a git si el archivo cambió? → A: git no
  distingue "lo editó el dueño" de "lo instaló `sdd-init` en el commit inicial",
  que es el caso normal: el 100% de la instalación entra en un solo commit. Y el
  derivado puede no ser un repo git todavía. El hash responde exactamente la
  pregunta que importa, sin depender del historial.
- Q: ¿Qué pasa con los derivados ya instalados, que no tienen lock? → A: se
  actualizan igual, en modo degradado: sin lock no se puede afirmar que una
  plantilla esté intacta, así que **todas** se tratan como editadas y ninguna se
  pisa. El vendorizado y los generados sí se actualizan (su autoridad no depende
  del lock). Al terminar queda lock escrito y la siguiente actualización ya es
  precisa.
- Q: ¿`--apply` u opt-out (`--yes`)? → A: preview por defecto y escritura bajo
  `--apply`. Un comando raro y destructivo no puede tener la escritura como
  default; y el kit ya tiene el precedente invertido de `render.py`, donde
  escribir es lo normal y `--check` lo excepcional, precisamente porque ahí lo que
  se escribe es derivado y descartable.
- Q: ¿Se reescribe `.sdd/config.yaml` para incorporar claves nuevas? → A: no.
  Reescribir YAML destruye comentarios, y es el archivo que el dueño más edita.
  `.sdd/config.reference.yaml` ya se reinstala siempre
  ([[SPEC-013-proyecto-derivado-coherente]] FR-008): alcanza con nombrar las
  claves que la referencia nueva trae y el config no tiene.
- Q: ¿Y si el dueño adaptó el wiring del gate? → A: es conflicto como cualquier
  otra plantilla, y no se pisa. `sdd-init` ya lo conserva por diseño y avisa
  ([[SPEC-014-derivado-dice-la-verdad]] FR-US1-001): pisarlo al actualizar sería
  contradecir esa decisión en el momento de menos supervisión.
- Q: ¿Se instala la skill `sdd-update` en el derivado, como el resto? → A: no.
  `PROJECT_SKILLS` son las que operan el derivado sin el kit; ésta necesita
  justamente el clon del kit nuevo, así que vive en el kit, del lado del que
  actualiza. Instalarla en el derivado sería prometer un comando que ahí no puede
  correr.
- Q: ¿Cómo llega el kit nuevo a la máquina? → A: fuera de alcance. La
  actualización se corre **desde el clon del kit apuntando al derivado**,
  simétrica a `sdd-init`. Que el derivado se autoactualice tirando de una red
  exige distribución (E-3), que es otra capacidad.
- Q: ¿El derivado necesita declarar una spec para recibir la actualización? → A:
  no. `tools/sdd/` está fuera de `dirs.source_roots` del derivado —asimetría ya
  declarada legítima en la reevaluación kit↔derivado—, así que el gate no
  interviene: el andamiaje es infra vendorizada, no el producto del proyecto.

### Session 2026-08-12 (`analyze`) — qué registra el lock y desde dónde se corre

- Q: (ANA-001) Tras un conflicto no resuelto, ¿el lock guarda el hash del archivo
  del dueño que quedó en disco, o el de la versión que traía el kit? → A: **el del
  kit**, y no es un detalle: guardar el del disco es un bug que pierde datos. El
  lock respondería "coincide" en la actualización siguiente, el archivo pasaría por
  intacto y la edición del dueño se pisaría **en silencio**, que es exactamente lo
  que esta spec existe para impedir. El lock deja de ser "cómo quedó el disco" y
  pasa a ser **qué entregó el kit**: la línea base contra la que se mide toda
  edición posterior. Efecto colateral deseable: si el dueño resuelve el conflicto
  adoptando la versión del kit, el archivo vuelve solo a "intacto" en la próxima
  corrida, sin tener que declararlo.
- Q: (ANA-002) Sin lock previo, ¿cómo se identifican los archivos `vendor`
  obsoletos? → A: no se identifican: el andamiaje se **purga y se recrea** entero,
  con o sin lock. Es 100% del kit, así que no hay nada que preservar ni que
  comparar, y el diff archivo por archivo solo agregaría una heurística que puede
  fallar. Además limpia residuos que hoy nadie borra (`__pycache__` viaja en el
  `copytree` de `_vendor_kit`). Borde: si el kit nuevo ya no trae el adaptador del
  lenguaje que el derivado declara, se aborta nombrándolo — dejar al derivado sin
  adaptador rompería su pipeline en la corrida siguiente, lejos de la causa.
- Q: (ANA-004) ¿Dónde vive físicamente la versión del kit? → A: constante
  `KIT_VERSION` en `core/sdd_config.py`, que ya es el hogar de las constantes del
  núcleo que otros módulos consultan (`VENDOR_PREFIX`, `GATE_WIRING`,
  `CODE_STEPS`, `TEST_DIRS`). Se evaluó un `core/VERSION` de texto plano, legible
  sin importar Python: se descartó porque ningún consumidor sin Python necesita la
  versión —a diferencia de `source_roots`, que sí la necesitan las capas de wiring
  en shell y JS ([[SPEC-015-wiring-apunta-al-codigo-real]])— y sería un archivo
  más que mantener sincronizado.
- Q: (ANA-005) Al regenerar, ¿se invoca `render.py` del clon del kit o el ya
  copiado en el destino? → A: **el del destino, después de actualizar el vendor**,
  con la raíz del derivado como directorio de trabajo. Dos razones: los
  regeneradores resuelven rutas y placeholders según si el repo es el kit o un
  derivado (`is_kit_repo` mira `templates/`), y correr el del clon dejaría al
  derivado renderizado por un script que no es el suyo; y ejecutar el recién
  copiado es la primera prueba de que el andamiaje nuevo funciona **ahí**, en vez
  de que el fallo aparezca en la próxima corrida del pipeline del dueño.
- Q: (ANA-006) ¿Con qué nombre queda la versión nueva al lado de un conflicto? →
  A: `<archivo>.kit-new`, sobrescrito en cada corrida. Sufijo propio y no `.new`
  genérico para que sea inequívoco de dónde salió y grepeable; va al final para no
  cambiar la extensión del original, que es lo que decide si algún paso lo mira.
- Q: (ANA-007) ¿Qué algoritmo de hash? → A: `sha256` sobre los bytes del archivo,
  declarado en el propio lock para que un cambio futuro de algoritmo sea legible
  en el archivo y no una ruptura silenciosa.

### Session 2026-08-12 (`analyze` 2) — el borde entre instalar y actualizar

- Q: (ANA-008) ¿Con qué valores se resuelven los placeholders al actualizar? → A:
  con los que declara `.sdd/config.yaml` del destino (`project.name`,
  `project.domain`), por el mismo helper que usa la instalación, y el lock
  **registra los valores usados**. Sin esto el criterio quedaba implícito y
  divergía: `sdd-init` sustituye hoy con el nombre de la carpeta destino y un
  `domain` literal de TODO, así que una actualización que leyera el config de un
  derivado ya configurado renderizaría distinto **toda** plantilla con
  placeholder y las reportaría a todas como conflicto. Lo que decide "intacta"
  nunca es la comparación contra el kit nuevo sino contra el lock, así que
  cambiar el dominio del proyecto no ensucia el veredicto: solo cambia lo que se
  escribe.
- Q: (ANA-009) ¿Qué pasa si la regeneración falla con el `vendor` ya recreado? →
  A: se aborta con código distinto de cero, sin reescribir el lock, nombrando que
  el andamiaje ya quedó en la versión nueva y qué reintentar. El lock es lo
  **último** que se escribe, y precisamente por eso un fallo intermedio queda
  legible: el lock viejo contra el `KIT_VERSION` nuevo es la definición de
  "actualización a medio aplicar" que FR-US1-005 le pide detectar a `sdd-doctor`.
  No hay rollback: restaurar el `vendor` anterior exigiría guardarlo, y el
  derivado prudente commitea antes de aplicar.
- Q: (ANA-010) En una instalación brownfield, ¿qué hash registra el lock de un
  archivo que ya existía y se conservó? → A: **el de la versión del kit**, no el
  del archivo del dueño. Es el mismo razonamiento de ANA-001 aplicado al origen:
  registrar el archivo del dueño lo daría por intacto y la primera actualización
  lo pisaría en silencio. Registrar el del kit lo hace nacer como conflicto, que
  es exactamente lo que es.
- Q: (ANA-011) ¿Y `.sdd/current-spec`, que se instala como wiring? → A: es
  `semilla`. Se reescribe con cada commit y ni siquiera se versiona (SPEC-004
  FR-008), así que como `plantilla` daría conflicto en **toda** actualización de
  **todo** derivado vivo. El resto del wiring (`.gitattributes`,
  `.agents/hooks.json`, los hooks del gate) sí es `plantilla`: son del kit y el
  dueño los pudo adaptar.
- Q: (ANA-012) ¿Qué pasa con una `plantilla` que el kit nuevo ya no trae? → A: si
  coincide con el lock se elimina —el dueño nunca la tocó, y dejarla es prometer
  una capacidad discontinuada—; si difiere, se reporta como conflicto y se
  conserva. Aplica igual a un `SKILL.md` retirado, cuyo adaptador generado se va
  con él. `semilla` y `dueño` no se eliminan nunca.
- Q: (ANA-013) ¿Quién limpia los `.kit-new`? → A: la corrida siguiente, cuando el
  archivo vuelve a coincidir con el lock: el conflicto se resolvió y el testigo
  sobra. El plan los lista, y el `.gitignore` **plantilla** del kit los ignora,
  para que un derivado nuevo no los commitee sin querer. El `.gitignore` de un
  derivado existente no se toca (FR-US2-002): el plan nombra la línea que le
  falta, como con cualquier otra clave.
- Q: (ANA-014) ¿`sdd-init --force` sigue borrando el registro y el historial? →
  A: no. Si el catálogo de clases es SSOT compartido por instalación y
  actualización (FR-US2-001), `--force` respeta `semilla` y `dueño` igual que la
  actualización. Cerrar la ruta nueva y dejar abierta la vieja —la que el README
  todavía nombra— haría falso a SC-002 por la puerta de al lado.
- Q: (ANA-015) ¿Qué destinos rechaza? → A: uno sin andamiaje instalado (sin
  `.sdd/config.yaml` ni `{{sdd.core}}`), porque actualizar no es instalar y
  dejaría media instalación que nadie pidió; y el repo del propio kit, donde
  purgar `tools/sdd/` no significa nada. Ambos abortan sin escribir, nombrando el
  motivo y el comando correcto (`sdd-init` en el primer caso).
- Q: (ANA-016) Sin lock no hay versión instalada: ¿qué hacen las reglas que la
  usan? → A: FR-US2-007 no aplica —no hay con qué comparar, y bloquear por las
  dudas dejaría sin salida justo a los derivados que más necesitan actualizar— y
  el plan cita el changelog entero declarando que la versión instalada se
  desconoce. Los derivados anteriores a esta spec tampoco traen `KIT_VERSION`
  vendorizado, así que no hay fallback que inventar.
- Q: (ANA-017) ¿El catálogo enumera también los artefactos `generado`? → A: no.
  Los conocen `render.py` y `gen_skill_adapters.py`, que son su SSOT; listarlos
  otra vez sería la duplicación que FR-US2-001 existe para evitar. Tampoco entran
  al lock: se rehacen en cada actualización, y su drift ya lo vigila
  `render --check` en el pipeline del derivado. El lock cubre `plantilla` y
  `semilla`, que son las únicas clases donde una edición del dueño decide algo.
- Q: (ANA-018) ¿Dónde se verifica el changelog? → A: en un unitario que exige
  entrada para la `KIT_VERSION` vigente, que el paso `tests` del pipeline corre
  como cualquier otro. "Bumpear sin entrada" no es verificable —un test no ve la
  versión anterior—; el invariante equivalente y comprobable es que la versión
  vigente esté documentada.
- Q: (ANA-019) ¿El `sdd-doctor` final decide el resultado? → A: sí: si reporta
  problemas, la actualización termina en rojo. Ya escribió todo, así que el valor
  está en que el operador se entere ahí y no en la próxima corrida del pipeline.
  Su siembra de `.sdd/current-spec` es escritura esperada, no una violación del
  catálogo.

### Session 2026-08-12 (`analyze` 3) — `--force`, altas del catálogo y el cierre

- Q: (ANA-002) `--force` respeta `semilla` y `dueño`, ¿pero qué hace con una
  `plantilla` que el dueño editó? → A: la misma política de conflictos que
  `sdd-update`: no la pisa, deja la versión del kit en `.kit-new` y la reporta.
  Cualquier otra respuesta hace falso a SC-002 por la misma puerta que FR-US2-013
  vino a cerrar, y encima en el comando de menos supervisión. `--force` sigue
  teniendo sentido —reinstala el `vendor`, regenera y pisa las plantillas
  **intactas**, que es el caso normal—: lo que fuerza es la reinstalación, no la
  destrucción de lo que el dueño escribió. Consecuencia: el aviso de wiring
  conservado ([[SPEC-014-derivado-dice-la-verdad]] FR-US1-001) deja de recomendar
  `--force` como "pisa tu versión" y pasa a nombrar el `.kit-new` que queda al
  lado para fusionar.
- Q: (ANA-003) ¿Y una `plantilla` o `semilla` que el kit nuevo trae y no existía
  antes? → A: se instala de cero, se reporta como `nuevo` en el plan y entra al
  lock. Es el caso de toda capacidad nueva del andamiaje —un playbook, una skill,
  un doc— y sin declararlo la actualización sólo sabría propagar cambios sobre lo
  ya instalado, que es la mitad del problema. La `semilla` nueva se crea sólo si
  falta, por definición de su clase.
- Q: (ANA-004) Si el lock es lo último que se escribe, ¿cómo puede `sdd-doctor`
  correr al terminar y sembrar `.sdd/current-spec`? → A: el doctor corre
  **después** del lock ya sellado, y no lo contradice: FR-US2-011 ordena la
  *aplicación*, y el doctor es la verificación posterior, no un paso de ella. De
  hecho necesita el lock escrito, porque parte de lo que verifica es que el lock
  coincida con el `KIT_VERSION` vendorizado (FR-US1-005). Lo que siembra es
  `semilla` local no versionada, así que no altera ninguna línea base.
- Q: (ANA-005) ¿Y si la versión instalada no figura en el `CHANGELOG.md` (kit
  local, historial truncado, versión de desarrollo)? → A: el mismo fallback que
  sin lock: cita el changelog completo y avisa que no encontró la versión
  instalada. La alternativa —abortar, o citar en silencio desde la entrada más
  vieja— convertiría un changelog incompleto en un bloqueo o en una lista que
  miente sobre qué se gana.

### Session 2026-08-12 (`analyze` 4) — el modo degradado y qué guarda el lock

- Q: (ANA-022) Sin lock, ¿una plantilla que el derivado **no tiene** es conflicto
  o alta? → A: alta, y se instala. "Sin lock, todo es conflicto" se escribió
  pensando en archivos que existen; aplicado a los que no, dejaría a los derivados
  anteriores a esta spec —el caso que SC-005 promete— sin recibir ninguna
  capacidad nueva del andamiaje, y sembrados de `.kit-new` de archivos
  inexistentes. Lo que el lock ausente impide afirmar es que un archivo esté
  intacto; sobre uno que no está no hay nada que afirmar.
- Q: (ANA-023) Entonces `--force` sin lock, ¿no pisa nada? → A: no pisa ninguna
  plantilla presente, y **lo dice**. Es incómodo —es justo el escenario donde el
  operador lo usa, wiring viejo o roto— pero la alternativa es pisar a ciegas
  ediciones que no puede distinguir, que es el daño que la spec impide. La salida
  explícita más los `.kit-new` dejan la fusión al alcance de la mano, y la corrida
  siguiente ya tiene lock y decide con precisión.
- Q: (ANA-024) ¿La spec extiende a otras o sigue siendo de eje propio? → A: las
  dos cosas, y hay que declararlo: el eje es el paso del tiempo, pero la ruta de
  actualización es imposible sin cambiar la instalación, así que **extiende**
  [SPEC-003](SPEC-003-install-happy-path.md) —`sdd-init` escribe el lock, deja de
  sembrar `project.kit_version`, `--force` cambia de semántica— y
  [SPEC-014](SPEC-014-derivado-dice-la-verdad.md), cuyo aviso de wiring conservado
  cambia el remedio que ofrece. Compartir módulos no sería relación declarable;
  ampliar el alcance de lo que esas specs gobiernan, sí.
- Q: (ANA-025) ¿Y una plantilla que el lock registra y el dueño borró? → A: se
  reporta y no se reinstala. Borrar es una decisión tan deliberada como editar:
  reponerla en cada corrida deshace en silencio lo que el dueño quiso, que es el
  mismo daño de esta spec visto del otro lado. Distinto es la que **nunca** se
  entregó (no está en el lock): esa es alta y se instala.
- Q: (ANA-026) ¿Para qué sirve el hash de una `semilla`? → A: para nada, así que
  no se guarda. Una `semilla` no se actualiza nunca, de modo que nadie compararía
  ese hash; el de `.sdd/current-spec` además nacería desactualizado —cambia con
  cada commit— y viajaría versionado sin significar nada. Lo único que el
  mecanismo necesita saber de una `semilla` es si ya se entregó, para distinguir
  "el dueño no la tiene todavía" de "la borró": eso lo responde su presencia en el
  lock.
- Q: (ANA-027) ¿`.gitignore` es `semilla` si la instalación lo modifica? → A: es
  `semilla` con una excepción declarada: la instalación le agrega la línea que
  exige [[SPEC-004-enforcement-hardening]] FR-009, porque sin ella el gate queda
  neutralizado en silencio. La actualización no hereda esa licencia. La excepción
  escrita es preferible a una clase elegida para que la regla cierre.
- Q: (ANA-028) ¿Quién avisa de las líneas que le faltan al `.gitignore`? → A: el
  plan, con el mismo criterio que usa para las claves del config: nombrar sin
  tocar. Estaba prometido en ANA-013 y no tenía requisito, así que ningún test lo
  iba a exigir y todo derivado anterior habría versionado sus `.kit-new` sin
  enterarse.

### Session 2026-08-12 (`analyze` 5) — entradas rotas y permisos

- Q: (ANA-029) Un `.sdd/kit.lock` ilegible —sintaxis rota, claves mínimas
  ausentes—, ¿degrada a "sin lock" o aborta? → A: **aborta sin escribir**,
  nombrando el archivo y qué no pudo leer, y ofreciendo la salida explícita
  (borrar el lock corre en modo degradado). Degradar solo es seguro para los
  datos: no se pisaría nada. Pero el lock se versiona (FR-US1-003), así que la
  causa más probable de un lock roto es un conflicto de merge sin resolver, y
  tratarlo como "no sé nada" haría que el proyecto perdiera su línea base sin que
  nadie se enterara —y que la corrida siguiente reportara como conflicto cada
  plantilla del derivado, sin explicar por qué—. Que el operador decida
  descartarlo es distinto de descartarlo por él. `sdd-doctor` lo reporta como
  problema, no como la nota que merece un lock ausente.
- Q: (ANA-030) ¿Y si `.sdd/config.yaml` no se puede parsear? → A: aborta antes de
  tocar nada, nombrando el archivo y el error del parser. No es un caso exótico:
  el config es el archivo que el dueño más edita, y la actualización **necesita**
  leerlo para resolver los placeholders (FR-US2-010), así que la alternativa es
  reventar a mitad de camino con una traza de YAML que no dice qué hacer. Vale
  igual para el plan, que resuelve los mismos placeholders sin escribir.
- Q: (ANA-031) ¿Qué pasa con el bit de ejecución de los hooks? → A: al escribir un
  artefacto que el catálogo declara ejecutable se le aplica el bit, igual que en
  la instalación (`_EXECUTABLE_WIRING`): un hook sin `+x` deja el gate mudo en
  silencio, que es el fallo que [[SPEC-014-derivado-dice-la-verdad]] persigue. El
  `.kit-new` **no** lo lleva: es un testigo para comparar, y darle permiso de
  ejecución invita a correr un archivo que nadie revisó. El hash cubre bytes, no
  permisos, así que un cambio de permisos del dueño no cuenta como edición y no
  genera conflicto: sobre una plantilla intacta se pierde al actualizar.
  Consecuencia aceptada —el kit no puede distinguir un `chmod` deliberado de uno
  accidental de `git`, y el modo que hace funcionar al gate es el del kit—.

### Session 2026-08-12 (`analyze` 6) — la versión no es el veredicto

- Q: (ANA-032) Un derivado "ya en la versión del kit", ¿no tiene nada que
  recibir? → A: sí puede tenerlo, y cortar por versión hace inerte a la spec en
  su caso más frecuente. El kit se desarrolla en `main` y `KIT_VERSION` sólo se
  bumpea al publicar: un derivado instalado desde el clon local y actualizado
  desde ese mismo clon una semana después está atrasado **sin que la versión lo
  diga**, y los hashes del lock lo saben. Lo que decide si hay trabajo es la
  comparación de contenido —la misma que ya decide "intacta"—; la versión sirve
  para dos cosas y ninguna es ésa: citar el changelog (FR-US4-002) y abortar si
  la instalada es posterior (FR-US2-007).
- Q: (ANA-033) `specs/SPECS_REGISTRY.md` e `historial/sdd.md` son `semilla`, pero
  el `vendor` nuevo trae reglas que los juzgan. ¿Alcanza con no tocarlos? → A:
  no. Precedentes reales: SPEC-023 hizo obligatoria la sección de relaciones y
  SPEC-024 exige el FR como token dentro del test. Tras actualizar, el pipeline
  del derivado corre reglas nuevas sobre contenido viejo del dueño y se rompe
  **lejos de la causa**, en la próxima corrida y sin mencionar la actualización.
  Migrar sigue fuera de alcance —es contenido del dueño—, pero **avisar** no: la
  entrada del changelog declara qué cambios exigen acción y el plan las destaca
  antes de escribir.
- Q: (ANA-034) Si `sdd-doctor` decide el resultado, ¿un problema preexistente
  del derivado hace fallar una actualización correcta? → A: hoy sí, y es un
  falso rojo: el doctor reporta wiring, `.gitignore`, tests sin ejecutor y
  relaciones sin cerrar, deuda que el dueño ya tenía. Se corre **antes y
  después**: lo que ya estaba se reporta como preexistente y no decide nada; lo
  que aparece en la corrida nueva es responsabilidad de la actualización y la
  pone en rojo. Sin la línea base previa, el operador no puede distinguir "falló
  la actualización" de "mi proyecto ya estaba así".
- Q: (ANA-035) ¿Qué clase tiene `.sdd/config.reference.yaml`? → A: `vendor`, aun
  viviendo fuera de `tools/sdd/`. Es el catálogo de claves del kit y
  [[SPEC-013-proyecto-derivado-coherente]] FR-008 ya manda reescribirlo siempre;
  como `plantilla` una edición lo congelaría en conflicto y como `semilla`
  quedaría viejo, y en los dos casos FR-US3-004 —que compara el config del dueño
  contra la referencia **nueva**— nombraría claves de una versión anterior. La
  clase describe autoridad, no ubicación.
- Q: (ANA-036) ¿Dónde vive el ejecutable y cómo se lo invoca? → A: en
  `core/sdd_update.py`, con la CLI simétrica a `sdd-init` (destino posicional o
  `--target`, más `--apply` y `--diff`). Viaja vendorizado, porque `_vendor_kit`
  copia `core/` entero y excluir un archivo sería una lista más que mantener;
  para que eso no prometa lo que no puede cumplir, aborta si su propio origen no
  es un clon del kit (sin `templates/`), que es exactamente el caso del
  vendorizado del derivado.
- Q: (ANA-037) ¿Alcanza con el README y `SDD-OPERACION`? → A: no. La spec crea
  tres SSOT —`CHANGELOG.md`, el catálogo de clases de propiedad y
  `.sdd/kit.lock`— y el protocolo exige que todo SSOT esté en el mapa de
  `00-INDEX.md` (Principio IV). Vale para el del kit y para el del derivado, que
  es plantilla.
- Q: (ANA-038) SC-002 promete que ninguna edición del dueño se pierde sin
  reporte, pero FR-US2-005 acepta perder un `chmod`. ¿Cuál gana? → A: gana
  FR-US2-005 y SC-002 se acota: habla de **contenido**, y nombra la excepción de
  permisos en vez de dejar un criterio de éxito literalmente falso. Un criterio
  con una excepción escrita es verificable; uno absoluto que el propio cuerpo
  contradice, no.
- Q: (ANA-039) Sin lock, ¿se elimina una plantilla que el kit nuevo ya no trae?
  → A: no. Sin lock no se puede afirmar que esté intacta, y FR-US2-012 sólo
  autoriza eliminar lo que coincide: se reporta y se conserva, igual que
  cualquier otra plantilla presente en modo degradado.
- Q: (ANA-040) ¿Quién lee los valores de sustitución que guarda el lock? → A: el
  plan, cuando difieren de los del config actual: es la única explicación de por
  qué una corrida reescribe **toda** plantilla con placeholder sin que ninguna
  esté en conflicto (FR-US2-010). Sin consumidor declarado sería un dato que
  diverge sin que nadie se entere.
- Q: (ANA-041) ¿`--diff` con `--apply`? → A: válido: `--diff` es modificador de
  salida, no un modo. Con el parseo estricto de FR-US3-005 el silencio se paga
  con un aborto que nadie decidió.
- Q: (ANA-042) ¿Por qué partir el Coverage mapping? → A: porque
  `test_sdd_update.py` cubría nueve FR y [[SPEC-024-traza-fr-en-test]] sólo
  puede exigir que el token aparezca en el archivo: nueve FR en un archivo hacen
  pasar la traza con un test que los cita en un comentario. Se parte por eje
  —vendor y orden, plantillas, doctor— para que la fila signifique algo.

### Session 2026-08-12 (`analyze` 7) — el alta que colisiona y el formato del lock

- Q: (ANA-043) Una `plantilla` que el kit nuevo trae, que el lock no registra y
  que **ya existe en disco** porque el dueño escribió un archivo suyo en esa
  ruta, ¿es alta? → A: no: es conflicto, no se pisa y la versión del kit queda
  en `.kit-new`. FR-US2-012 decía "se instala de cero" pensando en una ruta
  vacía, y aplicado a una ocupada perdía en silencio un archivo del dueño, que
  es exactamente lo que SC-002 prohíbe. Es el mismo caso que la instalación
  brownfield ya resuelve así (FR-US1-002, ANA-010): el criterio no puede
  depender de si el archivo llegó al derivado antes o después de instalarse. Al
  lock entra igual, con el hash de lo que entregó el kit, para que nazca como
  conflicto y no como intacta. "No está en el lock" no significa "no está en
  disco": lo que decide es el disco.
- Q: (ANA-044) ¿En qué formato se escribe `.sdd/kit.lock`? → A: JSON, con claves
  ordenadas, indentación fija y una entrada por línea. Tres razones: lo lee y lo
  escribe la biblioteca estándar, sin depender de `pyyaml` —que el propio núcleo
  trata como opcional, con fallback declarado—; nadie lo edita a mano, así que
  lo único que YAML aportaría (comentarios) no vale nada acá; y la escritura
  determinista hace que el diff de una actualización muestre exactamente los
  archivos que cambiaron y que un conflicto de merge quede acotado a esas
  líneas, en vez de a todo el archivo. Es contra ese parser que FR-US3-006 juzga
  "ilegible". Nota de encuadre: el Principio I es sobre no acoplar a proveedores
  ni UI concretas; elegir formato no lo compromete —`AGENTS.md` declara que el
  kit maneja yaml y json por diseño— y el kit ya escribe JSON en el wiring
  (`.claude/settings.json`, `.agents/hooks.json`).

## Acceptance Scenarios

### US1 — registro de la instalación

- **Given** una carpeta vacía, **When** se instala con `sdd-init`, **Then**
  `.sdd/kit.lock` existe y declara la versión real del kit, los valores de
  sustitución usados, un hash por cada `plantilla` instalada que coincide con el
  contenido en disco, y la presencia —sin hash— de cada `semilla`.
- **Given** un derivado recién instalado, **When** se edita un documento de
  plantilla, **Then** el lock deja de coincidir para ese archivo y sigue
  coincidiendo para todos los demás.
- **Given** un proyecto que ya tenía un `AGENTS.md` propio, **When** se instala
  con `sdd-init` (que lo conserva), **Then** el lock registra para ese archivo el
  hash de la versión del kit, de modo que la primera actualización lo trate como
  conflicto y no lo pise.
- **Given** un derivado recién instalado, **When** se lee `.sdd/kit.lock`,
  **Then** es JSON válido para la biblioteca estándar, con claves ordenadas, y
  dos instalaciones equivalentes producen el mismo archivo byte a byte.
- **Given** un derivado con lock, **When** corre `sdd-doctor`, **Then** reporta la
  versión instalada tomada del lock, no del config.
- **Given** un derivado cuyo andamiaje vendorizado declara una versión distinta de
  la del lock, **When** corre `sdd-doctor`, **Then** lo reporta como problema:
  hay una actualización a medio aplicar.

### US2 — actualización

- **Given** un derivado instalado con una versión anterior, **When** se actualiza
  con `--apply`, **Then** `tools/sdd/` queda en la versión nueva, los artefactos
  generados se regeneran y el lock queda reescrito con la versión nueva.
- **Given** un derivado con filas propias en `specs/SPECS_REGISTRY.md`, entradas
  en `historial/sdd.md` y un `.sdd/config.yaml` editado, **When** se actualiza,
  **Then** los tres quedan byte a byte intactos.
- **Given** una plantilla que el dueño editó y que además cambió en el kit nuevo,
  **When** se actualiza, **Then** el archivo no se pisa, se reporta como conflicto
  y la versión del kit queda disponible al lado para comparar.
- **Given** una plantilla intacta que cambió en el kit nuevo, **When** se
  actualiza, **Then** se actualiza sin preguntar.
- **Given** un hook del gate que el catálogo declara ejecutable, **When** se
  actualiza, **Then** queda con permiso de ejecución; su `.kit-new`, si lo hay,
  **no**.
- **Given** un derivado sin `.sdd/kit.lock`, **When** se actualiza, **Then** el
  vendorizado y los generados se actualizan, ninguna plantilla se pisa y al
  terminar queda un lock escrito.
- **Given** un módulo del andamiaje que el kit nuevo ya no trae, **When** se
  actualiza, **Then** se elimina de `tools/sdd/` en vez de quedar como código
  muerto que nadie invoca.
- **Given** un derivado cuya versión instalada es más nueva que la del kit,
  **When** se actualiza, **Then** aborta nombrando ambas versiones, sin escribir.
- **Given** una plantilla que quedó en conflicto y que el dueño no resolvió,
  **When** se actualiza a una versión posterior, **Then** vuelve a reportarse como
  conflicto y sigue sin pisarse.
- **Given** una plantilla que quedó en conflicto y que el dueño resolvió adoptando
  la versión del kit, **When** se actualiza, **Then** se la trata como intacta,
  deja de reportarse y su `.kit-new` se elimina.
- **Given** un derivado cuyo `.sdd/config.yaml` declara un `project.domain`
  distinto del que tenía al instalarse, **When** se actualiza, **Then** las
  plantillas intactas se reescriben con el dominio nuevo y **ninguna** se reporta
  como conflicto por ese motivo.
- **Given** un derivado con `.sdd/current-spec` apuntando a la spec en curso,
  **When** se actualiza, **Then** no se reporta como conflicto ni se lo pisa.
- **Given** una plantilla intacta que el kit nuevo ya no trae, **When** se
  actualiza, **Then** se elimina; **Given** una que el dueño editó, **Then** se
  reporta como conflicto y se conserva.
- **Given** un derivado cuyo `render.py` nuevo falla al regenerar, **When** se
  actualiza con `--apply`, **Then** termina en rojo nombrando que el andamiaje ya
  quedó en la versión nueva, el lock **no** se reescribe, y `sdd-doctor` reporta
  la actualización a medio aplicar.
- **Given** un proyecto con registro de specs e historial propios, **When** se
  corre `sdd-init --force`, **Then** ambos quedan intactos.
- **Given** un derivado con una plantilla editada a mano, **When** se corre
  `sdd-init --force`, **Then** no se pisa: se reporta y la versión del kit queda
  en `.kit-new`, igual que en una actualización; una plantilla intacta sí se pisa.
- **Given** un kit nuevo que trae una plantilla que la versión instalada no tenía,
  **When** se actualiza, **Then** se instala, se reporta como `nuevo` y queda
  registrada en el lock.
- **Given** un kit nuevo que trae una plantilla en una ruta que el lock no
  registra pero donde el dueño ya tiene un archivo propio, **When** se
  actualiza, **Then** no se pisa: se reporta como conflicto, la versión del kit
  queda en `.kit-new` y el lock registra el hash de lo que entregó el kit.
- **Given** un derivado **sin lock** y un kit nuevo que trae una plantilla que ese
  derivado no tiene, **When** se actualiza, **Then** se instala igual: sin archivo
  en disco no hay edición del dueño que preservar.
- **Given** una plantilla que el lock registra y que el dueño borró del disco,
  **When** se actualiza, **Then** se reporta y **no** se reinstala.
- **Given** un derivado sin lock, **When** se corre `sdd-init --force`, **Then**
  ninguna plantilla presente se pisa y la salida explica que sin lock no puede
  distinguir lo editado de lo original.
- **Given** un derivado cuya versión instalada es **igual** a la del kit pero
  cuyo andamiaje difiere en contenido, **When** se actualiza, **Then** los
  cambios se propagan igual: la igualdad de versión no corta la corrida.
- **Given** un derivado **sin lock** que tiene en disco una plantilla que el kit
  nuevo ya no trae, **When** se actualiza, **Then** se reporta y **no** se
  elimina: sin lock no hay con qué afirmar que esté intacta.
- **Given** un derivado con un `.sdd/config.reference.yaml` editado a mano,
  **When** se actualiza, **Then** se reescribe con el del kit nuevo sin
  reportarse como conflicto: es `vendor`.
- **Given** un derivado que ya tenía problemas de `sdd-doctor` antes de
  actualizar, **When** se actualiza con `--apply` y la actualización sale bien,
  **Then** esos problemas se reportan como preexistentes y la corrida **no**
  termina en rojo por ellos.
- **Given** un derivado sano, **When** una actualización introduce un problema
  que `sdd-doctor` detecta, **Then** la corrida termina en rojo nombrándolo.
- **Given** el vendorizado `tools/sdd/core/sdd_update.py` de un derivado,
  **When** se lo invoca, **Then** aborta nombrando que la actualización se corre
  desde un clon del kit, sin escribir nada.

### US3 — el plan

- **Given** un derivado atrasado, **When** se corre sin `--apply`, **Then** el
  árbol queda byte a byte idéntico —incluido el lock— y la salida clasifica cada
  artefacto afectado.
- **Given** el mismo derivado, **When** se corre con `--diff`, **Then** la salida
  muestra el contenido de los cambios, no solo los nombres.
- **Given** un config al que le faltan claves que la referencia nueva trae,
  **When** se corre el plan, **Then** las nombra como avisos y no reescribe el
  config.
- **Given** un derivado cuyo `.gitignore` no ignora `*.kit-new`, **When** se corre
  el plan, **Then** nombra la línea faltante y no toca el archivo.
- **Given** una invocación con un flag desconocido o dos destinos distintos,
  **When** se corre, **Then** aborta con el uso, sin escribir nada.
- **Given** un destino sin andamiaje instalado, o el repo del propio kit,
  **When** se corre, **Then** aborta nombrando el motivo y el comando correcto,
  sin escribir nada.
- **Given** un derivado sin ningún cambio que aplicar —contenido idéntico al que
  entrega el kit—, **When** se corre, **Then** lo dice y no propone nada. El
  veredicto es por contenido, no por versión.
- **Given** un derivado cuyo `.sdd/config.yaml` declara valores de sustitución
  distintos de los que registra el lock, **When** se corre el plan, **Then**
  nombra el cambio como motivo de que se reescriban las plantillas intactas.
- **Given** una invocación con `--diff --apply`, **When** se corre, **Then** se
  aplica y además se muestra el diff: `--diff` no es un modo.
- **Given** un derivado con conflictos de una corrida anterior, **When** se corre
  el plan, **Then** los `.kit-new` presentes aparecen listados.
- **Given** un `.sdd/kit.lock` ilegible (marcadores de conflicto de merge, o sin
  las claves mínimas), **When** se corre —con o sin `--apply`—, **Then** aborta
  nombrando el archivo y el problema, sin escribir nada y sin degradar a "sin
  lock", y ofrece borrarlo para correr en modo degradado.
- **Given** un `.sdd/config.yaml` que no parsea, **When** se corre, **Then**
  aborta nombrando el archivo y el error del parser, antes de tocar nada.

### US4 — qué trae la versión nueva

- **Given** un `CHANGELOG.md` con entradas para varias versiones, **When** se
  corre el plan sobre un derivado atrasado, **Then** cita las entradas
  estrictamente posteriores a la instalada y hasta la del kit.
- **Given** un derivado sin lock, **When** se corre el plan, **Then** declara que
  la versión instalada se desconoce, cita el changelog completo y no aborta por
  versión.
- **Given** un derivado cuya versión instalada no figura en el `CHANGELOG.md` del
  kit, **When** se corre el plan, **Then** cita el changelog completo y dice por
  qué, sin abortar.
- **Given** el kit, **When** corre su suite, **Then** falla si `KIT_VERSION` no
  tiene entrada en `CHANGELOG.md`.
- **Given** una entrada del changelog marcada como que exige acción del dueño,
  **When** se corre el plan sobre un derivado atrasado que la alcanza, **Then**
  la destaca antes de escribir, separada de las demás.
- **Given** el kit, **When** se lee su `README.md`, **Then** la ruta de
  actualización está nombrada donde hoy se afirma que el kit es desechable.
- **Given** el kit y un derivado recién instalado, **When** se leen sus
  `00-INDEX.md`, **Then** `CHANGELOG.md`, el catálogo de clases de propiedad y
  `.sdd/kit.lock` figuran en el mapa de SSOTs.

## Functional Requirements

### US1 — registro

- **FR-US1-001** MUST: el kit declara su versión en la constante `KIT_VERSION` de
  `core/sdd_config.py`, que **viaja con el andamiaje vendorizado** (bajo
  `{{sdd.core}}` en el derivado), de modo que un derivado pueda afirmar qué
  versión tiene sin el clon del kit al lado. Es el mismo hogar que las demás
  constantes del núcleo que otros módulos consultan, y el único lugar de donde
  `sdd-doctor` la lee. Nace en `0.1.0` —el valor que el config viene declarando,
  así que ningún derivado existente queda describiendo una versión que nunca
  hubo— y es **independiente de `constitution.version`**: son dos líneas de
  versionado distintas que conviven en el repo, una del andamiaje y otra de los
  principios, y atarlas obligaría a bumpear una cada vez que cambia la otra.
- **FR-US1-002** MUST: `sdd-init` escribe `.sdd/kit.lock` con la versión
  instalada y el `sha256` del contenido que **entregó el kit** para cada
  artefacto `plantilla` —después de resolver placeholders—, de modo que el hash
  sea comparable contra el disco sin volver a renderizar. De las `semilla` se
  registra la **presencia**, no el hash: nunca se actualizan, así que nadie
  compararía ese hash, y el de `.sdd/current-spec` nacería desactualizado —cambia
  con cada commit— viajando versionado sin significar nada. Lo que sí necesita
  saberse de una `semilla` es si ya se entregó alguna vez (FR-US2-012). Registra
  además los valores de sustitución usados (FR-US2-010), que **consume el plan**:
  cuando difieren de los del config actual son la única explicación de por qué
  una corrida reescribe toda plantilla con placeholder sin que ninguna esté en
  conflicto. Cuando el
  instalador **conserva** un archivo preexistente del proyecto (instalación
  brownfield), el lock registra igual el hash de la versión del kit, no el del
  archivo en disco: registrar el del dueño lo daría por intacto y la primera
  actualización lo pisaría en silencio (mismo criterio que FR-US2-008). El
  algoritmo se declara dentro del propio lock: cambiarlo algún día tiene que ser
  legible en el archivo, no una ruptura silenciosa. El formato es **JSON**, con
  claves ordenadas, indentación fija y una entrada por línea, y es contra ese
  parser que FR-US3-006 juzga si el lock es legible: lo maneja la biblioteca
  estándar sin depender de `pyyaml` —opcional en el núcleo, con fallback
  declarado—, nadie lo edita a mano, así que lo único que YAML aportaría son
  comentarios que no tendría, y la escritura determinista hace que el diff de
  una actualización muestre sólo los archivos que cambiaron y que un conflicto
  de merge quede acotado a esas líneas.
- **FR-US1-003** MUST: `.sdd/kit.lock` se versiona en el repositorio del derivado.
  Es registro compartido del proyecto, no estado de sesión local: la distinción
  con `.sdd/current-spec` ([[SPEC-004-enforcement-hardening]] FR-008) es que el
  lock describe una instalación que todos los que clonan comparten.
- **FR-US1-004** MUST: la clave `project.kit_version` se elimina del catálogo de
  claves, del config sembrado y del `.sdd/config.yaml` del propio kit, que
  dogfoodea su andamiaje ([[SPEC-002-dogfooding-integro]]). Su valor era una
  constante copiada del ejemplo, y conservarla junto al lock sería un segundo
  SSOT de la misma verdad.
- **FR-US1-005** MUST: `sdd-doctor` reporta la versión instalada leyéndola del
  lock, y reporta como problema que la versión del lock no coincida con la del
  andamiaje vendorizado (actualización a medio aplicar). Un lock ausente es nota,
  no problema: los derivados anteriores a esta spec son válidos. Un lock
  **ilegible** sí es problema, y se distingue del ausente al nombrarlo: un archivo
  versionado que no parsea suele ser un conflicto de merge sin resolver.

### US2 — actualización

- **FR-US2-001** MUST: el catálogo de artefactos que el kit instala declara, por
  entrada, su **clase de propiedad**, y es SSOT único compartido por la
  instalación y la actualización. Las clases son: `vendor` (del kit),
  `generado` (derivado del config), `plantilla` (del kit, adoptable por el
  dueño), `semilla` (se crea si falta y nunca se actualiza) y `dueño` (jamás se
  toca). Duplicar el catálogo en dos listas sería R-1/C-8 de `docs/IDEAS.md` sobre
  cuarenta archivos. Los artefactos `generado` **no se enumeran** en el catálogo:
  su SSOT son `render.py` y `gen_skill_adapters.py`, que ya declaran cuáles son;
  la clase existe para nombrar cómo se los trata, no para listarlos otra vez.
- **FR-US2-002** MUST: la clase se asigna archivo por archivo, no por grupo.
  `specs/SPECS_REGISTRY.md`, `historial/sdd.md`, `.sdd/config.yaml`,
  `.sdd/current-spec` y `.gitignore` son `semilla`: la actualización no los
  modifica bajo ninguna bandera. `.gitignore` lleva una **excepción declarada**:
  la instalación le agrega la línea que garantiza [[SPEC-004-enforcement-hardening]]
  FR-009 (`.sdd/current-spec`) cuando falta, porque sin ella el gate queda
  neutralizado en silencio; la actualización no hereda esa licencia y se limita a
  nombrar lo que falta (FR-US3-004). El resto del wiring (`.gitattributes`,
  `.agents/hooks.json`, los hooks del gate) es `plantilla`, con la política de
  conflicto de FR-US2-005. `.sdd/config.reference.yaml` es `vendor` pese a vivir
  fuera de `tools/sdd/`: es el catálogo de claves del kit y
  [[SPEC-013-proyecto-derivado-coherente]] FR-008 ya manda reescribirlo siempre;
  como `plantilla` una edición lo congelaría en conflicto y como `semilla`
  quedaría viejo, y en ambos casos FR-US3-004 compararía el config del dueño
  contra una referencia de una versión anterior. La clase declara autoridad, no
  ubicación.
- **FR-US2-003** MUST: el árbol `vendor` se **purga y se recrea** con el del kit
  nuevo, con o sin lock: es del kit por completo, así que la eliminación de lo
  obsoleto no requiere saber qué había antes ni admite heurística. Si el kit nuevo
  no trae el adaptador del lenguaje que el derivado declara, se aborta nombrándolo
  en vez de dejarlo sin adaptador.
- **FR-US2-004** MUST: los artefactos `generado` se regeneran **después** de
  actualizar el `vendor`, invocando `render.py` y `gen_skill_adapters.py` **ya
  copiados en el destino**, con la raíz del derivado como directorio de trabajo:
  son los que resuelven las rutas y los placeholders del derivado, y ejecutarlos
  ahí es además la primera prueba de que el andamiaje nuevo funciona en ese
  proyecto. No se reimplementa su criterio.
- **FR-US2-005** MUST: una `plantilla` cuyo hash coincide con el lock se actualiza
  sin intervención; una cuyo hash difiere **no se pisa nunca**: se reporta como
  conflicto y la versión nueva queda escrita en `<archivo>.kit-new` —sufijo al
  final, para no alterar la extensión del original— sobrescribiendo la de corridas
  anteriores. Una `plantilla` que el lock registra y que **no está en disco** se
  trata como una edición más —el dueño la borró a propósito—: se reporta y no se
  reinstala, porque deshacer esa decisión en silencio es el mismo daño que esta
  spec impide en la otra dirección. **Al aplicar**, el `.kit-new` se elimina en
  cuanto el archivo vuelve a coincidir con el lock: el conflicto se resolvió y el
  testigo sobra; el plan sin `--apply` lo lista como resuelto y no lo toca
  (FR-US3-001). El `.gitignore` plantilla del kit ignora `*.kit-new`, para que un
  derivado nuevo no los versione sin querer. A todo artefacto escrito que el
  catálogo declara ejecutable se le aplica el bit de ejecución, con el mismo SSOT
  que usa la instalación: un hook sin `+x` deja el gate mudo en silencio. El
  `.kit-new` nunca lo lleva —es un testigo para comparar, no algo para ejecutar—.
  El hash cubre bytes y no permisos, así que un `chmod` del dueño no cuenta como
  edición ni genera conflicto, y sobre una plantilla intacta se pierde al
  actualizar: el kit no puede distinguir un cambio de modo deliberado de uno
  accidental, y el modo que hace funcionar al gate es el suyo.
- **FR-US2-006** MUST: sin lock, toda `plantilla` **presente en disco** se trata
  como conflicto y ninguna se pisa **ni se elimina** —tampoco las que el kit
  nuevo ya no trae (FR-US2-012): eliminar exige poder afirmar que están intactas,
  y sin lock no se puede—; una ausente se instala como alta (FR-US2-012), porque
  no hay edición del dueño que perder. `vendor` y `generado` se actualizan
  igual, y al terminar queda un lock escrito. Sin lock tampoco hay versión
  instalada conocida: FR-US2-007 no aplica y el plan lo declara en vez de
  suponerla.
- **FR-US2-007** MUST: la actualización aborta sin escribir si la versión
  instalada es posterior a la del kit, nombrando ambas.
- **FR-US2-014** MUST: la versión **no** decide si hay trabajo que hacer. Lo que
  hay para aplicar lo determina la comparación de contenido —lock contra disco
  contra lo que entrega el kit—, así que un derivado cuya versión instalada
  coincide con la del kit se actualiza igual si el andamiaje difiere, y uno sin
  ninguna diferencia de contenido lo dice y no propone nada aunque las versiones
  no coincidan. El kit se desarrolla en `main` y `KIT_VERSION` sólo se bumpea al
  publicar: cortar por igualdad de versión dejaría inerte a esta capacidad en su
  caso más frecuente —un derivado instalado desde el clon local y actualizado
  desde ese mismo clon más tarde—. La versión sirve para citar el changelog
  (FR-US4-002) y para el aborto de FR-US2-007, y para nada más.
- **FR-US2-008** MUST: al aplicar, se reescribe el lock con la versión nueva y,
  por archivo, el hash de **lo que el kit entregó en esa corrida** —no el del
  contenido que quedó en disco—. La distinción decide el caso del conflicto:
  registrar el archivo del dueño lo daría por intacto en la actualización
  siguiente y se pisaría en silencio, que es el daño que esta spec impide. El lock
  es la línea base del kit, no una foto del disco.
- **FR-US2-009** MUST: `sdd-doctor` se corre sobre el derivado **antes de
  escribir y al terminar de aplicar**, y lo que decide el resultado de la
  corrida es el **delta**: un problema que ya estaba se reporta como
  preexistente y no la pone en rojo; uno que aparece recién en la corrida final
  sí, porque lo introdujo la actualización. Sin la línea base previa, la deuda
  del dueño —wiring, `.gitignore`, tests sin ejecutor, relaciones sin cerrar—
  haría fallar toda actualización correcta y el operador no podría distinguir
  "falló la actualización" de "mi proyecto ya estaba así". El estado resultante
  queda igual afirmado y no supuesto. La corrida final va **después** del lock
  ya sellado —parte de lo que verifica
  es que el lock coincida con el `KIT_VERSION` vendorizado (FR-US1-005)—, y su
  siembra de `.sdd/current-spec` es escritura esperada: es verificación posterior,
  no un paso de la aplicación que ordena FR-US2-011.
- **FR-US2-010** MUST: los placeholders se resuelven con los valores que declara
  el `.sdd/config.yaml` del destino (`project.name`, `project.domain`) y con el
  mismo helper que usa la instalación —no una copia—, y el lock registra los
  valores usados. Que el dueño cambie su dominio reescribe las plantillas
  intactas, pero **no** las convierte en conflicto: lo que decide "intacta" es la
  comparación contra el lock, nunca contra el kit nuevo.
- **FR-US2-011** MUST: el lock es lo último que se escribe de la **aplicación**, y
  sólo si todo lo anterior salió bien (la corrida final de `sdd-doctor`
  (FR-US2-009) viene después, y necesita el lock ya sellado; la previa es
  anterior a toda escritura). Si la regeneración falla con el `vendor` ya recreado, la
  corrida aborta en rojo nombrando que el andamiaje quedó en la versión nueva y
  qué reintentar; el lock viejo contra el `KIT_VERSION` nuevo es lo que hace
  detectable ese estado (FR-US1-005). No hay rollback: preservar el `vendor`
  anterior exigiría copiarlo entero, y el operador prudente commitea antes.
- **FR-US2-012** MUST: las altas y bajas del catálogo se propagan. Una
  `plantilla` o `semilla` que el kit nuevo trae y el lock no tiene se instala de
  cero **si la ruta está libre**, se reporta como `nuevo` y entra al lock —la
  `semilla`, sólo si falta—: sin esto la actualización sabría propagar cambios
  sobre lo instalado pero no las capacidades nuevas del andamiaje. Si esa ruta
  ya está ocupada por un archivo del dueño, no es alta sino **conflicto**: no se
  pisa, la versión del kit queda en `.kit-new` y al lock entra igual el hash de
  lo que el kit entregó, para que nazca como conflicto y no como intacta. Es el
  mismo criterio que la instalación brownfield (FR-US1-002): no puede depender
  de si el archivo llegó al derivado antes o después de instalarse, y pisarlo
  por venir de un catálogo nuevo perdería en silencio lo que SC-002 protege. Una `plantilla` que el kit nuevo ya no trae se
  elimina si coincide con el lock, y se reporta como conflicto —conservándola— si
  difiere; con ella se van sus artefactos `generado` derivados (el adaptador de un
  `SKILL.md` retirado). `semilla` y `dueño` no se eliminan nunca.
- **FR-US2-013** MUST: `sdd-init --force` respeta el mismo catálogo de clases
  (FR-US2-001): no toca `semilla` ni `dueño` —deja de borrar
  `specs/SPECS_REGISTRY.md` e `historial/sdd.md`— y aplica a `plantilla` la misma
  política de conflictos que la actualización (FR-US2-005): pisa las intactas, y
  las que difieren del lock las reporta dejando la versión del kit en `.kit-new`.
  Lo que `--force` fuerza es la reinstalación, no la destrucción de lo que el
  dueño escribió; cualquier otra lectura haría falso a SC-002 en el comando de
  menos supervisión. Sin lock —todo derivado anterior a esta spec, y toda
  instalación brownfield— rige el mismo criterio degradado que FR-US2-006: no se
  pisa ninguna plantilla presente, y la salida **lo dice**, porque un `--force`
  que parece no hacer nada es peor que uno que explica por qué. En consecuencia,
  el aviso de wiring conservado deja de
  ofrecer `--force` como "pisa tu versión" y nombra el `.kit-new` que queda al
  lado ([[SPEC-014-derivado-dice-la-verdad]] FR-US1-001 sigue vigente: cambia el
  remedio que recomienda, no el aviso).

### US3 — el plan

- **FR-US3-001** MUST: sin `--apply` no se escribe **ningún** byte en el destino,
  incluido el lock.
- **FR-US3-002** MUST: el plan clasifica cada artefacto afectado en un vocabulario
  cerrado —sin cambios / actualizar / regenerar / conflicto / nuevo / eliminado—
  y resume el conteo por categoría. Los `.kit-new` presentes de corridas
  anteriores se listan: son conflictos sin resolver a la vista del operador. Si
  los valores de sustitución del lock difieren de los del config actual, el plan
  lo nombra: es lo que explica que se reescriban plantillas intactas sin que
  ninguna esté en conflicto (FR-US2-010).
- **FR-US3-003** MUST: con `--diff` la salida muestra el diff unificado de cada
  cambio, producido con la biblioteca estándar: la promesa "solo Python + pyyaml"
  del README no admite una dependencia nueva para esto. `--diff` es modificador
  de salida y no un modo: es válido con `--apply` y sin él, porque bajo el
  parseo estricto de FR-US3-005 dejarlo sin declarar se pagaría con un aborto
  que nadie decidió.
- **FR-US3-004** MUST: el plan nombra lo que los artefactos `semilla` del derivado
  no tienen y la versión nueva del kit sí trae, **sin reescribirlos**: las claves
  del `config.reference.yaml` ausentes en el `.sdd/config.yaml` del dueño, y las
  líneas del `.gitignore` plantilla ausentes en el suyo —empezando por
  `*.kit-new`, sin la cual un derivado anterior versionaría sus conflictos sin
  enterarse—. Es el mismo criterio para los dos: nombrar sin tocar es lo único
  compatible con que sean del dueño.
- **FR-US3-005** MUST: el parseo de argumentos es estricto y aborta antes de
  escribir ante cualquier flag desconocido o destino ambiguo, con la misma
  política que [[SPEC-003-install-happy-path]] FR-012. Aborta igual, nombrando el
  motivo y el comando correcto, si el destino no tiene andamiaje instalado
  —actualizar no es instalar— o si es el repo del propio kit, donde purgar el
  vendorizado no significa nada.
- **FR-US3-006** MUST: las entradas que el mecanismo necesita leer se validan
  antes de escribir, y si no se pueden interpretar la corrida aborta nombrando el
  archivo y el error, sin tocar nada. Son dos: un `.sdd/kit.lock` ilegible —que
  **no** degrada a "sin lock": el lock se versiona, así que un archivo roto suele
  ser un conflicto de merge sin resolver, y descartarlo por el operador le haría
  perder la línea base en silencio; la salida ofrece borrarlo para correr en modo
  degradado— y un `.sdd/config.yaml` inparseable, que hace imposible resolver los
  placeholders (FR-US2-010). Vale igual para el plan, que resuelve los mismos
  placeholders sin escribir.

### US4 — qué trae la versión nueva

- **FR-US4-001** MUST: el kit mantiene un `CHANGELOG.md` con una entrada por
  versión publicada, y un unitario —que el paso `tests` corre como cualquier
  otro— falla si la `KIT_VERSION` vigente no tiene la suya. El invariante se
  enuncia sobre la versión vigente y no sobre el bump: un test no ve la versión
  anterior, así que "bumpear sin entrada" no sería verificable. Cada entrada
  declara además, de forma legible por el plan, qué cambios **exigen acción del
  dueño**: el kit no migra su contenido (registro de specs, historial, specs),
  pero el andamiaje nuevo sí lo juzga con reglas nuevas —SPEC-023 hizo
  obligatoria la sección de relaciones, SPEC-024 exige el FR como token en el
  test—, y sin ese aviso el pipeline del derivado se rompe en la corrida
  siguiente sin mencionar la actualización.
- **FR-US4-002** MUST: el plan cita las entradas del changelog estrictamente
  posteriores a la versión instalada y hasta la del kit inclusive, y **destaca
  aparte** las que exigen acción del dueño (FR-US4-001), antes de escribir nada.
  Sin versión instalada conocida —derivado sin lock, o versión que el changelog
  no registra— cita el changelog completo y declara el motivo: un historial
  incompleto no puede convertirse ni en un bloqueo ni en una lista que miente
  sobre qué se gana.
- **FR-US4-003** MUST: el comando vive en `core/sdd_update.py`, con la CLI
  simétrica a `sdd-init` —destino posicional o `--target`, más `--apply` y
  `--diff`—, y su skill y su playbook viven en el kit y **no** se instalan en el
  derivado: operan sobre el clon del kit, que el derivado no tiene. El módulo sí
  viaja vendorizado, porque `_vendor_kit` copia `core/` entero y excluir un
  archivo sería otra lista que mantener; para que eso no prometa lo que no puede
  cumplir, aborta sin escribir si su propio origen no es un clon del kit (sin
  `templates/`), que es exactamente el caso de la copia vendorizada.
- **FR-US4-004** MUST: el `README.md` del kit nombra la ruta de actualización
  donde afirma que el kit es desechable, `templates/docs/SDD-OPERACION.md`
  explica qué esperar del lado del derivado —incluido que la actualización se
  corre desde el kit—, y los mapas de SSOTs (`00-INDEX.md` del kit y su
  plantilla) registran los tres que esta spec crea: `CHANGELOG.md`, el catálogo
  de clases de propiedad y `.sdd/kit.lock`. Un SSOT fuera del mapa contradice el
  Principio IV en el documento que existe para hacerlo cumplir.

## Key Entities

- **`KIT_VERSION`** — constante de `core/sdd_config.py`; viaja vendorizada
  (FR-US1-001).
- **`.sdd/kit.lock`** — manifiesto de la instalación, en JSON determinista
  (FR-US1-002): versión, algoritmo, valores
  de sustitución usados, `sha256` por `plantilla` **tal como la entregó el kit**
  (línea base, no foto del disco) y la presencia de cada `semilla` entregada.
  Versionado, escrito por `sdd-init` y reescrito por `sdd-update` al final de una
  corrida exitosa.
- **Clase de propiedad** — `vendor` / `generado` / `plantilla` / `semilla` /
  `dueño`: qué autoridad tiene el kit sobre cada archivo que instaló.
- **Conflicto** — archivo `plantilla` cuyo contenido en disco no coincide con el
  lock. No se resuelve automáticamente: se reporta y se deja la versión nueva
  en `<archivo>.kit-new`, que se borra cuando el archivo vuelve a coincidir.
- **Plan de actualización** — clasificación por artefacto, previa a toda
  escritura.
- **`CHANGELOG.md`** — qué cambió por versión, en términos de capacidades, y qué
  de eso exige acción del dueño (FR-US4-001).
- **`sdd-update`** — `core/sdd_update.py`: el comando, con CLI simétrica a
  `sdd-init`. Corre desde un clon del kit apuntando al derivado.

## Success Criteria

- **SC-001** Un derivado instalado con una versión anterior recibe los arreglos
  del andamiaje con un solo comando, y su `specs/SPECS_REGISTRY.md`,
  `historial/sdd.md` y `.sdd/config.yaml` quedan intactos.
- **SC-002** Ningún cambio de **contenido** del dueño sobre un archivo instalado
  se pierde sin que el operador lo haya visto reportado antes como conflicto —
  por ninguna de las dos rutas del kit, ni `sdd-update` ni `sdd-init --force`.
  Única excepción, declarada en FR-US2-005: el bit de ejecución, que el hash no
  cubre y que se reaplica con el modo del kit.
- **SC-003** Correr la actualización sin `--apply` deja el destino byte a byte
  idéntico.
- **SC-004** `sdd-doctor` sobre cualquier derivado nombra su versión de andamiaje,
  y detecta una actualización aplicada a medias.
- **SC-005** Un derivado instalado **antes** de esta spec (sin lock) se puede
  actualizar sin perder nada y queda con lock para la vez siguiente.
- **SC-006** La afirmación "el kit es desechable, salvo para actualizar" del
  README deja de apuntar a un mecanismo inexistente.
- **SC-007** El escenario e2e de la actualización corre en el pipeline como un
  escenario más de `tests/e2e/` ([[SPEC-018-verificacion-e2e]] FR-US1-007): esta
  capacidad no se puede afirmar con unitarios solos, porque su objeto es un
  proyecto instalado que envejeció.

## Assumptions

- Quien actualiza tiene un clon del kit en la versión que quiere instalar. Cómo
  obtiene ese clon es distribución (E-3), no esta spec.
- El derivado puede no ser un repositorio git; el mecanismo no depende de git,
  aunque el operador prudente commitee antes de aplicar.
- La versión del kit sigue semver, con el mismo criterio que la constitución ya
  documenta para sus enmiendas.
- Un archivo `plantilla` intacto se puede pisar sin consultar: el dueño que nunca
  lo tocó no tiene expectativa sobre su contenido.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-US1-001 | tests/unit/test_kit_version.py |
| FR-US1-002 | tests/unit/test_kit_lock.py |
| FR-US1-003 | tests/unit/test_kit_lock.py |
| FR-US1-004 | tests/unit/test_kit_version.py |
| FR-US1-005 | tests/unit/test_sdd_doctor_version.py |
| FR-US2-001 | tests/unit/test_catalogo_artefactos.py |
| FR-US2-002 | tests/unit/test_catalogo_artefactos.py |
| FR-US2-003 | tests/unit/test_sdd_update_vendor.py |
| FR-US2-004 | tests/unit/test_sdd_update_vendor.py |
| FR-US2-005 | tests/unit/test_sdd_update_plantillas.py |
| FR-US2-006 | tests/unit/test_sdd_update_plantillas.py |
| FR-US2-007 | tests/unit/test_sdd_update.py |
| FR-US2-008 | tests/unit/test_kit_lock.py, tests/unit/test_sdd_update_plantillas.py |
| FR-US2-009 | tests/unit/test_sdd_update_doctor.py, tests/e2e/escenarios/test_actualizacion_kit.py |
| FR-US2-010 | tests/unit/test_sdd_update.py |
| FR-US2-011 | tests/unit/test_sdd_update_vendor.py |
| FR-US2-012 | tests/unit/test_sdd_update_plantillas.py |
| FR-US2-013 | tests/unit/test_sdd_init_force_propiedad.py |
| FR-US2-014 | tests/unit/test_sdd_update.py |
| FR-US3-001 | tests/unit/test_sdd_update_plan.py |
| FR-US3-002 | tests/unit/test_sdd_update_plan.py |
| FR-US3-003 | tests/unit/test_sdd_update_plan.py |
| FR-US3-004 | tests/unit/test_sdd_update_plan.py |
| FR-US3-005 | tests/unit/test_sdd_update_plan.py |
| FR-US3-006 | tests/unit/test_sdd_update_plan.py |
| FR-US4-001 | tests/unit/test_changelog.py |
| FR-US4-002 | tests/unit/test_sdd_update_plan.py |
| FR-US4-003 | tests/unit/test_skills_instaladas.py, tests/unit/test_sdd_update.py |
| FR-US4-004 | tests/unit/test_docs_actualizacion.py |

## Fuera de alcance

- **Distribución del kit** (publicarlo, descargarlo, `pip install`): es E-3 de
  `docs/IDEAS.md`. Acá el kit nuevo ya está en disco.
- **Merge automático de conflictos.** Se reportan y se deja la versión nueva al
  lado; fusionar es del dueño, que es el único que sabe por qué adaptó el archivo.
- **Reescribir `.sdd/config.yaml`** para incorporar claves nuevas: destruye
  comentarios en el archivo más editado del derivado.
- **Migrar contenido del dueño** (specs, historial, código) entre versiones del
  formato. Si algún día un cambio lo exigiera, es capacidad propia.
- **Actualizar el kit desde el derivado sin clon del kit.** Depende de
  distribución.
- **Salida UTF-8 del entrypoint nuevo**: ya lo garantiza
  [[SPEC-012-suite-multiplataforma]] FR-005, cuyo barrido falla nombrando al
  entrypoint que se olvide del helper. Reenunciarlo acá sería un segundo SSOT del
  mismo criterio.

## Historial

- 2026-08-12: creada (draft). Promueve E-2 de `docs/IDEAS.md`, abierto desde la
  primera revisión crítica (2026-07-02) y confirmado en la campaña de usabilidad
  del derivado (2026-08-05). El análisis previo encontró dos cosas que E-2 no
  registraba: `project.kit_version` es una constante copiada del ejemplo —así que
  no hay nada que comparar—, y `sdd-init --force`, la ruta de actualización
  "manual" que E-2 daba por existente, borra `specs/SPECS_REGISTRY.md` y
  `historial/sdd.md`.
- 2026-08-12: `analyze` (6 hallazgos, todos aceptados). El de más peso no era
  subespecificación sino un defecto de diseño: como estaba escrito, FR-US2-008
  registraba en el lock el contenido **del disco**, lo que habría dado por intacta
  la plantilla en conflicto y la habría pisado en silencio en la actualización
  siguiente. El lock pasa a ser línea base de lo que entregó el kit. Quedan además
  fijados: purga y recreación del `vendor` (en vez de una heurística de obsoletos
  imposible sin lock), regeneración con los scripts ya copiados en el destino,
  `KIT_VERSION` en `core/sdd_config.py`, sufijo `.kit-new` y `sha256` declarado en
  el propio lock. Se agrega FR-US2-009 (`sdd-doctor` al cerrar), que estaba fundido
  con FR-US2-008.
- 2026-08-12: `analyze` 2 (14 hallazgos, todos corregidos). Los cuatro de más peso
  eran del mismo eje —el borde entre instalar y actualizar— y hacían que el lock
  naciera mintiendo o se volviera ruido: en instalación brownfield registraba como
  línea base el archivo del dueño (el bug de ANA-001 en el otro extremo, ahora
  cerrado en FR-US1-002); no declaraba con qué valores se resuelven los
  placeholders, con lo que un derivado ya configurado habría reportado conflicto en
  **toda** plantilla (FR-US2-010); no decía qué pasa si la regeneración falla con
  el `vendor` ya recreado (FR-US2-011); y `.sdd/current-spec`, que se reescribe en
  cada commit, quedaba como `plantilla` y habría dado conflicto en toda corrida de
  todo derivado vivo (FR-US2-002). Se agregan además FR-US2-012 (plantilla
  retirada) y FR-US2-013: `sdd-init --force` deja de borrar el registro y el
  historial, porque cerrar la ruta nueva y dejar abierta la destructiva que el
  README todavía nombra hacía falso a SC-002. Precisiones menores: los `generado`
  no se enumeran en el catálogo ni entran al lock (su SSOT son los regeneradores),
  ciclo de vida de los `.kit-new`, destinos que la actualización rechaza, modo
  degradado sin versión conocida, el changelog verificado sobre la versión vigente
  y no sobre el bump, y `project.kit_version` fuera también del config del propio
  kit. Nota de secuencia: los 11 archivos del Coverage mapping tienen que existir
  antes de pasar la spec a `active`, o el paso `traceability` rompe.
- 2026-08-12: `analyze` 3 (4 hallazgos, todos corregidos). FR-US2-013 cerraba el
  agujero de `--force` sobre `semilla`/`dueño` pero callaba sobre `plantilla`, con
  lo que SC-002 seguía siendo falso justo en el comando de menos supervisión:
  ahora `--force` aplica la política de conflictos de FR-US2-005 —pisa las
  intactas, deja `.kit-new` para las editadas—, y en consecuencia el aviso de
  wiring conservado deja de recomendarlo como "pisa tu versión". FR-US2-012 pasa
  de cubrir sólo las bajas del catálogo a cubrir también las **altas**: sin eso la
  actualización propagaba cambios sobre lo instalado pero no las capacidades
  nuevas del andamiaje. Y se fija el orden del cierre —`sdd-doctor` corre después
  del lock sellado, porque parte de lo que verifica es la coincidencia
  lock↔vendorizado— y el fallback del changelog cuando la versión instalada no
  figura en él.
- 2026-08-12: `analyze` 4 (10 hallazgos, todos corregidos). Deuda de las
  correcciones anteriores, concentrada en el **modo degradado**: "sin lock, toda
  plantilla es conflicto" (FR-US2-006) se había escrito pensando en archivos que
  existen, y desde que FR-US2-012 agregó las altas y FR-US2-013 metió a `--force`
  en el mismo régimen, esa regla absoluta dejaba a los derivados sin lock —el caso
  de SC-005— sin recibir ninguna capacidad nueva y con `--force` convertido en un
  no-op mudo. Ahora la regla distingue presente de ausente, y `--force` sin lock
  explica por qué no pisa. Se declara además la relación que las dos pasadas
  previas habían creado sin registrar (`Extiende: SPEC-003, SPEC-014`), se acota
  el lock a hashear `plantilla` y registrar sólo la presencia de las `semilla`
  —el hash de una semilla no lo consulta nadie, y el de `.sdd/current-spec` nacía
  desactualizado—, se resuelve la clase de `.gitignore` con su excepción de
  SPEC-004 FR-009, y el aviso de las líneas faltantes del `.gitignore` —prometido
  en ANA-013 y sin requisito— pasa a FR-US3-004. Menores: la plantilla borrada por
  el dueño no se reinstala, el borrado del `.kit-new` se acota a `--apply`,
  `KIT_VERSION` nace en `0.1.0` e independiente de `constitution.version`, y
  FR-US2-009 suma unitario al mapeo porque el e2e no puede afirmar el orden
  respecto del lock.
- 2026-08-12: `analyze` 5 (3 hallazgos, todos corregidos). Faltaba declarar qué
  pasa cuando lo que el mecanismo **lee** está roto, que es lo primero que ocurre
  en la vida real de un archivo versionado: se agrega FR-US3-006 y un lock
  ilegible **no** degrada a "sin lock" —viene versionado, así que lo más probable
  es un conflicto de merge sin resolver, y descartarlo por el operador le haría
  perder la línea base en silencio— sino que aborta ofreciendo esa salida
  explícita; lo mismo para un `.sdd/config.yaml` inparseable, sin el cual no hay
  cómo resolver los placeholders. `sdd-doctor` distingue lock ausente (nota) de
  lock ilegible (problema). Y FR-US2-005 declara el bit de ejecución: se reaplica
  a los artefactos que el catálogo declara ejecutables —un hook sin `+x` deja el
  gate mudo—, nunca al `.kit-new`, y se acepta por escrito que el hash cubre
  bytes y no permisos, así que un `chmod` del dueño no es conflicto y se pierde
  sobre una plantilla intacta.
- 2026-08-12: `analyze` 6 (11 hallazgos, todos corregidos). Las cinco pasadas
  anteriores habían mirado el mecanismo desde el archivo; ésta lo mira desde el
  uso real del kit, y ahí aparecieron los dos de peso. **La versión no es el
  veredicto** (FR-US2-014): como estaba, un derivado "ya en la versión del kit"
  no recibía nada, y como `KIT_VERSION` sólo se bumpea al publicar mientras el
  kit se desarrolla en `main`, la capacidad quedaba inerte justo en su caso más
  frecuente —instalar desde el clon local y actualizar desde ese mismo clon—;
  ahora lo que hay para aplicar lo decide la comparación de contenido. Y el
  andamiaje nuevo **juzga con reglas nuevas** contenido del dueño que la
  actualización no toca (SPEC-023 exigió la sección de relaciones, SPEC-024 el FR
  como token en el test): migrar sigue fuera de alcance, pero el changelog ahora
  marca qué exige acción y el plan lo destaca antes de escribir (FR-US4-001/002).
  Se corrigen además: `sdd-doctor` corre antes y después y decide por **delta**,
  para que la deuda preexistente del dueño no ponga en rojo una actualización
  correcta (FR-US2-009); `.sdd/config.reference.yaml` pasa a ser `vendor`, la
  única clase compatible con SPEC-013 FR-008 y con que FR-US3-004 compare contra
  la referencia nueva; se declara el entrypoint `core/sdd_update.py`, su CLI y
  su aborto cuando se lo invoca desde la copia vendorizada; y los tres SSOT que
  la spec crea entran al mapa de `00-INDEX.md` (Principio IV). Menores: sin lock
  tampoco se **eliminan** plantillas retiradas, los valores de sustitución del
  lock ganan consumidor declarado (el plan explica con ellos por qué reescribe
  plantillas intactas), `--diff` se declara válido con `--apply`, y SC-002 se
  acota a cambios de contenido —su redacción absoluta era literalmente falsa
  contra la excepción de permisos que FR-US2-005 ya aceptaba—. El Coverage
  mapping se parte por eje (`_vendor`, `_plantillas`, `_doctor`): nueve FR en un
  solo archivo hacían pasar la traza de SPEC-024 sin verificar nada.
- 2026-08-12: `analyze` 7 (2 hallazgos externos, verificados y corregidos). El
  primero era una pérdida de datos que las seis pasadas anteriores no vieron:
  FR-US2-012 mandaba instalar "de cero" toda alta del catálogo, y aplicado a una
  ruta que el dueño ya ocupaba con un archivo suyo la pisaba en silencio —el
  daño de SC-002, entrando por la puerta de las capacidades nuevas—. Ahora "no
  está en el lock" no alcanza: lo que decide es el disco, y una ruta ocupada es
  conflicto, con el mismo criterio que la instalación brownfield ya aplicaba
  (FR-US1-002). El segundo: el lock se describía por su contenido pero nunca por
  su formato, así que FR-US3-006 hablaba de un archivo "ilegible" sin decir
  contra qué parser; se fija **JSON determinista** —biblioteca estándar, sin
  depender de `pyyaml`, nadie lo edita a mano y el diff de una actualización
  queda acotado a los archivos que cambiaron—.
