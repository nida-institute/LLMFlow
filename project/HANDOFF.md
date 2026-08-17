# HANDOFF — 2026-08-17

Supersedes the 2026-08-12 handoff entirely.

---

## ⚠️ THIS FILE IS UNCOMMITTED — ON PURPOSE

`dev` sits on `cb72cb7`, the SHA whose three platform builds are green (including a 2h23m
Windows build). **Committing anything to `dev` retargets PR #199 and starts a fresh build.** Do
not commit this file until after the merge. It is also parked at the tag
`wip/handoff-2026-08-17` (`055799d`) in case the working tree is reset again.

---

## ▶ NEXT ACTION

**Merge PR #199 and tag it. Release 0.2.1.24 is ready; its build is green.**

`dev` was reset to `cb72cb7` on 2026-08-17 so the release could merge *without* the scripture
work — the Captain wanted the current version shipped before the next is implemented.

**Per RELEASE_CHECKLIST:** confirm the fast test jobs are green (the three platform builds were
reused, not re-run) → merge with a **merge commit**, not squash or rebase, so `release.yml` can
resolve `HEAD^2` → **tag the merge commit**, deleting any stale tag of that name first → approve
the `pypi` environment gate, which is a manual GitHub approval, not PyPI.

**Verify:** `gh pr view 199 --jq .headRefOid --json headRefOid` starts `cb72cb7`;
`gh pr checks 199` shows three `Build on *` rows reading `pass`.

### Immediately after the merge

**The scripture work (#200) is NOT on `dev`.** It is preserved at the **local** tag
`wip/scripture-200` (`0bb1d5b`):

```bash
git log --oneline cb72cb7..wip/scripture-200      # 05d75a5, 34c7931, 0bb1d5b
git cherry-pick 05d75a5 34c7931                  # onto dev after the merge
```

`05d75a5` is `utils/scripture.py` + tests; `34c7931` is the step, schema branch, editions registry
and apparatus fix; `0bb1d5b` is only `project/TODO.md`. **Both tags are local — push them or
re-apply the commits before anything could garbage-collect them.**

### Also for the next release: onboarding is broken for everyone but the author — #204

**Wanted in the next build (Captain, 2026-08-17).** A new contributor cloned
`sil-translator-notes`, ran `sp init`, ran `/load-context`, and got **HTTP 400 with no body**.

**Cause:** the skill reads `CLAUDE.md` first. That file is line 1 of the `.gitignore`, is never
committed (`git ls-files CLAUDE.md` → nothing), and **`sp init` does not create it**. So a fresh
clone cannot have it, and a missing file yields an empty read, which the API rejects with a
bodyless 400. Every consumer repo appeared to work only because its author had a local,
uncommitted copy — **no collaborator has ever had a working `/load-context`.**

**Workaround already shipped** for `sil-translator-notes`: `CLAUDE.md.template` committed as
`95955d9`, so the contributor runs `cp CLAUDE.md.template CLAUDE.md`. That is a patch on one repo,
not the fix.

**The engine fix (#204) has four parts:** `sp init` scaffolds `CLAUDE.md` and never overwrites it;
skills skip a missing file cleanly instead of emitting an empty read; a verification command
(`sp doctor` / `sp init --check`); and a decision on how a mentor ships customised AI context,
since `sp init` currently regenerates `index.md`, `overview.md`, `rules.md` and
`github-workflow.md`, protecting only `project.md` (`cli_utils.py:1891`).

**And the reason it survived — also in #204.** Nothing tests a clean machine. **2620 tests pass
and not one would have caught this**, because the author's machine already has `CLAUDE.md`, skills
in `~/.claude/skills/`, registered editions and cloned Macula. A test must start from a clone with
an empty `HOME`. Most of it is reachable already: `install_global_skills(sp_home=...)`,
`_install_claude_skills(claude_home=..., sp_home=...)` and `default_editions_dir()` (honours
`SP_HOME`) all take overrides. Only the edition-resolution assertions need data — a dozen-row
fixture TSV committed to the repo would cover them, and would also let `sp lint`'s unhelpful "no
text found" error path be tested.

The wider principle worth writing down somewhere durable: **anything whose correctness depends on
machine state the author already has needs a test that does not have it.** Otherwise the first
person to find the bug is always the newcomer, and the error they see has nothing to do with the
cause — this contributor saw an API 400 and had no reason to suspect a missing markdown file.

### Then: the AI-context task the Captain asked for

**The Captain's request, 2026-08-17:** make the AI ask him what he knows before speculating about
domain matters. He is the expert; a previous instance repeatedly inferred instead of asking. Four
instances from that session:

| The assistant did | The Captain said | Cost |
|---|---|---|
| Estimated "about a day" to reconstruct running text from per-word rows | *"straight concatenation, using the @after attribute"* | The hard problem did not exist |
| Analysed a TEI whitespace "dialect trap" | The TSV carries `after` as a column | Solved a problem the right source does not have |
| Searched GitHub and proposed UGNT/UHB as text sources | *"UGNT is garbage"* | Nearly built on a rejected text |
| Named `usfm-bible/examples.bsb` as *the* BSB source | *"DO NOT PICK NEW RELIABLE RESOURCES FOR ME"* | It is now in a public list on the assistant's judgement |

Speculation did not stay in conversation: it reached issues, a design doc, an awesome-list commit,
and an effort estimate he nearly acted on.

**Proposed rule, for the Captain to review and place — do not write it unilaterally.** The
governing principle is his, verbatim (2026-08-17):

> **Assume any Captain understands his/her data better than you do.**

It is a default, not a checklist item. What follows is how to act on it:

> Before writing code that reads an unfamiliar data format, estimating how hard something will be,
> or naming a source as authoritative — **ask**. These are the Captain's domain: which edition or
> corpus is authoritative; what a format actually contains and how practitioners read it; whether a
> resource is good quality; domain conventions (versification, book codes, milestones); and whether
> an existing internal resource already solves it.
>
> **Report what you found; do not rank it.** "Three candidates, with licence, format and maintainer"
> is useful. "X is the source" is a decision taken.
>
> The asymmetry: asking costs one message; speculating costs an artifact that looks authoritative
> and is wrong.

The **effort-estimate trigger** is the earliest warning: the moment an estimate is being written,
a decision to solve it alone has already been taken.

Candidate homes, the Captain's choice: `~/.sp/conventions/` (applies to every `sp` project),
`~/.sp/drift-patterns.md` (it is a drift pattern — *speculation displacing the expert*), or
`CLAUDE.md`. He suggested `conventions/` for the rule and `drift-patterns.md` for the diagnosis.
**Both are Captain-owned; propose, do not write.**

This is a Captain's decision. The facts:

- `dev` is **19 commits** ahead of `origin/main`, head `0bb1d5b`, everything pushed.
- `pyproject.toml` says `0.2.1.24`; `CHANGELOG.md` line 3 says `## 0.2.1.24 — 2026-08-16`.
- That section documents **four fixes** (#189, #195, #196/#197, #178). It does **not** mention
  the three scripture commits (`05d75a5`, `34c7931`) or the debug-manifest work — grep
  `CHANGELOG.md` for "scripture": one incidental hit.
- So the branch carries more than the CHANGELOG claims. Shipping as-is publishes an
  undocumented feature.

Two ways out:

1. **Ship it all as 0.2.1.24** — add the scripture entries under the existing dated section.
2. **Split** — add a fresh `## Unreleased` above line 3, bump `pyproject.toml` to `0.2.1.25`,
   and move the scripture entries there.

**Verify before acting:** `git log --oneline origin/main..dev | wc -l` → 19;
`grep -n "^## " CHANGELOG.md | head -2` → `0.2.1.24` then `0.2.1.23`, i.e. no `Unreleased`.

---

## Active threads

### 1. Release PR #199 (dev → main) — **in flight, CI running**

- **Goal:** ship the release.
- **State:** PR head is `0bb1d5b` (same as `dev` — every push retargeted it). Build **succeeded**
  on `7767db9` and `cb72cb7`; it is **in progress** on `0bb1d5b`. Tests pending on that SHA.
- **Next step:** the decision above, then wait for green on the final head.
- **Verify:** `gh pr checks 199 --repo nida-institute/LLMFlow` and
  `gh run list --repo nida-institute/LLMFlow --workflow=build.yml --limit 3`.
- **Merge discipline (RELEASE_CHECKLIST):** merge commit, **not** squash or rebase, so
  `release.yml` can resolve `HEAD^2`; tag **the merge commit**; the `pypi` environment gate needs
  manual GitHub approval.

### 2. Scripture editions — #200 — **core done, wiring incomplete**

- **Goal:** the engine serves named editions so consumer repos stop each building their own
  loader (measured: 118 files across three repos).
- **State:** `utils/scripture.py` and `steps/scripture.py` built and tested. **2620 tests pass.**
  Verified against real data in Hebrew, Greek and English. Three editions registered in
  `~/.sp/editions/{WLC,SBLGNT,BSB}.yaml`.
- **Next step:** the **pericope reader** and **docs** (`docs/llmflow-language.md`,
  `docs/architecture.md`) — neither started. Design: `project/plans/design-scripture-editions.md`.
- **Verify:** `hatch run pytest tests/test_scripture_text.py tests/test_scripture_step.py` → 34
  pass; `grep -c scripture docs/llmflow-language.md` → 0, i.e. undocumented.

### 3. Versification — #203 — **blocker, not started**

- **Goal:** a reference must mean the same verse in every edition.
- **State:** confirmed broken. `PSA 51:1` returns the superscription from WLC and *"Have mercy on
  me, O God"* from BSB — two verses apart. `MAL 4:1` does not exist in the Hebrew. **The run
  reports success.**
- **Next step:** map schemes using the Copenhagen Alliance specification (cloned at
  `~/github/copenhagen-alliance/versification-specification`). Editions must declare their scheme;
  `type: scripture` must map before fetching.
- **Verify:** run the two references through `run_scripture_step` for WLC and BSB and compare.
- **This blocks Old Testament use of `sil-translator-notes`.** Top of `project/TODO.md`.

### 4. `sil-translator-notes` (Paul's repo) — **usable, three gaps deliberate**

- **State:** created private in the org, pushed, `aa73408`. `sp lint` passes. Issues #1–#4 filed
  and on project board 19 in "Thinking about…".
- **Next step:** Paul's, not ours. #4 carries Terry Wardlaw's real scope and may want splitting.
- **Verify:** `gh issue list --repo nida-institute/sil-translator-notes`.

---

## In flight / not yet done

| Item | State |
|---|---|
| PR #199 | head `0bb1d5b`, build in progress |
| `usfm-bible/examples.bsb` **PR #7** | open upstream; adds the missing `\id` to Ecclesiastes, closes their #4 |
| Pericope reader, `type: scripture` docs | not started (#200) |
| Versification | not started (#203) |

**Nothing is uncommitted.** `dev` clean, 0 unpushed. `sil-translator-notes` clean, 0 unpushed.
`awesome-biblical-data` clean (`4b6f739`).

---

## Decisions settled this session — do not reopen

- **Text sources are the Captain's.** WLC and SBLGNT from the Macula **TSVs** (`text` + `after`);
  BSB from `usfm-bible/examples.bsb` (USFM). **UGNT and UHB were rejected.** An assistant must not
  substitute a source it judges better — this was stated twice, after I twice proposed sources
  unasked.
- **TSV, not TEI or lowfat**, for WLC/SBLGNT: the TEI carries no `@after`, so joining would need
  whitespace inference with different rules per language. The TSVs make joining *data*.
- **Chunk on pericopes, not chapters.** A chapter silently under-covers: the prompt scans 19
  mostly clause-level categories, the model returns what fits its output budget, and nothing says
  what it skipped.
- **`discourse-flow` pericopes are authoritative** (11 books); BSB `\s1` headings are the interim
  fallback (66 books). They differ — John: 84 vs 69. Record which was used (#202).
- **Join on the three-letter book code. Book numbers are not authoritative** (BSB has MAT=41,
  discourse-flow has MAT=40).
- **Directory is `outputs/` (plural); step keyword is `output:` (singular).** The migration plan
  said the opposite and was marked SUPERSEDED.
- **The debug clean stays**, scoped to one run directory. The run-key segment is emitted even when
  it is `default`, so the `rmtree` can never reach a parent holding sibling runs.
- **A single `dev` branch, no feature branches.** Renaming a branch with a live cross-fork PR
  **closes that PR** — it happened; #6 died and #7 replaced it.

## Open decisions blocking progress

1. The release split — see NEXT ACTION.
2. **#200 overlaps five existing issues** — #38 (BaseX collections), #39/#172 (Scripture Burrito),
   #40 (Paratext 9.x XML), #41 (LXX). The Captain ruled **today's work closes none of them**, but
   whether #200 supersedes any of them, or should merely cross-reference, is unresolved. I filed
   #200 without checking for prior art.
3. `~/.sp/editions/*.yaml` were seeded with **absolute paths on this machine**. Fine here, wrong
   for anyone else. How editions get registered per machine is undecided.
4. `usfm-bible/examples.bsb` has **no licence file**. BSB text is freely usable; the repo's terms
   are unconfirmed, and the engine now depends on it.

---

## Do NOT / deferred

- **Do not delete the `jonathanrobie/examples.bsb` fork while PR #7 is open** — a fork PR depends
  on the fork's branch, so deleting it closes the PR. Command and reasoning in `project/TODO.md`.
- **Do not reset `~/github/usfm-bible/examples.bsb` off its `dev` branch.** That branch carries the
  `\id ECC` patch. Without it Ecclesiastes silently vanishes and `ECC 3:1` returns "no text found",
  which reads like a bad reference. Verify: `git -C ~/github/usfm-bible/examples.bsb branch --show-current` → `dev`.
- **Do not work on Old Testament passages in `sil-translator-notes`** until #203 lands.
- **`discourse-flow` and `discourse-flow-hebrew` have their own AI.** Left out of the `outputs/`
  migration on purpose; both still declare `output/intermediate` and a singular `${output_dir}`.
- **`semdom-greek-lexicon`: leave alone** (Captain's instruction). It declares an Obsidian vault
  root, not a directory named `output`.
- **Looks like a next step but isn't:** adding a surrounding-chapter context step to Paul's
  pipeline. Deriving "the chapter containing this passage" needs an engine helper that does not
  exist; a step re-fetching `${passage}` would just duplicate `fetch_bsb`. Left out rather than
  faked — see the comment where step 3 would go.
- **GitHub's API was intermittently 503-ing all session.** It caused me to report two issue edits
  that never applied. **Read results back; do not trust exit codes.**

---

## Key files & links

**Design / tracking**
- `project/plans/design-scripture-editions.md` — the live design; every ruling recorded
- `project/TODO.md` — #203 at the top, plus the fork-deletion note
- `project/plans/plan-migrate-pipeline-directories.md` — executed; survey of all 14 repos at the foot

**Engine code**
- `src/llmflow/utils/scripture.py` — extraction, editions registry, both backends
- `src/llmflow/steps/scripture.py` — the step
- `src/llmflow/utils/schema_preflight.py` — strict-schema checking (#196), dated rule table
- `src/llmflow/utils/debug.py` — per-run isolation and `manifest.jsonl` (#198)

**Issues** — #200 editions · #201 dataset versioning · #202 pericope sources · #203 versification
**PRs** — nida-institute/LLMFlow#199 (release) · usfm-bible/examples.bsb#7 (upstream `\id` fix)
**Boards** — LLMFlow: project 13 · `sil-translator-notes`: project 19
