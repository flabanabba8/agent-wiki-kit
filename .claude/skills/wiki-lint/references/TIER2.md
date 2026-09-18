# Tier 2 — LLM-Powered Deep Analysis

Only run if structural score < 90 or user requests it.

## Contradiction Detection

1. Read `wiki/index.md` to identify **concept pages that share `related:` links** — these are the pages most likely to have overlapping claims.

2. For each pair of pages that share 2+ related links, read both and check for:
   - **Conflicting numbers** (e.g., one says "under 200 lines" and another says "under 60 lines" for the same thing)
   - **Conflicting recommendations** (e.g., one says "use hooks" and another says "use CLAUDE.md" for the same goal)
   - **Outdated claims** superseded by information in a newer page

3. **Record findings** using this exact format in the affected page:
   ```markdown
   > [!contradiction]
   > [[page-a]] says X. [[page-b]] says Y.
   > Last reviewed: 2026-05-14
   > Resolution: pending | resolved — explanation
   ```

4. Add `contradicts: [page-name]` to frontmatter of both pages.

5. Report all contradictions found.

## Model Collapse Detection

Only run if user requests it or as part of a monthly audit.

1. Pick **5 wiki pages** that cite raw sources — prioritize pages that have been updated multiple times.

2. For each page, read the wiki page AND its cited raw source(s).

3. Check for **drift**: claims in the wiki that are no longer supported by the raw source. Common patterns:
   - Specific numbers or limits that were smoothed out ("about 200" when the source says "exactly 200 lines")
   - Qualifications dropped ("usually" or "in most cases" removed, making a conditional claim absolute)
   - Details lost (a 3-step process reduced to 2 steps)
   - Vocabulary homogenized (varied terms replaced with a single term)

4. For each drift found, update the wiki page to match the raw source and note the correction in `wiki/log.md`.

## After Tier 2

Update `wiki/hot.md` with:
- New contradictions found
- Pages corrected for drift
- Open investigations needing human review
- Update the `updated:` date in hot.md frontmatter
