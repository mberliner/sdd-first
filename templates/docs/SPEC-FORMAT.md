# Formato y método de redacción de specs

> SSOT del formato de spec. Adaptación del enfoque híbrido estilo GitHub Spec Kit:
> una spec describe un **corte vertical** de capacidad (user story + requisitos
> verificables), no un diseño técnico exhaustivo.

## Secciones obligatorias (formato híbrido)

`core/check_traceability.py` exige, en specs `hibrido`:

1. **User Story** con **prioridad** declarada (P1/P2/P3) y un *Independent Test*.
2. **Functional Requirements** con IDs `FR-NNN` (o `FR-USk-NNN` en specs multi-HU).
   Cada FR empieza con la keyword `MUST:` / `SHOULD:` / `MAY:`.
3. **Success Criteria** con IDs `SC-NNN`, binarios y agnósticos de implementación.
4. **Coverage mapping**: tabla `| Requisito | Cubierto por |` que mapea cada
   `FR-NNN` a el/los test(s) que lo verifican. La relación FR↔SC es N:M.

## Template copiable

```markdown
# SPEC-NNN: <título agnóstico>

## User Story (Priority Pn)

Como <rol>, quiero <capacidad> para <beneficio>.

**Why this priority:** ...
**Independent Test:** ...

## Clarifications

### Session YYYY-MM-DD
- Q: ... → A: ...

## Acceptance Scenarios

- **Given** ... **When** ... **Then** ...

## Functional Requirements

- **FR-001** MUST: ...
- **FR-002** SHOULD: ...

## Key Entities

- ...

## Success Criteria

- **SC-001** ...

## Assumptions

- ...

## Coverage mapping

| Requisito | Cubierto por |
|-----------|--------------|
| FR-001 | tests/unit/test_x.py |

## Fuera de alcance

- ...

## Historial

- YYYY-MM-DD: creada (draft).
```

## Ciclo de vida

`draft` → (implementación + tests) → `active` → `superseded`/`archived`. El estado
vive en `SPECS_REGISTRY.md`; la spec es viva y se actualiza si el comportamiento
implementado difiere.
