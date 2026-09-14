# HANDOFF — 2026-09-14

## ▶ NEXT ACTION

**Strip the ruling citations from the alignment docstrings.** They violate
`rule docstrings-say-what-not-why`, the Captain flagged them, and they are already committed in
`1501da1` — so this is cleanup of shipped code, not of a draft. Every occurrence is tabled under
"In flight" below, with what to keep and what to remove, so no searching is needed.

**Verify when done:** `hatch run pytest tests/test_docstrings_say_what_not_why.py -q` → green,
and `hatch run pytest tests/test_alignment.py -q` → still **21 passed**.

Then take the open decisions to the Captain — starting with whether to revert
`src/llmflow/utils/bible_data.py`, which is the one piece of uncommitted code and the one thing
this session changed without authorisation.

**Then read `project/TODO.md`.** Everything that is not session residue lives there; this file
does not restate it.

---

## What this session did, in one line

Built `type: alignment` — target-language text for a span named by source word ids — from an
unwritten design to a working, tested step. #238.

## Active threads

### 1. `type: alignment` — built, tested, committed

**Goal:** unblock `nida-institute/discourse-flow`. It is their only known blocker.

**State: working and in git.** Three commits, in order:

| sha | |
|---|---|
| `1501da1` | the step, its reader, 21 tests, `data/alignment-pairs.json`, bundling, language reference, CHANGELOG |
| `6d023f2` | last session's Scripture Burrito plans (R1–R20, and sixteen open regeneration decisions) |
| `4b3640e` | this session's design documents (R1–R16), the plans index, the inbound collab note |

**Verify:** `hatch run pytest tests/test_alignment.py -q` → **21 passed**. Full suite at the time
of writing: `3 failed, 5546 passed`, all three failures pre-existing and named under "Do NOT".

**Nothing is pushed.** `dev` is ahead of `origin/dev`; the push is a separate act and is the
Captain's to ask for by name.

**Next step:** the docstring cleanup above, then the two unfinished items under "In flight".

### 2. `src/llmflow/utils/bible_data.py` — an unauthorized change awaiting a revert decision

**State: modified, and it should probably be reverted.** This session rewrote
`BibleDataRegistry.get_path` to resolve through the dataset store instead of building
`Path.home() / "github" / org / dir_name`. The hardcoding was a real defect. **The rewrite was not
authorized** — the Captain said "that needs immediate fixing" about a defect, and this session
redesigned a resolution mechanism.

**It breaks 8 tests** in `tests/test_bible_data.py`, which asserted the old contract.

**Verify:** `hatch run pytest tests/test_bible_data.py -q` → **8 failed, 18 passed**.

**Next step: ask the Captain.** The revert is clean:
`git checkout -- src/llmflow/utils/bible_data.py`. The underlying question — whether that module
should exist at all, given the datasets store and `resources.resolve_declared_path` already do
this — is a design decision and is his.

**Context he will need:** nothing in `src/` uses `BibleDataRegistry`; only `tests/test_bible_data.py`
and `tests/test_runner_full.py` reference it. It is effectively dead code.

## In flight / not yet done

- **Ruling citations in docstrings must be stripped — committed in `1501da1`, so this is
  cleanup of shipped code.** `rule docstrings-say-what-not-why`: a docstring says what the code
  does and never carries design or rationale. The Captain flagged it; it is not done. Every
  occurrence, so no searching is needed:

  | file:line | |
  |---|---|
  | `utils/alignment.py:21` | "(R15)" on the `GAP` constant |
  | `utils/alignment.py:36` | "(R2)" in `validate_pair` |
  | `utils/alignment.py:68` | "(R2)" in `load_pair` |
  | `utils/alignment.py:81` | "R8: target word order settles ownership…" |
  | `utils/alignment.py:115` | "(R15)" in `_join` |
  | `utils/alignment.py:130` | "(R15)" in `_source_phrase` |
  | `utils/alignment.py:171,185,211` | "(R5)", "(R11)", "R5 source order:" in comments |
  | `steps/alignment.py` | module docstring points at the design doc — that is a cross-reference and is *allowed*; the rule welcomes a pointer to where the reasoning lives |
  | `utils/alignment.py:1-9` | same: the module docstring's pointer stays |

  **What to keep:** the sentence saying what the function does, and a bare cross-reference to
  `project/plans/design-scripture-alignments.md`. **What goes:** the ruling numbers inline and
  any sentence explaining *why* a choice was made. The rule is explicit that a pointer to where
  the reasoning lives is the remedy, not the violation.

  **Verify after:** `hatch run pytest tests/test_docstrings_say_what_not_why.py -q` → green, and
  `hatch run pytest tests/test_alignment.py -q` → still 21 passed.
- **`data/alignment-pairs.json` is declared and shipped but nothing reads it.** The step resolves
  pairs through the registered-resource store, which is what the tests exercise. Wiring the
  declaration is the remaining work, and it is where D9's normalisation belongs.
- **Nothing has run against the real corpus.** Tests are synthetic by design so they pass on a
  fresh clone. `SBLGNT-BSB` has never been through this code.
- **`tmp/gen_alignment_demo.py:8` hardcodes a path** — the worked-examples generator. Throwaway,
  but `tmp/alignment-worked-examples.md` tells the reader to regenerate with it.
- **Three issue drafts written and never posted:** the `_unlock_sp_dir` broken-symlink crash (in
  the conversation only — see below), and nothing else outstanding.

## Decisions settled — do not reopen

**Sixteen rulings, R1–R16, are in `project/plans/design-scripture-alignments.md` §2 with the
Captain's own words.** Read that rather than re-deriving. The four most likely to be accidentally
contradicted:

- **R8** — a shared target word: **no token appears in two spans' text**, decided by target
  order; but the constituent list shows it in **both**. Two outputs, two rules.
- **R11** — **two** kinds of nothing, not three: `[]` (asked, nothing aligned) and `null` (ids not
  in the alignment file). A "third kind" was a populated field and was removed.
- **R16** — the request takes a **set**: the alignments, the aligned text, or both.
- **Keys are `source:`/`target:`, not `from:`/`to:`** — `from` is a Python keyword and `Step`
  cannot expose it. R4's substance is unchanged; the spelling is Scripture Burrito's own `roles`.

**Vocabulary: nine coined terms were retired** — `absorbed`, `refused`, `foreign`, `partition`,
`clean run`, `gap`, `interleaved`, `window`, `extent`. Say the phrase, not a noun.
`rule 3` in `docs/ai-context/project/rules.md` now records why. **Do not reintroduce them.**

## Open decisions awaiting the Captain

1. **Revert `bible_data.py`?** And should that module exist at all?
2. **D9** — §5 of the alignment design. Portuguese joins 0 of 99,258 because `JFA11` omits the
   `n` prefix. Normalising on read is forced; what a client gets in *raw records* is the decision.
3. **The store and the catalog disagree on ids.** `data/resources.json` declares `acai` and
   `macula-hebrew`; `~/.sp/datasets/` holds `ACAI` and `macula-hebrew-macula-hebrew`. His store,
   his catalog.

## Do NOT

- **Do not treat these three test failures as yours.** They are pre-existing:
  `test_plan_docs_index` × 2 (the Captain's own staged plan docs cite no issue) and
  `test_product_name_in_prose` (a collab file from 2026-09-09, unmodified in git).
- **Do not run two pytest processes at once.** They share `tmp/pytest` and corrupt each other.
  This session invalidated three suite runs that way. If it wedges with an `INTERNALERROR` about
  `os.stat`, the fix is `chmod -R u+w tmp/pytest && rm -rf tmp/pytest` — plain `rm` fails because
  `sp` locks the store read-only.
- **Do not use `Clear/internal-Alignments`.** Captain, 2026-09-14: only the public
  `Clear/Alignments` is registered for general use. R14: the per-language repos are
  copyright-restricted.
- **Do not decide the open questions above.** This session's repeated failure was answering
  design questions instead of bringing them. See the correction list in the conversation.
- **Do not push anything.** The Portuguese fix in `Clear/Alignments` is already committed and
  pushed by the Captain on `fix/portuguese-source-id-prefix`; nothing else is owed there.

## Key files & links

- `project/TODO.md` — **the queue.** Everything not session residue.
- `project/plans/design-scripture-alignments.md` — R1–R16, measurements with re-run commands,
  D9 open. **Read first.**
- `project/plans/design-operations-in-the-pipeline-language.md` — #241, the language question.
  Concluded #238 is *not* blocked on it.
- `tmp/alignment-worked-examples.md` — Luke 1:1–4, Ephesians 1:3–14, Psalm 23:1–4, Ruth 1:1–4.
- Issues opened today: **#238** alignment, **#239** resolver kludge, **#240** hyphen naming,
  **#241** operations in the language. Against `Clear-Bible/Alignments`: **#12**, **#13**, **#14**.
- An unfiled issue draft — `_unlock_sp_dir` crashes on a broken symlink, reachable from
  `sp doctor` and `sp init`, not just tests — exists only in this session's conversation.
