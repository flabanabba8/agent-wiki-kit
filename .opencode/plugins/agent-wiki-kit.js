// OpenCode adapter for the agent-wiki-kit wiki. Loaded automatically from .opencode/plugins/.
//
// Claude Code enforces this repo's rules with hooks in .claude/settings.json. This plugin applies
// the same rules in OpenCode by calling the same scripts through scripts/agents/adapter.py:
//   - an existing file under raw/ is never edited (new raw files are fine, so this cannot be a
//     declarative permission.edit rule: that would block ingest from creating sources);
//   - a webfetch that came back empty, blocked or as a JavaScript shell is re-rendered in
//     Camoufox, and the tool result gains a line saying where the real text was saved;
//   - the first message of a session carries the harness health line;
//   - editing a wiki page without a wiki/log.md entry earns one reminder per session.
// Every hook except the raw guard swallows its own errors: a broken adapter must never break a tool.
import { spawnSync } from "node:child_process"
import path from "node:path"

const WRITE_TOOLS = new Set(["edit", "write", "apply_patch"])

export const AgentWikiKit = async ({ directory, worktree }) => {
  const root = worktree || directory
  const adapter = path.join(root, "scripts", "agents", "adapter.py")

  const run = (mode, payload, timeoutMs) => {
    const r = spawnSync("python3", [adapter, mode], {
      input: JSON.stringify({ cwd: directory, ...payload }),
      encoding: "utf8",
      timeout: timeoutMs,
    })
    return { code: r.status, out: (r.stdout || "").trim(), err: (r.stderr || "").trim() }
  }

  let bannerShown = false
  let remindedAboutLog = false

  return {
    "tool.execute.before": async (input, output) => {
      if (!WRITE_TOOLS.has(input.tool)) return
      const r = run("guard", { args: output.args }, 10_000)
      if (r.code === 2) throw new Error(r.err || "BLOCKED: existing raw/ source.")
    },

    "tool.execute.after": async (input, output) => {
      try {
        if (input.tool === "webfetch") {
          const r = run("fetch-notice", { args: input.args, result: output.output, tool: "webfetch" }, 175_000)
          if (r.out) output.output = `${output.output}\n\n${r.out}`
        } else if (WRITE_TOOLS.has(input.tool) && !remindedAboutLog) {
          const r = run("log-reminder", {}, 10_000)
          if (r.out) {
            remindedAboutLog = true
            output.output = `${output.output}\n\n${r.out}`
          }
        }
      } catch {}
    },

    "experimental.chat.system.transform": async (_input, output) => {
      try {
        if (bannerShown) return
        bannerShown = true
        const r = run("banner", {}, 30_000)
        if (r.out && Array.isArray(output.system)) output.system.push(r.out)
      } catch {}
    },
  }
}
