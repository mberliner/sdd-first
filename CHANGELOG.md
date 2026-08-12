# Changelog — sdd-first

> Una entrada por `KIT_VERSION` publicada (`core/sdd_config.py`).
> `tests/unit/test_changelog.py` exige entrada para la versión vigente.
> Las entradas marcadas **Acción requerida** son cambios que el andamiaje
> nuevo juzga con reglas que el contenido ya instalado del dueño (specs,
> historial) no migra solo: `sdd-update` las destaca aparte antes de aplicar.

## 0.1.0 — 2026-08-12

Primera versión que se declara a sí misma. Antes de esta versión no había
`KIT_VERSION` ni forma segura de actualizar un derivado ya instalado:
`project.kit_version` era una constante copiada del ejemplo (siempre
`"0.1.0"`, nunca comparada contra nada), y la única ruta de "actualización",
`sdd-init --force`, borraba `specs/SPECS_REGISTRY.md` y `historial/sdd.md`.

Trae:

- `KIT_VERSION` vendorizado (`core/sdd_config.py`), independiente de
  `constitution.version`.
- `.sdd/kit.lock`: manifiesto JSON de la instalación (versión, valores de
  sustitución usados, hash por `plantilla`, presencia de cada `semilla`).
- Catálogo de clases de propiedad (`core/sdd_catalog.py`:
  vendor/plantilla/semilla) — SSOT único para instalación y actualización.
- `sdd-update` (`core/sdd_update.py`): plan por defecto, `--apply` escribe,
  `--diff` muestra el contenido de los cambios. Nunca pisa una `plantilla`
  editada: la reporta como conflicto y deja la versión del kit en
  `<archivo>.kit-new`.
- `sdd-init --force` deja de destruir `specs/SPECS_REGISTRY.md` y
  `historial/sdd.md`, y aplica la misma política de conflicto que
  `sdd-update` sobre las plantillas editadas.
