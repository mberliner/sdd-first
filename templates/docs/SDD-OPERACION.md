# Manual de operación SDD — {{project.name}}

> Catálogo humano de las herramientas SDD instaladas en este proyecto. Para el
> protocolo formal que sigue el agente ver `AGENTS.md`; para el detalle técnico
> paso a paso de cada una ver su playbook en `docs/playbooks/`.

Este proyecto sigue **SDD (Spec-Driven Development)**: ninguna capacidad nueva
se codea sin una spec vigente. Estas son las herramientas disponibles para
trabajar con ese flujo, ya sea como skill de tu asistente (`analyze`,
`clarify`, `sdd-spec`, `sdd-doctor`, `sdd-configure`) o invocando directo el
script vendorizado bajo `tools/sdd/core/`.

## `sdd-spec` — crear una spec nueva

Genera `specs/SPEC-NNN-slug.md` desde la plantilla, la registra en
`SPECS_REGISTRY.md` y la declara en `.sdd/current-spec` para desbloquear el
gate. **Usala antes de codear cualquier capacidad nueva** — es el primer paso
de cualquier feature o fix de comportamiento.

## `clarify` — cerrar ambigüedades de una spec

Detecta subespecificación en una spec (hasta 5 preguntas dirigidas) y graba
las respuestas en la propia spec. Usala después de crear la spec y antes de
empezar a codear, si la capacidad tiene zonas grises.

## `analyze` — validar que la spec es sólida

Análisis de solo lectura: chequea la spec contra tests, el registro y
`CONSTITUTION.md`. Usala antes de implementar (para confirmar que la spec
está completa) o para auditar una spec ya existente.

## `sdd-doctor` — diagnosticar la salud de la instalación

Verifica config, artefactos requeridos, gates cableados, drift de artefactos
generados y versión del kit vendorizado. Reporta o autorepara con `--fix`.
Usala cuando algo no cierra (el gate bloquea sin motivo claro, el pipeline
falla de forma rara) o después de actualizar el kit.

## `sdd-configure` — personalizar los parámetros del proyecto

Wizard interactivo sobre `.sdd/config.yaml` (dominio, lenguaje, principios,
palabras excluidas, capas) que regenera `CONSTITUTION.md` y las skills
derivadas. Usala para configurar SDD la primera vez o para reconfigurarlo si
cambian las reglas del proyecto (nueva capa, nueva palabra excluida, etc.).

## Verificación completa

Ninguna de estas skills reemplaza correr el pipeline entero:

```
python tools/sdd/core/pipeline.py
```

Corré esto antes de cerrar cualquier iteración.
