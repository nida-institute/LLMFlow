# Design — keeping the shared files in step with Human at the Helm, one repository at a time

**Status:** decided (2026-10-14) — §6 answered A throughout. Not yet authorization to build:
that waits on the Captain's go.
**Issues:** #271.
**Author:** AI, from the Captain's answers to Helm's D1–D4 (2026-10-14) and measurements of
`tools/sync_helm.py`, `data/helm-sync.yaml`, `tests/test_helm_sync.py` and the Helm clone, taken
the same day.

---

## 1. Ruled

**By the Captain, 2026-10-14, for this release:** option **B** — build the mechanism on this side
— with **A**, Helm catching up, as the first case it handles. Answered as *"b"*, then *"both"*.

**His answers to the four decisions in Helm's `project/plans/design-coordinating-changes-with-sp.md`,
2026-10-14.** Recorded here because this design depends on them; Helm's `=>` slots are still
empty and are his, or a Helm session's, to fill.

- **D1 — C, split.** Helm keeps checksums of its own shared files; this repository's
  `data/helm-sync.yaml` keeps the rulings and the statuses. They hold different things, so neither
  can contradict the other.
- **D2 — C, both.** Helm's own check is a scheduled CI job **and** a session-start report from
  `/helm-check`.
- **D3 — a standing rule.** A session in one repository may write into the other's `collab/`
  directory, nowhere else, and never commits there.
- **D4 — nothing is sent.** He sets both sides; this document is the answer to Helm's six
  questions.

**Standing rulings this design must satisfy** — Helm's, 2026-09-23, and this repository's:

| Ruling | What it forces here |
|---|---|
| H3-B: this repository is upstream; the sides differ only where a ruling says so | The record stays here, and a difference needs a reason |
| `failure-lands-where-the-fix-belongs` | This suite stays green when Helm is behind |
| `helm-is-written-not-generated` | Nothing here writes Helm's text; Helm adopts by hand |
| `helm-checks-itself-without-sp` | Helm's check must work with no clone of this repository |
| `upstream-is-not-touched`, mirrored by D3 | Neither repository writes in the other outside `collab/` |

## 2. What exists, measured 2026-10-14

- **13 shared files.** `hatch run python tools/sync_helm.py`: 7 `same`, 2 `ruled`
  (`skills/commit-ready`, `skills/load-context`), **4 `DIVERGED`** — `disciplines/github-authority.md`,
  `disciplines/project-tracking.md`, `disciplines/workflow.md`, `skills/authorize`.
- **The suite is green only by exemption.** `EXEMPT_KEYS` (`tests/test_helm_sync.py:135`) lists
  six keys; `HELM_EXEMPT` (`tests/test_portable_skills.py:53`) is `xfail(strict=True)` on them and
  on `test_helm_ships_nothing_the_record_cannot_explain`.
- **The record has two statuses**, `identical` and `differs` (`test_every_divergence_carries_a_ruling`
  refuses any other), so "changed here, not yet adopted there" cannot be written down.
- **The comparison reads working trees.** `_sha256()` is `path.read_bytes()` on both sides, so two
  dirty trees can agree while neither has committed the text — Helm's design documents this
  happening on 2026-09-25.
- **`--apply` writes into Helm** (`shutil.copyfile` into the clone, `tools/sync_helm.py:192`). That is
  the second half of a twin edit, the shape behind all three incidents in Helm's design, and D3
  now forbids it.
- **Helm today:** branch `main`, 7 commits ahead of `origin/main`, uncommitted edits to seven
  `skills/*/SKILL.md` — including `authorize`, `commit-ready`, `load-context` — and untracked
  `skills/stage-commits/`. Its handoff is dated 2026-10-01. `--apply` run now would overwrite work
  that exists nowhere else.

## 3. The approach

### 3.1 A shared file changes in one repository per act

A change here is committed here. Helm learns of it from the record and adopts it in its own
commit, on its own schedule. Parity means *equal, or differing with a recorded reason and a
named owner of the next move* — not *always equal*.

### 3.2 The record gains `pending`

```yaml
- set: disciplines
  name: workflow.md
  sha256: 16fc48…          # this repository's committed copy, as today
  status: pending           # identical | differs | pending
  owner: helm               # whose move it is
  since: 2026-10-07         # when the change was committed here
  note: the workshop collab's rulings — the human commits, pushes and opens pull requests
```

`pending` requires `owner`, `since` and `note`. It is not a failure here: it is the normal state
between a change and its adoption. `tools/sync_helm.py --refresh-record` sets it whenever a shared
file's hash changes, so editing a shared file and refreshing the record is one act with no
second half.

### 3.3 This suite fails only on what this repository controls

**Kept, unchanged — they check this repository against its own record:**
`test_the_record_covers_exactly_the_shared_set`, `test_the_recorded_hash_matches_the_shipped_file`,
`test_every_divergence_carries_a_ruling` (extended: `pending` needs `owner`, `since`, `note`),
`test_a_forked_skill_is_absent_from_the_record`, `test_drift_patterns_must_be_byte_identical`
(extended: `pending` is allowed, `differs` still is not).

**Moved out of the suite into the report** — each checks Helm's state, which this repository
cannot fix: `test_the_shared_file_is_present_in_helm`,
`test_the_two_sides_agree_where_the_record_says_they_do`, `test_a_recorded_divergence_still_diverges`,
`test_a_divergent_copy_in_helm_still_carries_no_engine_vocabulary`,
`test_helm_ships_nothing_the_record_cannot_explain`. Their logic stays, as checks
`tools/sync_helm.py` runs and prints; Helm's own check (§4) is where they turn red.

`EXEMPT_KEYS` and `HELM_EXEMPT` are deleted. Nothing is exempt, because nothing about Helm can fail
here.

**One exception, found while building:** `tests/test_helm_manifest.py` checks Helm's
`manifest.yaml` and was not in the list above. It stays, skipping without a clone, until Helm's
CI (D2) can carry it — moving it now would leave the manifest watched by nothing.

**`stage-commits` is forked** — the Captain, 2026-10-14, answering what the unclassified skill
`test_every_shipped_skill_is_classified` found. Helm's copy is its own adaptation.

### 3.4 The comparison reads committed files

Both sides are hashed from `HEAD` — `git show HEAD:<path>` — not from disk. When either tree has
uncommitted changes on a shared path, the report says so by name and declines to call that file
`same`. The test half already reads committed state in effect: CI checks out a commit.

### 3.5 `--apply` is removed

Under D3 nothing here writes Helm's files. Its replacement is §6's D-B.

## 4. Helm's side — built in Helm, not here

Listed so the contract between the two halves is visible. None of it is this repository's work,
and no session working here writes it.

- **Its checksums (D1-C):** for each shared file, the upstream `sha256` it last adopted, or the
  word `ruled` where `data/helm-sync.yaml` permits a difference.
- **Its check (D2-C):** a scheduled job, and `/helm-check` at session start. Each compares Helm's
  adopted hashes with the `sha256` in this repository's published record, and is red where they
  differ and the entry is not `ruled`. That is how "Helm goes red when it is behind" works with no
  clone of this repository present.
- **The catch-up (A):** commit Helm's own uncommitted work first; then adopt the four `pending`
  files by hand, in Helm's words where Helm's differ; record the adopted hashes.
- **D3 in Helm's rules**, mirroring the one added here.

## 5. Build order, test first

1. **D3 as a project rule** in `docs/ai-context/project/rules.md`.
2. **Failing tests:** `pending` accepted with `owner`, `since` and `note`, refused without them;
   `--refresh-record` marks a changed file `pending`; the report reads `HEAD`, names a dirty path,
   and never writes into the Helm clone; no test in the suite reads the Helm clone.
3. **The record:** the four `DIVERGED` entries become `pending`, `owner: helm`, with their dates
   and notes. `commit-ready` and `load-context`, in `EXEMPT_KEYS` but already ruled, stay
   `differs`.
4. **The tool and the tests** to make step 2 pass; delete `EXEMPT_KEYS` and `HELM_EXEMPT`.
5. **The full suite, as CI runs it**, green with no `xfail` left from Helm.

## 6. Decisions for the Captain

Answer after each `=>`.

### D-A. Which branch carries the record Helm checks against?

Helm's job (§4) fetches `data/helm-sync.yaml` over the network.

- **A — `main`** (recommended): Helm adopts what has shipped. A change sits on `dev` for one
  release before Helm sees it as `pending`.
- **B — `dev`**: Helm sees a change the day it is committed, including ones that are later reworked
  before release.

=> A — the Captain, 2026-10-14, answering D-A to D-D together: *"A"*

### D-B. What replaces `--apply`?

- **A — a collab note** (recommended): `--note` writes, into Helm's `collab/scripture-pipelines/`,
  one note per `pending` file carrying this repository's text and the diff. D3 permits exactly
  that write, and Helm's session applies it.
- **B — nothing**: the report names what is pending, and a Helm session reads this repository's
  files itself.

=> A — the Captain, 2026-10-14, answering D-A to D-D together: *"A"*

### D-C. A shared file that Helm changed and this repository did not — whose move?

Today it fails here as `DIVERGED`. Under H3-B this repository is upstream, so Helm differing with
no ruling is Helm's divergence.

- **A — Helm's** (recommended): Helm's check is red until it reverts, or until a ruling here
  permits the difference. The report here names it; this suite stays green.
- **B — this repository's**: this suite fails until the change is adopted here or ruled — the
  polarity `failure-lands-where-the-fix-belongs` was ruled to end.

=> A — the Captain, 2026-10-14, answering D-A to D-D together: *"A"*

### D-D. Does a `pending` entry ever go red, if Helm never adopts it?

Helm's design calls this *"how a known backlog avoids becoming a red light nobody reads."*

- **A — red in Helm, from the day it is recorded** (recommended): that is what `pending` with
  `owner: helm` means, and Helm's check is where it shows.
- **B — red in Helm only after a set number of days**, so a change can sit for one working
  session without a red light.

=> A — the Captain, 2026-10-14, answering D-A to D-D together: *"A"*

## 7. Not in this design

- **Which unit is tracked** — a whole file or a single rule. Still whole files.
- **What else this repository has that Helm should consider** — the `upstream-is-scripture-pipelines`
  record of ideas, not files. Still unbuilt, and separate.
- **The prefix question**, Helm's issue #3.
