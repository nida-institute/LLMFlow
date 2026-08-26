# tmp-context — 2026-08-25, mid-session checkpoint

Written by `/stand-down`. Captures what is only in conversation. Delete once folded into a
design document or `project/HANDOFF.md`.

## Rulings from the Captain today, not yet recorded anywhere else

1. **`data/file-catalog.yaml` holds only what sp itself specifies.** A document a project
   invented is not sp's to create. *"we should not enumerate every file some project created
   here in this file"* and *"these stay in the specific projects, and that is accomplished by
   listing them in that projects index.md."*
   Removed on that basis: `docs/ai-context/project/project.md`, `docs/audits/INDEX.md`,
   `docs/audits/audit-passage.md`, `docs/audits/audit-leadersguide.md`, their four constants,
   and the `docs/audits/` mkdir in `init_project`.

2. **Consumer projects need the same change made for them** — *"we should make those changes
   for the projects, which will not know how to do it for themselves."* Not started. It is
   edits in other repositories, so it needs a per-repo survey and the Captain's word on each.

3. **No design, rulings, or version history in docstrings or comments.** *"docstrings go stale
   as our designs evolve, and LLMs are tempted to trust the docstring instead of the design
   documents"*; *"don't try to embed version history in docstrings"*; *"keep it declarative,
   don't make me think about which files once used to do something else."* Applies repo-wide:
   21 test files and 7 modules under `src/llmflow/` still quote the Captain in code.

4. **The catalog lists sp's half before the project's half**, three standard documents each in
   the order overview, index, rules, then topic documents.

5. **CHANGELOG entries are high level**, per `docs/ai-context/sp/github-workflow.md`: 2–4 lines,
   one completed change each, `(#XX)` reference. Not a session transcript.

6. **Field documentation in the catalog needs to be fuller**, *"especially source"* — the next
   piece of work, and it should be grounded in what `file_catalog.py` actually does with each
   value rather than in the existing comment.

## State of the tree, measured

- **1 failing test:** `tests/test_catalog.py::test_project_md_is_user_owned_and_never_repaired`
  asserts `project.md` is catalogued. Ruling 1 reverses that; the test encodes the superseded
  decision and has not been updated.
- 2959 passed, 26 skipped.
- `ruff`: 22 errors in the files changed this session; 631 repo-wide, mostly pre-existing
  (untouched `runner.py` alone has 40).
- `project/HANDOFF.md` and `project/REVIEW.md` were written earlier today and **do not reflect
  anything after ruling 1** — both are stale on the catalog, the constants, and the CHANGELOG.
- `CHANGELOG.md`: the `### Documentation` block is still at the old verbose length.
- `tmp/commit-1-engine.txt` and `tmp/commit-2-records.txt` are written at the old verbose length
  and name files that have since changed.
- `docs/ai-context/sp/index.md` has **not** been regenerated since four entries left the catalog,
  so it still lists documents sp no longer ships.

## Open, and the Captain's

- Whether `tests/test_design_lives_in_documents.py` (proposed in stand-down) is wanted.
- `scope: project` names a *location*, not ownership — every `docs/ai-context/sp/*` entry carries
  it. That ambiguity is what let a comment about project-authored files sit above an `sp/` entry
  without anything failing. Worth a rename, and not an AI's call.
