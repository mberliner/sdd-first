# Playbook: sdd-update

Actualiza el andamiaje SDD vendorizado de un proyecto derivado a la versión
de este clon del kit, sin perder lo que el dueño escribió o adaptó. **No se
instala en el derivado**: se corre desde el clon del kit, apuntando al
proyecto — simétrico a `sdd-init`.

## Procedimiento

1. Mostrá el plan (no escribe nada):

   ```
   python core/sdd_update.py <ruta-del-derivado>
   ```

   Clasifica cada artefacto: `sin cambios` / `actualizar` / `conflicto` /
   `nuevo` / `eliminado` / `regenerar`, nombra los `.kit-new` de una corrida
   anterior sin resolver, las claves nuevas de `.sdd/config.reference.yaml`
   que el config del dueño no tiene, y cita el `CHANGELOG.md` entre la
   versión instalada y la de este clon.

2. Para ver el contenido de cada cambio, no solo los nombres:

   ```
   python core/sdd_update.py <ruta-del-derivado> --diff
   ```

3. Si el plan se ve bien, aplicalo:

   ```
   python core/sdd_update.py <ruta-del-derivado> --apply
   ```

   Purga y recrea `tools/sdd/`, actualiza las plantillas intactas, deja las
   editadas sin tocar (con la versión nueva en `<archivo>.kit-new` al lado
   para fusionar a mano), regenera los artefactos derivados, y reescribe
   `.sdd/kit.lock`. Corre `sdd-doctor` antes y después: si aparece un
   problema nuevo (no preexistente), la corrida termina en rojo.

4. Si hay `.kit-new`, fusioná a mano lo que corresponda y borrá el archivo
   (o dejalo: la corrida siguiente lo borra sola cuando el original vuelve a
   coincidir con lo que entrega el kit).

## Qué NO hace

- No reescribe `.sdd/config.yaml` (destruiría comentarios); nombra las
  claves nuevas para que las agregues a mano.
- No fusiona conflictos automáticamente.
- No migra contenido del dueño (`specs/`, `historial/sdd.md`) a las reglas
  nuevas que el andamiaje pueda traer — el `CHANGELOG.md` avisa cuáles
  exigen revisión.
