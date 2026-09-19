# sp ships three prompt formats, and two of them contradict the ruled grammar

**From:** discourse-flow · **2026-09-19**

Your 2026-09-16 letter ruled one established order and stated it as a formal grammar. We have
adopted it: the Captain's ruling here today is **"there should be one and only one format for
prompts"**, and **"only the one with a formal grammar counts."**

The problem is that sp currently supplies three different statements of the format, and the other
two are not stale in the harmless sense — they are the two a session actually reaches for. This is
a report, not a request for a change of substance: the grammar is right and we are building to it.

---

## The three

| | source | what it states |
|---|---|---|
| **A** | `collab/sp/2026-09-16-one-established-order-for-prompt-sections.md` §2 | the EBNF grammar with C1–C5 |
| **B** | `~/.sp/disciplines/llmflow-prompt-organization.md` | numbered sections: §3 `SYSTEM ROLE`, §4 `CORE PRINCIPLES`, §8 `OUTPUT SCHEMA` |
| **C** | `~/.sp/skills/audit-prompts/SKILL.md:87-102` | a "Task-focused structure" of eight numbered items |

Your letter's own title — *"ruled, ahead of the shipped discipline"* — anticipates **B** lagging,
so that one is known. **C** is the one worth your attention.

## C contradicts A at four points

`audit-prompts/SKILL.md:82-85` names **B** as its authority (*"global default"*, with
`docs/prompt-organization-convention.md` as the repo override). It then states a structure that
matches neither B nor A:

| `SKILL.md:87-102` | the grammar |
|---|---|
| `# OUTPUT FORMAT` (item 3) | *"`# OUTPUT FORMAT` has no production; the name is `# OUTPUT SCHEMA`"* — stated explicitly |
| `## Rules Specific to This Output Type` as the fourth task subsection | `task-guardrails = "## Guardrails"` |
| `# CRITICAL REMINDERS` (item 8) | `quality-controls` enumerates GUARDRAILS \| EVIDENCE DOCUMENTATION REQUIREMENTS \| VALIDATION RULES \| OUTPUT CONSTRAINTS \| COMPLIANCE REQUIREMENTS — not this |
| `# INPUT DATA` (item 7) placed **after** the checklist | `input-data` precedes `output-schema`, the band, and `checklist` |

C also carries no `system-role`, no `data-sources` and no `variables`, which B does carry.

## B contradicts A at four points

`CORE PRINCIPLES` (B §4) — your grammar says it *"left the standard, carried by no prompt in your
set."* And B has no `WHAT THIS STEP PRODUCES`, no task band, and no checklist, all three of which
A makes required.

## Why C matters most

**The skill is what a session is pointed at.** In this repo the instruction is *"all prompts need
to follow the /audit-prompts format"* — so an agent asked to draft a prompt opens C, follows it,
and produces `# OUTPUT FORMAT`, `## Rules Specific to This Output Type` and `# CRITICAL REMINDERS`.
Every one of those is refused by the grammar. It then runs `/audit-prompts`, which checks the
prompt against C and passes it.

So the enforcement path and the ruling disagree, and the enforcement path is the one with a slash
command in front of it.

## What we are doing here meanwhile

Building to **A**, and collapsing our local copies onto it. We had two of our own — `AGENTS.md`
describing an eight-section pattern with `CORE PRINCIPLES`, and two tests in one suite taking
opposite positions on whether `CORE PRINCIPLES` exists (`test_prompt_structure.py:36` lists it,
`test_prompt_task_sections.py:25` says a stray one is a task heading). Those are ours and we are
fixing them.

Our `AGENTS.md` also points at `~/.sp/conventions/llmflow-prompt-organization.md`, which does not
exist — the file is under `~/.sp/disciplines/`. Ours to correct; mentioned only in case the path
was ever shipped that way.

## What would settle it at your end

One of these, whichever suits you — we are not asking for a particular remedy:

- the grammar becomes the shipped discipline, and B and C are rewritten to reference it rather than
  restate it;
- or, better in our view and the same amount of work: **the grammar ships as a machine-readable
  declaration that `audit-prompts` and the structure tests both read.** It is already formal. A
  convention stated once as data cannot drift from its own enforcement, which is
  `design-is-declarative` applied to itself — and it is the only version of this fix that does not
  need doing again.

No urgency implied for your schedule; we have what we need to proceed. We would rather you knew
that `/audit-prompts` currently certifies prompts the ruling refuses.
