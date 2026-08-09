#!/bin/sh
# Transporte stdin del SDD gate para Claude Code (hook PreToolUse de las tools
# de edicion: Edit|Write|MultiEdit|NotebookEdit).
#
# Resuelve un interprete Python y delega la decision en core/sdd_gate.py
# (SSOT agnostico de asistente). Copia del kit dogfoodeando su propio wiring:
# identica a templates/wiring/sdd_gate_hook.sh salvo que aca el andamiaje vive
# en core/ y no vendorizado en core/. Contrato: exit 0 = permitir,
# exit 2 = bloquear (stderr lleva el motivo).
#
# FAIL-CLOSED: si ningun interprete logra correr el gate, se BLOQUEA la edicion
# bajo las carpetas de codigo del proyecto, en vez de permitirla en silencio.
# Fuera de esas rutas se permite, para que un checkout sin Python siga siendo
# reparable. Cuales son esas carpetas NO esta hardcodeado (SPEC-015 FR-002): se
# derivan de `dirs` en .sdd/config.yaml, igual que hace el gate. Este pre-filtro
# decide *si preguntar*, no *que politica aplicar* (SSOT: sdd_gate.decide).
#
# Portabilidad: POSIX sh sin bashismos y sin comandos externos (solo builtins:
# `command -v`, `case`, `printf`, `read`, `set`) — corre igual en Linux/macOS y
# en Git Bash/WSL sobre Windows, y la rama fail-closed no puede caerse por un
# PATH roto. NO usa `where` (comando de Windows, inexistente en Linux) y prueba
# `python3` antes que `python`: hay entornos sin `python` en PATH.
#
# Ver docs/SDD-ENFORCEMENT.md. Wiring: .claude/settings.json.

# Quita las comillas envolventes de un escalar YAML (`domain: "src/x"`) y deja
# el resultado en _v. Sin `$(...)`: seria un subshell mas en la rama fail-closed.
_sdd_unquote() {
  _v="$1"
  _v="${_v#\"}"
  _v="${_v%\"}"
  _v="${_v#\'}"
  _v="${_v%\'}"
}

# Carpetas de codigo fuente segun .sdd/config.yaml, separadas por espacios.
# Replica la regla de SddConfig.source_roots: `dirs.source_roots` explicito
# (lista inline o en bloque) si esta; si no, el primer componente de cada valor
# de `dirs:` salvo los de tests; si no hay nada, `src`. La paridad con el config
# la verifica tests/unit/test_prefilter_source_roots.py.
sdd_source_roots() {
  _cfg="$1/.sdd/config.yaml"
  _explicit=""
  _implicit=""
  _in_dirs=0
  _in_sr=0
  if [ ! -f "$_cfg" ]; then
    printf 'src'
    return 0
  fi
  # `set -f`: el word splitting de `set -- $_l` no debe expandir globs del YAML.
  set -f
  while IFS= read -r _l || [ -n "$_l" ]; do
    # CR final de un config con CRLF (habitual en Windows): sin esto el ultimo
    # token de cada linea queda con el \r pegado y ningun root matchea. Se usa
    # la clase POSIX en vez de un CR literal o `$(printf '\r')` para no meter
    # un byte invisible ni un subshell en la rama fail-closed.
    _l="${_l%[[:cntrl:]]}"
    _l="${_l%%#*}"
    # Una clave sin indentar cierra (o abre) el bloque `dirs:`. YAML prohibe
    # tabs para indentar, asi que alcanza con mirar el espacio inicial.
    case "$_l" in
      "" | " "*) ;;
      *)
        _in_sr=0
        case "$_l" in
          dirs:*) _in_dirs=1 ;;
          *) _in_dirs=0 ;;
        esac
        continue
        ;;
    esac
    [ "$_in_dirs" = 1 ] || continue
    set -- $_l
    [ $# -gt 0 ] || continue
    # Item de la lista en bloque de `source_roots:`.
    if [ "$1" = "-" ]; then
      if [ "$_in_sr" = 1 ] && [ -n "$2" ]; then
        _sdd_unquote "$2"
        _explicit="$_explicit $_v"
      fi
      continue
    fi
    _in_sr=0
    case "$1" in
      source_roots:)
        shift
        if [ $# -eq 0 ]; then
          _in_sr=1
        else
          for _v in "$@"; do
            _v="${_v#"["}"
            _v="${_v%"]"}"
            _v="${_v%,}"
            _sdd_unquote "$_v"
            [ -n "$_v" ] && _explicit="$_explicit $_v"
          done
        fi
        ;;
      tests_unit: | tests_integration:) ;;
      *:)
        _v="${2%%/*}"
        _sdd_unquote "$_v"
        if [ -n "$_v" ]; then
          # Dedup: varias capas pueden colgar del mismo root (src/domain, src/ui).
          case " $_implicit " in
            *" $_v "*) ;;
            *) _implicit="$_implicit $_v" ;;
          esac
        fi
        ;;
    esac
  done < "$_cfg"
  set +f
  if [ -n "$_explicit" ]; then
    printf '%s' "${_explicit# }"
  elif [ -n "$_implicit" ]; then
    printf '%s' "${_implicit# }"
  else
    printf 'src'
  fi
}

# Modo introspeccion: `sh sdd_gate_hook.sh --source-roots [raiz]` imprime los
# roots derivados y sale. Lo usa el test de paridad; tambien sirve para
# diagnosticar por que el fail-closed bloquea (o no) una ruta.
if [ "$1" = "--source-roots" ]; then
  sdd_source_roots "${2:-${CLAUDE_PROJECT_DIR:-.}}"
  exit 0
fi

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
  for _root in $(sdd_source_roots "$ROOT"); do
    case "$INPUT" in
      *"\"$_root/"* | *"/$_root/"*)
        case "${SDD_GATE_BYPASS:-}" in
          *[![:space:]]*)
            echo "sdd-gate fail-closed bypass activo - se permite igual. Motivo: $SDD_GATE_BYPASS" >&2
            exit 0
            ;;
        esac
        echo "sdd-gate: no se encontro un interprete Python capaz de correr core/sdd_gate.py." >&2
        echo "Se BLOQUEA la edicion bajo $_root/ (fail-closed). Crea el .venv del proyecto o instala python3." >&2
        exit 2
        ;;
    esac
  done
  exit 0
fi

printf '%s' "$INPUT" | "$PYBIN" "$ROOT/core/sdd_gate.py"
