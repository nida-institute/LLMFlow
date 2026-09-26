# Plan — the starter example writes passage commentary for group leaders and preachers

**Status:** proposed (2026-09-25). The rulings in §2 are the Captain's and are settled; the
sample output in §5 is drafted and needs his review, because it is domain content. **Nothing is
built.** `proposed` is not authorization to build.
**Issue:** #244. *Sequencing corrected 2026-09-26: **#176 does not gate this work.*** It was
recorded as gating on the reasoning that the prompts would otherwise be rewritten against
post-frontmatter-stripping behaviour. Read against `steps/llm.py`, that rework does not exist:
`body` is computed at line 88 for the contract check and discarded, and the whole file reaches the
model as `rendered_prompt` (157 → 232 → 310). So #176 changes what the model receives and the
token count, and changes nothing about the pipeline YAML or how a `.gpt` file is authored. **What
it does gate is #255** — replay aligns the `.gpt` file against a captured request, so if #176
strips at render time the capture shortens and `--prompt` must be stripped to match; if it strips
only at the call site, captures are unaffected. That choice is open inside #176 and is recorded in
neither issue.
**Depends on:** the Parallel Passages step → **#258**, filed 2026-09-26. Ruling 7 makes the
commentary step require that input, so the example cannot be finished without it.
**Author:** AI, from the Captain's direction on 2026-09-25 and from the passage text fetched the
same day. Every claim about what Mark 1:1-8 contains was read from the text, not recalled.

---

## 1. What I understand the goal to be

`prompts/hello.gpt` asks for greetings in five languages and `reply.gpt` replies to one. Neither
touches scripture, a resource, a versification or a schema, so neither shows what the engine is
for — and the second does not consume the first, which is the thing a two-step example exists to
demonstrate.

The replacement writes the kind of commentary already produced for small-group leaders, and which
a preacher needs alongside an outline. Step one fetches the passage with its analyses; step two
writes commentary that cites them.

**The audience is the Captain's, stated 2026-09-25:** small-group leaders preparing in advance,
and preachers.

## 2. Ruled

From 2026-09-25 unless noted:

1. **Two genres**, both illustrated by samples the Captain supplied:
   - **How This Passage Works** — prose. What the passage does, where it sits, what it sets up.
   - **Expect Your Group to Connect With** — a list. Each item pairs a concrete moment in the
     text with the human experience it opens onto.
2. **The commentary is scoped to the passage, which may be as little as a single verse.**
3. **Context belongs in the commentary** — the passage is not read in isolation.
4. **Greek, `SBLGNT`, `MRK 1:1-8` as the default passage** (ruled earlier; Hebrew discourse is
   private until it publishes and nothing shipped may reference it).
5. **No statistics.** Asking a model to count is the failure `sp/audits-pattern.md` records, where
   it wrote 98 while listing 114.
6. **The service and the step are called Parallel Passages** (2026-09-26). The name is the data's
   rather than "cross references": the database carries parallels and OT quotations and holds no
   allusions or thematic chains, so a reader told "cross references" would expect the Elijah echo
   at 1:6 and not find it.
7. **The commentary step requires Parallel Passages when present** (2026-09-26). There is no
   `optional:` key, so the step supplies the input on every run and `[]` is the engine saying it
   looked and found none — one prompt, and D2 stands. Rule `say-which-kind-of-nothing`.

## 3. The one rule the design turns on

**Training knowledge as the *interpreter* of supplied material is the job. Training knowledge as
the *source* of claims is the defect.** Rule `source-text-required`, and the Tier 1 grading in
`sp/audits-pattern.md`.

The Captain's own second sample already enforces this in its shape — every item is
`[moment in the text]: [experience it opens onto]`. The left side cannot be written without
naming something in the passage, and the right side is visibly downstream of it. A reader can
check the left half even where they cannot check the right.

Three consequences:

**Subject and context are different inputs.** "Scoped to the passage" and "context belongs in the
commentary" pull against each other, and separating the two resolves it. The verse under
commentary is the **subject**; surrounding verses are supplied as **context the commentary may
cite but is not about**. Mark 1:4's wilderness means something only because of the quotation in
1:2-3; scope the payload to one verse and that is gone.

**The number of items follows the text.** Not a fixed count. Mark 1:6 carries two or three honest
anchors, 1:5 carries one, and 1:1 carries none. Ask for four and a verse with none supplies four
inventions.

**An empty list is a legal answer and means something.** Per `say-which-kind-of-nothing`, `[]` is
"looked, found nothing" and `null` is "did not look". A title sentence yielding `[]` is correct
output, not a failed run.

## 4. What the anchor is, and why single-verse scope is the stronger case

At pericope scale the anchor is a narrative beat — *Peter warming himself by the fire* — and the
model has to perceive it.

At verse scale the anchor is a textual detail, and **the engine supplies it**: `include:
[discourse]` returns features at word ids, so a point of departure or a topic shift arrives
already identified. The left-hand column becomes checkable against the payload rather than
against the model's reading.

So the single-verse form is *more* grounded than the pericope form, not a thinner version of it.

## 5. The pipeline shape — five steps, four of which call no model

Ruled 2026-09-25: the example carries steps that are pure engine, alongside the fetch and the
commentary. Ruling 7 (2026-09-26) adds the parallels step, so four of the five cost nothing.

**Every step takes its passage from one variable, `${passage}`, and the example supplies no
default.** Ruled 2026-09-26: *"examples should not use defaults, that hides information the reader
needs."* A default would let the reader run the example without ever learning that the passage is
theirs to choose, which is the one thing this example exists to teach.

```yaml
description: |
  Requires --var passage=<reference>, e.g. --var passage="MRK 1:1-8".
variables:
  output_dir: "outputs"
```

```bash
sp run --pipeline pipelines/commentary.yaml --var passage="MRK 1:1-8"
```

**`passage` is not declared in `variables:` at all, and that is deliberate.** Ruled 2026-09-26:
the example teaches *explicit variable reference as an input to a step* and nothing else — every
step names `${passage}` where it needs it, and the reader learns the one rule that always applies.
The three other mechanisms the language supports are advanced and are not taught here: a `--var`
reaching a step without being declared, a self-referential declaration `passage: "${passage}"`,
and derived variables computed inside the `variables:` block.

A self-referential declaration was considered as a way to announce the input at the top of the
file and rejected: it is inert, and it would teach a device rather than the rule. `description:`
carries that information in words instead, which a first-time reader can act on without decoding
anything. The language cannot yet declare a required input; that is filed separately.

**Measured 2026-09-26, corrected the same day.** An earlier note here said *"nothing catches a
missing input — not lint, not `--dry-run`"*. That was wrong, and it was wrong because the probe
used the two fields lint does not scan. What lint actually does:

| where the undefined `${nope}` sits | `sp lint` |
|---|---|
| `saveas:` | **error** — *"Variable '${nope}' not available. Available: (none)"* |
| `inputs:` on a `function` step | **error**, same form |
| `content:` on a `save` step | passes, silently |
| `path:` on a `save` step | passes, silently |

`--var` values are counted as available, which is correct — `lint_pipeline_full(path, vars=…)`
takes them, and `tests/test_linter_variable_validation.py:585` pins it.

So lint does catch a missing input in the fields it scans, and `content:` and `path:` are not among
them although they are `type: save`'s own required fields. That is a field-coverage gap, not a
design tolerance, and it is filed separately. For this example it means: name the passage in every
step through fields lint checks, and do not rely on `content:` to catch a typo.

```yaml
- name: subject                 # the passage with its analyses
  type: scripture
  resource: SBLGNT
  passage: "${passage}"
  format: usj
  include: [ids, discourse]
  output: subject

- name: english                 # the same verses in English, resolved from the source scheme
  type: scripture
  resource: BSB
  passage: "${passage}"
  versification: org            # the reference is numbered as SBLGNT numbers it
  format: milestones
  output: english
  saveas: "${output_dir}/${passage_info.filename_prefix}-english.txt"

- name: reference               # what the engine computes about the reference itself
  type: function
  function: llmflow.utils.data.parse_bible_reference
  inputs:
    passage: "${passage}"
  output: [passage_info]
  saveas: "${output_dir}/${passage_info.filename_prefix}-reference.json"

- name: parallels               # what else in the canon this passage is parallel to
  type: parallel-passages
  resource: SBLGNT              # the text the result is expressed against
  passage: "${passage}"        # the passage parallels are sought for
  returns: [references]
  output: parallels
  saveas: "${output_dir}/${passage_info.filename_prefix}-parallels.json"

- name: commentary              # the only step that costs anything
  type: llm
  ...
```

**The parallels step takes the same `${passage}`, and that is a decision rather than a default.**
§3 separates subject from context: the commentary is *about* the subject and may *cite* context.
Parallels follow the subject — the question is "what is this passage parallel to", not "what is
anything nearby parallel to" — so wiring it to a wider context payload would return groups the
commentary is not entitled to talk about. Where the subject is narrowed with
`--var passage="MRK 1:6"`, the parallels narrow with it, and `MRK 1:6` correctly returns the single
group it shares with `MAT 3:4`.

**Why `versification: org` on the English step is the whole point of including it.** That key
states the scheme the *passage string* is written in — the request side — while the resource
declares its own source side (`sp/passage-references.md`). The Greek is numbered `org`; saying so
makes the engine map the reference before reading BSB, so the English lines up with the Greek
verses rather than merely looking as though it does. Left unstated it defaults to `eng`, and the
two agree in Mark and disagree elsewhere — WLC and BSB differ by two verses at `PSA 51:1`, and
the run reports success either way (#203).

So the step demonstrates the correct habit on a passage where getting it wrong is invisible,
which is the only safe place to teach it.

**The English is load-bearing, not a demonstration.** The audience does not read Greek, so the
commentary quotes from this step. That makes the example show the pattern that matters — analyses
from one resource, quotable text from another, joined on a reference — rather than a step added
to show a feature off.

**The reference object is free and shows what the engine already knows.**
`parse_bible_reference` returns `book_code`, `testament`, `original_language`,
`canonical_reference`, `filename_prefix`, `display_name` and the four versification fields
(`project/data-shapes.md`). Saving it teaches two things at once: the engine has already parsed
what a consumer would otherwise re-parse, and `filename_prefix` is what the other steps name their
output with — which the pipeline above then uses.

**Neither step calls a model.** A reader watching the run sees three of four steps complete before
anything is spent, which is worth more in a starter example than a paragraph claiming the engine
does the plumbing.

## 6. Sample output — drafted, and needs the Captain's review

Text is BSB, fetched 2026-09-25. **These are illustrations of shape, not approved content.**

### MRK 1:1 — the degenerate case, and the acceptance test

> This is the beginning of the gospel of Jesus Christ, the Son of God.

**How This Passage Works**

> This is a title, not a scene. Before anyone appears or speaks, Mark states what the book is and
> makes a claim about its subject. Nothing here is demonstrated — "Son of God" is asserted at the
> outset, and the rest of the book is what the claim costs. A group that expects a story will find
> a heading instead, and that is the point worth making: Mark tells you his conclusion first and
> then shows his working.

**Expect Your Group to Connect With**

> *(no items)*
>
> This verse offers no moment to enter. It is a claim, not an experience. Where the passage is
> this verse alone, the connecting work belongs to what follows.

**Why this is the acceptance test.** If the prompt manufactures four touch points for a title
sentence, the design has failed. If it returns an empty list and says why, it holds. The case is
free: 1:1 is inside the ruled default passage.

### MRK 1:2-3 — cited scripture, and where the line falls

> As it is written in Isaiah the prophet: "Behold, I will send My messenger ahead of You, who will
> prepare Your way." "A voice of one calling in the wilderness, 'Prepare the way for the Lord, make
> straight paths for Him.'"

**How This Passage Works**

> Mark opens not with Jesus but with a quotation, and hands the reader a frame before handing them
> a story. The language is all preparation and route — a messenger sent ahead, a way made ready,
> paths straightened. Whoever is coming is important enough that the road has to be worked on
> first. The wilderness named here is where the next verse puts John, so the text delivers what
> the quotation promises almost immediately.

**Expect Your Group to Connect With**

> - **"Prepare the way" — the road has to be made ready before the person arrives.** Most people
>   know the work that happens before someone important comes, and how that work is invisible
>   afterwards.
> - **"A voice of one calling in the wilderness."** Speaking where it seems no one is listening,
>   and not knowing whether it lands.

**Where the line falls, and this unit is why it is in the plan.** That the quotation is composite
— Malachi joined to Isaiah while attributed to Isaiah alone — is a real and useful fact, and it is
the kind of thing a leader is asked about. **It is not in the payload.** So either the pipeline
supplies it (a cross-reference input, or a resource that carries it) and the commentary may cite
it, or it is omitted. What the example must not do is state it from recall while every other claim
is grounded, because a reader cannot tell the two apart.

=>

*Corrected 2026-09-26.* **"It is not in the payload" is false of the Parallel Passages database.**
It carries the compositeness as two separate groups — `MAL 3:1 ↔ MAT 11:10 ↔ MRK 1:2 ↔ LUK 7:27`
and `ISA 40:3 ↔ MAT 3:3 ↔ MRK 1:3 ↔ LUK 3:4 ↔ JHN 1:23`. Malachi attaches to 1:2 and Isaiah to
1:3, under a citation Mark attributes to Isaiah alone, so the commentary can cite it grounded
rather than from recall. Read from `ParallelPassages.xml`, not recalled. D1 settles the question
this slot asks; the slot is left as it stands.

### MRK 1:4-6 — the case with real material

> John the Baptist appeared in the wilderness, preaching a baptism of repentance for the
> forgiveness of sins. People went out to him from all of Jerusalem and the countryside of Judea.
> Confessing their sins, they were baptized by him in the Jordan River. John was clothed in camel's
> hair, with a leather belt around his waist. His food was locusts and wild honey.

**How This Passage Works**

> The wilderness the quotation named now has someone standing in it. John's message is short and
> demanding, and the response is disproportionate to it — people leave Jerusalem and the
> surrounding country and go out to him. The direction matters: the movement is away from the city
> and its temple, out to a man in the desert. Then the text stops to describe what he wore and ate,
> which is not decoration; it is the detail that tells a reader what kind of figure this is before
> he says anything further.

**Expect Your Group to Connect With**

> - **People going out from the city to a man in the desert.** The pull of someone who seems to
>   have something real, strong enough to make people travel and leave the usual places behind.
> - **Confessing their sins, out loud, in a river, in front of others.** Saying something true
>   about yourself where others can hear it — and how much harder that is than thinking it.
> - **Camel's hair, a leather belt, locusts and wild honey.** Someone whose appearance marks them
>   as not belonging to ordinary life, and the mixture of suspicion and attraction that provokes.

**The same boundary appears here.** That the clothing echoes Elijah is not in the payload either.
Same treatment as above.

*Measured 2026-09-26: still true, and now for a stated reason.* `MRK 1:6` appears in exactly one
parallel-passage group, whose only other member is `MAT 3:4`, and `2KI 1:8` occurs **0 times** in
the whole database. The database carries quotations and parallels, never allusions — which is
ruling 6's reason for the name. So this unit stays as the case where the honest move is to omit
or to label, and acceptance test 4 is what holds it.

## 7. Acceptance tests

- [ ] `MRK 1:1` as the whole passage returns **no** connecting items, and says why
- [ ] `MRK 1:6` returns two or three, not a fixed count
- [ ] Every connecting item names something quotable from the subject verses
- [ ] No claim appears that is neither in the subject, in the supplied context, nor labelled as
      interpretation
- [ ] The commentary is about the subject even when context is supplied — widening the payload
      does not widen the subject
- [ ] `sp lint` is silent on both prompts: nine positions, four subsections per task section, and
      an ❌ counterexample in each task's `## Examples` (C3)
- [ ] The tutorial, the two example pipelines and the four `policy: example` template twins move
      in the same change
- [ ] The English step resolves through `versification: org` and its output lines up verse for
      verse with the Greek
- [ ] The reference object is saved, and the other steps name their output from its
      `filename_prefix` rather than rebuilding a name
- [ ] Three of the four steps complete before any model is called — verifiable with `--dry-run`

## 8. Open

**Answer inline after each `=>`.**

### D1. Does the pipeline supply cross-reference material, or is it out of scope?

§5 shows two places where the useful fact is outside the passage — the composite quotation, and
the Elijah echo. Supplying it makes the commentary better and the example larger. Omitting it
keeps the example small and every claim checkable.

parallel passages/ParallelPassages.xml (336 KB, CC BY-SA 4.0) — 2,193 passage groups over 5,266 verse rows. That is the whole of what UBS Open gives you for passage-to-passage linkage.

 It covers OT↔OT parallels, NT↔NT synoptics, and OT quotations in the NT, and it is word-level, not verse-level. Each <Verse> carries a digit string, one digit per word:

  <Passage>
    <Verse HEB="222222222222222222222222">GEN 2:24</Verse>
    <Verse GRK="00222222222211122222222">MAT 19:5</Verse>
    <Verse GRK="222222222222222222222220000000">MRK 10:7-8</Verse>
    <Verse GRK="0000010000020022222">1CO 6:16</Verse>
    <Verse GRK="1222222222222222222222">EPH 5:31</Verse>
  </Passage>

=>  Yes. We need to add cross references to the services sp provides.  Not as part of Scripture Text,  a separate call of its own.  Use the UBS Open dataset cross references. 

### D2. Two prompts or one?

The two genres could be one prompt with two task sections, or two steps. Two steps demonstrate
chaining twice and cost a second call; one prompt is cheaper and still satisfies the grammar.

=> We can already chain between sp native steps and LLM steps. That is sufficient.  No more complexity than is needed for the task, and it illustrates both chaining and LLM steps.

### D3. Does the example keep the `hello.gpt` / `hello.yaml` paths?

Carried from the earlier session and still unanswered. New names cost four catalog rows, four
template twins, `docs/tutorial.md` and `docs/ai-context/sp/command-line.md`.

=>  No, drop these, they are much less relevant to learning sp than the new examples.

### D4. Does the OT half of Parallel Passages ship?

The database itself and the Greek word-level mappings are CC BY-SA. The Hebrew word-level mapping
we hold — Macula Hebrew `xml:id` to MARBLE ids — declares itself non-public and not for
distribution, so the OT half cannot ship on the same terms as the NT half.

**What turns on this is only the word-level scores on the Hebrew side.** Verse-level linkage needs
no mapping at all and is unaffected, so an OT passage would still get its parallels and its
quotations; what it would lack is which Hebrew words matched. The starter example is Greek
(`MRK 1:1-8`), so nothing in §5 depends on the answer.

Three positions: ship NT word-level and OT verse-level only; hold the OT half entirely until the
mapping can be published; or pursue publication of the mapping first.

=>

## 9. What this does not change

- **The grammar.** The example conforms to `data/prompt-structure.yaml` rather than proposing a
  change to it — though it would be the first conforming prompt in either repository, and #244
  records that whether the four-subsection rule matches how prompts are actually written is not
  settled.
- **The resource.** `SBLGNT`, already ruled, already registered.
- **`sp lint`'s conformance check.** It ships with this example or waits for it; that ordering is
  in #244 and is not reopened here.
