# Design — onboarding from a fresh clone (#204)

**Status:** D1–D7 ruled by the Captain 2026-08-18. **D1 has a blocking technical conflict — see D1.**
No implementation code written yet.
**Issue:** #204 (diagnosis corrected 2026-08-17) · related: #181, #32
**Author:** AI, from code read at `c1e8829` and from an actual `sp init` run against a fake `HOME`
(§2.1). Every claim cites `file:line` or an observed command output — verify any of them.

---

## 1. What I understand the goal to be

> A user clones a mentoring repository such as `sil-translator-notes`, runs `sp init`, and
> `/load-context` works. Nothing hand-carried, nothing hand-edited.

With one stated preference (Captain, 2026-08-17):

> "If possible, I don't want to write to Claude memory at all, but I do need `/load-context` to
> work and am willing to write to Claude memory if necessary."

**Confirmed by the Captain, 2026-08-18: this is the goal.**

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
| **`sp init` creates `~/.sp` AND registers the project**, non-interactively | `cli_utils.py:1962`, `_register_in_global_registry` at `1965-1988`; observed §2.1 |
| Registration is idempotent — skips an already-registered project | `cli_utils.py:1984-1988` |
| `sp init` also indexes `docs/ai-context/*.md` into `~/.sp/ai-context/` | `cli_utils.py:1990+`; observed §2.1 |
| **Claude Code does not read skills from `~/.sp/`** — only `~/.claude/skills/` or `.claude/skills/` | Claude Code docs, "Skills" location table |

The registration row was **missing from the first revision of this table** — the Captain caught it.

## 2.1 Empirically verified, not just read

Run: `env HOME=<fake> python -m llmflow.cli init` in an empty directory. stdin was not a TTY.

**What `sp init` produced with no prior state:**

```
✓ Installed llmflow-pipeline-steps.md to ~/.sp/conventions/    (5 conventions)
✓ Installed load-context skill to ~/.sp/skills/                (10 skills)
Registered project 'freshclone' in ~/.sp/projects/
Indexed index.md in ~/.sp/ai-context/                          (5 files indexed)
```

Created: `~/.sp/{conventions,skills,projects,ai-context,databases,datasets}`, the full
`docs/ai-context/` set, `project/`, `docs/audits/`, `outputs/`.

**Not created: `CLAUDE.md`. Not created: `~/.claude` at all.** The non-TTY silent return
(`cli_utils.py:805-806`) is therefore observed behaviour, not inference.

### The overwrite question — settled by experiment

Three files were hand-edited, then `sp init` was run twice. This tests the claim that `sp init`
"writes to the context and could overwrite it".

| File | State before | Plain `sp init` | `sp init --update` |
|---|---|---|---|
| `index.md` | marker on line 1 | preserved | **OVERWRITTEN** — edit destroyed |
| `rules.md` | marker stripped | preserved | preserved |
| `project.md` | — | preserved | preserved ("yours to own") |

Plain `sp init` reported `already exists; leaving as-is` for **every** ai-context file and changed
none of them. `--update` reported `Updated docs/ai-context/index.md` and replaced the hand-written
content with the generated text.

**Conclusion:** the claim is **half right**. `sp init` *can* overwrite AI context — but only with
`--update`, and only for a file still carrying the marker. Plain `sp init` never does. This also
confirms D7-A already works today: stripping the marker protects a file. Which is precisely why the
marker is load-bearing, and why the Captain's objection to depending on it stands.

## 2.2 T4 executed — the empty-read hypothesis is REFUTED

Ran every read `/load-context` performs against a fresh git repo with a fresh `HOME` after `sp init`.

| Read | Result on a clean machine |
|---|---|
| `git rev-parse --show-toplevel` | ok, 123 bytes |
| `git status --short` | **EMPTY OUTPUT, rc=0** |
| `cat CLAUDE.md` | ERROR rc=1 |
| `cat docs/ai-context/index.md` | ok, 7253 bytes |
| `cat docs/ai-context/rules.md` | ok, 3330 bytes |
| `cat docs/ai-context/overview.md` | ok, 877 bytes |
| `cat ~/.sp/conventions/*.md` | ok, 18742 bytes |
| `cat ~/.sp/drift-patterns.md` | ERROR rc=1 |
| `cat ~/.claude/projects/*/memory/MEMORY.md` | ERROR rc=1 |

**The three missing files are not silent — they are loud.** Each exits 1 and prints
"No such file or directory" to stderr. A missing file therefore produces a *non-empty* result, so it
**cannot** be the empty content block that yields a bodyless 400. The hypothesis carried by #204 and
by revision 1 of this plan is wrong.

### What the same run did find

**`git status --short` returns zero bytes with exit 0** — and it does so precisely when a checkout
has no local changes, which is *exactly* a fresh clone. It is **step 1 of the skill, the first
command run.**

This is textbook author-machine blindness: during this entire session, this repository has never had
a clean tree, so `git status --short` has never once been empty here. `git branch --show-current` is
a second, narrower case — empty on a detached HEAD.

### Still not proven

**A 400 has not been reproduced.** What is established: (a) missing files are loud, not silent, so
they are not the cause; (b) the skill contains a command that genuinely produces an empty result, in
exactly the fresh-clone condition Paul was in. Whether an empty content block is what the API
rejects remains unverified — that needs the step-9 clean-`HOME` run with a real Claude Code session.

### Verified fix candidate

`git status --short --branch` always emits a `##` header line — 19 bytes even on a clean detached
checkout — and adds ahead/behind information that the orientation report wants anyway. One word.

### Design impact — one ask changes

"Skills must skip a missing file cleanly, never emit an empty read" was premised on missing files
being silent. **They are not.** That ask survives only as hygiene — a `cat` error is noise in the
transcript and the skill should tolerate absence gracefully — but it is **not** the fix for the 400,
and it should stop being described as such. D3-A remains correct for its own reasons.

**T4's real deliverable is `tests/test_skill_command_output.py`**: no command in a shipped skill may
exit 0 with neither stdout nor stderr. It fails today on `git status --short`.

---

## 3. Open decisions — Captain's, not mine

**Answer inline after each `=>`.**

### D1. Where does the `load-context` skill live?

| | Approach | For | Against |
|---|---|---|---|
| **A** | **Repo-scoped** — commit `.claude/skills/load-context/SKILL.md` in the mentoring repo | Satisfies the no-Claude-memory preference outright. Clone and it exists. Mentor controls the version their trainees get | Requires carving `.claude/skills/` out of the `.claude/` gitignore rule. **Your personal copy shadows it**, so you cannot verify it works from this machine |
| **B** | **Home-scoped** — keep `~/.claude/skills/`, fix the consent defaults | No gitignore change; matches the current design; one copy serves every project | Writes to Claude memory, which you would rather avoid. Trainee's copy silently diverges from the mentor's |
| **C** | **Both** — repo is source of truth, `sp init` also copies to `~/.claude/skills/` | Works whether or not the user starts Claude in the repo root | Two copies to keep in step; the shadowing problem gets worse, not better |

=>  We don't want to use ~/.claude anything if possible. It belongs in ~/.sp, but it should also invoke local project context found in project.md and files that it refers to.

#### ⚠️ Blocker — the ruling cannot be implemented as literally stated

**Claude Code does not read skills from `~/.sp/`.** Its documented locations are exactly two:

| Type | Location | Available in |
|---|---|---|
| Personal | `~/.claude/skills/<name>/SKILL.md` | All your projects |
| Project | `.claude/skills/<name>/SKILL.md` | This project only |

`~/.sp/` is LLMFlow's own directory; Claude Code knows nothing about it. A skill sitting in
`~/.sp/skills/load-context/` is **invisible** — `/load-context` does not exist as a command. That is
exactly why `_install_claude_skills` copies `~/.sp/skills` → `~/.claude/skills` today
(`cli_utils.py:778`): the copy is not redundancy, it is the only thing that makes the skill
invocable.

So `~/.sp/` can be the **canonical source**, but something must place a copy where Claude Code
looks. There is no third option.

**What is still possible, given the preference:**

- **A′ — repo-scoped.** `sp init` copies `~/.sp/skills/` → the repo's `.claude/skills/`, committed.
  **Nothing is written to your home `~/.claude`.** This is the only route that honours "no
  `~/.claude` anything". It does still create a directory *named* `.claude`, inside the repo —
  if the objection is to the name rather than to writing outside the project, this fails too and
  `/load-context` cannot be a slash command at all.
  Cost: carve `.claude/skills/` out of the `.claude/` gitignore line; and **a personal skill of the
  same name shadows the project one**, so your machine will keep running your copy and cannot
  verify the shipped one.
- **B′ — home-scoped**, i.e. today's design with the consent defaults fixed. Invokes the stated
  fallback: *"willing to write to Claude memory if necessary."* This is that case.

**Captain — which? A′ or B′?** The second half of the ruling ("should also invoke local project
context found in `project.md` and files it refers to") is unaffected and will be implemented either
way: the skill reads `docs/ai-context/project.md` and follows its references.

=> I can live with a minimal use of .claude, I think it should be project level, and it should load all of our ~/.sp skills and any local project skills.

#### Ruled: A′ — project-level `.claude/skills/`, committed. Nothing in `~/.claude`.

`sp init` populates `<repo>/.claude/skills/` from **both** sources:

1. every skill in `~/.sp/skills/` — the 10 shipped ones, so a trainee gets the same set as the mentor
2. any project-local skills the repo defines

**Four consequences that follow, each needing work:**

1. **`.gitignore` must change in consumer repos.** `.claude/` is currently ignored wholesale
   (`sil-translator-notes/.gitignore:4`, commented *"local session state and AI memory (never
   commit)"*). `.claude/skills/` must be carved out and committed while the rest of `.claude/`
   — `settings.local.json` and session state — stays ignored. Both the engine's generated
   `.gitignore` and existing consumer repos need this.
2. **Collision policy is needed.** If `~/.sp/skills/load-context` and a project-local
   `load-context` both exist, one wins. This is D7's catalog question again — the copy needs a
   declared rule, not last-write-wins.
3. **Shadowing affects manual verification only — it is not a design blocker.**
   *(This corrects an earlier overstatement in this document, which claimed the Captain's machine
   could not verify the result and called it "the single hardest thing about testing this fix". That
   was wrong, and it nearly cost a design constraint.)*

   A personal skill shadows a project skill of the same name, so typing `/load-context` on this
   machine resolves `~/.claude/skills/load-context/` (confirmed present, byte-identical to the
   `~/.sp/` copy at 5888 bytes). Consequences, in order of usefulness:

   - **Automated tests are unaffected.** T6, T7 and T9 assert *where `sp init` puts files* — pytest
     with a fake `HOME`, exactly as §2.1 already does. Shadowing is a Claude Code runtime
     resolution rule and has no bearing on filesystem assertions. This covers most of the fix.
   - **For end-to-end verification, run Claude Code with a clean `HOME`:**
     `env HOME=<tmpdir> claude` inside the test clone. That process sees no personal skills, so the
     project `.claude/skills/` copy is what resolves — which is exactly a trainee's situation.
     Nothing on the Captain's machine is modified.
   - **Moving the personal copy aside also works but is worse.** `~/.claude/skills/` is
     `dr-xr-xr-x` — locked read-only by the engine's own protection — so `mv` fails until
     `chmod u+w ~/.claude/skills`. Reversible, but it mutates a working setup for no gain over the
     clean-`HOME` route.
4. **`.claude/skills/` becomes committed generated content** — a new category. It is generated by
   `sp init` yet lives in git, so the D7 catalog must model "generated but committed" distinctly
   from "generated, gitignored".

### D2. What about the `~/.sp/` content the skill reads?

`/load-context` step 5 reads `~/.sp/conventions/*.md` and `~/.sp/drift-patterns.md`. A fresh machine
gets 5 of 8 conventions and no drift-patterns.

| | Approach | For | Against |
|---|---|---|---|
| **A** | Skill tolerates absence — reads what is there, notes what is missing | Smallest change; fixes the crash regardless of anything else | Trainee silently gets less context than the mentor. A green run does not mean a complete one |
| **B** | Ship the missing content in `templates/` so `~/.sp/` is complete after `sp init` | Trainee gets the same context as the mentor; closes #181 too | Machine-scoped writes continue; the three conventions become engine-owned and must be maintained there |
| **C** | Move that content into the repo | Fully self-contained; nothing machine-scoped | Duplicates content across every mentoring repo; divergence is then permanent |

A and B are not exclusive — A is a robustness fix, B a completeness fix.

=> `sp init` should make these available.

### D3. Does `/load-context` still read `CLAUDE.md`?

Your preference is not to write it. It is gitignored by convention in every consumer repo, so a
clone never has one. `docs/ai-context/` is committed and can carry the same content.

- **A** — skill reads it only if present, and the repo's real context lives in `docs/ai-context/`
- **B** — skill stops reading it entirely; `docs/ai-context/` becomes the sole contract
- **C** — `sp init` scaffolds it after all (abandons the preference)

=> A

### D4. What should `sp init` do when stdin is not a TTY?

Currently: nothing, silently (`cli_utils.py:805-806`).

- **A** — configure everything project-scoped, skip only machine-scoped writes, and say so
- **B** — keep skipping but print what was skipped and how to get it
- **C** — add an explicit flag (`--ai-assistant=claude`) for non-interactive use

=> Educate me.  I have no idea what to do here.

**Answer.** Non-TTY happens in CI, Docker builds, `sp init < /dev/null`, and any scripted
onboarding — so it is the exact path a "one command" story would take. Today it does nothing and
says nothing, which is the worst of the options.

The important thing the §2.1 run showed: **the gate is far narrower than it looks.** Everything
substantial already happens non-interactively — all of `docs/ai-context/`, `project/`, `outputs/`,
the whole of `~/.sp/`, and project registration. `_configure_ai_assistants` gates only:

- four project-scoped files — the `CLAUDE.md` block, `.cursorrules`, `.windsurfrules`,
  `.github/copilot-instructions.md`
- the one machine-scoped action — copying skills into `~/.claude/skills/`

Under D1 the machine-scoped action either moves into the repo (A′) or is the thing you've accepted
as necessary (B′). Either way the gate ends up guarding **four harmless, idempotent, non-destructive
project files** — §2.1 proved plain `sp init` cannot clobber them.

**Recommended: A, and treat C as a convenience.** Write the project-scoped files unconditionally,
print one line naming what was written and what was skipped. A prompt whose every answer is safe is
pure friction, and its cost is a silently broken setup when someone presses Enter. Keep prompting
for machine-scoped writes only. A flag (`--ai-assistant=claude`) is worth having for explicit
scripted control, but the default path must work without it.

=>

### D5. Should `Claude Code` still default to No?

`GitHub Copilot` defaults to Yes, `Claude Code` to No (`cli_utils.py:811-812`), and skills are a
second No (`cli_utils.py:777`). A user pressing Enter throughout gets Copilot and no Claude setup.

=> Educate me. I don't know the right answer.

**Answer.** Two things are wrong here, and only one is about the default.

The narrow point: the defaults encode "Copilot yes, Claude Code no" for a project whose entire
skill, convention and drift-pattern system is Claude Code. That is backwards. And because the
consents nest, a user must say yes **twice** — miss either and there is no `CLAUDE.md` and no
invocable skill.

The broader point: **given D4, this question largely dissolves.** If the project-scoped writes are
non-destructive and idempotent — proven in §2.1 — the fix is not to flip a default but to stop
asking. Write the assistant files for all four assistants, or detect what the repo already uses.
Prompting belongs only on machine-scoped writes, and D1 either removes those or makes them the
accepted cost.

**Recommended:** remove the first prompt entirely rather than flip it; keep a single prompt for the
one genuinely machine-scoped action, if B′ is chosen at D1. If A′ is chosen, no prompt remains and
`sp init` becomes fully non-interactive — which is what "one command" requires.

=>

### D6. Should your `~/.sp/user-context/` files ship?

**I owe you a correction here.** I wrote in #204 that `user-context/` is "unobtainable by any
`sp init`." That was overstated. It is a deliberate, tested location — `tests/test_init.py:485-530`
covers it including the absent case, and `tests/test_sp_lock.py:67-68` asserts `sp init` must leave
it writable. It does not ship because it is *the user's own* context, which may well be correct.

But you put `filesystem-access.md`, `github-authority.md` and `consumer-repo-conventions.md` in
Paul's zip, so you wanted him to have them. Are they per-user, or should some ship as defaults?

=> Educate me. I'm inclined to think user context is not part of the product, only project context and global context.

**Ruled 2026-08-18 (Captain agreed): split the three files.** Two ship, one never does.

| File | Kind | Ships? |
|---|---|---|
| `github-authority.md` | policy constraining what an AI may do to a GitHub account | **yes** — should bind everyone, not only its author |
| `consumer-repo-conventions.md` | shared convention for consumer repos | **yes** |
| `filesystem-access.md` | **a permission the user grants** | **never** |

`filesystem-access.md` in full — seven lines:

```markdown
# Filesystem Access

All pipeline projects on this machine have full read access to:
- `~/github/` and all subdirectories
- `~/.sp/` and all subdirectories

Read files from these paths freely without asking for permission.
```

The reason it must never ship is **not** that `~/github/` is a machine-specific layout, though it is.
It is that the file is a **consent artifact**: it grants an AI standing permission to read a tree
without asking. Only the owner of a machine can grant that. Shipping it as a default would have
`sp init` hand the engine read access across every user's home directory on their behalf, without
them having said anything — wrong on principle even if the paths were right. It is also wrong in the
other direction: a mentee who is never asked never learns the grant exists.

**Consequence for `sp doctor` (D8):** it must **not** check whether `filesystem-access.md` exists.
Absence is the correct default state, not a misconfiguration. If `doctor` mentions it at all, it says
this file is the user's to write if they want it.

**Answer.** The principle holds. The refinement is that two of the three files are not user context
at all — they are mislabelled.

Three tiers, by **who owns the content**:

| Tier | Owner | Ships? | Lives in |
|---|---|---|---|
| Product / global | the engine, versioned | yes | `templates/sp-conventions/` → `~/.sp/conventions/` |
| Project | the repo, committed | n/a — travels with the clone | `docs/ai-context/` |
| User / machine | the individual | **no** | `~/.sp/user-context/` |

Now look at what is actually in `~/.sp/user-context/`:

- `github-authority.md` — a policy about what an AI may do to someone's GitHub account. That should
  bind **everyone on the team**, not just whoever wrote it. It is global content in the wrong tier.
- `consumer-repo-conventions.md` — conventions for consumer repos. Also team-wide. Same.
- `filesystem-access.md` — genuinely machine-specific. Correctly placed.

**Recommended:** don't decide whether `user-context/` ships — **split it.** Promote the two policy
files into shipped conventions (which also gets Paul what you wanted him to have), and leave the
machine-specific one as the user's own, never shipped. Your principle survives intact and the
directory keeps its meaning.

=>

### D7. Ownership of a generated file

`sp init --update` rewrites any file still carrying `<!-- Generated by sp init -->` on line 1, even
one hand-edited, because the marker is the only test. A mentor has no way to say "I own this now."

- **A** — hand-editing strips the marker (document it); `--update` then leaves the file alone
- **B** — `--update` merges rather than overwrites
- **C** — document that everything durable goes in `project.md`

=> Relying on this marker is fragile. We need a catalog that says what files sp init works on. We have already had failures when subsequent versions of our software changed the exact text in that string.

**Ruled: a catalog, not a magic string.** Confirmed by experiment — §2.1 shows the marker is the sole
test, so a file whose marker text drifts becomes either permanently un-updatable or silently
overwritable, depending on which side of the comparison changed. The stale help string already found
in this session is the same class of failure: `cli.py:118-122` advertises
`'<!-- Generated by llmflow init -->'` while the constant is `'<!-- Generated by sp init -->'`
(`cli_utils.py:568`) — the two are already out of step in the shipped product.

Design implication: a declared catalog of managed files with per-file policy
(`generated` / `create-once` / `user-owned`), keyed by path rather than by content sniffing. Ownership
becomes a property of the catalog entry, not a string inside the file. `project.md` is then simply a
`create-once` entry rather than a special case in the code (`cli_utils.py:1890`).

**Captain, 2026-08-18: `.claude` files belong in the catalog too, so we don't lose sight of them.**

So the catalog's scope is every file `sp init` touches or places, **including everything under
`.claude/`** — the copied `.claude/skills/*` (D1-A′), and any other `.claude` file the engine writes
or expects. Rationale: `.claude/` is the one tree that is simultaneously generated, partly committed
and partly gitignored, so it is exactly where untracked files go unnoticed. An entry per file also
gives the collision policy of D1 consequence 2 somewhere to live, and lets the `.gitignore` carve-out
of consequence 1 be *derived* from the catalog rather than hand-maintained in a second place.

Minimum fields this implies per entry: path, policy, whether it is committed or ignored, and its
source (packaged template, `~/.sp/`, or project-local).

### D8. The verification command — name and prerequisite

Not a question I raised originally; it surfaced because #204's asks name `sp doctor` as though it
were settled. **It is not built and never was** — the name came from the previous session's wishlist
and I had been repeating it as decided.

**Ruled 2026-08-18: `sp doctor`.** Reason: discoverability is the feature. The failure this whole
issue is about is someone hitting an error that names nothing, so they need a command they can
*guess* — `doctor` is the conventional name for exactly that (`brew doctor`, `flutter doctor`).
`sp init --check` was the alternative and matches the locked "`--update` is a flag on its parent"
rule, but that rule is about `--update` specifically and does not bind here; `init --check` also
reads as "check what init would do" rather than "is this machine healthy", and is undiscoverable
unless you already know `init` exists.

**Blocked on #205.** Two further rulings from the Captain, same day:

> "I don't want to maintain so many alternative ways of saying the same thing."

> "I would like the same discipline for the CLI."

`sp registry status` already partly does `doctor`'s job, three separate commands own
`docs/ai-context/`, `sp transition` is orphaned from `sp content`, and `gui/backend/server.py`
hand-maintains a second copy of the CLI's command names. Adding `doctor` by hand would make a sixth
overlapping entry point. **#205 brings the CLI under the same declarative-schema discipline as
pipeline steps; `sp doctor` should be the first command declared under it, not the last one
hand-wired before it.**

Consequence for scope: `doctor` moves out of this plan's critical path. It is still a #204 ask, but
it is delivered by #205's mechanism.

---

## 4. Test plan — written before any implementation

Ordered by value. Every one of these fails today.

| # | Test | Catches | Notes |
|---|---|---|---|
| T1 | ✅ **DONE** — `EXPECTED_CONVENTIONS` mirroring `EXPECTED_SKILLS`, plus a README-index guard | The three drifted conventions, and all future drift | Landed `design-authority.md`, `sp-debugging.md`, `sp-workflow.md`. Verified on a fresh machine: 8 of 8 installed. Also found the conventions `README.md` had itself drifted to indexing 3 of 8 — now guarded |
| T2 | `sp init` with an empty `HOME`: assert every file `/load-context` reads either exists or is explicitly optional | The whole class of clean-machine bugs | Reachable now — `install_global_skills(sp_home=…)`, `_install_claude_skills(claude_home=…, sp_home=…)`, `default_editions_dir()` all take overrides |
| T3 | Non-TTY `sp init` produces a stated, asserted outcome | The silent return at `cli_utils.py:805-806` | Shape depends on **D4** |
| T4 | Reproduce Paul's failure from an empty `HOME` | Confirms or refutes the empty-read hypothesis | Do this **first** — the fix depends on the mechanism being what we think |
| T5 | ~~`sp init --update` leaves a file whose ownership was taken~~ | — | **Superseded by T8.** D7 replaces marker-sniffing with a catalog, so the test asserts catalog policy, not marker behaviour |
| T6 | After `sp init`, `<repo>/.claude/skills/` contains every `~/.sp/skills/` skill plus project-local ones, and `~/.claude` is never written | D1-A′ | Shape now known. §2.1 already gives the harness: fake `HOME`, assert `~/.claude` absent |
| T7 | The generated `.gitignore` ignores `.claude/` but **not** `.claude/skills/` | D1 consequence 1 | Cheap, and catches the case where the skills are copied but never committed |
| T8 | Catalog-driven ownership: a `user-owned` entry survives `--update`; a `generated` entry is refreshed; policy is keyed by path, not by marker text | D7 | Replaces T5. Must also assert the two marker strings in `cli.py:118-122` and `cli_utils.py:568` agree — they do not today |
| T9 | **Every file `sp init` writes appears in the catalog, including all `.claude/` files** — a file written but uncatalogued fails the test | D7, Captain 2026-08-18 | The guard against losing sight of files. Same shape as T1's drift guard, applied to the catalog: the set of written paths must equal the set of catalogued paths |

**Honest limit, correctly stated.** These are all pytest and all runnable here — the fake-`HOME`
harness in §2.1 is sufficient, and skill shadowing does not affect them (see D1 consequence 3).

The one thing pytest cannot cover is **the skill's own behaviour**: `SKILL.md` is markdown executed
by a model, not code. "Skip a missing file cleanly" is a change to skill *text*, so a test can assert
the files it names exist, or that it declares them optional — but not that a model degrades
gracefully when one is missing.

That gap is closed by a **manual end-to-end run against a clean `HOME`**
(`env HOME=<tmpdir> claude` in the test clone), which needs no second machine and modifies nothing.
It should be recorded as an explicit acceptance step, not left implicit — it is the only check that
exercises what Paul actually hit.

---

## 5. Sequence

D1–D7 are now ruled, so the sequence is unblocked end to end. Ordered so that each step's result can
change the next — nothing later assumes an earlier step's outcome.

1. **T4 — reproduce from an empty `HOME`.** Confirm the bodyless-400 mechanism *before* designing
   against it. §2.1 already built the harness. If the cause turns out not to be the empty read, D3
   and the skip-missing-file work change shape, so this genuinely goes first.
2. **T1 — conventions drift guard** (`EXPECTED_CONVENTIONS`). Independent of every ruling; the
   cheapest real fix in the plan. Lands the three missing conventions with it.
3. ✅ **DONE — D6 split.** `github-authority.md` and `consumer-repo-conventions.md` now ship;
   `filesystem-access.md` deliberately does not, because it is a permission the user grants.
   The shipped `github-authority.md` had its bot-account line replaced by a pointer to
   `~/.sp/user-context/`. Guarded by a test that fails if any shipped template contains an email
   address or absolute home path.
3a. ✅ **DONE — `drift-patterns.md` ships**, installed to the root of `~/.sp/` via a new
   `templates/sp-root/` location for files whose path is a contract. Verified byte-identical to the
   `human-at-the-helm` copy at time of vendoring, so HATH#1's "where truth lives" question is not
   foreclosed. **Every read `/load-context` performs now succeeds on a clean machine except
   `CLAUDE.md`**, which is D1/D4 work.
4. **T8, T9 + the catalog** (D7). The catalog is a prerequisite for the `.claude/skills/` copy,
   because the copy needs a declared collision policy (D1 consequence 2), and because every
   `.claude/` file must be catalogued. Fix the two disagreeing marker strings here. T9 — every
   written path is a catalogued path — is what stops files going missing later.
5. **T7 + `.gitignore` carve-out** (D1 consequence 1) — engine-generated and consumer repos.
6. **T6 + the `.claude/skills/` copy** (D1-A′), sourced from `~/.sp/skills/` plus project-local.
7. **T3 + non-TTY / prompt removal** (D4, D5) — write project-scoped files unconditionally, report
   what was written and skipped.
8. **T2** — the full clean-machine assertion, last, because it is the acceptance test for
   everything above.
9. **Acceptance step — manual, and not optional.** In a fresh clone of a mentoring repo, run
   `sp init`, then `env HOME=<tmpdir> claude` and invoke `/load-context`. This is the only check
   that exercises what Paul hit, because it is the only one where a model reads the files. Needs no
   second machine and modifies nothing on the Captain's setup.
10. `/commit-ready`: full suite, CHANGELOG, commit message with issue refs.

**Steps 1 and 2 need nothing further from the Captain** and are the natural starting point.

---

## 6. Constraints in force

- **No push this session** (Captain). `origin/dev` stays at `cb72cb7` so PR #199 is not retargeted
  and the ~2h Windows build is not restarted. **Commit yes, push no.**
- **CHANGELOG is frozen** while #199 is in flight; this work is for the version after 0.2.1.24.
- **`.gitignore` changes land in consumer repos and in whatever `sp init` generates** — the engine
  change and the mentoring-repo change are not the same edit. D1-A′ means **both are needed.**
- **This plan is not authorization.** Per `rules.md` #15, implementation waits on your explicit
  direction after reviewing it.

=> Do add to CHANGELOG, just don't commit and push.  We may decide to merge this into the current version before merging to main, since we haven't shipped the one that built.

**Ruled, 2026-08-18 — this supersedes the "CHANGELOG is frozen" bullet above.** Do add CHANGELOG
entries as work lands. Do commit. **Do not push.** The version this ships under is deliberately left
open: it may be folded into 0.2.1.24 before that merges to `main`, since the built release has not
shipped yet. So a CHANGELOG entry should be written where it can be re-targeted — do not assume a new
version heading.

No CHANGELOG entry exists yet because no behaviour has changed; the commits so far are this plan,
the corrected #204 diagnosis, and TODO.md.
