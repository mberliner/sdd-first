// SDD gate para opencode — paridad con el hook PreToolUse de Claude Code.
//
// Intercepta las tools de ESCRITURA (edit, write, multiedit, apply_patch y
// cualquier variante de patch) ANTES de ejecutarse, extrae todas las rutas que
// tocarian y delega la decision en `core/sdd_gate.py` (SSOT
// agnostico de asistente, vendorizado por sdd-init, transporte argv) por cada
// ruta bajo las carpetas de codigo del proyecto. Cuales son NO esta
// hardcodeado (SPEC-015 FR-003): se derivan de `dirs` en .sdd/config.yaml,
// igual que hace el gate. Contrato del gate: exit 0 = permitir, exit 2 =
// bloquear (stderr lleva el motivo). Cualquier otro exit significa que el gate
// NO llego a correr (interprete ausente/roto): es FAIL-CLOSED, se bloquea.
// Backstop universal a posteriori (cubre tools no interceptadas aqui):
// pre-commit + pipeline.
//
// Sin imports de @opencode-ai/plugin: opencode inyecta el runtime y este
// archivo se versiona (a diferencia de node_modules/, ver .opencode/.gitignore).
//
// Wiring del lado Claude: .claude/settings.json + .claude/sdd_gate_hook.sh
// (stdin JSON). Ver docs/SDD-ENFORCEMENT.md.

import fs from "node:fs"
import path from "node:path"

// Ruta del nucleo relativa a la raiz, en partes. `core` lo resuelve
// quien instala este archivo: `tools/sdd/core` en un proyecto derivado,
// `core` en el kit dogfoodeando sobre si mismo (SPEC-005 FR-008). Hardcodear
// uno de los dos dejaba el plugin inerte del otro lado: `gate` no existia y el
// hook salia sin preguntar.
const GATE_REL = ["core", "sdd_gate.py"].flatMap((p) => p.split("/"))

// Tools que pueden escribir archivos. Enganchar por nombre es una allowlist
// (las tools de lectura no deben disparar el gate); pre-commit es la red para
// tools de escritura no contempladas aqui. `includes("patch")` cubre variantes.
const isWriteTool = (tool) => {
  const t = String(tool ?? "").toLowerCase()
  return (
    t === "edit" ||
    t === "write" ||
    t === "multiedit" ||
    t.includes("patch")
  )
}

// Rutas declaradas en un patch estilo Codex (apply_patch): cabeceras
// `*** Add|Update|Delete File: <ruta>` y `*** Move to: <ruta>`.
const PATCH_FILE_RE = /^\*\*\*\s+(?:Add|Update|Delete)\s+File:\s*(.+?)\s*$/gim
const PATCH_MOVE_RE = /^\*\*\*\s+Move to:\s*(.+?)\s*$/gim

// Recolecta todos los valores string de `args` (recursivo) — el texto del patch
// vive en alguno de ellos y no asumimos el nombre del campo (`args` es `any`).
const collectStrings = (val, out) => {
  if (typeof val === "string") out.push(val)
  else if (Array.isArray(val)) val.forEach((v) => collectStrings(v, out))
  else if (val && typeof val === "object")
    Object.values(val).forEach((v) => collectStrings(v, out))
}

// Recolecta valores de claves de ruta conocidas (filePath/file_path/path) en
// cualquier nivel — cubre edit/write sin asumir profundidad del shape.
const collectKeyedPaths = (val, out) => {
  if (Array.isArray(val)) {
    val.forEach((v) => collectKeyedPaths(v, out))
  } else if (val && typeof val === "object") {
    for (const [k, v] of Object.entries(val)) {
      if (typeof v === "string" && /^(filePath|file_path|path)$/.test(k))
        out.push(v)
      else collectKeyedPaths(v, out)
    }
  }
}

// Todas las rutas que la tool tocaria, sin duplicar. La ruta puede llegar en
// `input.args` (shape real del runtime) o `output.args` (lo que sugieren los
// tipos .d.ts); leemos de ambos por robustez ante variaciones de version.
const collectPaths = (input, output) => {
  const args = input?.args ?? output?.args ?? {}
  const paths = new Set()
  const keyed = []
  collectKeyedPaths(args, keyed)
  keyed.forEach((p) => paths.add(p))
  const strings = []
  collectStrings(args, strings)
  for (const s of strings) {
    for (const re of [PATCH_FILE_RE, PATCH_MOVE_RE]) {
      re.lastIndex = 0
      let m
      while ((m = re.exec(s))) paths.add(m[1])
    }
  }
  return [...paths]
}

// Carpetas de codigo fuente segun .sdd/config.yaml. Replica la regla de
// SddConfig.source_roots: `dirs.source_roots` explicito (lista inline o en
// bloque) si esta; si no, el primer componente de cada valor de `dirs:` salvo
// los de tests; si no hay nada, `src`. Parseo minimo a proposito: el plugin se
// versiona sin dependencias (no hay parser YAML disponible) y esto decide *si
// preguntarle al gate*, no *que politica aplicar*. La paridad con el config la
// verifica tests/unit/test_prefilter_source_roots.py.
const unquote = (s) => s.replace(/^["']|["']$/g, "")

export const sourceRoots = (root) => {
  let text
  try {
    text = fs.readFileSync(path.join(root, ".sdd", "config.yaml"), "utf8")
  } catch {
    return ["src"]
  }
  const explicit = []
  const implicit = []
  let inDirs = false
  let inBlock = false
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.replace(/#.*$/, "")
    if (line.trim() === "") continue
    // Una clave sin indentar cierra (o abre) el bloque `dirs:`.
    if (!/^\s/.test(line)) {
      inBlock = false
      inDirs = /^dirs\s*:/.test(line)
      continue
    }
    if (!inDirs) continue
    const item = line.match(/^\s*-\s*(\S+)/)
    if (item) {
      if (inBlock) explicit.push(unquote(item[1]))
      continue
    }
    const kv = line.match(/^\s*([\w-]+)\s*:\s*(.*)$/)
    if (!kv) continue
    inBlock = false
    const key = kv[1]
    const value = kv[2].trim()
    if (key === "source_roots") {
      if (value === "") inBlock = true
      else
        for (const v of value.replace(/^\[/, "").replace(/\]$/, "").split(",")) {
          const t = unquote(v.trim())
          if (t) explicit.push(t)
        }
      continue
    }
    if (key === "tests_unit" || key === "tests_integration") continue
    const top = unquote(value).split("/")[0]
    if (top && !implicit.includes(top)) implicit.push(top)
  }
  const roots = explicit.length ? explicit : implicit
  return roots.length ? roots : ["src"]
}

// ¿La ruta absoluta cae dentro de alguno de los `roots` del proyecto?
const isUnderRoots = (root, roots, abs) => {
  const rel = path.relative(root, abs)
  if (rel.startsWith("..") || path.isAbsolute(rel)) return false
  return roots.some((r) => {
    const norm = r.split("/").join(path.sep)
    return rel === norm || rel.startsWith(norm + path.sep)
  })
}

// Resuelve una ruta de tool a su ABSOLUTA bajo un source root, o null si no
// toca ninguno. Pre-filtro barato (no la politica spec-first, SSOT de
// core/sdd_gate.py) para no depender de Python fuera del codigo.
// Devolver la absoluta es necesario: el gate tambien resuelve contra el root,
// asi que una relativa como `dummy.py` (apply_patch lanzado con cwd dentro del
// codigo) se le escaparia.
//
// Las rutas del patch son relativas al cwd de la tool, que la API de opencode
// NO expone al hook (`tool.execute.before` solo trae tool/sessionID/callID).
// Heuristica: si la relativa no cae en un root contra la raiz pero SI existe al
// resolverla bajo alguno, asumimos que el cwd estaba ahi dentro. Cubre
// edit/move/delete sobre archivos existentes; la *creacion* de un archivo nuevo
// con cwd interno al codigo no es determinista aqui y la cubre pre-commit.
const resolveSourcePath = (root, roots, p) => {
  const direct = path.resolve(root, p)
  if (isUnderRoots(root, roots, direct)) return direct
  if (!path.isAbsolute(p)) {
    for (const r of roots) {
      const under = path.resolve(root, r, p)
      if (isUnderRoots(root, roots, under) && fs.existsSync(under)) return under
    }
  }
  return null
}

export const SddGate = async ({ directory, $ }) => {
  const root = directory
  const gate = path.join(root, ...GATE_REL)
  // Orden de preferencia: venv del proyecto, luego python/python3 del PATH.
  // Los del venv se filtran por existencia; los del PATH se prueban al ejecutar
  // (un exit != 0 y != 2 los descarta y pasa al siguiente).
  const candidates = [
    path.join(root, ".venv", "Scripts", "python.exe"),
    path.join(root, ".venv", "bin", "python"),
    "python3",
    "python",
  ]

  // Corre el gate sobre una ruta. Lanza si el gate bloquea (exit 2) o si ningun
  // interprete logra ejecutarlo (fail-closed). Retorna si el gate permite.
  const runGate = async (filePath) => {
    let lastDetail = "ningun interprete de Python disponible"
    for (const py of candidates) {
      if (path.isAbsolute(py) && !fs.existsSync(py)) continue
      const res = await $`${py} ${gate} ${filePath}`.cwd(root).nothrow().quiet()
      if (res.exitCode === 0) return // el gate corrio y permitio
      if (res.exitCode === 2) {
        const reason = res.stderr.toString().trim()
        throw new Error(
          reason ||
            "sdd-gate: edicion de codigo fuente bloqueada (Principio de gate).",
        )
      }
      // exit != 0 y != 2: el gate no llego a ejecutarse con este interprete.
      lastDetail = `${py} -> exit ${res.exitCode}: ${res.stderr.toString().trim()}`
    }
    throw new Error(
      `sdd-gate: no se pudo ejecutar ${GATE_REL.join("/")}, edicion de ` +
        "codigo fuente bloqueada por seguridad. Crea el .venv del proyecto o " +
        "instala Python en el PATH. Detalle: " +
        lastDetail,
    )
  }

  return {
    "tool.execute.before": async (input, output) => {
      if (!isWriteTool(input?.tool)) return
      if (!fs.existsSync(gate)) return
      // Se releen los roots por invocacion: el config puede cambiar durante la
      // sesion y el costo es una lectura de archivo chica.
      const roots = sourceRoots(root)
      const sourcePaths = new Set()
      for (const p of collectPaths(input, output)) {
        const abs = resolveSourcePath(root, roots, p)
        if (abs) sourcePaths.add(abs)
      }
      for (const p of sourcePaths) await runGate(p)
    },
  }
}
