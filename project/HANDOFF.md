# HANDOFF — 2026-08-22

Supersedes the 2026-08-21 handoff. Its two open items are resolved: `dev` was pushed (it is
level with `origin/dev` at `f5bb40a`), and HATH step 7 is untouched but no longer blocking.

---

## ▶ NEXT ACTION — hand the Captain a commit, then stop

Nine files are uncommitted on `dev`. **Rule 27, added today, makes the commit his** — an agent
runs the gates, drafts the message, hands over the command, and does not run `git commit`.

The gates: `hatch run pytest tests/test_ai_rules_single_source.py tests/test_plan_docs_index.py`
→ **66 passed, 13 skipped**. The full suite has *not* been run — see #207 under Do NOT.
CHANGELOG is **not** updated; that is the one gate outstanding.

Drafted message, for him to use or edit:

```
feat: design-document index, and the commit is the human's (#163)

`project/plans/` held 25 documents, all declaring a status and none indexed, and
`docs/ai-context/index.md` did not mention the directory — so an assistant following
the topic map never learned they existed. Generated index, plus a test that every
document declares a parseable status and names an issue.

Separately: nothing `sp init` installed said who may commit. The five shipped context
documents and the 26 rules contained no mention of `git commit`, `git push` or
`git merge` — absent text, not wrong text — leaving the machine-wide `commit-ready`
skill, whose gates have the agent committing and merging, as the only voice a session
in a client project heard. Rule 27 now says the commit, push and merge are the human's.

Refs #163, #200, #208
```

Then: **do not start building anything.** Q1 in the new design document (one knob or two)
gates the `format: usj` work, and it is unanswered.

---

## Active threads

### 1. Scripture representations — design document written, four questions open

- **Goal:** #200, rewritten today as the epic. Serve named editions in several representations,
  query Lowfat in BaseX, and settle what reaches a model.
- **State:** `project/plans/design-scripture-representations.md` (265 lines, **untracked**).
  Sources, precedence and representation shape are ruled; the schema shape is open.
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
  `tools/update_ai_context.py`. All untracked or unstaged.
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

---

## In flight / not committed

Branch `dev`, level with `origin/dev` at `f5bb40a`. Nine changes, nothing staged:

```
 M data/ai-rules.yaml                              rule 27, id commit-authority
 M docs/ai-context/index.md                        regenerated — plans row
 M docs/ai-context/rules.md                        regenerated — rule 27
 M tools/update_ai_context.py                      the topic-map row
?? project/plans/README.md                         generated index, 25 documents
?? project/plans/design-scripture-representations.md
?? tests/test_plan_docs_index.py
?? tools/update_plans_index.py
?? tmp/issue-200-epic.md                           leftover; safe to delete
```

`tmp/issue-200-epic.md` was the paste source for #200's body, which is now applied. Deleting it
is the documented cleanup; `tmp/.gitignore` covers only `*.pyc`, `__pycache__/` and `*.log`, so
Markdown there shows as untracked.

**GitHub, done today:** #208 created · #200 retitled and its body replaced · #163 commented
(`issuecomment-5381015360`).

**Two design pointers still missing.** #200's only `project/plans/` mention is the parked-work
line about `design-scripture-editions.md`; the pointer to the current design document is absent.
#169 has none. Text to paste is in the #163 thread and in the session log.

---

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
- **The convention work is tracked in #163**, not a new issue.
- **`llmflow.md` deepening is its own epic (#208)**, not folded into #200.

**Naming, corrected by the Captain:** *edition* (SBLGNT, WLC, BHS, BSB), *source repository*
(`Clear-Bible/macula-greek`, `LogosBible/SBLGNT`), *serialisation* (`tsv`, `lowfat`, `tei`, USFM).
Collapsing these into labels like "Macula" or "Logos" is what he corrected — `macula-greek` holds
two editions, so "Macula" is not an edition. Use "SBLGNT (macula-greek)" and "SBLGNT (LogosBible)".

---

## Do NOT / deferred

- **Do not commit or push.** Rule 27. Draft the message, hand over the command.
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
