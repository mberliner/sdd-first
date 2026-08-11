# SPEC-011: Onboarding del operador del kit: bootstrap reproducible en el README

> Origen: revisión del `README.md` del kit el 2026-08-04. Un operador que clona
> el repo y quiere generar un proyecto derivado desde cero no puede seguir los
> pasos literalmente: la secuencia publicada arranca a mitad de camino.

## User Story (Priority P1)

Como operador que clona `sdd-first` por primera vez, quiero que el `README.md`
publique la secuencia completa y ejecutable de bootstrap — desde obtener el kit
hasta el pipeline en VERDE y la primera spec — para poder generar un proyecto
derivado copiando comandos, sin inferir pasos ni leer el código del instalador.

**Why this priority:** es la primera impresión del kit y hoy falla al primer
comando. SPEC-003 dejó verde el happy path *técnico* y SPEC-007 dio README y
manual al *proyecto derivado*, pero nadie cubrió el onboarding del operador
del kit: el `README.md` de la raíz sigue siendo el único punto de entrada y
está incompleto.

**Independent Test:** ejecutar literalmente, en orden y sin conocimiento
previo, los comandos del bloque de bootstrap del `README.md` sobre un
directorio nuevo → termina en `pipeline` VERDE sin errores intermedios ni
pasos inferidos.

## Relación con specs existentes

- **Extiende:** — | **Supersede:** — | **Depende de:** —
- **Extendida por:** — | **Es dependencia de:** — | **Superseded por:** —
- **Por qué no cabe en una spec existente:** —

## Clarifications

### Session 2026-08-04

- Q: ¿Alcanza con documentar, o el instalador debe cambiar? → A: el
  comportamiento del instalador no cambia (ya crea el destino, ya es
  idempotente), pero **su mensaje de cierre sí**: es la otra mitad del mismo
  hueco. El operador termina la instalación mirando esa salida, no el README,
  y ahí faltaba el `cd` al destino —sin el cual los comandos `tools/sdd/...`
  no resuelven— y la primera spec.
- Q: ¿El mensaje repite el README entero? → A: no. Imprime la secuencia
  ejecutable con el path real del destino y omite los pasos ya satisfechos
  (`git init` si ya es repo, `pip install pre-commit` si ya está importable):
  un paso que no hace falta es ruido que resta credibilidad al que sí.
- Q: ¿`sdd-init` debería instalarse como skill en el derivado para cerrar el
  bootstrap circular? → A: no. SPEC-007 lo declaró fuera de alcance por diseño
  (es bootstrap de una sola vez). La spec resuelve la confusión explicándolo,
  no revirtiendo la decisión.
- Q: ¿Cómo se evita que el bloque de comandos del README se pudra? → A: un
  test parsea el bloque y verifica que cada script del kit que cita exista en
  disco (FR-007), igual que `test_template_paths.py` protege las plantillas.
- Q: ¿El README debe explicar `pre-commit install` a mano? → A: no. El paso
  `hooks` del pipeline ya los instala (`core/bootstrap_hooks.py`); lo que hay
  que documentar son sus dos precondiciones: que el destino sea repo git y que
  `pre-commit` esté instalado.

## Acceptance Scenarios

- **Given** un operador sin el repo clonado, **When** lee el `README.md`,
  **Then** encuentra el comando de clonado y el de instalación de `pyyaml`
  antes del primer uso de `sdd_init.py`.
- **Given** el bloque de bootstrap del README, **When** se lo lee de arriba a
  abajo, **Then** el cambio de directorio del kit al proyecto destino es
  explícito antes del primer comando `tools/sdd/...`.
- **Given** el bloque de bootstrap, **When** corre el test de FR-007, **Then**
  cada script del kit citado (`core/*.py`) existe en el repo.
- **Given** un operador que terminó la instalación, **When** busca en el README
  cómo empezar a codear, **Then** encuentra que el gate exige crear la primera
  spec con `sdd-spec` antes de tocar código fuente.

## Functional Requirements

- **FR-001** MUST: el `README.md` documenta la obtención del kit (`git clone` +
  `cd`) como paso previo a cualquier invocación de `core/sdd_init.py`.
- **FR-002** MUST: el `README.md` documenta la instalación de PyYAML
  (`pip install pyyaml`) antes del instalador. Es bloqueante: `sdd_init.py`
  importa `sdd_config`, que aborta con `SystemExit` si falta
  (`core/sdd_config.py:29-34`).
- **FR-003** MUST: la secuencia distingue explícitamente los dos directorios de
  trabajo — los comandos `core/...` corren en el clon del kit y los
  `tools/sdd/core/...` en el proyecto destino — con el `cd` intermedio a la
  vista.
- **FR-004** MUST: el `README.md` aclara que la skill `sdd-init` no se instala
  en el proyecto derivado (es bootstrap de una sola vez, se corre desde el clon
  del kit) y que, una vez vendorizado el andamiaje en `tools/sdd/`, el clon del
  kit es descartable.
- **FR-005** MUST: el `README.md` documenta las precondiciones de la capa git
  del enforcement: el destino debe ser repo git y `pre-commit` debe estar
  instalado para que el paso `hooks` cablee los hooks; sin eso el gate de
  commit queda inactivo (el gate SDD sigue funcionando sin git, por diseño).
- **FR-006** MUST: el `README.md` indica que antes de editar código hay que
  crear la primera spec con `sdd-spec`, porque el gate spec-first bloquea las
  ediciones mientras `.sdd/current-spec` esté vacío.
- **FR-007** MUST: existe un test que extrae los scripts del kit citados en el
  bloque de bootstrap del `README.md` y verifica que cada uno exista, para que
  un rename en `core/` no deje el README apuntando al vacío.
- **FR-008** SHOULD: el `README.md` enumera los valores válidos de
  `--language` (`python`, `none`) y cuál es el default.
- **FR-009** MUST: el mensaje de cierre de `core/sdd_init.py` imprime la
  secuencia completa para continuar, con el **path real** del destino en un
  `cd` explícito antes de cualquier comando `tools/sdd/...`, e incluye la
  creación de la primera spec (`sdd_spec.py`) como paso previo a editar código.
- **FR-010** MUST: ese mensaje omite los pasos de preparación ya satisfechos —
  no sugiere `git init` si el destino ya es repo git, ni
  `pip install pre-commit` si `pre_commit` ya es importable — y omite el `cd`
  si el destino es el directorio actual.
- **FR-011** SHOULD: el mensaje aclara que el andamiaje quedó vendorizado en
  `tools/sdd/` y que el clon del kit es descartable (paridad con FR-004).

## Key Entities

- `README.md` — único punto de entrada del operador del kit (SSOT del
  onboarding); no es plantilla, no se genera.
- `tests/unit/test_readme_bootstrap.py` — guarda de FR-001..FR-008 (nuevo).
- `core/sdd_init.py` — mensaje de cierre (FR-009..FR-011); su comportamiento de
  instalación no cambia.
- `tests/unit/test_sdd_init_next_steps.py` — guarda de FR-009..FR-011 (nuevo).
- `core/sdd_config.py`, `core/bootstrap_hooks.py` — solo como referencia del
  comportamiento documentado; no se modifican.

## Success Criteria

- **SC-001** La secuencia del README, ejecutada literalmente sobre un
  directorio nuevo, termina en pipeline VERDE (Independent Test).
- **SC-002** `python core/pipeline.py` sigue en VERDE tras el cambio.
- **SC-003** `pytest tests/unit` verde, incluyendo el test nuevo de FR-007.
- **SC-004** `python core/sdd_doctor.py` sano, sin drift de generados.

## Assumptions

- El operador tiene Python 3.11+ y `git` disponibles: ya está declarado en la
  sección "Requisitos" y queda fuera del bloque de comandos.
- El README sigue siendo un documento escrito a mano (no derivado del config),
  así que la protección contra drift es un test, no el render.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_readme_bootstrap.py |
| FR-002 | tests/unit/test_readme_bootstrap.py |
| FR-003 | tests/unit/test_readme_bootstrap.py |
| FR-004 | tests/unit/test_readme_bootstrap.py |
| FR-005 | tests/unit/test_readme_bootstrap.py |
| FR-006 | tests/unit/test_readme_bootstrap.py |
| FR-007 | tests/unit/test_readme_bootstrap.py |
| FR-008 | tests/unit/test_readme_bootstrap.py |
| FR-009 | tests/unit/test_sdd_init_next_steps.py |
| FR-010 | tests/unit/test_sdd_init_next_steps.py |
| FR-011 | tests/unit/test_sdd_init_next_steps.py |

## Fuera de alcance

- Instalar la skill `sdd-init` en el proyecto derivado (decidido en SPEC-007).
- `sdd-update` / ruta de actualización del kit vendorizado (E-2 de
  `docs/IDEAS.md`).
- Cambios en *qué instala* `core/sdd_init.py` o en el wiring (solo cambia su
  mensaje de cierre).
- El `README.md` del proyecto derivado (`templates/README.md`), cubierto por
  SPEC-007.

## Historial

- 2026-08-04: creada (draft), registrada en `SPECS_REGISTRY.md` y declarada en
  `.sdd/current-spec`.
- 2026-08-04: ampliada con FR-009..FR-011 (mensaje de cierre del instalador)
  tras notar que la salida de `sdd_init.py` repetía el mismo hueco que el
  README: comandos `tools/sdd/...` sin el `cd` al destino.
- 2026-08-04: implementada y promovida a `active`. Bootstrap verificado
  end-to-end en sandbox siguiendo el README literal (pipeline VERDE 8/8),
  8 tests nuevos en verde, cobertura 55% ≥ 50%. Nota: el pipeline del kit sale
  ROJO 8/10 en Windows por un fallo **preexistente y ajeno**
  (`test_main_instala_y_marca_ejecutable`: `chmod` no aplica en NTFS) más
  `coverage` en cascada; anotado como deuda en `historial/sdd.md`.
