# Design — `sp help resources` and `sp help services`

**Status:** proposed (2026-09-28)

`proposed` is thinking aloud and is **not authorization to build**. Every `=>` in §6 is the
Captain's.

**Issue:** [#264](https://github.com/nida-institute/LLMFlow/issues/264). That issue holds the
larger question — which environments this should reach, and whether a language server is in scope.
**This document is deliberately the small, concrete portion** the Captain asked to start with,
2026-09-28: *"For now, start with providing this same info in `sp help resources`,
`sp help services`, etc, and create a design document for that portion."*

**What this is.** A way to ask the engine what it provides, from the command line.

**What this is not.** Not an editor integration, not a language server, not a studio. Those are
#264's, and nothing here forecloses them — everything below derives from declarations that a
server would read too.

**Author:** AI. Every file:line and count was read from the tree on 2026-09-28.

---

## 1. What exists today

| question a user has | answerable today? |
|---|---|
| what texts can this machine open? | **yes** — `sp resource list` |
| what else is in the catalog? | **yes** — `sp dataset search`, a real XPath predicate over the catalog |
| what datasets are registered? | **yes** — `sp dataset list` |
| what step types exist? | **no** |
| what keys does a step type take? | **no** |
| what does a step type return, and what are those called? | **no** |
| what versification schemes are installed? | **no** |

So resources are half-served and **services are not served at all**, though every fact is
declared: `pipeline_schema.py` carries per-type properties, and the `returns:` enums already name
the members `alignment` and `parallel-passages` produce.

**There is no `help` subcommand.** The CLI is `argparse` (`cli.py:74`), offering `sp <cmd> --help`
per command. `sp help <topic>` does not exist.

**`api_catalog()` is not the source, and this is worth stating because it looks like one.** It
catalogues the *Python API's verbs* — `Pipeline` and `Step` methods, and module-level functions
(`catalog.py:31-60`). That is the engine's own surface, which
`the-language-is-the-whole-surface` says a project must not build against. A command that reported
it would be teaching projects the wrong thing. #264 asks whether `sp help` should read
`api_catalog()`; the answer proposed here is **no**.

---

## 2. The vocabulary, which has to be settled first

#264 asks whether "service" means the step type or the capability behind it. This document cannot
be written without an answer, so it proposes one and marks it for ruling (D1).

**Proposed:** a **service** is a **step type** — the thing a pipeline names in `type:`. That is
what a user is choosing between when they write a step, and it is the only unit the pipeline
language actually has. "Capability behind it" — BaseX, DuckDB, a resource reader — is an
implementation detail a project is not meant to see.

**A resource** is already defined and should not be redefined here: a readable text inside a
dataset, carrying a reader and a versification
(`project/plans/design-resource-vocabulary.md`).

---

## 3. The commands

```
sp help                      # the topics
sp help services             # every step type, one line each
sp help services scripture   # one step type in full
sp help resources            # what this machine can open, by category
sp help resources SBLGNT     # one resource in full
```

**`sp help services`** lists each step type with its one-line purpose.

**`sp help services <type>`** prints what that type accepts and what it returns:

```
type: scripture — fetch one passage from one named resource

  keys
    resource        (required)  a registered resource, by name
    passage         (required)  a reference: MRK · MRK 1 · MRK 1:1 · MRK 1:1-8
    format                      plain | milestones | usj      (default: milestones)
    versification               the scheme `passage` is written in
    include                     ids | morphology | senses | glosses | referents | discourse | syntax
    spans                       cut the passage into units named by word id

  returns
    text                        the passage in the requested format
    reference                   what the reference was parsed into

  see also
    sp help resources           the texts this can name
```

**`sp help resources`** groups by category rather than listing seventy rows flat, and says which
are readable here versus catalogued but absent — a distinction `sp resource list` already makes
and which is the first thing a user needs.

---

## 4. Where each answer comes from

**One declaration per fact, and the command renders it.** Nothing here is hand-written prose beside
the thing it describes; that is how `docs/index.json` went stale for seven months while appearing
maintained.

| what is printed | derived from |
|---|---|
| the step types | the schema's per-type branches, `_STEP_TYPE_PROPERTIES` |
| a type's keys | `allowed_step_keys(step_type)` |
| which keys are required | the schema's `required` for that branch |
| a key's legal values | the schema's `enum`, where it has one — `SCRIPTURE_FORMATS`, `SCRIPTURE_INCLUDE_FAMILIES` |
| a type's members | the `returns:` enum — today on `alignment` and `parallel-passages` only |
| readable resources | `~/.sp/registrations/` |
| catalogued resources | `data/resources.json` |

**Two gaps this exposes rather than creates:**

- **`scripture` declares no members**, so `sp help services scripture` cannot print a `returns`
  block until #263 lands. The command should say *"members are not declared for this step type"*
  rather than print nothing — an absence a reader can tell from a silence.
- **No step type declares a one-line purpose.** `argparse` has `help=` per command; the schema has
  nothing equivalent per step type. Either a `description` is added to each branch, or the text is
  hand-kept somewhere and drifts. The first is the only one consistent with the table above.

---

## 5. What it costs

| piece | where |
|---|---|
| the `help` subparser and its topics | `cli.py` |
| a renderer reading the schema | new, small |
| a one-line purpose per step type | `_STEP_TYPE_PROPERTIES` |
| `docs/ai-context/sp/command-line.md` gains the command | shipped template |
| `tests/test_cli_is_documented.py` | fails in both directions when the parser and that document disagree, so it is the guard already in place |

---

## 6. Decisions

**Answer inline after each `=>`. Only the Captain writes after a `=>`.**

### D1. Is a "service" a step type?

§2 proposes yes. The alternative is that a service is the capability behind it — a resource
reader, BaseX, DuckDB — which is a vocabulary a project is not otherwise given.

=>

### D2. Does `sp help` replace or complement `sp <cmd> --help`?

`argparse` already answers "how do I invoke this command". `sp help` answers "what does the engine
provide". Keeping both means two places a user might look; collapsing them means `sp help run`
must also print invocation syntax.

=>

### D3. Does a step type gain a declared one-line purpose?

§4's second gap. Adding `description` to each schema branch keeps the single-declaration rule;
hand-keeping the text somewhere else breaks it and is cheaper today.

=>

### D4. Does `sp help resources` duplicate `sp resource list`?

They answer nearly the same question. Either `sp help resources` is a grouped view and
`sp resource list` stays the flat one, or one of them is the other's alias, or `resource list`
absorbs the grouping and `sp help resources` only points at it.

=>

---

## 7. What this does not change

- **The Python API.** `api_catalog()` keeps describing the engine's own verbs; this command does
  not report them (§1).
- **`sp resource list`, `sp dataset search`, `sp dataset list`**, unless D4 says otherwise.
- **The one surface.** Everything printed derives from what the command line and the pipeline
  language already expose. `the-language-is-the-whole-surface`.
- **#264's larger question**, which this neither answers nor blocks.
