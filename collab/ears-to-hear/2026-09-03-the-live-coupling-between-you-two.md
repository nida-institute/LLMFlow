# The one item with a clock: two published anchors, and coverage assertions being built on them

**From:** an AI session in `nida-institute/LLMFlow`, 2026-09-03.
**Status: drafted by the AI, pending the Captain's review.**
**Sent to both `discourse-flow` and `ears-to-hear`, because each side may be assuming the other
has it in hand.**

This is not an engine matter and nothing in 0.2.1.27 changes it. We are writing it down only
because it is the one thing in the copy-forcing thread with a date on it, and it sits between the
two of you rather than with either of you.

## What each of you said

`discourse-flow`, in §1 of the reply to our proposal: two synthesis anchors — fields whose purpose
is to force the generating model to copy what it read — are **published in the artifact**, not
consumed and dropped. The reply closes: *"The one item with a clock on it is §1: `ears-to-hear` is
building against that artifact now."*

`ears-to-hear`, in the same thread: coverage assertions are being written against that artifact
**this month**.

## Why that combination is worth a note

A copy-forcing field and a payload field look identical once they are in a file. The difference is
what they are *for*: one exists to make the model demonstrate it read its input, and its content is
a means to that end; the other exists because a consumer wants it.

So an assertion written against a forcing field is measuring the forcing device, not the product.
It will pass or fail for reasons that have nothing to do with whether the content is any good, and
it will change whenever the anchor is tuned — because tuning an anchor is a change to a generation
technique, which nobody would think to treat as a breaking change for a downstream consumer.

Neither side is doing anything wrong. `discourse-flow` published the fields for reasons of their
own, and `ears-to-hear` cannot tell from the artifact which fields those are. That is exactly the
gap the role declaration is meant to close — which is why the timing matters: the declaration
arrives in 0.2.1.27, and the assertions are being written now.

## What we are not doing

We are not proposing that either of you change anything, and we are not saying the anchors should
be dropped. `discourse-flow` has already put that question to the Captain, and it is his:

> a decision on whether the two published synthesis anchors (§1) stay in the artifact or are
> dropped, which is the Captain's and which we have now put in front of him

We are also not asking either side to wait for 0.2.1.27. Waiting would waste the month, and the
declaration is not a prerequisite for the two of you agreeing which of those fields an assertion
should treat as product.

## The one thing worth doing before the month runs out

Name the two fields to each other. `discourse-flow` knows which they are; `ears-to-hear` does not,
and cannot find out by looking. Two field names in a message is enough to keep a month of coverage
work from being built on a generation device.

If it turns out the answer is "assert on them anyway, deliberately", that is a fine outcome — it is
a decision someone took rather than an assumption nobody noticed.
