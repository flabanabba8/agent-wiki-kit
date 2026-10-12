---
title: AI-Driven Code Modernization
type: how-to
tldr: "Plan large legacy migrations with Claude"
sources:
  - raw/articles/ai-driven-code-modernization.md
related: ["[[workflows]]", "[[subagents]]", "[[plugins]]", "[[agent-evals]]", "[[claude-code-in-practice]]", "[[enterprise-admin]]"]
created: 2026-09-25
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [code-modernization, legacy-migration, cobol-to-java, modernization-certificate, promotion-policy, uplift-transform-reimagine]
---

# AI-Driven Code Modernization

Agents can finish a modernization once scoped as a multi-year effort in months or weeks. The change-management, review and approval around each change stays the same, so the bottleneck moves from writing changes to getting the organization ready to accept them. This page follows Anthropic's forward deployed engineers' "Notes from the Field" guide (Sep 2026) for critical systems and regulated enterprises.

The guide has six steps: define the **target**, write the **certificate**, set the **promotion policy**, put the **prerequisites** in place, build and refine the **agentic workflow**, then **run** it.

## 1. Define the target

| Type | What it is | Choose when | The target is |
|---|---|---|---|
| Uplift | Same-stack version bump (C++11 → C++20) | The stack is fine but the version is behind: end-of-life runtimes, unpatched security issues | A runtime version and package set |
| Transform | Cross-stack rewrite with behavior fixed (COBOL → Java) | The stack is the problem and the behavior is trusted | Uplift items plus language, frameworks and architectural conventions |
| Reimagine | Greenfield rebuild with modified behavior | Behavior must change along with the code | Transform items plus a written behavioral spec agreed with user groups |

Settle the type early. People closest to production usually want a transform; long-time maintainers and business stakeholders often want a reimagine. Left open, the question returns as arguments over whether each change is "correct".

Map the current system first. Claude can map dependencies and document forgotten workflows; the code modernization plugin's assess, map and extract-rules commands mine business rules with source citations for engineers to review. Interviews and internal documentation fill the gaps. Justify the project mainly by **risk reduction** (unpatched vulnerabilities, unsupported runtimes, a shrinking pool of people who know the system) rather than cost savings.

## 2. Write the certificate

The certificate is the set of conditions every change must meet. Each must be checkable without a human, so the workflow can iterate until a change passes or flag it for review. Typical conditions:

- The original test suite and Claude-written tests pass, and coverage meets an agreed threshold.
- Performance benchmarks stay within an agreed bound.
- Independent adversarial reviews by Claude, each in a fresh context window, find no blocking issues.
- For UIs, Claude-driven computer use finds no regressions.
- Old and new versions give the same output for the same input, and persisted state and wire formats round-trip.
- Staging runs show no regressions; static analysis and security scans show no new findings; compiled targets build and type-check cleanly.

What parity means depends on the type. An uplift can lean on the original test suite. A transform relies on production-traffic replay, differential testing and a prod-parallel deployment, because old tests rarely run on the new stack. A reimagine is anchored in the spec, which is less objective, so expect more variable outcomes and revise the certificate as the spec is clarified. Where old systems lack tests or telemetry, use Claude to build the missing evidence first. Write the certificate with the people who will review and promote changes: if they would merge on its evidence alone, promotion can be lighter.

## 3. Set the promotion policy

Agents produce changes faster than anyone can review them diff by diff. The promotion policy is a tiered review path, agreed in advance:

- Tier changes by blast radius and agent confidence, and keep full human review for critical paths.
- When the same flag keeps recurring, fix the workflow or certificate instead of reviewing each case.
- Design the review output format with the reviewers.
- Point subject-matter experts straight at the highest-risk tiers and flagged agent decisions.

Engage reviewers early, so their sign-off on samples justifies lighter review later. A hard deadline (a runtime losing support) calls for lighter review and explicitly more risk per change. In regulated settings the directive should come from the top, so responsibility for a bug is shared rather than pinned on one approver.

## 4. Put the prerequisites in place

Start these early; they run through other teams' backlogs.

- **Environment:** a dedicated remote host that Claude can reach the code from, test capacity, and anything that strengthens the certificate (telemetry, a prod-parallel setup, replay data).
- **Codebase and CI/CD:** a dependency map grounded in build logs, import analysis or runtime traces; a plan for each dependency; a CI compatibility check; a code-freeze policy and communication plan if modernizing in place.
- **Teams:** dependent teams agree how they take part, with reviewer time reserved.
- **Security and compliance:** an approved model access path for source code; least privilege (write only to modernization branches, no production credentials); secrets and PII scrubbed; every PR linked to its agent transcript and certificate evidence; license and vulnerability checks on new dependencies.

## 5. Build and refine the workflow

Build a custom dynamic workflow ([[workflows]]) in Claude Code that splits the work across many parallel [[subagents]]. Start from the code modernization plugin and put the target, certificate, promotion policy, code, docs and data on the file system or behind MCP. Have experts review any codebase-specific skills or extracted rules first. Refine on small parts of the codebase, and when issues surface, **fix the workflow, not each change**.

## 6. Run it

Complete the whole path, including review and landing, on a small partition, fix what breaks while it is cheap, then scale. Transforms and reimagines are built alongside the old system and cut over. An uplift can also run in place on a live codebase: partition from the leaves inward, freeze and modernize one partition at a time, and gate CI/CD so new commits can't undo a finished partition.

## Estimating cost

Token cost is driven by how much code is read versus changed, how involved the certificate is (verification is usually the larger share in regulated settings), how much test writing and repair it demands, and how much reconciliation other teams' merges cause. Measure tokens on the pilot and extrapolate for a cost floor, treating anything the pilot couldn't see as unknown. Put expensive verification behind cheaper gates. Use a model like Sonnet for mechanical, fully checked work and stronger models for hard transformations and adversarial reviews. Escalating to a pricier model on failure can help, but several cheap retries can cost more than one expensive attempt. Model choice is covered on [[models-and-effort]].

Keep the workflow, certificate, promotion policy and evidence trail as a reusable playbook for the next upgrade.
