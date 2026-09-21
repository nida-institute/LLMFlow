# HANDOFF — 2026-09-21

## ▶ NEXT ACTION

**Nothing is committed. `dev` is at `30ac1de`, ahead 14 and unpushed, with 21 modified files and
several untracked on top.** The suite is at its known baseline, so the tree is landable — but it
is one session's worth of unrelated work in one diff, and the commit is the Captain's.

Suggested split, smallest risk first. Each is independently green:

1. **The parser work** — `src/llmflow/utils/versification.py`, `src/llmflow/utils/data.py`,
   `tests/test_book_names.py`, `tests/test_parse_bible_reference.py`,
   `tests/test_data_utilities.py`. Fixes the live blocker and unifies two parsers.
2. **The prompt grammar** — `data/prompt-structure.yaml`, `src/llmflow/prompt_structure.py`,
   `src/llmflow/utils/linter.py`, the two `templates/sp/` files,
   `tests/test_prompt_structure_*.py`, `docs/llmflow-language.md`.
3. **#245 groundwork** — `src/llmflow/runner.py`, `src/llmflow/utils/file_io.py`,
   `tests/test_run_manifest.py`, `tests/test_run_pipeline.py`.
4. **Records** — `CHANGELOG.md`, `project/TODO.md`, this file, and the four untracked
   `collab/discourse-flow/*.md` (untracked since 09-16; `plans-are-temporary` wants them tracked
   so deleting them later is safe).

**Then `project/TODO.md`.** Its 0.2.1.28 section carries the queue and its order. Do not read the
queue out of this file.

**A push is the Captain's act and has not been requested.**

---

## Active threads

### 1. #245 — a re-run leaves the previous run's intermediates. **Started, mostly unbuilt**

**Goal.** A re-run deletes only its own previous output, so `/audit-output` stops reading two
runs as one set. The Captain, 2026-09-21: *"this is crucial."*

**State: one piece landed, the rest not written.** The landed piece is the foundation:
`file_io.reset_written_files()` replaces `runner.py`'s `global WRITTEN_FILES; WRITTEN_FILES = []`,
which bound a name in `runner` and left the real list untouched, so it accumulated across every
run in a process. #245 deletes from that list, so a stale entry is a file removed that this run
never wrote.

**Verify.** `hatch run pytest tests/test_run_manifest.py tests/test_run_pipeline.py -q` → 15
passed.

**Next step.** Write the `--rewind-to` guard test **first** — it is the regression that would
hurt most, because replay reads the very files a clean would remove. Then the manifest write, the
keyed delete, `clean_before_run:` in `PIPELINE_SCHEMA`, and `--no-clean`. The full design and the
four rails are in the issue; do not re-derive them.

### 2. The prompt grammar and `sp lint` — done, uncommitted

**State: built and green.** `sp lint` warns on a prompt that does not fit the grammar; position 12
`reference` is declared and rendered into the discipline; the `/audit-prompts` worked example no
longer approves the old shape.

**Verify.** `hatch run pytest tests/test_prompt_structure_conformance.py
tests/test_prompt_structure_single_source.py -q` → 27 passed.
`hatch run sp lint --pipeline pipelines/hello.yaml` warns (expected — see #244).

### 3. Reference parsing — done, uncommitted

**State: built and green.** Multi-word book names parse alone; spaced ranges parse;
`parse_bible_reference` reads `parse_passage_ref` and its 168 duplicate lines are deleted.

**Verify.** `hatch run pytest tests/test_book_names.py -q` → 82 passed, including
`test_every_declared_spelling_parses_as_a_whole_book` over all 341 spellings in 66 books.

---

## In flight / not yet done

- **`dev` ahead 14, unpushed**, tip `30ac1de`. Everything above is uncommitted on top of it.
- **PR #236 cannot be retitled by this agent.** `gh pr edit` returns
  `Resource not accessible by personal access token (updatePullRequest)`. The chosen title and
  the exact command are in `project/TODO.md`. **This token cannot change any PR title, body,
  label or state** — relevant to the whole release process.
- **The reply to discourse-flow is sent**, into their tree, untracked for them:
  `discourse-flow/collab/sp/2026-09-21-the-example-is-fixed-and-lint-now-reads-the-grammar.md`.
- **Four inbound collab notes are untracked here**, the newest being
  `collab/discourse-flow/2026-09-21-parse_passage_ref-refuses-every-book-whose-name-has-a-space.md`.
  Everything it asks for is done, including the exhaustive test it requested by name.
- **Uncommitted and the Captain's, not this session's:** `data/models.json`,
  `docs/ai-context/project/data-sources.md`, `project/0x28.md`, `.cursorrules`, `.windsurfrules`,
  `docs/ai-context/sp/github-workflow.md` and its template twin.
- **`~/.claude/settings.json`** is still modified — the unreviewed one-line change reported at
  session start (a `Write(//Users/jonathan/.claude/projects/**)` permission removed).

## Six tests are RED, all pre-existing

`hatch run pytest -q` → **5673 passed, 6 failed**, plus a network-dependent MCP integration test
that fails only when the server is unreachable. None is from this session:
`test_types.py` (npx broken, so nothing is type-checked), `test_plan_docs_index.py` ×3 (two
untracked 2026-09-17 design documents), `test_product_name_in_prose.py` (hits the Captain's
`data-sources.md`), `test_resource_provisioning.py`.

Two pre-existing `ruff check src/` errors, in `cli_utils.py` and `runner.py`, both untouched here.

## Decisions settled — do not reopen

- **The grammar binds a prompt whose first line is `---`.** Not a `#` heading: binding follows a
  deliberate declaration, so any prompt may use `#` sections without being surprised. Not
  `requires:` as well: a prompt may have zero required variables.
- **The extension point is `reference`, not `extensions` or `appendix`** — a content word says
  what belongs there; a mechanism or position word guides nobody. Design notes are refused there
  because the whole `.gpt` reaches the model.
- **Conformance is a warning, first finding per prompt, sequence once per run.** The Captain saw
  the live output and ruled it fine as is — **do not make it lint-only.**
- **`sp clean` before a run is the wrong fix for #245.** It deletes every parameterisation's
  intermediates (#198's bug, relocated) and breaks `--rewind-to`.
- **Where a book ends is decided by the declaration, not by whitespace.**
- **The CHANGELOG keeps both `## Unreleased` and a dated version section.** That two-section shape
  is enforced by `tests/test_changelog_*`; an attempt to fold them was wrong and was reverted.

## Do NOT

- **Do not run `sp doctor` in this repository** — #210. It is safe in consumer projects, and was
  run in `discourse-flow` this session to refresh installed skills.
- **Do not `git add -A`** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.
- **Do not read a passing suite as type-checked** — `npx` is broken.
- **Do not edit `docs/ai-context/sp/`** — regenerated; the fix belongs in
  `src/llmflow/templates/project/docs/ai-context/sp/`.
- **Do not hand-edit the rendered block in `templates/sp/disciplines/llmflow-prompt-organization.md`**
  — regenerate it from `data/prompt-structure.yaml` via `prompt_structure.render_markdown()`.
- **Do not fix the two `ruff` errors or the `is_whole_book` asymmetry while passing** — each is
  noted and out of scope.
- **Do not run two pytest processes at once** — they share `tmp/pytest`.

## Unfiled, noted only here and in the CHANGELOG

- `linter_config.treat_warnings_as_errors` is documented in two places and implemented nowhere.
- `parse_bible_reference` returns `is_whole_book` on a whole-book result and omits it otherwise.
- `_book_code("Song of Solomon")` is `None` while `Song of Songs` resolves — an alias question
  discourse-flow raised, and a data question for the Captain rather than a bug.

## Key files & links

- `project/TODO.md` — the queue and its order. **#245 is its first entry.**
- Issues **#245** (re-run intermediates), **#244** (replace the starter prompts), **#176** (strip
  frontmatter before the LLM call), **#242** (lint reads the declaration — shipped).
- `data/prompt-structure.yaml` — the grammar, and the pattern to copy: declare once, render, guard.
- `src/llmflow/utils/debug.py` — `run_key_for()` and `manifest.jsonl`, the machinery #245 reuses.
