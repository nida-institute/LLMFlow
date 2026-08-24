# Tests and Audits Answer Different Questions

## The Discipline

**Unit tests answer "does the code work?" Audit scripts answer "how good is this output?"**
They live in different places and must not be blurred.

- Tests under `tests/` exercise code paths against small synthetic fixtures.
- Audit scripts under `scripts/` load real generated artifacts, cross-check them against their
  sources, and report findings.

A test in `tests/` that loads a built artifact from `outputs/` is the anti-pattern.

## Why They Must Stay Apart

A generated artifact is not a stable thing to assert against:

- **It is large.** One book summary measured ~10MB. A suite that loads it is slow for every
  developer on every run.
- **It is tied to build state.** Regenerating with an improved prompt changes the artifact, so
  the test fails for a reason that is not a bug. The suite then trains people to ignore it.
- **It may not exist.** A fresh clone has no `outputs/`, so the test cannot run at all until
  someone spends money regenerating one.
- **It is derived.** A pipeline, its prompts and its schema can all change; the artifact is
  the consequence, never the specification. Asserting against it inverts which one is
  authoritative.

Audit scripts pay none of those costs, because reporting on a real artifact is exactly their
job. They can grow freely, they can be slow, and they can be run when there is something to
look at.

## How to Apply

- **A test in `tests/`** uses fixtures under `tests/fixtures/`. It does not read `outputs/`.
- **"Is the built artifact correct?"** is a script under `scripts/`, not a test.
- **A hybrid** — "load the real book and assert X" sitting in `tests/` — is the case this
  discipline exists to catch. Move it to a script.

The question to ask of any assertion: *would regenerating the output with a better prompt make
this fail?* If yes, it is an audit, wherever it currently lives.

## Related

- The rule that generated output is a draft until a human has reviewed it.
- The rule that stale generated output is a defect rather than an asset — the same premise seen
  from the other side: output is derived, so it is neither precious nor authoritative.

**Source:** recovered 2026-08-24 from a deleted `~/.claude` memory file written in
`nida-institute/ears-to-hear`, during the audit of the memory store. It had never been visible
in any repository.
