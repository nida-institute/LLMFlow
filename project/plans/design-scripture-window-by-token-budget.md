# Window a scripture document by token budget, with a verse-sid cursor

Status: proposed (2026-09-21)

Targets 0.2.1.28. **Proposed is not authorization to build** — the four decisions at the foot are
unanswered, and they change what gets built.

**This document is also the drafted body of a GitHub issue that has not been created.** The title
above is the issue title. Once the issue exists, put its number here and the document becomes an
ordinary design note.

## What

`window` iterates a **list**, and its cursor is a **list index**. Scripture is a **document**,
and its cursor is a **verse sid**. A project windowing scripture by token budget has to bridge
that gap itself.

## Why it is the engine's

Reported by `nida-institute/discourse-flow` in
`collab/discourse-flow/2026-09-21-a-second-defect-log-and-three-more-things-sp-could-carry.md`,
where it is 655 lines of adapter across `plugins/windowing.py` and `plugins/milestone_content.py`,
and their own `architecture.md` §5 already records it as belonging upstream.

Four operations, and every project windowing scripture by token budget needs all four:

1. flatten the document to a list
2. translate a verse sid to an index
3. rebuild conformant USJ from a slice
4. reassemble the book

Only (1) and (4) are about their pipeline. (2) and (3) are about the scripture representations
this engine already owns — `format: usj`, the word addressing, `usj_to_text`.

## One constraint, learned expensively downstream

**The cursor's two kinds of nothing must stay distinguishable.** *End of input* is not *cursor
not found*. Returning `None` for an absent sid reads as "book finished" and silently truncates
the segmentation, surfacing much later as a coverage gap pointing nowhere near its cause.

This is `say-which-kind-of-nothing` in a case where the engine has not yet applied it. Whatever
shape a scripture window takes, that distinction has to survive it.

## Decisions needed before anything is built

**D1 — where this lives in the language.** A second step type, a `format:`-like option on
`window`, or an operation in the sense of #241. `use-the-pipeline-language` says iteration is
`window` and chunking is `window`, which argues against a new step type; #241's open question —
whether standalone operations are expressions or step methods — governs the alternative.

=>

**D2 — what the cursor is, in the YAML.** A verse sid is a string that looks like a reference
but addresses a position in a specific document. Whether the pipeline author writes a sid, a
reference that resolves to one, or neither, is a language decision.

=>

**D3 — what "token budget" counts.** Tokens are model-specific. Whether the budget is declared
in tokens against a named model, in characters, or in words is a question about who has to be
right for the window to be correct.

=>

**D4 — whether the four operations are separately callable.** Flatten and reassemble are useful
on their own; sid-to-index and slice-to-USJ are the halves nobody should reimplement.

=>

## Related

- #241 — how the language expresses one domain with many operations. Parked, and this may be its
  first real customer.
- `say-which-kind-of-nothing` — D-level constraint above, not a nicety.
- `verses-are-milestones` — a window boundary must not become a structural claim.
