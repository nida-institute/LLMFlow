# Project TODO

> **Convention:** Active work lives here. Bugs and permanent decisions go to
> [GitHub Issues](https://github.com/nida-institute/LLMFlow/issues).
> Link issues with `→ #N` so this file doesn't duplicate GitHub.
> Board: https://github.com/orgs/nida-institute/projects/13

## 🔥 Active

### 📐 THE GOAL THIS CYCLE — scripture text representation

> Set by the Captain 2026-09-10. Everything else in this list yields to it.

`include:` is refused unless `format: usj`, so a pipeline that needs annotation cannot have
milestone-cost text. Measured downstream on Philemon 1:1–7: **622 characters of Greek delivered
as 14,045 of JSON, 22.6×**; across the book 334 words carry an anchor and **228 are referenced
by nothing**.

The design is drafted and unreviewed: **`project/plans/design-annotation-without-anchors.md`**,
status `proposed`. It was raised by
`collab/discourse-flow/2026-09-09-include-forces-the-most-expensive-text-form.md`.

- [ ] **Ruling needed on five decisions** — design §6. In short: is the payload made
      self-describing (option C, recommended), is the cost simply accepted (A), or are anchors
      thinned (B, which makes the text vary with the `include` list)
- [ ] **Measure before ruling** — design §7. Philemon 1:1–7 under today's `usj` + families
      against `milestones` + a self-describing payload. If C is not decisively cheaper its main
      argument goes, and this may settle the question without a discussion
- [ ] Read `collab/discourse-flow/2026-09-09-what-we-still-compute-that-other-projects-will-need.md`
      — an inventory of what a consumer computes in plugins that the engine might absorb. Bears
      directly on this
- [ ] Then implement whatever is ruled

**The one fact worth carrying:** a per-word payload is keyed by an opaque word id and carries
only the annotation — no surface form, no reference. That is the *whole* reason anchors are
load-bearing, and it was established by fetching `WLC Ruth 1:1`, not by reading comments.

### 🚢 0.2.1.28 — merged? tagged? released?

- [ ] **PR #236** — `dev` → `main`, 8 commits, `MERGEABLE`, build `34409536310` green on all four
      jobs. Merge with a **merge commit**, tag the merge commit, watch all five `release.yml` jobs
- [ ] Artifacts **expire 16–17 September**. After that the build re-runs, and Windows takes 2h17m
- [ ] `data/models.json` is held back deliberately — one line, and committing it restarts a
      two-hour build. It belongs to the cycle after

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
      because neither corpus sits at a repository root. `resources.resolve_annotation_path`,
      20 tests, documented in the language reference.
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

### 🔼 Two fixes belong upstream in `awesome-biblical-data`, not here

> `data/resources.json` is **vendored** and currently identical to upstream, so editing it here is
> reverted by the next sync.
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
- [ ] Verse range operations (`overlaps`, `contains`, `intersection`, `union`) → #169
  - Design document: `project/plans/design-verse-range-operations.md`
  - 6 decisions needed before implementation (see design doc / issue comment)
- [ ] List transformation: flatten, project, slice as framework primitives → #167
- [ ] Predicate filtering: filter lists by value / cross-list membership → #168
- [ ] Accumulator initialization in `variables:` block → #170

## ✅ Done

---
_Audit notes and QA reports → project/audits/_
_Pipeline decisions → project/decisions.md (create when needed)_
_Project board → https://github.com/orgs/nida-institute/projects/13_
