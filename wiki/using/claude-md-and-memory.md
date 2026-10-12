---
title: CLAUDE.md and Memory
type: reference
tldr: "CLAUDE.md, AGENTS.md, rules, auto memory"
sources:
  - raw/docs/official/memory.md
  - raw/docs/official/best-practices.md
  - raw/docs/official/context-window.md
  - raw/docs/official/prompt-caching.md
  - raw/docs/official/commands.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
related: ["[[context-window]]", "[[skills]]", "[[hooks]]", "[[settings]]", "[[enterprise-admin]]", "[[prompting-and-workflows]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [claude-md, auto-memory, claude-rules, memory-md, project-instructions]
---

# CLAUDE.md and Memory

Two mechanisms carry knowledge between sessions, and both load at the start of every conversation:

| | CLAUDE.md files | Auto memory |
|---|---|---|
| Written by | You | Claude |
| Scope | Project, user, or org | Per repository, shared across worktrees |
| Loaded | Every session, full content | Every session, first 200 lines or 25KB of `MEMORY.md` |
| Use for | Coding standards, workflows, architecture | Your preferences, corrections, context Claude can't derive from code |

Both are **context, not enforcement**: Claude reads them and tries to follow them. For anything that must happen regardless of what Claude decides, use a hook ([[hooks]]) or permission rules ([[permissions-and-modes]]).

## CLAUDE.md

Add an entry when Claude makes the same mistake twice, when review catches something Claude should have known, or when a new teammate would need the same context. Keep CLAUDE.md to facts needed in every session: build commands, conventions, layout, "always do X" rules. Multi-step procedures belong in [[skills]]; area-specific guidance in a path-scoped rule.

Add an entry when Claude makes the same mistake twice, review catches something Claude should have known, or a new teammate would need the context. Keep CLAUDE.md to facts needed in every session: build commands, conventions, layout, and "always do X" rules. Multi-step procedures belong in [[skills]], and guidance for one area of the codebase belongs in a path-scoped rule.

### Locations

Listed in load order, broadest first:

| Scope | Location | Shared with |
|---|---|---|
| Managed policy | `CLAUDE.md` in the managed-settings directory for your platform ([[enterprise-admin]]) | Everyone on the machine; can't be excluded |
| User | `~/.claude/CLAUDE.md` | Just you, all projects |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team, via source control |
| Local | `./CLAUDE.local.md` (gitignore it) | Just you, this project |

**How they load:**

- Files in the working directory **and every parent** load at launch, concatenated rather than overridden: root-most first, working directory last, `CLAUDE.local.md` after `CLAUDE.md` at each level. **Subdirectory** files load on demand when Claude reads files there.
- Block-level HTML comments (`<!-- notes -->`) are stripped before injection, so they cost no tokens.
- Files from `--add-dir` directories load only with `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`.
- A CLAUDE.md up to 4 MiB loads in full; larger files are skipped. The content arrives as a user message after the system prompt.

### Generate one with `/init`

`/init` analyzes the codebase and writes build commands, test instructions, and conventions. If CLAUDE.md already exists, it suggests improvements instead. It also pulls in relevant Cursor rules (`.cursor/rules/`, `.cursorrules`) and Copilot rules (`.github/copilot-instructions.md`). Set `CLAUDE_CODE_NEW_INIT=1` (safe to leave set) for an interactive flow that asks which artifacts to set up (CLAUDE.md, skills, hooks) and shows a proposal before writing; it also reads `AGENTS.md`, `.devin/rules/`, `.windsurf/rules/`, and `.clinerules`. `/import` copies another coding agent's instruction files, MCP servers, commands, subagents, and skills into Claude Code.

### Write instructions that stick

- **Size:** under 200 lines per file. Longer files cost context and reduce adherence.
- **Structure:** use headers and bullets, not dense paragraphs.
- **Specificity:** make instructions verifiable. Write "Use 2-space indentation", not "Format code properly". Write "Run `npm test` before committing", not "Test your changes".
- **Consistency:** when two rules contradict, Claude may pick either. Review nested files and rules periodically.
- **Emphasis:** add "IMPORTANT" only to the one line Claude keeps skipping.
- **The pruning test:** for each line, ask "Would removing this cause Claude to make mistakes?" If Claude asks about something CLAUDE.md already answers, the phrasing is ambiguous.

| Include | Exclude |
|---|---|
| Bash commands Claude can't guess | Anything Claude can learn by reading the code |
| Style rules that differ from defaults | Standard language conventions |
| Test instructions and preferred runners | Detailed API docs (link instead) |
| Repo etiquette (branch naming, PR conventions) | Frequently changing information |
| Project-specific architectural decisions | Long tutorials or file-by-file descriptions |
| Env quirks, required env vars, gotchas | "Write clean code" |

`/doctor` proposes trims for a checked-in CLAUDE.md. It cuts derivable content such as layouts, dependency lists, and architecture overviews, and keeps pitfalls, rationale, and non-default conventions.

**Include** commands Claude can't guess, test instructions, style rules that differ from defaults, repo etiquette, architectural decisions, and environment quirks. **Exclude** anything Claude can learn from the code, standard conventions, API docs (link instead), long tutorials, frequently changing information, and "write clean code". `/doctor` proposes trims for a checked-in CLAUDE.md, cutting content derivable from the code and keeping pitfalls, rationale, and non-default conventions. A "Compact Instructions" section steers what survives compaction ([[context-window]]).

### Imports

```text
See @README for project overview and @package.json for npm commands.
- git workflow @docs/git-instructions.md
- @~/.claude/my-project-instructions.md
```

- Relative paths resolve from the importing file. Imports nest up to **four hops**, and imports inside code spans and fenced blocks are ignored, so `` `@README` `` stays literal.
- Imported files load at launch, so imports organize content without saving context.
- The first time a project file imports a path outside the working directory, Claude Code asks for approval; decline and those imports stay disabled. Imports in your own user-scope files load without asking.
- A gitignored `CLAUDE.local.md` exists only in the worktree where you made it; to share personal notes across worktrees, import a file from your home directory.

### AGENTS.md

By default Claude reads `AGENTS.md` (and `.claude/AGENTS.md`) in the working directory and its parents only when none of those directories has a `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md`; user and managed CLAUDE.md and `.claude/rules/` don't count and load alongside. A subdirectory's `AGENTS.md` loads when Claude reads a file there. `AGENTS.local.md`, `AGENTS.override.md`, and `.agents/` are not read. Adding a `CLAUDE.local.md` therefore stops `AGENTS.md` loading.

Change this with **Project instructions** in `/config`, or `pluginConfigs["agents-md@builtin"].options.instructionFiles` in user, `--settings`, or managed settings (ignored in project settings):

| Value | Reads |
|---|---|
| `claude-md-or-agents-md` (default) | CLAUDE.md files, or AGENTS.md when there are none |
| `claude-md-and-agents-md` | Both, CLAUDE.md first in each directory; an already-imported AGENTS.md isn't read twice |
| `claude-md` | CLAUDE.md only |
| `managed-only` | Managed CLAUDE.md and auto memory at launch |

Where the setting is missing (the built-in `agents-md` plugin is disabled, or sometimes the first session after an upgrade), only CLAUDE.md loads; there, and whenever a CLAUDE.md also exists, put `@AGENTS.md` at the top of a CLAUDE.md with Claude-specific notes below it. A symlink (`ln -s AGENTS.md CLAUDE.md`) works too, but Edit and Write refuse to write through it, and Windows clones without `core.symlinks` get a one-line file. A directly read AGENTS.md doesn't fire `InstructionsLoaded` hooks or load from `--add-dir` directories. Remove any `SessionStart` hook that prints AGENTS.md, since it now adds a second copy. `/memory` lists an AGENTS.md that loaded.

Claude Code can read `AGENTS.md` as your project instructions, so a repository already set up for other coding agents needs no `CLAUDE.md`, import, or setting. By default it reads your `AGENTS.md` files only when no `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` sits in the working directory or above it, and your CLAUDE.md files instead when one does. Your `~/.claude/CLAUDE.md`, the managed policy file, and `.claude/rules/` don't count for that check and load either way — but a `CLAUDE.local.md` holding your uncommitted notes does count, and stops Claude reading `AGENTS.md` until you change the setting below.

When `AGENTS.md` loads, every `AGENTS.md` and `.claude/AGENTS.md` in the working directory and its parents loads at session start, and an interactive session prints a line such as `no CLAUDE.md found; AGENTS.md loaded: <path>`. A subdirectory's `AGENTS.md` loads when Claude reads a file there and that subdirectory has none of the three CLAUDE.md files. `@path` imports expand and `claudeMdExcludes` applies as for CLAUDE.md, and subagents that skip project instructions skip these too. `AGENTS.local.md`, `AGENTS.override.md`, and anything under `.agents/` are never read.

**Choose which files load** in `/config` → **Project instructions**:

| Value | Claude reads |
|---|---|
| `claude-md-or-agents-md` | The default above |
| `claude-md-and-agents-md` | Both, each directory's CLAUDE.md first and its AGENTS.md after; one already loaded through an import or symlink isn't read twice |
| `claude-md` | CLAUDE.md files only |
| `managed-only` | Only the managed CLAUDE.md and auto memory at launch; a subdirectory's CLAUDE.md and rules still load when Claude reads a file there |

In a settings file, set it under the built-in `agents-md` plugin in `pluginConfigs` — in `~/.claude/settings.json`, a `--settings` file, or managed settings, since project and local files are ignored. It applies from your next message.

```json
{ "pluginConfigs": { "agents-md@builtin": { "options": { "instructionFiles": "claude-md-and-agents-md" } } } }
```

A directly-read `AGENTS.md` differs from a CLAUDE.md in four ways: it isn't listed in `/memory` or under **Memory files** in `/context`, so confirm it from the `AGENTS.md loaded` line or by asking Claude what its project instructions say; `InstructionsLoaded` hooks don't fire for it, though they do for one reached through an import or symlink; `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` doesn't load an added directory's `AGENTS.md`; and an external `@path` import loads with no prompt if you already approved external imports, and otherwise not at all.

Some sessions read CLAUDE.md only, with no **Project instructions** row in `/config`: ones that don't fetch feature flags, such as Amazon Bedrock and other third-party providers or telemetry off; the first session after an install or upgrade; ones with `disableAllHooks` or `allowManagedHooksOnly` set; and ones where you disabled the `agents-md` plugin in `/plugin`.

**To share one file with other coding tools** in those sessions, alongside a `CLAUDE.md`, or under `claude-md`, put `@AGENTS.md` at the top of a `CLAUDE.md` beside it with any Claude-specific instructions below the import, which Claude reads first. A symlink (`ln -s AGENTS.md CLAUDE.md`, silent on success) works when you need nothing extra, with two constraints: Edit and Write refuse to write through a symlink and direct Claude to edit `AGENTS.md` instead, and on Windows a symlink needs Administrator or Developer Mode while Git checks a committed one out as a plain one-line file unless `core.symlinks` is on.

## Rules: `.claude/rules/`

Put one topic per markdown file in `.claude/rules/`; subdirectories are found recursively. **Unscoped rules** (no `paths`) load at launch with the same priority as `.claude/CLAUDE.md`. **Path-scoped rules** load only when Claude reads a matching file:

```markdown
---
paths:
  - "src/**/*.{ts,tsx}"
  - "tests/**/*.test.ts"
---
- All API endpoints must include input validation
```

| Pattern | Matches |
|---|---|
| `**/*.ts` | TypeScript files anywhere |
| `src/**/*` | Everything under `src/` |
| `*.md` | Markdown in the project root |
| `src/components/*.tsx` | Components in one directory |

- Brace expansion multiplies patterns. A rule's `paths` list shares a budget of 1,000 expanded patterns and 4 MiB, and a pattern that would exceed it matches nothing.
- Escape a literal `[` as `\[`. Otherwise an invalid pattern matches nothing.
- **Frontmatter:** `paths` (a YAML list or comma-separated string) is the only field read; others are ignored. Unparseable YAML loads the rule unscoped (`claude --debug` shows why).
- **User rules** in `~/.claude/rules/` apply to every project and load before project rules. Neither overrides the other, so if they conflict Claude may follow either.
- **Symlinks** into `.claude/rules/` work. A target outside the working directory is treated like an external import and needs approval.
- Path-scoped rules and nested CLAUDE.md files live in message history, so compaction summarizes them away until a matching file is read again. If a rule must survive compaction, remove its `paths:` or move it to the root CLAUDE.md.

## Teams and monorepos

- **Org-wide:** deploy the managed-policy file with MDM, Group Policy, or Ansible, or put the content in the `claudeMd` key of `managed-settings.json`. Managed CLAUDE.md gives behavioral guidance; enforcement belongs in managed settings ([[enterprise-admin]]).
- **Skip irrelevant files** with `claudeMdExcludes`, globs matched against absolute paths. Arrays merge across settings layers. Managed-policy CLAUDE.md can't be excluded.

```json
{ "claudeMdExcludes": ["**/monorepo/CLAUDE.md", "/home/user/monorepo/other-team/.claude/rules/**"] }
```

## Auto memory

Claude saves notes for itself as it works, and not every session. Each note's frontmatter records its `type`:

- `user`: your role, expertise, and preferences
- `feedback`: corrections you give and approaches you confirm
- `project`: ongoing work, deadlines, and decisions not visible in code or git
- `reference`: where to find outside information such as trackers and dashboards

It skips anything derivable from the code or already in CLAUDE.md. "Remember that the API tests require a local Redis" goes to auto memory; say "add this to CLAUDE.md" to put it there.

**Storage.** Memory lives in `~/.claude/projects/<project>/memory/`, one directory per git repo, shared by all worktrees and subdirectories, and local to the machine:

```text
~/.claude/projects/<project>/memory/
├── MEMORY.md            # index, one line per memory, loaded every session
├── user_role.md
└── feedback_testing.md  # topic files, read on demand
```

- Only the first **200 lines or 25KB** of `MEMORY.md` load at startup. Claude Code reminds Claude to tighten the index as it nears the limit and errors when it goes over.
- Memory files are exempt from the `cleanupPeriodDays` sweep, and Claude Code stamps a `modified` ISO 8601 timestamp into files it writes.
- Subagents don't get the main conversation's auto memory, except forks. A subagent can keep its own via its `memory` field ([[subagents]]).

**Controls.** `/memory` toggles auto memory (writing `autoMemoryEnabled` to `~/.claude/settings.json`) and opens the folder, which is plain markdown. `"autoMemoryEnabled": false` in a project's settings turns it off there, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` turns it off by environment, and `"autoMemoryDirectory"` moves the folder (absolute or `~/`).

| Want | Do |
|---|---|
| Toggle it | `/memory` → auto memory toggle (writes `autoMemoryEnabled` to `~/.claude/settings.json`) |
| Off for one project | `"autoMemoryEnabled": false` in the project's settings |
| Off via env | `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` |
| Different location | `"autoMemoryDirectory": "~/my-custom-memory-dir"` (absolute or `~/`). From project settings it needs workspace trust, and is ignored while `blockReadsOutsideWorkingDirectories` is on |
| Browse or edit | `/memory` → open the auto memory folder. It's plain markdown |

## When edits apply

`/memory` lists every CLAUDE.md, CLAUDE.local.md, and memory location in user and project scope, and opens one in your editor, creating it if needed. `/context` shows which CLAUDE.md and rules files actually loaded, under **Memory files**.

Project-root and user CLAUDE.md are read once at session start, so **editing them mid-session has no effect** until `/clear`, `/compact`, or a restart. Nested CLAUDE.md files and path-scoped rules that haven't loaded yet do pick up edits.

## Troubleshooting

| Symptom | Check |
|---|---|
| Claude ignores CLAUDE.md | `/context` → **Memory files**. Confirm the location loads for this session, be more specific, resolve conflicts |
| `AGENTS.md` seems unread | A `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` in the working directory or above, other than `~/.claude/CLAUDE.md`; or `/config` → **Project instructions** missing, `claude-md`, or `managed-only` |
| Want system-prompt-level instructions | `--append-system-prompt` at launch (best for scripts; see [[cli-reference]]) |
| Unsure which files loaded and why | Log them with the `InstructionsLoaded` hook |
| Instruction gone after `/compact` | It was said only in chat, sits in a nested CLAUDE.md, or is a path-scoped rule that hasn't matched again. Move it to root CLAUDE.md |
| CLAUDE.md too large (the startup notice counts all instruction files and `@` imports together) | Move content to path-scoped rules or skills, or run `/doctor` for trim proposals |
