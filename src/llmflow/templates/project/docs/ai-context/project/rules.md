<!-- Created once by sp init. This file is yours; sp never overwrites it. -->
# This project's rules

Constraints that hold in **this** project and nowhere else. `sp` creates this file once and
never touches it again, so it is safe to write here.

## What belongs here

Things an AI session would otherwise get wrong, and that no general rule covers:

- domain constraints — *"never italicise anything that could contain Hebrew text"*
- data facts that change what is correct — *"this dataset's identifiers are not unique"*
- local conventions — naming, layout, what must never be regenerated
- prohibitions with a reason — what went wrong before, so it is not repeated

Write the reason, not only the rule. A constraint whose *why* is missing gets argued with, or
quietly dropped when it becomes inconvenient.

## What does not belong here

- **General practice** — how to run pipelines, how to write prompts, how to use git. That is in
  `sp/rules.md` and in the shipped disciplines, and a copy here would drift from them.
- **What is in flight** — that is `project/TODO.md`.
- **Description** — what this project *is* goes in `project/overview.md`.

## The rules

_(none yet — add them as they are learned)_
