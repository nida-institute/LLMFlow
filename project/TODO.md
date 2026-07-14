# Project TODO

> **Convention:** Active work lives here. Bugs and permanent decisions go to
> [GitHub Issues](https://github.com/nida-institute/LLMFlow/issues).
> Link issues with `→ #N` so this file doesn't duplicate GitHub.
> Board: https://github.com/orgs/nida-institute/projects/13

## 🔥 Active

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
- [ ] **Release** — re-cut `v0.2.1.20` with for/in (delete stale tag, re-tag the merge commit)

### 🔥 Monday priorities
- [ ] **Fix GUI Content Lifecycle** — Content Lifecycle page displays blank, needs debugging
- [ ] **Publish v0.2.1.14 to PyPI** — Built and tagged, needs PyPI credentials
  - Reset password at https://pypi.org/account/reset-password/ (jonathan.robie@gmail.com)
  - Create API token scoped to `llmflow` project
  - Run: `hatch publish` (username: `__token__`, password: token)

### 🎓 Workshop readiness (main next goal)
- [ ] Build Mac + Windows installers via GitHub Actions CI → #32
  - PyInstaller spec already exists (`llmflow.spec`)
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

### 🎓 Workshop readiness
- [ ] Replace hello-world example with a domain-relevant pipeline
      (e.g. translation notes for a Bible passage, or back-translation check)
- [ ] Polish error messages — every ❌ should say what to fix, not just what went wrong
- [ ] Workshop handout: 1-page "what is this and why do I care"
- [ ] API key story for workshop: shared org key so participants don't each need one

### 🚀 Publishing
- [ ] Clean up repo for public release → #33
  (metadata, data licensing, .gitignore gaps, README, history audit)
- [ ] Publish to PyPI as `llmflow` (name is currently available)

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
