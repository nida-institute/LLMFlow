# HANDOFF — 2026-08-19

Supersedes the 2026-08-17 handoff entirely.

---

## ⚠️ 18 COMMITS COMMITTED LOCALLY, NOT PUSHED — ON PURPOSE

`origin/dev` sits at `cb72cb7`. **Do not push.** Captain's standing instruction, 2026-08-18:
*"committing is safe, push is not"* — pushing to `dev` retargets release PR #199 and starts a fresh
build, including a ~2h Windows job. That happened twice by accident on 2026-08-17 and cost two builds.

```bash
git log --oneline origin/dev..dev | wc -l    # expect 18
git rev-parse --short origin/dev             # expect cb72cb7
```

Push only after PR #199 is merged.

---

## ▶ NEXT ACTION

**D1-A′: copy skills into `<repo>/.claude/skills/`.** It is the last substantive piece of #204, and
`sp doctor` now names it as the only remaining failure on a clean machine:

```
✗ No skills are where Claude Code can find them
    ~/.sp/skills is not a location Claude Code reads. Slash commands such as
    /load-context will not exist until skills are in .claude/skills.
```

**But three questions are open and are the Captain's** — see "Open decisions" below. D1-A′ cannot be
finished without at least the first.

---

## What was done 2026-08-18/19

All of it on #204. Every claim below was verified by running commands, not by reading code.

| Done | Evidence |
|---|---|
| `git status --short` → `--branch` in `load-context` | `git status --short` returns 0 bytes on a clean clone; `--branch` always emits `##` |
| Test: no skill command may return an empty result | `tests/test_skill_command_output.py`, all 10 shipped skills |
| Shipped 3 missing conventions + `EXPECTED_CONVENTIONS` drift guard | fresh machine went 5/8 → 10/10 |
| Conventions `README.md` index guard | it had drifted to listing 3 of 8 |
| Shipped `drift-patterns.md` via new `templates/sp-root/` | was in no package at all |
| Promoted `github-authority.md`, `consumer-repo-conventions.md` | D6 split |
| Guard: no shipped template may contain an email or absolute home path | `github-authority.md` had named a personal bot account |
| **`sp doctor`** — `src/llmflow/doctor.py`, 8 tests | isolates the remaining defect in one line |

**Suite: 2621 passed, 13 skipped.** `ruff` clean. CHANGELOG entries are under `## Unreleased` with
the version deliberately unset — the Captain may fold this into 0.2.1.24 before it merges to main,
so **retarget that heading rather than assuming a new version.**

### Every read `/load-context` performs, on a clean machine

| Read | Before | Now |
|---|---|---|
| `git status --short` | EMPTY, rc=0 | ok (`--branch`) |
| `~/.sp/drift-patterns.md` | ERROR rc=1 | ok, 24928 bytes |
| `~/.sp/conventions/*.md` | 5 files | 10 files |
| `CLAUDE.md` | ERROR rc=1 | ERROR rc=1 — **by design**, see D3-A |

---

## Open decisions — Captain's, blocking

**1. D4 / D5 — the interactive gate.** Still unruled. The Captain said *"educate me"* on both; the
plan contains recommendations, and **an AI recommendation is not a ruling.** This blocks D1-A′,
because `_configure_ai_assistants` returns silently when stdin is not a TTY
(`cli_utils.py:805-806`), and Claude Code setup sits behind two `default=False` prompts
(`cli_utils.py:777`, `811-812`). A fresh clone therefore gets no skills copied.

What still needs a decision: whether the other three assistants' files (`.cursorrules`,
`.windsurfrules`, `copilot-instructions.md`) are written unconditionally, and whether the prompts
disappear entirely.

**2. `.gitignore` — `sp init` writes none at all.** Verified: a fresh `sp init` produces no
`.gitignore` and no `.claude/`. Earlier notes described a "carve-out in the generated `.gitignore`";
there is nothing to carve. `sil-translator-notes` ignores `.claude/` wholesale, so committing
`.claude/skills/` needs a hand edit there. **Does `sp init` start generating a `.gitignore`, or does
the mentor edit theirs?** If the engine never writes one, "clone and it works" depends on the
mentoring repo having been hand-configured — the class of problem #204 exists to remove.

**3. Release split.** Unchanged from the last handoff and still unresolved.

**4. `sp doctor` checks presence, not content — and the Captain's own machine is stale.**
The `=>` answer-slot convention was added to `templates/sp-conventions/surface-decisions.md`
(2109 bytes). The Captain's installed copy is the old **790-byte** version with zero `=>`
occurrences, because `install_global_conventions` uses `force=False` and skips existing files.

```bash
sp init --update      # the only thing that will refresh it
```

The general gap: a machine can pass every `doctor` check while holding stale convention *content*.
Adding a content comparison is not obviously right — a user may have edited a convention
deliberately, and flagging that as a fault would be wrong — so the severity and whether to do it at
all is the Captain's call. This is the same silent-drift class as the unshipped conventions, one
level down.

---

## Do NOT

- **Do not push.** See the top of this file.
- **Do not treat the bodyless 400 as diagnosed.** Two mechanisms were proposed and **both refuted by
  test.** Missing files exit non-zero and print to stderr, so they are loud, not silent. `git status
  --short` returning nothing is a *candidate*, not a conclusion — no 400 has been reproduced. #204
  now says the cause is unknown. Do not let a third theory quietly become the story.
- **Do not ship `filesystem-access.md`.** It grants an AI standing read access to a directory tree;
  only the machine's owner can grant that. Its absence is correct, and `sp doctor` deliberately does
  not check for it.
- **Do not put personal information in `templates/`.** A test fails the build on any email address or
  absolute home path, added after `github-authority.md` was found naming a personal bot account.
- **Do not use `_sp_dir_writable()` on the `~/.sp` root.** It locks its directory on exit
  *unconditionally*, even when it was writable before. Doing so left the whole tree read-only and
  silently broke `install_global_skills()` — the call sits in a `try/except` that only warns. See the
  comment in `install_global_conventions`.
- **`sp doctor` is not blocked on #205.** An earlier revision of the plan and of #205 both claimed it
  was; retracted in both. `doctor` is built.

---

## Two process failures worth remembering

Recorded because both nearly cost scope the Captain had not asked to give up, and both were caught by
him rather than by me.

1. **Claimed skill shadowing made the fix unverifiable.** It does not — `env HOME=<tmpdir> claude`
   gives a clean run, and the automated tests never touch skill resolution. The Captain was about to
   relax a design constraint on the strength of it.
2. **Claimed `sp doctor` was blocked on #205.** It never was; `doctor` needed an `add_parser`, a
   handler and tests. He asked why, and the dependency did not survive the question.

Both times a concern I had just written up was then treated as a constraint — an AI-authored
rationale acquiring the force of a design decision. That is circular authority, and the tell is that
the "blocker" always appeared immediately after I had finished documenting something.

---

## New issues filed

- **#205** — bring the CLI under the same declarative-schema discipline as pipeline steps. Captain's
  rulings: *"I don't want to maintain so many alternative ways of saying the same thing"* and *"the
  same discipline for the CLI."* Six questions open. Evidence: three commands own `docs/ai-context/`,
  `sp update-ai-context` violates the locked `--update` rule, `sp transition` is orphaned from
  `sp content`, and `gui/backend/server.py` hand-maintains a second copy of the CLI's command names.
  Board 13, Todo.
- **human-at-the-helm#1** — upgrade HATH to current functionality: an installer, the full skill set,
  support for pure-Python projects. **The goal after this release.** Board 13, Todo position 1.
  Provenance recorded: HATH came first and inspired the AI context here, then fell behind, so the
  origin is now the less advanced text. Questions deferred by the Captain until the goal starts.

## Key files

- `project/plans/design-onboarding-fresh-clone.md` — the live design. D1–D8 with the Captain's
  answers inline after each `=>`. **Answer format: a bare `=>` line, never checkboxes or blanks.**
- `src/llmflow/doctor.py` · `tests/test_doctor.py`
- `tests/test_skill_command_output.py` · `tests/test_global_conventions.py`
- `src/llmflow/templates/sp-root/` — new; files whose path is part of a contract
