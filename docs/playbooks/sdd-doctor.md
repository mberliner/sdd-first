# Playbook: sdd-doctor

Diagnostica la salud de la instalación SDD y, opcionalmente, autorepara el drift.

## Procedimiento

1. Ejecutá el chequeo:

   ```
   python tools/sdd/core/sdd_doctor.py
   ```

   Verifica: config presente y parseable, versión del kit registrada, artefactos
   requeridos presentes (CONSTITUTION, AGENTS, registro, SPEC-000, config,
   current-spec), gates cableados (`.claude/settings.json`,
   `.pre-commit-config.yaml`), y ausencia de drift en los artefactos generados
   (render y gen_skill_adapters con `--check`).

2. Interpretá el reporte para el usuario: qué está sano y qué falta o divergió.
3. Si hay drift de artefactos generados y el usuario lo aprueba, autorepará:

   ```
   python tools/sdd/core/sdd_doctor.py --fix
   ```

4. Para una verificación completa (no solo salud estructural), sugerí correr
   `python tools/sdd/core/pipeline.py`.
