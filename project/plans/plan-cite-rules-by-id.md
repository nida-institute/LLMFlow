# Plan — rules are cited by id, not by number

**Status:** approved — ruled in conversation, building now. #225

**Ruled by the Captain, 2026-08-31:** *"citing by id is going to be important long term. we
should bite the bullet in the next release we are starting now."* Rendering: the id leads and
the number disappears. Guards: both.

Prerequisite for `design-biblical-text-conventions.md` — no rule can move out of `sp/rules.md`
while its position is its identity.

## The defect

`data/ai-rules.yaml` states one fact twice, and the two statements disagree:

```
line 22   Order is significant: it is the numbering readers cite. Append rather than reorder.
line 25   id  stable slug. Cite this, not the number — collapsing or adding a rule renumbers.
```

The header already tells a reader to cite the id. Nine numeric citations were written anyway,
because `render_numbered()` puts the number where the eye lands and the id nowhere at all. The
convention was documented and unenforceable — `design-is-declarative`, breached inside the file
that declares it.

## What changes

**1. The renderer.** `src/llmflow/ai_rules.py:73`, `render_numbered()` → `render_rules()`,
emitting a bulleted list with the id leading:

```markdown
- `read-the-docs` — **Consult the docs before guessing.** The references listed in
  `sp/index.md` are authoritative for syntax, architecture and workflows. Read the file
  rather than recalling it.
```

Both renderers call it — `tools/update_ai_context.py` and `cli_utils.ai_rules_doc()` — so they
change together or not at all. `test_init.py` asserts the two outputs are equal, which keeps
that honest for free.

**2. The nine live citations**, converted:

| file | was | becomes |
|---|---|---|
| `docs/ai-context/project/index.md:21` | rule 20 | `todo-is-the-session-cache` |
| `docs/ai-context/sp/audits-pattern.md:6` | rule 17 | `audits-are-diagnostic` |
| `src/llmflow/templates/project/docs/ai-context/sp/audits-pattern.md:6` | rule 17 | `audits-are-diagnostic` |
| `docs/llmflow-language.md:259` | rule 5 | `model-capabilities` |
| `tests/test_plan_docs_index.py` (4 places) | rule 14 | `file-organisation` |
| `tools/update_plans_index.py:18` | rule 14 | `file-organisation` |
| `tests/test_scripture_step.py:8` | rule 1 | `read-the-docs` |
| `tests/test_sp_home_is_relocatable.py:13` | rule 29 | `design-is-declarative` |

**3. The yaml header**, so lines 22 and 25 stop contradicting each other. Order stays
significant for reading; it stops being the citation.

**4. Two guards** (written first — the project is test-driven):

- `test_rule_citations_resolve` — every rule id cited anywhere in `docs/`, `src/`, `tests/`,
  `tools/` exists in `data/ai-rules.yaml`. Catches a citation of a rule since renamed or
  removed, which is the failure the id was supposed to prevent and currently does not.
- `test_rules_are_cited_by_id` — no `rule <number>` outside the two history exemptions.

## What does not change

- **`CHANGELOG.md`.** It records what was true when written. Rewriting it would falsify the
  record, and `test_changelog_is_not_a_transcript` already governs that file.
- **`project/plans/*.md`.** Same reason: a plan is dated evidence of a decision, not a live
  reference. Both are exempt in the guard, by name.
- **`docs/design/optional-parameters.md`.** Its "Rule 1…4" is a local list about prompt
  frontmatter and has nothing to do with `ai-rules.yaml`. The guard must not match it — which
  is why the exemption is by path, not by pattern.
- **`~/.sp`.** Zero numeric citations; the portable layer is already clean.
- **The rules themselves.** No rule is added, removed, reworded or reordered. Ids are as they
  stand — all 35 already have one.

## One permission needed

`docs/ai-context/sp/rules.md` and `docs/ai-context/project/index.md` are under the hard
prohibition on modifying `docs/ai-context/`. `rules.md` is *generated* — the change reaches it
only by running `tools/update_ai_context.py` — and `project/index.md` needs a one-word edit.

**=> Permission to regenerate `docs/ai-context/sp/rules.md` and edit that one line in
`docs/ai-context/project/index.md`?**

=>

## Order of work

1. Both guard tests — failing, against the nine citations that exist today.
2. `render_rules()`, and the two renderers.
3. The nine citations.
4. The yaml header.
5. Regenerate `rules.md`; `tools/update_plans_index.py` for this file and the design doc.
6. Full suite, `ruff`, CHANGELOG entry.
