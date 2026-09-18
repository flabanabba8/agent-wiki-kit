---
name: write-a-skill
description: Create new agent skills with proper structure, progressive disclosure, and bundled resources. Use when user wants to create, write, or build a new skill.
user-invocable: true
---

# Writing Skills

<what-to-do>

1. **Gather requirements** — what task, what use cases, scripts needed?, reference materials?
2. **Read SKILL-TEMPLATE.md** for the standard format (check project `.claude/skills/` first, then `~/.claude/skills/`)
3. **Determine scope** — user-level (`~/.claude/skills/`) for cross-project skills, project-level (`.claude/skills/`) for project-specific
4. **Draft the skill** — SKILL.md (<100 lines), references/ if needed, scripts/ if deterministic
5. **Validate the skill** — test it against 2-3 representative tasks before finalizing. If results are poor, apply bounded edits (add/delete/replace specific lines), don't rewrite from scratch.
6. **Review with user** — iterate until approved

</what-to-do>

<supporting-info>

## Skill Structure

```
skill-name/
├── SKILL.md           # Main instructions (<100 lines, required)
├── references/        # Split deep content here
└── scripts/           # Utility scripts (deterministic ops only)
```

## Skill Placement

- `~/.claude/skills/` — available in ALL projects (handoff, write-a-skill, etc.)
- `.claude/skills/` — project-specific (render, export, ingest, etc.)

## Description & Trigger Rules

The description is the **only thing the agent sees** when picking skills. Max 1024 chars, third person. First sentence: what it does. Second: "Use when [triggers]."

Triggers should be **state-action predicates**, not vague keywords.
- Good: "Use when WebFetch returns 403/empty or a page is bot-walled."
- Bad: "Use when user wants to browse the web."

## Sizing Guidance (SkillOpt)

Optimal skill size is 300-2000 tokens (~20-80 lines of SKILL.md body). Research shows diminishing returns beyond this range. If your skill exceeds this, split into references/.

## When to Split

- SKILL.md exceeds 100 lines → move detail to references/
- Deterministic operations → utility scripts (saves tokens vs generated code)

## Skill Evolution

- Use bounded edits (add/delete/replace), not full rewrites
- Preserve what works — don't rewrite a working skill from scratch
- Document rejected approaches (they prevent repeat mistakes)
- After 1-4 validated edits, most skills converge

## Review Checklist

- [ ] Description includes "Use when..." triggers
- [ ] Triggers are specific state-action predicates, not vague keywords
- [ ] Skill body is 300-2000 tokens (20-80 lines)
- [ ] SKILL.md under 100 lines
- [ ] `user-invocable: true` in frontmatter (hyphen; `user_invocable` is not a real field)
- [ ] Uses `<what-to-do>` / `<supporting-info>` XML tags
- [ ] Concrete examples included
- [ ] Tested against 2-3 representative tasks
- [ ] Failed approaches documented (if iterating on existing skill)

</supporting-info>
