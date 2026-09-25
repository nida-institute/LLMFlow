# HANDOFF — 2026-09-25

## ▶ NEXT ACTION

**Commit this session's work. Nothing here is committed, and it spans two repositories.**

The commit is the Captain's (`commit-authority`). The files are listed under **In flight** below,
grouped by what they are. One group is *not* this session's and must not be swept in: the
pre-existing modifications listed as "the Captain's".

**Then:** `project/TODO.md` holds the queue and its order. Do not read the queue out of this file.

---

## Active threads

### 1 — three new release goals were set and recorded (DONE, uncommitted)

**Goal.** The next release carries the existing goals plus three new ones, all set 2026-09-25.

- **`/stage-commits`** — a skill that stages the outstanding changes and hands over the runnable
  commit command, in POSIX shell syntax. **Placed first in `project/TODO.md`**, which was "perhaps
  first" — the position is the Captain's to confirm. No issue, no plan file. It is rule
  `commit-authority` made mechanical, and its boundary with `commit-ready` (gate, not mechanism) is
  stated in the task list so the two do not become one design in two files.

**State.** Recorded in `project/TODO.md`. One is filed as an issue; one is drafted and not filed.

- **Refactoring collaboration with Human at the Helm** — both halves in scope: Helm adopting sp's
  idioms and installing into paratext-copilot, *and* how the two repositories share files at all.
  Issue **drafted, not filed**: `tmp/issue-helm-collaboration.md`.
- **A dataset announces its terms when it lands** — filed as **#252**. Plan:
  `project/plans/plan-terms-on-download-and-register.md`, `Status: ruled (2026-09-25)`. Open
  decisions in `project/open-decisions.md` §L.

**Verify.** `gh issue view 252`; `git status --short -- project/ CHANGELOG.md`.

### 2 — the skill-type prefixes are ruled out and sp's are stripped (DONE, uncommitted)

**Goal.** Settle the 2026-09-24 Helm change that stripped `**WORKFLOW SKILL** —` from six shared
skill descriptions and was left in the working tree pending a ruling.

**State.** Ruled 2026-09-25: the prefixes go and stay gone. The 09-24 change **stands rather than
being reverted**. Five sp-only skills that still carried one were stripped to match —
`audit-code`, `audit-output`, `audit-pipeline`, `audit-prompts`, `release`.

**Helm's files were not touched**, on explicit instruction. Two things there now contradict the
ruling and were named rather than edited: `.claude/skills/install/SKILL.md` still carries
`**COMMAND SKILL** —`, and `project/plans/design-skill-defects.md` D3's slot reads
*"Discuss. Need more information."*

**Verify.** `grep -rn "SKILL\*\* —" src/llmflow/templates/sp/skills/` returns nothing.
`hatch run pytest tests/test_helm_sync.py -q -p no:randomly` → **82 passed** (run 2026-09-25,
after the change).

**⚠️ `.claude/skills/` and `~/.sp/skills/` still carry the prefixes.** They are installed copies,
regenerated from the templates, so they refresh on the next `sp init --update` — **not
`sp doctor`, which must not be run here (#210)**.

### 3 — Helm has been told, in their tree (DONE, untracked there)

`~/github/nida-institute/human-at-the-helm/collab/sp/2026-09-25-the-prefixes-are-ruled-out-and-sp-has-stripped-its-own.md`

Written into the recipient's tree per `plans-are-temporary`. **It is untracked in that
repository** and that repository has its own uncommitted state — see **Do NOT**.

### 4 — `project/open-decisions.md` is new here (DONE, uncommitted)

The `=>` convention now has a named home in this repository, following
`nida-institute/discourse-flow`. Adapted: answers move to `CHANGELOG.md` or
`docs/ai-context/project/rules.md`, this project's two declared homes, because there is no
`project/rulings.md` here.

**Open, and not decided:** `project/plans/design-decisions-awaiting-ruling.md` (2026-09-02) already
does part of the same job. Two files for one purpose is the drift this repository has been burned
by; consolidating them is the Captain's call and was deliberately not done while adding the second.

---

## In flight, and whose

Branch `dev`, level with `origin/dev` at `3dbb55b`. **Nothing from this session is committed.**

| | |
|---|---|
| **this session's, new** | `project/open-decisions.md`, `project/plans/plan-terms-on-download-and-register.md` |
| **this session's, modified** | `project/TODO.md`, `CHANGELOG.md`, `project/plans/README.md` (regenerated), 5 × `src/llmflow/templates/sp/skills/{audit-code,audit-output,audit-pipeline,audit-prompts,release}/SKILL.md` |
| **ruled in this session, changed on 2026-09-24** | `data/helm-sync.yaml`, 6 × `src/llmflow/templates/sp/skills/{authorize,commit-ready,handoff,health-check,load-context,stand-down}/SKILL.md` |
| **the Captain's, pre-existing — do not sweep in** | `data/models.json`, `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its template twin |
| **gitignored drafts** | `tmp/issue-helm-collaboration.md` (unfiled), `tmp/issue-licence-display.md` (filed as #252), `tmp/helm-rogue-edits-2026-09-24.diff` |
| **another repository** | `human-at-the-helm/collab/sp/2026-09-25-…md`, untracked |

**`project/plans/README.md` is generated.** Adding a plan document without regenerating it turns
`tests/test_plan_docs_index.py` red — it did, and was fixed with
`hatch run python tools/update_plans_index.py`.

**`docs/ai-context/project/data-sources.md:48` still breaks CI if committed unchanged.** Run
`hatch run pytest tests/test_product_name_in_prose.py` for the line rather than reproducing it —
quoting it re-trips the guard.

---

## Decisions

### Settled 2026-09-25 — do not reopen. All are in `CHANGELOG.md` → Unreleased → Ruled

- **#248 D3a** — append each finished iteration to a temporary TOML during the run, reassemble
  into the canonical JSON manifest at the end. *Not settled by it:* whether partial-loop resume is
  now reliable (the earlier answer was conditional), and concurrent appends, which are #249's.
- **The issue is the plan for #248** — no plan file, and none is wanted.
- **#252's three rulings** — print at both commands; gate `resource add` only; `--accept-terms`
  with fail-closed on no TTY.
- **The skill-type prefixes go and stay gone.**
- **`=>` slots live in `project/open-decisions.md` and `project/plans/`, never in a GitHub issue.**
  An empty `=>` in an issue is a convention that travelled by mistake, not an open question.
### ⚠️ One instruction could not be carried out as given

**The rulings were to go into `CHANGELOG.md` for a permanent home. Three guards refused them**, and
the refusal is correct rather than a bug to work around:

- `### Ruled` is not in the allowed section set — `tests/test_changelog_is_not_a_transcript.py:22`
  permits only Added, Changed, Deprecated, Removed, Fixed, Security, New Features, Test Coverage,
  Documentation.
- The verbatim quotes are first-person, and the guard forbids `I`, `we`, `our` **with no exemption
  for quotation** (`:27-32`).
- "in conversation" is banned as session commentary (`:37`).

So only the prefix removal went in, under `### Changed`, where it belongs as a real change.

**This is a genuine collision between two of this project's own rules**, not a mistake to route
around: `plans-are-temporary` says a ruling lives in `CHANGELOG.md`, and
`test_changelog_is_not_a_transcript` says the changelog carries changes written for an outsider.
An unimplemented ruling is neither. **The Captain's call**, and the cheapest options are adding
`Ruled` to that test's `SECTIONS`, or naming a different durable home.

**Nothing was lost meanwhile.** The four 2026-08-24 rulings are still in
`project/plans/design-source-licensing.md`, which is therefore **not yet safe to delete** — that
document remains their only copy.

### Open, and awaiting the Captain

1. **File the Helm collaboration issue?** Draft at `tmp/issue-helm-collaboration.md`.
2. **The spent 2026-09-23 collab note** — `collab/human-at-the-helm/2026-09-23-…md` is resolved and
   **untracked**, which the convention it introduced forbids. Commit then delete, or delete?
3. **Where unimplemented rulings live** — see the collision above. Until it is settled,
   `design-source-licensing.md` holds the only copy of four rulings and **must not be deleted**.
6. **The installed-copy drift** — commit or stash `docs/ai-context/sp/github-workflow.md`, then
   `sp init --update`. One test is red until then.
4. **`open-decisions.md` §L** — L1 (what agreement means when a licence is a URL) blocks the gate
   but not the printing; L2 and L3 block nothing.
5. **The CHANGELOG entry for 0.2.1.28** — PR #236 merged 2026-09-24 under its *original* title,
   `Release 0.2.1.28 — the bugs a first setup hits`; the chosen retitle never applied. Whether the
   CHANGELOG carries the chosen title is open.

---

## Do NOT

- **Do not `git add -A`** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.
- **Do not run `sp doctor` here** — #210.
- **Do not hand-edit `docs/ai-context/sp/rules.md`** — regenerated from `data/ai-rules.yaml`.
- **Do not hand-edit `.claude/skills/` or `~/.sp/skills/`** — installed copies; fix the template.
- **Do not edit anything in `human-at-the-helm`** beyond the collab note already written. That tree
  was on `main`, 5 ahead unpushed, with staged work; an incautious restore there destroys it.
- **Do not delete `tmp/`** — it holds the unfiled Helm issue draft and the only copy of the 09-24
  diff, and it is gitignored.
- **Looks like a next step but is not:** pruning `project/TODO.md`'s #204 section. It still lists
  two prompt defects as live — the silent non-TTY return and "defaults to No" — which
  `cli_utils.py:230-244` shows were fixed. Flagged twice this session and deliberately not edited;
  it is a separate change.
- **Also not a next step:** building #252. The printing half is unblocked, but no test is written
  and `plans-first` wants the failing test first.

## Known-failing

**Verify:** `hatch run pytest tests/ -q --tb=line -m "not integration" -p no:randomly` →
**6 failed, 5728 passed, 25 skipped** on 2026-09-25 (2m35s). Three of those six were fixed
immediately afterwards, so **the expected state is 3 failed**:

- `test_product_name_in_prose` — working tree only, from the Captain's uncommitted
  `docs/ai-context/project/data-sources.md`. The committed copy is clean.
- `test_resource_provisioning` — `skipif` on a local clone being present, so it skips in CI.
- **`test_prompt_structure_single_source::test_an_installed_copy_has_not_drifted_from_the_template`
  — NEW, caused by this session, and BLOCKED on a decision.** See below.

Also green after the fixes: `tests/test_changelog_is_not_a_transcript.py` **7 passed**,
`tests/test_helm_sync.py` **82 passed**, `tests/test_plan_docs_index.py` +
`tests/test_record_closure_claims.py` **176 passed, 15 skipped**.

### The installed-copy drift, and why it was not fixed

Stripping the prefix from the five sp-only skill templates left `.claude/skills/*/SKILL.md` behind.
The test names the remedy itself: *"Run `sp init --update` or `sp doctor` to refresh it; editing it
in place is lost on the next run."*

**Neither was run, deliberately.** `sp doctor` must not be run here (#210). And `sp init --update`
rewrites any file carrying the `<!-- Generated by sp init -->` marker — which includes
`docs/ai-context/sp/github-workflow.md`, currently modified in the working tree and **not this
session's**. Running it would silently revert that work.

**The unblock is the Captain's:** commit or stash `docs/ai-context/sp/github-workflow.md`, then run
`sp init --update`. Hand-editing `.claude/skills/` is not the fix — it is what the test exists to
catch.

## Key files & links

- `project/TODO.md` — the queue and its order.
- `project/open-decisions.md` — `=>` slots. Only the Captain writes after one.
- `project/plans/plan-terms-on-download-and-register.md` — #252's plan.
- `tmp/issue-helm-collaboration.md` — drafted, unfiled.
- Issues **#252** (new), **#248**, **#249**, **#245**, **#201**, **#181**, **#204**.
