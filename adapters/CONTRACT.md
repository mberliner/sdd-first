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
- Salida: tres estados. El pipeline agrega el resultado.

  | Exit | Estado | Significado |
  |------|--------|-------------|
  | `0` | OK | el paso verificó y pasó |
  | `3` | OMITIDO | el paso **no se pudo verificar**: sin targets existentes, sin la tool instalada, sin umbrales declarados, o paso no soportado por el lenguaje |
  | otro | FALLO | el paso verificó y encontró violaciones |

- El estado OMITIDO existe para que una instalación fresca no arranque en ROJO
  por tooling que todavía no tiene, **sin** que eso haga pasar por verificado lo
  que nadie miró: el pipeline no lo cuenta entre los pasos OK y lo informa
  aparte. La constante es `EXIT_OMITIDO` en `core/sdd_config.py` (SSOT).
  Ver SPEC-003 FR-009 y SPEC-001 FR-005.
- Parametrización: el adaptador lee `.sdd/config.yaml` vía `core/sdd_config.py`
  (source_roots, dirs, naming, layers). No hardcodea rutas ni palabras excluidas.

## Adaptadores

- **`python/`** — referencia completa (ruff, mypy, bandit, pytest, import-linter,
  `check_naming.py` AST, `gen_import_linter.py`).
- **`node/`, `go/`** — roadmap. Implementar el mismo `adapter.py <step>`.
