# Design — the ai-context layout: three standard files, two halves, one catalog (#210)

**Status:** In progress, 2026-08-25. Eleven rulings recorded from the Captain (§2).
**Q1–Q5 are answered**; **Q6 alone remains open**, and it is blocked on #211 (§7). Steps 2, 5 and
6 are built and tested; steps 1, 3, 4 and 7 are not. Three guards in
`tests/test_ai_context_layout.py` are deliberately red and name what is left.
**Issue:** #210 (the `overview.md` split, which this completes). Blocks #211, which cannot name
a template while document placement is unsettled. Bears on #204, whose acceptance criterion is
that a cloned project runs `/load-context` successfully.
**Author:** AI, from the Captain's rulings in conversation on 2026-08-25 and from measurements
of `docs/ai-context/`, `data/file-catalog.yaml`, `src/llmflow/file_catalog.py`,
`tools/update_ai_context.py` and the shipped `load-context` skill. Every count below was
measured on 2026-08-25 and can be re-measured.

---

## 1. What I understand the goal to be

`eb7c720` split the AI context index by filename prefix; `8d8ac2a` replaced that the same
evening with directories, `sp/` and `project/`. The intent is stated in that commit: *"Ownership
is structural rather than lexical: everything under `sp/` is regenerated, everything under
`project/` is created once and never touched again."*

The restructure moved this repository's eleven context documents into `sp/` wholesale and
created no `project/` directory. So the repository that defines the layout does not yet live
under it, `sp/` holds seven hand-authored documents in a directory that means "regenerated", and
`sp doctor` still cannot be run here.

The goal is to finish it: every document on the side that owns it, one catalog behind the sp
half, a hand-written map on the project half, and `sp doctor` safe in this repository.

---

## 2. Rulings recorded — the Captain, 2026-08-25

Quoted from conversation. These are his, not the author's.

**R1 — the index lists the directory.** *"the index file in each needs to reference all the
files that are needed, typically all files in that directory."*

**R2 — the sp/project split of the seven.** Asked to rule on the author's reading, he answered
*"yes, this is correct"*:

| half | documents |
|---|---|
| project's | `gui-architecture.md`, `data-sources.md`, `paratext-schemas.md`, `data-shapes.md` |
| sp's | `audits-pattern.md`, `json-reliability.md`, `README.md` |

**R3 — a project's map cannot be derived.** *"we cannot know what files a project might want in
advance."* This restates the ruling already recorded above the `project/index.md` catalog entry
from #204 — *"we can't know what files a project has created in advance"* — and is why that path
is `create-once` rather than `derived`.

**R4 — a catalog in Python is wrong.** *"having a separate catalog in a Python code is (1) a
violation of our declarative principles (read your AI context), and (2) a second source of
truth. Seems wrong to me."*

**R5 — the standard set is three.** *"there are a few standard files, especially index.md,
rules.md ... there were 3, I think."* Confirmed: `sp/README.md` names the pinning order
`overview.md`, `index.md`, `rules.md`, and `rules.md` closes *"pin these rules alongside
`overview.md` and `index.md`."* The shipped `load-context` skill reads the same three.

**R6 — this work gets a plan file**, not a GH issue, and not neither.

**R7 — `ENGINE_REFERENCES` is renamed.** Offered a choice between naming what it denotes and
naming the property that makes it a category, he ruled **A**: the term is **Scripture Pipelines
documentation**, the identifier `SP_DOC_LINKS`, the rendered heading
`## Scripture Pipelines documentation`. `project/plans/design-vocabulary.md` governs and is
*"Draft, but in force… authoritative for user-facing text"*: **Scripture Pipelines** is the
product name there, its Names table marks the older one *"Deprecated as a product name"*, and
*engine* is not a ruled term at all — it occurs once in that document, as a section heading. The `ecosystem` row's principle,
*"Vague; replace with what it denotes,"* rules out *references*. The old heading
`## Engine reference, canonical` is rendered into every project's index, so this is user-facing
text and not only an identifier.

**R8 — do not trust docstrings, and prefer deleting them.** *"Don't trust docstrings. See your AI
context."* and *"deleting docstrings is often helpful, they get stale and lead LLMs and people
astray."* `disciplines/design-authority.md` is the governing text: *"Existing code behaviour,
docstrings, AI-generated rationale and prior unreviewed AI choices carry none"* — no design
authority. `disciplines/workflow.md` gives the tell: a design comment must cite a GH issue, and
without one *"future sessions cannot tell whether the comment reflects an intentional decision or
a stale assumption."* An earlier draft of this plan called the `ENGINE_REFERENCES` comment's
premise "true" on the comment's own say-so. §3.4a tests it: it is false. Under R8 that comment is
deleted rather than corrected.

**R9 — one tutorial.** *"For Q4, what we REALLY need to do is have one and only one tutorial, in
the right place."* This is rule 18 (`one-design`) applied, and it subsumes Q4 and Q5: the
duplicate link and the drifted copy are two symptoms of the same thing. It also generalises past
the tutorial — §3.9 finds `audits-pattern.md` already exists as two divergent copies with no
shipping mechanism at all.

**R10 — of the two sp-side documents, only `audits-pattern.md` survives, and it is fixed.**
*"include only audits-pattern.md, fix it. make sure it covers things like /audit-output,
/audit-prompts, and `sp tools replay`."* `json-reliability.md` is deleted: its durable content —
use `response_format` with `json_schema` — is already in `docs/llmflow-language.md` §"Structured
JSON Output", which the deleted file itself linked to as *"full documentation."* Its removal
loses nothing and ends a document whose headline advice was contradicted by three independent
witnesses (§3.11). This revises R2, which had placed both on the sp side.

**R11 — the tutorial link is dropped; the tutorial itself was never the problem.** *"yes, do it"*,
to: drop the Tutorial link from `SP_DOC_LINKS`, the language spec and Python API links stay,
because those are documents sp does not write into a project and linking them is the only way to
reach them.

This closes Q4′ and Q5, and the reason is that **there was never a second tutorial.**
`data/ai-rules.yaml` is the precedent: one source, a rendered copy in every project, and nobody
calls that a duplicate — a copy that is regenerated is not a second design. `docs/tutorial.md` is
built the same way, catalogued `policy: generated` from `TUTORIAL_DOC`, so `sp doctor` repairs it
in any consumer project. **This repository's copy is the one that escaped**, because `sp doctor`
cannot run here (§3.3) — which is the whole of the `output/` against `outputs/` drift, and step 7
regenerates it at no cost. §3.10 settles which text is right: `outputs/`.

What was left was one reader-visible defect, not a design question: the rendered index listed
`docs/tutorial.md` as a file the project has *and* linked the same document on the web, nine
lines apart, with nothing distinguishing them. Dropping the link removes the duplicate name and
leaves the file the project actually has.

---

## 3. Measured state, 2026-08-25

### 3.1 The directories

`docs/ai-context/sp/` holds **11 files**. `docs/ai-context/project/` **does not exist** — zero
files. The catalog declares **8** ai-context paths, four per half.

Of the 11 files in `sp/`, **4 are catalogued** and 7 are not:

| file | catalogued | provenance |
|---|---|---|
| `index.md`, `overview.md`, `rules.md` | yes | `<!-- Generated by tools/update_ai_context.py -->` |
| `github-workflow.md` | yes | hand-authored |
| `audits-pattern.md`, `data-shapes.md`, `data-sources.md`, `gui-architecture.md`, `json-reliability.md`, `paratext-schemas.md`, `README.md` | **no** | hand-authored |

### 3.2 Against R1

`sp/index.md` references **2 of the 11 files in its own directory** — `rules.md` and
`README.md`. Nine are unreferenced, including `overview.md` and `github-workflow.md`, which are
catalogued. Its one row for `rules.md` is labelled `docs/ai-context/rules.md`, the
pre-restructure path.

`project/index.md` references nothing, because neither it nor its directory exists.

### 3.3 Two producers on three paths

`tools/update_ai_context.py` writes `sp/index.md`, `sp/overview.md` and `sp/rules.md`
(lines 16–19). The catalog also claims all three — `index.md` as `source: derived`, the other
two as `source: constant`. Whichever ran last wins.

This is the #210 defect reproduced at the new path. `8d8ac2a` fixed it for `overview.md` by
splitting the document in two; it did not fix it for `index.md` or `rules.md`, and the hazard it
described — *"the catalog can name only one owner per path"* — still holds. It is the live
reason `sp doctor` must not run in this repository.

**`rules.md` is the exception, and it is the precedent.** `data/ai-rules.yaml` holds the rules
and nothing else does: `update_ai_context.py:12` imports `llmflow.ai_rules`, and
`cli_utils.ai_rules_doc()` renders `AI_RULES_DOC` from the same module. The repair is recorded
at `cli_utils.py:975` — it ended the state where *"which rules a project was held to depended on
which generator last ran."* One source, two renderers. That is the shape R4 asks for, already
working in this repository since 2026-08-21.

### 3.4 Four hand-kept document lists in Python — R4's target

| location | what it lists | count |
|---|---|---|
| `tools/update_ai_context.py:22–33` | the index table: topic → path → note | 11 rows |
| `tools/update_ai_context.py:36–43` | the overview's "Foundational Docs" — the same paths, described again | 8 |
| `tools/update_ai_context.py:78–83` | the same paths a third time | 6 |
| `file_catalog.py:ENGINE_REFERENCES` | engine docs appended to every rendered index | 3 |

The first three name **this repository's own documents** — `INSTALL.md`, `docs/tutorial.md`,
`docs/architecture.md`, `docs/python-api.md`, `project/plans/README.md`.

### 3.4a The `ENGINE_REFERENCES` comment is false — tested, not taken on trust

Its comment claims *"They are not catalogued paths — nothing writes them into a project — so they
are listed here rather than derived."* Checked against the catalog on 2026-08-25, link by link:

| link it emits | target | catalogued? |
|---|---|---|
| Pipeline language spec | `docs/llmflow-language.md` | no — but `docs/llmflow-language-quickref.md` **is**, `policy: generated` |
| Tutorial | `docs/tutorial.md` | **yes** — `file-catalog.yaml:179`, `policy: generated`, `source: constant TUTORIAL_DOC` |
| Python API | `docs/python-api.md` | no |

**One of the three is written into every project**, so the premise is false as stated. The
comment cites no issue, has no author and no date, and was believed. R8 applies.

**What a reader of a consumer project actually sees.** Rendering `render_sp_index()` today, nine
lines apart in one file:

```
 24 | `docs/tutorial.md` | Step-by-step walkthrough: variables, saveas, and a two-step pipeline. |
 ...
 33 - [Tutorial](https://github.com/nida-institute/LLMFlow/blob/main/docs/tutorial.md)
```

Line 24 is a file in their repository. Line 33 is a different document on the web. Both are
called the tutorial and nothing distinguishes them. That is #210's defect — one name, two
documents — inside a single generated file.

**And the two tutorials have already diverged.** This repository's `docs/tutorial.md` differs from
`TUTORIAL_DOC` by 44 diff lines (`output/` against `outputs/`), so `sp doctor` run here would
rewrite it. Same class as the `overview.md` hazard #210 was opened for, and step 7 would hit it.

### 3.5 What the catalog rendering drops

`render_sp_index()` (`file_catalog.py:241`) emits two columns, `path` and `purpose`. The
catalog's `policy` field — `generated` vs `create-once`, which is *whether `sp doctor` will
overwrite this file* — is not rendered. A reader in a consumer project cannot tell from
`sp/index.md` which of their files sp owns.

That is the information `nida-institute/discourse-flow` needed on 2026-08-23 and did not have,
when `sp doctor` replaced a hand-authored 26-line map and a 79-line Copilot instruction file
with packaged content. Both were restored on 2026-08-25 from `HEAD`.

`SP_INDEX_HEADER` also tells every reader *"That is `project-index.md`"* — the filename `eb7c720`
introduced and `8d8ac2a` retired the same evening. Every project's rendered index currently
points at a path that does not exist.

### 3.5a Two of the three `policy` values are never read — bears on Q3

Screening for R8 cases found this. `Policy` declares three values, each with a docstring stating
a guarantee:

| value | docstring | read anywhere in `src/`? |
|---|---|---|
| `GENERATED` | *"sp owns the content. Restored when missing or when it has diverged (D10)."* | yes — `file_catalog.py:197`, once |
| `CREATE_ONCE` | *"sp writes it when absent and never touches it again."* | **no** |
| `USER_OWNED` | *"sp never writes it."* | **no** — one entry, `llmflow.log` |

`grep -rn "Policy\." src/llmflow/` returns exactly one line. Nothing reads `policy` by string
either. So create-once behaviour is not enforced from the declaration; it is implemented by
hand-written `if not exists` guards at each write site in `cli_utils.py` (≈1777, 1809, 1817,
1833). Two encodings of one fact — the defect rule 29 names, and the same shape as the
2026-08-23 overwrite, where *"does sp own this file?"* had two encodings that disagreed.

**Consequence for Q3, now ruled *"Yes"*.** Rendering the `policy` column publishes those
guarantees to every consumer project. A column saying `create-once` is a promise that sp will not
touch the file — and today nothing enforces it. So step 6 renders the column *and* makes the
write sites read the policy, or it ships a guarantee the code does not keep. Recorded as part of
step 6 rather than as a new question.

### 3.9 Step 1 is blocked: two sp documents have no source, and one already has two copies

Found while implementing step 1 on 2026-08-25. Cataloguing a document requires a `source:` —
`template`, `constant`, `derived` or `sp-home`. For the two documents R2 leaves on the sp side,
**none of those exists**:

| document | constant in `cli_utils`? | template under `llmflow/templates/`? | in a consumer repo? |
|---|---|---|---|
| `audits-pattern.md` | no | no | **yes** — discourse-flow has one |
| `json-reliability.md` | no | no | no |

So `audits-pattern.md` reached `discourse-flow` by some route that no longer exists. **The two
copies are both 140 lines and they differ** — it was copied once and has drifted since, with
nothing to reconcile them. That is R9's *"one and only one"* problem in a second place, found
because the tutorial ruling sent me looking.

`json-reliability.md` has no copy anywhere and no way to ship, so on the evidence it is this
repository's own document about sp rather than a document sp gives to projects.

**What this needs from the Captain** — it is the same question R9 answers for the tutorial,
asked of these two. Recorded as Q6.

### 3.10 Q5 answered by the codebase — `outputs/` is correct

Looked up rather than asked, at the Captain's direction. Three independent sources agree:

- `cli_utils.py:1661` — `output_dir = base_dir / "outputs"`, what `sp init` actually creates
- the four shipped pipeline templates — `output_dir: "outputs"` at lines 53, 87, 137, 217
- `tests/test_init.py:645` — `test_init_uses_outputs_not_singular_output_decoy`, a test that
  exists specifically to stop the singular

So `TUTORIAL_DOC` is right and **this repository's `docs/tutorial.md` is the drifted copy**. The
one tutorial carries `outputs/`.

### 3.11 The two sp-side documents, assessed for Q6

**`audits-pattern.md` (140 lines).** Describes structure sp really ships — `docs/audits/INDEX.md`,
`audit-passage.md` and `project/audits/README.md` are all catalogued. Two defects:

- it ships a **wrong path** — *"See `nida-institute/Ears-to-Hear` repo (`LLMFlow/docs/audits/`)"*.
  `project/HANDOFF.md` records that repository's root as `scriptorium/`, not `LLMFlow/`, and flags
  the same error elsewhere as not to be promoted. Every project receives this pointer.
- it ships **other projects' examples** — `audit-leadersguide.md`, `audit-MRK-6-14-29.md`,
  `audit-LUK-1-semlex-multipass.md` — which are noise to a project doing something else.

**The two copies differ on one line only**, line 31. This repository's names
`~/.sp/disciplines/project-tracking.md` and `sp-workflow.md`; discourse-flow's names
`~/.sp/conventions/llmflow-project-tracking.md`. Both files exist on this machine, but
`conventions/` is the retired directory. Reconciling means discourse-flow takes this line.

**`json-reliability.md` (319 lines).** The longest document in `sp/`, and it reaches no project.
Its durable content is one paragraph — use `response_format` with `json_schema` — which
`docs/llmflow-language.md` already documents and which this file links to as *"full
documentation."* Around it:

- **its headline model advice is measurably false.** It states *"❌ NOT `gpt-4.1` — uses Responses
  API"*. discourse-flow measured the opposite: *"all four arms ran on `gpt-4.1` with strict
  `json_schema` across 200+ calls and produced zero schema failures. The claim is stale, and
  acting on it would mean changing a model that demonstrably works"*
  (`project/audits/audit-clause-relations.md:79-84`). An assistant following this document
  abandons a working model.
- **a dead link** — `pipelines/semlex-singlepass.yaml` does not exist. Already noted in
  `project/HANDOFF.md`.
- **unsourced figures presented as fact** — *"40-60% failure rate"*, *"$150-200 wasted per
  pipeline run"*.
- **an "AI Assistant Response Template"** scripting what the assistant should say verbatim.
- a dated model string, `gpt-4o-2024-08-06`, which goes stale by construction — R8's failure mode
  at document scale.

### 3.6 The unrendered catalog

`data/file-catalog.yaml` is packaged into the installed engine (`pyproject.toml:65` →
`llmflow/data/file-catalog.yaml`), so it travels with `sp` to every machine. Nothing copies it
into a consumer repository. One source, shipped with the tool, rendered per project — the same
shape as `data/ai-rules.yaml`, and not a second source of truth.

### 3.7 The shipped `load-context` skill

`src/llmflow/templates/sp-skills/load-context/SKILL.md`, byte-identical to the installed
`~/.sp/skills/load-context/SKILL.md`, reads:

- step 3 — `project/index.md`, `sp/index.md`, `index.md`, each with `2>/dev/null`
- step 4 — `sp/rules.md 2>/dev/null || rules.md`, then `docs/ai-context/overview.md`

It never reads `project/rules.md`, `project/overview.md` or `sp/overview.md`. The bare
`cat docs/ai-context/overview.md` carries **no `2>/dev/null`** and no fallback; under the new
layout that path does not exist, so the skill emits a read error — the failure class #204 names:
*"skills must skip a missing file cleanly and never emit an empty read."*

---

## 4. The design

### 4.1 Three standard files per half, everything else a topic document

R5 with R1. The trio is the frame; the index is what makes the rest reachable.

```
docs/ai-context/
  sp/       index.md  overview.md  rules.md      ← generated
            + topic documents: github-workflow, audits-pattern,
                               json-reliability, README

  project/  index.md  overview.md  rules.md      ← create-once
            + topic documents: project, gui-architecture, data-sources,
                               paratext-schemas, data-shapes
```

`8d8ac2a` describes a fourth mirrored slot — *"a map, a self-description, constraints, and the
documents each side carries."* The first three hold. The fourth does not: `github-workflow.md`
is issue references, version numbering and `gh` conventions; `project.md` is *"facts,
conventions and gotchas."* Two different functions in one slot. Both are topic documents, and
under R1 both are reached through their side's index.

**Consequence for the skill.** It reads the trio on both sides — six reads, a fixed set that
never grows. It does *not* enumerate topic documents; a skill that listed them would be a fifth
hand-kept list of exactly the kind R4 rejects. `project.md` went invisible because no index
names it, not because the skill fails to read it.

### 4.2 The sp half is the catalog, rendered

`sp/index.md` is `source: derived` and stays so. Every document in `sp/` gains a catalog entry
with a `purpose:`, which under `documents()` is what puts it in the index —
*"forgetting to index it is impossible — the purpose is the index entry"*
(`file_catalog.py:205`). R1 is then satisfied structurally rather than by discipline.

`tools/update_ai_context.py` loses its index and overview generation and its three document
lists. It keeps the `ai_rules` rendering, which already follows §3.3's precedent.

### 4.3 The project half is hand-written

R3. `project/index.md` is `create-once`, hand-authored, and lists the project's own documents —
in this repository: `INSTALL.md`, `docs/tutorial.md`, `docs/getting-started.md`,
`docs/llmflow-language.md`, `docs/architecture.md`, `docs/why-scripture-pipelines.md`,
`docs/python-api.md`, `docs/moderation-handling.md`, `project/plans/README.md`, and the four
project-half topic documents from R2.

That content exists today as the Python tuples in §3.4. It is not migrated to a YAML — moving it
to a declarative file the engine reads would rebuild the same mistake in a better format, a
generator that can only be right in this one repository. It is written as markdown, by hand,
once, the way every other project writes its own map.

**Hand-authored markdown here is not a second source of truth.** It is the one artifact the
design says must be hand-written. What makes the current code a second source is that it looks
derived and is not.

### 4.4 Acceptance test

`sp doctor` runs in this repository and reports no diff. That is the single check that the
layout, the catalog and the generators agree; it is currently forbidden here, and the
prohibition in `project/HANDOFF.md` can be lifted when it passes.

---

## 5. The work, in order

Each step is testable and none is authorized yet.

1. **Catalog the sp half.** Add `purpose:` entries for `audits-pattern.md`,
   `json-reliability.md`, `README.md`. Test: every file in `docs/ai-context/sp/` has a catalog
   entry, and every catalogued `sp/` path exists — derived from `data/file-catalog.yaml`, so a
   new document cannot be added and forgotten.
2. **Create `project/` and move R2's four documents** into it. Test: no file in
   `docs/ai-context/project/` is `policy: generated`.
3. **Write `project/index.md` by hand**, listing everything in §4.3. Test: every file in each
   ai-context directory is referenced by that directory's `index.md` — R1, enforced.
4. **Retire the two generators** in `tools/update_ai_context.py` and its three lists. Test: no
   path under `docs/ai-context/` has two producers.
5. **Fix the shipped `load-context` skill** to read the trio on both sides, every read guarded.
   Test: the skill names no path outside the six, and every `cat` is guarded.
6. **Rename per R7, and correct the rendering.** `ENGINE_REFERENCES` → `SP_DOC_LINKS`, and the
   heading it emits → `## Scripture Pipelines documentation`. Correct `SP_INDEX_HEADER`'s dead
   `project-index.md` reference. Render the `policy` column into `sp/index.md`. The rename and
   the dead reference are unconditional; the `policy` column is subject to Q3, and where the
   links finally live is subject to Q4. Test: no user-facing string rendered into a project
   names the product anything other than **Scripture Pipelines**.
7. **Run `sp doctor` here.** §4.4.

Steps 1–3 are independent of 4–6 and can land first.

---

## 6. Open questions

Answer on the `=>` line. Nothing in §5 is built before Q1–Q3 are answered.

**Q1 — do the four project-half documents keep their names and content unchanged in the move?**
`gui-architecture.md`, `data-sources.md`, `paratext-schemas.md`, `data-shapes.md` are yours.
A move is `git mv` and nothing else unless you want otherwise; `CLAUDE.md` cites
`gui-architecture.md` by name and would need its path updated either way.

=> yes, git mv

**Q2 — `README.md` in `sp/`: keep, or fold into `sp/overview.md`?** R2 placed it on the sp side.
It is the "AI Context Bundle" document, and its content is the pinning order from R5 plus a
maintenance checklist that names `overview.md`, `index.md` and `rules.md` — three files whose
generation this plan changes. Keeping it means a fourth sp document to catalog; folding it means
its maintenance checklist moves into a generated file.

=> Fold it in

**Q3 — should `sp/index.md` render the `policy` column?** §3.5. It costs one column and tells
every consumer which of their files sp will overwrite — the fact discourse-flow lacked. Against:
it exposes an sp-internal vocabulary (`generated`, `create-once`) to readers who have not asked
for it, and `sp doctor` reports the same thing on demand.

=>  Yes

**Q4 — the three Scripture Pipelines documentation links: what happens to them?** R7 settled the
name. §3.4a establishes the facts: one of the three links duplicates a file sp writes into the
project, under the same document name, in the same rendered file. R8 deletes the comment either
way. Three options, each shown as the text a consumer project's `sp/index.md` would end with.

**Option 1 — keep all three links; rename only.**

```
## Scripture Pipelines documentation

- [Pipeline language spec](…/docs/llmflow-language.md)
- [Tutorial](…/docs/tutorial.md)
- [Python API](…/docs/python-api.md) — …
```

*Cost:* nothing beyond the rename. *What it leaves:* line 24 of the same file still says
`docs/tutorial.md` is in their repository, and a reader cannot tell the two tutorials apart. The
list stays hand-kept in Python, which is what R4 objects to.

**Option 2 — delete the constant; link only what sp does not write.**

```
## Scripture Pipelines documentation

- [Pipeline language spec](…/docs/llmflow-language.md)
- [Python API](…/docs/python-api.md) — …
```

*Cost:* a reader who wants the upstream tutorial has no link; they get the copy in their own
repository instead, which is the one their `sp` version matches. *What it fixes:* the duplicate
name is gone. Still a hand-kept list, now of two.

**Option 3 — catalog all three; delete the constant entirely.** The links become rows in the
same table as every other document, and the section disappears:

```
| `docs/llmflow-language.md` (upstream) | The full pipeline language specification. |
| `docs/python-api.md` (upstream)       | Drive the engine in-process from Python. |
```

*Cost:* the catalog is keyed by a path in the project, and these have none — so it needs a new
field to hold a URL and a `policy` or `scope` value meaning "linked, never written". That is new
machinery for three rows. *What it fixes:* R4 fully — one declaration, nothing hand-kept — and it
forces the tutorial collision into the open, because the catalog cannot hold two rows for one
path.

**Superseded by R9, and closed by R11.** None of the three options above delivers one tutorial;
all keep two and differ only on whether both are named. R11 records the ruling and why the
question dissolved — the tutorial is one source with regenerated copies, and only the redundant
link needed removing. Kept here as the record of what was considered.

**Q4′ — where does the one tutorial live? — ANSWERED by R11.** The premise was wrong: it already
lives in one place, `TUTORIAL_DOC`, and every copy is derived from it. The two options below were
drafted before that was checked, and are kept as the record.

- **In each project.** Keep `TUTORIAL_DOC` and the catalog row; `sp init` writes
  `docs/tutorial.md` into every project, including this one, so this repository stops having its
  own. Drop the Tutorial link from `SP_DOC_LINKS`, because it would point at a copy. *Cost:* this
  repository's `docs/tutorial.md` is overwritten by the constant, so the `output/` vs `outputs/`
  difference must be resolved first — see Q5.
- **In Scripture Pipelines only.** Delete `TUTORIAL_DOC` and its catalog row; no project gets a
  `docs/tutorial.md`; the `SP_DOC_LINKS` Tutorial link is the only route. *Cost:* a project
  working offline, or pinned to an older `sp`, reads a tutorial that may not match its version.

=>  I don't understand.  One tutorial, indexed from index.md.  Where is the difficulty?

**Q5 — `docs/tutorial.md` has the `overview.md` problem. Which text is right? — ANSWERED.** The
Captain directed that the codebase be consulted rather than asked; §3.10 records the result,
`outputs/`, on three independent witnesses. Now measured, so this was never a decision. `TUTORIAL_DOC` is what sp writes into a project; this
repository's `docs/tutorial.md` is the same 92-line document, drifted by 44 diff lines. The whole
difference is one word: the constant says generated content goes in **`outputs/`**, the file on
disk says **`output/`**.

Whichever is wrong, `sp doctor` run here silently replaces the file with the constant, so the
question must be settled before step 7. Two sub-questions, and only you can answer the first:

- **which directory name is correct** for what `sp init` creates — `outputs/` or `output/`?
- once that is known, does this repository keep its own `docs/tutorial.md` at all, or read the
  shipped one like any other project? Keeping it means one path with two owners, which is the
  defect #210 exists to remove.

=>  Surely your codebase and our record answers this question definitively, no?  Look it up or test it.

**Q6 — `audits-pattern.md` and `json-reliability.md`: what is their source?** §3.9. Step 1 cannot
catalog a document without one, so this blocks steps 1 and 3. R9 applied to each:

- **`audits-pattern.md`** already exists twice and the copies differ. Either it ships — which
  needs a template or constant that does not exist today, and the two copies reconciled — or it
  is this repository's own, and discourse-flow's copy becomes theirs to keep.
- **`json-reliability.md`** has no copy anywhere and no way to ship. On the evidence it is this
  repository's own document, which would move it to the project half, revising R2.

=> Reconcile audits-pattern.md.  And let's discuss - how useful are these two documents for LLMs working with sp on projects?

---

## 7. What this does not cover

- **#211**, moving 21 shipped documents from Python constants to `source: template`. Distinct
  from R4: #211 is about where a document's *content* lives, this plan is about where the *list*
  lives.
  **Correction, 2026-08-25 — and then a correction to the correction.** This plan first said #211
  was unblocked by step 3; a later revision said the reverse, that step 1 was blocked on #211
  because no project-scoped path could be template-sourced. **The second was also wrong.** Verified
  by construction: `shipped_path` and `shipped_content` match on `source`, never on `scope`, and
  `entries()` has always passed `template` through for plain files. The capability exists and is
  simply unused. **Step 1 is blocked on neither.** Recorded in
  `project/plans/design-shipping-the-audit-method.md` §4, which carries the measurement.
- **The flat-layout migration in consumer repositories.** `discourse-flow` and `ears-to-hear`
  carry the pre-restructure flat `docs/ai-context/*.md`. Those files are no longer catalogued,
  so `sp doctor` will neither refresh nor remove them. The content is authored, so nothing
  automates the move and nothing should. Recorded in `project/HANDOFF.md`.
- **`~/.sp/skills/`.** The installed copy is the Captain's store; a reinstall is his act.
- **The vocabulary entry for R7.** *Scripture Pipelines documentation* — the documents that live
  in the Scripture Pipelines repository and are linked rather than installed — is a concept
  `design-vocabulary.md` does not yet carry, and that document's own instruction is *"if a needed
  concept is missing, propose an addition rather than coining a term."* The proposed row is
  offered here; placing it is the Captain's, and this plan does not write to it.
