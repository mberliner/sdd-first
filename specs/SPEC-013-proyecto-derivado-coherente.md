# SPEC-013: Proyecto derivado coherente: principios elegidos y referencias disponibles

> Origen: revisión de la constitución de un derivado el 2026-08-04. Un proyecto
> recién instalado declara principios que su dueño nunca eligió y referencias a
> herramientas que su instalación no incluye.

## User Story (Priority P1)

Como dueño de un proyecto recién derivado del kit, quiero que su
`CONSTITUTION.md` declare únicamente los principios que elegí y que cada
`Enforcement:` y `Detalle:` apunte a algo que mi instalación realmente tiene,
para que la constitución sea un compromiso verdadero y no una lista heredada
que nadie puede cumplir.

**Why this priority:** un principio que el dueño no eligió, o cuyo enforcement
no existe en su instalación, enseña que la constitución es decorativa. Eso
degrada el artefacto central del kit: si el primer contacto con la constitución
es "esto no aplica a mi proyecto", deja de leerse.

**Independent Test:** instalar en un directorio vacío con `--language none` y
con `--language python`; en ambos casos el `CONSTITUTION.md` generado contiene
solo los cuatro principios del núcleo, y ninguna ruta citada en los documentos
instalados apunta a un archivo ausente.

## Clarifications

### Session 2026-08-04

- Q: ¿Qué principios se siembran? → A: solo el núcleo mínimo obligatorio
  (I..IV: nomenclatura, capas, trazabilidad, gate). Los opcionales quedan
  comentados en el config y **se preguntan al iniciar el derivado**: es lo que
  el playbook de `sdd-configure` ya manda hacer ("partí del núcleo mínimo y
  preguntá qué principios opcionales agregar"), contradicho hasta ahora por un
  sembrado que los traía puestos.
- Q: ¿Se borran del config de ejemplo? → A: no. `examples/config/config.yaml`
  es el catálogo de referencia y debe seguir mostrando el set completo, igual
  que conserva los 10 pasos de pipeline aunque se siembren 8 (SPEC-003 FR-005).
  Lo que cambia es el sembrado, no el ejemplo.
- Q: ¿Cuál es la referencia rota? → A: `docs/ARCHITECTURE.md` cita
  `{{sdd.adapters}}/python/gen_import_linter.py`, que con `--language none` no
  se vendoriza: ningún adaptador se copia. Verificado en instalación real.
- Q: ¿Cómo se evita que vuelva a pasar? → A: un test que instala de verdad (en
  los dos lenguajes) y verifica que ninguna ruta citada en los docs quede
  colgada. `check_constitution` ya hace esto para las líneas de la
  constitución, pero nada cubría el resto de los documentos instalados.
- Q: ¿Y los enforcements que existen pero no validan nada (`check_naming.py`
  con `language: none`)? → A: fuera de alcance de los FR, pero se documenta:
  `sdd-configure` avisa cuando un principio declara un enforcement que la
  instalación no puede ejecutar, en vez de dejarlo pasar en silencio.

## Acceptance Scenarios

- **Given** un directorio vacío, **When** se instala y se corre `render.py`,
  **Then** el `CONSTITUTION.md` generado tiene exactamente los principios
  I..IV y ningún opcional.
- **Given** el `.sdd/config.yaml` sembrado, **When** el dueño lo abre,
  **Then** encuentra los principios opcionales comentados, con la instrucción
  de descomentar los que apliquen.
- **Given** una instalación con `--language none`, **When** se recorren las
  rutas citadas en los documentos instalados, **Then** todas existen.
- **Given** el config de ejemplo, **When** se lo consulta como catálogo,
  **Then** sigue mostrando el set completo de principios.

## Functional Requirements

- **FR-001** MUST: `core/sdd_init.py` siembra en `.sdd/config.yaml` solo los
  principios del núcleo mínimo obligatorio (los cuatro primeros del ejemplo);
  los demás se emiten comentados, con una línea que indique descomentar los que
  apliquen.
- **FR-002** MUST: `examples/config/config.yaml` conserva el catálogo completo
  de principios — el cambio es del sembrado, no del ejemplo.
- **FR-003** MUST: `templates/docs/ARCHITECTURE.md` no cita rutas de un
  adaptador que puede no estar instalado; describe el mecanismo (el adaptador
  del lenguaje traduce `layers` a contratos de imports) sin depender de que
  exista un archivo concreto.
- **FR-004** MUST: existe un test que instala en los dos lenguajes soportados
  (`python` y `none`) y falla si algún documento instalado cita una ruta de
  archivo inexistente.
- **FR-005** SHOULD: el playbook de `sdd-configure` indica avisar cuando un
  principio declara un `Enforcement:` que la instalación no puede ejecutar
  (por lenguaje o por tooling ausente), para que el dueño lo decida en vez de
  heredarlo en silencio.

## Key Entities

- `core/sdd_init.py::_seed_principles` — sembrado del núcleo (nuevo, análogo a
  `_seed_pipeline_steps`).
- `examples/config/config.yaml` — catálogo de referencia; no se recorta.
- `templates/docs/ARCHITECTURE.md` — deja de citar el generador del adaptador.
- `tests/unit/test_derived_references.py` — auditoría de rutas colgadas
  (nuevo).
- `templates/docs/playbooks/sdd-configure.md` — aviso de enforcement no
  disponible.

## Success Criteria

- **SC-001** `CONSTITUTION.md` de una instalación fresca tiene 4 principios
  (antes: 6, dos de ellos nunca elegidos).
- **SC-002** Instalación con `--language none`: cero rutas citadas
  inexistentes (antes: 1, `gen_import_linter.py`).
- **SC-003** Pipeline de una instalación fresca sigue VERDE en ambos lenguajes
  (sin regresión de SPEC-003 SC-001).
- **SC-004** El kit sigue VERDE 10/10.

## Assumptions

- El núcleo mínimo son los cuatro primeros principios del ejemplo, ya marcados
  como tales por un comentario en `examples/config/config.yaml`; el sembrado
  los toma por posición relativa a ese marcador, no por una lista duplicada en
  el código (Principio de SSOT).
- El principio II (capas) se siembra también con `language: none`, coherente
  con la decisión de SPEC-003 de sembrar el paso `layers` aunque su tool pueda
  faltar: el invariante aplica, el enforcement se omite con aviso.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_sdd_init_seeded_principles.py, tests/unit/test_example_config.py (ancla del marcador) |
| FR-002 | tests/unit/test_example_config.py |
| FR-003 | tests/unit/test_derived_references.py |
| FR-004 | tests/unit/test_derived_references.py |
| FR-005 | verificación manual (playbook) |

## Fuera de alcance

- Que el paso `naming` valide algo con `language: none` (el adaptador `none` no
  valida código por diseño).
- Renumerar los principios opcionales al descomentarlos: el config usa `id`
  explícito y es el dueño quien elige la numeración.
- Matriz de CI multiplataforma (SPEC-012).

## Historial

- 2026-08-04: creada (draft), registrada en `SPECS_REGISTRY.md` y declarada en
  `.sdd/current-spec`.
- 2026-08-04: implementada y promovida a `active`. Constitución de una
  instalación fresca: 4 principios (antes 6). Cero rutas colgadas en ambos
  lenguajes. Pipelines VERDE: derivado `none` 4/4, derivado `python` 8/8,
  kit 10/10. 146 tests + 1 skip.
