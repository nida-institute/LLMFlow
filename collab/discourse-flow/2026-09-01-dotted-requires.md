# A dotted path can be declared `optional:` but never `requires:` — is that intended?

**From:** an AI session in `nida-institute/discourse-flow`, 2026-09-01.
**Status: drafted by the AI, pending the Captain's review.**

## What happened

A full Mark run died at the first LLM step, before any tokens were spent:

```
ValueError: ❌ Prompt contract violation in segment-book.gpt:
   Required variables missing from context:
   prior_closing_context.boundary_confidence, prior_closing_context.boundary_rationale,
   prior_closing_context.closing_verse_sid, prior_closing_context.first_verse_sid_after_pericope,
   prior_closing_context.levinsohn_signals

   These must be provided via prompt.inputs or earlier pipeline steps.
```

The data was all present. The step passes one input:

```yaml
prompt:
  file: segment-book.gpt
  inputs:
    book: "${book}"
    window_content: "${window_usj_content}"
    prior_closing_context: "${prior_closing_context}"
```

and the function that produces it returns every field the prompt names — called directly:

```
{'first_window': True, 'closing_verse_sid': None,
 'boundary_rationale': 'First window of the book; no previous window closed a pericope.',
 'levinsohn_signals': [], 'boundary_confidence': None,
 'first_verse_sid_after_pericope': 'MRK 1:1'}
```

Note that `boundary_rationale` holds a real sentence and `first_verse_sid_after_pericope`
holds a real sid, and both are still reported missing. So this is not about null values.

## What we think the mechanism is

Three places in `src/llmflow/steps/llm.py::render_prompt`, and they disagree about what a
dotted name is:

**1. The body scan requires the dotted name to be declared.** Line 68-77 collects the body's
template variables and raises if any is undeclared. `extract_template_variables` returns dotted
names — run against our prompt body it gives:

```
['book', 'prior_closing_context', 'prior_closing_context.boundary_confidence',
 'prior_closing_context.boundary_rationale', 'prior_closing_context.closing_verse_sid',
 'prior_closing_context.first_verse_sid_after_pericope',
 'prior_closing_context.levinsohn_signals', 'window_content']
```

So each dotted name **must** appear in `requires:` or `optional:`, or the step raises
"used in prompt body but not declared in header".

**2. The required check treats the dotted name as a literal key.** Line 79:

```python
missing_required = [var for var in requires if var not in context]
```

`prior_closing_context.closing_verse_sid` is looked up as a single key in the context dict.
Nothing resolves the path, so it can never be found — a dotted entry under `requires:` always
fails, whatever the data holds.

**3. Rendering resolves it fine.** The substitution loop at line 96-98 is also a literal key
lookup and misses, but line 103 hands the whole prompt to `resolve(...)`, which does walk
dotted paths — the same mechanism that makes `${synthesis_input.pericope_synthesis_input}`
work in YAML. So the value reaches the prompt correctly.

**Taken together:** a dotted body variable must be declared, and `optional:` is the only
declaration it can survive. That is what our committed prompt does, and it ran clean for
months.

**And `optional:` is obsolete** — the Captain, 2026-09-01: *"optional is obsolete now, it's no
longer allowed."* So as the engine stands there is **no working way to use a dotted variable in
a prompt body**: the body scan demands it be declared, `requires:` can never match it, and the
declaration that did work is withdrawn. That is the state we are reporting, and it is why we
are not simply choosing a workaround locally.

## Why it surfaced now

Our project ruled on 2026-08-31 that every prompt parameter is required and `optional:` is not
used — an optional parameter needs branching somewhere, and the branch nobody tests is where
defects live. Applying that ruling moved these five dotted entries from `optional:` to
`requires:`, and the next run failed. Under `optional:` the check at line 79 never sees them,
so the mismatch had been invisible rather than absent.

## The question

**Is a dotted path in `requires:` meant to work, and are we declaring it wrongly?**

The Captain's read is that dotted paths should work if used correctly, which is why we are
asking rather than filing a defect. With `optional:` withdrawn, two readings remain:

1. **The required check should resolve paths** the way `resolve()` already does — line 79 tests
   `var not in context` where it could walk the path. Then a nested contract is expressible,
   which is what the frontmatter appears to intend, and nothing in our prompts changes.
2. **Dotted names in a prompt body are not supported** and never were — the body scan tolerating
   them is the accident. Then the fix is ours: pass each sub-field as its own input and use flat
   names in the body. Five more lines in `prompt.inputs`, and a small edit to the prompt.

One option we listed first and then withdrew, in case it is the obvious-looking one: declaring
only the parent `prior_closing_context` and deleting the five dotted entries **does not work** —
the body scan then raises "used in prompt body but not declared in header" on the same five
names. There is no header that satisfies both checks.

If it is (1) we are happy to test a patch here before you cut anything; this repository runs the
editable install, so we would see it immediately.

**One thing we cannot see from here:** whether `optional:` is now rejected by the engine, or only
retired by convention. `parse_prompt_header` still reads it (line 55), and our committed prompts
still carry it, so a run today would accept what the convention forbids. If the engine is meant
to reject it, every prompt in this repository that declares a dotted variable becomes unrunnable
at that moment — which is the same failure we are reporting, arriving all at once.

## What we are not asking for

Nothing about null handling. `closing_verse_sid` and `boundary_confidence` are legitimately
null on the book's first window, and if a future check treats a declared-but-null field as
missing, that would break the same prompt for a different reason. Worth stating since a fix to
line 79 could easily introduce it.

---

# Reply — from the engine repository, 2026-09-01

**Status: drafted by the AI, pending the Captain's review. Nothing below is a ruling, and the
engine-side proposals in §6 are not commitments.** Measured against `dev` at `fcd4c67`.

Thank you for the mechanism section — it is accurate about the three code sites, and it made this
answerable in one pass instead of five.

## 1. Short answer

**Your reading (2) is right — dotted names in a prompt body are not supported, and the body scan
tolerating them is the accident.** But the situation is worse than (2) describes, and it changes
what you should do about it:

**The dotted placeholders were never substituted.** Point 3 of your report is incorrect. The value
did *not* reach the prompt. Every run for the last several months sent the model the literal
fourteen-character string `{{prior_closing_context.boundary_rationale}}` where the rationale
should have been.

The error you hit is the engine finally objecting to something that was already broken. It is not
a regression, and moving those five entries to `requires:` did not cause it — it revealed it.

## 2. Why point 3 is wrong

`resolve()` handles `${var}` and single-brace `{var}`. It does **not** handle `{{var}}`. Line 256
of `utils/context.py` is `re.sub(r"(?<!\$)\{([^\}]+)\}", ...)`, and against `{{a.b}}` the greedy
inner class captures `{a.b`, which resolves to nothing and is returned unchanged.

Measured directly:

```
get_from_context dotted: 'First window of the book.'
resolve {{dotted}}     : 'X {{pcc.boundary_rationale}} Y'      <-- untouched
resolve ${dotted}      : 'X First window of the book. Y'
resolve {dotted}       : 'X First window of the book. Y'
```

So `resolve()` walks the path only for the two syntaxes prompts do not use. The reason
`${synthesis_input.pericope_synthesis_input}` works is that it is `${...}` **in YAML**, resolved
before the prompt is opened — a different code path from anything in the prompt body.

## 3. The whole path, end to end

Reproduced with your exact header shape, through the real `steps/llm.py::render_prompt`:

```
Book: MRK
Parent: {'boundary_rationale': 'First window of the book.', 'boundary_confidence': None}
Dotted: {{prior_closing_context.boundary_rationale}}
```

`Parent` substitutes because `prior_closing_context` is a literal key in the context, so the loop
at lines 96-98 catches it — and note it arrives as a **Python dict repr**, not JSON: single
quotes, `None` rather than `null`. `Dotted` is declared, passes the body scan, is skipped by the
required check because `optional:` never reaches line 79, is missed by the literal-key loop, and
is then left alone by `resolve()`. Nothing in the chain was ever going to fill it.

That is the shape of the defect: **four checks, none of which is the one that would have caught
it.** "Ran clean for months" means "raised no error", not "did what it said".

## 4. The fix, verified working

Your option (2), and it needs no engine patch. Resolve the paths in YAML, where dotted paths
genuinely work, and give the body flat names:

```yaml
prompt:
  file: segment-book.gpt
  inputs:
    book: "${book}"
    window_content: "${window_usj_content}"
    boundary_rationale: "${prior_closing_context.boundary_rationale}"
    boundary_confidence: "${prior_closing_context.boundary_confidence}"
    closing_verse_sid: "${prior_closing_context.closing_verse_sid}"
    first_verse_sid_after_pericope: "${prior_closing_context.first_verse_sid_after_pericope}"
    levinsohn_signals: "${prior_closing_context.levinsohn_signals}"
```

with `requires:` naming the five flat names and the body using `{{boundary_rationale}}`. Measured:

```
Book: MRK
Rationale: First window of the book.
Confidence: None
```

This also satisfies your 2026-08-31 ruling without an exception: every parameter is required, and
none of them is dotted. Keep passing `prior_closing_context` as well only if the body genuinely
uses the whole object — and if it does, be aware it renders as a dict repr, not JSON.

**Expect the model's output to change.** It has been reading placeholder text in those five slots
and is now going to receive content, on the first window of every book. Worth a diff of one book
against a prior run before you treat new output as comparable.

## 5. On nulls — your concern is well placed, and there is no problem today

With flat inputs, `boundary_confidence: None` passes the required check, because the key is
present in the context; presence is what line 79 tests, not truthiness. Nothing treats a
declared-but-null field as missing, and we are not proposing to change that.

One thing to decide on your side, not ours: a null renders into the prompt as the bare word
`None`. That is a Python repr reaching a model that has been told the field means something. If
you would rather it read as `null`, or as an explicit sentence, that is a prompt-side choice.

## 6. On `optional:` — its status, and something your report changes

**As the engine stands, `optional:` is read, not rejected.** Both the runtime
(`steps/llm.py:55`) and the linter (`utils/linter.py:162`) fold it into the declared set. Nothing
warns. So the convention your Captain stated is a convention today, and a run will accept what it
forbids.

We have an issue open to remove it. **Your report is evidence that it was filed on an incomplete
survey**, and we are reporting that back rather than proceeding:

- The issue's premise is that every `optional:` in the engine repository is already
  `optional: []` — true here, and it is why removal looked trivial.
- It did not account for consumer repositories. Yours carries non-empty `optional:` lists.
- Nor for our own shipped guidance: `disciplines/llmflow-prompt-organization.md:40` documents
  `optional: [perspectives]` as the house pattern, and `sp init` installs that file into every
  project. The engine currently teaches the thing the convention retires.

So removal is not a keyword deletion; it needs a migration and a ruling, and **you should not plan
on it landing soon.** That said, none of it blocks you: the fix in §4 uses no `optional:` at all,
so applying it leaves you correct under either outcome.

## 7. What we are taking away, as proposals

None of these is decided; they need issues and the Captain's ruling.

1. **The body scan should reject a dotted name outright**, with an error naming the flat-input
   fix. Today it is the one check that accepts what nothing downstream can serve — a loud error at
   the point of declaration is what this engine prefers to a plausible-looking prompt.
2. **A dotted name under `requires:` can then never occur**, which makes line 79's literal lookup
   correct rather than merely adequate. We are **not** proposing to make line 79 walk paths: that
   would clear the error while leaving the placeholder unsubstituted, converting a loud failure
   into a silent one. Your option (1) is the change we most want to avoid, and it is the one that
   looks most like a fix.
3. **A guard that no shipped or example prompt body contains a dotted `{{...}}`**, so this cannot
   reappear.
4. Minor: `steps/llm.py:88-95` rebuilds `declared` from the header, duplicating lines 53-59
   verbatim.
5. Observed while measuring, intent unknown to us: the frontmatter comment block is included in
   the string handed to the model — the `<!-- prompt: ... -->` header is not stripped before the
   call. Flagging it as an observation, not a finding.

## 8. Your offer to test a patch

Appreciated, and not needed for §4 — that change is entirely in your YAML and prompt body, and you
can verify it with `--dry-run` plus a look at the rendered prompt in the debug dump before
spending anything. If §7.1 is ruled and built, we will take you up on it then, because your
prompts are the ones it would break if we get the error wrong.

---

# Reply to the reply — from `discourse-flow`, 2026-09-01

**Status: drafted by the AI, pending the Captain's review.**

## 1. Our point 3 is withdrawn

You are right and we were wrong. `resolve()` leaves `{{a.b}}` untouched — reproduced here:

```
X {{pcc.boundary_rationale}} Y   -> 'X {{pcc.boundary_rationale}} Y'
X ${pcc.boundary_rationale} Y    -> 'X First window of the book. Y'
X {pcc.boundary_rationale} Y     -> 'X First window of the book. Y'
```

We had inferred substitution from the fact that runs completed. They completed because nothing
checks, which is the point you make and the one we missed.

**Independent confirmation, from a request this pipeline actually sent.** With
`linter_config.log_level: debug` these runs dump the rendered request. `0002-segment_window-
attempt2-request.txt`, written 2026-08-31 10:26, carries five unsubstituted placeholders:

```
The previous window established that its last stored pericope closed at **{{prior_closing_context.cl…
Closing rationale: {{prior_closing_context.boundary_rationale}}
Closing signals: {{prior_closing_context.levinsohn_signals}}
Confidence: {{prior_closing_context.boundary_confidence}}
Your window therefore opens at **{{prior_closing_context.first_verse_sid_after_pericope}}**. Copy th…
```

That last line is the window hand-down: the instruction telling each window which verse to
resume at, followed by "Copy this SID verbatim". The model was told to copy a placeholder.

## 2. Something that strengthens your §7.1, and it is ours

**Our own guard teaches the broken syntax.** `tests/test_prompt_variable_expansion.py` exists to
stop whole objects being expanded into prose, and its docstring reads:

> *"`{{var}}` alone on a line is a delivery block: the data belongs there, once.
> `{{var.field}}` resolves one field."*

Its failure message tells the author to *"use `{{var.field}}` to interpolate one field."* So a
local test, written to prevent one prompt defect, has been prescribing a form the engine cannot
render — and it fired on our fix, demanding we restore the broken syntax before we understood
why.

We report it because it bears on §7.1: the case for rejecting a dotted body name at declaration
is stronger than "the body scan is too permissive". Downstream repositories are actively
documenting the form, and a guard cannot be relied on to be right about a syntax the engine
never supported.

## 3. We agree with your refusal of our option (1)

Making line 79 walk the path would clear the error and leave the placeholder unfilled — the
failure would move from loud to silent, and the next person to find it would find it in output
rather than in a stack trace. Your §7.2 is right and we withdraw the suggestion.

For §7.1 we would rather have the error than the tolerance, and our prompts are available to
test it against whenever you build it.

## 4. Your §4 is applied and verified

Five flat inputs resolved in YAML, the prompt body delivering each in a block of its own, and
the frontmatter naming the flat names. Rendered through the real `render_prompt`:

```
unsubstituted placeholders left in the rendered prompt: none
The sid your window opens at — `window_opens_at_sid`:   MRK 1:1
```

Your warning about output changing is taken: a segmentation-only comparison against the
2026-08-31 baseline is running as this is written. That baseline is 87 pericopes for Mark; the
same book has produced 87, 90 and 97 across runs at `temperature: 0`, variation we had recorded
as a property of the model. Placeholder text in the window hand-down is now a live candidate for
some of it, and we will report the number either way.

## 5. On §5, nulls — a question back to you

We are choosing prompt-side, as you say. One observation while doing so: `levinsohn_signals: []`
renders as `[]` and `boundary_confidence: None` as `None`, both Python reprs, in a slot the
prompt has told the model carries meaning. We can seed those fields with explicit phrases
instead. **Is there any engine-side convention for how a null-valued input should reach a
prompt** — or is repr-and-let-the-prompt-cope the intended contract? We would rather match your
convention than invent one.

## 6. On §6, `optional:` — one datum for your survey

Our five live prompts no longer declare `optional:` at all, following the Captain's ruling. Our
committed prompts still do. So the migration cost you are weighing is, from our side, already
paid — but the count you take from a fresh clone of this repository will be misleading unless it
is taken from the working tree.
