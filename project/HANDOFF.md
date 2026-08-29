# HANDOFF — 2026-08-29

Supersedes 2026-08-28. **This repository is clean, committed and pushed.** HEAD is **`db3c4d7`**,
`## dev...origin/dev` with nothing else. Version is **0.2.1.25**, and the CHANGELOG has its
dated section.

---

## ▶ NEXT ACTION — open the release PR

Everything the release needs is on `dev`. The remaining steps are `project/RELEASE_CHECKLIST.md`
§6–§9, and **each is the Captain's**:

1. `dev` → `main` pull request. **It must be a merge commit**, not a squash.
2. Tag **the merge commit** — delete any stale tag first; the checklist's §7 records why.
3. Watch **every** `release.yml` job, not just the build. §8 is marked MANDATORY VERIFICATION.

**Two checks worth doing first, neither blocking, neither yet done:**

- **The store migration has never run on a real machine.** `sp doctor` moves `~/.sp/editions/`
  to `~/.sp/registrations/` and `~/.sp/data/` to `~/sp/resources/`. Tested only against pytest
  temp directories. This machine has `~/.sp/editions` with three registrations and no
  `~/.sp/data`. Run it in a **consumer** repo — not this one, which #210 still forbids.
- **`sp resource add` has never fetched anything for real.** Every download test mocks the
  response. One `sp resource add SBLGNT` (~150MB) would exercise fetch, unpack, version-record
  and register end to end before Paul does.

---

## What landed today

Six commits, `a49fd1d` through `db3c4d7`:

| | |
|---|---|
| `a49fd1d` | the shipped document says which `include:` families are built |
| `e88f751` | reference resolution — extent from a named versification, one lean parser — #218 |
| `e8369a8` | the hook that makes file reads go through `Read` |
| `9c629ce` | `sp resource` — a catalog says how to open a text, the store says where it is — #217 |
| `06f0767` | one declaration of book names, so `Mark 1:1-8` and `MRK 1:1-8` both work |
| `860e627` | `data/book-names.json` shipped nowhere, and nothing could tell |
| `2794d6f` | the discipline says which tools a session actually has |
| `db3c4d7` | 0.2.1.25, and a guard so the changelog cannot be forgotten |

**Test state: 3685 passed, 24 skipped.** The only intermittent failure is
`test_mcp.py::test_connection_to_biblica_server`, an `httpx.ReadTimeout` against a live server.
It passes on some runs. Do not "fix" it by changing the test. Verify with
`hatch run pytest tests/ -q --ignore=tests/integration`.

## Decisions settled today — do not reopen

**`sp resource` is the whole surface, and `sp download-data` is gone.** `list`, `add` (fetching
by default, `--no-download` to skip, `--path` for a Paratext project or a text of your own),
`download` for a resource no reader can open. The old command carried a four-entry catalog beside
the public one; its `berean-usx` entry pointed at a 404.

**The catalog is `resources.json` in `awesome-biblical-data`, vendored into the wheel.** It
carries **shape, never state**: which file holds a text, which backend reads it, its versification
and canon. Anything that changes as a maintainer works stays in that resource's own repository —
a copy here would eventually call a reviewed file unreviewed, authoritatively. Entries gained
`provides`; a `validate_resources.py` and a pre-commit hook now check the file, which found a
duplicate `scripture-burrito` nobody had noticed.

**Corpora are visible, registrations are not.** `~/sp/resources/<owner>/<repo>/` for the texts —
configuration belongs in a dotfile and a library of several hundred megabytes does not —
`~/.sp/registrations/` for the small files saying what this machine may read. Directories are
named for the source (`Clear-Bible/macula-greek`, or `https-<host>/<file>`), never a catalog id.

**Every fetch records what it fetched** — source, archive SHA-256, size, timestamp — because a
directory name says which resource it holds and nothing about which copy.

**`known_editions` is empty and should stay so.** WLC, SBLGNT and BSB answer from the catalog with
their evidence. Add an entry there only for something the catalog cannot describe.

**BSB comes from the official USFM release**, not `usfm-bible/examples.bsb`, which omits `\id` in
Ecclesiastes and silently loses the book. The official release carries `\mt1`/`\mt2`, `\s1`, `\p`,
`\q1` and full footnotes — what `format: print` needs.

**`format: usj` emits `sid` and no `eid`.** USX pairs them; USJ does not, and `usfmtc` discards
ends in its USX-to-USJ conversion. discourse-flow accepted this after seeing the evidence.

**Both ways of naming a book work**, case-insensitively, from `data/book-names.json`. A reference
is tokenized, not pattern-matched. A range may cross a chapter and not a book. Testament and
original language are declared per book, not derived from a number threshold.

## Do NOT / landmines

- **Do not commit, push, or merge.** Run the gates, write the message, hand over the command.
- **Do not run `sp doctor` in this repository** — #210, still open.
- **Do not modify `docs/ai-context/`, `CLAUDE.md`, or project memory** without explicit approval.
  The Captain authorised specific edits to `data-shapes.md`, `data-sources.md` and `CLAUDE.md`
  today; those approvals were per-act and do not carry forward.
- **Do not write after a `=>`.** Those are the Captain's.
- **`data/book-names.json` and `data/resources.json` must stay in `pyproject.toml`'s
  force-include and in *both* Nuitka commands.** `book-names.json` reached a release candidate
  bundled nowhere; two guards now catch it.
- **`Grep` and `Glob` do not exist in this installation.** A `general-purpose` subagent declared
  `Tools: *` also lacks them, so it is not a session-launch quirk. Search with `grep` via bash,
  one command at a time — a chained command matches no permission rule and costs an approval.

## Open, with the reasoning recorded

| | |
|---|---|
| **#223** | `type: scripture` records nothing about how it resolved a reference. Filed from discourse-flow's argument; explicitly *not* a change to `parse_bible_reference`, whose nulls are closed |
| **#201** | datasets record no version — half-addressed: fetches now record one, but the catalog is still not validated against what is installed |
| **#210, #211** | `overview.md` is two documents sharing one path; 21 shipped documents to `source: template`. #211 looks substantially done and wants re-scoping or closing |
| **#215** | `sp init`'s write paths. The registry warning naming a retired filename still fires on every init |
| **CHANGELOG history** | `0.1.5.04` carries two headings from a mis-merge. Left alone deliberately — editing it would rewrite the record to satisfy a new test |

## Other repositories

| where | what |
|---|---|
| `awesome-biblical-data` | committed. Now carries `provides` blocks, the validator and the pre-commit hook. We are taking over its maintenance |
| `human-at-the-helm` | committed — `disciplines/workflow.md`, synced. It must move with this repository's copy or `test_helm_sync` goes red |
| `discourse-flow` | our reply committed. **Their** `2026-08-29-reference-provenance.md` and a modified `2026-08-27-discourse-family-is-built.md` are still uncommitted there, and are theirs |
| `~/.claude` | `settings.json` carries the hook fix. The Captain's store, `cgit`. **Report, never commit** |

## Key files

| | |
|---|---|
| `src/llmflow/resources.py` | the catalog reader, path resolution, registration, status |
| `src/llmflow/books.py` | which book a reference names |
| `data/book-names.json`, `data/resources.json` | the two declarations added today |
| `project/plans/design-edition-provisioning.md` | #217's decisions, D1–D6 with the Captain's `=>` answers |
| `project/RELEASE_CHECKLIST.md` | §6–§9 are the remaining steps |
