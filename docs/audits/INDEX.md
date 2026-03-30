# Audit Dispatch

**What this file does:** Maps artifact types to their audit checklist files. When you need to audit something, find its row below, use the trigger phrase listed, and the AI assistant will open the corresponding procedure file before evaluating your artifact.

## Dispatch Table

| What you have | Say | Open |
|---|---|---|
| Leader's guide `.md` | "audit this per the checklist" | `audit-leadersguide.md` |
| Verse atlas `.json` | "audit the verse atlas" | `audit-verse-atlas.md` |
| Book summary `.md` | "audit the book summary" | `audit-book-summary.md` |
| Passage output `.md` | "audit this passage" | `audit-passage.md` |

## Adding New Audit Procedures

1. Create a new checklist file in this directory (e.g. `audit-my-artifact.md`)
2. Keep it 20–60 lines max
3. Use `- [ ]` checkbox format only — no explanatory prose
4. Put STOP conditions in bold at the top
5. Add a row to the table above with the trigger phrase

## Audit Records

Audit findings go in `project/audits/`, not here. One file per audit run:
- `project/audits/audit-MRK-6-14-29.md`
- `project/audits/audit-LUK-1-full-pipeline.md`

This directory (`docs/audits/`) contains only **procedures** (version-controlled, reusable). Records (`project/audits/`) are **findings** (per-run, not committed).
