# AutoResearch Scoring Rubric — Detailed Guidance

## Completeness (0-10)

| Score | Criteria |
|-------|----------|
| 0-2 | Page is a stub or placeholder, missing major sections |
| 3-4 | Covers the topic superficially, missing key details |
| 5-6 | Covers the main points but has gaps in edge cases or advanced usage |
| 7-8 | Comprehensive coverage, includes examples and common patterns |
| 9-10 | Authoritative reference — covers all aspects including edge cases, limitations, and alternatives |

**How to improve:** Add missing sections, cover edge cases, add code examples, document limitations.

## Accuracy (0-10)

| Score | Criteria |
|-------|----------|
| 0-2 | Contains factual errors or outdated information that could mislead |
| 3-4 | Mostly correct but some claims are unverified or vaguely sourced |
| 5-6 | Claims are generally correct, most trace to sources |
| 7-8 | All claims traceable to raw sources, code examples tested |
| 9-10 | Cross-verified against multiple sources, contradictions flagged with callouts |

**How to improve:** Verify claims against raw sources, add source citations, flag contradictions.

## Freshness (0-10)

| Score | Criteria |
|-------|----------|
| 0-2 | last_verified > 180 days ago or references deprecated features |
| 3-4 | last_verified > 90 days ago |
| 5-6 | last_verified within 90 days but sources may have changed |
| 7-8 | last_verified within 30 days, sources confirmed current |
| 9-10 | Verified this week, all sources checked |

**How to improve:** Re-verify claims against current sources, update last_verified, check for new features.

## Structure (0-10)

| Score | Criteria |
|-------|----------|
| 0-2 | Missing frontmatter or broken format |
| 3-4 | Has frontmatter but missing required fields (tldr, confidence, etc.) |
| 5-6 | Complete frontmatter, but weak wikilinks or no code blocks |
| 7-8 | Complete frontmatter, good wikilinks, code blocks with language tags |
| 9-10 | Perfect frontmatter, rich cross-references, tables, code examples, callouts |

**How to improve:** Add missing frontmatter fields, add wikilinks to related pages, add code examples.

## Usefulness (0-10)

| Score | Criteria |
|-------|----------|
| 0-2 | Purely theoretical, no practical application shown |
| 3-4 | Mentions usage but doesn't show how |
| 5-6 | Includes some practical examples or commands |
| 7-8 | Clear actionable guidance, copy-paste commands, real scenarios |
| 9-10 | Complete workflow from problem to solution, addresses common mistakes |

**How to improve:** Add real-world examples, copy-paste commands, common mistake tables, troubleshooting.

## Conciseness (0-10)

| Score | Criteria |
|-------|----------|
| 0-2 | Massive wall of text, no structure, buried signal |
| 3-4 | Verbose with significant redundancy |
| 5-6 | Reasonable length but could be tighter |
| 7-8 | Well-edited, no filler, right level of detail |
| 9-10 | Every sentence earns its place, scannable via tables/lists/headers |

**How to improve:** Remove filler, deduplicate, convert prose to tables/lists, move deep content to separate pages.

## Quick Diagnostic

| Question | If No → Action |
|----------|---------------|
| Does the page have complete frontmatter? | Add missing fields |
| Are all claims sourced? | Trace back to raw/ or flag as low confidence |
| Is last_verified within 90 days? | Re-verify and update |
| Does it have code examples? | Add practical examples |
| Would a newcomer understand it? | Simplify jargon, add context |
| Is it under 500 lines? | Split into page + sub-pages |
