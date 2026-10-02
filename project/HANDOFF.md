# HANDOFF — 2026-10-01

## ▶ NEXT ACTION

**Land this session's work. Three steps, in order, the first needing the Captain's word:**

1. **Regenerate the rendered copies — ask first.** The quickref template was fixed; its rendered
   copy `docs/llmflow-language-quickref.md` was not, and two tests read it. The route is
   `hatch run sp init --update` then `hatch run python tools/update_ai_context.py` (**both**, in
   that order — `sp init --update` alone overwrites `docs/ai-context/sp/rules.md` with the
   consumer variant). `sp init --update` also writes `~/.sp`, which **is the Captain's store**;
   he declined that once today for another repository. Ask, and say it would also bring
   `~/.sp/disciplines/sp-debugging.md` up to date.
2. **`tests/test_parallel_passages_step.py:254` carries a date** (`Ruled 2026-09-29: …`), which
   `test_docstrings_say_what_not_why` refuses. That file is the **2026-09-30 session's**
   uncommitted fix, not this one's. Removing the date is a one-line change; it still needs his
   yes.
3. **`/stage-commits`.** It must ask whose each change is — the tree holds four parties' work,
   listed below. Do not sweep.

Then the release walkthrough: **`project/TODO.md` → 🚢 THE NEXT RELEASE**, item 1. He asked for
it one item at a time, in that order.

---

## Active threads

### 1. This session's pass — built, green where it can be, uncommitted

**Goal.** Contradictions found at session start, then widened by the Captain: the positional
`output:` form and retired `returns:` in the docs; dotted `{{…}}` taught as working; stale
debug-dump filenames; the `<!-- -->` prompt header retired (**breaking**); lint expanding mixins
the way a run does; quickref wrong statements and a mixins section. `CHANGELOG.md` Unreleased →
Fixed and Removed has the whole of it.

**State.** Done, uncommitted. Suite: **11 failed, 5985 passed, 24 skipped**
(`hatch run pytest tests/ -q -m "not integration" -p no:randomly`, 140 s). Two of the 11 are this
session's and clear on regeneration (NEXT ACTION step 1):
`test_doc_examples_lint::…name_declared_output_members` and
`test_template_layout::…matches_its_own_templates`.

**Verify.**
`hatch run pytest tests/test_prompt_header_is_frontmatter.py tests/test_lint_expands_mixins.py tests/test_doc_examples_lint.py -q -p no:randomly`
→ 15 + 1 pass, 1 fails on the rendered quickref only.

### 2. The nine failures that were already red

Not this session's; none touches a file it changed. Listed so nobody attributes them:
`test_helm_sync` ×3 (Helm parity — now **out of this release**, see TODO), `test_global_disciplines`
and `test_portable_skills` (`stage-commits` unclassified, S1), `test_resource_provisioning`
(vendored catalog behind upstream), `test_rules_are_cited_by_id` ×2 ("rule 1" in
`project/TODO.md:85` and `project/audits/audit-one-surface.md`), and the docstring date above.

---

## In flight / not yet done

Branch `dev`, level with `origin/dev` at **`c5e88fa`**. Nothing committed this session.

| whose | paths |
|---|---|
| **this session** | `src/llmflow/utils/linter.py`, `src/llmflow/steps/llm.py`; `src/llmflow/templates/project/docs/llmflow-language-quickref.md`, `src/llmflow/templates/sp/disciplines/sp-debugging.md`; `docs/sp-language.md`, `docs/getting-started.md`, `docs/architecture.md`, `docs/ai-context/project/data-shapes.md`; `CHANGELOG.md`, `project/TODO.md`, `project/HANDOFF.md`; new `tests/test_prompt_header_is_frontmatter.py`, `tests/test_lint_expands_mixins.py`; `tests/test_doc_examples_lint.py`; fixtures in `tests/conftest.py`, `test_lint_structured_output.py`, `test_linter_append_to.py`, `test_linter_integration.py`, `test_prompt_contract_enforcement.py`, `test_xpath_integration.py` |
| **2026-09-30 session** | `src/llmflow/utils/parallel_passages.py`, `tests/test_parallel_passages_step.py` — the warning names how to obtain the dataset |
| **the Captain's — do not stage** | `data/models.json`, `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md` |
| **untracked, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, seven `collab/discourse-flow/` notes, `collab/human-at-the-helm/` |
| **deliberately unstaged** | `scripts/representation-grid/{cells/,grid.json,grid.tsv}` — Q5 of `design-representation-workbench.md` |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

**Done elsewhere today, nothing outstanding:** `sil-translator-notes` was refreshed from the dev
engine with `~/.sp` redirected, and the Captain committed it — `c18f427`, level with
`origin/dev`. **#266** (`sp` cannot tell a user a newer build exists) was filed on his approval.

---

## Decisions

Today's rulings are in **`project/TODO.md` → 🚢 THE NEXT RELEASE**, each with its why. Two
corrections to the previous handoff, so they are not reopened:

- **Thread 1 of the 2026-09-30 handoff is withdrawn.** It said `prompts/commentary.gpt` "must be
  redone against Ears to Hear". The Captain, 2026-10-01: Ears to Hear is a client, and that work
  belongs in `ears-to-hear`. The A/B "Prepare the way" question and the two-headings question at
  `commentary.gpt:105,109` dissolve with it. The prompt stays as approved 2026-09-28.
- **The `\q` loss is not established as an engine defect.** This session called it one without
  evidence. What is known is in TODO under the release section.

**Still open, his, carried from 2026-09-29:** whether `2591d3e` and `7c4d133` — pushed with
messages naming files they did not contain, repaired by `c5e88fa` — want correcting. Nothing
rewrites history unasked.

---

## Do NOT

- **Do not run `sp init --update` here without `tools/update_ai_context.py` straight after**, and
  not at all without the Captain's word — it writes `~/.sp`. **Do not run `sp doctor`** (#210).
- **Do not carry a client's methodology into the engine.** Ears to Hear's is theirs. Do not name
  clients in anything that leaves this repository (`no-stakeholder-speculation`).
- **Do not take a written claim on trust.** Five of nine corrections this session were exactly
  that — `command-line.md`, a TODO line, CLAUDE.md's `apply_template`, and two inherited framings.
  Check the code or ask.
- **Do not fix the untriaged findings quietly.** TODO lists them; each wants an issue or a ruling.

## Key files & links

- `project/TODO.md` → **🚢 THE NEXT RELEASE** — the queue for this release, and today's rulings
- `CHANGELOG.md` → Unreleased → Fixed / Removed — what this session built
- `project/plans/plan-starter-example-commentary.md` §7 — release item 1
- Issues: **#244**, **#176**, **#252**, **#266** (filed today), **#263**/**#242** (built, close at merge)
