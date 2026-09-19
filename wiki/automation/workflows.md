---
title: Dynamic Workflows
type: how-to
tldr: "Script-orchestrated subagents at scale"
sources:
  - raw/docs/official/workflows.md
  - raw/docs/official/agents.md
  - raw/docs/changelog-2.1.275-to-2.1.278.md
related: ["[[subagents]]", "[[agent-teams]]", "[[skills]]", "[[models-and-effort]]", "[[costs-and-usage]]", "[[worktrees-and-background-work]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [dynamic-workflows, workflow-tool, ultracode, deep-research, orchestrate-subagents]
valid_until: 2027-03-15
---

# Dynamic Workflows

A **dynamic workflow** is a JavaScript script that orchestrates many [[subagents]]. Claude writes the script for your task, and a runtime runs it in the background while your session stays responsive. Workflows are available on all paid plans, with Anthropic API access, and on Bedrock, Google Cloud's Agent Platform and Microsoft Foundry. On Pro, turn them on from the Dynamic workflows row in `/config`.

## When to use one

What sets a workflow apart is who holds the plan.

| | Subagents | [[skills]] | [[agent-teams]] | Workflows |
|---|---|---|---|---|
| Who decides what runs next | Claude, turn by turn | Claude, following the prompt | Lead agent | The script |
| Where intermediate results live | Claude's context | Claude's context | Shared task list | Script variables |
| Scale | A few tasks per turn | Same as subagents | A handful of peers | Dozens to hundreds of agents per run |
| On interruption | Restarts the turn | Restarts the turn | Teammates keep running | Resumable in the same session |

A workflow fits a codebase-wide bug sweep, a 500-file migration, research whose sources need cross-checking, or a plan drafted from several angles. Because the script holds the loop, only the final answer lands in Claude's context. The script can also apply a quality pattern, such as having agents adversarially verify each other's findings.

## Run one

**Bundled:** `/deep-research <question>` fans out web searches, cross-checks sources, votes on each claim and returns a cited report. It needs the WebSearch tool. Claims the verifiers couldn't check are marked unverified.

**Ask Claude to write one**, in either of these ways:
- Put the keyword `ultracode` in your prompt, or say "use a workflow":
  ```text
  ultracode: audit every API endpoint under src/routes/ for missing auth checks
  ```
  The keyword works only in prompts you type yourself. It does nothing in a `-p` prompt, a scheduled task, a webhook payload, or a relayed PR comment. Dismiss the highlight with `Option+W` (macOS) or `Alt+W`, or turn off "Ultracode keyword trigger" in `/config`.
- Turn on **ultracode** for the whole session with `/effort ultracode` or `claude --effort ultracode`. It combines `xhigh` effort with automatic workflow planning for every substantive task. That uses more tokens and time per request. Go back with `/effort high`. The `ultracode` setting makes it the default for new sessions (see [[models-and-effort]]).

Example prompt shapes: "use a workflow to run npx tsc --noEmit and keep fixing until the type check passes or two rounds make no progress", or "…migrate every component under src/components/ to TypeScript, each file in its own isolated copy".

## Approval

In the CLI, a prompt shows the planned phases with these options: **Yes, run it**, **Yes, and don't ask again for `<name>` in `<path>`** (only for named bundled, saved or plugin workflows), **View raw script**, or **No**. `Ctrl+G` opens the script in your editor.

| Permission mode | When you are prompted |
|---|---|
| Auto | First launch only. Never when ultracode is on |
| Manual, accept edits | Every run, unless you chose "don't ask again" |
| Bypass permissions | Never |
| `claude -p`, Agent SDK | Never shown. The Workflow tool call goes through normal permission evaluation |

In `-p` and the SDK, a workflow can start through an allow rule (`Workflow` or `Workflow(<name>)`), auto mode's classifier, bypass mode, a `PreToolUse` hook returning `allow`, or a host approval (`--permission-prompt-tool`, `canUseTool`, or a `PermissionRequest` hook). The spawned agents use your permission rules, so add the tools they need to your allow rules before a long run (see [[permissions-and-modes]]).

## Watch and manage runs

Run `/workflows` to list runs and open one's progress view. You can also expand the run's line in the task panel below the input.

| Key | Action |
|---|---|
| `↑`/`↓`, `Enter`/`→`, `Esc`/`←` | Navigate phases → agents → detail |
| `f` | Filter agents by status |
| `p` | Pause or resume the run |
| `x` | Stop the selected agent, or the whole run |
| `r` | Restart the selected running agent |
| `s` | Save the run's script as a command |

**Resume semantics.** Resume a paused run with `p`. For a stopped run, ask Claude to relaunch it. On replay, completed agents return their cached results until the first agent whose prompt differs, and that agent and every later one run again. Agents that were running start over. A failed agent reruns along with every agent started after it, so a failure mid-fan-out reruns finished work. Stopping a single agent with `x` counts as a failure.

What happens when you leave the session:
- Backgrounding with `/bg` replays and continues the run in the background session.
- On exit with agent view on, `Move to background and exit` carries the run over.
- A session you reopen with `claude --resume` can replay saved results if you ask Claude to relaunch.

**Usage limits.** In an interactive claude.ai-subscription session with `autoContinueAtUsageLimit` on, the run pauses at a usage limit that resets within 24 hours and continues after the reset, up to two waits per run. In `-p`, SDK or background sessions, the affected agents fail instead.

## Save and reuse

In `/workflows`, select a run and press `s`, then choose where to save:
- `.claude/workflows/` in the project, shared with the repository. In a monorepo it uses the closest existing `.claude/workflows/`.
- `~/.claude/workflows/`, personal to you.

The workflow then runs as `/<name>`. If the same name exists in both places, the project one wins. To distribute a workflow, put it in a plugin's `workflows/` directory (see [[plugins]]). It is namespaced as `/<plugin>:<name>`.

Pass input in natural language ("Run /triage-issues on issues 1024, 1025, and 1030"). The script receives it as the `args` global, already structured.

## Script shape

```javascript
export const meta = {
  name: 'audit-routes',
  description: 'Audit every route handler for missing auth checks',
}

const found = await agent('List every .ts file under src/routes/.', {
  schema: { type: 'object', required: ['files'], properties: { files: { type: 'array', items: { type: 'string' } } } },
})

const audits = await pipeline(found.files, file =>
  agent(`Audit ${file} for missing authentication checks.`, { label: file }),
)

return audits.filter(Boolean)
```

- `agent()` spawns one subagent, `pipeline()` runs one per item, and `parallel()` runs a set of tasks at once. `phase()` groups agents under a title in the progress view, and `log()` prints a message above the phases.
- `agent()` resolves to `null` when stopped, when it hits an unrecoverable API error, or when auto mode's classifier blocks it. That is why the example ends with `.filter(Boolean)`.
- A `schema` makes the subagent return JSON. Validation retries 5 times by default (`MAX_STRUCTURED_OUTPUT_RETRIES`), and Claude Code rejects a schema that contradicts itself before the agent starts.
- `meta` must be the first statement and a plain literal, or `/<name>` disappears from autocomplete.
- `Date.now()`, `Math.random()` and a no-argument `new Date()` throw, which keeps replays deterministic. Pass timestamps through `args`.
- `import()` is not allowed, and the script itself has no filesystem or shell access. Only its agents do.
- On Bedrock, Google Cloud's Agent Platform and Microsoft Foundry, a prompt the script computes reaches the subagent framed as script-authored text, so the safety classifier doesn't read it as coming from you.

Before editing a saved script, run the `/workflow-authoring` bundled skill. After editing, run `/reload-skills`. Each run's script is also written under the session directory in `~/.claude/projects/`, where you can diff or edit it and ask Claude to relaunch.

## Limits

| Constraint | Value |
|---|---|
| Concurrent agents | 16 by default, fewer with fewer CPUs available. `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` takes 1 to 256 |
| Items per `parallel()`/`pipeline()` call | 4,096 (longer lists are rejected with an error) |
| Agents per run | 1,000 |
| Mid-run user input | None, apart from agent permission prompts and usage-limit waits |
| Fan-out cache stagger | Matching agents wait up to `CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS` (default `5000`, `0` disables) so they can reuse the first agent's prompt cache |

The prompt cache for workflow agents lasts 5 minutes by default. Set `subagentPromptCacheTtl` to `1h` to lengthen it, at a higher cache-write price.

## Cost control

- Try a small slice first, such as one directory. Token use per agent shows in `/workflows`.
- A `Large workflow` warning appears above 25 agents or 1.5 million projected tokens. It is advisory only and doesn't appear when ultracode is on.
- **Size guideline** (advice to Claude, not a hard cap): `workflowSizeGuideline` is `unrestricted`, `small` (<5 agents), `medium` (<10, the default), or `large` (<50). Pro defaults to `small`. Set it with `/config workflowSizeGuideline=small` or in a settings file.
- Agent models follow the same order as subagents, and a model the script names counts as the per-invocation choice. Ask Claude to use a smaller model for easy stages. See [[costs-and-usage]].

## Turn workflows off

Toggle Dynamic workflows off in `/config`, set `"disableWorkflows": true` (in user settings, or in managed settings for an organization), or set `CLAUDE_CODE_DISABLE_WORKFLOWS=1`. That removes the bundled workflow commands, `/workflow-authoring`, the `ultracode` keyword, and `ultracode` in `/effort`.

For running independent sessions in parallel instead, see [[worktrees-and-background-work]].
