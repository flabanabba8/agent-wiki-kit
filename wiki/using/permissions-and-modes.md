---
title: Permissions and Modes
type: reference
tldr: "Permission modes, rules, auto mode, trust"
sources:
  - raw/docs/official/permission-modes.md
  - raw/docs/official/permissions.md
  - raw/docs/official/auto-mode-config.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
related: ["[[sandboxing-and-security]]", "[[settings]]", "[[hooks]]", "[[headless-mode]]", "[[enterprise-admin]]", "[[trustworthy-agents]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [permission-modes, auto-mode, allow-ask-deny-rules, bypass-permissions, plan-mode]
---

# Permissions and Modes

A **permission mode** sets the session baseline and **permission rules** (allow, ask, deny) pre-approve or block specific tools. Claude Code enforces both; a prompt or CLAUDE.md shapes only what Claude tries. The OS-level sandbox is in [[sandboxing-and-security]].

## The six modes

| Mode (config value) | Runs without asking | Use for |
|:--|:--|:--|
| `default` (labeled **Manual**; `manual` alias) | Reads only | Sensitive work, reviewing every action |
| `acceptEdits` | Reads, file edits, and `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` inside the working directories | Iterating while you review diffs afterwards |
| `plan` | Reads and exploration; edits blocked until you approve a plan | Exploring before changing code |
| `auto` | Everything, with a classifier reviewing actions | Long tasks, less prompt fatigue |
| `dontAsk` | Reads and pre-approved tools; anything that would prompt is denied | Locked-down CI and scripts |
| `bypassPermissions` | Everything | Isolated containers and VMs only |

Never auto-approved in any mode, `bypassPermissions` included: tools matched by an explicit ask rule, `AskUserQuestion` and MCP tools marked `requiresUserInteraction`, connector tools an organization set to `ask`, `rm`/`rmdir` targeting a critical path, and, while `permissions.blockReadsOutsideWorkingDirectories` is on, unsandboxed reads outside the working directories or commands the shell parser can't trace. Deny rules block in every mode. Allow rules have no effect in `bypassPermissions`.

### Which mode a session starts in

A terminal session takes the first of these that applies:

1. `--permission-mode <mode>` or `--dangerously-skip-permissions`
2. `permissions.defaultMode` in a settings file. `"auto"` and `"bypassPermissions"` don't take effect from a project's `.claude/settings.json` or `.claude/settings.local.json`; put them in `~/.claude/settings.json`, `--settings`, or managed settings.
3. The built-in default: `auto` on Pro, Max, and Team plans in a terminal or the VS Code extension. It is `default` for `claude -p`, the Agent SDK, Enterprise, Console API keys, cloud providers and Claude apps gateway sessions, and when `disableAutoMode` is `"disable"` or feature-flag fetching is off.

If `auto` is selected but unavailable, the session starts in Manual.

### Switching during a session

- **CLI and JetBrains:** `Shift+Tab` cycles `default` → `acceptEdits` → `plan`, then `auto` if enabled, and `bypassPermissions` only when you launched with `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions` or that mode. `dontAsk` never joins the cycle. Where auto mode is available, Bash prompts offer **Yes, and switch to auto mode**.
- **VS Code and Desktop:** the mode indicator or selector ([[ide-integrations]], [[desktop-app]]).
- **Cloud sessions** ([[claude-code-on-the-web]]) offer Accept edits, Plan, and Auto, and ignore `dontAsk` and `bypassPermissions` from settings files.

## Plan mode

Claude explores and writes a plan without editing source. Enter it with `Shift+Tab`, `/plan` on a single prompt, or `claude --permission-mode plan`. With auto mode available and `useAutoModeDuringPlan` on (the default), the classifier reviews shell commands while planning; otherwise commands outside the read-only set prompt.

When the plan is ready, choose **Yes, and use auto mode** (**Yes, auto-accept edits** when auto isn't available to the session), **Yes, manually approve edits**, or **No, keep planning**; `Ctrl+G` edits the plan first.

## Auto mode

A classifier reviews each action before it runs, blocking actions that escalate beyond your request, target unrecognized infrastructure, or look driven by hostile content. It reduces prompts but doesn't guarantee safety.

**Requirements.** On the Anthropic API and Claude Platform on AWS it needs Opus 4.6 or later, Sonnet 4.6 or later, or a Fable model; on Bedrock, Agent Platform, Foundry, and apps-gateway sessions it needs Sonnet 5, Opus 4.7 or later, or Fable. Team and Enterprise admins turn it off with `permissions.disableAutoMode: "disable"` in managed settings.

**Where the review runs.** On Enterprise plans and Claude API accounts, on every cloud provider, and whenever `ANTHROPIC_BASE_URL` points at a gateway or proxy, Claude Code asks the server to review classifier-bound actions as part of the session's model requests, and the server's verdicts decide them. Where the server doesn't, most often because a gateway interferes with the traffic, Claude Code falls back to its own classifier requests and warns about classifier-request charges on accounts where those are billed. `CLAUDE_CODE_AUTO_MODE_SERVER=0` skips asking the server; the variable isn't read on a direct Anthropic API connection, and `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` also stops Claude Code asking while it is unset. `/status` carries an **Auto mode server** row for this session.

**Decision order** (first match wins):

1. Allow, ask, and deny rules resolve immediately, except: protected-path writes, critical-path removals, and commands carrying per-command sandbox domains go to the classifier; `requiresUserInteraction` MCP tools and content-scoped ask rules such as `Bash(git push *)` prompt.
2. Reads and working-directory edits are auto-approved, except protected paths. The first Read, Grep, or Glob outside the working directories asks whether to keep allowing such reads.
3. Everything else goes to the classifier. Claude Code's own classifier requests carry user messages, tool calls, and CLAUDE.md but not tool results.
4. On a block, Claude gets the matched rule name, such as `[Data Exfiltration]`, and tries another approach.

**Blocked by default** (abridged; `claude auto-mode defaults` prints all rules): `curl | bash`, data exfiltration, production deploys, mass cloud deletion, granting IAM or repo permissions, force push, `git reset --hard`, and printing live credentials.

**Blocked by default** (abridged; `claude auto-mode defaults` prints every rule): `curl | bash`, sending sensitive data out, production deploys, mass cloud deletion, IAM or repo permission grants, force push, `git reset --hard`, `terraform destroy`. **Allowed by default:** working-directory file operations, installing declared dependencies, sending `.env` credentials to their matching API, read-only HTTP, and pushing to any branch of the working repo except deploy branches such as `production`.

In auto mode, broad allow rules that grant arbitrary code execution are dropped until you leave it: `Bash(*)`, `PowerShell(*)`, wildcarded interpreters like `Bash(python*)`, package-manager run commands, and `Agent` and `Monitor` allow rules. `autoMode.classifyAllShell: true` suspends every shell allow rule.

**Fallback.** After 3 consecutive blocks or 20 in a session (not configurable), auto mode pauses and prompting resumes. **Recently denied** in `/permissions` lists blocks; `r` retries with manual approval. Use a deny rule, not a chat instruction, for a hard boundary.

**Subagents** are checked at spawn, on every action, and on return; a flagged or unreviewable report still arrives, prefixed with a warning. A subagent's `permissionMode` frontmatter is ignored.

**Approvals in chat** clear a block only if you name the action and what makes it dangerous ("force-push to `release`", not "you can force-push"), and cover that one action; use `autoMode.allow` for standing patterns.

**Server-side review.** The server can review actions inside the session's own model requests, with no separate classifier calls to bill: on direct Anthropic API interactive sessions (rolling out), cloud providers, `ANTHROPIC_BASE_URL` gateways, Claude apps gateway sessions, and any session that doesn't fetch feature flags. Read-only and sandboxed shell commands then also wait for review. If the server doesn't review the session, Claude Code falls back to its own classifier (billed where applicable, with a notice); an action with no verdict is denied, and ten in a row stop the turn. `CLAUDE_CODE_AUTO_MODE_SERVER=0` forces Claude Code's own classifier and `1` enables server review in `-p` and SDK sessions; `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` also disables it. `/status` shows an **Auto mode server** row.

**Trusted infrastructure.** By default the classifier trusts only the working directory and the repo's configured remotes. Add your org's repos, buckets, and domains to `autoMode.environment` in user, managed or `--settings` settings (project settings are ignored); `/auto-mode-setup` drafts entries. `claude auto-mode config` shows the effective rules, `claude auto-mode critique` reviews custom ones, and `claude auto-mode reset` resets them.

## dontAsk and bypassPermissions

`dontAsk` denies every call that would prompt, including ask rules and `AskUserQuestion`, which suits CI:

```bash
claude -p "run the test suite" --permission-mode dontAsk --allowedTools "Bash(npm test)" "Read"
```

`bypassPermissions` (`--dangerously-skip-permissions`) skips prompts and safety checks and offers no protection against prompt injection.

- It can't be entered from a session started without it.
- On Linux and macOS it refuses to run as root or under `sudo` outside a recognized sandbox.
- `--restricted` refuses it, and admins can block it with `permissions.disableBypassPermissionsMode: "disable"`.

Run it only inside a container, VM, or sandbox runtime (see [[sandboxing-and-security]]).

## Protected and critical paths

**Protected paths:** writes prompt in `default` and `acceptEdits`, go to the classifier in `auto`, are denied in `dontAsk`, and are allowed only in `bypassPermissions`. An allow rule such as `Edit(.claude/**)` doesn't pre-approve them. The directories are `.git`, `.config/git`, `.vscode`, `.idea`, `.husky`, `.cargo`, `.devcontainer`, `.yarn`, `.mvn`, and `.claude` except `.claude/worktrees`; the files include shell rc files (`.bashrc`, `.zshrc`, `.profile`, `.envrc`), `.gitconfig`, `.gitmodules`, `.npmrc`, `.pre-commit-config.yaml`, `.mcp.json`, and `.claude.json`.

**Critical paths:** no allow rule or `PreToolUse` hook can approve `rm` or `rmdir` against the filesystem root, a top-level directory, your home directory, the working directory or its parents, or a glob or trailing slash directly under a shell variable, such as `rm -rf "$DIR"/*`, which removes from root if the variable is empty. Such a removal (even nested in a subshell or substitution) is asked in most modes, sent to the classifier in `auto` and denied in `dontAsk`; guarding every expansion (`"${DIR:?}"`) or a literal path makes it non-critical. A recursive `rm` whose target is only command-substitution output, such as `rm -rf "$(pwd)"`, asks even with an allow rule and in auto and bypass mode (`CLAUDE_CODE_DISABLE_SUBSTITUTION_RM_PROMPT=1` turns that off). In auto and bypass mode this prompt denies after 2 minutes (`CLAUDE_CODE_DISABLE_DANGEROUS_RM_TIMEOUT=1` removes the timeout).

**Symlinks:** writes are judged by where they land.

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

- **Compound commands** split on `&&`, `||`, `;`, `|`, and newlines; every part must match.
- **Wrappers** such as `timeout`, `nice`, `nohup`, and bare `xargs` are stripped before matching. Runners such as `npx` and `devbox run` are not, so write `Bash(devbox run npm test)`.
- **Rules match command text:** `Bash(git push *)` doesn't stop `git -C . push`.
- **Read-only commands** (`ls`, `cat`, `grep`, `find`, read-only `git`) never prompt. The set isn't configurable; add an ask or deny rule to gate one.
- **Path rules** only apply to `Edit(...)` and `Read(...)`. `Write(...)` path rules are never consulted.

## Precedence, hooks, and managed policy

Rules follow normal [[settings]] precedence, but a deny at any level can't be overridden. A managed deny beats `--allowedTools`, and a user-level deny beats a project-level allow. `allowManagedPermissionRulesOnly` makes managed settings the only rule source, and then repository, user and `--add-dir` skills and commands can't pre-approve their tools with `allowed-tools` (see [[enterprise-admin]]). `PreToolUse` hooks run before the prompt and can allow, ask, or deny, but deny and ask rules still apply after a hook returns `"allow"`. A hook exiting with code 2 blocks before rules are evaluated. See [[hooks]].

## Working directories

Extend file access beyond the launch directory with `--add-dir <path>`, `/add-dir`, or `permissions.additionalDirectories` (only the first two also load that directory's skills, commands and subagents), or move the session with `/cd <path>`, which loads the new project config after a trust prompt.

Claude reads files in the launch directory without prompting. Extend that with `--add-dir <path>`, `/add-dir`, or `permissions.additionalDirectories`, or move the session with `/cd <path>` ([[slash-commands]]), which loads the new directory's project config after a trust prompt. Added directories grant file access, not configuration, and only `--add-dir` and `/add-dir` also load that directory's skills, commands and subagents.

Project `permissions.allow` rules and `additionalDirectories` apply only after you accept the workspace trust dialog, keyed on the git repository root; deny and ask rules apply immediately. `claude -p` and SDK runs have no dialog: project allow rules are skipped with a warning, but project hooks, the `env` block, `apiKeyHelper` and `.mcp.json` servers still run. To trust a folder by hand, set `projects["<path>"].hasTrustDialogAccepted` to `true` in `~/.claude.json`.

Before `claude -p` in a repository you didn't write, pass `--setting-sources user` or `--bare`, plus `--settings '{"disableAllHooks": true}'` ([[headless-mode]]). The classifier's rationale: [[trustworthy-agents]].
