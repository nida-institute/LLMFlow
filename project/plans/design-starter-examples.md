# Design — the starter examples: a reader's guide, and the significance of parallel passages

**Status:** ruled (2026-10-02)

Ruled by the Captain the same day, directing the build: *"finish #244 first, then #252 and #261"*.
The work order is `project/plans/plan-starter-examples.md`. Nothing here is implemented yet.

---

## 1. What was asked

The Captain, 2026-10-02:

> let's scratch the commentary example entirely and replace it with two things: (1) a reader's
> guide, focused on less common Greek words, the force of infinitives, the force of participles,
> relationships among the verb, in plain language, at the level of Grosvenor and Zerwick or the
> Linguistic Key to the Greek New Testament, but using modern linguistics like what you see in the
> Cambridge Greek Grammar or the volumn Runge edited on the Greek verb

> and (2) a second LLM step that interprets the significance of the parallel passages, not in some
> humanistic way, but by referring to the original meaning in the original context and how it is
> adapted to the current context.

**What this replaces.** `pipelines/commentary.yaml`, `prompts/commentary.gpt`, their template
twins, their two `policy: example` rows in `data/file-catalog.yaml`, and the tutorial written for
them. `project/plans/plan-starter-example-commentary.md` is superseded in full, and #244's scope
changes with it. Under `one-design` the commentary goes in the same change that brings in the
replacement — nothing half-migrated.

**What stays from the commentary work.** The engine changes it drove are language features, not
example features, and they stay: named step outputs (#263), `passage_info` as the `scripture`
step's `reference` member, the `parallel-passages` step (#258), and the twelve-position prompt
structure. The new example uses them all.

**Who reads it.** The example ships to every project as the worked pattern for the language, and
its output is read by someone working through the Greek text. Two audiences, two standards: the
YAML has to teach the language cleanly; the output has to be something a reader of Zerwick would
recognise as the same kind of help, in plain language.

---

## 2. The shape I read from the request

One pipeline, two model steps, everything else free:

| # | step | type | what it supplies |
|---|---|---|---|
| 1 | `greek` | `scripture`, SBLGNT, `usj` | the passage, with the analyses the guide cites; `reference` → `passage_info` |
| 2 | `english` | `scripture`, BSB, `milestones` | the English the guide may quote |
| 3 | `rarity` | loads the committed frequency table — D1′ | how often each lemma occurs in the GNT |
| 4 | `reader_guide` | `llm` | **model step (1)** |
| 5 | `parallels` | `parallel-passages` | the groups this passage takes part in |
| 6 | `parallel_texts` | `for-each` over groups, then over references | the text **and its context** of every member — D4, D5 |
| 7 | `significance` | `llm` | **model step (2)** |

One pipeline, as specified (D3).

---

## 3. What the data can and cannot ground — measured 2026-10-02

The rule that decides most of this design is `source-text-required`: a model reasons only about
data put in front of it. Each thing the request asks for was checked against what a step type can
actually deliver.

| the guide must say | grounded by | state |
|---|---|---|
| which words are less common | a count per lemma, committed once | settled, see D1; location D1′ |
| the form of each infinitive and participle | `include: [morphology]` — `tense`, `voice`, `mood`, `case` | built |
| what an infinitive or participle attaches to | `include: [ids, syntax]` — the constituency tree, `role`, `clauseType`, `junction` | built |
| the force it carries | the model, reading the two rows above | interpretation, legitimately the model's |
| the sense of a less common word | `include: [senses, glosses]` — Louw-Nida `domain`/`ln`, the resource's glosses | built |

**A non-finite verb is read against its whole sentence.** The Captain, 2026-10-02: *"Important:
non-finite verbs MUST be interpreted in relation to the rest of the sentence to grok their
semantics properly."* So the guide's prompt states it as a rule, and the payload must contain the
whole sentence each infinitive and participle stands in — not only the verses requested.

**What the engine does today, read from `src/llmflow/utils/syntax.py:227-233`:** the `syntax`
family carries a sentence **whole** wherever the passage meets it at all, *"even where it runs past
both"* ends. But the words themselves — text, morphology, glosses — come from the resource's rows
for the requested verses only, so *"some tokens may name words outside the rows returned."* Where a
sentence runs past the passage, the model gets that sentence's tree but not all of its words. A
participle near a passage boundary is exactly the case the Captain's rule is about. D8.

**Rarity has no source.** `~/sp/resources/Clear-Bible/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv`
has 27 columns, read in full from its header: `xml:id ref role class type english mandarin gloss
text after lemma normalized strong morph person number gender case tense voice mood degree domain
ln frame subjref referent`. None is a frequency. The only frequency code in the engine is a
docstring example in `src/llmflow/utils/bible_data.py:328`, for Hebrew, not reachable from a
pipeline. A model told to pick "less common words" with no count in front of it picks them from
training — which is the Tier 1 field `sp/audits-pattern.md` names, *"a field that nothing in the
request could have produced"*.

**So the count is produced once from the Lowfat trees and committed** — see D1. The guide step
receives it as a named input. No engine change, and no BaseX on a user's machine.

**The cost of `syntax`.** About 9,500 characters for `MRK 1:1-8`
(`sp/scripture-representations.md`). It is the only source for what a participle attaches to, so
the guide's third and fourth subjects are guesses without it.

| the significance step must say | grounded by | state |
|---|---|---|
| which passages are parallel | `parallel-passages` → `references` | built; **dataset not on this machine** |
| the parallel passage's text | `scripture` on each member reference | built |
| its **original context** | `scripture` on a wider passage around each member | built; **how wide — D5** |
| how it is adapted here | the subject passage, already fetched in step 1 | built |

**References come back in `org`.** `DATABASE_SCHEME = "org"` at
`src/llmflow/utils/parallel_passages.py:24`, so every member fetch states `versification: org`.
Settled from the code; not a question.

**Nested `for-each` is supported** — `docs/sp-language.md:568`. A group is a list of references,
so iterating groups then members needs no new construct.

**No Septuagint is readable.** In the vendored `data/resources.json`, `rahlfs-hanhart` and
`swete-lxx` both have `"provides": null` — catalogued, not openable by any step. The Old Testament
text the engine can deliver is WLC Hebrew and BSB English. That matters here because an NT
quotation's wording often follows the Greek of the Septuagint rather than the Hebrew — D6.

**One technical question I will settle by measurement rather than ask.** A `scripture` step names
one `resource`, and a parallel group mixes testaments (`MAL 3:1` with `MRK 1:2`). Which resource a
member is fetched from therefore depends on its book. Candidates: an `if` per testament, or a
resource variable set per member. I will try both against the linter and report which the language
expresses cleanly; if neither does, that is a missing construct and gets its own issue
(`the-language-is-the-whole-surface`).

---

## 4. Decisions

Answer inline after each `=>`.

### D1. Where does "less common" come from? — settled in conversation, 2026-10-02

The Captain: *"one group by lemma query on the Macula Lowfat, using group by and order by, will
produce the table for the GNT."*

And then: *"no no no, we produce the dataset, once, and keep it in our repository."*

So the count is **data, produced once and committed**, not a step that runs on every pipeline run.
The `.xq` that produced it is committed beside it, with the command, so anyone can regenerate it
and check it (`declared-not-inferred`). No user needs BaseX. The engine-side `frequency` family
this document first recommended is withdrawn.

**Trial run, 2026-10-02**, from a scratch query, not yet committed:

    basex -b database=SBLGNT-lowfat lemma-frequency.xq

| measure | value |
|---|---|
| words (`//w`) | 137,741 — 137,741 distinct `id`s, 27 documents, 0 without `@lemma` |
| distinct lemmas | 5,518 |
| top of the table | ὁ 19,795 · καί 8,973 · αὐτός 5,059 · σύ 2,894 · δέ 2,766 · ἐν 2,737 |

**Cross-checked against the resource the pipeline reads.** `macula-greek-SBLGNT.tsv` has 137,742
lines by `grep -c ""` — a header plus 137,741 words, the same count. (`wc -l` says 137,741 because
the last line has no newline; that is not a missing word.)

One caveat on the source: this machine has three BaseX databases built from the same directory —
`SBLGNT-lowfat` (27 resources), `macula-sblgnt-lowfat` (28) and `sblgntlowfat` (1). The trial used
the first. The committed query should read the Lowfat files of the registered resource directly
rather than whichever database happens to exist, so the result does not depend on this machine.

**Hebrew, the same way** — the Captain, 2026-10-02: *"now do the same for Hebrew."* Trial run,
not yet committed:

    basex -b database=macula-hebrew-lowfat hebrew-lemma-frequency.xq

| measure | value |
|---|---|
| unit | **`m`, the morpheme** — Hebrew Lowfat has no `w` element; the first document's elements are `chapter sentence p milestone wg m` |
| morphemes | 475,911 — 475,911 distinct `xml:id`s, 930 documents, 0 without `@lemma` |
| language | `lang="H"` 468,362 · `lang="A"` 7,549 |
| distinct lemmas | 8,456 |
| top of the table | וְ 51,004 · הוּא 46,940 · הַ 30,462 · לְ 20,447 · בְּ 15,768 · אֵת 11,870 · מִן 7,728 · יהוה 6,521 |

**Cross-checked against the registered resource.** `~/.sp/registrations/WLC.yaml:8` points at
`~/github/Clear/macula-hebrew/WLC/tsv/macula-hebrew.tsv`, the same clone the BaseX database was
built from; it has 475,912 lines by `grep -c ""`, a header plus 475,911 rows.

**הוּא is 46,940 because the pronominal suffixes carry its lemma.** Broken down by `@pos`:
`suffix` 45,530 (`Sp1cs`, `Sp2ms`, …), `pronoun` 1,405 (`Pp3ms`), `particle` 5. The prefixed
conjunction, article and prepositions are separate morphemes with their own lemmas in the same way.
For finding *less common* words this changes little — those lemmas are frequent however they are
counted — but a table that says הוּא occurs 46,940 times is a claim a reader will misread. How to
count is D1″.

### D1″. What does the Hebrew table count?

Two questions about the data, which are the Captain's (`ask-about-the-data`):

1. **Morphemes, or not suffixes?** Count every `m`, so the table matches the resource row for row;
   or leave out `@pos="suffix"`, so הוּא counts the 1,405 free-standing pronouns.
2. **Hebrew and Aramaic together, or apart?** Group by lemma alone, or by `@lang` and lemma, so
   the 7,549 Aramaic morphemes are counted against their own vocabulary.

=>  Not suffixes.  Count them together, but clearly mark Aramaic, which will usually be less familiar.

### D1′. Where do the datasets live, and how does a project's pipeline reach them?

- **A** — in this repository at `data/`, shipped into every project by a catalog row, and read by a
  `load_json` step. Simplest; every project carries it, about 5,500 entries.
- **B** — as a registered resource, so a pipeline names it the way it names `SBLGNT`. Cleaner
  for a dataset that is about one text; needs a catalog entry and a reader.

Format is JSON either way, one entry per lemma with its count.

=>  A, in this repository.

### D2. What counts as "less common"? — answered in the D3 slot below

A threshold in GNT occurrences — for example 50 or fewer, or 10 or fewer. It decides how long the
guide is, and where it is applied: in the XQuery, so the model receives only the words below it,
or in the prompt, with the model given the whole table.

=>

### D3. One pipeline — withdrawn, 2026-10-02

Not a question: the request already said "a second LLM step". The Captain: *"D3 - one pipeline,
that's what I specified, please just withdraw the question."*

The answer below was written in this slot and answers **D2**, the threshold. It is kept here
verbatim rather than moved, since only the Captain writes after a `=>`.

=>  Make this parameterizable via an input variable so that the user can choose whatever level works for their reading level in a given language. I would use different thresholds for Greek, which I know quite well, than for Hebrew, which I know  much less well.

### D4. Which parallels does the significance step interpret?

The database holds two kinds: synoptic parallels (`MRK 1:6` with `MAT 3:4`) and Old Testament
passages quoted in the New (`MAL 3:1` with `MRK 1:2`). "The original meaning in the original
context" is plain for a quotation. For a synoptic parallel, which passage is the *original* is a
position on the synoptic problem, not something the data says.

- **A** — quotations only
- **B** — both, with synoptic parallels treated as one tradition adapted in each context, no
  passage named as the source
- **C** — both, as written

=>  B, assuming Markan priority as in Goodacre

### D5. How much of the original context is fetched?

`verses-are-milestones` rules out "N verses either side": it divides content by verse count. What
the language can fetch by declaration:

- **A** — the whole chapter containing each member
- **B** — only the member reference itself, no wider context. Cheapest; the model then supplies
  the context from training, which is the failure this step exists to avoid
- **C** — a pericope boundary from a declared source. None is registered today

=>  Ultimately, C.  But if there is no pericope boundary yet, we'll settle for A and instruct the LLM to isolate the relevant pericope.  If there is a registered pericope (which will start happening soon), then use it.

### D6. The Old Testament text, given that no Septuagint is readable — deferred, 2026-10-02

The Captain: *"Don't worry about LXX yet."* The example uses what is readable — WLC Hebrew and
BSB English — and the Septuagint is not part of this design.

### D7. The passages the acceptance tests run against

The tests must include at least one passage with an Old Testament quotation and one with a dense
participle chain. `MRK 1:1-8` has the first (`MAL 3:1`, `ISA 40:3` in 1:2-3).

=>  For now, use Matthew 19:1-11

### D8. How does the guide get every word of a sentence that crosses the passage boundary? → #267

- **A** — the `scripture` step widens its rows to the sentences the passage meets, whenever
  `syntax` is included, so tree and words always cover the same text. **Engine change**, with its
  own issue and tests; changes the payload of every pipeline that includes `syntax`
- **B** — the same, as an explicit option on the step (a key saying "whole sentences"), so no
  existing pipeline changes. **Engine change**, plus one key in the language
- **C** — no engine change: the example chooses passages that begin and end on sentence
  boundaries, and the prompt is told some sentences may be incomplete. Leaves the rule unenforced
  for every other passage

=>  A

---

## 5. What this needs from the Captain beyond the decisions

- **The UBS Parallel Passages dataset on this machine.** `parallels` is `null` here, so a run
  without it tests the significance step with nothing to interpret. Downloading writes `~/.sp`.
- **The `sp run`** that proves the example end to end. It calls two models.
- **Approval of every ❌ and ✅ example in both prompts** before they ship. An example teaches on
  every run (`sp/audits-pattern.md`).

---

## 6. What changes, once ruled

Listed so the removal is one pass. Not a plan yet — the decisions above change it.

| what | change |
|---|---|
| `pipelines/commentary.yaml`, `prompts/commentary.gpt` | deleted |
| `src/llmflow/templates/project/pipelines/commentary.yaml`, `.../prompts/commentary.gpt` | deleted; new twins added |
| `data/file-catalog.yaml` | two `example` rows replaced |
| `src/llmflow/cli.py`, `src/llmflow/cli_utils.py` | `COMMENTARY_*` constants and `_EXAMPLE_PATHS` |
| `tests/test_init.py`, `tests/test_linter.py` | point at the new files |
| `docs/tutorial.md`, the quickref and `command-line.md` templates | rewritten for the new example |
| `data/ai-rules.yaml` rule `cite-paths` | uses the commentary files as its example citation |
| `docs/ai-context/sp/index.md` | regenerated from the catalog |
| `project/plans/plan-starter-example-commentary.md` | superseded; deletion is the Captain's |
| #244 | scope restated; the body is the Captain's to approve |

Added: the frequency table and the `.xq` that produced it, placed per D1′.
