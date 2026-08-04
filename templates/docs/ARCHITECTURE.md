# Arquitectura — {{project.name}}

> SSOT de capas. La matriz concreta de dependencias vive en `layers` de
> `.sdd/config.yaml`; el adaptador del lenguaje la traduce a contratos de
> imports verificables (en Python, import-linter). Sin adaptador
> (`language: none`) la matriz sigue siendo el SSOT, pero se verifica en code
> review en vez de automáticamente.

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
