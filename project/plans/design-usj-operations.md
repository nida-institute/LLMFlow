# USJ operations: flatten a document, locate a verse, rebuild a slice

Status: D1-D4 ruled (2026-09-22); one follow-on open, D3c. Not authorization to build.

Targets 0.2.1.28.

**This document is also the drafted body of a GitHub issue that has not been created.** The
title above is the issue title. Once the issue exists, put its number here.

> **Retitled 2026-09-22.** It opened as *"Window a scripture document by token budget, with a
> verse-sid cursor"*, which D2 and D4a between them made false: there is no verse-sid cursor, and
> the subject is not windowing. The old title is recorded here because the request that started
> this arrived under it.

## What already ships

Token-budget windowing is built and in use. `type: window` takes `size_by_tokens`,
`stride_by_tokens` and `model:`, counts with tiktoken, and `!window_advance` lets a step compute
where the next window starts. `nida-institute/discourse-flow` runs it today at
`size_by_tokens: 30000, model: gpt-4.1`.

**So the budget is not the gap.** The gap is what is being windowed, and what the cursor is:

| | the engine | scripture |
|---|---|---|
| what is windowed | a **list** | a **document** |
| what the cursor is | a **list index** | a **verse sid** |

## What a client carries to bridge it

Reported in
`collab/discourse-flow/2026-09-21-a-second-defect-log-and-three-more-things-sp-could-carry.md`;
their `docs/ai-context/project/architecture.md` §5 records it as belonging upstream.

Measured 2026-09-22 with `wc -l`: **350 lines** — `plugins/windowing.py` 142,
`plugins/milestone_content.py` 208. The collab note says 655; that figure does not reproduce
against their tree today and should not be repeated.

Four operations, and what each actually knows:

| | what it knows | whose |
|---|---|---|
| flatten document → list | nothing but USJ: concatenate each `para`'s content. Six lines | the engine's |
| locate a verse sid in the list | the two-kinds-of-nothing rule below, and little else | the engine's |
| rebuild conformant USJ from a slice | that a `para` may not span chapters (`usx.rnc:553`), so a slice crossing one becomes two paras plus a `chapter` node; and that a slice opening mid-verse carries `@vid` rather than a verse marker | the engine's |
| reassemble the book | pericopes, ordering, sequence numbers | **the client's** |

Flatten and rebuild are one round trip, not two utilities. An earlier revision of this document
assigned flatten to the client and rebuild to the engine, splitting a single contract across the
boundary.

## Two constraints on any shape this takes

**The cursor's two kinds of nothing must stay apart.** *End of input* is not *cursor not found*.
Returning `null` for an absent sid reads as "document finished" and silently truncates everything
downstream, surfacing much later as a coverage gap pointing nowhere near its cause. This is
`say-which-kind-of-nothing`; `llmflow.utils.discourse.Outcome` is the pattern to copy.

**A window boundary is a physical cut and carries no meaning** — `verses-are-milestones`. What a
client does about a unit the cut truncated — discard it, re-adjudicate it, where to put the
cursor relative to it — is that client's application semantics and is **out of scope here**. The
engine supplies the mechanism and says where the cut fell. It does not decide what a truncated
unit means.

## The decisions

Answer inline after each `=>`.

**D1 — where this lives in the language.** A second step type, a `format:`-like option on
`window`, or an operation in the sense of #241.

=>  Agreed, no new step type is needed.

*What follows:* `window` is the only windowing construct. Whatever is built attaches to it or
sits beside it as callable functions — D4.

**D2 — what the cursor is, in the YAML.** A verse sid is a string that looks like a reference
but addresses a position in a specific document. Whether the pipeline author writes a sid, a
reference that resolves to one, or neither, is a language decision.

=>  Windowing has no idea what an sid is.

*What follows:* the cursor stays a list index and the window step stays domain-blind — no verse
sids, no references, no scripture knowledge inside `window`. Translating a domain identifier to
a position is the pipeline's, called explicitly. This settles the shape of D4 as well: the two
operations nobody should reimplement cannot live *inside* the step, so they are functions the
pipeline wires.

**D3 — what a token budget counts.** Tokens are model-specific.

=> Can tiktoken ask the model?  If so, that's what we should do. I have only OpenAI keys.

*What follows, and what is still open.* **tiktoken cannot ask a model.**
`tiktoken.model.encoding_for_model` is a static lookup — 45 model entries plus 17 prefix rules,
measured 2026-09-22 — resolving to a local BPE vocabulary. It makes no request to any model.

For OpenAI models that costs nothing: tiktoken *is* OpenAI's tokenizer, so the count is exact,
and with OpenAI keys every count in use today is already right. For a model it does not
recognise, `steps/window.py:90-92` substitutes `cl100k_base` **without a word** — so a run
cannot tell an exact count from a guess. An exact count elsewhere means calling that provider's
own token-count endpoint, which needs a key for that provider and a network call per window
computation.

So the live question is not which library, but what the engine does when it is guessing:

**D3a — an unrecognised model: refuse, or warn and approximate?**

=>  warn and approximate.

A second half of D3 was not raised before and is untouched by the ruling: the budget counts each
list item's `json.dumps` separately, **not the assembled string the prompt receives**. Those are
different strings, and no measurement of the difference exists in either tree.

**D3b — is the budget a promise about what the model receives, or a reproducible proxy for
cutting a list?** If the first, it must count the rendered payload. If the second, present
behaviour is correct and the documentation must say so plainly instead of implying the first.

=> a promise or a guesstimate, depending on what is possible.

*What is possible, per provider.* An exact count exists for all three, and two of them cost a
network call:

| provider | exact count | cost |
|---|---|---|
| OpenAI | tiktoken, locally | none — it is OpenAI's own tokenizer |
| Anthropic | `POST /v1/messages/count_tokens` — `client.messages.count_tokens(model=…, messages=[…])` → `input_tokens` | an API call, and an Anthropic key |
| Google | `count_tokens` on the Gemini SDK's models surface | an API call, and a Google key. **Not verified in session** — recorded from documentation, not re-derived |

**tiktoken against a Claude model is not a near miss.** Anthropic's own guidance: it undercounts
Claude by ~15-20% on typical text, and by more on code or non-English input. This project's
payloads are Greek and Hebrew, so the error sits at the bad end of that range — which is what
makes D3a's silent fallback worth removing.

**Remote counting is dropped, and the reason is not cost.** It was raised here on the assumption
that the budget that breaks a run is the input one. It is not: a run dies because the *output*
was cut off at `max_tokens`, and no input-side count predicts that, because the length of the
answer is unknowable before asking. The exact input count also comes back free in `usage` on
every call. So an input budget needs only to be good enough to leave room, and paying a network
call per window to sharpen it buys nothing. That is #247's subject, and it is not this document's.

Recorded so it is not re-proposed: an exact count does exist for Anthropic
(`POST /v1/messages/count_tokens`) and for Google (`count_tokens` on the Gemini SDK's models
surface), and `_build_windows_token` counts **every item separately** —
`counts = [count_tokens(item) for item in items]` — so a remote counter used that way would be
of the order of 10^5 HTTP calls for a book. Counting assembled candidates instead would make it
affordable. Neither is worth doing for a budget whose job is to leave headroom.

What remains is a **local** accuracy question, with no network on either side:

**D3c — sum the items, or count the assembled slice?** Both use tiktoken and cost nothing. The
present sum silently omits the separators and the wrapper, so it understates what the prompt
actually receives; counting the assembled slice measures the string the model is handed. The
budget stays an approximation of an output-side risk either way — the question is only whether
the approximation should be of the right string.

=>

**D4 — whether the four operations are separately callable.**

=>  Discuss. Should we implement sid-to-index and slice-to-USJ on top of windows as helper functions? They sound convenient, and USJ actually IS part of sp semantics.

*The discussion.* Helper functions are the only shape left, and for the reason you give. D2 put
scripture knowledge outside the window step; "USJ is part of sp semantics" says where it goes
instead. `slice-to-USJ` is the clearest case — it carries USX conformance (a para may not span
chapters; a mid-verse opening needs `@vid`) that every consumer would otherwise re-derive, and
re-derive differently.

**Reassemble does not ship, under any shape.** It sorts *pericopes* and sets `sequence`. Its
generic core — concatenate per-window results, order by opening reference — is two lines, and
shipping it means shipping a signature that names the client's domain. Out.

**Flatten does ship, despite being six lines**, because it is `slice-to-USJ`'s inverse. The two
share one contract: what a stream item is. Ship rebuild without flatten and that contract has
two owners, which is the failure `design-is-declarative` names — they agree until they silently
do not.

**Keep the end-of-input test out of `locate`.** Their `content_index_of_sid` folds it in, taking
a `stop_after_sid` drawn from the last pericope's closing verse. That is their loop's semantics.
The engine's version answers one question — where is this verse in this stream — with a result
that tells *not found* from *past the end*, and the client decides what either means.

So three operations ship and one does not. What remains is where flatten lives:

- **A — three functions beside the window.** `flatten`, `locate`, `rebuild`, all called as
  `type: function`. The pipeline reads flatten → window → rebuild, so the round trip is visible
  in the YAML. `type: scripture` is unchanged.
- **B — `type: scripture` emits the stream; two functions beside the window.** Flattening moves
  into the step that already owns the representation, as an opt-in return. One less step per
  pipeline, at the cost of another member on the most loaded step in the language — and
  flattening a document you already hold is not fetching a passage.

**Recommended: A.** It is D2's ruling applied one level out — keep the scripture knowledge in
named functions the YAML shows, rather than growing `type: scripture`, which already carries
four formats and seven `include` families.

**D4a — A or B?**

=> I much prefer A.  And this is orthogonal to windowing, it can be applied to any set of characters.  The design should reflect that.  we may find other USJ functions to add for other purposes, so grouping them somehow is wise.

*What follows, and it reshapes the whole thing.* These are **USJ operations, not windowing
operations**. Nothing in flatten, locate or rebuild refers to a window: flatten takes a document,
locate takes a stream and a verse, rebuild takes any slice. Windowing is one caller and will not
be the only one — slicing a passage for a prompt, cutting a document for side-by-side display and
extracting a span for review all want the same three.

Two things that follow directly:

- **They are named and grouped as USJ**, not as window helpers, and the group is open — it is the
  place the next USJ operation goes. `llmflow.utils.scripture` already holds the representation
  code, so the group sits with it rather than beside `steps/window.py`.
- **Nothing in their signatures mentions a window**, a budget, or a cursor. `rebuild` takes a
  slice and returns conformant USJ; whether that slice came from a window, a verse range or a
  hand-written span is not its business.

This also disposes of the framing this document opened with. The engine is not gaining a
scripture window. It is gaining a small USJ vocabulary, which a domain-blind `window` can then be
pointed at — which is D1 and D2 holding at the level below them.

## Related

- **#241** — how the language expresses one domain with many operations. Parked; D1 keeps this
  inside `window` rather than making it #241's first customer.
- **#246** — three defects in the shipped token windowing, fixed separately and not waiting on
  this design: partiality decided by position rather than fill, `include_partial` ignored under
  `!window_advance`, and the tiktoken setup duplicated across two functions. Work order in
  `plan-window-token-defects.md`.
- **#247** — a response truncated at `max_tokens` reported as malformed JSON. This is the budget
  that actually breaks a run, and no input-side counting predicts it.
- **#248** — `--rewind-to` cannot resume a loop, so a run that dies mid-book restarts.
- **#249** — `parallel:` tested only with function steps; telemetry loses records concurrently.
- The encoding fallback (D3a) and the counting basis (D3b) are **not** among those fixes. They
  are design questions, not bugs.
