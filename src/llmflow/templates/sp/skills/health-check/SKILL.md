---
name: health-check
description: |
  **SESSION SKILL** — Assess whether this session is still working well, and whether it is
  time to hand off and exit. About the *session* — not the machine, and not whether the
  tooling is installed correctly.
  USE FOR: when the human asks how the session is holding up; when you notice yourself
  re-deriving something; after a long stretch of work; before starting something large.
  DO NOT USE FOR: writing the handoff itself (use handoff); orienting at session start
  (use load-context).
---

# Health Check

## Purpose

Answer one question, with evidence: **is what this session knows still recoverable from what is
written down?**

That is the real question behind "should we exit?". Not *am I running out of room* — a context
mostly full of settled, committed work is fine, and one barely used but holding a day of
unrecorded reasoning is not.

The reframe matters because it makes the answer actionable. If the session's knowledge is
recoverable, exiting costs nothing and a fresh instance is strictly better — it reasons from the
full record rather than from a compressed one. If it is not recoverable, **the gap is the work to
do before exiting**, which makes "should I exit?" and "what next?" the same question.

---

## Report these five, each with its evidence

Do not summarise. Give the observation, then what it implies.

### 1. Has this session been compacted?

The strongest single signal, and the only binary one. If earlier exchanges have been replaced by
a summary, you are working from your own notes rather than the original reasoning — and you
cannot tell what the summary dropped.

**How to know:** the transcript says so. A summary of prior conversation at the start, or a note
that context was condensed.

**What it implies:** once is a warning; twice means a fresh instance would almost certainly do
better work than you.

### 2. Are you re-deriving?

Looking something up you already established is the behavioural tell of context loss, and it is
visible as it happens.

**How to know:** you re-read a file to answer a question you answered earlier; you re-run a
command whose output you already had; you restate a decision as though it were open.

**What it implies:** each instance is cheap, the pattern is not. Two or three in a stretch means
the working set no longer fits.

### 3. What is the correction rate, and is it rising?

Count the times in this session you stated something and then had to correct it — a wrong file
count, an unverified claim, a misdiagnosis.

**How to know:** you will remember the recent ones. That is the point — recency is what matters.

**What it implies:** everyone makes these. **A rising density is degradation showing**, and it is
the signal humans notice last, because each correction individually looks like diligence.

### 4. How much is uncommitted?

**How to know:** `git status --short --branch`, in every repository this session touched. Name the
files.

**What it implies:** this is the *cost* side. It is what would be lost, and it is what makes a
handoff urgent rather than optional. A clean tree means exiting is nearly free.

### 5. Is the next action blocked on the human?

**How to know:** does it need a ruling, an approval, a credential, or an answer only they have?

**What it implies:** if yes, continuing spends context producing nothing. Exit and let them
resume when they have decided.

---

## Do not report these

They look like metrics and carry no information:

- **Token counts.** Often not reliably visible, and the number does not answer the question —
  what is *in* the context matters more than how much.
- **Elapsed time or message count.** Proxies for nothing. A long session can be in excellent
  shape and a short one can be lost.
- **"It feels like a lot."** Unfalsifiable, and a model asked whether it is tired will say yes.

If you cannot observe something, say you cannot observe it. **A confident guess about your own
state is worse than "I don't know"** — it is the one claim nobody else can check.

---

## When *not* to exit, whatever the signals say

Finish first, then ask again. A handoff written mid-transaction describes a mess:

- an edit is half-applied, or a change is partly propagated across files
- the suite is red for a reason you introduced
- something you started is still running — a build, a release, a long job
- you are one small step from a natural boundary: a release cut, a decision recorded, a test
  turning green

The boundary matters more than the timing. **Exiting one step before a natural seam costs the
next instance more than continuing costs you.**

---

## Then answer, in this shape

1. **A recommendation**, in one line: continue, finish-then-exit, or exit now.
2. **The evidence**, as the five observations above — so the human can disagree with your
   reasoning rather than only with your conclusion.
3. **What would be lost** if the session ended right now without a handoff.
4. **The one thing to do first**, if the recommendation is anything but "continue".

**The decision is the human's.** This skill produces an assessment, not a verdict — say what you
observe and what you would do, then let them choose. They can see things you cannot: what they
plan to do next, how much of your recent work they have actually checked, and whether they trust
this session's judgement any more.

---

## Related

- `/handoff` — write the durable record. Usually the next step when this says exit
- `/load-context` — the bookend, for the instance that follows
- `/stand-down` — a different problem: not a tired session, but one that has been steering
