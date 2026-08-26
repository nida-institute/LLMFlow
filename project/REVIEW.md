# REVIEW — the uncommitted working tree, 2026-08-25

101 changed paths, nothing committed. All paths below are relative to the repository root.

Suite: **2964 passed, 26 skipped, 0 failed** (~95s), measured three times. `ruff` clean on every
changed Python file. Two gates are **not** met — see §6.

---

## 1. Read these six. Everything else is mechanical.

| # | file | why it matters |
|---|---|---|
| 1 | `tests/conftest.py` | New `pytest_configure` hook and autouse fixtures change how **every** test in the suite runs. If this is wrong, every other green result here is unreliable. |
| 2 | `src/llmflow/cli_utils.py` — `_write_catalogued_files`, ~line 1707 | Decides which files `sp init` writes and which `--update` overwrites **in every consumer project**. A wrong `policy` check silently overwrites someone's authored file — the failure that cost `discourse-flow` two files on 2026-08-23. |
| 3 | `data/file-catalog.yaml` | 22 changed lines: four template globs, and the new `audits-pattern.md` row — the first project-scoped `source: template` entry, and therefore the precedent #211 will follow 22 more times. |
| 4 | `docs/ai-context/sp/audits-pattern.md` (+350 lines) | **Content that ships into every project**, and it states other repositories' measured results as fact. The only thing here whose errors propagate outward. |
| 5 | `docs/ai-context/project/index.md` (new) | Hand-authored, this repository's own map, and yours to own rather than mine to get right. |
| 6 | `tools/update_ai_context.py` (−147 lines) | Reduced from three generated documents to one. Worth one pass to confirm nothing needed went with the deleted tuples. |

**Also worth a look, smaller:** `pytest.ini` (two settings plus comments) and
`src/llmflow/paths.py` (new, 42 lines, one function).

---

## 2. Skim these. Nothing to decide.

| group | paths | what changed |
|---|---|---|
| Template moves | 22 files under `src/llmflow/templates/sp/` | **Verified byte-identical** to their old paths under `sp-disciplines/`, `sp-root/`, `sp-skills/`. Pure renames. |
| The one edited template | `src/llmflow/templates/sp/skills/load-context/SKILL.md` | The exception — reads the standard three documents on both ai-context halves, every read guarded. |
| Document moves | 4 files, `docs/ai-context/sp/*` → `docs/ai-context/project/*` | `data-shapes.md`, `data-sources.md`, `gui-architecture.md`, `paratext-schemas.md`. Content unchanged; `CLAUDE.md` cites `gui-architecture.md` by name. |
| Test path updates | 13 files under `tests/` | `test_catalog.py`, `test_commit_ready_gate.py`, `test_doctor.py`, `test_download_data.py`, `test_global_disciplines.py`, `test_helm_sync.py`, `test_init.py`, `test_init_noninteractive.py`, `test_package_resources.py`, `test_portable_disciplines.py`, `test_portable_skills.py`, `test_registry.py`, `test_skill_command_output.py`, `test_sp_lock.py`, `test_two_indexes.py` |
| Store-path call sites | `src/llmflow/registry.py`, `src/llmflow/download_data.py`, `src/llmflow/doctor.py` | Now call `paths.sp_home()` instead of computing `~/.sp` |
| Sync record | `data/helm-sync.yaml` | Hash update plus an annotation that asks you a question — §5 |

---

## 3. Deletions — confirm you want each

| path | why |
|---|---|
| `docs/ai-context/sp/README.md` | Folded into `sp/overview.md` per your Q2 ruling, *"Fold it in"* |
| `docs/ai-context/sp/json-reliability.md` | Deleted per your R10. Its durable content is already in `docs/llmflow-language.md`; its headline model advice was contradicted by 200+ measured calls |
| `tests/test_catalog_covers_init.py` | Superseded by `tests/test_init_writes_the_catalog.py` |

**Note on authority:** files under `docs/ai-context/` were modified *and deleted* here, which
`CLAUDE.md` prohibits the AI from doing. It was done by the previous session under your recorded
rulings R2, R10 and Q2 in `project/plans/design-ai-context-layout.md` — not on an AI's initiative.
It is still worth knowing that this is part of what you are approving.

---

## 4. New files

**Tests** (7): `tests/test_ai_context_layout.py` (12 tests) · `tests/test_template_layout.py` (6) ·
`tests/test_sp_home_is_relocatable.py` (4) · `tests/test_pytest_writes_inside_the_repository.py` (8) ·
`tests/test_init_writes_the_catalog.py` (3) · `tests/test_init_is_idempotent.py` (3) ·
`tests/test_doctor_help_is_honest.py` (2)

**Source** (1): `src/llmflow/paths.py`

**Documents** (4): `docs/ai-context/project/index.md` ·
`src/llmflow/templates/project/docs/ai-context/sp/audits-pattern.md` ·
`project/plans/design-ai-context-layout.md` · `project/plans/design-shipping-the-audit-method.md`

---

## 5. Three things that need your word, not just review

1. **`data/helm-sync.yaml`** carries a question addressed to you. Your 2026-08-24 permission
   (*"I permit this difference"*) covered a `load-context` divergence across three files. It is now
   six, because the standard set became three documents per half. Whether the permission still
   covers the wider difference is yours to say.

2. **Q6 of `project/plans/design-ai-context-layout.md`** — the mechanical half answered itself;
   your actual question did not: *"how useful are these two documents for LLMs working with sp on
   projects?"*

3. **`~/.sp` has one uncommitted file** — `skills/load-context/SKILL.md`, byte-identical to
   `src/llmflow/templates/sp/skills/load-context/SKILL.md`. The store carries the new version.
   Committing it there is your act.

---

## 6. Gates

| gate | state |
|---|---|
| Full suite | **2964 passed, 26 skipped, 0 failed**, three runs |
| `ruff` | clean on all changed Python |
| CHANGELOG | updated, **and being rewritten to the `github-workflow.md` convention** — in progress, not finished |
| Version bump | **not done** — `pyproject.toml` is at 0.2.1.24 |
| GitHub issues | **#207, #210, #211, #214 all open, none reflects this work** |
| Commit 1 green in isolation | **reasoned, not measured** — run the suite between the two commits |

---

## 7. Known defects this does not fix

1. **The suite writes `/private/tmp/llmflow.log` on every run.** Some test leaves the process
   working directory outside the repository and the GUI test then writes a cwd-relative log there.
   Reproduced by deleting it and running again. Same family as #207, different bug.
2. **Twenty-odd tests use `tempfile.NamedTemporaryFile(..., delete=False)`**, which is why the
   `tempfile` redirect was needed. Repointing them at `tmp_path` is the deeper repair.
3. **`sp doctor` has not been run here** — step 7 of `design-ai-context-layout.md`, the acceptance
   test that the layout, the catalog and the generators agree. It writes, so it wants a clean tree
   and your word.
4. **1,196 lines of markdown remain embedded as Python string constants** in
   `src/llmflow/cli_utils.py`, across 22 catalog entries — #211, which you have directed but which
   is not started.
5. **Design narrative in docstrings**, including your rulings quoted in code: **21 test files and
   7 source modules** under `src/llmflow/` and `tests/`. `src/llmflow/cli_utils.py` alone has 11
   occurrences. Stripped from the two files you named; the rest is unstarted and needs your
   decision on whether it becomes a rule.

---

## 8. The commit plan

Two commits. The split has one clean seam and no others: `test_index_is_current` compares
`project/plans/README.md` against the plan documents present, so the index and the two designs must
land together, and the code commit is green without either.

`src/llmflow/cli_utils.py` and `src/llmflow/doctor.py` each carry hunks belonging to three
different concerns, so a finer split needs `git add -p` in your own terminal.

```bash
# Commit 1 — 67 paths: engine, templates, catalog, tests, CHANGELOG
git add -A -- . \
  ':!project/plans/design-ai-context-layout.md' \
  ':!project/plans/design-shipping-the-audit-method.md' \
  ':!project/plans/README.md' \
  ':!project/HANDOFF.md' \
  ':!project/REVIEW.md'
git commit -F tmp/commit-1-engine.txt

hatch run pytest -q          # confirm commit 1 is green on its own

# Commit 2 — 4 paths: the records
git add project/plans/ project/HANDOFF.md
git commit -F tmp/commit-2-records.txt
```

Messages are in `tmp/commit-1-engine.txt` and `tmp/commit-2-records.txt`; both need shortening to
the `github-workflow.md` convention before use — they are currently written at the old verbose
length. Delete them after committing, per the `tmp/` rule.

This file is itself uncommitted and excluded from both commits. Delete it once the review is done.
