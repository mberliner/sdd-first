# Cómo contribuir — {{project.name}}

> SSOT del workflow humano (Definition of done, bloque `[SDD-Check]`, code review).

## Filosofía: SDD adaptativo

La spec precede al código, pero la spec es **viva**: se ajusta cuando la
implementación revela algo. Cambios pequeños → spec liviana; cambios grandes →
spec completa + `clarify`/`analyze` antes de codear.

## Definition of done (checklist de cierre)

- [ ] El cambio mapea a una o más specs registradas y vigentes.
- [ ] Identificadores nuevos respetan `SPEC-000-naming.md`.
- [ ] El dominio quedó limpio (sin imports hacia afuera).
- [ ] Hay tests para todo cambio de comportamiento.
- [ ] La spec se actualizó si el comportamiento difiere.
- [ ] `python {{sdd.core}}/pipeline.py` está verde.
- [ ] Entrada agregada en `historial/sdd.md`.
- [ ] Commit con bloque `[SDD-Check]`.

## Bloque `[SDD-Check]`

```
[SDD-Check]
- Specs leídas: SPEC-NNN-x, SPEC-NNN-y
- Includes/excludes verificados: ...
- SSOTs afectados: ...
```

## Code review (5 preguntas)

1. ¿El cambio mapea a una spec vigente?
2. ¿Los identificadores son agnósticos (SPEC-000)?
3. ¿El dominio quedó limpio (capas respetadas)?
4. ¿Hay tests que cubran el comportamiento?
5. ¿La spec quedó actualizada respecto de lo implementado?
