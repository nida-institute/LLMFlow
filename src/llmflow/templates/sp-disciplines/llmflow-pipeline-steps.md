# LLMFlow Pipeline Step Documentation Convention

## The description Field

Use the `description` field to document a step. For simple steps a single line
is sufficient. For steps with non-obvious purpose, inputs, or return shapes, use
a YAML block scalar (`|`) for multi-line content.

```yaml
# Simple step — one line is enough
- name: load_annotated_book
  description: Load pre-built annotated USJ for the requested book.
  type: function
  function: llmflow.utils.io.read_json
  inputs:
    path: "${output_dir}/${book_code}_annotated.json"
  outputs: annotated_book

# Complex step — multi-line description using block scalar
- name: prepare_for_synthesis
  description: |
    Compresses per-pericope analyses (~4K tokens each) to lightweight summaries
    (~150 tokens each) so all pericopes in a book fit within the synthesis
    prompt's context window.

    Returns two parallel structures consumed by synthesize_book_structure:
      book_segmentation        — pericope metadata (id, reference, title,
                                 discourse_function) for structural overview.
      pericope_synthesis_input — analyses_summary[] and opening_segments[],
                                 one entry per pericope.

    See plugins/synthesis_prep.py for compression details.
  type: function
  function: plugins.synthesis_prep.prepare
  inputs:
    pericopes: "${pericope_analyses}"
    book: "${book_code}"
  outputs: synthesis_input
```

## What Belongs in the Description

- **Why the step exists** — especially when it is not obvious from the step name
- **What it returns** — when the return shape is not obvious from the step type
  or output variable name
- **Constraints or invariants** — ordering requirements, preconditions, size limits
- **A pointer to the plugin** — when a function step has a plugin with more detail

## What Does Not Belong in the Description

- Restatement of what the step name already says
- Implementation details that belong in the plugin docstring
- Cryptic shorthand that requires knowing the internals to parse

## Do Not Use Mid-Step YAML Comments for Documentation

YAML comments placed between step fields (between `outputs:` and `saveas:`, for
example) are disorienting to read and invisible to tooling. All step documentation
belongs in `description`.
