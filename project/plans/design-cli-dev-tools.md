# Design: sp CLI dev tools — `replay` first, a family to follow

**Status:** Partly implemented. `replay` shipped as `sp tools replay`; the wider family of dev
tools sketched here was **not** built. Treat the `replay` sections as historical record and the
rest as an unbuilt proposal.

Note: `replay` changed in 0.2.1.24 — it now reads request/response pairing from the run
`manifest.jsonl` rather than matching filenames (#198).

(`dev`, f8d3b2a), shipped as-is. The remaining decisions/gaps in this doc are the
*generalization* roadmap, tracked in **#177 (In Progress)**. Q1–Q6 are answered inline.

## Motivation

`replay` is a working tool in the scriptorium project
(`scriptorium/collab/replay/`, `scripts/replay_prompt.py`) that lets you test a
prompt edit cheaply: it takes a captured debug **request** sp already wrote, swaps
in your edited prompt while keeping the exact same data, sends one call per variant,
and reports the field-level change across N draws — instead of re-running a whole
pipeline.

Two things make it worth generalizing:
1. **Zero new instrumentation.** Every sp pipeline with an LLM step already writes the
   debug requests it consumes. The mechanism generalizes for free.
2. **The Captain expects more tools like it** — utilities that read sp's captured
   artifacts (debug request/response files, intermediate step outputs, telemetry) to
   support the human-in-command edit→observe loop. So this doc designs the *pattern*,
   with `replay` as instance #1.

## Part A — The dev-tool family (the pattern)

These tools share a shape: **consume sp's captured artifacts, support an edit→observe
loop, add no new instrumentation.** Likely future members: response/field diff across
runs, cost/telemetry analysis, debug-request inspection, batch audit replays.

Design questions (see Q-block):
- **Exposure.** First-class subcommands (`sp replay`, grouped under something like
  `sp dev <tool>`), a plugin-style discovery convention (as step plugins are), or a
  separate namespace. Lean: grouped subcommands (`sp dev …`) so the family is
  discoverable and the top-level CLI stays uncluttered.
- **Shared layer, factored once** so each tool doesn't reinvent it:
  1. a **capture reader** decoupled from today's debug-filename format (pairs
     request↔response, records model/params);
  2. reuse of the **engine call path** (`call_llm`, via #175) — provider-agnostic,
     production parity;
  3. **response-schema / field-selection** utilities (schema-driven field naming);
  4. an **N-draws + semantic-comparison** harness (compare named fields, not raw text).
- **Decision:** build the shared layer now, or extract it after the 2nd tool exists?

## Part B — Generalizing `replay` (the concrete first tool)

The scriptorium README's "Current limitations" section is the roadmap — the gap between
"works for us" and "ships as sp":

1. **Schema-driven `--show`.** Today `has_content`/`sensory`/`characters` are wired to
   this project's schema. General version selects comparable fields from the prompt's
   `response_format` schema (or user-specified). — *Q3*
2. **Nested `--set`.** Inject values nested inside another variable's blob, not just
   top-level variables.
3. **Concurrency + streamed progress.** Calls run sequentially and the table prints only
   at the end; parallelize and stream so large batches don't need backgrounding.
4. **Reuse the engine call path (#175).** Replace the direct OpenAI SDK with in-process
   `call_llm` (pinned to the run's engine version) — provider-agnostic, inherits schema
   expansion / param remap / routing / temperature default.
5. **Stable capture contract.** Don't depend on the current debug-filename convention
   for request↔response pairing; define a documented capture format. — *Q4*

**Keep as-is** (the clever core): *template inversion* — diff the original `.gpt`
against the captured request to recover the `var → value` map with no render engine.
Note its constraint: it needs the **prompt version that generated the request** (use the
git version from capture time), and an unresolved `{{var}}` is a hard error.

## Scope — v1 vs later (proposed, Captain decides — Q5)

- **v1:** `sp <…> replay` with schema-driven `--show`, engine call path (#175), and a
  documented capture reader.
- **v1.1+:** nested `--set`, concurrency/progress, additional tools in the family.

## Dependencies / related

- **#175** (programmatic call path — `pip install scripture-pipelines` → `call_llm`) —
  the enabler for gap 4.
- **#176** (strip frontmatter) — `replay` assumes frontmatter is sent; if #176 lands,
  the faithfulness assumption shifts. Track together.
- Source to port from: `scriptorium/scripts/replay_prompt.py`,
  `tests/test_replay_prompt.py`, and the decision history in
  `scriptorium/project/plans/replay-prompt-tool-2026-07-19.md`.

## Questions for the Captain — answer inline after each `=>`

**Q1. Exposure/CLI shape** — grouped `sp dev <tool>`, top-level `sp replay`, or a
plugin-style discovery convention?
=> sp tools <tool>

**Q2. Shared tools layer** — build it now, or extract it after a 2nd tool exists?

- **Shared layer, factored once** so each tool doesn't reinvent it:
  1. a **capture reader** decoupled from today's debug-filename format (pairs
     request↔response, records model/params);
  2. reuse of the **engine call path** (`call_llm`, via #175) — provider-agnostic,
     production parity;
  3. **response-schema / field-selection** utilities (schema-driven field naming);
  4. an **N-draws + semantic-comparison** harness (compare named fields, not raw text).
- **Decision:** build the shared layer now, or extract it after the 2nd tool exists?


=> I assume this refers to the above? If so, and you can do it quickly, please do.

**Q3. `--show` field selection** — schema-driven, user-specified, or both?
=> schema-driven

**Q4. Capture contract** — define a stable documented format now, or keep reading the
current debug files for v1?
=> v.next

**Q5. v1 scope** — which gaps are v1 vs later (proposal above)?
=> We can ship what we have NOW, with only changes that can be done quite quickly.
   Anything that delays shipping now should be noted in an issue, the issue should
   be "In Progress" or "Doing" or whatever our board calls that.

**Q6. Source home** — port into core (`src/llmflow/…`) as a subcommand, or a separate
`tools/` area first?
=> What would the advantage of porting into tools first be?
