---
name: audit-scheduled-jobs
description: Audit this repo's scheduled jobs (weekly maintenance cron and anything else it installed) from schedule to verified delivery. Use when the user asks whether maintenance is working, when doctor.sh reports unmerged maintenance branches or an old hot.md, or after changing a cron entry.
user-invocable: true
argument-hint: "[job-name or empty for all]"
---

# Audit scheduled jobs

A job that fired is not a job that delivered. Weekly maintenance can exit 0 and still leave the wiki stale: it skips a dirty tree, and its branches pile up unmerged. Follow each job from schedule to the thing a person actually reads.

1. **Inventory.** `crontab -l | grep -E 'weekly-maintenance'` plus `systemctl --user list-timers`. For each job record: schedule, working directory, the script, where output goes, and why the job exists (one line). No documented reason means flag it.
2. **Trace to delivery.** Weekly maintenance: cron entry -> `outputs/.maintenance.log` -> branch `maintenance/<date>` -> `outputs/reverify-queue.md` -> merged into the main branch. A run counts as delivered only at the last step.
3. **Read the evidence, one window.** Use the last four weeks. Separate: skipped runs (`working tree has uncommitted changes; skipping`, `already exists`), failed runs, and runs that produced a branch nobody merged. Count each.
4. **Check the silent failures.** A skip exits 0. An unmerged branch is not an error. `doctor.sh` warns about the second; nothing warns about the first, so grep the log for it.
5. **Check overlap and staleness.** Two maintenance branches from different weeks that touch the same raw files conflict; only the newest is worth merging. Compare `wiki/hot.md` age and the newest changelog version against `claude --version`.
6. **Propose the smallest repair** and stop. Changing a schedule, merging a branch or deleting one needs the user's approval. Say how to undo it (the old crontab line, the branch hash).
7. **Report** with the states below, then log a line in `wiki/log.md`.

<supporting-info>

Report each job as one of:

| State | Meaning |
|-------|---------|
| DELIVERING | Ran on schedule and its output reached the place it is read |
| STALLED | Runs, but output is skipped, empty or unmerged |
| BROKEN | Fails or never fires |
| UNKNOWN | Evidence missing; say what to look at |

Never promote STALLED to DELIVERING because the cron exit code was 0. A scheduler success does not establish useful output or successful delivery.

Method adapted from `skills/scheduled-job-audit` and `skills/test-evidence-integrity` in Sahil-SS9/agent-personas (MIT, commit 068a989). Sources: `raw/articles/agent-personas-scheduled-job-audit-2026-10-11.md`, `raw/articles/agent-personas-test-evidence-integrity-2026-10-11.md`.

</supporting-info>
