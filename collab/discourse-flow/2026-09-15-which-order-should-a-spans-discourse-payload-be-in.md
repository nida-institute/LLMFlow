# Which order should a `spans:` discourse payload come back in?

**From:** an AI session in `nida-institute/discourse-flow`.
**About:** **two requests** — that `include: [discourse]` return a span's citations in document
order (§2), and that discourse stay something a resource declares for itself rather than anything
that can be projected onto a translation (§3). Plus a report that the path works, and a note on
where your tests stop.
**Status: the requests in §2 and §3 are the Captain's, given 2026-09-15 — he directs this project and
yours. The prose and the measurements are the AI's, pending his review.**

## 1. It works, and it replaced code of ours

We have wired `type: scripture` with `spans:` and `include: [discourse]` so that each segment of a
pericope carries the Levinsohn citations for its own words, and run Philemon through it.

Until now the model wrote that field: it was told to copy every citation whose id fell in a
segment's range. It did not. On Philemon 1:20-20 — the words `n57001020001`–`n57001020013` — four
citations fall in range and it published three, two of them dropped and one imported from eight
words past the close, in the next verse. The two it dropped were both `Main clauses`, which for
Levinsohn is the organising frame rather than noise.

With your span filter deciding instead, on the same book: **106 citations given across the four
pericopes, 106 published, none outside the segment carrying it, none on two segments.** An exact
partition, because the spans tile the pericope. That deleted a range filter of ours and, with it,
the class of defect above.

## 2. The request: document order

Your filter at `src/llmflow/utils/scripture.py:576` is a comprehension over the family, so a span's
citations come back in the order the source states them. LGNTDF is emitted one feature file at a
time, so that order is grouped by feature within a verse rather than by word. Philemon 1:20-20
comes back:

```
n57001020001  Main clauses
n57001020008  Main clauses
n57001020003  Referential PoD
n57001020009  Topical Genitive
```

The ids are not ascending. Our own range filter sorted them — `plugins/milestone_content.py`, with
the reason recorded beside it: document order "is what a reader scanning the range needs", the sort
stable so two features on one word keep their relative order.

**We are asking for the payload to come back in document order, sorted by word id, stably** — so
two features on one word keep the source's relative order. A consumer asks for a span because it
has a stretch of text in mind; what it gets back should run the way that stretch runs. Otherwise
every consumer sorts, each in its own way, and the engine has handed out a sequence none of them
wanted.

`order:` on `type: alignment` is the precedent we would point at: there you made the sequence an
explicit part of the contract, with target order the default because it is what nearly every
reader wants. The same reasoning applies to a span's annotation, and document order is its
`[target]`.

The interface is yours. If you would rather keep source order available — it is the source's own
statement, and there may be a reader who wants exactly that — an `order:` set on `include:` would
serve both, and is a larger change than we are asking for.

**If this is not one you want to make, say so and we will sort on our side.** The content is right
either way; this is about who does it once rather than everyone doing it separately.

## 3. The second request: a translation has no discourse of its own to give

The Captain's words, and the principle we are asking you to hold to: **if a source-language text is
requested with signals, the signals come back in source order; if a target-language text is
requested with signals, discourse should come back only where someone has provided discourse data
for that target language.** A translation does not carry the discourse signals of the Greek or the
Hebrew. Levinsohn analysed Greek; his features are claims about Greek words.

**You already do this, and your own docstring states it better than we would.**
`src/llmflow/utils/scripture.py:1292` — *"Which corpus applies follows from the resource, not from
the language: a resource names its own with `discourse_path`."* We checked the consequences rather
than assuming them: `~/.sp/registrations/BSB.yaml` names no `discourse_path`, so a BSB request with
`include: [discourse]` returns `null` and warns (`:1298-1301`); BSB is `kind: usfm`, so `spans:` on
it raises in any case; and `type: alignment` takes no `include:` at all, so there is no route today
by which Greek features could arrive attached to English.

**So the request is that it stay that way, and that the contract say so** rather than resting on it
being currently impossible. The temptation is specific and will arrive with a feature rather than a
bug: an alignment is exactly the machinery that *could* carry a source annotation across to the
target, one word id to another, and it would look like a convenience. It would be a category error
— the English word aligned to a Greek point of departure is not a point of departure, because the
translation was not analysed. If annotation is ever offered on the target side of `type: alignment`
or anywhere else, we are asking that it come from a `discourse_path` registered for the target
resource and from nowhere else.

One thing we are not sure about and leave to you: a resource naming no discourse source logs a
warning. For a consumer who asked for a family the resource cannot have, `null` plus a warning may
be exactly right — it is `say-which-kind-of-nothing` working — or the warning may be noise on a
question that was always going to be answered "no". We have no evidence either way; we mention it
because the rule above makes that path the normal one for translations rather than an edge.

## 4. Where your tests stop, which you may want to know

`tests/test_scripture_spans.py` covers `spans:` with `include: [ids]` —
`test_a_span_carries_the_annotation_of_its_own_words_only`. We did not find a test for `spans:`
with `include: [discourse]`, so as far as we can tell we are the first to exercise line 576 on that
family. It behaved correctly on the run above; we mention it because a path carrying a consumer's
output with no test of its own is worth knowing about, not because anything went wrong.

One difference between the two families that makes the discourse case not merely the `ids` case
again: `ids` are read off the word rows the span already cut, while discourse is standoff and is
matched back by comparing a citation's `id` against the cut rows' `xml:id`. Greek is one row per
word and the two forms coincide, which is why it works for us.
