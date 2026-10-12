---
title: Change Log
updated: 2026-09-19
---

# Change Log

Append-only. Newest entry first. Older months move to `log-YYYY-MM.md`. Record what changed and why;
corrections belong here, never on the pages.

> Older entries: `wiki/log-2026-09.md` (not indexed).

## 2026-10-11 - queue marks, wiki map, log archive, duplicate check

Four ideas taken from two other wiki projects. The re-verification queue is merged across weeks and maintenance branches so `[~]` and `[-]` marks and unfinished items survive ([[harness]]). A generated, bounded wiki map sits in `CLAUDE.md`. `wiki/log.md` keeps the current month and archives earlier ones to `wiki/log-YYYY-MM.md`, newest first, and the session-start hook prints the newest log and hot lines ([[mem0]]). `wiki-lint.sh` warns on near-duplicate pages. The doctor's queue count no longer prints a second `0`.

## 2026-10-11 - scheduled-job audit, evidence states and fact grades

Took three more methods from Sahil-SS9/agent-personas (MIT, commit 068a989). New skill `audit-scheduled-jobs` follows the weekly maintenance cron to a merged result and reports DELIVERING, STALLED, BROKEN or UNKNOWN. The `ingest` skill now grades each fact high, medium or low and reports checks as PASS, PARTIAL, BLOCKED or INVALID. Sources pinned in `sources/manifest.tsv`.

## 2026-10-11 - parity with the private source wiki

Brought the 2026-09-25 content batch across. Claude Code changelog to 2.1.282, the Opus 5.5 release and migration guidance, the plugin docs split into 20 pages, and three new pages: [[plugin-marketplaces]], [[code-modernization]] and [[prompting-claude-models]]. [[claude-projects]] now has one home under surfaces, replacing the earlier copy under automation. 64 pages were merged three-way from the common ancestor; where both sides had edited the same passage the newer verification won, and passages that only added sourced facts were kept. `refetch-docs.sh` now refuses an HTML or bot-challenge response instead of overwriting a snapshot with it. The disposable-vision skill gained its local-inference backend. Manifest rebuilt: 442 sources, all matching.

## 2026-10-11 - changelog 2.1.283 to 2.1.296

Fourteen releases ingested from the saved changelog. Sonnet 5.5 and Haiku 5.5 landed as the default Sonnet and Haiku models ([[claude-models]]); terminal and VS Code sessions start in auto mode on every plan and provider ([[permissions-and-modes]]); Ultracode became its own `/effort` toggle ([[models-and-effort]]); Claude Mods arrived on [[plugins]]; and `allowedProviders`, `availableModelsMatch` and `deniedModels` joined the managed settings ([[enterprise-admin]]). New environment variables, hook `onFailure`, subagent fields, gateway upstream options and the background-command time limit went to their owning pages; the timeline is in [[whats-new]]. Fixes and VS Code, cloud-session and Claude Tag UI changes that need no wiki fact were left in the raw file.
## 2026-10-09 — disposable image workers and bounded agent contracts

Added the portable disposable-vision skill, offline CI tests, prerequisite checker, and non-overwriting installer for Codex, Claude Code, and Hermes. Shared project instructions route image work through fresh workers; generated output receives an independent review. No credentials, user paths, global settings, or generated image artifacts are included.

Reviewed Sahil-SS9/agent-personas at commit 068a9894bb87291aab5d369404dd27047906b5e9. Adopted task briefs and evidence-scoped completion reports in the existing native agents, and documented the distinction between packaging, discovery, and behavior in [[multi-agent-systems]]. Saved pinned source snapshots locally under raw/ and registered their origins. The upstream catalogue and runtime are not imported.

Validation: 63 unit tests passed; retrieval found the expected page in all 47 cases. Lint scored 99/100 with one source-hash freshness warning, no temporal failures, and no unsourced identifiers. The imported worker runtime matches the previously live-tested installed bundle byte for byte. New worker/installer files passed detect-secrets and a personal-deployment-pattern check. No publication was performed; a full published-ref/history audit remains required before any public push.

