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
related: ["[[context-window]]", "[[claude-md-and-memory]]", "[[subagents]]", "[[permissions-and-modes]]", "[[headless-mode]]", "[[coding-principles]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [claude-code-best-practices, explore-plan-implement-commit, common-workflows, prompt-tips, debugging-with-claude]
---

# Prompting and Workflows

Almost every best practice here follows from one constraint: **the context window fills fast, and performance degrades as it fills**. One debugging session or codebase exploration can use tens of thousands of tokens, and once the window is crowded Claude may start forgetting earlier instructions. Mechanics are in [[context-window]]; this page covers how to work.

## 1. Give Claude a way to verify its work

Claude stops when the work *looks* done. Give it something that returns pass or fail — tests, a build exit code, a linter, a fixture diff, a screenshot to compare — so it iterates until the check passes instead of waiting for you to spot mistakes.

| Strategy | Before | After |
|---|---|---|
| Verification criteria | "implement a function that validates email addresses" | "write a validateEmail function. example test cases: user@example.com is true, invalid is false, user@.com is false. run the tests after implementing" |
| Verify UI visually | "make the dashboard look better" | "[paste screenshot] implement this design. take a screenshot of the result and compare it to the original. list differences and fix them" |
| Root cause, not symptom | "the build is failing" | "the build fails with this error: [paste error]. fix it and verify the build succeeds. address the root cause, don't suppress the error" |

Choose how hard the check gates the stop:

| Gate | How | Details |
|---|---|---|
| In one prompt | Ask Claude to run the check and iterate | Works for any task |
| Across a session | `/goal <condition>`, re-checked by an evaluator every turn | Below |
| Deterministic | A Stop hook blocks the turn from ending until your check passes; Claude Code ends it anyway after 8 consecutive blocks | [[hooks]] |
| Second opinion | A verification subagent or a workflow that tries to refute the result | [[subagents]], [[workflows]] |

Ask for **evidence** — test output, the command and its result, a screenshot — not a claim of success. After the check passes, `/verify` builds and runs your app to confirm the change live.

### Keep working toward a goal with `/goal`

`/goal <condition>` sets a completion condition and Claude keeps working toward it without you prompting each step. After every turn a small fast model — Haiku on the Claude API — reads the condition and conversation and returns one of three verdicts: **not yet met**, and Claude takes the reason as guidance for another turn; **met**; or **impossible** — the last two clear the goal and record the outcome. One goal is active per session; a new one replaces it. Use one for substantial work with a verifiable end state: a migration until every call site compiles, or a backlog until empty.

| Invocation | Effect |
|---|---|
| `/goal all tests in test/auth pass and the lint step is clean` | Sets the condition and starts a turn with it as the directive; `◎ /goal active` shows elapsed time |
| `/goal` | Shows the condition, elapsed time, turns evaluated, token spend, and the evaluator's latest reason |
| `/goal clear` | Drops an active goal; `stop`, `off`, `reset`, `none`, `cancel` and `/clear` also drop it |
| `claude -p "/goal <condition>"` | Runs the loop to completion in one non-interactive run; `--output-format stream-json --verbose` shows progress |

The evaluator never runs commands or reads files: it judges only what Claude surfaced. Name a measurable end state, the check that proves it (`npm test` exits 0), and anything that must not change. Conditions run to 4,000 characters; `or stop after 20 turns` bounds the loop.

A goal doesn't change your permission mode: run it in auto mode for unattended turns ([[permissions-and-modes]]). Several turns without tool use stop the loop and hand control back, goal still set. Failed auth, an exhausted credit balance, an unclearable context overflow or an unavailable model clears it; other failures retry or pause, and pending background work defers evaluation until a check-in (`CLAUDE_CODE_GOAL_CHECKIN_MINUTES`). The evaluator is a session-scoped prompt-based Stop hook, so `/goal` needs hooks enabled and a trusted folder ([[hooks]]); resuming restores an active goal ([[sessions-and-checkpoints]]).

## 2. Explore → plan → implement → commit

Use plan mode to keep research separate from edits, so Claude doesn't solve the wrong problem.

1. **Explore.** Press `Shift+Tab` until the status bar shows `⏸ plan mode on`, or start with `claude --permission-mode plan`; Claude reads files without changing them.
   `read /src/auth and understand how we handle sessions and login.`
2. **Plan.** `I want to add Google OAuth. What files need to change? What's the session flow? Create a plan.` Press `Ctrl+G` to edit the plan in your editor.
3. **Implement.** Approve the plan (or `Shift+Tab` out), then: `implement the OAuth flow from your plan. write tests for the callback handler, run the test suite and fix any failures.`
4. **Commit.** `commit with a descriptive message and open a PR`

**Skip the plan** when you could describe the diff in one sentence — a typo, a log line, a rename. Planning pays off when the approach is uncertain, the change spans several files, or the code is unfamiliar. Plan-mode mechanics are in [[permissions-and-modes]].

## 3. Write specific prompts

| Strategy | Before | After |
|---|---|---|
| Scope the task | "add tests for foo.py" | "write a test for foo.py covering the edge case where the user is logged out. avoid mocks." |
| Point to sources | "why does ExecutionFactory have such a weird api?" | "look through ExecutionFactory's git history and summarize how its api came to be" |
| Reference patterns | "add a calendar widget" | "look at how existing widgets are implemented on the home page… HotDogWidget.php is a good example. follow the pattern…" |
| Describe the symptom | "fix the login bug" | "users report that login fails after session timeout. check the auth flow in src/auth/, especially token refresh. write a failing test that reproduces the issue, then fix it" |

Vague prompts are fine when you're exploring and can course-correct: `what would you improve in this file?` surfaces things you wouldn't think to ask.

**Feed rich context:**

- `@src/utils/auth.js` includes a file's full content. `@src/components` gives a directory listing. `@server:resource` pulls an MCP resource. An @-referenced file also brings in the CLAUDE.md files in its directory and parents.
- Paste or drag in images (`Ctrl+V`, `Alt+V` on Windows and WSL): screenshots of errors, mockups, diagrams.
- Pipe data: `cat error.log | claude`.
- Give URLs for docs. Allowlist domains you use often with `/permissions`.
- Tell Claude to use CLI tools like `gh`, `aws` or `gcloud`, the most context-efficient way to reach external services. Unfamiliar ones: `Use 'foo-cli-tool --help' to learn about foo tool, then use it to solve A, B, C.`

**For big features, let Claude interview you:**

```text
I want to build [brief description]. Interview me in detail using the AskUserQuestion tool.
Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs. Don't ask obvious questions, dig into the hard parts I might not have considered.
Keep interviewing until we've covered everything, then write a complete spec to SPEC.md.
```

Then implement in a **fresh session**. Good specs name files and interfaces, state what's out of scope, and end with an end-to-end verification step.

## 4. Everyday recipes

| Task | Prompt sequence | Tips |
|---|---|---|
| Learn a codebase | `give me an overview of this codebase` → `explain the main architecture patterns used here` → `how is authentication handled?` | Go broad, then narrow. Ask for a glossary of project terms |
| Find code | `find the files that handle user authentication` → `trace the login process from front-end to database` | Use the project's domain language. A code intelligence plugin adds go-to-definition |
| Refactor | `find deprecated API usage in our codebase` → `refactor utils.js to use ES2024 features while maintaining the same behavior` → `run tests for the refactored code` | Work in small, testable increments |
| Tests | `find functions in NotificationsService.swift that are not covered by tests` → `add test cases for edge conditions` → `run the new tests and fix any failures` | Claude matches existing test style. Ask it to find edge cases you missed |
| Pull requests | `summarize the changes I've made to the authentication module` → `create a pr` | Ask Claude to flag risks. `claude --from-pr 1234` finds a PR's session later |
| Docs | `find functions without proper JSDoc comments in the auth module` → `add JSDoc comments…` | Name the doc style you want |

Claude Code also works in non-code folders such as notes vaults or docs trees. Ask about its own features, or run `/powerup` for lessons ([[interface]]).

## 5. Debugging

1. Share the failure with the reproduction command: `I'm seeing an error when I run npm test`. Include the stack trace, reproduction steps, and whether it's intermittent or consistent.
2. Ask for options before a fix: `suggest a few ways to fix the @ts-ignore in user.ts`.
3. Apply one: `update user.ts to add the null check you suggested`.
4. Prefer "write a failing test that reproduces it, then fix it", and insist on the root cause rather than suppressing the error.

If a large file or log keeps flooding context, see [[context-window]]. For Claude Code's own problems, see [[troubleshooting]].

## 6. Manage the session

- **Course-correct early.** `Esc` stops Claude and keeps context; `Esc Esc` or `/rewind` restores conversation, code, or both ([[sessions-and-checkpoints]]). "Undo that" reverts changes.
- **Corrected twice on the same issue?** The context is full of failed approaches: `/clear` and start over with a better prompt that includes what you learned. A clean session beats a long corrected one.
- **`/clear` between unrelated tasks.**
- **Delegate investigation:** `Use subagents to investigate how our authentication system handles token refresh, and whether we have any existing OAuth utilities I should reuse.` The reads stay in the subagent's context ([[subagents]]).
- **Try risky ideas and rewind** if they fail. Checkpoints miss Bash-made changes, so they're no replacement for git.
- **Name sessions** with `/rename` and treat them like branches.

## 7. Review and scale

- **Adversarial review.** Before calling unattended work done, have a fresh-context subagent check the diff; `/code-review` checks correctness. For plan conformance: `Use a subagent to review the rate limiter diff against PLAN.md. Check that every requirement is implemented, the listed edge cases have tests, and nothing outside the task's scope changed. Report gaps, not style preferences.` A reviewer asked for gaps always finds some, so act only on ones affecting correctness or requirements.
- **Writer/Reviewer.** Session A implements; session B reviews `@src/middleware/rateLimiter.ts` with fresh context and A applies the feedback. A variant: one session writes tests, another writes code to pass them.
- **Parallel sessions and fan-out** with worktrees, background agents, or `/batch`: [[worktrees-and-background-work]]. Scripted `claude -p` loops scoped with `--allowedTools`: [[headless-mode]].

## Failure patterns

| Pattern | Fix |
|---|---|
| Kitchen-sink session mixing unrelated tasks | `/clear` between tasks |
| Correcting over and over | After two failed corrections, `/clear` and write a better first prompt |
| Over-specified CLAUDE.md, where rules get lost | Prune hard, or turn rules into hooks ([[claude-md-and-memory]]) |
| Trust-then-verify gap: plausible code misses edge cases | Always provide verification; if you can't verify it, don't ship it |
| Infinite exploration: unscoped "investigate" reads hundreds of files | Scope narrowly or use subagents |

These are starting points: sometimes accumulated context is valuable, planning is overhead, or a vague prompt is exactly right. For principles on thinking first and surgical changes, see [[coding-principles]].
