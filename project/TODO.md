# Project TODO

> **Convention:** Active work lives here. Bugs and permanent decisions go to
> [GitHub Issues](https://github.com/nida-institute/LLMFlow/issues).
> Link issues with `→ #N` so this file doesn't duplicate GitHub.
> Board: https://github.com/orgs/nida-institute/projects/13

## 🔥 Active

### 🤝 Helm adopts sp's idioms, then installs into paratext-copilot

> **The Captain's second priority, 2026-09-19.** *"finish the new helm and install in paratext
> copilot."* Nothing is built. The design is `human-at-the-helm/project/plans/design-helm-project-layout.md`
> (R1–R12 ruled, steps 2–5 built) — but several of its §7 steps were **overtaken** by the rulings
> below, and step 6 as written is now withdrawn. Read these before that document.

**Ruled 2026-09-19, all the Captain's:**

1. **Helm uses the same idioms as sp** — *"or we have two different implementations of the same
   thing and we have to maintain each."* Three of them: `templates/<root>/` mirrors the
   destination, so the path *is* the mapping (guarded in sp by
   `test_project_templates_mirror_their_destination`); the declaration carries only what the tree
   cannot say; ownership is a property of the half — `helm/` ours, `project/` theirs, which is R1.
2. **The manifest's mapping rows go.** *"just copy the subdirectory and the files it contains."*
   Its `groups:` already read the tree; its four `files:` rows are hand-kept and are the second
   source. Once `templates/` mirrors the destination there may be nothing left to declare, since
   Helm has no index to render and no `.gitignore` to generate — that is the same idiom producing
   less declaration, not a divergence.
3. **No migration record, no moves ledger, no stamp.** *"we are the source of these skills, we can
   track them using source code control here."* D7.1's "permanent and accumulating" answered a
   question the AI had posed; it is not a request for the thing it presupposed. Install and update
   are one act: re-copy and read the diff.
4. **Helm keeps its own installer.** `/install` stays a markdown skill any assistant can follow.
   Shared idioms, not shared code — a methodology that needs a Bible-pipeline package installed is
   not tool-neutral, and that is Helm's premise.
5. **Helm gets `CHANGELOG.md` and `docs/`, and so does every Helm project.** It has neither today,
   which is why its own rulings have had nowhere to live. `templates/project/CHANGELOG.md`,
   create-only.

- [ ] **Open:** D9 — the shape of Helm's own AI context, an empty `=>` in that design document.
      Read as **B** (`docs/ai-context/project/` only, the shipped half being the source tree) and
      **not confirmed**. It blocks §7 steps 11–12
- [ ] Lay `templates/` out as a mirror of the destination, and delete what that makes redundant
- [ ] Then install into `nida-institute/paratext-copilot`. **Its tree is not clean** — it carries
      an uncommitted pre-2026-09-17 Helm install (`health-check/`, `helm-check/`,
      `docs/ai-context/helm-manifest.yaml`, `project/` all untracked; `handoff/SKILL.md` modified
      +14/−6) and is in the old flat `docs/ai-context/` layout. Installing over it without the
      Captain reviewing that diff first would sweep someone's unreviewed work into the result
- [ ] `sp doctor` labels the disciplines group **"Conventions"**, the directory's old name. That is
      almost certainly where discourse-flow's stale `~/.sp/conventions/…` pointer came from

### 🚨 HIGH — there is no type checking, and the suite does not say so

> **Flagged 2026-09-16.** `tests/test_types.py` fails, and it is easy to read as one more known
> red line among four. It is not. Its output is:
>
> ```
> PYRIGHT TYPE ERRORS:
> ================================================================================
> (nothing)
> ```
>
> **Pyright is not starting.** `npx` itself is broken — `MODULE_NOT_FOUND` in `npx-cli.js`,
> most likely a casualty of deleting `gui/frontend/node_modules` for disk space. So the test
> fails on a non-zero exit code with an empty error list: it is not reporting that the code is
> clean, and it is not reporting that the code is dirty. **It is reporting nothing, and the
> whole type check is absent.**
>
> This is the failure shape `check-the-source-not-the-rendering` exists to name — a guard
> reduced to nothing while still appearing present in a triage. It was catching a real defect
> the day before: `_owner_of_each_target_token` annotated `-> Dict` while returning a tuple.
>
> **Until `npx` works, nobody should read a passing suite as type-checked**, and no change to
> `src/` has been type-checked since it broke.
- [ ] Fix `npx` — reinstall via volta, or restore/regenerate `gui/frontend/node_modules`
- [ ] **Then re-run `hatch run pytest tests/test_types.py`** and see what accumulated while the
      check was off
- [ ] **Ruling wanted:** should this test *fail loudly as a broken check* rather than as an
      ordinary type error? A guard that cannot run and a guard that found a problem currently
      look identical in the summary line, which is what let this sit

> **Related, and not the same thing:** `gui/frontend/node_modules` is **tracked in git** — 7,997
> files, 1,787,308 lines — so deleting it from disk frees the working copy but not the
> repository, and `git status` reports 7,997 deletions until it is restored or deliberately
> untracked. Any `git add -A` would commit that deletion. Untracking it with a `.gitignore`
> entry is the change that actually saves the space; it is a decision, not a side effect.

### 🎯 THE GOAL — give discourse-flow what they need to implement segment-level text

> Set by the Captain 2026-09-10, superseding the representation goal below. **Everything else in
> this list comes after this.**
>
> They have answered our collab and their side is specified and ready:
> `collab/discourse-flow/2026-09-10-a-pericope-does-not-need-the-text-if-its-segments-have-it.md`.
> Their closing line — *"your engine change lands first"* — is the whole of what blocks them.

**What they need from us, in the order it unblocks them:**

- [x] **E3 — `usj_to_text` keeps the chapter and the punctuation.** Chapter falls back to the
      verse `sid`; a bare string keeps its own spacing. Both paths now return the same 665
      characters for Philemon 1:1–7 — `tests/test_scripture_usj.py`, 35 passing
- [x] **E1 — `include:` valid with every format.** `{text, scripture_pipelines}` when `include:`
      is non-empty, bare string when it is not; container built once and shared with the USJ
      path — `tests/test_scripture_include.py`, 30 passing
- [x] **The word addressing as ruled** — a map keyed by word id, `null` for a slot the text does
      not render, a list for a word written in several morphemes. Keyed rather than positional
      on the Psalm 23:1 evidence
- [x] **E2 — `spans:` cuts a passage into units named by word id**, one result per span, read
      once — `tests/test_scripture_spans.py` plus an end-to-end step test through `load_pipeline`
- [ ] **Tell them it has landed** — the reply promised "we will tell you when the first of those
      lands", and all three have
- [x] **`save_json`'s `indent=2` is ruled and stays** — see the section below

**Their three answers, all the Captain's, so they are rulings and not opinions:**

1. **Segment-level text is right, in our exact shape** — `text` and `translation` as plain
   strings per segment, and the pericope-level `source_text` goes.
2. **Do not ask who reads the USJ.** His decree: *"downstream consumers are a black box to us. I
   decree that we do not need the text at pericope level if we have it at segment level."* Do
   not design around a consumer census, and do not wait for one.
3. **The Hebrew cases.** A morpheme with no surface form is `null` **in the morpheme slot** —
   `[null, "בָּ…"]` — not an empty string and not omitted, so `null` reads the same at both
   levels and index alignment survives, which is what keeps the ids derivable. **Compounds must
   be identifiable and the representation is ours to choose**, under one constraint: the index
   stays the address, so בֵּית and לֶחֶם may not collapse into one slot. Detection is `unicode`,
   not `lemma` — our own measurement, 53 of 53 against 11 of 53.

**Two corrections they made to our note, both accepted:**

- **The indentation is ours.** `utils/io.py:409` — `json.dump(..., indent=2)`, hardcoded in
  `save_json`, so every `saveas` JSON artifact in every pipeline is indented. Their tree has no
  `json.dump` at all; verified. Our note told them to fix it with `separators=(",",":")`, a fix
  that does not exist on their side. **`genre_markers` in that same row genuinely is theirs** and
  that half stands.
- **Calling prompt payload a "focus question rather than a cost one" was wrong.** A prompt
  payload is tokens, and the object reaches a prompt once per pericope per book. It is both, and
  the analysis-quality half is the expensive one because a degraded run is re-run and re-reviewed
  on the Captain's time. Accepted; the design document's §4 framing needs the same correction.

### 🎯 Alignment — **the only known blocker for discourse-flow**

> Captain, 2026-09-13: *"alignment is the only known blocker for discourse flow at this point."*
> E1, E2 and E3 all landed, so the segment-text goal above is done except for telling them.
> This is what replaces it.
>
> Design: **`project/plans/design-scripture-alignments.md`**, status `proposed`. Read it rather
> than re-deriving — it carries the rulings and the measurements with the commands to re-run them.

**Ruled 2026-09-13 and 2026-09-14, all the Captain's:**

1. **R1** — a span returns its aligned tokens **plus** the unaligned tokens between them. A target
   token aligning to *nothing* is included; one aligning to a *different* source word is not.
2. **R2** — the engine reads **our own** declaration of supported pairs, not
   `Clear/Alignments/data/catalog.tsv`. Validated at read time against each alignment file's own
   `documents` block.
3. **R3** — the corrected catalog omits the bogus Hausa OT pair only; `SBLGNT-OHCB` is genuine.
4. **R4** — *"alignments are directional. both `from` and `to` must be specified."*
5. **R5** — of the two readings of reordering, **target order is correct**: the aligned tokens are
   put back into the translation's own reading order, so the English reads as English.
   **Extended 2026-09-14:** *"I would like an option for source order vs. target order, default =
   target order."* Both orderings ship; target is the default. R5 governs **sequence** only —
   membership is R8's, settled by target order in both modes. Source order does not read as
   English and is not meant to; it is for comparing the two texts side by side. **Who each serves:**
   *"most people will prefer target order, period. the few people who know Greek or Hebrew want
   both orders."* So target order is the default because nearly every reader wants it. **The
   request takes a set, not a choice** — *"you should be able to ask for one or the other or
   both."* Three legal requests: target alone, source alone, both; default target alone. Where
   both are asked for they cover the **same token set** — R8 fixes membership, so the two differ
   in order only. Open sub-question: which source position places a token that aligns to several
   source words.

6. **R6** — **the alignment is filed per verse; our units are not.** Captain, 2026-09-14,
   correcting an earlier heading that called the verse "the unit of work": *"The alignment format
   does one record per verse, but we do our work in linguistic units - clauses, phrases,
   sentences. So we have to read past the verse scope."* The verse is a lookup key, never a unit
   of analysis — `verses-are-milestones`. Gather every verse a span draws from and assemble
   across them; never treating the whole span as one stretch of the target.
7. **R7** — a Psalm title is offered as a **target-side convention, never as a correspondence**.
   Where a span covers the source verse holding the superscription and the target happens to carry
   a verse `000`, it is offered as a separately labelled field, positional and saying so. Verse 000
   is **not** a general mechanism: BSB carries it for 116 of 150 psalms, YLT for 11, the Hebrew
   source never, and no verse-000 token is aligned anywhere.
8. **R8** — a shared target word: **no token appears in two spans' text, but the constituent list
   shows it in both.** Captain,
   first *"both spans get it"*, then refining: *"the target word order tells us what span to put it
   in — or at least, the end user cannot see which span we drew it from"* and *"but a constituent
   list should show it both places."* So the **span text** gives the word to whichever span's target
   stretch contains it and to that one only — adjacent spans concatenate exactly, with no repeat —
   while the **constituent list** and the opt-in correspondence map show it in **both**, because
   that is what the alignment says.
9. **R9** — the correspondence map is **opt-in**. Captain: *"by default, no, but provide an option
   that does for debugging and transparency."*

**Measured, against `SBLGNT-BSB` (115,008 records) and `SBLGNT-YLT`:**

- alignment is **not monotonic** — 17% of adjacent source-order steps run backward in target order
- **81%** of spans have source order disagreeing with target order; **35%** have two or more source
  words sharing an identical target set. Word correspondence is a many-to-many graph and cannot be
  recovered by position
- **the alignment is filed per verse — that is the data's shape, not our unit of analysis.** Only
  **80 of 115,008** records (0.070%) have source and target outside one verse, so the verse is a
  reliable lookup key. A span is a clause, phrase or sentence and crosses verses whenever the
  language does, so the operation **reads past verse scope**. Where a span happens to cover whole
  verses its tokens are contiguous (**7,933 / 7,934**); a token belonging to a different source
  unit can fall inside what a span covers only where a span opens or closes
  *inside* a verse — which discourse-flow measured at 4 of 390 units in Mark, **1%**, and which is
  the whole reason the step was asked for
- **An earlier "49% of spans are interleaved" figure is withdrawn.** It came from arbitrary
  word tiling, which nobody does; it was a property of the test harness, not of the data
- word order is **locally coherent**: consecutive source words move `+1` in target position 34% of
  the time and `+1/+2/+3` 62%, while large backward jumps (≤ −6) are 2.1%. A verse breaks into a
  median of **3 ascending runs** — consistent with the Captain's model of phrase-coherent blocks
  whose internal order is largely kept and whose relative order sometimes is not. **Not yet checked
  against syntax**; Macula Lowfat would settle whether a run is a phrase
- **A BSB-versus-YLT comparison was run and is void** — do not repeat it or cite its numbers. It
  was framed on the AI's assumption that YLT is the more literal translation; the Captain corrected
  that on 2026-09-13, and the comparison is confounded regardless: YLT's alignment has **0.6%**
  multi-source records against BSB's **4.9%**, and 21% unaligned tokens against 15%. It measures
  how the two alignment files were built, not the translations
- target ids join the target TSV **100% directly**; no identifier reshaping needed

10. **R10** — a span **reaches outward over unaligned tokens and stops at a neighbour**. Within
    each verse the bounds move out from the first and last aligned token over runs of unaligned
    tokens, halting where a token belonging to a different source unit begins. Reaching outward is
    what keeps verse-final punctuation and verse-initial words — without it the text reads
    `wordTherefore` and Ephesians 1:11 loses its opening *"In Him"*. Of the 29,964 tokens that
    align to nothing, **98% are punctuation and 2% are words**; the 2% are the ones whose absence
    breaks a sentence.
11. **R11** — **two kinds of nothing, told apart**, per `say-which-kind-of-nothing`: an empty
    collection (asked, nothing aligned) and `null` (the source ids are not in the alignment file).
    A third "kind" the AI had listed was R7's Psalm title — a *populated* field, not a nothing —
    and was removed 2026-09-14 when the Captain checked R11 against the rule. Where the title is
    absent it is **`null` and present**, never omitted, because no request list governs it;
    `alignments` and `correspondence` may be omitted precisely because `returns:` is a request
    list, which is the rule's stated exemption.

12. **R12** — a span carries **one boolean** saying whether its tokens are contiguous in every
    verse it draws from. True for ~99% of units; false exactly at the boundaries this step exists
    to serve. A list of the offending tokens was considered and not taken.
13. **R13** — **all twenty pairs ship**, across ten languages. Reframed around cost: R2 already
    validates each pair against the file's declared `documents` at read time, which is what catches
    a file misdescribing itself, so a pair costs one row and a bad file fails loudly. **Flagged, not
    resolved:** `por/JFA11` is `-transfer`, not `-manual` — machine-transferred rather than hand
    aligned, and whether the declaration records provenance is undecided.

**Tracked as → #238. Built and committed 2026-09-14** — `1501da1` (step, reader, 21 tests,
declaration, bundling, docs), `4b3640e` (the design documents). Design status `ruled (2026-09-14)`,
R1–R16, D1–D8 answered. **Not pushed.**

> ⚠️ **"Built" does not cover every ruling above it. Two are ruled and not built**, and this
> entry read as though they were:
> - **R7 — Psalm titles.** No field, no code, no test. Measured 2026-09-16 against Hebrew→BSB:
>   1,303 target tokens sit at verse `000` across 116 of the 150 psalms and **not one is aligned
>   to anything**, while the Hebrew source has no verse-`000` ids at all. So a span over Psalm 23
>   returns the psalm and **silently drops "A Psalm of David"**. Undecided before it can be
>   built: what the field is called, and whether `returns:` gains a member for it.
> - **R9 — the opt-in correspondence map.** `correspondence` appears nowhere in `src/` or
>   `tests/`; the schema's `returns` enum is `["text", "alignments"]`. This one fails loudly —
>   `returns: [correspondence]` is refused at lint — so it is the less dangerous of the two.

**Verify:** `hatch run pytest tests/test_alignment.py -q` → 22 passed.

**Worked examples**: `tmp/alignment-worked-examples.md` — Luke 1:1–4, Ephesians 1:3–14,
Psalm 23:1–4 and Ruth 1:1–4, Greek and Hebrew, regenerable with
`hatch run python tmp/gen_alignment_demo.py`. In all four, the tokens are contiguous in every verse.

**What is left before discourse-flow can use it — all but one done 2026-09-16:**
- [x] **Ruling citations stripped from the alignment docstrings** — `rule
      docstrings-say-what-not-why`. `utils/alignment.py` and `steps/alignment.py`, docstrings and
      comments only; the module-level pointers to the design document stay, which the rule asks
      for. **The guard does not catch this** — it forbids a date, a commit hash and the word
      "Captain", not `(R15)` — so it was judgment, and nothing goes red if it regresses
- [x] **`data/alignment-pairs.json` is wired** — `steps/alignment.py` `resolve_pair()` reads the
      declaration and resolves each row under the `clear-alignments` dataset. The per-machine
      `kind: alignment` route is gone rather than kept beside it.
      `tests/test_alignment_declaration.py`, 10 tests
- [x] **Run against the real corpus** — `scripts/check_alignment_pairs.py`, an audit script
      rather than a test because a fresh clone has no corpus. **18 pairs, 0 unusable**;
      `SBLGNT→BSB` joins **100% on both sides** across 115,008 records
- [x] **D9's Portuguese half is fixed** — `JFA11` source ids now carry the `n` prefix, 99,258 of
      99,258 join. Fixed in `Clear/Alignments`, **committed on `fix/portuguese-source-id-prefix`
      and not merged upstream**, so it holds on this machine only
- [x] **discourse-flow told** — `collab/sp/2026-09-14-alignment-has-landed.md` in their tree, and
      `2026-09-16-document-order-is-in.md` answering their reply
- [ ] The unbuilt `union`/`intersect` in `verse_ranges` bear on this; see Pipeline data operations

**Three pairs are declared out, each measured, not guessed** — `scripts/check_alignment_pairs.py`
re-derives all of it. `hau WLCM-OHCB` is byte-identical to its SBLGNT sibling and declares that
sibling's pair (Clear#12); `eng BGNT-BSB` has 12-character target ids where `nt_BSB.tsv` has 11,
so 0 of 172,736 join, and dropping the trailing character still leaves 240 ids naming rows that
do not exist; `fra WLCM-LSG` names `ot_LSG.tsv`, which is 66 bytes — a header row and no data.
**Two further defects were found and fixed** in `Clear/Alignments` and are likewise unmerged:
`hin WLCM-IRVHin` declared no `roles`, and `spa WLCM-RV09` declared its source as lowercase
`wlcm`; both made our own `validate_pair` refuse a real pair. Five issue drafts and two pull
request bodies sit unfiled in `tmp/`.

### 🅿️ Parked 2026-09-14 — three issues raised to defer, not to work

> Raised while designing #238's step syntax, then deliberately set aside. **None blocks #238**,
> which ships on flags. Design: `project/plans/design-operations-in-the-pipeline-language.md`.
- [ ] **#241 — how the language expresses one domain with many operations.** Ruled: one design;
      alignment on flags; XPath/XQuery generally the right direction. Open: whether standalone pure
      operations (verse algebra, list transformation, filtering) are **expressions** or **step
      methods** — §7 of the design doc has both written out with syntax
- [ ] **#240 — normalise names to hyphens**, with a carve-out: a key forwarded to a provider keeps
      the provider's spelling. Ruled but **not scheduled** — *"not worth the churn right now"*
- [ ] **#239 — the `${...}` resolver is regex substitution, not a parser.** A kludge, off the
      critical path. #241 governs it: modest fix under step methods, precondition under expressions
- [ ] **#125 is open although the feature is built** — `group_by`/`order_by` ship at
      `steps/for_each.py:283` with `tests/test_group_by.py`. Close or re-scope it

### 🐞 Three defects filed against `Clear-Bible/Alignments`, 2026-09-13

> Found while surveying the alignment data. All three are Clear's to fix, not ours; they are
> recorded here because R2 and R3 exist because of them.
- [ ] **#12** — `hau/alignments/OHCB/WLCM-OHCB-manual.json` is byte-identical to its SBLGNT
      sibling while its filename and TOML claim Hebrew/OT. 1 of 21 alignment files; the only
      duplicate. **Never resolve a pair by filename** — this is why R4 validates against `documents`
- [ ] **#13** — `data/catalog.tsv` is an orphaned Git LFS pointer with no `.gitattributes`
      anywhere. The only LFS-tracked file in the repo; a fresh clone gets three lines of pointer
- [ ] **#14** — that catalog's contents do not describe the tree: 19 listed, 21 present, **one**
      name in common
- [ ] Fixing the catalog on the local `dev` branch in `Clear/Alignments` is a contribution to
      offer upstream, **not** something the engine reads — R2 settles that. That branch has no
      upstream today

### 📄 `docs/llmflow-language.md` contradicts shipped behaviour

> Reported by discourse-flow in their 2026-09-11 note, §7, and confirmed. `3ca7139` made
> `include:` valid with every format and our own tests assert it, but the document still says
> otherwise in two places — and it is the sentence that would stop a reader adopting the feature.
- [ ] Line **802** — `include: [ids]  # optional; valid only with format: usj`
- [ ] Line **961** — *"It is valid **only** with `format: usj`"*

### ✅ `save_json` indents every artifact — ruled, and deliberately unchanged

> Found 2026-09-10 by discourse-flow, correcting our own note: `utils/io.py:409`,
> `json.dump(content, f, ensure_ascii=False, indent=2)`, which is 47.7% of
> `57-PHM-discourse.json` and cannot be declined by a pipeline.
- [x] **Ruled by the Captain, 2026-09-10, and the item closes.** *"we normalize spaces by pretty
      printing … the number of spaces doesn't matter, 2, is fine, what matters is validity.
      adding complexity to the interface is the wrong move."* No `indent` knob, no
      output-versus-intermediate rule. It is consistent with the standing ordering — readability
      outranks size — and the bytes are the third-ranked consideration, not the first.
- [x] Told to discourse-flow in the reply, so they do not plan around a compact-output option

### 📐 The representation design — ruled, feeding the goal above

> Set by the Captain 2026-09-10 and now serving the goal above rather than standing alone.

`include:` is refused unless `format: usj`, so a pipeline that needs annotation cannot have
milestone-cost text. Measured downstream on Philemon 1:1–7: **622 characters of Greek delivered
as 14,045 of JSON, 22.6×**; across the book 334 words carry an anchor and **228 are referenced
by nothing**.

The design is drafted and unreviewed: **`project/plans/design-annotation-without-anchors.md`**,
status `proposed`. It was raised by
`collab/discourse-flow/2026-09-09-include-forces-the-most-expensive-text-form.md`.

- [x] **Measured** — `project/plans/design-representation-workbench.md`, 72 cells, regenerate
      with `hatch run python tmp/representation-grid/generate.py`
- [x] **Inventory collab read** and folded into the design
- [x] **Ruled 2026-09-10, Q1–Q10** in `project/plans/design-pericope-segments-and-text.md` §10:
      segments hold text; `include` works with any format; word array replaces anchors, `null`
      for gaps, two-level arrays for morphemes; engine supplies text-by-span; `usx`/`usfm` added;
      `lexical` family provisional
- [x] **Q6 and Q9 answered by discourse-flow's reply**, both by the Captain: the elided article
      is `null` in the morpheme slot; compounds must be identifiable, detected by `unicode`, with
      the representation ours so long as the index stays the address
- [ ] **Four carve-outs awaiting a yes or no**, each an empty `=>` in §10: E3 shipping ahead of
      the E1–E4 bundle, the collab sharing mechanics, striking `print` *(done)*, Q9
- [ ] **Build E1–E6.** Nothing is implemented. E3 (`usj_to_text` loses the chapter, detaches
      punctuation) should go first — another team's live fix depends on it
- [ ] **Shipped documentation drafted, not installed** —
      `project/plans/plan-scripture-documentation.md`. Ships **with** the code, never before

**The one fact worth carrying:** a per-word payload is keyed by an opaque word id and carries
only the annotation — no surface form, no reference. That is the *whole* reason anchors are
load-bearing, and it was established by fetching `WLC Ruth 1:1`, not by reading comments.

### 🤝 The working-document lifetime belongs in Human at the Helm too

> **Sequenced deliberately, 2026-09-10: the sp-local half is done, this half is not.**
> `plans-are-temporary` now names collab notes, states that age is measured from the later of
> the declared date and the last commit (never mtime), and rules that a collab is written once
> into the recipient's tree. The Captain: *"this is valuable, and belongs in helm as well."*
>
> The general principle is engine-neutral and Helm needs it: documents that accumulate have a
> death; commit them so deleting is safe; move the ruling to the CHANGELOG first, because that
> entry is the index into the graveyard; recover with
> `git log --diff-filter=D` then `git show <commit>^:<path>` — verified against a real deletion.
>
> **The draft text is written** — see the conversation of 2026-09-10, or re-derive it from the
> rule. `disciplines/project-tracking.md` is the natural home: it already carries the *rolling*
> half (*"Git history is the audit trail. Do not accumulate dated copies"*) and lacks the half
> about documents that accumulate anyway. It is a **shared** file, so this costs a
> `helm-sync.yaml` hash refresh and a twin commit.
- [ ] **Decide the home first:** extend `disciplines/project-tracking.md`, or a new shared
      discipline
- [ ] **Then decide whether `data/ai-rules.yaml` keeps the full text or points at the
      discipline.** Two statements of one idea is the drift this repository has been burned by
      twice; the `github-workflow.md` precedent is *"Not restated here"*
- [ ] Parity handling: `hatch run python tools/sync_helm.py --apply`, and the shared copy must
      carry no engine vocabulary — the guard refuses it

### 🚢 0.2.1.28 — merged? tagged? released?

> **Title, chosen by the Captain 2026-09-21: "the order is declared once, and lint reads it."**
> So the PR reads `Release 0.2.1.28 — the order is declared once, and lint reads it`. **Not yet
> applied:** `gh pr edit` fails with `Resource not accessible by personal access token
> (updatePullRequest)`, so the retitle is the Captain's to make in the browser, or with a token
> carrying PR write scope.
>
> **Scope grew 2026-09-21, at the Captain's direction.** This is no longer only "the bugs a first
> setup hits": it now carries prompt-grammar enforcement, a prompt behaviour change and replaced
> examples.
>
> **Before tagging:** the CHANGELOG carries a dated `## 0.2.1.28 — 2026-09-09` heading *and* an
> `## Unreleased` section above it, so one release would ship as two sections, one dated twelve
> days early. Fold them or redate before the tag.

**Crucial, and first — #245: a re-run leaves the previous run's intermediates.** The Captain,
2026-09-21: *"this is crucial."* Every run and every `/audit-output` is affected until it lands,
because an audit reads two runs' files as one set. **Do not fix it with `sp clean` before the
run:** that deletes every parameterisation's intermediates, which is #198's bug moved from
`debug/` into `intermediate/`, and it breaks `--rewind-to`, which replays by reading the very
files a pre-run clean removes. The design is a per-run write manifest keyed by pipeline and
`debug.run_key_for(cli_vars)`, so a run deletes only its own previous output and the directory
tree does not change. `clean_before_run: true|false` with `true` the documented default, and
`--no-clean` per invocation. Four rails in the issue, all load-bearing.

- [ ] **#245** — write the `--rewind-to` test first; it is the regression that would hurt most

**Prompt work added to this release, in the order it has to land:**

- [ ] **#176 — strip YAML frontmatter before the LLM call.** A **behaviour change**: the whole
      `.gpt` file reaches the model today, frontmatter included (`steps/llm.py:220` → `307`; the
      stripped `body` at line 85 feeds the contract check only and is discarded). Write the test
      first, then validate across existing pipelines. Open: strip everything, or keep and relocate
      `description:`
- [ ] **#244 — replace the starter prompts.** Sequenced **after #176**, so the replacement is
      written against post-#176 behaviour rather than rewritten after it
- [ ] **Position 12, `reference`, in `data/prompt-structure.yaml`.** Ruled 2026-09-21: prompts
      need an extension point and the end is the place for it. `reference` rather than
      `extensions` or `appendix` — a content word, not a mechanism or a position, so it says what
      belongs there. One `# REFERENCE` section, subsections free-form inside it, with C6
      constraining it to material the tasks cite and no obligation. **Design notes are refused:**
      everything in a `.gpt` reaches the model, so notes for maintainers would be tokens the model
      reads and may act on; they belong in `project/plans/` or the header's `description:`
- [x] **`sp lint` warns on a prompt that does not fit the grammar → #242.** Shipped. Warns, first
      finding per prompt, required sequence once per run. What the grammar binds is declared, not
      coded: a prompt whose **first line** is `---`

> **Why the ordering is a constraint and not a preference:** `sp lint` now warns on all six
> prompts in `prompts/`, so shipping the conformance check while keeping the current starter means
> a new user's first lint warns about the example we gave them. #244 and the check ship together,
> or the check waits.

- [ ] **PR #236** — `dev` → `main`, **18 commits** as of 2026-09-21 and growing (`dev` is 14
      further commits ahead, unpushed), `MERGEABLE`. Merge with a **merge commit**, tag the merge
      commit, watch all five `release.yml` jobs
- [x] Artifacts **expired 16–17 September** — past, so the build re-runs on this release whatever
      else changes
- [ ] `data/models.json` was held back because committing it "restarts a two-hour build". **That
      reason has expired with the artifacts above**, so the one line now costs nothing it was not
      already going to cost. Whether it joins this release is the Captain's call

BaseX is **not** in this release; see below.

### 🦷 The shell/file-tool rules have no teeth — the AI must ask, not just violate

> **Targets this release.** The Captain's words, verbatim: *"The File Commands part of the ai
> context has no teeth. I want to change it so that LLMs ask permission when there is a good
> reason to do something else, e.g. File Tools does not support this operation, it's testing
> candidate Python code from a file (not a heredoc), etc."* And: *"otherwise, I have to give it
> permission on the command line to violate each rule, then interrupt and ask why it did it, and
> it requires my attention, which I want to focus elsewhere."*
>
> The rule is written as a prohibition with no sanctioned exception, so an agent with a genuine
> reason has two moves: obey and fail the task, or violate silently and get caught at the
> permission prompt. **Asking first is not a path the text offers.** The cost lands on the
> Captain's attention, which is the thing the rule was supposed to protect.
>
> **Where the text lives is undecided and is the Captain's call.** `docs/ai-context/` has no
> "File Commands" section. The rules are in `CLAUDE.md` "Shell Commands" (this repo only) and
> `~/.sp/disciplines/workflow.md` "Shell Commands" (every project on this machine, and shared
> with Human at the Helm, so a change there costs a `helm-sync.yaml` hash update and a twin
> commit). A third home is `data/ai-rules.yaml`, the enforced single source, where each rule
> already declares `enforcement:` and `scope:`.
- [ ] Decide the home, then rewrite the rule so that a named exception obliges the AI to ask
      first rather than proceed

### 📓 A pipeline needs a defect log → #232

> Somewhere a step can record what it noticed but did not fail on — a discrepancy in the data, a
> unit needing checking, an assumption it had to make — reaching the end of the run intact and
> attached to the output. `discourse-flow` built `plugins/defects.py` for this, and it is a
> module-level list with a lock, which `context-is-the-only-channel` forbids. They had to break
> the rule because the engine offers no sanctioned channel.
>
> **The engine is already writing these records as unqueryable prose**: `partialVerses` not
> interpreted, a mapping entry skipped as naming no join, `versification_guessed`. So this is not
> a plugin feature — the engine is one of its writers.
>
> Four routes are compared in the issue comment. The suggestion is a **reserved key in a step's
> output** as the channel, which reaches every step type and needs no exemption from
> `context-is-the-only-channel`; a **stdlib `logging` handler** as the Python convenience, since
> `Logger` is already `logging.getLogger('llmflow')`; and a declarative `check:` later.
- [x] **Ruled 2026-09-08.** The Captain took the recommendation: **C as the channel** — a step
      returns a reserved `defects` key alongside its data, so the record travels as ordinary step
      output and needs no exemption from `context-is-the-only-channel`, and every step type can
      write one, not only Python. **B as the Python convenience** — a handler on the `llmflow`
      logger, since `Logger` is already `logging.getLogger('llmflow')`, so plugin authors keep
      writing `logger.warning(..., extra={...})` and need no new import. The sink is **written
      automatically under `intermediate_file_directory`** and **summarised at the end of the run**.
- [ ] Build it. `[]` and absence must differ, per `say-which-kind-of-nothing`: an empty log means
      the run looked and found nothing
- [ ] `for-each` with `parallel:` means concurrent writes — their lock exists because of a real
      race in `subdivide_candidates`

### 🔗 An edition cannot name its discourse or syntax source portably

> Reported by `discourse-flow`; every checkable claim verified against the code. Thread and reply:
> `collab/discourse-flow/2026-09-07-an-edition-cannot-name-its-discourse-source-portably.md`.
>
> `load_registry_editions` resolves **only** `path` through `resources.resolve_path()`
> (`utils/scripture.py:879-885`). `discourse_path` and `lowfat_path` reach `Path()` raw, so a
> dataset-relative value is resolved against the process working directory and absolute is the
> only form that works. A registration therefore carries two kinds of reference at once, under a
> header that promises the file "means the same thing on every machine" — and
> `docs/llmflow-language.md:985` documents the absolute form, so this is the documented outcome.
> Our own `tests/test_discourse_loading.py:15` makes the same assumption via `Path.home()`, in the
> one place a reader would look for guidance.
>
> **Against the Captain's standing rule:** *"never, ever write absolute paths, they will not work
> on another machine."* They can satisfy it everywhere except this file and these two keys.
- [x] **Ruled and built.** The Captain: *"they cannot proceed using hard coded paths, I forbid
      that, they need this to work."* Both keys now accept a dataset-relative value **and** a
      registered dataset id with an optional subpath — the subpath is required in practice,
      because neither corpus sits at a repository root. `resources.resolve_declared_path`,
      20 tests in `tests/test_analysis_path_resolution.py`, documented in the language reference.
      *(Corrected 2026-09-16: this line named `resolve_annotation_path`, which has never
      existed.)*
  - [ ] **Greek discourse still cannot be named portably**, and not for want of the feature:
        `levinsohn-lgntdf` is absent from `~/.sp/datasets/`, so `levinsohn-lgntdf/LGNTDF` falls
        through to dataset-relative and lands nowhere. Registering it needs
        `sp resource download levinsohn-lgntdf`, which needs the upstream `branch` field. Syntax
        works today: `SBLGNT/lowfat` resolves inside the store copy
  - [ ] `tests/test_discourse_loading.py:15` still hardcodes `Path.home()`. It is now the only
        place in the repository modelling the shape we have just replaced
- [x] **`sp resource search` ships.** `sp resource list` showed 3 of 70 entries under a legend
      reading as a full inventory, and nothing listed the rest — which misled a session into
      proposing a hand-written absolute path into the store. A bare word is a keyword; anything
      else is a real XPath predicate evaluated by `lxml` over the catalog as a tree, with
      `lower-case()` and `matches()` supplied at their XPath 2.0 meanings. The `list` legend now
      names `search`.
- [ ] Nothing writes `discourse_path` / `lowfat_path`: `sp resource add` does not set them, so the
      only route is hand-editing a file whose first line says `sp resource add` wrote it
- [ ] A 404 on an archive URL surfaces as a bare `HTTPError` traceback rather than naming the
      branch as the likely cause

### 🔼 Two fixes belong in our catalog repo `awesome-biblical-data`, not in the vendored copy here

> **`nida-institute/awesome-biblical-data` is ours**, so these are ours to schedule, not another
> party's to answer. `data/resources.json` here is **vendored** and currently identical to it, so
> editing it here is reverted by the next sync. Edit `resources.json` there; `README.md` is
> generated after `scripts/validate_resources.py` passes.
- [ ] `levinsohn-lgntdf` has no `branch`, and that repository's default branch is `master`, so
      `sp resource download levinsohn-lgntdf` 404s. `download_data.py:49` already honours
      `branch`, so the fix is one field — upstream. Worth sweeping the other 69 entries
- [ ] This is the second thread now waiting on that repository; BaseX #38 is blocked on
      `awesome-biblical-data#5` — see the BaseX section below

### 🗄️ BaseX collections — **not scheduled**, and not in 0.2.1.28

> **Moved out of x.27 on 2026-09-09, and out of x.28 on the same grounds.** x.28 became a
> bug-fix release cut small and fast for a new contributor's blockers, and BaseX was not in it —
> the CHANGELOG entry says so plainly rather than letting the version number imply progress.
>
> It has no target release. Its critical path still starts in another repository, so scheduling
> it here would be scheduling something this repository cannot finish.

**What ships already, and what does not.** The half that works is the half that was never blocked:

| piece | issue | state |
|---|---|---|
| `type: basex` — query an existing database | #49 | **CLOSED, shipping.** `src/llmflow/steps/basex.py`, three test files |
| `sp setup-db` — load a corpus under a canonical name | #52 | **OPEN, no code.** `grep -n "setup-db" src/llmflow/cli.py` returns nothing |
| collection naming taken from the catalog | #38 | **OPEN, no code.** `design-basex-collections.md` reads `Status: proposal … Nothing is built` |
| `provides` able to describe a treebank or a lexicon | `awesome-biblical-data#5` | **OPEN, zero comments**, untouched since raised 2026-09-07 |

**Why the upstream issue is the whole thing, not a formality.** `provides` requires
`versification`, `canon` and `language` of every entry, so only a scripture text can be declared.
The catalog bears it out: **3 of 70** entries carry a `provides` block and all three are Bibles —
`WLC`, `SBLGNT`, `BSB`. The feature exists to load treebanks and lexicons, and the catalog cannot
name one. Since the first design ruling is *"names come from the catalog"*, there is no input to
build against.

**Verify:** `python3 -c "import json;d=json.load(open('data/resources.json'));print(len(d), sum(1 for e in d if e.get('provides')))"` → `70 3`.

- [ ] **Upstream first:** `awesome-biblical-data#5` — the schema change that lets `provides`
      describe a non-scripture subtree. Not designed here or there yet
- [ ] **Then the catalog content**, which is editorial rather than code: up to 67 entries need a
      `provides` block, and deciding what a meaningful name is needs the maintainer's judgment
- [ ] **Seven decisions in §8** of `design-basex-collections.md` remain unruled even once the
      blocker clears — `LANG` per subtree, `FTINDEX` by default or declared, whether a raw BaseX
      name in `database:` keeps working, the local root for a non-git source, and three more
- [ ] **Then build `sp setup-db`** (#52)
- [ ] **The `done` label on #38 is false and invites a wrong close.** It reads "Ready to be closed -
      implementation complete", which is true of #49 and not of #38's own subject. Changing a label
      is the Captain's act

### 📄 Whitelist design documents by declared status, rather than blacklisting

> ⚠️ **Probably superseded 2026-09-08 by `rule plans-are-temporary`.** That rule deletes a working
> document at eight days rather than classifying it, which was chosen over this proposal on the
> grounds that the valuable content cannot be reliably told from the rest. If it is superseded,
> this section and its two items should go; that is the Captain's call, not an agent's.

> **The Captain's proposal, verbatim:** *"how about whitelisting design documents rather than
> blacklisting? Only rely on design documents with status=[implementing, implemented], and ask
> about any design document marked [implementing] if it is more than 3 days old?"*
>
> This is `declared-not-inferred` applied to plan documents: rely on a declared status rather than
> inferring from prose whether a design is current. Two things it needs that do not exist yet.
> **The status is free prose today** — `project/plans/` carries "proposal, awaiting the Captain.
> Nothing is built.", "Implemented — historical record", "Proposed" and now "implemented", so a
> whitelist needs an enum before it can be a whitelist. **Nothing records when a status changed**,
> so the three-day question cannot be asked; a `since:` date beside the status would answer it.
>
> Unlike most rules in `data/ai-rules.yaml` this one is **guardable**: `project/plans/README.md`
> is already generated from the documents, so a test can refuse an unknown status and flag a stale
> `implementing`.
- [ ] **Ruling needed:** the status enum, and whether `since:` is a separate field or part of it
- [ ] Then the guard, and the generator reading it

### 🔍 `sp lint` checks the prompt contract in one direction only

> **Targets this release.** The Captain's words, verbatim: *"sp lint checks one direction only —
> linter.py:1326, 'every {{var}} must be in requires:'. There is no reverse check. Its own message
> for a withdrawn key even says 'delete it if the body does not use it', which is advice to a
> human, not an enforced rule."*
>
> `validate_gpt_body_declares_all_vars` computes `undeclared = body_vars - declared`
> (`linter.py:214`) and stops. The reverse set — a name in `requires:` that the body never uses —
> is never computed. So a prompt can declare an input, `validate_all_step_contracts` can oblige
> every calling step to supply it, and the body can ignore it, with nothing said anywhere. The
> remedy the withdrawn-`optional:` message advises at `linter.py:161` *is* this check, unenforced.
> **The `audit-prompts` skill has the same blind spot.** Its nine steps check convention
> structure, grounding of *output* fields, example diversity, guardrail integrity, AI-written
> examples, JSON formatting and structured outputs. None compares a prompt's `requires:` list
> against the `{{var}}` names its body uses, so a declared-but-unused input passes the audit
> exactly as it passes lint. The Captain: *"ALSO should catch this error."*
>
> **Two surfaces, one defect, but not one fix.** The linter is ours. The skill lives in
> `~/.sp/skills/audit-prompts/SKILL.md`, which is the Captain's store — and per #204 most of
> `~/.sp` is not in the package, so a check added there reaches this machine and no other until
> that is fixed.
- [ ] **Ruling needed first:** is an unused `requires:` entry an error or a warning? Then add the
      reverse check to `validate_gpt_body_declares_all_vars`
- [ ] Add the same check to the `audit-prompts` skill — **the Captain's store, needs his approval**

### 🐛 A skill added after a project was set up never reaches it, and `sp doctor` says all is well

> **Found by the Captain 2026-09-19** in `nida-institute/discourse-flow`. `sp doctor` reports no
> problems — *"✓ Skills in `~/.sp`: all 11 present and unchanged"* and *"✓ Skills are where Claude
> Code reads them"* — while `ls .claude/skills` there returns **ten**. `health-check` is the missing
> one. It was added 2026-09-10; that project predates it.
>
> **Not a catalogue problem, and an earlier diagnosis saying so was wrong.** `data/file-catalog.yaml`
> names the *directory*, not its contents — `sp/skills/*` at lines 50–54 and 73–77, for `~/.sp` and
> `.claude/skills/` respectively. Every skill is covered, and a fresh `sp init` today installs
> `health-check` into both. The first diagnosis searched for the string `health-check`, did not find
> it, and concluded it was uncatalogued; no skill name appears in that file.
>
> **The verified cause** is `doctor.py:651–664`, which asks whether Claude Code can see **any**
> skills rather than all of them:
>
> ```python
> if project_skills.is_dir() and any(
>     (p / "SKILL.md").exists() for p in project_skills.iterdir() if p.is_dir()
> ):
>     found.append(".claude/skills (this project)")
> ```
>
> One skill directory and the check is green. Its own comment says so, and
> `tests/test_doctor.py:207–233` confirms the design by placing a single `load-context` skill and
> asserting OK. **Nothing anywhere adds a newly-shipped skill to an already-initialised project, and
> nothing reports its absence.**
>
> **Why no test caught it.** `tests/test_catalog.py:203`, `test_skills_derive_from_shipped_templates`,
> is exactly the right comparison — shipped against catalogued — but line 208 restricts it to
> `Scope.SP_HOME`. The project destination has only `test_claude_skills_are_catalogued` at line 105,
> which ends at `assert skill_entries`: that *an* entry exists, not that it delivers everything.
>
> **Two projects, so not a local accident:** `paratext-copilot` lacks `health-check` too.
- [x] **Fixed 2026-09-19, and the ruling it was waiting on dissolved.** Report-versus-install was
      the wrong question: the Captain ruled that `sp doctor` and `sp init --update` are synonyms
      and share code, so both restore. The starter examples are the only difference, and that is
      now `policy: example` on four catalog rows rather than a flag in code.
- [x] **Answered — the `Scope.PROJECT` check excluded project skills, twice over.** The filter at
      `doctor.py:635` was `source in (CONSTANT, TEMPLATE)` and project skills are `source: sp-home`;
      and the check took its expected count from the files that existed, so absence could not be
      represented. Both deleted, with `skills_reachable` and `restore_when_absent`. Guarded by
      `tests/test_doctor.py::test_a_project_missing_a_shipped_skill_is_not_reported_green`, which
      runs through `main(["init"])` and `main(["doctor"])` rather than the Python API.
- [x] **The CLI now has a specification** — `docs/ai-context/sp/command-line.md`, shipped to every
      project, with `tests/test_cli_is_documented.py` failing in both directions when it and the
      parser disagree. Nothing had described the commands at all.
- [ ] **Still to do: `sp init --update` stops having its own code and calls doctor** (§4.2 of
      `plan-init-doctor-unification.md`). They now *behave* the same; they are not yet one
      implementation, which is what the Captain ruled on 2026-08-23 and again on 2026-09-19
- [ ] **Still to do: replace the hello-world examples with scripture examples** (Captain,
      2026-09-19). `policy: example` is the row that says which four files those are
- [ ] **File this as a GitHub issue** — the convention at the top of this file says bugs go there.
      Not filed; creating issues needs the Captain

### 🐛 `sp init`'s write paths — three defects, found migrating discourse-flow → #215
> Filed together because they share a cause: `sp init` writes through paths `sp doctor` has
> already hardened, and reports failure inconsistently.
- [ ] `_upsert_delimited_block` writes without unlocking; `doctor._restore` unlocks
      (`doctor.py:194`). A read-only `CLAUDE.md` crashed `sp init --update`. **Needs a ruling
      first:** unlock and write, or skip and report? The read-only bit may be protection.
- [ ] `sp init` is not atomic — the crash left a half-updated assistant configuration
      (Copilot done, Claude Code / Cursor / Windsurf not) and said nothing but a traceback.
- [ ] The registry write fails as a warning naming `~/.sp/ai-context/project-index.md.yaml` —
      a filename retired on 2026-08-24. The store is deliberately read-only, so that failure is
      the normal case, not an exception.

### ▶ Do these in this order — set by the Captain, 2026-08-24

1. **`overview.md` is two documents sharing one path → #210.** Small: a rename in *this* repo
   plus an audit of the other three `docs/ai-context/` files. It is why `sp doctor` must not be
   run here.
2. **21 shipped documents from Python constants to `source: template` → #211.** Wide and
   mechanical. Blocked on #210: naming a template while `overview.md`'s reader is ambiguous
   means naming it wrong and moving it twice. Finishing it is what makes `sp doctor` safe here.
3. **`format: usj` → #200.** Everything it needs is ruled through `f93e9ca`. Start from the
   parked local tag `wip/scripture-200`.

> **Before starting 3, one ruling is needed** — §4.4 of
> `project/plans/design-scripture-representations.md`, the Greek/Hebrew asymmetry. Five `=>`
> slots there are empty; that one blocks. `include: [senses]` yields `{domain, ln}` on SBLGNT and
> `{lexdomain, contextualdomain, coredomain, sdbh, sensenumber}` on WLC. The recorded
> unnormalised position is a **proposal, not a ruling** — implementable as written, but a
> normalising ruling changes the payload and anything built first is wrong.

> **Insurance worth taking:** `wip/scripture-200` is a **local tag with no remote**, and
> `project/plans/design-scripture-editions.md` exists nowhere else — not on `dev`, not in the
> working tree. `git push origin wip/scripture-200` costs nothing and removes a single point of
> failure. A push is the Captain's act.

> **Deliberately not scheduled:** #209, the repository rename. Filed with its migration detail
> and an order of operations, to be picked up when the Captain chooses.

### 🆕 Opened 2026-09-01 — five issues, order not yet set
> **Where these sit relative to the ordered list above is the Captain's to set.** They are
> recorded here because the task list is the queue; `HANDOFF.md` carries only session residue.
> One is built: #225, rules cited by id — `fcd4c67` on `dev`, carrying `Closes #225`. **The issue
> is still open on GitHub** and closes when `dev` merges to `main`; the change is already live in
> consumer repos here through the editable install. Guarded by
> `tests/test_record_closure_claims.py`.
- [x] **Remove `optional:` from prompt frontmatter → #228.** Shipped in 0.2.1.26. Breaking: both
      header forms are refused by `sp lint` and `sp run` with one shared message. The shipped
      discipline now teaches the key's absence rather than `optional: [perspectives]`, so `sp init`
      no longer installs the retired convention.
  - [ ] **Consumer migration is outstanding.** `nida-institute/discourse-flow` carries **non-empty**
        `optional:` lists, so it will fail lint against 0.2.1.26 until each name moves to
        `requires:` or is deleted. Mechanism and evidence:
        `collab/discourse-flow/2026-09-01-dotted-requires.md`. Their repository, their change —
        tell them the release is out.
- [ ] **`include: [syntax]`, Lowfat as standoff JSON → #227.** Design ruled and recorded in
      `project/plans/design-scripture-representations.md` §4.5 and §7. Read the issue for the JSON
      shape, not the handoff.
- [ ] **Extract the biblical-text convention layer → #226.** Design in
      `project/plans/design-biblical-text-conventions.md`; the middle layer lives in
      `awesome-biblical-data`. D3 is ruled. **D1, D2, D4 and D5 are unanswered `=>` slots and are
      the Captain's** — do not answer them.
- [ ] **Epic: enforce rules, don't instruct them → #230.** The AI context is ~27,000 words read at
      session start, and keeping it enforced currently depends on the Captain knowing all of it.
      Substantially advanced in 0.2.1.26 and still open — read `CHANGELOG.md` for what shipped,
      not this entry. Each rule now declares `enforcement:` and `scope:` in `data/ai-rules.yaml`,
      which is the single source for the triage; the counts once kept here are not maintained.
  - [x] **The `lxml-for-xml` violation is fixed.** `src/llmflow/plugins/xml_entry_to_base_json.py`
        imports `lxml.etree`, and `tests/test_lxml_not_elementtree.py` refuses an
        `xml.etree.ElementTree` import anywhere in `src/`, so the rule now holds by test rather
        than by attention.
  - [ ] **Still open in the epic:** the nine rules classified `guardable` — a test is possible and
        not yet written. `data/ai-rules.yaml` names them; no separate list is kept.
  - [ ] **Candidate guard, unruled:** `HANDOFF.md` is stale if its date is older than HEAD's
        commit date. The Captain has not ruled whether this belongs in #230 or its own issue.
- [ ] **Completion reports, requirement softening, decision churn → #229.** Filed; **explicitly
      not being chased.** The remedy is recorded in it: checklists, and never ticking a box
      without showing the evidence.

### ✅ Settled 2026-08-24 — the #204 catalog questions are all ruled
> `project/plans/plan-init-doctor-unification.md` Q1–Q6. **Built:** nine catalog rows (the four
> hello-world examples `generated`, the four audit documents `create-once`),
> `.github/copilot-instructions.md` now block-managed like its two siblings, and the two-index
> split — `project-index.md` (`create-once`, the project's own map) and `sp-index.md`
> (`generated`, **rendered from the catalog's new `purpose:` field**, so it cannot go stale).
> **Not built:** §4.1–4.3, the `sp init --update` → `sp doctor` unification itself.

### ⚠️ Versification — a reference means different verses in different editions → #203
> **Blocks OT use of `sil-translator-notes`.** WLC and BSB disagree by two verses on `PSA 51:1`
> and the run reports success. Fix via the Copenhagen Alliance specification, cloned at
> `~/github/copenhagen-alliance/versification-specification`.
>
> **The design content lives in `project/plans/plan-scripture-step.md` §3.-1** — the mappings, the
> `MAL 4:1` case, and the requirement that editions declare their scheme and `type: scripture` map
> before fetching. It is recorded there because an earlier condensation of *this* entry lost it:
> summarising in place is right for a session cache, but a requirement has to move to a design
> document rather than be shortened.
>
> **Two pieces shipped in 0.2.1.26, and the entry stays open.** The container now reports the
> edition's own scheme instead of the caller's requested one — it was labelling verses with a
> scheme they were not numbered in — and an edition declaring no versification is read as `eng`
> with a warning, rather than raising, with `versification: null` plus `versification_guessed`
> keeping the guess distinguishable from a declaration. Neither closes the entry: the `PSA 51:1`
> disagreement above is about the mapping being applied on the way in, not about labelling.

### ⚠️ Paratext `custom.vrs` is detected and ignored → #222
> **A project's own versification should win, and today it loses silently.** `_paratext_scheme`
> finds a `custom.vrs`, warns that it will not read it, and uses the numbered scheme — so
> references into such a project are wrong wherever the overlay changes something.
>
> The format is the three concepts `utils/versification.py` already models: 193 amended chapter
> lengths, 465 mappings, 5 exclusions across 29 real files on this machine. A `custom.vrs` is a
> Copenhagen scheme with `basedOn` set to the numbered one.
>
> The substance is not the parser but this: `edition_scheme()` returns a scheme *name* and
> `map_reference` takes names, while an overlay has none. Synthetic name, or `Scheme` objects
> through the API — that choice is the work. Scripture Burrito is #221 and follows, reusing
> whatever shape this settles.

### 📖 Scripture editions — core landed, wiring incomplete → #200
> Commits are parked on the **local** tag `wip/scripture-200` (`05d75a5`, `34c7931`) and are
> **not on `dev`**, which was reset to `cb72cb7` so the release could ship without them.
> Cherry-pick after PR #199 merges. Design: `design-scripture-editions.md`, which exists **only
> on that tag** — not on `dev` and not in the working tree, so read it with
> `git show wip/scripture-200:project/plans/design-scripture-editions.md`.
- [ ] Pericope reader
- [ ] Docs — `docs/llmflow-language.md` and `docs/architecture.md` currently never mention it
- [ ] Decide whether #200 supersedes or merely cross-references #38, #39/#172, #40, #41
- [ ] `~/.sp/editions/*.yaml` were seeded with absolute paths on this machine; how editions get
      registered per machine is undecided
- [ ] Datasets record no version and the catalog is never validated; `berean-usx` points at a
      404 → #201
- [ ] Prefer discourse-flow pericopes and segments over BSB `\s1` headings once coverage allows
      → #202 *(board: Backlog)*

### 🧹 `jonathanrobie/examples.bsb` fork — keep open until upstream PR #7 is accepted
> **Decided (Captain, 2026-08-17): keep the fork open until the PR is accepted.** No GitHub issue
> tracks this; the note lives here because the constraints are local. Upstream:
> https://github.com/usfm-bible/examples.bsb/pull/7 (adds the missing `\id` to Ecclesiastes).
- [ ] **Do not delete the fork** — a fork PR depends on the fork's branch, so deleting it closes
      the PR. Only once #7 is accepted: `gh repo delete jonathanrobie/examples.bsb --yes`
- [ ] **Keep `~/github/usfm-bible/examples.bsb` on branch `dev`** meanwhile — it carries the patch
      that makes all 66 books load; without it BSB Ecclesiastes silently disappears

### 🔁 for/in syntax migration (breaking — one syntax, no aliases)
> See `project/plans/design-foreach-syntax-migration.md`. Systematic commits, one per repo.
> Migration: `item_var:`→`for:`, `input:`/`over:`→`in:` (for before in). Old keys fail loud.
- [x] **Core engine** — runtime/schema/linter/tests/docs (`86b3f2b`, pushed `dev`)
- [x] **discourse-flow** — committed + pushed (clean)
- [x] **discourse-flow-hebrew** — committed + pushed (clean)
- [x] **semdom-greek-lexicon** — pipeline committed `0e050f6` (incl. in-file WIP); not pushed
- [x] **macula-lxx-greek** — pipeline committed `b55fca7`; not pushed
- [x] **image-scene-descriptions** — pipeline committed; not pushed
- [x] **Fast-follow** — `tests/test_doc_examples_lint.py` + filled `ALLOWED_STEP_KEYS` gaps
      (`content`, `key`, `where`, `offset`, `columns`) + `prompt_file` doc fixes
- [x] **json-reliability.md** — `response_mime_type`/`response_schema` were real Gemini keys
      missing from `ALLOWED_STEP_KEYS` (doc was correct); added them + re-included ai-context
      in the doc-lint scan. No ai-context edit needed.
- [x] **Release** — re-cut `v0.2.1.20` shipped 2026-07-14: GitHub Release (3 binaries) + PyPI 0.2.1.20. (Hit a PyPI trusted-publisher/workflow-rename snag; fixed — see RELEASE_CHECKLIST failure modes.)

### 🔥 Monday priorities
- [ ] **Fix GUI Content Lifecycle** — Content Lifecycle page displays blank, needs debugging
      *(no GitHub issue; this file is the only record)*

> **PyPI publishing is automated — there is no task here.** Kept as reference because the note
> that occupied this slot described a manual flow that no longer exists (it named v0.2.1.14, the
> package `llmflow`, and a password/API-token/`hatch publish` sequence).
>
> - `release.yml` job `publish-pypi` uses PyPI **trusted publishing** (OIDC, `id-token: write`)
>   and is gated on the `pypi` **GitHub** environment approval — not a PyPI login. No password
>   and no API token are involved.
> - The package is **`scripture-pipelines`** (`pyproject.toml:2`), not `llmflow`;
>   `pypi.org/project/llmflow` does not exist. Published: 0.2.1.18, .19, .20, .22, .23.
>   Verify at https://pypi.org/project/scripture-pipelines/
> - PyPI account: `jonathan.robie@gmail.com` (also the `authors` entry in `pyproject.toml:5`)
> - **Do not rename `release.yml`.** Trusted publishing matches on the workflow *filename*;
>   renaming it breaks the OIDC claim with `invalid-publisher`. Update the PyPI publisher config
>   (project → Manage → Publishing) first. Full failure mode in `project/RELEASE_CHECKLIST.md`.

### 🎓 Workshop readiness (main next goal)

#### 🎯 Doing now — bugs Paul hit setting up on his own machine → #204
> Board 13: **In Progress**. Targets the **next** version, not the 0.2.1.24 release in flight.
>
> **Acceptance criterion (Captain, 2026-08-17):** a user clones a mentoring repository such as
> `sil-translator-notes`, runs `sp init`, and `/load-context` works. Nothing hand-carried.
>
> Paul cloned the repo, ran `sp init`, ran `/load-context`, and got **HTTP 400 with no body**.
> Getting him working took a hand-built zip of `~/.sp/`, copying `~/.sp/skills` →
> `~/.claude/skills`, hand-editing three edition files to strip another machine's absolute paths,
> and patching a USFM file — and it still did not work.

**⚠️ The cause recorded in #204 is wrong.** Read against `cli_utils.py` on 2026-08-17:
> #204 says *"`sp init` does not create `CLAUDE.md` — there is no code that creates one"* and
> *"`sp init` overwrites hand-written AI context"*. **Both are false.** `_configure_claude_code`
> (`cli_utils.py:756-761`) upserts a delimited block into `CLAUDE.md`, and every generated
> ai-context file is guarded `if not exists → write / elif update and _is_generated → rewrite /
> else → leave as-is` (`cli_utils.py:1854-1888`). Plain `sp init` overwrites nothing.
> **#204 needs correcting before anything is built against it.**

What actually blocks the acceptance criterion:
- [ ] **`_configure_ai_assistants` returns silently when stdin is not a TTY**
      (`cli_utils.py:805-806`). No `CLAUDE.md`, no skills, no message saying so
- [ ] **"Claude Code" defaults to No** (`cli_utils.py:812`, `default=False`). A user pressing
      Enter through the prompts gets no `CLAUDE.md` and no skills
- [ ] **"Install Claude Code skills?" also defaults to No** (`cli_utils.py:777`) — and that
      consent branch is the *only* path that copies into `~/.claude/skills/`, which is where
      Claude Code actually reads. `~/.sp/skills/` is populated either way, and is the wrong place
- [ ] **Most of `~/.sp/` is not in the package.** `templates/` ships only `sp-conventions/`
      (5 files) and `sp-skills/` (10 skills). Missing, and therefore unobtainable by any
      `sp init`: `drift-patterns.md`; the whole `user-context/` directory
      (`filesystem-access.md`, `github-authority.md`, `consumer-repo-conventions.md`);
      the conventions `design-authority.md`, `sp-debugging.md`, `sp-workflow.md`;
      `editions/*.yaml.template`; and the 12 `ai-context/*.yaml` registry files.
      **This is what the zip was carrying** — overlaps #181
- [ ] **`/load-context` reads files that a fresh machine cannot have** — its step 5 runs
      `cat ~/.sp/drift-patterns.md`, which the package does not ship. Skills must skip a missing
      file cleanly and never emit an empty read (an empty content block is the bodyless 400)
- [ ] **No verification step** — `sp doctor` or `sp init --check`: are skills in
      `~/.claude/skills/`, are editions registered and resolvable, is `CLAUDE.md` present
- [ ] **Editions are not portable** — `~/.sp/editions/*.yaml` carry absolute paths. Ship the
      `.yaml.template` files and add a per-machine registration flow
- [ ] **Confirm `~/.sp` creation.** `install_global_conventions`/`install_global_skills` run
      non-interactively (`cli_utils.py:1952-1954`) and `mkdir(parents=True)`, so this appears
      already satisfied — but the call is wrapped in a `try/except` that only *warns* on failure
      (`cli_utils.py:1955-1956`), so a silent partial install is possible
- [ ] **Hazard, `--update` only:** a file still carrying the `<!-- Generated by sp init -->`
      first line is rewritten by `sp init --update` even if hand-edited. Only `project.md` is
      exempt (`cli_utils.py:1890`)
- [ ] **Nothing tests a clean machine** — 2620 tests pass and none caught any of the above. Needs
      a run from a clone with an empty `HOME`, plus a committed fixture-edition TSV so `sp lint`'s
      "no text found" path can be tested

#### Installers and setup
- [ ] Build Mac + Windows installers via GitHub Actions CI → #32
  - Built via Nuitka in `.github/workflows/build.yml` (`--standalone --onefile`, per-platform)
  - Trigger: push a version tag `v*` → auto-publish to GitHub Releases
  - Install script renames binary to `llmflow` (no manual rename needed):
    ```bash
    curl -fsSL .../llmflow-macos -o ~/bin/llmflow && chmod +x ~/bin/llmflow
    ```
- [ ] Implement `llmflow setup` command (per-machine, run once after install) → #32
  - Silently installs `llm` plugins (e.g. `llm install llm-gpt4all`)
  - Prompts user for OpenAI API key (`llm keys set openai`)
  - `llmflow setup --update` re-runs (update plugins, change key)
- [ ] **Naming convention locked:** `--update` is always a flag on its parent command, never a standalone subcommand
  - `llmflow init --update` — refresh generated project docs
  - `llmflow setup --update` — update plugins / change API key
  - No bare `llmflow update` command (use install script or `brew upgrade` to update binary)

## 📋 Backlog

### 🧹 Debug/log docs follow-ups + `sp` terminology audit → #180
> Fallout from documenting the `log_level: debug` request/response dump feature
> (added `docs/architecture.md` §15; new `~/.sp/conventions/sp-debugging.md`).
- [ ] Cross-ref the debug-dump feature from `docs/llmflow-language.md` — `log_level`
      is documented there (≈ line 57) only as a verbosity knob; point it at
      `architecture.md` §15 so the dump behavior is discoverable from the language spec.
- [ ] **Decide:** rename the log file `llmflow.log` → `sp.log`? Core change
      (`runner.py` default `log_file='llmflow.log'`, the `--log` flag default, and the
      debug-dir log co-location). If yes, update the docs that name it literally
      (`architecture.md` §15, `~/.sp/conventions/sp-debugging.md`) in the same change.
- [ ] **Audit** for other stale references worth changing at the same time: product/CLI
      name (`llmflow run/lint/template` → `sp`) across `docs/`, any remaining `.llmflow/`
      path fictions, and consumer-repo docs (e.g. ears-to-hear
      `docs/architecture/debugging.md` still uses `llmflow …` command names and
      leaders-guide framing). Scope the sweep before making edits.

### 🎓 Workshop readiness
- [ ] Replace hello-world example with a domain-relevant pipeline
      (e.g. translation notes for a Bible passage, or back-translation check)
- [ ] Polish error messages — every ❌ should say what to fix, not just what went wrong
- [ ] Workshop handout: 1-page "what is this and why do I care"
- [ ] API key story for workshop: shared org key so participants don't each need one

### 🚀 Publishing
- [ ] Clean up repo for public release → #33
  (metadata, data licensing, .gitignore gaps, README, history audit)
- [x] Published to PyPI as `scripture-pipelines` — latest 0.2.1.23. (The name `llmflow` was never
      used; see the PyPI note under Monday priorities.)

### 🔧 Open issues on board
- [ ] Bootstrap New Project UX improvements → #28
- [ ] Conditionals and switches → #11
- [ ] Checkpointing support → #8

### 🗂 Pipeline data operations

#### ⚠️ Verse range operations → #169 — **partly built, and the plan says otherwise**
> **Corrected 2026-09-13.** This entry said "6 decisions needed before implementation". The
> module is built: `src/llmflow/utils/verse_ranges.py`, with `tests/test_verse_ranges.py` at
> 371 lines. What is stale is the plan beside it.
>
> `project/plans/plan-verse-range-set-ops.md` declares *"Approved 2026-08-17 — authoritative for
> the implementation (names, signatures, files)"* and *"No code yet"*. Both are now false, and
> the code took a different shape:
>
> | | plan says | code does |
> |---|---|---|
> | naming | `verse_range_overlaps`, … | `overlaps`, `contains`, … |
> | representation | 8-char sort key `BBCCCVVV` | `Range` dataclass, **book-local ordinals** |
> | adjacency | `adjacent` | `touches` |
> | also present | — | `equals`, `select`, `RELATIONS` |
> | **not built** | `union`, `intersect` | — |
>
> This is a `one-design` breach: two documents and one implementation, disagreeing. Reconciling
> them is a ruling, not a cleanup — the Captain's.
- [ ] **Ruling needed:** does the shipped `Range`/`overlaps` shape stand and the plan get
      rewritten to match, or does the code move to the approved `verse_range_*` spec?
- [ ] `union` and `intersect` are unbuilt. They are the operations an alignment mapping would
      compose with, so this blocks the idea in the alignment section above
- [ ] Design document: `project/plans/design-verse-range-operations.md` (data model);
      `plan-verse-range-set-ops.md` (spec and work order)
- [ ] List transformation: flatten, project, slice as framework primitives → #167
- [ ] Predicate filtering: filter lists by value / cross-list membership → #168
- [ ] Accumulator initialization in `variables:` block → #170

## ✅ Done

---
_Audit notes and QA reports → project/audits/_
_Pipeline decisions → project/decisions.md (create when needed)_
_Project board → https://github.com/orgs/nida-institute/projects/13_
