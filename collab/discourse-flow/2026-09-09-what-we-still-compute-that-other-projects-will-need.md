# What we still compute in plugins that every project after us will have to compute

**From:** an AI session in `nida-institute/discourse-flow`, 2026-09-09.
**Status: drafted by the AI, pending the Captain's review.** He is handing it to you to
discuss which of these you want to implement; nothing here is a request for a change today.

The Captain asked: *what do we still use plugins to compute that other projects will need to
compute?* — with the engine now moving versification, morphology and resource location inside.
This is the inventory, read off the live pipeline (`pipelines/book-discourse-flow.yaml`), all 26
plugins, and your current `src/llmflow/utils/` so as not to propose moving what you already ship.

Three groups: what is already yours and is now duplication here; what is generic and has no home
in the engine yet; and what stays ours. Group 2 is the part worth your design attention.

---

## 1. Already yours — the plugin is duplication now

| Computation | Where it lives here | Where it already lives in the engine |
|---|---|---|
| **Verse-reference parsing, comparison, sorting** | **23 local implementations across 12 files** — `continuity_validation.py:6,14,174`, `windowing.py:31,37,42`, `derive_boundaries.py:17,104`, `milestone_content.py:356,362`, `discourse_export.py:24,32`, `leitwort.py:19`, `macula_greek.py:66,71,327`, `nested_pericopes.py:216,234`, `cohesion_links.py:29`, `source_language.py:95`, `utils/discourse_tree.py:163`; plus 9 ad-hoc `(\d+):(\d+)` regexes | `utils/versification.py` — `parse_passage_ref`, `as_single_verse`, `format_reference`, `references_in`, `Scheme.contains`; `utils/verse_ranges.py` — `Range`, `overlaps`, `contains`, `touches`, `verse_count`, `select` |
| **Verses-per-chapter, "next verse"** | `continuity_validation.py:38,163` derives chapter extents *from the loaded text* | `Scheme` knows the extents |
| **Defect log** | `plugins/defects.py` — module-global list, lock, `SEVERITIES = ("error", "warning")` | `llmflow/defects.py` — `DefectLog` with `record`, `extend`, `counts`, `summary`, `write()`, and a logging handler. Added `ce37401`, **today** |
| **Macula TSV load / slice / summarize** | `plugins/macula_greek.py`, 377 lines, hard-coded `/Users/jonathan/github/Clear/macula-greek` at `:25` | `type: scripture` with `include: [morphology, …]`, which the live pipeline already uses |
| **BSB translation loading** | `source_language.py:66-91` reads `bsb-vline-refs.txt` out of the internal-Alignments clone | BSB is a catalogued resource — `data/resources.json:946`, `kind: usfm`, versification `eng` |
| **"Where is dataset X?"** | `plugins/dataset_paths.py`, a plugin whose whole job is to wrap `llmflow.registry.Registry` | The registry itself |

Three notes on that table, because "duplication" is not the same claim in each row.

**The verse-reference row closes a thread of ours.** `2026-09-01-verse-reference-handling.md` asked
you §5.1: *do verse ordering and range membership belong in the engine?* `utils/verse_ranges.py`
landed `6615ded` on 2026-09-06 and answers yes. We have not migrated. The ten functions that note
listed are now twenty-three, which is what happens to an open question in a working repository.
The migration is ours to do and does not need anything from you — we record it here so the count
is on the table when you weigh group 2.

**`extract_chapter_verse_counts` has no caller.** The live coverage path
(`continuity_validation.validate_book_coverage:139-156`) reads the verse milestones out of the
running text and treats *that* as the authoritative verse list, which is why the scheme-derived
branch went dead without anyone noticing. Three different answers to "what verses does this book
have" — derived from text, derived from the old `book_text` shape, and your `Scheme` — is the shape
of the problem in miniature.

**Your `defects.py` is one day old, and ours is not.** Ours carries two things yours does not: a
severity vocabulary that a caller cannot get wrong (`record` raises on an unknown severity) and a
lock, because `subdivide_candidates` runs parallel and appends race. If you want those upstream,
they are small; if you would rather they stayed a project's business, say so and we will keep the
wrapper thin and stop calling it a defect log.

**One latent defect, in the BSB row.** `source_language.py:226` joins translation to Greek by
**string-matching the reference**. BSB is `eng`-numbered, SBLGNT is `org`, and you ship
`versification.map_reference` for exactly this join. In the NT the divergences are few — 3 John,
Romans 16, 2 Corinthians 13, Revelation 12 — but they are silent: a mismatched reference yields no
translation rather than an error. We have not measured whether any book we have run is affected.
That is a check to run here, not a claim, and not yours to fix.

---

## 2. Generic, with no home in the engine yet

Ranked by how many projects after us hit the same wall. What every item shares: it is computed
**from what `sp` hands us**, which is the tell that it belongs on the same side of the line as the
thing it reads.

### 2.1 Reading and slicing milestone USJ — the one we would start with

`plugins/milestone_content.py`, 371 lines: `inline_stream:26`, `wrap_stream_as_usj:52`,
`word_ids_in_stream:122`, `slice_usj_content:245`, `_select_span:287`.

You *produce* USJ (`scripture.rows_to_usj`) and you flatten it to text (`usj_to_text`). Between
those two there is nothing that walks or cuts it. `data.py`'s `_extract_chapter_usj:945` and
`_extract_verse_range_usj:1022` are private and container-shaped — they assume a verse contains its
words, which milestone USJ does not.

So a project that receives your USJ and needs *part* of it writes this itself. We have written it
six times: the module above, plus `derive_boundaries.words_in_order:23` and `words_by_verse:57`,
`boundary_evidence._walk_verses:107`, `source_language._strip_levinsohn_features:146`, and
`families._has_srcloc:24`. Five of those six exist only because there is no public walker.

The operations, in the order we needed them:

- flatten `usj.content` to the running text (yours is one `para` per chapter, so any
  element-count operation over `content` sees a two-item book)
- the word ids in a span, in document order
- cut a span by verse `sid` **or** by word id, and get conformant USJ back
- strip one annotation family from a document without disturbing the rest

`discourse-flow-hebrew` will need all four before it needs anything else we have.

### 2.2 Slicing the annotation families

`milestone_content.citations_in_span:138`, `citations_in_range:169`,
`word_annotations_in_range:215` — "the items of family F covering this span."

The families arrive from `type: scripture`. The slice is the second half of the same act, and it
carries an assumption we made up: that Macula word ids are fixed-width, therefore string order is
document order. That is true today and is not a fact a project should be asserting on its own.

### 2.3 Word-id identity and order

`plugins/identifiers.py` — `n\d{11,}`, `make_id`, `parse_id` — plus the same fixed-width assumption
in `cohesion_links._ordered_word_ids:24`. Your only word-id helpers are private
(`discourse._word_identifier:218`).

Generic: parse a word id, compare two, name the verse one falls in, express a span as a pair. Ours
to keep: the namespace vocabulary (`division|pericope|segment`), which is a discourse-flow
statement about what kinds of unit exist.

### 2.4 Coverage and partition validation

`plugins/continuity_validation.py` entire, plus `derive_boundaries.overlap_errors:281` and
`stated_closing_mismatches:316`.

The question is always the same: *does this set of ranges cover the text exactly once?* — gaps,
overlaps, a first unit that does not start at the beginning, a last that runs past the end, and the
window variant (does this slice tile its own range). You ship the range predicates; there is no
partition validator over them. Anything that carves a text into units needs one — a Hebrew
discourse run, an outliner, a translation planner.

### 2.5 Advancing a window by verse or word anchor

`windowing.content_index_of_sid:106`, `first_verse_sid_in_stream:89`,
`first_window_closing_context:69`.

You own `type: window` and its cursor. What we supply is the arithmetic that turns "the model
stopped at `MRK 3:6`" into an absolute index into the inline stream — and the code comment points
at `window.py:276-287` to explain why it must be absolute. That coupling is a sign the index
belongs on your side of it. The first-window case is the same thing at the other end: we
manufacture an opening context so window 1 has something to validate against.

### 2.6 Derived profiles over the families you deliver

`plugins/cohesion_analysis.py` — Louw-Nida subdomain distribution from `senses`, tense × mood ×
voice counts from `morphology`, syntactic subjects by lemma, inclusio from the first and last `cl`
in `syntax`. `cohesion_links.backward_links:44` — directed antecedent links from Macula's
`subjref` and `referent`. `leitwort.py` — lemma recurrence across units.

Every one is a pure derivation over an engine family, and the module docstring already records that
its predecessor was an XQuery re-deriving what you now deliver (`project/rulings.md`, "`sp` is the
data layer for anything `sp` provides"). The natural split: the **derivation** is yours, the
**tuning** stays ours — `EXCLUDED_DOMAINS`, `FUNCTION_CLASSES`, `INCLUSIO_NOISE` and the
two-pericope minimum are discourse judgment and we should keep having to defend them.

### 2.7 Prompt-convention pre-flight

`plugins/check_prompt_compliance.py` is step 1 of our pipeline. It parses the pipeline YAML to find
every `prompt.file`, then enforces the 8-section convention and a phantom-field registry, and
raises before any LLM call.

You have `utils/prompt_hygiene.py` (passage contamination, and `sp lint` gained the
`type: function` input check yesterday). The convention itself is machine-wide, in
`~/.sp/conventions/llmflow-prompt-organization.md` — it is not ours. A project should not be
carrying a checker for a convention it does not own, and no project should have to remember to add
step 1.

### 2.8 A split, not a move: `genre_markers.py`

The **matcher** is generic — `_find_word(words, **criteria)`, `_has_lemma`, and the marker shape
(`type`, `text`, `tier`, `corpus`, `source: precomputed`). The Hebrew sibling will want exactly
that shape with a different table. The **15 Greek genre rules** are ours and should stay ours.
Worth a look only after 2.1–2.4; we mention it because it is the clearest case of a rule table
wanting a declarative matcher rather than 200 lines of Python.

---

## 3. What stays ours

`nested_pericopes`, the boundary-derivation policy in `derive_boundaries`, `citation_grounding`'s
verdict rules, `division_provenance`, `synthesis_prep`, `pericope_packaging`, `unified_hierarchy`,
`discourse_export`, the id namespaces in `add_pericope_ids`, `scaffold_experiment`. These encode
discourse-analysis decisions. None of them should move, and if a future engine feature makes one of
them shorter we would rather it made the *inputs* better than absorb the judgment.

---

## 4. Where we would start, and the questions that are yours

**2.1 and 2.2 together**, if you take one thing. They are a single capability — *walk, slice and
re-emit the milestone USJ you hand me, annotation families included* — they retire 371 lines plus
five duplicate walkers here, and they are the first thing the Hebrew project will reach for. The
verse-reference cleanup in group 1 is larger by line count but it is mechanical work against an API
you already shipped, and it can follow.

Four questions where the design is yours and not ours:

1. **Is milestone-USJ traversal a public surface you want?** If yes, we delete
   `milestone_content.py` and five walkers. If no, we consolidate them into one module here and
   stop treating the gap as yours — the same disposition question as `2026-09-01` §5.1, and either
   answer is workable.
2. **Should slicing an annotation family come from the same place the family does?** Our vote is
   yes, mostly because the fixed-width-word-id assumption should be asserted once, by whoever owns
   the ids.
3. **Does the defect log want a severity vocabulary and a lock?** Yours is a day old and ours has
   both. Cheap to move, cheaper to decide before two of them diverge.
4. **Is partition coverage an engine concern?** It reduces to your range predicates plus a
   traversal, and every partitioning project needs the same four checks.

Nothing here blocks us. We can consolidate locally either way; we would rather do it once, in the
place you think it belongs.
