# Arquitectura — {{project.name}}

> SSOT de capas. La matriz concreta de dependencias vive en `layers` de
> `.sdd/config.yaml` y se traduce a contratos de import-linter con
> `adapters/python/gen_import_linter.py`.

## Capas (Clean Architecture)

Dependencias unidireccionales apuntando al dominio:

```
ui / composition roots  ──►  application  ──►  domain  ◄── adapters
```

- **domain/** — núcleo puro: entidades, puertos (interfaces), reglas. Sin I/O ni
  dependencias de proveedor. No importa de ninguna otra capa.
- **application/** — casos de uso; orquesta el dominio. Importa solo de `domain`.
- **adapters/** — implementaciones concretas de los puertos (proveedor, UI,
  formato, persistencia). Importa de `domain` (y `application` si aplica).
- **ui / composition roots** — ensamblan todo; son el único lugar que conoce a
  los concretos.

La "regla de oro" (el dominio no importa hacia afuera) la valida `lint-imports`
(paso `layers` del pipeline).

## ADRs

Registrá acá las decisiones de arquitectura del proyecto (formato ADR: contexto,
decisión, consecuencias).

- **ADR-001** — (ejemplo) ...
