# Design: Pre-flight Validation of Structured-Output Schemas

## Status: Design — Awaiting Captain's Review

---

## Problem

A step that asks for structured output declares a JSON Schema:

```yaml
response_format:
  type: json_schema
  json_schema:
    name: book_segmentation
    strict: true
    schema: { ... }
```

Under `strict: true`, OpenAI does not accept arbitrary JSON Schema. It accepts a
restricted subset, and a schema outside that subset is rejected with **HTTP 400 at request
time** — not a degraded answer, no answer at all.

Nothing in the engine checks this before the call:

| Check | Where | When |
|---|---|---|
| Prompt `requires:` satisfied | `linter.py` | before any spend ✅ |
| Step keys valid for the type | `linter.py` | before any spend ✅ |
| **Schema is acceptable to the provider** | — | **never** ❌ |
| `schema_file` exists and parses | `_expand_response_format_schema()` | at call time |
| Model may not support `response_format` | `llm_runner.py:329` | at call time, **warning only** |

`sp lint` never mentions `response_format`, `json_schema`, or `strict` — the words do not
appear in `linter.py`.

The failure therefore lands in the worst possible place. A pipeline passes every check, the
Captain runs it, the passage is fetched, three steps succeed, and step four dies on a 400
whose message names a JSON path rather than a line in the YAML. The steps before it have
already been paid for.

This contradicts the engine's central bargain, stated in `docs/ai-context/overview.md`:
prompt contracts are checked before token spend. The schema half of the same call is not.

### This is not hypothetical — our own flagship example is broken

`pipelines/json-schema-example.yaml` is the canonical demonstration of structured outputs.
Its own header advertises:

> - "Defines complete JSON schema with strict mode"
> - "Eliminates 40-60% JSON parse failure rate"
> - "No retry waste, guaranteed schema compliance"
>
> purpose: "Example of production-ready JSON output with schema validation"

**All three of its steps violate strict mode.** Strict mode requires every key in
`properties` to appear in `required`; optional fields are expressed as a nullable type
union, still listed in `required`.

| Step | Object | In `properties` but not `required` |
|---|---|---|
| `segment_book` | root | `segmentation_rationale` |
| `segment_book` | `pericopes.items` | `start_verse`, `end_verse`, `pericope_type` |
| `analyze_first_pericope` | root | `applications` |
| `analyze_first_pericope` | `literary_features.items` | `significance` |
| `generate_summary` | root | `genre_distribution` |

The first call this pipeline would make should 400. The example that teaches structured
outputs cannot itself run.

*Correction (2026-08-15):* an earlier draft of this document said the example "lints clean
today" and would then 400. It does **not** lint clean — it fails first, for an unrelated
reason. All three steps write their prompt inline as `prompt.template`, a form
`render_prompt()` does not implement, so `sp lint` rejects them with "No prompt file
specified" and no model is ever called. Filed as #197. The schema defects above are
unaffected and remain unreported by any check; the example is broken in two independent
ways, not one.

*Verification note:* the schema defects are established by reading the schemas against the
documented rule. Confirming the exact 400 requires one live API call, which needs the
Captain's authorization — and currently also requires fixing #197 first, since the run
cannot reach the provider. The fix is not contingent on that confirmation, since the rule
is documented and unambiguous.

### Why now

`HANDOFF.md` in hebrew-poetry-features instructs Benjamin to write OpenAI schemas for all
LLM calls. He will write them by hand, hit these rules one at a time, and get provider
error text that points into a JSON document rather than at his YAML. The first thing a new
user learns should not be that our own example is wrong.

---

## Design

### Where it goes: `sp lint`, not `sp tools`

`sp lint` is already the pre-flight command and already reads every step. Structured-output
validation is the same kind of check as a prompt contract — a claim about the request that
can be settled without making it. Users who lint already get it; nobody has to learn a new
command.

`sp tools` stays what it is: debug-time utilities like `replay`, reached deliberately.

A dedicated `sp tools check-schemas` is **rejected** — an opt-in check that catches a
guaranteed 400 is a check most people will not run.

### What is validated

A new module, `src/llmflow/utils/schema_preflight.py`, exporting:

```python
def check_strict_schema(schema: dict, *, path: str = "") -> list[Finding]
```

`Finding` carries `severity` (`error` | `warning`), a JSON path into the schema, the rule
violated, and a suggested fix. It is pure — no network, no provider client — so it is
cheap to test and cannot itself cost money.

**Errors** (the provider rejects these outright):

1. **Every property must be required.** Every key of `properties` appears in `required`.
   Fix offered: add it, or make it nullable — `"type": ["string", "null"]` — and still list it.
2. **`additionalProperties: false` on every object.** Missing or `true` is rejected.
3. **The root must be an object.** Not an array, not a scalar, not `anyOf` at the root.
4. **`$ref` targets must resolve** within the document.

**Warnings** (accepted by some models/versions, rejected by others):

5. Keywords outside the supported subset — `default`, `allOf`, `not`, `if`/`then`/`else`,
   `dependentRequired`, and validation keywords whose support has varied over time
   (`minLength`, `pattern`, `format`, `minimum`, `minItems`, …).
6. Nesting deeper than 5 levels, or more than 100 object properties in total.

Warnings, not errors, because **OpenAI has widened the accepted subset over time**. A hard
error on a keyword the provider has since accepted would block work that is fine. The
warning names the risk and lets the Captain proceed.

### The rule table is data, and it is dated

The keyword lists live in one module-level table with a `LAST_VERIFIED` date and a link to
the provider documentation. When the provider moves, one table changes. Encoding these
rules across a dozen `if` statements is how a checker becomes wrong quietly.

### Provider scope

Strict-mode rules are OpenAI's. The check runs when the step's resolved model is an OpenAI
model that supports structured outputs, and is skipped otherwise — a Gemini step is not
measured against OpenAI's rules. See *Second defect* below for how "supports structured
outputs" should be decided.

### Output

Findings render in the existing lint format, addressed to the YAML the Captain wrote:

```
✗ segment_book: response_format.json_schema.schema
    Every property must be listed in 'required' under strict mode.
    Missing: segmentation_rationale
    Fix: add it to 'required'; if it is genuinely optional, use
         type: ["string", "null"] and list it in 'required' anyway.

✗ segment_book: response_format.json_schema.schema.properties.pericopes.items
    Missing: start_verse, end_verse, pericope_type
```

Errors fail the lint. Warnings print and do not.

`schema_file` references are resolved and checked too — otherwise the check misses exactly
the schemas that are shared across steps, which are the ones worth getting right.

### Escape hatch

`linter_config.skip_strict_schema_check: true` in the pipeline, for the case where the
provider has accepted something our table calls an error. It exists so a stale table cannot
block real work. Its use should be rare enough to be conspicuous.

---

## Second defect, found while investigating

Two mechanisms answer "does this model support structured outputs," and the decision point
uses the weaker one.

- `telemetry.supports_json_schema(model)` — reads `supports_json_schema` from
  `data/models.json`, data-driven, covered by tests in `test_model_metadata.py`.
- `llm_runner.py:322-329` — substring match against `MODEL_FAMILIES["gpt-4"] + ["gpt-5"]`.

The call path uses the substring match. So a model whose metadata says it supports
structured outputs but whose name does not contain a listed pattern falls through to a
**warning** and is then called *without* `response_format` — the request silently proceeds
as free-form text, and the schema is not enforced at all. The output may still parse, and
nothing says the guarantee was dropped.

The gate should consult `supports_json_schema()`, and the fallback should be an error
rather than a silent downgrade — asking for a guarantee and not getting one should stop the
run, not warn.

This is a separate change from the linter work and should be its own commit. Whether it
becomes its own issue is the Captain's call.

---

## Implementation Plan

Test-driven, per CLAUDE.md.

1. **Failing test first** — `tests/test_schema_preflight.py`, using the three real schemas
   from `json-schema-example.yaml` as fixtures. They are known-bad and their defects are
   enumerated above, so they make honest test data.
2. `schema_preflight.py` — the pure checker plus the dated rule table.
3. Wire into `linter.py`, gated on the resolved model.
4. **Fix `pipelines/json-schema-example.yaml`** so the flagship example passes its own
   lint. This is the acceptance test for the whole feature.
5. Sweep the other structured-output pipelines: `json-response-openai.yaml`, and the
   `.bak` files if the Captain wants them kept at all.
6. `docs/` — the language reference gains the strict-mode rules; `sp lint` documentation
   gains the new check. **Note: `docs/ai-context/` is the Captain's; findings reported, not
   written.**

### Out of scope

- Validating *returned data* against the schema — the `json_schema_validator` plugin
  already does that, as an explicit step.
- Gemini's `response_mime_type`/`response_schema` (issue #191) — adjacent, separate.
- Generating schemas from prompt contracts. Tempting, and a different design.

---

## Captain's Decisions — 2026-08-14

1. **Errors, not warnings**, for the four hard rules. Consumer-repo pipelines that newly
   fail lint were already 400ing or silently downgraded; the lint failure reports a defect
   that was there before.
2. **`.bak` files deleted.** All 14 in `pipelines/`, not just the four mentioning
   `response_format`. Verified safe before deleting: five were keyword-migration residue
   whose migrated counterpart is live, and nine were byte-identical to their last tracked
   version, extracted to `llmflow-historical-pipelines` in `8caf8be`. Recoverable from
   history and from that repo. `*.bak` is already in `.gitignore:12`, which is why the
   migration residue sat unnoticed.
3. **`MODEL_FAMILIES` scope** — still open, pending the explanation below.
