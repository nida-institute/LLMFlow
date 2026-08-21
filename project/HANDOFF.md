# HANDOFF — 2026-08-21

Supersedes the 2026-08-20 handoff entirely. Its NEXT ACTION — HATH step 6 — is done and pushed.

---

## ▶ NEXT ACTION — ask the Captain whether to narrow the bot's GitHub token

The machine user account `jonathanrobie-ai-agent` was built today and works. One decision was
left with him and nothing else is blocked on anything:

**Its fine-grained PAT reaches all 33 repos in `nida-institute`, not the four intended** — it was
generated with *All repositories*. It is read-only (`push: false` verified on four repos), so
nothing can be changed, but every private repo in the org is readable by any session. Narrowing
it is an edit to the token's *Repository access* in the bot's browser; it may re-enter pending
approval, and it needs no re-login and no new credential file.

**Verify before raising it:**

```bash
GH_CONFIG_DIR=~/.config/gh-agent gh api user -q .login          # jonathanrobie-ai-agent
GH_CONFIG_DIR=~/.config/gh-agent gh api user/repos --paginate -q '.[].full_name' | wc -l   # 33
GH_CONFIG_DIR=~/.config/gh-agent gh api repos/nida-institute/LLMFlow -q .permissions.push   # false
```

`GH_CONFIG_DIR` and `GIT_AUTHOR_*`/`GIT_COMMITTER_*` are in `~/.claude/settings.json`, and they
were **already in effect for shells spawned after the settings were written** — not only from
the next session, as first assumed. So **plain `gh` is the bot**, with org-read-only reach: `gh`
calls that worked as the Captain (org admin endpoints, `biblica/*`) now 404. And **a plain
`git commit` is authored `Claude (AI agent)`** — this file's commit is the first in LLMFlow to
carry that author. The Captain's own terminal is unaffected.

Everything else below is either finished or explicitly parked.

---

## Active threads

### 1. LLMFlow `dev` — **ahead of `origin/dev` and unpushed. Today's work is `137f69b..HEAD`.**

- **Goal:** the release the Captain has not yet declared complete.
- **State:** working tree clean. Today's four:

| | |
|---|---|
| `137f69b` | permissions: 67 accumulated allows → 20 reviewed; `ask` on push and PR-merge |
| `5fe1904` | HATH step 6 — sync record, script, guard; `design-authority` unified; `=>` prohibition; identity rewrite |
| `c1647af` | window: cursor example fixed, `size`/`stride` resolve once, `window_num` taught to lint |
| `b75da26` | one source for the AI rules, and 26 of them |

- **Next step:** nothing until the Captain says the release contents are complete.
- **Verify:** `git log --oneline 8979a59..HEAD` — everything after `8979a59` is this session.
  `gh pr view 199 --repo nida-institute/LLMFlow --json headRefOid` → `cb72cb7`, which contains
  none of it.
- **CHANGELOG** has an `## Unreleased` section with the heading deliberately unset, per the
  convention in `ee28721`, so it can be folded into 0.2.1.24 or retargeted.

### 2. human-at-the-helm#1 — **steps 1–6 done and pushed. Step 7 is the Captain's.**

- **State:** `main` level with `origin/main` at `f064d55`; six commits public.
- **Remaining:** step 7 — a real Claude Code session in a plain project running `/load-context`.
  Ruled C: run it here and record what it cannot prove (see Decisions).
- **`ai-accounts.md` corrected and pushed** (`f064d55`): the file claimed
  `~/.claude/settings.json` "is never committed to any repository" and told adopters to put the
  bot's `GH_TOKEN` there — a conflict with versioning `~/.claude`, which this methodology now
  encourages. The path now goes in settings and the credential goes in its own `GH_CONFIG_DIR`.
- **Verify:** `git -C ~/github/nida-institute/human-at-the-helm log --oneline -1` → `f064d55`,
  tree clean, level with `origin/main`. `hatch run pytest tests/test_hath_sync.py` → 70 passed.

### 3. The machine user account — **built; two follow-ups, both the Captain's.**

- **State:** `jonathanrobie-ai-agent`, org member, 2FA via Google Authenticator on his phone,
  fine-grained PAT approved under the org policy, credentials in `~/.config/gh-agent`.
  `~/.claude/settings.json` carries `GH_CONFIG_DIR` plus `GIT_AUTHOR_*`/`GIT_COMMITTER_*`.
- **Follow-ups:** narrow the token (NEXT ACTION); decide whether the bot ever gets
  `Contents: write`, without which **it cannot open pull requests** — creating one needs a
  pushed branch. Issues and PR comments work.
- **Verify:** `cat ~/.claude/settings.json` — `env` has five variables; `deny` has `sudo rm` and
  three `gh-agent` read rules.

### 4. `#204` fresh-clone onboarding — **one piece left, unchanged today.**

`_is_generated` call sites still decide ownership by marker string rather than by
`data/file-catalog.yaml`. **Verify:** `hatch run pytest tests/test_catalog.py tests/test_doctor.py`.

### 5. Parked, untouched today

`#205` CLI schema discipline (six questions await the Captain) · `#200` editions ·
`#203` versification · `#192` implement `else` · `#33` missing project files ·
`#207` the suite writes to the real `~/.sp/`.

---

## In flight / not committed

- **LLMFlow: clean.** All four commits above are in; nothing staged or dirty.
- **HATH: clean and pushed** through `f064d55`.
- **discourse-flow: `collab/` is untracked** and three files are modified
  (`pipelines/experiments/clause-relations-windowed.yaml`,
  `plugins/check_prompt_compliance.py`, `tests/test_check_prompt_compliance.py`).
  **None of that is ours** — it predates this session except the appended reply and addendum in
  `collab/sp/windowing-semantics-gap.md`, which is where the engine-side answers to their report
  live. Do not commit that repo without the Captain.
- **`~/.sp` and `~/.claude` are both clean**, bare repos at `~/.sp-git` / `~/.claude-git`,
  aliases `spgit` / `cgit`. Four commits there are authored `Claude (AI agent)`; earlier ones
  are authored as the Captain but were in fact the AI's — `~/.claude/CLAUDE.md` says so.

---

## Decisions settled today — do not reopen

- **26 AI rules, one source.** `data/ai-rules.yaml` is the only place they are written; both
  generators render from it. *Why:* two generators held two independently maintained texts (17
  vs a different 12), so which rules a project was held to depended on which ran last, and
  `sp doctor` would silently swap one for the other.
- **Rules 25 and 26 are the Captain's**, split at his instruction, trimmed twice. Rule 26 read
  *"sole understanding is decision authority, whoever types the approval"* until he flagged that
  it "seems to invite freelancing" — a description that a loose reading turns into a grant. His
  reasoning is quoted in `plan-ai-rules-single-source.md` §6; the rules no longer restate it.
- **`size`/`stride` resolve once at step entry** — not per iteration, and not literal-only.
  *Why:* his argument (the partition must be computable at loop start) rules out mid-loop
  change but, as he said himself, "doesn't reach variables that can be resolved before the
  'loop' begins". Lint warns it cannot verify a variable's value.
- **`window_num` taught to the linter** (D2-A). He said "let's finish both of these now" without
  naming A or B; the plan records that the AI took its recommendation as the instruction.
- **Only the Captain writes after a `=>`** — except with explicit authorization in the current
  conversation. Now in `surface-decisions.md`, both repos.
- **Identity: `env` in `settings.json`, not per-repo config.** *Why:* git cannot tell who ran
  `git commit`, so any repo-default mislabels one party. `env` reaches only Claude Code's own
  shells. Per-repo config and an `include.path` slot were both built and removed.
- **`github-authority.md` identity in three levels** — a git author is a string, not a login;
  a paid seat, org role or extra AI-tool account is never required. *Why:* the Captain does not
  have the right to create accounts, and "Others may have the same problem."

**One open `=>`** — `plan-window-semantics.md` §4 D1 has an empty slot with the ruling recorded
*beneath* it, per the new discipline. Do not fill it in.

---

## Do NOT / deferred

- **Do not push LLMFlow.** The single push waits on the Captain declaring the release complete;
  pushing retargets PR #199 and restarts a ~2h Windows build.
- **Do not merge PR #199.** It contains none of this work.
- **Do not commit discourse-flow or the HATH `ai-accounts.md` draft** without him.
- **Do not run the full test suite casually.** `#207` — the suite writes to the real `~/.sp/`.
  This is now *recoverable* (`~/.sp` is versioned; `spgit restore .` after
  `chmod -R u+w ~/.sp`), but it is still an unreviewed write to his machine. It has **not** been
  run today; today's work is verified by targeted runs only.
- **Do not put a secret in `~/.sp/user-context/` or `~/.claude/settings.json`.** Both are
  versioned now. The 2FA secret is deliberately absent — a session can read those files, and
  secret-plus-password is full account control.
- **Do not fill in a `=>`.** New discipline, this session.
- **`sp doctor` is still dangerous in this repo** — it would revert `docs/ai-context/*` to the
  packaged constants. Run it from a scratch directory if you want `~/.sp` refreshed. The
  converged-frames fix (making this repo's context genuinely what the package ships) is
  designed but unstarted; its precondition — `~/.sp` versioned — is now met.
- **Looks like a next step but isn't:** the side-write / use-the-language guard over
  `plugins/*.py`. Rules 23 and 24 exist and nothing checks them; the Captain chose neither
  option A (an `audit-code` checklist plus AST script) nor B (a `sp lint` pass). Do not build
  either unasked.
- **`window.py:334-346`** builds the static `windows` list even in dynamic mode and discards it.
  Harmless; tidying it is its own change.
- **`ruff`:** `window.py` has one pre-existing I001. `cli_utils.py` sits at its HEAD baseline of
  22. Sweeping either would bury correctness changes.

---

## Key files & links

**Plans** — `project/plans/plan-ai-rules-single-source.md` (complete; §6 the 26 rules, §9 the
two new ones) · `plan-window-semantics.md` (complete; §5 what was left alone) ·
`design-hath-parity.md` (H7 step 6, H8 step 7's limits) · `design-onboarding-fresh-clone.md` (#204)

**New this session** — `data/ai-rules.yaml` · `data/hath-sync.yaml` · `src/llmflow/ai_rules.py` ·
`tools/sync_hath.py` · `tests/test_{hath_sync,ai_rules_single_source,window_cursor_guidance,window_literal_fields,window_lint_context}.py`
· `.claude/settings.json` (committed on purpose; `settings.local.json` still ignored)

**Machine stores** — `~/.claude/CLAUDE.md` (how the stores are versioned, who may write) ·
`~/.sp/user-context/github-authority.md` (the account as built; `#143` superseded in three places)

**External thread** — `~/github/nida-institute/discourse-flow/collab/sp/windowing-semantics-gap.md`
— their report, our verification reply, and the addendum recording both rulings.

**Issues** — human-at-the-helm#1 · #204 · #205 · #207 · #200 · #201 · #203 · #192 · #33 ·
**#143 is open and superseded** (username, email alias, and a gh config dir inside `~/.sp`).

**PRs** — nida-institute/LLMFlow#199 (release, OPEN, head `cb72cb7`).

**Board** — 13 (LLMFlow Roadmap).
