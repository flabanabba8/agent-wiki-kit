---
title: Prompting and Workflows
type: how-to
tldr: "Verify, plan first, prompt precisely"
sources:
  - raw/docs/official/best-practices.md
  - raw/docs/official/common-workflows.md
  - raw/docs/official/quickstart.md
  - raw/docs/official/how-claude-code-works.md
  - raw/docs/official/commands.md
  - raw/docs/official/goal.md
  - raw/articles/getting-the-most-out-of-opus-5-5.md
  - raw/docs/prompting-claude-opus-5-5.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
related: ["[[context-window]]", "[[claude-md-and-memory]]", "[[subagents]]", "[[permissions-and-modes]]", "[[prompting-claude-models]]", "[[models-and-effort]]", "[[coding-principles]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [claude-code-best-practices, explore-plan-implement-commit, common-workflows, prompt-tips, debugging-with-claude, steering-long-runs, opus-5-5-playbook]
---

# Prompting and Workflows

Almost every best practice here follows from one constraint: **the context window fills fast, and performance degrades as it fills**. Mechanics are in [[context-window]]; this page covers how to work in Claude Code. Prompt design for the Claude API (system prompts, effort calibration, progress updates) is in [[prompting-claude-models]].

## 1. Give Claude a way to verify its work

Claude stops when the work *looks* done. Give it something that returns pass or fail (tests, a build exit code, a linter, a screenshot to compare) so it iterates until the check passes.

| Strategy | Before | After |
|---|---|---|
| Verification criteria | "implement a function that validates email addresses" | "write a validateEmail function. test cases: user@example.com is true, user@.com is false. run the tests after implementing" |
| Verify UI visually | "make the dashboard look better" | "[paste screenshot] implement this design. screenshot the result, compare, and fix the differences" |
| Root cause, not symptom | "the build is failing" | "the build fails with this error: [paste error]. fix the root cause and verify the build succeeds" |

Choose how hard the check gates the stop:

| Gate | How | Details |
|---|---|---|
| In one prompt | Ask Claude to run the check and iterate | Any task |
| Across a session | `/goal <condition>`, re-checked every turn | Below |
| Deterministic | A Stop hook blocks the turn from ending until the check passes (at most 8 consecutive blocks) | [[hooks]] |
| Second opinion | A verification subagent or workflow that tries to refute the result | [[subagents]], [[workflows]] |

Ask for **evidence** (test output, a screenshot), not a claim of success. After the check passes, `/verify` builds and runs your app to confirm the change live.

### Keep working toward a goal with `/goal`

`/goal <condition>` sets a completion condition and Claude keeps working toward it without you prompting each step. After every turn a small fast model (Haiku on the Claude API) reads the condition and conversation and returns **not yet met** (Claude takes the reason as guidance for another turn), **met**, or **impossible**; the last two clear the goal. One goal is active per session. Use one for work with a verifiable end state, such as a migration until every call site compiles.

| Invocation | Effect |
|---|---|
| `/goal all tests in test/auth pass and the lint step is clean` | Sets the condition and starts a turn with it as the directive |
| `/goal` | Shows the condition, elapsed time, turns, token spend, and the evaluator's latest reason |
| `/goal clear` | Drops an active goal; so does `/clear` |
| `claude -p "/goal <condition>"` | Runs the loop to completion non-interactively |

The evaluator never runs commands or reads files: it judges only what appears in the transcript. Name a measurable end state, the check that proves it (`npm test` exits 0), and anything that must not change. Conditions run to 4,000 characters; `or stop after 20 turns` bounds the loop.

A goal doesn't change your permission mode: run it in auto mode for unattended turns ([[permissions-and-modes]]). Failed auth, an exhausted credit balance, an unclearable context overflow or an unavailable model clears it; pending background work defers evaluation until a check-in (`CLAUDE_CODE_GOAL_CHECKIN_MINUTES`). The evaluator is a session-scoped prompt-based Stop hook, so `/goal` needs hooks enabled and a trusted folder ([[hooks]]); resuming restores an active goal.

## 2. Explore → plan → implement → commit

Use plan mode to keep research separate from edits, so Claude doesn't solve the wrong problem.

1. **Explore.** Press `Shift+Tab` until the status bar shows `⏸ plan mode on`, or start with `claude --permission-mode plan`: `read /src/auth and understand how we handle sessions and login.`
2. **Plan.** `I want to add Google OAuth. What files need to change? Create a plan.` `Ctrl+G` edits the plan in your editor.
3. **Implement.** Approve the plan, then: `implement the OAuth flow from your plan. write tests for the callback handler, run the test suite and fix any failures.`
4. **Commit.** `commit with a descriptive message and open a PR`

**Skip the plan** when you could describe the diff in one sentence. Planning pays off when the approach is uncertain, the change spans several files, or the code is unfamiliar. Plan-mode mechanics are in [[permissions-and-modes]].

## 3. Write specific prompts

| Strategy | Before | After |
|---|---|---|
| Scope the task | "add tests for foo.py" | "write a test for foo.py covering the edge case where the user is logged out. avoid mocks." |
| Reference patterns | "add a calendar widget" | "look at how existing widgets are implemented on the home page… HotDogWidget.php is a good example. follow the pattern…" |
| Describe the symptom | "fix the login bug" | "login fails after session timeout. check token refresh in src/auth/. write a failing test that reproduces it, then fix it" |

Vague prompts suit exploration: `what would you improve in this file?`

**Hand over the whole task with a finish line.** Opus 5.5 keeps going on long, multi-part work, so give the task in one message, say what "done" looks like, and say when to stop and ask:

```text
Migrate the payment endpoints from the old client to the new one.
Done means: every endpoint uses the new client, the old client is
deleted, and the test suite passes.
Stop and ask me only if a test fails for a reason you can't explain.
```

- **Drop "think carefully" lines** from prompts and saved instructions. Opus 5.5 always thinks and decides how much; removing such a line made replies start sooner with no clear quality drop. Say "Answer directly" for a quick answer, or change effort ([[models-and-effort]]).
- **For design work, list the styles to leave out** ("no cream background, no italic accent words in headings, no pill-shaped buttons"). "Avoid a generic look" only swaps one default style for another.

**Feed rich context:**

- `@src/utils/auth.js` includes a file (plus the CLAUDE.md files in its directory and parents); `@src/components` gives a listing; `@server:resource` pulls an MCP resource.
- Paste or drag in images (`Ctrl+V`, `Alt+V` on Windows and WSL) rather than retyping a chart's numbers, pipe data (`cat error.log | claude`), and give doc URLs.
- Tell Claude to use CLI tools like `gh` or `aws`, the most context-efficient way to reach external services; for unfamiliar ones, `Use 'foo-cli-tool --help' to learn about foo tool`.

**For big features, let Claude interview you:**

```text
I want to build [brief description]. Interview me in detail using the AskUserQuestion tool.
Skip obvious questions; dig into the hard parts. Then write a complete spec to SPEC.md.
```

Then implement in a **fresh session**. Good specs name files and interfaces, state what's out of scope, and end with an end-to-end verification step.

## 4. Steer a long run

On a long task Opus 5.5 sometimes stops to report instead of continuing: a summary naming the next step, an offer to continue, or non-blocking choices. It follows instructions that name the stops you want, so put a rule in CLAUDE.md ([[claude-md-and-memory]]):

```markdown
When a step doesn't need my input, keep going. Put status notes in the
same message as your next action.
Stop and ask only when you can't continue without me, or before anything
destructive: deleting data, force-pushing, or changing anything outside
this repository.
```

- If a run stops with "Want me to continue?", reply "continue"; if it happens often, add the rule above. Fewer stops means fewer checks, so keep permission prompts on for destructive commands ([[permissions-and-modes]]).
- For pair programming, ask for the opposite instead: a one-line plan before starting and a short recap at the end.
- **Add to a running task** by typing a follow-up and pressing Enter while Claude works: Claude reads it as soon as the current tool calls finish, in the same turn. The send-now key (`Ctrl+Enter`, or `Ctrl+X Ctrl+S`) sends queued messages immediately ([[interface]]).
- **Fan out big audits and migrations** to subagents, and have the main session check each one's evidence: `Give each service to its own subagent. When a subagent reports back, check its evidence before you accept it. Finish with one table: service, affected yes or no, and the evidence.` ([[subagents]])
- **Keep the task list in a file**: `Keep a checklist in TASKS.md. Tick each item when it's done, and add anything new you find.` A file survives compaction of older turns, and you read it instead of the scrollback.

## 5. Everyday recipes and debugging

Go broad, then narrow, when learning a codebase (`give me an overview of this codebase` → `how is authentication handled?`), refactor in small testable increments, and ask for tests of uncovered edge cases in the existing style. `claude --from-pr 1234` finds a PR's session later.

**Debugging:** share the failure with its reproduction command and stack trace, ask for options before a fix, and prefer "write a failing test that reproduces it, then fix it" over suppressing the error. For Claude Code's own problems, see [[troubleshooting]].

## 6. Manage the session

- **Course-correct early.** `Esc` stops Claude and keeps context; `Esc Esc` or `/rewind` restores conversation, code, or both ([[sessions-and-checkpoints]]).
- **Delegate investigation:** `Use subagents to investigate how our authentication system handles token refresh.` The reads stay in the subagent's context ([[subagents]]).
- **Try risky ideas and rewind** if they fail. Checkpoints miss Bash-made changes, so they're no replacement for git.
- **Name sessions** with `/rename` and treat them like branches.

## 7. Check the result, review and scale

- **Read what it needs from you first.** A long Opus 5.5 run ends with a plain summary of what it did, what it found, and what it needs from you; look for open decisions and approvals before the rest. Set the format in CLAUDE.md, for example `End every run with three headings: Blocked on me, Changed, Found.`
- **Review before a person does:** `Review the diff on this branch against main. List only problems you'd block the merge for. For each one, give the file and line, why it's wrong, and how to show it fails.`
- **Ask it to mark what it couldn't confirm** in research and analysis: `Mark anything you couldn't confirm, and say where you looked.`
- **Adversarial review.** Before calling unattended work done, have a fresh-context subagent check the diff against the plan (`Check that every requirement is implemented and nothing outside the task's scope changed. Report gaps, not style preferences.`); `/code-review` checks correctness. A reviewer asked for gaps always finds some, so act only on ones affecting correctness or requirements.
- **Writer/Reviewer.** Session A implements; session B reviews with fresh context. A variant: one session writes tests, another writes code to pass them.
- **Parallel sessions and fan-out** with worktrees, background agents, or `/batch`: [[worktrees-and-background-work]]. Scripted `claude -p` loops scoped with `--allowedTools`: [[headless-mode]].

## Failure patterns

| Pattern | Fix |
|---|---|
| Kitchen-sink session mixing unrelated tasks | `/clear` between tasks |
| Correcting over and over | After two failed corrections the context is full of failed approaches: `/clear` and write a better first prompt |
| Over-specified CLAUDE.md, where rules get lost | Prune hard, or turn rules into hooks ([[claude-md-and-memory]]) |
| Trust-then-verify gap: plausible code misses edge cases | Always provide verification; if you can't verify it, don't ship it |
| Infinite exploration: unscoped "investigate" reads hundreds of files | Scope narrowly or use subagents |

These are starting points, not rules. For thinking first and surgical changes, see [[coding-principles]].
