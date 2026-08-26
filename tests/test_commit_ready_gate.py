"""The local commit gate must cover every suite CI runs (#206).

`gui/frontend/` is a TypeScript project with seven Vitest test files, and CI runs them —
`.github/workflows/test.yml` does `npm test -- --run` and `npx tsc --noEmit`. The
`commit-ready` skill, which calls itself *"the full LLMFlow definition of done"*, named
only `hatch run pytest`.

So a contributor who edited `gui/frontend/src/App.tsx`, followed the skill to the letter,
and saw 2677 Python tests pass had run none of the TypeScript tests. CI caught it
afterwards — but the skill exists to be the check *before* the push.

Same shape as several defects found the same day: **a check applied to one of two paths,
reading as complete because the path it covers is green.** Compare LLMFlow#198, where the
unresolved-`${var}` guard existed on the lint and rewind paths but not on the one that
writes.

**These tests derive the requirement from `test.yml` rather than restating it.** A second
hand-written list of commands is what let the gate and CI drift apart in the first place;
if CI gains a step, this fails until the skill gains it too.

The Captain ruled the frontend gate **conditional** (2026-08-19): *"only when the change
touches gui/frontend"*. A Python-only commit must not require a Node install.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "test.yml"
FRONTEND = "gui/frontend"


def _skill_text() -> str:
    import llmflow

    path = (
        Path(llmflow.__file__).parent
        / "templates"
        / "sp" / "skills"
        / "commit-ready"
        / "SKILL.md"
    )
    return path.read_text(encoding="utf-8")


def _ci_frontend_commands() -> list[str]:
    """The commands CI runs against the frontend, read from the workflow itself."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    commands: list[str] = []
    for job in workflow.get("jobs", {}).values():
        for step in job.get("steps", []):
            run = step.get("run")
            if not run or FRONTEND not in run:
                continue
            for line in run.splitlines():
                line = line.strip()
                if line and not line.startswith(("cd ", "#")):
                    commands.append(line)
    return commands


def test_ci_actually_runs_frontend_commands():
    """Guard on the guard — if CI stops running these, the tests below prove nothing."""
    commands = _ci_frontend_commands()
    assert commands, f"no frontend commands found in {WORKFLOW.name}; this test is stale"


@pytest.mark.parametrize("command", _ci_frontend_commands())
def test_commit_ready_names_every_frontend_command_ci_runs(command: str):
    """Whatever CI runs against the frontend, the local gate must tell you to run too."""
    assert command in _skill_text(), (
        f"CI runs {command!r} against {FRONTEND} but commit-ready never mentions it. "
        "The local gate and CI must not be two descriptions of the definition of done."
    )


def test_commit_ready_names_the_frontend_directory():
    """The reader has to know which changes trigger the extra step."""
    assert FRONTEND in _skill_text(), (
        f"commit-ready does not mention {FRONTEND}, so a contributor changing it has no "
        "reason to think anything beyond pytest applies"
    )


def test_the_frontend_gate_is_conditional_not_unconditional():
    """Captain's ruling: only when the change touches gui/frontend.

    Pinned so a later edit cannot quietly make every Python-only commit require Node,
    nor drop the condition and leave the step looking optional.
    """
    text = _skill_text()
    assert "If the change touches" in text, (
        "the frontend gate must be stated as a condition on touching gui/frontend, "
        "not as an unconditional step"
    )


def test_the_python_suite_is_still_the_baseline():
    """Adding the frontend gate must not displace the suite that covers the engine."""
    assert "hatch run pytest" in _skill_text()
