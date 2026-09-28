# HANDOFF — 2026-09-28

## ▶ NEXT ACTION

**Two commits. Both message files are written.**

```sh
git add src/llmflow/file_catalog.py src/llmflow/cli_api.py data/file-catalog.yaml docs/cli-api.json docs/index.json docs/python-api.md docs/ai-context/project/index.md docs/ai-context/sp/index.md tools/index_cli_api.py tools/index_signatures.py tools/hooks/pre-commit tests/test_cli_api_map.py tests/test_internals_map_declares_itself.py tests/test_shipped_context_names_one_surface.py tests/test_init.py
git commit -F tmp/commit-1.txt

git add project/TODO.md project/HANDOFF.md
git commit -F tmp/commit-2.txt
```

Then delete `tmp/commit-1.txt` and `tmp/commit-2.txt` **by name** — `tmp/` holds other sessions'
unbacked drafts and is git-ignored, so a sweep is unrecoverable.

**Then run this once, and it is the Captain's to run**, because it changes his git config:

```sh
git config core.hooksPath tools/hooks
```

Until it does, **neither generated map refreshes on commit.** The live hook is
`.git/hooks/pre-commit`, a copy nobody has updated; the tracked source is `tools/hooks/pre-commit`
and it now regenerates both. Both maps have staleness tests, so drift fails loudly rather than
silently — but the hook is the mechanism.

**Then: goal 3, discourse-flow.** Four items inventoried in `project/TODO.md`; the expensive one
for them is #255, replay, which costs them ~$22 per prompt edit today.

`project/TODO.md` holds the queue and its order. Do not read the queue out of this file.

---

## In flight, and whose

Branch `dev`, level with `origin/dev` at `94f1edb`.

| | |
|---|---|
| **this session's, uncommitted** | the two groups above |
| **the Captain's, uncommitted — do not sweep in** | `data/models.json`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md`, `project/plans/README.md`, two tracked `tmp/` deletions, and `docs/ai-context/project/data-sources.md` |
| **unread, arrived 2026-09-28** | `collab/discourse-flow/2026-09-28-the-defect-log-needs-an-info-severity-and-lint-refuses-a-safe-builtin.md` — **inventoried in the queue as goal 3, not acted on** |
| **untracked, not this session's** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, five earlier `collab/discourse-flow/` notes, `collab/human-at-the-helm/` |

**`docs/ai-context/project/data-sources.md` cannot be split by path** — the Captain's paragraph
and a two-line product-name fix are one hunk. His to commit or authorise whole.

**Do not `git add -A`** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.

## Known-failing — 4, down from 7 at the start of the day

**Verify:** `hatch run pytest tests/ -q -m "not integration" -p no:randomly`
→ **5916 passed, 24 skipped, 4 failed** (2026-09-28, 138s).

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
