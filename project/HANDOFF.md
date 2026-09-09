# HANDOFF — 2026-09-09

## ▶ NEXT ACTION

**Commit the working tree. Six of seven groups are still uncommitted.**
The Captain committed group 1 himself as `ce37401`. The remaining groups are listed below with
their subjects; the full messages were composed in the session that ended and are *not* in this
file, so recompose the bodies from the diffs rather than guessing at them. Then, in order:

1. **Write the CHANGELOG entries first.** `## Unreleased` carries nothing from this session, and
   `rule plans-are-temporary` makes the CHANGELOG the durable home for a ruling. Four rulings
   landed today and none is recorded there: the defect-log channels, the unused-`requires:`
   verdict, `plans-are-temporary` itself, and the two new registration commands.
   **Verify:** `grep -n "defect" CHANGELOG.md` returns nothing today.
2. **Commit the seven groups.**
3. **Thread 4 — BaseX #38.** Unstarted, and still the last of the order the Captain set (2, 3, 4).
   His words: *"I don't know if there are still BaseX blockers. If so, I do not know what they
   are."* So the work is **not** to build: read `project/plans/design-basex-collections.md` §8
   item 0, check `gh issue view 5 --repo nida-institute/awesome-biblical-data` is still open, and
   **explain the blocker to him in his vocabulary before proposing anything**
   (`rule transfer-the-expertise`). Do not trust the recorded blocker — see the false-records
   table below.

**Second, and cheap:** `sil-translator-notes` does not lint. Two of its prompts still declare the
retired `optional:` key (#228). Their repo, their commit.

---

## Where the repository is

| | |
|---|---|
| `dev` | `ce37401`, **1 ahead of `origin/dev` — unpushed**. 18 commits ahead of `main` |
| working tree | **DIRTY — 14 modified, 8 untracked.** Six of the seven groups below |
| `pyproject.toml` | `0.2.1.26`. x.27 is unreleased |
| suite | **5289 passed, 25 skipped, 28 deselected**, exit 0 |
| `ruff check src/` | clean. `ruff check tests/` has 444 pre-existing findings — not this session's |

**Verify:** `git status --short --branch`, `hatch run pytest -q -p no:randomly -m "not integration"`,
`ruff check src/`.

### The seven commits — one made, six to make

| # | subject | files |
|---|---|---|
| 1 | `feat(defects): a run records what it noticed without failing` | **DONE — `ce37401`.** It also swept in `docs/index.json` |
| 2 | `feat(prompts): warn when a prompt's example is the passage under test` | `utils/prompt_hygiene.py`, `utils/versification.py`, `steps/llm.py`, `tests/test_example_contamination.py` |
| 3 | `feat(lint): warn on unused requires, and stop lint from poisoning sys.modules` | `utils/linter.py`, `tests/test_unused_requires.py`, `tests/test_lint_function_signatures.py` |
| 4 | `feat(cli): sp dataset add and sp resource set` | `cli.py`, `resources.py`, `tests/test_registration_commands.py` |
| 5 | `test(guard): a test that calls a live model is marked integration` | `tests/test_paid_calls_are_marked_integration.py`, `tests/test_schema_file.py` |
| 6 | `docs(rules): a working document has a death; a ruling does not` | `data/ai-rules.yaml`, `docs/ai-context/sp/rules.md`, `templates/sp/disciplines/workflow.md`, `data/helm-sync.yaml`, `tests/test_ticked_boxes_carry_evidence.py`, `tests/test_shell_rules_stay_in_step.py`, `project/plans/design-one-working-document.md`, `project/plans/README.md` |
| 7 | `docs(project): handoff for 2026-09-09` | `project/HANDOFF.md`, `project/TODO.md` |

Group 3 carries two subjects because both changes live in `linter.py` and separating them needs
`git add -p`. Split it only if the Captain asks.

---

## What was built this session

Only the defect log is committed; the rest is in the working tree.

| thread | state | verify |
|---|---|---|
| Defect log (#232) | **built and committed (`ce37401`).** Reserved `defects` key + a handler on the `llmflow` logger; written to `defects.json` under `intermediate_file_directory` | `hatch run pytest tests/test_defect_log.py` — 26 tests |
| Example contamination | **built.** Warns when a prompt's example overlaps the passage under test | `hatch run pytest tests/test_example_contamination.py` — 16 tests |
| Unused `requires:` | **built**, as a warning | `hatch run pytest tests/test_unused_requires.py` — 9 tests |
| `sp dataset add` / `sp resource set` | **built** | `hatch run pytest tests/test_registration_commands.py` — 12 tests |
| Paid calls in the ordinary run | **fixed and guarded.** Was making 6 API calls per `-m "not integration"` run | `hatch run pytest tests/test_paid_calls_are_marked_integration.py` — 3 tests |
| `plans-are-temporary` | **ruled and written** into `data/ai-rules.yaml` | `hatch run pytest tests/test_ticked_boxes_carry_evidence.py` — 4 tests |
| BaseX #38 | **not started** — the NEXT ACTION | — |

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
| 6 | BaseX | #38 | **blocked, unverified** — the NEXT ACTION |

**Added to x.27 this session, none of it previously planned:** the defect log (#232), the
contamination guard, the unused-`requires:` warning, `sp dataset add`, `sp resource set`, the
integration-marker guard, and `rule plans-are-temporary`.

**Left for the release itself:** bump `pyproject.toml` to `0.2.1.27`, rename the CHANGELOG's
`## Unreleased` heading (guards require the literal word until then —
`test_changelog_is_not_a_transcript.py:72` and `test_changelog_covers_the_version.py`), and open
the `dev` → `main` PR (closes #222, #227).

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

Nothing new was found false this session, because nothing was taken on trust. The standing list:

| record | claimed | actual |
|---|---|---|
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
- `project/plans/design-basex-collections.md` — **§8 item 0 is the NEXT ACTION's blocker**
- `project/TODO.md` — the open rulings
- `CHANGELOG.md` — **`## Unreleased` is missing this session's four rulings**
