# `include:` forces `format: usj`, so annotation cannot be had at milestone cost

**From:** an AI session in `nida-institute/discourse-flow`.
**Status: drafted by the AI, pending the Captain's review.**

One finding about `type: scripture`. We think the coupling is a defect rather than a design,
and we would rather ask than work around it.

## The rule as it stands

`docs/llmflow-language-quickref.md`:

```yaml
  include: [ids, discourse]   # optional — valid only with format: usj
```

And `docs/ai-context/sp/scripture-representations.md` costs the four forms:

| form | cost |
|---|---|
| `plain` | baseline |
| `milestones` | **1.072× — the default, "almost always right"** |
| `usj`, no `include` | 2.56× codepoints, 6.74× as escaped JSON |
| `usj` + families | up to **11.78×** |

So a pipeline that needs any annotation cannot have milestone-cost text. The two choices —
how the text is represented, and which annotations come back — are independent questions, and
today one answer forces the other.

## Why we think they are separable

Your own document says the annotation is standoff:

> Everything `include` delivers lives under one key, `scripture_pipelines`, which the USJ
> specification does not define and never will.

and of `syntax`, "the constituency tree, **standoff** — one entry per sentence".

Six of the seven families are sidecars keyed by word id. `discourse`, `morphology`, `senses`,
`glosses`, `referents` and `syntax` need nothing from the shape of the text; they would be the
same payload beside milestone text as beside USJ.

**`ids` is the exception, and it is the interesting one.** It is not container content — it
becomes `srcloc` on a `\w` node, "where USX already carries a word's source location". So `ids`
does need somewhere in the text to live. That is a real constraint and we are not asking you to
pretend otherwise.

## What it costs us, measured

Philemon, 25 verses, fetched as `format: usj` with
`include: [ids, discourse, morphology, senses, referents, syntax]`:

| | |
|---|---|
| Levinsohn citations in the book | **106** |
| words carrying a `\w` anchor | **334** |
| words anchored that nothing references | **228** |

And for one pericope, Philemon 1:1-7, in the artifact we publish:

```
the Greek as prose      :     622 chars
the JSON that carries it:  14,045 chars
inflation               :    22.6x
```

The text arrives as 107 word objects separated by 106 punctuation strings — `' '` ninety-eight
times, then `', '`, `'· '`, `'’ '`, `'. '`. There is no prose in it at all; a reader
reconstructs the sentence by concatenation. Every word carries `lemma` and `strong` as well,
which arrive with `morphology`.

## The line that states the problem best is yours

> **asking for a family you do not read is pure cost.** `include` defaults to empty
> deliberately, because a payload nobody asked for is a payload nobody checked.

We agree, and we have our own housekeeping to do against it. But the inverse is what this note
is about: **asking for a family you *do* read forces a text form you did not want.** We need
`discourse` — it is Levinsohn's features, the entire subject of this pipeline — and the only
way to get it is the 11.78× row.

## What we are asking

Not for a specific design. Two questions:

1. **Can `include` be valid with `milestones` and `plain`** for the six standoff families,
   with the payload under `scripture_pipelines` exactly as it is today?
2. **For `ids`, is there a form between "every word" and "none"?** A consumer that cites word
   ids needs anchors only where something references the word. For Philemon that is 106 of 334.
   Our own segmentation prompt already describes that shape to the model — *"anchors sit at
   Levinsohn-marked positions"* — which is what the retired file-based loader produced, and it
   is not what the engine returns.

If the answer to the second is "anchor everything or nothing", that is a fine answer and we
will design around it. We ask because the middle form is what our prompts were written for.

## What we are not doing

**Not stripping the payload ourselves.** A locally-thinned USJ would be a fourth shape that is
no `sp` format at all, and this repository has already paid for that mistake once — 555 lines
of `milestone_content.py` re-deriving what the engine delivers. If the right answer is that we
take the 11.78× and live with it, we would rather do that than invent a private format.

So nothing is blocked, and there is no deadline here. The cost is recorded on our side and the
pipeline runs.
