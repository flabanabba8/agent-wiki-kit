---
title: Agent Standards
type: research
tldr: "Agent Skills spec and MCP under the AAIF"
sources:
  - raw/articles/agent-skills-open-standard.md
  - raw/articles/agent-skills-engineering.md
  - raw/articles/anthropic-mcp-agentic-ai-foundation.md
  - raw/articles/anthropic-trustworthy-agents-in-practice.md
  - raw/docs/official/skills.md
related: ["[[skills]]", "[[mcp]]", "[[plugins]]", "[[skill-evolution]]", "[[trustworthy-agents]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [agent-skills-open-standard, agentskills-io, agentic-ai-foundation, aaif, skill-md-spec]
---

# Agent Standards

Two open standards shape how Claude Code is extended:

- **Agent Skills** (agentskills.io) is a portable folder format for procedural knowledge.
- **Model Context Protocol (MCP)** connects agents to external tools and data. Anthropic donated it to the Linux Foundation's **Agentic AI Foundation (AAIF)**.

Anthropic's case for open protocols is that "security properties [can] be designed into the infrastructure once, rather than patched together one deployment at a time," and that open protocols keep competition focused on the quality and safety of agents rather than on who controls integrations.

This page covers the standards themselves. For using skills and MCP servers in Claude Code, see [[skills]] and [[mcp]].

## Agent Skills

Anthropic developed the Agent Skills format and published it as an open standard in December 2025. It is open to contributions, and a growing number of agent products support it.

### Format

A skill is a directory with a required `SKILL.md`. The file holds YAML frontmatter followed by Markdown instructions.

```
skill-name/
├── SKILL.md      # Required: metadata + instructions
├── scripts/      # Optional: executable code
├── references/   # Optional: documentation
├── assets/       # Optional: templates, resources
└── ...           # Any additional files or directories
```

| Field | Required | Constraints |
|---|---|---|
| `name` | Yes | 1–64 characters; lowercase letters, digits and hyphens; no leading, trailing or consecutive hyphens; must match the parent directory name |
| `description` | Yes | 1–1024 characters; says what the skill does **and when to use it**, with task keywords |
| `license` | No | License name or bundled license file |
| `compatibility` | No | 1–500 characters; environment requirements. Most skills don't need it |
| `metadata` | No | Map of string keys to string values |
| `allowed-tools` | No | Space-separated pre-approved tools, e.g. `Bash(git:*) Bash(jq:*) Read`. Experimental |

The spec contrasts two descriptions. "Helps with PDFs." is too vague. "Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction." is what it recommends.

The body has no format restrictions. Suggested sections are step-by-step instructions, input/output examples and edge cases.

- `scripts/` holds self-contained code with helpful errors.
- `references/` holds focused documents loaded on demand.
- `assets/` holds templates, images and data files.

### Progressive disclosure

Agents load a skill in three stages. That is why many skills can be installed at once.

| Stage | What loads | Budget |
|---|---|---|
| Discovery (startup) | `name` and `description` of every skill | ~100 tokens per skill |
| Activation (task matches) | Full `SKILL.md` body | < 5000 tokens recommended; keep under 500 lines |
| Execution | Referenced files and scripts, only as needed | Unbounded; scripts can run without entering context |

Reference files by relative path from the skill root, one level deep, and avoid nested reference chains. To check frontmatter and naming rules, run `skills-ref validate ./my-skill`.

### How Claude Code relates to the standard

Claude Code follows the standard and adds features on top, such as invocation control, running a skill in a subagent, and dynamic context injection. Its frontmatter accepts more fields than the spec (the full table is on [[skills]]). Other distribution paths accept **only the six spec fields**: claude.ai skill uploads, the Skills API, and `package_skill.py` from anthropics/skills. Any other key fails with a hard error:

```
Unexpected key(s) in SKILL.md frontmatter: argument-hint. Allowed properties are: allowed-tools, compatibility, description, license, metadata, name
```

Claude Code-only body features such as dynamic context injection don't work in claude.ai chat or through the API. Frontmatter written to the spec loads in Claude Code unchanged.

### Where skills run

- **Claude apps:** Team and Enterprise admins can provision skills organization-wide. Provisioned skills are on by default, and users can switch them off. Partner skills (Notion, Canva, Figma, Atlassian and others) are listed at claude.com/connectors.
- **Claude Developer Platform:** skills can be added to Messages API requests and managed through the `/v1/skills` endpoint.
- **Claude Code:** install skills through plugins, check them into a repository, or place them in `~/.claude/skills` ([[plugins]]).
- **Claude Agent SDK:** the same Agent Skills support.

### Authoring and security guidance

From Anthropic's engineering post:

- **Start with evaluation.** Run the agent on representative tasks, find the gaps, and build skills incrementally to fill them.
- **Structure for scale.** Split an unwieldy `SKILL.md` into separate files. Keep mutually exclusive contexts in separate paths.
- **Think from Claude's perspective.** Watch real usage, and pay particular attention to `name` and `description`, since they decide when the skill triggers.
- **Iterate with Claude.** Ask Claude to capture successful approaches and common mistakes into the skill.

Skills can direct Claude to run code or exfiltrate data, so install them only from trusted sources. For anything less trusted, audit bundled scripts, dependencies, images and any instructions that reach external network sources first. Research on automatically evolving skills is on [[skill-evolution]].

## MCP and the Agentic AI Foundation

On December 9, 2025, Anthropic donated MCP to the **Agentic AI Foundation**, a directed fund under the Linux Foundation. Anthropic, Block and OpenAI co-founded it, with support from Google, Microsoft, AWS, Cloudflare and Bloomberg.

| Founding project | Contributed by |
|---|---|
| Model Context Protocol | Anthropic |
| goose | Block |
| AGENTS.md | OpenAI |

MCP's governance model is unchanged: its maintainers continue to prioritize community input and transparent decision-making. The foundation's stated aim is to keep these technologies neutral, open and community-driven.

Adoption reported at the time of the donation:

- More than 10,000 active public MCP servers.
- Adopted by ChatGPT, Cursor, Gemini, Microsoft Copilot and Visual Studio Code.
- Deployment support from AWS, Cloudflare, Google Cloud and Microsoft Azure.
- An official, community-driven Registry for discovering servers.
- Official SDKs in all major languages, with 97M+ monthly SDK downloads across Python and TypeScript.
- A November 25 spec release that added asynchronous operations, statelessness, server identity and official extensions.
- More than 75 MCP-powered connectors in Claude's directory.

### Skills and MCP together

MCP gives an agent access to tools and data. Skills teach it procedures. Anthropic describes skills as complementing MCP servers by teaching agents more complex workflows that involve external tools. Both are also supply-chain and prompt-injection surfaces ([[trustworthy-agents]]).

## What this means for Claude Code users

- To share a skill beyond Claude Code, stick to the six spec fields and the size budgets above. Use Claude Code-only fields only for skills that stay in Claude Code ([[skills]]).
- Package and distribute skills and MCP servers together with [[plugins]].
- MCP servers configured in Claude Code use the open, foundation-governed protocol, so the same server works in other MCP clients ([[mcp]]).
- Before installing any third-party skill or MCP server, audit it as you would code ([[trustworthy-agents]]).
