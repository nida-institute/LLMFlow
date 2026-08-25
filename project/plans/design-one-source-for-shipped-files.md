# Design — one way to ship a file, and file-level granularity (#211)

**Status:** Proposed, 2026-08-25. Nothing built. Four questions in §4 await a ruling.
**Issue:** #211. Supersedes the mechanism half of `design-shipping-the-audit-method.md` §5,
which proved a project path can be template-sourced and left the other entries alone.
**Author:** AI, from the Captain's rulings on 2026-08-25 and from measurement of
`data/file-catalog.yaml`, `src/llmflow/file_catalog.py` and `src/llmflow/cli_utils.py`.

---

## 1. What I understand the goal to be

The Captain, on three fields of the catalog, in one sitting:

> *"this embeds a bunch of data that should be stored separately as files, using string
> constants in Python. Let's be declarative and also represent files that get copied over as
> files."*

> On `source: constant` — *"this seems like a case that should never exist."*

> On `block` — *"this is a feature I never asked for, one we probably should never use.
> granularity should be at the file level."*

So the goal is not to document these fields better. It is to **reduce the ways a file can be
shipped to one**, and to make ownership a property of a whole file rather than a region inside
one. A field the design does not want is a field no amount of documentation improves.

---

## 2. Measured state, 2026-08-25

`source` values in use: **19 `constant`, 1 `template`, 1 `derived`, 2 `none`.**
The 19 constants hold **1,047 lines of markdown, YAML and prompt text inside
`src/llmflow/cli_utils.py`.**

| destination | lines | note |
|---|---|---|
| `docs/llmflow-language-quickref.md` | 385 | |
| `docs/ai-context/sp/github-workflow.md` | 135 | |
| `docs/tutorial.md` | 93 | |
| `CLAUDE.md` | 75 | `block` |
| `docs/vscode.md` | 74 | |
| `docs/ai-context/sp/overview.md` | 40 | |
| `docs/ai-context/project/index.md` | 37 | |
| `pipelines/hello-llmflow.yaml` | 35 | |
| `docs/ai-context/project/rules.md` | 29 | |
| `project/audits/README.md` | 28 | |
| `docs/ai-context/project/overview.md` | 24 | |
| `project/TODO.md` | 24 | |
| `pipelines/hello.yaml` | 23 | |
| `prompts/reply.gpt` | 16 | |
| `prompts/hello.gpt` | 14 | |
| `.github/copilot-instructions.md` | 13 | `block` |
| `.cursorrules` | 1 | `block` |
| `.windsurfrules` | 1 | `block` |
| `docs/ai-context/sp/rules.md` | 0 | rendered from `data/ai-rules.yaml` |

**`docs/ai-context/sp/rules.md` is not a constant in substance.** `AI_RULES_DOC` is rendered
from `data/ai-rules.yaml` through a frame, so it is already single-sourced and belongs on
`derived`, beside `sp/index.md`.

**The four `block` entries are the four files sp does not own.** `CLAUDE.md` is the human's;
`.cursorrules`, `.windsurfrules` and `.github/copilot-instructions.md` belong to the project and
carry its own content. The block mechanism exists because sp had overwritten one of them whole.

---

## 3. The proposal

**3.1 `source: constant` is deleted.** Every shipped file becomes a real file under
`src/llmflow/templates/project/`, mirroring its destination path — the mirror already ruled for
the template tree. `Source.CONSTANT` goes from the enum, so the case cannot be reintroduced.
`sp/rules.md` moves to `derived`. Remaining values: `template`, `derived`, `sp-home`, `none`.

**3.2 `block` stays. The convention lives in the file, not in a keyword.** An earlier revision of
this section proposed deleting it, on the reasoning that ownership should be file-level. That was
rejected: those four paths are fixed by external tools — Claude Code, Cursor, Copilot and Windsurf
each read a file at a location sp does not choose, in which the project also has content — so one
file genuinely has two owners and the delimited region is what expresses it.

What the keyword could not do was tell the *project* to leave the region alone; it lives in sp's
catalog, which the project never reads. **Built 2026-08-25:**

- `SP_BLOCK_WARNING`, one copy of the text, composed into `CLAUDE_MD_LLMFLOW_BLOCK` and
  `ASSISTANT_RULES_POINTER` (the `.cursorrules` and `.windsurfrules` constants are aliases of the
  latter, so it is two definitions, not four). It states that only `sp` may write there, that
  edits are lost, that changing it breaks how the system behaves, and that the project's own
  content goes below.
- The warning is shipped content rather than marker text, so **no migration is needed** — existing
  projects receive it through the ordinary update path. Changing the marker text would be a
  migration, because `read_delimited_block` matches it literally and a project holding the old
  marker would get a second block appended.
- **Project content goes below the block only.** `_upsert_delimited_block` now strips the block
  from wherever it sits and writes it at position 0, so a file that received it at the bottom is
  relocated on the next run — this repository's `CLAUDE.md` included.
- Guarded by `tests/test_sp_block_is_first_and_warned.py`, and the ≤20-line cap in
  `test_assistant_files_do_not_restate_the_rules` now measures the signpost with the warning
  stripped, so it still catches the defect it was written for.

**3.3 What this does not touch.** `groups` already expand from what the package ships and are
already `source: template`. `outputs/` and `llmflow.log` stay `source: none` — nothing to ship.

---

## 4. Questions

Answer on the `=>` line.

**Q1 — CLOSED, and the opposite way round from how it was asked.** It asked which of two
file-level options replaced `block`. Ruled 2026-08-25: neither. `block` stays, because an external
tool fixes each of those four paths and the project has content in the same file; what was missing
was a warning in the file telling the project not to write in the region, and the specific
requirements were the emoji, no naming of `sp doctor` but say that `sp` can change it, a statement
that editing it breaks how the system behaves, and project content permitted **below the block
only**, with existing blocks relocated on the next run. Built and recorded in §3.2.

*The question as posed was wrong, not merely unanswered: it offered a choice between two ways of
removing a mechanism that should not be removed. Kept, rather than deleted, so a later reader can
see what was considered — and one revision of it recorded `create-once` as though it had been
chosen, which it had not.*

**Q2 — does `sp doctor` lose the ability to repair those four?**
It follows from Q1: `create-once` is outside `managed_by_doctor()`, so `sp doctor` will neither
refresh nor report them. Today three of the four are `generated` and doctor rewrites sp's block
in them. Naming it here because it is a capability being given up, not an implementation detail.

=>

**Moot, once Q1 was ruled the other way.** `block` stays, so nothing is given up: `sp doctor`
still repairs the three `generated` ones by replacing its own region, and an improvement to the
pointer text — the warning itself is the first such improvement — reaches every existing project.
`CLAUDE.md` is unaffected either way: it is `create-once`, so `sp doctor` never touched it, though
`sp init` rewrites its block on every run because `_configure_claude_code` ignores its `update`
argument.

**Q3 — is `scope` the right word?** It names a *location* — the project directory or `~/.sp` —
but reads as ownership, and every `docs/ai-context/sp/*` entry carries `scope: project`. That
ambiguity is what let a comment about project-authored files sit above an `sp/` entry with
nothing failing. `root`, `installs-to`, or leave it.

=>

**Q4 — one pass, or the 19 in tranches?** Rule 18 says one pass, and the template tree was moved
that way. Against: it is 1,047 lines of content moving plus ~40 test assertions that import those
constants by name, in a working tree that already carries roughly 100 changed paths and one
failing test.

=>

*Ruled in conversation, 2026-08-25: **"yes, one path."** All 19 in one pass.*

**Q5 — `scope` is deleted; which directory structure states the root?**

Ruled, 2026-08-25: *"if we use both directory membership and scope to determine if it's sp or
project scope, that's two sources of truth that can disagree. use only the directory structure."*
After Q4 the field is redundant, and the structure that replaces it is undecided. Two could
carry it — the template tree, or the destination path — and this document offers no
recommendation between them.

**A correction, because an earlier revision ruled one out on a misreading.** It claimed the
template tree could not carry the root, on the grounds that `templates/sp/skills/*` installs to
both `~/.sp/skills/{name}` and `<project>/.claude/skills/{name}`. Two errors:

- *Same by value is not same by identity.* Those are two distinct files that happen to hold
  identical bytes. Two destinations are two entries; neither has two roots.
- *The project copy does not come from the template tree.* `project-skills` declares
  `source: sp-home`, and `_expand_group` (`file_catalog.py:170`) passes `template=` only when
  `source` is `template`. So that glob enumerates skill *names* and the content is read from the
  installed store. The template tree serves one root.

What each option would cost is unmeasured, and measuring it is the next step once the shape is
chosen — not before.

=>

**Q6 — may a project change a file that lives in its own directory?**

Asked 2026-08-25: *"and the project would be allowed to change it if it is in that location,
no?"* — of `<project>/.claude/skills/{name}`. **Today it may not**, and four statements about
those files disagree:

| | says |
|---|---|
| `policy: generated` | sp owns the content |
| `managed_by_doctor()` | includes them — claims `sp doctor` restores them |
| `run_doctor` project pass, `doctor.py:387` | excludes them: it filters on `source is CONSTANT` |
| `_install_claude_skills`, `cli_utils.py` | overwrites them on **every** `sp init`, not only `--update` |

So a project that adapts a shipped skill loses the edit at the next init, `sp doctor` reports
nothing, and because these are `committed: true` the revert appears in that project's git diff.

This is the general form of Q1: a file in the project's directory that sp keeps rewriting. The
same trade applies — if the project may change it, an improvement to a shipped skill never
reaches a project that already has it.

=>

---

## 5. Consequences already known

**`sp doctor` repairs project files only when `source` is `constant`.** `doctor.py:387` reads
`e.scope is Scope.PROJECT and e.source is Source.CONSTANT`. Deleting `Source.CONSTANT` without
changing that line leaves the filter matching nothing, so **`sp doctor` would silently stop
repairing every project file** — the capability #211 exists to preserve. Found by reading the
call sites for Q3. It must change in the same pass, and a test should fail if the project-repair
list is ever empty.

- **`tests/test_catalog.py::test_project_md_is_user_owned_and_never_repaired` fails now.** It
  asserts `project.md` is catalogued, which today's ruling reverses. It is the superseded
  decision written as a test and needs deleting, independently of this plan.
- **Consumer projects need the same treatment**, per *"we should make those changes for the
  projects, which will not know how to do it for themselves."* Not in this plan: it is edits in
  other repositories, each of which is the Captain's to commit.
- **`docs/ai-context/sp/index.md` is stale** — four entries left the catalog and it has not been
  regenerated.
