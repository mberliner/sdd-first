# Playbook: sdd-spec

Deja una spec declarada en `.sdd/current-spec` para desbloquear el gate. Puede
ser una spec **nueva** o una **ya existente**: decidir cuál es el primer paso, no
un detalle. Una capacidad vive en un único documento; multiplicar specs que se
pisan rompe ese invariante y deja la verdad repartida.

## Procedimiento

1. **Leé `specs/SPECS_REGISTRY.md`** y preguntate si la capacidad ya cabe en una
   spec vigente.
2. **Corré el triage**, que compara el título pedido contra los títulos vigentes
   y contra los archivos que cada spec ya gobierna:

   ```
   python tools/sdd/core/sdd_spec.py "<slug>" --title="<Título legible>"
   ```

   Si hay candidatas, aborta y las lista con el motivo. Podés afinar la búsqueda
   nombrando los archivos que vas a tocar, uno por bandera:

   ```
   ... --touches src/domain/pedido.py --touches tests/unit/test_pedido.py
   ```

3. **Proponé al usuario reusar o crear**, nombrando la spec candidata. La
   decisión es suya, no del script: el triage expone el solape, no lo arbitra.
4. Ejecutá `sdd_spec.py` con la bandera que corresponda a esa decisión:

   - **Reusar** — escribí primero el requisito nuevo en la spec adoptada (ver
     abajo dónde) y después:

     ```
     python tools/sdd/core/sdd_spec.py --reuse SPEC-NNN --fr FR-NNN
     ```

     No crea archivo ni fila: solo declara esa spec como vigente. Verifica que
     `FR-NNN` ya esté escrito en ella, y si la spec está `active`, que tenga
     además su fila en el *Coverage mapping* con un test que exista. El test
     puede —y se espera que— fallar: ese es el rojo de TDD, y `sdd_spec.py` no
     ejecuta la suite.

   - **Crear igual** — dejá escrito por qué no cabe en ninguna:

     ```
     python tools/sdd/core/sdd_spec.py "<slug>" --new --rationale="<por qué>"
     ```

   - **Crear enlazada** — cuando la capacidad nueva amplía o reemplaza a una
     vigente, declaralo al crear y el enlace queda escrito en **los dos**
     documentos:

     ```
     python tools/sdd/core/sdd_spec.py "<slug>" --extends SPEC-NNN
     python tools/sdd/core/sdd_spec.py "<slug>" --supersedes SPEC-NNN
     ```

     Ambas banderas son repetibles y combinables. Ver abajo cuándo usar cada una.

5. Si creaste una spec, **completala** según `docs/SPEC-FORMAT.md` (User Story
   con prioridad, FR-NNN con `MUST:`, SC-NNN, Coverage mapping). Es obligatorio:
   el gate exige que la spec declarada tenga requisitos escritos.
6. Opcional pero recomendado: corré la skill `clarify` para cerrar ambigüedades y
   `analyze` para validar adecuación antes de codear.
7. Recién entonces empezá a editar código.

## Dónde escribir el FR nuevo en una spec adoptada

En la **User Story cuyo alcance cubre la capacidad**, con el ID que corresponda a
esa historia (`FR-USk-NNN` en specs multi-historia, `FR-NNN` en las de una sola).
Si ninguna la cubre, agregá una User Story nueva —con su prioridad y su
*Independent Test*— y que el requisito nazca ahí, junto con su fila de *Coverage
mapping* y su test.

Así cada FR sigue perteneciendo a un corte vertical y la spec receptora no se
degrada con cada adopción. La regla la aplica quien escribe: `sdd_spec.py`
verifica que el FR exista, no dónde está.

## Cuándo usar `--extends` y cuándo `--supersedes`

- **`--extends SPEC-NNN`**: la spec nueva **amplía el alcance** de SPEC-NNN sin
  reemplazarla; SPEC-NNN sigue vigente y gobernando lo suyo.
- **`--supersedes SPEC-NNN`**: la spec nueva **reemplaza** a SPEC-NNN.

Ninguna de las dos es "menciono a SPEC-NNN": citar un invariante suyo, compartir
archivos o haberse diseñado al lado no es una relación declarable — va en prosa.
El criterio completo, incluido cuándo corresponde `Depende de:`, vive en
`docs/SPEC-FORMAT.md`.

Dos cosas que `--supersedes` **no** hace al crear:

- No cambia el estado de SPEC-NNN. La spec nueva nace `draft`, y degradar la
  vieja en ese momento dejaría la capacidad sin spec vigente. SPEC-NNN pasa a
  `superseded` **al cerrar la iteración**, junto con el paso de la nueva a
  `active`, actualizando `specs/SPECS_REGISTRY.md`.
- No te deja reemplazar una spec de la que cuelga otra `active`: aborta sin
  escribir nada, porque dejaría a esa otra apoyada en una spec no vigente.

Si la relación aparece **después** —escribiendo los FR descubrís que la spec
depende de otra—, escribí el campo a mano y cerrá el recíproco con
`python tools/sdd/core/sdd_doctor.py --fix`.

## Parámetros del triage

Viven en `specs.triage` de `.sdd/config.yaml`: `stopwords` (las palabras que por
comunes no señalan solape), `min_word_len` y `min_matches`. **Sembrá `stopwords`
con el vocabulario de tu propio dominio**: sin eso, las palabras que aparecen en
todos los títulos marcan candidata a media docena de specs y el aviso se vuelve
ruido que se aprende a ignorar.
