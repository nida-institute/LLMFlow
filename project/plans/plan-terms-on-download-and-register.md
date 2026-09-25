# Plan — a dataset announces its terms when it lands

**Status:** ruled (2026-09-25). Three decisions are the Captain's and are recorded in §2.
Implementation may start on §4 step 1; step 2 waits on **L1** in `project/open-decisions.md`.
**Issue:** drafted 2026-09-25, not yet filed — `issues-need-approval`.
**Author:** AI, from the Captain's instruction and rulings in conversation on 2026-09-25, and from
measurements of `src/llmflow/cli.py`, `src/llmflow/resources.py` and `data/resources.json` taken
the same day. Every figure below can be re-measured with the command beside it.

---

## 1. What I understand the goal to be

Scripture Pipelines puts other people's texts on a user's machine. Those texts carry obligations —
attribution, restricted purpose, "not for sale", "ask before redistributing" — and the engine
currently states them at the one moment they are least needed and stays silent at the two moments
they are incurred.

The Captain, 2026-09-25: *"when sp downloads and registers a dataset, it needs to display the
copyright and license strings, reminding the user of his/her obligations, such as attribution,
using only for Bible translation purposes, or whatever."* And, scoping it: *"just print the string
to the terminal. perhaps with a requirement for the user to say he/she agrees with the terms before
actually registering - if that's feasible, it is a really good additional step."*

**This is the display, not the permissions model.** `project/plans/design-source-licensing.md`
describes a four-case model of how permission arises, with licence and availability as separate
axes and entitlement held per-machine. That design is `proposed`, nothing is built, and six of its
questions are unanswered. **This plan needs none of those answers** and does not implement it.

## 2. Ruled by the Captain, 2026-09-25

1. **Print the licence at `sp dataset download` and `sp resource add`.**
2. **The consent gate is on `resource add` only.** Registering is the act that takes the obligation
   on; `dataset download` prints and proceeds. Downloading a file you then delete is not agreement
   to anything.
3. **`--accept-terms` for non-interactive use, and fail closed naming it when there is no TTY.**
   Blocking breaks every script and CI run; assuming yes makes the gate theatre.

## 3. What exists today

**The licence is already carried end to end**, so this is display rather than plumbing:

| where | what it does |
|---|---|
| `resources.py:248` | merges `license` from the catalog entry |
| `resources.py:423` | `REGISTERED_FIELDS` includes `license`, so a registration stores it |
| `resources.py:693` | carries `license` into report rows |
| `resources.py:137` | `SEARCHABLE_FIELDS` includes it |

**And the two commands that matter say nothing.** Measured 2026-09-25:

| command | terms shown today |
|---|---|
| `sp resource list` | a **LICENCE** column — `cli.py:594-599` |
| `sp resource add` | none. `✅ Registered '<id>' — <path>` and nothing else — `cli.py:625` |
| `sp dataset download` | none. Calls `fetch(entry, dest=…)` and returns — `cli.py:710-721` |
| `sp dataset search` | none — `cli.py:665-676` |

**The catalog's licence values.** Every entry has one; 30 distinct values. Re-derive with:

```bash
grep -o '"license"[^,]*' data/resources.json | sort | uniq -c | sort -rn
```

The ones that carry real obligations are the point of the feature: `Restricted`, `No license file
— ask before redistributing`, `Custom — see http://sblgnt.com/license/`, and `levinsohn-lgntdf`'s
*"freely distributable, not for sale"*.

**There is no `copyright` field** — `grep -c copyright data/resources.json` returns `0`. So the
goal's "copyright and license strings" is one string until L3 is answered.

## 4. The work

**Step 1 — print, both commands.** No decision blocks this.

- `sp dataset download` (`cli.py:710-721`) already resolves the catalog `entry` before fetching, so
  the string is in hand. Print before `fetch`, so a user who interrupts has still seen it.
- `sp resource add` (`cli.py:609-626`) prints after `register(...)` returns. The licence must be
  printed **before** the write, which means resolving it ahead of registration rather than reading
  it back out.
- A resource registered by `--path` (`register_local`) has no catalog entry and therefore no
  licence string. **Derived, not asked:** there is nothing to print and nothing to gate, so the
  gate does not apply and the command says so rather than staying silent — rule
  `say-which-kind-of-nothing`.

**Step 2 — the gate on `resource add`.** Blocked on **L1**.

- `click` is already the CLI library (`cli_utils.py:10`), so `click.confirm` is the mechanism.
  It raises `Abort` when it cannot prompt, so **fail-closed is its default behaviour** rather than
  something to write.
- `--accept-terms` skips the prompt. With no TTY and no flag, exit non-zero and name the flag.
- **Write down why this prompt exists.** `_configure_ai_assistants` is *"non-interactive by design
  (#204, D4/D5)"* (`cli_utils.py:230-244`) because four prompts defaulting to *No* silently broke a
  fresh setup — the Captain: *"a fresh clone must get skills."* This gate is the same shape and the
  opposite ruling, so the reason it differs belongs beside it: a skills prompt protected nothing,
  and a licence prompt protects someone else's rights. Without that note the next cleanup removes
  it as an inconsistency.

## 5. Tests, written first

- `sp dataset download` prints the licence string for a catalog entry that has one
- `sp resource add` prints it, and prints it **before** the registration is written
- `sp resource add` with no TTY and no `--accept-terms` exits non-zero and names the flag
- `sp resource add --accept-terms` registers without prompting
- `sp resource add --path …` registers with no licence and says there is none
- a declined prompt leaves **no registration file** — the check that the gate is a gate

## 6. What this does not change

- **`resources.json`'s schema**, unless L3 is answered yes — and that is `awesome-biblical-data`'s.
- **`design-source-licensing.md`.** Its six questions stay open; this plan answers none of them and
  depends on none.
- **What a licence permits.** The string is read from the catalog and printed verbatim. The engine
  states terms; it never interprets them. Eight entries say "read this page", and that instruction
  is for a human.
- **`sp resource list`**, which already shows the column.
