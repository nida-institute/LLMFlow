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

**List them. Do not characterise them.** One line each, in the order they happened, saying what
you claimed and what was true:

```
- asserted "35 commits" in a PR body from a stale local `main` — actual: 8
- put three unverified claims in issue #230, one of them false
- said the corrupt config broke the styling — it did not; nothing uses that class
- reported a directory as empty when `head -20` had truncated the listing
- said "38 curly quotes" when it was 162 — `grep -c` counts lines, not occurrences
```

The list is the whole point of this signal, and a summary destroys it. *"A few small
corrections"* is unfalsifiable and always sounds acceptable; five dated lines with the true
value beside each is checkable, and the human can see for themselves whether they cluster.

**How to know:** you will remember the recent ones, and recency is what matters. Where the
conversation is still in front of you, scan it rather than recalling — an assessment of your own
reliability is exactly the claim least worth taking on trust.

**What it implies:** everyone makes these, so a count alone means little. **Look at the
distribution.** Several in the last stretch, after a quiet earlier one, is degradation showing —
and it is the signal humans notice last, because each correction individually looks like
diligence rather than decline.

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

**People read the first line and the last line before they read anything else.** Whatever sits
there is what they will act on; the middle is what they consult if they doubt it. So put the
answer at both ends and the evidence between them — the opening states what is true, the closing
states what to do. Anything important that appears only in the middle has been published in the
least-read part of the page.

**Open with the verdict, in two words.** The human asked a yes/no question and is entitled to the
answer before the reasoning. Burying it under five paragraphs of evidence is its own kind of
overwhelm — they cannot act on an assessment they have to extract.

```
**Handoff: yes. Exit: yes.** — compacted once, eight corrections with four in the last
ninety minutes, eleven files uncommitted, and the next action needs your ruling.
```

`/handoff` and `/exit` are separate answers and often differ. **Handoff yes, exit no** is the
common case mid-session: capture the state, keep working. **Handoff no, exit no** means carry on
and ask again later. **Handoff no, exit yes** is rare and only right when the tree is clean and
the record already current.

Then, below it:

1. **The five observations** — enumerated, never summarised, with the corrections listed
   individually. This is so the human can disagree with your reasoning rather than only with
   your conclusion.
2. **What would be lost** if the session ended right now without a handoff. Name the files.
3. **The one thing to do first**, unless the answer was no to both.

**The detail earns its place — do not trim it to be brief.** The enumerated corrections and the
named files are what make the assessment checkable, and an assessment nobody can check is worth
nothing. What must be short is the *verdict*, at each end. A reader who wants only the answer
gets it in two words; a reader who wants to test it has everything they need in between.

**Close with a conclusion that rhymes with the opening** — the same judgement, arrived at rather
than announced, said as an instruction and carrying the reasons with it:

```
**Finish, then exit.** Commit what is in flight and stop; do not start the design discussion
here. Compaction, a correction rate that has doubled in the last hour, and a next action that
needs your ruling — none of which improve by carrying on.
```

Three things it must do, and the third is the one usually missed:

- **Say what to do**, concretely. The opening says what is true; the closing says what to do
  about it.
- **Name the specific thing not to start.** The temptation at the end of a long session is to
  begin one more piece of work, and the line that names which work to leave alone is the part
  most likely to be obeyed.
- **Name the categories that drove the verdict** — which two or three of the five actually
  decided it. A conclusion that repeats the recommendation without its reasons asks to be taken
  on trust, and by this point in the report the reader has the evidence in hand and can check
  whether those categories really carry the weight you are putting on them.

**The decision is the human's.** This skill produces an assessment, not a verdict — say what you
observe and what you would do, then let them choose. They can see things you cannot: what they
plan to do next, how much of your recent work they have actually checked, and whether they trust
this session's judgement any more.

---

## Related

- `/handoff` — write the durable record. Usually the next step when this says exit
- `/load-context` — the bookend, for the instance that follows
- `/stand-down` — a different problem: not a tired session, but one that has been steering
