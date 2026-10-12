---
name: disposable-vision
description: Inspects images with the requested vision provider and generates GPT-Image art in isolated sessions; returns text and file paths only. Use when reviewing screenshots, sprites, diagrams or visual defects, or creating art with optional image references, while keeping image payloads out of the main conversation.
---

# Isolated vision inspection and image generation

Inspection defaults to warm stateless local vision. Native generation uses GPT-Image. Keep image payloads out of the coordinator context. Local vision is available for other tasks only when no requested model/provider excludes it.

<what-to-do>

1. Use fresh stateless requests to an already-running loopback server for routine inspection. Batch related images. Use local commands for alpha, geometry, hashes and pixel comparisons. An explicitly requested model/provider overrides this default. No automatic downloads, server restarts or provider fallback.
2. Run the bundled scripts through the shell. Supply a focused question, acceptance criteria and at most four images. Whole-frame previews must be <=50,000 bytes each; never crop for vision. Keep originals local. Inspect dimensions, alpha, exact hashes and pixel preservation deterministically before asking the model about visible appearance.
3. Read only returned text/JSON and text reports. Do not emit image/base64 payloads or use the coordinator image viewer. Uncertainty requires relevant evidence, not automatic repeated reviews.
4. For generation, run `scripts/check_environment.py` once to check Codex prerequisites, then the generation command below. Every generator is fresh; never resume it. Its independent review uses a fresh isolated image task. PASS requires supported criteria; FAIL/UNCERTAIN stays a draft until resolved. No automatic regeneration or publication.

## Inspection

Use the Python interpreter with Pillow installed (in this kit, `.venv/bin/python`). Substitute it for `python3` below, and replace `SKILL_DIR` with the actual path to this skill:

```bash
python3 SKILL_DIR/scripts/vision_inspect.py \
  --question 'Are the sprite edges clean?' \
  --criteria 'No visible halos, clipping, or missing limbs' \
  /absolute/path/to/sprite.png
```

- One to four compressed whole-image JPEG previews, at most50KB each. Preview matte is not proof of opaque source pixels. Source alpha/dimensions require local measurements, not visual guessing.
- Returns a bounded text report of findings, uncertainty, and recommended action.
- Reports are cached by ordered image contents/names, question, criteria, model, and worker/preview code. Use `--refresh` for a new opinion. Changing an input invalidates the cache.
- Default `--backend local` avoids agent startup for inspection; `--backend codex` explicitly selects an isolated OpenAI image review.
- `--backend local` sends only the short system instruction and current images/question, with no tools or history. `--max-tokens` defaults to512; `--timeout` to120seconds. Report-cache hits avoid inference.
- No backend automatically falls back to another provider. Batch substantial related evidence; avoid model calls for tiny deterministic checks.

## Generation with optional references

```bash
python3 SKILL_DIR/scripts/image_reference_generate.py /absolute/path/to/new-art.png \
  --prompt 'Create a potion icon matching the supplied reference style' \
  --criteria 'One blue bottle, centered, no lettering' \
  --reference /absolute/path/to/style.png
```

- Omit `--reference` when no reference is needed. Up to four originals, at most 4 MB each and 8 MB combined. Their detail and transparency are preserved. The output must be a new PNG path.
- Uses the native GPT-Image tool through Codex's existing login, not API-key image endpoints. `--model` selects the coordinator, not the underlying image model. Generation timeout defaults to 300 seconds.
- Fresh image tasks independently review output/references; measured source transparency is supplied. Larger sets are bounded batches. Review failure produces UNCERTAIN, never automatic acceptance.
- Returns JSON containing `image`, `review`, and `verdict`. The sibling `.review.json` contains the evidence. Generated images remain on disk even if review fails, so the work is not lost.

## Review rubric

- **PASS:** every stated criterion is visibly satisfied by the inspected preview.
- **FAIL:** at least one criterion has a visible violation.
- **UNCERTAIN:** any required detail is unresolved, or the review could not finish. Obtain better evidence before acceptance; a low-resolution preview is not pixel-perfect verification.

</what-to-do>

<supporting-info>

Project inspection/generation require Python3.11+, Pillow and a logged-in Codex CLI. Optional local inspection requires an existing loopback vision server. If unavailable, report the missing prerequisite; do not substitute a paid provider or fetch credentials. Worker commands suppress raw transcripts and clean up temporary attachments. `--ephemeral` prevents normal local session persistence; it is not a promise of zero server retention or removal of Codex's generated-image cache.

State defaults to `$XDG_CACHE_HOME/disposable-vision` (or `~/.cache/disposable-vision`). `VISION_WORKER_STATE` overrides it. Reports and numeric metrics persist there; prompts and image payloads are not recorded in metrics. Worker images exist only in temporary directories except for generated artifacts.

```bash
python3 SKILL_DIR/scripts/vision_metrics.py              # recent worker metrics
python3 SKILL_DIR/scripts/vision_metrics.py --seconds 60 # traffic and internet RTT during a slowdown
python3 -m unittest discover -s SKILL_DIR/tests -q       # offline checks
```

Traffic counters include other applications. Attachment bytes are not exact network request sizes; neither metrics nor session-log sizes prove context re-upload or router bufferbloat.

This skill guides tool use; installing it does not disable native image tools globally. The kit routes image work through disposable workers in its shared project instructions. Keep each worker's stdout text-only when invoking from Claude Code or Hermes, just as from Codex.

</supporting-info>

## Cost evidence

Local metrics retain actual prompt/completion/cached token usage when reported, attachment bytes, elapsed time, backend and model. Codex generation/escalation captures JSON usage privately; raw event streams are discarded. Earlier metrics did not retain tokens, so historical total savings cannot be established. JPEG byte size measures upload size, not image-token usage.

Use ordinary local commands for small lookups and exact image checks. The reason to isolate a large review is bounded coordinator context; isolation alone does not prove lower total tokens.

Workers inherit your environment except variables whose names start with a prefix in `VISION_WORKER_DROP_ENV_PREFIXES` (comma separated, default none); set it when a host application's own session variables should not reach a nested worker.
