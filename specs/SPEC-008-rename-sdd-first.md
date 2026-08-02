# SPEC-008-rename-sdd-first: Renombrar mensajes internos sdd-kit a sdd-first

## User Story (Priority P3)

Como mantenedor de sdd-first, quiero que los mensajes de error/print del
núcleo digan "sdd-first" (no "sdd-kit") para que sean consistentes con el
resto del repo, ya renombrado en el commit anterior.

**Why this priority:** cosmético, no cambia comportamiento; se hace ahora
solo porque el gate spec-first exige spec antes de tocar `core/`.

**Independent Test:** grep de "sdd-kit" sobre `core/` no devuelve resultados.

## Clarifications

### Session 2026-08-02
- Q: ¿alcance del cambio? → A: solo texto literal en mensajes de
  `core/sdd_config.py` y `core/sdd_init.py`, sin tocar lógica.

## Acceptance Scenarios

- **Given** el mensaje de error por PyYAML ausente en `sdd_config.py`,
  **When** se dispara, **Then** menciona "sdd-first" en vez de "sdd-kit".
- **Given** el print de inicio de instalación en `sdd_init.py`,
  **When** corre `sdd_init.py`, **Then** el texto dice "sdd-first".

## Functional Requirements

- **FR-001** MUST: `core/sdd_config.py` no debe contener el literal
  `"sdd-kit"`.
- **FR-002** MUST: `core/sdd_init.py` no debe contener el literal
  `"sdd-kit"`.

## Key Entities

- N/A (cambio de texto, no de datos).

## Success Criteria

- **SC-001** `grep -ri "sdd-kit" core/` no devuelve coincidencias.
- **SC-002** El pipeline (`core/pipeline.py`) sigue en VERDE tras el cambio.

## Assumptions

- El rename ya se aplicó al resto de la documentación en un commit previo;
  esta spec cubre únicamente los dos archivos de `core/` que quedaron
  bloqueados por el gate spec-first.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | grep manual + `core/pipeline.py` (paso tests, no rompe suite existente) |
| FR-002 | grep manual + `core/pipeline.py` (paso tests, no rompe suite existente) |

## Fuera de alcance

- Cambiar el nombre del paquete/carpeta del repo.
- Cualquier cambio funcional en `sdd_config.py` o `sdd_init.py`.

## Historial

- 2026-08-02: creada (draft).
