# Plan — window semantics: the shipped example, the spec gap, two inconsistencies

**Source:** `nida-institute/discourse-flow`, `collab/sp/windowing-semantics-gap.md`, written
2026-08-21 by an AI session in that repo. A consumer report, not design authority.

**Status:** complete, 2026-08-21. Items 1 and 3 landed; item 2's two decisions were ruled and
built — D1 in a third form the Captain drove out, D2 as recommended. §5 records what was
deliberately left alone.

---

## 1. Verified before acting

Six checkable claims in the report, all confirmed against this repo:

| claim | verdict |
|---|---|
| the spec has no hits for `cursor` / `logical` / `physical` / `resume` | **0** — confirmed |
| `size` is unresolved while `in` is resolved | `size = step.get("size")` at `window.py:324` vs `resolve(step.get("in"), context)` at `:315` |
| `window_num` set at runtime, unknown to the linter | set at `window.py:241` and `:390`; **zero** occurrences in `linter.py` |
| the static `windows` list is built then discarded in dynamic mode | built `:335-347`, `has_advance` checked `:377` |
| the worked cursor example teaches the dropped-unit form | `cli_utils.py:381` — `pericopes[-1].opening_verse_sid` |
| the two guards are real and unadvertised | `cursor: null` stop, and the no-advance raise at `:281` |

**One thing the report understated.** It described the example as living in "CLI help output,
which an agent reading the language reference has no reason to run". In fact the constant is
`LANGUAGE_QUICKREF_DOC`, and `sp init` **writes it to `docs/llmflow-language-quickref.md` in
every project** (`cli_utils.py:1885`). Four shipped AI-context documents then point assistants
at that file as the reference for writing pipeline YAML (`cli_utils.py:1230`, `:1275`, `:1280`,
`:1333`). The buggy example was installed guidance, not buried help text.

**Independent corroboration, same day.** Asked in this repo how to make a window start at the
end of a logical unit, this session read the field table, answered `end_when`, and was
corrected by the Captain — *"there's a higher order operator .. perhaps using !"*. Two agents
in different repositories took the same wrong path from the same page within hours. That is
what makes this a documentation defect rather than one session's mistake.

---

## 2. Item 1 — the shipped example. **Done.**

`cli_utils.py` now teaches the kept-edge form
(`pericopes[-2].first_verse_sid_after_pericope`), states that the cursor is a list index
rather than a domain identifier, names both halves of the pattern (discard *and* resume) and
advertises the two guards.

Guarded by `tests/test_window_cursor_guidance.py`, written first and failing on the shipped
text. Two of its four assertions initially passed for the wrong reason — `index` and `discard`
occur elsewhere in those documents — so both were scoped to the `type: window` section before
any fix was written.

## 3. Item 3 — the spec subsection. **Done.**

`docs/llmflow-language.md` gains "Physical windows, logical units", placed **before** the field
table so a reader meets the semantics ahead of the complete and inviting `stride` row. It
carries the physical/logical distinction, the three-step corollary, "half is worse than none",
and the cursor-is-an-index rule.

**Added beyond the report's proposal, and the reason for it:** an explicit statement that
**the engine enforces none of steps 1–3**. The report's "rule that holds" is pipeline-side
discipline; writing it into the spec risks a reader assuming the runtime guards it. It does
not, and a run that gets it wrong loses content silently.

---

## 4. Item 2 — two inconsistencies, two decisions. **Both ruled; see beneath each.**

Each is a "one side or the other is wrong" case. Both are small and testable; neither should be
guessed.

### D1. `size` is not resolved, while `in` is.

`size: "${window_size}"` fails validation; `in: "${list}"` works. Same step, two rules.

- **A — resolve it.** `size` becomes a variable like everything else, so a pipeline can take
  its window size from `--var window_size=50`. Cost: a `--var` value arrives as a *string*, so
  resolving is not enough — the validation at `window.py:344-347` requires `isinstance(size,
  int)` and would reject `"50"`. So A means resolve **and** coerce a digit string, with a clear
  error for anything else. Slightly more code than it first looks.
- **B — document the asymmetry.** One line in the field table: `size` is a literal, not an
  expression. Cheapest, and honest, but it leaves a trap that reads as a bug to every consumer
  who hits it.

The AI's read: **A.** The asymmetry has no reason behind it that this session could find, and
window size is exactly the kind of thing a pipeline wants to parameterise per run.

=>

**Ruled and built, 2026-08-21 — neither A nor B, but a third form the Captain drove out.**
First B′ (explain, do not resolve), on his reasoning that *"being able to compute this at the
start of a 'loop' is also helpful for the implementation … a variable that changes during loop
execution is going to be harder to debug, that's what the cursor is for."* Then he marked its
limit himself — *"my argument doesn't reach variables that can be resolved before the 'loop'
begins"* — and, on the lint gap, *"lint can warn that it can't determine if it's a positive
integer or not, and that runtime errors are possible."* Built on *"build it, don't forget unit
tests"*: `size` and `stride` resolve once at step entry, digit strings coerce, lint warns that
it cannot verify the value, and per-iteration resolution stays unsupported. `include_partial`
and the two token fields remain literal — a string→bool coercion has no demand behind it.

### D2. `window_num` is valid at runtime and fails lint.

`_run_window_dynamic` and the static path both set `window_num` and `_window_index` in the
iteration context; the linter's available-variable set contains neither, so `${window_num}` in
a step input fails `sp lint` while working in a real run.

- **A — teach the linter.** Add `window_num` (and `_window_index`) to the variables a window
  step makes available. Keeps a genuinely useful value — window numbering in prompts, filenames
  and logs — and breaks nothing.
- **B — stop setting it.** Removes the inconsistency in the other direction. But any pipeline
  already using `${window_num}` breaks, silently at first, and this session cannot see the
  consumer repositories to know who does.

The AI's read: **A.** B removes working behaviour to fix a linter omission, and the blast radius
is unknowable from here.

**Ruled A and built, 2026-08-21.** The Captain: *"let's finish both of these now."* He did not
name A or B; the AI took its twice-stated recommendation as the instruction, and records that
here rather than implying a ruling he did not give. The linter now injects the five variables
the runtime sets — `window_num`, `_window_index`, `_window_first`, `_window_last`,
`_window_cursor` — plus the two `_for_each_*` frames, making `window` symmetric with
`for-each`. `tests/test_window_lint_context.py` pins each name, and pins that an undefined
variable and a plausible near-miss (`window_index`, no underscore) still fail lint.

---

## 5. Not in scope, recorded so it is not lost

- **`window.py:334-346`** builds the static `windows` list even in dynamic mode, then discards
  it. Harmless, and it briefly suggests the two modes interact. Tidying it is a separate change
  with no user-visible effect.
- **The report's sharp edge 3** — it added a tag-tolerant `SafeLoader` to keep parsing pipeline
  files, because `!window_advance` is a YAML tag. `docs/python-api.md` and the topic index
  already recommend `load_pipeline()` *"over re-parsing pipeline YAML or shelling out to `sp`"*
  (#175), which would have avoided the workaround. The finding worth keeping is not the
  consumer's mistake but ours: the API is not surfaced where somebody writing pipeline tooling
  would look.
- **A guard for side writes and for language-vs-Python reimplementation** — see
  `plan-ai-rules-single-source.md` §9. Rules 23 and 24 there are written; nothing checks them.
