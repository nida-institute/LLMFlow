# HANDOFF — 2026-08-28

Supersedes 2026-08-27. Nothing is committed; HEAD is `fcd2ec4` and **HEAD is internally
inconsistent** — see the next action.

---

## ▶ NEXT ACTION — commit the schema, because HEAD is broken without it

`fcd2ec4` was a partial commit. It landed `utils/file_io.py`, which accepts `tsv`, `csv`, `xml`,
`usj`, `usfm` and mime spellings as `saveas` formats — but **not** the schema, whose enum still
reads `['json', 'yaml', 'text', 'markdown', 'auto']`, and **not** the 34 tests covering it.

So at HEAD, `saveas: {path: out.tsv, format: tsv}` writes correctly and `sp lint` rejects it.

**Verify:** `git show HEAD:src/llmflow/schema/pipeline.schema.json` and look at
`$defs.SaveasConfig.properties.format.enum` — five values. Then `grep -c tsv` the same path for
`src/llmflow/utils/file_io.py` at HEAD — four hits.

**The commit and the push are the Captain's.** Commands are in the section below.

---

## In flight — four pieces, all uncommitted

| piece | files | note |
|---|---|---|
| **A. the other half of `fcd2ec4`** | `src/llmflow/schema/pipeline.schema.json`, `tests/test_saveas_format.py` | fixes the inconsistency above |
| **B. the joining rule** | 3 hunks in `utils/scripture.py`, `tests/test_scripture_tei.py`, part of `tests/test_scripture_text.py` | |
| **C. the `include:` families** | 8 hunks in `utils/scripture.py`, `data/include-families.json`, `tests/test_scripture_families.py`, `tests/test_scripture_include.py`, `pyproject.toml`, `.github/workflows/build.yml`, `project/plans/plan-scripture-step.md` | |
| **D. today's records** | `project/TODO.md`, `project/plans/design-reference-resolution.md`, `project/plans/README.md`, this file | |

**B and C share two files** (`utils/scripture.py`, `tests/test_scripture_text.py`). The hunks are
disjoint but interactive git flags are unavailable in-session, so they cannot be split from here.
Committing B+C together was recommended and is coherent: both are corrections to how
`scripture.py` reads Macula, from one session and the same measurements.

**Test state: 3540 passed, 25 skipped, 1 failed.** The failure is an MCP network timeout
(`test_verify_citations_integration.py` or `test_mcp.py`, whichever ran) — environmental, not
ours. Do not "fix" it by changing the test. Verify with
`hatch run pytest tests/ -q --ignore=tests/integration`.

## Uncommitted in other repositories

| where | what |
|---|---|
| `discourse-flow` | `collab/sp/2026-08-26-scripture-step-plan.md` (untracked) and two `sp` replies appended to `collab/sp/2026-08-27-discourse-family-is-built.md`. **Stage by name only** — that tree has four of the Captain's own modified files |
| `Clear/macula-greek` | `collab/sp/2026-08-28-inter-word-material.md`, in a third-party checkout that already carries someone's in-progress critical apparatus. **Do not commit there** |
| `~/.sp` | `versification/` and `projects/sil-translator-notes.yaml` untracked, `skills/load-context/SKILL.md` modified. **Report with the diff, never commit.** Bare repo at `~/.sp-git`, alias `spgit` |

## Decisions settled today — do not reopen

**The joining rule was ours to fix, not Macula's.** Macula Greek's convention is uniform: *a space
follows every non-space `after`*, and a word-final mark is carried in `text` instead — which is why
`ἀλλ’` appears in `text` with `·` in `after` in exactly 3 places. Reconstructing 7,330 verses under
that rule matches a printed SBLGNT in **7,197 (98.19%)** with **zero spacing differences**.
`JOINING_MARKS` had wrongly contained U+2019, spacing 1,221 Greek elisions against the printed
edition. Hebrew is different: 9 `after` values, 170,393 empty (morpheme continuation) and 42,569
maqqef, both correctly joining. Paseq and bare `ס`/`פ` stand *between* words and take a space on
each side — `STANDALONE_MARKS`.

**Families are edition-shaped; we do not merge ontologies.** *"Greek and Hebrew are different
languages. The analyses differ. We provide what Macula provides for each language."* And *"`morph`
is line noise."* `data/include-families.json` declares each family's columns across all editions;
a family emits whichever the edition has. Field names are the source's column names **verbatim**;
the only renames are `lemma` and `strong`, which are USX-defined attributes on a `w` node. A
per-word family requires `ids`, because the container keys by word id.
`IMPLEMENTED_FAMILIES` is now everything but `syntax`.

**Reference resolution — five questions closed.** Recorded in
`project/plans/design-reference-resolution.md` **§7 Resolved**, with the reasoning. Summary:
whole-chapter extent returns real counts not `999` (breaking change accepted); `maxVerses` comes
from the packaged copy at `llmflow/templates/sp/versification/`, never `~/.sp`; a book the scheme
lacks has three cases (one other scheme → use it; `ODA`/`PSS` → raise naming both; no lookup needed
→ parse, metadata says so, log warns); `filename_prefix` and `display_name` **keep** the resolved
verse, decided not deferred; **two** parsers, the third folding into the lean one via a part field.

**`syntax` is on hold** by explicit instruction. `frame` is one line (18.4% populated, both
editions); the lowfat tree is 10× payload, depth 18, and per-book in Greek against per-chapter in
Hebrew. Shipping `frame` as `syntax` and adding the tree later would raise every consumer's payload
10× without their pipeline changing.

## Open, awaiting the Captain

- **Two rules proposed for `docs/ai-context/project/rules.md`** in a `/stand-down` — one that a
  ruling is not an authorization and does not carry its sub-decisions, one about never writing into
  repositories we do not own. Exact content was shown in conversation; neither is written.
- **Whether to write `project/plans/tmp-context.md`** (stand-down step 3). Probably moot now that
  §7 of the design document carries the decisions.
- **The reference-resolution implementation is unstarted.** All decisions are recorded, so the
  scope declaration can be precise. Declare it and wait for sign-off before editing.

## Do NOT / landmines

- **Do not commit, push, or merge.** Run gates, write the message, hand over the command. A push is
  authorized per act and names remote and branch.
- **Do not modify `docs/ai-context/`, `CLAUDE.md`, or project memory.** Hard prohibitions.
- **Do not write after a `=>`.** Those are the Captain's, in both design documents.
- **Do not decide what the Captain has not decided.** This session was stood down for exactly that:
  an authorization to implement was treated as covering six further design decisions. When building
  reveals an unmade decision, stop and ask.
- **Do not create or modify files in another organisation's checkout.**
- **Looks like a next step but isn't:** implementing `syntax`, or splitting B from C with clever
  patch machinery.

## Key files & links

| | |
|---|---|
| `project/plans/design-reference-resolution.md` | §5 the Captain's `=>` answers, §7 the resolved set |
| `project/plans/plan-scripture-step.md` | §5 steps 5–7 record the families ruling |
| `data/include-families.json` | the family declaration — the whole design |
| `src/llmflow/utils/scripture.py:103` | `JOINING_MARKS`, `STANDALONE_MARKS`, and why U+2019 is absent |
| issues | **#218** reference resolution · **#219** saveas collision · **#220** pipeline header declaration · **#221** Burrito versification · **#222** Paratext `custom.vrs` (in `TODO.md` Active) |
| others | **#216** binary data, fixed and unreleased · **#211** done, closable |
