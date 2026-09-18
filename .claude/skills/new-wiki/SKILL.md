---
name: new-wiki
description: "Turn this kit into a new self-maintaining wiki on another subject. Use when the user wants to start their own project with agent-wiki-kit, build a knowledge base about a different topic, or reuse the harness for their own sources."
user-invocable: true
argument-hint: "the subject of the new wiki"
---

# Start a new wiki with this kit

The harness (lint, evals, freshness, memory, cross-agent setup) does not care what the wiki is about.
The shipped wiki about Claude Code is one instance. This procedure replaces it with the user's subject.
Do the steps in order and show the user the plan from step 1 before changing anything.

## 1. Agree the shape first

Ask for, or propose and confirm:
- **Subject and audience**, in one sentence each.
- **Topic folders:** 5 to 11 kebab-case folders under `wiki/`. Keep `project/`, which documents the harness.
- **First sources:** the 5 to 20 documents the first pages will be written from. Official documentation
  beats commentary. Every page must trace to a source, so no sources means no pages.

## 2. Clear the shipped content, keep the harness

- Delete every page under `wiki/` except `wiki/project/harness.md` and `wiki/project/cross-agent-setup.md`.
- Create the new topic folders. Set `DIRS` in `scripts/update-stats.py` to the new folder list, in order, and give each folder a heading in `HEADINGS` in `scripts/build-index.py`.
- Reset `wiki/log.md` to a single dated "initial release" entry, and `wiki/hot.md` to its header, the
  two Wiki State lines and an empty observations section.
- Empty `sources/manifest.tsv` and `sources/identifiers.txt` down to their comment lines.
- Replace the questions in `evals/wiki-eval.yaml` and `evals/answer-eval.yaml`. Write them only after
  pages exist, 2 to 4 per page, phrased the way a person would ask.

## 3. Rewrite the instructions for the new subject

Edit `CLAUDE.md` (`AGENTS.md` is a symlink to it, so every agent sees the change): the opening
paragraph, the folder list and any subject-specific rule. Keep the frontmatter spec, the rules about one
home per fact, current facts only and sourced identifiers, and the workflows.

If the subject is not Claude Code, the identifier lint's patterns will not match anything useful.
Edit `PATTERNS` in `scripts/lint_identifiers.py` and `ID_PATTERNS` in `scripts/sources.py` to the
identifiers that matter in the new domain (API names, config keys, CLI flags), or leave both empty.

## 4. Ingest the first sources

For each source, follow the Ingest workflow in `CLAUDE.md`: save it under `raw/` with a first-line
`<!-- SOURCE: <url> | fetched: <date> -->` header, write or update the page that owns the topic, add
the page to `wiki/index.md`, and append to `wiki/log.md`. `raw/` is gitignored on purpose: sources are
other people's text. Record them with `./scripts/sources.py manifest`, which is what gets committed.

## 5. Prove it works

```bash
./scripts/build-index.py && ./scripts/update-stats.py && ./scripts/hot-compact.py
./.venv/bin/python scripts/mem0/index_wiki.py --rebuild
./scripts/wiki-lint.sh && ./scripts/wiki-temporal.sh && python3 scripts/lint_identifiers.py
./.venv/bin/python -m pytest -q tests && ./.venv/bin/python scripts/wiki-eval.py
./scripts/doctor.sh
```

Fix what fails before reporting. Then update `README.md` (title, description, wiki map) and tell the
user what exists, what each page was written from, and which sources they should add next.

## Rules that carry over

One page owns each topic. Pages state current facts only, and corrections go in `wiki/log.md`. Never
invent an identifier. Never edit an existing file under `raw/`. When two current sources disagree, keep
a short `> [!contradiction]` callout instead of picking one.
