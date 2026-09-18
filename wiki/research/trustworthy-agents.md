---
title: Trustworthy Agents
type: research
tldr: "Anthropic's agent safety principles and data"
sources:
  - raw/articles/anthropic-trustworthy-agents-framework.md
  - raw/articles/anthropic-trustworthy-agents-in-practice.md
  - raw/articles/how-we-contain-claude.md
  - raw/articles/claude-code-sandboxing.md
  - raw/articles/claude-code-auto-mode.md
  - raw/articles/prompt-injection-defenses.md
  - raw/articles/claude-opus-5-system-card-agentic-coding.md
  - raw/articles/claude-sonnet-5-system-card-agentic-coding.md
related: ["[[permissions-and-modes]]", "[[sandboxing-and-security]]", "[[claude-models]]", "[[multi-agent-systems]]", "[[mcp]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [agent-safety-framework, prompt-injection-results, containment-tiers, auto-mode-classifier-design]
valid_until: 2027-03-15
---

# Trustworthy Agents

This page collects Anthropic's published research on keeping agents safe. It covers the five-principle framework, the containment patterns behind claude.ai, Claude Code and Cowork, how the sandbox and auto mode were designed, and measured prompt-injection robustness for the Claude 5 models. For the settings and modes you actually configure, see [[permissions-and-modes]] and [[sandboxing-and-security]].

## The five principles

Anthropic's framework names five principles. The in-practice follow-up applies them to four agent components: the **model**, the **harness** (instructions and guardrails), the **tools**, and the **environment** where the agent runs. "A well-trained model can still be exploited through a poorly configured harness, an overly permissive tool, or an exposed environment."

| Principle | What it means | Claude Code example given |
|---|---|---|
| Keep humans in control | Autonomy, with approval before high-stakes actions | Read-only by default; Plan Mode lets the user approve a whole plan instead of each step |
| Transparency | Show the agent's reasoning at the right level of detail | Real-time to-do checklist |
| Align with human values and expectations | Avoid actions that look reasonable to the agent but aren't what the user wanted | Training rewards pausing to ask when a situation is ambiguous |
| Protect privacy | Don't carry sensitive information across contexts | MCP connector controls: one-time or permanent access, admin allowlists |
| Secure interactions | Defend against prompt injection and compromised tools | Classifiers, threat monitoring, a reviewed MCP directory |

Anthropic's agent-autonomy research found that on complex tasks, users interrupt only slightly more often than on simple ones, while Claude's own check-in rate roughly doubles.

## Three risks, three places to defend

The containment post sorts agent risk into **user misuse**, **model misbehavior** and **external attackers** (prompt injection, or attacks on the runtime or proxy). Defenses go in three places:

- **Environment:** sandboxes, VMs, filesystem boundaries and egress controls. Credentials that never enter the sandbox can't be exfiltrated.
- **Model:** system prompts, classifiers, probes and training. On Gray Swan's Agent Red Teaming benchmark, Claude Opus 4.7 holds attack success to roughly 0.1% on a single attempt and around 5–6% after 100 adaptive attempts. These defenses are probabilistic, so they can't be the only layer.
- **External content:** MCP servers, plugins and search results. "An audited connector isn't the same as audited data." A GitHub connector can pass malware checks and still load a poisoned README.

Supervising every step has limits. In Anthropic's telemetry, users approved roughly 93% of permission prompts. Experienced users auto-approve about twice as often as new users but interrupt more often mid-run.

### Containment patterns by product

| | claude.ai code execution | Claude Code | Claude Cowork |
|---|---|---|---|
| Pattern | Ephemeral gVisor container, server-side | Human-in-the-loop OS sandbox | Local VM (Apple Virtualization framework, HCS on Windows) |
| Blast radius | Server-side container | Local workspace | Mounted workspace folder |
| Relies on the user to | Nothing | Read and judge bash | Nothing |
| Isolation cost | Container spin-up | Low-latency native sandbox | Full VM boot |

The choice follows who the user is. Developers can judge a bash command. Knowledge workers get an always-on boundary instead. Cowork keeps credentials in the host keychain and gives the VM a scoped, revocable per-session token. The agent loop and local MCP servers run on the host, while code execution stays inside the VM.

### Lessons from real incidents

- **Code that runs before the trust dialog.** A cloned repo's `.claude/settings.json` could define a hook that ran before the "Do you trust this folder?" prompt. The fix was to defer parsing project-local config until the user accepts. Treat project-open, config-load and localhost listeners as untrusted input.
- **The user as the injection vector.** In an internal red-team exercise, a phished employee pasted a prompt that quietly asked Claude to read `~/.aws/credentials` and POST it externally. It succeeded 24 times in 25 retries. Model-layer defenses anchor on user intent, so nothing looked anomalous. Only egress controls and filesystem boundaries hold here.
- **An allowlist grants capabilities.** Cowork allowed `api.anthropic.com`, so an injected file used an attacker's API key to upload workspace files to the attacker's account. The fix is an in-VM proxy that accepts only the session's own token.
- **Custom components break first.** Hypervisors, seccomp and gVisor held up. The custom allowlist proxy failed.
- **Isolation hides activity from EDR.** Endpoint detection can't see inside the VM. The current mitigation is pull-based OTLP log export.

Open problems the post names: memory poisoning through CLAUDE.md files and persistent agent state, **multi-agent trust escalation** (subagent output treated as more trusted than raw tool output; see [[multi-agent-systems]]), and whether an agent should have its own identity.

## Sandboxing design

Claude Code's sandbox needs **both** filesystem and network isolation. Without network isolation, a compromised agent can exfiltrate SSH keys. Without filesystem isolation, it can escape the sandbox and reach the network. The runtime uses bubblewrap on Linux and Seatbelt on macOS, and the rules also apply to any subprocesses a command spawns. Writes are allowed inside the working directory, and network traffic goes through a proxy outside the sandbox that enforces a domain allowlist. Internally this cut permission prompts by 84%. The runtime is open source, and `/sandbox` turns it on. Claude Code on the web keeps git credentials outside the sandbox and routes pushes through a proxy that checks the branch and repository.

## Auto mode design

Auto mode replaces per-action prompts with model-based classifiers. It is meant for people who would otherwise use `--dangerously-skip-permissions`, not as a replacement for careful human review.

**Threat model.** A dangerous action can come from overeager behavior, an honest mistake, prompt injection, or a misaligned model. The classifier is tuned on the first two.

**Two layers:**

1. A server-side **prompt-injection probe** scans tool outputs and adds a warning to the agent's context when content looks like a hijack attempt.
2. A **transcript classifier** (Sonnet 4.6) checks each action before it runs. Stage 1 is a single-token filter told to err toward blocking. Stage 2 applies chain-of-thought reasoning only to what stage 1 flags.

**Decision tiers.** Tier 1 is a built-in safe-tool allowlist plus user allow rules. Entering auto mode drops blanket rules that grant arbitrary code execution. Tier 2 allows in-project file edits without a classifier call. Tier 3 sends everything else (shell, web fetches, subagent spawns, writes outside the project) to the classifier.

**Reasoning-blind by design.** The classifier sees only user messages and the bare tool calls. Stripping Claude's own prose stops the agent from talking the classifier into a bad call, and stripping tool results is the main injection defense at this layer. The default block rules number more than twenty, grouped as destroy or exfiltrate, degrade security posture, cross trust boundaries, and bypass review. `claude auto-mode defaults` prints them.

| Pipeline | Real traffic (n=10,000) FPR | Real overeager (n=52) FNR | Synthetic exfil (n=1,000) FNR |
|---|---|---|---|
| Stage 1 only | 8.5% | 6.6% | 1.8% |
| Stage 1 → Stage 2 | 0.4% | 17% | 5.7% |

In most misses, the classifier saw the danger but wrongly treated something in the session as consent for it. Subagent handoffs are checked in both directions: at delegation the classifier can deny, and on return it only warns. After 3 consecutive denials or 20 in total, the session escalates to the human. In `claude -p` the process terminates instead.

## Prompt-injection defenses and results

Anthropic layers RL training against injections, classifiers on all untrusted content, and expert red teaming. For browser use with Claude Opus 4.5, the post calls a 1% attack success rate "meaningful risk."

**Claude 5 system-card results** (lower is better; measured on the model without product safeguards unless a safeguard is named):

| Evaluation | Claude Opus 5 | Claude Sonnet 5 | Reference |
|---|---|---|---|
| Gray Swan IPI benchmark (28 scenarios, 1,130 attacks), success within 15 attempts | 2.0% (0.2% at k=1) | 5.9% | Opus 4.8: 5.5% |
| Shade coding (40 scenarios, 200 attempts each), with thinking | 0.56%; 0.18% with probes | 0.31%; 0.09% with safeguards | Opus 4.8: 7.03% |
| Shade computer use (14 scenarios), with thinking | 0.54%; 0.25% with probes | 2.25%; 1.46% with safeguards | Opus 4.8: 7.14% |
| Browser use, 129 environments (Cowork harness, per the Opus 5 card) | 3.84%; 0% with auto mode | 0.47%; 0% with auto mode | Fable 5: 0.25% with auto mode |

The Opus 5 card's browser-use prose gives 3.70% for Opus 5 where its table shows 3.84%. The Sonnet 5 card, using an earlier harness, reports Sonnet 5 at 0.93% without safeguards. The Agent Red Teaming benchmark is retired in favor of IPI, because Claude models had saturated it.

> [!contradiction]
> The two system cards give different live bug-bounty results (both cards say 11 scenarios across tool use, coding and computer use). The Opus 5 card reports Opus 5 0.08%, Opus 4.8 0.11%, Sonnet 5 0.12% and Fable 5 0.04%. The Sonnet 5 card reports Sonnet 5 and Opus 4.8 tied at 0.19%.

## What this means for Claude Code users

- A sandbox caps the damage when the model layer fails. Pair [[sandboxing-and-security]] with network allowlists, and keep credentials out of reach.
- Auto mode is a classifier with a measured 17% miss rate on real overeager actions. Run it inside a sandbox, and keep manual review for production infrastructure ([[permissions-and-modes]]).
- Treat MCP servers and plugins as injection vectors even when you trust them ([[mcp]], [[plugins]]). Test remote servers against fake data first.
- Opening an untrusted repo, pasting a stranger's prompt, and anything that writes to CLAUDE.md are all attack surfaces ([[claude-md-and-memory]]).
- Current per-model robustness figures live on [[claude-models]].
