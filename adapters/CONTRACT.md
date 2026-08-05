# Contrato de adaptador de lenguaje

Un adaptador vive en `adapters/<language>/` y provee los validadores de **código**
que el pipeline agnóstico delega. El pipeline (`core/pipeline.py`) invoca:

```
python adapters/<language>/adapter.py <step>
```

## Pasos que debe soportar

| Paso | Qué valida |
|------|------------|
| `naming` | Nomenclatura agnóstica (palabras excluidas de `.sdd/config.yaml`). |
| `layers` | Dependencias entre capas (matriz `layers` del config). |
| `lint` | Estilo/errores estáticos. |
| `format` | Formato (modo check). |
| `types` | Tipos (si el lenguaje lo soporta). |
| `security` | Análisis de seguridad estático. |
| `tests` | Suite de tests unitarios. |

## Contrato

- Entrada: un único argumento (el nombre del paso).
- Salida: **exit 0 = OK, exit ≠ 0 = falla**. El pipeline agrega el resultado.
- Parametrización: el adaptador lee `.sdd/config.yaml` vía `core/sdd_config.py`
  (source_roots, dirs, naming, layers). No hardcodea rutas ni palabras excluidas.
- Un paso no soportado por el lenguaje puede devolver 0 con un aviso (no-op).

## Adaptadores

- **`python/`** — referencia completa (ruff, mypy, bandit, pytest, import-linter,
  `check_naming.py` AST, `gen_import_linter.py`).
- **`node/`, `go/`** — roadmap. Implementar el mismo `adapter.py <step>`.
