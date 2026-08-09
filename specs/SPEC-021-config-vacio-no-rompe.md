# SPEC-021-config-vacio-no-rompe: Una clave del config declarada pero vacía no rompe el pipeline

> Origen: bug encontrado el 2026-08-08 al cubrir `check_naming.main()` como parte
> de K-3 (`docs/IDEAS.md`). Es la confirmación de la hipótesis con la que se
> encaró la deuda de cobertura: cubrir un módulo nunca ejecutado destapa defectos,
> no solo sube un número.

## User Story (Priority P1)

Como dueño de un proyecto con SDD instalado, quiero que comentar o vaciar una
lista de `.sdd/config.yaml` degrade el paso correspondiente en vez de reventarlo,
para que un edit razonable del config no me deje el pipeline con un traceback en
lugar de un diagnóstico.

**Why this priority:** `.sdd/config.yaml` es el archivo que el kit invita a
editar a mano, y vaciar una lista es la forma natural de desactivar una regla —
más natural que borrar la clave entera. Hoy, `naming.prohibited:` sin ítems
(YAML lo carga como `None`) hace que el paso `naming` aborte con
`TypeError: 'NoneType' object is not iterable`, tapando el mensaje
"sin palabras excluidas (nada que verificar)" que el propio `check_naming.main`
ya tiene escrito para exactamente ese caso.

**Independent Test:** un config con `naming.prohibited:` (clave presente, sin
ítems) hace que `check_naming.py <root>` salga 0 imprimiendo el aviso de "nada
que verificar", en vez de propagar una excepción.

## Clarifications

### Session 2026-08-08

- Q: ¿es un fix puntual de `naming_prohibited` o de una clase? → A: de la clase,
  pero acotada: son **tres** propiedades (`naming_prohibited`,
  `naming_allowed`, `naming_relax_in_tests`) — las únicas del loader que iteran
  el resultado de un `.get(clave, [])` sin verificar el tipo. `_project`,
  `dirs`, `layers`, `pipeline_steps`, `pipeline_coverage` y `principles` ya
  guardan con `isinstance` o con `or []`.
- Q: ¿vaciar y omitir deben comportarse igual? → A: sí. `prohibited:` vacío y
  `prohibited` ausente expresan lo mismo —no hay palabras excluidas— y el
  consumidor ya trata la tupla vacía como "nada que verificar".
- Q: ¿por qué no validar el config y fallar con un error legible? → A: porque la
  regla ya está declarada en el módulo, en el docstring de `pipeline_coverage`:
  "el config es un SSOT editado a mano y un typo no debe volver ilegible el
  proyecto". Esta spec extiende esa regla ya vigente a las claves que se la
  saltaban; cambiarla por validación estricta sería otra decisión, y más ancha.

## Acceptance Scenarios

- **Given** `naming: {prohibited: }` (clave sin ítems), **When** se lee
  `cfg.naming_prohibited`, **Then** devuelve `()` sin excepción.
- **Given** lo mismo para `allowed_identifiers` y `relax_in_tests`, **When** se
  leen, **Then** devuelven `frozenset()` sin excepción.
- **Given** un config con `naming.prohibited` vacío, **When** corre
  `check_naming.py src`, **Then** sale 0 e imprime el aviso de que no hay nada
  que verificar.
- **Given** un valor de tipo inesperado (`prohibited: acme`, un escalar en vez
  de lista), **When** se lee, **Then** no revienta.

## Functional Requirements

- **FR-001** MUST: `naming_prohibited`, `naming_allowed` y `naming_relax_in_tests`
  de `core/sdd_config.py` devuelven la colección vacía cuando la clave está
  ausente, declarada sin ítems (`None`) o tiene un tipo no iterable como lista.
- **FR-002** MUST: el comportamiento de "clave vacía" es idéntico al de "clave
  ausente" en todos los consumidores del paso `naming`.
- **FR-003** SHOULD: la guarda se expresa una sola vez y no repetida en cada
  propiedad, para que una clave de lista nueva la herede por construcción.

## Key Entities

- **Lista del config** — clave de `.sdd/config.yaml` cuyo valor esperado es una
  secuencia. Ausente, vacía y malformada colapsan al mismo resultado: vacía.

## Success Criteria

- **SC-001** El pipeline no propaga ninguna excepción de tipo por un config con
  listas vacías; los pasos afectados se omiten o se declaran sin trabajo.
- **SC-002** `check_naming.py` sobre un proyecto con `prohibited:` vacío sale 0
  con mensaje, no con traceback.

## Assumptions

- YAML carga una clave sin ítems como `None`; es el caso real que dispara el bug.
- No se persigue validar el config entero: fuera de las listas, el loader ya
  tolera lo que recibe.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_sdd_config.py |
| FR-002 | tests/unit/test_check_naming.py |
| FR-003 | tests/unit/test_sdd_config.py |

## Fuera de alcance

- Validación estricta del config con mensajes de error por clave.
- Las claves que ya guardan el tipo (`dirs`, `layers`, `pipeline.*`,
  `principles`): esta spec no las toca.

## Historial

- 2026-08-08: creada (draft) a partir del bug destapado por la cobertura de K-3.
- 2026-08-08: implementada y promovida a `active` (iteración 5). La guarda quedó
  en un helper único (`_naming_list`), así que una lista nueva del bloque `naming`
  la hereda por construcción (FR-003).
