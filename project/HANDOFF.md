# HANDOFF — 2026-09-28

## ▶ NEXT ACTION

**Two commits, in this order. Both message files are written.**

```sh
git add project/plans/design-named-step-outputs.md project/plans/design-sp-help.md
git commit -F tmp/commit-1.txt

git add project/TODO.md project/plans/plan-terms-on-download-and-register.md project/HANDOFF.md
git commit -F tmp/commit-2.txt
```

Then delete `tmp/commit-1.txt` and `tmp/commit-2.txt` **by name** — `tmp/` holds other sessions'
unbacked drafts and is git-ignored, so a wildcard sweep is unrecoverable.

**`dev` is one commit ahead of `origin/dev`** at `c90f7a1`, unpushed. A push is the Captain's act.

**Then: implement → #263**, which is what the starter example now waits on. **One small decision
comes first** — see *Open, and blocking*.

**`/stage-commits` still cannot be invoked.** The template and `~/.sp/skills/stage-commits/` exist;
`.claude/skills/stage-commits/` does not, here or in `~/.claude/`. Follow its template by hand, or
install it with `hatch run sp init --update`. **Not `sp doctor`** (#210). `sp` is not on the bare
PATH — only inside the hatch environment.

`project/TODO.md` holds the queue and its order. Do not read the queue out of this file.

---

## In flight, and whose

Branch `dev`, **one ahead of `origin/dev`** at `c90f7a1`.

| | |
|---|---|
| **this session's, uncommitted** | `project/TODO.md`; untracked `project/plans/design-named-step-outputs.md` and `project/plans/design-sp-help.md`; `project/plans/plan-terms-on-download-and-register.md`; two of the eighteen changed lines in `docs/ai-context/project/data-sources.md` |
| **the Captain's, uncommitted — do not sweep in** | `data/models.json`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md`, `project/plans/README.md`, the other sixteen lines of `data-sources.md`, and two tracked deletions under `tmp/` |
| **unread, arrived today** | `collab/discourse-flow/2026-09-28-the-defect-log-needs-an-info-severity-and-lint-refuses-a-safe-builtin.md` — **inbound, untracked, nobody has read it** |
| **untracked, older** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, five earlier `collab/discourse-flow/` notes, `collab/human-at-the-helm/` |

**`docs/ai-context/project/data-sources.md` cannot be split by path** — the Captain's paragraph and
this session's two-line product-name fix are one hunk. It is his to commit or to authorise whole.

**Do not `git add -A`** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.

## Known-failing — 6

**Verify:** `hatch run pytest tests/ -q -m "not integration" -p no:randomly`
→ **5894 passed, 24 skipped, 6 failed** (2026-09-28, 130s).

`test_global_disciplines`, `test_plan_docs_index`, `test_portable_skills`,
`test_prompt_structure_single_source`, `test_resource_provisioning`, `test_template_layout`.
Three clear with `hatch run sp init --update`. **What each one names is in `project/TODO.md`**,
first section under 🔥 Active.

**Do not run two pytest runs at once** — they share `tmp/pytest/` and the second dies with
`INTERNALERROR … FileNotFoundError`.

---

## Decisions

### Settled 2026-09-28 — do not reopen

- **A step's outputs are named, not positional**, with an optional rename:
  `[text_bsb=text, reference]`. Naming a member requests it; a caller may request a subset. That
  one ruling dissolved the mapping-direction question and removed the need for a second key.
  → #263, `project/plans/design-named-step-outputs.md`.
- **The language will parse expressions with precedence.** This answers #241's open question —
  operations are **expressions**, not step methods — and reclassifies #239 from "a kludge, off the
  critical path" to a **precondition**.
- **The starter example waits for #263**, so `📖 FIRST — finish the examples` is blocked. Group C
  (removing the `hello.*` starters) is *not* blocked by it.
- **`sp help resources` / `sp help services`** is the concrete first piece of discoverability
  → #264, `project/plans/design-sp-help.md`.

### Open, and blocking

1. **The residual of D2 in `design-named-step-outputs.md`** — what a **bare** `output: name` binds:
   the primary member, or the whole object. The list form is ruled; this decides whether every
   existing pipeline keeps working unchanged, so it is needed **before** implementation, not after.
2. **Three more slots in that design** — D1′ (how a caller learns a step's members), D3 (are member
   *shapes* in scope, or only *names*), and the identifier question below.
3. **Four slots in `design-sp-help.md`**, D1 first: is a "service" a step type?
4. **`text-bsb` cannot be written as ruled.** Hyphenated names do not resolve and fail silently —
   `resolve("${text-bsb}", …)` returns the literal, because the identifier class at
   `utils/context.py:148` is `[a-zA-Z0-9_]+`. Either the example becomes `text_bsb`, or the
   resolver learns hyphens, which is #239's territory.
5. **The expressions ruling is recorded nowhere binding.** It belongs in #241 and in
   `design-operations-in-the-pipeline-language.md`, whose `=>` slots are the Captain's alone.

---

## Do NOT

- **Do not implement #263 before the D2 residual is answered.** It fixes the backwards-compatibility
  contract, and building first means choosing it by accident.
- **Do not write the starter example** (group B). Its `output:` line is the thing under design, and
  it ships as the pattern other projects copy.
- **Do not do the three open A″ documentation boxes.** They document the *positional* form that
  #263 replaces. Note that `c90f7a1` already shipped that documentation into
  `docs/llmflow-language.md` and the quick-reference template — **shipped documentation currently
  teaches a form under replacement**, which should be corrected before a release, not before a commit.
- **Do not regenerate `project/plans/README.md`.** Generated, stale, and carrying the Captain's
  uncommitted hand edit — and it would also index two plan documents added today.
- **Do not run `sp doctor`** (#210). **Do not** commit, push or merge: `commit-authority`.
- **Do not re-audit what `TODO.md` records for 2026-09-27/28.** Every claim there was checked
  against the tree, the suite or `gh issue list`, not against another document.

## Key files & links

- `project/TODO.md` — the queue. 🧭 *The language's shape* is the new section and sits ahead of the
  examples.
- `project/plans/design-named-step-outputs.md` → #263 · `project/plans/design-sp-help.md` → #264.
- `project/open-decisions.md` — S1 ruled and not yet retired to `CHANGELOG.md`; L1–L3 open.
- Issues opened 2026-09-28: **#263**, **#264**. Comment posted on **#239** carrying the parser
  comparison and its measurements.
