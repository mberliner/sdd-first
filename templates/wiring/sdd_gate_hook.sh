#!/bin/sh
# Transporte stdin del SDD gate para Claude Code (hook PreToolUse Edit|Write).
#
# Resuelve un interprete Python y delega la decision en
# tools/sdd/core/sdd_gate.py (SSOT agnostico de asistente, vendorizado por
# sdd-init). Contrato: exit 0 = permitir, exit 2 = bloquear (stderr lleva el
# motivo).
#
# FAIL-CLOSED: si ningun interprete logra correr el gate, se BLOQUEA la
# edicion bajo src/ (el layout de referencia — ajusta el patron `case` mas
# abajo si tu proyecto usa otra carpeta como source_roots en
# .sdd/config.yaml) en vez de permitirla en silencio. Fuera de esa ruta se
# permite, para que un checkout sin Python siga siendo reparable.
#
# Portabilidad: POSIX sh sin bashismos y sin comandos externos (solo builtins:
# `command -v`, `case`, `printf`) — corre igual en Linux/macOS y en Git Bash/WSL
# sobre Windows, y la rama fail-closed no puede caerse por un PATH roto.
# NO usa `where` (comando de Windows, inexistente en Linux) y prueba `python3`
# antes que `python`: hay entornos sin `python` en PATH.
#
# Ver docs/SDD-ENFORCEMENT.md. Wiring: .claude/settings.json.

# Buffer del payload con `read` (builtin) en vez de `cat`: hay que inspeccionarlo
# y reenviarlo, y ni siquiera un PATH roto debe poder tumbar la rama fail-closed.
# JSON no admite saltos de linea crudos dentro de strings, asi que reensamblar
# por lineas es fiel.
INPUT=""
while IFS= read -r _line || [ -n "$_line" ]; do
  INPUT="$INPUT$_line
"
done
ROOT="${CLAUDE_PROJECT_DIR:-.}"

# 1) .venv del proyecto (Windows y POSIX), 2) python3, 3) python.
PYBIN="$ROOT/.venv/Scripts/python.exe"
[ -x "$PYBIN" ] || PYBIN="$ROOT/.venv/bin/python"
for _cmd in python3 python; do
  [ -x "$PYBIN" ] && break
  PYBIN="$(command -v "$_cmd" 2>/dev/null)" || PYBIN=""
  # El alias stub de la Microsoft Store aparece en PATH pero no ejecuta nada.
  case "$PYBIN" in *WindowsApps*) PYBIN="" ;; esac
done
# Ultimo filtro: que el candidato realmente ejecute.
[ -n "$PYBIN" ] && "$PYBIN" -c "" >/dev/null 2>&1 || PYBIN=""

if [ -z "$PYBIN" ]; then
  case "$INPUT" in
    *'"src/'* | */src/*)
      echo "sdd-gate: no se encontro un interprete Python capaz de correr tools/sdd/core/sdd_gate.py." >&2
      echo "Se BLOQUEA la edicion bajo src/ (fail-closed). Crea el .venv del proyecto o instala python3." >&2
      exit 2
      ;;
  esac
  exit 0
fi

printf '%s' "$INPUT" | "$PYBIN" "$ROOT/tools/sdd/core/sdd_gate.py"
