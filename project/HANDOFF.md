# HANDOFF — 2026-08-22

Supersedes the 2026-08-21 handoff. Its two open items are resolved: `dev` is pushed and level
with `origin/dev`, and HATH step 7 is untouched but no longer blocking.

---

## ▶ NEXT ACTION — commit three files, then get the ruling on Q1; build nothing until then

**Most of today is committed and pushed: `505c257` on `dev`, 10 files, 750 insertions.** Three
files remain uncommitted — see "In flight" below.

Two things, and neither is code.

**First, commit the three uncommitted files** — rule 28, the regenerated `docs/ai-context/rules.md`,
and this file. Guard is green. Rule 27 makes the commit the Captain's.

**Then the ruling that unblocks work: Q1 in
`project/plans/design-scripture-representations.md` §8 — one knob or two — gates the `format: usj`
work**, and Q2 and Q4 gate the apparatus and paragraph questions behind it. Until Q1 is answered,
`type: scripture` cannot be extended without guessing at the schema.

**Also awaiting him, not blocking code:** where `project_ears_to_hear_structure` should live, his
own reading of `feedback_call_your_own_drift`, and whether to audit the remaining 70 memory files
— see thread 6.

Do not start implementing. The parked code on `wip/scripture-200` is not authorization either —
see Do NOT.

**Verify before trusting this file:**

```bash
git -C . log --oneline -1                    # 505c257
git -C . status --short --branch             # clean, level with origin/dev
grep -c '^=>' project/plans/design-scripture-representations.md   # 4, all empty
hatch run pytest tests/test_ai_rules_single_source.py tests/test_plan_docs_index.py -q
```

The last is 66 passed, 13 skipped. The full suite has **not** been run — #207.

## Active threads

### 1. Scripture representations — design document written, four questions open

- **Goal:** #200, rewritten today as the epic. Serve named editions in several representations,
  query Lowfat in BaseX, and settle what reaches a model.
- **State:** `project/plans/design-scripture-representations.md` (265 lines, committed in
  `505c257`). Sources, precedence and representation shape are ruled; the schema shape is open.
- **Next step:** the Captain answers the four `=>` slots in §8. **Q1 gates implementation.**
- **Verify:** `gh issue view 200 --repo nida-institute/LLMFlow --json title` → title has no
  leading space and begins `Epic: scripture editions`. `grep -c '^=>' project/plans/design-scripture-representations.md` → 4.

### 2. Pipeline-language guidance — #208 created, nothing built

- **Goal:** one source for the language reference; step sections that state semantics and failure
  modes; examples checked for meaning, not spelling.
- **State:** issue created today, no work started. Four open questions recorded in it.
- **Verify:** `gh issue view 208 --repo nida-institute/LLMFlow --json number,state`.

### 3. Plan-document index — landed, with a known defect

- **State:** `tools/update_plans_index.py`, generated `project/plans/README.md`,
  `tests/test_plan_docs_index.py`, and a `Design & plan documents` row in
  `tools/update_ai_context.py`. All committed in `505c257`.
- **Known defect, recorded in #163:** the index's Issues column is a **mention scrape**, not a
  declaration — a document that merely cross-references an issue looks like that issue's design.
  `design-scripture-representations.md` names #38, #52, #201, #203, #208 while being the design
  for #200 alone. Proposed fix (needs his approval, because it means adding a line to 25
  documents he wrote): each document declares `Issue: #200` beside its status, and the generator
  reads the declaration.
- **Verify:** `hatch run python tools/update_plans_index.py --check` → exits 0.
  `hatch run pytest tests/test_plan_docs_index.py -q` → 64 passed, 13 skipped.

### 4. Commit authority — rule 27 landed; the louder voice still contradicts it

- **State:** rule 27 is in `data/ai-rules.yaml`, renders as #27 in both renderers, and is in the
  regenerated `docs/ai-context/rules.md`.
- **Outstanding and consequential:** `~/.sp/skills/commit-ready/` still tells every session in
  every repo on this machine that the agent commits, pushes, merges and deletes branches
  (its Gate 5, 6 and 7). `~/.sp` is `dr-xr-xr-x`, locked by `_lock_sp_dir()`. **Only the Captain
  unlocks it** — the procedure is in `~/.claude/CLAUDE.md` under "Restoring a store".
- **Verify:** `grep -c "commit, the push and the merge" docs/ai-context/rules.md` → 1.
  `ls -ld ~/.sp` → `dr-xr-xr-x`.

### 5. Parked, untouched today

`#203` versification · `#200`'s parked code on the **local** tag `wip/scripture-200`
(`05d75a5`, `34c7931`) — still not on `dev`, and `project/plans/design-scripture-editions.md`
still exists **only there** · `#201` dataset versions · `#204`'s last piece (`_is_generated` by
marker string rather than `data/file-catalog.yaml`) · `#192` · `#33` · `#207`.


### 6. `~/.claude` memory stores — 81 files deleted on purpose, triage part-done

- **State:** the Captain deleted every `~/.claude/projects/*/memory/` file — **81 across 12
  projects** — deliberately, because they were unreviewed AI artifacts loaded into every session's
  context ahead of the documents that do carry authority, invisible to him in any repository.
  **Not committed:** the store shows 81 ` D` entries. Recoverable from `8678309` indefinitely,
  since git keeps the blobs even after the deletion is committed.
- **Audit done for this repo's 11.** Seven were second copies of authored sources (rule 14,
  `disciplines/surface-decisions.md`, `design-vocabulary.md`, `consumer-repo-conventions.md`,
  `docs/getting-started.md:85-99`, `RELEASE_CHECKLIST.md`). **One contradicted the record:**
  `project_ai_github_account` told sessions to set `GH_CONFIG_DIR=~/.sp/gh-ai-config`; the actual
  value is `/Users/jonathan/.config/gh-agent` and the `~/.sp` variant is superseded. Three held
  something real.
- **Of those three:** `feedback_dev_branch` is promoted — it is now **rule 28**.
  `project_ears_to_hear_structure` (ears-to-hear's project root is its `LLMFlow/` subdirectory;
  do not blanket-exclude `/LLMFlow/` when working across repos) **has no home decided**.
  `feedback_call_your_own_drift` awaits the Captain's own reading — its trigger is his question,
  its countable threshold ("twice on the same class, or three times on anything") is the AI's, and
  an AI arguing for a rule that governs it is the circular-authority shape.
- **discourse-flow's 28 audited, none promoted.** Far richer than this repo's, because
  LLMFlow's rules absorbed its memories over time and discourse-flow's never did. Six duplicate
  authored sources (`branch_workflow` is now rule 28; `git_commands`, `design_authority`,
  `test_runner`, `pyproject_toml`, and `plan_vs_design` — which cites
  `~/.sp/conventions/llmflow-project-tracking.md`, a path that no longer exists). **Fourteen are
  domain or project knowledge with no home anywhere**, including: Levinsohn signals mark openings
  not closings — which is *why* windowing drops the last pericope, and whose own text complains it
  "has been explained to LLMs at least 3 times"; verses-as-milestones-never-arrays with the
  specific schema rulings; the discourse-vs-narrative repo boundary; `tradition_comparison` as the
  single designated freelancing zone; board **17** with its field IDs and the note that `Next Up`
  *is* the TODO column; Hebrew `ref` non-injectivity at ~50% of words. **Five are workflow
  constraints stricter than the shared rules** — prompt edits shown as a diff and approved before
  applying; no pipeline commit until it runs clean on a book (Philemon); never italicise anything
  that could hold Hebrew; `/tmp` not authorized, use `./tmp`; never implement windowing in Python.
  Three overlap partially with specifics the shared version lacks.
- **Two of them conflict with how this session behaved**, both discourse-flow-scoped:
  `feedback_no_recommending` forbids recommending design choices, and this session recommended
  throughout (the Captain asked for advice directly); `feedback_filesystem_access` says `/tmp` is
  not authorized, while this session wrote to `/private/tmp/claude-501/...` per its own
  configuration. Neither is resolved.
- **Not audited:** 46 files across ten other projects.
- **The mechanism is unfixed.** This repository's `CLAUDE.md` requires approval before writing a
  memory file; the machine-wide default does not, which is how twelve projects accumulated 81.
  Emptying the store does not stop sessions refilling it.
- **Verify:** `cgit status --short | grep -c "^ D"` → 81.
  `cgit show 8678309:projects/<project>/memory/<file>.md` reads any of them without restoring.

---

### 7. Two reports from discourse-flow's AI, both about shipped guidance being wrong

- **Reported 2026-08-22 by discourse-flow's AI session:** the `audit-prompts` skill flags
  `gpt-4.1` as incompatible with strict `json_schema`. Contradicted by evidence — four arms, 200+
  calls on `gpt-4.1` with strict `json_schema`, zero schema failures. It asked that the skill be
  corrected rather than the pipeline.
- **This repository's own rules already agree with the report.** `docs/ai-context/rules.md` rule 5
  says `response_format` is OpenAI-only, "**GPT-4o/4.1 families**".
- **Three places contradict rule 5:** `~/.sp/skills/audit-prompts/SKILL.md:565,584,634,702` ·
  `docs/llmflow-language.md:254` ("Must use `gpt-4o-2024-08-06` or later (not `gpt-4.1` — uses
  different API)") · `docs/ai-context/json-reliability.md:19,26`. Two of those sit inside
  `docs/ai-context/` contradicting each other.
- **Nothing changed.** The wording that replaces it should name what actually gates structured
  outputs rather than swapping one model list for another, so OpenAI's capability table wants
  checking first. The skill is in the locked `~/.sp` store and is the Captain's.
- **This is a fifth instance of #208's thesis**, arriving unprompted from another repository hours
  after the issue was filed. **Not yet added to #208.**
- **Verify:** `grep -rn "not .gpt-4.1" docs/` → 1 hit in `llmflow-language.md`.
  `grep -n "GPT-4o/4.1" docs/ai-context/rules.md` → rule 5.

**7b. The prompt template forbids markdown fences and then fences its own example.**
`~/.sp/disciplines/llmflow-prompt-organization.md` §8: line 128 of the template says "Output a
single valid JSON object. No markdown fences, no commentary before or after"; lines 131-135 show
the schema example inside a ```json fence. A prompt built by copying the template reproduces the
fence — which is the "one code fence inside OUTPUT SCHEMA in each prompt" the audit skill then
flags. The standard causes the finding.

- Line 142 carries a disclaimer, and it does not resolve it: it says where the *instruction*
  should sit, never that the fence should be dropped, and it sits after the template rather than
  beside it. Prompt text, template and checklist disagree three ways.
- **Severity is low and the reason matters:** with `strict: true` the shape is enforced at the API
  boundary, so a fenced example costs no parse failures. The cost is false audit findings on every
  prompt, indefinitely.
- Both the standard and the skill are in the locked `~/.sp` store — the Captain's.
- **Verify:** `sed -n '124,142p' ~/.sp/disciplines/llmflow-prompt-organization.md`.
- **Not recorded in any issue.** Same class as #208 — shipped guidance that is itself the defect —
  but a different document in a different store.

---

## In flight / not committed

**Three files, uncommitted** — `data/ai-rules.yaml` (rule 28), the regenerated
`docs/ai-context/rules.md`, and this file. `dev` is otherwise level with `origin/dev` at
`505c257`. The guard `tests/test_ai_rules_single_source.py` passes (2 passed), so the source and
the generated file agree. The commit is the Captain's — rule 27, and a drafted message is at
`tmp/commit-msg.txt` (untracked; delete after use).

What that commit contains: rule 27 in `data/ai-rules.yaml` and the regenerated
`docs/ai-context/{rules,index}.md` · `tools/update_plans_index.py` and the generated
`project/plans/README.md` · `tests/test_plan_docs_index.py` · the topic-map row in
`tools/update_ai_context.py` · `project/plans/design-scripture-representations.md` · CHANGELOG
entries under `## Unreleased` · an earlier revision of this file.

**GitHub, done 2026-08-22:** #208 created · #200 retitled and its body replaced · #163 commented
(`issuecomment-5381015360`).

**Two design pointers still missing.** #200's only `project/plans/` mention is the parked-work
line about `design-scripture-editions.md`; the pointer to the current design document is absent.
#169 has none. Both need a manual edit — the machine user has `pull` only and cannot edit an
issue the Captain authored.

## Decisions settled today — do not reopen

- **Nestle1904 out of scope.** Present in `macula-greek` alongside SBLGNT; not wanted.
- **HOT is BHS and WLC** — minimal diffs, the only two in widespread use.
- **Macula Greek's text rules**, even where SBLGNT (LogosBible) carries a variant reading. The
  apparatus is information *about* the text, never a competing text to use. *Why it matters:* an
  LLM handed both could treat a variant as an alternative reading to adopt.
- **`format: usj` for TSV editions is synthesised from the TSV** — verses and text, no structure.
  Ruled after being shown that `LogosBible/SBLGNT` has real paragraphs the TSV lacks.
- **Both representations, produced per pipeline according to need.**
- **Documents stay in the repo and the issue links to them, plus a generated index** (B + D).
  *Why not paste documents into issue bodies:* two independently maintained texts for one
  subject, the failure `b75da26` fixed for the AI rules and #208 exists for in the language
  reference. #200's own body was carrying a duplicated survey and a superseded TEI decision
  until today.
- **Rule 28: work on a single `dev` branch**, feature branches only when asked, `main` for what
  is released — with an explicit clause that a project may declare a different workflow and that
  decision governs locally. *Why the branch is named:* a first draft declined to name one, to avoid
  imposing this repository's convention; the Captain overruled it because a default that names
  nothing tells an agent nothing when a project declares nothing.
- **Memory files are not a place for guidance.** Unreviewed, invisible in the repositories, and
  loaded ahead of authored documents. What survives goes where it can be reviewed:
  `data/ai-rules.yaml`, `project/plans/`, `~/.sp/disciplines/`, `~/.sp/user-context/`.
- **The convention work is tracked in #163**, not a new issue.
- **`llmflow.md` deepening is its own epic (#208)**, not folded into #200.

**Naming, corrected by the Captain:** *edition* (SBLGNT, WLC, BHS, BSB), *source repository*
(`Clear-Bible/macula-greek`, `LogosBible/SBLGNT`), *serialisation* (`tsv`, `lowfat`, `tei`, USFM).
Collapsing these into labels like "Macula" or "Logos" is what he corrected — `macula-greek` holds
two editions, so "Macula" is not an edition. Use "SBLGNT (macula-greek)" and "SBLGNT (LogosBible)".

---

## Do NOT / deferred

- **Do not commit or push.** Rule 27. Draft the message, hand over the command.
- **Do not restore the deleted memory files, and do not commit `~/.claude`.** The deletion was
  deliberate. Triage is per-file and the Captain's; `~/.claude/CLAUDE.md` says a dirty store is
  reported with the diff, never committed by an agent.
- **Do not write a memory file.** Not for this session's findings either.
- **Do not promote any discourse-flow memory** — 28 were read and classified, none was moved. The
  ruling is the Captain's, per file.
- **Do not reword the `gpt-4.1` guidance before checking OpenAI's capability table.** Four
  locations disagree; changing three of them from memory would replace one stale claim with
  another.
- **Do not run the full test suite casually.** #207 — it writes to the real `~/.sp/`. Today's work
  is verified by targeted runs only.
- **Do not unlock `~/.sp`.** The `commit-ready` fix is his procedure, not an agent's.
- **Do not build against design-document Q1** (one knob or two) until it is answered. Same for
  Q2 (apparatus step type) and Q4 (paragraph source).
- **Do not add `Issue: #N` lines to the 25 plan documents** unasked — proposed, not approved.
- **Do not trust the plans index's Issues column** as a design relationship; see thread 3.
- **The machine user cannot read project boards.** Confirmed exhausted today: the fine-grained
  PAT reaches all 33 org repos but `organization.projectV2` is FORBIDDEN for every one of the 19
  boards. `project/TODO.md`'s board annotations are the only bridge, and nothing verifies them.
  Ask the Captain for column state rather than inferring it.
- **The machine user has `pull` only** — `{"admin":false,"maintain":false,"pull":true,"push":false,"triage":false}`.
  It can create issues and edit its own; **it cannot edit an issue the Captain authored.** Write
  is the minimum role for that, and Write also permits pushing, so granting it for an issue edit
  is a bad trade.
- **`gh` identity collision, unresolved.** The Captain's own `gh` config and the agent config
  present **the same token fingerprint** (`github_pat_11CMGLR2A0LfXLCQL1QrHk_`), so his terminal
  authenticates as the bot and hits the same refusals. Diagnostic:
  `env -u GH_CONFIG_DIR gh api /user --jq '.login'`. Fix is his: `env -u GH_CONFIG_DIR gh auth login`,
  browser rather than a pasted token.
- **`sp doctor` is still dangerous in this repo** — it would revert `docs/ai-context/*` to the
  packaged constants, including today's regeneration.
- **`#205` was closed during this session**, by someone other than this session. HANDOFF-2026-08-21
  listed it as parked with six questions awaiting the Captain. State change noted, cause unknown.
- **Looks like a next step but isn't:** a lint check for the Lowfat ordering trap. The evidence
  supports it (§6.1 of the design document), the Captain has not asked for it, and he declined to
  choose an option for the analogous rules 23/24 guard.

---

## Key files & links

**New today** — `project/plans/design-scripture-representations.md` ·
`tools/update_plans_index.py` · `tests/test_plan_docs_index.py` · `project/plans/README.md`

**Measured facts worth not re-deriving** (all in the design document with commands):
Lowfat departs from document order in ~40% of Mark's verses (334 transitions, 268 verses);
`sort`/`uniq` under a UTF-8 locale merge `⸀ ⸂ ⸁` and need `LC_ALL=C`; USJ costs 4.26× a milestone
string before any metadata and 11.78× as discourse-flow ships it; `tei` is referenced by zero
files across the three consumer repos; only four `.xq` files exist across them.

**Issues** — #200 (epic, rewritten) · #208 (new epic) · #163 (convention, commented) · #159
(overlaps #163, untouched) · #38 vs #52 (BaseX naming, in conflict) · #201 · #203 · #204 · #207

**External** — `discourse-flow/project/plans/per-verse-representation-defect-design.md` (453 lines,
14 ratified decisions, the prior art) · `discourse-flow/plugins/milestone_content.py` (builds USJ
from Macula morphology with `srcloc`) · `discourse-flow#75`, `#26`, `#43`

**Board** — 13 (LLMFlow Roadmap), unreadable by any AI session on this machine.
