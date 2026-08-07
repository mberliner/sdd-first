# Playbook: sdd-configure

Personaliza `.sdd/config.yaml` (SSOT de parámetros) con un wizard, y regenera los
artefactos derivados.

**Para quién es esto:** quien lo corre puede estar arrancando este proyecto
por primera vez y no conocer el vocabulario de SDD. Antes de preguntar nada,
explicá en una o dos frases qué es `.sdd/config.yaml` (el archivo que decide
cómo se comporta el kit en este proyecto: qué nombres prohíbe, qué capas
existen, qué pasos corre el gate antes de cada commit) y que cada pregunta de
este wizard escribe un valor ahí. Nadie tiene por qué saber de entrada qué es
una "palabra excluida" o un "principio opcional": explicalo en el momento, no
asumas que ya lo sabe.

## Procedimiento

1. Leé el `.sdd/config.yaml` actual (si existe) para partir de sus valores.
2. Preguntá, una por vez (usá `AskUserQuestion` si está disponible), y escribí
   cada respuesta en el config. Antes de cada pregunta, explicá con una frase
   simple qué es ese campo, para qué se usa y qué efecto concreto tiene
   responderlo — no des por sentado que quien contesta conoce el término:
   - **project.name** y **project.domain**: nombre del proyecto y una
     descripción corta de su dominio (a qué se dedica). Se usan para generar
     `CONSTITUTION.md` y los docs derivados con el contexto correcto en vez de
     placeholders genéricos.
   - **project.language** (`python` | `none`): qué lenguaje habla el código
     del proyecto. Determina qué adaptador se instala (el que sabe chequear
     imports, tipos y estilo en ese lenguaje); con `none` el kit sigue
     funcionando pero sin verificación automática de código, solo en code
     review.
   - **naming.prohibited**: una lista de palabras que **no pueden aparecer en
     nombres de funciones, clases o variables** del código (por ejemplo,
     nombres de proveedores concretos como `watson`, `stripe`, o de tecnologías
     de UI/formato). El objetivo es que el código no quede acoplado a una
     herramienta o proveedor específico por el nombre que eligió alguien de
     forma casual — así se puede cambiar de proveedor sin renombrar medio
     proyecto. Se aplica automáticamente en el paso `naming` del pipeline,
     sobre los directorios declarados en `dirs.source_roots`. Confirmá también
     `allowed_identifiers` (excepciones puntuales permitidas) y
     `relax_in_tests` (si la regla se relaja en el código de test).
   - **principles**: los principios son las reglas de fondo que declara
     `CONSTITUTION.md` (por ejemplo, "el código respeta las capas declaradas"
     o "todo cambio tiene una spec"). Partí del núcleo mínimo obligatorio
     (nomenclatura, capas, trazabilidad, gate) y preguntá qué principios
     opcionales agregar — el config los trae comentados, listos para
     descomentar. Si un principio declara un `enforcement` que esta
     instalación no puede ejecutar (por `language: none`, o porque la tool no
     está), decílo al ofrecerlo: se verificará en code review, no
     automáticamente.
   - **layers**: los nombres de las capas de la arquitectura (por ejemplo
     `domain`, `application`, `infrastructure`) y qué capa puede importar a
     cuál. Esto es lo que el paso `layers` del pipeline verifica en cada
     commit para evitar que, por ejemplo, el dominio termine dependiendo de
     detalles de infraestructura.
   - **dirs**: en qué carpeta física vive cada capa y en cuál viven los tests.
     Incluye **`dirs.source_roots`**: las carpetas que el gate protege y que
     los pasos de código (`naming`, `layers`, etc.) efectivamente recorren. Si
     `sdd-init` detectó el layout, confirmalo con el usuario en vez de
     asumirlo; si quedó sin declarar, preguntalo — apuntando a una carpeta
     inexistente el pipeline sale VERDE sin haber mirado nada (falso positivo
     silencioso).
   - **pipeline.steps**: la lista de verificaciones que corren antes de cada
     commit (naming, capas, tests, cobertura, etc.). Cada paso que se activa
     acá es una verificación real que puede bloquear un commit si falla; los
     que no apliquen a este proyecto se dejan afuera.
3. Guardá el config editado (es el SSOT; queda editable a mano después).
4. Regenerá artefactos derivados y verificá:

   ```
   python tools/sdd/core/render.py
   python tools/sdd/core/gen_skill_adapters.py
   python tools/sdd/core/check_constitution.py CONSTITUTION.md
   ```

5. Mostrá un resumen de lo que cambió. No inventes principios ni palabras excluidas: si el
   usuario no sabe, ofrecé los defaults del kit.
