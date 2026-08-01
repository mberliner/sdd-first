# Playbook: sdd-init

Instala el andamiaje SDD del kit en el proyecto actual.

## Procedimiento

1. Confirmá la raíz del proyecto destino (por defecto, el cwd) y si es un repo git.
2. Preguntá el lenguaje principal (`python` o `none`) si no está claro.
3. Ejecutá el instalador:

   ```
   python <kit>/core/sdd_init.py <target_dir> --language=<python|none>
   ```

   Esto copia plantillas de gobernanza, vendoriza `core/` y el adaptador bajo
   `tools/sdd/`, instala el wiring de gates (`.claude/settings.json`,
   `.pre-commit-config.yaml`, `.opencode/plugin/sdd-gate.js`, `.gitattributes`),
   y siembra `.sdd/config.yaml` + `.sdd/current-spec`. Es idempotente (no pisa
   lo existente salvo `--force`).
4. Corré `sdd-configure` para personalizar el config al dominio del proyecto.
5. Regenerá los artefactos derivados y verificá:

   ```
   python tools/sdd/core/render.py
   python tools/sdd/core/gen_skill_adapters.py
   python tools/sdd/core/pipeline.py
   ```

6. Reportá qué se instaló y los próximos pasos. No sobreescribas archivos del
   usuario sin confirmar.
