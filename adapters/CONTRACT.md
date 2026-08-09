# Contrato de adaptador de lenguaje

Un adaptador vive en `adapters/<language>/` y provee los validadores de **código**
que el pipeline agnóstico delega. El pipeline (`core/pipeline.py`) invoca:

```
python adapters/<language>/adapter.py <step>
```

## Pasos que debe soportar

> El vocabulario de esta tabla está declarado en `CODE_STEPS`
> (`core/sdd_config.py`) — es del núcleo, porque lo que reserva estos nombres es
> el contrato; el lenguaje aporta la implementación de cada paso, no la lista.
> `tests/unit/test_vocabulario_de_pasos.py` cruza el dispatcher de cada adaptador
> contra esa constante en las dos direcciones (SPEC-005 FR-006).

| Paso | Qué valida |
|------|------------|
| `naming` | Nomenclatura agnóstica (palabras excluidas de `.sdd/config.yaml`). |
| `layers` | Dependencias entre capas (matriz `layers` del config). |
| `lint` | Estilo/errores estáticos. |
| `format` | Formato (modo check). |
| `types` | Tipos (si el lenguaje lo soporta). |
| `security` | Análisis de seguridad estático. |
| `tests` | Suite de tests unitarios (`dirs.tests_unit`). |
| `integration` | Suite de tests de integración (`dirs.tests_integration`). |
| `coverage` | Umbrales de `pipeline.coverage` (SPEC-009 FR-001). |

## Consultas que puede soportar

Una **consulta** produce un dato en vez de validar. No es un paso de pipeline: no
entra a `pipeline.steps`, no entra a `CODE_STEPS` del núcleo, y quien la
invoca es una herramienta puntual, no el pipeline. Se llama igual:
`python adapters/<language>/adapter.py <consulta>`.

| Consulta | Qué produce | Salida |
|----------|-------------|--------|
| `coverage-baseline` | Cobertura real de las carpetas de código, medida sobre las carpetas de tests declaradas. La consume `core/sdd_coverage_baseline.py` para escribir el primer umbral de un proyecto que no tiene ninguno (SPEC-009 FR-US2-001). | Una línea `SDD-COVERAGE-BASELINE <porcentaje> <paths separados por coma>`. El prefijo es `COVERAGE_BASELINE_PREFIX` en `core/sdd_config.py` (SSOT). |

Los mismos tres estados de salida que un paso: `0` produjo el dato, `3` no se pudo
medir (sin la tool, sin código o sin tests todavía), otro = falló. Un adaptador
puede no ofrecer una consulta: el núcleo lo trata como omisión, no como error.

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
- Cada carpeta de tests declarada en `dirs` tiene **su** paso: `tests` corre la
  unitaria y `integration` la de integración, cada uno sin adivinar la carpeta del
  otro. Qué pasos corren de verdad lo decide `pipeline.steps` del proyecto; que
  una carpeta declarada quede sin ejecutor es un problema que reporta `sdd-doctor`
  (SPEC-019), no algo que el adaptador resuelva por su cuenta.

## Adaptadores

- **`python/`** — referencia completa (ruff, mypy, bandit, pytest, pytest-cov,
  import-linter, `check_naming.py` AST, `gen_import_linter.py`).
- **`node/`, `go/`** — roadmap. Implementar el mismo `adapter.py <step>`.
