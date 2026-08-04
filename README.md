# sdd-first

**Un método de trabajo, listo para instalar, que hace que tus specs manden sobre
el código.** sdd-first lleva el desarrollo guiado por especificaciones (SDD) a
cualquier proyecto: define principios, obliga a escribir la spec antes de codear,
verifica la trazabilidad entre spec y código, y trae skills para asistentes de IA
(Claude Code, Codex, opencode, Cursor…) — todo configurable desde un único
archivo.

## ¿Para quién es?

Está pensado para **proyectos chicos y medianos** y equipos pequeños que quieren
disciplina de specs sin montar una infraestructura pesada. Es liviano: unos pocos
scripts y plantillas, sin servicios ni base de datos. Si tu proyecto es enorme o
ya tiene un framework de gobernanza propio, esto probablemente te quede corto (o
tengas que adaptarlo).

## Qué te da

- **Una constitución** con los principios del proyecto (nomenclatura agnóstica,
  capas limpias, trazabilidad, y el gate spec-first como mínimo obligatorio).
- **Un formato de spec** híbrido (user story + requisitos verificables + mapeo a
  tests) y un registro central de specs.
- **Un "gate" spec-first**: bloquea editar código si no hay una spec vigente
  declarada y actualizada. Se engancha a Claude Code, pre-commit y opencode.
- **Skills para tu asistente de IA**: `sdd-init`, `sdd-configure`, `sdd-doctor`,
  `sdd-spec`, `analyze`, `clarify` — escritas una vez y generadas para **Claude
  Code** (`.claude/skills/`) y **opencode** (`.opencode/command/`), más
  **Codex** y **Antigravity**, que leen la fuente `.agents/skills/` directo.
  El mecanismo está en `docs/SKILLS-MULTITOOL.md`.
- **Un pipeline local** que corre todos los chequeos y te dice VERDE o ROJO,
  con umbrales de cobertura opcionales.
- **Un workflow de CI** generado desde el mismo config: corre el pipeline, no
  una lista de pasos duplicada que después diverge.

Todo se parametriza en `.sdd/config.yaml` (nombre, dominio, tokens prohibidos,
capas, principios, pasos del pipeline). No hay listas escondidas en el código.

## Requisitos

> **Importante:** el andamiaje del kit está escrito en **Python** y necesita
> **Python 3.11+** instalado para funcionar, *aunque tu proyecto sea de otra
> tecnología* (Node, Go, etc.). Python es la única dependencia del kit, más la
> librería `pyyaml`. Es una herramienta de proceso que corre "al costado" de tu
> proyecto, no una dependencia de tu producto.
>
> El kit es **agnóstico respecto del lenguaje que validás**, no respecto del que
> lo ejecuta: los validadores de *código* (naming, capas, lint, tipos) se enchufan
> por lenguaje mediante adaptadores. Hoy viene el adaptador **Python** completo y
> el modo **`none`** (solo gobernanza y specs, sin validar código). Node/Go están
> en el roadmap: implementan el mismo contrato (`adapters/CONTRACT.md`).
>
> Los pasos de código del adaptador Python usan tooling del proyecto, opcional:
> `lint`/`format` → **ruff** · `types` → **mypy** · `security` → **bandit** ·
> `tests` → **pytest** · `layers` → **import-linter**. El paso `naming` no
> requiere nada extra. Si una tool no está instalada (o todavía no hay código),
> el paso se **omite con aviso** en vez de fallar: el pipeline recién instalado
> arranca VERDE y vas habilitando tooling a medida que lo agregás.

## Cómo se usa

Desde tu asistente de IA, lo natural es pedirle que corra las skills `sdd-init` y
`sdd-configure`. Por debajo, esto es lo que ocurre:

```bash
# 1. Instalar el andamiaje en tu proyecto
python core/sdd_init.py /ruta/a/tu/proyecto --language=python   # o --language=none

# En tu proyecto ya quedaron: CONSTITUTION.md, AGENTS.md, specs/, docs/,
# los gates cableados y el kit vendorizado en tools/sdd/.

# 2. Personalizar (o corré la skill sdd-configure, que es un wizard)
#    Editá .sdd/config.yaml: dominio, tokens prohibidos, capas, principios.

# 3. Generar los artefactos derivados del config y verificar
python tools/sdd/core/render.py               # CONSTITUTION.md + SPEC-000 + CI
python tools/sdd/core/gen_skill_adapters.py   # skills para cada asistente
python tools/sdd/core/pipeline.py             # chequeo completo → VERDE / ROJO
```

Para arrancar una capacidad nueva: la skill `sdd-spec` crea la spec, la registra y
la declara vigente; a partir de ahí el gate te deja tocar el código.

## Cómo está armado

```
core/          Núcleo agnóstico (Python): constitución, trazabilidad, gate,
               generador de skills, pipeline, render, instalador.
adapters/      Validadores de código por lenguaje (python, y el contrato para más).
templates/     Los documentos y el wiring que se copian a tu proyecto.
.agents/skills Fuente única de las skills; se generan las de Claude y opencode.
specs/, docs/  El propio SDD del kit (se usa a sí mismo — dogfooding).
```

## Estado

v0.1.0 — primer release. El kit corre su propio pipeline en verde. Ver
`specs/SPEC-001-agnostic-core.md` e `historial/sdd.md` para el detalle y la deuda
pendiente (adaptadores Node/Go, mapeo estricto FR→test).
