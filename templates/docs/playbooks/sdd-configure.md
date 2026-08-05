# Playbook: sdd-configure

Personaliza `.sdd/config.yaml` (SSOT de parámetros) con un wizard, y regenera los
artefactos derivados.

## Procedimiento

1. Leé el `.sdd/config.yaml` actual (si existe) para partir de sus valores.
2. Preguntá, una por vez (usá `AskUserQuestion` si está disponible), y escribí
   cada respuesta en el config:
   - **project.name** y **project.domain** (descripción corta del dominio).
   - **project.language** (`python` | `none`).
   - **naming.prohibited**: palabras excluidas (proveedores, UI, formatos, auth
     que el proyecto quiere vetar). Confirmá también `allowed_identifiers` y
     `relax_in_tests`.
   - **principles**: partí del núcleo mínimo obligatorio (nomenclatura, capas,
     trazabilidad, gate) y preguntá qué principios opcionales agregar — el
     config los trae comentados, listos para descomentar. Si un principio
     declara un `enforcement` que esta instalación no puede ejecutar (por
     `language: none`, o porque la tool no está), decílo al ofrecerlo: se
     verificará en code review, no automáticamente.
   - **layers**: nombres de capas y matriz de imports permitidos.
   - **dirs**: rutas de cada capa y de los tests.
   - **pipeline.steps**: qué pasos correr.
3. Guardá el config editado (es el SSOT; queda editable a mano después).
4. Regenerá artefactos derivados y verificá:

   ```
   python tools/sdd/core/render.py
   python tools/sdd/core/gen_skill_adapters.py
   python tools/sdd/core/check_constitution.py CONSTITUTION.md
   ```

5. Mostrá un resumen de lo que cambió. No inventes principios ni palabras excluidas: si el
   usuario no sabe, ofrecé los defaults del kit.
