# Design — documentation inside the prompt, stripped at load

**Status:** Proposed, 2026-09-16. **Nothing is built.** Awaiting authorization to implement §6 and
rulings on §8.
**Issue:** none yet. Written to be posted to one.
**Author:** AI, from the Captain's rulings on 2026-09-16 and from measurement of
`src/llmflow/steps/llm.py`, `src/llmflow/utils/linter.py`,
`discourse-flow/tests/test_prompt_structure.py` and all five `discourse-flow/prompts/*.gpt`.
Every line number was measured on 2026-09-16 and can be re-measured.

Companion to `design-one-prompt-order.md`, whose §3.4 requires that explanations of a notation
live outside the prompt without saying where. This document says where, and it is deliberately
mechanism-specific so that §3.4 can stay mechanism-neutral.

---

## 1. The ruling

Documentation is written **in the `.gpt` file, beside the rule it explains**, inside a `~~~doc`
fence, and `sp` strips those fences before the prompt reaches the model.

The Captain, arriving at it in one sitting:

> *"perhaps we can encourage `<promptname>.gpt` and `<promptname>.md` files both be created … Or
> is that overkill?"*
>
> *"or we could use literate programming, where `<promptname>.md` has BOTH prompt content and
> documentation, and `<promptname>.gpt` is generated from it?"*
>
> *"what if sp were to automatically convert the .md to a .gpt when loading? and if we do THAT,
> then we could simply let documentation be written directly in the .gpt file, strip the
> documentation, and give the LLM what it needs without multiplying files?"*

### 1.1 Why the prompt is the right home, not merely the convenient one

§2 argues this design beats the sidecar and the tangler on drift. That is a comparison between
mechanisms. It is not the reason documentation belongs in a `.gpt` at all, and the Captain's is
stronger:

> *"`.gpt` files are something we DO want readers to read and understand. Python, etc, not so
> much — we should be able to find all relevant documentation without looking there. `.gpt` files
> are essentially part of the higher level language environment we are defining."*

So the principle is not "documentation may live in source." It is **documentation goes where its
reader already is**, and the two artifacts have different readers:

| artifact | is the reader expected to open it? | where its documentation belongs |
|---|---|---|
| `.gpt` | **yes** — it is part of the language this project defines | in the file, beside the rule (`~~~doc`) |
| Python under `src/llmflow` | **no** — everything needed should be findable without it | `data/ai-rules.yaml`, design documents, `docs/ai-context/` |

**The project already draws this line.** `tests/test_docstrings_say_what_not_why.py` enforces that
a docstring "says what the code does, and carries no provenance" across `src/llmflow`, `tests` and
`tools` — no dates, no commit hashes, no history — and its reasoning lives in `data/ai-rules.yaml`
rather than in the code it governs. It exempts exactly one tree:

```python
#: Shipped documentation, not code.
EXEMPT_DIRS = ("src/llmflow/templates",)
```

That exemption is this distinction, already made: the templates are read as documentation, so the
rule that keeps rationale out of code does not apply to them. A `.gpt` is the same kind of thing
one level further out — an artifact whose reader is meant to read it — and this design extends the
line to cover it.

**The guard that follows.** This document is scoped to `.gpt` and must not be cited to move
architecture or design notes into Python. The opposite rule holds there and is tested. A `~~~doc`
block is documentation in the artifact its reader is already reading; the same move in
`src/llmflow` would be documentation hidden where the reader was promised they need not look.

---

## 2. Why this and not the two designs it replaces

| design | why not |
|---|---|
| sidecar `<name>.md` beside `<name>.gpt` | two artifacts that must agree, with nothing enforcing it. `prompts/hello-view.md` already demonstrates the failure — it opens `# hello.gpt` and embeds a copy of the prompt's frontmatter and body |
| literate `<name>.md` tangled into `<name>.gpt` | removes drift, but the `.gpt` becomes generated: line numbers reported by `sp lint` and the structure tests point into a derived file, and this project cites line numbers constantly. Also needs a tangler, a `DO NOT EDIT` banner, a freshness test and a `sp doctor` rule |
| **documentation in the `.gpt`, stripped at load** | one artifact, so drift is impossible rather than discouraged. The `.gpt` stays the file the author edits, the linter reports on, and the tests read |

The third needs one stripper function and its call sites. The second needed a subsystem.

---

## 3. The notation

A documentation block is a CommonMark fence opened with `~~~doc` and closed with `~~~` at line
start.

~~~text
~~~doc
Both of these are examples, not instructions:

```json
{"scene": "1", "citation": "PHM 1:3"}
```
~~~
~~~

**Standard syntax, our semantics.** Tilde fences and info strings are both CommonMark. What
belongs to Scripture Pipelines is only the meaning of the info string `doc`. Every editor,
renderer and diff tool therefore handles the file correctly while knowing nothing about us: they
see a code block in an unrecognised language and leave it alone.

**Why tildes rather than backticks.** A fence is closed only by the same character. `~~~doc`
therefore contains ```` ```json ````, ```` ```html ```` and ```` ```xml ```` examples at any
length, and the author never counts backticks. With backtick fences the outer block must be
strictly longer than every fence inside it — a rule that holds until someone pastes a longer
example, at which point the block ends early and documentation leaks into the prompt **with no
error**. A literal `~~~` inside a doc block takes `~~~~doc`, which is rare where inner backtick
fences are certain.

The containment and closing rules are CommonMark's, and are not restated here. Per
`design-one-prompt-order.md` §3.4, an existing specification is cited rather than paraphrased —
a second statement of a rule is a statement that drifts.

**Preformatted prose is the intended behaviour, not a concession.** To markdown a `~~~doc` block
is a code block, so its contents are literal: no rendered headings, lists or links. Documentation
reads as source text, which is what a maintainer opening a `.gpt` wants.

**Measured, 2026-09-16.** All 54 fences across the five prompts are ```` ```json ````. The `doc`
info string is unused, and `doc` is not a language any common highlighter claims, so such a block
renders unhighlighted rather than wrongly.

---

## 4. What is stripped, and what is not

This is the part that can go wrong silently, because a stripper that removes too much leaves no
trace.

| | |
|---|---|
| **stripped** | documentation *about* the prompt: what a notation means and where to learn it, links, design history, what was tried and rejected, maintenance notes |
| **kept** | instruction to the model, including the reasons behind a rule and what to weigh when two rules pull against each other |

*Documentation* and *rationale* are not the same thing. `design-one-prompt-order.md` §3.4 keeps
prose for judgement — why a rule exists, what a good answer reads like — because that improves
compliance. Only material addressed to the maintainer is stripped.

This is why the marker is explicit and per-block rather than a heuristic. An author marks what
goes. A stripper that infers will eventually remove something that was doing work, and nothing
will report it.

`sp tools replay` records what was actually sent, so "the model saw less than the file" stays
answerable after the fact.

---

## 5. Where the stripping happens

**The seam already exists.** `steps/llm.py:79–85` computes a `body` by slicing past the
frontmatter — exactly the concept "what the model should see" — and then discards it: it feeds
`extract_template_variables(body)` at line 86 and the undeclared-variable check at 103, while the
function returns `str(rendered_prompt)` at **line 154**, the whole file.

One consequence is worth recording on its own: **the frontmatter is sent to the model today.**
Every LLM call ships `--- requires: … format: … description: … ---`, addressed to the linter.
Whether the strip also drops the header is §8.1.

**Proposed order inside `render_prompt`**, with the reason each position is forced:

| step | line today | why here |
|---|---|---|
| read the file | 44 | |
| `expand_mixins` | 46 | a mixin may carry `~~~doc` blocks of its own; stripping after expansion catches them |
| **strip `~~~doc`** | new | |
| `warn_about_contamination` | 50–51 | a doc block quoting a passage as an example is not contamination of what is sent |
| `resolve` | 58 | a doc block showing `${var}` is an example. Stripping first keeps it from being substituted, or from erroring on a name nothing defines |
| header parse and contract checks | 62–113 | `body_vars` should not see placeholders that exist only in examples |

**One shared function, three callers.** `render_prompt`, `sp lint`, and the structure tests must
all strip through the same code. `test_prompt_structure.py:44` finds headings with
`line.startswith("# ")` — it does not parse markdown, so a `# Heading` inside a doc fence, which
no markdown parser would treat as a heading, is a heading to that scanner. Left unshared, a doc
block would be classified as a task section and fail the band test.

---

## 6. What changes

| where | change |
|---|---|
| `src/llmflow/utils/io.py` | new `strip_doc_blocks(text) -> str`, the single implementation |
| `src/llmflow/steps/llm.py` | call it between `expand_mixins` (46) and `warn_about_contamination` (50) |
| `src/llmflow/utils/linter.py` | `sp lint` strips before structural analysis |
| shipped structure tests | strip before scanning headings |
| discipline and skill | `~~~doc` documented as where explanations live, satisfying `design-one-prompt-order.md` §3.4 |

**Test first.** A test that a `~~~doc` block containing `# HEADING`, `${var}` and a ```` ```json ````
fence survives mixin expansion, is absent from the rendered prompt, and is invisible to the
heading scanner.

---

## 7. What does not change

- **The header parser.** `<!-- -->` keeps its single meaning as the alternative frontmatter form
  (`steps/llm.py:83`, `utils/linter.py:105`). Choosing fences over HTML comments is what avoids
  touching it, and avoids the hazard of a doc block that *shows an example header* being parsed
  as the real one.
- **Prompt file naming and the pipeline contract.** One file per prompt, named as today; `sp run`
  still reads a `.gpt` from disk.
- **`.md` files beside prompts.** Untouched. `hello-view.md` and `reply-view.md` keep whatever
  they are; this design gives them no new meaning.

---

## 8. Rulings needed

1. **Does the strip also drop the YAML frontmatter?** It reaches the model today (§5) and is
   addressed to the linter. Dropping it shortens every call, but it is a behaviour change to
   every existing prompt, and a prompt that relied on the model reading its own `description:`
   would change. Recommended: yes, separately and after the `~~~doc` work, so the two are not
   diagnosed together.
2. **Is `~~~doc` encouraged or required for transformation prompts?** Encouraged, conditional on
   there being non-instruction content to record — which for any prompt with a task band there
   is. Trivial prompts such as `hello.gpt` need none.
3. **Does `sp lint` warn on a `.gpt` whose only documentation is outside a `doc` block?** That is
   the drift this design prevents, but detecting "prose that should have been marked" is a
   heuristic, and §4 argues against heuristics here.

---

## 9. What this buys

The "why" gets written beside the rule, at the moment the author knows it, in the file the author
already has open — and never reaches the model. One artifact, standard syntax, and a stripper
small enough to read in a sitting.
