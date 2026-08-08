# Suite e2e — verificación del kit instalado

> **SSOT de la estrategia de verificación e2e.** Qué cubre, cómo se corre y cómo
> se agrega un escenario. El *por qué* y los requisitos están en
> [`SPEC-018`](../../specs/SPEC-018-verificacion-e2e.md).

Cada escenario instala el kit de verdad —`core/sdd_init.py` como subproceso,
sobre un repositorio git nuevo— y verifica las promesas que el instalador le hace
al adoptante. Es el nivel que la suite unitaria no alcanza: ninguna función
miente, lo que miente es el conjunto instalado.

## Cómo se corre

```bash
pytest tests/e2e -q          # ~35 s
```

`pytest` a secas **no** los recoge: `testpaths` en `pyproject.toml` apunta solo a
`tests/unit`, y ese es el único mecanismo de selección (no hay marca `e2e`).
`python core/pipeline.py` tampoco los corre.

| Variable | Efecto |
|---|---|
| `SDD_E2E_WORK` | Workspace de trabajo. Por defecto `<temp del sistema>/sdd-e2e`. Nunca puede solaparse con el árbol del kit: la suite aborta si lo hace. |
| `SDD_E2E_STRICT` | Con valor no vacío, las omisiones por entorno incompleto (falta `pre-commit`) pasan a ser fallos. CI la setea. |

El workspace se borra y recrea **al inicio** de la corrida, no al final: así la
regeneración no depende de que la corrida anterior haya terminado bien, y los
artefactos quedan en disco para inspeccionar un fallo.

Ese borrado no es incondicional: la suite siembra `.sdd-e2e-workspace` en la raíz
del workspace y solo borra lo que no existe, lo que está vacío o lo que lleva esa
marca. Un `SDD_E2E_WORK` que apunte a una carpeta con contenido ajeno aborta la
corrida y la deja intacta; borrar la marca a mano es la forma de blindar un
workspace que querés conservar.

## Qué verifica cada escenario

| Escenario | Promesa |
|---|---|
| `test_instalacion_limpia` | Carpeta vacía: archivos clave, las 5 skills en los 4 formatos, veredicto del pipeline sin pasos inventados, `sdd-doctor` sano. |
| `test_instalacion_brownfield` | Proyecto con historia git: conserva lo del dueño, detecta `source_roots`, el gate protege esa carpeta, el CI dispara en la rama real. |
| `test_wiring_propio` | Wiring del dueño preexistente: se conserva, se avisa, y `sdd-doctor` no dice "sana" con cero capas activas. |
| `test_configuracion` | Editar `.sdd/config.yaml` cambia los artefactos **y** el veredicto sobre el mismo código. |
| `test_ciclo_spec_first` | Los tres escenarios de SPEC-017 US3 con commits reales, más el escape hatch y su aviso al operador. |
| `test_tests_de_integracion` | Declarar `dirs.tests_integration` alcanza para que esos tests corran, fallen en su propio paso y no queden huérfanos (SPEC-019). |

## Cómo se agrega uno

1. Un archivo en `escenarios/`, con docstring que diga qué promesa verifica y —si
   nació de un defecto reproducido— cuál.
2. Partir de un fixture de `conftest.py`: `destino` (carpeta vacía), `repo` (con
   git), `derivado` (kit instalado y `render` corrido) o `derivado_con_hooks`.
3. Actuar con los helpers de `lib/entorno.py` (`instalar`, `commitear`, `paso`,
   `herramienta`, `pipeline`) y afirmar con los de `lib/aserciones.py`.
4. **Afirmar contenido, no solo el exit code.** El peor hallazgo de la campaña
   manual fue un `sdd-doctor` que decía "Instalación SDD sana" con cero capas de
   gate activas y salía exit 0: un `assert res.exit == 0` lo habría dado por bueno.
5. Si el escenario necesita `pre-commit` real, usar `derivado_con_hooks`: degrada
   solo cuando corresponde.

Los unitarios del propio harness viven en `tests/unit/test_e2e_entorno.py` y
`tests/unit/test_e2e_aislamiento.py`.
