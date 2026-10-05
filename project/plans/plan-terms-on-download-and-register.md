# Plan — a dataset announces its terms when it lands

**Status:** ruled (2026-09-25, and the rest 2026-10-05 — §2a) and built, uncommitted.
**Issue:** #252.
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

## 2a. Ruled by the Captain, 2026-10-05

4. **L1 — (c), a pointer is not gated.** A licence that points elsewhere rather than stating terms
   is printed, the resource is registered without a prompt, and the record says the terms were
   shown and not agreed. *Narrowed by 8 and 10 the same day:* only a bare pointer whose text
   could not be fetched.
5. **L2 — agreement is recorded on the registration.** *"A user needs a record of agreements to
   use when they publish their own artifacts."* Asked once; a re-registration asks again when
   the catalog's licence string differs from the one recorded — or, after 9, the fetched text.
6. **The registration contains a link to the licensing agreement.** The catalog has no such field
   (its keys, measured 2026-10-05: `id name category description formats license github url
   acquire notes download provides`), so the engine fills it — the Captain chose option B:
   a URL inside the licence string; else the official page of a standard licence (`CC BY-SA 4.0`,
   `MIT`, `Apache-2.0`, …); else the source's `url`, marked `link_kind: source-page` so it is
   never mistaken for the agreement. A `license_url` field upstream in `awesome-biblical-data` is
   the lasting fix and goes there as an issue.
7. **The record reads back as `sp resource terms [ID …]`** — every registration, or the ones a
   publication used. Under `sp resource`, not `sp tools`: an agreement belongs to a registration.

The record, written under `terms:` in `~/.sp/registrations/<id>.yaml`:

```yaml
terms:
  license: "Apache-2.0 (code) — see LICENSE.md for data terms"   # exactly as shown
  agreed_to: summary            # or: text, for a bare pointer whose text was fetched
  link: https://github.com/…    # where the full terms are
  link_kind: source-page        # or: licence
  pointer: "see LICENSE.md for data terms"        # only when the string points
  text_sha256: …                # or text_not_fetched: <why>
  text_source: https://github.com/…/LICENSE.md
  agreed: 2026-10-05            # absent when shown and not agreed
  via: prompt                   # or: --accept-terms
  presented: true
  text: ~/.sp/registrations/<id>.licence.txt
```

8. **The licence string is a summary, and agreement is to the summary, with the pointer
   recorded.** *"I would like it to say they agreed to the summary and also provide the
   pointer."* `MIT`, `Apache-2.0 (code) — see LICENSE.md`, `Restricted — see <url>` and
   levinsohn's are all summaries; the *see …* part is recorded as `pointer`. **`Custom — see
   <url>` is a summary** (Captain: yes). Only a string that is nothing but a pointer — `See repo`,
   `See site`, `See source`, four entries — has no summary.
9. **The full text is fetched, saved and hashed** (Captain: yes) — a GitHub repository's licence
   through the API, or a plain-text file the licence names; a web page stays a link. Saved as
   `~/.sp/registrations/<id>.licence.txt`, recorded by SHA-256 and source; a changed text asks
   again. Why it could not be fetched is recorded rather than left blank.
10. **A bare pointer whose text was fetched is gated** (Captain: yes), and agreement is to the
    text. L1 (c) now covers only a bare pointer whose text could not be fetched.

Measured against the live catalog after building: `macula-hebrew`, `macula-greek-nt`, `acai` and
`levinsohn-lgntdf` fetch their licence files; `bsb` has nowhere to fetch from; `sblgnt.com/license/`
is a web page.

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

**Step 2 — the gate on `resource add`.** L1 ruled (c), 2026-10-05.

- **The TTY check is explicit — `sys.stdin.isatty()` — not left to `click.confirm`.**
  ⚠️ **Corrected 2026-10-05.** This said `click.confirm` fails closed because it raises `Abort`
  when it cannot prompt. That holds only at end of input: with stdin piped, `yes | sp resource add
  X` answers it and registers. The ruling is fail-closed *when there is no TTY*, so the check is
  written, and `click.confirm` is only the prompt.
- **The prompt comes before the download**, not only before the write: declining after fetching
  hundreds of megabytes wastes them, and a declined prompt still leaves no registration.
- ~~**`click.confirm` is the mechanism.** It raises `Abort` when it cannot prompt, so **fail-closed
  is its default behaviour** rather than something to write.~~
  ⚠️ **Corrected 2026-09-28.** This read *"`click` is already the CLI library (`cli_utils.py:10`)"*,
  which is false and would mislead anyone building on it. Measured: `click` is imported by
  `cli_utils.py` and `utils/linter.py` and used **only for terminal output** (`click.echo`);
  **argument parsing is `argparse`** — `cli.py:74` builds the `ArgumentParser`, and
  `tools/replay.py` has its own. The conclusion stands, because `click` is a declared dependency
  and `confirm` is available whatever parses the arguments; what does not stand is any assumption
  that click's command, group or option machinery is in play.
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
