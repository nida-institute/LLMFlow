# HANDOFF — 2026-09-07

## ▶ NEXT ACTION

**Nothing is uncommitted and nothing is half-built. Pick a thread; here they are ranked.**

`dev` is at `f061917`, pushed, in sync with `origin/dev`. Working tree clean. Suite green.

1. **Workshop readiness** — `TODO.md:188` calls it the *"main next goal"* and names three concrete
   blockers in `cli_utils.py` (below). **Verify the timing before acting**: the previous handoff
   said mentoring was the week of 2026-09-08, but that date appears nowhere in `TODO.md` and this
   session could not source it. Ask the Captain rather than assume it has passed or is imminent.
2. **`discourse-flow` asked for lint to check `function` step inputs** —
   `collab/discourse-flow/2026-09-07-lint-does-not-check-function-step-inputs.md`, arrived today,
   **unanswered**. Small, static, and the machinery exists: `steps/function.py:30` already calls
   `inspect.signature` at runtime; `utils/linter.py:298` restricts contract checking to `type: llm`.
   It also bears on work just shipped — `verse_ranges.select` is called through a `function` step,
   so a wrong input name passes lint today.
3. **Paratext #222** — design complete, no decisions left, **nothing built**. Four ordinary pieces
   in `design-paratext-versification.md` §7.
4. **BaseX #38** — **blocked upstream** on `nida-institute/awesome-biblical-data#5`. Do not start.

---

## Where the repository is

| | |
|---|---|
| `dev` | `f061917`, pushed, in sync. **9 commits ahead of `main`**; all x.27 work is here, unreleased |
| `main` | `5822104`, pushed |
| tag | `v0.2.1.26` on `0edb6d1`; PyPI at `0.2.1.26` |
| `pyproject.toml` | `0.2.1.26` — stays at the released version during development, by ruling |
| suite | **4986 passed, 25 skipped, 26 deselected**, exit 0 |
| `ruff check src/` | clean |

**Verify:** `git status --short --branch`, `hatch run pytest -q -m "not integration"`,
`ruff check src/`.

---

## x.27 — five of six shipped

| # | Feature | Issue | State |
|---|---|---|---|
| 1 | Hebrew resolves in `include: [discourse]` | #230 | **SHIPPED** |
| 2 | Copy forcing | #230 | **SHIPPED** — `src/llmflow/field_roles.py` |
| 3 | Paratext via `type: scripture` | #222 | **designed, unbuilt** — see NEXT ACTION 3 |
| 4 | Comparing verse references | #169 | **SHIPPED** — `src/llmflow/utils/verse_ranges.py` |
| 5 | `include: [syntax]` | #227 | **SHIPPED**, plus the constituent attributes. **GitHub issue still open — closing it is the Captain's** |
| 6 | BaseX | #38 | **blocked upstream** |

**Not in x.27, by ruling:** ACAI entity data (the largest gap), Lowfat beyond #227, lexicons and
semantic domains.

### Also outstanding, not features

- **Guard refactor** — move the shared/engine-only/rewritten classification into
  `data/helm-sync.yaml`; `EXPECTED_DISCIPLINES` and `SHARED_WITH_HELM`/`ENGINE_ONLY`/`REWRITTEN`
  read it; generate `disciplines/README.md`. Adding one discipline costs five edits across four
  files. **The Captain gave the word; never started.**
- **`github-authority.md`** — add the "show the body before running the command" rule. Home
  undecided: shared discipline (reaches every project and Human at the Helm, costs a
  `helm-sync.yaml` hash update and a twin commit) or a narrower `CLAUDE.md` line.
- **`RELEASE_CHECKLIST.md` §12 is wrong** and fails four guards. Unclaimed.
- **`#204`'s recorded cause is false** and `TODO.md:201` says so — *"needs correcting before
  anything is built against it."* Unclaimed, and it sits under the workshop goal.
- **`sp lint` checks the prompt contract in one direction only** — added to `TODO.md` by the
  Captain's direction. `validate_gpt_body_declares_all_vars` computes `body_vars - declared`
  (`linter.py:214`) and never the reverse, so a `requires:` entry the body never uses passes
  silently, while every calling step is still obliged to supply it. Error or warning is unruled.
- **The shell/file-tool rules have no teeth** — also added to `TODO.md` this session. The rule
  offers no ask-first path, so an agent with a genuine reason either fails the task or violates
  silently; the cost lands on the Captain's attention. Which file owns the change is undecided.
- **`query_macula_hebrew` / `query_macula_greek`** — both broken, both uncalled. Fix or delete.
- **`load_db.py` has four defects**, all recorded in `design-basex-collections.md` §6 and none
  fixed: no `INTPARSE` (so loading `macula-greek/SBLGNT/lowfat` **fails on Luke**, element depth
  101), no `XINCLUDE`, no `DIACRITICS` (the full-text index folds τίς and τις together), and
  `f"CREATE DB {db_name} {source}"` interpolates unquoted so **no path with a space can load** —
  including `Paratext 9 Projects/`.

---

## ⚠️ Before trusting any record in this repository

**Records asserting false state is this repository's dominant defect class.** Verify against code,
tests and CI. Found false this session alone:

| record | claimed | actual |
|---|---|---|
| previous `HANDOFF.md` | mentoring is the week of 2026-09-08 | **unsourced.** Not in `TODO.md`; inherited from an earlier handoff and nearly propagated a third time |
| `design-verse-range-operations.md` §§182–204 | the verse-count table blocks `adjacent`/`verse_count` | false since versification shipped — 95 books, six schemes |
| `data/book-names.json` | `pss` is an alias of Psalms | it is **also** the USFM code for Psalms of Solomon. Fixed |
| `include-families.json` | `syntax` "Not implemented" | it had shipped. Fixed |
| `#204` | `sp init` creates no `CLAUDE.md` | false — `cli_utils.py:756-761` |
| `#38` | closed as completed 2026-08-26 | never implemented; reopened |

`test_record_closure_claims.py` cannot catch this class — it scans for "closed by `<sha>`", and a
claim made in prose never takes that form.

---

## Settled this session — do not reopen

**Verse ranges (#169)** — books are distinct documents, so ordinals are book-local and the schemes
disagreeing on book inventory stops mattering; `overlaps` means the colloquial thing (shares at
least one verse, containment and equality included) and Allen's strict case is deliberately
unnamed, which is what keeps the relation partition internal; `touches` not `meets`; both `select`
and the predicates, because YAML has no comprehension and **filter was the one missing combinator**
(`for-each`+`append_to` is map, `append_to` is fold, `if` is the conditional); module
`verse_ranges` not `verse_algebra`; bare predicate names; point-set operations out. Full reasoning
in `design-verse-regions.md`.

**`syntax` attributes** — groups carry `class, role, articular, head, type, clauseType, junction,
predication`; leaves carry `class, role, junction, discontinuous`. `rule` and `nodeId` are the
parser's bookkeeping, not facts about the constituent. `clauseType` is **the one field name that is
not the source's verbatim** (Greek `clauseType`, Hebrew `clausetype`). Absence is the negative for
`articular`, `discontinuous`, `head`.

**Participant reference** — `referent` is Greek-only, `participantref` Hebrew-only, and they are
**not** unified: declaring two independently-produced corpora equivalent is an editorial judgment
about someone else's data. Values are **declared, not repaired** — the rule lives in
`notes.participant_ids`.

**Versification merges** — a run of verses may be one verse in another scheme, and both directions
occur, so `to_hub` holds a **list** per verse. Five of seven previously-skipped shipped entries now
resolve; `rso`'s five-to-six and `vul`'s backwards range stay refused, because neither says where a
verse went.

**Paratext** — the project identifies its own versification; the container reports the **project
id** meaning *the versification the project specified*, whether standard or custom; **no generated
scheme file**, because `custom.vrs` is the declaration and a derived `.json` beside it is the second
source the template machinery exists to prevent.

**BaseX** — names come from the catalog, not a scheme the engine constructs; only declared subtrees
load; one identifier per repository with its corpora as `provides` entries; the registry carries a
SHA and a load date, in fields that **already exist** and that `sp doctor` already reports as
unknown.

---

## Landmines

- **Never write to `docs/ai-context/` by hand.** Files there are `policy: generated`. Edit the
  template in `src/llmflow/templates/` and sync. `sp doctor` is the sanctioned sync **and is banned
  in this repo** until #210/#211, so the practical route is a byte copy —
  `test_template_layout.py:106` holds them identical.
- **`data/ai-rules.yaml`, `CLAUDE.md`, `~/.sp` and `~/.claude` are the Captain's.** `~/.sp` is
  read-only by design; never unlock it.
- **`data/resources.json` is vendored** from `nida-institute/awesome-biblical-data`. Editing it here
  edits a copy. It is currently identical to upstream — keep it that way.
- **Both consumer repos install this working tree editable**, so `dev` *is* their engine with no
  pull. Keep the tree consistent between *commits*, not between edits.
- **Two pytest runs collide** on `tmp/pytest/` and produce an `INTERNALERROR`. One at a time — and
  **do not edit `CHANGELOG.md`, `HANDOFF.md`, `TODO.md` or `project/plans/` while a run is in
  flight**; guards read them at test time and this session raced itself three times.
- **`ruff check src/ --fix` deleted `llmflow.runner`'s re-export surface** twice, breaking the suite
  at *import* time. Now in `__all__`, guarded by `tests/test_runner_reexports.py`.
- **The GUI has two copies.** `build_gui.py` copies `gui/backend/{server,executor}.py` over
  `src/llmflow/gui/`.
- **Never run `sp run`** (costs money) or **`sp doctor`** (unsafe here until #210/#211).
- **Prose is guarded.** `test_product_name_in_prose.py` forbids the deprecated product name in
  `.md`; a docstring guard forbids dates, hashes and "the Captain" in source; the CHANGELOG guard
  forbids commit hashes. All three fired on this session's drafts.
- **Use BaseX/XQuery for XML and `jq` for JSON**, not throwaway Python — the Captain's direction,
  and heredoc Python is sanctioned as a *form*, not as a reason to reach for it. A verification
  worth doing is worth doing as a test.
- **Shell:** one command per call, no `cd`, no chaining with `;` or `&&` — anything else matches no
  permission rule and prompts.

---

## Consumer threads

**`discourse-flow`** — three threads, one **unanswered** (NEXT ACTION 2). The other two are
answered in full: `2026-09-06-syntax-payload-and-registration.md` (the constituent attributes,
where `discontinuous` turned out to be our own gap — 6,038 Greek words in 4,404 of 8,010 sentences,
the source's own marking of the phenomenon `syntax` is standoff *for*) and
`2026-09-06-participant-reference.md`.

**`ears-to-hear`** — **three defects reported to nobody yet.** `division_lookup.py` discards the
book (so `Mark 1:1-5` and `John 1:1-5` compare as overlapping), returns on first match (so a
passage spanning two divisions silently gets one), and catches `ValueError` to return `False` (so an
unreadable reference reports as overlapping nothing). All three are in `design-verse-regions.md`
§1.1. **Telling them is unclaimed.**

**C-level** — `collab/clevel/2026-09-04-what-the-engine-work-can-and-cannot-tell-you.md`.

---

## Key files

- `project/plans/design-verse-regions.md` — #169 as built; **§10 is what contact with the code
  changed**
- `project/plans/design-paratext-versification.md` — #222; §7 has no open decisions
- `project/plans/design-basex-collections.md` — #38/#52/#49; **§8 item 0 is the upstream blocker**;
  §6 lists the four `load_db.py` defects
- `src/llmflow/utils/verse_ranges.py`, `syntax.py`, `discourse.py`, `versification.py`
- `data/include-families.json` — the seven families, and `notes.participant_ids`
- `data/ai-rules.yaml` — 38 rules, each with `enforcement` and `scope`
- `project/TODO.md:188` — workshop readiness, with the false `#204` cause called out at :201
