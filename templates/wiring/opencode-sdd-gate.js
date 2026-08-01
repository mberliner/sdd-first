// Plugin de opencode: gate spec-first (fail-closed).
// Ejecuta core/sdd_gate.py con las rutas del edit antes de aplicar el tool.
// Prueba intérpretes en orden; si ninguno corre el gate, bloquea (fail-closed).
const { execFileSync } = require("child_process");

const INTERPRETERS = [
  process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python",
  "python",
  "python3",
];

function extractPaths(input) {
  const paths = [];
  if (input && input.file_path) paths.push(input.file_path);
  if (input && input.path) paths.push(input.path);
  // Patches estilo Codex: *** Add|Update|Delete File: <ruta>
  const patch = (input && (input.patch || input.diff)) || "";
  const re = /\*\*\* (?:Add|Update|Delete) File: (.+)/g;
  let m;
  while ((m = re.exec(patch)) !== null) paths.push(m[1].trim());
  return paths;
}

module.exports = {
  "tool.execute.before": async (ctx) => {
    if (!["edit", "write"].includes((ctx.tool || "").toLowerCase())) return;
    const paths = extractPaths(ctx.input);
    if (paths.length === 0) return;
    for (const py of INTERPRETERS) {
      try {
        execFileSync(py, ["tools/sdd/core/sdd_gate.py", ...paths], { stdio: "pipe" });
        return; // exit 0: permite
      } catch (e) {
        if (e.status === 2) {
          throw new Error(String(e.stderr || "gate spec-first: edición bloqueada"));
        }
        // intérprete no encontrado u otro error: probar el siguiente
      }
    }
    throw new Error("sdd-gate: no se pudo ejecutar el gate (fail-closed).");
  },
};
