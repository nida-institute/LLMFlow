# HANDOFF — 2026-10-01

## ▶ NEXT ACTION

**This session's work is committed and not pushed.** `dev` is five commits ahead of `origin/dev`:
`93eee8b`, `637a8c9`, `ebfad50`, and the two this handoff lands with. Pushing is the Captain's act,
asked for by name each time (`commit-authority`; `~/.claude/CLAUDE.md` "Pushing is its own act").
Verify with `git status --short --branch` → `[ahead 5]`.

Then the release walkthrough: **`project/TODO.md` → 🚢 THE NEXT RELEASE**, item 1. He asked for
it one item at a time, in that order.

---

## Active threads

### 1. This session's pass — committed

**Goal.** Contradictions found at session start, then widened by the Captain: the positional
`output:` form and retired `returns:` in the docs; dotted `{{…}}` taught as working; stale
debug-dump filenames; the `<!-- -->` prompt header retired (**breaking**); lint expanding mixins
the way a run does; quickref wrong statements and a mixins section. Then, on *"fix the tests"*:
the rendered quickref regenerated from its template (`fc.shipped_content`, nothing else written),
the vendored `data/resources.json` re-synced verbatim from `awesome-biblical-data` (`2565f2d`,
clean, level with `origin/main`), `stage-commits` added to `EXPECTED_SKILLS`, numbered rule
citations qualified, and the dated docstring line removed. `CHANGELOG.md` Unreleased → Fixed and
Removed carries the behaviour changes.

**State.** Suite: **4 failed** (`hatch run pytest tests/ -q -m "not integration" -p no:randomly`),
both groups blocked on the Helm coordination design, not on code.
`docs/ai-context/sp/scripture-representations.md` was regenerated from its template on his
explicit yes (CLAUDE.md holds `sp/` under a hard prohibition) — one line, the stale
`llmflow-language.md` pointer:

- `test_helm_sync` ×3 — Helm parity, **out of this release** (TODO)
- `test_portable_skills::test_every_shipped_skill_is_classified` — `stage-commits` unclassified.
  Ruled *shared with Helm* (S1), and that cannot be delivered until the coordination design lands

**Verify.** The command above, and read the four names.

---

## In flight / not yet done

Branch `dev`, five commits ahead of `origin/dev` once this handoff lands — see NEXT ACTION.
Everything this session and the 2026-09-30 session changed is in those commits. What remains in
the tree is not ours:

| whose | paths |
|---|---|
| **the Captain's — do not stage** | `data/models.json`, `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md` |
| **untracked, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, seven `collab/discourse-flow/` notes, `collab/human-at-the-helm/` |
| **deliberately unstaged** | `scripts/representation-grid/{cells/,grid.json,grid.tsv}` — Q5 of `design-representation-workbench.md` |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

**Done elsewhere today, nothing outstanding:** `sil-translator-notes` was refreshed from the dev
engine with `~/.sp` redirected, and the Captain committed it — `c18f427`, level with
`origin/dev`. **#266** (`sp` cannot tell a user a newer build exists) was filed on his approval.

---

## Decisions

Today's rulings are in **`project/TODO.md` → 🚢 THE NEXT RELEASE**, each with its why. Two
corrections to the previous handoff, so they are not reopened:

- **Thread 1 of the 2026-09-30 handoff is withdrawn.** It said `prompts/commentary.gpt` "must be
  redone against Ears to Hear". The Captain, 2026-10-01: Ears to Hear is a client, and that work
  belongs in `ears-to-hear`. The A/B "Prepare the way" question and the two-headings question at
  `commentary.gpt:105,109` dissolve with it. The prompt stays as approved 2026-09-28.
- **The `\q` loss is not established as an engine defect.** This session called it one without
  evidence. What is known is in TODO under the release section.

**Still open, his, carried from 2026-09-29:** whether `2591d3e` and `7c4d133` — pushed with
messages naming files they did not contain, repaired by `c5e88fa` — want correcting. Nothing
rewrites history unasked.

---

## Do NOT

- **Do not run `sp init --update` here without `tools/update_ai_context.py` straight after**, and
  not at all without the Captain's word — it writes `~/.sp`. **Do not run `sp doctor`** (#210).
- **Do not carry a client's methodology into the engine.** Ears to Hear's is theirs. Do not name
  clients in anything that leaves this repository (`no-stakeholder-speculation`).
- **Do not take a written claim on trust.** Five of nine corrections this session were exactly
  that — `command-line.md`, a TODO line, CLAUDE.md's `apply_template`, and two inherited framings.
  Check the code or ask.
- **Do not fix the untriaged findings quietly.** TODO lists them; each wants an issue or a ruling.

## Key files & links

- `project/TODO.md` → **🚢 THE NEXT RELEASE** — the queue for this release, and today's rulings
- `CHANGELOG.md` → Unreleased → Fixed / Removed — what this session built
- `project/plans/plan-starter-example-commentary.md` §7 — release item 1
- Issues: **#244**, **#176**, **#252**, **#266** (filed today), **#263**/**#242** (built, close at merge)
