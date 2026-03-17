# LLMFlow Intermediate Artifact Data Shapes

Reference for the major data structures that flow between pipeline steps.

---

## Engine-level utilities

### `create_json_dictionary(**kwargs)` → `dict`

`src/llmflow/utils/data.py`

This function is literally `dict(kwargs)`. The shape of its output is exactly the keyword arguments the caller passes. There is no schema enforced by the engine — the shape is defined by the pipeline YAML that calls it.

```python
# Implementation:
def create_json_dictionary(**kwargs):
    return dict(kwargs)
```

**Implication for AI assistants:** When a pipeline step calls `create_json_dictionary`, check the pipeline YAML's `inputs:` block to discover the actual shape.

---

## Consumer-project artifacts (`package_pericope_payload`, etc.)

`package_pericope_payload`, `pericope_package`, `book_flow_json`, `pericope_results` and similar names **do not exist in this repo.** They are artifacts defined in consumer projects (e.g., `ears-to-hear`, `discourse-flow`) that use LLMFlow as an engine.

To find their schemas:
- Look at the consumer project's pipeline YAML for the step that calls `create_json_dictionary` (or similar) and read its `inputs:` block.
- Look for `.json` snapshot files in the consumer project's `outputs/` or `context/` directories.
- Look at the consumer project's `docs/ai-context/` if it has one.

---

## Engine-owned artifact shapes

### `passage_info`

Produced by `llmflow.utils.data.parse_bible_reference(passage: str)` →  `dict`.

```json
{
  "book_name":           "Luke",
  "book_number":         "42",
  "book_code":           "LUK",
  "chapter":             12,
  "chapter_padded":      "012",
  "start_verse":         5,
  "end_verse":           19,
  "is_whole_chapter":    false,
  "filename_prefix":     "042012005-042012019",
  "display_name":        "Luke-12-5-19",
  "canonical_reference": "Luke 12:5-19"
}
```

Access in YAML: `${passage_info.filename_prefix}`, `${passage_info.book_code}`, etc.

---

### `scene_list` items (storyflow pipelines)

Produced by an LLM step with `output_type: json`. The shape is defined by the prompt, but all active storyflow pipelines expect items with at least:

```json
[
  {
    "Title":    "string — short scene title",
    "Citation": "string — verse reference, e.g. 'Luke 12:5-8'",
    "WLC":      "string — Hebrew/Greek source text for the scene",
    ...
  }
]
```

Access in YAML: `${scene_list[0].Title}`, `${scene.Citation}`, `${scene.WLC}` (when `item_var: scene`).

**Note:** `${scene_list[*].Title}` is documented but **NOT YET IMPLEMENTED** — see the `[*]` section in `llmflow-language.md` and `tests/test_variable_resolution.py::TestStarWildcardResolution`.

---

## `[*]` wildcard — semantics and implementation

`${list[*].field}` fans out over the list and applies the **entire remaining path** to each element via recursive `get_from_context()`, returning a flat list at that depth.

```python
# ${pericope_results[*].segments[0].boundary_signals}
# is equivalent to:
[get_from_context("segments[0].boundary_signals", item) for item in pericope_results]
# → ["high", "medium", "none"]  (one entry per outer item)
```

**Key semantics:**
- The remaining path after `[*]` — including further dot-steps, numeric indices, and dict-key brackets — is applied recursively to each element.
- If a nested index is out of bounds, or a field is missing, that slot is `None` (not skipped).
- `[*]` on a non-list returns `None`.
- `[*]` on an empty list returns `[]`.
- Result is always a flat list at the fan-out depth — `[*]` does not produce nested lists.

**Tested in:** `tests/test_variable_resolution.py::TestStarWildcardResolution`, including:
- `test_star_extracts_field_from_list` — single remaining field
- `test_star_deep_path_with_index` — `list[*].segments[0].boundary_signals`
- `test_star_deep_path_missing_index` — out-of-bounds slot → `None`
- `test_star_missing_field_none_filled` — absent field → `None`
- `test_star_empty_list` — empty source list → `[]`

**String interpolation caveat:** If `[*]` appears inside a larger string template
(e.g. `"titles: ${list[*].Title}"`), the list is stringified as Python `str([...])`.
To get native list semantics, the entire `inputs:` value must be *only* the `${...}` expression with nothing else.
