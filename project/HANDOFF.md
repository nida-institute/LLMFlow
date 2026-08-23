# HANDOFF — 2026-08-23

Supersedes the 2026-08-22 handoff.

---

## ▶ NEXT ACTION

**1. Commit two files.** `project/plans/design-scripture-representations.md` (§4.3 the JSON
representation, §4.4 the `include` members, §4.5 what `include` does not carry) and this file.
Rule 27 makes the commit the Captain's; gates green — `hatch run pytest
tests/test_plan_docs_index.py` → 67 passed, 13 skipped.

**2. `format: usj` is now implementable.** Shape, payload, container, member names and text
authority are all ruled. Start from the parked `wip/scripture-200` work — but read §4.4's open
`=>` first: the Greek/Hebrew asymmetry is a *proposal*, not a ruling. It is implementable as
written (source column names, unnormalised, documented per edition); if the Captain wants a
normalised shape instead, the payload changes and code written now is wrong.

**3. The documentation is part of the work, not after it** — see thread 2. He said twice that this
must reach the AI environment, most recently of the member names specifically.

**Verify before trusting this file:**

```bash
git -C . log --oneline -3                         # c7aa0d2, a725932, 505c257
git -C . rev-list --left-right --count origin/dev...dev   # 0  2  — unpushed
git -C . status --short                           # design-scripture-representations.md only
grep -c '^=>' project/plans/design-scripture-representations.md   # 4, all still empty
hatch run pytest tests/test_plan_docs_index.py tests/test_catalog_covers_init.py -q
```

---

## Active threads

### 1. Scripture representations (#200) — design settled except the member names

**Ruled and recorded** in `project/plans/design-scripture-representations.md` §7:

| | |
|---|---|
| shape | `format: milestones \| plain \| usj` |
| payload | `include: [...]` — a **list**, valid only with `format: usj` |
| USJ for TSV editions | **synthesised** from the TSV: verses and text, no structure |
| spec attributes | `srcloc`, `lemma`, `strong` stay in their spec places |
| everything else | one container per word, **`scripture_pipelines`** |
| text authority | **Macula Greek rules**, even where SBLGNT (LogosBible) has a variant |
| editions | Nestle1904 out of scope; HOT is BHS and WLC |

**Member names ruled (§4.4): families, not columns** — `ids`, `morphology`, `senses`, `glosses`,
`referents`. `morphology` straddles both homes deliberately: `lemma` and `strong` are spec
attributes and go where the spec puts them, the parse goes in the container, and a caller asking
for `morphology` gets both. `glosses` is separate from `senses` because a Louw-Nida domain, an SDBH
sense and an English gloss are not interchangeable.

**One open `=>` in §4.4: the Greek/Hebrew asymmetry.** `include: [senses]` yields `{domain, ln}` on
SBLGNT and `{lexdomain, contextualdomain, coredomain, sdbh, sensenumber}` on WLC. The proposal
recorded there is that the member name stays stable while the fields keep the source's own column
names, unnormalised — because normalising means inventing an equivalence that does not exist, and
rule 25 puts that in his domain. **Implementable as proposed; a normalising ruling would change the
payload.**

**Also open, none of which blocks:** Q2 apparatus step type · Q3 default when unspecified · Q4
paragraph source. `syntax` and `paragraphs` do not fit `include` at all — USJ has nowhere to put a
constituency tree — so they are probably a different `format:`, which is what #200's table implied.

**Verify:** `sed -n '/^### 4.3/,/^## 5/p' project/plans/design-scripture-representations.md`.

### 2. The documentation requirement — stated twice, and part of the work

The Captain, 2026-08-23, of the JSON representation and again of the member names: this **needs
adequate documentation in the AI context**. A design document is a record, not a delivery channel —
nothing an assistant reads at session start points at `project/plans/`. When `type: scripture`
ships, its section in `docs/llmflow-language.md` must carry:

- the cost table — milestone form is +7% over bare text; the USJ container is **4.26x** before any
  metadata; word ids **5.67x**; one repo's annotations **11.78x** (measured on all of Mark)
- the choosing test — *if the model's output must reference individual words, the input must carry
  word identity*
- the `scripture_pipelines` container, and that spec attributes stay in their spec places
- the constraint that the milestone form is **derived from** USJ, never produced independently
- the Lowfat ordering failure mode (§6.1)
- the five `include` members and what each yields per edition, including the asymmetry

Written to whatever standard #208 sets, because scripture will be the first section written to it.
Cross-cutting parts belong in `data/ai-rules.yaml`, the only channel that reaches every project
automatically.

**Blocked on:** the step existing, and #208's standard. Not startable yet.

### 3. Pipeline-language guidance (#208) — filed, nothing built, evidence accumulating

Four open questions in the issue. Since filing, **three more instances arrived unprompted**, all
from discourse-flow sessions: the `gpt-4.1` gate, the fenced prompt template, and `sp doctor` not
refreshing the quickref. All three fixed; none recorded in #208 yet.

### 4. `~/.sp` is derived — the lesson from today, not yet written down anywhere durable

A hand-edit to `~/.sp/disciplines/llmflow-prompt-organization.md` was **silently reverted** by
`sp doctor` restoring the packaged copy. The `gpt-4.1` fix survived the same run **because the
package had been fixed too**. Same store, same run, no error either way.

**So: a fix belongs in `src/llmflow/templates/`. `~/.sp/disciplines/` and `~/.sp/skills/` record
what arrived, not what was decided.** `~/.claude/CLAUDE.md`'s `~/.sp` section explains the
versioning and the lock but never says most of the store is generated. Worth a line there — the
Captain's file, so propose, don't write.

**Verify:** `git --git-dir=$HOME/.sp-git --work-tree=$HOME/.sp log --oneline -1` → `c662291`,
whose message records the experiment.

### 5. `~/.claude` memory stores — 81 files deleted, triage done, nothing carried out

Deleted deliberately by the Captain: unreviewed AI artifacts, invisible in any repository, loaded
into every session ahead of the documents that carry authority. **Still uncommitted** — 81 ` D`
entries — and readable from `8678309` indefinitely.

`project/plans/plan-memory-recovery.md` preserves the 22 items worth keeping from the 39 audited,
each with a proposed destination. **None has been carried out.** One item was promoted before that
document existed: `feedback_dev_branch` → rule 28.

42 files across ten projects remain unaudited.

### 6. Done today, no follow-up needed

- **`sp doctor` could not refresh the quickref** (#204). Four files `sp init` writes were absent
  from `data/file-catalog.yaml`; `managed_by_doctor()` returns only catalogued entries, so
  `c1647af`'s cursor fix could not reach a project. Fixed in `a725932`, with
  `tests/test_catalog_covers_init.py` closing the class. **Eight further files sit in that test's
  `AWAITING_CATALOG_RULING` set** — the four hello-world examples and four audit documents, all
  `generated` at their write sites. They need one ruling: `generated` means `sp init --update`
  rewrites a user's edited example pipeline.
- **`gpt-4.1` is not incompatible with structured outputs.** Corrected in four places including
  the packaged skill. `docs/ai-context/json-reliability.md:254` still carries it — that directory
  needs per-file approval.
- **The prompt template forbade fences and fenced its own example.** Fixed in the package
  (`c7aa0d2`) after the store fix was reverted.

---

## In flight

**LLMFlow `dev`:** `c7aa0d2`, **two commits ahead of `origin/dev` and unpushed.** One file
uncommitted: `project/plans/design-scripture-representations.md`.

**`~/.sp`:** clean, committed at `c662291`.

**`~/.claude`:** 81 deletions pending, deliberately.

---

## Decisions settled — do not reopen

- **Two knobs, `format:` and `include:`.** *Why:* the measurement says payload dominates container
  — 4.26x for the container before any metadata, 11.78x with one repo's annotations. The dimension
  worth controlling separately is the payload. Invalid pairings (`milestones` + ids) are rejected
  by the `allOf`/`if` pattern `pipeline_schema.py` already uses per step type.
- **`include` over `carry`.** The Captain: *"context disambiguates it from, say, an include file."*
  Rejected: `with` (reads as step arguments to anyone from GitHub Actions), `layers` (means
  analytical layers in discourse-flow), `detail`/`level` (a scalar ladder that stops working once
  senses and syntax are independently selectable).
- **One container, `scripture_pipelines`, underscored.** *Why a container:* strippable in one
  operation, and never mistakable for spec content. *Why underscores:* `get_from_context` matches
  each dotted part against `^([a-zA-Z0-9_]+)` (`utils/context.py:148`), so a space or hyphen
  returns a **sentinel object rather than raising** — the natural `${w.scripture pipelines.morph}`
  fails silently.
- **Macula Greek's text rules** even against a LogosBible variant. The apparatus is information
  *about* the text, never a competing text to use.
- **Rule 28 names `dev` explicitly.** A first draft declined to name a branch; he overruled it
  because a default that names nothing tells an agent nothing when a project declares nothing.
- **`project/TODO.md` is `create-once` in the catalog**, not `generated` — its write site has no
  `--update` branch and rule 20 makes it a file people edit. Marking it `generated` would have had
  `doctor` overwrite it.

---

## Do NOT / deferred

- **Do not commit or push.** Rules 27 and 28. Two commits are unpushed; that is his call.
- **Do not run the full test suite casually** — #207, it writes to the real `~/.sp/`.
- **Do not hand-edit `~/.sp/disciplines/` or `~/.sp/skills/`.** Derived; `sp doctor` reverts it.
  Fix `src/llmflow/templates/` instead. See thread 4.
- **Do not run `sp doctor` from this repository** — it reverts `docs/ai-context/*` to the packaged
  constants, which would undo rule 28. Run it from a consumer repo or a scratch directory.
- **Do not restore the deleted memory files, and do not commit `~/.claude`.**
- **Do not write a memory file.**
- **Do not promote anything from `plan-memory-recovery.md`** without a per-item ruling.
- **Do not fill in a `=>`.** Four remain empty in the scripture design document; Q1's ruling is
  recorded *beneath* its slot, per the discipline.
- **Do not edit `docs/ai-context/`** — including `json-reliability.md:254`, which still carries
  the stale `gpt-4.1` claim and needs his word for that file specifically.
- **The machine user cannot read project boards, and has `pull` only** — it can create issues and
  edit its own, never one the Captain authored.
- **`gh` identity collision, unresolved.** His own `gh` config and the agent config present the
  same token fingerprint, so his terminal authenticates as the bot. Diagnostic:
  `env -u GH_CONFIG_DIR gh api /user --jq '.login'`.
- **Looks like a next step but isn't:** a lint check for the Lowfat ordering trap. Evidence
  supports it; he has not asked; he declined to choose an option for the analogous rules 23/24
  guard.

---

## Key files & links

**Design** — `project/plans/design-scripture-representations.md` (§2 the serialisations, §3 the
alignment spine, §4 what reaches the model, **§4.3 the JSON representation**, §6 traps, §7 rulings,
§8 four open questions) · `plan-memory-recovery.md` · `design-scripture-editions.md`, which still
exists **only** on the local tag `wip/scripture-200`

**Measured facts, so they are not re-derived** — Lowfat departs from document order in ~40% of
Mark's verses (334 transitions, 268 verses) · `sort`/`uniq` under a UTF-8 locale merge
`⸀ ⸂ ⸁`, needing `LC_ALL=C` · USJ costs 4.26x a milestone string before metadata, 11.78x as
discourse-flow ships it · `tei` is referenced by zero files across the three consumer repos · only
four `.xq` files exist across them · `srcloc`/`lemma`/`strong` are spec attributes
(`usfm.ext:1325`, `usx.rnc:965`); the USJ schema declares `additionalProperties` nowhere

**Issues** — #200 (epic) · #208 (guidance) · #163 (conventions, commented) · #204 · #38 vs #52
(BaseX naming, in conflict) · #201 · #203 · #207

**External** — `discourse-flow/project/plans/per-verse-representation-defect-design.md` (453 lines,
14 ratified decisions) · `discourse-flow/plugins/milestone_content.py` (builds USJ from Macula with
`srcloc`) · `usfm-bible/tcdocs` (the TC source; **not** BridgeConn's copy)
