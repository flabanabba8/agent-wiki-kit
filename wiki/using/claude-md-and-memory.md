---
title: CLAUDE.md and Memory
type: reference
tldr: "CLAUDE.md, rules, imports, auto memory"
sources:
  - raw/docs/official/memory.md
  - raw/docs/official/best-practices.md
  - raw/docs/official/context-window.md
  - raw/docs/official/prompt-caching.md
  - raw/docs/official/commands.md
related: ["[[context-window]]", "[[skills]]", "[[hooks]]", "[[settings]]", "[[enterprise-admin]]", "[[prompting-and-workflows]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [claude-md, auto-memory, claude-rules, memory-md, project-instructions]
---

# CLAUDE.md and Memory

Every session starts with a fresh context window. Two mechanisms carry knowledge between sessions, and both load at the start of every conversation:

| | CLAUDE.md files | Auto memory |
|---|---|---|
| Written by | You | Claude |
| Contains | Instructions and rules | Learnings and patterns |
| Scope | Project, user, or org | Per repository, shared across worktrees |
| Loaded | Every session, full content | Every session, first 200 lines or 25KB of `MEMORY.md` |
| Use for | Coding standards, workflows, architecture | Your preferences, corrections, context Claude can't derive from code |

Both are **context, not enforcement**. Claude reads them and tries to follow them. For anything that must happen regardless of what Claude decides, use a hook ([[hooks]]) or permission rules ([[permissions-and-modes]]).

## CLAUDE.md

### When to add something

Add an entry when Claude makes the same mistake twice, when code review catches something Claude should have known, when you retype a correction from last session, or when a new teammate would need the same context. Keep CLAUDE.md to facts needed in every session: build commands, conventions, layout, and "always do X" rules. Multi-step procedures belong in [[skills]], and guidance for one area of the codebase belongs in a path-scoped rule.

### Locations

Listed in load order, broadest first:

| Scope | Location | Shared with |
|---|---|---|
| Managed policy | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`; Linux/WSL `/etc/claude-code/CLAUDE.md`; Windows `C:\Program Files\ClaudeCode\CLAUDE.md` | Everyone on the machine. Can't be excluded |
| User | `~/.claude/CLAUDE.md` | Just you, all projects |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team, via source control |
| Local | `./CLAUDE.local.md` (add it to `.gitignore`) | Just you, this project |

**How they load:**

- CLAUDE.md and CLAUDE.local.md files in the working directory **and every parent** load at launch. They're concatenated, not overridden: root-most first, working directory last, and `CLAUDE.local.md` after `CLAUDE.md` at each level.
- Files in **subdirectories** load on demand when Claude reads files there.
- Block-level HTML comments (`<!-- notes -->`) are stripped before injection, so maintainer notes cost no tokens.
- Files from `--add-dir` directories load only with `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`.
- A CLAUDE.md up to 4 MiB loads in full. Larger files are skipped.
- The content arrives as a user message after the system prompt, not inside the system prompt.

### Generate one with `/init`

`/init` analyzes the codebase and writes build commands, test instructions, and conventions. If CLAUDE.md already exists, it suggests improvements instead. It also pulls in relevant Cursor rules (`.cursor/rules/`, `.cursorrules`) and Copilot rules (`.github/copilot-instructions.md`). Set `CLAUDE_CODE_NEW_INIT=1` for an interactive multi-phase flow. That flow asks which artifacts to set up (CLAUDE.md, skills, hooks), explores with a subagent, asks follow-up questions, and shows a proposal before writing. It also reads `AGENTS.md`, `.devin/rules/`, `.windsurf/rules/`, and `.clinerules`. `/import` copies another coding agent's instruction files, MCP servers, commands, subagents, and skills into Claude Code.

### Write instructions that stick

- **Size:** under 200 lines per file. Longer files cost context and reduce adherence.
- **Structure:** use headers and bullets, not dense paragraphs.
- **Specificity:** make instructions verifiable. Write "Use 2-space indentation", not "Format code properly". Write "Run `npm test` before committing", not "Test your changes".
- **Consistency:** when two rules contradict, Claude may pick either. Review nested files and rules periodically.
- **Emphasis:** add "IMPORTANT" only to the one line Claude keeps skipping. If many lines are emphasized, none stands out.
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

To shape what survives compaction, add a "Compact Instructions" section, for example "When compacting, always preserve the full list of modified files and any test commands" ([[context-window]]).

### Imports

```text
See @README for project overview and @package.json for available npm commands.
- git workflow @docs/git-instructions.md
- @~/.claude/my-project-instructions.md
```

- Relative paths resolve from the importing file. Imports can nest up to **four hops**.
- Imports inside code spans and fenced blocks are ignored, so `` `@README` `` stays literal.
- Imported files load at launch, so imports organize content but don't save context.
- The first time a project file imports a path outside the working directory, Claude Code asks for approval. If you decline, those imports stay disabled. Imports in your own user-scope files (`~/.claude/CLAUDE.md`, `~/.claude/rules/`) load without asking.
- A gitignored `CLAUDE.local.md` exists only in the worktree where you made it. To share personal notes across worktrees, import a file from your home directory.

**AGENTS.md:** Claude Code reads `CLAUDE.md`, not `AGENTS.md`. Make a CLAUDE.md that starts with `@AGENTS.md` and add Claude-specific notes below it, or symlink with `ln -s AGENTS.md CLAUDE.md`. Symlinks need Administrator or Developer Mode on Windows, so use the import there.

## Rules: `.claude/rules/`

Put one topic per markdown file in `.claude/rules/`. Subdirectories are discovered recursively.

- **Unscoped rules** (no `paths`) load at launch with the same priority as `.claude/CLAUDE.md`.
- **Path-scoped rules** load only when Claude reads a matching file:

```markdown
---
paths:
  - "src/**/*.{ts,tsx}"
  - "tests/**/*.test.ts"
---
# API Development Rules
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
- **User rules** in `~/.claude/rules/` apply to every project and load before project rules, so project rules take priority.
- **Symlinks** into `.claude/rules/` work. A target outside the working directory is treated like an external import and needs approval.
- Path-scoped rules and nested CLAUDE.md files live in message history, so compaction summarizes them away until a matching file is read again. If a rule must survive compaction, remove its `paths:` or move it to the root CLAUDE.md.

## Teams and monorepos

- **Org-wide:** deploy the managed-policy file with MDM, Group Policy, or Ansible, or put the content in the `claudeMd` key of `managed-settings.json` (honored only in managed/policy settings). Use managed settings (`permissions.deny`, `sandbox.enabled`, `env`) for enforcement and managed CLAUDE.md for behavioral guidance ([[enterprise-admin]]).
- **Skip irrelevant files** with `claudeMdExcludes`, glob patterns matched against absolute paths. Arrays merge across settings layers. Managed-policy CLAUDE.md can't be excluded.

```json
{ "claudeMdExcludes": ["**/monorepo/CLAUDE.md", "/home/user/monorepo/other-team/.claude/rules/**"] }
```

## Auto memory

Claude saves notes for itself as it works, and not every session. Each note's frontmatter records its `type`:

- `user`: your role, expertise, and preferences
- `feedback`: corrections you give and approaches you confirm
- `project`: ongoing work, deadlines, and decisions not visible in code or git
- `reference`: where to find outside information such as trackers and dashboards

It skips anything derivable from the codebase and anything already in CLAUDE.md. When you say "remember that the API tests require a local Redis instance", it goes to auto memory. Say "add this to CLAUDE.md" to put it there instead.

**Storage.** Memory lives in `~/.claude/projects/<project>/memory/`, one directory per git repo, shared by all worktrees and subdirectories, and local to the machine:

```text
~/.claude/projects/<project>/memory/
├── MEMORY.md            # index, one line per memory, loaded every session
├── user_role.md
└── feedback_testing.md  # topic files, read on demand
```

- Only the first **200 lines or 25KB** of `MEMORY.md` load at startup. Claude Code reminds Claude to tighten the index as it nears the limit and returns an error when it goes over. Topic files are read on demand with normal file tools.
- Memory files are exempt from the `cleanupPeriodDays` transcript sweep.
- Claude Code stamps a `modified` ISO 8601 timestamp into the frontmatter of memory files it writes.
- Subagents don't get the main conversation's auto memory, except forks. A subagent can keep its own via its `memory` field ([[subagents]]).

**Controls.**

| Want | Do |
|---|---|
| Toggle it | `/memory` → auto memory toggle (writes `autoMemoryEnabled` to `~/.claude/settings.json`) |
| Off for one project | `"autoMemoryEnabled": false` in the project's settings |
| Off via env | `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` |
| Different location | `"autoMemoryDirectory": "~/my-custom-memory-dir"` (absolute or `~/`) |
| Browse or edit | `/memory` → open the auto memory folder. It's plain markdown |

## `/memory` and when edits apply

`/memory` lists every CLAUDE.md, CLAUDE.local.md, and memory location in user and project scope, opens a file in your editor (creating it if needed), and toggles auto memory. `/context` shows what actually loaded, under **Memory files**.

Project-root and user CLAUDE.md are read once at session start. **Editing them mid-session has no effect** until `/clear`, `/compact`, or a restart. Nested CLAUDE.md files and path-scoped rules that haven't loaded yet do pick up edits.

## Troubleshooting

| Symptom | Check |
|---|---|
| Claude ignores CLAUDE.md | Run `/context` and check **Memory files**. Confirm the file location loads for this session. Make instructions more specific. Look for conflicts between files |
| Must happen at a fixed point (before commit, after edit) | Write a hook instead ([[hooks]]) |
| Want system-prompt-level instructions | `--append-system-prompt` at launch (best for scripts; see [[cli-reference]]) |
| Unsure which files loaded and why | Log them with the `InstructionsLoaded` hook |
| Instruction gone after `/compact` | It was said only in chat, sits in a nested CLAUDE.md, or is a path-scoped rule that hasn't matched again. Move it to root CLAUDE.md |
| CLAUDE.md too large | Move content to path-scoped rules or skills, or run `/doctor` for trim proposals |
