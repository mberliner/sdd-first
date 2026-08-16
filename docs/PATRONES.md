# Patrones recurrentes de defecto — sdd-first

> SSOT de las **clases de defecto que ya se repitieron** en este kit, destiladas
> de los post-mortems de [`IDEAS-CERRADAS.md`](IDEAS-CERRADAS.md). Cada patrón
> cita los ítems que lo evidencian y **no reproduce su razonamiento**: el detalle
> vive en el ítem.
>
> Para qué sirve: es lo que conviene leer antes de escribir una spec o de dar por
> cerrada una iteración. Casi todos estos patrones se descubrieron *dos o tres
> veces* antes de tener nombre, y varios ítems abiertos de [`IDEAS.md`](IDEAS.md)
> son instancias todavía sin pagar.

## 1 · El mecanismo correcto que los casos nuevos no adoptan

Arreglar el sitio no arregla la clase. Un helper, un placeholder o una
convención correcta no se propagan solos: el archivo número siete nace roto
igual que el primero. **Lo que sostiene el fix no es el mecanismo, es un test que
barre la superficie entera y falla nombrando al que se olvidó.**

Evidencia: C-2 (2 de 15 entrypoints; lo sostiene `test_salida_utf8.py`) ·
E-6/F-5 (ocho plantillas, no una; barrido parametrizado de `templates/`) ·
R-4 (la lista de destinos se deriva de `sdd_catalog.WIRING`, con test que falla
si aparece un destino nuevo) · G-8 (las specs en rojo se migran en la misma
iteración, sin lista de exenciones).

## 2 · La lista duplicada que nada ata

Dos enumeraciones del mismo hecho divergen en la primera edición, y el drift no
lo detecta nadie hasta que cuesta. Es el Principio IV en su forma más barata de
violar. El fix nunca es "acordarse de tocar las dos": es **derivar una de la
otra**, o atarlas con un test de paridad.

Evidencia: R-1 · R-2 · R-3 · R-4 (el wiring del kit era copia manual de su
plantilla) · C-8 (`CODE_STEPS` y el dispatcher del adaptador) · F-2 (el proyecto
de referencia sí duplicó su pipeline, y sus dos copias ya divergieron).

## 3 · El aviso que suena siempre enseña que el verde no significa nada

Un paso que se omite con aviso en cada corrida, o una advertencia perpetua,
degrada a ruido y con él degrada la señal del VERDE entero. Si algo importa,
tiene que poder fallar; si no puede fallar, no debería hablar en cada corrida.

Evidencia: U-3 (VERDE 8/8 con 4 pasos que no verificaron nada) · C-1 (paso
desconocido contado como OK) · K-5 (`coverage` sembrado sin umbrales, o sea
inerte) · X-8 (el primer VERDE de todo derivado se emitía con el 100% de sus
principios sin enforzar). T-1 lo usa como precedente para descartar el aviso
perpetuo de lote sobredimensionado.

## 4 · La carpeta que existe y ningún paso mira

Una clave de config declarada, una carpeta presente, un artefacto instalado —
y ningún paso del pipeline que los visite. No falla: **calla**. Y el silencio se
lee como salud.

Evidencia: V-1 (`tests_integration` era clave de primera clase y no la ejecutaba
ningún paso) · V-4 (la raíz de `tests/`, fuera de `naming`/`lint`/`format`) ·
K-1 (el derivado nacía sin el paso `render`, así que nada vigilaba su drift).
De ahí salió el aviso de `sdd-doctor` cuando una carpeta declarada no la corre
ningún paso.

## 5 · Validar existencia en vez de contenido

Chequear que un archivo *esté* es barato y casi siempre insuficiente: el archivo
está y dice otra cosa. Todo check que se conforme con `exists()` es un check que
va a reportar salud sobre algo roto.

Evidencia: G-4 (`sdd-doctor` daba por cableado un `.pre-commit-config.yaml` con
solo `ruff`) · G-8 (el archivo de test existía sin nombrar el FR que decía
cubrir) · K-1/FR-008 (auditar el `.gitignore` por contenido, no por existencia).
Abierto: X-6 — el Coverage mapping sigue mapeando archivos, no casos.

## 6 · La garantía unitaria que se evapora de punta a punta

El test de unidad afirma el contenido de la función; el flujo real mete de por
medio un `git commit`, un `pre-commit` que descarta stdout, un venv sin
dependencias o un subproceso. **Lo que no se prueba por la ruta real, no está
probado.**

Evidencia: G-9 (el test miraba el archivo tras `sdd_reset.main()`, nunca el ciclo
con `git commit`; pasó dos rondas sin detectarse) · V-2 (el aviso de bypass lo
comía `pre-commit`) · K-3 (la suite cubría helpers y nunca los `main()`, que son
los que corren en un proyecto instalado) · G-9/FR-009 (el fix solo estaba probado
por unidad interna hasta que se sumó un escenario e2e con `sdd_init.py` real).

## 7 · Medir antes de cablear, y poner el trinquete en el piso real

Un umbral que no se calibró contra el dato no protege nada, y uno importado de
otro contexto protege menos todavía. El método de la casa es: medís tu piso real,
lo escribís como trinquete, y solo sube.

Evidencia: K-3 (umbral 50 contra un real de 75: 25 puntos de aire) · F-7
(*superseded* justamente por conformarse con "fijar el piso") · K-5 (medir el
piso del proyecto en vez de dejar la clave comentada) · X-6 ("medir antes de
cablear", literal). Abierto: T-1 (c), que se sorprende a sí mismo proponiendo un
umbral no supervisado presentado como empírico.

## 8 · El fix fácil que mueve el blanco

El arreglo obvio suele desplazar el criterio que otra cosa ya usaba, y rompe en
silencio a un tercero que no estaba en la conversación.

Evidencia: B-2 (relajación en tests atada al *basename*) · V-4 (mover el blanco
de `tests/unit` a `tests/` volvía a mover ese mismo basename, y destapó que
`_is_test_root` miraba la relación en una sola dirección) · C-4 (el kit tenía dos
criterios de normalización de texto y el defecto estaba en el que no la hacía).
