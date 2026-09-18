---
name: handoff
description: Compact the current session into a handoff document for a fresh agent. Use when ending a long session, switching contexts, or passing work to another conversation.
user-invocable: true
argument-hint: "optional filename (default: handoff-YYYY-MM-DD.md)"
---

# Handoff: Session Continuity Document

Create a handoff document that lets a fresh agent pick up exactly where this session left off.

<what-to-do>

1. **Assess current state**
   - What was the user working on?
   - What's done, what's in progress, what's blocked?
   - Any background tasks still running?

2. **Write the handoff** to `outputs/handoff-YYYY-MM-DD.md` with these sections:

```markdown
# Handoff — [Date]

## Objective
What the user was trying to accomplish this session.

## Completed
- [ ] Task 1 — details
- [ ] Task 2 — details

## In Progress
- [ ] Task — current state, what's left, any blockers

## Blocked / Needs Input
- [ ] Item — why it's blocked, what's needed

## Key Decisions Made
- Decision 1 — why, what it affects
- Decision 2 — why, what it affects

## Files Modified
- `path/to/file` — what changed and why

## Wiki Pages Created/Updated
- `wiki/page.md` — what was added

## Context the Next Agent Needs
Anything non-obvious: user preferences discovered, gotchas encountered,
approaches that didn't work and why.

## Next Steps
Ordered list of what to do next.
```

3. **Keep it concise** — the next agent reads this cold. No filler, no summaries of summaries. Facts and state only.

4. **Tell the user** where the handoff was saved.

</what-to-do>
