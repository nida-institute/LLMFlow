# Design — a prompt's documentation lives in `description`, and the model reads only the prompt

**Status:** approved ("agreed", 2026-10-06) and built, uncommitted. D3's choice to keep the
`# DATA SOURCES` heading and D4's warning are the AI's, within that approval, and are his to
overrule.
**Issues:** #176 (strip the frontmatter before the model call), which this absorbs.
**Author:** AI, from the Captain's direction and measurements of `data/prompt-structure.yaml`,
`src/llmflow/prompt_structure.py`, the shipped discipline and prompts, taken 2026-10-06.

---

## 1. Ruled by the Captain, 2026-10-06

1. **#176: the model receives no frontmatter.** Asked whether to keep `description` for the
   model, the Captain proposed instead: *"what if we allow description to contain markdown and
   move everything there, where it logically belongs?"*
2. **Reading A** — confirmed: `description` is the prompt's documentation for the people who
   maintain it, written in Markdown, never sent to a model. Everything in the body is for the
   model; anything a model cannot act on belongs in `description`.
3. **In this release.**

## 2. What exists, measured 2026-10-06

- **The whole `.gpt` file is sent, frontmatter included** — `steps/llm.py` `render_prompt`
  substitutes into and returns the full text. Every starter prompt rendered this session began
  `---\nprompt:\n  requires: …`.
- **The grammar** (`data/prompt-structure.yaml`): position 3 `# VARIABLES` (present iff the prompt
  declares variables, C1) and position 6 `# DATA SOURCES` (required). The discipline teaches
  VARIABLES as `- {{var}} — description` and DATA SOURCES as an input's origin and its fields.
  Position 12's own comment already says maintainer notes belong in `description:`.
- **Grammar findings are lint warnings, not errors** (`prompt_conformance_warnings`): a prompt out
  of shape still runs. So no change here can break a consumer's pipeline; it can only warn.
- **In scope here:** the two starter prompts and their template twins. The other four prompts in
  `prompts/` open with a header, so the grammar binds them, and before this change they already
  drew a grammar warning (no `# WHAT THIS STEP PRODUCES`); D4 adds a second. They are example
  prompts and are left as they are unless the Captain says otherwise.
  `prompts/sikkemese/typology-checking.gpt` has no header.
- **Not shared with Helm:** `llmflow-prompt-organization.md` is not in `data/helm-sync.yaml`.
- **The saving is small** — VARIABLES ~125 tokens and DATA SOURCES' provenance lines ~75–90 per
  starter prompt, ~2% of a rendered prompt. The point is that the model reads a prompt, not a
  maintainer's notes; cost is not the argument.

## 3. Design — for approval

**D1 — the engine strips the frontmatter before the call (#176).** `render_prompt` still parses
the header for the contract checks and returns only the substituted body. A prompt without a
header is unchanged.

**D2 — `description` is Markdown, and carries the reader's material.** A YAML block scalar
(`description: |`), so no parser change. Its suggested shape, taught by the discipline:

```yaml
description: |
  A reader's guide to a passage in its original language …

  ## Inputs
  - `original` — `type: scripture`, `SBLGNT` or `WLC`, `format: analysis`,
    `include: [ids, morphology, senses, glosses, syntax, frequency]`, `frequency_cutoff`
  - `english` — `type: scripture`, `BSB`, `format: milestones`

  ## Notes
  Design notes for whoever maintains this prompt.
```

The split is by audience, not by heading: **where an input came from** (which step, resource,
format, options) goes here; **how to read it** (what each field means — "`freq` is filled only for
a less common word", "`LN 34.22` is a sense, not a count") stays in the body, because the model
needs it.

**D3 — the grammar changes in two places.**
- **`# VARIABLES` leaves the body.** Removed from the positions and added to `refused`, with
  "variables are described in the header's `description`; the body names an input where it uses
  it". The existing C1 goes with it.
- **`# DATA SOURCES` keeps its heading and changes its job**: how to read each input — its
  structure and the meaning of its fields — with no provenance. Keeping the heading means no
  existing prompt is refused for it; the discipline says what now belongs under it.

*Recommended over renaming DATA SOURCES (e.g. to `# READING THE INPUT`), which says the new job
more plainly but warns on every existing prompt in every consumer for a heading change alone.*

**D4 — lint warns when `description` does not name a required input.** Every name in
`requires:` appears in `description` — so moving VARIABLES out cannot silently drop the
documentation of an input. A warning, like the rest of the grammar's findings.

## 4. The work

1. Tests first: the rendered prompt has no frontmatter; a prompt with no header is unchanged;
   `# VARIABLES` is refused with its message; a required input missing from `description` warns.
2. `steps/llm.py` (D1); `data/prompt-structure.yaml` and `prompt_structure.py` (D3); the
   description check (D4).
3. The two starter prompts and twins: VARIABLES and provenance into `description`; DATA SOURCES
   left with how to read each input.
4. The shipped discipline (`templates/sp/disciplines/llmflow-prompt-organization.md`), its
   README row if it describes the order, and the `audit-prompts` skill. **Their rendered copies
   under `docs/ai-context/sp/` need the Captain's approval to regenerate.**
5. `docs/sp-language.md`'s prompt format; CHANGELOG (Changed — every prompt's input to the model
   shifts slightly).
6. Verify by rendering both starter prompts offline and linting every pipeline. No `sp run` is
   needed; one is the Captain's to direct if he wants the output compared.

## 5. Not in this

- **Consumers' prompts** — discourse-flow's and Ears to Hear's. They will see the new warnings;
  a collab note saying what moved and why is worth sending, and is the Captain's to direct.
- **`format:` and `requires:`** stay where they are; only `description` changes role.
