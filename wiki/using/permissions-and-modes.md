---
title: Permissions and Modes
type: reference
tldr: "Permission modes, rules, auto mode, trust"
sources:
  - raw/docs/official/permission-modes.md
  - raw/docs/official/permissions.md
  - raw/docs/official/auto-mode-config.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.278.md
related: ["[[sandboxing-and-security]]", "[[settings]]", "[[hooks]]", "[[headless-mode]]", "[[enterprise-admin]]", "[[trustworthy-agents]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [permission-modes, auto-mode, allow-ask-deny-rules, bypass-permissions, plan-mode]
---

# Permissions and Modes

Two layers decide whether a tool call runs: a **permission mode** sets the session baseline, and **permission rules** (allow, ask, deny) pre-approve or block specific tools on top of it. Claude Code enforces both, not the model, so a prompt or CLAUDE.md shapes what Claude tries, never what is allowed. The OS-level sandbox is in [[sandboxing-and-security]].

## The six modes

| Mode (config value) | Runs without asking | Use for |
|:--|:--|:--|
| `default` (labeled **Manual**; `manual` alias) | Reads only | Sensitive work, reviewing every action |
| `acceptEdits` | Reads, file edits, and `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` inside the working directories | Iterating while you review diffs afterwards |
| `plan` | Reads and exploration; edits blocked until you approve a plan | Exploring before changing code |
| `auto` | Everything, with a classifier reviewing actions | Long tasks, less prompt fatigue |
| `dontAsk` | Reads and pre-approved tools; anything that would prompt is denied | Locked-down CI and scripts |
| `bypassPermissions` | Everything | Isolated containers and VMs only |

The status bar names the active mode, such as `⏵⏵ auto mode on`. Some actions are never auto-approved in any mode, including `bypassPermissions`: tools matched by an explicit ask rule, `AskUserQuestion` and MCP tools marked `requiresUserInteraction`, connector tools an organization set to `ask`, `rm`/`rmdir` targeting a critical path, and reads outside the working directories while `permissions.blockReadsOutsideWorkingDirectories` is on. That last one also prompts for a command the shell parser can't trace, such as one running a subshell, even when it names no outside path, unless the sandbox enforces the block itself. Deny rules block in every mode; allow rules have no effect in `bypassPermissions`.

### Which mode a session starts in

A terminal session takes the first of these that applies:

1. `--permission-mode <mode>` or `--dangerously-skip-permissions`
2. `permissions.defaultMode` in a settings file. `"auto"` and `"bypassPermissions"` don't take effect from a project's settings files; put them in `~/.claude/settings.json`, `--settings`, or managed settings.
3. The built-in default: `auto` on Pro, Max, and Team plans in a terminal or the VS Code extension. It is `default` for `claude -p` and the Agent SDK, Enterprise plans, Console API keys, every cloud provider ([[cloud-providers]]), signed-in apps-gateway sessions, and whenever a settings file sets `disableAutoMode` to `"disable"` or feature-flag fetching is off.

If `auto` is selected but unavailable, the session starts in Manual.

### Switching during a session

- **CLI and JetBrains:** `Shift+Tab` cycles `default` → `acceptEdits` → `plan`, then `auto` if enabled; `bypassPermissions` joins only when you launched with it or one of its flags ([[cli-reference]]), and `dontAsk` never joins. Where auto mode is available, Bash prompts offer **Yes, and switch to auto mode**.
- **VS Code:** the mode indicator, with `claudeCode.initialPermissionMode` pinning any start mode but `auto` ([[ide-integrations]]). Cloud and desktop sessions have their own pickers ([[claude-code-on-the-web]], [[desktop-app]]) and ignore `dontAsk` and `bypassPermissions` from settings files.

## Plan mode

Claude reads files, explores, and writes a plan without editing source. Enter it with `Shift+Tab`, `/plan` on a single prompt, or `claude --permission-mode plan`. With auto mode available and `useAutoModeDuringPlan` on (the default), the classifier reviews shell commands while planning; otherwise commands outside the read-only set prompt.

On a finished plan you choose **Yes, and use auto mode** (or **Yes, auto-accept edits** where auto is unavailable), **Yes, manually approve edits**, or **No, keep planning**; `Ctrl+G` opens the plan in your editor first. Approving exits plan mode ([[sessions-and-checkpoints]]).

## Auto mode

A separate classifier model reviews each action before it runs, blocking actions that escalate beyond your request, target infrastructure it doesn't recognize, or look driven by hostile content Claude read. It reduces prompts but doesn't guarantee safety.

**Requirements.** On the Anthropic API and Claude Platform on AWS it needs Opus 4.6 or later, Sonnet 4.6 or later, or a Fable model; on Bedrock, Agent Platform, Foundry, and apps-gateway sessions it needs Sonnet 5, Opus 4.7 or later, or Fable. Team and Enterprise admins turn it off with `permissions.disableAutoMode: "disable"` in managed settings.

**Where the review runs.** On Enterprise plans and Claude API accounts, on every cloud provider, and whenever `ANTHROPIC_BASE_URL` points at a gateway or proxy, Claude Code asks the server to review classifier-bound actions as part of the session's model requests, and the server's verdicts decide them. Where the server doesn't, most often because a gateway interferes with the traffic, Claude Code falls back to its own classifier requests and warns about classifier-request charges on accounts where those are billed. `CLAUDE_CODE_AUTO_MODE_SERVER=0` skips asking the server; the variable isn't read on a direct Anthropic API connection, and `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` also stops Claude Code asking while it is unset. `/status` carries an **Auto mode server** row for this session.

**Decision order** (first match wins):

1. Allow, ask, and deny rules resolve immediately, except that protected-path writes, critical-path removals, and a command naming its own sandbox hosts ([[sandboxing-and-security]]) still reach the classifier, and content-scoped ask rules such as `Bash(git push *)` still prompt.
2. Reads and working-directory edits are auto-approved, except protected paths. The first Read, Grep, or Glob outside the working directories asks whether to keep allowing such reads.
3. Everything else goes to the classifier. In the requests Claude Code sends itself, it sees user messages, tool calls, and CLAUDE.md, but not tool results.
4. On a block, Claude gets the matched rule name, such as `[Data Exfiltration]`, and tries another way.

**Blocked by default** (abridged; `claude auto-mode defaults` prints every rule): `curl | bash`, sending sensitive data out, production deploys, mass cloud deletion, IAM or repo permission grants, force push, `git reset --hard`, `terraform destroy`. **Allowed by default:** working-directory file operations, installing declared dependencies, sending `.env` credentials to their matching API, read-only HTTP, and pushing to any branch of the working repo except deploy branches such as `production`.

Broad allow rules granting arbitrary code execution are dropped while auto mode is on: `Bash(*)`, `PowerShell(*)`, wildcarded interpreters like `Bash(python*)`, package-manager run commands, `Agent` and `Monitor` rules. `autoMode.classifyAllShell: true` suspends every shell allow rule.

**Fallback.** After 3 consecutive blocks or 20 in a session, auto mode pauses and prompting resumes; neither threshold is configurable. Blocked actions appear under **Recently denied** in `/permissions`, where `r` retries with manual approval. A boundary you state in chat ("don't push") is honored, but compaction can drop the message stating it, so use a deny rule.

**Subagents** are checked at spawn and on every action, in the parent's mode ([[subagents]]). On return the classifier reviews the subagent's work and its final report before the parent reads it; a flagged report is still delivered, prefixed with a security warning, and when the classifier is unavailable the report arrives with a note to verify the work first.

**Cost.** The classifier runs on Sonnet 5 by default; on Enterprise, API and cloud-provider accounts its calls count toward token usage. Where the server reviews the actions there are no separate calls to count.

**Trusted infrastructure.** By default the classifier trusts only the working directory and the repo's configured remotes. Add your org's repos, buckets, and domains to `autoMode.environment` in `~/.claude/settings.json`, managed settings, or `--settings`; project settings are ignored for `autoMode`. `/auto-mode-setup` drafts entries and `claude auto-mode critique` reviews custom rules ([[cli-reference]]).

## dontAsk and bypassPermissions

`dontAsk` denies every call that would prompt, including explicit ask rules and `AskUserQuestion`, so nothing waits for input; pair it with `--allowedTools` for a fixed tool surface in CI ([[headless-mode]]).

`bypassPermissions` (`--dangerously-skip-permissions`) skips prompts and safety checks, including protected-path writes, and offers no protection against prompt injection. It can't be entered from a session started without it, and the first interactive start shows a one-time acceptance dialog. On Linux and macOS it refuses to run as root or under `sudo` outside a recognized sandbox — which is where it belongs ([[sandboxing-and-security]]). `--restricted` refuses it, and admins can block it with `permissions.disableBypassPermissionsMode: "disable"`.

## Protected and critical paths

**Protected paths:** writes prompt in `default` and `acceptEdits`, go to the classifier in `auto`, are denied in `dontAsk`, and are allowed only in `bypassPermissions`. An allow rule such as `Edit(.claude/**)` doesn't pre-approve them. The directories are `.git`, `.config/git`, `.vscode`, `.idea`, `.husky`, `.cargo`, `.devcontainer`, `.yarn`, `.mvn`, and `.claude` except `.claude/worktrees`; the files include shell rc files (`.bashrc`, `.zshrc`, `.profile`, `.envrc`), `.gitconfig`, `.gitmodules`, `.npmrc`, `.pre-commit-config.yaml`, `.mcp.json`, and `.claude.json`.

**Critical paths:** no allow rule or `PreToolUse` hook can approve `rm` or `rmdir` against the filesystem root, a top-level directory, your home directory, the working directory or its parents, or a glob or trailing slash directly under a shell variable, such as `rm -rf "$DIR"/*`, which removes from root when the variable is empty. Such a removal is asked in most modes, classified in `auto`, denied in `dontAsk`, and nesting it in a subshell, brace group, or substitution doesn't skip the check.

## Rule syntax

A rule is `Tool` or `Tool(specifier)`, evaluated **deny, then ask, then allow**; the first match wins and specificity doesn't matter, so `Bash(aws *)` in deny beats `Bash(aws s3 ls)` in allow. A deny rule naming a bare tool (`Bash`) removes it from Claude's context. In `/permissions`, **Yes, and don't ask again** saves Bash and WebFetch approvals to `.claude/settings.local.json`; file-edit approvals last only for the session.

| Rule | Matches |
|:--|:--|
| `Bash(npm run *)` | `npm run build`, `npm run` (a trailing ` *` also matches the bare command) |
| `Bash(ls *)` vs `Bash(ls*)` | The space matters: only the second also matches `lsof` |
| `Read(./.env)`, `Read(**/.env)` | That file; any `.env` at or below the current directory |
| `Edit(/src/**)` | `src/` relative to the settings source (`//path` absolute, `~/path` home) |
| `WebFetch(domain:*.example.com)` | Subdomains at any depth, not `example.com` itself |
| `mcp__github__get_*` | One server's tools; allow globs need a literal `mcp__<server>__` prefix |
| `Agent(Explore)`, `Agent(model:opus)` | That subagent; and, in deny or ask only, calls whose top-level `model` is `opus` |

Bash matching details:

- **Compound commands** split on `&&`, `||`, `;`, `|`, and newlines; every part must match. **Wrappers** such as `timeout`, `nice`, `nohup`, and bare `xargs` are stripped first; runners such as `npx` and `devbox run` are not, so write `Bash(devbox run npm test)`.
- **Rules match command text, not the program**, so `Bash(git push *)` doesn't stop `git -C . push`. Use the sandbox or a `PreToolUse` hook for real enforcement.
- **Read-only commands** (`ls`, `cat`, `grep`, `find`, read-only `git`) never prompt; the set isn't configurable, so add an ask or deny rule to gate one.
- **Path rules** apply only to `Edit(...)` and `Read(...)`; `Write(...)` path rules are never consulted.

## Precedence, hooks, and managed policy

Rules follow normal [[settings]] precedence, except that a deny at any level can't be overridden: a managed deny beats `--allowedTools`, a user deny beats a project allow. `allowManagedPermissionRulesOnly` makes managed settings the only rule source ([[enterprise-admin]]). `PreToolUse` hooks run before the prompt and can allow, ask, or deny, but deny and ask rules still apply after a hook returns `"allow"`; exit code 2 blocks before rules are evaluated ([[hooks]]).

## Working directories and trust

Claude reads files in the launch directory without prompting. Extend that with `--add-dir <path>`, `/add-dir`, or `permissions.additionalDirectories`, or move the session with `/cd <path>` ([[slash-commands]]), which loads the new directory's project config after a trust prompt. Added directories grant file access, not configuration, and only `--add-dir` and `/add-dir` also load that directory's skills, commands and subagents.

A project's `permissions.allow` rules and `additionalDirectories` apply only after you accept the workspace trust dialog, which lists them first ([[settings]]). Trust is keyed on the git repository root (the main checkout for worktrees), and the dialog appears only in interactive sessions. In `claude -p` and SDK runs, project allow rules are skipped with a `this workspace has not been trusted` warning, while project hooks, the `env` block, `apiKeyHelper`, and `.mcp.json` servers still run. To trust a folder by hand, set `projects["<path>"].hasTrustDialogAccepted` to `true` in `~/.claude.json`.

Before `claude -p` in a repository you didn't write, pass `--setting-sources user` or `--bare`, plus `--settings '{"disableAllHooks": true}'` ([[headless-mode]]). The classifier's rationale: [[trustworthy-agents]].
