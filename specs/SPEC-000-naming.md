# SPEC-000: Nomenclatura agnóstica a tecnología

> Generado por `core/render.py` desde la sección `naming` de
> `.sdd/config.yaml`. Editá el config, no este archivo.

## Regla

Ningún identificador de código (clase, función, variable, módulo) puede
contener un token que nombre un proveedor, framework de UI, formato de
almacenamiento/serialización o protocolo de autenticación. El código nombra
*conceptos del dominio*, no *tecnologías*; los detalles de tecnología viven
detrás de puertos, en la capa de adaptadores.

## Tokens prohibidos

- `watson`
- `streamlit`
- `flask`
- `django`
- `gradio`
- `oauth`
- `jwt`
- `apikey`

## Identificadores permitidos (excepciones)

- (ninguno)

## Tokens relajados en tests

En las carpetas de tests se toleran los siguientes tokens (los nombres de
tests describen el escenario, no acoplan a tecnología):

- (ninguno)

## Enforcement

Automático vía `adapters/<language>/check_naming.py` (paso `naming` del
pipeline). Ver `.sdd/config.yaml`.
