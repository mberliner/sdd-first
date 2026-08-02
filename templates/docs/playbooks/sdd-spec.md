# Playbook: sdd-spec

Crea una spec nueva, la registra y la declara vigente para desbloquear el gate.

## Procedimiento

1. Pedí (o inferí del contexto) un título/slug agnóstico para la capacidad.
2. Creá la spec:

   ```
   python tools/sdd/core/sdd_spec.py "<slug>" --title="<Título legible>"
   ```

   Esto genera `specs/SPEC-NNN-slug.md` desde la plantilla, agrega la fila `draft`
   al registro y escribe `SPEC-NNN-slug` en `.sdd/current-spec`.
3. **Editá la spec** completando las secciones de `docs/SPEC-FORMAT.md` (User
   Story con prioridad, FR-NNN con `MUST:`, SC-NNN, Coverage mapping). Este paso
   es obligatorio: el gate exige que la spec sea modificada *después* de
   declararla en `.sdd/current-spec`.
4. Opcional pero recomendado: corré la skill `clarify` para cerrar ambigüedades y
   `analyze` para validar adecuación antes de codear.
5. Recién entonces empezá a editar código: el gate spec-first ya permite las
   ediciones de las carpetas de código fuente.
