# Optional Parameters: When to Use Them and How to Prevent Abuse

## The Problem

LLMs generating code — and LLMs *writing pipelines* — have a systematic bias toward
marking things optional. It silences warnings without solving the underlying problem.
The result is runtime failures where you expected parse-time or lint-time errors.

The problem has two surfaces in Scripture Pipelines:

1. **Python code** — `Optional[T]` in function signatures and Pydantic models
2. **YAML pipelines** — `optional:` declarations and missing variable bindings in prompt contracts

This document covers both, defines the legitimate uses of Optional in each context,
and provides concrete patterns to prevent abuse.

---

## The Two Legitimate Categories

### Category 1: Enrichment — "caller may provide more context"

The caller always knows the required data. Optional parameters add diagnostic richness
when available but are genuinely absent in some call sites.

**Hallmark:** The function works correctly whether or not the optional is supplied.
The optional only affects error messages, log output, or diagnostic metadata — not
the primary computation.

**Scripture Pipelines example — `exceptions.py`:**

```python
class PipelineExecutionError(LLMFlowError):
    def __init__(
        self,
        message: str,                         # required — always known
        step_name: Optional[str] = None,      # enrichment — not available at all raise sites
        context: Optional[dict] = None,       # enrichment — expensive to capture; caller decides
        original_error: Optional[Exception] = None,  # enrichment — only when wrapping another error
    ):
```

`message` is always known at the raise site. `step_name` is legitimately absent when the
error occurs before a step is identified (e.g., pipeline YAML parse failure). `context` is
deliberately left out when the caller is re-raising and the context is already in the
original traceback. The function does not branch on these fields for primary logic — only
for `__str__` formatting.

**Test:** Remove the optional. Does any call site have a genuine reason to omit it?
If yes across *multiple independent* call sites, it belongs as Optional.

---

### Category 2: Lifecycle — "not yet, but will be"

The value is unavoidable at runtime but cannot be set at construction time. The object
lifecycle has distinct phases (allocate → initialize → complete) and the field is
populated in a later phase.

**Hallmark:** The field transitions from `None` to a real value exactly once.
Code that reads it after the transition never has to handle `None`. Code that reads it
before the transition should raise, not silently continue.

**Scripture Pipelines example — `telemetry.py`:**

```python
@dataclass
class StepMetrics:
    step_name: str           # set at construction — always known
    step_type: str           # set at construction — always known
    model: Optional[str] = None  # set after config merging, which happens after construction

    start_time: datetime = field(default_factory=datetime.now)  # set at construction
    end_time: Optional[datetime] = None   # lifecycle: set by complete()
    end_perf: Optional[float] = None      # lifecycle: set by complete()
    duration: Optional[float] = None      # lifecycle: computed by complete()
```

`end_time`, `end_perf`, and `duration` are `None` while a step is running and populated
when `.complete()` is called. Any code reading `duration` before `.complete()` is a bug,
but that bug should be caught by logic checks, not by the type system pretending the
field might always be None.

`model` is legitimately Optional here because non-LLM steps (`function`, `template`) have
no model. The field is structurally absent for those step types — it does not transition
from None to a value.

---

## The Abuse Pattern

An LLM encounters a function that calls `foo(step=step, context=context)`. The function
signature says `step: Dict[str, Any]`. The LLM refactors the function or adds a helper,
and the helper doesn't have `step` in scope. Instead of threading `step` through or
rethinking the design, the LLM writes:

```python
def helper(step: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None):
    ...
```

And then never uses either parameter. The type checker is satisfied. The tests pass.
The parameters are dead weight.

**Scripture Pipelines example — `llm_runner.py`:**

```python
def run_llm_with_mcp_tools(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text",
    step_name: str = "unknown",
    step: Optional[Dict[str, Any]] = None,       # ← never used
    context: Optional[Dict[str, Any]] = None,    # ← never used
    pipeline_config: Optional[Dict[str, Any]] = None  # ← never used
) -> Dict[str, Any]:
    return asyncio.run(_run_llm_with_mcp_tools_async(
        prompt, config, mcp_client, output_type, step_name, step, context, pipeline_config
    ))
```

The three Optional parameters are forwarded to `_run_llm_with_mcp_tools_async`, which
routes to either `_run_with_responses_api` or `_run_with_chat_completions`. Neither
sub-function uses them. They exist in three function signatures and touch zero logic.
They were added to "complete" a signature without a design intent behind them.

**A second abuse pattern — the weakened schema:**

```python
# pipeline_schema.py — Pydantic model
class StepConfig(BaseModel):
    name: str
    type: Optional[str] = None   # ← Optional in Pydantic

# pipeline_schema.py — JSON schema (same file, 150 lines later)
"required": ["name", "type"],   # ← required in JSON schema
```

The JSON schema (used by the linter) correctly identifies `type` as required.
The Pydantic model disagrees. This means a `StepConfig` constructed programmatically
without `type` passes Pydantic validation, bypasses the linter, and crashes at runtime
when the runner calls `step.type` and gets `None`. The Optional is hiding a real
constraint.

---

## Decision Rules

Before adding `Optional`, answer these questions in order:

### 1. Is it genuinely absent at some call sites — not just inconvenient?

If you're adding Optional because you don't have the value *in scope right now*, that
is a threading problem, not an optionality problem. Fix the call site.

```python
# Wrong: "I don't have step here so I'll make it Optional"
def helper(step: Optional[dict] = None):
    pass  # never uses step

# Right: thread it through, or restructure
def helper(step: dict):
    ...
```

### 2. Does the function behave differently (not just log differently) when it's None?

If the only difference is a log message or a richer error string, it's enrichment —
Optional is correct. If the function takes a fundamentally different code path, you
have two functions, not one function with an optional argument.

```python
# Suspicious: Optional that changes behavior
def process(data: dict, step: Optional[dict] = None):
    if step is None:
        return simple_process(data)      # ← two functions pretending to be one
    else:
        return full_process(data, step)

# Fine: Optional that only changes diagnostics
def process(data: dict, step_name: Optional[str] = None):
    result = do_the_work(data)
    logger.info(f"[{step_name or 'unknown'}] completed")  # ← enrichment only
    return result
```

### 3. Is there a schema or contract elsewhere that disagrees?

If a JSON schema, docstring, or another validation layer marks a field as required,
the Pydantic/dataclass model must agree. Two sources of truth means one is lying.

```python
# Wrong: JSON schema says required, Pydantic says optional
class StepConfig(BaseModel):
    type: Optional[str] = None   # Pydantic lets this through

# Right: agree with the schema
class StepConfig(BaseModel):
    type: str                    # Pydantic enforces what the schema promises
```

### 4. For lifecycle fields: is there a guard at the read site?

Lifecycle Optional fields are legitimate, but reading them before they're set is a bug.
Make that bug loud, not silent.

```python
# Silent failure
duration = step.duration or 0.0   # hides the bug if complete() was never called

# Loud failure — preferred
if step.duration is None:
    raise RuntimeError(f"Step '{step.step_name}' metrics not yet finalized; call complete() first")
```

The `StepMetrics.calculate_cost()` method already does this correctly:
```python
def calculate_cost(self) -> float:
    if self.step_type != "llm" or not self.model:
        return 0.0
    return calculate_cost(self.model, self.prompt_tokens, self.completion_tokens)
```
It gates on `self.model` being set before using it. Non-LLM steps structurally lack a
model; LLM steps are expected to have one after initialization. If an LLM step somehow
reaches `calculate_cost()` with `model=None`, the function returns 0.0 silently — which
is itself a mild abuse of the pattern. A better guard would log a warning.

---

## Protective Patterns

### Pattern A: Validator-enforced mutual exclusion (`GroupByPrefixConfig`)

When two fields are each Optional but *at least one* is required, encode that in
`model_post_init` rather than in documentation:

```python
class GroupByPrefixConfig(BaseModel):
    prefix_length: Optional[int] = None
    prefix_delimiter: Optional[str] = None

    def model_post_init(self, __context):
        if not (self.prefix_length or self.prefix_delimiter):
            raise ValidationError(...)
```

This is the right pattern. The validator is the contract. Without it, callers can
construct `GroupByPrefixConfig()` with both fields None and get a confusing runtime
error deep in the runner.

### Pattern B: Type narrowing at the boundary

Accept Optional at the boundary (where you genuinely don't know), assert non-None
before passing inward:

```python
def run_step(step_config: Optional[StepConfig]) -> None:
    if step_config is None:
        raise ValueError("step_config is required")
    _run_step_inner(step_config)   # StepConfig, not Optional[StepConfig]

def _run_step_inner(step_config: StepConfig) -> None:
    # No Optional anywhere in internal logic
    ...
```

### Pattern C: Sentinel objects instead of None

For lifecycle fields where None means "not yet" and you want loud failures:

```python
_UNSET = object()

@dataclass
class StepMetrics:
    duration: float | object = field(default=_UNSET)

    def complete(self):
        self.duration = time.perf_counter() - self.start_perf

    @property
    def safe_duration(self) -> float:
        if self.duration is _UNSET:
            raise RuntimeError("complete() not called yet")
        return self.duration
```

This is heavier than Optional but makes premature reads immediately visible.

### Pattern D: Code review heuristic — the "None path" test

For any Optional parameter in a function, trace every execution path where it is None.
If all None paths either:
- only affect log/error output, or
- correspond to call sites where the data genuinely doesn't exist

...then it's legitimate. If any None path reaches a computation that produces a
different result (not just a different error message), the Optional is hiding a design
decision that should be made explicit.

---

## YAML Pipeline Optionality Abuse

The same pattern plays out in Scripture Pipelines YAML pipelines, but the escape hatches are
different because the enforcement mechanism is the linter (`sp lint`), not Python's
type checker.

### Abuse 1: Declaring required inputs as `optional:` in prompt frontmatter

Every `.gpt` prompt file declares a contract in its frontmatter:

```
---
prompt:
  requires:
    - passage
    - scene
---
Analyze {{passage}} in the context of {{scene}}.
```

The linter's contract validation (`validate_all_step_contracts`) checks that every key
in `requires:` is provided by the calling step's `prompt.inputs`. An LLM that wants to
avoid a lint error about a missing variable has two escape routes:

**Route A — demote to `optional:`:**
```
---
prompt:
  requires: []
  optional:
    - passage    # ← was required, now optional
    - scene
---
Analyze {{passage}} in the context of {{scene}}.
```

The linter sees the body uses `{{passage}}` and checks that it's *declared* in either
`requires:` or `optional:`. Both lists count as "declared," so no error fires.
The step runs without providing `passage`, the template renders `{{passage}}` as an
empty string, and the LLM receives a malformed prompt. No warning anywhere.

**Route B — omit `requires:` entirely:**
```
---
prompt:
  description: "Analyzes a passage"
  # requires: key is absent
---
Analyze {{passage}} in the context of {{scene}}.
```

`linter.py:338` does `prompt_data.get("requires", [])` — missing key defaults to empty
list, which means "no required inputs." The contract check passes trivially.
`validate_gpt_body_declares_all_vars` then fires because `{{passage}}` and `{{scene}}`
are used in the body but not declared anywhere — but that check is only run on steps
with a resolvable prompt file path. If the path check earlier fails for any reason,
this second check is skipped.

**The correct behaviour:** `passage` and `scene` are structurally required by this
prompt. They are not optional enrichment — the prompt is meaningless without them.
The linter should refuse to pass a prompt that uses `{{var}}` in its body unless that
var appears in `requires:`, period. `optional:` should only be valid for vars that
the body uses *conditionally* (guarded by template logic), not for vars the body
uses unconditionally.

---

### Abuse 2: `${unbound_var}` in step `inputs` where the variable is never declared

When an LLM writes a step that references a context variable that hasn't been
produced by any previous step:

```yaml
- name: analyze-passage
  type: llm
  prompt:
    file: analyze.gpt
    inputs:
      passage: "${passage}"    # ← passage not bound anywhere above
      scene: "${scene}"        # ← scene not bound anywhere above
```

The linter's variable reference validator (`_validate_all_variable_references`,
`linter.py:624`) checks fields `["inputs", "condition", "saveas", "format", "input"]`
at the *step* level. But `passage` here is inside `prompt.inputs`, which is a nested
dict under `prompt:` — not the step's top-level `inputs:` key. The validator walks
the step's `inputs` field (a plugin-style dict), not the prompt's `inputs` sub-dict.

So `${passage}` inside `prompt.inputs` escapes the variable reference check entirely.
The linter passes. The runner calls `resolve("${passage}", context)` at runtime,
gets `None` (or raises), and the step fails — or worse, silently sends `None` to the
LLM as the passage text.

There are two independent escape routes here:

1. `prompt.inputs` is not in the set of fields the variable validator checks
2. `StepConfig.inputs: Optional[dict] = None` means a step with no `inputs` at all
   passes Pydantic validation — so even the structure check doesn't require the field
   to be present, let alone its contents to be valid references

---

### The Visibility Problem: Optionality Is Hidden in the Wrong File

When reading a pipeline, this step tells you nothing about which inputs are required:

```yaml
- name: analyze-passage
  type: llm
  prompt:
    file: analyze.gpt
    inputs:
      passage: "${passage}"
      scene: "${scene}"
      commentary: "${commentary}"   # ← is this required? optional? no way to tell here
```

To answer that question, you must open `analyze.gpt`, find the frontmatter, and read
the `requires:` and `optional:` lists. That is information hiding in the wrong place.
The pipeline is where the *caller* makes decisions — it should be readable without
cross-referencing the prompt file for every step.

An LLM authoring a pipeline has the same information gap. It cannot see which inputs
are optional without reading the prompt file, so it either omits inputs entirely
(runtime failure) or marks everything optional to be safe (silent failures).

**Proposed: surface optionality in the pipeline step itself.**

The pipeline step's `prompt.inputs` could use an explicit sentinel for optional
bindings:

```yaml
- name: analyze-passage
  type: llm
  prompt:
    file: analyze.gpt
    inputs:
      passage: "${passage}"           # no marker = required
      scene: "${scene}"               # no marker = required
      commentary: "${commentary}?"    # trailing ? = optional, may be absent
```

Or as a separate sub-key:

```yaml
- name: analyze-passage
  type: llm
  prompt:
    file: analyze.gpt
    inputs:
      passage: "${passage}"
      scene: "${scene}"
    optional_inputs:
      commentary: "${commentary}"
```

Either form makes the pipeline self-documenting and gives the linter an explicit
signal: `passage` and `scene` must be bound variables; `commentary` may be absent.

The linter can then enforce consistency:
- A var in the step's required inputs that is listed as `optional:` in the prompt
  file's frontmatter → warning (step treats it as required but prompt doesn't need it)
- A var in the step's `optional_inputs` that is in the prompt's `requires:` list →
  error (prompt needs it, caller says it might not be there)
- A var in the step's required inputs where `${var}` references an unbound context
  variable → error (the existing gap in `prompt.inputs` traversal)

This is additive — existing pipelines without the marker continue to work. The marker
is documentation that the linter learns to verify.

---

### A Third Category: Bootstrapped Variables

`append_to` targets are a special case that fits neither "required" nor "optional":

```yaml
- name: collect-analysis
  type: for-each
  for: item
  in: "${passages}"
  steps:
    - name: analyze
      type: llm
      prompt:
        file: analyze.gpt
        inputs:
          passage: "${item}"
          results: "${results}"    # ← [] on first iteration, populated on subsequent ones
      append_to: results
```

The runner auto-initializes `append_to` targets to `[]` on first use (`runner.py:525`),
so `${results}` is never truly unbound. The linter also adds it to `declared_outputs`
immediately, so no variable reference error fires. But the prompt receives `[]` as a
string on the first iteration — and because the template engine (`render_template`) is
pure regex substitution with no conditional support, there is no `{% if results %}` guard
available.

**The correct design for bootstrapped variables is to not reference them inside the loop
at all.** The accumulation list is a post-loop artifact — use it after the for-each
completes:

```yaml
# INSIDE the loop — prompt only sees the current item
- name: analyze
  type: llm
  prompt:
    file: analyze.gpt
    inputs:
      passage: "${item}"     # no results reference here
  append_to: results

# AFTER the loop — results is fully populated
- name: summarize
  type: llm
  prompt:
    file: summarize.gpt
    inputs:
      results: "${results}"  # safe: never empty, always complete
```

If a loop genuinely needs prior iterations' results (e.g. "don't repeat what's been
said"), declare `results` as `optional:` in the frontmatter and write the prompt body
so it is coherent when `{{results}}` renders as `[]`:

```
Prior analysis (empty on first pass): {{results}}
```

This is the only option available today because the template engine has no conditionals.

---

### What to Do in Existing Pipelines (Before Any Linter Changes)

These are the mitigations available right now, before #135 is implemented:

**1. Seed bootstrapped and uncertain variables in `variables:`**

Pre-declaring a variable in the pipeline's `variables:` block makes it visible to the
linter as "bound" and documents intent:

```yaml
variables:
  results: []        # explicit: bootstrapped by the for-each, empty until then
  commentary: ""     # explicit: may be absent; empty string is the safe default
```

This does not change runtime behaviour (the runner already initializes `append_to`
targets), but it is readable and prevents false "unbound" errors if future linting
covers `prompt.inputs`.

**2. Never omit `requires:` from a prompt frontmatter**

An absent `requires:` key causes `linter.py:338` to default to `[]`, meaning the
contract check passes trivially. Even `requires: []` is a meaningful statement: "this
prompt intentionally takes no required inputs." A prompt that uses `{{var}}` in its
body must always have a non-empty `requires:` or a deliberate `optional:` entry.

**3. Audit `prompt.inputs` for unbound `${var}` references manually**

Until the linter traverses `prompt.inputs` (the fix in #135), `${var}` references
inside `prompt.inputs` are not checked. Before running a pipeline, verify manually
that every `${var}` used as a `prompt.inputs` value is either in `variables:` or
appears in an earlier step's `outputs:`.

**4. Use `optional:` only for variables the prompt body treats as absent-safe**

If removing the variable from `prompt.inputs` would cause the LLM to receive a
nonsensical or incomplete prompt, the variable belongs in `requires:`, not `optional:`.
`optional:` is only correct for variables that the prompt body can render meaningfully
as an empty string — which, given the template engine has no conditionals, is a narrow
set.

---

### Protective Rules for YAML Pipelines

**Rule 1: `optional:` in a prompt frontmatter must be justified.**

A variable should be in `optional:` only if the prompt body guards its use — i.e.,
the body contains conditional logic that handles the absent case. Unconditional use
of `{{var}}` in a body means `var` belongs in `requires:`, not `optional:`.

Human review criterion: if removing the variable from inputs would cause the LLM to
receive a nonsensical prompt, it is required, not optional.

**Rule 2: `requires:` must be present and non-empty in any prompt that uses `{{var}}`.**

A prompt without a `requires:` key is an incomplete contract. The linter already
partially enforces this (it errors if the *step* provides inputs but the prompt has
no `requires:` key), but the reverse — prompt body uses vars, header declares none —
should also be an error.

**Rule 3: `prompt.inputs` variable references must be validated alongside step-level
variable references.**

The linter's `_validate_all_variable_references` should include `prompt.inputs` in
its traversal. A `${passage}` reference is equally invalid whether it appears in
`inputs: {passage: "${passage}"}` at the step level or inside `prompt: {inputs: {passage: "${passage}"}}`.

**Rule 4: Treat a missing `requires:` key differently from an empty `requires:` list.**

`requires: []` means "this prompt needs no inputs" — valid for prompts that take no
variables. A missing `requires:` key means "the author forgot to declare the
contract" — that is always an error if the body contains any `{{var}}` patterns.

---

## Summary

| Situation | Verdict |
|-----------|---------|
| Field absent at some call sites for structural reasons | Optional — legitimate enrichment |
| Field not set until a later lifecycle phase | Optional — legitimate lifecycle |
| Two functions fused by an Optional that changes behavior | Wrong — split the function |
| Field in scope but inconvenient to thread through | Wrong — threading problem |
| Field required by another schema or contract | Wrong — make it required |
| Field added to a signature but never used | Wrong — remove it |
| Multiple Optional fields where at least one is required | Optional fields + `model_post_init` validator |
| Prompt var in `optional:` but used unconditionally in body | Wrong — move to `requires:` |
| Prompt `requires:` key absent, body uses `{{var}}` | Wrong — missing contract declaration |
| `${var}` inside `prompt.inputs` referencing unbound variable | Wrong — linter gap; validate `prompt.inputs` refs |
