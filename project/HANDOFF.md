# HANDOFF — 2026-09-21

## ▶ NEXT ACTION

**Commit the uncommitted set.** It is coherent, green, and nothing else should start on top of it.
`dev` is at `2acb460`, **ahead 21 and unpushed**, with 8 modified and 1 new file on top (plus four
that are the Captain's, listed below).

The set is one change: `docstrings-say-what-not-why` broadened to cover `#` comments, the two
guards that hold it, the `/load-context` précis change, and the CHANGELOG entry for both.

- `data/ai-rules.yaml`, `docs/ai-context/sp/rules.md` (regenerated — never hand-edit)
- `tests/test_docstrings_say_what_not_why.py`, `tests/test_code_pointers_resolve.py` (new)
- `tests/test_shipped_skills_name_real_paths.py`, `src/llmflow/templates/sp/skills/load-context/SKILL.md`
- `data/helm-sync.yaml`, `CHANGELOG.md`, `project/TODO.md`
- `src/llmflow/runner.py`, `src/llmflow/utils/run_manifest.py` — comment trims only, no behaviour

**The commit message is not yet written to a file.** Write it, then hand over the command. The
commit, the push and the merge are the Captain's (`commit-authority`).

**Verify before committing:** `hatch run pytest -q` → **5698 passed, 6 failed**. Those six are the
known baseline — `test_types` (npx broken), `test_plan_docs_index` ×3, `test_product_name_in_prose`
(hits the Captain's `data-sources.md`), `test_resource_provisioning`. A seventh,
`tests/integration/test_mcp_batch_calls.py`, fails only when the network is down.

**Then `project/TODO.md`.** Its 0.2.1.28 section carries the queue and its order. Do not read the
queue out of this file.

---

## Active threads

### 1. Two features must ship in 0.2.1.28 — **ruled, unbuilt, and they gate the release**

The Captain, 2026-09-21, of discourse-flow's asks: both are built for this release rather than
filed and deferred. **PR #236 now waits on them.**

**State: issue bodies drafted, nothing created, no code.**

- `tmp/issue-scripture-window.md` — window a scripture document by token budget, verse-sid cursor
- `tmp/issue-artifact-conformance.md` — check a produced artifact against the schema its pipeline
  declares, recording a defect rather than raising

Each carries four `=>` slots that are **design calls for the Captain**, not implementation detail.

**Next step.** Get approval of the bodies, then `gh issue create` (`issues-need-approval` — never
create silently), then the `=>` answers, then tests first.

**⚠️ `tmp/` is git-ignored, so those two drafts are the only copy and no commit protects them.**

**Verify:** `ls tmp/issue-*.md`; `gh issue list --repo nida-institute/LLMFlow --search "window"`
returns nothing yet.

### 2. An unanswered inbound collab — **nobody has triaged it**

`collab/discourse-flow/2026-09-21-a-whole-chapter-has-no-extent-in-parse_passage_ref.md`,
**untracked**, arrived late in the session and was read but not acted on.

`parse_passage_ref('Mark 4')` returns `start_verse=None, end_verse=None`;
`parse_bible_reference('Mark 4')` returns `1`–`41` with `is_whole_chapter: True`. They ask that the
two agree, **or** that the two kinds of nothing be distinguishable per `say-which-kind-of-nothing`.

This is the **second** input on which those two parsers differ; the first was the space-in-book-name
crash fixed in `a7a0a66`. Whether they are meant to converge is undecided and is the Captain's.

**Next step.** Triage: reply, issue, or queue entry. Not yet filed anywhere.

**Verify:** `hatch run python -c` is not how to check this — use a heredoc, and call both functions
on `'Mark 4'`.

### 3. `/load-context` — changed here, not yet propagated

**State: template changed and green; the two stores untouched deliberately.**

`sp doctor` restores a *changed* file, not merely an absent one (`doctor.py` `_group_check`:
"Missing or changed"), so the Captain runs `sp doctor` in each project to propagate. **Not in this
repository** — #210.

Two things a later session will otherwise rediscover: `doctor` will leave `~/.claude` dirty, which
is expected rather than an unreviewed write; and the skill is shared with Human at the Helm under a
permitted divergence, so `data/helm-sync.yaml` was refreshed with `--refresh-record` and **Helm's
copy is untouched**. Do not run `--apply` on it.

---

## In flight / not yet done

- **`dev` ahead 21, unpushed**, tip `2acb460` (`#245`, committed by the Captain this session).
- **A push has not been requested** and is the Captain's own act.
- **The reply to discourse-flow is sent**, into their tree, untracked for them:
  `discourse-flow/collab/sp/2026-09-21-the-defect-log-already-shipped.md`. Our 09-21 reply sits
  untracked there too — if they sweep, both vanish.
- **Two inbound collab notes untracked here**, both 2026-09-21: the defect-log one (answered) and
  the chapter-extent one (thread 2, unanswered). `plans-are-temporary` wants them tracked.
- **Uncommitted and the Captain's, not this session's:** `data/models.json`,
  `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its
  template twin, `.cursorrules`, `.windsurfrules`, `project/0x28.md`.
- **`~/.claude/settings.json` is still modified** — the unreviewed one-line change reported at
  session start (a `Write(//Users/jonathan/.claude/projects/**)` permission removed). Not this
  session's doing; `cgit restore settings.json` reverts it.

## Decisions settled — do not reopen

- **The rule covers the container it is written in.** A design note in a `#` comment is the same
  defect as one in a docstring. The guard already read both; only the wording was narrow.
- **A cross-reference in code must resolve**, and the document it names must be committed —
  otherwise `git show <commit>^:<path>` cannot return the version the comment was written against.
- **`#245`'s manifest lives at `<intermediate>/.sp-runs/<pipeline>/<run key>.json`** — not under
  `debug/`, which `_clear_debug_dir` empties at the start of every run.
- **`#245` uses a new `utils/run_manifest.py`**, not an extension of `debug.py`: a write manifest
  is not debug evidence.
- **The CHANGELOG is user-facing feature notes.** No names, no rulings, no session narrative —
  "high level features, not a copy of our discussions". `tests/test_changelog_is_not_a_transcript.py`
  enforces the voice.
- **The pre-split flat context paths in `/load-context` are deliberate**, and live in
  `UNSPLIT_EQUIVALENT`. That decision predates this session; it was merely incomplete.

## Do NOT

- **Do not run `sp doctor` in this repository** — #210. Safe in consumer projects.
- **Do not `git add -A`** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.
- **Do not run `tools/sync_helm.py --apply`** for `load-context` or `commit-ready` — both are
  ruled divergences. `--refresh-record` is the command.
- **Do not edit `docs/ai-context/sp/`** — regenerated by `tools/update_ai_context.py`.
- **Do not fix the two `ruff` errors** (`cli_utils.py` F401, `runner.py` I001) — both pre-existing
  and out of scope. `runner.py`'s was verified present at `HEAD` before this session's change.
- **Do not read a passing suite as type-checked** — `npx` is broken, so `test_types` reports
  nothing rather than reporting clean.
- **Do not run two pytest processes at once** — they share `tmp/pytest`.
- **Looks like a next step but is not:** merging PR #236. It now waits on the two unbuilt features
  above, and the merge is the Captain's act regardless.

## Key files & links

- `project/TODO.md` — the queue and its order.
- `tmp/issue-scripture-window.md`, `tmp/issue-artifact-conformance.md` — drafted, uncreated,
  **in a git-ignored directory**.
- `collab/discourse-flow/2026-09-21-a-whole-chapter-has-no-extent-in-parse_passage_ref.md` — the
  untriaged thread.
- Issues **#245** (shipped this session), **#176**, **#244**, **#236** (the release PR), **#232**
  (the defect log discourse-flow can now delete their copy of), **#241** (governs where a new
  language operation belongs — bears on the scripture window).
