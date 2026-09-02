# Scripture Pipelines Language Quick Reference

This file is a compact, self-contained reference to the Scripture Pipelines
pipeline language for day-to-day work in this repository.

If you have access to the engine repo, the full specification lives
in `docs/llmflow-language.md` there, but this quickref is designed to
be enough to author and review pipelines on its own.

## 1. Pipeline structure

```yaml
name: my_pipeline
description: |
  One-line or multi-line description of what this flow does.

variables:
  output_dir: "outputs"

llm_config:
  model: gpt-4o-mini
  max_tokens: 1024
  temperature: 0.2

linter_config:
  enabled: true
  treat_warnings_as_errors: true

steps:
  - name: first-step
    type: llm | function | for-each | window | save | if
    # ...
```

Key sections:

- `name`, `description`: human-readable name and summary for the flow.
- `variables`: global variables available to all steps.
- `llm_config`: default model parameters for `llm` steps.
- `linter_config`: controls validation behavior for this pipeline.
- `steps`: ordered list of operations that make up the flow.

## 2. Referencing variables and templates

In pipeline YAML, use `${var}` syntax to reference variables and
step outputs:

- `${output_dir}` – root-level variable.
- `${greeting}` – value produced by a previous step.
- `${scene.WLC}` – field access on an object.
- `${scene_list[0]}` – first element of a list.
- `${scene_list[-1]}` – last element of a list.
- `${scene_list[-1].field}` – field on the last element.
- `${scene_list[0].field}` – field on the first element.
- `${scene_list[:-1]}` – every element except the last.
- `${scene_list[-10:]}` – last 10 elements (returns all if fewer than 10).
- `${scene_list[*].Title}` – extract one field from every item; returns a flat list.
- `${scene_list[-3:][*].Title}` – field from each of the last 3 items.

In prompt and template files (`*.gpt`, `*.md`), use `{{var}}` — and **only flat names**:

- `{{language_count}}`
- `{{greeting_markdown}}`

**`{{scene.WLC}}` is not valid, even though `${scene.WLC}` is.** The two syntaxes are not
symmetrical: `${...}` resolves a path through an object, while `{{...}}` is filled by matching
its name against a literal key of the context — and `scene.WLC` is not a key, so nothing fills
it. Field access belongs on the pipeline side: pass the value in under a flat name.

```yaml
prompt:
  file: analyse.gpt
  inputs:
    wlc_text: "${scene.WLC}"      # the path is resolved here …
```

```
Analyse {{wlc_text}}.                # … and the prompt names the result
```

Both `sp lint` and `sp run` refuse a dotted name in a prompt body rather than sending the model
an unfilled placeholder.

Prompt files usually include a small contract (often in a comment
block) that documents which inputs they expect ("requires" / "optional").
Make sure every required value is provided by the pipeline step
via `prompt.inputs`.

## 3. Common step types

### type: `llm`

Runs a prompt through an LLM and stores the response.

```yaml
- name: generate_text
  type: llm
  prompt:
    file: "template.gpt"
    inputs:
      topic: "${topic}"
  output: draft
  saveas:
    path: "${output_dir}/draft.md"
```

- `prompt.file` points to a prompt in `prompts/`.
- `prompt.inputs` provides values that the prompt template expects.
- `outputs` names the variable that will hold the LLM response.
- `saveas.path` writes that response to disk.

Optional extras you may see:

- `output_type: json` – ask the engine to parse the response as JSON.
- `log: debug` – per-step log level.

### type: `function`

Calls a Python function as part of the flow.

```yaml
- name: parse_data
  type: function
  function: some.module:callable
  inputs:
    raw: "${raw_text}"
  output: parsed
  saveas:
    path: "${output_dir}/parsed.json"
```

Use `function` steps for deterministic utilities: parsing, loading
files, rendering templates, reshaping JSON, etc.

### type: `for-each`

Loops over a list variable and runs nested steps for each item.

```yaml
- name: process_each_item
  type: for-each
  for: item
  in: "${items}"
  parallel: 4                      # optional: run up to 4 iterations concurrently
  group_by: "${item.category}"     # optional: group results by this field
  order_by: "${item.sequence}"     # optional: sort results within groups
  steps:
    - name: handle-item
      type: llm
      prompt:
        file: "item.gpt"
        inputs:
          item_text: "${item}"
      output: item_result
      append_to: all_results
```

- `for` is the name used to refer to each element (XQuery-style: `for $x in $list`).
- `in` points to the list value.
- Use `append_to` in nested steps to build a list across iterations.
- `parallel: N` runs N iterations concurrently; results are collected in
  input order regardless. Omit for sequential execution (default).
- `group_by` and `order_by` accept `${expr}` expressions evaluated against
  each item. `group_by` groups `append_to` results by the expression value;
  `order_by` sorts within each group.

### type: `window`

Slides over a list in overlapping or tumbling windows, running nested
steps on each slice. Useful when a list is too large to process at once.

```yaml
- name: segment_by_windows
  type: window
  for: window_content
  in: "${content_list}"
  size: 50                   # fixed: 50 items per window
  # or: size_by_tokens: 4000 # token-aware: ~4000 tokens per window
  include_partial: true      # include the last partial window
  steps:
    - name: process_window
      type: llm
      prompt:
        file: "process.gpt"
        inputs:
          chunk: "${window_content}"
      output: window_result
      append_to: all_results

    # Optional: dynamic cursor — tell the engine where the next window starts.
    # Without this, windows advance by the full size (tumbling / non-overlapping).
    #
    # Two halves, and half is worse than none:
    #   1. DISCARD the last logical unit of a non-final window. The physical cut may
    #      have truncated it, so its end is not known. The next window re-decides it.
    #   2. RESUME from the trailing edge of the last unit you KEPT — never from the
    #      opening of the unit you dropped. If the model left a gap between them, a
    #      cursor set to the dropped unit's opening skips it and nothing sees it again.
    # The final window keeps everything: nothing truncated it.
    - !window_advance
      name: advance_cursor
      cursor: next_start      # a LIST INDEX into `in:` — not a domain identifier
      step:
        name: compute_next
        type: function
        function: plugins.windowing.content_index_of_sid
        inputs:
          # [-2] is the last unit kept, because [-1] was discarded as possibly cut.
          # Its trailing edge, not its opening.
          verse_sid: "${window_result.pericopes[-2].first_verse_sid_after_pericope}"
          content: "${content_list}"
          # A domain boundary has to be converted to a position; that is all this
          # function does.
        output: next_start
```

- `size` — fixed item count per window. Required even in cursor mode, where it bounds
  how far each window may reach.
- `size_by_tokens` — token-aware; requires `model` key (inherits from `llm_config`).
- `include_partial: true` — process the final window even if it is shorter than `size`.
- `!window_advance` — when present, switches to dynamic (cursor-driven) mode.
  The inner `step` runs each iteration; if its `cursor` variable is `null`
  the loop stops after the current window.
- Two guards, both raising rather than misbehaving: a cursor that is not a non-negative
  integer is rejected, and a cursor that does not advance beyond the current start raises
  instead of looping forever.
- Use `size`/`stride` when list items are independent (summarise every 10 reviews); use a
  cursor whenever the LLM is finding structure *inside* the block. See "Physical windows,
  logical units" in the Scripture Pipelines language reference for why.

### Cross-iteration state in `for-each` and `window`

Each iteration starts from a **fresh copy of the outer context**. Variables set
inside an iteration are not automatically visible to the next one — unless they
are propagated out via `outputs` or `append_to`.

**`outputs` (last-iteration-wins):** the final value written by each iteration
replaces the outer variable. Each subsequent iteration sees the updated value.

**`append_to` (accumulating list):** each iteration appends to a list in the
outer context. Subsequent iterations see the growing list — including the items
appended by earlier iterations. This enables "rolling context" patterns:

```yaml
- name: analyze_pericopes
  type: for-each
  for: pericope
  in: "${leaf_pericopes}"
  steps:
    - name: analyze
      type: llm
      prompt:
        file: analyze.gpt
        inputs:
          passage: "${pericope.canonical_reference}"
          # Only pass the last 10 summaries — prior_pericopes grows each iteration
          prior_context: "${prior_pericopes[-10:]}"
      output: pericope_analysis

    - name: summarize
      type: function
      function: llmflow.utils.data.pick_fields
      inputs:
        obj: "${pericope_analysis}"
        fields: ["title", "themes"]
      output: summary
      append_to: prior_pericopes   # visible to next iteration
```

The slice `${prior_pericopes[-10:]}` always returns the last 10 items,
or all items if fewer than 10 have accumulated so far.

### type: `scripture`

Fetch one passage from one **named** edition. The name resolves through
`~/.sp/editions/*.yaml`, so no path appears in a pipeline and the same
pipeline runs on any machine.

```yaml
- name: fetch_source
  type: scripture
  edition: SBLGNT             # a registered edition
  passage: "${passage}"       # MRK · MRK 1 · MRK 1:1 · MRK 1:1-8 · MRK 1:40-2:12
  format: milestones          # plain | milestones | usj  (default: milestones)
  versification: eng          # optional — the scheme `passage` is written in
  include: [ids, discourse]   # optional — valid only with format: usj
  output: source_text
```

**Formats.** `plain` is running text. `milestones` adds `⌊1:1⌋` markers and
costs 1.072x — it is the default and usually enough. `usj` returns a **dict**,
2.56x in codepoints and 6.74x as escaped JSON, so pay for it only when
something consumes the structure. Verses are milestones, never containers:
do not restructure the text into a list or dict keyed by verse.

**Versification.** A reference is not a location until a scheme is named:
`PSA 51:1` is `PSA 51:3` in the original and `PSA 50:3` in the Vulgate.
`versification:` names the scheme *your* `passage` is written in; the engine
maps it before reading any text. An edition's own scheme comes from its
registry entry, a Paratext project's settings, or the shipped table — there is
no global default, and asking to cross schemes without one is an error.

**`include`** delivers annotation under one key, `scripture_pipelines`, which a
consumer can strip to get standard USJ. Seven families are named; `ids` and
`discourse` work and the rest raise. `ids` becomes `srcloc` on each word.
`discourse` attaches Levinsohn's features at word ids, each carrying an
`outcome` — his indices are NA28-family and the text is SBLGNT, so a
disagreement is reported rather than silently resolved.

### type: `save`

Writes literal content to disk without calling an LLM.

```yaml
- name: write-confirmation
  type: save
  content: |
    ✅ Scripture Pipelines is installed and running.
    2 + 2 = ${total}
  saveas:
    path: "${output_dir}/hello-llmflow.txt"
```

Use `save` when you just need to materialize a small message or
artifact from existing variables.

### type: `if`

Conditionally executes a block of steps.

```yaml
- name: add-detail
  type: if
  condition: "${include_detail}"
  steps:
    - name: generate-detail
      type: llm
      prompt:
        file: "detail.gpt"
        inputs:
          topic: "${topic}"
      output: detail_text
```

- `condition` is evaluated first; if falsy the whole block is skipped.
- Any step type is valid in the nested `steps:` list.

### Step-level `condition:` (skip guard)

Any step (any type) can be skipped individually:

```yaml
- name: optional-step
  type: llm
  condition: "${run_optional}"
  prompt:
    file: "optional.gpt"
    inputs:
      data: "${data}"
  output: optional_result
```

The expression follows the same rules as `type: if` — variable reference,
Python eval expression, or boolean literal.

## 4. Saving outputs with `saveas`

Any step can write its primary output (or literal content) to a file:

```yaml
- name: save_report
  type: llm
  prompt:
    file: "report.gpt"
    inputs:
      data: "${analysis}"
  output: report_md
  saveas:
    path: "${output_dir}/report.md"
```

Notes:

- Parent directories are created automatically.
- You can include `${variables}` and nested fields inside the path.
- If you need multiple files, add more steps, each with its own
  `saveas`.

## 5. Running and linting pipelines

From the project root (where `pipelines/` lives):

```bash
sp run --pipeline pipelines/my-pipeline.yaml
```

To pass variables from the CLI:

```bash
sp run --pipeline pipelines/my-pipeline.yaml   --var passage="Psalm 23"   --var output_dir="outputs"
```

To validate a pipeline without running it:

```bash
sp lint pipelines/my-pipeline.yaml
```

The `linter_config` block in the pipeline controls how strict
validation should be (for example, whether warnings become errors).

## 6. Prompt file format (`.gpt`)

Every `.gpt` file must begin with a YAML frontmatter block that declares
the variables it expects. The linter enforces this contract.

```
---
requires:
  - language_count
optional: []
format: Markdown
description: Brief description of what this prompt does.
---
system: |
  You are a helpful assistant.
user: |
  Do something with {{language_count}} items.
```

Key rules:

- `requires:` — list of variable names the caller *must* provide via `prompt.inputs`.
- `optional:` — list of variable names the caller *may* provide.
- Variables in the body use `{{double_braces}}`.
- If `requires:` is missing, the linter cannot validate the contract and will
  emit warnings about undeclared inputs.
