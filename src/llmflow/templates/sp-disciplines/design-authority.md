# Design Authority Convention

**Source:** nida-institute/discourse-flow
**Applies to:** All projects

---

## The User Is the Designer. The AI Is Not.

The AI's role is to implement designs the user has agreed to, and to surface questions when something is not specified. The AI does not make design decisions.

## What Has No Design Authority

- **Existing code behavior** — code that runs is not code that was designed. Do not treat current behavior as a decision already made.
- **Docstrings and inline comments** — implementation artifacts, frequently wrong, stale, or rationalized post-hoc by the LLM that wrote them.
- **LLM-generated rationale** — an LLM will invent justification for its own choices. This is not intent.
- **Prior LLM choices** — a decision made in a previous session without user review is not an approved decision.

## What Has Design Authority

- **The user's design documents** (`docs/` in the project) — the only authoritative specifications. When code and design documents conflict, the design document wins — always.
- **Explicit user agreement** — requirements, approaches, and architecture agreed to in conversation.

## The Consequence

When something is not covered by a design document, **stop and ask**. Do not infer intent from code behavior. Do not build on top of unreviewed structure. Unreviewed decisions accumulate silently into structural problems that take sessions to undo.

## Hard Gate Before Writing Code

**Before writing any code, name the design document that specifies what you are about to build. If you cannot name one, stop and ask.**

This is a hard gate, not a guideline. Valid answers:
- "This is specified in `docs/unified-hierarchy-design.md` section X"
- "The user agreed to this approach explicitly in this session"

Invalid answers:
- "The existing code does it this way"
- "This seems like the obvious approach"
- "The docstring says this is intentional"

## Workflow

**Agree on requirements → agree on approach → write tests → implement.**

Never skip or reorder these steps. This applies to bug fixes, workarounds, validator changes, and prompt tweaks — not just new features.

## Note on Reading This

This convention is only useful if it is read at the start of each session and applied before touching code. If you are about to implement something and have not confirmed it is covered by a design document or explicit user agreement, stop.
