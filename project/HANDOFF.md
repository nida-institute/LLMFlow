# HANDOFF — 2026-08-19

Supersedes the 2026-08-17 handoff entirely.

---

## ▶ NEXT ACTION — merge release PR #199. It is green and clean.

**This changed late on 2026-08-19: the ~2h Windows build finished and passed.** All five checks
pass; the PR is `MERGEABLE` / `CLEAN`. It was the blocker for everything else, including pushing.

```bash
gh pr checks 199                    # expect 5 rows, all "pass"
gh pr view 199 --json mergeStateStatus,headRefOid
                                    # expect CLEAN, head cb72cb7
```

**Per `project/RELEASE_CHECKLIST.md`, in this order:**

1. Merge with a **merge commit** — not squash, not rebase — so `release.yml` can resolve `HEAD^2`.
2. **Tag the merge commit**, deleting any stale tag of that name first.
3. Approve the **`pypi` environment gate** — a manual GitHub deployment approval, *not* a PyPI login.
   Publishing uses trusted publishing (OIDC); there is no password or token.

**Then, and only then, push the 21 local commits** (see the next section).

**Decide before or during the merge — the release split.** `CHANGELOG.md:3` is now `## Unreleased`
with the version deliberately unset, holding this session's onboarding work. `pyproject.toml:3` says
`0.2.1.24`. The Captain's ruling (2026-08-18): *"We may decide to merge this into the current version
before merging to main, since we haven't shipped the one that built."* So either retarget
`## Unreleased` → `0.2.1.24` and include it, or bump to `0.2.1.25` and ship it next. **Unresolved.**

---

## ⚠️ 21 COMMITS COMMITTED LOCALLY, NOT PUSHED

`origin/dev` is at `cb72cb7`; `dev` is 21 ahead. Standing instruction from the Captain, 2026-08-18:
*"committing is safe, push is not."* Pushing to `dev` while #199 is open retargets the PR and starts
a fresh build — it happened twice on 2026-08-17 and cost two builds, including a 2h Windows job.

**That constraint expires the moment #199 is merged.** After the merge, push.

```bash
git log --oneline origin/dev..dev | wc -l    # expect 21
git rev-parse --short origin/dev             # expect cb72cb7
git status --short                           # expect empty
```

Working tree is clean. Nothing is uncommitted. Suite: **2621 passed, 13 skipped**.

---

## Active threads

### 1. Release PR #199 (dev → main) — **green, awaiting merge**

- **Goal:** ship 0.2.1.24.
- **State:** all five checks pass; head `cb72cb7`; `MERGEABLE` / `CLEAN`.
- **Next step:** the NEXT ACTION above.
- **Verify:** `gh pr checks 199` → 5 × pass.

### 2. #204 fresh-clone onboarding — **substantially done, one piece left, blocked on the Captain**

- **Goal:** clone a mentoring repo such as `sil-translator-notes`, run `sp init`, and
  `/load-context` works. Nothing hand-carried. (Captain confirmed this wording 2026-08-18.)
- **State:** the `~/.sp` packaging gap is closed and `sp doctor` exists. **Every read
  `/load-context` performs now succeeds on a clean machine except `CLAUDE.md`, which is
  deliberate** (D3-A).
- **Next step:** **D1-A′** — copy skills into `<repo>/.claude/skills/`. **Blocked:** see decisions 1
  and 2 below.
- **Verify:** run `sp doctor` after `sp init` against a fresh `HOME`; every check passes except
  `✗ No skills are where Claude Code can find them`. That one line *is* the remaining work.

  ```bash
  H=$(mktemp -d); R=$(mktemp -d); git init -q $R
  (cd $R && env HOME=$H sp init >/dev/null 2>&1 && env HOME=$H sp doctor)
  ```

Landed this session, with SHAs:

| Commit | What |
|---|---|
| `e20af51` | `git status --short` → `--branch` in `load-context`; guard across all 10 skills |
| `ee28721` | 3 missing conventions shipped; `EXPECTED_CONVENTIONS` drift guard; README index guard |
| `6d52ffd` | `drift-patterns.md` shipped via new `templates/sp-root/`; D6 split; no-personal-data guard |
| `ae78a7f` | **`sp doctor`** — `src/llmflow/doctor.py`, `tests/test_doctor.py` (8 tests) |
| `fd605f2`, `c49a61c` | `=>` answer slots, no-jargon, well-formed-request rules shipped as conventions |

### 3. #205 CLI schema discipline — **filed, not started**

- **Goal:** one declarative source for CLI commands, as pipeline steps already have. Captain's
  rulings: *"I don't want to maintain so many alternative ways of saying the same thing"* and *"I
  would like the same discipline for the CLI."*
- **State:** issue filed with verified evidence; six questions open. No code.
- **Next step:** the Captain answers the six questions. **Not a gate on anything in #204.**
- **Verify:** `gh issue view 205`.

### 4. human-at-the-helm#1 — **filed, deferred until after this release**

- **Goal:** HATH needs an installer, the full skill set, and to work for pure-Python projects.
- **State:** filed; questions deferred by the Captain until the goal starts. Board 13, Todo,
  position 1.
- **Verify:** `gh issue view 1 --repo nida-institute/human-at-the-helm`.

### 5. Scripture editions #200 / versification #203 — **parked, unchanged**

- **State:** #200's code is on the **local** tag `wip/scripture-200` (`05d75a5`, `34c7931`) and is
  **not on `dev`**. Cherry-pick after #199 merges. #203 blocks OT use of `sil-translator-notes`.
- **Verify:** `git log --oneline cb72cb7..wip/scripture-200`. Both `wip/*` tags are **local only** —
  push them or re-apply before anything could collect them.

---

## Open decisions — the Captain's, blocking

1. **D4 / D5 — the interactive gate. Blocks D1-A′.** The Captain said *"educate me"* on both; the
   plan holds recommendations, and **a recommendation is not a ruling.** `_configure_ai_assistants`
   returns silently when stdin is not a TTY (`cli_utils.py:805-806`), and Claude Code setup sits
   behind two `default=False` prompts (`cli_utils.py:777`, `811-812`) — so a fresh clone gets no
   skills copied. Still to decide: whether `.cursorrules`, `.windsurfrules` and
   `copilot-instructions.md` are written unconditionally, and whether the prompts disappear entirely.
2. **`.gitignore` — `sp init` writes none at all.** Verified: a fresh `sp init` produces no
   `.gitignore` and no `.claude/`. Earlier notes describing a "carve-out in the generated
   `.gitignore`" were wrong; there is nothing to carve. `sil-translator-notes` ignores `.claude/`
   wholesale, so committing `.claude/skills/` needs a hand edit there. **Does `sp init` start
   generating a `.gitignore`, or does the mentor edit theirs?** If the engine never writes one,
   "clone and it works" depends on the mentoring repo being hand-configured — the class of problem
   #204 exists to remove.
3. **The release split** — see NEXT ACTION.
4. **`sp doctor` checks presence, not content.** The Captain's own
   `~/.sp/conventions/surface-decisions.md` is the stale **790-byte** copy with zero `=>`
   occurrences; the shipped one is 3404 bytes. `install_global_conventions` uses `force=False`, so
   only `sp init --update` refreshes it. Whether `doctor` should compare content is genuinely open —
   a user may have edited a convention deliberately, and calling that a fault would be wrong.

---

## Decisions settled this session — do not reopen

- **D1-A′: project-level `.claude/skills/`, committed; nothing in `~/.claude`.** *Why:* Claude Code
  reads skills only from `~/.claude/skills/` or `.claude/skills/` — a skill in `~/.sp/skills/` is
  not invocable, which is why the copy exists at all. The Captain accepted "minimal use of
  `.claude`" at project level, populated from `~/.sp/skills` plus project-local skills.
- **D3-A: `/load-context` reads `CLAUDE.md` only if present.** *Why:* it is gitignored by
  convention, so a clone never has one; committed context lives in `docs/ai-context/`. **A missing
  `CLAUDE.md` is therefore not a bug** — `sp doctor` reports it as INFO.
- **D6: `filesystem-access.md` must never ship.** *Why:* it grants an AI standing read access to a
  directory tree. Only a machine's owner can grant that; shipping it would have `sp init` pre-grant
  it on every user's behalf. `github-authority.md` and `consumer-repo-conventions.md` are team
  policy and do ship — with the personal bot account removed.
- **D7: a catalog replaces marker-sniffing**, and per the Captain **all `.claude` files belong in
  it** so none are lost sight of. *Why:* the `<!-- Generated by sp init -->` marker is the only
  ownership test, and its text has already drifted in shipped code (`cli.py:118-122` says
  `llmflow init`; `cli_utils.py:568` says `sp init`).
- **D8: `sp doctor`, not `sp init --check`.** *Why:* discoverability is the feature — the failure is
  an error that names nothing, so the user needs a command they can guess.
- **`sp doctor` is NOT blocked on #205.** *Why:* it needed an `add_parser`, a handler and tests.
  The earlier claim was retracted in `d60a4fc` and in the issue body.
- **No aliases anywhere.** Renames are clean breaks that fail loud and name their replacement,
  following the `for`/`in` precedent (*"one syntax, no aliases"*).

---

## Do NOT / deferred

- **Do not push until #199 is merged.** Then push all 21.
- **Do not treat the bodyless HTTP 400 as diagnosed.** Two mechanisms were proposed and **both
  refuted by test.** Missing files exit non-zero and print to stderr — they are loud, not silent.
  `git status --short` returning nothing is a **candidate, not a conclusion**; no 400 has been
  reproduced. #204 now states the cause as unknown. **Do not let a third theory become the story.**
  Settling it needs a real Claude Code session against a clean `HOME`.
- **Do not use `_sp_dir_writable()` on the `~/.sp` root.** It locks its directory on exit
  *unconditionally*, even when it was writable before. Doing so left the whole tree read-only and
  silently broke `install_global_skills()` — that call sits in a `try/except` that only warns. See
  the comment in `install_global_conventions` (`cli_utils.py`).
- **Do not put personal information in `templates/`.** A test fails the build on any email address
  or absolute home path, added after `github-authority.md` was found naming a personal bot account.
- **Do not add a content-drift check to `sp doctor` unasked** — see open decision 4.
- **Looks like a next step but isn't:** building D1-A′ now. It is blocked on decisions 1 and 2, and
  guessing at D4/D5 would be implementing an AI recommendation as though it were a ruling.
- **Do not delete the `jonathanrobie/examples.bsb` fork.** Ruled 2026-08-17: keep it open until
  upstream PR #7 is accepted, because deleting a fork closes its PR. Verified still open. Keep
  `~/github/usfm-bible/examples.bsb` on branch `dev` — it carries the `\id ECC` patch.
- **Do not work Old Testament passages in `sil-translator-notes`** until #203 lands.
- **GitHub's API was intermittently 503-ing on 2026-08-17.** Read results back; do not trust exit
  codes.

---

## Two process failures — read before trusting this file's reasoning

Both nearly cost scope the Captain had not asked to give up, and both were caught by him asking,
not by me checking.

1. **Claimed skill shadowing made the fix unverifiable.** It does not — `env HOME=<tmpdir> claude`
   gives a clean run, and the automated tests never touch skill resolution. He was about to relax a
   design constraint on the strength of it.
2. **Claimed `sp doctor` was blocked on #205.** It never was.

Both times a concern I had just written up was then treated as a constraint — an AI-authored
rationale acquiring the force of a design decision. **The tell: the "blocker" appeared immediately
after I finished documenting something.** Also corrected twice: a jargon-heavy ask with no
information to decide on, and two wrong diagnoses of the 400.

---

## Key files & links

**Design / tracking**
- `project/plans/design-onboarding-fresh-clone.md` — the live design. D1–D8 with the Captain's
  answers inline after each `=>`. Verified fact table with `file:line`; §2.1 the empirical `sp init`
  run; §2.2 the T4 refutation.
- `project/TODO.md` — #204 sits under Workshop readiness as "Doing now".
- `project/RELEASE_CHECKLIST.md` — merge/tag/gate order and failure modes.

**Answer format:** a bare `=>` line. Never checkboxes or blanks. Once the Captain writes after a
`=>`, that text is the ruling — quote it, never reword it. Now shipped in
`templates/sp-conventions/surface-decisions.md`.

**Engine code touched**
- `src/llmflow/doctor.py`, `tests/test_doctor.py`
- `tests/test_skill_command_output.py`, `tests/test_global_conventions.py`
- `src/llmflow/templates/sp-root/` — new; files whose path is part of a contract
- `src/llmflow/cli_utils.py` — `install_global_conventions` root-file block

**Issues** — #204 onboarding · #205 CLI schema · #200 editions · #201 dataset versioning ·
#202 pericope sources · #203 versification · #181 convention drift ·
human-at-the-helm#1 HATH upgrade
**PRs** — nida-institute/LLMFlow#199 (release, green) · usfm-bible/examples.bsb#7 (upstream, open)
**Board** — 13 (LLMFlow Roadmap); HATH#1 at Todo position 1
