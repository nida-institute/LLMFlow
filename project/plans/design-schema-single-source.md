# Design: One schema, one step vocabulary

**Status:** Approved 2026-08-12 — **(1) hybrid** (per-type schema + per-type linter, generic-flat
object model) and **(3) generate `Step` attributes from the schema**. Building into the next PR.
**Trigger:** ears-to-hear report `2026-08-12-pipeline-schema-omits-output-and-output-type.md`.
**Fixes:** the "two sources of truth" for step keys; makes `architecture.md` §16 *true*.

---

## The problem

The complete step-key vocabulary is split across two sources:

- **`PIPELINE_SCHEMA`** (`pipeline_schema.py`) — ~19 common keys.
- **`_EXTRA_STEP_KEYS`** (`utils/linter.py`) — ~40 more the engine honors (`output`,
  `output_type`, `format`, `response_format`, `plugin`, `value`, `pattern`, `content`,
  `query`, `query_file`, `xpath`, …). `ALLOWED_STEP_KEYS = _SCHEMA_STEP_KEYS | _EXTRA_STEP_KEYS`.

The object model derives from `PIPELINE_SCHEMA` **alone**, so `Step` exposes only half the
real vocabulary. An audit of what the runner/steps actually read found **~34 step keys absent
from the schema**. The drift test can't catch this — a key missing from *both* the schema and
the model looks like agreement. §16's "schema is the single source" is currently aspirational.

## Decisions

- **(1) Schema richness — THREE OPTIONS, decision open** (the sharpened silent-ignore argument
  reopened this):
  - **(a) generic** — one flat step schema, every key optional. Simplest; but publishes an
    over-permissive grammar and cannot catch wrong-type keys (they stay silently ignored).
  - **hybrid** *(recommended)* — per-type schema + per-type linter (closes the silent-ignore,
    truthful §17 grammar, one source), **keep the object model generic-flat**. Most of (b)'s
    value at moderate cost.
  - **(b) full** — hybrid + per-type `Step` subclasses. Truest, but the per-type object model is
    the expensive, low-value part; defer it.

  See "Generic (a) vs per-step-type (b)" and "Implementing (b)" below for the tradeoff and cost.
- **(2) One source — delete `_EXTRA_STEP_KEYS`.** Move the full curated step-key set into
  `PIPELINE_SCHEMA`. The linter derives `ALLOWED_STEP_KEYS` from the schema alone. There is
  then exactly one declaration of the vocabulary.
- **(3) Object model — GENERATE `Step`'s attributes from the schema** *(reopens #187
  Decision 3)*. **DECISION NEEDED.**
  - #187 chose *hand-written* properties (one per key) for static typing + docstrings — fine
    at 19 keys. At ~50 it's heavy boilerplate, and the drift test churns on every schema
    change.
  - Generating `Step`/`Pipeline` attributes from `PIPELINE_SCHEMA` (e.g. a typed `__getattr__`
    over the schema's keys) makes drift **impossible by construction** — the purest expression
    of "one source" — at the cost of per-attribute static typing/autocomplete (mitigate: the
    published `PIPELINE_SCHEMA` is the discoverability source; `__getattr__` returns `Any`).
  - **Recommendation:** generate. The whole point of this change is a single source; a
    hand-maintained mirror of a 50-key schema is a *third* place to drift.
- **(4) Third-loop test — add it.** A guard asserting `PIPELINE_SCHEMA` ⊇ every step-config
  key the engine reads. First cut: regex-scan of `step.get("…")` across `steps/` + `runner.py`
  + `plugins/` (pragmatic; note the fragility — a more robust form instruments `step.get` at
  runtime, deferred). This is the check that would have caught the gap, and it drives the
  curation in (5).

## Generic (a) vs per-step-type (b) — the tradeoff, honestly

**What (b) is.** The pipeline language is a *tagged union*: a step's valid keys depend on its
`type`. `output_type` and `response_format` are meaningful only on `llm` steps; `query_file`
only on `duckdb`/`basex`; `cursor`/`size`/`stride` only on `window`; `pattern`/`delimiter` only
on loaders. (b) encodes that — the schema is `type`-discriminated (JSON Schema `if/then` or
`oneOf` per type), and the object model exposes only the keys that apply to a step's type.

**Why (b) is "truer to the language."** Under (a) the schema asserts *"any step may carry any of
these ~50 keys."* That is literally false: a `type: llm` step with `cursor:`, or a `function`
step with `output_type:`, is nonsense — yet (a)'s schema, and the linter derived from it, accept
both. (b) states the real grammar: each `type` has its own key set. So (a) buys "one source" but
publishes an *over-permissive* description; (b) publishes an *accurate* one.

**Is it of practical import? Partly — and it depends which goal you weight.**

- **Unblocking consumers / "not an attribute ⇒ not a key" (their ask): (a) is enough.** Both put
  the keys in the schema, so `step.output_type` exists and their blocked test becomes
  expressible. (b) adds nothing here.
- **Catching mistakes: (b) closes a real silent hole.** *Unknown* keys are caught today — the
  linter flags any key not in the global `ALLOWED_STEP_KEYS` as an **error** (with a typo hint),
  and `sp run` lints by default. But a key valid on *some* type placed on the *wrong* one
  (`output_type:` on a `function` step) passes — the allowed set is global, not per-type — and
  the handler never reads it: **no error, no warning, no effect. Silently ignored.** Per-type
  validation is the only thing that turns that silent no-op into a lint error. A modest-frequency
  class (copy-paste across step types) and not a correctness bug today, but a genuine silent
  failure mode — not benign tolerance.
- **Machine-readable semantics (§17): (b) matters most here — the sharpest argument.** We just
  published `PIPELINE_SCHEMA` so a program or LLM can read the language and compose calls. Under
  (a) that published map tells the reader *the wrong thing* — that `query_file` is a valid key on
  an `llm` step. A model composing from the syntax gets a less accurate grammar. (b) gives the
  true per-type shape. If the §17 goal is real, this is the one place the imprecision actually
  costs something.
- **Object-model cleanliness: (b) is nicer, not essential.** Under (a) an `llm` `Step` carries
  ~50 attributes, ~45 returning `None`; under (b) it carries only its real keys. Noise vs.
  precision; not blocking.

**Cost.** (b) is a real redesign: a discriminated-union schema, per-type linter validation, and a
type-aware object model (per-type `Step` behavior). (a) is a straight fold of one flat set.

**Where this lands.** (a) fixes the stated bug (two sources; keys-not-in-schema) at modest cost
and — importantly — **does not foreclose (b)**: the schema can be tightened from generic to
per-type later without breaking the "keys are in the schema" contract consumers rely on. A
lighter middle path also exists: keep the schema generic for *validity*, but add a per-type
**advisory** in the linter (warn on `output_type` on a non-`llm` step) — most of (b)'s
mistake-catching without the union redesign.

**Recommendation: (a) now**, with (b) recorded as the correct long-term model — *unless* you
weight §17 (machine-readable semantics) highly enough that an over-permissive *published* schema
is itself the defect worth fixing today. That single consideration is the one that could justify
paying for (b) immediately.

## Implementing (b): cost, and the hybrid

(b) has a cheap half and an expensive half, and the value above lives entirely in the cheap
half. The sharpened value — closing the silent-ignore hole and a truthful published grammar for
§17 — comes from per-type *validation*, which needs a per-type *schema*. The expensive part is
the per-type *object model*, and it is separable.

| Piece | Effort | Notes |
|---|---|---|
| Per-type schema (discriminated union) | moderate | `common + if type==X then {X keys}`, ~12–15 types, small key sets (from the audit + step handlers). JSON Schema `allOf`/`if`/`then`. Mechanical. |
| Per-type linter | moderate | Swap the global `ALLOWED_STEP_KEYS` check for a per-type allowed set derived from the schema. **This is what closes the silent-ignore hole.** Highest value. |
| Object model — **generic** (keep flat) | easy | `Step` exposes the union of all per-type keys; drift test = attrs vs the union. Per-type *validation* without a per-type *model*; meets the consumer's need. |
| Object model — **per-type `Step`** | hard | Factory + typed per-type subclasses; reopens the model design. Least valuable, most expensive. **Defer.** |
| Third-loop test, `output` deprecation | same as (a) | independent |

**The "(b) that matters"** — per-type schema + per-type linter, generic flat model — is
*moderate*: roughly (a)'s fold plus the linter change (~a day with tests). The scary redesign is
only the per-type object model, which can be deferred indefinitely.

## (5) Curated key set

Authoritative per-type map from the per-type audit (2026-08-12). This is the build spec for the
discriminated union — finalized by making the third-loop test green.

**Common (all types, read in the generic runner path):** `name`, `type`, `condition`, `saveas`,
`require`, `warn`, `retry`, `log`, `after` — plus `outputs`/`append_to` via the shared output
helper (`utils/step_outputs.py`).

**Per type:**
- **llm:** `prompt`, `llm_options`, `model`, `temperature`, `max_tokens`, `max_completion_tokens`,
  `timeout_seconds`, `response_format`, `reasoning_effort`, `mcp`, `output_type`, `template`,
  `format_with` (+ `output`/`outputs`/`append_to`/`format` via `handle_step_outputs`).
- **function:** `function`, `inputs` (+ output keys via helper).
- **duckdb:** `query_file`, `inputs`, `format` (+ output keys).
- **basex:** `query_file`, `inputs`, `timeout` (+ output keys).
- **for-each:** `in`, `for`, `steps`, `debug_label`, `parallel`, `group-by`, `order-by`.
- **window:** `in`, `for`, `steps`, `size`, `stride`, `include_partial`, `start_when`,
  `end_when`, `size_by_tokens`, `stride_by_tokens`, `model`, `merge`.
- **if:** `steps` (`condition` is generic).
- **json:** `output` (singular, required), `value`.
- **load_\*** (`load_json/yaml/xml/csv/tsv/text/directory`): `output`|`outputs`, `path`,
  `pattern`, `format`, `delimiter`.
- **save:** `path`, `content` — does **not** read `outputs`/`saveas`/`format` (unique).
- **plugin / registered-type:** reads the entire step dict → **permissive branch**
  (`additionalProperties: true`); can't enumerate plugin keys.

**Exclude (not public step syntax):**
- `_tag`, and the `!window_advance` inner `step`/`cursor` (a nested tagged sub-item, not a
  top-level step key).
- Plugin **flat-config shim** keys read top-level only when `inputs` is absent
  (`from`, `xpath`, `namespaces`, `output_format`, `lemma`, `sense_structure`,
  `reference_analysis`, `stylesheet_path`, `xml_string`, `xml_path`) — a compat hack; the
  intended form is nested under `inputs`.

**Drop (dead top-level keys):** `tools`, `response_mime_type`, `response_schema` — in the
linter's `_EXTRA_STEP_KEYS` but never read top-level by `run_llm_step` (only nested inside
`llm_options`/`response_format`). Removing them is a cleanup the single-source move enables.

**Note — the third-loop test must catch hyphenated keys** (`group-by`, `order-by`); its current
regex is `[a-zA-Z_]+` and misses them.

## `output` vs `outputs` (their Q1)

> **SUPERSEDED 2026-08-13.** The proposal below (declare both, name `outputs` canonical,
> deprecation-warn `output`) was **not** what shipped, on two counts.
>
> 1. **Direction.** `project/plans/design-pipeline-schema.md` §1 had already ruled — ✅ DECIDED —
>    *"standardize on `output` (singular) everywhere. A step produces one result, even if that
>    result is a list."* That ruling stands; `output` is canonical and `outputs` is retired.
>    This section was written without checking for that prior decision.
> 2. **No aliases.** The Captain's ruling: one syntax per concept, migrate pipelines as needed.
>    A retired spelling is a **lint error naming its replacement**, not a deprecated alias — a
>    second accepted spelling is indistinguishable from a bug to anyone reading a pipeline.
>
> Shipped in 0.2.1.23: ~1,100 sites migrated across 15 repos. See `tests/test_one_syntax.py`.

Both were honored. `load` treated them as synonyms (`step.get("output") or step.get("outputs")`);
`json` used `output`; the common output mechanism used `outputs`. **Original proposal:** declare
both in the schema (so neither is "not a key"), name `outputs` canonical in the docs, and have the
linter emit a **deprecation warning** for `output` — ears-to-hear uses it 98× and asked to be
told which to normalise to. (Deprecation is additive; no runtime break.)

## Rollout (into the next PR)

1. Third-loop test (drives curation).
2. Move the curated vocabulary into `PIPELINE_SCHEMA`; delete `_EXTRA_STEP_KEYS`; linter derives
   from the schema.
3. Object model per Decision (3).
4. `output` deprecation warning; docs name `outputs` canonical.
5. Update `architecture.md` §16 (now literally true) + `docs/python-api.md`.
6. Answer the ears-to-hear thread.

**Nothing built yet. Awaiting review — especially Decision (3): generate `Step`, or keep it
hand-written?**
