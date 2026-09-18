# AutoResearch — wiki quality loop

You improve the wiki one page at a time, keeping only changes that measurably help.

## Target selection (impact × risk)

1. `./scripts/freshness.py --json`: `drifted` and `snapshot` pages carry the most risk.
2. Inbound links (`grep -rl "\[\[<slug>\]\]" wiki | wc -l`) measure impact; hubs come first.
3. `confidence: medium`, `[!contradiction]` callouts and retrieval-eval misses (`outputs/eval-*.json`, latest) add risk.
4. Skip `index`, `hot`, `log` and pages edited in the last 7 days.

## Rubric (100)

| Criterion | Points | Check |
|---|---|---|
| Claims traceable to cited raw files | 25 | Verify 3 claims against the files in `sources:` |
| Identifiers sourced | 10 | `python3 scripts/lint_identifiers.py` reports nothing for the page |
| One home per fact | 15 | No topic restated that another page owns; links instead |
| Current facts only | 10 | No history narration, no expired `valid_until` |
| Practitioner detail | 20 | Exact commands, config, limits for someone doing the task |
| Links and tldr | 10 | 3+ relevant links; tldr helps decide whether to read |
| Concision | 10 | No filler or repetition |

## Outcome memory

Self-improvement judges get worse at predicting which edits stick as iterations pile up (see [[self-improving-agents]]). Before editing, read `outputs/autoresearch-outcomes.jsonl` for prior attempts on the page and criterion, and never retry an edit that was reverted. After each iteration append `{"date","page","criterion","before","after","lint_before","lint_after","kept","why"}`.

## Loop

1. `./scripts/wiki-lint.sh --json` and `./.venv/bin/python scripts/wiki-eval.py` for baselines.
2. Pick the target, check the outcome memory, score the rubric.
3. Fix the lowest criterion using raw sources only.
4. Re-run lint; re-score. Keep and commit if both held or improved; otherwise revert. Record the outcome.
5. After 10 pages or 30 minutes: reindex, re-run the eval, and report the lint and eval deltas.

## Constraints

Never fabricate; never edit existing raw files; never lower lint; no private project details; never run subagents on Fable.
