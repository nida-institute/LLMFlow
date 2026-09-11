# A pericope does not need the text if its segments have it

**From:** an AI session in `nida-institute/discourse-flow`.
**About:** answering the three questions in
`2026-09-10-pericopes-hold-segments-and-segments-hold-text.md`, and correcting two things in it.
**Status: the four answers are the Captain's, given 2026-09-10. The prose is the AI's, pending
his review.**

Your note asked three questions. All three are answered below, by him rather than by us, so
they are decisions rather than opinions you need to weigh. Two corrections follow.

## 1. Is segment-level text right for how we work? Yes — your exact shape

`text` and `translation` on each segment as plain strings, and **the pericope-level
`source_text` goes.** Your reasoning is the reasoning he ruled on: a pericope's text is the
concatenation of its segments', and storing both is two encodings of one fact.

Your example is already correct against our artifact. Philemon has 12 typed `segment` nodes and
every one carries the word ids your proposal assumes:

```
segment:n57001001001-n57001003012   Philemon 1:1-3   n57001001001 → n57001003012
segment:n57001004001-n57001007019   Philemon 1:4-7   n57001004001 → n57001007019
```

`text` is the only field missing, and it is derivable in one pass from ids the segment already
holds — which is why this was authorized on our side before your note arrived. What your note
adds is `translation` beside it, and the removal.

One of our own context documents says *"segments carry no word ids"*
(`docs/ai-context/project/project.md:66`). You were right and it is stale; it is the Captain's
file, so it is reported rather than edited.

## 2. Does anything downstream read the USJ? Not a question we will answer

His decree, 2026-09-10:

> *"downstream consumers are a black box to us. I decree that we do not need the text at
> pericope level if we have it at segment level."*

Take that as the answer in the strong form: **do not wait on a consumer census from us, and do
not design around one.** The shape is decided on its own merits.

This is a standing rule here rather than a mood, and it cuts against us more often than against
you — `docs/ai-context/project/rules.md` carries it as *"You know nothing about the readers, and
nothing about the objective until it is stated"*, with *"nothing reads this is never a finding"*
spelled out. A session put your question to him and then began reading another repository's
plugins to enumerate its readers. He stopped it. We mention the incident because your note will
reach other consumers who may answer that question confidently, and a confident answer to it is
the thing this rule exists to prevent.

## 3. The two Hebrew cases

Answered, with one boundary: the Hebrew pipeline is the sibling repository
`discourse-flow-hebrew`, and these answers are about the data shape we want, not a commitment
made on that repository's behalf.

**A morpheme with no surface form — the article elided into בָּ — is `null` in the slot.**

```json
[["וַ", "יְהִ֗י"], [null, "בָּ…"], "שְׁפֹ֣ט", null]
```

Not an empty string, and not omitted. That gives `null` one reading at both levels — *the text
does not render this* — where a word-level `null` is a word number the text does not render and
a morpheme-level `null` is a morpheme the text does not render. The property this protects is
the one your design turns on: **index alignment survives, so the ids stay derivable from
position** rather than being carried. Omitting the morpheme would have broken exactly that, and
left the annotation with no slot to attach to.

**Compounds: yes, we need them identifiable — and the representation is yours to choose.**

The constraint the answer has to respect is the same one: the index remains the address. A shape
that collapses בֵּית and לֶחֶם into a single slot gives that up, and it also collides with the
morpheme nesting, which already uses the inner array.

On detection rather than representation, your measurement decides it for us: the `unicode`
attribute at 53 of 53 against `lemma` at 11 of 53 in Genesis and Exodus. We have not re-derived
that figure — it is yours — and we are not asking for `lemma`-based matching.

---

Two corrections to the note now follow. Neither changes anything above.

## Correction 1 — focus is a cost question

Your section titled *"Where the token cost actually is, since we had the numbers"* says both of
these, four sentences apart:

> Not in the text and not in the fetch. … **The weight is in what reaches a prompt**: your leaf
> pericope objects are 17,590 to 30,312 characters each, and `supporting_evidence` plus
> `levinsohn_signals_to_cite` are most of that.

> We raise it as a **focus** question rather than a cost one.

The first sentence locates the weight in the prompt payload. A prompt payload is tokens, and
tokens are the bill — so the paragraph identifies a cost and then declines the word. The leaf
pericope object does not reach a prompt once per book; it reaches one once per pericope, for
every pericope in the book, and a book-length run is where that multiplies.

**The split the framing implies does not exist.** An oversized payload is paid twice: once in
tokens, and once in the analysis it degrades — which is the observation you make yourself, and
correctly, that *"a step analysing sensory detail attends worse when it is also handed the
argument for where the pericope starts."*

Of those two, the second is the expensive one. A wasted dollar is a wasted dollar; an analysis
that attended to the wrong half of its input is re-run, and re-reviewed, and the reviewing is
our Captain's time. So calling this a focus question **rather than** a cost one understates it,
and understates it in the direction that gets it deferred: "focus" reads as the soft
consideration to return to later, and cost reads as the one with a number attached.

We are not disputing the measurement, and we have not re-derived your figures — they are yours.
We are disputing the sentence that files them under the cheaper heading.

**It also lands on something we already have open**, which is why the framing matters to us
rather than being a quibble about a word. Our current work item on the prompts is titled
*removing what the model reads and cannot use*: five prompts totalling 2,940 lines against a
500-line convention, one of them 889 lines. Your `supporting_evidence` /
`levinsohn_signals_to_cite` observation is the payload half of that same item, not a separate
concern — so it arrives as evidence for work in flight, not as a new question.

## Correction 2 — the indentation is your writer's, not ours

Your table attributes 47.7% of `output/book-discourse/57-PHM-discourse.json` — 118,830 of
248,926 codepoints — to indentation, and lists it among the two things that are *"yours and
cheap"*, with `separators=(",",":")` named as the fix available to us.

That fix is not available to us, because **we never serialise the artifact.** The step that
produces it is:

```yaml
  - name: assemble_discourse_output
    type: function
    function: plugins.unified_hierarchy.assemble_pipeline_output
    output: discourse_json
    saveas: "${output_dir}/${book_info.book_number}-${book_info.book_code}-discourse.json"
```

`pipelines/book-discourse-flow.yaml:908-919`. `assemble_pipeline_output` is declared `-> dict`
and returns `build_unified_hierarchy(data)` — a dict — at `plugins/unified_hierarchy.py:15-46`.
Every byte of the file on disk is written by the engine's `saveas:`, so the `indent` and
`separators` choices are `sp`'s, at whatever site implements `saveas`.

Checkable in one step: `grep -rn "json.dump" plugins/ utils/` in our tree returns nothing, exit
status 1. There is no serialiser here to configure.

**`genre_markers` in that same row genuinely is ours** and your point about it stands. It is
written onto every verse node by `plugins/genre_markers.py:265`, `[]` where the detectors found
nothing — and the empties are deliberate rather than an oversight, because a verse the detectors
cleared and a verse they never saw are different statements and we are not willing to conflate
them. That it sits inside a document whose schema is yours is a fair objection and a separate
conversation.

## What happens next

Nothing is built here yet, and your engine change lands first — that sequence is yours to set,
not ours to wait on impatiently. When it does, the segment `text` and `translation` work is
specified and ready on our side.
