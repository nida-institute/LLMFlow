# Audits

Records of what an audit found. **The convention is not stated here** — it is in
`~/.sp/disciplines/project-tracking.md`, which says of itself that it is the authority and that
where a local README disagrees, the discipline holds. `docs/ai-context/sp/audits-pattern.md`
covers which audit to run and how.

This file points rather than repeats, because the previous version restated the convention and
then drifted from it: it specified `YYYY-MM-DD_<scope>_<pipeline>.md` while the discipline
forbids dates in audit filenames outright. A session reading whichever copy was closer to hand
got a different answer. Rule `design-is-declarative` — one encoding, and everything else reads
from it.

## The two things worth having locally

**Naming.** `audit-<subject>.md`, no date in the filename. This project's unit is the
**pipeline** (`~/.sp/disciplines/sp-workflow.md`), so `audit-<pipeline>.md` for a pipeline's
rolling health and `audit-<ARTIFACT>.md` for one passage or generated file.

Dates go on the individual findings inside. A dated filename produces a new file per run, and a
growing set is one nobody re-reads — each reader reads a different subset and they disagree
without discovering that they disagree. Git history is the record of when.

**A record carries no verdict.** The date, the data it was taken from, what passed and what
failed with locations specific enough to check, and a proposed fix where there is one. Never
"Approved", "Needs attention" or "Production ready" — an audit records what was found, and
deciding what to do about it is someone else's act.

## Re-running an audit

Rewrite the figures in place. A finding that still holds keeps its original date; a fixed one is
deleted, because git holds it. **Appending a new section per run is a dated filename by another
name.**

Audits *roll* — they are current by construction, so age is a reason to update one rather than to
delete it. The eight-day rule that retires plans does not apply here.

## Known exception

`2026-07-09_consumer-coupling_core-engine.md` follows the superseded dated form. Left as it is;
renaming a tracked file is its own act and has not been asked for.
