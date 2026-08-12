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

Todo se parametriza en `.sdd/config.yaml` (nombre, dominio, palabras excluidas
de la nomenclatura, capas, principios, pasos del pipeline). No hay listas
escondidas en el código.

## El kit es desechable

Una vez instalado, **tu proyecto se sostiene solo**: no necesitás este repo para
nada del día a día. `sdd-init` no deja un enlace ni una dependencia — copia el
andamiaje dentro de tu proyecto (`tools/sdd/`), resuelve las plantillas y genera
las skills ahí mismo. El pipeline, el gate, las skills de tu asistente y la
documentación corren contra esa copia, con las rutas de tu proyecto.

Eso es deliberado, y define qué es este kit: **una herramienta de bootstrap, no
un framework del que quedás colgado.** Podés borrar el clon después de instalar.
La única razón para volver es traer una versión nueva del andamiaje a un proyecto
ya instalado: `python core/sdd_update.py <ruta-del-proyecto>` desde este clon
muestra el plan (nada se escribe sin `--apply`) y nunca pisa una plantilla que
editaste — la reporta como conflicto y deja la versión nueva en
`<archivo>.kit-new` para fusionar a mano. Detalle completo en
`docs/playbooks/sdd-update.md` y en `CHANGELOG.md` (qué trae cada versión).

Corolario para quien contribuye al kit: todo lo que el usuario del proyecto
derivado vaya a necesitar tiene que **viajar con la instalación**. Un documento,
un ejemplo o un comando que solo exista en este repo es un hueco, no una
referencia.

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

El kit no se instala como paquete: se clona una vez y se usa para **sembrar** el
andamiaje dentro de tu proyecto. Los comandos siguientes son la secuencia
completa, en orden, desde cero.

### 1. Obtener el kit e instalar su única dependencia

```bash
git clone https://github.com/mberliner/sdd-first.git
cd sdd-first
pip install pyyaml
```

`pyyaml` es obligatorio desde el primer comando: el instalador lee
`.sdd/config.yaml` y aborta con un mensaje explícito si falta.

### 2. Sembrar el andamiaje en tu proyecto

```bash
python core/sdd_init.py /ruta/a/mi-proyecto --language=python
```

`--language` acepta `python` (default) o `none` (solo gobernanza y specs, sin
validar código). El directorio destino se crea si no existe, y la instalación es
idempotente: no pisa archivos tuyos salvo que pases `--force`.

En tu proyecto quedaron `CONSTITUTION.md`, `AGENTS.md`, `specs/`, `docs/`, los
gates cableados, el kit **vendorizado** en `tools/sdd/` y —ya generadas para cada
asistente— las skills del paso siguiente. A partir de acá el clon del kit es
descartable: tu proyecto ya tiene su propia copia del andamiaje.

### 3. Configurar el proyecto con la skill `sdd-configure`

`sdd-init` deja instaladas cinco skills, disponibles en tu asistente apenas
termina la instalación — no hay ningún paso extra para habilitarlas:

| Skill | Para qué |
|---|---|
| **`sdd-configure`** | Wizard sobre `.sdd/config.yaml`: dominio, lenguaje, principios, palabras excluidas, capas y carpetas de código. **Es el primer paso.** |
| `sdd-spec` | Crea la spec, la registra y la declara vigente. Antes de codear cualquier capacidad nueva. |
| `clarify` | Cierra ambigüedades de una spec con hasta 5 preguntas dirigidas. |
| `analyze` | Valida (read-only) que la spec sea sólida contra tests, registro y constitución. |
| `sdd-doctor` | Diagnostica la salud de la instalación; autorepara con `--fix`. |

Abrí tu asistente en el proyecto y pedile **`sdd-configure`**. El wizard pregunta
y escribe el config por vos, y regenera los artefactos derivados. El catálogo
completo queda instalado en `docs/SDD-OPERACION.md`.

Si preferís hacerlo a mano, editá `.sdd/config.yaml` directamente. Dos claves
merecen atención especial:

- **`dirs.source_roots`** es lo que hace que el gate proteja tu código y que los
  pasos de código lo miren. Si apunta a una carpeta que no existe, el pipeline
  sale VERDE sin haber verificado nada. `sdd-init` intenta detectarlo y te dice
  qué encontró — confirmalo antes de seguir.
- **`naming.prohibited`** son fragmentos de identificadores de código (clases,
  funciones, variables, módulos) vetados por acoplar el núcleo a un proveedor,
  framework o tecnología concreta; ver `specs/SPEC-000-naming.md`.

### 4. Verificar — desde tu proyecto

Los comandos que siguen corren en el **proyecto destino**, no en el clon del kit;
por eso la ruta es `tools/sdd/core/…`:

```bash
cd /ruta/a/mi-proyecto
git init                    # si todavía no es repo (ver nota abajo)
pip install pre-commit      # para que el paso `hooks` pueda cablear la capa git

python tools/sdd/core/render.py     # CONSTITUTION.md + SPEC-000 + CI
python tools/sdd/core/pipeline.py   # chequeo completo → VERDE / ROJO
```

(`sdd-configure` ya corre `render.py` por vos; el comando queda a mano para
cuando edites el config directamente.)

> **Sobre la capa git:** el paso `hooks` del pipeline instala los hooks de
> `pre-commit` (gate en el commit, reset post-commit), pero necesita que el
> destino sea un repo git y que `pre-commit` esté instalado. Si falta alguna de
> las dos, el paso avisa y sigue: el gate spec-first del asistente funciona igual
> —sin git— por diseño, pero el bloqueo en el commit queda inactivo.

### 5. Primera spec, y recién ahí, código

El gate spec-first bloquea las ediciones de código mientras `.sdd/current-spec`
esté vacío. Antes de codear, pedile a tu asistente la skill `sdd-spec` (o corré
`python tools/sdd/core/sdd_spec.py "<slug>" --title="<Título>"`): crea la spec,
la registra y la declara vigente. Lo mismo vale para cada capacidad nueva.

> **Nota sobre las skills:** `sdd-init` es bootstrap de una sola vez y **no** se
> instala en el proyecto derivado — se corre desde el clon del kit, como en el
> paso 2. Las cinco del paso 3 sí quedan instaladas, en los cuatro formatos
> (`.agents/skills/` para Codex y Antigravity, `.claude/skills/` para Claude Code,
> `.opencode/command/` para opencode). Sólo si agregás o editás una skill hace
> falta regenerar los adaptadores con
> `python tools/sdd/core/gen_skill_adapters.py` — ver `docs/SKILLS-MULTITOOL.md`.

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
