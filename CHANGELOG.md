# Changelog

## Unreleased

### Added

- **A rule can now say a gate stops the act, which two rules were already relying on and could not
  express (#230).** `enforcement` had four values, all describing *detection*: a test that fails
  today, one that could, one that could not. The strongest mechanism in use here is neither — a
  `PreToolUse` hook or an `ask` entry in the operator's permissions refuses the act or puts it in
  front of a human **before it happens**. Rules held that way were recorded as `judgment`, the
  weakest value, because the vocabulary had no word for them.

  `enforcement: gated` and `scope: harness` are that word, and the generated rules document leads
  with them — prevention above detection, judgment last.

  | rule | was | gated by |
  |---|---|---|
  | `issues-need-approval` | `judgment` | `Bash(gh issue create:*)` |
  | `commit-authority` | `guardable` | `Bash(git push:*)`, `Bash(gh pr merge:*)` |

  **A gate is not verifiable from this repository**, and the value says so rather than hiding it:
  it lives in the operator's environment, so on an unconfigured machine those rules are `judgment`
  like any other. `guard:` names a file the tests open; `gate:` names something they take on trust,
  which is why a `gated` rule must name it — a reader can then check their own configuration.

- **New rule `declared-not-inferred`.** Rely on a published format, on a declaration this project
  maintains, or on a measurement anyone can re-derive; not on the file tree, a directory layout, a
  naming convention, how often a value occurs, or a mechanism that merely sounds plausible. A
  hand-kept list is not a declaration — it is an inference about one, and it drifts.

  The general form of three separate rulings, with the worked cases in
  `project/plans/design-what-the-engine-may-rely-on.md`, including the four inferences that
  produced wrong answers in two days: the file tree read as a specification, a plausible mechanism
  that measurement refused, a frequency described as a failure rate before that was established,
  and assuming what a value means to whoever receives it.

### Fixed

- **`reference-data-is-json` said no test held it while its test was passing.** Classified
  `guardable` — "a test is possible and nobody has written it" — with
  `tests/test_reference_data_is_json.py` in the repository and a CHANGELOG entry saying the rule was
  enforced. So the file told every session the rule depended on attention.

  The classification checks had run one direction only: a rule *claiming* a guard must name one
  that exists. Nothing asked the reverse. `test_a_rule_whose_test_exists_is_not_still_called_guardable`
  now derives the correspondence — a rule id maps to `tests/test_<id>.py` with dashes as
  underscores — so writing the obvious test and forgetting to reclassify is a red test. It is a
  floor rather than a ceiling: `lxml-for-xml` is guarded by `test_lxml_not_elementtree.py`, which
  the pattern cannot see.

### Added

- **Copy forcing: a field's role is declared, and two checks read it (#230).** A role map sits
  beside its schema — `X.roles.yaml` next to `X.json` — and says which fields are `evidence`,
  copied from the input so the model attends to it before deciding, and which are `content`, the
  thing the pipeline exists to produce. `supports` states which evidence backs which claim.

  ```yaml
  fields:
    verse:                               [evidence]
    opening_word_id:                     [evidence, content]
    levinsohn_signals_to_cite[].signal:  [evidence]
    is_boundary:                         [content]

  supports:
    levinsohn_signals_to_cite[].verdict: ["levinsohn_signals_to_cite[].signal"]
    is_boundary:                         [verse, greek_quoted]
  ```

  Two role words, list-valued because a field can honestly be both. The role belongs to the
  (schema, field) pair rather than to the field name: the same name is copy-forced evidence in one
  step and payload in the next, so a project-level file could only lie about one of them.

  **`sp lint` runs two checks, and neither needs a model call.**

  1. **The order rule** — a supporting path must precede what it supports in schema property
     order, because that is the order the model generates in. Checked at the top level *and*
     inside an array item, comparing two paths at the first segment where they diverge. Evidence
     written after its claim cannot have forced it.
  2. **Structural validity** — every declared path exists in the schema, including `a[].b` through
     `items.properties`; no path declared twice; roles list-valued.

  This is why declaring beats inferring: `discourse-flow` found the failure the order rule catches
  by generating seven artifacts and scanning them, and the cause was ordering — visible in the
  schema alone. `ears-to-hear` measured the same class of defect in one of their own schemas.

  **Reported, never judged.** Findings are warnings; a pipeline decides what is fatal.
  `discourse-flow`, reconciling two of their own rules: *"`sp` computes the verdict and exposes it;
  the pipeline says `fatal` or `report`."*

  A role word the engine does not define is carried without complaint — a project may declare a
  role of its own for a field a later step consumes and no reader sees, and these checks do not
  touch it. A `supports` path need not appear in `fields`: what the engine needs about a field it
  orders is its position, not a name for it.

  **Not included, by ruling:** severity, occupancy reporting, `empty_expected`, audience. Each
  needs a judgment about somebody else's data. The declaration is machine-readable and complete,
  so a project computing any of those reads the same file.

  Verified against the five role maps `discourse-flow` had already written — 92 fields, 21
  `supports` entries, no findings — and against inverting one of their real entries, which
  produces one. A check that reports nothing on sound input and something on unsound input is the
  only kind worth shipping.

  Unbuilt from the design: `identifies` and the coverage check, which compares identifiers
  returned against identifiers requested and so needs a response rather than a schema.

- **`frame` is carried by `include: [referents]`.** It holds the predicate's semantic roles as
  participant ids — `A0:190230010031; A1:190230010022` — populated on about a fifth of words in
  both corpora, and it belonged to no family, so no pipeline could ask for it.

  `data/include-families.json` had listed it under `not_carried` as *"syntactic frame, belongs with
  `syntax`"*. That was filed before `include: [syntax]` was ruled standoff: the `syntax` payload is
  the constituency tree with leaves carrying only references, so a per-word attribute cannot ride
  in it. In Lowfat terms `syntax` is the `wg` node tree while `frame` is an `m` leaf attribute, and
  the families are organised by form.

  `referents` is the right home because `frame` is the semantic-role counterpart to `subjref`'s
  grammatical one, and the two come apart where a discourse boundary criterion bites: a passive
  whose subject is the undergoer reads to `subjref` as "same participant, still the subject", and
  the role reversal is invisible. Reported by `discourse-flow`, who found it correcting a Psalm 23
  division — `A0` and `A1` reverse between vv. 2–3 and v4, and v6 introduces a participant absent
  from the earlier cast.

### Fixed

- **A Hebrew discourse citation resolved against the wrong word, and 85–99% of them failed
  (#230).** `resolve_citation` matched Levinsohn's 1-based index against *row position*. That is
  right for Macula Greek, which has exactly one row per word, and wrong for Macula Hebrew, where a
  word written with a prefix or suffix occupies several rows: Ruth 1:1 is 33 rows over 19 words, so
  word 4 begins at row 6. Reported by `discourse-flow` while migrating to `include: [discourse]`,
  and confirmed here before anything changed.

  | | rows per word | `verified` before | after |
  |---|---:|---:|---:|
  | Greek `MRK 1`, `1JN 1`, `PHM 1` | 1.00 | 94–100% | unchanged |
  | Hebrew `JON 1` | 1.62 | 1% | **96%** |
  | Hebrew `RUT 1` | 1.58 | 2% | **85%** |
  | Hebrew `OBA 1` | 1.51 | 5% | **91%** |
  | Hebrew `HAG 1` | 1.53 | 7% | **87%** |
  | Hebrew `PSA 51` | 1.66 | 10% | **87%** |

  The `ref` column already carries the word index in both corpora — `RUT 1:1!4` *is* word 4 — so
  the fix reads what the edition declares instead of inferring it from how the file is laid out. No
  new configuration, no per-edition flag, and no knowledge of morphology.

  **The word id now addresses the word.** Macula ids are `BBCCCVVVWWWP` in Hebrew and
  `BBCCCVVVWWW` in Greek, per *MACULA Hebrew Treebank for OSHB* §2.1, where `WWW` is the word
  index and `P` the word part. The payload had been reporting a morpheme id, so a consumer
  highlighting it showed `הַ` rather than `הַשֹּׁפְטִ֔ים`. Dropping `P` yields the same shape Greek
  already uses, so one format serves both languages.

  A second instance of the same defect was in `resolve_verse`, which carried its own row-indexing
  for notes: a note at index 4 anchored to the second morpheme of word 2.

  **What this does not fix**, stated so it is not assumed: 79 of 521 citations in `RUT 1` still
  report `disagrees`, and the offsets scatter — +1, +2 and −1 — with 28 having no single found
  position. There is no further systematic cause. A maqqef hypothesis was measured and refused:
  `RUT 1:1` has a failure at index 11 with no maqqef in the verse. `Reported Speech` at 1 verified
  against 7 disagreeing is the one outlier worth a look.

- **A citation's span was discarded, for a quarter of the corpus (#230).** `OSIS_REF` had no
  end-capture, so `Mark.1.2!9-Mark.1.2!15` matched, consumed `Mark.1.2!9`, and dropped `!15`;
  `Citation` carried one index and no end. Every spanning citation therefore loaded with its
  opening word and its Greek intact, and its extent gone.

  `discourse-flow` reported it for quotations — 47 in Mark carrying 0 spans, their issue #92, a
  loss they had assumed was their own. Measured against LGNTDF, it is far wider: **13,096 of
  52,257 citations name a span**, led by `Focus+` (2,750), `Referential PoD` (2,065),
  `Reported Speech` (1,491) and `Situational PoD` (1,474), with `OT quotes` sixth at 644.

  `Citation` now carries the closing end as a reference in its own right — book, chapter, verse,
  word — because **657 spans close in a later verse** and some cross three
  (`Acts.26.16!14-Acts.26.18!71`). The payload reports `end_index`, `end_verse` and, where it
  differs, `end_chapter`; and `id_end` where this verse holds the closing word. A span closing
  elsewhere is reported without an id rather than dropped, and rather than given an id from the
  wrong verse's rows.

  The end is stated in full whether or not it falls in the opening verse, so `None` means "no
  span" and nothing reads a missing verse as "the same one". A `Citation` built by hand with only
  `end_index` fills the rest from its opening, so a bare closing index cannot silently become a
  span that closes in no verse at all.

  **Breaking:** `parse_osis_ref` returns five values instead of four, the fifth being the closing
  reference or `None`.

### Changed

- **The role-map example in `design-declaring-field-roles.md` §7 parses.** It did not: a path used
  as a value inside a flow sequence opens a nested sequence, so
  `a[].v: [a[].s]` fails with `ParserError`. `discourse-flow` copied the published example and four
  of their five maps failed. Paths used as values are quoted now, with the parse table and the
  block-style alternative beside them. A second broken block, which they had not hit, was found by
  parsing every block in the document rather than only the one reported.

## 0.2.1.26 — 2026-09-03

### Added

- **`include: [discourse]` reads a Hebrew corpus, not only a Greek one (#230).** The loader
  accepted a single corpus shape: `<feature>` document roots, OSIS book names, and one flat
  directory. HOTDF-LS — Hebrew Old Testament discourse features — uses `<markup>` and
  `<annotations>` roots, references already written in USFM (`LEV.1.14`, `1SA.2.15`), and files in
  subdirectories. Every file was therefore skipped and the payload came back empty, which is
  indistinguishable from a passage with no data.

  Three changes, and the second removes a duplicate rather than adding a table: document roots are
  now declared as a set; book names resolve through `llmflow.books.resolve`, which accepts either
  spelling because `data/book-names.json` single-sources them (#218); and the corpus glob recurses.
  The 27-entry OSIS translation table this module carried was a second copy of part of that file,
  and being New Testament only it refused every Old Testament reference.

  With this, every implemented `include:` family serves both Greek and Hebrew. An edition points
  at its corpus with `discourse_path` in its registry entry.

- **An edition that declares no versification is read as English, and says so (#203).** Much of
  the translation world uses English versification without meeting the issue, so a project may
  have no versification file at all. Reading such an edition across schemes used to raise; it now
  assumes `eng` and warns, every time, because where the assumption is wrong it is wrong by whole
  verses.

  The payload keeps the guess apart from a declaration:

  ```json
  "versification": null,
  "versification_guessed": "eng"
  ```

  so a consumer reading only `versification` gets the honest answer and cannot mistake a guess for
  a fact. `versification_guessed` appears only where there was a guess to report.

- **Book names resolve for every published scheme, and it is now guarded (#218).** All 66 OSIS ids
  from CrossWire and all 73 SBL abbreviations from *The SBL Handbook of Style* (2nd ed., 124-125)
  resolve to the right USFM code, in plain and dotted form — 140 checks. Most of that was already
  true, as a consequence of matching being case-insensitive and ignoring dots and spaces, and
  nothing asserted it: a tidy-up of `normalise()` could have broken every commentary-style
  citation with a green suite.

  Two spellings were missing and are added from those sources: `Qoh` for Ecclesiastes, and the
  Septuagint's `1-4 Kgdms` for Samuel and Kings. `3 Kgs` and `4 Kgs` name nothing in any scheme
  and are asserted to stay unresolved.

- **New shared discipline `working-for-a-person.md`.** Installed into every project by
  `sp init`, and shared with Human at the Helm. Two rules, checked at different moments: be
  curious about the person you are working for *before* choosing an approach — what this is for,
  who it serves, why the data matters to them, what they know that you do not — and optimize for
  their time rather than the machine's, because their attention is the scarce resource while
  compute, tokens, a re-run and a rewritten file are cheap.

  Written from two sessions of evidence rather than from theory. What it names: asking late and
  narrowly, in the AI's own vocabulary, about implementation details instead of early and plainly
  about the goal; treating the file tree as the specification and reasoning from it as though it
  were the human's design; adding a third option to a question that posed two; delivering an
  analysis where an issue recording a question was asked for; withholding a recommendation that
  costs cents in order to spend hours of the human's time; and answering a one-sentence question
  at a hundred lines.

- **New rule `check-the-source-not-the-rendering` (#230).** A check takes what it verifies from
  the declaration that produced the artifact — the YAML, the JSON, the schema, the AST — and
  compares an artifact against what its generator emits. Where a subject genuinely must be
  derived, because free prose has no parser, the check asserts the derived set is non-empty and
  compares it against a declared count where one exists.

  Written after two guards in this repository were found inert, and a third generator found to
  have gone stale for seven months while appearing maintained. Classified `judgment`: no
  non-fragile test for it is apparent, which is the rule making its own case.

- **`llmflow.runner` declares its import surface in `__all__`.** Nineteen names are imported from
  this module elsewhere in the tree, and only three of them — `logger`, `run_pipeline`, `run_step`
  — are defined there. The rest are re-exports, kept because `llmflow.runner` was their home
  before they moved into their own modules.

  Nothing said so, which made them look like dead imports. Clearing the source tree's lint
  deleted two, and each deletion broke callers at *import* time rather than at the call:
  `save_content_to_file`, which `llmflow.utils.llm_runner` imports back from the runner, and
  `_MISSING`. `tests/test_runner_reexports.py` now parses every `from llmflow.runner import` in
  `src/` and `tests/` and requires each name to be declared, so removing one is a deliberate act
  rather than a side effect. It found a nineteenth name on its first run that a line-based search
  had missed, imported inside a function body.

- **New rule `say-which-kind-of-nothing` (#230).** A payload distinguishes *asked and there is
  none* from *never asked*: an empty container for the first, `null` for the second. A consumer
  cannot tell those apart from an absent field, and the difference decides whether silence is a
  finding or a gap.

  Two states, each with one meaning: `{}` or `[]` says the lookup ran and found nothing, and
  `null` says there was nothing to look in, so no lookup ran. A key may be absent where another
  declaration accounts for it — `include:` is such a declaration — but absence carries no meaning
  of its own, and cannot: OpenAI's strict structured output marks every property `required`, so a
  model's response has no way to express it.

  The engine reports which of the two it produced and stops there. What either one *means* is
  application semantics and stays with the pipeline that declares it, which is why the rule asks
  only that whichever is meant be visible in the data.

  This is what made the empty Hebrew discourse payload above a reportable defect rather than a
  plausible answer: it said the lookup had run and found nothing, when no lookup had run. Guarded
  for the scripture container by `tests/test_say_which_kind_of_nothing.py`; `judgment` elsewhere.

- **`reference-data-is-json` is enforced (#230).** `tests/test_reference_data_is_json.py` asks
  PyYAML for each scalar's resolved tag and compares it with the text as written, so a bare
  `1:1` read as the integer `61` and a bare `NO` read as `False` are both caught — the two
  coercions the rule exists for. No pattern is matched against the file.

  Scoped to the YAML this codebase loads: `data/`, `pipelines/` and the shipped templates.
  `.github/workflows/*.yml` are parsed by GitHub rather than by us, and their `on:` key resolves
  to `True` under PyYAML — correct there, and noise here.

  This is the third of #230's six rule guards. Nothing in scope violates it today.


- **A dotted name in a prompt body is refused, by both `sp lint` and `sp run` (#230).** Nothing
  can fill `{{scene.title}}`: a placeholder is filled by matching its name against a literal
  context key, and a dotted name is not one. `resolve()` does not reach it either — it
  substitutes `${var}` and `{var}` and leaves a `{{...}}` placeholder untouched, inner braces
  included. Measured, not assumed.

  Nothing had refused it. Declaring the name satisfied the declaration check, declaring it
  optional satisfied the required-variables check, and the placeholder was then sent to the
  model unfilled. It is now an error in `validate_gpt_body_declares_all_vars` and in the
  runtime contract check, so a run that never lints fails too. Declaring the name no longer
  silences it — that was what hid the defect.

  `tests/test_prompt_bodies_use_flat_names.py` covers the linter, the runtime, the
  declared-anyway case, and every prompt this repository holds or ships. It scopes itself by
  location — a `.gpt` file, or markdown inside a `prompts/` directory — because documentation
  that shows an example contract parses as though it had one, and prose must stay free to name
  the form it warns against.

- **The rules no test can catch are listed apart from the rest, and the split is declared in the
  data (#230).** `sp/rules.md` ran 35 rules together as one list, so the twelve that genuinely
  require attention sat among twenty-three a test already catches or could — which spends a
  reader's attention on the wrong ones. Each entry in `data/ai-rules.yaml` now declares
  `enforcement:` — `guarded`, `partial`, `guardable` or `judgment` — and the renderer groups by
  it, so the twelve appear under their own heading at the end, with a line saying why they are
  the ones to carry.

  The classification is the triage recorded in #230, transcribed rather than re-derived. It is
  declared in the data so nothing keeps a second copy: a rule gaining a guard moves group by one
  edit, and `rules-a-test-can-catch` is never a hand-maintained list. Totals: 7 guarded, 4
  partial, 12 guardable, 12 judgment.

- **`lxml-for-xml` is enforced, and the violation it had been describing is fixed (#230).**
  `tests/test_lxml_not_elementtree.py` walks the AST of every module under `src/llmflow/` and
  fails on any `xml.etree` import, in either form. `plugins/xml_entry_to_base_json.py` had
  imported `xml.etree.ElementTree` since before the rule existed and now uses `lxml`.

  One behaviour change came with it: `lxml` refuses a `str` carrying an encoding declaration, so
  the plugin parses bytes, and malformed input now raises `lxml.etree.XMLSyntaxError` rather than
  `xml.etree.ElementTree.ParseError`. Both subclass `SyntaxError` but neither subclasses the
  other, so a caller catching the old class must be updated. Covered by two tests.

  This is the first of the six rule guards scheduled in #230; five remain.

### Changed

- **A rule is cited by its id, not by its position in the list (#225).** The shipped rules
  document — `docs/ai-context/sp/rules.md`, installed into every project by `sp init` — rendered
  an ordered list, so a citation could only name a position. Collapsing or adding a rule
  renumbered everything after it and silently repointed every existing citation at the wrong
  rule. Each entry now leads with its stable id and carries no number:

  ```
  - `verses-are-milestones` — **Verses are milestones, not units.** …
  ```

  `data/ai-rules.yaml` had asked for id citations since it was written, and numeric citations
  kept being written anyway: the number was where the eye landed, and the id appeared nowhere in
  the rendered output at all. Order still groups related rules for reading, and reordering is now
  free — renaming an id is the breaking change.

  Nine numeric citations across the documentation, tools and tests were converted to ids. Two
  remain numbers deliberately: `docs/ai-context/project/rules.md` is a separate, hand-written,
  id-less list, so a number qualified by the file that holds it is unambiguous. `CHANGELOG.md`
  and the plan documents keep theirs, because rewriting a dated record would falsify it.

  A project regenerating its AI context picks up the new rendering with no action; the renderer
  behind it, `llmflow.ai_rules.render_numbered`, is renamed `render_rules`.

- **The `handoff` skill now says where the handoff file ends and the task list begins.** The
  shipped skill — `sp init` installs it into every project — asked for a handoff and a "next
  action" without ever distinguishing `HANDOFF.md` from `project/TODO.md`, so the queue leaked
  into the handoff and went stale there.

  `HANDOFF.md` carries only what dies when the work is committed: uncommitted files, which test
  is RED, the branch, the SHAs. `project/TODO.md` carries what survives: the queue, its order,
  the rulings still awaited. The next action therefore points at the task list rather than
  restating it, unless it genuinely is "finish the uncommitted thing". A new adequacy-checklist
  item enforces the distinction — a next action that would still be the next action a week from
  now belongs in the task list.

  The failure is a measured one, not a hypothetical: a handoff that led with "merge and tag
  PR #224", a queue item, went stale the moment that pull request merged and then misdirected
  for three days.

  A project picks this up on the next `sp init --update`. The skill is shared with Human at the
  Helm and the two copies were resynced, so `data/helm-sync.yaml` records it as identical again.

### Removed

- **`optional:` is no longer a key of the prompt header syntax (#228).** Every prompt parameter
  is required. An optional one needs a branch somewhere, and the branch nobody tests is where
  defects live.

  **Breaking.** Removing a key from a language means the parser refuses it: `sp lint` and
  `sp run` both reject a header declaring `optional:`, with one shared message, in both the flat
  and the nested `prompt:` header forms. Old keys fail loud, as the `for`/`in` migration did.
  Migration is one line per prompt — move the name to `requires:`, or delete it if the body does
  not use it.

- **71 invented book-name aliases, across 55 books (#218).** `data/book-names.json` had accumulated
  spellings belonging to no published scheme — coined by whoever added a book and never reviewed
  as a set. Supported input is now SBL, OSIS and USFM, complete in each case, plus the handful of
  widely-used forms that predate this and are kept deliberately: `Psalm`, `Mt`, `Mk`, `Lk`, `Jn`,
  `Rv`, `1-2 Pt`, `Philem`, `SoS`, `Canticles`, `Qoheleth`, `1-2 Chron`, `Mar`, `Lu`.

  **Breaking** for anything that relied on one of the removed spellings; an unresolved book name
  raises rather than guessing. Three schemes with a stated authority each can be checked against
  their sources, which an open-ended alias list cannot.

  The abuse it enabled is why it went rather than being policed. The linter checked only that a
  body variable was *declared*, and both lists counted, so demoting a required name to
  `optional:` silenced the error, the step ran without the value, the placeholder was never
  substituted, and the model received a malformed prompt with no warning.

  Removed in the same pass, so nothing is left teaching it: eight prompts held or shipped here;
  four reads in `utils/linter.py` and `steps/llm.py`; two error messages that instructed the
  reader to *add* the key; the `optional: [perspectives]` house pattern in the shipped
  prompt-organization discipline; the shipped language quickref; `docs/architecture.md`,
  `docs/llmflow-language.md`, `docs/getting-started.md`, `docs/global-conventions.md`; and the
  pipeline half of `docs/design/optional-parameters.md`, whose reasoning is kept because it is
  the argument for the removal. Nine tests migrated, two of which asserted the withdrawn
  behaviour and were deleted with it.

  Guarded by `tests/test_prompt_headers_have_no_optional.py` — the linter, the runtime, the
  `optional: []` case, and every prompt held or shipped here.

### Fixed

- **A placeholder is expanded exactly once, and nothing else is expanded at all (#230).** Two
  defects, both silent.

  **Expanded more than once.** Values were substituted into the template and the resolver then ran
  over the result, so any value carrying braces was expanded a second time against the pipeline
  context. Fetched content — a passage, a lexicon entry, a prior response — became a template, and
  the output still read as a well-rendered prompt. Measured: a value of `"the scroll said
  {greeting}"` came back with `greeting` substituted from the context. The template's own
  references are now resolved *before* values are injected, and never afterwards. Braces arriving
  inside a value are that data's own characters and are left alone.

  **Expanded zero times.** Names beginning with `#`, `/` or `%` were exempt from the variable
  extractor — Handlebars convention in an engine that has no conditionals — so they escaped the
  declaration check and nothing substituted them, and `{{#directive}}` reached the model verbatim.
  No prompt, template or document in the repository used those forms and nothing handled them, and
  the two skip-lists naming them disagreed with each other. They now extract as ordinary names,
  and the contract check refuses them.

  Also: `{{ name }}` with surrounding whitespace is now the same placeholder as `{{name}}` — the
  extractor stripped the spaces while substitution matched literally, so the spaced form was
  extracted, demanded of the header, and then never filled. And after substitution, any of the
  template's own placeholders still present refuses the step instead of being sent.

- **The scripture container named a versification its labels were not in (#203).** `versification:`
  states the scheme a caller's *reference* is written in; the engine maps it inward to fetch the
  right verses. It does not relabel the result — the verse markers come from the edition's own
  rows — but the container reported the request rather than the edition. Asking for `shifted`
  against an edition numbered `org` returned `⌊1:3⌋` under a label saying `shifted`, and shifted
  1:3 is a different verse. The one field telling a consumer which scheme the labels were in was
  asserting the wrong answer, and a consumer that trusted it would mis-cite every verse it quoted.

  The container now names the edition's own scheme, always.

- **Two guards had stopped guarding, silently, and the triage still counted them (#230).**
  `tests/test_ai_rules_single_source.py` parsed rules out of both rules documents with a regex
  for *numbered* list items. When the rendering moved to an id-led list, the regex matched
  nothing — so both of its checks compared two empty sets and passed. The single-source
  guarantee and the wording-drift check had been inert ever since, while #230's triage listed
  the test as one of six live guards.

  Repaired, and given a check that makes the failure impossible to repeat: the parse must find
  exactly the rules `data/ai-rules.yaml` declares, so a rendering change fails loudly instead of
  emptying the test. A fourth check compares the generated file with what its generator produces
  now — agreement between the two renderers said nothing about the file on disk, which is how a
  stale `sp/rules.md` survived a full green suite.

- **The shipped language reference taught a placeholder form that cannot work (#230).**
  `docs/llmflow-language-quickref.md` listed `{{scene.WLC}}` beside `{{language_count}}` as
  though `{{...}}` and `${...}` were symmetrical. They are not: `${...}` resolves a path through
  an object, while `{{...}}` is filled by matching its name against a literal key of the
  context — and `scene.WLC` is not a key. The reference now says so, shows passing the value in
  under a flat name via `prompt.inputs`, and keeps the invalid form as a named counter-example.


- **The generated rules document had its own headings indented into code blocks (#230).**
  `tools/update_ai_context.py` interpolated the rendered rules into an indented f-string and
  then called `dedent`, but `dedent` takes the *common* leading whitespace of every line — and
  the rendered rules are unindented, so the common prefix was empty and the frame's eight spaces
  survived into the output. The frame is now dedented before substitution.

- **A record may no longer claim an issue closed before its commit reaches `main` (#230).** A
  GitHub closing keyword fires only when the commit lands on the default branch. Under this
  project's `branching-workflow` — work on `dev`, `main` holds what has been released — every
  `Closes #N` written on `dev` leaves its issue open until the `dev` → `main` pull request
  merges. The tracking documents recorded such work as *"closed by `<sha>`"*, so a session read
  finished-and-closed where GitHub showed open.

  The shipped convention taught it: `docs/ai-context/sp/github-workflow.md`, installed into
  every project by `sp init`, said *"When this commit is pushed to GitHub, Issue #96 will
  automatically close."* It now states the default-branch condition and separates the three
  states work passes through, because they are easy to conflate and only the second is "closed":

  | state | who has it | the issue |
  |---|---|---|
  | committed to `dev` | consumer repos on the same machine, via the editable install | open |
  | merged to `main` | anyone tracking `main` | closes here |
  | released | anyone, from PyPI or a binary | closed already |

  `tests/test_record_closure_claims.py` enforces both directions, offline, from git rather than
  from prose: no record may say an issue was closed by a commit that has not reached `main`, and
  no record may list as an unfinished task an issue that a `dev`-only commit declares finished.
  The second is the half that matters locally — since GitHub cannot tell a session what is
  already implemented here, the record must, and it is now checked instead of trusted.

  **What it does not catch:** work whose commit carries no closing keyword. #210 and #211 are
  both implemented and both still open for exactly that reason, and no test can infer it.

### Test Coverage

- Added `tests/test_rules_are_cited_by_id.py` — four guards, 413 collected cases across the
  files it scans: a citation names an id rather than a number, every cited id resolves to a rule
  that exists, ids are unique, and every rule has one.
- The resolution guard found a citation naming `output-and-intermediates-are-separate`, a slug
  whose halves had been reversed; the rule is `separate-output-from-intermediates`. It had been
  green for as long as it had existed, because nothing checked that a cited id was a real one.
- Full suite: **4116 tests passing**, 25 skipped.

## 0.2.1.25 — 2026-08-29

### New Features

- **Both ways of naming a book work everywhere.** `Mark 1:1-8` and `MRK 1:1-8` are the same
  passage, and case carries no meaning — `mark`, `MARK` and `mrk` all resolve. The prescribed
  parser took only names and the read path took only codes, so each form failed in one half of
  the engine; worse, the read path turned `Mark` into book `MARK`, a code nothing resolves, so a
  run reported "no text found" for a passage that exists.

  **One declaration, `data/book-names.json`** — 66 books with number, canonical name, testament,
  original language and 271 aliases, plus the 32 deuterocanonical codes the shipped versification
  schemes use. It replaces 281 lines of dict literal that lived *inside* `parse_bible_reference`,
  where nothing else could reach it. `testament` and `original_language` are now declared per
  book rather than derived from `int(number) >= 40`, a threshold nothing stated and nothing could
  correct.

  **A reference is tokenized, not pattern-matched.** The numeric tail has a fixed shape, so the
  book is whatever precedes it, looked up rather than guessed. That is what lets `1 John 1:1`
  work — scanning forward for the first number would find the book number. A code the catalog
  does not name still parses, because a canon may carry books this engine has never heard of.

  **A range may cross a chapter and not a book**: `Mark 16:1-Luke 1:4` is refused by name. An
  ambiguous abbreviation is refused rather than guessed — `Ph` names both Philippians and
  Philemon — and that error is worded differently from the one for an unrecognised book, because
  they ask the reader for different things.

  `llmflow.resolve_book` is published, so normalising a book name needs no bespoke function.

- **A new shipped document, `docs/ai-context/sp/passage-references.md`**, installed into every
  project by `sp init`: the forms that parse, the request-side and source-side versifications,
  what `parse_bible_reference` returns and which single field depends on a scheme. A guard test
  parses every form the document shows, so it cannot document something the parser refuses.

- **`sp resource` — one surface for scripture texts and everything else the catalog describes
  (#217).** A machine that had finished setup, had the versification store, and had never
  registered a text ran a pipeline that linted clean and failed deep in execution with
  `EditionNotRegistered` — whose remedy named `sp registry`, a command with no subcommand that
  could do it. Three facts were missing, and none of them was the data: which catalog entry
  carries a readable text, which file inside it, and how to read that file.

  ```
  sp resource list                          what exists, and what this machine has
  sp resource add WLC                       fetch if needed, then register
  sp resource add WLC --no-download         register now, fetch later
  sp resource add MYPROJ --path ~/pt/MYPROJ register a Paratext project of your own
  sp resource download acai                 fetch something no reader can yet open
  ```

  **The catalog is the public one.** `resources.json` in `nida-institute/awesome-biblical-data`
  gained a `provides` block stating, per readable text, which file inside the download carries
  it, which backend reads that shape, which versification it is numbered in, and which canon it
  covers. It is vendored into the wheel, so nothing needs a network to know what exists.

  **Registrations are portable.** `~/.sp/resources/` records a path relative to its download —
  `Clear-Bible/macula-hebrew` plus `WLC/tsv/macula-hebrew.tsv` — so the file means the same
  thing on every machine. Directories are named for their source (`owner/repo` in git,
  `https-host/file` for a download), which cannot collide between contributors. An absolute
  path is still honoured, which is what a maintainer working against their own clone needs.

  **Registering something of your own is a first-class path.** A Paratext project identifies
  itself — `Settings.xml` names the versification, the directory names the project — so almost
  nothing is typed. Anything else states its `kind`. Access is not gated on licence: a project
  you can open is one you have already established a right to read.

- **Corpora live somewhere visible, and record what they are.** The texts themselves go to
  `~/sp/resources/<owner>/<repo>/` rather than into a dotfile: configuration belongs in `~/.sp`,
  a library of several hundred megabytes does not, and a hidden store is one nobody notices
  duplicating itself. Registrations — the small files saying which texts this machine may read —
  stay with the configuration, at `~/.sp/registrations/`.

  Every fetch writes `.sp-resource.json` beside the data: the source URL, the archive's SHA-256,
  its size and when it was fetched. A directory named `Clear-Bible/macula-hebrew` says which
  resource it holds and nothing about *which copy*, so a machine that fetched in June and one
  that fetched today differed invisibly (#201). Data placed by hand records nothing and is
  reported as unknown rather than assumed current.

- **`sp doctor` reports resources and their versions**, migrates `~/.sp/editions/` to
  `~/.sp/registrations/` and `~/.sp/data/` to `~/sp/resources/` itself rather than telling anyone
  to move files, and warns when a registration points at something no longer on disk.

  It also **warns when `SP_HOME` or `LLMFLOW_DATA_DIR` redirects the store.** Those exist for
  test runs and containers; on a working machine they are how one machine comes to hold several
  copies of a text, and how two projects come to disagree about what a verse says with nothing
  in either's output to say which copy it read. A warning, not an error — a container setting it
  deliberately is not broken.

### Removed

- **`sp download-data`.** It carried its own four-entry catalog beside the public one: a
  drifting copy whose `berean-usx` entry pointed at a repository that 404s (#201) and whose
  dataset names disagreed with the catalog's ids. Fetching is now `sp resource add`, or
  `sp resource download` for a resource nothing can yet read. The fetcher also gained a
  zip-slip guard — an archive naming `../` can no longer write outside its own directory.

### Changed

- **`parse_bible_reference` resolves extent from a named versification scheme (#218).** A whole
  chapter's `end_verse` came from a table hardcoded inside the function covering Psalms and two
  other books; everything else fell through to a sentinel, so `Mark 3` returned `999` and
  `Mark 3:1-999` presented itself as canonical. It now reads `maxVerses` from the scheme the
  request names, defaulting to `eng` — the request side, a fact about the person who typed the
  reference, and deliberately unlike the source side, where an edition's scheme has no default.
  **Breaking:** `end_verse` for a whole chapter changes value, and code depending on `999` will
  see a real number.

  The result carries `requested_versification`, `source_versification` (echoed from the argument,
  never resolved against, because this function has no edition), `extent_versification` — the
  scheme the number actually came from — and `book_in_versification`.

  **A chapter or verse the scheme does not have is now an error.** `Mark 3:99` and `Mark 99:1`
  parsed silently before. The message names the scheme it judged against, which matters:
  `Psalm 3:9` exists in `org` and not in `eng`, so a caller thinking in Hebrew numbering is told
  which scheme to name rather than being given the wrong verse.

  **USFM codes are accepted.** `MRK 3:14` raised while the function already held `"MRK"` for
  every display name it took; the codes are now derived from that same table.

  **A book the named scheme does not define** resolves from another scheme when exactly one
  defines it, refuses when several do — naming them — and otherwise parses without an extent,
  recording the gap and warning.

- **Two reference parsers, not three (#218).** `versification.parse_reference` is gone;
  `PassageRef` carries the verse part it existed for, and the mapper uses the lean parser.
  `parse_passage_ref` moved to `llmflow.utils.versification` (the mapper cannot import
  `scripture`) and is re-exported from `scripture` where the read path imports it. It also stops
  accepting a display name as a book code: `Mark 1:1` silently became book `MARK`, and a USFM
  code is exactly three upper-case characters.

- **`format: usj` now emits a `sid` on every chapter and verse.** A chapter node carries
  `sid: "MRK 1"` and a verse node `sid: "MRK 1:1"`, so a consumer addressing a span has the
  standard's own identifier rather than having to rebuild one from `number` plus the enclosing
  chapter.

  **No `eid` is emitted, deliberately.** USX closes each milestone with a matching
  `<verse eid=…/>` element; USJ does not, and `usfmtc` — the USFM Technical Committee's
  reference implementation — discards verse and chapter ends in its USX-to-USJ conversion
  (`usjproc.py`: `if "eid" in out_obj and key in ['verse', 'chapter']: action = "ignore"`).
  Emitting them would put non-standard content in the standard node space, which
  `scripture_pipelines` exists to prevent, and a round-trip through any conformant tool would
  drop them. A verse ends where the next `sid` begins. Flattening still reproduces
  `format: milestones` exactly, and `usj_to_text` tolerates an `eid` node arriving from a
  USX-derived document produced elsewhere.

### Documentation

- **The shipped `scripture-representations.md` now states which `include:` families are built.**
  Six of seven — everything but `syntax`, which is held deliberately. Asking for an unbuilt
  family raises, and until now nothing a consumer could read said which those were; a project
  was still building against `{ids, discourse}` a day after the other four shipped. A guard test
  fails if the table diverges from `IMPLEMENTED_FAMILIES`.

## 0.2.1.24 — 2026-08-26

### New Features

- **Versification mapping — a reference is not a location until a scheme is named.**
  `llmflow.utils.versification` maps a reference between schemes through `org` as the hub.
  `PSA 51:1` in English is `PSA 51:3` in the original and `PSA 50:3` in the Vulgate; Malachi has
  four chapters in English and three in Hebrew. A scheme may declare `basedOn`, and inherits the
  verses it does not itself list.

  **`type: scripture` takes a `versification:` key** naming the scheme the passage is written
  in. When it differs from the edition's own, the reference is mapped before any text is read —
  fetching first would fetch the wrong verses.

  **An edition's scheme has no global default.** A Byzantine Greek text and a critical text are
  numbered differently, so the scheme is a property of the edition: declared as
  `versification_scheme` in its registry entry, or read from a Paratext project's
  `Settings.xml`, or taken from the table of editions sp constructs in
  `data/versification-editions.json`. If none answers and a cross-scheme mapping is asked for,
  that is an error naming the field to add rather than a guess. A Paratext project carrying a
  `custom.vrs` overlay is reported, because the overlay is not read.

  **Six schemes ship** — `org`, `eng`, `lxx`, `vul`, `rsc`, `rso` — installed into
  `~/.sp/versification/` by `sp init` and repaired by `sp doctor`. They are unmodified copies of
  the Copenhagen Alliance mappings, CC BY-SA 4.0, with the attribution alongside them. A custom
  scheme is a JSON file placed in that directory.

  Three properties the data forces, each covered by a test: mappings are independent pairs and
  never an ordering, because traditions disagree on sequence — the commandments in Exodus 20
  among them; the reverse direction is many-valued, since `DAN 4:4` is reached from both
  `DAG 4:1` and `DAG 4:7`, so `map_candidates` returns every candidate and `map_reference`
  raises rather than choosing one; and an entry whose two sides cover different numbers of
  verses is skipped and reported, one warning per scheme, rather than guessed at. A reference
  outside its scheme raises rather than returning an empty result.

- **A `kind: tei` edition backend.** A named edition may now point at a directory of Macula TEI
  book files, joined into running text alongside the existing `tsv` and `usfm` backends and
  producing identical output to the TSV for the same passage. Apparatus reference marks are not
  text and are dropped; a word ending in an elision mark joins to the next without a space; and
  several punctuation nodes after one word accumulate rather than replacing one another.

- **`size` and `stride` accept a variable**, resolved once at step entry so the partition stays
  constant for the loop and reproducible under `--rewind-to`. Anything that does not resolve to a
  positive integer fails at step entry; `sp lint` warns that it cannot verify a variable's value.

- **`tools/sync_helm.py` and `data/helm-sync.yaml`** — the set shared with Human at the Helm is
  recorded with hashes and rulings and checked on CI. Reports by default, copies only under
  `--apply`, and never touches a divergence that carries a ruling.

- **`tools/update_plans_index.py`** generates `project/plans/README.md` from each document's
  declared status and the issues it names, with `--check` exiting 1 when the index is stale. Kept
  outside `src/llmflow/`, so nothing it produces reaches a project. Its Issues column is a mention
  scrape rather than a declaration. (#163)

- **`sp init` ships the audit method**, not only the `/audit-*` skills —
  `docs/ai-context/sp/audits-pattern.md` covers which skill answers which question, tracing an
  output field back to the request that produced it, and testing a prompt fix with
  `sp tools replay`. It carries measured cases from real runs rather than general advice. The
  first project-scoped `source: template` entry, so its content is a reviewable markdown file
  rather than a Python string. (#214)

- **`$SP_HOME` relocates the store** — one resolver in `src/llmflow/paths.py`, replacing eleven
  call sites that each computed `~/.sp` independently, with a test that fails if any module
  computes it again. For tests, containers and CI. (#207)

- **A fresh clone now gets its skills (#204)** — `sp init` copies `~/.sp/skills/` into the
  repository's `.claude/skills/`, which is a location Claude Code actually reads. `~/.sp/skills/`
  is not: a skill left there is invisible, so `/load-context` did not exist as a command. Nothing
  is written to `~/.claude`, so no machine-scoped permission is needed. Whole skill directories are
  copied rather than `SKILL.md` alone.

- **`sp init` is fully non-interactive** — it previously returned silently when stdin was not a TTY,
  which is the path CI, Docker builds and any scripted onboarding take, and on a terminal it asked
  four questions with `Claude Code` defaulting to *No* and skills behind a second *No*. A user
  pressing Enter throughout ended up with a silently broken setup. Every write is inside the project
  directory and idempotent, so no prompt remains.

- **`sp init` generates a `.gitignore` when a project has none**, and never overwrites one that
  exists. Its contents are derived from the file catalog, so `.claude/skills/` cannot end up ignored
  — the mistake that leaves a clone with no slash commands.

- **A declared catalog of managed files, `data/file-catalog.yaml` (#204)** — ownership used to be
  decided by sniffing for `<!-- Generated by sp init -->` on line 1, and that marker's text had
  already drifted in shipped code (`cli.py` says `llmflow init`, `cli_utils.py` says `sp init`), so
  a file could become either permanently un-updatable or silently overwritable. Ownership is now a
  property of a catalog entry keyed by path. The catalog is data, not code: `llmflow/file_catalog.py`
  only reads it. Both the generated `.gitignore` and `sp doctor`'s ownership boundary are derived
  from it, so the two cannot disagree.

- **`sp doctor` — verify that a machine is set up correctly (#204)** — nothing previously answered
  "is this set up correctly?", so the first symptom of a missing markdown file was an API error that
  named nothing. `doctor` checks `~/.sp/`, the conventions, the files skills read directly, the
  installed skills, whether skills are anywhere Claude Code can actually find them, the project's
  `docs/ai-context/`, and whether the project is registered. Every failure names a remedy.

  Three design properties worth knowing:

  - **Read-only.** It reports and never repairs, so running it is always safe. Pinned by a test that
    fails if it creates or writes anything.
  - **Expectations come from the shipped package, not a list inside `doctor`.** Adding a template
    requires no change here. A second list would drift — which is exactly how three conventions went
    unshipped for months.
  - **It distinguishes absence from misconfiguration.** A missing `CLAUDE.md` is reported as
    information, not a failure: it is gitignored by convention, so a clone never has one, and
    committed context belongs in `docs/ai-context/`. A missing
    `~/.sp/user-context/filesystem-access.md` is not reported at all, because it grants an AI read
    access to a directory tree and only a machine's owner can grant that.

  Known overlap with `sp registry status`, which also reports on `~/.sp/`. Whether `doctor` subsumes
  it is tracked in #205; nothing is consolidated yet.

- **`sp lint` validates structured-output schemas before the run (#196)** — prompt contracts
  were checked before any token was spent; the JSON Schema in the same request was not
  checked at all. Under `strict: true` OpenAI accepts only a restricted subset and rejects
  anything else with **HTTP 400 at request time**, so a pipeline could pass every check,
  fetch its passage, complete three steps, and die on the fourth with a provider error
  naming a JSON path rather than a line in the YAML — with the earlier steps already paid for.

  `sp lint` now reports, per step and per schema path:

  ```
  ❌ Step 'segment_book': properties.pericopes.items: every property must be listed in
     'required' under strict mode. Missing: start_verse, end_verse, pericope_type
     Fix: add them to 'required'; if a field is genuinely optional, give it a nullable
          type — {"type": ["string", "null"]} — and list it in 'required' anyway
  ```

  Errors: every property listed in `required`; `additionalProperties: false` on every
  object; an object at the root; `$ref`s that resolve. Warnings: keywords outside the
  supported subset, and the documented size limits — OpenAI has widened the subset several
  times, and a stale rule table must not block work the provider would accept. The table is
  data, in one place, carrying a `LAST_VERIFIED` date.

  Gated two ways. `strict: true` gates the errors, since OpenAI does not enforce the subset
  without it — a schema missing `strict` gets a warning that the guarantee is not in force.
  And `response_format` is the trigger rather than the model name, so Gemini's
  `response_schema` (#191) is not measured against OpenAI's rules. `schema_file` is loaded
  and checked like an inline schema. `linter_config.skip_strict_schema_check: true` turns
  it off.

  The checker is pure — no network, no provider client, no key — so it cannot itself cost
  anything.

  **`pipelines/json-schema-example.yaml` was itself broken**, in all three steps, while
  advertising "guaranteed schema compliance". Five objects listed properties that were
  absent from `required`. It is fixed here, and passing its own lint is the acceptance test
  for the feature.

### Changed

- **New rule 34: a docstring says what the code does, and carries no status, rationale or
  design.** Design belongs in `project/plans/` and the AI context, status in issues and the
  CHANGELOG — all of which stay current while a docstring does not. Cross-references to where
  the reasoning lives are welcome; dates, commit hashes and quoted direction are not.
  `tests/test_docstrings_say_what_not_why.py` checks those three signals across `src/`,
  `tests/` and `tools/`, and carries a backlog of the 49 files that predate the rule, which a
  test forces to shrink. `src/llmflow/utils/scripture.py` and `src/llmflow/steps/scripture.py`
  are the first cleaned.

- **`CHANGELOG.md` is checked against being a session transcript.**
  `tests/test_changelog_is_not_a_transcript.py` rejects conversational voice, process
  commentary, commit hashes, uncategorised bullets and prose standing where a reader expects a
  list of changes. It applies to the unreleased section only: a released entry describes what
  users actually got, so it is a record, and the time to fix the wording is before it ships.

- **Rule 18 is now "Carry one design"**, replacing *"Prefer additive change to authored work"* —
  a design change is completed in one pass, and an older path that must survive names who depends
  on it and when it ends. The record still keeps its own words. Id changed from
  `additive-to-authored` to `one-design`.

- **New rule 29: express the design declaratively, syntax and semantics together.** Where a
  design can be stated as data — a schema, a catalog, a manifest, an enum, a pipeline — it is
  stated once there and the code reads it.

- **The shortname for Human at the Helm is `helm`.** Renamed `tools/sync_helm.py`,
  `data/helm-sync.yaml`, `tests/test_helm_sync.py`, `project/plans/design-helm-parity.md` and the
  `HELM_REPO` environment variable, with no dual-name transition. Guarded by
  `tests/test_shortname_is_helm.py`.

- **Prose uses the ruled product name, Scripture Pipelines.** `llmflow` remains the Python
  package and import namespace only. Swept from 43 markdown files and the shipped `cli_utils`
  constants, which had been passing the deprecated name into every project `sp init` touched.
  URLs, paths, identifiers and quotations are left as they are; renaming the repository is
  tracked separately. Guarded by `tests/test_product_name_in_prose.py`. (#209)

- **The generated project overview named the wrong CLI** — it said `llmflow`; the command is `sp`.

- **`docs/ai-context/` splits into `sp/` and `project/` halves** — three standard documents each
  (a map, a self-description, constraints). sp regenerates its half; the project's half is created
  once and never overwritten. `README.md` folded into `sp/overview.md`, `json-reliability.md`
  removed, `project/index.md` hand-authored. (#210)

- **`sp init` writes what `data/file-catalog.yaml` declares** — one loop replacing 21
  hand-written per-document blocks, keyed on each entry's `policy` rather than on the
  `<!-- Generated by sp init -->` marker, so `sp init --update` and `sp doctor` now agree on
  which files sp owns. (#211, #214)

- **`sp init --update` leaves unchanged files in place** instead of rewriting every shipped
  document.

- **Templates mirror their destination paths** — `templates/sp/` for what lands in `~/.sp`,
  `templates/project/` for what lands in a project, replacing the flattened `sp-*` prefixes.

- **sp's block in a shared file carries a warning, and sits at the top.** `CLAUDE.md`,
  `.cursorrules`, `.windsurfrules` and `.github/copilot-instructions.md` are files sp writes into
  but does not own, and nothing in them said so — the delimiters read as ordinary generated-code
  markers. Each block now opens with a warning that only `sp` may write there, that edits are
  lost, and that changing it breaks how an assistant finds the project's rules. The project's own
  content belongs below the block, and a block that was previously appended at the bottom is
  relocated to the top on the next run.

- **The catalog holds only what sp itself specifies.** `docs/ai-context/project/project.md` and
  the three `docs/audits/` checklists were shipped to every project though they are one project's
  documents; they are no longer created or managed, and a project reaches its own files by naming
  them in `docs/ai-context/project/index.md`. Existing copies are untouched.

- **The five methodology skills no longer carry Scripture Pipelines vocabulary (human-at-the-helm#1)** —
  `authorize`, `stand-down`, `handoff`, `load-context` and `commit-ready` are now one text serving
  this repository and Human at the Helm alike. The engine-specific lines are gone rather than
  duplicated: in `load-context` the "key rules to internalize" list was a paraphrase of
  `docs/ai-context/rules.md` items that the skill's own Step 4 already reads, so a summary which
  could drift from its source has been replaced by a pointer to the source. `audit-code` is
  deliberately **not** shared — its engine content is the subject matter, not a duplicated summary —
  and `audit-pipeline`, `audit-output`, `audit-prompts` and `release` stay here.

  `load-context` Step 5 now reads conventions from **both** `docs/ai-context/conventions/` and
  `~/.sp/conventions/`, whichever exist: a project set up by Human at the Helm has no `~/.sp`.

  `tests/test_portable_skills.py` fails the build if a shared skill names this engine, names one
  ecosystem's toolchain without the other's (`pytest` ↔ `vitest`), or sends a reader to
  `~/.sp/conventions` without offering the project-local path. Without it, "this skill is general"
  would be an assertion in a design document rather than something the build checks.

- **`load-context` reads the operational rules every session and the essays once** — Human at
  the Helm's disciplines directory holds two genres: short checkable rules, and longer documents
  explaining the failure modes behind them. The essays are written to be read in full by a person
  adopting the methodology, not re-read at every session start, so Step 5 now reads that
  directory's README first and treats what it marks as an essay as reference. Where no README
  draws the distinction — which is the case in this repository, where every shipped discipline is
  operational — every file is read as before.

- **`~/.sp/conventions/` is now `~/.sp/disciplines/` (human-at-the-helm#1)** — one word for these
  documents across both repositories, ruled by the Captain: *"I like 'disciplines' for each."* Human
  at the Helm has published `disciplines/` on a public unversioned `main` since before this engine
  had the directory at all, and its paths are linked from its README; `~/.sp/conventions/` is a
  directory an installer creates and nobody links to. Two words for one thing is what the split in
  the entry below exists to prevent, so the engine's internal name gives way rather than the
  methodology's published one.

  Renamed: `templates/sp-conventions/` → `templates/sp-disciplines/`, the catalog group and its
  install path, `install_global_conventions()` → `install_global_disciplines()`, `sp doctor`'s check,
  and the path in the `load-context` and `audit-prompts` skills. `consumer-repo-conventions.md`
  keeps its file name — the ruling was about what the category is called, not about renaming files
  whose subject happens to be a convention.

  **On upgrade, delete `~/.sp/conventions/` by hand.** `sp doctor` creates and fills
  `~/.sp/disciplines/`, but it only ever iterates what the package ships — it never enumerates what
  is already present, so the old directory is left behind untouched. Nothing reads it after this
  release.

- **The disciplines are split into general practice and engine practice (human-at-the-helm#1)** —
  step 4 of `project/plans/design-hath-parity.md`. `sp-workflow.md` mixed the two: shell command
  discipline, audit workflow, design-comment rules and "files the human controls" hold in any
  repository in any language, while `sp run` / `sp lint` do not. Its general half is now
  `workflow.md`; `sp-workflow.md` keeps the CLI rules — including the prohibition on running a
  pipeline unasked, which a test now pins because `.cursorrules` lost that exact line in a move and
  the loss was invisible. `llmflow-project-tracking.md` becomes `project-tracking.md`, stating the
  rolling audit/plan file structure for any subsystem; that the subsystem here is the pipeline moved
  to `sp-workflow.md`. `github-authority.md` no longer says "All Scripture Pipeline Projects" or
  names `~/.sp/user-context/` — the policy is unchanged, and where this project keeps the machine
  user account is stated in `sp-workflow.md`. `design-authority.md` and `surface-decisions.md`
  needed no edit; `llmflow-pipeline-steps.md`, `llmflow-prompt-organization.md`, `sp-debugging.md`
  and `consumer-repo-conventions.md` stay here.

  The conventions README now separates the two kinds explicitly, so a reader can tell shipped
  methodology from engine practice at a glance.

  `tests/test_portable_conventions.py` is the counterpart to `test_portable_skills.py` one level
  down: it fails if a shared convention names this engine, shows Python tooling without its
  TypeScript counterpart, or is added without being classified. Its patterns are imported from the
  skills test rather than restated, since a second definition of "engine vocabulary" is the failure
  this work exists to end.

  **Note for anyone who has already run `sp init`:** `sp doctor` installs the two new files but does
  not delete the renamed `llmflow-project-tracking.md` from `~/.sp/conventions/`, which stays behind
  as a stale copy until removed by hand.

- **A project rule that existed only inside a skill is now in `rules.md`** — *"Every LLM step must
  have source text as an explicit named input"* lived in `load-context` and nowhere else;
  `docs/ai-context/rules.md` had no rule about source text at all. Generalizing that skill would
  have silently deleted a substantive rule about ungrounded output.

- **`load-context` no longer states an unverified cause as fact** — it claimed a command returning
  no output "yields an empty result block, which the API rejects with a bodyless 400". Two proposed
  mechanisms for that failure were refuted by test and the cause remains unknown. The instruction to
  use `git status --short --branch` is unchanged and now rests on three checkable reasons: plain
  `--short` prints nothing in a clean checkout, the `##` header carries ahead/behind, and it
  replaces `git branch --show-current`, which is silent on a detached HEAD.

- **`sp doctor` now repairs what sp owns, not just reports it (#204)** — a convention that is
  missing, or whose content has diverged from the shipped version, is restored and the restoration
  is stated plainly. This supersedes the read-only property described below. A self-repaired file is
  a warning rather than a fault, so the command still exits 0; an error is reserved for a repair that
  could not be performed. Presence-only checking called a machine healthy while it ran a stale
  790-byte copy of a 3404-byte convention.

  What repair does not cover: `docs/ai-context/project.md`, which is the one file a project is
  invited to own; `CLAUDE.md`; and anything under `~/.sp/user-context/`. In a project, only files
  that exist and have drifted are restored — creating files that were never there is `sp init`'s job.

- **The assistant rule files point at the rules instead of restating them** — `.cursorrules`,
  `.windsurfrules` and `.github/copilot-instructions.md` now direct the reader to
  `docs/ai-context/rules.md` and carry no rules of their own. `.cursorrules` and `.windsurfrules`
  were byte-identical by construction and their shared six-line summary had lost the `sp run`
  prohibition, the memory-file prohibition and the `docs/ai-context/` prohibition — so an assistant
  reading `.cursorrules` as its rules found nothing saying that running a pipeline spends money and
  needs human authorisation. A signpost cannot drift out of alignment with the rules it points to.

- **`stand-down` ships like every other skill** — `install_global_skills` used to fetch it from
  `human-at-the-helm` at install time with the bundled template as a fallback, which made one skill's
  installed content depend on the network and differ by design from what the package ships. With
  `doctor` now restoring diverged files, that copy would have been overwritten on every run. The
  bundled version is the later of the two: it carries "Propose a Fix" — wait for approval before
  writing any file — and a checkpoint step the upstream copy does not.

### Fixed

- **The shipped window-cursor example lost content.** `docs/llmflow-language-quickref.md` set the
  cursor from the *dropped* last unit's opening, so any gap between the last kept unit and the
  dropped one was skipped by every later window. It now resumes from the trailing edge of the last
  unit **kept**. Reported from `nida-institute/discourse-flow`.

- **`window_num` worked at run time and failed `sp lint`.** The linter now injects all five
  variables a window step provides — `window_num`, `_window_index`, `_window_first`,
  `_window_last`, `_window_cursor` — making `window` symmetric with `for-each`.

- **One rule set, not two.** `docs/ai-context/rules.md` was written by two generators holding two
  independently maintained texts, so which rules a project was held to depended on which generator
  ran last. `data/ai-rules.yaml` is now the single source; both generators render from it.

- **`sp doctor` could not refresh four documents `sp init` writes.** `docs/tutorial.md`,
  `docs/llmflow-language-quickref.md`, `docs/vscode.md` and `project/TODO.md` were absent from
  `data/file-catalog.yaml`, and `managed_by_doctor()` returns only catalogued entries — so a fix to
  a shipped document could not reach an existing project. Now catalogued, with a test that fails if
  `sp init` writes anything the catalog does not declare. Reported from
  `nida-institute/discourse-flow`.

- **`gpt-4.1` was wrongly reported as incompatible with structured outputs.** The `audit-prompts`
  skill and `docs/llmflow-language.md` told auditors to change the model, contradicting rule 5.
  Measured elsewhere at 200+ calls with strict `json_schema` and zero failures. The hardcoded model
  allowlist is replaced by guidance to check the provider's capability table and the project's own
  run evidence.

- **`sp doctor --help` claimed to be read-only** — it restores any `policy: generated` file that
  is missing or has diverged, which cost a consumer repository two hand-authored files on
  2026-08-23. The help text now says it writes and what it overwrites.

- **The test suite wrote outside the project** — every init test registered its pytest temp
  directory as a permanent project in the real `~/.sp/`, and moving the store to pytest's default
  temp root then left tens of megabytes a run in the machine's temp area, including directories
  its cleanup could not remove. `$SP_HOME` is now redirected per test with a guard that fails the
  run if the real store is touched, intermediates go to `tmp/pytest/` inside the repository
  (declared in `pytest.ini`, git-ignored, announced at startup), and only failing tests'
  directories survive a run. (#207)

- **A test wrote `llmflow.log` into `/private/tmp` on every run.** `test_gui_cors_config.py` handed
  the executor a literal `/tmp` as the project path, and the executor runs with `cwd` set to it.
  It now uses a per-test directory, guarded by a check that no test hands a shared system
  directory to the executor and by a fixture that fails any test leaving the working directory
  changed. (#207)

- **`commit-ready` gated only the Python suite, leaving the GUI's TypeScript tests invisible (#206)** —
  `gui/frontend/` is a TypeScript project with seven Vitest test files, and CI has always run them
  (`npm test -- --run`, `npx tsc --noEmit`). The skill that calls itself "the full LLMFlow definition
  of done" named only `hatch run pytest`. So a change to `gui/frontend/src/App.tsx` could pass every
  check the gate described, with 2677 Python tests green, and still turn the build red.

  The gate now names the frontend commands, **conditionally** — a change touching no TypeScript does
  not need Node installed to be committable. `tests/test_commit_ready_gate.py` reads the required
  commands out of `.github/workflows/test.yml` rather than restating them, so a new CI step fails
  the build until the gate gains it too. A second hand-written list is what let them drift apart.

  Same shape as the `${var}` write guard (below) and the `.cursorrules` block: a check applied to one
  of two paths, reading as complete because the path it covers is green.

- **The install instructions named a package that is not on PyPI (#33)** — the project publishes as
  `scripture-pipelines`, but eleven places told users to run `pip install llmflow`, a name that
  returns 404. Anyone following the README got nothing, and an unclaimed name is one someone else
  can register. Several also requested a `[gui]` extra that does not exist: there is no
  `[project.optional-dependencies]` section at all and Flask is a hard dependency, so the extra was
  never needed. Corrected across `README.md`, `INSTALL.md`, `docs/GPT_CONTEXT.md`,
  `docs/testing-content-gui.md`, `gui/QUICKSTART.md`, `gui/README.md`, `src/llmflow/gui_launcher.py`
  and three test skip messages. `CHANGELOG.md` history is left as written.

  `tests/test_install_instructions.py` now reads the package name from `pyproject.toml` and fails
  the build if any document or source file names a package we do not publish, or an extra we do not
  declare. This trap was already recorded in `CLAUDE.md` and shipped regardless — a note in a
  pitfalls list does not fail a build.

- **`~/.sp/drift-patterns.md` was in no package and could not be obtained (#204)** — the
  `load-context` skill reads it by that exact path, and no `sp init` on any machine could produce
  it. It now ships and installs to the root of `~/.sp/`, alongside a new `templates/sp-root/`
  location for files whose path is part of a contract rather than a convenience.

- **Two machine-scoped policies promoted to shipped conventions (#204)** — `github-authority.md`
  (what an AI may and may not do to a GitHub account) and `consumer-repo-conventions.md` (never
  make the LLMFlow dependency non-editable) bound only their author's machine. Both are team
  policy, so both now ship.

  `github-authority.md` named a specific bot account; the shipped copy states the rule and directs
  the reader to record their own account in `~/.sp/user-context/`, which never ships. A new test
  fails the build if any shipped template contains an email address or an absolute home path.

  `~/.sp/user-context/filesystem-access.md` deliberately does **not** ship: it grants an AI standing
  read access to a directory tree, and only a machine's owner can grant that. Its absence is the
  correct default, not a misconfiguration.

- **`sp init` installed only 5 of 8 global conventions (#204, #181)** — `design-authority.md`,
  `sp-debugging.md` and `sp-workflow.md` existed on the author's machine but were never added to
  the package, so every other machine received a subset. A new contributor's `/load-context`
  silently loaded less guidance than the mentor's, with nothing reporting the shortfall.

  The three conventions now ship. The cause was an asymmetry in the test suite: `EXPECTED_SKILLS`
  pinned the shipped skill set exactly, and conventions had no equivalent, so skills held while
  conventions drifted. `EXPECTED_CONVENTIONS` now guards them the same way, and a further test
  requires the conventions `README.md` to index every convention it ships — it had itself drifted
  to listing 3 of 8.

- **`/load-context` step 1 could return an empty result (#204)** — `git status --short` prints
  nothing in a clean checkout, which is exactly a fresh clone, and a command that returns nothing
  yields an empty result block. Replaced with `git status --short --branch`, whose `##` header
  always prints and additionally reports ahead/behind. `git branch --show-current`, silent on a
  detached HEAD, is dropped since the header supplies that information.

  A new test asserts across **all ten shipped skills** that no informational command exits 0 with
  neither stdout nor stderr. Commands that change state rather than report it are excluded —
  silence is correct for those.

  **This is not confirmed to be the cause of the bodyless HTTP 400 reported in #204.** Two
  proposed mechanisms for that failure have been refuted by test, and the cause remains unknown;
  see #204. This change is justified on its own merits.

- **A second run no longer destroys the first run's audit trail (#198)** — the debug
  directory was emptied with `shutil.rmtree()` at the start of every run, and it was keyed
  by pipeline filename alone. So running the same pipeline for Ruth and then for Mark
  deleted every captured request and unedited reply from the Ruth run. When
  `intermediate_file_directory` was declared it took the run log too, because `llmflow.log`
  is written into that same directory. Nothing warned; the run reported success. Reported
  by Jonathan Robie from Ears to Hear.

  This mattered more than an inconvenience: the engine's claim is that a conclusion can be
  audited rather than taken on trust, and that a method can be applied across a whole
  corpus. Do exactly that and the evidence survived for one passage — the last one.

  **The clean stays** — a run directory should hold that run and nothing else, which was
  #145's point. What changed is its *scope*: the run's distinguishing variables now name the
  directory, taken from CLI `--var` values because those are by definition what varies
  between runs. Ruth lands in `debug/<pipeline>/book-Ruth/`, and the clear empties that leaf
  and nothing above it. The run-key segment is emitted even when it is `default`, precisely
  so the delete can never reach a parent holding sibling runs — without it, one `--var`-less
  run would wipe every per-book trail.

  **New layout**: debug filenames were doing a database's job, and `sp tools replay` had to
  parse them back out.

  ```
  outputs/debug/<pipeline>/book-Ruth/
    manifest.jsonl
    0001-segment_book-request.txt
    0001-segment_book-response.json
    0002-analyze-attempt2-request.txt      # a retry no longer overwrites its predecessor
    llmflow.log
  ```

  Three defects this removes, each verified first:

  - The step name was used **only when there was no prompt file**, so two steps sharing one
    `.gpt` produced identical filenames and the second silently overwrote the first.
  - A **retry** produced the identical name too, destroying the attempt worth reading.
  - The timestamp appeared **only when `passage` was absent**, so the one field that could
    establish ordering was missing exactly when there were most files to order.

  `manifest.jsonl` carries one line per call — sequence, step, attempt, prompt file, the
  model **actually called** (not the one declared, which differs whenever a default fills
  in), passage, for-each position, start and finish, status, and which files belong
  together. Paths are relative to the run directory, so a run can be archived or moved
  intact.

  `sp tools replay` now reads the pairing from the manifest instead of stripping timestamps,
  globbing, and taking "the earliest response at or after the request" — a join by string
  comparison that the two collision cases above could get wrong. Directories captured before
  this release have no manifest, so the filename-matching path is retained for them; a
  truncated manifest from an interrupted run falls back rather than making the directory
  unreadable.

  Also fixed: one of the four debug write sites (`llm_runner.py`) wrote to a hardcoded
  `outputs/debug/{filename}`, ignoring both `intermediate_file_directory` and the
  per-pipeline subdirectory, so those raw responses landed outside the run's own trail
  entirely. They are now saved beside the call they belong to.

  Each line also carries `prompt_tokens`, `completion_tokens`, `total_tokens` and
  `cost_usd`. Telemetry prints those to the console, where they are gone as soon as the
  terminal scrolls; in the manifest they can be queried per call, months later. Tokens are
  read after the Responses-API estimate fallback, so the figures recorded are the ones cost
  was charged on, and `cost_usd` is `null` rather than a guess when the model is unpriced.

  `build_debug_filename()` is **removed**, along with its tests and the demo script that
  exercised it. Nothing in the engine called it.

- **The `prompt` schema no longer accepts keys the renderer ignores (#197)** — `prompt` was
  `oneOf: [string, object]` with `additionalProperties: true`, so any key validated and was
  then discarded by `render_prompt()`, which reads only `file` and `inputs`. The step died
  later with `ValueError: Prompt 'file' must be a string, got NoneType`.

  The editor schema was worse: it advertised `prompt.text` — *"Inline prompt text. Supports
  {{var}} substitution."* — and `prompt.system`, neither of which exists. That is almost
  certainly where the mistake came from. Both schemas now declare `file` and `inputs`, with
  `file` required and `additionalProperties: false`.

  There is no inline prompt form; the prompt always lives in a file, because the contract
  header the linter checks lives there too. `template` **is** a real keyword — at *step*
  level, naming a file that formats the model's **output**.

  Surveyed before closing: across every pipeline in every sibling repo, `prompt:` used only
  `file` (185) and `inputs` (188). The three `template` uses were all the broken example.

- **Output templates accept `{{ spaced }}` placeholders** — `render_markdown_template()`
  built its placeholder by formatting `f"{{{{{key}}}}}"` and replaced it literally, so
  `{{ content }}` never matched while `{{content}}` did. It did not warn: the literal text
  landed in the rendered deliverable, so the run reported success and wrote the wrong file.
  Prompt templates had always accepted spaces, so the same spelling behaved differently
  depending on which kind of template it was in.

  The single regex sweep also fixes an order-dependent bug: the old loop kept iterating
  after substituting, so a model response containing `{{book}}` was itself interpolated if
  `book` happened to come later in the dict.

- **`basex` steps: `database:` now binds `$database` in the query (#189)** — the linter
  required `database:` and the engine then threw it away. Nothing passed it to BaseX, so
  queries hardcoded the database name inside the XQuery or smuggled it through an ad-hoc
  `inputs: db:` entry. Editing `database:` in a pipeline changed nothing at all.

  The keyword and the XQuery variable are deliberately the same word:

  ```yaml
  - name: leitwort
    type: basex
    database: macula-sblgnt-lowfat     # -> -bdatabase=macula-sblgnt-lowfat
    query_file: queries/leitwort-candidates.xq
  ```
  ```xquery
  declare variable $database external;
  collection($database)//w
  ```

  `database:` goes through `resolve()`, so `${...}` works in it like anywhere else.

  Setting `database:` **and** `inputs: database:` is now an error in both the linter and
  the step handler, rather than a precedence rule. BaseX accepts duplicate `-b` flags for
  one variable, takes the last silently and exits 0 — verified on 12.3 — so a pipeline
  could name one database while the query read another and still report success. The
  linter catches it first; the runtime guard covers `--skip-lint` and the Python API.

  `db` is now a recognised typo for `database`. BaseX drops bindings for variables a query
  never declares, without warning and with exit 0, so a stale `db:` would otherwise fail
  silently forever.

- **`sp setup` now configures the key the engine actually reads (#195)** — it wrote only
  `llm`'s keystore, while every structured-output step constructed the provider client
  directly and read `OPENAI_API_KEY` from the environment. So setup reported success and
  left `response_format` steps unauthenticated — and with structured outputs now the
  standard, that is most real pipelines.

  Keys now resolve through **one** path, `resolve_provider_key()`, which delegates to
  `llm.get_key`: explicit argument → the `llm` keystore entry for the provider → the
  environment variable. All four direct-client call sites go through it
  (`llm_runner.py:426,554,833`, `tools/replay.py:208`), for OpenAI, Anthropic and Gemini.
  The environment variable still works; it is simply no longer the only thing that does.

  On **Windows**, `sp setup` additionally persists the environment variable for the user
  account, since a CLI can legitimately do that there. On macOS/Linux it does not pretend
  to — a process cannot change its parent shell's environment — and no longer needs to.

  The `"env"` field in `setup_command.PROVIDERS` had been declared and never read; it is
  now the single provider→env-var mapping, with a test asserting it matches the resolver's.

- **Plugins load only when running a pipeline (#178)** — discovery ran at *import* time, and
  twice: once from `plugins/loader.py` and again from `runner.py`. So `sp --version` and
  `sp --help` printed two "Loading plugins…/Loaded N plugin(s)" pairs before doing anything, and
  every command paid the cost. Discovery now happens inside `run_pipeline()`; `sp lint` does not
  load plugins at all, because the linter never reads the registry. Reported by Benjamin Varghese.

  Safe to defer because `discover_plugins()` populates `plugin_registry` **in place** rather than
  rebinding it, so modules that imported the dict early see it filled later — pinned by a test.

- **`sp --version` now says `sp`** — the parser's `prog` was still the old `llmflow` branding, so
  the banner read `llmflow 0.2.1.23` for a command nobody types.

### Documentation

- **Rule 28: work on a single `dev` branch**, feature branches only when asked, `main` for what is
  released — with an explicit clause that a project may declare a different workflow in its own AI
  context and that decision governs locally. The only prior record of this was an unreviewed memory
  file in `~/.claude`, invisible in every repository.

- **`project/plans/plan-memory-recovery.md`** — the transfer record for the `~/.claude` memory
  stores, now emptied: 81 files across 12 projects, unreviewed,
  invisible in any repository, and loaded into every session ahead of the documents that carry
  design authority. 39 were audited. Thirteen were second copies of authored sources, one
  contradicted the record by pointing `GH_CONFIG_DIR` at a superseded path, and 22 items with no
  home anywhere are preserved in the plan with proposed destinations. Every file remains readable
  from `8678309`.

- **The scripture step takes two parameters, not one.** `format:` for the shape
  (`milestones` | `plain` | `usj`) and **`include:`** for what rides along. Measured on the whole of
  Mark: the USJ container costs 4.26x a milestone string before any metadata, word ids take it to
  5.67x, and one repo's annotations to 11.78x — so the dimension worth controlling separately is
  the payload, not the container. Recorded in
  `project/plans/design-scripture-representations.md` (#200).

- **Rule 27: the commit, the push and the merge are the human's.** Nothing `sp init` installed
  said who may commit. The five shipped context documents and the 26 rules contained no mention
  of `git commit`, `git push` or `git merge` — absent text, not wrong text — which left the
  machine-wide `commit-ready` skill, whose gates have the agent committing, pushing, merging and
  deleting branches, as the only voice a session in a client project heard on the subject. An
  agent now runs the gates, writes the message to a file, and hands over the command. Passing the
  gates is not authorization. The skill itself still contradicts this and sits in a store an agent
  may not change.

- **The topic map points at the design documents.** `docs/ai-context/index.md` did not mention
  `project/plans/`, so an assistant following the canonical map never learned the documents
  existed — and twelve of them named no issue, so one could be stranded without anyone noticing.
  That is how `design-scripture-editions.md` came to exist only on a local tag while
  `project/TODO.md` pointed at it. Verified not to reach consumer repositories: this repository's
  topic map and the one `sp init` installs are separate artifacts with no shared source.

- **`project/plans/design-scripture-representations.md`** specifies the representation half of
  #200 — what each serialisation carries and drops, the `xml:id`/`ref` alignment spine and why
  one source cannot join to it by id, the measured cost of each form sent to a model, and four
  questions awaiting a ruling. Records that Lowfat departs from document order in roughly 40% of
  Mark's verses, which makes naive text extraction wrong in a way that survives casual testing.

- **`docs/llmflow-language.md` explains windowing semantics**, not just its mechanics:
  physical block versus logical units, why a fixed `stride` asserts knowledge you do not have,
  the discard-and-resume corollary, and an explicit statement that the engine enforces none of
  it — that discipline is pipeline-side and a run that gets it wrong loses content silently.

- **Two rules added** — data moves between steps through the
  pipeline context and nowhere else, and pipeline logic belongs in the pipeline language rather
  than reimplemented in Python. Neither existed; the only prior statement was one descriptive
  sentence in `docs/architecture.md`.

- **`disciplines/surface-decisions.md`: only the Captain writes after a `=>`.** An AI filling in
  its own answer slot manufactures the authority it was asking for, and nothing distinguishes
  the two afterwards.

- **`disciplines/github-authority.md`: identity in three levels.** A git author is a string, not
  a login; a second hosting-service account covers only the service-facing half; a paid seat,
  org role or extra AI-tool account is never required.

- **The `sp` name clash in PowerShell is documented** — PowerShell defines `sp` as an alias for
  `Set-ItemProperty` and resolves aliases before programs, so `sp --version` runs the cmdlet and
  reports a confusing parameter error. `INSTALL.md` now covers it in the quick-install section, as
  its own Windows step (use `sp.exe`, use `cmd`, or override the alias in `$PROFILE`), and in the
  troubleshooting table. Reported by Benjamin Varghese. macOS and Linux are unaffected.

- **The API-key instructions are version-aware** — `INSTALL.md` told everyone to export
  `OPENAI_API_KEY`, which was the only thing that worked before #195. It now says that
  `sp setup` alone is sufficient from 0.2.1.24 on, and keeps the environment-variable
  route for anyone still on an earlier build.

## 0.2.1.23 — 2026-08-13

### New Features

- **One schema, one step vocabulary** — `PIPELINE_SCHEMA` is now the *only* declaration of the
  step vocabulary, and it is **per step type**. The step schema became a tagged union (common
  keys plus `allOf` `if type == …` branches), the linter derives its allowed keys per type from
  it (`allowed_step_keys()`), and `Step`'s attributes are **generated** from it. The linter's
  second key list (`_EXTRA_STEP_KEYS` / `ALLOWED_STEP_KEYS`, ~40 keys the schema never declared)
  is deleted — the object model previously saw only the schema half of the vocabulary, so ~34
  keys the engine reads were absent from the published API. Reported by ears-to-hear;
  design in `project/plans/design-schema-single-source.md`.
  - New derived helpers: `allowed_step_keys(step_type)` (returns `None` for plugin/registered
    types, whose keys cannot be enumerated), `common_step_keys()`, `step_keys()`.
  - Step attribute names extend the existing rule mechanically: a hyphen becomes an underscore
    (`group-by:` → `step.group_by`) alongside the keyword rule (`for:` → `step.for_`).
- **One syntax per concept — BREAKING** — the language admitted four redundant spellings, each a
  second name the engine honoured silently. A reader could not tell which was canonical, so all
  four are now single-spelled. Retired spellings are **lint errors naming their replacement**, not
  silent aliases; `tests/test_one_syntax.py` pins it.

  | Concept | Spelling | Retired |
  |---|---|---|
  | bind a step's result to context | `output` | `outputs` |
  | format the response through a template | `template` | `format_with` |
  | abandon a call after N seconds | `timeout_seconds` | `timeout` |
  | loop modifiers | `group_by`, `order_by` | `group-by`, `order-by` |

  `output` (singular) is the spelling: a step produces one result, even when that result is a
  list — the ruling in `project/plans/design-pipeline-schema.md` §1.

  **Migration:** every pipeline in every local repo was migrated in the same window — **~1,100
  sites across 15 repos**: 528 in consumer pipelines (discourse-flow 179, ears-to-hear 141,
  llmflow-historical-pipelines 93, and 10 more), plus the engine, both schemas, 472 test-fixture
  sites, and 116 in docs. `format_with`, `group-by` and `order-by` had **zero** usages anywhere.
  `sp lint` names the replacement for anything missed.
- **The editor schema is held to the same vocabulary** — `src/llmflow/schema/pipeline.schema.json`
  (wired to `pipelines/**/*.yaml` by `.vscode/settings.json`) is a second declaration of the
  vocabulary that no Python code reads, so nothing caught it drifting. It required `outputs`,
  offered `format_with`, and advertised two keys the engine never reads: `params` on basex (#189)
  and **`else` on `if` steps** (#192) — an if/else whose else branch silently never fired. It is
  now aligned, and a guard test asserts it declares no retired spelling and no key the engine
  would reject.
- **`sp init` — a project-owned AI-context lane** — `sp init` now creates
  `docs/ai-context/project.md`, a file for a repo's *own* project-specific AI context that
  `sp` **never overwrites** (even on `sp init --update`). The generated files (`index.md`,
  `overview.md`, `rules.md`, `github-workflow.md`) still refresh on `--update`; local context
  goes in `project.md`, which `index.md` links for AI assistants. Cleanly separates sp's
  evolving standard context from a repo's own, so neither pollutes the other. The stub carries a
  light suggested structure (what-this-repo-is, data sources, local conventions, gotchas, where
  active work lives) and a maintenance discipline (record non-obvious facts as learned; keep it a
  map) — so a project AI knows how to *structure* local context, not just where to put it.
- **The Python API is discoverable from generated AI context** — the `docs/ai-context/index.md`
  template now points project AIs at the engine's Python API (`load_pipeline` / `Pipeline` /
  `api_catalog` + `PIPELINE_SCHEMA`), so an assistant in a consumer repo finds the programmatic
  surface — not just the CLI and the YAML language. (#187)
- **`/handoff` skill — an adequacy standard** — the handoff skill now defines what makes a
  handoff *adequate*: a fresh instance, from `HANDOFF.md` + the repo alone, can name and start
  the next action without re-deriving settled decisions or hitting deferred landmines. It leads
  the output with the next action, adds a per-thread "verify" pointer and a "Do NOT / deferred"
  section, and ends with a tickable **adequacy checklist** (each item an outcome test, so a
  section filled with fluff doesn't pass). Distributed via `sp init`.

### Fixed

- **`${output_file_directory}` / `${intermediate_file_directory}` now lint** — referencing either
  in a `saveas` (or any checked field) failed lint with *"Variable not available"*, even though
  both resolve fine at run time. Since `sp run` lints by default, a pipeline that would run
  perfectly could not run at all, and the only workaround was to hardcode the output root in every
  `saveas`.

  The cause was a duplicated rule: `utils/context.py::build_run_context` — whose docstring calls
  itself *"the single source of the run context … so run-time and inspection-time behavior cannot
  drift"* — injects the two directory keys, but the linter built its own available-variable set
  from `variables:` alone. The linter was the one caller bypassing that single source, which is
  exactly how it drifted. It now calls `build_run_context`, so lint and run cannot disagree by
  construction. Found while wiring `hebrew-poetry-features`, where 23 `saveas` paths had to
  hardcode the root.

- **Wrong-type step keys are no longer silently ignored** — the linter's allowed-key set was
  *global*, so a key that is real but belongs to another step type passed lint and was then read
  by no handler: no error, no warning, no effect. `output_type:` on a `function` step,
  `query_file:` or `size:` on an `llm` step, and `content:` on a `json` step were all accepted
  and inert. Per-type validation makes each a lint error. Typo detection is unchanged for
  plugin/registered types, which stay permissive by design.
- **Loader filter keys were missing from the schema** — `key`, `where`, `limit`, `offset`,
  `columns`, `xpath`, `namespaces` and `output_format` are read top-level on `load_*` steps (by
  `utils/data.py`) and are covered by tests, but no schema declared them, so they were absent
  from the object model. Now declared on the loader branch. The schema-vs-runner guard test also
  scans `utils/` and `modules/` — handlers hand the step dict to helpers, and scanning only the
  handlers is what let these keys stay hidden.
- **Dead step keys removed** — `tools`, `response_mime_type` and `response_schema` were accepted
  top-level but never read there (only nested inside `llm_options` / `response_format`).
- **`Pipeline.schemas()` now covers validator steps and reports the reference kind** — it
  previously missed `json_schema_validator` steps (whose schema is referenced via
  `inputs.schema_path`), silently under-reporting. It now returns
  `{step: {"path": ..., "kind": "response_format" | "validator" | "frontmatter"}}`, covering all
  three routes a step can reference a JSON schema. (#187)
- **`sp init` no longer plants an `output/` decoy** — sp's scaffolding used singular `output/`
  (the created directory, the HELLO examples, the tutorial) while sp's own runtime default is
  plural `outputs/` (e.g. debug dumps under `outputs/debug/`, and real projects use `outputs/`).
  Every `sp init` left an empty `output/` beside where output actually lands, and the examples
  taught the wrong name. sp now scaffolds `outputs/` consistently.

### Documentation

- **`docs/architecture.md` §16–§18** — the *declarative schema as single source*
  (`PIPELINE_SCHEMA` drives validation, linting, the object-model API, and a schema-derived
  drift test — not code-generated tests); *machine-readable semantics for programs and LLMs*
  (`PIPELINE_SCHEMA` nouns + `api_catalog()` verbs, a total syntax↔API isomorphism); and
  *AI-context distribution* across consumer repos (sp-managed vs `project.md` lanes,
  `AGENTS.md`-first). `docs/ai-assistants.md` and `docs/python-api.md` cross-linked to match.

## 0.2.1.22 — 2026-08-10

### New Features

- **Public Python API — object model (`load_pipeline`, `Pipeline`, `Step`, `Pipeline.resolve`)** —
  `load_pipeline(path)` returns a read-only `Pipeline` whose attributes mirror the pipeline
  YAML 1:1 (`p.name`, `p.variables`, `p.steps`, `step.type`, `step.saveas`, nested
  `step.steps`; reserved words as `in_` / `for_`), so the calls are guessable directly from
  the syntax. `Pipeline.resolve(vars)` returns a same-shaped view with `${...}` expanded and
  `--var` applied (directory keys as `Path`) — backed by the engine's own context builder so
  it can't drift, and letting consumer repos delete hand-rolled YAML-reading path modules.
  `PIPELINE_SCHEMA` is a public export, and a drift test keeps the object model in lockstep
  with it. (#187)
- **Public Python API — `Pipeline.lint()` / `Pipeline.run()`** — thin facade methods that
  delegate to the engine's own `lint_pipeline_full` / `run_pipeline` (no reimplementation):
  `load_pipeline(p).lint(vars=...)` returns a `LintResult`; `load_pipeline(p).run(vars=...,
  dry_run=...)` runs the pipeline. (#187)
- **Public Python API — `Step.render_prompt()` and lazy `call_llm`** —
  `step.render_prompt(context)` renders the step's prompt (delegates to the engine's
  `render_prompt`); `llmflow.call_llm(prompt, config)` gives direct model access (#175),
  imported lazily so `import llmflow` stays light. (#187)
- **Public Python API — `Pipeline.schemas()` and `api_catalog()`** — `p.schemas()` returns
  `{step: schema_file}` for steps referencing a JSON schema via `response_format` or a
  prompt's `.gpt` frontmatter `schema:` (recursive). `llmflow.api_catalog()` returns the
  machine-readable method catalog
  (`{node, name, signature, doc}`), introspection-generated so it can't drift — the verb half
  of the published API mapping, with `PIPELINE_SCHEMA` the attribute half. (#187)
- **Public Python API — `Pipeline.saveas()`** — `{step_name: saveas}` declared output targets
  for every step (recursive); resolved paths come from `.resolve()`. (#187)
- **Public Python API — utilities** — `llmflow.parse_bible_reference` (scripture-reference
  parser) and `llmflow.model_metadata` (model pricing / context-window info) are exposed as
  lazy top-level functions and listed in `api_catalog()`. (#187)
- **`sp clean` honors `--var`** — `clean` resolves its target directory through the same
  accessor, so `sp clean --var output_file_directory=...` matches the run it cleans up
  after. (#186)

### Changed

- **CLI runs on the public API** — `sp run` / `sp lint` / `sp clean` now go through the
  `llmflow` facade (`load_pipeline().run()` / `.lint()` / `.resolve()`) instead of calling
  engine internals in parallel, so there is one code path per operation and CLI/API behavior
  cannot diverge. (`Pipeline.lint()` gained `rewind_to`; `Pipeline.run()` gained `log_file`.)
  (#187)
- **Pipeline schema recognizes the directory keys** — `intermediate_file_directory` and
  `output_file_directory` are now first-class in `PIPELINE_SCHEMA` / `PipelineConfig`
  (previously accepted only implicitly via `additionalProperties`), so the linter knows
  them. Internally, pipeline YAML loading is consolidated into a single
  `load_pipeline_config()` shared by the runner, linter, and path resolution — groundwork
  for the object-model public API. (#187)

### Documentation

- **`docs/python-api.md`** — documents the object-model public API (`load_pipeline`,
  `Pipeline`/`Step`, `.resolve` / `.lint` / `.run` / `.schemas`, `Step.render_prompt`,
  `call_llm`, `PIPELINE_SCHEMA`, `api_catalog`), the syntax→API mapping principle
  (read a pipeline, guess the calls), and the stability contract. (#187)

## 0.2.1.21 — 2026-07-30

### New Features

- **`sp tools replay`** — test a prompt change against captured debug requests without
  re-running the pipeline, so prompt edits can be checked cheaply. Usage:
  `sp tools replay --request <debug>/*_request.txt --prompt old.gpt --prompt-new new.gpt`.
- **`surface-decisions` global convention** — installed by `sp init` (shipped in
  `templates/sp-conventions/`): surface genuine decisions to the Captain and stop;
  never proceed on an assumption. (#181)
- **`/handoff` skill** — writes `project/HANDOFF.md` (active threads, in-flight work,
  open decisions, established facts, key files/issues) for the next session; the
  bookend to `/load-context`. Distributed via `sp init`.

### Documentation

- **Debug request/response dumps documented** — `docs/architecture.md` §15 describes
  the `linter_config.log_level: debug` dump mechanism: trigger, output location, file
  names, per-run clearing, and cleanup via `sp clean --debug-only`. (#180)
- **`docs/ai-assistants.md`** — working on Scripture Pipelines repos with any AI
  assistant (Claude Code, Codex, Gemini CLI, Cursor, VS Code, browser agents), including
  non-CLI setups, via the cross-tool `AGENTS.md` model. Linked from the README.
- **Editable-install pattern documented** — `docs/getting-started.md` §4 shows the
  known-good consumer-repo `pyproject.toml` (Hatch `post-install-commands` editable
  install) and why not to pin it or make it non-editable.

### Fixed

- **Frozen-binary packaging** — the Nuitka `sp` binary now bundles `data/models.json`
  (cost tracking works instead of silently disabling), the certifi CA bundle (HTTPS
  fetches no longer fail with `CERTIFICATE_VERIFY_FAILED`), and the package metadata
  (`sp --version` reports the real version instead of `unknown`). (#182, #184)
- **`load-db --register` now records the database** — the flag was parsed but never
  wired (a stubbed TODO), so it printed success while the registry stayed empty and
  `sp registry list` couldn't see the database. Databases loaded with `--register`
  are now recorded (idempotently, so `--force` reloads don't duplicate). (#183)

## 0.2.1.20 — 2026-07-06

### Breaking

- **Loop syntax is now `for`/`in` only.** for-each and window steps use the XQuery-style
  `for:` (loop variable) and `in:` (list) keys. The legacy aliases `item_var`/`input`/`over`/`as`
  have been **removed** — the runtime raises and the linter flags them (with a "did you mean
  'for'/'in'?" hint) rather than silently ignoring them. One syntax per language. Migrate
  pipelines with `item_var:`→`for:`, `input:`/`over:`→`in:`.

- **Step handlers extracted to `src/llmflow/steps/` package** — each step type now lives in
  its own module (`llm.py`, `function.py`, `for_each.py`, `window.py`, `if_step.py`,
  `load.py`, `save.py`, `json_step.py`, `basex.py`, `duckdb.py`, `plugin.py`). The runner
  dispatches to these handlers rather than containing all execution logic inline. This is
  Phase 1 of the schema-driven runner design: adding a new step type no longer requires
  touching `runner.py`.
- **Utils extracted from runner** — `context.py` (variable resolution), `file_io.py`
  (file writing), `step_outputs.py` (output binding and saveas), `debug.py` (debug
  directory management) are now standalone modules under `src/llmflow/utils/`.
- **JSON Schema draft 2020-12** — `src/llmflow/schema/pipeline.schema.json` formally
  defines the pipeline language: all step types, all fields, required/optional, types.
  Wired to VS Code via `.vscode/settings.json` for live autocompletion and inline
  validation across `pipelines/**/*.yaml`. See `project/plans/design-pipeline-schema.md`
  for the full design including the planned schema-driven execution loop (Phase 2).

### New Features

- **Loader step types** — `load_json`, `load_yaml`, `load_xml`, `load_csv`, `load_tsv`,
  `load_text`, `load_directory` load files directly into context without a function step.
  `load_tsv` and `load_csv` support `where:`, `limit:`, `offset:`, and `columns:` filters
  (full parity with the legacy `tsv` plugin). `load_xml` supports an `xpath:` key;
  `load_json` and `load_yaml` support a `key:` field for sub-document extraction.
- **Prompt mixins** — `{{mixin:path/to/file.md}}` directives in `.gpt` prompt files include
  shared content at render time, resolved relative to the prompt file. Enables reusable
  instruction fragments across prompts. The linter recognises mixin directives and does not
  flag them as unknown variables.
- **`parse_bible_reference()` extended** — now returns `testament` (`OT`/`NT`) and
  `original_language` (`Hebrew`/`Greek`) for all recognised book codes.

### Fixed

- **Derived variable resolution** — `resolve()` now recursively expands variables whose
  values reference other variables (e.g. `book_output_prefix: "${book_output_dir}/..."`
  where `book_output_dir` itself contains `${...}`). Previously, multi-level chains
  produced garbage paths like `$57-$PHM` or literal `${...}` directory names on disk.
- **Linter saveas directory check** — when a saveas path contains unresolved runtime
  `${vars}`, the linter now checks only the resolvable prefix against the declared
  directories rather than emitting a false-positive warning. Root-level pipeline keys
  (`intermediate_file_directory`, `output_file_directory`) are also now included in the
  linter's resolution context.
- **Root-level directory keys in runtime context** — `intermediate_file_directory` and
  `output_file_directory` declared at the pipeline root (not inside `variables:`) are now
  seeded into the runtime context, so `${intermediate_file_directory}` resolves correctly
  in `saveas` paths.
- **Double lint eliminated** — `sp run` was running `lint_pipeline_full()` twice (once in
  the CLI handler, once inside the runner). The runner now skips lint when called from the
  CLI (`skip_lint=True`).
- **Telemetry footer** — corrected stale command reference from `sp registry update-models`
  to `sp models --update`.

### Changed

- **Telemetry summary redesigned** — cost and total time are now visually prominent (double
  horizontal rule). Steps are grouped by name and sorted by cost descending, with iteration
  counts (`N×`) for for-each steps. Slowest single runs are shown on one line at the bottom.
- **Reduced default output verbosity** — `📦 Stored in context` and `📄 Loading schema`
  messages demoted to debug level; they appear in the log file and with `-v` but not in
  default console output.

### CI / Release

- **Executables build on PRs now, and get promoted (not rebuilt) on tag.** The
  Linux/macOS/Windows Nuitka builds run on every pull request as a merge gate and upload the
  three binaries as artifacts; `release.yml` attaches those same artifacts to the GitHub
  Release when a `v*` tag is pushed. A broken build shows up on the PR, before merge — not an
  hour after tagging. Replaces the old `build-release.yml`. See
  `project/plans/design-pr-build-promote.md`.
- **PyPI publish waits for a good build, but not for the build time** (#152). Because the
  build already ran on the PR, tagging doesn't re-run the ~1hr Nuitka build — `release.yml`
  just confirms the tagged commit has a successful build, then promotes and publishes. A
  broken binary still blocks the release; the pure-Python wheel isn't held up by build time.

## 0.2.1.19 — 2026-05-06

Catch-up entry — 0.2.1.19 shipped without a changelog section. The feature wave from roughly
0.2.1.15–0.2.1.19 (window steps, richer for-each, TSV filtering, …) never got written down,
so the highlights are recorded here.

### New Features

- **TSV filtering** (#141) — the `tsv` step takes `where:`, `limit:`, `offset:`, and
  `columns:`. Filter rows (`where: "book == '${book}'"`) and pick columns without a
  hand-rolled for-each. Safe parser, no `eval()`.
- **`window` step** — sliding / tumbling / condition-based windowing, including token-aware
  windows and a merge block.
- **Richer for-each** — `group-by`, `order-by`, and `parallel:` (parallel iterations with
  ordered results).
- **Paratext verse ranges** — verse-range selection with optional metadata loading.
- **Array slicing in `${...}`** — e.g. `${items[1:3]}`.
- **`~/.sp/user-context/`** — machine-level AI instructions shared across projects; `sp init`
  registers the project and indexes its ai-context files into `~/.sp/`.

### Fixed

- **`resolve()` None handling** — stopped treating missing keys as `None` (which caused silent
  data corruption), fixed the None sentinel, and propagated for-each outputs to the parent
  context.
- **Conditions evaluate via AST** — `${...}` conditions like `is None` / `is not None` work.
- **Linter loop-var scoping** — `!window_advance` inner-step outputs are registered, so loop
  variables aren't flagged as unknown.

### CI / Release

- **PyPI publishing workflow** added (automated publish on release).
- **`sp run` clears `outputs/debug/`** at the start of each run (#145).

## 0.2.1.18 — 2026-04-06

### Fixed

- **Windows install script diagnostics** — Added file size verification and existence checks after download in install.ps1. Changed workflow verification to run install script directly in pwsh instead of spawning subprocess. Improves error reporting for Windows installation issues.

## 0.2.1.17 — 2026-04-05

### Fixed

- **Windows binary runtime dependencies** — Bundle Visual C++ runtime DLLs (vcruntime140.dll, msvcp140.dll) directly into the Windows executable using Nuitka's `--windows-dependency-tool=pefile` flag. Eliminates runtime dependency errors on systems without VC++ redistributables installed. Windows binary is now fully standalone.

## 0.2.1.16 — 2026-04-05

### Fixed

- **Windows npm command resolution** — Added `shell=True` to subprocess.run() calls for npm commands in build_gui.py. Windows requires npm.cmd wrapper which shell resolves automatically. Fixes FileNotFoundError on Windows Nuitka builds.

## 0.2.1.15 — 2026-04-04

### Fixed

- **Windows build compatibility** — Replaced Unicode emoji characters in `build_gui.py` with ASCII tags ([BUILD], [OK], [ERROR], etc.) to avoid `UnicodeEncodeError` on Windows CMD (cp1252 encoding). Nuitka builds now succeed on all platforms.

## 0.2.1.14 — 2026-04-04

### Fixed

- **Telemetry token tracking** — Fixed `response.usage` property access error. Changed to `response.usage()` method call for OpenAI response objects. Token counts and costs now record correctly in telemetry.
- **Registry Unicode handling** — Added `allow_unicode=True` to `yaml.safe_dump()` calls in registry module. Hebrew and Greek text now stored correctly instead of escaped as `\uXXXX` sequences.
- **DuckDB reserved word conflict** — Quoted `references` column name in `acai_entities` table to avoid SQL reserved word collision.
- **Pyright type coverage** — Fixed 149 type errors across 18 files (Logger, cli.py, runner.py, gui/server.py, and 13 others). Full type coverage now 100%.

### Test Coverage

- **Unicode output tests** — Added 8 comprehensive tests in `tests/test_unicode_output.py` covering registry, YAML, JSON, and CSV output with Hebrew and Greek text.
- **Hebrew collation tests** — Added DuckDB and BaseX collation tests with niqquud and cantillation marks verifying correct alphabetical sorting.
- **GUI security tests** — Added executor and server security tests.
- **Full test suite** — All 1763+ tests passing, including integration tests for BaseX and DuckDB.

## 0.2.1.13 — 2026-04-02

### New Features

- **File-based schema loading** — Support `schema_file` in `response_format` config to load JSON schemas from external files instead of inline definitions. This keeps pipeline YAML cleaner and enables schema reuse across pipelines. Example:
  ```yaml
  response_format:
    type: json_schema
    json_schema:
      name: discourse_analysis
      strict: true
      schema_file: schemas/discourse_analysis.json
  ```
- Schema files use standard JSON Schema format and are loaded relative to the current directory.

### Changed

- Added `_load_schema_from_file()` helper to load and parse JSON schemas
- Added `_expand_response_format_schema()` to detect and expand `schema_file` references before calling OpenAI API
- Both inline `schema` and file-based `schema_file` approaches are supported

### Test Coverage

- Added `tests/test_schema_file.py` with 12 comprehensive tests:
  - Schema file loading (valid/invalid/missing files)
  - Response format expansion (inline schemas preserved, schema_file expanded)
  - Integration tests with real OpenAI API
  - Mocked unit tests for parameter passing
  - Error handling for missing/malformed schema files
- Full test suite: **1763 tests passing** (12 new tests added)

### Documentation

- Updated `docs/llmflow-language.md` with file-based schema examples
- Added example pipeline: `pipelines/discourse-analysis-schema-file.yaml`
- Created `schemas/discourse_analysis.json` as reference schema

## 0.2.1.12 — 2026-04-02

### New Features

- **Direct OpenAI Client for Structured Outputs** — LLMFlow now automatically uses OpenAI's client directly when `response_format` is present in step config, bypassing Simon Willison's `llm` package (which may not pass the parameter through). This ensures 100% compatibility with OpenAI's structured outputs feature (`json_schema` mode). No configuration changes needed — works transparently for all pipelines using `response_format`.

### Changed

- **call_llm() detects response_format** — When `response_format` is in config and model is from OpenAI families (gpt-4, gpt-5), automatically routes to `_call_openai_with_response_format()` which uses OpenAI client directly. Falls back to `llm` package for other models/parameters.

### Test Coverage

- **Integration tests for response_format** — Added `tests/test_response_format_integration.py` with 7 tests covering:
  - Basic json_object mode
  - json_schema with simple schema (strict mode, additionalProperties: false)
  - Nested arrays and objects (book segmentation pattern)
  - Prevention of hallucinated fields (strict mode enforcement)
  - Reliability testing (10 iterations, 100% success rate expected)
  - Edge cases: strings with quotes, apostrophes, both
- Tests are SKIPPED unless `OPENAI_API_KEY` is set (to avoid charges during normal test runs).
- Run with: `OPENAI_API_KEY=your-key pytest tests/test_response_format_integration.py -v`

### Documentation

- Updated `docs/llmflow-language.md` — Added note that LLMFlow automatically uses OpenAI client when response_format is present (removes uncertainty about `llm` package support).

## 0.2.1.11 — 2026-04-02

### New Features

- **Structured Outputs Documentation** — Comprehensive documentation for `response_format` with `json_schema` mode guarantees 100% valid JSON from LLM responses. Added to `docs/llmflow-language.md` with full examples showing schema definition, model requirements, and migration path. Eliminates 40-60% intermittent JSON parse failure rate observed in production. (Issue #95)

- **AI Context for JSON Reliability** — Created `docs/ai-context/json-reliability.md` as mandatory reading for AI assistants working with JSON pipelines. Documents the problem (missing commas, unescaped quotes, variable error positions), solution (structured outputs), migration path, and common pitfalls. Referenced prominently in `docs/ai-context/index.md`.

- **JSON Schema Example Pipeline** — Added `pipelines/json-schema-example.yaml` demonstrating three production-ready patterns: (1) nested arrays with complex objects, (2) multi-level required fields, (3) strict mode with `additionalProperties: false`. Includes inline documentation of all schema features.

### Changed

- **audit-prompts Skill Now Audits Pipelines** — Extended `/audit-prompts` skill to check pipeline YAML files for missing `response_format` on JSON steps. New Step 9 detects: (1) JSON steps without `response_format` (legacy/unreliable), (2) steps using `json_object` vs `json_schema` mode, (3) model compatibility (gpt-4o-2024-08-06+ required), (4) project-wide adoption stats. Reports risk level and provides migration code snippets. Skill now applies to `**/*.gpt` AND `**/*.yaml` files.

- **Documented response_format in Language Spec** — Added `response_format` to optional fields for `type: llm` steps in `docs/llmflow-language.md` with cross-reference to new "Structured JSON Output" section. Section includes comparison table (with vs without structured outputs), model requirements, and Gemini alternative syntax.

### Documentation

- **Structured JSON Output section in llmflow-language.md** — 80+ line section with: (1) complete yaml example, (2) results comparison table, (3) key requirements (model, strict mode, additionalProperties), (4) when to use which mode, (5) Gemini alternative. Positioned immediately after `type: llm` field documentation for visibility.

- **Issue #95 comment** — Posted comprehensive solution guide to https://github.com/nida-institute/LLMFlow/issues/95 with migration instructions for discourse-flow project, cost/benefit analysis, and testing checklist.

### Bug Fixes

None (documentation and tooling release only).

## 0.2.1.10 — 2026-04-02

### New Features

- **JSON Output Format Validation in audit-prompts skill** — Added Step 8 to check JSON-producing
  prompts for common formatting issues that cause intermittent parse failures. Detects: (1) code
  fences in OUTPUT SCHEMA sections (confuses LLM into markdown mode), (2) missing JSON formatting
  rules (escaping guidance, structural requirements), (3) incorrect escaping examples (apostrophe
  escaping that's wrong in JSON), (4) inconsistency across multiple JSON prompts in same project.
  Reports risk level and provides specific line numbers with fix recommendations. Based on real
  production failures in discourse-flow where 2 of 8 books failed with delimiter/comma errors due
  to missing formatting guidance. (Issue #94)

## 0.2.1.09 — 2026-04-02

### Changed

- **GUI dependencies now included by default** — Flask, Flask-SocketIO, Flask-CORS, and
  python-socketio moved from optional `[gui]` extra to main dependencies. Since `sp gui`
  is a first-class subcommand of the main `sp` CLI, its dependencies should work out of
  the box without requiring `pip install llmflow[gui]`.

## 0.2.1.08 — 2026-03-30

### New Features

- **Global Prompt Organization Convention** — `sp init` now automatically installs a
  standard organization pattern for `.gpt` prompt files to `~/.sp/conventions/`.
  The convention enforces verifiable transformations (explicit input → output mapping),
  co-located knowledge (rules/examples/data sources grouped by task), consistent heading
  hierarchy, and flexible quality controls with domain-specific naming (GUARDRAILS,
  EVIDENCE DOCUMENTATION REQUIREMENTS, etc.). Projects can override with local
  `docs/prompt-organization-convention.md`. (Issue #93)

- **Audit Prompts Skill** — VS Code Copilot skill installed to `~/.sp/skills/audit-prompts/`
  by `sp init`. Audits `.gpt` files for convention compliance, sprawl detection, and
  three CRITICAL checks: (1) input data grounding (verifies every output field has
  documented input source to prevent hallucination), (2) example diversity (ensures
  examples generalize across passages, not hardcoded to single case), (3) AI-generated
  examples (compares to last commit, flags ANY new examples — #1 source of problems).
  Read-only skill that reports findings with line numbers without modifying files.
  (Issue #93)

- **Automatic editable install in hatch environment** — Added `post-install-commands`
  to `pyproject.toml` so `hatch shell` or `hatch run` automatically installs the package
  in editable mode. The `sp` command is now immediately available for development work
  without manual `pip install -e .` step. (Issue #94)

### Documentation

- Added `docs/global-conventions.md` — comprehensive guide to the prompt organization
  convention and audit skill, including usage examples, best practices, complexity
  categories, project-specific overrides, and critical checks explanation.
- Updated `README.md` — added "Global Conventions & Skills" section with quick usage.

### Bug fixes

- **Telemetry was silently reporting $0.00 / 0 tokens** on every pipeline run.
  Root cause: `response.usage` in `llm_runner.py` was being read as a property but
  the `llm` package exposes it as a method; changed to `response.usage()`.
- **Registry YAML wrote ASCII-escaped Unicode** (`\u05e9` instead of `שׁ`) when
  storing project descriptions containing Hebrew or Greek. Fixed all four
  `yaml.safe_dump` call sites in `registry.py` with `allow_unicode=True` and
  `encoding='utf-8'`.
- **DuckDB `acai_entities` table failed to create** because `references` is a SQL
  reserved word. Column now quoted as `"references"` in `bible_data.py`.
- **DuckDB integration tests were unconditionally skipped** (`skipif(True, ...)`).
  Skip condition replaced with `importlib.util.find_spec("duckdb") is None` so they
  run automatically when DuckDB is installed.

### Type safety — Pyright now reports 0 errors (was 149 across 18 files)

Key fixes across the codebase:
- `modules/logger.py`: added `ClassVar[Optional["Logger"]]` annotation to `_instance`
  and explicit `-> "Logger"` return type on `__new__` so callers see a non-optional type.
- `cli.py`: moved `Logger` import and initialization to module top level, eliminating
  the `logger: None | Logger` union that propagated 22 errors through the module.
- `runner.py`: `resolve()` return values cast to `str` at call sites; `run_llm_step`
  return type widened to `Any` (was `str`, which broke JSON step results);
  `apply_output_template` defined (was called but missing).
- `gui/server.py`: `sys._MEIPASS` accessed via `getattr` instead of direct attribute
  (not in type stubs); `app.static_folder` captured in a typed local variable to
  survive closure narrowing; `room=` → `to=` (Flask-SocketIO API).
- `utils/io.py`: `raise UnicodeDecodeError(msg)` → `raise ValueError(msg)`
  (constructor requires 5 positional arguments).
- `utils/guards.py`: keyword dict comprehension filtered with `if kw.arg is not None`
  to eliminate `str | None` key type.
- Additional fixes in `exceptions.py`, `bible_data.py`, `cli_utils.py`, `linter.py`,
  `rewind.py`, `xml.py`, `xpath.py`, `data.py`, `pipeline_schema.py`, `llm_runner.py`.

### Test coverage

- **Unicode output** (`tests/test_unicode_output.py`, 8 tests): verifies that
  `save_content_to_file` in JSON and text formats, and `ProjectRegistry.register()`,
  write literal Unicode rather than `\uXXXX` escape sequences. Sentinel string is
  `שָׁלוֹם` (shalom with niqquud) plus `בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים` (Genesis 1:1
  with niqquud and cantillation marks — tifha, munah, atnah).
- **Hebrew collation — DuckDB** (2 tests added to `TestDuckDBIntegration`):
  - `COLLATE he` sorts `גָּדוֹל / אֱלֹהִים / בָּרָא` into correct aleph-bet order
    despite attached niqquud.
  - `שָׁלוֹם` (with niqquud) and `שלום` (bare) both sort before `תּוֹרָה`, confirming
    the base consonant — not the niqquud — is the primary sort key.
- **Hebrew collation — BaseX** (2 tests added to `TestBasexIntegration`, run with
  `BASEX_INTEGRATION_TESTS=1`):
  - `fn:sort` with `UCA?lang=he` collation produces aleph-bet order for niqquud-bearing words.
  - `fn:compare("שָׁלוֹם", "שלום", "UCA?lang=he;strength=primary")` returns `0`,
    confirming niqquud are transparent at primary collation strength (essential for
    searching pointed text without knowing whether sources include niqquud).
- `pytest.ini`: fixed section header (`[tool:pytest]` → `[pytest]`); registered
  `duckdb` mark to silence `PytestUnknownMarkWarning`.

### GUI executor refactor

- Extracted `PipelineExecutor` class into a standalone module
  (`src/llmflow/gui/executor.py`) with a parallel copy in `gui/backend/executor.py`.
  Separates testable execution logic from Flask/SocketIO wiring.
- New test files: `tests/test_gui_executor.py` (418 lines),
  `tests/test_gui_server_security.py` (178 lines).

## 0.2.1.07 — 2026-03-27

### GUI Bundling for Nuitka Distribution
- **Restructured GUI for single-binary distribution**: React frontend now builds to static files that are bundled into the nuitka `sp` binary.
- **New production server** (`gui/backend/server.py`): Flask server that serves bundled static React files + REST API in a single process.
- **Build script** (`build_gui.py`): Automates `npm build` → copy to `src/llmflow/gui/static/` → ready for nuitka bundling.
- **CLI command updates**:
  - Added `sp gui` command with `--host`, `--port`, `--no-browser` options.
  - GUI server auto-opens browser and provides clean shutdown on Ctrl+C.
- **Updated `sp-gui` launcher**: Simplified to call bundled server module.
- **Package structure**: GUI static files included via `pyproject.toml` force-include directive.
- **Documentation**:
  - [gui/BUILD.md](gui/BUILD.md): Complete build process documentation.
  - [gui/README.md](gui/README.md): Updated with end-user vs developer workflows.
  - [gui/BUNDLING-SUMMARY.md](gui/BUNDLING-SUMMARY.md): Implementation summary.
- **Test suite** (`test_gui_bundle.py`): Verifies build, static files, imports, and CLI command.
- **Size impact**: Adds ~10-15 MB to binary (Flask ~8MB + React static ~2-3MB). Optional feature - CLI-only users unaffected.
- **Nuitka integration**: Documented `--include-data-dir` flags for embedding static assets.
- **No Python/Node environment needed by end users** - just run `sp gui` from the compiled binary!

## 0.2.1.06 — 2026-03-27

### Global Registry System (Issue #78)
- Added `~/.sp/` global registry for tracking projects, datasets, and databases across the filesystem.
- Implemented `Registry` class with three sub-registries: `ProjectRegistry`, `DatasetRegistry`, `DatabaseRegistry`.
- Added `AIContextRegistry` for tracking AI context files with topics and searchable metadata.
- CLI commands: `sp registry list/info/status/context` for managing global resources.
- Auto-discovery script: `discover_and_register.py` successfully registered 12 projects and 24 datasets from local directories.
- Registry respects `SP_REGISTRY_PATH` environment variable (defaults to `~/.sp/`).
- YAML-based storage for human-readable configuration and easy Git tracking.
- 40 comprehensive tests added in `tests/test_registry.py`; all tests passing.
- Closes issue #78.

### AI Context Discoverability (Issue #79)
**Phase 1: Comprehensive AI Context Index**
- Enhanced `sp init` to create comprehensive `docs/ai-context/index.md` (100+ lines) with:
  - Explicit "Check this FIRST" instruction for AI assistants.
  - Complete list of core files and suggested context files (basex-patterns.md, duckdb-patterns.md, etc.).
  - Usage examples for both AI assistants and project maintainers.
  - Integration guidance for registry system.
- Updated `.github/copilot-instructions.md` template to emphasize checking index.md as second read (after TODO.md).
- Templates marked with `<!-- Generated by sp init -->` for `--update` support.

**Phase 2: CLI Discovery Commands**
- Added `sp context list` command: scans `docs/ai-context/` and displays files with auto-extracted descriptions.
- Implemented context file discovery in `src/llmflow/context.py` (~165 lines):
  - `list_context_files()` - directory scanning and metadata extraction.
  - `extract_description()` - intelligent markdown parsing for descriptions.
  - `format_context_list()` - formatted terminal output.
  - `generate_context_inventory()` - prepared for future AI prompt injection.
- 14 comprehensive tests in `tests/test_context.py`; all tests passing.

**Phase 3: Registry Integration with Topics**
- Extended `AIContextRegistry` with searchable topic-based metadata.
- Added `sp context add <file> --description "..." --topics "basex,xquery,greek"` - register context files with rich metadata.
- Added `sp context search <topics>` - find relevant context across all projects by topic.
- Context files stored in `~/.sp/ai-context/*.yaml` with structured metadata (file, project, description, topics, path, created timestamp).
- Cross-project search enables discovering patterns from any registered project.
- 10 AIContextRegistry tests added to `tests/test_registry.py`.
- Closes issue #79.

### DuckDB Analytics Step Type
- Added `type: duckdb` step: query CSV/Parquet/JSON files with SQL and return results in multiple formats.
- Supports `query:` (inline SQL with `${variable}` substitution) or `query_file:` (path to `.sql` file).
- Output formats: `records` (list of dicts), `dict` (single record), `json` (JSON string), `dataframe` (pandas DataFrame).
- Variable substitution in queries: `SELECT * FROM '${input_file}' WHERE book = '${book}'`.
- Added dependency: `duckdb>=1.0.0` and `pandas>=1.3.0` in `pyproject.toml`.
- 18 comprehensive tests in `tests/test_duckdb_step.py` covering query execution, formats, errors, and integration.
- Design document: `docs/duckdb-analytics-design.md` with rationale and examples.
- Use case document: `docs/xquery-greek-analytics.md` with 10 Greek NT analysis patterns using XQuery+DuckDB.

### Bible Data Access Utilities
- Added `src/llmflow/utils/bible_data.py` with `BibleDataRegistry` for discovering biblical datasets.
- Maps resource IDs (acai, macula-hebrew, macula-greek, sblgnt) to filesystem paths.
- High-level APIs: `load_acai_entity()`, `get_entities_for_passage()`, `parse_reference_to_verse_range()`.
- Supports multiple organizations: checks `~/github/BibleAquifer/` and `~/github/Clear/` automatically.
- Custom base path support with proper isolation (fixes test_custom_base_path).
- XQuery integration: `to_basex_verse_range()` converts human references to BaseX verse IDs.
- DuckDB integration helpers included for loading biblical datasets into DuckDB.
- 27 tests in `tests/test_bible_data.py`; all tests passing.

### Collaboration Principles Documentation
- Added `docs/collaboration-principles.md`: structured framework for AI-human collaboration on Scripture Pipelines.
- Documents five key principles: Common Language, Defined Authority, Testable Claims, Incremental Progress, Explicit Context.
- Includes anti-patterns, implementation guidelines, and measurement criteria.
- Provides practical examples of effective collaboration patterns.

### Test Suite
- **1593 tests passing** (81 new tests added across registry, context, duckdb, and bible_data modules).
- Zero test regressions - all existing functionality preserved.
- Comprehensive TDD workflow: tests written first, implementation followed, all tests passing.

## 0.2.1.05 — 2026-03-25

### Paratext project metadata access
- Added `load_project_file(base_dir, project_name, file)` function to load Paratext project metadata files (Scripture Burrito `metadata.json`, Paratext `Settings.xml`, `BiblicalTerms.xml`, etc.). Auto-detects format by extension: `.json` → dict, `.xml` → lxml Element.
- Added `xpath_text(element, path)` helper function for extracting text values from XML elements via XPath queries.
- Scripture Burrito metadata supports direct dict access in templates: `${burrito.languages[0].name.en}`, `${burrito.identification.name.en}`.
- Paratext XML requires extraction via `xpath_text()` before passing to LLM templates (cannot serialize `_Element` objects directly).
- 9 tests added in `tests/test_paratext_metadata.py`; all 1225 tests passing.
- **Design rationale (eager evaluation):** USFM files are parsed upfront to protect against network mount disconnects during long-running LLM steps. Once `load_usfm_book(format="usj")` returns a dict, the pipeline is independent of filesystem I/O.
- Created example repository: https://github.com/nida-institute/paratext-pipelines with backtranslation and multi-project comparison pipelines.
- Closes issue #73.

### Audit checklists in `sp init`
- Added `docs/audits/` directory created by `sp init` with audit procedure checklists (version-controlled).
- Added `docs/audits/INDEX.md` dispatch table mapping artifact types to checklist files.
- Added `docs/audits/audit-passage.md` (40-line checklist for passage outputs) and `docs/audits/audit-leadersguide.md` (45-line checklist for leader's guides).
- All checklists follow pattern: 20-60 lines, checkbox format only, STOP conditions in bold, no prose.
- Templates marked with `<!-- Generated by sp init -->` for `--update` support.
- `project/audits/` directory remains for audit findings (gitignored, not version-controlled).
- 3 tests added in `tests/test_init.py`.
- Implementation complete for issue #72 (documentation pending).

### AI context documentation
- Added `docs/ai-context/paratext-schemas.md` with comprehensive schema reference for Scripture Burrito and Paratext XML metadata files.
- Documents Scripture Burrito structure: `languages`, `identification`, `agencies`, `copyright` fields with access paths.
- Documents Paratext Settings.xml elements: `LanguageName`, `LanguageIsoCode`, `Versification`, `IsRTL`, etc. with XPath queries.
- Provides guidance on choosing between Scripture Burrito vs Settings.xml for different metadata needs.
- Includes structure overview for `BiblicalTerms.xml` and `BookNames.xml`.
- Updated `docs/ai-context/data-sources.md` to reference the new schema file.

## 0.2.1.02 — 2026-03-20
- Renamed product to **Scripture Pipelines** and CLI binary to `sp` throughout install scripts (`install.sh`, `install.ps1`), `README.md`, `INSTALL.md`, and all docs. Asset names updated to `sp-macos`, `sp-linux`, `sp-windows.exe`. CI workflow asset labels updated to match. `PROJECT_TODO` tutorial backlog in `cli_utils.py` expanded to 8 steps mirroring `sp init` tutorial issues; 5 new tests added to `TestProjectTodoTutorial`.

## 0.2.1.01 — 2026-03-20
- Added `type: basex` step: runs XQuery against a local BaseX database and stores the result in pipeline context. Accepts `database:` (any existing BaseX DB name), `query:` (inline XQuery string) or `query_file:` (path to `.xq` file), `params:` (dict resolved from context and substituted into the query via `{key}` placeholders), and `timeout:` (default 120 s). Built-in error handling for missing `basex` binary, non-zero exit, and timeout. Linter validates required fields and allows all basex-specific keys. (See `src/llmflow/plugins/basex.py`, `src/llmflow/runner.py`, and `tests/test_basex.py`; closes nida-institute/LLMFlow#49.)

## 0.1.5.07 — 2026-03-18

### `llmflow init` scaffolding expanded
- Added `docs/vscode.md`: recommended VS Code settings with privacy/convenience explanation table for AI-assisted pipeline work. Regenerated by `init --update`.
- Added `project/TODO.md`: Active/Backlog/Done task tracking file. Created once on first `init`, never overwritten (designed to be hand-edited). Convention: link GitHub Issues with `→ #N`.
- Added `project/audits/README.md`: naming conventions and guidelines for QA reports and output review notes. Regenerated by `init --update`.

### AI context docs improved
- `AI_RULES_DOC` (→ `docs/ai-context/rules.md`) gains two new rules:
  - Rule 8: read `project/TODO.md` at session start; update Active/Done sections; link issues by number.
  - Rule 9: do not create GitHub Issues — flag the need and let the human open them.
- `AI_INDEX_DOC` (→ `docs/ai-context/index.md`) now points AI assistants to `project/TODO.md` as the first thing to read each session.

### Prompt contract enforcement tightened
- `HELLO_PROMPT` and `HELLO_REPLY_PROMPT` now include proper `requires:` frontmatter so the linter can validate the hello-world pipeline contracts.
- `LANGUAGE_QUICKREF_DOC` gains §6 "Prompt file format" showing the full `---requires:/optional:---` pattern with example.
- `AI_RULES_DOC` rule 7 (declare prompt contracts) was already present; now backed by tests.
- `validate_step_prompt_contract()` in `linter.py`: when a step provides inputs but the `.gpt` header has no `requires:` key, now emits a `❌` error instead of silently treating it as "no requirements". Previously this produced only a ⚠️ warning on "unexpected inputs", which never failed lint. (4 new tests in `TestMissingRequiresIsError`.)

### INSTALL.md
- Mac install instructions now use `~/bin` (no `sudo` or admin rights needed).
- New §3 "Install the `llm` package and models": `llm keys set openai`, Anthropic/Gemini plugin examples, `llm models` verification.
- Windows section rewritten with step-by-step PATH setup, SmartScreen clearing, and persistent API key via PowerShell.

## 0.1.5.06 — 2026-03-18
- Fixed `rewind.py` `replay_step()`: replayed artifacts are now JSON-parsed before being stored in context, so downstream steps receive a `list`/`dict` the same as from a live run. Plain-text artifacts fall back to `str` as before. Steps declaring `output_type: json` emit a warning if their artifact cannot be parsed. (4 new tests in `TestReplayStepJsonParsing`.)

## 0.1.5.05 — 2026-03-17
- Implemented `[*]` wildcard in `get_from_context()`: `${list[*].field}` and deep paths like `${list[*].a[0].b}` now fan out over the list, apply the remaining path to each element, and return a flat list. Missing fields or out-of-bounds indices produce `None` slots; an empty source list produces `[]`. Previously the expression resolved silently to `None`. (6 new tests in `TestStarWildcardResolution`, including `pericope_results[*].segments[0].boundary_signals` deep-path coverage.)
- Added `llmflow init --update`: regenerates files carrying the `<!-- Generated by llmflow init -->` marker (quickref, ai-context docs, tutorial) while leaving hand-edited files untouched. (2 new tests in `test_init.py`.)
- Updated `LANGUAGE_QUICKREF_DOC` (emitted by `init`) to include `type: if`, step-level `condition:`, and the `${list[*].field}` array mapping syntax.
- Documented `condition:` step-level skip guard and `type: if` block in `docs/llmflow-language.md` — both were fully implemented in the runner but absent from the language spec.
- Added `docs/ai-context/data-shapes.md`: canonical shapes for engine-owned artifacts (`passage_info`, `scene_list` items), `[*]` semantics with Python-equivalent mental model, and a clarifying note that consumer-project artifacts are not defined in this repo.

## 0.1.5.04 — 2026-03-16
- Implemented `[*]` wildcard in `get_from_context()`: `${list[*].field}` and deep paths like `${list[*].a[0].b}` now fan out over the list, apply the remaining path to each element, and return a flat list. Missing fields or out-of-bounds indices produce `None` slots; an empty source list produces `[]`. Previously the expression resolved silently to `None`. (6 new tests in `TestStarWildcardResolution`, including `pericope_results[*].segments[0].boundary_signals` deep-path coverage.)
- Documented `condition:` step-level skip guard and `type: if` block in `docs/llmflow-language.md` — both were fully implemented in the runner but absent from the language spec.
- Added `docs/ai-context/data-shapes.md`: canonical shapes for engine-owned artifacts (`passage_info`, `scene_list` items), `[*]` semantics with Python-equivalent mental model, and a clarifying note that consumer-project artifacts (`pericope_package`, `book_flow_json`, etc.) are not defined in this repo.

## 0.1.5.04 — 2026-03-16
- Added `--version` flag to the CLI (`llmflow --version`). The existing `version` subcommand is unchanged. The flag is what CI binary smoke tests call and what users expect from a standard Unix tool. Fixes CI Run #15 failure where `$BIN --version` exited with code 2 because argparse didn't recognise it.

## 0.1.5.03 — 2026-03-16
- Added `json_schema_validator` plugin: validates a pipeline payload against a JSON Schema file. Handles both live Python objects (fresh LLM run) and raw JSON strings/bytes loaded from disk via `--rewind-to`, fixing a crash (`'<string>' is not of type 'array'`) that made schema-validated steps unusable after rewind. (See `src/llmflow/plugins/json_schema_validator.py` and `tests/test_json_schema_validator.py`.)
- Added binary smoke tests to `build-release.yml`: each platform build now runs `--version`, `lint`, and `--dry-run` against the Nuitka binary before uploading, catching packaging failures before they reach GitHub Releases. Added `tests/fixtures/smoke.yaml` as the no-API-key test fixture.
- Fixed `test_parse_bible_reference.py`: bare book name (e.g. `"Psalm"`) is a valid whole-book reference returning `is_whole_book: True`; corrected incorrect `pytest.raises(ValueError)` assertion.

## 0.1.5.02 — 2026-03-10
- Added rewind-friendly checkpoints: every step with `saveas` now records its outputs to `.llmflow/rewind/` so you can rerun later steps without waiting through expensive calls. The CLI exposes `--rewind-to`, `--stop-after`, and `--rewind-dir` for precise debugging, and the linter verifies that required checkpoints and saved artifacts exist before a rewind run.

## 0.1.5.01 — 2026-03-09
- Hotfix release so downstream environments pick up the new step-level retry schema and telemetry updates introduced in 0.1.5.

## 0.1.5 — 2026-03-09
- Added for-each iteration metadata (nesting level, variable label, optional `debug_label` template) to debug transcript filenames so each loop iteration writes a distinct request/response pair. (See [src/llmflow/runner.py](src/llmflow/runner.py#L43-L125) and [tests/test_debug_utilities.py](tests/test_debug_utilities.py#L62-L97).)
- Bumped the package version to 0.1.5 for downstream consumers.

## 0.1.3 — 2026-03-08
- Expanded `llmflow init` scaffolding to generate multilingual reply prompts plus tutorial, quick reference, and AI-context guardrail docs so new projects start with batteries included. (See `src/llmflow/cli_utils.py`, `docs/tutorial.md`, and `docs/ai-context/`.)
- Added OpenAI Responses API moderation detection and friendlier CLI interrupts to avoid noisy tracebacks when pipelines are blocked or stopped manually. (See `src/llmflow/utils/llm_runner.py`, `src/llmflow/exceptions.py`, and `src/llmflow/cli.py`.)
