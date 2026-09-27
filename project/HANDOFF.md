# HANDOFF — 2026-09-27

## ▶ NEXT ACTION

**Run `hatch run sp init --update` in this repository, and commit its output separately.**

The session's work is committed and pushed: `0030ef9`, 25 files, and `dev` is level with
`origin/dev`. Nothing is in flight.

`sp` is not on the bare PATH here — it exists only as the editable install inside the hatch
environment, so it must be `hatch run sp init --update` or a command run from inside
`hatch shell`. Plain `sp` fails with "command not found". Three rendered copies are
behind their templates — `docs/ai-context/sp/overview.md`,
`docs/ai-context/sp/passage-references.md`, `docs/llmflow-language-quickref.md` — because this
session changed the templates and nothing regenerated the copies. `test_template_layout` names
exactly those three, and regenerating is what makes it pass.

**Nothing is at risk, checked rather than assumed.** An earlier handoff said to commit or stash
`docs/ai-context/sp/github-workflow.md` first, on the reasoning that regeneration would
overwrite it. It would not: that file and its template twin carry the same 42-line addition,
and the two are identical both at HEAD and in the working tree, so the copy regenerates from
the template into exactly what is already there. `docs/ai-context/sp/rules.md` is likewise
safe — `cli_utils.ai_rules_doc()` renders it from `data/ai-rules.yaml` at call time, which is
the file the new rule lives in.

Separate commit, because a mechanical regeneration read alongside a real change hides both.
Expect `.cursorrules`, `.windsurfrules` and the `hello.*` starter files to be refreshed too.

**The standing "do not run `sp doctor` here — #210" looks stale, and the Captain has not ruled
on it.** #210's hazard was that `docs/ai-context/overview.md` was one path serving two
documents, so doctor would replace the engine's overview with a project's. That path is no
longer in `data/file-catalog.yaml` at all; the engine's own overview is now
`docs/ai-context/project/overview.md`, catalogued at `file-catalog.yaml:169` as
`policy: create-once`, which neither command overwrites. Note also that the hazard, being in
the catalog, would have applied to `sp init --update` equally — doctor was never the more
dangerous of the two, and it is the more conservative, since it never touches starter examples.
Ask before acting on either reading.

**Then do the survey below.** It was asked for on 2026-09-27 and deliberately not started here,
because it is a wide research task and this session's corrections had begun to cluster around
exactly its failure mode — repeating a written claim without checking it.

`project/TODO.md` holds the queue and its order. Do not read the queue out of this file.

---

## Asked for on 2026-09-27, not started: find the half-finished work

**The request, in the Captain's words:** *"I think we have multiple open items like this — the
examples are half way up the mountain, so is the copyright notice for registrations, I really
don't know what all needs to be done. Please track them down and put checklists in the plan file
for anything only part way finished."*

**The deliverable:** a checklist per partly-finished item, saying what is done and what remains,
in `project/plans/` per `file-organisation`. Propose the filename and get sign-off before
writing — this is a new accumulating document and `plans-are-temporary` applies to it.

**Two he named as examples**, both genuinely mid-climb:

- the starter example replacement → **#244**, ruled and nothing built
- the licence and copyright notice shown on download and registration → **#252**, whose consent
  gate #261 says it reuses

**Sources to mine, none of them read for this purpose yet:**

| where | what it holds |
|---|---|
| `project/TODO.md` (1389 lines) | the queue, with mixed `[x]`/`[ ]` items — the richest source |
| `project/open-decisions.md` (109 lines) | decisions raised and not ruled |
| `project/plans/README.md` | 63 documents, each declaring its own status; scan for *Partly implemented*, *In progress*, *implemented in part* |
| `project/REVIEW.md` (149 lines) | note: `:136-147` names four `tmp/` commit files that no longer exist |
| `gh issue list --state open` | **60 open issues** as of 2026-09-27 |

### Three observations from `sp doctor`, 2026-09-27 — not filed, and not verified

Read from terminal output the Captain pasted after running `sp doctor` in
`ears-to-hear/scriptorium`. **Nobody has checked them against that machine**, so confirm each
before filing. They belong to the survey because each is a thing part-way done.

1. **The summary contradicts itself.** The report ends `No problems found.`, then
   `1 warning(s).`, and the warning is actionable — `Project 'scriptorium' is not registered in
   ~/.sp/projects/`. A green headline over a non-green state is the same class of defect
   `sp/command-line.md` records for skills, where doctor called a project holding ten of eleven
   complete.

2. **That project carries both AI-context layouts at once, and doctor reports `✓`.** Its
   `docs/ai-context/` holds seven pre-split flat documents — `overview.md`, `rules.md`,
   `index.md`, `github-workflow.md`, `audits-pattern.md`, `conventions.md`, `project.md` — plus
   eight `sp/` ones, **and no `project/` half at all**. So two copies of overview, rules, index
   and github-workflow coexist with nothing saying which is live, and `/load-context` there
   would read the flat `rules.md` while `sp/rules.md` is current. With no `project/rules.md`,
   that project also has nowhere to put its own constraints — the absence `sp/rules.md`
   describes as having sent project-specific rules into a memory store nobody read. This is the
   substantial one.

3. **The remedy printed for an unregistered project is `Run sp init`**, which also writes
   starter examples into a project that has been running for months. `sp init --update` looks
   like the right advice there.

Explicable rather than defective, recorded so nobody re-investigates it: `Skills in ~/.sp: 12
of 12 restored` is expected once, because the CHANGELOG's *"skill descriptions no longer open
with a type prefix"* touched eleven and `stage-commits` is new. It should report `✓` on a
second run. **Unverified — no second run was seen.**

**Method, and why it is stated.** Cite a `file:line` or an issue number for every item, and mark
anything you could not confirm as unverified rather than inferring it from a document that says
it. `declared-not-inferred`. A survey is nothing but claims, and an unchecked one sends the
Captain to read the wrong thing — which is the specific failure this session made twice on its
last stretch.

---

## Active threads

### 1 — #258, the `type: parallel-passages` step (DONE, committed at `0030ef9`)

**Goal.** Link a passage to the passages it is parallel to or quotes, so a commentary can cite
that rather than state it from training.

**State.** Built and green. The verse-level `references` half only.

**Verify.** `hatch run pytest tests/test_parallel_passages_step.py tests/test_parallel_passages.py -q`
→ **22 passed**. One of them drives `main(["run", …, "--var", …])` end to end.

**Next step is #244**, the starter example, which consumes this. Queued in `project/TODO.md`.

### 2 — the one-surface ruling (DONE, committed at `0030ef9`)

**Goal.** A project reaches the engine through the `sp` command line and the pipeline language,
and shipped material shows none of our Python.

**State.** Recorded as rule `the-language-is-the-whole-surface` in `data/ai-rules.yaml`;
`docs/ai-context/sp/rules.md` regenerated from it. Five shipped files changed.

**Verify.** `hatch run pytest tests/test_shipped_context_names_one_surface.py -q` → **77 passed**.
`grep -rn "import llmflow\|llmflow\.utils" src/llmflow/templates/` returns nothing.

---

## In flight, and whose

Branch `dev`, **level with `origin/dev` at `0030ef9`.** Nothing of this session's is
outstanding: it went in as one commit of 25 files, `git show 0030ef9` to read it.

| | |
|---|---|
| **this session's** | all committed and pushed at `0030ef9` |
| **the Captain's, uncommitted — do not sweep in** | `data/models.json`, `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md`, `project/plans/README.md`, and two tracked deletions, `tmp/commit-msg-helm.txt` and `tmp/commit-msg-sp.txt`, whose origin is unknown |
| **untracked, not this session's** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, five `collab/discourse-flow/` notes, `collab/human-at-the-helm/` |

**Do not `git add -A`** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.

---

## Decisions

### Settled 2026-09-26 — do not reopen

- **A group is returned whole, and groups are not collapsed.** `MRK 1:2` sits in two groups with
  identical NT members, one also naming `MAL 3:1`. Both are returned: merging them asserts a
  judgment the database never makes, and no reader could then tell "Mark quotes Malachi" from
  "Mark runs parallel to Matthew and Luke".
- **`returns: [references]` is the reference list only.** The per-word digits index UBSGNT5, not
  the resource asked about, so nothing can read them until the MARBLE join exists — the reason
  `syntax` carries no `rule` or `nodeId`. `returns: [words]` is declared in the schema and
  refused at run time.
- **`words` is refused, never approximated.** Counting positions instead of joining through
  MARBLE is wrong about one row in eleven, and silently.
- **One surface, not two.** The shipped context described the Python API as a second surface;
  a project told about one builds against a contract nobody offered it.
- **Tests state shapes, not measurements.** No assertion names a figure read off the real UBS
  database: that would freeze a reader defect in as the expected answer and turn a correct
  engine red on the next UBS release. Measurements belong in #258.
- **The `=>` slots in `plan-starter-example-commentary.md` §6 and D4 are answered.** Supply the
  cross-reference material; the OT half ships.

### Open, and blocking

1. **The starter example's reference step.** `plan-starter-example-commentary.md` §5 names
   `llmflow.utils.data.parse_bible_reference`, which rule `the-language-is-the-whole-surface`
   now forbids in an example. No step type returns `passage_info`, so this is either a construct
   to add or a step to drop. #244's call; the plan's `Status:` line says so.
2. **The CHANGELOG entry for `23d9d74`** — still unwritten. This session's entry covers the step,
   not the reader that landed before it.

---

## Do NOT

- **Do not run `sp doctor`** — #210. **Do not run `sp init --update`** before the Captain's
  `github-workflow.md` is committed or stashed.
- **Do not build the word-level MARBLE join.** It looks like the next step and is not: #258's
  open questions 2 and 4 are unanswered, and #244 needs only `returns: [references]`.
- **Do not fix the seven failing tests as a batch.** They predate this session — see below.
- **Do not write a verse comparison, a reference parser, or a scheme mapper.** Search
  `docs/index.json` first.
- **Do not sweep `tmp/`** — `tmp/index.md` justifies each survivor. The one file this session
  added, `tmp/commit-msg-258-one-surface.txt`, is deleted once the commit exists.

## Known-failing

`hatch run pytest tests/ -q -m "not integration" -p no:randomly` → **5878 passed, 24 skipped,
7 failed**. Down from 9 before this session; none of the seven is this session's:
`test_global_disciplines`, `test_plan_docs_index`, `test_portable_skills`,
`test_product_name_in_prose`, `test_prompt_structure_single_source`,
`test_resource_provisioning`, `test_template_layout`.

`test_template_layout` names three stale copies rather than one — that widening is this
session's, and `sp init --update` is its remedy (see NEXT ACTION).

## Key files & links

- `project/TODO.md` — the queue and its order.
- `project/plans/plan-starter-example-commentary.md` — the work order for #244, now `ruled`.
- `tmp/commit-msg-258-one-surface.txt` — the commit message, delete after committing.
- Issues: **#258** (the step, open questions 2 and 4 still open), **#244** (the example).
