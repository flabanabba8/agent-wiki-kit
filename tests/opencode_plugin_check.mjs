// Fires the OpenCode plugin's hooks with OpenCode-shaped input, without OpenCode or a model.
// Run by tests/test_agent_sync.py. Prints one JSON object.
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { fileURLToPath, pathToFileURL } from "node:url"
const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
// OpenCode loads the plugin as an ES module under Bun. Node only does that for a bare .js file on
// recent versions, so import a temporary .mjs copy: the test then runs on any Node the CI image has.
const copy = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "agent-wiki-kit-plugin-")), "agent-wiki-kit.mjs")
fs.copyFileSync(path.join(repo, ".opencode/plugins/agent-wiki-kit.js"), copy)
const { AgentWikiKit } = await import(pathToFileURL(copy).href)
const hooks = await AgentWikiKit({ directory: repo, worktree: repo })
const before = hooks["tool.execute.before"]
const blocked = async (tool, args) => {
  try { await before({ tool, sessionID: "s", callID: "c" }, { args }); return false } catch (e) { return String(e.message) }
}
const out = {
  hooks: Object.keys(hooks).sort(),
  editExistingRaw: await blocked("edit", { filePath: path.join(repo, "raw/README.md"), oldString: "a", newString: "b" }),
  writeNewRaw: await blocked("write", { filePath: path.join(repo, "raw/docs/never-existed.md"), content: "x" }),
  patchExistingRaw: await blocked("apply_patch", { patchText: "*** Begin Patch\n*** Update File: raw/README.md\n@@\n-a\n+b\n*** End Patch\n" }),
  patchAddRaw: await blocked("apply_patch", { patchText: "*** Begin Patch\n*** Add File: raw/docs/never-existed.md\n+x\n*** End Patch\n" }),
  editWiki: await blocked("edit", { filePath: path.join(repo, "wiki/index.md"), oldString: "a", newString: "b" }),
  readIsIgnored: await blocked("read", { filePath: path.join(repo, "raw/README.md") }),
}
const sys = { system: [] }
await hooks["experimental.chat.system.transform"]({}, sys)
await hooks["experimental.chat.system.transform"]({}, sys)
out.bannerLines = sys.system.length
out.bannerMentionsDoctor = sys.system.join("\n").includes("doctor")
console.log(JSON.stringify(out))
