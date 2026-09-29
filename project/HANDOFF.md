# HANDOFF — 2026-09-28

## ▶ NEXT ACTION

**Two commits. Both message files are written.**

```sh
git add src/llmflow/tools/replay.py tests/test_replay_multiline_values.py data/file-catalog.yaml src/llmflow/templates/project/docs/ai-context/sp/audits-pattern.md docs/ai-context/sp/audits-pattern.md docs/ai-context/sp/index.md
git commit -F tmp/commit-1.txt

git add project/TODO.md project/HANDOFF.md
git commit -F tmp/commit-2.txt
```

Then delete `tmp/commit-1.txt` and `tmp/commit-2.txt` **by name**.

**All four of discourse-flow's items are then done**, and a collab note is waiting untracked in
their tree at `collab/sp/2026-09-28-all-four-have-landed.md` — written, not committed there.

**Then: goal 4, ANTLR → #239.** The parser. The comparison and its measurements are already a
comment on that issue; the decisions are ruled. Nothing blocks it but the choice between ANTLR
and Lark, which is partly downstream of #264's editor question.

`project/TODO.md` holds the queue and its order. Do not read the queue out of this file.

---

## In flight, and whose

Branch `dev`, level with `origin/dev` at `78eacc9`.

| | |
|---|---|
| **this session's, uncommitted** | the two groups above — the three defect/lint fixes, then the queue and this file |
| **the Captain's, uncommitted — do not sweep in** | `data/models.json`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md`, `project/plans/README.md`, two tracked `tmp/` deletions, and `docs/ai-context/project/data-sources.md` |
| **unread, arrived 2026-09-28** | `collab/discourse-flow/2026-09-28-the-defect-log-needs-an-info-severity-and-lint-refuses-a-safe-builtin.md` — **inventoried in the queue as goal 3, not acted on** |
| **untracked, not this session's** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, five earlier `collab/discourse-flow/` notes, `collab/human-at-the-helm/` |

**`docs/ai-context/project/data-sources.md` cannot be split by path** — the Captain's paragraph
and a two-line product-name fix are one hunk. His to commit or authorise whole.

**Do not `git add -A`** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.

## Known-failing — 4, down from 7 at the start of the day

**Verify:** `hatch run pytest tests/ -q -m "not integration" -p no:randomly`
→ **5956 passed, 24 skipped, 4 failed** (2026-09-28, 140s).

`test_global_disciplines`, `test_plan_docs_index`, `test_portable_skills`,
`test_resource_provisioning`. **What each names is in `project/TODO.md`**, first section under
🔥 Active.

**`test_types.py` is live again and catching real errors** — it found two in this session's own
code. The queue's note calling it a broken check reporting nothing is **stale**.

**Do not run two pytest runs at once** — they share `tmp/pytest/` and the second dies with
`INTERNALERROR`.

---

## Decisions

### Settled 2026-09-28 — do not reopen

- **Goal order:** examples → the CLI is the external API → discourse-flow → ANTLR.
- **A step's outputs are named, not positional**, with an optional rename; a bare name binds the
  primary member; **`returns:` is retired**. → #263, implemented.
- **The language will parse expressions with precedence** → reclassifies #239 as a precondition.
- **A "service" is a step type**, so the command is `sp help step-types`. → #264.
- **The CLI is THE external API**, and `docs/index.json` maps the implementation and is not an
  API for users or for tests. Both maps now say so in their own `about` fields.
- **The starter example ships**: `pipelines/commentary.yaml`, `prompts/commentary.gpt`. The prompt
  is **approved** — *"the prompt looks good"*.
- **`info` is a third defect severity**, least-to-most-serious, and the logging handler maps onto
  it rather than promoting everything below ERROR to `warning`. **`sp lint` accepts any condition
  the evaluator accepts**, from one declaration both halves read. Three of the four things
  discourse-flow asked for; the fourth is #255 and is also done.
- **Replay aligns on variable sites, not line counts** → #255. A value spanning many lines is no
  different from one spanning none. It still refuses a `--prompt` that did not produce the
  capture, and refuses two adjacent `{{a}}{{b}}` rather than guessing where one value ends.

### Open, and blocking

1. **The `sp run` that proves the starter example end to end.** Costs money; the Captain's to
   direct. Everything else about the example is done and green.
2. **Does the map boundary belong in `data/ai-rules.yaml`** as a rule, or stay as prose plus the
   two artifacts' `about` fields? A rule reaches every project, and `docs/index.json` is a file
   only this repository has. The last open box of goal 2.
3. **Three slots in `design-named-step-outputs.md`** and **three in `design-sp-help.md`**.
4. **`tmp/comment-264-vocabulary.md`** — drafted, reviewed, **not posted**.

---

## Do NOT

- **Do not run `sp init --update` here without re-running
  `hatch run python tools/update_ai_context.py` afterwards.** Two generators write
  `docs/ai-context/sp/rules.md` and they disagree: `sp init` emits the consumer-project variant,
  the tool emits this repository's own. Caught by `test_ai_rules_single_source`. The #210 hazard,
  still live, and it wants an issue.
- **Do not put a renderer in `tools/`.** It is not in the wheel, so `sp init` cannot reach it in
  an installed project. `llmflow.cli_api` exists because that was tried and was wrong.
- **Do not regenerate `project/plans/README.md`** — generated, stale, and carrying the Captain's
  uncommitted hand edit.
- **Do not run `sp doctor`** (#210). **Do not** commit, push or merge: `commit-authority`.

## Key files & links

- `project/TODO.md` — the queue. 🧱 *Order of goals* is the top section.
- `docs/cli-api.json` — the public surface, shipped. `docs/index.json` — the implementation, not.
- `src/llmflow/cli_api.py` — one renderer, two callers: `sp init` and the pre-commit hook.
- `pipelines/commentary.yaml`, `prompts/commentary.gpt` — the starter example; lints clean with
  zero grammar warnings.
- Issues: **#263**, **#264**; a comment on **#239** carrying the parser comparison.
