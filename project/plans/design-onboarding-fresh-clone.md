# Design — onboarding from a fresh clone (#204)

**Status:** awaiting Captain's review. No code written.
**Issue:** #204 (diagnosis corrected 2026-08-17) · related: #181, #32
**Author:** AI, from code read at `c1e8829`. Every claim below cites `file:line` — verify any of them.

---

## 1. What I understand the goal to be

> A user clones a mentoring repository such as `sil-translator-notes`, runs `sp init`, and
> `/load-context` works. Nothing hand-carried, nothing hand-edited.

With one stated preference (Captain, 2026-08-17):

> "If possible, I don't want to write to Claude memory at all, but I do need `/load-context` to
> work and am willing to write to Claude memory if necessary."

**Captain — is this the goal?** ☐ yes ☐ no, it is: ______________________

---

## 2. Verified facts

These are read from the code, not inferred.

| Fact | Evidence |
|---|---|
| `sp init` **does** create `CLAUDE.md` — upserts a delimited block | `cli_utils.py:756-761` |
| Plain `sp init` overwrites **nothing** — `if not exists / elif update and _is_generated / else leave as-is` | `cli_utils.py:1854-1888` |
| `project.md` is exempt even from `--update` | `cli_utils.py:1890-1895` |
| `_configure_ai_assistants` returns **silently** when stdin is not a TTY | `cli_utils.py:805-806` |
| `Claude Code` consent is `default=False`; `GitHub Copilot` is `default=True` | `cli_utils.py:811-812` |
| Skill install is a **second** opt-out, `default=False` | `cli_utils.py:777` |
| That branch is the only path copying into `~/.claude/skills/` | `cli_utils.py:778` |
| `~/.sp` is created non-interactively via `mkdir(parents=True)` | `cli_utils.py:1669`, `1717`, `1727`, called `1952-1954` |
| …but failures are swallowed with a warning only | `cli_utils.py:1955-1956` |
| `templates/` ships exactly `sp-conventions/` (5 files) and `sp-skills/` (10 skills) | `src/llmflow/templates/` |
| `drift-patterns.md` ships nowhere, yet `/load-context` step 5 reads it | package tree; skill text |
| Conventions absent from the package: `design-authority.md`, `sp-debugging.md`, `sp-workflow.md` | 8 on this machine vs 5 shipped |
| `EXPECTED_SKILLS` guards skill drift; **there is no equivalent for conventions** | `tests/test_global_conventions.py:16,67-77` |
| No test references `CLAUDE.md`, `isatty`, `_configure_ai_assistants`, or `_configure_claude_code` | `grep tests/` |
| Claude Code loads project skills from `.claude/skills/` up to the repo root, and they are meant to be committed | Claude Code docs, "Skills" |
| **Personal skills shadow project skills of the same name** | Claude Code docs: "`/deploy` runs the personal one" |
| `sil-translator-notes` gitignores `CLAUDE.md` (line 1) and `.claude/` (line 4) | its `.gitignore` |
| Its `docs/ai-context/` **is** committed | `git ls-files` → `index.md`, `project.md`, `rules.md` |

### Unverified

The bodyless-400 mechanism. An empty read producing an empty content block that the API rejects is
the most plausible explanation for what Paul saw, but **it has not been reproduced**. Reproducing it
from an empty `HOME` is step 1 of the work, and it may turn out to be something else.

---

## 3. Open decisions — Captain's, not mine

### D1. Where does the `load-context` skill live?

| | Approach | For | Against |
|---|---|---|---|
| **A** | **Repo-scoped** — commit `.claude/skills/load-context/SKILL.md` in the mentoring repo | Satisfies the no-Claude-memory preference outright. Clone and it exists. Mentor controls the version their trainees get | Requires carving `.claude/skills/` out of the `.claude/` gitignore rule. **Your personal copy shadows it**, so you cannot verify it works from this machine |
| **B** | **Home-scoped** — keep `~/.claude/skills/`, fix the consent defaults | No gitignore change; matches the current design; one copy serves every project | Writes to Claude memory, which you would rather avoid. Trainee's copy silently diverges from the mentor's |
| **C** | **Both** — repo is source of truth, `sp init` also copies to `~/.claude/skills/` | Works whether or not the user starts Claude in the repo root | Two copies to keep in step; the shadowing problem gets worse, not better |

**Captain's ruling:** ______________________

### D2. What about the `~/.sp/` content the skill reads?

`/load-context` step 5 reads `~/.sp/conventions/*.md` and `~/.sp/drift-patterns.md`. A fresh machine
gets 5 of 8 conventions and no drift-patterns.

| | Approach | For | Against |
|---|---|---|---|
| **A** | Skill tolerates absence — reads what is there, notes what is missing | Smallest change; fixes the crash regardless of anything else | Trainee silently gets less context than the mentor. A green run does not mean a complete one |
| **B** | Ship the missing content in `templates/` so `~/.sp/` is complete after `sp init` | Trainee gets the same context as the mentor; closes #181 too | Machine-scoped writes continue; the three conventions become engine-owned and must be maintained there |
| **C** | Move that content into the repo | Fully self-contained; nothing machine-scoped | Duplicates content across every mentoring repo; divergence is then permanent |

A and B are not exclusive — A is a robustness fix, B a completeness fix.

**Captain's ruling:** ______________________

### D3. Does `/load-context` still read `CLAUDE.md`?

Your preference is not to write it. It is gitignored by convention in every consumer repo, so a
clone never has one. `docs/ai-context/` is committed and can carry the same content.

- **A** — skill reads it only if present, and the repo's real context lives in `docs/ai-context/`
- **B** — skill stops reading it entirely; `docs/ai-context/` becomes the sole contract
- **C** — `sp init` scaffolds it after all (abandons the preference)

**Captain's ruling:** ______________________

### D4. What should `sp init` do when stdin is not a TTY?

Currently: nothing, silently (`cli_utils.py:805-806`).

- **A** — configure everything project-scoped, skip only machine-scoped writes, and say so
- **B** — keep skipping but print what was skipped and how to get it
- **C** — add an explicit flag (`--ai-assistant=claude`) for non-interactive use

**Captain's ruling:** ______________________

### D5. Should `Claude Code` still default to No?

`GitHub Copilot` defaults to Yes, `Claude Code` to No (`cli_utils.py:811-812`), and skills are a
second No (`cli_utils.py:777`). A user pressing Enter throughout gets Copilot and no Claude setup.

**Captain's ruling:** ______________________

### D6. Should your `~/.sp/user-context/` files ship?

**I owe you a correction here.** I wrote in #204 that `user-context/` is "unobtainable by any
`sp init`." That was overstated. It is a deliberate, tested location — `tests/test_init.py:485-530`
covers it including the absent case, and `tests/test_sp_lock.py:67-68` asserts `sp init` must leave
it writable. It does not ship because it is *the user's own* context, which may well be correct.

But you put `filesystem-access.md`, `github-authority.md` and `consumer-repo-conventions.md` in
Paul's zip, so you wanted him to have them. Are they per-user, or should some ship as defaults?

**Captain's ruling:** ______________________

### D7. Ownership of a generated file

`sp init --update` rewrites any file still carrying `<!-- Generated by sp init -->` on line 1, even
one hand-edited, because the marker is the only test. A mentor has no way to say "I own this now."

- **A** — hand-editing strips the marker (document it); `--update` then leaves the file alone
- **B** — `--update` merges rather than overwrites
- **C** — document that everything durable goes in `project.md`

**Captain's ruling:** ______________________

---

## 4. Test plan — written before any implementation

Ordered by value. Every one of these fails today.

| # | Test | Catches | Notes |
|---|---|---|---|
| T1 | `EXPECTED_CONVENTIONS` set, mirroring `EXPECTED_SKILLS` | The three drifted conventions, and all future drift | **Smallest high-value test in this plan.** The asymmetry at `tests/test_global_conventions.py:16` is precisely why skills held and conventions drifted |
| T2 | `sp init` with an empty `HOME`: assert every file `/load-context` reads either exists or is explicitly optional | The whole class of clean-machine bugs | Reachable now — `install_global_skills(sp_home=…)`, `_install_claude_skills(claude_home=…, sp_home=…)`, `default_editions_dir()` all take overrides |
| T3 | Non-TTY `sp init` produces a stated, asserted outcome | The silent return at `cli_utils.py:805-806` | Shape depends on **D4** |
| T4 | Reproduce Paul's failure from an empty `HOME` | Confirms or refutes the empty-read hypothesis | Do this **first** — the fix depends on the mechanism being what we think |
| T5 | `sp init --update` leaves a file whose ownership was taken | The `--update` hazard | Shape depends on **D7** |
| T6 | Skill/context files reachable from a clone with no `~/.sp` and no `~/.claude` | D1's premise | Shape depends on **D1** |

**Honest limit:** T1–T5 are pytest. **The skill's own behaviour is not unit-testable** — `SKILL.md`
is markdown executed by a model, not code. "Skip a missing file cleanly" is a change to skill *text*;
the most a test can do is assert the files it names exist, or that the skill declares them optional.
Verifying it truly degrades gracefully needs a real run on a clean machine, and per D1 **that cannot
be this machine**, because your personal skill shadows any repo copy.

---

## 5. Sequence

1. **T4** — reproduce from an empty `HOME`. Confirm the mechanism before designing against it.
2. **T1** — conventions drift guard. Independent of every decision above; safe to land first.
3. Captain rules on D1–D7.
4. **T2, T3, T5, T6** written to the ruled shapes — failing.
5. Implement against them.
6. `/commit-ready`: full suite, CHANGELOG, commit message with issue refs.

**Steps 1 and 2 need no rulings** and could start on your word. Steps 3 onward are blocked on D1–D7.

---

## 6. Constraints in force

- **No push this session** (Captain). `origin/dev` stays at `cb72cb7` so PR #199 is not retargeted
  and the ~2h Windows build is not restarted. Local commits are fine.
- **CHANGELOG is frozen** while #199 is in flight; this work is for the version after 0.2.1.24.
- **`.gitignore` changes land in consumer repos and in whatever `sp init` generates** — the engine
  change and the mentoring-repo change are not the same edit. If D1 is A or C, both are needed.
- **This plan is not authorization.** Per `rules.md` #15, implementation waits on your explicit
  direction after reviewing it.
