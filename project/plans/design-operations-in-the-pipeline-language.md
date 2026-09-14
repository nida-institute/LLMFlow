# One domain, many operations — how the pipeline language should say it

**Status: proposed (2026-09-14).** Nothing here is built and nothing is decided. Every `=>` in §5
is the Captain's.

Tracked as **#241**. Raised because the same question arrived five times from five directions:
#167, #168, #125, #169 and #238. The naming half is **#240** and the resolver is **#239**, both
deferred. It is a **language** question, and answering it inside any one of those would settle the
language as a side effect of one feature.

---

## 1. The question

Several parts of this engine are *one domain offering many operations*:

| domain | operations | where it is being decided |
|---|---|---|
| alignment | text, correspondence map, constituent blocks, title field | **#238** |
| verse algebra | `overlaps`, `contains`, `touches`, `equals`, `union`, `intersect`, `verse_count`, `select` | **#169** |
| list transformation | `flatten`, `project`, `slice` | **#167** |
| predicate filtering | filter by value, by threshold, by cross-list membership | **#168** |
| grouping and ordering | `group-by`, `order-by` | **#125** |
| scripture | `format`, `include`, `spans` — already shipped | — |

Each needs a way to say *which operation* and *with what arguments*. The language has three idioms
for that today, they disagree, and every one of these issues is choosing between them again.

## 2. What the language does today, with evidence

**Dispatch is single-level, on `type` alone.** `_type_branch()` (`src/llmflow/pipeline_schema.py:366`)
builds `if {type: const} then {properties}`. Four walkers — `declared_step_types`,
`allowed_step_keys`, `step_value_enums`, `step_keys` — each iterate `allOf` one level deep and read
`branch["then"]["properties"]` (`pipeline_schema.py:430-486`).

**`Step` is flat and generic.** `step_keys()` unions every key across every type; the object model
exposes the union and only *validation* is per-type (`pipeline_schema.py:477-481`).

The three idioms, and what each costs:

| idiom | example | what lint can check |
|---|---|---|
| **flags on a declared type** | `type: scripture` with `format`, `include`, `spans` | everything: keys are per-type, and enums are read from the code that defines them (`SCRIPTURE_FORMATS`, `SCRIPTURE_INCLUDE_FAMILIES`) |
| **`type: function` + `function:`** | the planned `verse_range_union` | almost nothing. `allowed_step_keys("function")` is the common keys plus `function`; the method name is an unconstrained string and every function shares one signature |
| **plugin / registered types** | `type: xpath` | nothing — `allowed_step_keys` returns `None`, so any key is legal by design |

**The tell.** `project/plans/plan-verse-range-set-ops.md` chose the `verse_range_*` prefix, in its
own words, *"for unambiguity at pipeline call sites."* That prefix is a namespace simulated inside
a flat one. It does by naming convention what a type does by declaration, and it exists only
because there is no second dispatch level to put `union` under.

**Two answers already in the tree, and they contradict each other: #167 against #169.** Both
concern *standalone* operations over data. #167's comment calls new step types "the most
declarative" and sketches `type: flatten`, `type: project`. #169's **approved** plan routes the
same kind of thing through a flat function name — `plan-verse-range-set-ops.md:126`: *"A native
pipeline step type wrapping these — callers use `type: function`."* One proposed answer and one
approved answer, opposite, for operations of the same kind.

**#125 is not part of that conflict**, and an earlier draft of this document wrongly said it was.
`group-by` and `order-by` modify *how a host step iterates* and cannot stand alone — which is
exactly their status in XQuery FLWOR, where `group by` and `order by` are clauses of the same
expression as `for`. A clause on a host construct and a standalone operation are different in kind,
so #125 choosing keys on `for-each` says nothing against #167 choosing a step type for `flatten`.

That distinction is worth keeping rather than discarding, because it supplies a rule the rest of
this document needs: **flags on a type are right exactly when the operation cannot stand alone.**
`scripture`'s `format` and `include` pass that test — they modify a fetch. `flatten` and
`verse_range_union` fail it: they are operations in their own right with no host to modify.

## 3. Two axes, not one

The five issues conflate two independent questions. Separating them is most of the work.

**Axis A — where does an operation live?** In an **expression** (the resolver, `${...}`) or in a
**step**. The resolver already navigates, wildcards (`${items[*].field}`) and slices positionally
(`[-3:]`, `[:5]`); #167 and #168 both note it hints at more and stops. An expression composes
without a step per operation; a step is visible to `sp lint`, `--dry-run`, `--rewind-to` and
telemetry, which an expression is not.

**Axis B — how is a step's operation named?** Flags on one type; a `method:` key; one type per
operation; or a flat function name.

A five-operation chain is five steps under most answers to B, and one line under the expression
answer to A. That is the composition argument, and it is why these cannot be answered separately.

## 4. A precedent already in this repository

`sp resource search` evaluates **a real XPath predicate** over the catalog as a tree, with
`lower-case()` and `matches()` supplied at their XPath 2.0 meanings as scoped extension functions
(`src/llmflow/resources.py:154-205`). The engine also mandates `lxml` over `ElementTree` precisely
so XPath and XSLT are available (`rule lxml-for-xml`).

So an expression language over data, with a namespaced function library, is not a new idea here —
it is shipped, tested, and already the house answer for one query surface. #125 reaches for XQuery
FLWOR by name; #168 asks for what is an XPath predicate in all but spelling. Whether that
precedent should govern the pipeline's data operations is a decision, not a conclusion.

## 5. Decisions

### D1 — is this one design or five?

Either the language grows one answer that #167, #168, #125, #169 and #238 all adopt, or each
issue answers locally and the engine carries several idioms on purpose. `one-design` favours the
first and says the migration completes in one pass; the second ships sooner and risks the drift
this document exists because of.

=> One design.

### D2 — expression, step, or both

Whether list transformation and filtering belong in the resolver (composable, invisible to lint
and rewind), in steps (verbose, fully visible), or split by a stated rule — for example
*navigation and filtering in expressions, anything with a side effect or a cost in steps*.

=>  Visibility to lint is helpful if possible.  Usable syntax is also important.

### D3 — if steps, how the operation is named

Flags on one type; a `method:` key with per-method key sets; one step type per operation; or flat
function names. Only the second needs new machinery: recursion in the four walkers and
`_branch_types`. `Step` stays flat, so the object model is untouched and only validation gains a
level. Only the second and third let lint reject an operation that does not exist.

**Where §2's rule puts each domain, if that rule is accepted.** Operations that cannot stand alone
take flags; operations that can need a name of their own:

| domain | stands alone? | what the rule implies |
|---|---|---|
| scripture — `format`, `include` | no, they modify a fetch | flags — as shipped |
| grouping — `group-by`, `order-by` | no, they modify an iteration | flags on `for-each` — as #125 proposes |
| **alignment** — text / correspondence / constituents | **no** — each needs a pair and spans to mean anything | **flags**, which would make #238's current shape principled rather than a stopgap |
| verse algebra — `union`, `intersect` | yes | a name of its own — method, type, or function |
| list transformation — `flatten`, `project` | yes | a name of its own |

If that holds, #238 and #169 want *different* answers, and the language needs both rather than one.

=>  we already have group by and order by in for-each, don't we?

### D4 — whether XPath/XQuery semantics govern

The engine already evaluates XPath 2.0 predicates in `resources.py`, mandates `lxml` for XPath and
XSLT, and #125 cites FLWOR explicitly. Adopting those semantics deliberately would give one
borrowed, documented, widely known model instead of an invented one — and would make the namespace
question answer itself, since XQuery solves flat namespaces with prefixes (`fn:`, `local:`), which
is what `verse_range_*` is imitating. Against: it is a large surface, and pipeline authors are not
all XQuery readers.

=>  Generally the right direction. but how would you apply this to the syntax of sp for verse algebra operations? That is not yet spelled out with examples in this document.

### D5 — what #238 does in the meantime

Alignment is the only known blocker for a downstream project.

**D3's table, if accepted, largely dissolves this.** Alignment's returns cannot stand alone — each
needs a pair and spans to mean anything — so flags are the principled answer for it, not a stopgap,
and #238 is not waiting on the language question at all. The migration cost I first assumed here
would then not exist.

That leaves a narrower version of the question: alignment ships on flags either way, and what
remains open is whether it should *also* be reachable as a method once methods exist. Which is a
smaller decision, and a later one.

=>  Alignment is the bottleneck right now, so shipping on flags is ideal.

---

## 6. What is still open, after §5

The Captain's answers close most of this. **D1: one design. D5: alignment ships on flags.** And
D3's question — *"we already have group by and order by in for-each, don't we?"* — is **yes, and
shipped**: `group_by` and `order_by` are in the schema (`pipeline_schema.py:305-306`), implemented
at `steps/for_each.py:283`, and covered by `tests/test_group_by.py` and
`tests/test_group_by_prefix.py`. They use underscores, not the hyphens #125 proposed. **#125 is
still open on GitHub although the feature is built** — a stale issue, not a pending decision.

So two of the six domains are settled and are not part of what remains:

| domain | status |
|---|---|
| grouping / ordering | **shipped** — flags on `for-each` |
| scripture `format`/`include` | **shipped** — flags |
| alignment | **ruled**, D5 — flags |
| verse algebra, list transformation, predicate filtering | **open** — all standalone pure operations |

What is left is one question about one kind of thing: **how a standalone, pure operation over data
is written.** Two options are viable under D1 and D4; the third and fourth from D3 are not.

**Why two are ruled out.** *Flat function names* (`type: function` + `verse_range_union`) fail
D2's lint requirement outright — the name is an unconstrained string and every function shares one
signature, so nothing can be checked. *One step type per operation* survives lint but produces
`type: flatten`, `type: project`, `type: verse-range-union`, `type: verse-range-intersect` … a type
per operation, which under D1's "one design" is the outcome §2 identified as the drift itself.

## 7. What each viable option looks like

One task, written both ways: **keep the pericopes overlapping the current passage, and compute the
union of their ranges.** It exercises #168 (filter) and #169 (verse algebra) together.

### Option A — expression level, XPath/XQuery-flavoured

```yaml
- name: scope
  type: json
  content:
    in_scope: "${$pericopes[vr:overlaps(., $passage)]}"
    covered:  "${vr:union($pericopes[vr:overlaps(., $passage)])}"
  outputs: scope
```

List transformation (#167) in the same idiom, with projection and no `flatten` because sequences
do not nest:

```yaml
    summaries: "${$scenes ! map{'id': ?id, 'citation': ?citation}}"
    ids:       "${$accumulated?*?id}"
```

**Namespacing falls out** — `vr:` is a prefix, which is what `verse_range_*` was imitating.
**Composition is one line** rather than one step per operation, which is D2's "usable syntax".

**The cost is a parser, and it is filed as #239.** `${...}` is regex substitution today
(`utils/context.py:224`), so this means a real grammar where none exists. #239 records that as a
defect in its own right — the Captain: *"this is a kludge, and should probably be swapped out, but
it's not on our critical path"* — and says explicitly that **this document governs it**: under
Option B replacing the resolver is a modest lint-and-correctness fix, while under Option A it is a
precondition and becomes the larger half of the work. Lint visibility then becomes *achievable* — a parsed
expression can be statically checked for unknown functions and wrong arity — but it is not free,
and it is only as good as the parser. The second and third lines above also show where borrowed
syntax stops being friendly to a translator reading a pipeline: `?*?id` is XPath 3.1 lookup, and
it is not guessable.

### Option B — step level, typed methods

```yaml
- name: in_scope
  type: verse-range
  method: overlaps
  inputs:
    collection: "${pericopes}"
    probe: "${passage}"
  outputs: in_scope

- name: covered
  type: verse-range
  method: union
  inputs:
    ranges: "${in_scope}"
  outputs: covered
```

**Lint is cheap and complete**: each method declares its own key set, so an unknown method or a
missing argument is a lint error, and the machinery is recursion in the four walkers plus
`_branch_types`. Every operation stays visible to `--dry-run`, `--rewind-to` and telemetry.

**The cost is verbosity.** Two steps for what Option A writes in one expression, and a five-operation
chain is five steps carrying five names, five `outputs:` and five intermediate variables.

### The rule that makes either one design

Under D1 a rule has to say which operations live where. The candidate, following D2's own wording:

> **Pure operations over data already in the context are expressions. Anything that reads a
> resource, calls a model, or costs money is a step.**

Under that rule verse algebra, list transformation and filtering are all expressions; scripture,
alignment, `llm`, `basex` and `duckdb` are all steps — which is where they already are. It divides
the six domains exactly along the line §2's clause-versus-standalone rule drew, from the other
direction, and it leaves no domain ambiguous.

Note this rule and Option B are **alternatives, not companions**: if pure operations are
expressions, no `method:` key is needed at all, and the two-level dispatch machinery is never
built.

### The comparison, stated plainly

| | Option A — expressions | Option B — step methods |
|---|---|---|
| usable syntax (D2) | one line, composes | one step per operation |
| lint (D2) | achievable, but only after a parser exists | cheap and complete today |
| XQuery direction (D4) | this *is* the XQuery model | borrows the namespace idea only |
| namespacing | prefixes, free | per-type, free |
| cost | **a grammar and parser where none exists** | recursion in four schema walkers |
| risk | a borrowed syntax non-XQuery readers must learn | verbosity nobody can hide |

=> *(which option, or which parts of each)*

---

## 8. One naming convention, not three

Captain, 2026-09-14: *"we should normalize these names to use hyphens, one convention per
language."* Raised on finding that `group_by` and `order_by` are underscored while #125 proposed
them hyphenated. Measured across the whole schema — 17 declared types, 64 keys:

| | hyphen | underscore | concatenated |
|---|---|---|---|
| **types** | `for-each` — **1** | the seven `load_*` — **7** | — |
| **keys** | **0** | **18**, from `append_to` to `timeout_seconds` | `saveas` |

The finding is not what the `group_by`/`order_by` case suggested. **Keys are already consistent:
every multi-word key uses an underscore.** The inconsistency lives in *types*, where `for-each` is
the lone hyphen against seven `load_*`, and in `saveas`, which uses no separator at all and is a
third convention by itself.

**The Captain's reason for hyphens, 2026-09-14:** *"hyphen is easier to type on most keyboards."*
Underscore needs a shift on most layouts and hyphen does not, in a language whose readers and
writers are translators and analysts rather than programmers. Hyphens also leave `for-each` — the
most-used construct — unchanged, where underscores would rename it.

**Measured, so the cost is not guessed.** Occurrences across 132 files:

| | `for-each` | `saveas` | the 25 underscored types and keys |
|---|---|---|---|
| `pipelines/*.yaml` — the language surface | **0** | 10 | **24** |
| `docs/*.md` | 54 | 62 | 178 |
| `src/*.py` | 30 | 62 | 450 |

The YAML row is the one that matters for a breaking change, and it is small: **34 occurrences in
this repository's pipelines.** The `src` row is mostly Python identifiers, which a YAML rename does
not touch — only the key strings the code reads change. Consumer repositories multiply the YAML
row and not the others.

**A carve-out the count hides: some underscored keys are not ours to rename.** `max_tokens`,
`max_completion_tokens`, `response_format` and `reasoning_effort` are **provider parameter names**.
`rule model-capabilities` already records that `response_format` is OpenAI-only, and the config
notes that models differ on `max_tokens` versus `max_completion_tokens`. Hyphenating those would
break the correspondence with the provider documentation that makes them recognisable, and would
mean the engine spelling a vendor's parameter differently from the vendor.

So the rule probably has two clauses rather than one:

- **Keys the language invents** — `append_to`, `group_by`, `order_by`, `start_when`, `end_when`,
  `size_by_tokens`, `stride_by_tokens`, `output_type`, `output_format`, `include_partial`,
  `query_file`, `debug_label`, `llm_options`, `timeout_seconds`, the seven `load_*` types, and
  `saveas` — take the house convention.
- **Keys passed through to a provider** keep the provider's spelling, and that is a *feature*
  rather than an exception, because a reader matching our YAML against an API's documentation
  should find the same word.

Whether `timeout_seconds` and `llm_options` fall on our side or the provider's is not obvious and
needs checking against what is actually forwarded.

`one-design` requires picking one convention and completing it in a single pass rather than
leaving three standing.

**There is a precedent for how**: `project/plans/design-foreach-syntax-migration.md` ran exactly
this kind of breaking rename — `item_var:` → `for:`, `input:`/`over:` → `in:` — with one commit per
repository and old keys failing loud rather than being aliased. That migration's discipline is the
template, including its refusal to accept aliases, which is what stops a rename becoming a second
convention.

=> **Hyphens**, on the Captain's reason above — *"hyphen is easier to type on most keyboards"* —
with the provider carve-out: a key forwarded to a provider keeps the provider's spelling.
**Deferred, not scheduled**: *"this should be an open issue. not worth the churn right now."* So
the direction is settled and the work is not queued; it goes separately from the operations
question rather than riding with it.

---

## 9. Scope, and what this does not cover

**This document governs the YAML pipeline language only.** "Method" here means a `method:` key in a
step, not a Python method.

The Python API is a separate surface and today exposes none of these domains. `llmflow.__all__` is
`load_pipeline`, `Pipeline`, `ResolvedPipeline`, `Step`, `call_llm`, `parse_bible_reference`,
`resolve_book`, `model_metadata`, `PIPELINE_SCHEMA` and `api_catalog` — the pipeline machinery.
`verse_ranges.Range`, `overlaps` and the rest are not exported, and alignment would not be either.
So there is no second "objects with methods" surface competing with this one; a pipeline reaches
these domains through a step type, or by a dotted path into an internal module through
`type: function`, as #125's own example does with `function: plugins.compress.top_n`.

Worth noting while the subject is open, because it is the same gap seen from the other side: verse
algebra is **built, carries 371 lines of tests, is not publicly exported, and is reachable from a
pipeline only by dotted path into `llmflow.utils.verse_ranges`.** Whether these domains should
appear in the public Python API at all is a real question and is **not** decided here.

Also not addressed: what any individual operation *means* — that stays in each issue. This document
is only about how the language says which operation is being asked for, and where.
