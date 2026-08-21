# Plan — one source for the AI rules, and the merged rule set

**Status:** complete, 2026-08-21. The Captain approved §5 and §6 (*"I approve these rules"*)
and added rule 25. `data/ai-rules.yaml` holds all 25; both generators render from it;
`docs/ai-context/rules.md` has been regenerated; `_RETIRED_AI_RULES_DOC` is deleted.

**Found** 2026-08-21, while checking what `sp doctor` would overwrite in this repo.

---

## 1. What was wrong

`docs/ai-context/rules.md` was written by two generators, each holding its own
hand-maintained text:

| generator | writes | held |
|---|---|---|
| `tools/update_ai_context.py` | this repo's `docs/ai-context/rules.md` | 17 rules |
| `llmflow.cli_utils.AI_RULES_DOC` | what `sp init` puts in a new project | a *different* 12 |

Neither derived from the other, so which rules a project was held to depended on which
generator last ran — and `sp doctor` would replace one set with the other silently, because
`data/file-catalog.yaml` marks the file `policy: generated` and both claims were true.

Measured: a project scaffolded by `sp init` had no authorization workflow and no source-text
rule; this repository was missing five rules the shipped set had.

Captain, 2026-08-21: *"we need to fix this NOW, not file an issue for later."* And: *"why have
multiple generators at all? single source of truth ..."*

---

## 2. Step 1 — landed

`data/ai-rules.yaml` is now the only place the rules are written; `llmflow/ai_rules.py` loads
it; both generators render from it and neither holds a copy. `tools/update_ai_context.py`'s
`RULES` tuple is deleted. The file is force-included into the wheel beside
`file-catalog.yaml`.

Seeded with the Captain's 17 **byte-exact** — generated *from* the existing tuple and asserted
equal, rather than retyped. Retyping is the failure this fix exists to end.

`tests/test_ai_rules_single_source.py` asserts the two renderings hold the same rules and word
each identically. It was written first and failed on 12-vs-17.

**Known consequence, now closed by rule 21:** `tests/test_init.py:434` requires `AI_RULES_DOC` to contain
"design document", which came from retired rule 10. Until the merge below lands, `sp init`
ships no design-authority rule and that test fails. The retired 12 are kept verbatim in
`cli_utils._RETIRED_AI_RULES_DOC`, read by nothing, to be deleted when this merge lands.

---

## 3. Rulings so far

- **Keep all five** of the rules that existed only in the retired 12. Captain: *"keep all of
  these."*
- **Collapse the four near-duplicate pairs.** Captain: *"And yes, collapse them."*
- **Improve the wording** for LLM and human comprehension — the Captain asked whether it was
  needed; §4 states the three defects found.
- **Stale derived output: option B.** Captain: *"B"* — the AI deletes reproducible stale output
  on its own initiative and reports what it deleted and what regenerates it, rather than
  reporting and waiting. Reason, in the Captain's words: *"the AI is reluctant to delete even
  outdated output files or to do a run that would invalidate them, so we are using current code
  with ancient artifacts, a mismatch that gives us wrong results."*

---

## 4. The three wording defects

1. **The addressee shifts.** Some rules address the AI as a consultant advising a third party
   — *"Remind users that outputs are edited in resource repos"*, *"reference capability tables
   when advising users"* — while the rest addresses the AI directly. An LLM reading "remind
   users" infers someone who is not in the conversation, and the rule becomes about nobody.
2. **Rule and provenance are welded together.** The source-text rule carries three lines of its
   own history; the verses rule carries a versification treatise. The footnote competes with the
   imperative. Fixed by a `note:` field, rendered beneath the rule.
3. **Two items are not instructions.** *"**Tone:** technical clarity with interpretive
   awareness"* reads as a heading.

**Stable slugs.** Each rule gets an `id` in the YAML so citations stop depending on position.
Only two numbered citations exist today, both in `design-hath-parity.md`, so renumbering is
cheap now and will not be later.

---

## 5. One further collapse, found while assembling this

Not in the four the Captain ruled on. `#6` of the 17 (*"Highlight human-in-the-loop
expectations"*) and incoming rule 2 (*"Preserve human review"*) are the same rule: generated
output is not finished until a human has reviewed it. Merged below as `output-is-draft`.

=> approved, with §6.

---

## 6. The merged set — 26 rules

**Rules 25 and 26 were trimmed after the split, and rule 26's closing clause was rewritten:** *"sole understanding is decision authority, whoever types the approval"* described a failure state instead of instructing, and the Captain flagged that it "seems to invite freelancing". It now reads as a prohibition.

**Rules 25 and 26 — the Captain's, added and then split at his instruction.** 25 is
`ask-about-the-data`; 26 is `transfer-the-expertise`, whose trigger is his own signal rather
than the AI's estimate of what he knows. His reasoning, which the rules no longer restate:

> The Captain, 2026-08-21: "there are datasets like RST that I don't know that the LLM introduces to me, but I have to become educated enough to make wise decisions about it so the rule will continue to hold. The AI doesn't get to become the expert on these and make all the decisions, the goal is for the Captain to learn at a sufficient level to make the right decisions, growing in knowledge over time." Split from `ask-about-the-data` at his instruction, with the trigger set to his own signal rather than the AI's judgement.

Both were cut to roughly a third of their first draft at his instruction (*"make it less
wordy"*). What the trim removed: the six-item list of what an explanation must contain became
four, and the sentence explaining that rule 25 stops holding became "sole understanding is
decision authority". The quote above is where the removed reasoning is kept.

**Approved by the Captain, 2026-08-21:** *"I approve these rules."* §5's extra collapse approved in the same message. Rule 25 was added by him at that point and revised once, after he corrected the AI's reading of what "educate" required —
see its `note:` in `data/ai-rules.yaml` for his words.

Text below is final as proposed. Collapsed and new rules are marked; unmarked rules are the
Captain's existing text, unchanged.

| # | id | rule |
|---|---|---|
| 1 | `read-the-docs` | **Consult the docs before guessing.** The references listed in `index.md` are authoritative for syntax, architecture and workflows. Read the file rather than recalling it. |
| 2 | `pipeline-schema` | *(collapsed)* **Respect the pipeline schema.** Use only documented keys — `name`, `type`, `prompt`, `inputs`, `outputs`, `llm_config`, `saveas`, `append_to`, and the rest in `docs/llmflow-language.md`. Never invent a field. |
| 3 | `logging-telemetry` | **Preserve logging and telemetry conventions.** Always use `Logger()` from `llmflow.modules.logger`, and start telemetry only after config merging, per `docs/architecture.md`. |
| 4 | `prompts-in-sync` | *(collapsed)* **Keep prompts and pipelines in sync.** Every `requires:` entry in a `.gpt` file must be passed by the step that calls it, via `prompt.inputs`. Cite `docs/llmflow-language.md` when explaining a contract. |
| 5 | `model-capabilities` | *(collapsed)* **Stay within documented model capabilities.** Use a provider-specific feature only where the docs say it is supported — `response_format` is OpenAI-only (GPT-4o/4.1 families) — and name the capability table you checked. |
| 6 | `output-is-draft` | *(collapsed, §5)* **Generated output is a draft.** Files under `outputs/` are drafts until a human has reviewed and edited them, in a resource repo or Obsidian vault. Never call them final, approved, or ready for use, and never hand-wave the review step. |
| 7 | `clarity` | *(reworded)* **Write with technical clarity and interpretive awareness.** Explain *why* a change matters, not just *what* to type. |
| 8 | `ask-on-conflict` | **When requirements conflict, ask.** Use clarifying questions rather than assuming — especially before large edits. |
| 9 | `cite-paths` | *(collapsed)* **Cite concrete paths.** Point at real files — `pipelines/hello-llmflow.yaml`, `prompts/hello.gpt` — with line numbers where you know them, so a human can verify a claim in one step. |
| 10 | `policy` | **Stay within policy.** Follow repository security constraints, avoid leaking secrets, and decline harmful requests. |
| 11 | `project-boards` | **Project boards use four columns.** Backlog → Todo → Doing → Done, in that order, for every board in this organisation. Do not propose or create boards with different columns. |
| 12 | `verses-are-milestones` | **Verses are milestones, not units.** Treat verse references as location markers only — never as the basis for a structural or semantic decision. Do not divide scenes, passages or content blocks by verse count. Pericope boundaries, scene structure and semantic cohesion are determined by narrative and discourse analysis. |
| 13 | `source-text-required` | **Every LLM step must have source text as an explicit named input.** No LLM may reason about a passage unless the text is in front of it. A step without `source_text` in its inputs is producing ungrounded output — answering from training data about the passage rather than from the passage. |
| 14 | `file-organisation` | **File organisation.** Plans go in `project/plans/` (`design-*.md`, `plan-*.md`). Audits go in `project/audits/`. Use `tmp/` only for genuinely throwaway files. Never put a design doc or plan in `tmp/` or the repo root. |
| 15 | `authorization-workflow` | **Authorization workflow (mandatory).** Before editing any file: state the authorization — GH issue, explicit Captain instruction, or audit finding, quoted exactly; declare scope, naming every file that will change and what changes in each; list what will not change; ask whether a plan file, a GH issue, or neither is needed — always ask, never decide alone; wait for explicit sign-off; and write the failing test first if the change is testable, or state why it is not. Invoke with `/authorize`. |
| 16 | `plans-first` | **Plans before implementation.** A non-trivial change requires a plan file in `project/plans/` or a GH issue, reviewed and approved by the Captain, before any code is written. Implementation without one is unauthorized. |
| 17 | `audits-are-diagnostic` | **Audits are diagnostic, not mandatory gates.** An audit is how you find out what needs to change, and it often produces the plan or the issues that then authorize work. It is not required before every edit; it is run when the Captain wants a systematic assessment. |
| 18 | `additive-to-authored` | *(new — from the retired 12, split)* **Prefer additive change to authored work.** Add steps, prompts, pipelines or docs rather than deleting or rewriting existing ones, unless deletion is what was asked for. Authored work is anything a human wrote or approved: code, pipelines, prompts, schemas, docs, plans. |
| 19 | `stale-output-is-a-defect` | *(new — ruling B)* **Stale generated output is a defect, not an asset.** Output is derived, never precious. When the pipeline, prompts or schema that produced a file have changed since it was written, that file is wrong: say so plainly, delete it, and say what regenerates it. Never reason from an artifact whose inputs have changed, and never present a result built from one. Deleting derived output is not a destructive change. The test is reproducibility: if you can name the pipeline that regenerates a file, deleting it costs a run and nothing else — if you cannot name what produces it, it is not derived, so leave it and ask. Regenerating still needs the Captain's word, because a run costs money. |
| 20 | `todo-is-the-session-cache` | *(new — from the retired 12)* **`project/TODO.md` is the session cache.** Read it before anything else. Active is what is in flight, Backlog is what is next, Done is recent context. Link issues as `→ #N` and fetch the issue only when the link is not enough. Never duplicate issue content into it. |
| 21 | `design-authority` | *(new — the retired 12's three design rules, folded)* **Nothing is intentional unless the human says so.** Do not infer intent from code, comments, or a prior session's choices. If you cannot name the design document or the instruction that specifies what you are about to build, stop — you are going rogue. The order is: agree on requirements → agree on approach → write tests → implement, never skipped or reordered. See `disciplines/design-authority.md`. |
| 22 | `issues-need-approval` | *(new — §7, ruled "never silently")* **Draft GitHub Issues for approval.** Write the title and body and show them; run `gh issue create` only after explicit approval. Never create an issue silently. |
| 23 | `context-is-the-only-channel` | *(new — §9)* **Data moves between steps through the pipeline context, nowhere else.** A step reads its inputs from `inputs:` and `${var}`, and returns results through `outputs:`, `append_to:` or `saveas:`. A function or plugin must not write a file for a later step to read, stash state in a module global, or reach for a path the pipeline never declared. A side write is invisible to `sp lint`, to `--dry-run`, to `--rewind-to` and to telemetry, so a pipeline that depends on one cannot be reproduced or reasoned about from its YAML. If a step needs something an earlier step produced, name it in the YAML. |
| 24 | `use-the-pipeline-language` | *(new — §9)* **Express pipeline logic in the pipeline language, not in Python.** Iteration is `for-each`; chunking is `window`; branching is `if` and `condition:`; assembling a structure is `json`; writing a file is `saveas`; substitution is `${var}` and `{{var}}`. A `function` step is for what the language has no construct for — parsing, computation, I/O at a declared boundary. A Python loop over steps, an inline template renderer, or a plugin that decides what runs next moves the pipeline out of the YAML into code the linter cannot see. Read `docs/llmflow-language.md` before writing a plugin; if the language is genuinely missing something, say so and propose it rather than working around it. |
| 25 | `ask-about-the-data` | *(new — the Captain's)* **Assume the Captain knows the data; ask before speculating.** The texts, lexicons, entity data and versification files are his domain. When a field's meaning or a dataset's structure is unclear, ask — a guess about what data means is indistinguishable from knowledge once it reaches the output. |
| 26 | `transfer-the-expertise` | *(new — the Captain's, split from 25)* **When the Captain says he does not know a dataset, or cannot answer a question about it, teaching him is the work.** His word is the trigger, not the AI's estimate. He needs enough to decide, not enough to approve: what it holds, what it omits, where it conflicts with other sources, what is uncertain. Expect several passes. **Never be the only party who understands a dataset he has to decide about.** When he cannot yet check the reasoning, say so and keep explaining. Never proceed on the strength of being the one who knows. |

**Notes rendered beneath their rule, not inside it:**

- `verses-are-milestones` — For cross-versification work (KJV, LXX, Vulgate and others) use the
  Copenhagen Alliance Versification specification, listed in `index.md` under "Versification
  systems". Paratext `.vrs` files are semantically compatible with it — Copenhagen is derived
  from them — and the two can be used interchangeably.
- `source-text-required` — This rule lived only inside the `load-context` skill until
  2026-08-19, when generalizing that skill for human-at-the-helm#1 was about to delete it. It is
  recorded in the rules because rules belong in the rules file, not inside a procedure that
  reads it.

---

## 7. The one contradiction wording cannot fix

The retired rule **"Draft GitHub Issues for human approval — never create issues silently"** is
dropped from the merged set above, because it contradicts a discipline of equal standing:
`~/.sp/disciplines/github-authority.md` lists **"Create GitHub issues"** under *what AI may do
without asking*.

Both are the Captain's. This session has followed the stricter one throughout — asking before
filing, and no issue has been created.

- **A** — the discipline governs: creating an issue needs no approval. The rule stays dropped.
- **B** — the rule governs: add it back as rule 22, and `github-authority.md` moves issue
  creation out of the may-do list. That edit is the Captain's; the file is installed
  machine-wide.

=> never silently.

**Ruled B.** The rule returns as rule 22 — **"Draft GitHub Issues for approval.** Write the
title and body and show them; run `gh issue create` only after explicit approval. Never create
an issue silently." — and `github-authority.md` must stop listing issue creation as a may-do.

**Where that second half lands.** `github-authority.md` is one of the four disciplines shared
with Human at the Helm and byte-identical both sides, so the correction touches four places:

| | |
|---|---|
| `src/llmflow/templates/sp-disciplines/github-authority.md` | the shipped copy; edited here, since this repo is upstream (Q3) |
| `~/github/nida-institute/human-at-the-helm/disciplines/github-authority.md` | via `tools/sync_hath.py --apply` — this changes the **public** methodology, not just this engine |
| `data/hath-sync.yaml` | hash refreshed |
| `~/.sp/disciplines/github-authority.md` | the Captain's machine copy, refreshed by `sp doctor` from a scratch directory |

The change itself: "Create GitHub issues" moves from *what AI may do without asking* to a new
line under the hard stops — *draft the issue and show it; create it only on explicit approval.*
The stated reason for the may-do list stays intact for reading, commenting, branching, pushing
and opening PRs.

---

## 9. Two rules that were missing entirely — added 2026-08-21

The Captain asked whether `sp` has clear instructions against **side writes** (a plugin writing
a file for a later step to read, bypassing the pipeline's own data flow) and for **using the
pipeline language rather than reimplementing its features in Python**. Searched; neither exists.

**Side writes.** One sentence, in prose, in `docs/architecture.md:150`: *"The context is the
only communication channel between steps — there are no side channels."* It is a description of
the engine addressed to a reader, not a rule, and nothing enforces it. `audit-code`'s plugin
checklist covers determinism, data contracts and identifier normalisation; its only file-related
item is *"File reads use explicit paths, not glob patterns"*, which presumes reads are fine. A
plugin writing `/tmp/scenes.json` in step 3 and reading it in step 7 passes every check in the
repository, and the architecture sentence silently becomes false.

**Using the language.** The "no reimplementation" material that exists is about two other
things: `audit-code`'s *Core Reimplementation Check* (plugins reimplementing core utilities like
`parse_bible_reference`) and `design-python-api.md:181` (the API facade must delegate). Neither
addresses rebuilding the language's own constructs. `docs/llmflow-language.md:326` introduces the
`function` step as *"Calls a Python function from the Scripture Pipelines library or custom
code"* and offers no guidance on when a function step is the wrong instrument.
`CLAUDE.md`'s *"Never import Jinja2"* is an instance of this rule that lives only in CLAUDE.md.

**Ruled: `sp` only, not Human at the Helm.** Captain, 2026-08-21: *"add both to sp only, not to
HATH."* Structurally already the case — HATH ships its own `templates/ai-context/rules.md` as a
`create-only` template and the rules file is not in the shared set, so nothing propagates. Added
as rules 23 and 24 above.

**Not done, and not to be folded in:** nothing *checks* either rule. A guard over `plugins/*.py`
for writes outside declared outputs is the mechanical half, and belongs in its own issue.

---

## 8. What happens when §6 and §7 are answered

1. `data/ai-rules.yaml` rewritten with the merged set, `id` and `note` fields added.
2. `llmflow/ai_rules.py` renders `note:` beneath its rule; `render_numbered()` gains no new
   caller.
3. `cli_utils._RETIRED_AI_RULES_DOC` deleted — its five unique rules now live in the source.
4. `tools/update_ai_context.py` re-run, which rewrites `docs/ai-context/rules.md`. **That file
   is the Captain's**; this step is what §6's approval authorizes.
5. `tests/test_init.py:434` goes green again by way of rule 21 carrying "design document".
6. Full suite, and `ruff` held at its current baseline.
