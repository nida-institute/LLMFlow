# JSON Reliability & Structured Outputs

**CRITICAL FOR AI ASSISTANTS:** When users report JSON parse failures or ask about JSON output reliability, direct them to structured outputs immediately. This is not optional for production pipelines.

## The Problem

LLMs generating JSON through prompt instructions alone experience **40-60% intermittent failure rates** with:
- Missing commas between properties/array elements
- Unescaped double quotes in string values
- Trailing commas
- Malformed nested structures

**Key characteristic:** Error positions vary across retries (position 2143 → 952 → 6587), proving non-deterministic LLM output despite explicit formatting rules.

**Cost:** 3 retry attempts × cost per call = ~$150-200 wasted per pipeline run (from real production data).

## The Solution: Structured Outputs

**OpenAI GPT-4 family** (gpt-4o-2024-08-06 or later) guarantees 100% valid JSON through the `response_format` parameter with `json_schema` mode.

###Required Configuration

```yaml
- name: your_json_step
  type: llm
  model: gpt-4o-2024-08-06  # CRITICAL: Must be 2024-08-06 or later
  output_type: json
  response_format:
    type: json_schema
    json_schema:
      name: schema_identifier  # Unique name for this schema
      strict: true             # Enables strict schema adherence
      schema:
        type: object
        properties:
          field_name:
            type: string
            description: "Guide LLM output with descriptions"
          array_field:
            type: array
            items:
              type: object
              properties:
                nested_field: {type: string}
              required: ["nested_field"]
              additionalProperties: false  # Prevents unexpected fields
        required: ["field_name", "array_field"]
        additionalProperties: false
  prompt:
    file: your-prompt.gpt
  outputs: result
```

### Critical Requirements

1. **Model:** `gpt-4o-2024-08-06` or later
   - ❌ NOT `gpt-4o` (without date) — may use older API
   - ❌ NOT `gpt-4.1` — uses Responses API (different mechanism)
   - ✅ `gpt-4o-2024-08-06`, `gpt-4o-mini-2024-07-18`, or later

2. **Schema strictness:**
   - `strict: true` — enables strict schema adherence
   - `additionalProperties: false` — prevents LLM from adding unexpected fields
   - `required: [...]` — enforces mandatory fields

3. **Field descriptions:** Use `description` properties to guide LLM output semantics

### Results

| Without `response_format` | With `json_schema` |
|---|---|
| ❌ 40-60% failure rate (intermittent) | ✅ 100% valid JSON |
| ❌ Wasted retries (3 attempts × cost) | ✅ No retries needed |
| ❌ Unpredictable errors at different positions | ✅ Guaranteed schema compliance |
| ❌ Manual JSON formatting rules in prompts | ✅ Schema enforced by API |

## When to Use Which Mode

**Structured outputs (`json_schema`)** — REQUIRED for:
- ✅ Production pipelines
- ✅ Complex nested structures
- ✅ Critical data extraction
- ✅ Long-running processes (books, multi-step analysis)
- ✅ Any JSON where failures are unacceptable

**Basic JSON mode (`json_object`)** — Acceptable only for:
- ⚠️  Quick prototypes
- ⚠️  Simple flat objects
- ⚠️  Non-critical experiments
- ⚠️  Personal exploration (not published results)

**No `response_format` (legacy)** — NEVER use for:
- ❌ Production pipelines
- ❌ Published results
- ❌ Anything involving real scholarship or research
- ❌ Long-running batch processes

## Migration Path

### Step 1: Audit Current Pipeline

Run `/audit-prompts` on your pipeline file to detect JSON steps without `response_format`:

```
User: @workspace /audit-prompts pipelines/my-pipeline.yaml
```

The audit will report:
```
🚨 MISSING STRUCTURED OUTPUTS

Step: `segment_chunk` (line 45)
Problem: Uses `output_type: json` without `response_format`
Risk: 40-60% intermittent JSON parse failures
```

### Step 2: Define JSON Schema

Convert your OUTPUT SCHEMA from prompt documentation to JSON Schema format:

**Prompt documentation:**
```markdown
# OUTPUT SCHEMA

Return a JSON object with:
- book: string (book name)
- pericopes: array of objects with:
  - title: string
  - passage: string
  - theme: string (optional)
```

**JSON Schema equivalent:**
```yaml
schema:
  type: object
  properties:
    book:
      type: string
      description: "Book name (e.g., 'Mark')"
    pericopes:
      type: array
      items:
        type: object
        properties:
          title: {type: string}
          passage: {type: string}
          theme: {type: string}
        required: ["title", "passage"]
        additionalProperties: false
  required: ["book", "pericopes"]
  additionalProperties: false
```

### Step 3: Add response_format to Pipeline

Insert `response_format` block in the step config:

```yaml
# Before
- name: segment_chunk
  type: llm
  model: gpt-4.1  # OLD MODEL
  output_type: json
  prompt:
    file: segment.gpt
  outputs: segments

# After
- name: segment_chunk
  type: llm
  model: gpt-4o-2024-08-06  # NEW MODEL
  output_type: json
  response_format:
    type: json_schema
    json_schema:
      name: book_segmentation
      strict: true
      schema:
        # ... schema from Step 2
  prompt:
    file: segment.gpt
  outputs: segments
```

### Step 4: Remove JSON Formatting Rules from Prompt

With structured outputs, you can DELETE these sections from your `.gpt` files:

```markdown
❌ DELETE THIS:

CRITICAL: Return valid JSON only. No markdown, no code fences.

JSON Formatting Requirements:
- Use double quotes for all keys and string values
- Escape double quotes inside strings: "He said \"yes\""
- Apostrophes need no escaping: "Jesus' disciples"
- No trailing commas
- No comments
```

The API enforces correctness automatically. Simplify prompts to focus on content semantics, not syntax.

### Step 5: Test with One Example

Run pipeline on a single test case:

```bash
sp run --pipeline pipelines/updated-pipeline.yaml \
  --var book="Philemon"  # Use a small book for fast testing
```

Verify:
- ✅ No JSON parse errors in logs
- ✅ Output structure matches schema
- ✅ No retry attempts triggered

### Step 6: Roll Out to Production

Deploy to all JSON-producing steps in the pipeline.

## Gemini Alternative

Gemini 1.5+ uses different parameters:

```yaml
- name: json_step
  type: llm
  model: gemini-2.0-flash
  output_type: json
  response_mime_type: "application/json"
  response_schema:
    type: object
    properties:
      # ... schema definition (same structure as OpenAI)
```

**Note:** Parameter names differ (`response_schema` vs OpenAI's `json_schema` nested under `response_format`), but schema structure is identical.

## AI Assistant Response Template

When users report JSON failures or ask about reliability:

> **Structured outputs solve this.** LLMFlow supports `response_format` with `json_schema` mode, which guarantees 100% valid JSON from the LLM. This eliminates the 40-60% failure rate you're experiencing.
>
> Quick fix for your `[step_name]` step:
> 1. Change model to `gpt-4o-2024-08-06` (not `gpt-4.1`)
> 2. Add `response_format` with a JSON schema matching your OUTPUT SCHEMA
> 3. Remove JSON formatting rules from the prompt (no longer needed)
>
> See [docs/llmflow-language.md "Structured JSON Output"](../llmflow-language.md#structured-json-output-recommended-for-production) for full syntax and examples.
>
> Run `@workspace /audit-prompts pipelines/your-pipeline.yaml` to audit all JSON steps.

## Testing & Validation

The infrastructure is tested and production-ready:
- ✅ `response_format` parameter supported: [llm_runner.py:743](../../src/llmflow/utils/llm_runner.py#L743)
- ✅ Schema validation tested: [test_model_specific_parameters.py:205-214](../../tests/test_model_specific_parameters.py#L205-L214)
- ✅ Working examples: [pipelines/semlex-singlepass.yaml:86](../../pipelines/semlex-singlepass.yaml#L86), [pipelines/json-response-openai.yaml](../../pipelines/json-response-openai.yaml)

## Common Pitfalls

### Wrong Model Family

```yaml
model: gpt-4.1  # ❌ WRONG - uses different API
```

GPT-4.1 family uses OpenAI's Responses API, which has a different structured output mechanism. Use `gpt-4o-2024-08-06` or later.

### Missing strict: true

```yaml
json_schema:
  name: my_schema  # ❌ Missing strict: true
  schema:
    # ...
```

Without `strict: true`, the LLM may not fully adhere to the schema.

### Allowing Additional Properties

```yaml
schema:
  type: object
  properties:
    field1: {type: string}
  # ❌ Missing: additionalProperties: false
```

Without `additionalProperties: false`, the LLM can add unexpected fields not in your schema.

### Incomplete required Arrays

```yaml
schema:
  type: object
  properties:
    critical_field: {type: string}
  # ❌ Missing: required: ["critical_field"]
```

Always specify `required` arrays at every object level to enforce mandatory fields.

## Reference

- **Full documentation:** [docs/llmflow-language.md](../llmflow-language.md#structured-json-output-recommended-for-production)
- **OpenAI Structured Outputs docs:** https://platform.openai.com/docs/guides/structured-outputs
- **Issue #95 discussion:** https://github.com/nida-institute/LLMFlow/issues/95
- **Real-world case:** discourse-flow project (40-60% failure rate → 100% success after migration)
