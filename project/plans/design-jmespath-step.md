# Design: `type: jmespath` Step

**Status:** Proposed — not built. Nothing in `src/` implements this. Requires the Captain's approval before any code.

Verified 2026-08-17: no `jmespath` reference anywhere in `src/`.

**Related issues:** #167 (list transformation), #168 (predicate filtering)

---

## The Problem

The Scripture Pipelines variable resolver can navigate JSON structures and slice by position, but it cannot filter by value or project specific fields. When a pipeline needs to extract a subset of a list — keep only threads whose id appears in a given set, select specific fields from each object, flatten nested arrays — the only current options are a `type: function` step with custom Python or accepting the full structure and letting the LLM sort it out.

Both options are worse than a simple declarative expression.

---

## Why JMESPath

JMESPath is a query language for JSON. It is pure Python (`pip install jmespath`), no binary dependency, well-maintained, and is the query language used in AWS CLI, Ansible, and other tooling. A single expression handles field projection, predicate filtering, flattening, and sorting.

JMESPath works on a single input value. For cross-variable operations (filtering one list against values in another), the step passes a combined object as input — see examples below.

---

## Step Schema

```yaml
- name: step_name
  type: jmespath
  input: "${variable}"        # string: single variable
  query: "jmespath expression"
  outputs: result_variable
```

When filtering requires values from more than one variable, `input:` accepts a mapping:

```yaml
- name: step_name
  type: jmespath
  input:
    items: "${items}"
    ids: "${active_ids}"
  query: "items[?contains(ids, id)]"
  outputs: result_variable
```

All `${var}` references in `input:` are resolved before the query runs.

---

## Concrete Examples

### Project specific fields from a list

Select only the fields needed for a summary, discarding the rest:

```yaml
- name: scene_summaries
  description: Project id, reference, and title from full scene objects.
  type: jmespath
  input: "${scenes}"
  query: "[*].{id: id, reference: reference, title: title}"
  outputs: scene_summaries
```

### Filter by a field value

Keep only scenes whose genre is narrative:

```yaml
- name: narrative_scenes
  description: Filter scenes to narrative genre only.
  type: jmespath
  input: "${scenes}"
  query: "[?genre == 'narrative']"
  outputs: narrative_scenes
```

### Cross-variable predicate filtering

Keep only the threads whose id appears in the union of active thread ids across all scenes — the use case that originally exposed the resolver gap:

```yaml
- name: collect_active_ids
  description: Flatten active_thread_ids from all scenes into one list.
  type: jmespath
  input: "${scenes}"
  query: "[*].active_thread_ids[]"
  outputs: active_thread_ids

- name: active_threads
  description: |
    Filter full thread list to those referenced by at least one scene.
    Requires cross-variable input because JMESPath operates on a single root.
  type: jmespath
  input:
    threads: "${threads}"
    active_ids: "${active_thread_ids}"
  query: "threads[?contains(active_ids, id)]"
  outputs: active_threads
```

### Flatten nested arrays

Collect all word ids from across a list of verses:

```yaml
- name: all_word_ids
  type: jmespath
  input: "${verses}"
  query: "[*].words[*].id[]"
  outputs: all_word_ids
```

### Combine filtering and projection

Filter to significant discourse threads and project only the fields needed downstream:

```yaml
- name: key_threads
  description: Significant threads projected to summary shape for synthesis prompt.
  type: jmespath
  input: "${threads}"
  query: "[?significance > `2`].{id: id, title: title, type: discourse_type}"
  outputs: key_threads
```

### Sort and deduplicate

```yaml
- name: unique_references
  type: jmespath
  input: "${citations}"
  query: "[*].reference[] | sort(@) | reverse(@)"
  outputs: sorted_references
```

---

## Navigation: Down and Up

JMESPath navigates down into nested structures cleanly — drilling into objects, selecting across arrays, combining filtering and projection at any depth. Flattening upward (collecting child values into a parent-level list) also works with the `[]` flattening operator, as shown in the examples above.

What JMESPath cannot do is true upward navigation — given a child node, find its parent. There is no parent axis or ancestor function, unlike XPath. For SP pipeline data this is rarely a problem because structures are shaped top-down (scenes → pericopes → verses) and queries always start from the root. The case that requires care: "find the scene that contains thread X" cannot be expressed starting from a thread object — the query must start from scenes and filter down, which is the right shape anyway.

If upward navigation from an arbitrary node ever becomes a genuine need, that is a signal the data structure should be redesigned rather than that JMESPath is the wrong tool.

---

## What This Replaces

Any `type: function` step that does nothing but filter, project, flatten, or sort a JSON structure should be replaceable with `type: jmespath`. The test: if the step's Python function contains only list comprehensions and dict projections and no domain logic, it belongs here.

This does not replace steps that compute new values, call external systems, parse formats, or do anything beyond querying existing structure.

---

## Implementation Notes

**Dependency:** Add `jmespath` to `pyproject.toml` dependencies. Pure Python, no system binary required.

**Runner:** New `_run_jmespath_step()` in `runner.py`, dispatched from the main step loop alongside `_run_function_step()` etc.

**Input resolution:**
- If `input:` is a string: resolve the variable, use as JMESPath root.
- If `input:` is a mapping: resolve each value, build a dict, use as JMESPath root.

**Query:** Plain string, passed directly to `jmespath.search(query, data)`.

**Output:** The result of the search, stored in context under the `outputs:` name. If the result is `None` (expression matched nothing), store an empty list `[]` rather than `None` to avoid downstream KeyErrors.

**Linter:** Add `type: jmespath` to the known step types. Validate that `query:` is present. Validate that `input:` is either a string or a mapping of strings.

**Error handling:** A malformed JMESPath expression raises `jmespath.exceptions.ParseError` — surface this as a lint error if possible, or a clear runtime error with the expression quoted.

---

## Tests

- `test_jmespath_field_projection` — step projects fields from a list of dicts
- `test_jmespath_predicate_filter` — step filters list by field value
- `test_jmespath_cross_variable_filter` — step uses mapping input to filter one list against another
- `test_jmespath_flatten` — step flattens nested arrays
- `test_jmespath_none_result_becomes_empty_list` — no match returns `[]` not `None`
- `test_jmespath_invalid_expression_raises` — malformed query produces clear error
- `test_linter_rejects_jmespath_without_query` — linter catches missing `query:` field
