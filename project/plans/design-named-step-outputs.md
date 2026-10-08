# Design — a step's outputs are named, declared, and checkable before the run

**Issue:** [#263](https://github.com/nida-institute/LLMFlow/issues/263), filed 2026-09-28.
The issue carries the problem and the two rulings; this document carries the working, the
measurements and the open slots. The issue is the record outsiders read — it holds no `=>` slots
and no session vocabulary, per `write-shared-records-for-outsiders`.

**Status:** proposed (2026-09-28). All five decisions ruled; one residual slot open.

**All five are ruled in §6**, and D3's rename syntax settled D1, D2, D2′ and D4 in one stroke —
D1 being dissolved rather than answered. Two came back as questions rather than answers on the
way: D1 was badly posed and is withdrawn in favour of D1′, D3 asked for terms which §6 now
defines. **The open slot is the residual under D3**: whether a rename's variable name stays
`[A-Za-z_][A-Za-z0-9_]*` (`text_bsb=text`) or the resolver learns hyphens, which is #239's
territory and meets #240 head-on. Nothing here is implemented.

`proposed` is thinking aloud and is **not authorization to build**. Every `=>` in §6 is the
Captain's, and his answers are quoted verbatim where he gave them.

**Ruled 2026-09-28:** naming a member in `output:` **is** requesting it, and a caller may request
a subset (D4). **#244's starter example waits for this design** (D5) — which puts this in front
of "📖 FIRST — finish the examples" in `project/TODO.md`.

**What this is.** A design for naming the things a step returns, so a pipeline says *which*
result goes *where* by name rather than by position, and so a typo in that naming is caught by
`sp lint` rather than by a confusing failure three steps later.

**What this is not.** It is not a type system for the pipeline language, and it does not propose
checking the *values* a step produces. It proposes checking **names and declared shapes**, which
is a much smaller claim and — see §4 — a much larger fraction of what actually goes wrong.

**Author:** AI, from the Captain's direction on 2026-09-27 and 2026-09-28. Every count and
file:line below was read from the tree on 2026-09-28, not recalled.

---

## 1. What is wrong today

### 1.1 Three layers disagree about whether a named output exists

A dict-shaped `output:` is half-built, and the three layers that would have to agree do not:

| layer | `output: {…}` | where |
|---|---|---|
| schema | **illegal** — `oneOf: [string, array-of-strings]` | `pipeline_schema.py:101-106` |
| linter | **handled, twice** — keys taken as variable names | `linter.py:548`, `linter.py:703` |
| runtime | **ignored** — branches on `str` and `list` only, so nothing binds | `utils/step_outputs.py:41-57` |

A pipeline using the dict form today lints clean and binds nothing. Somebody intended named
outputs, the linter kept the intention, and the runtime never received it.

### 1.2 The list form is positional, and what a position means is decided by the step type

`output: [subject, passage_info]` binds by **order**. Nothing in the YAML says what position 1
holds, the same form means something entirely different on a `function` step, and a wrong order
binds silently and fails far from its cause.

Worse, the arity is unchecked. Measured 2026-09-28:

```
handle_step_outputs({"output": ["a","b","c"]}, "TEXT", ctx)
  -> {'a': 'TEXT', 'b': 'TEXT', 'c': 'TEXT'}
```

Three names on a step that offers two members is schema-legal, lints clean, and binds the same
value three times.

### 1.3 Nothing real depends on the positional form, which is why this is affordable now

Measured across the repository on 2026-09-28:

| | count |
|---|---|
| multi-name `output:` in shipped pipelines and templates | **0** |
| multi-name `output:` in documentation | **2**, both added 2026-09-27 by the change this design supersedes |
| multi-name `output:` in tests | 11 — **4** from that same change, **7** synthetic fixtures exercising the mechanism (`result1/result2`, `baz/qux`, `out1/out2`) |

Every other list in shipped material is a **single** name — `output: [result]`, `output: [burrito]`
— which is a bare name written with brackets and is unaffected by anything here.

So this is not breaking an established convention. It is choosing the design while there is
exactly one consumer, which is the moment `one-design` names: *"We have very few users now, this
is the time to make clean changes before it's too late."*

---

## 2. The vocabulary already exists — this connects two halves

**This is the finding that shapes the whole design.** The names are already declared, per step
type, in the schema, as the `returns:` enum:

| step type | declared members | where |
|---|---|---|
| `alignment` | `text`, `alignments` | `pipeline_schema.py:319-322` |
| `parallel-passages` | `references`, `words` | `pipeline_schema.py:344-347` |
| `scripture` | **none declared** — it has `format:` and `include:` instead | `pipeline_schema.py:247` |

So `returns:` already answers *which members a step produces*. What is missing is *where each one
lands*. Today a step asking for two members binds them to one variable as an undocumented dict,
or to two variables by position.

**The proposal is that these are one vocabulary with two consumptions**, which is the Captain's
addition of 2026-09-27: *"the named parameters could also specify the names used for the keys in
the corresponding dict."* One declaration, read by `returns:`, by `output:`, and by the keys of
the result object — `design-is-declarative`: *"derive everything that needs the same fact from
that one place."*

---

## 3. The proposed shape

### 3.1 Destructured, by name

```yaml
- name: subject
  type: scripture
  resource: SBLGNT
  passage: "${passage}"
  format: usj
  include: [ids, discourse]
  output:
    text: subject           # the step's member  ->  the pipeline's variable
    reference: passage_info
```

Order is irrelevant. A member name the step type does not declare is a lint error (§4).

### 3.2 Taken whole, by the same names

```yaml
  output: fetched           # fetched.text, fetched.reference
```

The keys of that object are the **same declared member names**, so a reader learns one set.

### 3.3 `scripture` gains its declared members

`scripture` has no `returns:` today. It would declare `text` and `reference`, where `reference`
is what `parse_bible_reference` computes — the fact #244's starter example needs so it can name
its output files without reaching into our Python (`the-language-is-the-whole-surface`).

`include:` is **not** part of this vocabulary and is not changed. Its families are content
*inside* the `text` member's container, not members of the step's result; conflating them would
be the opposite of the separation this design is for.

### 3.4 The `function` step is the stated boundary

A `function` step returns arbitrary Python, so the engine cannot know its member names. Positional
stays there and is the honest form.

That is not two designs for one thing — it is *"declare what the step type knows"*, with the one
case that cannot stated rather than left for a reader to discover. `one-design` asks that where an
older path survives we name who depends on it; this names it.

---

## 4. What can be checked before the run — correcting an earlier claim

**On 2026-09-27 an AI told the Captain that types "could not be checked at lint time" because the
engine has no type system for context values. That was wrong**, and it was wrong because it
confused checking a *value* with checking a *declared name*. The second is most of the benefit and
is entirely static. Recorded here rather than quietly fixed, because the claim was made in a
conversation that this document is the outcome of.

What lint can do, given the declarations in §2:

| check | static? | why |
|---|---|---|
| the member name exists on this step type | **yes** | the enum is in the schema; `output: {refrence: x}` is a typo lint can name |
| the member was actually requested | **yes** | `returns:` is a literal list in the YAML |
| arity — no more names than declared members | **yes** | fixes §1.2 outright |
| a field access on a member of declared shape — `${passage_info.filename_prefix}` | **yes, where the member's shape is declared** | `reference` is `parse_bible_reference`'s fixed return; its fields can be declared once |
| a field access on a member whose shape depends on data | **no** | and lint must say *unknown*, not pass |
| the value's runtime type | **no, and not proposed** | checked at bind time instead, where it fails loudly at the step rather than three steps later |

**The honest limit, and it must be stated in the implementation rather than discovered.** The
checks above hold to the degree the governing keys are **literals**. `format: "${fmt}"` or
`returns: "${members}"` leaves lint unable to know which members exist, and it must then report
*not checked* rather than *checked and fine*. A guard that silently gives up is the failure
`check-the-source-not-the-rendering` exists to name: *"a guard that can quietly reduce to nothing
is worse than an absent one, because a triage counts it as present."*

---

## 5. What this costs

| piece | where |
|---|---|
| the object form of `output:` | `pipeline_schema.py:101-106` |
| per-type member declarations, `scripture` gaining one | `_STEP_TYPE_PROPERTIES` |
| handlers return a member-keyed dict rather than a tuple | `steps/*.py` |
| the dict branch in output binding | `utils/step_outputs.py:41-57` |
| the linter's two dict branches **corrected**, not written | `linter.py:548, 703` |
| `api_catalog()` reports the members | `catalog.py` |
| the shipped language reference and quick reference | `docs/`, `templates/project/docs/` |

Nothing in `pipelines/` migrates, because nothing uses the multi-name form (§1.3).

---

## 6. Decisions

**Answer inline after each `=>`. Only the Captain writes after a `=>`.**

### D1. Which side of the mapping is the key?

`output: {text: subject}` reads "the step's `text` goes into my `subject`", and matches
renaming-destructuring elsewhere. The linter's existing branches assume the opposite — they take
the **keys** as variable names (`linter.py:703`, `declared_outputs.update(outs.keys())`), so
`{subject: text}`. One of the two is being corrected either way.

=> Not sure what "is the key" means, but the `sp` language provides services, they return specific things, and we can treat them kind of like Python libraries. Or assume one global library. The caller needs to be aware of the arity, names, and types that each service provides, what mechanisms should we consider?

**Not answered — the question was badly posed and is withdrawn.** "Which side is the key" is
jargon about YAML mapping mechanics, and it asked the reader to decode the implementation before
they could answer. The question underneath it is the one asked back: **how does a caller learn
the arity, names and types a step provides?** Restated as D1′ below, which must be answered
first; the mapping direction then falls out of it rather than being chosen on its own.

**D1′ — how does a caller learn what a step provides?**

The framing offered is *"the `sp` language provides services… we can treat them kind of like
Python libraries. Or assume one global library."* Taking that seriously: a library user learns a
signature from documentation, from a tool, or from the language failing them at the right moment.
All three are available here and they are not alternatives.

| mechanism | what the caller does | exists today? |
|---|---|---|
| **the declaration** — `returns:` enums per step type in `pipeline_schema.py` | nothing; it is the single source the rest derive from | **yes**, for `alignment` and `parallel-passages`; `scripture` has none |
| **the reference document** — a table per step type in the shipped language reference | reads it | partly, and written by hand, so it drifts |
| **the command line** — e.g. `sp lint` naming the legal members when one is wrong, or a command that prints a step type's members | asks the tool | **no** |
| **`api_catalog()`** — the machine-readable syntax-to-API map | reads it programmatically | **yes**, but it does not report members |

**The recommendation, and the reason it is not "all four".** One declaration, three derivations.
The `returns:` enum is the source; the reference table is *generated* from it rather than typed;
`api_catalog()` reports it; and lint's error message lists the legal members rather than merely
saying one was wrong. Nothing is hand-kept, so nothing drifts — `design-is-declarative`, and the
same pattern `sp/index.md` already uses to stay true.

**What that leaves genuinely open** is whether the command line grows a way to *ask* — something
like `sp lint --explain scripture`, or members in `sp` help output. That is the one piece with no
existing home, and `the-language-is-the-whole-surface` bears on it: a project reaches the engine
through the command line, so a member vocabulary a project can only discover by reading our
source is one it has not really been given.

=>  This is a smaller version of a larger question.  We need both the command line and the api to provide a way to ask what categories of resources are available, what resources exist in each category, what categories of services are available, what exists in each category, etc. We need a design document for that.  And later, we need to ask what user environments this might be most useful in - only in a Claude session, or perhaps also in Jupyter?   VS Code and Emacs?  Do we need our own studio that can show what is available in the UI and allow apps to be built with guidance and tested step by step?   Raise a gh issue for this and we can brainstorm later.   For now, start with providing this same info in `sp help resources`, `sp help services`, etc, and create a design document for that portion.

### D2. What does a single output name bind?

- **the primary member** (`text`) — exactly today's behaviour, breaks nothing, but the member
  vocabulary is then only visible in the mapping form;
- **the whole object** — cleaner, and changes the meaning of every existing `output: source_text`
  in every project;
- **primary when one member is filled, object when several** — convenient, and the kind of rule
  that surprises someone later.

=> It governs the name used within the sp service's implementation and the key in the dict. Let's consider requiring the calling module to specify the same name in returns ... is that too restrictive? Discuss ...

**Read as answering a different question, and left open.** The answer describes what a *member
name* governs — the name inside the step's implementation, and the key in the result dict — which
is a statement about the vocabulary rather than about what a bare `output: fetched` binds. The
slot stays open for that. **The substantive proposal inside it is taken up as D2′.**

**D2′ — must the caller name the member identically, rather than renaming it?**

The proposal: drop renaming, so a member lands in a variable of its own name.

```yaml
returns: [text, reference]     # requests them; each lands in `text` and `reference`
```

**What it buys.** The mapping direction question disappears entirely — there are no two sides,
so D1 is not merely answered but deleted. One name per member across the declaration, the
request, the binding and every reference to it. A reader of any pipeline sees the same word
everywhere, which is the property that makes a vocabulary learnable.

**What it costs, and this is the "too restrictive" the question asks about.** Two members from
two steps cannot coexist: two `scripture` steps both offering `text` would collide on one context
variable, and the second silently overwrites the first. The starter example has exactly this —
a Greek `subject` and an English `english`, both of which are `text`. So unrenamed binding
either forbids two steps of one type in a pipeline, or needs a qualifier — `${subject.text}`,
which is the whole-object form of D2 arriving by another road.

**So D2 and D2′ are one question, not two**, and the honest shape of it is: *does a member land
in a variable named by the pipeline, or under the step's own name?* The second is cleaner to read
and cannot express the example we are about to ship.

**RULED 2026-09-28 — A: a bare output name binds the primary member.** The Captain, answering the
residual after D3's rename syntax had settled the list form: *"Yes, A of course."*

So `output: subject` binds the step's **primary member**, not an object of all of them. For
`type: scripture` that is `text`, which is exactly what it binds today — **so no existing pipeline
changes.** The alternative would have turned `${subject}` from a string into a dict in every
pipeline in every project.

**What follows, and it is the one real cost:** every step type with more than one member must
**declare which is primary**. Proposed: `scripture` → `text`, `alignment` → `text`,
`parallel-passages` → `references`. That declaration goes beside the members in
`_STEP_TYPE_PROPERTIES`, so it is derived rather than hand-kept, and `sp help step-types` reports
it.

**A step type with exactly one member needs no such declaration** — its only member is primary by
construction, which is every step type in the language today except the two that carry `returns:`.

=> Agreed.

### D3. Is a declared member shape in scope, or only member names?

Names alone deliver rows 1–3 of §4. Declaring `reference`'s fields as well delivers row 4 —
`${passage_info.filename_pefix}` caught at lint. It is more declaration to write and to keep true.

=> shapes? Define terms.

**Terms, as asked.** Three things are being distinguished, and this document used one word for
the third without ever defining it:

| term | what it means here | example |
|---|---|---|
| **member** | one of the things a step returns, named in its `returns:` enum | `text`, `reference` |
| **arity** | how many members a step offers, and how many the caller asked for | `scripture` offers 2 |
| **shape** | the internal structure of one member — its fields and their types, if it has any | `reference` is an object with `book_code`, `filename_prefix`, … 18 fields |

So the question is: **does the engine declare only that `reference` exists, or also what is
inside it?**

- **Names only.** Lint catches `output: {refrence: …}` — a member that does not exist. It cannot
  catch `${passage_info.filename_pefix}`, because it does not know `reference` has a
  `filename_prefix` field.
- **Names and shapes.** Lint catches both. The cost is that every member's fields are declared
  somewhere and kept true; `reference` is the easy case because
  `parse_bible_reference`'s return is fixed and already documented field by field in
  `docs/ai-context/project/data-shapes.md`. `text` is the hard case — it is a plain string for
  `format: milestones`, and a USJ document for `format: usj`, so its shape is conditional on
  another key.

**A middle position exists and may be the right one:** declare a shape where a member *has* a
fixed one, and declare the others as unspecified — provided lint then reports *unchecked* rather
than passing silently, per §4.

=>  Let's introduce a syntax that allows a step to keep the existing name or to rename it.  
`returns [text-bsb=text, reference] means "get the text and store it in a variable named text-bsb, get the reference and return it as reference".

**RULED 2026-09-28, and this one answer settles D1, D2, D2′ and D4 together.** It is recorded
here under D3 because that is where it was written; its reach is wider than the question it sits
under.

**The form.** A member is named to request it, and may optionally be renamed on the way into the
context:

```yaml
returns: [text-bsb=text, reference]
#          ^variable ^member   ^member, kept under its own name
```

Left of `=` is the pipeline's variable, right is the step's member — an assignment, read the way
an assignment reads.

**What it settles, in one stroke:**

- **D1 is dissolved, not answered.** There is no mapping with two sides to choose between; there
  is a list, and an optional rename inside an entry.
- **D2 is answered.** A bare member name binds to a variable of its own name, so the common case
  needs no ceremony and the vocabulary is visible in every pipeline that uses it.
- **D2′'s objection is met.** Two `scripture` steps in one pipeline both offering `text` no longer
  collide, because either may rename. The starter example — a Greek passage and an English one —
  is expressible, which the unrenamed form could not do.
- **D4 is answered: one key, not two.** Requesting and placing are one act in one list.

**⚠️ The example's own name does not work today, measured 2026-09-28.** Hyphenated variable names
are not resolved, and they fail **silently**:

```
resolve("${text-bsb}", {"text-bsb": "HYPHEN OK"})   ->  '${text-bsb}'   # unresolved literal
resolve("${text_bsb}", {"text_bsb": "UNDERSCORE OK"}) ->  'UNDERSCORE OK'
```

The unresolved text is returned as a literal rather than raising, so `${text-bsb}` would be
written into a file or sent to a model exactly as written. That is the failure
`project/overview.md` calls the one to design against — *"a loud error rather than a plausible
result"*. It is also more evidence for **#239**, which records that the resolver is regex
substitution rather than a parser.

**So the syntax stands and the example must change**, one way or the other, and which is not
decided here:

- **variable names stay `[A-Za-z_][A-Za-z0-9_]*`** and the example is `text_bsb=text`; or
- **the resolver learns hyphens**, which is #239's territory and touches every `${…}` in every
  pipeline.

The second is the larger change and would want its own decision; the first costs one character.
Note that **#240** — normalise names to hyphens — points the other way for *key* names, so these
two conventions meet here and the meeting should be deliberate.

=>

### D4. Does `returns:` stay, or does `output:` subsume it?

They would then both name members: `returns:` asks for them, `output:` places them. That may be
one key too many — a step naming a member in `output:` has requested it by saying so.

=> Naming a member in output constitutes requesting it.  A caller is not required to request all possible outputs.

**RULED 2026-09-28.** Naming a member is requesting it, and a caller requests a subset freely.

**What follows.** There is one key, not two, and asking for a member is the same act as saying
where it goes. A member nobody names is not computed — which matters for cost, because
`parallel-passages`' `words` and `alignment`'s `correspondence` are the expensive members and
today's `returns:` exists largely to avoid paying for them.

**It also settles `say-which-kind-of-nothing` for this shape.** A member that was not requested
is **absent**, and `returns:`/`output:` is the declaration that explains the absence — which is
the exemption that rule states for a request list. A member that was requested and found nothing
is an empty collection; one that could not be looked up is `null`.

**One tension to resolve, and it is between two of these answers rather than within either.**
D2's answer proposes *"requiring the calling module to specify the same name in returns"*, which
presumes `returns:` survives; this answer removes the need for it. If `returns:` goes, D2′'s
"same name" requirement has to attach to `output:` instead. Both readings are live until D2 is
settled.

=> Why do we need both returns and output?  Can we do all this with just one?

**Answered: we do not, and one is enough.** D3's rename syntax does both jobs in one list —
naming a member requests it, and `variable=member` says where it lands. There is no second key
left to justify.

**Which word survives is the open part, and the answer is not the one the example suggests.**
The ruling was written as `returns: [...]`, but:

| | `output:` | `returns:` |
|---|---|---|
| step types carrying it | **every one** | 2 — `alignment`, `parallel-passages` |
| occurrences in this repository | hundreds, in every pipeline | a handful |
| what the word says | where the value goes | what the step produces |

Collapsing onto `returns:` renames the most widely used key in the language and rewrites every
pipeline in every project. Collapsing onto `output:` retires a key used by two step types and
leaves every existing pipeline untouched — and `output: [text_bsb=text, reference]` reads exactly
as well.

**Recommendation: keep `output:`, adopt the rename syntax, retire `returns:`.** The migration is
then two step types rather than the whole language. `one-design` is satisfied either way; the
difference is only in what it costs.

=> keep output  ...  ditch returns

**RULED 2026-09-28.** `output:` is the one key. `returns:` is retired from the language.

**Blast radius, measured the same day rather than estimated:**

| | |
|---|---|
| pipelines using `returns:` — `pipelines/`, shipped templates | **0** |
| source files | 4 — `pipeline_schema.py`, `steps/alignment.py`, `steps/parallel_passages.py`, `utils/alignment.py` |
| test files | 2 — `test_alignment.py`, `test_parallel_passages_step.py` |
| documentation | 3 lines of `docs/llmflow-language.md` |

So the migration is real but contained, and **no project's pipeline changes** — which is the same
argument §1.3 makes about the positional form.

**`utils/alignment.py` has a Python parameter named `returns`**
(`aligned_text_for_spans(..., returns=('text',))`). That is an internal signature, not the
language, so retiring the YAML key does not require renaming it. Left alone deliberately;
renaming it is a separate, cosmetic change.

**`one-design` applies to how this lands:** `alignment` and `parallel-passages` migrate in the
same change that introduces named outputs. A half-migrated language with two ways to ask for a
member is the thing the rule exists to prevent.

### D5. Does #244's starter example wait for this?

It currently demonstrates `output: [subject, passage_info]`, committed at `c90f7a1`. The example
ships as the worked pattern every project copies, so whatever it teaches is what spreads.

=> Yes, the starter example waits for this.

**RULED 2026-09-28.** #244 waits.

**What follows, and it reorders the queue.** `project/TODO.md` has "📖 FIRST — finish the
examples" ahead of everything. This design now sits in front of it, and group B — the pipeline
and the prompt — must not be written until D1′, D2 and D3 are settled, because the example's
`output:` line is the thing under design.

**The engine change already committed at `c90f7a1` is not wasted and is not wrong.** It delivers
`passage_info` through the language rather than through our Python, which is what
`the-language-is-the-whole-surface` required and what unblocked the example in the first place.
What changes is the *form* the example writes it in. **Whether `c90f7a1`'s positional form is
reverted, kept as a second form, or migrated once this lands is not decided here** — it is a
consequence of D2 and belongs with it.

---

## 7. What this does not change

- **`include:`** and the analysis container. Different concern, §3.3.
- **Single-name `output:`**, which is every existing pipeline.
- **`function` steps**, which keep positional, §3.4.
- **The one surface.** Everything here is expressed in the pipeline language and reported by
  `sp lint`; nothing asks a project to import anything. `the-language-is-the-whole-surface`.
