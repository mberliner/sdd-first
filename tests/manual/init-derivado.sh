#!/bin/bash

set -e

if [ -z "$1" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  echo "Uso: $0 <ruta-o-nombre-del-proyecto-derivado>"
  echo ""
  echo "Inicia un proyecto derivado SDD para pruebas manuales."
  echo "Parámetros:"
  echo "  <ruta-o-nombre>   Ruta destino donde se creará el proyecto."
  echo "                    (Si envías solo un nombre, se creará en el directorio actual)."
  echo "  -h, --help        Muestra este mensaje de ayuda."
  exit 1
fi

if [[ "$1" == *"/"* ]] || [[ "$1" == *"\\"* ]]; then
    TARGET_DIR="$1"
else
    if [ -n "$TMPDIR" ]; then
        BASE_DIR="$TMPDIR"
    else
        BASE_DIR="/tmp"
    fi
    TARGET_DIR="${BASE_DIR}/$1"
fi

PROJECT_NAME="$(basename "$TARGET_DIR")"
LANGUAGE="python"
KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=========================================================="
echo " Iniciando proyecto derivado '${PROJECT_NAME}'"
echo " Directorio destino: ${TARGET_DIR}"
echo " Lenguaje: ${LANGUAGE}"
echo "=========================================================="

# 1. Correr sdd-init
python "${KIT_ROOT}/core/sdd_init.py" "${TARGET_DIR}" --language="${LANGUAGE}"

# 2. Ir al derivado
cd "${TARGET_DIR}"

# Iniciar git si no existe, recomendado por sdd-init
if [ ! -d ".git" ]; then
    git init
fi

# 3. Llamar al cliente de IA con sdd-configure
echo "=========================================================="
echo " Llamando a 'agy' para ejecutar sdd-configure de forma automática..."
echo " Por favor espera... (Esto tarda ~60 segundos y no mostrará salida hasta el final)."
echo "=========================================================="

agy --dangerously-skip-permissions --add-dir "${TARGET_DIR}" --print "Ejecuta la skill sdd-configure para configurar este proyecto. Asume los siguientes valores por defecto en tu primera ejecución:
- project.name: '${PROJECT_NAME}'
- project.domain: 'Proyecto de prueba rápida generado automáticamente'
- project.language: '${LANGUAGE}'
- naming.prohibited: [] (ninguna palabra excluida adicional)
- principles: acepta los recomendados por defecto.
- dirs.source_roots: ['src']
- dirs.tests_unit: 'tests/unit'
- pipeline.steps: los recomendados.
Guarda los cambios en .sdd/config.yaml, y regenera los artefactos derivados ejecutando:
1. python tools/sdd/core/render.py
2. python tools/sdd/core/gen_skill_adapters.py
3. python tools/sdd/core/check_constitution.py CONSTITUTION.md"
