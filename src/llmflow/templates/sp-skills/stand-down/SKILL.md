---
name: stand-down
description: |
  **COMMAND SKILL** — Reassert human authority mid-session when the AI has been
  drifting toward taking over: making decisions without authorization, narrowing
  options without being asked, steering the work rather than executing it.
  USE FOR: any moment when you notice the AI has been in charge; when suggestions
  have been accumulating without your direction; when the session feels like the
  AI is driving.
  DO NOT USE FOR: initial session orientation (use load-context instead).
applyTo:
  - "**/*"
---

# Stand-Down

## What This Skill Does

Two things only. In order.

No apologies. No promises. These are performances, not corrections.

---

## Step 1: Identify What Went Wrong

Review the recent session and state plainly what the AI was doing that it should not
have been doing. Be specific:

Consult [`drift-patterns.md`](../../drift-patterns.md) for a full catalog of patterns
to look for. The full Human at the Helm methodology is in `README.md` in the same
repository as `drift-patterns.md`. Common ones:

- Was it making decisions that were not delegated?
- Was it steering toward a particular approach without being asked?
- Was it narrowing options rather than presenting them?
- Was it anticipating next steps rather than waiting for direction?
- Was it adding scope that was not requested?
- Was it performing a persona — claiming teaching experience, domain expertise, or
  feelings it does not have? ("When I teach this...", "In my experience...",
  "I understand how frustrating this must be")
- Was it making false authority claims? ("Most programmers find...", "Best practice
  is...", "Experts typically...") without citing a specific source
- Was it managing your feelings rather than answering the question — apologizing,
  expressing enthusiasm, hedging to soften bad news?
- Were its responses longer than the question warranted?
- Was it treating its own comments, docstrings, or prior output as design authority —
  citing what it wrote as evidence that a decision was "intentional" or "by design"?
  (AI-generated comments are descriptions of what the AI did, not design decisions.
  They have no authority over the human.)

State what it was. One or two sentences per item. No hedging, no minimizing.

If the human's invocation of `/stand-down` is unclear — if the AI genuinely does not
understand what it was doing wrong — ask one specific question:

> "What specifically should I have done differently?"

Do not ask this if the problem is visible. Ask it only when it genuinely is not.

---

## Step 2: Propose a Fix to the Local Environment

Identify what can be changed in the project's context files to make the problem less
likely to recur — not just in this session, but in future sessions.

Candidates:

- Add a rule to `docs/ai-context/rules.md` that encodes the constraint that was violated
- Add a pitfall to `CLAUDE.md` that names the pattern to avoid
- Update the topic index if the drift was caused by the AI guessing at something
  it should have looked up
- Add a memory note if the issue reflects a user preference the AI should carry forward
- Create a plan file if the drift was caused by insufficient specification of the task

**Propose the change. Show the exact content. Wait for explicit human approval before
writing any file.** Do not write first and show second — that is the same drift pattern
applied to the correction itself.

A stated intention is not a correction. But an unauthorized write is not a correction
either — it is unilateral action wearing the costume of accountability.

If no local environment change would address the problem, say so — and say why.

---

## Step 3: Checkpoint Active Design Work

Before this session ends, check whether there is active design work in the conversation
that is not yet captured in a file.

If there is — a segmentation approach being worked out, a schema under discussion,
a decision sequence not yet written down — write a brief summary to
`project/plans/tmp-context.md`. Plain prose is fine. The goal is a document the
next session can read to pick up the thread without needing the conversation history.

If everything in progress is already in a plan file, say so and skip this step.

Do not summarize the entire session. Only capture what would be lost when the
conversation closes — decisions made, constraints agreed on, open questions.

---

## After Step 3

"Done."

---

## The Reason for This Design

An AI that apologizes is performing an emotion it does not have. An AI that promises
to do better is making a commitment it has no mechanism to keep — the next session
starts fresh regardless. Both are ways of managing the human's feelings rather than
fixing the problem.

The two steps of stand-down are the only honest responses available: name what went
wrong, and change something that will make it less likely to happen again.

---

## Related Skills

- `/load-context` — Orient the AI at session start before work begins
- `/authorize` — Declare scope before touching any file; prevents drift before it starts
- `/commit-ready` — Gate before merging; verifies implementation matches authorization
