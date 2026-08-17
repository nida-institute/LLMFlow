# Design: Prompt Mixins

**Status:** Implemented — historical record. Describes why the code looks as it does; do not rebuild from it. Verify against the code before relying on any detail.

Shipped as `expand_mixins()` in `utils/io.py` (`tests/test_mixins.py`).

## Problem

Prompt files (`.gpt`) frequently repeat the same content:

- Output language guidelines (register, tone, vocabulary constraints)
- Guardrails that apply across a family of prompts (e.g., "do not import background
  from training knowledge")
- Schema documentation that is shared by multiple steps
- Framing instructions that define a persona or task context for a whole pipeline

When these are duplicated, updating them is error-prone — one file gets updated,
others don't, and the inconsistency is invisible until a human notices the outputs
have diverged.

---

## Design Goals

1. A single source of truth for shared text — edit once, all prompts pick it up
2. Minimal new syntax — the mechanism should be obvious to someone reading a prompt
3. Compatible with the existing prompt contract model (`requires`, `optional`)
4. Linter-checkable — `sp lint` can verify that included files exist
5. Variable substitution works inside included content (same `{{var}}` rules)

---

## Proposed Approach: Inline `{{mixin:...}}` Directive

Mixins are inserted inline using the same substitution syntax as `{{var}}`:

```
{{mixin:mixins/output-language.md}}
```

Place it anywhere in the prompt body — top, middle, or bottom. The renderer
expands it to the file's contents before sending the prompt to the model.
Mixin paths are resolved relative to the calling prompt file's directory.
Mixin files are plain Markdown with no header — they support `{{var}}`
substitution using the same variables available to the calling prompt.

Example prompt:

```
<!--
prompt:
  requires:
    - book
    - scene
    - source_text
-->

System: You are producing the Hearts layer for one scene in {{book}}.

{{mixin:../mixins/output-language.md}}

## Source text

{{source_text}}

{{mixin:../mixins/guardrails-no-training-knowledge.md}}
```

---

## Where Mixin Files Live

Mixins live inside the project's `prompts/` directory as a `mixins/` subdirectory,
alongside other prompt families:

```
prompts/
├── build-book/
│   ├── scene-bodies.gpt
│   └── scene-hearts.gpt
└── mixins/
    ├── output-language.md
    └── guardrails-no-training-knowledge.md
```

This keeps everything prompt-related in one place and under version control with
the project that uses it. There is no global mixin registry — each project maintains
its own.

---

## Open Questions

1. **Nesting** — should mixin files themselves be allowed to contain `{{mixin:...}}`?
   Simple to support; could make dependency tracing harder. Recommend no for now.

2. **Effect on the linter** — `sp lint` should verify:
   - All referenced mixin files exist
   - Circular mixin references are detected and rejected

3. **Effect on debug request files** — the request file should show the fully
   expanded prompt (post-mixin, post-substitution), which is what the model
   actually received. This is already the right behavior for detecting freelancing.

---

## Alternatives Considered

**Pipeline-level `inputs` that load file content** — e.g., `output_guidelines:
"@file:mixins/output-language.md"` passed as a variable. Works today with no new
syntax. Downside: the shared content appears as a variable value, not as part of
the prompt structure; harder to see in the header what a prompt depends on; doesn't
compose with the prompt contract model naturally.

**Prompt inheritance** — a `base` key pointing to a parent prompt that this one
extends. More powerful but significantly more complex; inheritance chains are hard
to read and debug. Mixins are simpler and compose without hierarchy.
