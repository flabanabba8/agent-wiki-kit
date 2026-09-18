---
title: CI/CD and Code Review
type: how-to
tldr: "Claude in CI, and automated PR review"
sources:
  - raw/docs/official/github-actions.md
  - raw/docs/official/github-actions-cloud-providers.md
  - raw/docs/official/gitlab-ci-cd.md
  - raw/docs/official/code-review.md
  - raw/docs/official/ultrareview.md
  - raw/docs/official/github-enterprise-server.md
  - raw/docs/official/cli-reference.md
  - raw/docs/official/commands.md
  - raw/docs/official/feature-availability.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[claude-code-on-the-web]]", "[[cloud-providers]]", "[[headless-mode]]", "[[costs-and-usage]]", "[[claude-md-and-memory]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [github-actions, gitlab-ci-cd, code-review-command, automated-pr-review, ultrareview]
valid_until: 2027-03-15
---

# CI/CD and Code Review

Four separate things run Claude against a pull request. Pick by who hosts the run and how much workflow you want to own.

| | Where it runs | Setup | Best for |
|---|---|---|---|
| **Code Review** | Anthropic infrastructure | An Owner enables it once; no workflow file | Automatic inline review on every PR (Team and Enterprise) |
| **GitHub Actions** | Your GitHub runners | Workflow file plus an auth secret | `@claude` mentions, issue-to-PR, scheduled automation |
| **GitLab CI/CD** | Your GitLab runners | One job in `.gitlab-ci.yml` plus a masked variable | The same on GitLab (beta, maintained by GitLab) |
| **`/code-review`** | Your machine, or the cloud with `ultra` | None | Checking a diff before you push |

## GitHub Actions

`anthropics/claude-code-action` runs Claude Code inside your repository's workflows. Either path needs admin access to the repository.

- **Quick setup**: run `/install-github-app` in the repository. It installs the Claude GitHub App, stores the auth secret, and pushes a branch with the workflow files plus a ready-to-create pull request. It works only with github.com remotes, and it wants the GitHub CLI installed and authenticated first. Re-running it on a repository that already has `claude.yml` offers **Update workflow file with latest version**.
- **Manual setup**: install the [Claude GitHub App](https://github.com/apps/claude), add the secret yourself, and copy `examples/claude.yml` into `.github/workflows/`.

### Authentication and secrets

| Secret | What it is |
|---|---|
| `ANTHROPIC_API_KEY` | A Claude API key; pass it to the `anthropic_api_key` input |
| `CLAUDE_CODE_OAUTH_TOKEN` | A subscription token from `claude setup-token` (Pro, Max, Team, Enterprise); pass it to `claude_code_oauth_token` |

Never commit either one. For an organization, install the app once at the org level, store the secret as an organization Actions secret, and either copy the workflow into each repository or call one reusable workflow. Prefer an API key for a shared secret, since an OAuth token is tied to one person's subscription.

To hold no long-lived secret at all, use workload identity federation: the action exchanges the workflow's GitHub OIDC token for Claude API access through a Console service account, using the `anthropic_federation_rule_id`, `anthropic_organization_id`, and optionally `anthropic_service_account_id` and `anthropic_workspace_id` inputs. The workflow needs `id-token: write` either way, since that permission also backs the action's default GitHub App authentication.

### A working workflow

```yaml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
jobs:
  claude:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
      id-token: write
      actions: read
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 1
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

`actions: read` lets Claude read CI results; the checkout step gives it a working copy; the `if` condition keeps runners from starting on unrelated comments.

### Modes and who can trigger runs

- **Interactive mode** (no `prompt` input): Claude waits for the trigger phrase, `@claude` by default and configurable with `trigger_phrase`, in a comment, a PR review, or a new issue's title or body, and replies in a comment.
- **Automation mode** (a `prompt` input): Claude runs on any GitHub event, including `schedule`. Results go to the run log unless the prompt directs Claude to post and it has a tool that can.

Two actor checks run before Claude starts, and the run fails if either rejects: the triggering user needs write access (widen it with `allowed_non_write_users` plus your own `github_token`), and bot actors are rejected unless listed in `allowed_bots`, which also covers scheduled runs GitHub attributes to a bot user.

### Useful inputs

`claude_args` passes any CLI argument through — `--max-turns`, `--model`, `--mcp-config`, `--allowedTools`, `--debug`. `settings` takes settings JSON or a path to it. `plugin_marketplaces` and `plugins` install plugins before the run, so `prompt` can invoke a plugin skill such as `/code-review:code-review`; for a repository-local skill, check out first and pass `/skill-name` ([[skills]]). A plain-text prompt gets no shell or GitHub access until you grant tools with `--allowedTools` or a `permissions.allow` rule ([[permissions-and-modes]]).

To route inference through your own cloud account, set `use_bedrock`, `use_vertex` or `use_foundry` to `"true"` and authenticate via OIDC federation, storing `AWS_ROLE_TO_ASSUME`, the `GCP_*` secrets or the `AZURE_*` secrets instead of a Claude key ([[cloud-providers]]). On public repositories those credential steps run before the write-access check, so add your own access check first if you don't want unauthorized comments to burn runner minutes.

Self-hosted GitHub works, with manual workflow setup only: `/install-github-app` is github.com-only, and the GitHub MCP server doesn't work against GitHub Enterprise Server.

### Costs

Each run spends GitHub Actions minutes plus tokens (or subscription usage, with an OAuth token). Cap them with `--max-turns`, workflow timeouts and concurrency limits, specific requests, and a concise `CLAUDE.md` — Claude reads it every run ([[claude-md-and-memory]], [[costs-and-usage]]). If CI doesn't run on Claude's commits, stop passing `github_token: ${{ secrets.GITHUB_TOKEN }}` so the action authenticates as the GitHub App.

## GitLab CI/CD

The GitLab integration is in beta and maintained by GitLab. Add `ANTHROPIC_API_KEY` as a masked CI/CD variable under **Settings → CI/CD → Variables**, then one job to `.gitlab-ci.yml`:

```yaml
claude:
  stage: ai
  image: node:24-alpine3.21
  rules:
    - if: '$CI_PIPELINE_SOURCE == "web"'
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  before_script:
    - apk add --no-cache git curl bash
    - curl -fsSL https://claude.ai/install.sh | bash
    - export PATH="$HOME/.local/bin:$PATH"
  script:
    - /bin/gitlab-mcp-server || true
    - >
      claude
      -p "${AI_FLOW_INPUT:-'Review this MR and implement the requested changes'}"
      --permission-mode acceptEdits
      --allowedTools "Bash Read Edit Write mcp__gitlab"
```

For GitLab API operations the job uses `CI_JOB_TOKEN`, or a Project Access Token with `api` scope stored as a masked `GITLAB_ACCESS_TOKEN`. Mention-driven triggers need your own listener: a project webhook on comment (note) events that calls the pipeline trigger API with `AI_FLOW_INPUT`, `AI_FLOW_CONTEXT` and `AI_FLOW_EVENT` when a comment contains `@claude`. For Bedrock or Google Cloud's Agent Platform, mint the job's OIDC token with an `id_tokens:` block and exchange it for cloud credentials — no stored keys. Bound cost with `--max-turns` and GitLab's job-level `timeout`. If Claude stays silent, check that the pipeline was triggered at all, that the provider variables exist, that the comment says `@claude`, and that `mcp__gitlab` is in `--allowedTools`.

## Code Review on pull requests

Code Review is a research preview for Team and Enterprise subscriptions, unavailable to organizations with Zero Data Retention. An Owner enables it at claude.ai/admin-settings/claude-code, installs the Claude GitHub App, selects repositories, and sets each repository's **Review Behavior**: once after PR creation, after every push, or manual. A fleet of agents analyzes the diff against the whole codebase in parallel, a verification step filters false positives, and findings post as inline comments plus a summary. Reviews average 20 minutes.

Anyone with write, maintain or admin permission can comment `@claude review` as a top-level comment to start one review, `@claude review always` to also subscribe the PR to push-triggered reviews, or `@claude review once` (same as the bare command). Manual triggers work on draft PRs, and a fork pull request is reviewed only when someone comments.

| Marker | Severity | Meaning |
|---|---|---|
| 🔴 | Important | A bug to fix before merging |
| 🟡 | Nit | Minor, worth fixing, not blocking |
| 🟣 | Pre-existing | A bug the PR didn't introduce |

The **Claude Code Review** check run always concludes neutral, so it never blocks a merge; to gate merges yourself, parse the severity counts from the check run's output text with `gh api` and jq. Findings also appear as annotations in **Files changed**, which survive when GitHub rejects an inline comment on a moved line.

Tune the review with two files: `CLAUDE.md` gives project context, and newly introduced violations of it become nits; `REVIEW.md` at the repository root is review-only instruction text (no `@` imports) that reaches the finding, verification and ranking agents — use it to redefine severity, cap nit volume, skip paths, add repo-specific checks, raise the verification bar, and shape the summary.

Billing is separate from your plan's included usage, through usage credits: roughly $15-25 per review, scaling with PR size. Reviewing on every push multiplies that by the number of pushes. Set a monthly cap at claude.ai/admin-settings/usage; when it's hit, Claude posts one comment saying the review was skipped and reviews resume next period or when an admin raises the cap. Watch activity and spend at claude.ai/analytics/code-review. A failed or timed-out run never blocks the PR and never retries itself — comment `@claude review` or click **Re-run**.

## Review locally with /code-review

`/code-review` reviews your branch's commits ahead of upstream plus uncommitted changes, reporting correctness bugs and reuse, simplification and efficiency cleanups; `/review` is an alias. Pass a target instead: a path, a PR number, a branch, or a range like `main...my-feature`.

- `--fix` applies findings to the working tree. A background review's edits sit outside session checkpoints, so `/rewind` won't undo them.
- `--comment` posts findings as inline comments on a GitHub pull request, or one note on a GitLab merge request through the `glab` CLI (pass the MR as a URL or `!123`).
- Effort levels `low` through `max` trade coverage for confidence; with no level, the review reuses the last level you typed.
- On any model that has no tuned settings of its own, the review runs leaner inline review prompts rather than spawning many review subagents.

It runs as a background subagent with its own context window, so it doesn't fill your conversation, and runs in the foreground when another review is already going, in non-interactive runs ([[headless-mode]]), or with `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` set to `1`. Claude can start it unprompted, and a scheduled task can too; a `skillOverrides` entry of `"code-review": "user-invocable-only"` restricts it to commands you type.

## The multi-agent ultra review

`/code-review ultra` runs the deep review on Claude Code on the web infrastructure: a fleet of reviewer agents in a remote sandbox, every finding independently reproduced and verified, nothing running locally. Where it's available, `/ultrareview` is an alias. It needs claude.ai authentication, and it isn't available on Amazon Bedrock, Google Cloud's Agent Platform or Microsoft Foundry, or with Zero Data Retention — in those cases `/code-review ultra` runs a local review instead.

- Scope with no argument: your branch against the default branch, including staged and uncommitted work. Pass a branch (`/code-review ultra develop`) to change the base, a PR number (`/code-review ultra 1234`) to review a pull request, or plain words to attach a note to the review.
- Limits: up to 500 changed files and 8,000 changed lines for a branch review; if the repository is too large to bundle, push a draft PR and review by number.
- On a github.com PR you can post the findings as one plain comment from your own GitHub account — `--no-post` is the default, and posting happens through a web session ([[claude-code-on-the-web]]).
- A run takes 5 to 10 minutes as a background task; track or stop it with `/tasks`.
- Pricing: 3 one-time free runs on Pro and Max, none on Team or Enterprise, then roughly $5-25 per review in usage credits, which must be turned on (check with `/usage-credits`).

From CI or a script, use the subcommand, which blocks until findings arrive and prints them to stdout: `claude ultrareview 1234 --json`, with `--timeout <minutes>` (default 45) and `--post`. It exits 0 when the review completes, 1 on failure or timeout, and 130 on Ctrl-C; progress and the live session URL go to stderr. Running it is your consent to the charge. In a `claude -p '/code-review ultra'` run Claude Code launches the review and prints a tracking link without waiting, and stops before launching if the run would bill usage credits.
