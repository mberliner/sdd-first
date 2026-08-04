# Desarrollo — {{project.name}}

> **SSOT del setup local y los comandos del día a día.** Qué instalar, qué
> correr y en qué orden. Las reglas de arquitectura viven en
> `docs/ARCHITECTURE.md`; el workflow de contribución, en
> `docs/CONTRIBUTING.md`.

## Requisitos

- **Python 3.11+** — lo necesita el andamiaje SDD (`{{sdd.core}}/`), aunque el
  producto esté escrito en otra tecnología.
- **PyYAML** — única dependencia del andamiaje: `pip install pyyaml`.
- Las dependencias del producto en sí: ver `requirements.txt` /
  `requirements-dev.txt` / el manifiesto que corresponda.

## Primer arranque

```bash
pip install -r requirements-dev.txt        # si existe
python {{sdd.core}}/bootstrap_hooks.py     # instala los hooks git del gate
python {{sdd.core}}/pipeline.py            # verificación completa → VERDE / ROJO
```

El paso de hooks es idempotente y también corre como paso 0 del pipeline: un
clon nuevo queda cableado a más tardar en su primera corrida.

## Comandos frecuentes

| Qué querés | Comando |
|---|---|
| Verificar todo antes de cerrar | `python {{sdd.core}}/pipeline.py` |
| Cortar en el primer fallo | `python {{sdd.core}}/pipeline.py --fail-fast` |
| Diagnóstico del andamiaje | `python {{sdd.core}}/sdd_doctor.py` |
| Crear y registrar una spec | skill `sdd-spec` (o `python {{sdd.core}}/sdd_spec.py`) |
| Regenerar docs derivados del config | `python {{sdd.core}}/render.py` |
| Regenerar las skills de los asistentes | `python {{sdd.core}}/gen_skill_adapters.py` |

## Tooling opcional del pipeline

Los pasos de código se habilitan en `pipeline.steps` de `.sdd/config.yaml` y
cada uno requiere su herramienta. **Si la herramienta no está instalada, el
paso se omite con aviso en vez de fallar**: el proyecto arranca en VERDE y vas
habilitando tooling a medida que lo agregás.

| Paso | Herramienta |
|---|---|
| `lint`, `format` | `ruff` |
| `types` | `mypy` |
| `security` | `bandit` |
| `tests`, `coverage` | `pytest` (+ `pytest-cov` para `coverage`) |
| `layers` | `import-linter` |
| `naming` | ninguna (lo provee el andamiaje) |

## Umbrales de cobertura

El paso `coverage` es opcional: sin la clave `pipeline.coverage` en el config,
se omite. Cuando la suite madure, declarala:

```yaml
pipeline:
  coverage:
    - paths: [src]
      min: 80
    - paths: [src/domain]     # al núcleo se le exige más que al resto
      min: 96
```

## Dependencias nuevas

Agregar una dependencia se justifica en este documento (qué problema resuelve
y por qué no alcanzaba con lo que ya había) antes de sumarla al manifiesto.
