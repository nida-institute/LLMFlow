# Plan: Recovering What Was Worth Keeping From `~/.claude` Memory

**Status:** transfer record. **The audit is complete as of 2026-08-24 — all 81 files across 12
projects have been read**, the 39 on 2026-08-22 and the remaining 42 on 2026-08-24 (§ "The
remaining 42"). The memory files are **deleted and uncommitted** in `~/.claude`; every one is
readable from `8678309` with `cgit show 8678309:projects/<project>/memory/<file>.md`. The
deletions are deliberately left uncommitted so that "this is unfinished" stays visible at every
session start. **Most destinations are still proposals**; what has been carried out is listed
under "Already carried out". Issue: #163.

## Why the files were deleted

The Captain deleted all 81 memory files across 12 projects on 2026-08-22. They were AI-written,
unreviewed, invisible in any repository, and loaded into every session's context ahead of the
documents that do carry design authority. `disciplines/design-authority.md` is explicit that
AI-generated artifacts have none. His question — *"I have no idea whether they agree with or
conflict with the design files I HAVE seen"* — had no answer anywhere, which was the problem.

**39 of the 81 were audited** (this repository's 11, discourse-flow's 28). **42 across ten other
projects were not.**

## What the audit found

| | Scripture Pipelines (11) | discourse-flow (28) |
|---|---|---|
| duplicated an authored source | 7 | 6 |
| contradicted the authored record | 1 | 0 |
| index file | 1 | 1 |
| carried something with no home | 2 | 21 |

Scripture Pipelines's memories were mostly duplicates because its rules absorbed them over time.
discourse-flow's never were absorbed, so its memories hold most of the real content.

**The one contradiction:** `project_ai_github_account` told sessions to set
`GH_CONFIG_DIR=~/.sp/gh-ai-config`. The actual value is `/Users/jonathan/.config/gh-agent`, and the
`~/.sp` variant is superseded in `~/.claude/CLAUDE.md`. An invisible file was sending sessions to
the wrong credential store.

## Already carried out

- **`feedback_dev_branch`** → **rule 28** in `data/ai-rules.yaml`, generalised with the
  project-override clause the Captain specified (2026-08-22).

Carried out 2026-08-24, each on the Captain's explicit ruling:

- **"Do not name customers or speculate about stakeholders"** (macula-greek
  `feedback_no_customer_speculation`) → **rule 30** `no-stakeholder-speculation`, with his words
  quoted in its `note:`.
- **"Verify actual state after an interrupted action"** (same file, orphan sentence) → an
  addition to `disciplines/github-authority.md`, the missing second half of a rule that said what
  may not be attempted but not what is owed when an attempt is cut off. Propagated to Human at
  the Helm with `tools/sync_helm.py --apply`.
- **"Unit tests answer *does the code work*; audit scripts answer *how good is this output*"**
  (ears-to-hear `feedback-no-artifact-deps-in-unit-tests`) → a new discipline,
  `templates/sp-disciplines/tests-and-audits.md`, classified engine-only because a shared
  discipline may carry no engine vocabulary and it names `outputs/`, prompts and schemas.
- **The scriptorium rename** (ears-to-hear `reference-llmflow-vs-scriptorium`) → fixed in code
  rather than recorded as a fact; see the correction under item 1.
- **Excluded by ruling:** `project_xquery_ownership` (macula-greek) and `project_team`
  (paratext-copilot). Both characterise named or identifiable people and the quality of their
  work. The Captain, of the first: *"I would leave 5 out."* The second is the same category and
  additionally contradicts its own neighbour, which says never to call those colleagues "junior".

## Proposed destinations — awaiting a ruling, per item

### A. Machine-local facts → `~/.sp/user-context/` (the Captain's; never shipped)

1. **ears-to-hear's project root is its `LLMFlow/` subdirectory.** The registry entry points there
   as of 2026-07-14. Cross-repo tooling that filters `/LLMFlow/` — assuming a vendored engine copy
   — silently skips ears-to-hear's real pipelines. The authoritative `CLAUDE.md` is
   `ears-to-hear/LLMFlow/CLAUDE.md`, not the repo root.
   *(from `project_ears_to_hear_structure`)*

   > **Wrong, corrected 2026-08-24.** Item 1 is kept as written because it records what that
   > memory file said. It is false. `ears-to-hear/LLMFlow` was renamed to
   > `ears-to-hear/scriptorium` on 2026-07-14, and a *different* memory file in the same store —
   > `reference-llmflow-vs-scriptorium.md`, in the unaudited 42 — recorded the rename on the day
   > it happened. Measured 2026-08-24: `scriptorium/` holds 4,814 files and is tracked in git;
   > `LLMFlow/` holds 1 and is untracked. Two AI-written memory files contradicted each other
   > invisibly, and only the audit surfaced it. **Do not promote item 1.** Consequences already
   > acted on: `src/llmflow/gui/server.py` no longer hardcodes a consumer's folder name (it finds
   > `pipelines/` by shape, guarded by `tests/test_gui_pipelines_dir_discovery.py`), and #209's
   > body and comments are corrected.

2. **Read access is assumed for `~/github` and `~/.sp`** and their subdirectories — do not ask
   permission to read within them. **`/tmp` was never authorized**; use `./tmp` relative to the
   project root. *(from discourse-flow `feedback_filesystem_access`. Note: this session wrote to
   `/private/tmp/claude-501/...` per its own configuration, so the constraint and the harness
   disagree — worth resolving rather than transcribing.)*

### B. Cross-project practice → `~/.sp/disciplines/`

3. **Prompt edits are shown as a diff and approved before they are applied.** Stated 2026-08-12 as
   a standing rule. Prompts are where output quality is decided and prompt edits fail silently: a
   weakened guardrail produces plausible output that is subtly worse, with nothing in the suite to
   catch it. Applies to every prompt change including mechanical-looking ones. Code, schema and
   pipeline edits are **not** covered. *(from `feedback_prompt_diffs`)*

4. **When something fails, stop and report — do not route around it.** Do not change `raise` to
   `warn` without discussion. Do not write tests that justify a workaround. When the Captain says
   he is fixing a root cause upstream, **"we must fix this at the right level" is an instruction to
   wait, not an invitation to redesign.** *(from `feedback_failures_and_quality`; the shared rules
   cover surfacing decisions but none of these specifics)*

5. **One orphan sentence:** if `sp` rejects a command that exists in the current source, suspect a
   stale non-editable install in the consumer repo. → `disciplines/consumer-repo-conventions.md`.
   *(from `feedback_llmflow_editable_install`; the rest of that file is already covered there and
   in `docs/getting-started.md:85-99`)*

### C. Engine-relevant, possibly a rule → the Captain's call

6. **Work with the engine, not around it.** Before writing a plugin or a `type: function` step,
   check whether a native step type or built-in already does it. The named failure:
   `plugins/cohesion_analysis.py` was a Python wrapper around `run_basex` when `type: basex`
   already existed. *(from `feedback_scripture_pipelines_first`. Rules 23 and 24 cover the
   principle; this adds the concrete check and a worked example.)*

7. **Never implement windowing, window merging or cursor logic in Python.** It lives in the YAML
   pipeline. `merge_windowed_pericopes.py` is the canonical case of an LLM "fixing" a perceived
   windowing problem by reimplementing what the pipeline already did correctly.
   *(from `feedback_windowing_in_python` — a specific instance of rule 24)*

### D. discourse-flow domain knowledge → that repository, not this one

These are the highest-value items in the whole set and they belong in `discourse-flow`'s own
`docs/` or AI context. Recorded here only so the deletion does not lose them.

8. **Levinsohn/HOTDF-LS signals mark the opening of new units, never the closing of old ones.**
   The boundary between pericope N and N+1 is found by locating N+1's opening signal; there is no
   closing signal to find. **This is why windowing drops the last pericope** — the window can see
   where the last pericope opens but not where it closes, which needs N+2's opening. Its own text
   records that this "has been explained to LLMs at least 3 times" because it lives in
   `book/architects/windowing.md` and `docs/window-cursor-redesign.md`, neither of which is in the
   session-start read path. *(from `feedback_levinsohn_opening_not_closing` — directly relevant to
   this engine's `window` step and to `c1647af`)*

9. **Verses may only be used as milestones, never as array elements** — strictest for any structure
   an LLM sees. `coverage_check[]` (verse objects with text) violates it; `verse_sids_in_window[]`
   is tolerated as a coverage anchor discarded before assembly. In Python, verse-centric structures
   are dicts keyed by SID, not arrays. *(from `feedback_verses_as_milestones_only`; rule 12 states
   the principle, this states the schema consequences)*

10. **Narrative analysis belongs to ears-to-hear; discourse analysis to discourse-flow.** Levinsohn
    signals, pericope boundaries, discourse structure, divisions → discourse-flow. Scene
    construction, embodied/interpersonal layer, emotional dynamics, narrative arc → ears-to-hear.
    ears-to-hear consumes discourse-flow output and does not redo discourse analysis.
    *(from `feedback_discourse_vs_narrative`)*

11. **A passage may operate under several genre conventions at once.** "Which genre applies"
    becomes "which conventions are active". Philemon is both epistolary and hortatory.
    *(from `feedback_genre_multi`)*

12. **`tradition_comparison` in `synthesize-book-arc.gpt` is the single designated freelancing
    zone** — the one field where training knowledge is knowingly accepted while vetted datasets do
    not exist. Do not flag it as a freelancing failure; every other synthesis field must be
    grounded in pipeline data. First field to migrate when a vetted outlines dataset exists
    (discourse-flow#64). *(from `project_tradition_comparison_strategy`)*

13. **Docs explain their own terms.** Every technical term (asyndeton, cataphoric focus, PoD,
    over-encoding) gets a plain definition, an English-language parallel, and why it matters —
    including in design documents. Stated 2026-08-13: the docs should collectively become a
    tutorial on understanding discourse, simpler than Levinsohn. *(from `feedback_doc_style`)*

14. **One board serves both discourse repos:** org project **17** "Discourse Flow"
    (`PVT_kwDOCyYjWs4Bf-Hr`). The Hebrew repo has no board of its own — do not create one.
    Status field `PVTSSF_lADOCyYjWs4Bf-HrzhaNIxw`; **there is no column named "TODO" — `Next Up`
    is the TODO column.** Hebrew lags Greek deliberately, so a Hebrew item is often downstream of
    a Greek one. *(from `project_shared_project_board`)*

15. **OT pipelines exist** in `discourse-flow-hebrew` (Psalms and Genesis live, Exodus next);
    `discourse-flow` is NT only. Hebrew diverges rather than copying: Macula tokenises morphemes,
    so `ref` is **not injective** — about 50% of Hebrew words hold more than one morpheme, and it
    diverges from the USFM word-reference standard on 16.2% of words, which is why addressing uses
    Macula `xml:id`. *(from `project_ot_data` — bears directly on #200's alignment spine)*

16. **Mark (678v, 39 pericopes) is the GNT gate book**; Philemon stays the quick smoke test.
    *(from `project_gnt_test_book`)*

17. **Do not commit pipeline changes until the pipeline runs clean on at least one book.** The
    suite exercises no live LLM calls, so schema bugs that draw a 400 from OpenAI are invisible to
    it. *(from `feedback_pipeline_gate`)*

18. **Never italicise anything that could contain Hebrew text** — stated as absolute ("never,
    ever"). Use colour, weight or size instead. *(from `feedback_no_italic_hebrew`)*

19. **Do not recommend design choices.** Describe options factually; no "Recommendation:" section,
    no editorialising about which is cleaner. *(from `feedback_no_recommending`. **This session
    recommended throughout**, though the Captain asked for advice directly — the rule is
    discourse-flow-scoped and the conflict is unresolved.)*

20. **Track exactly one output subdirectory** — `output/book-discourse/`. Siblings
    (`output/intermediate/`, `outputs/`, generated `input/annotated/`, logs) stay untracked, and
    `tmp/` is never committed. A blanket "untrack all output" proposal was rejected 2026-08-10.
    *(from `feedback_tmp_and_output_tracking`)*

21. **`lxml`, not `xml.etree.ElementTree`**, for XML in plugins. *(from `feedback_xml_parsing`)*

22. **Two designs in flight in ears-to-hear**, both early: a book-level leaders guide intended as a
    successor to per-pericope guides, and an oral study bible for English-speaking listeners with
    an explicit list of phrasings banned from prompts ("in the original Greek…", "scholars
    debate…", century-attribution, hypothetical-reader framing).
    *(from `project_ears_to_hear_book_guide`, `project_oral_study_bible`)*

## Discarded as duplicates — recorded so nobody re-audits them

**This repository:** `feedback_file_organization` (rule 14) · `feedback_surface_decisions` and
`feedback_captain_response_slots` (`disciplines/surface-decisions.md`) ·
`feedback_authorized_vocabulary` (`design-vocabulary.md`) · `reference_release_process`
(`RELEASE_CHECKLIST.md`) · most of `feedback_llmflow_editable_install` · `MEMORY.md`.

**discourse-flow:** `feedback_branch_workflow` (now rule 28) · `feedback_git_commands`
(`disciplines/workflow.md`) · `feedback_design_authority` (`disciplines/design-authority.md`, which
also carries the "Nothing is intentional unless it is MY intention" incident) · `feedback_test_runner`
· `feedback_pyproject_toml` · `feedback_plan_vs_design` — which cites
`~/.sp/conventions/llmflow-project-tracking.md`, **a path that no longer exists** ·  `MEMORY.md`.

## The remaining 42 — audited 2026-08-24

Ten projects. Read from `8678309`; none of these files exists on disk.

| project | files | disposition |
|---|---|---|
| paratext-copilot | 7 | 2 general candidates, 1 project-specific safety rule, 1 excluded (people), 1 index, 2 low value |
| ears-to-hear | 7 | 1 promoted, 1 acted on in code, 4 duplicates, 1 index |
| macula-greek | 6 | 2 promoted, 1 excluded (people), 2 duplicates, 1 index |
| biblical-terms-extension | 5 | 1 general candidate, 1 conflict found, 1 stale snapshot, 1 user profile, 1 index |
| scripture-burrito | 4 | project facts to that repo, 1 duplicate, 1 index |
| llm-gateway | 3 | 1 live security fact, 1 project pointer, 1 index |
| discourse-flow-hebrew | 3 | 1 engine-relevant, 1 project overview, 1 index |
| catenae-dev | 3 | 1 attribution to keep, 1 procedure, 1 index |
| nida-institute | 2 | org facts, largely duplicated by committed audits |
| biblica-translation-notes | 2 | **the most consequential file in the store**, 1 index |

### The three that must not be lost

1. **A confidentiality constraint with contractual weight** (translation-notes). The notes draw
   on NIV CBT internal rationale and formatting-review notes; published notes must **never**
   reference NIV, CBT or Biblica as sources, and must carry no translator names. Ruled by the
   Captain to live **in that project, not in sp global**. That repository has no
   `docs/ai-context/`, so the constraint currently exists only here and in `8678309`.
   Compounding it: the notes are intended to be freely licensed but are not yet published, so a
   leaked attribution would be copied beyond recall. See `design-source-licensing.md` §5.
2. **A live security fact** (llm-gateway, recorded twice): the API key is hardcoded in the
   paratext-copilot WebView source, with a Bearer token in `copilot-chat.web-view.tsx`. The fix —
   moving the call to the extension backend — is tracked in that project's #2 and #16.
3. **The Hebrew statement of the windowing principle** (discourse-flow-hebrew,
   `feedback_hotdfls_opening_not_closing`). Fuller than the Greek one at item 8, and it explains
   *why* the last pericope in each window is dropped and re-adjudicated — which is the cursor
   semantics `c1647af` fixed in this engine. Its own text says it has been *"explained to LLMs at
   least 3 times"*.

### Three general-rule candidates, not yet ruled

- **Questions are not instructions** (paratext-copilot). *"Is that clear?"*, *"Do we need X?"* are
  questions: answer and wait. Adds *"auto mode is not blanket authorization for scope the user did
  not request."* `surface-decisions.md` covers surfacing a decision, not mistaking a diagnostic
  question for a go-ahead.
- **Design documents must teach the tradeoffs** (biblical-terms-extension). *"If it's not
  educating me to decide wisely, it's not worth writing at all."* Rule 26 covers teaching the
  Captain about *datasets*; nothing covers design documents.
- **Do not characterise teammates in shared text** (paratext-copilot) — no "junior", no status
  filler. The natural sibling of rule 30.

### Two conflicts the audit exposed, both unresolved

- **Recommendations.** Recorded in three separate projects: discourse-flow (*"Do not recommend
  design choices"*), paratext-copilot (*"You are not the expert here"*, after a "Recommended
  defaults" section was appended to an issue), and by implication the design-docs item above.
  Yet the Captain asks for recommendations constantly in conversation. **Proposed reading, not
  ruled:** the prohibition is about *outward-facing artifacts* — issues, PR comments, documents a
  team reads — where an AI recommendation carries borrowed authority and forecloses the team's
  decision. It is not about conversation with him. That reading makes all three records true.
- **`git -C`.** biblical-terms-extension records *"Do not use `git -C <other-repo>` … this
  triggers a permission prompt even for read-only operations"*, quoting him: *"I don't want to sit
  around approving each step."* This repository's `CLAUDE.md` **mandates** `git -C /path`. Both
  are true of their own machines' permission configurations, but an agent moving between the two
  repositories will be wrong in one of them.

### Naming people — the distinction the audit forced

Three files name people, and they are not one category:

- **Credit** — *"Bruce Robertson (Mount Allison University) did the OCR"*, for TEI headers. That
  is attribution someone is owed; keep it, in catenae-dev.
- **Assignment** — *"domain consolidation is Reinier's responsibility."* An ordinary project fact.
- **Characterisation** — the quality of a contributor's work, or colleagues described as junior
  and sorted by which issues suit them. **Excluded by ruling.**

### Project-specific, belonging to their own repositories

scripture-burrito's schema archaeology and its Read the Docs publishing constraint (he has no RTD
admin access) · the Hebrew pipeline's architecture and its non-public HOTDF-LS dependency ·
catenae-dev's chapter-map regeneration procedure · nida.bible as the confirmed canonical domain ·
paratext-copilot's rule that a Paratext note write must always present editable text with an
explicit approve step before posting.

### Discarded

Four `MEMORY.md` indexes · two project-state snapshots, stale by nature · duplicates of existing
disciplines: scripture-burrito's Human-at-the-Helm summary, ears-to-hear's `=>`-slot,
surface-decisions and LLM-artifacts-are-not-authoritative files, macula-greek's TDD and
no-design-decisions files.

## Open

- ~~42 files across ten projects are unaudited~~ — **done 2026-08-24.** All 81 have been read.
- **The mechanism is unfixed.** This repository's `CLAUDE.md` requires approval before writing a
  memory file; the machine-wide default does not, which is how twelve projects accumulated 81.
  Emptying the store does not stop sessions refilling it.
- **Most of sections A–D has still not been carried out.** Each needs the Captain's ruling, and
  items 8–22 belong in another repository. Item 1 is wrong and must not be promoted.
- **The translation-notes confidentiality constraint has nowhere to go yet.** That repository has
  no `docs/ai-context/`, so it needs `sp init` run there or a hand-written `CLAUDE.md`. Of
  everything in this document it is the item with real-world consequences for someone other than
  us, and it is the one still resting entirely on this file.
- **Three rule candidates and two conflicts** are recorded above, unruled.
