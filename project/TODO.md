# Project TODO

> **Convention:** Active work lives here. Bugs and permanent decisions go to
> [GitHub Issues](https://github.com/nida-institute/LLMFlow/issues).
> Link issues with `→ #N` so this file doesn't duplicate GitHub.
> Board: https://github.com/orgs/nida-institute/projects/13

## 🔥 Active

### ⚠️ Versification — a reference means different verses in different editions → #203
> **Blocks OT use of `sil-translator-notes`.** WLC and BSB disagree by two verses on `PSA 51:1`
> and the run reports success. Fix via the Copenhagen Alliance specification, cloned at
> `~/github/copenhagen-alliance/versification-specification`.

### 📖 Scripture editions — core landed, wiring incomplete → #200
> Commits are parked on the **local** tag `wip/scripture-200` (`05d75a5`, `34c7931`) and are
> **not on `dev`**, which was reset to `cb72cb7` so the release could ship without them.
> Cherry-pick after PR #199 merges. Design: `project/plans/design-scripture-editions.md`.
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
> Paul cloned `sil-translator-notes`, ran `sp init`, ran `/load-context`, and got **HTTP 400 with
> no body**. Getting him to a working state took a hand-built zip of the portable parts of `~/.sp/`
> (`tmp/sp-for-paul.zip`), copying `~/.sp/skills` → `~/.claude/skills`, hand-editing three edition
> files to strip another machine's absolute paths, and patching a USFM file — and it still did not
> work. Interim workaround, `sil-translator-notes` only: `CLAUDE.md.template` (`95955d9`).

Each item is its own bug:
- [ ] **Nothing provides `CLAUDE.md`** — required by the skill, gitignored by convention, created
      by nothing. `sp init` should scaffold it and never overwrite an existing one
- [ ] **A missing file 400s instead of skipping cleanly** — an empty read yields an empty content
      block the API rejects with no body. Unattributable: Paul saw an API error, not a missing file
- [ ] **Skills are per-user and invisible** — they live in `~/.claude/skills/`, not the repo.
      Nothing tells a contributor this is required and nothing verifies it worked
- [ ] **Editions are not portable** — `~/.sp/editions/*.yaml` carry absolute paths and must be
      hand-edited. There is no per-machine registration flow
- [ ] **No verification step** — `sp doctor` or `sp init --check`: are skills installed, are
      editions registered and resolvable, is `CLAUDE.md` present
- [ ] **Decision needed:** `sp init` destroys hand-written AI context. It regenerates `index.md`,
      `overview.md`, `rules.md` and `github-workflow.md`; only `project.md` is protected
      (`cli_utils.py:1891`). Either merge instead of overwrite, or say plainly that everything
      durable goes in `project.md`
- [ ] **Nothing tests a clean machine** — 2620 tests pass and none caught any of the above. Needs a
      run from a clone with an empty `HOME`, plus a committed fixture-edition TSV so `sp lint`'s
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
