# HANDOFF — 2026-09-04

## ▶ NEXT ACTION

**Commit the seven uncommitted files, then push `dev`.** They are all x.27 correspondence and
design — no code. The Captain has approved the content of each; the commit and push are his.

```bash
git add -A
git commit -F tmp/commit-field-roles-ruled.txt   # REWRITE FIRST — see "In flight" below
git push origin dev
```

`tmp/commit-field-roles-ruled.txt` is **stale**: it predates the checks sections added to both
collab threads and the whole Hebrew-defects thread. Rewrite it to cover the full set before
committing.

After that, x.27 work begins. The Captain's ordering, given 2026-09-03: the guard refactor first
(item 1 under "x.27 cleanup"), because everything touching disciplines pays the old cost until it
lands.

---

## Where the repository actually is

| | |
|---|---|
| `dev` | `5822104` (local) — `origin/dev` is at `c00f50d`, behind by 11 historical merge commits |
| `main` | `5822104`, pushed. Same commit as local `dev`; trees identical |
| tag | `v0.2.1.26` on `c00f50d` |
| PR #231 | **MERGED** 2026-09-04 13:08 |
| suite | **4714 passed, 24 skipped, 26 deselected** with `-m "not integration"` (the CI selection) |
| `ruff check src/` | **clean** — first time; 182 findings cleared 2026-09-03 |

**Verify:** `git log --oneline -1 dev main origin/dev`, `hatch run pytest -q -m "not integration"`,
`ruff check src/`.

The "ahead 11" on `dev` is harmless: `git merge --ff-only main` pulled eleven main-only
`Merge pull request #NNN` commits that had never been on `dev`. `git diff main dev` is empty.

---

## 0.2.1.26 — released, one item outstanding

Published 2026-09-04 13:04. Not a draft, not a prerelease. `sp-linux` 140MB, `sp-macos` 96MB,
`sp-windows.exe` 98MB attached. Install script verified on macOS, Windows and Ubuntu.

**PyPI is at 0.2.1.25.** The Captain first rejected the `pypi` environment gate deliberately, then
changed his mind and wants 0.2.1.26 published. The run is complete, so the gate is closed; the
route is to re-run that one job, which re-requests approval:

```bash
gh run rerun 33875987740 --job 101033180577
```

Then he approves at https://github.com/nida-institute/LLMFlow/actions/runs/33875987740

Verified before recommending it: `pyproject.toml` at `v0.2.1.26` reads `0.2.1.26`, and the job
checks out the tag ref, so it builds 0.2.1.26 — 0.2.1.25 cannot be republished, and PyPI refuses
re-upload of an existing version anyway.

**The run's overall conclusion will stay `failure`** because the rejected attempt is in its
history. Check the job and PyPI, not the run badge.

---

## ⚠️ Read this before trusting any plan document in this repository

**Five plan and TODO documents asserted state that was false, found in one day.** This is the
repository's dominant defect class. Verify against code, tests and CI — never against the record.

| document | claimed | actual |
|---|---|---|
| `plan-release-0-2-1-26.md` §3.1 | catalogue fetch "build this release" (#217, #201, #212) | **shipped in 0.2.1.25**; #212 declined by ruling |
| 7 shipped docs | registrations live in `~/.sp/editions/` | `editions` is `LEGACY_REGISTRATION_DIRNAMES`; it is `~/.sp/registrations/` |
| `TODO.md` workshop section | 10 blockers, "2620 tests pass" | several fixed; 4714 tests; consent prompts and the TTY early-return are gone |
| `plan-release-0-2-1-26.md` | `include: [syntax]` "named but not implemented" | it is a **shipped silent no-op** — accepted by lint, returns no key at all |
| #38 | closed as completed 2026-08-26 | never implemented. Closed on an AI's conversational claim; no commit, no test. **Reopened 2026-09-03** |

The Captain, on the last one: **"We had to implement this because it's not in SP" is not proof
that it isn't needed, it is often proof that it is needed.**

Also note `test_record_closure_claims.py` cannot catch this class — it scans `TODO.md` and
`HANDOFF.md` for "closed by `<sha>`". A claim made only in conversation never enters a record.

---

## x.27 — scope ruled 2026-09-03

| # | Feature | Issue | State |
|---|---|---|---|
| 1 | Hebrew resolves in `include: [discourse]` | #230 | root cause **verified**: `resolve_citation` matches Levinsohn's index against *row position*; Hebrew rows are morphemes (`RUT 1:1` = 33 rows, 19 words, 1.74/word), Greek is 1.00/word. Fix: match `!N` from `ref`. Also `label` is read and dropped; `text` is kept for notes only (`discourse.py:285`) |
| 2 | Copy forcing — declare evidence vs content | #230 | design **ruled and revised**; build order in `design-declaring-field-roles.md` §10 |
| 3 | Paratext via `type: scripture`, own versification | #222 | `custom.vrs` found, warned about, ignored — references silently wrong |
| 4 | Comparing verse references | #169 | ruled into 0.2.1.26 and **never built**; blocked on decisions below |
| 5 | `include: [syntax]` — Lowfat, standoff | #227 | design **fully ruled** 2026-08-31, `design-scripture-representations.md` §4.5; nothing open |
| 6 | BaseX for all XML sources — *if it fits* | #38 | plumbing exists (`sp load-db basex`, `$database` binding, `sp resource download/add`); missing is collection organization |

**Not in x.27, by ruling:** ACAI entity data (the largest gap — 26,531 references in ears-to-hear,
engine has nothing), Lowfat beyond #227, lexicons and semantic domains.

### x.27 cleanup, also directed

1. **Guard refactor** — move the shared/engine-only/rewritten classification into
   `data/helm-sync.yaml`, have `EXPECTED_DISCIPLINES` (`test_global_disciplines.py`) and
   `SHARED_WITH_HELM`/`ENGINE_ONLY`/`REWRITTEN` (`test_portable_disciplines.py`) read it, and
   generate `disciplines/README.md`. Adding one discipline currently costs five edits across four
   files. **The Captain gave the word; do this first.**
2. `github-authority.md` — add the "show the body before running the command" rule. *Which home is
   undecided* (see Decisions).
3. `query_macula_hebrew` / `query_macula_greek` — both confirmed broken, both uncalled anywhere.
   Fix or delete is the Captain's.

---

## Decisions awaiting the Captain

**#169 — three left; the fourth is ruled.**
- **RULED:** scheme is a **required parameter, no default.** Four of the six operations need
  `Scheme.max_verses`/`excluded_verses` (`union` across a chapter boundary, `adjacent`,
  `verse_count`), and all six are only meaningful if both refs are in one numbering.
- Singletons only, or both? *Recommended: both* — singletons-only leaves the iteration in consumer
  Python, which is the thing being fixed.
- Bare names (`overlaps`) or `verse_range_*`? *Recommended: prefixed.*
- Confirm the plan's cross-book split: `overlaps` → False, `intersection` → None, `union` →
  **raises**.

**Hebrew (#230)**
- When a word spans rows 6–7, **which row's `xml:id` anchors the citation** — first morpheme, or
  the one the quote matched?
- Payload shape: sp emits a flat list, discourse-flow consumes a verse-keyed dict.
  `verses-are-milestones` argues for sp's. Who adapts?
- Is per-morpheme correct for every per-word `include:` family on Hebrew, or was only the resolver
  wrong?
- Structural vs prominence features (accent ranks are 225,840 of 422,211 HOTDF-LS citations).
  discourse-flow argues the **corpus** should declare it; HOTDF-LS does not. May be out of scope.

**Paratext (#222)** — `edition_scheme()` returns a scheme *name* and `map_reference` takes names;
an overlay has none. Synthetic name, or `Scheme` objects through the API?

**BaseX (#38)** — collection naming. #38 proposes semantic (`macula/gnt-lowfat`), #52 proposes
provenance (`github/<org>/<repo>/<path>`), both call theirs canonical. discourse-flow's input:
semantic name as the identifier, provenance as a declared attribute, following
`registrations/SBLGNT.yaml`'s existing `id:` + `dataset:` shape.

**`include: [syntax]` today** — it is accepted and returns nothing. Refuse at lint time now, or let
#227's implementation close it?

**`github-authority.md` prose rule** — shared discipline (reaches every project and Human at the
Helm, but needs a `helm-sync.yaml` hash update and a twin commit in that repo), or a narrower
`CLAUDE.md` line?

---

## Settled this cycle — do not reopen

- **Field roles are two words**, `evidence` and `content`. `handoff` and `adjudication` were cut:
  both describe what a *downstream* consumer does. The Captain's test — *"it's analogous to sp
  trying to own the application semantics of the pipelines that use it."* Each layer declares what
  it knows and stops. `adjudication` is carried by `supports`; `handoff` a project declares for
  itself, and `sp` does not reject a role word it has not defined.
- **`empty_expected`, occupancy reporting, severity and audience are out** of the engine. Each needs
  a judgment about somebody else's data.
- **`say-which-kind-of-nothing` is two states, not three.** `{}`/`[]` = the lookup ran and found
  nothing; `null` = there was nothing to look in. A key may be absent where another declaration
  accounts for it (`include:` is one), but absence carries no meaning — and cannot, since OpenAI
  strict mode marks every property `required`.
- **`pyproject.toml` stays at the released version during development** and is bumped as release
  prep. **`RELEASE_CHECKLIST.md` §12 is wrong** — it says to bump post-release and start a fresh
  CHANGELOG section, which fails three guards in `test_changelog_covers_the_version.py` (the
  declared version needs a *dated* section) and one in `test_changelog_is_not_a_transcript.py` (no
  prose before the first `###`). **Correcting §12 is unclaimed work.**
- **A scope note does not belong in the CHANGELOG.** It records changes, not plans.

---

## Landmines

- **Never write to `docs/ai-context/` by hand.** Both files modified this cycle are
  `policy: generated` in `data/file-catalog.yaml`: `sp/rules.md` renders from `data/ai-rules.yaml`
  via `AI_RULES_DOC`, and `sp/scripture-representations.md` is a copy of a shipped template held
  byte-identical by `test_template_layout.py:106`. Edit the source, regenerate the copy.
- **`data/ai-rules.yaml`, `CLAUDE.md`, `~/.sp` and `~/.claude` are the Captain's.** `~/.sp` is
  read-only by design; never unlock it. Its 20 uncommitted files are mostly install trace, but
  `disciplines/workflow.md` and `skills/load-context/SKILL.md` are genuine drift candidates.
- **`~/.sp` is *not* the source for disciplines.** `src/llmflow/templates/sp/` is; `~/.sp/` is the
  installed copy. This was got backwards once already.
- **Two pytest runs collide** on `tmp/pytest/` and produce an `INTERNALERROR`. One at a time.
- **`git rev-parse HEAD^2` needs quoting in zsh** — `^` globs. `"HEAD^2"`.
- **`ruff check src/ --fix` deleted `llmflow.runner`'s re-export surface** and broke the suite at
  *import* time, twice. It is now declared in `__all__` and guarded by
  `tests/test_runner_reexports.py`, which parses the tree. Do not delete a name from that list
  casually.
- **The GUI has two copies.** `build_gui.py` copies `gui/backend/{server,executor}.py` over
  `src/llmflow/gui/`. Fixing only the `src/` side gets erased by the next build;
  `test_gui_copies_are_identical.py` catches it.
- **Never run `sp run`** (costs money) or **`sp doctor`** (unsafe in this repo until #210/#211).
- **`tests/integration/test_mcp_batch_calls.py` needs a live external MCP server** and fails
  without it. CI deselects `integration`.
- **Prose is guarded.** `test_product_name_in_prose.py` forbids the deprecated product name in
  `.md` files; **Scripture Pipelines** is the ruled term, and `llmflow` stays only as the import
  namespace. See `design-vocabulary.md`. It caught three drafts this cycle — including the line
  that first described this landmine.

---

## Consumer threads — both live, neither needs a reply

**discourse-flow** has answered everything and asks for nothing. Outstanding from their side: they
offered a failing test for the morpheme defect (Ruth 1:1, `Kings` at index 4, expecting `verified`)
if wanted. They also reported, and it was verified here, that `plugins/levinsohn.py` carries the
exact three limitations removed from `discourse.py` on 2026-09-03 — `ElementTree`, an OSIS table
commented *"NT only (book numbers 40–66)"*, and `feature` roots only. **`sp` is now strictly ahead
of their fork.** 4,774 lines across 25 plugins, of which 4 import `llmflow`.

The Captain: *"I do want them to include [discourse], so we need to address this."* They were asked
to investigate whether their prompts render `label` and `text` and respond. **Nothing gets built on
that until they have looked.**

**The live-coupling item is closed.** They named the two copy-forcing fields to `ears-to-hear`
before our note was written. They also corrected a claim of ours worth keeping: an assertion
against a forcing field whose content is a **verbatim copy of the stage's input** is a genuine
cross-stage check, not a measurement of the device — and it caught two real faults, John 121 vs 123
leaves and Revelation 70 vs 72 with `REV 8:1-6` claimed by two divisions, which they had not found.

---

## Not on any list, and time-critical

**Workshop readiness is marked "main next goal" in `TODO.md`, and mentoring is the week of
2026-09-08.** Nothing in x.27 addresses it. Acceptance criterion, the Captain 2026-08-17: *a user
clones a mentoring repository such as `sil-translator-notes`, runs `sp init`, and `/load-context`
works. Nothing hand-carried.* That section's blocker list needs verifying against current code
before anyone works from it — see the staleness table above.

**`pip install scripture-pipelines` gets 0.2.1.25** until the PyPI job is re-run. A workshop
participant following pip-based install docs would get none of 0.2.1.26's fixes.

**`🔥 Monday priorities` in `TODO.md`** — the GUI Content Lifecycle page displays blank. No GitHub
issue; that file is the only record. `/api/content/transition` in `gui/server.py` is a stub
returning 501, which may be related and is unverified.

---

## Key files

- `project/plans/design-declaring-field-roles.md` — x.27 item 2, ruled; §10 is the build order
- `project/plans/design-scripture-representations.md` §4.5 — x.27 item 5, ruled
- `project/plans/design-verse-range-operations.md` + `plan-verse-range-set-ops.md` — #169's two
  approved documents; reconciling them into one is the first deliverable
- `project/plans/design-combining-levinsohn-and-ubs.md` §5 — HOTDF-LS measurements, attributed to
  discourse-flow and marked unverified here, with the command to re-derive them
- `collab/discourse-flow/2026-09-03-hebrew-discourse-defects.md` — the morpheme finding, both sides
- `collab/{discourse-flow,ears-to-hear}/2026-09-03-declaring-evidence-and-content.md` — the ruling,
  replied inline
- `data/ai-rules.yaml` — 39 rules, each with `enforcement` and `scope`; the single source
- `src/llmflow/templates/sp/disciplines/working-for-a-person.md` — added this cycle, shared with
  Human at the Helm
- `project/RELEASE_CHECKLIST.md` — **§12 is wrong**, see above
