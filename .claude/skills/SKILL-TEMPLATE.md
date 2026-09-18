# Skill Template Standard

All skills in this project follow this rigid structure. An agent can navigate any skill without re-learning the format.

## Required YAML Frontmatter

```yaml
---
name: skill-name
description: Brief capability. Use when [triggers].
user-invocable: true
argument-hint: optional argument description
---
```

## Required Sections (in order)

### 1. Title (H1)
One-line description of what the skill does.

### 2. `<what-to-do>` Block
Numbered steps the agent executes. Keep under 50 lines.

### 3. `<supporting-info>` Block (optional)
Reference material, formats, examples. Loaded but not acted on directly.

### 4. Scoring Rubric (where applicable)
0-10 scale with defined bands:

| Score | Band | Meaning |
|-------|------|---------|
| 0-2 | Critical | Broken, missing, or harmful |
| 3-4 | Poor | Exists but significantly incomplete |
| 5-6 | Acceptable | Meets minimum standards |
| 7-8 | Good | Complete, well-sourced, useful |
| 9-10 | Excellent | Authoritative, comprehensive, exemplary |

### 5. References (if content exceeds 100 lines)
Split deep content into `references/` directory:
```
skill-name/
├── SKILL.md           # Main instructions (<100 lines)
├── references/
│   ├── FORMATS.md     # Detailed format specs
│   ├── EXAMPLES.md    # Usage examples
│   └── RUBRIC.md      # Extended scoring criteria
```

## Constraints

- SKILL.md MUST stay under 100 lines (excluding frontmatter)
- Description MUST include "Use when [triggers]"
- Use `<what-to-do>` / `<supporting-info>` XML tags to separate instructions from reference
- Every evaluative skill MUST include a scoring rubric
