# HANDOFF — 2026-09-27

## ▶ NEXT ACTION

**Commit the staged package.** The message is written and the command is ready:

```sh
git commit -F tmp/commit-msg-258-one-surface.txt
git show HEAD
```

`git show HEAD`, not `git show --stat HEAD` — the Captain reads the diffs, and a file list is
not a review.

If nothing is staged yet, the `git add` list is in the same session's handover and can be
rebuilt from **In flight** below. Delete `tmp/commit-msg-258-one-surface.txt` once the commit
exists.

**Then run `sp init --update`, and commit its output separately.** Three rendered copies are
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

**Do not run `sp doctor` here** — #210.

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

**Method, and why it is stated.** Cite a `file:line` or an issue number for every item, and mark
anything you could not confirm as unverified rather than inferring it from a document that says
it. `declared-not-inferred`. A survey is nothing but claims, and an unchecked one sends the
Captain to read the wrong thing — which is the specific failure this session made twice on its
last stretch.

---

## Active threads

### 1 — #258, the `type: parallel-passages` step (DONE, uncommitted)

**Goal.** Link a passage to the passages it is parallel to or quotes, so a commentary can cite
that rather than state it from training.

**State.** Built and green. The verse-level `references` half only.

**Verify.** `hatch run pytest tests/test_parallel_passages_step.py tests/test_parallel_passages.py -q`
→ **22 passed**. One of them drives `main(["run", …, "--var", …])` end to end.

**Next step is #244**, the starter example, which consumes this. Queued in `project/TODO.md`.

### 2 — the one-surface ruling (DONE, uncommitted)

**Goal.** A project reaches the engine through the `sp` command line and the pipeline language,
and shipped material shows none of our Python.

**State.** Recorded as rule `the-language-is-the-whole-surface` in `data/ai-rules.yaml`;
`docs/ai-context/sp/rules.md` regenerated from it. Five shipped files changed.

**Verify.** `hatch run pytest tests/test_shipped_context_names_one_surface.py -q` → **77 passed**.
`grep -rn "import llmflow\|llmflow\.utils" src/llmflow/templates/` returns nothing.

---

## In flight, and whose

Branch `dev`, **ahead of `origin/dev` by 1** — `cd5108a` is unpushed. `origin/dev` is `23d9d74`.

| | |
|---|---|
| **this session's, staged for the commit above** | `src/llmflow/steps/parallel_passages.py` (new), `tests/test_parallel_passages_step.py` (new), `tests/test_shipped_context_names_one_surface.py` (new), `src/llmflow/utils/parallel_passages.py`, `utils/scripture.py`, `pipeline_schema.py`, `runner.py`, `resources.py`, `cli.py`, `tests/test_parallel_passages.py`, `tests/test_ai_rules_classification.py`, `data/ai-rules.yaml`, `docs/ai-context/sp/rules.md`, `docs/ai-context/project/index.md`, `docs/llmflow-language.md`, five files under `src/llmflow/templates/`, `CHANGELOG.md` |
| **mixed — carries both parties' work** | `project/plans/plan-starter-example-commentary.md`: the Captain's two `=>` answers, plus this session's one-line `Status:` change |
| **the Captain's, pre-existing — do not sweep in** | `data/models.json`, `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md`, `project/plans/README.md` |
| **untracked, not this session's** | `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py` |

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
