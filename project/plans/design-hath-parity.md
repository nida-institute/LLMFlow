# Design — bring Human at the Helm to current maturity (human-at-the-helm#1)

**Status:** awaiting the Captain's review. Not authorization to implement (rules.md #15).
**Started:** 2026-08-19, by the Captain's explicit override of this goal's own sequencing note.

> The issue said this goal starts "once release 0.2.1.24 has shipped and LLMFlow#204 is done. Not
> before." Neither has happened. Captain, 2026-08-19: *"I am overriding it. this is the same theme
> as what we just did, I think we are in context to do it."*

Filed in this repo rather than in `human-at-the-helm` because that repo has no `project/plans/`,
because board 13 tracks the issue, and because this is where the Captain reviews plans. If HATH
should own its own plans, say so and it moves.

---

## 1. What I understand the goal to be

The Captain, 2026-08-19:

> *"our ai context here is now more advanced than the original HATH, by quite a bit. I want HATH to
> have the same level of maturity, without whatever is specific to Scripture Pipelines."*

So this is not "add an installer to HATH". It is **bring the methodology across at its current
level of development, and leave the pipeline engine behind.** The installer is one consequence of
that; the harder half is deciding what "specific to Scripture Pipelines" actually covers, file by
file.

Provenance matters to how this reads. **HATH came first and inspired the AI context in LLMFlow**
(Captain, 2026-08-18). The derivative was exercised daily on real work and evolved; the origin was
not. So this is not porting conventions upstream — it is returning developed material to the
repository it came from.

---

## 2. Verified facts

Read from both repositories on 2026-08-19. Not recalled.

### HATH as it stands

`main`, clean, last commit `620fc10` — **2026-07-29**. Nothing has moved since the issue was filed.

| | |
|---|---|
| Skills | 4 — `authorize`, `commit-ready`, `load-context`, `stand-down` |
| Disciplines | 5 — `cross-repo-choreography`, `design-authority`, `explain-first`, `persistent-context`, `tdd` |
| Templates | `templates/ai-context/` (`github-workflow.md`, `index.md`, `overview.md`, `rules.md`), `templates/CLAUDE.md` |
| Root docs | `README.md`, `adopting.md`, `ai-accounts.md`, `drift-patterns.md` |
| Packaging | **none** — no `pyproject.toml`, `setup.py`, `Makefile` or `install.sh` |

### The shared content has diverged, and LLMFlow's copies are larger

| Skill | HATH | LLMFlow | |
|---|---|---|---|
| `authorize` | 4,353 | 5,422 | +25% |
| `commit-ready` | 4,296 | 7,422 | +73% |
| `load-context` | 3,576 | 6,405 | +79% |
| `stand-down` | 4,305 | 5,203 | +21% |

**`drift-patterns.md` is byte-identical** — 25,017 bytes both sides. It is the one shared artifact
with no drift problem, and HATH is its origin.

### Two premises in the issue are now stale

1. **The runtime coupling is gone.** The issue records that `cli_utils.py` fetched
   `skills/stand-down/SKILL.md` from HATH's `main` during every `sp init`, making HATH live-wired
   into every installation. **That fetch was removed on 2026-08-19** by the Captain's ruling —
   *"Drop the fetch — ship stand-down like every other skill, one source of truth"* — made to stop
   `sp doctor` overwriting a fetched file. **It was not a decision about HATH's role**, and is not
   treated here as having answered anything below. Its effect is only that nothing now forces the
   answer to Q3.

2. **HATH's context layout is already the pure-Python one.** `skills/load-context/SKILL.md` reads
   `CLAUDE.md` and `docs/ai-context/{index,rules,overview}.md` and **nothing under `~/.sp`**. It is
   LLMFlow's version that added the machine-global reads. So Q4 is less "design a new layout" than
   "decide where the `~/.sp` *content* goes when there is no `~/.sp`."

---

## 3. The Captain's rulings — 2026-08-19

Answers verbatim. Consequences recorded separately below each.

### The governing principle

=> our ai context here is now more advanced than the original HATH, by quite a bit. I want HATH to have the same level of maturity, without whatever is specific to Scripture Pipelines.

This is the test every file is measured against in §4. It also settles Q2 without a separate
ruling: which skills transfer is decided by whether they are Scripture-specific, not by taste.

### Q1 — what "installer" means

=> I'm open to suggestions, but it should be easy to install into an existing programming project repository.

Open for a recommendation; see decision **H1**. The operative constraint is **existing** repository —
this is not a project generator, it adds to a repo that already has code and history.

### Q2 — which of the six missing skills belong

=> see the general principle above

### Q3 — where truth lives for a shared skill

=> currently, sp is where we get more real world experience quickly, so I htink sp is where truth lives for now. that could change.

**LLMFlow is upstream for shared skills, for now.** Two consequences worth stating because they
are easy to get backwards:

- HATH's four skills are **replaced** by LLMFlow's larger versions, generalized. They are not
  merged, and HATH's are not preserved for being older.
- This is explicitly provisional. Whatever mechanism carries content across must be re-runnable in
  the other direction, and must not silently become the only copy.

### Q4 — the minimal context layout for a pure-Python project

=> no need for ~/.sp, but that means the contents of our ~/.sp live in the project repo itself.

**Everything is repo-scoped.** No machine-global directory at all — which is a simpler shape than
`sp`'s two-tier one, and the same direction as D1-A′ in `design-onboarding-fresh-clone.md`, where
skills moved into `<repo>/.claude/skills/` rather than `~/.claude`.

The unresolved part is *where* in the repo the conventions and `drift-patterns.md` land, since
LLMFlow's `load-context` reads them at fixed `~/.sp/` paths. See decision **H2**.

---

## 4. Classification — what transfers, what stays

Measured against the governing principle. Evidence is each artifact's own text, quoted where the
call is not obvious.

### Skills

| Skill | Verdict | Why |
|---|---|---|
| `authorize` | **transfers** | Pure methodology — declare scope, get sign-off. No engine coupling. |
| `stand-down` | **transfers** | Pure methodology. HATH is its origin. |
| `handoff` | **transfers** | Writes `project/HANDOFF.md` so a fresh session can resume. General practice; the path is the only thing to generalize. |
| `load-context` | **transfers** | HATH already has it; LLMFlow's is 79% larger. Generalize away the `~/.sp` reads and the `sp`/pipeline vocabulary. |
| `commit-ready` | **transfers** | The *shape* is general — a definition of done. Its content names `pytest`, `CHANGELOG`, version bumps and issue refs; those are conventions of this project, not of Scripture. Needs the specifics parameterized. |
| `audit-code` | **transfers, with surgery** | Framed as *"Audit Python plugins… verifying plugins are deterministic… local plugins don't silently reimplement LLMFlow core utilities."* The plugin framing is `sp`; "audit Python code for structural correctness and determinism" is general. The largest editing job of the six. |
| `audit-pipeline` | **stays** | *"Audit LLMFlow pipeline contracts… response_format… additionalProperties:false."* Entirely engine. |
| `audit-output` | **stays** | *"Audit pipeline output files against docs/audits/ checklist."* Entirely engine. |
| `audit-prompts` | **stays** | *"Audit LLMFlow prompt files (.gpt) AND pipeline files (.yaml)."* Entirely engine. |
| `release` | **stays** | *"Execute LLMFlow release process… verifying Nuitka builds actually succeeded on all platforms."* **The issue guessed this "looks like general practice"; its own text says otherwise** — it is about Nuitka and this repo's GitHub Actions. A general release discipline could be written later; this is not it. |

**Six transfer, four stay.** The issue's guess was that `handoff` and `release` were the obvious
methodology pair. Half right: `handoff` yes, `release` no.

### Conventions (`~/.sp/conventions/`)

| File | Verdict | Why |
|---|---|---|
| `design-authority.md` | **transfers** | General. Already exists in HATH as `disciplines/design-authority.md` — check for divergence before overwriting. |
| `surface-decisions.md` | **transfers** | General, and carries the `=>` answer-slot convention this document uses. |
| `github-authority.md` | **transfers** | About GitHub and AI authority, not Scripture. Already scrubbed of the personal bot account. |
| `llmflow-project-tracking.md` | **transfers, renamed** | The audits/plans rolling-file structure is general practice; "one file per pipeline" is not. |
| `sp-workflow.md` | **splits** | Mixed. Shell conventions, audit workflow and "files the human controls" are general; `sp run`/`sp lint` are not. |
| `README.md` | **rewritten** | An index of the above; must match whatever ships. |
| `llmflow-pipeline-steps.md` | **stays** | Pipeline YAML `description:` field. |
| `llmflow-prompt-organization.md` | **stays** | `.gpt` prompt structure. |
| `sp-debugging.md` | **stays** | `linter_config.log_level`, pipeline debug dumps. |
| `consumer-repo-conventions.md` | **stays** | About depending on LLMFlow. |

`drift-patterns.md` needs no transfer — it is already identical and HATH is its home.

---

## 5. Open decisions — the Captain's

**Answer inline after each `=>`.**

### H1. What form does the installer take?

The constraint is "easy to install into an existing programming project repository". Everything
being installed is markdown — no runtime, no dependencies.

| | Approach | For | Against |
|---|---|---|---|
| **A** | **`pip install human-at-the-helm`, then `hath init`** | Mirrors `sp init`, which we have just spent a release proving out. Version-pinnable, upgradeable, `hath doctor` comes almost free. | Requires Python and a package name on PyPI. Adds a dependency to a repo that gains nothing else from it. |
| **B** | **`curl … \| sh`, or a downloaded `install.sh`** | No language runtime, works for any repo. Simplest possible thing. | Piping the internet to a shell is the pattern this methodology exists to be sceptical of. Harder to upgrade or verify. |
| **C** | **`git clone` HATH, run `./install.sh /path/to/repo`** | Nothing hidden — you can read what you are about to run. No registry, no network at install time. | Two steps. The clone is a copy the user must remember to update. |

**The recommendation above is withdrawn.** It assumed the audience was "Python programmers working
in pure Python", which the issue said and which is wrong.

=> I am using this on a typescript project too, so we need to support multiple languages.

**Revised, 2026-08-19.** A `pip`-only installer cannot be the answer when a TypeScript developer
may have no Python at all. One fact narrows the problem: **HATH ships only markdown.** Nothing
lands in the target repo but text, so the question is purely what the *operator* must already have
installed — not what the project acquires.

| | Approach | For | Against |
|---|---|---|---|
| **A′** | **`install.sh`**, from a clone or a downloaded single file | No runtime at all; works for any language. HATH has no release infrastructure today and this needs none. | Windows without WSL or git-bash. `curl \| sh` is a trust pattern this methodology should be sceptical of — so: download, read, then run. |
| **B′** | **`pip` and `npm` wrappers** around the same content | Native to each ecosystem; `npx human-at-the-helm init` is what a TS developer expects. | Two packaging paths, two registries, two release processes — for a repo that has none. |
| **C′** | **A single binary**, as `sp` already ships via Nuitka | No runtime, all platforms including Windows. Precedent and machinery exist in LLMFlow. | Heaviest to stand up: build infrastructure for shipping markdown. |

**A′ was recommended, then withdrawn once the deciding facts arrived.**

=> I don't have a Windows machine. Mac and Linux. But I have users on Windows. However, most developers do seem to have Node these days.

=> we can tell them how to install Node and npx if they don't have it. a little heavyweight, but ...

**Ruled 2026-08-19: an `npx`-run installer, executed from GitHub. npm registry deferred.**

The deciding pair of facts is *Windows users but no Windows machine*. A shell script would force a
choice between excluding those users and making a promise neither the Captain nor the AI can
verify — the same shape as `sp setup` reporting success without configuring the key it claimed to
(LLMFlow#195). Node removes the problem instead of managing it: the cross-platform behaviour lives
in Node's `fs` and `path`, which are tested by Node. No CRLF-vs-shebang failure, no MSYS path
translation, no execute-bit loss.

Rejected along the way, and why:

- **`install.sh` + `install.bat`** — two implementations of "copy these files, never clobber one
  that exists". They drift, and the platform with fewer users gets the weaker guard. That is the
  `.cursorrules` failure and the two-of-three saveas-guard failure, both found the same day this
  was written. Writing it deliberately into the repository whose subject is that pattern is not
  defensible.
- **Dual `pip` + `npm`** — two packaging paths for one set of markdown; the same duplication in a
  different costume.
- **Single binary** — correct if Windows must be first-class *and* no runtime may be assumed. Node
  being widely present makes the build infrastructure disproportionate for shipping markdown.

**Run from GitHub for v1:** `npx github:nida-institute/human-at-the-helm`. No publish step, no
package name to claim, no release process for a repo that has none. Publishing to the registry
later only shortens the command.

**What the target repo gains: nothing but markdown.** `npx` runs on the operator's machine. A
Python or TypeScript project ends up with text files, not a Node dependency.

**On the heavyweight objection**, which the Captain raised and which is fair: telling a Python
developer to install Node in order to copy markdown is disproportionate on its face. Two things
make it acceptable rather than merely tolerable — Node is not a *requirement*, because the
documented `git clone` and copy remains as a fallback and is exactly what adoption is today, so
nobody is blocked; and the cost falls once, on the operator, not on the repository or its other
contributors.

**Windows remains untested.** Lower risk than a shell script, not zero. Our own code stays on
`path.join` and avoids shelling out, and the documentation says "should work on Windows; untested"
until a Windows user confirms it. Claiming more than that is the thing this methodology exists to
prevent.

---

#### H1 superseded, 2026-08-19 — there is no installer

The `npx` ruling above stood for one exchange before the Captain questioned the premise:

=> a documented git clone and copy is actually a pretty good solution, people should be able to do that, no? they can use the File Manager or whatever is comfortable for them. Maybe we don't need an installer.

=> yes

**Ruled: no installer. Documented `git clone` and copy, plus a `/hath-check` skill that verifies
the result.**

**Why this is better than anything above, not merely cheaper.** The job is four directory copies:
`skills/` → `<repo>/.claude/skills/`, conventions → `<repo>/docs/ai-context/conventions/`,
`drift-patterns.md` alongside them, and the templates if absent. Every option previously considered
was infrastructure wrapped around `cp -r`.

More pointedly: **LLMFlow#204 was an installer failure.** `sp init` returned silently on a non-TTY,
hid Claude Code setup behind two prompts defaulting to No, and placed skills where Claude Code does
not read them. A person copying a folder makes none of those mistakes. The clever tool was the part
that broke.

There is also a fit argument. HATH's audience is adopting a *methodology*; copying the files means
reading them, which for this content is closer to a feature than to friction.

**What is given up, and how each is recovered:**

| Lost | Recovered by |
|---|---|
| Getting the path exactly right — `.claude/skills/<name>/SKILL.md`, where a mistake fails **silently** because the slash command simply does not exist | `/hath-check` names the misplaced file |
| Updating — copy-once has no refresh path, and re-copying can clobber local edits | documented re-copy, with `/hath-check` reporting stale or half-applied state |
| Knowing what you got — no inventory, no answer to "is this set up correctly?" | `/hath-check` |

**`/hath-check` is a skill, not a program.** The audience already runs Claude Code, so the verifier
needs no runtime, no packaging, no registry, and works on every platform including Windows. This is
the same lesson as #204: what made that tractable was not `sp init` but `sp doctor` — the command
that turned an error naming nothing into a line naming the defect.

**This removes from the plan entirely:** Node, npm, the registry question, the Windows-testing
problem, and H1 itself. Cost: one additional markdown file in the skill set.

**Consequence for §4:** the skill set to ship becomes **seven** — the six that transfer, plus
`/hath-check`, which is new and has no LLMFlow counterpart.

**Consequence for §6:** test 3 ("nothing is written outside the target repository") and test 4
("an existing file is never clobbered") no longer describe an installer we control. They become
assertions about what `/hath-check` reports, and the no-clobber guarantee moves from code to the
documented procedure — a real weakening, accepted knowingly, because the procedure is four copies a
person performs and can see.

---

#### H1 settled, 2026-08-19 — Claude Code is the installer

=> could we use Claude Code as our installer?

=> clone, start Claude, give Claude a desination and ask it to install

**Ruled. The adoption flow is:**

```
git clone https://github.com/nida-institute/human-at-the-helm
cd human-at-the-helm
claude
> /install ~/code/my-typescript-app
```

**Why this is the answer and the previous three were not.** Every earlier option was a runtime we
would have to choose, ship and test on platforms we do not own. The audience already runs Claude
Code — that is the premise of the entire methodology — so it is the one dependency that can
honestly be assumed. It is cross-platform, so the Windows problem disappears rather than being
managed, and no Windows machine is needed to support Windows users.

**The bootstrap problem disappears too.** The install skill lives in **HATH's own**
`.claude/skills/install/`, committed. Cloning the repo and starting Claude Code there makes
`/install` available immediately as a project skill. The installer never has to be installed. The
source is the working directory and the destination is an argument, so there is no fetch, no
network, and no ambiguity about what is being copied.

**A manifest, not improvisation.** The obvious objection to "let the AI install it" is that this is
a methodology about *not* letting an AI perform unreviewed writes, and shipping an improvising
installer as its adoption path would be self-undermining. So the AI is given nothing to decide:

```
skills/authorize/          → .claude/skills/authorize/          create-or-replace
docs/conventions/*.md      → docs/ai-context/conventions/       create-or-replace
drift-patterns.md          → docs/ai-context/                   create-or-replace
templates/CLAUDE.md        → CLAUDE.md                          create-only
templates/ai-context/*.md  → docs/ai-context/                   create-only
```

**The manifest is the installer; Claude Code is the runtime.** Same shape as
`data/file-catalog.yaml` (LLMFlow#204, D7) — declarative data stating what goes where, with the
executor separated from the decision. `create-only` restores in data the no-clobber guarantee the
previous ruling recorded as lost, and `/hath-check` verifies afterwards that it held.

**Adoption becomes the first exercise of the methodology.** The skill declares scope — every file it
will write, every file it will not touch — and waits for approval before writing. That is
`/authorize`, one of the skills being installed, applied to its own installation. The user meets the
discipline before reading a word about it.

**Retained deliberately:** the documented `git clone` and copy-by-hand path stays in the README, for
anyone without Claude Code or who simply prefers a File Manager. It costs nothing — it is the
documentation the manifest describes anyway.

**Risk carried forward:** a manifest is a second list, and a second list drifts. It must be derived
from what the repository actually contains, or tested against it. That failure has appeared three
times in one day — unshipped conventions, the marker string, and the `${var}` guard on two paths of
three.

**Consequence for §4:** the skill set becomes **eight** — six transferred, plus `/hath-check`, plus
`/install`, the last living only in HATH's own repo and never copied to a target.

### H5. The conventions split — two names, ruled 2026-08-20

Step 4 needed two names before it could be executed. Both were put with a recommendation.

**D1 — the name of the general half of `sp-workflow.md`:** `workflow.md`, `session-conventions.md`,
or `ai-workflow.md`.

=> D1 - A.

**D2 — where the per-pipeline half of project tracking goes:** folded into `sp-workflow.md`, or kept
as an engine-side `llmflow-project-tracking.md` beside a general `project-tracking.md`.

=> D2 - A.

**Ruled: `workflow.md`, and one engine file rather than two tracking files.**

Executed the same day. What the split produced:

| File | |
|---|---|
| `workflow.md` | **new, transfers** — shell commands, audit workflow, design-comment rules, files the human controls. Tooling examples gained their TypeScript counterparts per §6 5a. |
| `sp-workflow.md` | **stays** — the CLI rules, the per-pipeline tracking unit, and where the machine user account is recorded. |
| `project-tracking.md` | **transfers**, renamed from `llmflow-project-tracking.md`; rolling files per subsystem, the project naming its own unit. |
| `github-authority.md` | **transfers** — four lines generalized; the policy itself untouched. |
| `design-authority.md`, `surface-decisions.md` | **transfer unedited** — measured clean of engine vocabulary before the work started. |
| `README.md` | **rewritten** — general and engine conventions under separate headings. |

`tests/test_portable_conventions.py` is the guard, importing its patterns from
`test_portable_skills.py`. Two of its tests are about the *move* rather than the vocabulary: one
fails if `sp-workflow.md` loses the prohibition on running a pipeline unasked, one fails if
`workflow.md` keeps a heading whose content went to the other file.

**Left for the Captain, not done here:** `docs/ai-context/audits-pattern.md:31` points at
`~/.sp/conventions/llmflow-project-tracking.md`, which no longer exists. That directory is under the
Captain's authority, so the stale pointer is reported rather than fixed.

### H6. The word, and what a session reads — ruled 2026-08-20

**D5 — one word for these documents, in both repositories.**

=> I like 'disciplines' for each, any reason to go with conventions?

=> recommend one convention for both

**Ruled: `disciplines`, and Scripture Pipelines is the side that renamed.** HATH has published
`disciplines/` on a public unversioned `main`, linked from its README and `adopting.md`, so its
paths break adopters if changed (§8); `~/.sp/conventions/` was created by an installer and
nobody links to it. Naming for methodology material comes from the methodology's home — the
reverse is this engine's internal vocabulary colonizing the published methodology. Measured
first: 19 files, ~155 lines, ~100 of them in two test files because the installer function name
is part of it. Landed in `a8d7c15`; `~/.sp/conventions/` is left behind on existing machines and
must be deleted by hand.

**D6 — do the essays install, and are they read every session?**

=> C

**Ruled C: install all nine; `load-context` reads the operational rules each session and treats
the essays as reference.** The mechanism is `disciplines/README.md`, the index that ships beside
the files — not a list inside the skill, which would be a second copy of the shipped set.

**The multi-tool question, asked while step 5 was being written:**

=> can people install with a gpt client like chatgpt, or only with a command line tool?

Answered in the README rather than by a ruling, because it is a fact rather than a preference:
any assistant with local file access can be pointed at `manifest.yaml`, which names no tool; a
browser-only chat client cannot, because it has no filesystem and what it prints for pasting is
an imitation of a file rather than the file. Three adoption paths are now documented.

**Still open, flagged not decided:** whether HATH should ship per-tool pointer files
(`.cursor/rules`, `.github/copilot-instructions.md`, `AGENTS.md`) so its skills reach Cursor,
Copilot and Codex users. This engine already generates that shape, so the pattern exists — but
it is four more manifest entries and a support claim for tools neither the Captain nor the AI
has tested.

=>

### H2. Where do the conventions and `drift-patterns.md` live in the repo?

Q4 says they live in the project repo. `load-context` has to read them from a fixed path.

- **A** — `docs/ai-context/` alongside `index.md`, `rules.md`, `overview.md`. One directory for all
  committed AI context; `load-context` already reads that directory.
- **B** — a dedicated `.hath/` directory, mirroring `~/.sp/`'s shape. Keeps methodology separate
  from project-authored context, at the cost of a second place to look.
- **C** — `docs/ai-context/conventions/` — inside the existing directory but distinguishable, so a
  reader can tell shipped methodology from this project's own writing.

**Recommendation: C.** A project must be able to tell which files are its own and which came from
HATH — that distinction is exactly what `sp doctor`'s ownership boundary turned out to need, and
what `docs/ai-context/project.md` exists to protect in `sp`. A flat directory (A) loses it; a
hidden directory (B) makes methodology feel like tooling rather than something to read.

=> d'accord

**Ruled 2026-08-19: C** — `docs/ai-context/conventions/`, with `drift-patterns.md` alongside it.
Shipped methodology is distinguishable from the project's own writing at a glance, which is what
makes an ownership boundary (and therefore a repair or update command) possible later.

### H3. How does content get from LLMFlow to HATH, and stay current?

Q3 makes LLMFlow upstream "for now". Whatever is built has to survive that changing.

- **A** — **manual, recorded.** A one-time port now, with a note in both repos saying which is
  upstream. Cheapest; drifts the moment either side is edited, which is how we got here.
- **B** — **a sync script** in one repo that copies and generalizes, run deliberately, with a test
  that fails when the two diverge unexpectedly. Mirrors `EXPECTED_CONVENTIONS` and the
  no-personal-data guard already in this repo.
- **C** — **HATH vendors from LLMFlow at release time**, the way `templates/sp-root/` vendors
  `drift-patterns.md` today.

**Recommendation: B.** The drift in §2 happened because a copy existed with nothing watching it.
A failing test is the only thing that has actually worked in this repo — the three unshipped
conventions were found that way.

=> good

**Ruled 2026-08-19: B** — a sync script, run deliberately, with a test that fails when the two
sides diverge unexpectedly.

### H4. Does the generalization edit LLMFlow's copies, or fork them?

Six skills transfer, and each needs `sp` vocabulary removed. Two ways:

- **A** — **HATH gets a generalized copy; LLMFlow keeps its specific one.** Two texts per skill,
  deliberately different. Honest, but doubles what H3 has to watch.
- **B** — **generalize in LLMFlow too**, so one text serves both, with project specifics moved into
  `docs/ai-context/` where they belong. Fewer copies; but it changes skills this project depends on
  daily, mid-release.

**Measured before recommending, 2026-08-19.** The `sp` vocabulary is *not* woven through these
skills. It clusters:

| Skill | Lines | Lines mentioning `sp` / pipeline vocabulary |
|---|---|---|
| `stand-down` | 127 | **0** |
| `handoff` | 92 | 1 |
| `authorize` | 150 | 5 |
| `commit-ready` | 256 | 13 |
| `load-context` | 147 | 17 |
| `audit-code` | 195 | **22** |

And in `load-context` the 17 sit in three blocks — "key rules to internalize" (`:88-90`), "what NOT
to do" (`:131-137`), and "related skills" (`:143-147`).

**The decisive finding: `:88-90` is a paraphrase of `docs/ai-context/rules.md` items 2, 3 and 4 —
the file the skill's own Step 4 instructs the reader to `cat`.** The skill summarises a document it
is about to make you read. That is the same defect fixed in `.cursorrules` on the same day: a
summary that drifts from its source and silently becomes a weaker version of it.

So B is not merely "fewer copies". It removes duplication that should not be in a skill at all. A
skill's job is the procedure — read these files, in this order, report this summary. The project's
rules belong in the files the procedure fetches.

=> ok, let's do that

**Ruled 2026-08-19: B for five, A for `audit-code`.**

- **B** — one shared text for `authorize`, `stand-down`, `handoff`, `load-context`, `commit-ready`.
  The `sp`-specific lines come out of the skill and stay only in `docs/ai-context/rules.md`, where
  they already exist. LLMFlow loses nothing: the session still receives those rules, from the file
  that owns them.
- **A** — `audit-code` is forked. Its 22 lines are not a duplicated summary but the actual subject
  matter (plugin determinism, local plugins reimplementing LLMFlow core utilities). There is no
  authoritative file elsewhere to move that to, so HATH needs a genuinely different skill rather
  than a generalized copy of this one.

**The risk, stated rather than minimized:** B edits `load-context` and `commit-ready`, which this
project runs at the start of every session, while 0.2.1.24 is unshipped. What makes it safe is that
only text duplicating a file the same skill already reads is removed — no capability is deleted —
and guard test 5 fails if any `sp` vocabulary survives.

---

## 6. Test plan — written before implementation

Following the pattern that has worked here: a failing test that encodes the requirement, not a
check that mirrors the implementation.

**Revised after H1 was superseded.** With no installer there is no install code to test. Tests 1, 5
and 6 are the load-bearing ones; the rest describe what `/hath-check` must report.

1. **The shipped set is derived, never a second hardcoded list.** Whatever enumerates the skills and
   conventions — `/hath-check`'s expectations, the sync script of H3, the README index — reads what
   the repository actually contains. A second list is how three conventions went unshipped for
   months in LLMFlow#204.
2. **`/hath-check` names a misplaced skill.** Given `SKILL.md` at `.claude/skills/SKILL.md` rather
   than `.claude/skills/<name>/SKILL.md`, it must say so. This is the silent failure the manual copy
   makes possible, and the only reason the checker exists.
3. **`/hath-check` names a missing file**, and says where it should go.
4. **`/hath-check` names a stale file** — present, but differing from what HATH ships. The update
   path is a re-copy, so detecting drift is what makes it safe.
5. **No Scripture-specific vocabulary ships.** A guard test failing on `sp run`, `.gpt`,
   `pipelines/`, `response_format` and similar in any transferred file. This is the mechanical half
   of the governing principle and the only thing that keeps it true.

5a. **Both ecosystems are served, concretely.**

=> it would be nice to provision this for both Python and Typescript, with pytest and a good Typescript test framework in mind

**Ruled 2026-08-19.** The first draft of guard 5 failed on any mention of `pytest`, which
would have pushed the skills toward abstraction — "run the test suite" teaches nobody
anything. A skill is *more* useful for naming a real command; it is only unusable when it
names one ecosystem's and not the other's.

So the rule is **parity, not silence**: wherever a Python command appears, its TypeScript
counterpart appears beside it — `pytest` ↔ `vitest`, `hatch` ↔ `npm`/`pnpm`. A skill naming
neither is fine; `stand-down` is entirely about conduct and needs no commands at all, and
passes untouched.

**Framework: Vitest named as the default, Jest noted as the widely-deployed alternative.**
Vitest is ESM-native and its API is Jest-compatible, so one example reads correctly for
both. Proposed by the AI, not ruled — swap it if you prefer Jest first.
6. **No personal data ships.** Port the existing LLMFlow test that fails on any email address or
   absolute home path.
7. **`drift-patterns.md` stays byte-identical** to what LLMFlow ships, per §8.

**Honest gap:** the no-clobber guarantee is no longer enforceable by code. It moves from an
installer's `if not exists` to a documented procedure a person follows. `/hath-check` can report
that a file was overwritten only if it can tell — which it can for shipped files, and cannot for a
project's own `CLAUDE.md`. Accepted knowingly.

---

## 7. Sequence

Ordered so each step's result can change the next.

1. **H1–H4 answered.** Everything below depends on at least one of them.
2. **Guard tests 5 and 6 first**, against the four skills HATH already has. They are the definition
   of "without whatever is specific to Scripture Pipelines", and writing them first makes the
   classification in §4 falsifiable rather than a claim in a document.
3. **Generalize the six transferring skills**, one at a time, each landing green against test 5.
4. **The conventions split** (H2), including breaking `sp-workflow.md` into its general and
   engine-specific halves. **Done 2026-08-20** — see H5 for the two names it needed and what it
   produced.
5. **The manifest, then `/install`, then `/hath-check`** — in that order, because the manifest is
   the specification the other two execute and verify against. `/install` lives in HATH's own
   `.claude/skills/` and is never copied to a target; `/hath-check` is shipped to targets. Both are
   written against the manifest rather than against each other, so a target can be verified by a
   checker that never saw the installer run. **Done 2026-08-20** (HATH `d8a3642`), preceded by the
   content transfer (`24fd64f`) after ruling D3-A moved it ahead of the manifest: a manifest
   written against directories that do not yet exist cannot be tested against reality, which is
   H1's stated risk.
6. **The sync mechanism** (H3), last — it can only be written once there is a stable set to sync.
7. **Acceptance, manual and not optional:** a real Claude Code session in a plain Python repo with
   no `~/.sp` and no pipelines, running `/load-context`. The only check where a model reads the
   files, and the same step LLMFlow#204 still owes.

---

## 8. Constraints in force

- **HATH's `main` is public and unversioned.** There is no release process and no tag scheme.
  Anything that breaks a path in `skills/` breaks it for anyone who has already adopted by hand.
- **`drift-patterns.md` must stay byte-identical** to what LLMFlow ships, or the vendoring in
  `templates/sp-root/` starts drifting — the exact failure this work exists to end.
- **LLMFlow's release is unshipped.** `dev` is 26 commits ahead of `origin/dev` and unpushed by the
  Captain's standing instruction. Work here must not require pushing that.
- **This plan is not authorization.** Per rules.md #15, implementation waits on the Captain's
  explicit direction after review.
