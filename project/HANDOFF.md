# HANDOFF — 2026-09-09

## ▶ NEXT ACTION

**Release 0.2.1.27.** All the feature work is committed and pushed; what is left is the release
itself, in this order:

1. **Bump `pyproject.toml`** — it still reads `0.2.1.26`.
2. **Rename the CHANGELOG heading** `## Unreleased` → `## 0.2.1.27 — <date>`. Do this *after* the
   bump, because guards require the literal word `Unreleased` until then
   (`test_changelog_is_not_a_transcript.py:72`, `test_changelog_covers_the_version.py`).
3. **Open the `dev` → `main` PR.** None is open; `dev` is 24 commits ahead. It closes #222 and
   #227. `project/RELEASE_CHECKLIST.md` §6 opens it; §4–5 are then checked against the build that
   opening it started; §7–9 tag the *merge* commit and watch all five `release.yml` jobs.

**Before the PR, two records need correcting — both are false as they stand:**

- **`#38` carries a `done` label** reading *"Ready to be closed - implementation complete."* The
  query half is complete (#49, closed, `steps/basex.py`); the naming scheme the issue is actually
  about has no implementation, and `sp setup-db` (#52) does not exist in `cli.py`. As labelled,
  the issue invites someone to close it and ship a scheme that was never built. Changing a label
  is the Captain's act, not an agent's.
- **BaseX is scheduled for 0.2.1.28**, not carried in x.27 as "blocked" (moved 2026-09-09).
  Nothing in this release depends on it. `project/TODO.md` holds the ordered work list; see
  "BaseX, measured" below for why it is much further from done than the label suggests.

**Third, and cheap:** `sil-translator-notes` does not lint. Two of its prompts still declare the
retired `optional:` key (#228). Their repo, their commit.

---

## Where the repository is

| | |
|---|---|
| `dev` | in sync with `origin/dev`. **24 commits ahead of `main`** |
| working tree | the CHANGELOG entries and the doc sync for the release; nothing else outstanding |
| `pyproject.toml` | `0.2.1.26` — **not yet bumped**. x.27 is unreleased |
| suite | **5289 passed, 25 skipped, 28 deselected**, exit 0 |
| `ruff check src/` | clean. `ruff check tests/` has 444 pre-existing findings — not from this work |

**Verify:** `git status --short --branch`, `hatch run pytest -q -p no:randomly -m "not integration"`,
`ruff check src/`.

### The seven commits, all pushed

```
9c1d53b docs(project): handoff for 2026-09-08
f90a926 docs(rules): a working document has a death; a ruling does not
bbbe060 test(guard): a test that calls a live model is marked integration
e8f2e21 feat(cli): sp dataset add and sp resource set
570e33d feat(lint): warn on unused requires, and stop lint from poisoning sys.modules
d319c52 feat(prompts): warn when a prompt's example is the passage under test
ce37401 feat(defects): a run records what it noticed without failing
```

Five of the six subjects carry two leading spaces, a paste artifact. They are pushed, so removing
them means a force-push to a shared branch — deliberately left alone.

---

## What was built

All committed and pushed.

| thread | state | verify |
|---|---|---|
| Defect log (#232) | **built and committed (`ce37401`).** Reserved `defects` key + a handler on the `llmflow` logger; written to `defects.json` under `intermediate_file_directory` | `hatch run pytest tests/test_defect_log.py` — 26 tests |
| Example contamination | **built.** Warns when a prompt's example overlaps the passage under test | `hatch run pytest tests/test_example_contamination.py` — 16 tests |
| Unused `requires:` | **built**, as a warning | `hatch run pytest tests/test_unused_requires.py` — 9 tests |
| `sp dataset add` / `sp resource set` | **built** | `hatch run pytest tests/test_registration_commands.py` — 12 tests |
| Paid calls in the ordinary run | **fixed and guarded.** Was making 6 API calls per `-m "not integration"` run | `hatch run pytest tests/test_paid_calls_are_marked_integration.py` — 3 tests |
| `plans-are-temporary` | **ruled and written** into `data/ai-rules.yaml` | `hatch run pytest tests/test_ticked_boxes_carry_evidence.py` — 4 tests |
| CHANGELOG + doc sync | **written**, uncommitted at the time this file was last saved | `grep -n "defects" docs/llmflow-language.md` |
| BaseX #38 | **not release work.** See below | — |

### Three faults the defect log's end-to-end test found

Worth knowing, because each was invisible to unit tests and each made the log silently empty:

- The handler was attached **above** the block that calls `Logger.reset()`, and that reset clears
  every handler on `llmflow`. It runs under exactly the condition that makes the log worth
  keeping — a declared `intermediate_file_directory`. So the runs that write `defects.json` were
  the runs whose log was empty. The reset is `runner.py:651`; the attach moved below it, to
  `runner.py:670`.
- Teardown named `llmflow.defects` where the attach named `llmflow`. Every run leaked its handler.
- Nothing removed the handler when a run **failed**, so the next run's warnings would be filed
  into the dead run's log. Now a `finally`.

---

## x.27 — what is done, and what is left

| # | Feature | Issue | State |
|---|---|---|---|
| 1 | Hebrew in `include: [discourse]` | #230 | SHIPPED |
| 2 | Copy forcing | #230 | SHIPPED |
| 3 | Paratext `custom.vrs` | #222 | SHIPPED — `8e8b1e1` |
| 4 | Comparing verse references | #169 | SHIPPED |
| 5 | `include: [syntax]` | #227 | SHIPPED; issue closes at the `dev` → `main` merge |
| 6 | BaseX | #38 | **moved to 0.2.1.28** (2026-09-09). Blocked upstream; nothing in x.27 depends on it |

**Added to x.27 unplanned:** the defect log (#232), the contamination guard, the
unused-`requires:` warning, `sp dataset add`, `sp resource set`, the integration-marker guard, and
`rule plans-are-temporary`.

### BaseX, measured — now 0.2.1.28

Scheduled out of x.27 on 2026-09-09. The full breakdown and the ordered work list live in
`project/TODO.md` under *🗄️ BaseX collections*; this is the short form.

The ratio is the point: the half that ships is the half that was never blocked.

| piece | issue | state |
|---|---|---|
| `type: basex` — run XQuery against an existing database | #49 | **CLOSED, shipping.** `src/llmflow/steps/basex.py`, three test files |
| `sp setup-db` — load a corpus into BaseX under a canonical name | #52 | **OPEN, no code.** `grep -n "setup-db" src/llmflow/cli.py` returns nothing |
| collection naming from the catalog | #38 | **OPEN, no code.** Design is `Status: proposal … Nothing is built` |
| `provides` can describe a treebank or a lexicon | `awesome-biblical-data#5` | **OPEN, zero comments**, untouched since it was raised 2026-09-07 |

The upstream issue is not a formality. `provides` requires `versification`, `canon` and `language`
of every entry, so **only a scripture text can be declared** — and the catalog bears that out:
3 of 70 entries carry a `provides` block, and all three are Bibles (`WLC`, `SBLGNT`, `BSB`). The
feature exists to load treebanks and lexicons, and the catalog cannot currently name one. Since the
first design ruling is *"names come from the catalog"*, there is no input to build against.

**Verify:** `python3 -c "import json;d=json.load(open('data/resources.json'));print(len(d), sum(1 for e in d if e.get('provides')))"` → `70 3`.

So the remaining work is, in order: a schema change in another repository; editorial catalog work
across up to 67 entries, which is the maintainer's judgment and not code; seven unruled decisions
in §8 of the design (LANG, FTINDEX, a raw database name, the local root, and three more); and only
then `sp setup-db`. That is not a tail to finish before a release, which is why it is x.28.

**Left for the release itself:** the three steps in NEXT ACTION. The CHANGELOG and the prose docs
are done — `## Unreleased` now carries all five of this cycle's late additions, and
`docs/llmflow-language.md` documents both the reserved `defects` key and the two new registration
commands.

---

## In flight elsewhere — verified 2026-09-09

Each is that repository's own commit to make. **No `edition:` key remains in any consumer's
pipelines** — checked with `grep -rn "^\s*edition:" pipelines/` in both, which returns nothing.

| repo | uncommitted | what |
|---|---|---|
| `discourse-flow` | `collab/sp/2026-09-08-old-documents-are-deleted-not-sifted.md` (modified). The three `pipelines/` files are **already committed** with `resource:` | the report on deleting old working documents; they have edited our report in place |
| `ears-to-hear` | `collab/` is **entirely untracked** — the directory has never been committed there | the same report; it will be invisible to them until they add it |
| `sil-translator-notes` | `pipelines/translators-notes.yaml`, `HANDOFF.md` | the `resource:` rename, done but uncommitted |
| `human-at-the-helm` | `disciplines/workflow.md` | `ask-for-the-exception` **and** the new "Completion Is Claimed With Evidence" section. `data/helm-sync.yaml` here records the hash that expects both |

`discourse-flow` carries 76 uncommitted files in total and `ears-to-hear` 35 — most of it theirs,
and most of it the document pile the eight-day rule addresses.

**Verify:** `git -C ~/github/nida-institute/discourse-flow status --short`.

---

## Decisions awaiting the Captain

Three of the five the previous handoff listed are now ruled and built. What remains:

1. **Where the contamination prohibition lives as a *principle*.** The guard is built here. The
   general rule — *an LLM must not use the data under test as a prompt example* — was proposed for
   Human at the Helm, since it is not specific to this engine. Unruled.
2. **`CLAUDE.md`'s local copy of the shell rules** — whether it stays as it is now that
   `data/ai-rules.yaml` is authoritative. His file; his call.
3. **D3: remove `project/audits/`.** Measured at **21 files** — a catalog entry, a shipped
   template, `sp/audits-pattern.md` and its mirror, two audit skills, three disciplines (one
   Helm-shared, so a twin commit), the `file-organisation` rule, two tests, four docs. Not started.
4. **`project/rolling/` and `project/scratchpad/`** — the directory split the Captain proposed so
   accumulating and rolling documents are distinguishable by location rather than by an
   unwritten rule. Designed in `design-one-working-document.md`; not built.
5. **The `done` label on #38.** It reads "implementation complete" over an issue whose subject has
   no implementation. Removing or re-wording a label on an issue is his act, not an agent's.

## Settled — do not reopen

- **Defect-log channels (2026-09-08).** The reserved `defects` key as the channel, so the record
  is ordinary step output and every step type can write one; a handler on the `llmflow` logger as
  the Python convenience; automatic file under `intermediate_file_directory` plus an end-of-run
  summary. `[]` and absence differ — an empty log means the run looked.
- **An unused `requires:` entry is a warning, not an error.** The run it produces is correct.
- **A working document dies at eight days; a ruling is permanent until overruled.** *"after a work
  week, it is usually either implemented or obsolete"*, *"rulings are permanent until overruled"*,
  and *"but ask the Captain before deleting"* — the deletion is never the AI's to make.
- **`resource`, not `edition`.** A **dataset** is an obtainable body of data; a **resource** is a
  readable text inside one.
- **`~/.sp` is never edited by hand.** *"you may never edit ~/.sp. period."* The template tree at
  `src/llmflow/templates/sp/` is the source; `sp` copies from it.
- **A push is its own act, requested every time**, naming remote and branch.

---

## ⚠️ Records that were false — still the dominant defect class

One new, and it is the first found on **GitHub** rather than in a design file — which matters,
because the issue tracker is the record a release is planned from.

| record | claimed | actual |
|---|---|---|
| **`#38`'s `done` label** | "Ready to be closed - implementation complete" | the issue's subject — collection naming — has no implementation, and `sp setup-db` does not exist. Only #49, a different issue, is complete |
| a previous `HANDOFF.md` | BaseX is "blocked, unverified" | the blocker is real and verified; but the query half ships, so "blocked" alone misdescribes it in the other direction |
| `TODO.md` #204 | `templates/` missing three files | all present under `templates/sp/` |
| `design-paratext-versification.md` §2 | three `custom.vrs` constructs | **four** — `partialVerses` was absent |
| the same, §2 | five files read | 66 exist |
| a previous `HANDOFF.md` | `RELEASE_CHECKLIST.md` §12 "fails four guards" | **unverified** — no test references `RELEASE_CHECKLIST`, and the suite is green |
| `discourse-flow`'s lint thread | a signature is reachable "without executing anything" | false; the import is three lines above the line they cited |

---

## Landmines

- **Do not evict a module from `sys.modules` on a "lives outside the working directory" test.**
  A first cut of the lint import fix treated any package not at `./name` as foreign, which makes
  **`llmflow` itself** foreign — it loads from `src/llmflow`. Evicting it mid-suite broke **84
  tests**, and the symptom is misleading: mocks report `Called 0 times` because every later import
  gets a fresh module object no patch knows about. `_is_sibling_of` in `linter.py` is deliberately
  exact; keep it that way.
- **`Logger.reset()` clears every handler on the `llmflow` logger** (`modules/logger.py:35`).
  Anything attached before `runner.py:651` is silently gone. This is what made the defect log
  empty.
- **The blanket rename is still the standing hazard.** A search-and-replace across the suite
  destroyed the one test whose subject was the retired word, rewrote a mapping's string literal
  into a tautology, and rewrote a **generated** file. Protect string literals and generated
  artifacts; never rename a file whose subject is the old name.
- **A wrapped multi-line paste breaks in the Captain's terminal.** A `git add` with backslash
  continuations ran its continuation lines as commands; an indented heredoc never terminated
  (Ctrl-C exits). **Give one short single-line command at a time.**
- **`output.txt` appeared untracked in the repo root** with the contents `Test content`, and was
  deleted 2026-09-09 at the Captain's direction. A full suite run does **not** recreate it, and no
  test was found that writes a bare relative `output.txt` — `steps/save.py` defaults to that name
  when a save step declares no path, so the likeliest source is a manual invocation. If it returns,
  that default is where to look.
- **Never run `sp run`** (costs money) or **`sp doctor`** (unsafe until #210/#211).
- **Two pytest runs collide** on `tmp/pytest/`. One at a time.
- **`tmp/` is scanned by `test_install_instructions.py`.** Scratch files there fail the suite.
- **`project/` keeps the word "edition"** in ~197 places deliberately — records of decisions made
  when that was the word.

---

## Key files

- `src/llmflow/defects.py` — `DefectLog`, `defect_logging_handler`; `__deepcopy__` returns `self`
  so a `for-each` iteration writes into the one log
- `src/llmflow/utils/prompt_hygiene.py` — `contaminating_references`, `warn_about_contamination`
- `src/llmflow/utils/linter.py` — `_cwd_importable`, `_is_sibling_of`, `_drop_foreign_package`,
  `unused_requires_warnings`
- `project/plans/design-one-working-document.md` — the eight-day rule, and the
  `rolling`/`scratchpad` split that is designed but unbuilt
- `project/plans/design-basex-collections.md` — §8 item 0 is the upstream blocker; §8 items 1–7
  are the decisions that would still be open even if it cleared
- `project/RELEASE_CHECKLIST.md` — reordered 2026-09-09 so the sections run in the order they are
  done. §1–3 are pre-PR; §6 opens the PR; §4–5 read the build that opening it started; §7–9 tag
  and watch
- `project/TODO.md` — the open rulings
- `docs/llmflow-language.md` — the reserved `defects` key under *Saving Outputs*; `sp dataset add`
  and `sp resource set` under *Registering the text a pipeline names*
