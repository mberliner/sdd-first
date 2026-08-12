# Índice de documentación — {{project.name}}

> Navegación y mapa de SSOTs. Evita duplicación: cada tema tiene un único archivo
> autoritativo. Este índice es sobre el protocolo SDD; `README.md` (fuera de este
> mapa) es la puerta de entrada al *producto* del proyecto, no a su gobernanza.

## Ruta de lectura recomendada

1. `CONSTITUTION.md` — principios (generado desde `.sdd/config.yaml`).
2. `00-INDEX.md` — este índice.
3. `AGENTS.md` — protocolo del agente.
4. `specs/SPECS_REGISTRY.md` — specs vigentes.
5. `specs/SPEC-000-naming.md` — nomenclatura agnóstica.
6. `docs/ARCHITECTURE.md` — capas.
7. `docs/SPEC-FORMAT.md` — cómo se escribe una spec.
8. `docs/SDD-ENFORCEMENT.md` — cómo se obliga el SDD.
9. `docs/SDD-OPERACION.md` — catálogo de las skills SDD instaladas.
10. `docs/CONTRIBUTING.md` — Definition of done y code review.
11. `docs/DEVELOPMENT.md` — setup local y comandos del día a día.
12. `docs/SKILLS-MULTITOOL.md` — cómo una skill sirve a varios asistentes.

## Mapa de SSOTs

| Tema | Archivo autoritativo |
|------|----------------------|
| Principios / constitución | `CONSTITUTION.md` (← `.sdd/config.yaml`) |
| Parámetros del proyecto | `.sdd/config.yaml` |
| Qué significa cada clave del config | `.sdd/config.reference.yaml` (catálogo, no se edita) |
| Protocolo del agente | `AGENTS.md` |
| Specs vigentes | `specs/SPECS_REGISTRY.md` |
| Nomenclatura | `specs/SPEC-000-naming.md` (← `.sdd/config.yaml`) |
| Capas / arquitectura | `docs/ARCHITECTURE.md` (matriz en `.sdd/config.yaml`) |
| Formato de spec | `docs/SPEC-FORMAT.md` |
| Enforcement | `docs/SDD-ENFORCEMENT.md` |
| Catálogo de skills SDD | `docs/SDD-OPERACION.md` |
| Mecanismo de skills multi-asistente | `docs/SKILLS-MULTITOOL.md` |
| Setup local y comandos | `docs/DEVELOPMENT.md` |
| Workflow / DoD | `docs/CONTRIBUTING.md` |
| Umbrales de cobertura y pasos del pipeline | `.sdd/config.yaml` |
| Workflow de CI | `.github/workflows/ci.yml` (← `.sdd/config.yaml`, generado) |
| Historial de iteraciones | `historial/sdd.md` |
| Ideas pre-spec | `docs/IDEAS.md` |
| Historial de versiones del andamiaje (lo trae `sdd-update`) | `CHANGELOG.md` del clon del kit -- no viaja acá, ver `docs/SDD-OPERACION.md` |
| Clases de propiedad de cada artefacto instalado | `{{sdd.core}}/sdd_catalog.py` |
| Manifiesto de esta instalación | `.sdd/kit.lock` (formato en `{{sdd.core}}/sdd_lock.py`) |
