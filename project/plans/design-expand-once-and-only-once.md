# Design — a placeholder is expanded once, and only once

**Status:** approved in conversation 2026-09-02 — *"double expansion is always a defect"*, and
*"yes, write the plan and do it."* Two defects are measured below; the invariant and the two
fixes follow from them. #230

Origin, the Captain, arriving at the general rule after three narrower attempts failed:
*"so ... in a prompt, every variable must be expanded"*, then *"once and only once"*.

---

## 1. The invariant

> **Every placeholder in a prompt is expanded exactly once, and nothing else is expanded at
> all.**

Nothing in it is domain-specific. It holds for a passage, a lexicon entry, a versification
table, a legal filing. Unlike "the model must be given the data it reasons about", it needs no
knowledge of what a prompt is asking, so it is a property of the **language** and the engine may
enforce it for every user — `scope: language`, in the vocabulary of `data/ai-rules.yaml`.

Both of the prompt defects fixed earlier today are instances of it: a dotted `{{a.b}}` is the
expanded-zero-times case, and `optional:` was a licence for the same. Neither was recognised as
an instance until the invariant was named.

## 2. The two defects, measured

### 2.1 Expanded more than once — data is re-expanded as template

`render_prompt` substitutes context values into the template, **then** calls `resolve()` over
the result. `resolve()` handles `${var}` and `{var}`. So any value carrying braces is expanded a
second time, against the pipeline context.

Measured:

```
context:  passage_text = "the scroll said {secret} and also ${secret}"
          secret       = "SUBSTITUTED-FROM-CONTEXT"

rendered: Analyse this text: the scroll said SUBSTITUTED-FROM-CONTEXT
                             and also SUBSTITUTED-FROM-CONTEXT
```

Fetched content becomes a template against the context. It is silent — the output reads as a
well-rendered prompt — and it is injection-shaped: the data decides what gets substituted.
Scripture, a lexicon entry, a model's own prior output, or anything a `function` step returns
can carry braces.

### 2.2 Expanded zero times — a placeholder reaches the model

`extract_template_variables` skips any name beginning with `#`, `/`, `%` or `mixin:`. The first
three are Handlebars convention — `{{#if}}…{{/if}}` — in an engine that has no conditionals;
`docs/design/optional-parameters.md` says so in as many words, and CLAUDE.md forbids importing
Jinja2 precisely because the engine has its own resolution.

Measured: **no prompt, template or document in the repository uses `{{#`, `{{/` or `{{%`**, and
nothing in the engine handles them. The only code that mentions them is the two skip-lists, and
**they disagree** — `linter.py:139-141` skips `%`, `utils/io.py:191` does not.

So a name in those forms is exempted from the declaration check *and* substituted by nothing:

```
{{#directive}}  ->  reaches the model verbatim
```

Not a directive being handled. A placeholder ignored twice.

## 3. The fixes

### 3.1 Substitute once — resolve the template first, inject data last

The ordering is the defect, so the ordering is the fix. `resolve()` must run over the template's
own references, never over text that already carries injected values. Concretely: resolve
`${...}` and `{...}` in the prompt text **before** substituting `{{name}}` placeholders, and do
not resolve again afterwards.

A value is then inert. Whatever braces it contains reach the model as the data's own characters,
which is what the author asked for when they passed it.

**Assert it, do not merely reorder.** After substitution, the rendered text must contain no
placeholder that the engine would have expanded. A test that only checks the happy path would
not have caught the present defect, because the present defect *renders successfully*.

### 3.2 Expand everything — delete the skip-lists

Nothing uses the skipped forms and nothing handles them, so the honest change is removal, not a
second handler. A name beginning with `#`, `/` or `%` then reads as what it is — an undeclared
variable — and the existing declaration check refuses it. That closes the hole rather than
patching around it, and it collapses two disagreeing lists into none.

`mixin:` stays: `expand_mixins` genuinely handles it, and it runs before the contract check.

### 3.3 Assert no placeholder survives

A final check in `render_prompt`, after all substitution: if any `{{...}}` remains, refuse the
step rather than send it. This is the backstop that makes the invariant true rather than
intended — it catches whatever the static checks cannot see, including a value that itself
arrives containing a placeholder.

## 4. What this changes for a caller

**Breaking, in one narrow way that is the point.** A pipeline relying on `${...}` inside a
*value* being resolved will stop having it resolved. That behaviour is the defect, so the break
is intended; a pipeline wanting a value composed from other variables composes it in the step's
`prompt.inputs`, where the resolution is declared and visible, rather than by smuggling a
template through data.

`sp lint` should report this rather than leaving it to a run. Whether any consumer pipeline
actually relies on it is not knowable from here and is worth asking the three projects.

## 5. Out of scope, stated so it is not inferred

- **`{{mixin:...}}`** — a real mechanism, handled by `expand_mixins`, unchanged.
- **Single-brace `{var}` in prompt bodies.** `prompts/sikkemese/typology-checking.gpt` uses it
  and is referenced by no pipeline. Whether the single-brace form is supported syntax at all is
  a separate question; this design neither blesses nor removes it.
- **Whether a prompt should have been given some data** — the judgment half of
  `source-text-required`, which no test can reach.

## 6. The guard

One new test file, and it must be non-vacuous — it asserts the two defects are gone by
reproducing them, not by rendering a clean prompt successfully:

| case | expectation |
|---|---|
| a value containing `{name}` where `name` is in the context | the braces reach the model unexpanded |
| a value containing `${name}` likewise | unexpanded |
| `{{#directive}}` in a body | refused, as an undeclared variable |
| `{{name}}` declared, passed | expanded exactly once |
| a value that itself contains `{{name}}` | reaches the model unexpanded, and is not refused |

The last row is the one that distinguishes "expanded once" from "expanded until stable", and it
is the case a naive implementation gets wrong.

=>
