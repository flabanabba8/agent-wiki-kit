---
title: Permissions and Modes
type: reference
tldr: "Permission modes, rules, auto mode, trust"
sources:
  - raw/docs/official/permission-modes.md
  - raw/docs/official/permissions.md
  - raw/docs/official/auto-mode-config.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[sandboxing-and-security]]", "[[settings]]", "[[hooks]]", "[[headless-mode]]", "[[enterprise-admin]]", "[[trustworthy-agents]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [permission-modes, auto-mode, allow-ask-deny-rules, bypass-permissions, plan-mode]
---

# Permissions and Modes

Two layers decide whether a tool call runs: a **permission mode** sets the session baseline, and **permission rules** (allow, ask, deny) sit on top, pre-approving or blocking specific tools. Claude Code enforces both, not the model, so an instruction in a prompt or CLAUDE.md shapes what Claude tries, never what is allowed. The OS-level Bash sandbox is covered in [[sandboxing-and-security]].

## The six modes

| Mode (config value) | Runs without asking | Use for | Status bar |
|:--|:--|:--|:--|
| `default` (labeled **Manual**; `manual` alias) | Reads only | Sensitive work, reviewing every action | `⏸ manual mode on` |
| `acceptEdits` | Reads, file edits, and `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` inside the working directories | Iterating while you review diffs afterwards | `⏵⏵ accept edits on` |
| `plan` | Reads and exploration; edits blocked until you approve a plan | Exploring before changing code | `⏸ plan mode on` |
| `auto` | Everything, with a classifier reviewing actions | Long tasks, less prompt fatigue | `⏵⏵ auto mode on` |
| `dontAsk` | Reads and pre-approved tools; anything that would prompt is denied | Locked-down CI and scripts | `⏵⏵ don't ask on` |
| `bypassPermissions` | Everything | Isolated containers and VMs only | `⏵⏵ bypass permissions on` |

Some actions are never auto-approved in any mode, `bypassPermissions` included: tools matched by an explicit ask rule, `AskUserQuestion` and MCP tools marked `requiresUserInteraction`, connector tools an organization set to `ask`, `rm`/`rmdir` targeting a critical path, and reads outside the working directories while `permissions.blockReadsOutsideWorkingDirectories` is on. Deny rules block in every mode. Allow rules have no effect in `bypassPermissions`.

### Which mode a session starts in

A terminal session takes the first of these that applies:

1. `--permission-mode <mode>` or `--dangerously-skip-permissions`
2. `permissions.defaultMode` in a settings file. `"auto"` and `"bypassPermissions"` don't take effect from a project's `.claude/settings.json` or `.claude/settings.local.json`; put them in `~/.claude/settings.json`, `--settings`, or managed settings.
3. The built-in default: `auto` on Pro, Max, and Team plans in a terminal or the VS Code extension. It is `default` for `claude -p` and the Agent SDK, Enterprise plans, Console API keys, Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry, Claude Platform on AWS, and signed-in Claude apps gateway sessions. It is also `default` when a settings file sets `disableAutoMode` to `"disable"` or when feature-flag fetching is off.

If `auto` is selected but unavailable, the session starts in Manual.

### Switching during a session

- **CLI and JetBrains:** `Shift+Tab` cycles `default` → `acceptEdits` → `plan`, then `auto` if enabled, and `bypassPermissions` only when you launched with `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions` or that mode. `dontAsk` never joins the cycle. Where auto mode is available, Bash prompts offer **Yes, and switch to auto mode**.
- **VS Code:** the mode indicator; `claudeCode.initialPermissionMode` pins a start mode (not `auto`). See [[ide-integrations]].
- **Desktop:** the mode selector, remembered per folder ([[desktop-app]]).
- **Cloud sessions** ([[claude-code-on-the-web]]) offer Accept edits, Plan, and Auto, and ignore `dontAsk` and `bypassPermissions` from settings files.

## Plan mode

Claude reads files, runs commands to explore, and writes a plan without editing source. Enter it with `Shift+Tab`, `/plan` on a single prompt, or `claude --permission-mode plan`. With auto mode available and `useAutoModeDuringPlan` on (the default), the classifier reviews shell commands while planning; otherwise commands outside the read-only set prompt.

When the plan is ready you choose **Yes, and use auto mode** (or **Yes, auto-accept edits** when auto is unavailable), **Yes, manually approve edits**, or **No, keep planning**. `Ctrl+G` opens the plan in your editor first. Approving exits plan mode and names an unnamed session from the plan.

## Auto mode

A separate classifier model reviews each action before it runs. It blocks actions that escalate beyond your request, target infrastructure it doesn't recognize, or look driven by hostile content Claude read. Auto mode reduces prompts but doesn't guarantee safety.

**Requirements.** On the Anthropic API and Claude Platform on AWS it needs Opus 4.6 or later, Sonnet 4.6 or later, or a Fable model. On Bedrock, Agent Platform, Foundry, and apps-gateway sessions it needs Sonnet 5, Opus 4.7 or later, or Fable, and the classifier runs locally unless `CLAUDE_CODE_AUTO_MODE_SERVER=1` selects the platform's server-side classifier. Team and Enterprise admins can turn it off with `permissions.disableAutoMode: "disable"` in managed settings.

**Decision order** (first match wins):

1. Allow, ask, and deny rules resolve immediately. Protected-path writes and critical-path removals still go to the classifier. Content-scoped ask rules such as `Bash(git push *)` still prompt.
2. Reads and working-directory edits are auto-approved, except protected paths. The first Read, Grep, or Glob outside the working directories asks whether to keep allowing such reads.
3. Everything else goes to the classifier, which sees user messages, tool calls, and CLAUDE.md but not tool results.
4. On a block, Claude gets the matched rule name, such as `[Data Exfiltration]`, and tries another approach.

**Blocked by default** (abridged; `claude auto-mode defaults` prints all rules): `curl | bash`, sending sensitive data out, production deploys, mass cloud deletion, granting IAM or repo permissions, force push, `git reset --hard`, `terraform destroy`, merging unapproved PRs, printing live credentials, and launching unsandboxed agent loops.

**Allowed by default:** working-directory file operations, installing declared dependencies, sending `.env` credentials to their matching API, read-only HTTP, and pushing to any branch of the working repo except deploy branches such as `production`.

In auto mode, broad allow rules that grant arbitrary code execution are dropped until you leave it: `Bash(*)`, `PowerShell(*)`, wildcarded interpreters like `Bash(python*)`, package-manager run commands, and `Agent` and `Monitor` allow rules. Set `autoMode.classifyAllShell: true` to suspend every shell allow rule so the classifier sees all commands.

**Fallback.** After 3 consecutive blocks or 20 in a session, auto mode pauses and prompting resumes; neither threshold is configurable. Blocked actions appear under **Recently denied** in `/permissions`, where `r` retries with manual approval. A boundary you state in chat ("don't push") is honored, but compaction can drop the message that stated it, so use a deny rule for a hard guarantee.

**Subagents** are checked at spawn, on every action, and on return. A subagent's `permissionMode` frontmatter is ignored.

**Cost.** The classifier runs on Sonnet 5 by default; on Enterprise, API and cloud-provider accounts its calls count toward token usage.

**Trusted infrastructure.** By default the classifier trusts only the working directory and the repo's configured remotes. Add your org's repos, buckets, and domains to `autoMode.environment` in `~/.claude/settings.json`, managed settings, or `--settings`. Project settings are ignored for `autoMode`. `/auto-mode-setup` drafts entries. Inspect the effective rules with `claude auto-mode config`, get feedback on custom rules with `claude auto-mode critique`, and reset with `claude auto-mode reset`.

## dontAsk and bypassPermissions

`dontAsk` denies every call that would prompt, including explicit ask rules and `AskUserQuestion`, so nothing waits for input — which suits CI:

```bash
claude -p "run the test suite" --permission-mode dontAsk --allowedTools "Bash(npm test)" "Read"
```

`bypassPermissions` (`--dangerously-skip-permissions`) skips prompts and safety checks, including protected-path writes, and offers no protection against prompt injection.

- It can't be entered from a session started without it.
- The first interactive start shows a one-time acceptance dialog.
- On Linux and macOS it refuses to run as root or under `sudo` outside a recognized sandbox.
- `--restricted` refuses it, and admins can block it with `permissions.disableBypassPermissionsMode: "disable"`.

Run it only inside a container, VM, or sandbox runtime (see [[sandboxing-and-security]]).

## Protected and critical paths

**Protected paths:** writes are prompted in `default` and `acceptEdits`, sent to the classifier in `auto`, denied in `dontAsk`, and allowed only in `bypassPermissions`. An allow rule such as `Edit(.claude/**)` does not pre-approve them. The protected directories are `.git`, `.config/git`, `.vscode`, `.idea`, `.husky`, `.cargo`, `.devcontainer`, `.yarn`, `.mvn`, and `.claude` except `.claude/worktrees`. Protected files include shell rc files (`.bashrc`, `.zshrc`, `.profile`, `.envrc`), `.gitconfig`, `.gitmodules`, `.npmrc`, `.pre-commit-config.yaml`, `.mcp.json`, and `.claude.json`.

**Critical paths:** no allow rule or `PreToolUse` hook can approve `rm` or `rmdir` against the filesystem root, a top-level directory, your home directory, the working directory or its parents, or a glob or trailing slash directly under a shell variable, such as `rm -rf "$DIR"/*`, which removes from root if the variable is empty. Such a removal is asked in most modes, sent to the classifier in `auto` and denied in `dontAsk`.

## Rule syntax

Rules take the form `Tool` or `Tool(specifier)`. Evaluation is **deny, then ask, then allow**; the first match wins and specificity doesn't matter, so `Bash(aws *)` in deny beats `Bash(aws s3 ls)` in allow. A deny rule naming a bare tool (`Bash`) removes the tool from Claude's context. Manage rules in `/permissions`. **Yes, and don't ask again** saves Bash and WebFetch approvals to `.claude/settings.local.json`; file-edit approvals last only for the session.

| Rule | Matches |
|:--|:--|
| `Bash(npm run *)` | `npm run build`, `npm run` (a trailing ` *` also matches the bare command) |
| `Bash(ls *)` vs `Bash(ls*)` | The space matters: only the second also matches `lsof` |
| `Bash(git log *)` | Only `git log`; put `*` after the subcommand, not before it |
| `Read(./.env)`, `Read(**/.env)` | That file; any `.env` at or below the current directory |
| `Edit(/src/**)` | `src/` relative to the settings source (`//path` is absolute, `~/path` is home) |
| `WebFetch(domain:*.example.com)` | Subdomains at any depth, not `example.com` itself |
| `mcp__github__get_*` | Tools from one MCP server; allow globs need a literal `mcp__<server>__` prefix |
| `Agent(Explore)` | The Explore subagent |
| `Agent(model:opus)` | Deny/ask only: calls whose top-level `model` parameter is `opus` |

Bash matching details:

- **Compound commands** split on `&&`, `||`, `;`, `|`, and newlines; every part must match.
- **Wrappers** such as `timeout`, `nice`, `nohup`, and bare `xargs` are stripped before matching. Runners such as `npx` and `devbox run` are not, so write `Bash(devbox run npm test)`.
- **Rules match command text, not the program.** `Bash(git push *)` doesn't stop `git -C . push`. Use the sandbox or a `PreToolUse` hook for real enforcement.
- **Read-only commands** (`ls`, `cat`, `grep`, `find`, read-only `git`) never prompt. The set isn't configurable; add an ask or deny rule to gate one.
- **Path rules** only apply to `Edit(...)` and `Read(...)`. `Write(...)` path rules are never consulted.

## Precedence, hooks, and managed policy

Rules follow normal [[settings]] precedence, but a deny at any level can't be overridden. A managed deny beats `--allowedTools`, and a user-level deny beats a project-level allow. `allowManagedPermissionRulesOnly` makes managed settings the only rule source (see [[enterprise-admin]]). `PreToolUse` hooks run before the prompt and can allow, ask, or deny, but deny and ask rules still apply after a hook returns `"allow"`. A hook exiting with code 2 blocks before rules are evaluated. See [[hooks]].

## Working directories

Claude can read files in the launch directory without prompting. Extend that with `--add-dir <path>`, `/add-dir`, or `permissions.additionalDirectories`, or move the session with `/cd <path>`, which loads the new directory's project config after a trust prompt. Added directories grant file access, not configuration, and only `--add-dir` and `/add-dir` also load that directory's skills, commands and subagents.

## Workspace trust

A project's `permissions.allow` rules and `additionalDirectories` grant capability, so they apply only after you accept the workspace trust dialog, which lists them first; deny and ask rules apply immediately. Trust is keyed on the git repository root (the main checkout for worktrees). The dialog appears only in interactive sessions. In `claude -p` and SDK runs, project allow rules are skipped with a `this workspace has not been trusted` warning, but project hooks, the `env` block, and helpers such as `apiKeyHelper` still run, and `.mcp.json` servers connect without asking. To trust a folder by hand, set `projects["<path>"].hasTrustDialogAccepted` to `true` in `~/.claude.json`.

Before `claude -p` in a repository you didn't write, pass `--setting-sources user` or `--bare`, plus `--settings '{"disableAllHooks": true}'`. See [[headless-mode]]; the classifier's design rationale is in [[trustworthy-agents]].
