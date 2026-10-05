# Project TODO

> **Convention:** Active work lives here. Bugs and permanent decisions go to
> [GitHub Issues](https://github.com/nida-institute/LLMFlow/issues).
> Link issues with `→ #N` so this file doesn't duplicate GitHub.
> Board: https://github.com/orgs/nida-institute/projects/13

## 🔥 Active

### 🚢 THE NEXT RELEASE — walked through with the Captain, 2026-10-01

> No GitHub milestone exists; this section is the release's only declared scope. Walk it **in
> this order**, one item at a time, with the Captain — he asked for exactly that.

**Ruled 2026-10-01:**

- **Helm parity is out of this release** — *"Let's take Helm parity out of this release."*
  `tests/test_helm_sync.py` stays red (3) until the coordination design lands. Ship with those
  known failures, or record an exemption: **his call, not yet made.**
- **The prompt rework is not the engine's.** The Ears to Hear methodology belongs to a client, and
  the commentary it shapes belongs in `ears-to-hear`, not in the engine's starter example.
  `prompts/commentary.gpt` stays as he approved it 2026-09-28. Whether Ears to Hear is told
  anything is his (`project/rules.md` rule 2).
- **The quickref stays short** — worked examples, the rules that bite, and a pointer to
  `docs/cli-api.json` for the complete key list. It is not to become a second copy of
  `docs/sp-language.md`. **Open, his:** whether `sp-language.md` ships to projects as a
  generated catalog row, which decides how thin the quickref can be.
- **The `<!-- -->` prompt header is withdrawn**, and **lint expands mixins** (his option A).
  Both built this session; `CHANGELOG.md` Unreleased carries them.

**The inventory, in order:**

1. **→ #244, the starter example's gates** — `plan-starter-example-commentary.md` §7. Tests 6, 7
   and 10 are met; 1–5 need one `sp run`. Four questions put to him and **unanswered**:

   > ⛔ **Superseded 2026-10-02.** The Captain scratched the commentary example entirely. Its
   > replacement — a reader's guide and a parallel-passage significance step — is designed in
   > `project/plans/design-starter-examples.md`. The gates and questions below are kept as the
   > record of what was open, and are not to be worked.
   >
   > ✅ **The replacement is done — the Captain, 2026-10-05:** *"The sample output looks great,
   > and examples are now done."* Work order and evidence: `project/plans/plan-starter-examples.md`.
   > **Not yet committed**, and the CHANGELOG entry is still to write.
   - [ ] download the UBS Parallel Passages dataset? `parallels` is `null` on this machine, so a
         run now tests the commentary step without one of its inputs. Writes `~/.sp` — his
   - [ ] which passages §7 evaluates — `MRK 1:1` and `MRK 1:6` as written, or another passage
   - [ ] test 9, *"the reference object is saved"* — nothing saves `passage_info`. Keep or drop
   - [ ] §7 still says "both prompts" and "nine positions"; D2 ruled one prompt, the grammar has
         twelve. Update the plan — his document
2. **→ #176**, strip frontmatter before the model call — not started
3. **→ #252**, licence terms at download and register — ruled 2026-09-25, not built:
   `grep -n "accept-terms\|click.confirm" src/llmflow/cli.py src/llmflow/cli_utils.py` → nothing
4. **Position 12, `# REFERENCE`**, in `data/prompt-structure.yaml` — ruled 2026-09-21; built or
   not is **unchecked**
5. **`data/models.json`** — his uncommitted change; whether it ships is his call
6. **A red suite blocks any cut** — see the 🔴 section below and `project/HANDOFF.md`
7. **The `sp/index.md` link to `llmflow-language.md` breaks at this release** — the rename reaches
   `main` with it. The link is `SP_DOC_LINKS` in `src/llmflow/file_catalog.py`
- [ ] **UBS Parallel Passages as a JSON dataset, generated once and saved in this repository** —
      the Captain, 2026-10-03: *"I said generate it once and save it as a dataset in this
      repository."* Design: `project/plans/design-parallel-passages-json.md`, D5 ruling. A
      generator in `tools/`, the JSON committed in `data/`, the `parallel-passages` step reading
      it instead of the XML. Open before building: the `counted_in` slot (line 329), and D7's
      layout (flat siblings or `addressed`/`counted` blocks). **Whether it is in this release is
      the Captain's call** — evidence:
8. **→ #261, resource preflight with an offer to install and register** — added to this release by
   the Captain 2026-10-02. **Not started**, measured the same day: no `resource_preflight` module,
   no plan in `project/plans/`, no mention in this file or `CHANGELOG.md` before this line. An
   earlier session reported it as done; nothing in the tree supports that. **Depends on #252**
   (item 3), whose licence display and consent gate it must reuse rather than duplicate. Seven
   questions in the issue body are open, and the Captain's

**Not in the release, raised for his decision: `\q` continuation lines lost from BSB.** Measured
2026-09-29: `~/github/usfm-bible/examples.bsb/42MRKBSB.usfm:12-18` carries the Isaiah quotation on
`\q1`/`\q2` lines; `playground/outputs/41001001-41001008-english.txt` delivered only
`⌊1:2⌋ As it is written in Isaiah the prophet: ⌊1:3⌋ "A voice of one calling in the wilderness,`.
**Not yet placed** — engine reader, the `examples.bsb` mirror BSB is registered against
(`~/.sp/registrations/BSB.yaml`; `data-sources.md` says the official release replaced it), or the
registration. The evidence shows the source has the lines and the output does not, nothing more.
No issue, no test.

**Found 2026-10-01, untriaged — each wants an issue or a ruling, not a quiet fix:**

- `sp init --update` **creates** absent starter examples (`cli_utils.py:637` skips them only
  under `--no-examples`); `docs/ai-context/sp/command-line.md` says it only refreshes present ones
- `docs/ai-assistants.md` and `docs/consumer-repo-layout.md` describe the pre-split four-file AI
  context and an `AGENTS.md` that `sp init` never writes
- `~/.sp/registrations/WLC.yaml:8` is an absolute path with no `dataset:`
- `~/github/nida-institute/levinsohn-samuel-hebrew`'s origin is `jonathanrobie/levinsohn-samuel-hebrew`
- `CHANGELOG.md` Unreleased has `### Changed` twice (lines 72 and 177)
- likely stale: the shell-rules box below (`ask-for-the-exception` exists, `data/ai-rules.yaml:638`);
  the unused-`requires:` box (`unused_requires_warnings` exists, warns — ruling unrecorded); the
  `levinsohn-lgntdf` box (it is registered, `~/.sp/datasets/levinsohn-lgntdf.yaml`)
- CLAUDE.md names `apply_template()` in `io.py`; there is no such function
- the 5 comment-header prompts in `llmflow-historical-pipelines` are now refused

### 📅 TOMORROW IS HELM — set by the Captain, Tuesday 2026-09-29

> In his words: **"I am mentoring sp tomorrow, Helm on Thursday, so we will focus on Helm
> tomorrow."**

So **Wednesday 2026-09-30 is Helm work**, ahead of mentoring Helm on **Thursday 2026-10-01**.
This is a scheduling instruction and does not supersede the order of goals below; it says which
day is spent where.

- [ ] **The parity suite is red on both sides, and this session made it so.**
      `src/llmflow/templates/sp/disciplines/project-tracking.md` gained a fourth directory —
      `project/upstream/<owner>-<repo>/` — and `hatch run python tools/sync_helm.py` reports
      **`DIVERGED disciplines/project-tracking.md`**, 12 of 13 shared files otherwise `same`.
      The Helm half has not been made. **Not applied**, because that tree is busy: 6 unpushed
      commits, staged *and* unstaged edits across eight skill files, and five untracked paths —
      evidence:
- [ ] **Helm already has a design in flight on exactly this subject** —
      `project/plans/design-coordinating-changes-with-sp.md`, untracked in their tree as of
      2026-09-29. Read it before starting, rather than designing the same thing twice — evidence:
- [ ] **No new folder is needed for Helm coordination**, checked 2026-09-29 rather than assumed.
      Three homes already exist and one is already in use: `collab/human-at-the-helm/` carries
      their note of 2026-09-23 (*"a helm session left three files changed here and two tests
      red"*), `data/helm-sync.yaml` declares the 13 shared files with a recorded ruling beside
      each permitted difference, and design documents go in `project/plans/`. `project/upstream/`
      is for repositories we do **not** own, which Helm is not

### 🧱 ORDER OF GOALS — set by the Captain, 2026-09-28

> In his words: **"(1) finish the bloody examples, (2) make df happy with latest collab and other
> outstanding df items, (3) ANTLR"**. This supersedes every earlier ordering in this file.

1. **Finish the examples → #244.** **Implementing #263 is inside this goal, not beside it** — he
   ruled 2026-09-28 that the example waits on named step outputs, so the order is: implement
   #263, write the example, do the removal, run the gates.
2. **Make the CLI the unmistakable external API** — inserted here by the Captain 2026-09-28. See
   immediately below.
3. **discourse-flow.** The inventory is below; four items, three of them small.
4. **ANTLR → #239.** The parser. Design decisions already ruled; nothing to build until the rest
   are done.

#### 🚪 GOAL 2 — the CLI API is THE external API, and `index.json` is not an API at all

> **Set by the Captain 2026-09-28:** *"we HAVE to make it clear that the CLI API is THE external
> API. index.json is a map of the implementation, not an API meant for users or tests."*

**The file says nothing about itself, which is the whole problem.** Measured 2026-09-28:
`docs/index.json` has exactly two top-level keys, `modules` and `summary`, and lists **881
functions across 93 modules**. There is no statement of purpose and no boundary anywhere in it. A
reader — person or model — who finds a catalogue of 881 functions concludes it is an API listing,
because nothing in it says otherwise. `project/index.md` describes it as *"Every module and
function this engine has"*, which reinforces exactly that reading.

**Rule `the-language-is-the-whole-surface` already says the engine is reached one way.** What is
missing is the same statement attached to the artifact that most invites the opposite conclusion,
and the explicit extension to **tests** — `docs/ai-context/project/rules.md` rule 1 says a test
exercises a step through the object model or the CLI, and #250 counts **29 files against 12** going
the other way.

- [x] **The generated file declares what it is**, in an `about` block placed **first**, before the
      catalogue: what it is, why it exists, `not_an_api`, `not_for_tests`, and what regenerates it.
      Written in `tools/index_signatures.py` so it survives regeneration. Guarded by
      `tests/test_internals_map_declares_itself.py` — **RED first** (no `about` at all), 3 passed
- [x] **`docs/ai-context/project/index.md`** — the row now reads *"A map of this engine's
      implementation — not an API"*, and says it is not a surface for tests either. The old
      headline was *"Every module and function this engine has"*, which is what a skimmer took
- [ ] **Decide whether this belongs in `data/ai-rules.yaml`** as an extension to
      `the-language-is-the-whole-surface`, or as prose in the project index. A rule reaches every
      project; this concerns a file only this repository has — **the Captain's call** — evidence:
- [x] **`docs/python-api.md`** — it **did** read as an offer: *"a stable, documented surface for
      programs that embed the engine"*, with nothing saying whose surface. It now opens with who
      it is for — work in this repository — names the one surface a project gets, and points at
      `index.json` as the thing most often confused with it
- [x] **Is it guardable? Not as posed** — measured 2026-09-29 by `grep -rlE` over `tests/`:
      **26 files** call a step handler directly, **14** use the object model, and **~230 of ~260**
      import `llmflow` at all, which is correct here since the rule binds projects and not the
      engine's own tests. **A ratchet on `project/rules.md` rule 1 is buildable instead**, on the
      `test_docstrings_say_what_not_why` pattern — findings, depth and what must be settled first
      in `project/audits/audit-one-surface.md`. **Not built**: a new guard needs its own
      authorization — evidence: that record

**Widened by the Captain, 2026-09-28:** *"that needs to be clear in our ai context, and in anything
exposed to users about our APIs."*

> 🔴 **A live contradiction found while scoping this, 2026-09-28 — the shipped index still sells
> the Python API.** `src/llmflow/file_catalog.py:235-243`, the `SP_DOC_LINKS` constant, renders
> into every project's `docs/ai-context/sp/index.md:35-37`:
>
> *"[Python API] — `import llmflow`: `load_pipeline(...)` then `.resolve()` / `.lint()` / `.run()`
> / `.schemas()`; `PIPELINE_SCHEMA` + `api_catalog()` are the machine-readable syntax-to-API map.
> **Prefer this** over re-parsing pipeline YAML."*
>
> Rule `the-language-is-the-whole-surface` was ruled 2026-09-27 and its own record says the
> shipped context was corrected — **it was corrected in `sp/overview.md` and not here.** So every
> project initialised since is being told to import the package and preferentially use it.
>
> **This is the third instance of one pattern this week**, after `include: … valid only with
> format: usj` (fixed in the language reference, alive in the shipped quickref) and `click` is
> "the CLI library" (fixed in the queue, alive in the plan). Each was recorded as fixed after
> checking the file a note cited. **The lesson, now three times paid: grep for the claim, never
> for the location.**

- [x] **`SP_DOC_LINKS` fixed** at `file_catalog.py`. It now states the one surface and points at
      the language reference, the quickref and `sp --help`; the Python API offer is gone.
      Regenerated into `docs/ai-context/sp/index.md`
- [ ] **Sweep the AI context, both halves.** `sp/` is generated and ships; `project/` is ours —
      evidence:
- [x] **Swept, and it was narrower than feared.** Counted rather than assumed: `README.md`,
      `docs/getting-started.md` and `docs/GPT_CONTEXT.md` mention the Python API **0 times**.
      `docs/architecture.md` has 8 and `docs/python-api.md` 14 — both legitimately, since both
      document the engine's internals for engine work. The defect was never the count; it was
      that neither said **whose** surface it described
- [x] **The guard is extended, and the gap was the finding.** It read `*.md` under `templates/`
      only, so text rendered from Python constants shipped unseen. Four new tests render what a
      project *receives* — `render_sp_index()` — and apply the same checks. **RED first**, naming
      all four offending terms (`load_pipeline`, `api_catalog`, `PIPELINE_SCHEMA`,
      `import llmflow`), then green: **80 passed**

#### The discourse-flow inventory, read 2026-09-28

From `collab/discourse-flow/2026-09-28-the-defect-log-needs-an-info-severity-and-lint-refuses-a-safe-builtin.md`,
which was untracked and unread when it arrived. **None of it blocks goal 1.**

- [x] **`info` is a third severity.** `SEVERITIES = ("info", "warning", "error")`, ordered
      least-to-most-serious so the order is part of the vocabulary. **The arithmetic trap they
      warned about does not exist here** — `counts()` derives per severity from `SEVERITIES`
      rather than `len(defects) - errors`, so it was already right. Pinned anyway by
      `test_counts_are_per_severity_rather_than_derived_by_subtraction`, because the subtraction
      form is the tempting simplification and fails *quietly*: the total stays right while the
      split goes wrong. **Tell them it was already safe here**
- [x] **`_DefectHandler.emit` no longer promotes.** `ERROR→error`, `WARNING→warning`, anything
      below→`info`. It was a defect either way, and until `info` existed there was nowhere to put
      an INFO. 11 tests in `tests/test_defect_info_severity.py`, **7 red first**
- [x] **`sp lint` accepts what the evaluator accepts.** `condition_safe_builtins()` is now one
      declaration read by both halves — the evaluator builds its environment from it, the
      validator skips those names. All seven builtins covered, **7 red first**. **The
      non-regression is the point:** `${len(nope) > 1}` still fails lint and names `nope`, because
      skipping builtins is only safe if an unknown name is still caught
- [x] **→ #255 replay — landed at `debce504`.** This box sat unticked until 2026-09-29 while the
      `🔁 SECOND` section below recorded the same work as finished; the commit is the evidence and
      this was the stale half. The scope was worse than first recorded — not one awkward prompt:
      `segment-book.gpt` (890 template lines vs 964 rendered) and `segments.gpt` (666 vs 742) both
      refused, and **every prompt in that pipeline embeds a JSON payload**, so none could be
      replayed. Four rulings in their segmentation audit said "test with sp replay" and could not
      be; a 37-rule prompt change landed untested, against an alternative of **~$22 per edit** for
      a Mark run. Replay now aligns on variable sites rather than line counts, so a multi-line
      value is no different from a single-line one. **One thing it still does not do**, deferred to
      #243 Part 3 and now named in the error message rather than left to surprise: it reads
      `schema:` from prompt frontmatter and does not fall back to the step's `response_format`,
      because replay is handed a prompt and a capture and never sees the pipeline



### 🔴 The suite is red in seven places, and every one is a half-finished thing

> **Audited 2026-09-27** at the Captain's direction — *"the last LLM instance left several
> features half-way up the mountain, reporting them as being done."* Measured, not recalled:
> `hatch run pytest tests/ -q -m "not integration" -p no:randomly` → **5878 passed, 24 skipped,
> 7 failed** in 138s. The count matches what `HANDOFF.md` claimed; what nobody had recorded is
> that each failure names an unfinished job rather than a flaky test.
>
> **Four of the seven clear with one command** — `hatch run sp init --update`, which is
> `HANDOFF.md`'s next action. `sp` is not on the bare PATH; it exists only inside the hatch
> environment. **Not `sp doctor`** (#210).

- [ ] **`test_template_layout`** — three rendered copies are behind their templates:
      `docs/ai-context/sp/overview.md`, `docs/ai-context/sp/passage-references.md`,
      `docs/llmflow-language-quickref.md`. Cleared by `sp init --update`
- [ ] **`test_global_disciplines::test_installed_skills_match_templates`** — the installed skills
      differ from what ships. Cleared by the same command
- [ ] **`test_prompt_structure_single_source`** — `.claude/skills/audit-prompts/SKILL.md` has
      drifted from its template; it still carries the `**WORKFLOW SKILL** —` prefix that was
      ruled out on 2026-09-25. Cleared by the same command
- [x] **`test_plan_docs_index` — GREEN 2026-09-29**, regenerated with
      `hatch run python tools/update_plans_index.py` on the Captain's instruction, *"it should be
      kept up to date, always"*. `hatch run pytest tests/test_plan_docs_index.py -q -p no:randomly`
      → **187 passed, 13 skipped, 0 failed**, from 186/13/1. Committed `8c97cd0`.
      **It was stale by four documents, not one** — `design-named-step-outputs.md`,
      `design-parallel-passages-json.md`, `design-sp-help.md` and
      `plan-starter-example-commentary.md`, 62 documents to 66 — and the last of those was the
      recorded symptom, `proposed (2026-09-25)` against the `ruled (2026-09-26)` its line 3
      declares. ⚠️ **The "uncommitted hand edit" this entry warned about was not one**: the diff
      was a partial regeneration someone had left — one added row and the count at 63 — so nothing
      authored was at risk. Looking at the diff first is still the right order
- [ ] **`test_portable_skills`** — `/stage-commits` is unclassified. **The blocker is S1 in
      `project/open-decisions.md`, an unanswered `=>`, and it is the Captain's.** See the
      `/stage-commits` section below
- [x] **`test_product_name_in_prose` — FIXED 2026-09-27** on the Captain's instruction
      (*"it must say Scripture Pipelines. Fix it."*). `docs/ai-context/project/data-sources.md:48`
      used the deprecated product name for `data/resources.json`'s vendored copy;
      `design-vocabulary.md` requires the ruled name. One occurrence, rewritten in place. The
      file is one of the Captain's uncommitted working-tree changes, so the fix rides with his
      edit rather than standing alone
- [ ] **`test_resource_provisioning`** — the vendored `data/resources.json` is behind its
      upstream in `awesome-biblical-data`: ids were renamed there
      (`bibleaquifer-bdb-hebrew` → `bdb-hebrewlexicon`, and 150 further diff lines). Re-sync the
      vendored copy; **never edit it here**, an edit is reverted by the next sync

**Guard wanted, noted and deliberately not built (Captain's call, 2026-09-27).** Nothing checks
this file against reality, which is why eleven finished entries sat here unticked. A test reading
every `→ #N` and failing when an entry marked open names a closed issue would catch it — it needs
either network in the suite or a committed snapshot, which is a design decision rather than a
tidy-up. **Do not build it without a ruling.**

### 🧭 The language's shape — three threads opened 2026-09-27/28, and they gate the examples

> Opened while unblocking #244 and now ahead of it. All three share one subject: **what the
> language declares, and how a caller finds out.**

**→ #263 — named step outputs.** Design: `project/plans/design-named-step-outputs.md`,
`proposed (2026-09-28)`.

- [x] Filed, design written, two decisions ruled — naming a member is requesting it; the example waits
- [x] **All five are ruled**, and this box said otherwise until 2026-09-29 — the **second** copy of
      that false claim in this file, corrected here after the first was fixed at the `A‴` entry
      below and this one was missed. That is the failure this file already records twice: **grep for
      the claim, never for the location.** D3's rename syntax settled D1, D2, D2′ and D4; D2 is
      ruled A, a bare output name binds the primary member. The one open slot is at
      `design-named-step-outputs.md:389` and is listed under `A‴`
- [ ] **Identifier rules are part of the grammar, so this waits on #239.** The rename syntax was
      written `text-bsb=text`; **hyphenated names do not resolve and fail silently** —
      `resolve("${text-bsb}", …)` returns the literal. Measured 2026-09-28 — evidence:

**→ #239 — the expression parser. Reclassified 2026-09-28.**

> This file recorded it as *"a kludge, off the critical path"*. **It is now a precondition.**
> Ruled by the Captain 2026-09-28: *"we WILL be parsing expressions with precedence."* That
> answers #241's open question — operations are **expressions**, not step methods — and makes a
> real grammar the larger half of that work rather than a cleanup.

- [x] **Parser comparison posted** as a comment on #239, 2026-09-28, with measurements
- [x] **Measured, not assumed:** ANTLR 4.13.2 codegen is **byte-deterministic** (two runs,
      `diff -r` identical, no timestamps or absolute paths); the header carries the version, so a
      version bump self-enforces the pin; a left-recursive expression rule compiles as written;
      output was **408 lines**, not the thousands an earlier draft claimed; **`antlr4-tools` does
      not pin the generator** — it depends on `install-jdk` and fetches a JDK and the jar at run
      time; the jar is pinnable by URL + sha256 instead
- [x] **Recommendation: ANTLR**, generated sources committed, drift caught in CI by regenerate-and-diff.
      A JDK in CI is smaller than the Node toolchain CI already carries
- [ ] **The Captain's ruling on expressions belongs in #241 and in
      `design-operations-in-the-pipeline-language.md`**, whose `=>` slots are his alone — evidence:
- [ ] **Choose the parser.** Partly downstream of #264's editor question: tree-sitter only earns
      its place if editor tooling is pursued — evidence:

**→ #264 — nothing lets a user ask what the engine provides.** Filed 2026-09-28.

- [x] Filed, with the LSP-versus-tree-sitter analysis and the shared-corpus argument in it
- [x] **Design for the concrete portion** — `project/plans/design-sp-help.md`,
      `proposed (2026-09-28)`: `sp help services`, `sp help resources`, everything rendered from
      the schema rather than hand-kept
- [x] **Corrected a premise of #264 while designing it:** `api_catalog()` is **not** the source.
      It catalogues the *Python API's verbs* (`catalog.py:31-60`) — the surface
      `the-language-is-the-whole-surface` says a project must not build against. `sp help services`
      derives from `PIPELINE_SCHEMA` instead
- [x] **D1 is ruled** — `design-sp-help.md:156`: *"Yes, a service is a step type, and 'step types'
      is a better name for it since it's what the user sees."* So the command is
      `sp help step-types`. This box listed it as open until 2026-09-29; found while re-reading the
      queue against the design documents' own `=>` slots, which are the authority
- [ ] **Three decisions in that design are still the Captain's** — the remaining empty slots at
      `design-sp-help.md:183`, `:190` and `:198` — evidence:
- [ ] **Two gaps it exposed rather than created:** `scripture` declares no members, so
      `sp help services scripture` has no `returns` block until #263 lands; and **no step type
      declares a one-line purpose**, so either the schema gains one or the text is hand-kept and
      drifts — evidence:

### 📖 FIRST — finish the examples

> ✅ **UNBLOCKED — #263 shipped at `3d6c8c5` on 2026-09-28**, the same day this block was written.
> The banner below is kept as the record of why the example waited; it stopped being true within
> hours and nothing updated it, which is how a session on 2026-09-29 came to report the example as
> blocked three times before checking `git log`.
>
> **Group B is done and was never restarted from this banner** — `pipelines/commentary.yaml`
> already carries the ruled syntax at line 44, `output: [subject=text, passage_info=reference]`,
> and lints clean. What actually remains is **Group D, the gates**, and **Group E, the Captain's
> `sp run`**. Both are below.
>
> ⛔ *Written 2026-09-28, superseded the same day:* **the example waits on → #263.** Ruled by the
> Captain answering D5 of `project/plans/design-named-step-outputs.md`: *"Yes, the starter example
> waits for this."* The example's `output:` line is the thing under design, and the example ships
> as the worked pattern every project copies — so writing it now would teach a form being replaced.
> **Group B is not to be started.** Three decisions in that design are open, and D2 in particular
> changes what the example's YAML looks like. Groups A″ (documentation) and C (the removal) are
> **not** blocked by it.
>
> **Set by the Captain 2026-09-26:** *"let's finish the examples first, then put that second on our
> todo list."* This goes ahead of everything below it, including the 2026-09-22 line that put
> #246–#248 before everything else — **and is itself now behind #263.**

The work order is `project/plans/plan-starter-example-commentary.md`, **`ruled (2026-09-26)`**
(this line said `proposed (2026-09-25)` until 2026-09-27; the file's line 3 is the authority) with
seven rulings in §2 and **all four** decisions in §8 answered. → #244

**Two pieces. #176 was listed here and is not a dependency** — corrected 2026-09-26 against
`steps/llm.py`: `body` at line 88 feeds the contract check and is discarded, the whole file reaches
the model (157 → 232 → 310), so #176 changes what the model sees and nothing about the pipeline
YAML or how a `.gpt` is authored. It gates #255 instead; see that section.

- [x] **The Parallel Passages step → #258.** Verse-level `references` shipped at `0030ef9`;
      `hatch run pytest tests/test_parallel_passages_step.py tests/test_parallel_passages.py -q`
      → 22 passed. `returns: [words]` stays refused and does **not** block: the example is Greek
      and needs references only

#### The completion checklist for #244 — tick a box only with its evidence beside it

> **Standing instruction, the Captain 2026-09-27: *"always keep progress up to date by checking
> off items."*** Tick a box **when the work lands, not at the end of a session** — a checklist
> updated in one batch afterwards is written from memory, which is the failure it exists to
> prevent. Evidence is a test id, a command and its result, a count, or a commit sha.

> **Built 2026-09-27** because §7 of the plan is not one: it covers the example's behaviour and
> says nothing about the catalog, the template twins, the docs or the deletions, and it carries no
> evidence column. Rule: *"not **done** — **how you know**: a test id, a file and line, a command
> and its result, a count, a date."* → #229, which was filed for exactly this failure.
>
> **The removal surface was measured, not estimated.** The plan says "four catalog rows, four
> template twins, `docs/tutorial.md` and `command-line.md`". The tree says otherwise, and the
> difference includes code:

| what | measured 2026-09-27 |
|---|---|
| files in `pipelines/` + `prompts/` | **12** — each `.yaml`/`.gpt` also has a `-view.md` and a `.html` |
| template twins under `src/llmflow/templates/project/` | 4 |
| `data/file-catalog.yaml` | lines **224–256** |
| **code** | `src/llmflow/cli.py`, `src/llmflow/cli_utils.py` |
| tests | `tests/test_init.py`, `tests/test_linter.py`, `tests/test_windows_encoding.py` |
| docs | `tutorial.md`, `command-line.md`, `llmflow-language-quickref.md`, `presentations/tabs.md`, `sp/index.md` (generated from the catalog), plus 4 template twins and `templates/project/project/TODO.md` |

**A — the engine change. Ruled by the Captain 2026-09-27: expose `passage_info` from the
`scripture` step**, rather than adding a `reference` step type or dropping the step. Chosen over
both because `type: scripture` already parses the reference in order to fetch the passage, so
nothing new parses and no step type is added. It is a **contract change to an existing step's
output**, which is the cost.

> **Built and COMMITTED 2026-09-27 at `c90f7a1`.** Five paths in the commit, not the four
> staged: `.git/hooks/pre-commit` regenerates `docs/index.json` and stages it, adding one line
> (`"llmflow.utils.data"`, the new import). **Expect that file to join any commit that changes
> imports under `src/` — group C's deletions will pick it up too, and there the diff is larger.**
>
> The mechanism is a **second output name**, not a key in the result:
> `output: [subject, passage_info]`. Chosen because `type: scripture` returns a **bare string**
> for `format: milestones` with an empty `include`, so a `passage_info` key would force every
> result into a dict and change the output shape of every scripture step in every project. The
> pair is returned only when a step names exactly two outputs — `src/llmflow/steps/scripture.py:71-78`.

- [x] Failing test first — `tests/test_scripture_passage_info.py`, **2 failed / 1 passed** before
      the handler changed, 3 passed after. The one that passed first is the non-regression test,
      which is the point: it pins today's behaviour before the change touches it
- [x] `passage_info` reaches the scripture step's output —
      `test_a_second_output_name_receives_the_parsed_reference`, asserting `book_code`,
      `canonical_reference`, `filename_prefix` = `01001001-01001001`, `testament`,
      `original_language` and all four versification fields
- [x] `pipeline_schema.py` and the object model agree — **no schema change was needed**: `output`
      already accepts a list. `hatch run pytest tests/test_pipeline_model.py
      tests/test_schema_covers_runner_keys.py tests/test_one_syntax.py` + all seven scripture test
      files → **200 passed**
- [x] **Existing consumers are unaffected, and that is tested rather than asserted.**
      `test_a_single_output_name_is_unchanged` proves `output: source` still binds a `str` and
      binds no `passage_info`. The change is opt-in, so `discourse-flow`'s editable install sees
      no difference until a pipeline there asks for two names
- [x] `docs/sp-language.md` documents it under `type: scripture` — a new subsection with two
      worked YAML blocks, both **linted by `test_doc_examples_lint`** (the suite's collected count
      rose by 9 because of them)
- [ ] **Lint and runtime disagree about a step's own output, found while doing this — not fixed,
      not in scope.** `handle_step_outputs` binds `output` *before* writing `saveas`
      (`step_outputs.py:39-85`), so a step naming its own output in its own `saveas` works at run
      time; the linter adds outputs to the available set only *after* checking the step
      (`linter.py:701-708`), so the same pipeline fails lint. **§5 of the plan is wrong for this
      reason** — its `english` step (2nd) names `${passage_info.filename_prefix}` while the
      `reference` step that declared it was 3rd. Declaring it on the first step fixes the example;
      the lint/runtime inconsistency is a separate defect and needs its own issue — evidence:

##### The schema declares syntax and no semantics — raised by the Captain, 2026-09-27

> `output` is declared once, in the common keys (`pipeline_schema.py:167`), as
> `_OUTPUT_TARGET = {"oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]}`.
>
> **That declaration carries syntax only. It has no `description`, no per-type constraint, and no
> upper bound. So right now:**
>
> - nothing declarative says that on a `scripture` step position 0 is the passage and position 1
>   is the parsed reference;
> - nothing says the same two-name form means something entirely different on a `function` step;
> - **`output: [a, b, c]` on a `scripture` step is schema-legal, lints clean, and silently binds
>   the text to all three names** — verified 2026-09-27:
>   `handle_step_outputs({"output": ["a","b","c"]}, "TEXT", ctx)` → `{'a': 'TEXT', 'b': 'TEXT', 'c': 'TEXT'}`.
>
> This is a `design-is-declarative` breach: *"each field says what it governs, what it forbids,
> and which ruling decided it, so a reader can act on it without reading the implementation."*
> The semantics currently live in `steps/scripture.py:71-78` and in prose, which is two encodings
> of one fact with the declaration carrying neither.
>
> **One correction to an earlier claim in this session:** adding `maxItems` to the schema would
> **not** by itself make the three-name case a lint error. Measured — `PIPELINE_SCHEMA` is
> consumed by `model.py`, `catalog.py`, `file_catalog.py` and `__init__.py`, and **not** by
> `linter.py`, which validates *which keys are legal on which type* via `allowed_step_keys()` and
> never evaluates value constraints. Nothing validates a pipeline against the schema as JSON
> Schema. So declaring and enforcing are two separate pieces of work.

> ⛔ **The three items below are SUPERSEDED, 2026-09-28.** The Captain preferred named outputs to
> positional — *"I prefer named parameters if this is possible… named parameters, perhaps even
> typed, will be more robust"* — and added that the same names should key the result object.
> Patching the positional form with `maxItems` and a lint arity check would be building the thing
> we have decided to replace. **They are kept, struck, so nobody re-derives them.**

- [x] ~~**Declare it** — `maxItems: 2` and a `description` on the `scripture` branch.~~ Superseded
      by the design below; a per-type constraint on a positional form we are replacing is wasted work
- [x] ~~**Enforce it** — lint refusing three or more names.~~ Superseded: arity falls out of
      declared members for free, and needs no special-case check
- [x] ~~**Decide whether per-type output semantics belong in the schema generally.**~~ **Answered**,
      and the answer changed the design: the vocabulary **already exists**, declared per step type
      as the `returns:` enum — `alignment` offers `["text", "alignments"]`
      (`pipeline_schema.py:319-322`), `parallel-passages` offers `["references", "words"]`
      (`:344-347`), `scripture` declares none. So this is connecting two halves rather than
      inventing a mechanism

**A‴ — named step outputs. Written up 2026-09-28 on the Captain's instruction.**

- [x] **Design document** — `project/plans/design-named-step-outputs.md`,
      `Status: proposed (2026-09-28)`, five decisions as `=>` slots. **`proposed` is not
      authorization to build**
- [x] **Issue body drafted** — `tmp/issue-named-step-outputs.md`. **Not filed**;
      `issues-need-approval` requires the Captain to read the body and create it. Written for an
      outsider: no `=>` slots, no session vocabulary — `write-shared-records-for-outsiders`
- [x] **Static checking reconsidered, and the earlier claim corrected.** On 2026-09-27 an AI said
      types "could not be checked at lint time". Wrong: that confused checking a *value* with
      checking a *declared name*. Member existence, member-was-requested and arity are **fully
      static**; a field access is static where the member's shape is declared; only the runtime
      value type is not, and that belongs at bind time. Recorded in §4 of the design rather than
      quietly fixed
- [x] **Filed as → #263**, 2026-09-28, on the Captain's instruction and with the body reviewed
      first. No `=>` slots and no session vocabulary in it —
      `write-shared-records-for-outsiders`; verified by grep before posting
- [x] **Drafts deleted by name** — `tmp/issue-named-step-outputs.md` and `tmp/issue-body.md`.
      `project/upstream/Clear-Bible-Alignments/issue-hin-roles.md` is another session's and was left
- [x] **Two of the five decisions are RULED** (2026-09-28), moved verbatim into the design's `=>`
      slots from the issue draft the Captain answered in: **naming a member in `output:` is
      requesting it**, a caller may request a subset; and **#244's example waits for this design**
- [x] **All five decisions are ruled**, and this entry said otherwise until 2026-09-29 — corrected
      against the document's own `=>` slots, which are the authority. **D3's rename syntax settled
      four at once**: `returns: [text-bsb=text, reference]`, left of `=` the pipeline's variable and
      right the step's member. D1 is **dissolved** — there is no mapping with two sides, only a list
      with an optional rename inside an entry. **D2 is ruled A** — *"Yes, A of course"* — a bare
      output name binds the **primary member**, so `${subject}` stays a string and no existing
      pipeline changes; the cost is that every step type with more than one member must declare
      which is primary, beside the members in `_STEP_TYPE_PROPERTIES`. D2′'s collision objection is
      met, because either of two `scripture` steps may rename. D4: one key, not two
- [x] **#263 IS IMPLEMENTED — `3d6c8c5`, 2026-09-28**, *"feat(language): a step's outputs are named
      members, not positions"*, an ancestor of HEAD. `hatch run pytest tests/test_named_step_outputs.py
      -q -p no:randomly` → **7 passed**. `pipelines/commentary.yaml:44` uses the ruled syntax —
      `output: [subject=text, passage_info=reference]` — and lints clean.
      ⚠️ **This file, `HANDOFF.md` and the design document all said it was unbuilt**, and a session
      on 2026-09-29 repeated that to the Captain three times before checking `git log`. The claim
      was never measured; it was copied forward. **The check that settles it is one command against
      the path, not a reading of the queue**
- [ ] **The hyphen residual at `design-named-step-outputs.md:389` was decided in code, not in the
      slot** — the slot is still empty, and the implementation took option 1: variable names stay
      `[A-Za-z_][A-Za-z0-9_]*`, which is why the example reads `passage_info=reference` and not a
      hyphenated name. Hyphenated names still **fail silently** — `resolve("${text-bsb}", …)`
      returns the literal — so the choice is real and unrecorded. **#240 points the other way for
      key names.** Either the Captain writes the slot to match what shipped, or the discrepancy
      stands as an undeclared decision — evidence:
- [ ] **The design still declares `Status: proposed` and "Nothing here is implemented", and both
      are false** — `3d6c8c5` shipped it. `proposed` is never authorization to build, so a document
      reading `proposed` beside a shipped feature says either that the status was never updated or
      that something was built without authorization; nothing in the file distinguishes those, and
      the next reader cannot tell. **The Captain's to set** — `ruled`, with the date the
      implementation landed — evidence:

**A′ — the CLI API must carry this too.** Raised by the Captain 2026-09-27. Rule
`the-language-is-the-whole-surface`: a project reaches the engine through the `sp` command line
and the pipeline language, so a semantic the command line cannot express or report is a semantic
a project does not have.

> 🔄 **Re-read against the #263 ruling, 2026-09-29.** These boxes were written for the
> **two-name positional** `output:` form. D2 and D3 replaced that with named members and an
> optional rename, so what each box asks for has changed even where the box is still worth doing.
> Restated below rather than left to be worked as written; two were struck.

- [ ] **`PIPELINE_SCHEMA` surfaces the member list and which member is primary** — restated
      2026-09-29. It was *"a `description` added above must reach a caller of `api_catalog()`"*,
      which is doubly wrong now: the thing that must reach a caller is the **declared members and
      the primary one**, not a positional description; and `api_catalog()` is the wrong vehicle —
      the box four rows above already records that it catalogues the *Python API's verbs*, the
      surface a project must not build against. `sp help step-types` derives from `PIPELINE_SCHEMA`
      instead — evidence:
- [x] ~~**`sp lint` says something useful** about a two-name `scripture` output, and something
      actionable about three.~~ **Struck 2026-09-29 — obsolete as posed.** Arity was already
      recorded as falling out of declared members for free, needing no special-case check. Under
      named members there is no "two-name versus three-name" case to report on: lint's job is
      refusing a member name the step does not declare. That is the next box, not this one
- [ ] **`sp lint` refuses an undeclared member name** and names it, the way it already names an
      unknown variable — the non-regression that matters, since requesting a subset is legal and
      only an *unknown* member is an error — evidence:
- [ ] **Check whether any `sp` command's output or help text changes.**
      `tests/test_cli_is_documented.py` fails in both directions when the parser and
      `docs/ai-context/sp/command-line.md` disagree, so if nothing changes, say so and record that
      it was checked rather than leaving it unexamined — evidence:
- [ ] **`docs/python-api.md`** — the engine's own surface, documented for work in this repository.
      Does `.schemas()` or the `Step` view need to say anything about **the member list**? —
      restated 2026-09-29; it read *"about the pair"*, which named the positional two-name form —
      evidence:

**A″ — the AI context, which is documentation for humans *and* LLMs.** The Captain, 2026-09-27:
*"these semantics are then specific to the step type and must be clearly documented in the ai
context."* The risk this addresses is a model carrying the `scripture` rule to another step type.

- [x] `docs/sp-language.md` — new subsection under `type: scripture`, two worked YAML blocks,
      both linted by `test_doc_examples_lint` (the suite's collected count rose by 9 for them).
      **Committed `c90f7a1`**
- [x] **The shipped quickref template** —
      `src/llmflow/templates/project/docs/llmflow-language-quickref.md:285`. States the two-name
      form, the field list, that `versification:` feeds the parse, and the three rules that bite:
      order decides meaning not the names; declare on an earlier step than the one that uses it;
      one name behaves exactly as before. **Committed `c90f7a1`**
- [x] ~~**State the general principle where it cannot be missed** — that `output:` as a list is
      positional and what each position means is decided by the step type.~~ **Struck 2026-09-29 —
      the principle is false under the ruling.** The list is no longer positional: it names members,
      each optionally renamed with `=`, so order carries no meaning at all. Documenting it as
      positional would teach the form being replaced. **What replaces it is the next box**
- [ ] **State the general principle where it cannot be missed** — that `output:`/`returns:` as a
      list **names members**, that a bare name binds that member under its own name, that `=`
      renames, and that **which members exist and which is primary is declared per step type**. The
      risk is unchanged from the Captain's 2026-09-27 framing — a model carrying one step type's
      member vocabulary to another — evidence:
- [ ] **`docs/ai-context/project/data-shapes.md`** already documents `passage_info` as
      `parse_bible_reference`'s return. It should say the `scripture` step produces it too, **under
      the member name the ruling gives it** rather than as a second output position, or a reader
      concludes the function is the only route — evidence:
- [ ] **The rendered `docs/llmflow-language-quickref.md` regenerates** — it is `generated`, so it
      is not hand-edited; `sp init --update` refreshes it. It is already named by
      `test_template_layout` among the three stale copies, so this adds no new failure — evidence:
- [ ] **Document in the AI context what the schema actually is, and what validates what.** Raised
      by the Captain 2026-09-27. This is the fact a session most reliably gets wrong — I got it
      wrong in this very session, claiming a `maxItems` would make lint fail. What has to be
      written down, because none of it is currently stated anywhere a session reads:
      **`PIPELINE_SCHEMA` is a key vocabulary, not a validator**; it drives `Step`'s attribute set
      in `model.py`, `allowed_step_keys()` for *which keys are legal on which type*, and
      `api_catalog()`; **nothing validates a pipeline against it as JSON Schema**, so a value
      constraint written there documents intent and enforces nothing; and **`output:` as a list
      names declared members, not positions** (corrected 2026-09-29 — this clause said "positional,
      with each position's meaning decided by the step type", which the #263 ruling made false).
      Home is
      `docs/ai-context/project/` — this is engine-internal, and `sp/` is generated. A new topic
      document needs a row in `project/index.md` — evidence:
- [ ] **Document the CLI API's part in the AI context too**, per `the-language-is-the-whole-surface`:
      which semantics a project can reach from the `sp` command line and the pipeline language,
      and which live only in the engine's own Python surface. A reader who cannot tell the two
      apart builds against a contract nobody offered — evidence:

- [x] ⚠️ **A stale claim survived a fix that was recorded as complete — found, fixed and
      committed at `c90f7a1`.** Restored to this file 2026-09-27 after being deleted from it the
      same day. The entry said `docs/sp-language.md:802,961` claimed `include:` was *"valid
      only with `format: usj`"* and that the fix had landed. It had, **in that file only**.
      `grep -rn "valid only with"` found it still live in **the shipped quickref and its
      template**, which is the copy every project reads. The template is fixed; the rendered copy
      regenerates with `sp init --update`. **The lesson is the one this audit exists for: a fix
      verified in one file is not a fix, when the fact is rendered into several.**

**B — the example itself.** One pipeline, one prompt: D2 ruled *"no more complexity than is needed
for the task"*.

- [x] `pipelines/commentary.yaml` — **four** steps, not five: the separate `reference` step is
      gone, absorbed into `scripture`'s members, so **three of four call no model** rather than
      four of five. `${passage}` is named in every step and there is no default.
      `hatch run sp lint --pipeline pipelines/commentary.yaml` → **✅ Pipeline OK**, zero warnings
- [x] **The output semantics are recorded in the example pipeline itself**, in `description:`
      block scalars as ruled — the list form, that members are decided by the step type and do
      not carry to a `function` step, and why `passage_info` is declared on the first step.
      Originally stated as Set by the Captain 2026-09-27. The example is what a reader copies, so a semantic
      that lives only in the language reference does not travel with the thing being copied. It
      It says — corrected 2026-09-29, this having been the **third** copy of the superseded
      positional claim in this file — that the list form **names members and is positional in
      neither sense**, `variable=member` renaming one; that what the members *are* is decided by the
      step type, so it does not carry to a `function` step; and that `passage_info` is declared on
      an **earlier** step than the one whose `saveas` names it, because a step's own `saveas` cannot
      see its own output. **Verified against the file, not recalled**: `pipelines/commentary.yaml`
      lines 28-38 and `output: [subject=text, passage_info=reference]` at line 44
  - [x] **Ruled by the Captain 2026-09-27: use `description:`** — *"sure, use description, that's
        better."* So the output semantics go in a `description: |` block scalar and short `#`
        notes stay for one-line labels, which is what `~/.sp/disciplines/llmflow-pipeline-steps.md`
        already requires — *"all step documentation belongs in `description`"*, `#` being reserved
        for *"short inline notes and section dividers only"*. No divergence from the discipline to
        record. This matters beyond style: the example ships as the worked demonstration of how a
        step is documented, so whatever it does is what every project copies
- [x] `prompts/commentary.gpt` conforms to `data/prompt-structure.yaml` — twelve positions, four
      subsections in each of its two task sections, an ❌ counterexample in each (C3). **It is the
      first prompt in this repository to conform**: `sp lint` warns on `prompts/hello.gpt` at
      position 2 and produces **zero** warnings on this one, so the check is live and the prompt
      passes it rather than the check being absent
- [x] `sp lint --pipeline pipelines/commentary.yaml` is **silent** — 0 warnings, verified against
      `hello.yaml` warning as a control
- [x] `--dry-run` resolves every path and variable and names the four steps in order —
      `subject`, `english`, `parallels` (all free), then `commentary`. Run with
      `--var passage="MRK 1:1-8"`; calls no model and writes nothing
- [x] **The prompt is approved.** The Captain, 2026-09-28: *"the prompt looks good."* That covers
      `prompts/commentary.gpt` and the eleven ❌ counterexamples in it, which are the examples
      that teach a model on every run.
- [ ] **§6's sample output in the plan is still unreviewed** — a plan document, read by nobody at
      run time, so it ships nothing. Review it only if the drafted commentary itself is wanted —
      evidence:

**C — the removal (D3: *"drop these"*).** One pass, `one-design`: nothing half-migrated.

- [x] 12 files deleted from `pipelines/` and `prompts/` — the four starters plus their eight
      `-view.md` / `.html` companions
- [x] 4 template twins deleted; **2 added** — `templates/project/pipelines/commentary.yaml` and
      `templates/project/prompts/commentary.gpt`
- [x] `data/file-catalog.yaml` — four `policy: example` rows replaced by two, with the reason
      the hello pair was dropped recorded on the row rather than lost
- [x] **`cli.py` and `cli_utils.py` no longer name the starter files.** The one the plan missed:
      `HELLO_PROMPT`/`HELLO_REPLY_PROMPT`/`HELLO_YAML`/`HELLO_PIPELINE` → `COMMENTARY_PIPELINE`
      and `COMMENTARY_PROMPT`; `_EXAMPLE_PATHS` rewritten; two docstrings and a `--help` string.
      Deleting to the plan would have left `tests/test_init.py` unimportable, which is exactly
      what happened until these were fixed
- [x] 2 test files updated, not 3. `tests/test_init.py` substantially rewritten — **43 passed**;
      `tests/test_linter.py` points at the shipped prompt — 7 passed.
      `tests/test_windows_encoding.py` needed **no** change: its `hello.gpt` is a throwaway
      fixture name in `tmp_path`, not the shipped file. The estimate counted a grep hit
- [x] Docs updated at their sources, then regenerated: `docs/tutorial.md` **rewritten** for the
      new example; the quickref and `command-line.md` templates; and **`data/ai-rules.yaml`,
      where rule `cite-paths` used the deleted files as its own example of a good citation**
- [x] `sp/index.md` regenerated from the catalog and names the new example —
      `hatch run sp init --update`

**D — the gates, run and quoted.**

- [ ] §7's eleven acceptance tests, each ticked with its evidence — evidence:
- [ ] Full suite, not a subset: `hatch run pytest tests/ -q -m "not integration" -p no:randomly`,
      with the count and every failure named — evidence:
- [ ] `CHANGELOG.md` entry — evidence:

**E — what only the Captain can do.** None of these is an AI's to assume.

- [x] **Prompt approved 2026-09-28** — *"the prompt looks good."*
- [ ] **§6's sample output** in the plan, if it is wanted at all — it ships nothing
- [ ] **Direct the `sp run`** that proves the example end to end. It calls a model and costs money;
      no prior run authorizes a later one
- [ ] **Rule the ordering with #242's conformance check** — it ships with this example or waits
      for it. Recorded under 0.2.1.28 below and not reopened here
- [ ] `sp lint`'s prompt-conformance check ships with the new example or waits for it — the
      ordering constraint recorded under 0.2.1.28 below, unchanged

### 🔁 SECOND — #255, `sp tools replay` cannot align multi-line variables

> **Placed second by the Captain 2026-09-26**, behind the examples.

**Nothing is implemented.** Verified 2026-09-26: the line-count refusal is present on `dev`,
`origin/dev` and `main` at `src/llmflow/tools/replay.py:50`, and none of the three affected files
has working-tree changes.

- [x] `recover_var_map` aligns on variable sites rather than line counts. One pattern over the
      whole prompt — literals escaped, each variable a capture group, `DOTALL`, `fullmatch` — so
      a multi-line value is no different from a single-line one
- [x] **This prediction was wrong, in the safe direction.** `test_line_count_mismatch_raises`
      did **not** need to change: its case — no variables, unequal text — is still refused, now
      because the literals do not match rather than because the line counts differ. All 23
      existing replay tests pass untouched
- [x] `tests/test_replay_multiline_values.py` — 14 tests, **7 red first**: multi-line JSON, two
      multi-line values, regex metacharacters in a value, an empty value, a variable at the very
      end, a repeated variable, adjacent variables refused, and a round trip through `render`
- [x] **The shipped caveat is corrected**, and it mattered most of the five: it told every
      project *"if the line counts differ, replay refuses"*, which is the sentence that would
      stop a reader trying again. Template fixed and the rendered copy regenerated. Sending a
      collab saying "fixed" while the document in their own tree described the bug would have
      been the fourth instance this week of a claim fixed in one file and alive in another
- [x] **Explicitly deferred to #243 Part 3, in the error message.** Replay is handed a prompt and
      a capture and never sees the pipeline, so it *cannot* read a step's `response_format`
      without a new argument. The message now says what was looked at, what was not, why adding
      the frontmatter key is harmless, and where the real fallback belongs

> **#176 lands on this, and neither issue says so.** Replay aligns the `.gpt` file against a
> captured request. If #176 strips the frontmatter at render time, the capture
> (`steps/llm.py:232`) shortens while `--prompt` is still the whole file, so every replay
> mismatches by the frontmatter's length and the fix must strip the header from `--prompt` too. If
> #176 strips only at the call site, captures are unaffected. Which it is, is open inside #176.
> Settle that before building the alignment, or build it to strip either way.

### 🔤 THIRD — the three variable mechanisms: CLI tests, lint tests, and documentation

> **Set by the Captain 2026-09-26:** *"we need cli-level tests to ensure all three mechanisms work
> … we need to make sure this is well documented in the ai context … the tests should also cover
> lint."*

**The three mechanisms, each measured 2026-09-26:**

1. **A `--var` reaches steps without being declared anywhere.** The value enters the *context*;
   `variables:` is one contributor to it, not a gate. Measured: `r.variables` stayed
   `{'output_dir': 'outputs'}` while `step.content` resolved to `MRK 1:6`.
2. **A self-referential declaration, `passage: "${passage}"`.** Functionally inert — the `--var`
   value replaces it. With no `--var` it leaves the literal `${passage}` in place.
3. **Derived variables inside `variables:`**, resolved transitively before any step runs.
   `derived: "ref=${passage}"` became `ref=MRK 1:6`.

**Existing coverage, checked rather than assumed:**

- `tests/test_linter_variable_validation.py:585` `test_var_supplied_variables_are_available` — 1,
  at lint level only
- `tests/test_resolve_derived_variables.py` — 3
- **2 has no test anywhere**, and appears in `pipelines/storyflow-psalms.yaml` and the complete
  example in `docs/sp-language.md` unexplained
- **nothing exercises any of the three through the CLI** — `main(["run", …])` — so no test proves
  a `--var` reaches a step's written output end to end

- [ ] CLI-level tests for all three, through `main([...])`, using native steps only so no model is
      called. `tests/test_doctor.py` is the precedent for driving `main()`
- [ ] **Lint bug found while measuring: `content:` and `path:` on a `save` step are not scanned for
      undefined variables**, although they are that step type's own required fields. `saveas:` and
      `inputs:` are scanned and error correctly. Fix the field list, then test all four
- [ ] Decide whether an unused `requires:` entry is an error or a warning — the reverse-direction
      check that is still missing, already recorded further down this file
- [ ] **→ #257, filed 2026-09-26: a pipeline cannot declare a required input.** The root cause
      under mechanisms 1 and 2 and under the lint inconsistency. Four open questions in it, the
      first being the key's name. Not scheduled here; the examples do not wait for it
- [ ] Document all three in the shipped AI context. The home is
      `src/llmflow/templates/project/docs/llmflow-language-quickref.md` §2, which already has a
      variables section and is catalogued at `data/file-catalog.yaml:206`; the full statement goes
      in `docs/sp-language.md`. **Not the rendered copies** — those are regenerated
- [ ] Say in that documentation which idiom is recommended and which are advanced, since the
      starter example teaches only explicit variable reference as a step input (2026-09-26)

### 🧰 `/stage-commits` — written, NOT installed, and not invocable by anyone (2026-09-27)

> **Set by the Captain 2026-09-25.** *"a skill that means 'stage the outstanding commits, and show
> me the strings needed to commit them.' It should use universal shell syntax, so that it is
> compatible with .zsh, bash, and any commonly used linux shell."* Named `/stage-commits` the same
> day. **Placed first**, which was *"perhaps first"* — move it if that is wrong.

**Why first.** This is rule `commit-authority` made mechanical — *"an agent runs the gates, writes
the commit message to a file, and hands over the exact command."* Nothing implements that today, so
every session ends with an assistant listing paths in prose and a human retyping them. The session
that set this goal ended with **15 changed files and 2 new ones** needing exactly that treatment.
It is small, and it is the only goal whose absence is paid for at the end of every other one.

**The boundary with `commit-ready`, so this is not a second design.** `commit-ready` is the gate —
issue, TDD, suite, CHANGELOG, message format, Actions, merge. It decides *whether* a commit may
happen and *what the message must contain*. `/stage-commits` is the mechanism: it stages the paths
and hands over a runnable command. It **checks nothing** `commit-ready` checks, and points at it
rather than repeating it.

**Universal shell syntax — what that rules out.** The requirement is real rather than stylistic;
these differ between `zsh` and `bash` today:

- **`git commit -F <file>`, never `-m "…"`.** A message containing a quote, a backtick or a `$`
  is the thing that breaks, and it breaks *differently* in each shell. A message file sidesteps
  quoting entirely, and `commit-authority` already asks for the message to be written to a file.
- **Quote every path.** `zsh` does not word-split an unquoted variable; `bash` does. An unquoted
  path with a space behaves differently in each.
- **`printf`, not `echo -e`** — `echo`'s flag handling is not portable.
- **No `[[ ]]`, no `(( ))`, no arrays, no `+=`, no process substitution.** POSIX `sh` only, and
  `#!/bin/sh` on anything emitted as a script.

**The landmines it exists to avoid** — all of them have already happened in this repository:

- **Never `git add -A` or `-a`.** `gui/frontend/node_modules` is tracked, ~8,000 files, and a
  sweep commits their deletion.
- **`git add` aborts the entire command on an unmatched pathspec and stages nothing** — but if an
  earlier `git mv` already staged something, the commit still succeeds carrying a message that
  describes work it does not contain.
- **A renamed file needs both halves named**, or history does not follow.
- **Another party's uncommitted work sits in the same tree.** This session's did. The skill
  **cannot infer** whose a change is, so it groups and asks rather than guessing.
- **`git show --stat HEAD` afterwards**, with the file count checked against the intended list.

> ⚠️ **Corrected 2026-09-27: this was reported as built and the skill cannot be invoked by
> anyone.** The template exists and `~/.sp/skills/stage-commits/` exists, but
> **`.claude/skills/stage-commits/` is absent** — both in this repository and in `~/.claude/`.
> That is the directory Claude Code actually reads (`docs/ai-context/sp/command-line.md`), so
> `/stage-commits` does not appear in any session's skill list. Measured with `find` over all
> four stores, 2026-09-27.

- [x] **Built 2026-09-25 → #253.** `src/llmflow/templates/sp/skills/stage-commits/SKILL.md`, with
      `tests/test_stage_commits_is_portable.py` written first and red before it existed —
      **17 passed** after (16 when this line was written; a test was added since). The test reads
      the shipped template and refuses `[[ ]]`, `(( ))`, arrays, `+=`, process substitution,
      `echo -e`, `$'…'` and `&>`, plus `git add -A`, `git commit -m`, and `git push`/`git merge`
      as instructions
- [x] **Ruled: several commits, grouped by concern, and it asks before staging.** Nothing in
      `git status` says whose a change is, so grouping is presented rather than guessed
- [x] **Ruled: it does not run `commit-ready`'s gates.** That skill is the gate, this is the
      mechanism; it points rather than re-checking. `one-design`
- [x] **Ruled: it writes nothing but message files, all under `./tmp`, deleted by name once the
      commit exists.** It reports whether the changelog and handoff are in the staged set and
      points at their owning skills rather than writing either — a third writer would be two
      encodings of one fact
- [x] **Ruled: `git show --stat HEAD` once a commit exists**, because "committed" is not evidence
      that the commit holds what the message claims

**What remains, one line per step, each checked against the tree on 2026-09-27:**

- [x] **`~/.sp/skills/stage-commits/` is present.** This arrived at some point after the item
      below was written; the item claimed both destinations were blocked and only one was
- [x] **`.claude/skills/stage-commits/` is now present** — `hatch run sp init --update` installed
      **12 skills**, `stage-commits` among them, and it appears in a session's skill list. The
      finding was correct and the remedy was the command nobody had run
- [ ] **`~/.claude/skills/stage-commits/` is still absent.** The project store is fixed; the
      machine-wide one is not, and that directory is the Captain's — evidence:
- [x] **The route was `sp init --update`, not `sp doctor`** (#210), exactly as
      `data/file-catalog.yaml:52` and `:75` implied — the glob already covered it

> ⚠️ **Running `sp init --update` here overwrote this repository's own `docs/ai-context/sp/rules.md`
> with the consumer-project variant.** Two generators write that one file and they disagree:
> `sp init` emits `<!-- Generated by sp init -->` / `# AI Assistant Rules for This Repo`, while
> `tools/update_ai_context.py` emits `<!-- Generated by tools/update_ai_context.py -->` /
> `# AI Assistant Rules`. Caught by `test_ai_rules_single_source` and repaired by re-running the
> generator. **This is the hazard #210 names, still live**, and it is two encodings of one file —
> `design-is-declarative`. Worth its own issue — evidence:
- [ ] **`tests/test_stage_commits_checks_the_handoff.py` is untracked** — 3 tests that exist in
      the working tree and in no commit. `git status` lists it under `??`. Either commit it or
      say why it should go
- [ ] **`tests/test_portable_skills.py::test_every_shipped_skill_is_classified` is red because
      of this skill** — confirmed in the 2026-09-27 suite run. It is unclassified, and the
      classification is **S1 in `project/open-decisions.md`**, an unanswered `=>`. `ENGINE_ONLY`
      passes mechanically and is false; `SHARED_WITH_HELM` costs a Helm commit and a
      `data/helm-sync.yaml` row. **The Captain's ruling, and it is what blocks a green suite**
- [ ] **Verify after installing** — `/stage-commits` appears in a fresh session's skill list.
      Nothing else proves it; the tests read the template, not the installed copy

### 🎯 THE GOAL — #246, #247, #248, all for discourse-flow

> **Set by the Captain 2026-09-22.** Three issues, filed this session, and they come before
> everything else in this list. Told to discourse-flow in
> `discourse-flow/collab/sp/2026-09-22-segment-text-landed-and-the-windowing-ask-is-ruled.md`.

- [x] **#246 — three defects in token windowing. Committed to `dev` at `500601b`; closes at the
      release.** Work order: `project/plans/plan-window-token-defects.md`. Partiality decided by
      position rather than fill; `include_partial` accepted and ignored under `!window_advance`
      (**ruled A — honour it**); the tiktoken counter written twice
- [x] **#247 — a truncated response is reported as malformed JSON, then retried three times
      identically. Committed to `dev` at `6f9840b`; closes at the release.** The budget that
      actually breaks a run is the *output* one, and no input-side counting predicts it. Reads
      the provider's stop reason across five provider shapes, reports the step and the budget,
      stops retrying a certainty, and names the ceiling — `min(max_output_tokens,
      max_context_tokens − prompt_tokens)`, derived from `data/models.json`, never a guessed
      number. Also: a step near its budget is recorded in the defect log, and
      `generate_optimization_suggestions` — which had no caller anywhere — now reaches the
      operator. **`ModerationError` is still retried three times** by the same bare
      `except Exception`; same defect, different condition, and the Captain's call
- [ ] **#248 — `--rewind-to` cannot resume a loop.** `append_to` is refused outright
      (`utils/rewind.py:77-88`), which is how every accumulating loop stores results, so a
      book run that dies in window 8 of 13 restarts at window 1. **D1, D2 and D4 were ruled
      earlier; D3a was ruled 2026-09-25** — each finished iteration is appended to a temporary
      TOML while the run is going, and reassembled into the canonical JSON manifest at the end.
      The durable artifact stays JSON. **The issue is the plan**, ruled 2026-09-25; there is no
      plan file and none is wanted → #248. The concurrency half is #249's and is unfixed
  - [x] **Recorded in `CHANGELOG.md`** under Unreleased → Ruled, 2026-09-25, with what it does not
        settle named beside it. **Ignore the `=>` markers in #248's body** —
        `write-shared-records-for-outsiders` says that device does not belong in an issue, so an
        empty one there is not an open question; slots live in `project/open-decisions.md` and
        `project/plans/`
  - [ ] **D1's answer was conditional** — *"ideally, we want to resume a partial loop, but if we
        cannot do that reliably, then we do what is possible."* A per-iteration record is what
        "reliably" was waiting on, so D3a probably settles D1 in favour of partial resume.
        **Confirm rather than assume**
  - [ ] **Appending from several iterations at once is #249's problem, not solved here.** TOML
        appends cleanly for one writer; parallel iterations appending to one file still need
        something to stop the writes interleaving
- [ ] **#249 — `parallel:` is filed and NOT scheduled.** Tested only with `type: function`
      steps, while `telemetry.start_step` is called only from `steps/llm.py` and
      `steps/duckdb.py` — so no test has ever run a telemetry-recording step inside a parallel
      loop, and the single `current_step` slot loses records and misattributes tokens silently.
      Read from code, not from a red test

> **The scripture-window design is ruled and is no longer about windowing.** Retitled and renamed
> to `project/plans/design-usj-operations.md` — D1-D4 answered: no new step type,
> `window` has no idea what a verse sid is, and the three operations become **USJ operations**
> (flatten, locate, rebuild), grouped and open for more. Reassemble stays discourse-flow's. D3c
> is open and its framing is stale — see the note in that document.

### 🎯 NEXT AFTER THE GOAL — #243, the prompt data contract

> **Set by the Captain 2026-09-23:** *"add this next after the current set of goals."*
> → #243. Raised from discourse-flow; full report in
> `collab/discourse-flow/2026-09-18-a-prompt-cannot-name-the-schema-its-step-is-wired-to.md`.
> Nothing is blocked there — the pipeline runs and lints clean, and both stale paths are
> fixable by hand. What cannot be built without the engine is the **guarantee** that they
> cannot come back.

**⚠️ The issue names two different things as first. The order is the Captain's.**
Part 2 is *"the half we would fix first"*; Part 3's one field is *"useful ahead of
everything else here."* Both are cheap; they are not the same work.

- [ ] **Part 2 — a prompt's input paths are unchecked, and a stale path is silent.** A prompt
      says where its data is; when the producer moves the key the model finds nothing, fills
      the gap from training, and returns something plausible with nothing recording that the
      input was never read. Two live instances, both real. Makes the `## Input` table
      checkable: `sp lint` for the variable column against `prompt.inputs`, and a path lookup
      **at render, before the call** — so it fails before money is spent, not after a
      plausible answer comes back
- [ ] **Part 3 — `schema_file` in the debug manifest.** A capture cannot today answer which
      schema a call was made against: `grep -c json_schema` on a request capture returns 0.
      One field, and it gives `sp tools replay` its resolution path
- [ ] **Part 1 — the runner substitutes the step's resolved schema into the prompt.** One
      prompt is wired to **three** different schemas in discourse-flow, so which schema applies
      is a property of the step, not the prompt — which is why neither frontmatter nor a mixin
      can be right, and why only the engine can guarantee the two agree. Builds on
      `Pipeline.schemas()` (`model.py:223`)
- [ ] **Design it once with #177's unticked roadmap item** — *"Schema-driven `--show`"*, sitting
      unticked under an issue closed COMPLETED. It needs the same missing capability

### 🤝 THE NEW GOAL — refactoring how we work with Human at the Helm

> ⛔ **Taken out of the next release by the Captain, 2026-10-01:** *"Let's take Helm parity out of
> this release."* `tests/test_helm_sync.py` stays red (3 failures) until the coordination design
> lands; whether the release ships with those known failures or an exemption is still his call.
>
> **Set by the Captain 2026-09-25**, for the next release, alongside the goals above. **Both
> halves are in scope:** Helm adopting sp's idioms and installing into paratext-copilot — the
> section below, unchanged — **and how the two repositories share files at all.**

**Why it is a goal and not a tidy-up.** Two incidents in two days, both the same shape — a Helm
session editing this tree directly:

- **2026-09-23** — three files: the two shared disciplines plus `data/helm-sync.yaml`, leaving
  `tests/test_helm_sync.py` red. **Resolved:** the content was kept and committed at `473cd80`,
  and the suite is green — 82 passed, re-run 2026-09-25. The collab note reporting it is
  `collab/human-at-the-helm/2026-09-23-a-helm-session-left-three-files-changed-here-and-two-tests-red.md`,
  which is **spent and untracked** — untracked being what the convention that same note
  introduced forbids
- **2026-09-24** — seven files: `data/helm-sync.yaml` and six `templates/sp/skills/*/SKILL.md`,
  stripping the `**WORKFLOW SKILL** —` prefix from each description. **Still in the working
  tree.** Left in place deliberately so 0.2.1.28 could ship; that release is out, so the reason
  has expired. Recorded in `project/HANDOFF.md` and in no issue

**Ruled: Helm communicates by collab note in future rather than by editing this tree.**

**The sharing mechanism is the other half of the goal.** Shared files are tracked by sha256 in
`data/helm-sync.yaml`, so an edit on one side turns the other side's suite red — and so does
reverting one side alone. Every fix is a twin commit across two repositories, which is why both
incidents above ended in a tree nobody could clean unilaterally.

#### ⛔ Coordination between Helm and Scripture Pipelines has no design, and the old one is obsolete

> **Set by the Captain 2026-09-27**, in his words: *"coordination with HELM is its own TODO. we
> do not yet have a plan for coordination shared between Helm and Scripture Pipelines, and we
> need to design it."* And: *"The old design is obsolete."*
>
> **This blocks every cross-repository act, and it is why S1 below could be ruled but not
> delivered.** Nothing should be synced, hashed or twin-committed until the design exists.

- [ ] **Design how the two repositories coordinate.** No plan file yet; propose a name and get
      sign-off before writing one. `plans-are-temporary` applies to it
- [ ] **`project/plans/design-helm-parity.md` is obsolete** (45 KB, 2026-09-10). It is still
      cited as live in two places that will mislead the next session:
      `tests/test_portable_skills.py:49` names its §4 as *"Source of truth for this list"*, and
      `project/plans/README.md` lists it as *"awaiting the Captain's review"*. Neither says
      obsolete. Retiring it is the Captain's act
- [ ] **Helm already has a draft nobody here has read** —
      `human-at-the-helm/project/plans/design-coordinating-changes-with-sp.md`, **untracked** in
      that tree as of 2026-09-27. Read it before designing anything, so this is not designed
      twice
- [ ] **The Helm tree is mid-flight and must not be written to.** Measured 2026-09-27: `main`
      **6 commits ahead of `origin/main`**, nine modified files — including *all six* currently
      shared skills — two of them staged-and-modified, and five untracked paths. Any
      `tools/sync_helm.py --apply` now would record hashes against somebody's unreviewed work,
      which is the failure mode `disciplines/README.md` warns about in as many words

**The problem is already written down. Read these two before designing anything:**

`collab/human-at-the-helm/2026-09-23-a-helm-session-left-three-files-changed-here-and-two-tests-red.md`
names the mechanism that fails: both sides edited, the record was refreshed with
`--apply`, **the Helm side was reverted and this side was not**, so the record carried hashes for
text that existed in one tree only. Its own diagnosis is the sentence to design against — the
session *"did not treat this repository's green suite as part of the definition of done for work
that touched it."*

`human-at-the-helm/project/plans/design-coordinating-changes-with-sp.md`,
`Status: proposed (2026-09-25)`, **untracked in their tree**, proposes seven changes — a shared
file changes in one repository per act; a third record status `pending`; the check compares
**committed** state; polarity follows ownership; Helm carries its own record and check; neither
side writes in the other except into `collab/`; the second half of a twin edit is its own act.

- [ ] **Answer the six questions Helm has addressed to us.** They are in §"What we ask Scripture
      Pipelines" of that document and every one lands in *our* tree. **All six are the Captain's:**
      1. does one-side-at-a-time work from upstream, when upstream is normally ahead;
      2. who holds the record — a copy each is the very drift this exercise exists to prevent;
      3. do we accept a `pending` status in `data/helm-sync.yaml` and in `tools/sync_helm.py`;
      4. do we make the check compare committed state rather than the working tree —
         **their evidence is that it currently reports green across two dirty trees, and this
         repository's 2026-09-27 state reproduces it exactly**;
      5. do we accept the symmetric write restriction, `collab/` only, never committing there;
      6. where do Helm's own tests live, given they have no suite and ship only markdown
- [ ] **Reply as a collab note into their tree**, once answered — `plans-are-temporary` and
      `workflow.md`'s one carve-out: one new file in their `collab/sp/`, not committed there
- [ ] **Dispose of the spent inbound note.** The 09-23 note says *"This note dies with whichever
      choice is made"*; the choice was made — content kept, committed at `473cd80`. It is still
      here and still **untracked**, which the very convention it delivered forbids. Commit then
      delete, or delete. **The deletion is the Captain's**

**S1 is ruled and cannot be delivered yet.** The Captain, 2026-09-27, answering
`project/open-decisions.md` S1 — *does Human at the Helm get `/stage-commits`?* — **yes**.

- [ ] **Record the ruling** in `CHANGELOG.md` in his words and retire S1 from
      `project/open-decisions.md`, per that file's own header. Not done here: writing after a
      `=>` is his alone, and both edits were outside this change's declared scope
- [ ] **Do not add `stage-commits` to `SHARED_WITH_HELM` until the coordination design lands.**
      Tried on 2026-09-27 and reverted: membership is not a label but a claim that the skill is
      delivered and parity-checked, so it turned `test_helm_sync::test_the_record_covers_exactly_the_shared_set`
      red (*"shared but unrecorded: ['skills/stage-commits']"*) and
      `test_shared_skill_serves_both_ecosystems[stage-commits]` red as well — the latter because
      `ECOSYSTEM_MARKERS` matches a bare `.py` path in the skill with no TypeScript counterpart
      beside it. **`test_portable_skills::test_every_shipped_skill_is_classified` therefore stays
      red, now for a known and ruled reason with a named blocker rather than an unasked question**

- [x] **Ruled 2026-09-25: the prefixes go and stay gone.** The 09-24 change stands rather than
      being reverted, and the five sp-only skills that still carried one — `audit-code`,
      `audit-output`, `audit-pipeline`, `audit-prompts`, `release` — were stripped to match.
      `tests/test_helm_sync.py` **82 passed** afterwards, confirming those five are not shared.
      Recorded in `CHANGELOG.md`
- [x] **Helm's files were not touched**, on explicit instruction — sp's only. Two things there now
      contradict the ruling and were named rather than edited: `.claude/skills/install/SKILL.md`
      still carries `**COMMAND SKILL** —`, and `project/plans/design-skill-defects.md` D3's slot
      reads *"Discuss. Need more information."*
- [x] **Helm told**, in their tree —
      `collab/sp/2026-09-25-the-prefixes-are-ruled-out-and-sp-has-stripped-its-own.md`
- [x] **Filed as #259**, 2026-09-26, with the body reviewed first. Both halves in scope: the
      sharing mechanism, and Helm adopting sp's idioms. #181 is adjacent (`~/.sp` convention
      drift) and is not the same thing
- [ ] **Decide what happens to the spent 09-23 collab note** — committed and then deleted, per
      `plans-are-temporary`, or deleted. The deletion is the Captain's, either way
- [ ] **`.claude/skills/` and `~/.sp/skills/` still carry the prefixes.** They are installed
      copies, regenerated from the templates, so they refresh on the next `sp init --update` —
      **not `sp doctor`, which must not be run here (#210)**. Until then this project's own skill
      list shows the old descriptions

#### Helm adopts sp's idioms, then installs into paratext-copilot

> **The Captain's second priority, 2026-09-19**, and now the first half of the goal above.
> *"finish the new helm and install in paratext
> copilot."* Nothing is built. The design is `human-at-the-helm/project/plans/design-helm-project-layout.md`
> (R1–R12 ruled, steps 2–5 built) — but several of its §7 steps were **overtaken** by the rulings
> below, and step 6 as written is now withdrawn. Read these before that document.

**Ruled 2026-09-19, all the Captain's:**

1. **Helm uses the same idioms as sp** — *"or we have two different implementations of the same
   thing and we have to maintain each."* Three of them: `templates/<root>/` mirrors the
   destination, so the path *is* the mapping (guarded in sp by
   `test_project_templates_mirror_their_destination`); the declaration carries only what the tree
   cannot say; ownership is a property of the half — `helm/` ours, `project/` theirs, which is R1.
2. **The manifest's mapping rows go.** *"just copy the subdirectory and the files it contains."*
   Its `groups:` already read the tree; its four `files:` rows are hand-kept and are the second
   source. Once `templates/` mirrors the destination there may be nothing left to declare, since
   Helm has no index to render and no `.gitignore` to generate — that is the same idiom producing
   less declaration, not a divergence.
3. **No migration record, no moves ledger, no stamp.** *"we are the source of these skills, we can
   track them using source code control here."* D7.1's "permanent and accumulating" answered a
   question the AI had posed; it is not a request for the thing it presupposed. Install and update
   are one act: re-copy and read the diff.
4. **Helm keeps its own installer.** `/install` stays a markdown skill any assistant can follow.
   Shared idioms, not shared code — a methodology that needs a Bible-pipeline package installed is
   not tool-neutral, and that is Helm's premise.
5. **Helm gets `CHANGELOG.md` and `docs/`, and so does every Helm project.** It has neither today,
   which is why its own rulings have had nowhere to live. `templates/project/CHANGELOG.md`,
   create-only.

- [ ] **Open:** D9 — the shape of Helm's own AI context, an empty `=>` in that design document.
      Read as **B** (`docs/ai-context/project/` only, the shipped half being the source tree) and
      **not confirmed**. It blocks §7 steps 11–12
- [ ] Lay `templates/` out as a mirror of the destination, and delete what that makes redundant
- [ ] Then install into `nida-institute/paratext-copilot`. **Its tree is not clean** — it carries
      an uncommitted pre-2026-09-17 Helm install (`health-check/`, `helm-check/`,
      `docs/ai-context/helm-manifest.yaml`, `project/` all untracked; `handoff/SKILL.md` modified
      +14/−6) and is in the old flat `docs/ai-context/` layout. Installing over it without the
      Captain reviewing that diff first would sweep someone's unreviewed work into the result
- [ ] `sp doctor` labels the disciplines group **"Conventions"**, the directory's old name. That is
      almost certainly where discourse-flow's stale `~/.sp/conventions/…` pointer came from

### ⚖️ THE NEW GOAL — a dataset announces its terms when it lands

> **Set by the Captain 2026-09-25**, for the next release. *"when sp downloads and registers a
> dataset, it needs to display the copyright and license strings, reminding the user of his/her
> obligations, such as attribution, using only for Bible translation purposes, or whatever."*
> Scoped the same day: *"just print the string to the terminal. perhaps with a requirement for
> the user to say he/she agrees with the terms before actually registering - if that's feasible,
> it is a really good additional step."*

**The gap, measured 2026-09-25.** The command that lists what the machine already has shows the
terms. The two commands that put something new on it — the moments an obligation is incurred —
say nothing.

| command | terms shown today |
|---|---|
| `sp resource list` | a **LICENCE** column — `cli.py:594-599` |
| `sp resource add` | none. `✅ Registered '<id>' — <path>` and nothing else — `cli.py:625` |
| `sp dataset download` | none. Calls `fetch(entry, dest=…)` and returns — `cli.py:710-721` |
| `sp dataset search` | none — `cli.py:665-676` |

**The licence is already carried, so this is display rather than plumbing.** Merged at
`resources.py:248`, stored in registrations (`REGISTERED_FIELDS`, `:423`), carried into report
rows at `:693`. Every catalog entry has a `license` — 30 distinct values, including `Restricted`,
`No license file — ask before redistributing`, `Custom — see http://sblgnt.com/license/` and
Levinsohn's *"freely distributable, not for sale"*.

**There is no `copyright` field** — 0 occurrences in `data/resources.json`. So "copyright and
licence strings" is one string today. Adding one is `awesome-biblical-data`'s, and would be the
third thread now waiting on that repository.

**Ruled 2026-09-25, the Captain agreeing to all three:**

1. **Print the licence at `sp dataset download` and `sp resource add`.**
2. **The consent gate is on `resource add` only.** Registering is the act that takes the
   obligation on; `dataset download` prints and proceeds. Downloading a file you then delete is
   not agreement to anything.
3. **`--accept-terms` for non-interactive use, and fail closed naming it when there is no TTY.**
   Blocking breaks every script and CI run; assuming yes makes the gate theatre.

- [ ] Build it. **`click.confirm` is the mechanism** — it aborts rather than proceeding when it
      cannot prompt, so fail-closed is the default behaviour rather than something to write.
      ⚠️ **Corrected 2026-09-28: this line said "`click` is already the CLI library", which is
      false.** Measured: `click` is imported by `cli_utils.py` and `utils/linter.py` and used
      **only for terminal output** (`click.echo`); **argument parsing is `argparse`**, in
      `cli.py:74` and `tools/replay.py`. The conclusion survives — `click` is a declared
      dependency and `confirm` is available — but nobody should reach for click's command or
      group machinery on the strength of it, and anyone designing `sp help` (→ #264) needs the
      right framework
- [ ] **This adds a prompt to a CLI that just removed four.** `_configure_ai_assistants` is
      *"non-interactive by design (#204, D4/D5)"* (`cli_utils.py:230-244`) precisely because
      prompts defaulting to No broke a fresh setup silently. A licence gate has something to
      protect that the skills prompt did not, which is why it survives the comparison — but it is
      the same shape, and the reason it differs should be written into the code, not assumed
- [ ] **Eight catalog entries carry a pointer rather than terms** — `Custom — see <url>`,
      `See repo`, `See site`, `No license file — see repo`. The gate can require agreement, but
      what it shows for those is a URL the user has not opened. Worth deciding whether they read
      differently
- [x] **Filed as #252**, 2026-09-25, with the body reviewed first. Plan:
      `project/plans/plan-terms-on-download-and-register.md`, `Status: ruled (2026-09-25)`.
      Three open decisions in `project/open-decisions.md` §L — L1 blocks the gate, not the printing

> **The larger design exists, is not this goal, and is past its life.**
> `project/plans/design-source-licensing.md` — Proposed 2026-08-24, nothing built, four of the
> Captain's rulings verbatim in §3, six open `=>` slots in §8, and a dedicated issue proposed in
> §9 and never filed. **This goal needs none of the six answers.** At 32 days the document is
> past the eight-day line and is the only copy of those four rulings, so they move to
> `CHANGELOG.md` before it goes. The deletion is the Captain's.

### 🚨 HIGH — there is no type checking, and the suite does not say so

> **Flagged 2026-09-16.** `tests/test_types.py` fails, and it is easy to read as one more known
> red line among four. It is not. Its output is:
>
> ```
> PYRIGHT TYPE ERRORS:
> ================================================================================
> (nothing)
> ```
>
> **Pyright is not starting.** `npx` itself is broken — `MODULE_NOT_FOUND` in `npx-cli.js`,
> most likely a casualty of deleting `gui/frontend/node_modules` for disk space. So the test
> fails on a non-zero exit code with an empty error list: it is not reporting that the code is
> clean, and it is not reporting that the code is dirty. **It is reporting nothing, and the
> whole type check is absent.**
>
> This is the failure shape `check-the-source-not-the-rendering` exists to name — a guard
> reduced to nothing while still appearing present in a triage. It was catching a real defect
> the day before: `_owner_of_each_target_token` annotated `-> Dict` while returning a tuple.
>
> **Until `npx` works, nobody should read a passing suite as type-checked**, and no change to
> `src/` has been type-checked since it broke.
- [ ] Fix `npx` — reinstall via volta, or restore/regenerate `gui/frontend/node_modules`
- [ ] **Then re-run `hatch run pytest tests/test_types.py`** and see what accumulated while the
      check was off
- [ ] **Ruling wanted:** should this test *fail loudly as a broken check* rather than as an
      ordinary type error? A guard that cannot run and a guard that found a problem currently
      look identical in the summary line, which is what let this sit

> **Related, and not the same thing:** `gui/frontend/node_modules` is **tracked in git** — 7,997
> files, 1,787,308 lines — so deleting it from disk frees the working copy but not the
> repository, and `git status` reports 7,997 deletions until it is restored or deliberately
> untracked. Any `git add -A` would commit that deletion. Untracking it with a `.gitignore`
> entry is the change that actually saves the space; it is a decision, not a side effect.

### 🎯 THE GOAL — give discourse-flow what they need to implement segment-level text

> Set by the Captain 2026-09-10, superseding the representation goal below. **Everything else in
> this list comes after this.**
>
> They have answered our collab and their side is specified and ready:
> `collab/discourse-flow/2026-09-10-a-pericope-does-not-need-the-text-if-its-segments-have-it.md`.
> Their closing line — *"your engine change lands first"* — is the whole of what blocks them.

**What they need from us, in the order it unblocks them:**

- [x] **E3 — `usj_to_text` keeps the chapter and the punctuation.** Chapter falls back to the
      verse `sid`; a bare string keeps its own spacing. Both paths now return the same 665
      characters for Philemon 1:1–7 — `tests/test_scripture_usj.py`, 35 passing
- [x] **E1 — `include:` valid with every format.** `{text, scripture_pipelines}` when `include:`
      is non-empty, bare string when it is not; container built once and shared with the USJ
      path — `tests/test_scripture_include.py`, 30 passing
- [x] **The word addressing as ruled** — a map keyed by word id, `null` for a slot the text does
      not render, a list for a word written in several morphemes. Keyed rather than positional
      on the Psalm 23:1 evidence
- [x] **E2 — `spans:` cuts a passage into units named by word id**, one result per span, read
      once — `tests/test_scripture_spans.py` plus an end-to-end step test through `load_pipeline`
- [x] **Told them it has landed 2026-09-22** — all three, not just the first, in
      `discourse-flow/collab/sp/2026-09-22-segment-text-landed-and-the-windowing-ask-is-ruled.md`.
      Their editable install resolves to our tree, which they confirmed on 09-21, so they have it
- [x] **`save_json`'s `indent=2` is ruled and stays** — see the section below

**Their three answers, all the Captain's, so they are rulings and not opinions:**

1. **Segment-level text is right, in our exact shape** — `text` and `translation` as plain
   strings per segment, and the pericope-level `source_text` goes.
2. **Do not ask who reads the USJ.** His decree: *"downstream consumers are a black box to us. I
   decree that we do not need the text at pericope level if we have it at segment level."* Do
   not design around a consumer census, and do not wait for one.
3. **The Hebrew cases.** A morpheme with no surface form is `null` **in the morpheme slot** —
   `[null, "בָּ…"]` — not an empty string and not omitted, so `null` reads the same at both
   levels and index alignment survives, which is what keeps the ids derivable. **Compounds must
   be identifiable and the representation is ours to choose**, under one constraint: the index
   stays the address, so בֵּית and לֶחֶם may not collapse into one slot. Detection is `unicode`,
   not `lemma` — our own measurement, 53 of 53 against 11 of 53.

**Two corrections they made to our note, both accepted:**

- **The indentation is ours.** `utils/io.py:409` — `json.dump(..., indent=2)`, hardcoded in
  `save_json`, so every `saveas` JSON artifact in every pipeline is indented. Their tree has no
  `json.dump` at all; verified. Our note told them to fix it with `separators=(",",":")`, a fix
  that does not exist on their side. **`genre_markers` in that same row genuinely is theirs** and
  that half stands.
- **Calling prompt payload a "focus question rather than a cost one" was wrong.** A prompt
  payload is tokens, and the object reaches a prompt once per pericope per book. It is both, and
  the analysis-quality half is the expensive one because a degraded run is re-run and re-reviewed
  on the Captain's time. Accepted; the design document's §4 framing needs the same correction.

### 🎯 Alignment — **the only known blocker for discourse-flow**

> Captain, 2026-09-13: *"alignment is the only known blocker for discourse flow at this point."*
> E1, E2 and E3 all landed, so the segment-text goal above is done except for telling them.
> This is what replaces it.
>
> Design: **`project/plans/design-scripture-alignments.md`**, status `proposed`. Read it rather
> than re-deriving — it carries the rulings and the measurements with the commands to re-run them.

**Ruled 2026-09-13 and 2026-09-14, all the Captain's:**

1. **R1** — a span returns its aligned tokens **plus** the unaligned tokens between them. A target
   token aligning to *nothing* is included; one aligning to a *different* source word is not.
2. **R2** — the engine reads **our own** declaration of supported pairs, not
   `Clear/Alignments/data/catalog.tsv`. Validated at read time against each alignment file's own
   `documents` block.
3. **R3** — the corrected catalog omits the bogus Hausa OT pair only; `SBLGNT-OHCB` is genuine.
4. **R4** — *"alignments are directional. both `from` and `to` must be specified."*
5. **R5** — of the two readings of reordering, **target order is correct**: the aligned tokens are
   put back into the translation's own reading order, so the English reads as English.
   **Extended 2026-09-14:** *"I would like an option for source order vs. target order, default =
   target order."* Both orderings ship; target is the default. R5 governs **sequence** only —
   membership is R8's, settled by target order in both modes. Source order does not read as
   English and is not meant to; it is for comparing the two texts side by side. **Who each serves:**
   *"most people will prefer target order, period. the few people who know Greek or Hebrew want
   both orders."* So target order is the default because nearly every reader wants it. **The
   request takes a set, not a choice** — *"you should be able to ask for one or the other or
   both."* Three legal requests: target alone, source alone, both; default target alone. Where
   both are asked for they cover the **same token set** — R8 fixes membership, so the two differ
   in order only. Open sub-question: which source position places a token that aligns to several
   source words.

6. **R6** — **the alignment is filed per verse; our units are not.** Captain, 2026-09-14,
   correcting an earlier heading that called the verse "the unit of work": *"The alignment format
   does one record per verse, but we do our work in linguistic units - clauses, phrases,
   sentences. So we have to read past the verse scope."* The verse is a lookup key, never a unit
   of analysis — `verses-are-milestones`. Gather every verse a span draws from and assemble
   across them; never treating the whole span as one stretch of the target.
7. **R7** — a Psalm title is offered as a **target-side convention, never as a correspondence**.
   Where a span covers the source verse holding the superscription and the target happens to carry
   a verse `000`, it is offered as a separately labelled field, positional and saying so. Verse 000
   is **not** a general mechanism: BSB carries it for 116 of 150 psalms, YLT for 11, the Hebrew
   source never, and no verse-000 token is aligned anywhere.
8. **R8** — a shared target word: **no token appears in two spans' text, but the constituent list
   shows it in both.** Captain,
   first *"both spans get it"*, then refining: *"the target word order tells us what span to put it
   in — or at least, the end user cannot see which span we drew it from"* and *"but a constituent
   list should show it both places."* So the **span text** gives the word to whichever span's target
   stretch contains it and to that one only — adjacent spans concatenate exactly, with no repeat —
   while the **constituent list** and the opt-in correspondence map show it in **both**, because
   that is what the alignment says.
9. **R9** — the correspondence map is **opt-in**. Captain: *"by default, no, but provide an option
   that does for debugging and transparency."*

**Measured, against `SBLGNT-BSB` (115,008 records) and `SBLGNT-YLT`:**

- alignment is **not monotonic** — 17% of adjacent source-order steps run backward in target order
- **81%** of spans have source order disagreeing with target order; **35%** have two or more source
  words sharing an identical target set. Word correspondence is a many-to-many graph and cannot be
  recovered by position
- **the alignment is filed per verse — that is the data's shape, not our unit of analysis.** Only
  **80 of 115,008** records (0.070%) have source and target outside one verse, so the verse is a
  reliable lookup key. A span is a clause, phrase or sentence and crosses verses whenever the
  language does, so the operation **reads past verse scope**. Where a span happens to cover whole
  verses its tokens are contiguous (**7,933 / 7,934**); a token belonging to a different source
  unit can fall inside what a span covers only where a span opens or closes
  *inside* a verse — which discourse-flow measured at 4 of 390 units in Mark, **1%**, and which is
  the whole reason the step was asked for
- **An earlier "49% of spans are interleaved" figure is withdrawn.** It came from arbitrary
  word tiling, which nobody does; it was a property of the test harness, not of the data
- word order is **locally coherent**: consecutive source words move `+1` in target position 34% of
  the time and `+1/+2/+3` 62%, while large backward jumps (≤ −6) are 2.1%. A verse breaks into a
  median of **3 ascending runs** — consistent with the Captain's model of phrase-coherent blocks
  whose internal order is largely kept and whose relative order sometimes is not. **Not yet checked
  against syntax**; Macula Lowfat would settle whether a run is a phrase
- **A BSB-versus-YLT comparison was run and is void** — do not repeat it or cite its numbers. It
  was framed on the AI's assumption that YLT is the more literal translation; the Captain corrected
  that on 2026-09-13, and the comparison is confounded regardless: YLT's alignment has **0.6%**
  multi-source records against BSB's **4.9%**, and 21% unaligned tokens against 15%. It measures
  how the two alignment files were built, not the translations
- target ids join the target TSV **100% directly**; no identifier reshaping needed

10. **R10** — a span **reaches outward over unaligned tokens and stops at a neighbour**. Within
    each verse the bounds move out from the first and last aligned token over runs of unaligned
    tokens, halting where a token belonging to a different source unit begins. Reaching outward is
    what keeps verse-final punctuation and verse-initial words — without it the text reads
    `wordTherefore` and Ephesians 1:11 loses its opening *"In Him"*. Of the 29,964 tokens that
    align to nothing, **98% are punctuation and 2% are words**; the 2% are the ones whose absence
    breaks a sentence.
11. **R11** — **two kinds of nothing, told apart**, per `say-which-kind-of-nothing`: an empty
    collection (asked, nothing aligned) and `null` (the source ids are not in the alignment file).
    A third "kind" the AI had listed was R7's Psalm title — a *populated* field, not a nothing —
    and was removed 2026-09-14 when the Captain checked R11 against the rule. Where the title is
    absent it is **`null` and present**, never omitted, because no request list governs it;
    `alignments` and `correspondence` may be omitted precisely because `returns:` is a request
    list, which is the rule's stated exemption.

12. **R12** — a span carries **one boolean** saying whether its tokens are contiguous in every
    verse it draws from. True for ~99% of units; false exactly at the boundaries this step exists
    to serve. A list of the offending tokens was considered and not taken.
13. **R13** — **all twenty pairs ship**, across ten languages. Reframed around cost: R2 already
    validates each pair against the file's declared `documents` at read time, which is what catches
    a file misdescribing itself, so a pair costs one row and a bad file fails loudly. **Flagged, not
    resolved:** `por/JFA11` is `-transfer`, not `-manual` — machine-transferred rather than hand
    aligned, and whether the declaration records provenance is undecided.

**Tracked as → #238. Built and committed 2026-09-14** — `1501da1` (step, reader, 21 tests,
declaration, bundling, docs), `4b3640e` (the design documents). Design status `ruled (2026-09-14)`,
R1–R16, D1–D8 answered. **Pushed and released** — corrected 2026-09-27: `git branch --contains`
puts both commits on `origin/dev` *and* `origin/main`. This line read "Not pushed" for thirteen days.

> ⚠️ **"Built" does not cover every ruling above it. Two are ruled and not built**, and this
> entry read as though they were:
> - **R7 — Psalm titles.** No field, no code, no test. Measured 2026-09-16 against Hebrew→BSB:
>   1,303 target tokens sit at verse `000` across 116 of the 150 psalms and **not one is aligned
>   to anything**, while the Hebrew source has no verse-`000` ids at all. So a span over Psalm 23
>   returns the psalm and **silently drops "A Psalm of David"**. Undecided before it can be
>   built: what the field is called, and whether `returns:` gains a member for it.
> - **R9 — the opt-in correspondence map.** `correspondence` appears nowhere in `src/` or
>   `tests/`; the schema's `returns` enum is `["text", "alignments"]`. This one fails loudly —
>   `returns: [correspondence]` is refused at lint — so it is the less dangerous of the two.
>
> **Both re-verified 2026-09-27.** `grep -rn correspondence src/ tests/` returns one unrelated
> hit in `test_ai_rules_classification.py`, and `pipeline_schema.py:321` still reads
> `"enum": ["text", "alignments"]`. Neither has moved since 2026-09-16.

- [ ] **R7 — build it or drop it.** Undecided before it can be built: what the field is called,
      and whether `returns:` gains a member for it. A span over Psalm 23 silently drops
      "A Psalm of David" until this lands — silent is what makes it the dangerous half
- [ ] **R9 — build it or drop it.** Adding `correspondence` to the enum at
      `pipeline_schema.py:321` is the visible part; the map itself is the work

**Verify:** `hatch run pytest tests/test_alignment.py -q` → 22 passed.

**Worked examples**: `scripts/alignment-worked-examples.md` — Luke 1:1–4, Ephesians 1:3–14,
Psalm 23:1–4 and Ruth 1:1–4, Greek and Hebrew, regenerable with
`hatch run python scripts/gen_alignment_demo.py`. In all four, the tokens are contiguous in every verse.

**What is left before discourse-flow can use it — all but one done 2026-09-16:**
- [x] **Ruling citations stripped from the alignment docstrings** — `rule
      docstrings-say-what-not-why`. `utils/alignment.py` and `steps/alignment.py`, docstrings and
      comments only; the module-level pointers to the design document stay, which the rule asks
      for. **The guard does not catch this** — it forbids a date, a commit hash and the word
      "Captain", not `(R15)` — so it was judgment, and nothing goes red if it regresses
- [x] **`data/alignment-pairs.json` is wired** — `steps/alignment.py` `resolve_pair()` reads the
      declaration and resolves each row under the `clear-alignments` dataset. The per-machine
      `kind: alignment` route is gone rather than kept beside it.
      `tests/test_alignment_declaration.py`, 10 tests
- [x] **Run against the real corpus** — `scripts/check_alignment_pairs.py`, an audit script
      rather than a test because a fresh clone has no corpus. **18 pairs, 0 unusable**;
      `SBLGNT→BSB` joins **100% on both sides** across 115,008 records
- [x] **D9's Portuguese half is fixed** — `JFA11` source ids now carry the `n` prefix, 99,258 of
      99,258 join. Fixed in `Clear/Alignments`, **committed on `fix/portuguese-source-id-prefix`
      and not merged upstream**, so it holds on this machine only
- [x] **discourse-flow told** — `collab/sp/2026-09-14-alignment-has-landed.md` in their tree, and
      `2026-09-16-document-order-is-in.md` answering their reply
- [ ] The unbuilt `union`/`intersect` in `verse_ranges` bear on this; see Pipeline data operations

**Three pairs are declared out, each measured, not guessed** — `scripts/check_alignment_pairs.py`
re-derives all of it. `hau WLCM-OHCB` is byte-identical to its SBLGNT sibling and declares that
sibling's pair (Clear#12); `eng BGNT-BSB` has 12-character target ids where `nt_BSB.tsv` has 11,
so 0 of 172,736 join, and dropping the trailing character still leaves 240 ids naming rows that
do not exist; `fra WLCM-LSG` names `ot_LSG.tsv`, which is 66 bytes — a header row and no data.
**Two further defects were found and fixed** in `Clear/Alignments` and are likewise unmerged:
`hin WLCM-IRVHin` declared no `roles`, and `spa WLCM-RV09` declared its source as lowercase
`wlcm`; both made our own `validate_pair` refuse a real pair. Five issue drafts and two pull
request bodies sit unfiled in `tmp/`.

### 🅿️ Parked 2026-09-14 — three issues raised to defer, not to work

> Raised while designing #238's step syntax, then deliberately set aside. **None blocks #238**,
> which ships on flags. Design: `project/plans/design-operations-in-the-pipeline-language.md`.
- [ ] **#241 — how the language expresses one domain with many operations.** Ruled: one design;
      alignment on flags; XPath/XQuery generally the right direction. Open: whether standalone pure
      operations (verse algebra, list transformation, filtering) are **expressions** or **step
      methods** — §7 of the design doc has both written out with syntax
- [ ] **#240 — normalise names to hyphens**, with a carve-out: a key forwarded to a provider keeps
      the provider's spelling. Ruled but **not scheduled** — *"not worth the churn right now"*
- [ ] **#239 — the `${...}` resolver is regex substitution, not a parser.** A kludge, off the
      critical path. #241 governs it: modest fix under step methods, precondition under expressions
- [ ] **#125 is open although the feature is built** — `group_by`/`order_by` ship at
      `steps/for_each.py:283` with `tests/test_group_by.py`. Close or re-scope it

### 🐞 Three defects filed against `Clear-Bible/Alignments`, 2026-09-13

> Found while surveying the alignment data. All three are Clear's to fix, not ours; they are
> recorded here because R2 and R3 exist because of them.
- [ ] **#12** — `hau/alignments/OHCB/WLCM-OHCB-manual.json` is byte-identical to its SBLGNT
      sibling while its filename and TOML claim Hebrew/OT. 1 of 21 alignment files; the only
      duplicate. **Never resolve a pair by filename** — this is why R4 validates against `documents`
- [ ] **#13** — `data/catalog.tsv` is an orphaned Git LFS pointer with no `.gitattributes`
      anywhere. The only LFS-tracked file in the repo; a fresh clone gets three lines of pointer
- [ ] **#14** — that catalog's contents do not describe the tree: 19 listed, 21 present, **one**
      name in common
- [ ] Fixing the catalog on the local `dev` branch in `Clear/Alignments` is a contribution to
      offer upstream, **not** something the engine reads — R2 settles that. That branch has no
      upstream today

### ✅ `save_json` indents every artifact — ruled, and deliberately unchanged

> Found 2026-09-10 by discourse-flow, correcting our own note: `utils/io.py:409`,
> `json.dump(content, f, ensure_ascii=False, indent=2)`, which is 47.7% of
> `57-PHM-discourse.json` and cannot be declined by a pipeline.
- [x] **Ruled by the Captain, 2026-09-10, and the item closes.** *"we normalize spaces by pretty
      printing … the number of spaces doesn't matter, 2, is fine, what matters is validity.
      adding complexity to the interface is the wrong move."* No `indent` knob, no
      output-versus-intermediate rule. It is consistent with the standing ordering — readability
      outranks size — and the bytes are the third-ranked consideration, not the first.
- [x] Told to discourse-flow in the reply, so they do not plan around a compact-output option

### 📐 The representation design — ruled, feeding the goal above

> Set by the Captain 2026-09-10 and now serving the goal above rather than standing alone.

`include:` is refused unless `format: usj`, so a pipeline that needs annotation cannot have
milestone-cost text. Measured downstream on Philemon 1:1–7: **622 characters of Greek delivered
as 14,045 of JSON, 22.6×**; across the book 334 words carry an anchor and **228 are referenced
by nothing**.

The design is drafted and unreviewed: **`project/plans/design-annotation-without-anchors.md`**,
status `proposed`. It was raised by
`collab/discourse-flow/2026-09-09-include-forces-the-most-expensive-text-form.md`.

- [x] **Measured** — `project/plans/design-representation-workbench.md`, 72 cells, regenerate
      with `hatch run python scripts/representation-grid/generate.py`
- [x] **Inventory collab read** and folded into the design
- [x] **Ruled 2026-09-10, Q1–Q10** in `project/plans/design-pericope-segments-and-text.md` §10:
      segments hold text; `include` works with any format; word array replaces anchors, `null`
      for gaps, two-level arrays for morphemes; engine supplies text-by-span; `usx`/`usfm` added;
      `lexical` family provisional
- [x] **Q6 and Q9 answered by discourse-flow's reply**, both by the Captain: the elided article
      is `null` in the morpheme slot; compounds must be identifiable, detected by `unicode`, with
      the representation ours so long as the index stays the address
- [ ] **Four carve-outs awaiting a yes or no**, each an empty `=>` in §10: E3 shipping ahead of
      the E1–E4 bundle, the collab sharing mechanics, striking `print` *(done)*, Q9
- [ ] **Build E1–E6.** Nothing is implemented. E3 (`usj_to_text` loses the chapter, detaches
      punctuation) should go first — another team's live fix depends on it
- [ ] **Shipped documentation drafted, not installed** —
      `project/plans/plan-scripture-documentation.md`. Ships **with** the code, never before

**The one fact worth carrying:** a per-word payload is keyed by an opaque word id and carries
only the annotation — no surface form, no reference. That is the *whole* reason anchors are
load-bearing, and it was established by fetching `WLC Ruth 1:1`, not by reading comments.

### 🤝 The working-document lifetime belongs in Human at the Helm too

> **Sequenced deliberately, 2026-09-10: the sp-local half is done, this half is not.**
> `plans-are-temporary` now names collab notes, states that age is measured from the later of
> the declared date and the last commit (never mtime), and rules that a collab is written once
> into the recipient's tree. The Captain: *"this is valuable, and belongs in helm as well."*
>
> The general principle is engine-neutral and Helm needs it: documents that accumulate have a
> death; commit them so deleting is safe; move the ruling to the CHANGELOG first, because that
> entry is the index into the graveyard; recover with
> `git log --diff-filter=D` then `git show <commit>^:<path>` — verified against a real deletion.
>
> **The draft text is written** — see the conversation of 2026-09-10, or re-derive it from the
> rule. `disciplines/project-tracking.md` is the natural home: it already carries the *rolling*
> half (*"Git history is the audit trail. Do not accumulate dated copies"*) and lacks the half
> about documents that accumulate anyway. It is a **shared** file, so this costs a
> `helm-sync.yaml` hash refresh and a twin commit.
- [ ] **Decide the home first:** extend `disciplines/project-tracking.md`, or a new shared
      discipline
- [ ] **Then decide whether `data/ai-rules.yaml` keeps the full text or points at the
      discipline.** Two statements of one idea is the drift this repository has been burned by
      twice; the `github-workflow.md` precedent is *"Not restated here"*
- [ ] Parity handling: `hatch run python tools/sync_helm.py --apply`, and the shared copy must
      carry no engine vocabulary — the guard refuses it

### 🚢 0.2.1.28 — SHIPPED. Two items did not land and roll forward

> **Merged and tagged.** PR #236 merged 2026-09-24, `v0.2.1.28` is tagged, and `CHANGELOG.md`
> carries `## 0.2.1.28 — 2026-09-21`. Verified 2026-09-25 with `gh pr view 236` and
> `git tag --list "v0.2.1.2*"`.
>
> **The double-heading hazard this section warned about was fixed before the tag** — the
> CHANGELOG no longer carries a `2026-09-09` heading beside an `## Unreleased` one.
>
> **The retitle never happened.** The Captain chose "the order is declared once, and lint reads
> it" on 2026-09-21, `gh pr edit` failed on token scope, and the PR merged under its original
> title, `Release 0.2.1.28 — the bugs a first setup hits`. That is now permanent history; the
> only remaining question is whether the CHANGELOG entry should carry the chosen title instead.
>
> **#176 and #244 did not ship.** Both are still open. They were listed below as "added to this
> release, in the order it has to land"; the release went out without them, so they **roll
> forward to the next release** with the goals at the top of this file. The ordering constraint
> between them still holds — see the note under them.

**Crucial, and first — #245: a re-run leaves the previous run's intermediates.** The Captain,
2026-09-21: *"this is crucial."* Every run and every `/audit-output` is affected until it lands,
because an audit reads two runs' files as one set. **Do not fix it with `sp clean` before the
run:** that deletes every parameterisation's intermediates, which is #198's bug moved from
`debug/` into `intermediate/`, and it breaks `--rewind-to`, which replays by reading the very
files a pre-run clean removes. The design is a per-run write manifest keyed by pipeline and
`debug.run_key_for(cli_vars)`, so a run deletes only its own previous output and the directory
tree does not change. `clean_before_run: true|false` with `true` the documented default, and
`--no-clean` per invocation. Four rails in the issue, all load-bearing.

- [x] **#245 — shipped and CLOSED**, confirmed 2026-09-27. The `--rewind-to` guard was written
      first; `tests/test_run_manifest.py`, 14 tests

**Prompt work, rolled forward to the next release, in the order it has to land:**

- [ ] **#176 — strip YAML frontmatter before the LLM call.** A **behaviour change**: the whole
      `.gpt` file reaches the model today, frontmatter included (`steps/llm.py:220` → `307`; the
      stripped `body` at line 85 feeds the contract check only and is discarded). Write the test
      first, then validate across existing pipelines. Open: strip everything, or keep and relocate
      `description:`
- [ ] **#244 — replace the starter prompts.** Sequenced **after #176**, so the replacement is
      written against post-#176 behaviour rather than rewritten after it
- [ ] **Position 12, `reference`, in `data/prompt-structure.yaml`.** Ruled 2026-09-21: prompts
      need an extension point and the end is the place for it. `reference` rather than
      `extensions` or `appendix` — a content word, not a mechanism or a position, so it says what
      belongs there. One `# REFERENCE` section, subsections free-form inside it, with C6
      constraining it to material the tasks cite and no obligation. **Design notes are refused:**
      everything in a `.gpt` reaches the model, so notes for maintainers would be tokens the model
      reads and may act on; they belong in `project/plans/` or the header's `description:`
- [x] **`sp lint` warns on a prompt that does not fit the grammar → #242. Shipped — but #242 is
      still OPEN on GitHub** (checked 2026-09-27). Close it or say why it stays open. Warns, first
      finding per prompt, required sequence once per run. What the grammar binds is declared, not
      coded: a prompt whose **first line** is `---`

> **Why the ordering is a constraint and not a preference:** `sp lint` now warns on all six
> prompts in `prompts/`, so shipping the conformance check while keeping the current starter means
> a new user's first lint warns about the example we gave them. #244 and the check ship together,
> or the check waits.

- [x] **PR #236 merged 2026-09-24** — `dev` → `main`, and `v0.2.1.28` tagged
- [x] Artifacts **expired 16–17 September** — past, so the build re-runs on this release whatever
      else changes
- [ ] `data/models.json` was held back because committing it "restarts a two-hour build". **That
      reason has expired with the artifacts above**, so the one line now costs nothing it was not
      already going to cost. Whether it joins this release is the Captain's call

BaseX is **not** in this release; see below.

### 🦷 The shell/file-tool rules have no teeth — the AI must ask, not just violate

> **Targets this release.** The Captain's words, verbatim: *"The File Commands part of the ai
> context has no teeth. I want to change it so that LLMs ask permission when there is a good
> reason to do something else, e.g. File Tools does not support this operation, it's testing
> candidate Python code from a file (not a heredoc), etc."* And: *"otherwise, I have to give it
> permission on the command line to violate each rule, then interrupt and ask why it did it, and
> it requires my attention, which I want to focus elsewhere."*
>
> The rule is written as a prohibition with no sanctioned exception, so an agent with a genuine
> reason has two moves: obey and fail the task, or violate silently and get caught at the
> permission prompt. **Asking first is not a path the text offers.** The cost lands on the
> Captain's attention, which is the thing the rule was supposed to protect.
>
> **Where the text lives is undecided and is the Captain's call.** `docs/ai-context/` has no
> "File Commands" section. The rules are in `CLAUDE.md` "Shell Commands" (this repo only) and
> `~/.sp/disciplines/workflow.md` "Shell Commands" (every project on this machine, and shared
> with Human at the Helm, so a change there costs a `helm-sync.yaml` hash update and a twin
> commit). A third home is `data/ai-rules.yaml`, the enforced single source, where each rule
> already declares `enforcement:` and `scope:`.
- [ ] Decide the home, then rewrite the rule so that a named exception obliges the AI to ask
      first rather than proceed

### 📓 A pipeline needs a defect log → #232

> Somewhere a step can record what it noticed but did not fail on — a discrepancy in the data, a
> unit needing checking, an assumption it had to make — reaching the end of the run intact and
> attached to the output. `discourse-flow` built `plugins/defects.py` for this, and it is a
> module-level list with a lock, which `context-is-the-only-channel` forbids. They had to break
> the rule because the engine offers no sanctioned channel.
>
> **The engine is already writing these records as unqueryable prose**: `partialVerses` not
> interpreted, a mapping entry skipped as naming no join, `versification_guessed`. So this is not
> a plugin feature — the engine is one of its writers.
>
> Four routes are compared in the issue comment. The suggestion is a **reserved key in a step's
> output** as the channel, which reaches every step type and needs no exemption from
> `context-is-the-only-channel`; a **stdlib `logging` handler** as the Python convenience, since
> `Logger` is already `logging.getLogger('llmflow')`; and a declarative `check:` later.
- [x] **Ruled 2026-09-08.** The Captain took the recommendation: **C as the channel** — a step
      returns a reserved `defects` key alongside its data, so the record travels as ordinary step
      output and needs no exemption from `context-is-the-only-channel`, and every step type can
      write one, not only Python. **B as the Python convenience** — a handler on the `llmflow`
      logger, since `Logger` is already `logging.getLogger('llmflow')`, so plugin authors keep
      writing `logger.warning(..., extra={...})` and need no new import. The sink is **written
      automatically under `intermediate_file_directory`** and **summarised at the end of the run**.
- [ ] Build it. `[]` and absence must differ, per `say-which-kind-of-nothing`: an empty log means
      the run looked and found nothing
- [ ] `for-each` with `parallel:` means concurrent writes — their lock exists because of a real
      race in `subdivide_candidates`

### 🔗 An edition cannot name its discourse or syntax source portably

> Reported by `discourse-flow`; every checkable claim verified against the code. Thread and reply:
> `collab/discourse-flow/2026-09-07-an-edition-cannot-name-its-discourse-source-portably.md`.
>
> `load_registry_editions` resolves **only** `path` through `resources.resolve_path()`
> (`utils/scripture.py:879-885`). `discourse_path` and `lowfat_path` reach `Path()` raw, so a
> dataset-relative value is resolved against the process working directory and absolute is the
> only form that works. A registration therefore carries two kinds of reference at once, under a
> header that promises the file "means the same thing on every machine" — and
> `docs/sp-language.md:985` documents the absolute form, so this is the documented outcome.
> Our own `tests/test_discourse_loading.py:15` makes the same assumption via `Path.home()`, in the
> one place a reader would look for guidance.
>
> **Against the Captain's standing rule:** *"never, ever write absolute paths, they will not work
> on another machine."* They can satisfy it everywhere except this file and these two keys.
- [x] **Ruled and built.** The Captain: *"they cannot proceed using hard coded paths, I forbid
      that, they need this to work."* Both keys now accept a dataset-relative value **and** a
      registered dataset id with an optional subpath — the subpath is required in practice,
      because neither corpus sits at a repository root. `resources.resolve_declared_path`,
      20 tests in `tests/test_analysis_path_resolution.py`, documented in the language reference.
      *(Corrected 2026-09-16: this line named `resolve_annotation_path`, which has never
      existed.)*
  - [ ] **Greek discourse still cannot be named portably**, and not for want of the feature:
        `levinsohn-lgntdf` is absent from `~/.sp/datasets/`, so `levinsohn-lgntdf/LGNTDF` falls
        through to dataset-relative and lands nowhere. Registering it needs
        `sp resource download levinsohn-lgntdf`, which needs the upstream `branch` field. Syntax
        works today: `SBLGNT/lowfat` resolves inside the store copy
  - [ ] `tests/test_discourse_loading.py:15` still hardcodes `Path.home()`. It is now the only
        place in the repository modelling the shape we have just replaced
- [x] **`sp resource search` ships.** `sp resource list` showed 3 of 70 entries under a legend
      reading as a full inventory, and nothing listed the rest — which misled a session into
      proposing a hand-written absolute path into the store. A bare word is a keyword; anything
      else is a real XPath predicate evaluated by `lxml` over the catalog as a tree, with
      `lower-case()` and `matches()` supplied at their XPath 2.0 meanings. The `list` legend now
      names `search`.
- [ ] Nothing writes `discourse_path` / `lowfat_path`: `sp resource add` does not set them, so the
      only route is hand-editing a file whose first line says `sp resource add` wrote it
- [ ] A 404 on an archive URL surfaces as a bare `HTTPError` traceback rather than naming the
      branch as the likely cause

### 🔼 Two fixes belong in our catalog repo `awesome-biblical-data`, not in the vendored copy here

> **`nida-institute/awesome-biblical-data` is ours**, so these are ours to schedule, not another
> party's to answer. `data/resources.json` here is **vendored** and currently identical to it, so
> editing it here is reverted by the next sync. Edit `resources.json` there; `README.md` is
> generated after `scripts/validate_resources.py` passes.
- [ ] `levinsohn-lgntdf` has no `branch`, and that repository's default branch is `master`, so
      `sp resource download levinsohn-lgntdf` 404s. `download_data.py:49` already honours
      `branch`, so the fix is one field — upstream. Worth sweeping the other 69 entries
- [ ] This is the second thread now waiting on that repository; BaseX #38 is blocked on
      `awesome-biblical-data#5` — see the BaseX section below

### 🗄️ BaseX collections — **not scheduled**, and not in 0.2.1.28

> **Moved out of x.27 on 2026-09-09, and out of x.28 on the same grounds.** x.28 became a
> bug-fix release cut small and fast for a new contributor's blockers, and BaseX was not in it —
> the CHANGELOG entry says so plainly rather than letting the version number imply progress.
>
> It has no target release. Its critical path still starts in another repository, so scheduling
> it here would be scheduling something this repository cannot finish.

**What ships already, and what does not.** The half that works is the half that was never blocked:

| piece | issue | state |
|---|---|---|
| `type: basex` — query an existing database | #49 | **CLOSED, shipping.** `src/llmflow/steps/basex.py`, three test files |
| `sp setup-db` — load a corpus under a canonical name | #52 | **OPEN, no code.** `grep -n "setup-db" src/llmflow/cli.py` returns nothing |
| collection naming taken from the catalog | #38 | **OPEN, no code.** `design-basex-collections.md` reads `Status: proposal … Nothing is built` |
| `provides` able to describe a treebank or a lexicon | `awesome-biblical-data#5` | **OPEN, zero comments**, untouched since raised 2026-09-07 |

**Why the upstream issue is the whole thing, not a formality.** `provides` requires
`versification`, `canon` and `language` of every entry, so only a scripture text can be declared.
The catalog bears it out: **3 of 70** entries carry a `provides` block and all three are Bibles —
`WLC`, `SBLGNT`, `BSB`. The feature exists to load treebanks and lexicons, and the catalog cannot
name one. Since the first design ruling is *"names come from the catalog"*, there is no input to
build against.

**Verify:** `python3 -c "import json;d=json.load(open('data/resources.json'));print(len(d), sum(1 for e in d if e.get('provides')))"` → `70 3`.

- [ ] **Upstream first:** `awesome-biblical-data#5` — the schema change that lets `provides`
      describe a non-scripture subtree. Not designed here or there yet
- [ ] **Then the catalog content**, which is editorial rather than code: up to 67 entries need a
      `provides` block, and deciding what a meaningful name is needs the maintainer's judgment
- [ ] **Seven decisions in §8** of `design-basex-collections.md` remain unruled even once the
      blocker clears — `LANG` per subtree, `FTINDEX` by default or declared, whether a raw BaseX
      name in `database:` keeps working, the local root for a non-git source, and three more
- [ ] **Then build `sp setup-db`** (#52)
- [ ] **The `done` label on #38 is false and invites a wrong close.** It reads "Ready to be closed -
      implementation complete", which is true of #49 and not of #38's own subject. Changing a label
      is the Captain's act

### 📄 Whitelist design documents by declared status, rather than blacklisting

> ⚠️ **Probably superseded 2026-09-08 by `rule plans-are-temporary`.** That rule deletes a working
> document at eight days rather than classifying it, which was chosen over this proposal on the
> grounds that the valuable content cannot be reliably told from the rest. If it is superseded,
> this section and its two items should go; that is the Captain's call, not an agent's.

> **The Captain's proposal, verbatim:** *"how about whitelisting design documents rather than
> blacklisting? Only rely on design documents with status=[implementing, implemented], and ask
> about any design document marked [implementing] if it is more than 3 days old?"*
>
> This is `declared-not-inferred` applied to plan documents: rely on a declared status rather than
> inferring from prose whether a design is current. Two things it needs that do not exist yet.
> **The status is free prose today** — `project/plans/` carries "proposal, awaiting the Captain.
> Nothing is built.", "Implemented — historical record", "Proposed" and now "implemented", so a
> whitelist needs an enum before it can be a whitelist. **Nothing records when a status changed**,
> so the three-day question cannot be asked; a `since:` date beside the status would answer it.
>
> Unlike most rules in `data/ai-rules.yaml` this one is **guardable**: `project/plans/README.md`
> is already generated from the documents, so a test can refuse an unknown status and flag a stale
> `implementing`.
- [ ] **Ruling needed:** the status enum, and whether `since:` is a separate field or part of it
- [ ] Then the guard, and the generator reading it

### 🔍 `sp lint` checks the prompt contract in one direction only

> **Targets this release.** The Captain's words, verbatim: *"sp lint checks one direction only —
> linter.py:1326, 'every {{var}} must be in requires:'. There is no reverse check. Its own message
> for a withdrawn key even says 'delete it if the body does not use it', which is advice to a
> human, not an enforced rule."*
>
> `validate_gpt_body_declares_all_vars` computes `undeclared = body_vars - declared`
> (`linter.py:214`) and stops. The reverse set — a name in `requires:` that the body never uses —
> is never computed. So a prompt can declare an input, `validate_all_step_contracts` can oblige
> every calling step to supply it, and the body can ignore it, with nothing said anywhere. The
> remedy the withdrawn-`optional:` message advises at `linter.py:161` *is* this check, unenforced.
> **The `audit-prompts` skill has the same blind spot.** Its nine steps check convention
> structure, grounding of *output* fields, example diversity, guardrail integrity, AI-written
> examples, JSON formatting and structured outputs. None compares a prompt's `requires:` list
> against the `{{var}}` names its body uses, so a declared-but-unused input passes the audit
> exactly as it passes lint. The Captain: *"ALSO should catch this error."*
>
> **Two surfaces, one defect, but not one fix.** The linter is ours. The skill lives in
> `~/.sp/skills/audit-prompts/SKILL.md`, which is the Captain's store — and per #204 most of
> `~/.sp` is not in the package, so a check added there reaches this machine and no other until
> that is fixed.
- [ ] **Ruling needed first:** is an unused `requires:` entry an error or a warning? Then add the
      reverse check to `validate_gpt_body_declares_all_vars`
- [ ] Add the same check to the `audit-prompts` skill — **the Captain's store, needs his approval**

### 🐛 A skill added after a project was set up never reaches it, and `sp doctor` says all is well

> **Found by the Captain 2026-09-19** in `nida-institute/discourse-flow`. `sp doctor` reports no
> problems — *"✓ Skills in `~/.sp`: all 11 present and unchanged"* and *"✓ Skills are where Claude
> Code reads them"* — while `ls .claude/skills` there returns **ten**. `health-check` is the missing
> one. It was added 2026-09-10; that project predates it.
>
> **Not a catalogue problem, and an earlier diagnosis saying so was wrong.** `data/file-catalog.yaml`
> names the *directory*, not its contents — `sp/skills/*` at lines 50–54 and 73–77, for `~/.sp` and
> `.claude/skills/` respectively. Every skill is covered, and a fresh `sp init` today installs
> `health-check` into both. The first diagnosis searched for the string `health-check`, did not find
> it, and concluded it was uncatalogued; no skill name appears in that file.
>
> **The verified cause** is `doctor.py:651–664`, which asks whether Claude Code can see **any**
> skills rather than all of them:
>
> ```python
> if project_skills.is_dir() and any(
>     (p / "SKILL.md").exists() for p in project_skills.iterdir() if p.is_dir()
> ):
>     found.append(".claude/skills (this project)")
> ```
>
> One skill directory and the check is green. Its own comment says so, and
> `tests/test_doctor.py:207–233` confirms the design by placing a single `load-context` skill and
> asserting OK. **Nothing anywhere adds a newly-shipped skill to an already-initialised project, and
> nothing reports its absence.**
>
> **Why no test caught it.** `tests/test_catalog.py:203`, `test_skills_derive_from_shipped_templates`,
> is exactly the right comparison — shipped against catalogued — but line 208 restricts it to
> `Scope.SP_HOME`. The project destination has only `test_claude_skills_are_catalogued` at line 105,
> which ends at `assert skill_entries`: that *an* entry exists, not that it delivers everything.
>
> **Two projects, so not a local accident:** `paratext-copilot` lacks `health-check` too.
- [x] **Fixed 2026-09-19, and the ruling it was waiting on dissolved.** Report-versus-install was
      the wrong question: the Captain ruled that `sp doctor` and `sp init --update` are synonyms
      and share code, so both restore. The starter examples are the only difference, and that is
      now `policy: example` on four catalog rows rather than a flag in code.
- [x] **Answered — the `Scope.PROJECT` check excluded project skills, twice over.** The filter at
      `doctor.py:635` was `source in (CONSTANT, TEMPLATE)` and project skills are `source: sp-home`;
      and the check took its expected count from the files that existed, so absence could not be
      represented. Both deleted, with `skills_reachable` and `restore_when_absent`. Guarded by
      `tests/test_doctor.py::test_a_project_missing_a_shipped_skill_is_not_reported_green`, which
      runs through `main(["init"])` and `main(["doctor"])` rather than the Python API.
- [x] **The CLI now has a specification** — `docs/ai-context/sp/command-line.md`, shipped to every
      project, with `tests/test_cli_is_documented.py` failing in both directions when it and the
      parser disagree. Nothing had described the commands at all.
- [ ] **Still to do: `sp init --update` stops having its own code and calls doctor** (§4.2 of
      `plan-init-doctor-unification.md`). They now *behave* the same; they are not yet one
      implementation, which is what the Captain ruled on 2026-08-23 and again on 2026-09-19
- [ ] **Still to do: replace the hello-world examples with scripture examples** (Captain,
      2026-09-19). `policy: example` is the row that says which four files those are
- [ ] **File this as a GitHub issue** — the convention at the top of this file says bugs go there.
      Not filed; creating issues needs the Captain

### 🐛 `sp init`'s write paths — three defects, found migrating discourse-flow → #215
> Filed together because they share a cause: `sp init` writes through paths `sp doctor` has
> already hardened, and reports failure inconsistently.
- [ ] `_upsert_delimited_block` writes without unlocking; `doctor._restore` unlocks
      (`doctor.py:194`). A read-only `CLAUDE.md` crashed `sp init --update`. **Needs a ruling
      first:** unlock and write, or skip and report? The read-only bit may be protection.
- [ ] `sp init` is not atomic — the crash left a half-updated assistant configuration
      (Copilot done, Claude Code / Cursor / Windsurf not) and said nothing but a traceback.
- [ ] The registry write fails as a warning naming `~/.sp/ai-context/project-index.md.yaml` —
      a filename retired on 2026-08-24. The store is deliberately read-only, so that failure is
      the normal case, not an exception.

### ▶ Do these in this order — set by the Captain, 2026-08-24

1. **`overview.md` is two documents sharing one path → #210.** Small: a rename in *this* repo
   plus an audit of the other three `docs/ai-context/` files. It is why `sp doctor` must not be
   run here.
2. **21 shipped documents from Python constants to `source: template` → #211.** Wide and
   mechanical. Blocked on #210: naming a template while `overview.md`'s reader is ambiguous
   means naming it wrong and moving it twice. Finishing it is what makes `sp doctor` safe here.
3. **`format: usj` → #200.** Everything it needs is ruled through `f93e9ca`. Start from the
   parked local tag `wip/scripture-200`.

> **Before starting 3, one ruling is needed** — §4.4 of
> `project/plans/design-scripture-representations.md`, the Greek/Hebrew asymmetry. Five `=>`
> slots there are empty; that one blocks. `include: [senses]` yields `{domain, ln}` on SBLGNT and
> `{lexdomain, contextualdomain, coredomain, sdbh, sensenumber}` on WLC. The recorded
> unnormalised position is a **proposal, not a ruling** — implementable as written, but a
> normalising ruling changes the payload and anything built first is wrong.

> **Insurance taken — corrected 2026-09-27.** `wip/scripture-200` **is on the remote**:
> `git ls-remote --tags origin` finds it. This entry asked for a push that had already happened,
> so `project/plans/design-scripture-editions.md` is no longer a single point of failure. Read it
> with `git show wip/scripture-200:project/plans/design-scripture-editions.md`.

> **Deliberately not scheduled:** #209, the repository rename. Filed with its migration detail
> and an order of operations, to be picked up when the Captain chooses.

### 🆕 Opened 2026-09-01 — five issues, order not yet set
> **Where these sit relative to the ordered list above is the Captain's to set.** They are
> recorded here because the task list is the queue; `HANDOFF.md` carries only session residue.
> One is built: #225, rules cited by id — `fcd4c67` on `dev`, carrying `Closes #225`. **#225 is
> now CLOSED** (verified 2026-09-27); this line read "still open on GitHub" after the merge that
> closed it. Guarded by `tests/test_record_closure_claims.py`, which checks closure *claims* and
> cannot catch a claim that has gone stale in the other direction.
- [x] **Remove `optional:` from prompt frontmatter → #228. Shipped in 0.2.1.26 — but #228 is
      still OPEN on GitHub** (checked 2026-09-27), two releases after it shipped. Close it or say
      why it stays open. Breaking: both
      header forms are refused by `sp lint` and `sp run` with one shared message. The shipped
      discipline now teaches the key's absence rather than `optional: [perspectives]`, so `sp init`
      no longer installs the retired convention.
  - [ ] **Consumer migration is outstanding.** `nida-institute/discourse-flow` carries **non-empty**
        `optional:` lists, so it will fail lint against 0.2.1.26 until each name moves to
        `requires:` or is deleted. Mechanism and evidence:
        `collab/discourse-flow/2026-09-01-dotted-requires.md`. Their repository, their change —
        tell them the release is out.
- [ ] **Extract the biblical-text convention layer → #226.** Design in
      `project/plans/design-biblical-text-conventions.md`; the middle layer lives in
      `awesome-biblical-data`. D3 is ruled. **D1, D2, D4 and D5 are unanswered `=>` slots and are
      the Captain's** — do not answer them.
- [ ] **Epic: enforce rules, don't instruct them → #230.** The AI context is ~27,000 words read at
      session start, and keeping it enforced currently depends on the Captain knowing all of it.
      Substantially advanced in 0.2.1.26 and still open — read `CHANGELOG.md` for what shipped,
      not this entry. Each rule now declares `enforcement:` and `scope:` in `data/ai-rules.yaml`,
      which is the single source for the triage; the counts once kept here are not maintained.
  - [x] **The `lxml-for-xml` violation is fixed.** `src/llmflow/plugins/xml_entry_to_base_json.py`
        imports `lxml.etree`, and `tests/test_lxml_not_elementtree.py` refuses an
        `xml.etree.ElementTree` import anywhere in `src/`, so the rule now holds by test rather
        than by attention.
  - [ ] **Still open in the epic:** the nine rules classified `guardable` — a test is possible and
        not yet written. `data/ai-rules.yaml` names them; no separate list is kept.
  - [ ] **Candidate guard, unruled:** `HANDOFF.md` is stale if its date is older than HEAD's
        commit date. The Captain has not ruled whether this belongs in #230 or its own issue.
- [ ] **Completion reports, requirement softening, decision churn → #229.** Filed; **explicitly
      not being chased.** The remedy is recorded in it: checklists, and never ticking a box
      without showing the evidence.

### ✅ Settled 2026-08-24 — the #204 catalog questions are all ruled
> `project/plans/plan-init-doctor-unification.md` Q1–Q6. **Built:** nine catalog rows (the four
> hello-world examples `generated`, the four audit documents `create-once`),
> `.github/copilot-instructions.md` now block-managed like its two siblings, and the two-index
> split — `project-index.md` (`create-once`, the project's own map) and `sp-index.md`
> (`generated`, **rendered from the catalog's new `purpose:` field**, so it cannot go stale).
> **Not built:** §4.1–4.3, the `sp init --update` → `sp doctor` unification itself.

### ⚠️ Versification — a reference means different verses in different editions → #203
> **Blocks OT use of `sil-translator-notes`.** WLC and BSB disagree by two verses on `PSA 51:1`
> and the run reports success. Fix via the Copenhagen Alliance specification, cloned at
> `~/github/copenhagen-alliance/versification-specification`.
>
> **The design content lives in `project/plans/plan-scripture-step.md` §3.-1** — the mappings, the
> `MAL 4:1` case, and the requirement that editions declare their scheme and `type: scripture` map
> before fetching. It is recorded there because an earlier condensation of *this* entry lost it:
> summarising in place is right for a session cache, but a requirement has to move to a design
> document rather than be shortened.
>
> **Two pieces shipped in 0.2.1.26, and the entry stays open.** The container now reports the
> edition's own scheme instead of the caller's requested one — it was labelling verses with a
> scheme they were not numbered in — and an edition declaring no versification is read as `eng`
> with a warning, rather than raising, with `versification: null` plus `versification_guessed`
> keeping the guess distinguishable from a declaration. Neither closes the entry: the `PSA 51:1`
> disagreement above is about the mapping being applied on the way in, not about labelling.

### 📖 Scripture editions — core landed, wiring incomplete → #200
> Commits are parked on the **local** tag `wip/scripture-200` (`05d75a5`, `34c7931`) and are
> **not on `dev`**, which was reset to `cb72cb7` so the release could ship without them.
> Cherry-pick after PR #199 merges. Design: `design-scripture-editions.md`, which exists **only
> on that tag** — not on `dev` and not in the working tree, so read it with
> `git show wip/scripture-200:project/plans/design-scripture-editions.md`.
- [ ] Pericope reader
- [ ] Docs — `docs/sp-language.md` and `docs/architecture.md` currently never mention it
- [ ] Decide whether #200 supersedes or merely cross-references #38, #39/#172, #40, #41
- [ ] `~/.sp/editions/*.yaml` were seeded with absolute paths on this machine; how editions get
      registered per machine is undecided
- [ ] Datasets record no version and the catalog is never validated; `berean-usx` points at a
      404 → #201
- [ ] Prefer discourse-flow pericopes and segments over BSB `\s1` headings once coverage allows
      → #202 *(board: Backlog)*

### 🧹 `jonathanrobie/examples.bsb` fork — keep open until upstream PR #7 is accepted
> **Decided (Captain, 2026-08-17): keep the fork open until the PR is accepted.** No GitHub issue
> tracks this; the note lives here because the constraints are local. Upstream:
> https://github.com/usfm-bible/examples.bsb/pull/7 (adds the missing `\id` to Ecclesiastes).
- [ ] **Do not delete the fork** — a fork PR depends on the fork's branch, so deleting it closes
      the PR. Only once #7 is accepted: `gh repo delete jonathanrobie/examples.bsb --yes`
- [ ] **Keep `~/github/usfm-bible/examples.bsb` on branch `dev`** meanwhile — it carries the patch
      that makes all 66 books load; without it BSB Ecclesiastes silently disappears

### 🔁 for/in syntax migration (breaking — one syntax, no aliases)
> See `project/plans/design-foreach-syntax-migration.md`. Systematic commits, one per repo.
> Migration: `item_var:`→`for:`, `input:`/`over:`→`in:` (for before in). Old keys fail loud.
- [x] **Core engine** — runtime/schema/linter/tests/docs (`86b3f2b`, pushed `dev`)
- [x] **discourse-flow** — committed + pushed (clean)
- [x] **discourse-flow-hebrew** — committed + pushed (clean)
- [x] **semdom-greek-lexicon** — pipeline committed `0e050f6` (incl. in-file WIP); not pushed
- [x] **macula-lxx-greek** — pipeline committed `b55fca7`; not pushed
- [x] **image-scene-descriptions** — pipeline committed; not pushed
- [x] **Fast-follow** — `tests/test_doc_examples_lint.py` + filled `ALLOWED_STEP_KEYS` gaps
      (`content`, `key`, `where`, `offset`, `columns`) + `prompt_file` doc fixes
- [x] **json-reliability.md** — `response_mime_type`/`response_schema` were real Gemini keys
      missing from `ALLOWED_STEP_KEYS` (doc was correct); added them + re-included ai-context
      in the doc-lint scan. No ai-context edit needed.
- [x] **Release** — re-cut `v0.2.1.20` shipped 2026-07-14: GitHub Release (3 binaries) + PyPI 0.2.1.20. (Hit a PyPI trusted-publisher/workflow-rename snag; fixed — see RELEASE_CHECKLIST failure modes.)

### 🔥 Monday priorities
- [ ] **Fix GUI Content Lifecycle** — Content Lifecycle page displays blank, needs debugging
      *(no GitHub issue; this file is the only record)*

> **PyPI publishing is automated — there is no task here.** Kept as reference because the note
> that occupied this slot described a manual flow that no longer exists (it named v0.2.1.14, the
> package `llmflow`, and a password/API-token/`hatch publish` sequence).
>
> - `release.yml` job `publish-pypi` uses PyPI **trusted publishing** (OIDC, `id-token: write`)
>   and is gated on the `pypi` **GitHub** environment approval — not a PyPI login. No password
>   and no API token are involved.
> - The package is **`scripture-pipelines`** (`pyproject.toml:2`), not `llmflow`;
>   `pypi.org/project/llmflow` does not exist. Published: 0.2.1.18, .19, .20, .22, .23.
>   Verify at https://pypi.org/project/scripture-pipelines/
> - PyPI account: `jonathan.robie@gmail.com` (also the `authors` entry in `pyproject.toml:5`)
> - **Do not rename `release.yml`.** Trusted publishing matches on the workflow *filename*;
>   renaming it breaks the OIDC claim with `invalid-publisher`. Update the PyPI publisher config
>   (project → Manage → Publishing) first. Full failure mode in `project/RELEASE_CHECKLIST.md`.

### 🎓 Workshop readiness (main next goal)

> **#204 and #32 are CLOSED and their sections were deleted 2026-09-27.** Both carried unticked
> boxes for work that had shipped — #204 eleven of them, #32 two. Verified with
> `gh issue list --state all`. Git holds what went; `git log --diff-filter=D` finds it.

**Two things survived those sections because they are still live, and one ruling needs a home:**

- [ ] **Most of `~/.sp/` is still not in the package → #181, which is OPEN.** `drift-patterns.md`,
      the whole `user-context/` directory, and several disciplines are unobtainable by any
      `sp init` on a fresh machine. This was #204's most substantial item and #181 is where it
      lives now; do not re-derive it from the deleted text
- [ ] **Nothing tests a clean machine.** No run from a clone with an empty `HOME`. The count in
      the deleted text said "2620 tests pass and none caught any of the above"; the suite is
      **5878 passed / 7 failed** as of 2026-09-27 and the gap is unchanged
- [ ] **Move one ruling to `CHANGELOG.md` before it is lost** — *"`--update` is always a flag on
      its parent command, never a standalone subcommand"*, so `sp init --update` and
      `sp setup --update`, never a bare `sp update`. It lived only in the deleted #32 section.
      `plans-are-temporary` puts a ruling in the CHANGELOG; **that edit is not in this change's
      scope and needs the Captain**

## 📋 Backlog

### 🪪 Retiring the name `llmflow` → #265, #209

> **Set aside by the Captain 2026-09-29: low priority for today.** Filed so it is not
> re-derived; not scheduled.

- [x] **Ruled 2026-09-29:** the public API is imported as **`import scripture_pipelines as sp`**,
      and **`llmflow` does not survive** — no shim, no alias, no grace period. Design, the method
      and its four risk tiers: `project/plans/design-public-api-namespace.md` → **#265**
- [x] **`docs/llmflow-language.md` → `docs/sp-language.md`**, done 2026-09-29 on the Captain's
      *"there is no llmflow language"*. Engine-only and uncatalogued, so no project is orphaned.
      17 referring files updated, records left alone;
      `hatch run pytest tests/test_init.py tests/test_ai_context_layout.py
      tests/test_window_cursor_guidance.py tests/test_ai_rules_single_source.py` → **63 passed**
- [ ] **The quickref rename waits on a catalog that can retire a path.** `file_catalog.py` has
      **no orphan handling** — grepped 2026-09-29 — so renaming a `policy: generated` shipped file
      writes the new name beside the old in every existing project and nothing ever removes the
      stale one. Needs a `retires:` field or equivalent first — evidence:
- [ ] **`llmflow.log` → `sp.log`.** Ruled 2026-09-29. A behaviour change, not prose: 26 files,
      including `modules/logger.py`, 13 test files, `data/file-catalog.yaml` (so the generated
      `.gitignore` follows), the shipped `sp-debugging.md` discipline, and `CLAUDE.md`, which is
      the Captain's. Wants a failing test first and a CHANGELOG entry — evidence:
- [ ] **Two generated files still name the old doc path** — `docs/ai-context/sp/index.md` and
      `sp/scripture-representations.md`. They come from the file catalog, so the route is
      `sp init --update` followed by `hatch run python tools/update_ai_context.py`; not run,
      because it does more than the rename asked — evidence:

### 🧹 Debug/log docs follow-ups + `sp` terminology audit → #180
> Fallout from documenting the `log_level: debug` request/response dump feature
> (added `docs/architecture.md` §15; new `~/.sp/conventions/sp-debugging.md`).
- [ ] Cross-ref the debug-dump feature from `docs/sp-language.md` — `log_level`
      is documented there (≈ line 57) only as a verbosity knob; point it at
      `architecture.md` §15 so the dump behavior is discoverable from the language spec.
- [ ] **Decide:** rename the log file `llmflow.log` → `sp.log`? Core change
      (`runner.py` default `log_file='llmflow.log'`, the `--log` flag default, and the
      debug-dir log co-location). If yes, update the docs that name it literally
      (`architecture.md` §15, `~/.sp/conventions/sp-debugging.md`) in the same change.
- [ ] **Audit** for other stale references worth changing at the same time: product/CLI
      name (`llmflow run/lint/template` → `sp`) across `docs/`, any remaining `.llmflow/`
      path fictions, and consumer-repo docs (e.g. ears-to-hear
      `docs/architecture/debugging.md` still uses `llmflow …` command names and
      leaders-guide framing). Scope the sweep before making edits.

### 🎓 Workshop readiness
- [ ] Replace hello-world example with a domain-relevant pipeline
      (e.g. translation notes for a Bible passage, or back-translation check)
- [ ] Polish error messages — every ❌ should say what to fix, not just what went wrong
- [ ] Workshop handout: 1-page "what is this and why do I care"
- [ ] API key story for workshop: shared org key so participants don't each need one

### 🚀 Publishing
- [ ] **Missing project files: `CONTRIBUTING.md`, `SECURITY.md`, issue/PR templates → #33.**
      Retitled upstream; this line said "Clean up repo for public release (metadata, data
      licensing, .gitignore gaps, README, history audit)" until 2026-09-27. Read the issue for
      the scope, not this line
- [x] Published to PyPI as `scripture-pipelines` — latest 0.2.1.23. (The name `llmflow` was never
      used; see the PyPI note under Monday priorities.)

### 🗂 Pipeline data operations

#### ⚠️ Verse range operations → #169 — **partly built, and the plan says otherwise**
> **Corrected 2026-09-13.** This entry said "6 decisions needed before implementation". The
> module is built: `src/llmflow/utils/verse_ranges.py`, with `tests/test_verse_ranges.py` at
> 371 lines. What is stale is the plan beside it.
>
> `project/plans/plan-verse-range-set-ops.md` declares *"Approved 2026-08-17 — authoritative for
> the implementation (names, signatures, files)"* and *"No code yet"*. Both are now false, and
> the code took a different shape:
>
> | | plan says | code does |
> |---|---|---|
> | naming | `verse_range_overlaps`, … | `overlaps`, `contains`, … |
> | representation | 8-char sort key `BBCCCVVV` | `Range` dataclass, **book-local ordinals** |
> | adjacency | `adjacent` | `touches` |
> | also present | — | `equals`, `select`, `RELATIONS` |
> | **not built** | `union`, `intersect` | — |
>
> This is a `one-design` breach: two documents and one implementation, disagreeing. Reconciling
> them is a ruling, not a cleanup — the Captain's.
- [ ] **Ruling needed:** does the shipped `Range`/`overlaps` shape stand and the plan get
      rewritten to match, or does the code move to the approved `verse_range_*` spec?
- [ ] `union` and `intersect` are unbuilt. They are the operations an alignment mapping would
      compose with, so this blocks the idea in the alignment section above
- [ ] Design document: `project/plans/design-verse-range-operations.md` (data model);
      `plan-verse-range-set-ops.md` (spec and work order)
- [ ] List transformation: flatten, project, slice as framework primitives → #167
- [ ] Predicate filtering: filter lists by value / cross-list membership → #168
- [ ] Accumulator initialization in `variables:` block → #170

## ✅ Done

---
_Audit notes and QA reports → project/audits/_
_Pipeline decisions → project/decisions.md (create when needed)_
_Project board → https://github.com/orgs/nida-institute/projects/13_
