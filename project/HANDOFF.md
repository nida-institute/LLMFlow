# HANDOFF — 2026-09-28

## ▶ NEXT ACTION

**Three commits, in this order. All three message files are written.**

```sh
git add src/llmflow/pipeline_schema.py src/llmflow/utils/step_outputs.py src/llmflow/utils/linter.py src/llmflow/steps/scripture.py src/llmflow/steps/alignment.py src/llmflow/steps/parallel_passages.py tests/test_named_step_outputs.py tests/test_alignment.py tests/test_parallel_passages_step.py tests/test_scripture_passage_info.py
git commit -F tmp/commit-1.txt

git add pipelines/commentary.yaml prompts/commentary.gpt src/llmflow/templates/project/pipelines src/llmflow/templates/project/prompts data/file-catalog.yaml data/ai-rules.yaml src/llmflow/cli.py src/llmflow/cli_utils.py tests/test_init.py tests/test_linter.py src/llmflow/templates/project/docs/tutorial.md src/llmflow/templates/project/docs/llmflow-language-quickref.md src/llmflow/templates/project/docs/ai-context/sp/command-line.md docs/tutorial.md docs/llmflow-language-quickref.md docs/ai-context/sp/command-line.md docs/ai-context/sp/index.md docs/ai-context/sp/rules.md docs/ai-context/sp/overview.md docs/ai-context/sp/passage-references.md pipelines/hello.yaml pipelines/hello-llmflow.yaml prompts/hello.gpt prompts/reply.gpt src/llmflow/templates/project/pipelines/hello.yaml src/llmflow/templates/project/pipelines/hello-llmflow.yaml src/llmflow/templates/project/prompts/hello.gpt src/llmflow/templates/project/prompts/reply.gpt pipelines/hello-view.md pipelines/hello.html pipelines/hello-llmflow-view.md pipelines/hello-llmflow.html prompts/hello-view.md prompts/hello.html prompts/reply-view.md prompts/reply.html
git commit -F tmp/commit-2.txt

git add project/TODO.md project/plans/design-named-step-outputs.md project/plans/design-sp-help.md project/HANDOFF.md
git commit -F tmp/commit-3.txt
```

Then delete `tmp/commit-1.txt`, `tmp/commit-2.txt` and `tmp/commit-3.txt` **by name** — `tmp/`
holds other sessions' unbacked drafts and is git-ignored, so a sweep is unrecoverable.

**`docs/index.json` will join commits 1 and 2** — `.git/hooks/pre-commit` regenerates and stages
it whenever imports under `src/` change. Expected, not a stray.

**Then: goal 2** — make the CLI the unmistakable external API, starting with `SP_DOC_LINKS` at
`src/llmflow/file_catalog.py:235-243`, which ships wrong guidance to every project today.

`project/TODO.md` holds the queue and its order. Do not read the queue out of this file.

---

## In flight, and whose

Branch `dev`, level with `origin/dev` at `c2f97df`.

| | |
|---|---|
| **this session's, uncommitted** | the three groups above |
| **the Captain's, uncommitted — do not sweep in** | `data/models.json`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md`, `project/plans/README.md`, two tracked `tmp/` deletions, and `docs/ai-context/project/data-sources.md` |
| **unread, arrived today** | `collab/discourse-flow/2026-09-28-the-defect-log-needs-an-info-severity-and-lint-refuses-a-safe-builtin.md` — **inventoried in `project/TODO.md` as goal 3, not acted on** |
| **untracked, not this session's** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, five earlier `collab/discourse-flow/` notes, `collab/human-at-the-helm/` |

**`docs/ai-context/project/data-sources.md` cannot be split by path** — the Captain's paragraph
and this session's two-line product-name fix are one hunk. His to commit or authorise whole.

**Do not `git add -A`** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.

## Known-failing — 4, down from 7

**Verify:** `hatch run pytest tests/ -q -m "not integration" -p no:randomly`
→ **5894 passed, 24 skipped, 4 failed** (2026-09-28, 139s).

`test_global_disciplines`, `test_plan_docs_index`, `test_portable_skills`,
`test_resource_provisioning`. **What each names is in `project/TODO.md`**, first section under
🔥 Active.

Cleared this session: `test_product_name_in_prose`, `test_template_layout`,
`test_prompt_structure_single_source`.

**Do not run two pytest runs at once** — they share `tmp/pytest/` and the second dies with
`INTERNALERROR`.

---

## Decisions

### Settled 2026-09-28 — do not reopen

- **A step's outputs are named, not positional.** `output: [text_bsb=text, reference]` — naming a
  member requests it, an entry may rename it, and a **bare name binds the primary member**, which
  is today's behaviour and is why no existing pipeline changed. **`returns:` is retired.**
  → #263. Implemented; `alignment` and `parallel-passages` migrated in the same change.
- **The language will parse expressions with precedence**, which reclassifies #239 from "a kludge,
  off the critical path" to a **precondition** and answers #241's open question.
- **A "service" is a step type, and "step type" is the name** — so the commands are
  `sp help step-types`, not `sp help services`. → #264.
- **The CLI is the external API; `docs/index.json` maps the implementation** and is not an API for
  users or tests. Goal 2.
- **Goal order:** examples → the CLI-is-the-API work → discourse-flow → ANTLR.

### Open, and blocking

1. **The prompt's examples and §6's sample output need the Captain's approval before they ship.**
   They are domain content. `audits-pattern.md`: a wrong example *"does not read as a rule — it
   reads as a demonstration."* The ❌ counterexamples in `prompts/commentary.gpt` are an AI's
   judgement about what bad commentary looks like.
2. **The `sp run` that proves the example end to end** — calls a model, costs money, his to direct.
3. **Three slots in `design-named-step-outputs.md`** (D1′, D3, and the identifier question) and
   **three in `design-sp-help.md`**.
4. **`tmp/comment-264-vocabulary.md`** — drafted, reviewed, **not posted**.

---

## Do NOT

- **Do not run `sp init --update` in this repository without re-running
  `hatch run python tools/update_ai_context.py` afterwards.** Found today: **two generators write
  `docs/ai-context/sp/rules.md` and they disagree** — `sp init` emits the consumer-project variant
  (`# AI Assistant Rules for This Repo`), `tools/update_ai_context.py` emits this repository's own.
  Caught by `test_ai_rules_single_source`. This is the #210 hazard, still live, and wants an issue.
- **Do not write the starter example's examples as settled.** See *Open* above.
- **Do not regenerate `project/plans/README.md`** — generated, stale, carries the Captain's
  uncommitted hand edit, and would index two plan documents added yesterday.
- **Do not run `sp doctor`** (#210). **Do not** commit, push or merge: `commit-authority`.
- **Do not re-audit what `TODO.md` records for 2026-09-27/28.** Every claim was checked against
  the tree, the suite or `gh issue list`.

## Key files & links

- `project/TODO.md` — the queue. 🧱 *Order of goals* is the top section.
- `pipelines/commentary.yaml`, `prompts/commentary.gpt` — the new starter example. Lints clean
  with **zero** grammar warnings; the first prompt here to conform to `data/prompt-structure.yaml`.
- `project/plans/design-named-step-outputs.md` → #263 · `project/plans/design-sp-help.md` → #264.
- Issues: **#263**, **#264** opened 2026-09-28; comment on **#239** carrying the parser comparison.
