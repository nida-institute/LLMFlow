# Scripture Pipelines Intermediate Artifact Data Shapes

> **Use this file for:** intermediate artifact data shapes — `create_json_dictionary`, step input/output contracts, consumer-project artifact schemas (pericope_payload, book_flow_json, etc.).
> **Budget: 150 lines / 5KB.** If adding content would push past this, split and add a row to `index.md`.

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

`package_pericope_payload`, `pericope_package`, `book_flow_json`, `pericope_results` and similar names **do not exist in this repo.** They are artifacts defined in consumer projects (e.g., `ears-to-hear`, `discourse-flow`) that use Scripture Pipelines as an engine.

To find their schemas:
- Look at the consumer project's pipeline YAML for the step that calls `create_json_dictionary` (or similar) and read its `inputs:` block.
- Look for `.json` snapshot files in the consumer project's `outputs/` or `context/` directories.
- Look at the consumer project's `docs/ai-context/` if it has one.

---

## Engine-owned artifact shapes

### `passage_info`

Produced by
`llmflow.utils.data.parse_bible_reference(passage, versification="eng", source_versification=None)`
→ `dict`. `"Luke 12:5-19"`:

```json
{
  "book_name":               "Luke",
  "book_number":             "42",
  "book_code":               "LUK",
  "chapter":                 12,
  "chapter_padded":          "012",
  "start_verse":             5,
  "end_verse":               19,
  "end_chapter":             12,
  "is_whole_chapter":        false,
  "filename_prefix":         "42012005-42012019",
  "display_name":            "Luke-12-5-19",
  "canonical_reference":     "Luke 12:5-19",
  "testament":               "NT",
  "original_language":       "Greek",
  "requested_versification": "eng",
  "source_versification":    null,
  "extent_versification":    null,
  "book_in_versification":   true
}
```

A whole-book reference — `"Romans"` — returns the same keys with `chapter`, `chapter_padded`,
`end_verse` and `end_chapter` all `null`, an extra `is_whole_book: true`, and a
`filename_prefix` of `"45_book"`.

**The four versification fields (#218).** Only one part of this structure ever depended on a
versification scheme: `end_verse` when `is_whole_chapter`. It is resolved from the named
scheme's `maxVerses`, so `Psalm 3` ends at verse 8 in `eng` and verse 9 in `org`.

| field | what it says |
|---|---|
| `requested_versification` | the scheme the reference was read in. Defaults to `eng`, because a person who names none is almost always thinking in English numbering. This is the **request** side |
| `source_versification` | the scheme an edition's text is numbered in, echoed from the argument. Recorded and **never resolved against** — this function has no edition, and the source side has no default anywhere in the engine |
| `extent_versification` | which scheme `end_verse` actually came from, or `null` where no extent was resolved. Usually equal to `requested_versification`; different when that scheme does not define the book and exactly one other does |
| `book_in_versification` | `false` when the named scheme does not define the book. `lxx` does not define `NEH`, `EST` or `DAN`; `vul` does not define `EST` |

**Two things now raise that previously returned.** A chapter or verse outside the scheme —
`Mark 3:99`, `Mark 99:1` — is an error naming the scheme and the real extent. And a whole
chapter in a scheme that does not define the book is refused when more than one other scheme
could answer, rather than one being chosen. `Psalm 3:9` is the case worth knowing: it exists in
`org` and not in `eng`, so under the default it raises and the message says which scheme to name.

`filename_prefix` and `display_name` **keep** the resolved end verse. They are fields on a
returned dict, not a mandated naming scheme; a pipeline wanting a name that cannot move builds
one from the parts it chooses.

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

Access in YAML: `${scene_list[0].Title}`, `${scene.Citation}`, `${scene.WLC}` (when `for: scene`).

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
