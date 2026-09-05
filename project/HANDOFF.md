# HANDOFF — 2026-09-05

## ▶ NEXT ACTION

**Commit the one uncommitted file, then get the Captain's rulings on the three open decisions
below.** All remaining x.27 work is decision-gated; nothing can start without them.

```bash
git add collab/discourse-flow/2026-09-03-hebrew-discourse-defects.md
git commit -F tmp/commit-collab-syntax-addendum.txt   # write this first; content is in the log
git push origin dev
```

The file is an addendum telling `discourse-flow` that `syntax` landed at `2af0c66` and giving them
the four consumer-facing facts the original reply lacked. Content approved in conversation; the
commit and push are the Captain's.

After the rulings: the **guard refactor** is the Captain's stated first item (see "x.27 cleanup"),
because everything touching disciplines pays the old cost until it lands.

---

## Where the repository actually is

| | |
|---|---|
| `dev` | `2af0c66`, pushed — `origin/dev` matches. **5 commits ahead of `main`**; all x.27 work is here and unreleased |
| `main` | `5822104`, pushed — `origin/main` matches |
| tag | `v0.2.1.26` on `0edb6d1` |
| PyPI | **`0.2.1.26` — published.** No longer outstanding |
| `pyproject.toml` | `0.2.1.26` (stays at the released version during development, by ruling) |
| CHANGELOG | `## Unreleased` has content; `## 0.2.1.26 — 2026-09-03` is dated and closed |
| suite | **4897 passed, 25 skipped, 26 deselected in 110s**, exit 0 — measured at `2af0c66` |
| `ruff check src/` | **clean** |

**Verify:** `git for-each-ref --format='%(refname:short) %(objectname:short)' refs/heads/dev
refs/heads/main refs/remotes/origin/dev refs/remotes/origin/main`, then
`hatch run pytest -q -m "not integration"` and `ruff check src/`. PyPI:
`curl -s https://pypi.org/pypi/scripture-pipelines/json | python3 -c "import json,sys;
print(json.load(sys.stdin)['info']['version'])"`.

---

## ⚠️ Read this before trusting any plan document in this repository

**Plan and TODO documents in this repository assert state that is false.** It is the dominant
defect class here — five were found false in one day. Verify against code, tests and CI, never
against the record. Two found since:

| document | claimed | actual |
|---|---|---|
| `design-verse-range-operations.md` §§182–204 | the verse-count table blocks `adjacent` and `verse_count` — "covers only Psalms, Luke, and John" | **false now.** `packaged_scheme("org").max_verses` has complete counts for **95 books** across six schemes (`eng lxx org rsc vul rso`). Verified 2026-09-05 |
| the previous `HANDOFF.md` | `include: [syntax]` is a shipped silent no-op | it **raised** `NotImplementedError`; now built |

`test_record_closure_claims.py` cannot catch this class — it scans for "closed by `<sha>`", and a
claim made only in prose never enters that form.

---

## x.27 — three of six shipped

| # | Feature | Issue | State |
|---|---|---|---|
| 1 | Hebrew resolves in `include: [discourse]` | #230 | **SHIPPED** `4858323`, `623916e`. Three fixes: word index read from `ref`'s `!N` rather than row position; maqqef (`־`) as a phrase separator; and the precedence chain — index first, then quote, then say you could not find it. Cross-verse span closings carried too |
| 2 | Copy forcing — declare evidence vs content | #230 | **SHIPPED** `4858323`. `src/llmflow/field_roles.py`, read by the linter |
| 3 | Paratext via `type: scripture` | #222 | **OPEN — blocked on a decision** |
| 4 | Comparing verse references | #169 | **OPEN — blocked on three decisions** |
| 5 | `include: [syntax]` | #227 | **SHIPPED** `2af0c66`. Both languages, measured end to end. **The GitHub issue is still open — closing it is the Captain's** |
| 6 | BaseX for all XML sources — *if it fits* | #38 | **OPEN — blocked on a decision** |

**Not in x.27, by ruling:** ACAI entity data (the largest gap — 26,531 references in
`ears-to-hear`, engine has nothing), Lowfat beyond #227, lexicons and semantic domains.

### x.27 cleanup, also directed

1. **Guard refactor** — move the shared/engine-only/rewritten classification into
   `data/helm-sync.yaml`; have `EXPECTED_DISCIPLINES` (`test_global_disciplines.py`) and
   `SHARED_WITH_HELM`/`ENGINE_ONLY`/`REWRITTEN` (`test_portable_disciplines.py`) read it; generate
   `disciplines/README.md`. Adding one discipline costs five edits across four files today.
   **The Captain gave the word; this is first after the rulings.**
2. `github-authority.md` — add the "show the body before running the command" rule. *Home
   undecided* (see Decisions).
3. `query_macula_hebrew` / `query_macula_greek` — both confirmed broken, both uncalled anywhere.
   Fix or delete is the Captain's.
4. `RELEASE_CHECKLIST.md` §12 is wrong (see Settled). **Correcting it is unclaimed.**

---

## Decisions awaiting the Captain

Walked through with him 2026-09-05; **no rulings received yet.** Recommendations are the AI's.

### #169 — comparing verse references (three open)

The previous handoff listed three; the design doc actually holds six. **Two are now dead** — see
the staleness table: complete verse counts exist, so `adjacent` and `verse_count` need no
deferral and the table is not a blocker. What remains:

- **`contains` set semantics.** Union-covers, or some-single-range-covers? The doc's example:
  `Mark 1:1-5` + `Mark 1:8-12` against `Mark 1:3-10` — union says yes, single range says no.
  *Recommended: both, as `contains_any` / `contains_all`*, because they are different questions
  and collapsing them means the caller cannot say which they meant.
- **Bare names (`overlaps`) or `verse_range_*`?** *Recommended: prefixed* — flat namespace, and
  `contains` will collide.
- **Singletons only, or singletons and lists?** *Recommended: both* (the doc agrees) — singleton-only
  leaves the iteration in consumer Python, which is what #169 exists to remove.

**Already ruled, do not reopen:** scheme is a **required parameter, no default** (four of six
operations need `Scheme.max_verses`/`excluded_verses`, and all six are meaningless across two
numberings). Cross-book, ruled 2026-08-17: `overlaps` → False, `intersection` → None, `union` →
**raises**; the doc asks only that implementation confirm it.

**Not a decision, but document it loudly:** `union` is the **convex hull**, so
`Mark 1:1-5 ∪ Mark 1:8-12` = `Mark 1:1-12` *including the gap*. Right for "what is the span",
wrong for "what is covered". An exact-set-union `merge` can come later if anyone needs it.

### #222 — Paratext versification

`custom.vrs` is detected, warned about and ignored, so references are silently wrong.
`edition_scheme()` returns a scheme *name* and `map_reference` takes names — a project's overlay
has none. Synthetic name, or `Scheme` objects through the API?

*Recommended: `Scheme` objects*, on the Captain's own `declared-not-inferred` rule — a synthetic
name is an identifier the engine invents for a thing the project never named, and it will leak
into someone's output. Wider API change; that is the cost.

### #38 — BaseX collection naming

#38 proposes semantic (`macula/gnt-lowfat`), #52 provenance (`github/<org>/<repo>/<path>`), both
calling theirs canonical. *Recommended: discourse-flow's synthesis* — semantic name as the
identifier, provenance as a declared attribute, which is the `id:` + `dataset:` shape
`registrations/SBLGNT.yaml` already uses. Not a compromise; the pattern is already in the repo.

### `github-authority.md` prose rule

Shared discipline (reaches every project and Human at the Helm; costs a `helm-sync.yaml` hash
update and a twin commit there), or a narrower `CLAUDE.md` line? *Leaning shared* — the failure it
prevents is not specific to this repo.

---

## Settled — do not reopen

**From the `syntax` work (2026-09-05):**
- **Only the first, primary interpretation** of a Lowfat tree. Measured across 137,741 Greek words
  and 25,025 Hebrew morphemes: **zero** sentences carry a second subtree, so there is nothing to
  select between and the ruling became a parity check.
- **`class` and `role` are carried; `rule` is not.** `class` is the syntactic category, `role` the
  role with respect to the governing verb. `rule` names the parser's derivation, not a fact about
  the constituent.
- **Hebrew stays morpheme-based.** Collapsing a word's morphemes was proposed and rejected: 171 of
  Ruth 1's 172 multi-morpheme words differ in `class` or `role`. Costs 40%, buys the analysis.
- **`<c>` compound words are carried as nodes**, not leaves — they span two *words*, so no single
  token names them. They were being dropped silently, taking ten morphemes of Ruth 1.
- **`syntax` requires `ids`** and raises without it. Stronger than the per-word rule deliberately:
  a tree is *over* words, so `per_word: true` would be the wrong route to the same requirement.
- **A sentence is carried whole** where it meets the passage, so a token may name a word outside
  the rows returned. Pruning would return the constituency of half a sentence, which is not a fact
  about the text. *`discourse-flow` has been told; if they ask for the boundary to be flagged, that
  is a new decision, not a commitment already made.*
- **Lowfat files are matched by the `ref` each declares**, not by filename — neither corpus
  declares a convention. 0.33s across all 930 Hebrew files.

**From the Hebrew resolution work:**
- **Word ids drop the word-part digit** when doing so leaves the id ending in the word index —
  `BBCCCVVVWWWP` → `BBCCCVVVWWW`. Not invented: `WWW` is a declared component of the MACULA format.
- **Resolution precedence: index, then quote, then say you could not find it** — and where index
  and quote disagree, report both.

**Earlier, still binding:**
- **Field roles are two words**, `evidence` and `content`. `handoff` and `adjudication` were cut:
  both describe what a *downstream* consumer does. The Captain's test — *"it's analogous to sp
  trying to own the application semantics of the pipelines that use it."*
- **`empty_expected`, occupancy reporting, severity and audience are out** of the engine. Each
  needs a judgment about somebody else's data.
- **The general coverage check is not being built.** Three shapes were tried (`expects`, `covers`,
  copy-verification) and all three dissolved. The Captain: *"I do not yet see a feature with
  simple, clean semantics for us to implement."*
- **`say-which-kind-of-nothing` is two states, not three.** `{}`/`[]` = the lookup ran and found
  nothing; `null` = there was nothing to look in. Absence carries no meaning and cannot, since
  OpenAI strict mode marks every property `required`.
- **`pyproject.toml` stays at the released version during development**, bumped as release prep.
  **`RELEASE_CHECKLIST.md` §12 contradicts this** and fails four guards.
- **A scope note does not belong in the CHANGELOG.** It records changes, not plans.

---

## Landmines

- **Never write to `docs/ai-context/` by hand.** Files there are `policy: generated` in
  `data/file-catalog.yaml`: `sp/rules.md` renders from `data/ai-rules.yaml` via `AI_RULES_DOC`,
  and `sp/scripture-representations.md` is a copy of a shipped template held byte-identical by
  `test_template_layout.py:106`. Edit the source in `src/llmflow/templates/`, regenerate the copy.
- **`data/ai-rules.yaml`, `CLAUDE.md`, `~/.sp` and `~/.claude` are the Captain's.** `~/.sp` is
  read-only by design; never unlock it.
- **`~/.sp` is *not* the source for disciplines.** `src/llmflow/templates/sp/` is; `~/.sp/` is the
  installed copy. This was got backwards once already.
- **Both consumer repos install this working tree editable**, so `dev` *is* their engine with no
  pull and no version bump. A half-applied edit breaks their runs — `discourse-flow` lost one that
  way. Keep the tree consistent between *commits*, not between edits.
- **Two pytest runs collide** on `tmp/pytest/` and produce an `INTERNALERROR`. One at a time.
- **`git rev-parse HEAD^2` needs quoting in zsh** — `^` globs. Use `"HEAD^2"`.
- **`ruff check src/ --fix` deleted `llmflow.runner`'s re-export surface** and broke the suite at
  *import* time, twice. It is now declared in `__all__` and guarded by
  `tests/test_runner_reexports.py`, which parses the tree. Do not delete a name from that list.
- **The GUI has two copies.** `build_gui.py` copies `gui/backend/{server,executor}.py` over
  `src/llmflow/gui/`. Fixing only the `src/` side is erased by the next build;
  `test_gui_copies_are_identical.py` catches it.
- **Never run `sp run`** (costs money) or **`sp doctor`** (unsafe here until #210/#211).
- **`tests/integration/test_mcp_batch_calls.py` needs a live external MCP server.** CI deselects
  `integration`; that is the 26.
- **Prose is guarded.** `test_product_name_in_prose.py` forbids the deprecated product name in
  `.md` files — **Scripture Pipelines** is the ruled term, `llmflow` only as the import namespace
  (`design-vocabulary.md`). A docstring guard also forbids dates and "the Captain" in source. Both
  caught three drafts each last cycle.

---

## Consumer threads

**`discourse-flow`** — `collab/discourse-flow/2026-09-03-hebrew-discourse-defects.md`, 1,928 lines,
six replies each way. Everything they raised has been answered: the `--resume` fix, the absent
anchor (already in `validate_structure`), the empty anchor (already reachable with `require:`,
which runs after outputs are stored), `pericope_sequence` (their finding to act on), and `syntax`.
**Nothing is outstanding to them.** The one thing that could come back is the whole-sentence
overhang described under Settled.

They also found a real ordering defect in their own `book-segmentation.json` — `coverage_check`
declared before `pericopes` despite its description — which is theirs, not ours.

**`ears-to-hear`** — `collab/ears-to-hear/2026-09-03-declaring-evidence-and-content.md`. The
live-coupling item is closed.

**C-level** — `collab/clevel/2026-09-04-what-the-engine-work-can-and-cannot-tell-you.md`, written
for a separate documentation session working outside this repo.

---

## Not on any list, and time-critical

**Workshop readiness is "main next goal" in `TODO.md`, and mentoring is the week of 2026-09-08 —
next week.** Nothing in x.27 addresses it. Acceptance criterion, the Captain 2026-08-17: *a user
clones a mentoring repository such as `sil-translator-notes`, runs `sp init`, and `/load-context`
works. Nothing hand-carried.* **That section's blocker list must be verified against current code
before anyone works from it** — see the staleness warning. PyPI is no longer a blocker: `pip
install scripture-pipelines` now gets 0.2.1.26.

**`🔥 Monday priorities` in `TODO.md`** — the GUI Content Lifecycle page displays blank. No GitHub
issue; that file is the only record. `/api/content/transition` in `gui/server.py` is a stub
returning 501, which may be related and is unverified.

---

## Key files

- `project/plans/design-verse-range-operations.md` + `plan-verse-range-set-ops.md` — #169's two
  approved documents. **Reconciling them into one is the first deliverable**, and the verse-count
  sections are stale
- `project/plans/design-scripture-representations.md` §4.5 — the `syntax` ruling, now built
- `project/plans/design-declaring-field-roles.md` §10 — copy forcing, built
- `project/plans/design-what-the-engine-may-rely-on.md` — the declared-vs-inferred principle
- `src/llmflow/utils/syntax.py`, `tests/test_syntax_payload.py` — the tree family; the *why* of
  every shape decision is in the test docstrings
- `src/llmflow/utils/discourse.py` — resolution, spans, the precedence chain
- `src/llmflow/field_roles.py` — copy forcing, read by `utils/linter.py`
- `data/ai-rules.yaml` — 38 rules, each with `enforcement` and `scope`; the single source
- `data/include-families.json` — the seven families; `frame` rides with `referents`
- `project/RELEASE_CHECKLIST.md` — **§12 is wrong**, see Settled
