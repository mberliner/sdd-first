# Formato y método de redacción de specs

> SSOT del formato de spec. Adaptación del enfoque híbrido estilo GitHub Spec Kit:
> una spec describe un **corte vertical** de capacidad (user story + requisitos
> verificables), no un diseño técnico exhaustivo.

## Secciones obligatorias (formato híbrido)

`{{sdd.core}}/check_traceability.py` exige, en specs `hibrido`:

1. **User Story** con **prioridad** declarada (P1/P2/P3) y un *Independent Test*.
2. **Functional Requirements** con IDs `FR-NNN` (o `FR-USk-NNN` en specs multi-HU).
   Cada FR empieza con la keyword `MUST:` / `SHOULD:` / `MAY:`.
3. **Success Criteria** con IDs `SC-NNN`, binarios y agnósticos de implementación.
4. **Coverage mapping**: tabla `| Requisito | Cubierto por |` que mapea cada
   `FR-NNN` a el/los test(s) que lo verifican. La relación FR↔SC es N:M.
5. **Relación con specs existentes**: los seis campos de enlace que declaran cómo
   se apoya esta spec en las demás (gramática y criterio, abajo).

## Relación con specs existentes

SSOT de la sección. Es obligatoria en toda spec `hibrido` —también en las `draft`—
y `{{sdd.core}}/check_traceability.py` la verifica. Va después de las User
Stories y antes de *Clarifications*.

### Gramática

Seis campos en tres pares simétricos, agrupados en dos líneas más una de prosa:

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

Reglas:

- **Valor:** una o más referencias separadas por coma, en la forma
  `[SPEC-NNN](SPEC-NNN-slug.md)`. Lo que se lee es el `SPEC-NNN`; el enlace es
  para quien navega el documento.
- **Vacío:** el em dash `—`, el en dash `–`, el guion simple `-` o el campo sin
  valor. Las specs se escriben a mano y en consolas que no siempre producen el
  mismo carácter: tratarlos distinto convertiría un detalle tipográfico en una
  violación.
- **Reciprocidad:** cada campo declarado en A exige en B el campo que le
  corresponde según su par. El grafo queda tipado en ambas direcciones, así que
  leyendo solo el lado inverso se distingue si la otra spec extiende, depende o
  reemplaza.
- **Estado:** en una spec `active`, `Extiende:` y `Depende de:` solo pueden
  apuntar a specs `active`: ambos expresan apoyo en algo que tiene que seguir en
  pie. `Supersede:` queda fuera de la restricción —apuntar a una `superseded` es
  el desenlace normal de reemplazarla—, igual que los tres campos inversos.
- **Prosa:** el último campo es texto libre, no un enlace. Lo escribe
  `{{sdd.core}}/sdd_spec.py --new --rationale="<texto>"`.

### Cuándo corresponde cada campo

Saber escribirlos no alcanza: sin criterio, el validador verifica forma sin
significado y cada autor enlaza distinto.

- **`Depende de: B`** — esta spec **no puede entregarse sin B implementada**. De
  ahí que el estado se encadene: una `active` apoyada en una `draft` es una
  promesa a medias.
- **`Extiende: B`** — amplía el alcance de B sin reemplazarla, con B vigente.
- **`Supersede: B`** — la reemplaza. B pasa a `superseded` cuando la nueva pasa a
  `active`, no antes: degradarla al crear dejaría la capacidad sin spec vigente.

Citar un invariante de B, compartir archivos con B o haberse diseñado junto a B
**no es depender**: eso va en prosa. Dos specs hermanas que se referencian pero
que se entregan por separado no se enlazan — hacerlo obligaría a que pasen a
`active` juntas, un encadenamiento sin fundamento técnico.

### Herramientas

- Al crear: `{{sdd.core}}/sdd_spec.py "<slug>" --extends SPEC-NNN` (repetible y
  combinable con `--supersedes`) escribe la relación en **los dos** documentos.
- Después: `{{sdd.core}}/sdd_doctor.py --fix` inyecta la sección en una spec que
  no la tenga y cierra los recíprocos de los enlaces escritos a mano. Es
  repetible, no un paso único de migración.

## Template copiable

El template real vive en un único archivo, `specs/SPEC-TEMPLATE.md` (lo
consume `{{sdd.core}}/sdd_spec.py` al crear una spec nueva). No se embebe una copia
acá para no duplicar el SSOT — abrí ese archivo directamente.

## Ciclo de vida

`draft` → (implementación + tests) → `active` → `superseded`/`archived`. El estado
vive en `SPECS_REGISTRY.md`; la spec es viva y se actualiza si el comportamiento
implementado difiere.
