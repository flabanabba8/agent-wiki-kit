---
name: autoresearch
description: Run the autonomous wiki quality loop — pick the highest-risk page, score it against the rubric, fix the weakest criterion, keep or revert. Use when the user says "improve the wiki" or runs /loop /autoresearch.
user-invocable: true
disable-model-invocation: true
argument-hint: optional page slug to target
---

# AutoResearch

Follow `program.md`: target selection, rubric, outcome memory and the loop. Run lint and the retrieval eval before and after; stop after 10 pages or 30 minutes and report the lint and eval deltas.
