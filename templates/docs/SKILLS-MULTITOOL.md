# Skills multi-asistente — {{project.name}}

> **SSOT de este tema.** Describe cómo una misma skill sirve a varios
> asistentes de IA sin duplicar contenido ni usar symlinks. El *contenido* del
> procedimiento de cada skill vive en `docs/playbooks/`; este documento define
> solo el mecanismo de adaptación.

## El problema

No existe un formato de skill común a todos los asistentes. Lo que sí existe
es una fuerte convergencia:

| Asistente | Carpeta de skills (proyecto) | Formato | Descubrimiento |
|---|---|---|---|
| **Codex** | `.agents/skills/<n>/SKILL.md` | `SKILL.md` · `name` + `description` | automático por `description` |
| **Antigravity** | `.agents/skills/<n>/SKILL.md` | `SKILL.md` · `description` (`name` opcional) | automático por `description` |
| **Claude Code** | `.claude/skills/<n>/SKILL.md` | `SKILL.md` · `name` + `description` + `allowed-tools` | automático por `description` |
| **opencode** | `.opencode/command/<n>.md` | command md · `description` | solo explícito (`/comando`) |

Codex y Antigravity comparten ruta y formato idénticos. Claude usa el mismo
`SKILL.md` en otra carpeta. opencode es el único realmente divergente: usa
commands, sin auto-descubrimiento.

Escribir la skill cuatro veces garantiza que las cuatro copias diverjan. La
alternativa —un solo archivo, tres adaptadores generados— es la que usa este
proyecto.

## Modelo de capas

```
docs/playbooks/<n>.md              ← SSOT del CONTENIDO (a mano, agnóstico de asistente)
.agents/skills/<n>/SKILL.md        ← SSOT del WRAPPER  (a mano) → lo leen Codex y Antigravity directo
        │  {{sdd.core}}/gen_skill_adapters.py
        ├──→ .claude/skills/<n>/SKILL.md     (generado, committeado)
        └──→ .opencode/command/<n>.md        (generado, committeado)
```

Dos lugares editables por skill: el **playbook** (qué hace la skill, paso a
paso) y el **`SKILL.md` fuente** (metadata + cuerpo del wrapper que invoca al
playbook). Todo lo demás son artefactos generados, con cabecera
`NO EDITAR A MANO`.

**Sin symlinks, a propósito.** Se generan archivos reales committeados: los
symlinks de git requieren Developer Mode en Windows y se degradan a archivos
de texto sin él. Las líneas se escriben siempre con `\n` para que el `--check`
sea determinista entre sistemas operativos (ver `.gitattributes`).

## Frontmatter del `SKILL.md` fuente

```yaml
---
name: analyze                      # id de la skill
description: <largo>               # lo usa el auto-descubrimiento (Claude/Codex/Antigravity)
allowed-tools: Read, Grep, Glob    # solo lo usa Claude; los demás lo ignoran
opencode-description: <corto>      # solo para el command de opencode (opcional)
opencode-constraint: <línea>       # restricción que se anexa al command (opcional)
---
```

Los campos `opencode-*` alimentan únicamente al generador: nunca se filtran al
`SKILL.md` de Claude. El playbook se referencia por convención,
`docs/playbooks/<name>.md`.

## Generador

```bash
python {{sdd.core}}/gen_skill_adapters.py            # regenera los adaptadores
python {{sdd.core}}/gen_skill_adapters.py --check    # falla si hay drift
```

El `--check` es el paso `skills` del pipeline: si alguien edita a mano un
archivo generado, o edita la fuente y olvida regenerar, el pipeline sale ROJO.

## Agregar una skill nueva

1. Escribí el procedimiento en `docs/playbooks/<nombre>.md` (agnóstico de
   asistente: nada de "usá la tool X de Claude").
2. Creá `.agents/skills/<nombre>/SKILL.md` con el frontmatter de arriba y un
   cuerpo que apunte al playbook.
3. Regenerá los adaptadores y verificá con `--check`.
4. Commiteá las tres cosas juntas: fuente, playbook y generados.
