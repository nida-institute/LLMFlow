---
name: audit-pipeline
description: |
  **WORKFLOW SKILL** — Audit Scripture Pipelines pipeline contracts: identifier matching, field-name consistency, JSON schema coverage, and structured output enforcement.
  USE FOR: finding fields that prompts reference but schemas don't define; finding fields schemas require but plugins don't produce; finding LLM calls missing response_format; tracing identifier lifecycle across pipeline stages; catching additionalProperties:false violations.
  FOUR AUDIT AXES: (1) Identifier audit — which fields are used as match keys across stages, their formats, and where they're produced vs. consumed; (2) Field contract audit — do prompts tell the LLM to read fields that don't exist in the data it receives? (3) Schema coverage audit — are schemas wired to LLM calls with json_schema enforcement? (4) Plugin/schema sync — does plugin output match what the schema requires?
  CRITICAL CHECKS: (1) additionalProperties:false schemas where actual output has unlisted fields (silently dropped or rejected); (2) required fields in schema not produced by the step; (3) LLM calls using json_object or no response_format when a schema exists; (4) identifier format mismatches (same concept, different format strings across stages); (5) late identifier computation (id fields absent in early phases that downstream depends on); (6) parallel array mismatches (arrays that must be index-aligned but can diverge).
  READ-ONLY: identifies issues, does not fix them. Reports findings with specific file+line references.
  FOR PYTHON PLUGIN INTERNALS (determinism, core reimplementation, plugin data contracts): use audit-code instead.
applyTo:
  - "**/*.yaml"
  - "**/*.json"
  - "**/*.py"
  - "**/*.gpt"
toolRestrictions:
  forbidden:
    - replace_string_in_file
    - multi_replace_string_in_file
    - create_file
  reasoning: "Read-only audit skill. Identifies issues but does not make changes."
---

# Audit Pipeline Skill

## The Core Problem: Silent Contract Violations

Scripture Pipelines pipelines connect LLM calls, Python plugins, and YAML steps through data dictionaries. Each boundary is a contract: the producing step promises to supply certain fields; the consuming step assumes they exist. When these contracts are violated:

- **Schema has `additionalProperties: false` but actual output has unlisted fields** → runtime drops or rejects fields silently
- **Schema requires fields not produced by the step** → LLM ignores required fields it wasn't told to produce (or produces them hallucinated)
- **LLM call has no `response_format: json_schema`** → model produces structurally arbitrary output that happens to look right most of the time
- **Identifier used for matching changes format across stages** → lookups silently fail, data is lost
- **Field computed late but referenced early** → downstream code gets None or empty string with no warning

None of these failures are loud. The pipeline may run to completion with subtly wrong output. The goal of this audit is to surface all such silent violations.

---

## Audit Axes

### Axis 1: Identifier Audit

**What to look for:** Every field used as a match key or lookup key across pipeline stages. For each:
- What is the exact format? (e.g. `"5:1"` vs `"JHN 5:1"` vs `"John 5:1-18"`)
- Which step produces it?
- Which steps consume it as a key?
- Is there a normalization step, and if so, when does it run relative to all uses?
- Are there multiple identifier families for the same concept (e.g. `sequence`, `canonical_reference`, and `id` all potentially identifying a pericope)?

**Common patterns to flag:**
- Deduplication by a single field when two fields together define uniqueness (e.g. dedup by `opening_verse` alone when `closing_verse` also matters)
- Normalization that runs in Phase 5 when the unnormalized form is compared in Phase 3
- IDs that don't exist until late in the pipeline but that schema fields reference throughout
- Parallel arrays indexed together (array A[N] corresponds to array B[N]) — these can silently diverge if any step inserts or drops items asymmetrically

**How to find them:**
```
grep -rn "\.get\(\"opening_verse\"\|\.get\(\"sequence\"\|\.get\(\"id\"\|\.get\(\"canonical_reference\"\" plugins/
grep -n "by_opening\|by_sequence\|by_id\|leaf_map\|lookup" plugins/
```

---

### Axis 2: Field Contract Audit

**What to look for:** Every field that a prompt tells the LLM to read from input data. For each:
- Does that field exist in the schema of the object being passed?
- Does the plugin that produces the object actually set that field?
- Is the field optional or required?

**How to audit a prompt:**
1. Read the DATA SOURCES / INPUT DATA section of the prompt
2. For each field reference (`pericope.opening_verse_sid`, `analyses_summary[].rhetorical_features`, etc.):
   - Find the schema for that input object
   - Check whether the field is present (even if optional)
   - Find the plugin or LLM step that produces the object and confirm it sets the field

**Common patterns to flag:**
- Field referenced in prompt but absent from schema (`additionalProperties: false` will drop it before the LLM sees it)
- Field referenced as required in prompt but only optional (or absent) in schema
- Field referenced in prompt that is only computed in a later pipeline phase
- Nested field path that doesn't match actual object shape (`foo.bar.baz` when actual is `foo.baz`)

**How to find them:**
```
grep -n "\`\`\." prompts/*.gpt        # field references using backtick notation
grep -n "\.field_name" prompts/*.gpt  # dot-notation field references
grep -n "required\|properties" schemas/*.json
```

---

### Axis 3: Schema Coverage Audit

**What to look for:** Every `type: llm` step in the pipeline YAML. For each:
- Does it have `response_format: type: json_schema` with `strict: true`?
- If it uses `type: json_object`, that only guarantees valid JSON — no field enforcement
- If it has no `response_format`, the output format is entirely unguided

**The quality chain:**
```
No response_format  →  format depends entirely on prompt instructions
json_object         →  valid JSON guaranteed; field names/types not enforced
json_schema         →  field names, types, required fields enforced by runtime
json_schema strict  →  additionally: no extra fields; all object properties declared
```

**Before flagging a missing `json_schema`**, check whether the schema is ready:
- Is there a schema file in `schemas/` for this step's output?
- Does the schema have `additionalProperties: false`?
- Does the schema declare all properties that the prompt actually produces? (If not, enabling strict mode will silently drop fields)
- Does the prompt have sufficient local focus to work with schema enforcement? (Prompts relying on vague global reasoning fail analytically under schema pressure — they spend attention on compliance instead of content)

**How to find them:**
```
grep -n "type: llm\|response_format\|json_schema\|json_object" pipelines/*.yaml
```

---

### Axis 4: Plugin/Schema Sync

**What to look for:** Every `type: function` step that reads or writes pericope data. For each:
- What fields does the plugin read? Are they all defined in the schema for the input object?
- What fields does the plugin write? Are they all defined in the schema for the output object?
- Does the plugin use `.get("field", default)` — what is the default, and what happens if a caller passes None?
- Is there a schema with `additionalProperties: false` that would reject fields the plugin produces?

**Common patterns to flag:**
- Plugin reads field with `.get("field", {})` when `{}` would cause the wrong code branch to fire (e.g. dict default for an array field)
- Plugin produces fields not in the output schema — silently dropped if `additionalProperties: false`
- Plugin required fields that match schema required fields — but the producing LLM step has no schema enforcement, so the field may be absent
- Two parallel arrays assembled by different steps — one may have fewer items if a step silently skips items

**How to find them:**
```
grep -n "\.get(" plugins/*.py              # field reads with defaults
grep -n "additionalProperties" schemas/*.json  # strict schemas
python3 -c "import json; s=json.load(open('schemas/X.json')); print(s.get('required'))"
```

---

---

### Axis 5: Source Text Grounding

**The rule:** No LLM step is ever allowed to reason from a passage unless the actual source text is right in front of it. A step missing `source_text` in its inputs is producing ungrounded output.

**What to look for:**
1. Every `type: llm` step in the pipeline YAML — does its `inputs:` block include `source_text`?
2. Every plugin or intermediate file that carries `source_text` — is the value continuous running text with inline verse markers (e.g. `⌊1:1⌋ Καὶ... ⌊1:2⌋ καὶ...`), or an array of verse objects?

**Array-of-verses is always wrong.** The representation `{"verses": [{"verse_ref": "MRK 1:1", "text": "..."}]}` treats verses as structural containers. Verse numbers are reference milestones inserted into continuous text. The only valid format is a single string with inline markers.

**How to check:**
```
grep -n "type: llm" pipelines/*.yaml   # find all LLM steps
# For each: check its inputs block for source_text
grep -n "source_text" pipelines/*.yaml # see where it is and isn't passed

# Check intermediate files for wrong format:
grep -r '"verses"' outputs/intermediate/ | grep '"verse_ref"'  # array-of-verses violation
```

**What to flag:**
- Any `type: llm` step without `source_text` in inputs: **CRITICAL — ungrounded output**
- Any `source_text` value that is a dict with a `verses` array: **CRITICAL — wrong format; violates milestone rule**

---

## Workflow

### Step 1: Map the pipeline stages

Read the pipeline YAML. For each step, record:
- Step name
- Step type (`llm`, `function`, `for-each`, `window`)
- Input variables
- Output variables
- `saveas` path (if any — these are the intermediate files that can be inspected)
- `response_format` (for `llm` steps)

Build a stage table:
```
Stage | Step | Type | Inputs | Outputs | Schema | response_format
------|------|------|--------|---------|--------|----------------
...
```

### Step 2: Inventory all schemas

For each schema file:
- List all `required` fields
- List all `properties` (including optional)
- Note `additionalProperties` setting
- Note which pipeline step uses it (input validation or output enforcement)
- Confirm the step is actually wired to this schema (or flag it as disconnected)

### Step 3: Trace identifiers

For each field used as a lookup or match key in any plugin:
```python
by_opening[opening] = pericope      # match key: opening_verse
by_sequence.get(seq)               # match key: sequence
leaf_map.get(p_id) or leaf_map.get(ref)  # match keys: id, canonical_reference
```
Trace the full lifecycle: when produced, when normalized, when used as a key.

### Step 4: Audit each LLM call's field contract

For each `type: llm` step:
1. Read the prompt file
2. List every field the prompt references from each input variable
3. For each field, verify it exists in the input schema
4. For each required output field in the schema, verify the prompt instructs the LLM to produce it
5. Flag mismatches

### Step 5: Check actual intermediate files

If `saveas` outputs exist, read them and compare against the schema:
```python
import json
data = json.load(open('output/intermediate/XX_book_segmentation.json'))
print(list(data.keys()))
print(list(data['pericopes'][0].keys()))
```
Compare actual keys against schema properties. This is more reliable than reading code — the pipeline may have changed without schema updates.

### Step 6: Produce the report

Structure:

```markdown
# Pipeline Contract Audit — [date]

## Identifier Audit
[Table: identifier, format, produced by, consumed by, risks]

## Field Contract Audit
[Per-prompt: input variable → field → exists in schema? → flagged?]

## Schema Coverage Audit
[Table: step, response_format, schema file, strict, ready to wire?]

## Plugin/Schema Sync
[Per-plugin: fields read, fields written, mismatches]

## Fix Checklist
[Grouped by dependency: schema fixes → prompt audits → wiring → plugin fixes → docs]
[Dependency graph showing ordering]
```

---

## Key Things to Check (Quick Reference)

| Check | What to look for | Where |
|---|---|---|
| `additionalProperties: false` + actual extra fields | Fields in actual output not in schema | Compare `output/intermediate/*.json` vs schema |
| Stale required fields | Schema requires field not in actual output | `schemas/*.json` required vs actual saveas output |
| Missing `json_schema` | `type: llm` without `response_format: json_schema` | `pipelines/*.yaml` |
| Late ID computation | `id` field absent until Phase 5; referenced earlier | `plugins/add_pericope_ids.py` vs earlier steps |
| Dict default for array field | `.get("field", {})` when field should be `[]` | `plugins/*.py` |
| Parallel array divergence | Two arrays meant to be index-aligned | `synthesis_prep.py`, accumulator plugins |
| Unnormalized identifier used as key | `canonical_reference` compared before normalization | Trace normalization call vs. uses |
| Prompt references non-existent nested field | `foo.bar.baz` path in prompt vs actual object shape | Prompt DATA SOURCES sections |
| **LLM step missing source_text** | Any `type: llm` step without `source_text` in its inputs | `pipelines/*.yaml` — every LLM step must have source text explicitly named |
| **source_text as array of verses** | `source_text` represented as `{"verses": [...]}` | Plugin outputs, intermediate JSON — must be continuous text with inline verse markers |

---

## Output

Produce a structured report with:
- Stage table (Step 1)
- Schema inventory (Step 2)
- Identifier lifecycle table (Step 3)
- Per-prompt field contract findings (Step 4)
- Actual vs. expected schema comparison (Step 5)
- Prioritized fix checklist with dependency graph (Step 6)

File the report at `project/audits/pipeline-contracts-audit-[date].md`.

**Do not:**
- Modify any files (read-only audit)
- Propose specific code changes (flag the issue and location; user decides the fix)
- Make assumptions about intent — if a field is absent from a schema but present in output, flag both possibilities (intentional or stale)

---

## Example Invocations

```
/audit-pipeline
```
Full audit of the pipeline in the current working directory.

```
/audit-pipeline --focus schemas
```
Focus on Axis 3 (schema coverage) and Axis 4 (plugin/schema sync) only.

```
/audit-pipeline --focus identifiers
```
Focus on Axis 1 only — trace all match keys across stages.

```
/audit-pipeline --focus contracts
```
Focus on Axis 2 — prompt field references vs. actual schema.

---

## Related Skills

- `/audit-code` — Audits Python plugin internals: determinism, identifier normalization
  inside plugins, data contract enforcement at plugin boundaries, and local reimplementations
  of Scripture Pipelines core utilities. Run this when the issue is *inside a plugin*, not in the
  pipeline contract between stages.
- `/audit-prompts` — Audits prompt structure, conventions, and structural forcing. Run this before wiring `json_schema` to a call — a prompt with weak local focus will produce structurally valid but analytically shallow output under schema pressure.
- `/audit-output` — Audits pipeline output quality (content, not contracts).

## Important Interaction

**Wiring `json_schema` to an LLM call changes model behavior.** When a schema is enforced:
- The model attends to schema shape during generation
- A prompt with poor local focus (global reasoning over all data) will lose analytical quality as attention shifts to compliance
- Always run `/audit-prompts` on the prompt before running `/audit-pipeline` to wire its schema

The two skills are complementary prerequisites for adding structured output enforcement to any step.
