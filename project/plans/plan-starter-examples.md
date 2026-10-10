# Plan — build the starter example (#244), then #252 and #261

**Status:** ruled (2026-10-02)

The design is `project/plans/design-starter-examples.md`. This file is the work order and the
checklist. **A box is ticked only with its evidence beside it** — a test id, a command and its
result, a count, a commit sha. Not *done*: *how you know*.

Order, set by the Captain 2026-10-02: *"finish #244 first, then #252 and #261"*.

---

## Rulings this plan carries, beyond the design's slots

The Captain, 2026-10-02, answering the authorization questions:

1. **The example takes Old Testament passages too** — *"it needs this regardless, just do two
   variables, e.g. hebrew_frequency_cutoff, greek_frequency_cutoff, both in percent."* So the
   subject step reads WLC or SBLGNT by testament, and there are two cut-off variables.
2. **The cut-offs have defaults, overridable with `--var`** — *"yes, and they can be overriden on
   the command line."*
3. **This plan file** — *"absolutely."*
4. **The design is ruled** — *"yes."*

Three more, answered in conversation the same day — *"Q1 - B. Q2 - yes. Q3 - yes"*:

5. **A cut-off of N percent is a rank among lemmas** — a word is less common when its lemma falls
   in the least frequent N% of lemmas, ranked by count. (Offered against: coverage of the running
   text, and share of all words.)
6. **#267: the text widens with the analyses**, in every format, so text and analyses never
   disagree about which words are present.
7. **#267: each word outside the requested verses is marked**, one field per word.
8. **Defaults: `greek_frequency_cutoff: 80`, `hebrew_frequency_cutoff: 90`** — the Captain, the
   same day, *"use these."* At 80 the Greek guide covers lemmas occurring at most 9 times (4,388
   lemmas); at 90 the Hebrew guide covers at most 43 (7,601). Every hapax shares one percentile —
   36.32 Greek, 31.94 Hebrew — so a cut-off below that selects nothing.

---

## 1. #267 — whole-sentence words with `syntax` (prerequisite, D8 → A)

- [x] failing tests first, through the object model — `tests/test_syntax_whole_sentences.py`,
      **6 failed / 1 passed** before the change (the pass is the no-`syntax` non-regression);
      9 passed after, including the real-corpus `MRK 1:3-8` (20 words, all `n41001002…`) and
      `MAT 19:1-11` (`{}`), which agree with the BaseX measurement in #267
- [x] open question 1 in #267 (marking the widened words) — **yes**, ruling 7 above, 2026-10-02
- [x] open question 2 in #267 (does the text widen too) — **yes**, ruling 6 above, 2026-10-02
- [x] implemented — `utils/syntax.py` (`covering_sentences`, `sentence_word_ids`,
      `payload_for_sentences`), `utils/scripture.py` (`widen_to_sentences`, `_emit`,
      `outside_passage` in the container; TSV and TEI both pass book rows). `tests/test_syntax_payload.py`
      26 passed unchanged
- [x] `docs/sp-language.md` under `type: scripture`, and the shipped
      `scripture-representations.md` template, say so — both edited
- [x] this repository's rendered `docs/ai-context/sp/scripture-representations.md` regenerated —
      on the Captain's *"yes"*, 2026-10-02, from `fc.shipped_content` for that one entry, nothing
      else written. `tests/test_template_layout.py` → 8 passed

## 2. The frequency tables (D1, D1′ → A, D1″)

- [x] `.xq` for the GNT — `tools/lemma-frequency/greek.xq`. **Reads the BaseX database
      `SBLGNT-lowfat`, not the files**: parsing `03-luke.xml` directly stops at the JDK's element
      depth limit (101 > 100), and neither `db:intparse` nor `-OINTPARSE=true` lifts it in BaseX
      12.3. The database was built from the directory the registration names
- [x] `.xq` for the Hebrew Bible — `tools/lemma-frequency/hebrew.xq`, `macula-hebrew-lowfat`:
      `pos="suffix"` excluded, `aramaic` count per lemma, counted together
- [x] JSON tables generated, regenerating command in each query's header —
      `data/lemma-frequency-{greek,hebrew}.json` and their template twins. Two runs each,
      byte-identical by `cmp`. **Not yet committed**
- [x] counts cross-checked against the registered TSV — Greek 137,741 words = 137,741 rows;
      Hebrew 428,469 morphemes = 475,911 rows − 47,442 `pos=suffix` rows (`awk` over
      `macula-hebrew.tsv`)
- [x] catalog rows ship both tables — `data/file-catalog.yaml`, `policy: example`;
      `tests/test_init.py` 43 passed, `test_template_layout` passes for both

## 3. The pipeline

- [ ] the subject step chooses WLC or SBLGNT by testament — the language expresses it, or a
      missing construct is filed — evidence:
- [ ] `greek_frequency_cutoff` and `hebrew_frequency_cutoff` declared with defaults, overridden
      by `--var` — evidence:
- [ ] the frequency table reaches the guide step as a named input — evidence:
- [ ] parallels: each member fetched with its whole chapter, `versification: org` (D5 → A) —
      evidence:
- [ ] `description:` on every step, as `llmflow-pipeline-steps.md` requires — evidence:
- [ ] `sp lint` silent — evidence:
- [ ] `--dry-run` on `MAT 19:1-11` resolves every path and variable — evidence:

## 4. The two prompts

- [ ] `prompts/reader-guide.gpt` conforms to the twelve positions; `sp lint` gives no
      conformance warning — evidence:
- [ ] non-finite verbs read against the whole sentence, stated as a rule — evidence:
- [ ] Aramaic words marked in the guide — evidence:
- [ ] `prompts/parallel-significance.gpt` conforms — evidence:
- [ ] synoptic parallels read assuming Markan priority (D4 → B); the model isolates the relevant
      pericope from the chapter (D5) — evidence:
- [ ] **every ❌/✅ example in both prompts approved by the Captain** — evidence:

## 5. The removal, one pass (design §6)

- [ ] `pipelines/commentary.yaml`, `prompts/commentary.gpt` and their template twins deleted;
      new twins added — evidence:
- [ ] `data/file-catalog.yaml` example rows replaced — evidence:
- [ ] `cli.py`, `cli_utils.py` constants and `_EXAMPLE_PATHS` — evidence:
- [ ] `tests/test_init.py`, `tests/test_linter.py` — evidence:
- [ ] `docs/tutorial.md`, quickref and `command-line.md` templates rewritten — evidence:
- [ ] `data/ai-rules.yaml` `cite-paths` example — evidence:
- [ ] `docs/ai-context/sp/index.md` regenerated — evidence:
- [ ] `grep -rn commentary` over `src/ docs/ data/ tests/ pipelines/ prompts/` → only intended
      hits — evidence:

## 6. Gates

- [ ] full suite: `hatch run pytest tests/ -q -m "not integration" -p no:randomly`, count and every
      failure named — evidence:
- [ ] `CHANGELOG.md` Unreleased — evidence:
- [x] **the Captain directs the `sp run`** on `MAT 19:1-11` — run by the Captain 2026-10-05 in
      `playground/sp-example` after `sp init`, with `gpt-4.1` (discourse-flow's settings). His
      words: *"The sample output looks great, and examples are now done."*

---

## Then #252, then #261

Each gets its own section here when #244 is done. #252's plan exists:
`project/plans/plan-terms-on-download-and-register.md`. #261 has none yet, and its seven open
questions are in the issue body.
