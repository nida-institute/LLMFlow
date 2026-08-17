# Audit: consumer-specific coupling in the core engine

**Date:** 2026-07-09
**Scope:** `src/llmflow/` — code that couples the general-purpose LLMFlow engine to a
specific consumer project (primarily nida-institute/ears-to-hear and its "storyflow"
pipelines).
**Method:** grep sweep for consumer-domain terms (`bodies`, `scene`, `Citation`,
`pericope`, `storyflow`, `psalm`, `ears-to-hear`, …), then read each hit in context and
classify. Reachability checked via caller grep.
**Status:** Findings only — **nothing fixed.** Triggered by the Captain spotting a
`"bodies"` debug block in `runner.py`.

**Findings not re-verified since 2026-07-09.** The engine has moved substantially (0.2.1.24 and the releases before it). Confirm each finding against the current code before acting on it.

## Important distinction: domain vs. consumer

LLMFlow is *for* biblical/linguistic scholarship, so **biblical reference parsing is
legitimate core** and is NOT flagged below:
- `utils/data.py` / `utils/bible_data.py` — book codes, verse counts, Psalms, USFM parsing.
  This is the engine's stated domain.

"Consumer coupling" means the engine hardcodes **one project's pipeline structure, step
names, field names, or directory layout** — things that belong in the consumer repo, not
the shared engine.

## Summary

| # | Location | Kind | Severity |
|---|----------|------|----------|
| F1 | `utils/data.py:72` `_format_as_markdown` | Functional — hardcodes ears-to-hear's 4-step scene structure | High |
| F2 | `utils/linter.py:1131` | Functional — hardcoded `prompts/storyflow/` search path | High |
| F3 | `steps/llm.py:29` | Functional — `Citation`/`scene.Citation` fallbacks for `passage` | Medium |
| F4 | `runner.py:382–385` | Functional — `scene`/`Citation` in require-error context | Medium |
| D1 | `runner.py:368–376` | Debug cruft — `"bodies"` guard logging | Low (no-op) |
| D2 | `utils/step_outputs.py:24–25` | Debug cruft — `"bodies"` first-100-chars log | Low (no-op) |
| Z1 | `utils/data.py` `flatten_structure` | Dead code — `pass` stub, no callers | Low |
| E1 | `cli_utils.py` (help text) | Docs/examples — scene/pericope/`storyflow-psalms` | Low |
| E2 | `templates/sp-conventions/*.md` | Shipped docs — "Originated in ears-to-hear" | Low |
| E3 | `schema/pipeline.schema.json` | Schema example descriptions — scene/pericopes | Low |

## Findings

### F1 — `_format_as_markdown` hardcodes a consumer's content structure (High)
`src/llmflow/utils/data.py:72`
```python
step_names = {
    "step1": "Senses (What's Happening?)",
    "step2": "Context (What's the Background?)",
    "step3": "Spiritual and Emotional Journey (What's at the Heart for Them?)",
    "step4": "Connections (What's at the Heart for Us?)",
}
...
section_parts = [f"## Scene {i}\n"]
```
This is the ears-to-hear storyflow pipeline's exact four-step framing and "Scene N" heading,
baked into a core util. **It is load-bearing, not dead**: `interleave(output_format="markdown")`
calls it (`data.py:67`), `interleave` is a pipeline-facing operation (see `io.py`
`extract_interleave_fields`), and it is covered by `tests/test_data_utilities.py`. A naive
deletion breaks interleave-markdown pipelines; genericizing the labels *changes the rendered
output*. See "Load-bearing analysis" below.

### F2 — linter hardcodes a consumer pipeline directory (High)
`src/llmflow/utils/linter.py:1131`
```python
for possible_path in [
    f"prompts/{prompt_file}",
    f"prompts/storyflow/{prompt_file}",   # <-- consumer-specific
    prompt_file,
]:
```
The core prompt-contract validator special-cases `prompts/storyflow/`, a directory that only
exists in the consumer repo. Arbitrary and non-general; any other project's subdirectory
layout gets no such treatment.

### F3 — LLM step derives `passage` from consumer field names (Medium)
`src/llmflow/steps/llm.py:29`
```python
passage = context.get("passage") or context.get("Citation") or context.get("scene", {}).get("Citation")
```
Used only to build debug filenames, so it degrades gracefully — but `Citation` and
`scene.Citation` are ears-to-hear field names hardcoded into the generic LLM handler. The
generic `passage` key is the only one that belongs here.

### F4 — require-failure error context reaches into consumer data shape (Medium)
`src/llmflow/runner.py:382–385`
```python
if "scene" in context:
    scene = context.get("scene")
    if isinstance(scene, dict):
        context_info["scene_citation"] = scene.get("Citation", "unknown")
```
Functional (feeds error messages), but assumes a `scene` object with a `Citation` field —
again consumer-specific.

### D1 — `"bodies"` guard debug logging (Low, no-op)
`src/llmflow/runner.py:368–376` — debug-only logging gated on `step.get("name") == "bodies"`.
The Captain's original catch. No functional effect.

### D2 — `"bodies"` output debug logging (Low, no-op)
`src/llmflow/utils/step_outputs.py:24–25` — `"bodies"`-only "First 100 chars" debug line.

### Z1 — dead code in `utils/data.py` (Low)
`flatten_structure` is a `pass` stub with **no callers** — genuinely dead, safe to delete.
(Correction: `_format_as_markdown` is **not** dead — see F1.)

### E1/E2/E3 — documentation & shipped templates (Low, judgment call)
- **E1** `cli_utils.py` help/tutorial text uses scene/pericope examples and the filename
  `2026-03-17_Ruth-1_storyflow-psalms.md`. Illustrative; acceptable if we're fine with
  scripture-flavored examples in help output.
- **E2** `src/llmflow/templates/sp-conventions/*.md` ship with the package (`sp init` copies
  them) and contain pericope/book examples; `llmflow-prompt-organization.md:7` literally says
  *"Originated in nida-institute/ears-to-hear repository."* These reach every user of the
  engine, so consumer-flavored content here has the widest blast radius of the "low" items.
- **E3** `schema/pipeline.schema.json` uses `scene`/`pericopes` in `description` examples.
  Purely illustrative; lowest concern.

## Load-bearing analysis — will fixing this degrade pipeline quality?

Short answer: **generated OUTPUT is at risk in exactly one place (F1).** Everything else
affects debug logging, tooling, or error messages — not the content the LLM produces.

| # | Useful function it serves | If deleted naively | Just remove? |
|---|---------------------------|--------------------|--------------|
| D1 | none — leftover debug | nothing | ✅ yes |
| D2 | none — leftover debug | nothing | ✅ yes |
| Z1 `flatten_structure` | none — `pass` stub | nothing | ✅ yes |
| F3 | readable debug filenames | debug files named by timestamp, not passage | ✅ yes (cosmetic, debug only) |
| F4 | richer require-failure errors | error loses "which scene" context | ✅ yes (error text only) |
| F2 | linter finds prompts under a subdir | **ears-to-hear lint breaks** (false "prompt not found") | ❌ generalize, don't delete |
| F1 | renders interleave data as markdown | **interleave-markdown breaks; genericizing changes output** | ❌ generalize + coordinate w/ consumer |

Is it "useful but badly implemented"?
- **F1, F2 — yes.** Real functions (markdown rendering; prompt discovery) hardcoded to one
  consumer. Must be *generalized*, not deleted, or ears-to-hear degrades.
- **F3, F4 — mildly.** Quality-of-life (filenames, error text); no output impact; safe to
  simplify.
- **D1, D2, `flatten_structure` — no.** Pure leftover; safe to delete outright.

Two reasons "fix it all at once" is risky:
1. **F1 changes output.** The `step1..step4` → "Senses/Context/…" mapping and "## Scene N"
   heading *are* the format ears-to-hear expects. Genericizing means moving those labels into
   pipeline/consumer config; until the consumer supplies them, its interleave output changes.
2. **ears-to-hear vendors this engine as a subdirectory**, so F1/F2 changes land there
   immediately — they need a coordinated consumer-side change, not a unilateral core edit.

Recommended sequencing: remove the safe items (D1, D2, `flatten_structure`) now; treat F1/F2
as generalization work paired with an ears-to-hear update; F3/F4 as low-priority cleanup.

## Recommendations (not yet actioned)

Suggested grouping into issues for the Captain to prioritize:
1. **Remove debug cruft** (D1, D2) — trivial, no behavior change. (Already proposed
   separately.)
2. **Delete dead code** (Z1) — `_format_as_markdown`, `flatten_structure`.
3. **Decouple functional hits** (F2, F3, F4) — replace hardcoded consumer names/paths with
   general mechanisms (e.g. configurable prompt search paths; a generic `passage`/label key
   convention documented for consumers; error-context hooks instead of `scene.Citation`).
4. **Decide on docs/templates** (E1–E3) — whether scripture examples are acceptable in a
   general engine, or should be genericized / moved to consumer docs. E2 matters most since
   those files ship to all users.

## Not fixed
Per direction, this audit only identifies. No source files were modified.
