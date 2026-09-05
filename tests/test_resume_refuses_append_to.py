"""`--resume` must refuse a step that accumulates, as `--rewind-to` already does.

A resumed step is skipped and its saved artifact loaded into its declared `output`. That is sound
for a step whose result *is* its output, and wrong for one that also appends to a list:
`_load_resume_output` assigns the file's text to the output variable and never mentions
`append_to`, so the accumulator gains nothing while every later step runs happily on an empty
list.

The failure mode is the one worth refusing for: **the run reports success.** `discourse-flow` lost
a full Mark run this way — 17 windows, 57 subdivisions, 128 pericope analyses and a synthesis, all
completed, then a crash on a function step; and neither salvage path worked. `--rewind-to` refuses
the pipeline outright at `utils/rewind.py:77`, which is annoying and honest. `--resume` would have
produced an empty book and called it done.

Refusing matches the behaviour already chosen on the other path, and is what they asked for:
*"a resume that produces an empty accumulator is worse than one that refuses, because the run
appears to succeed."*
"""

import pytest

from llmflow.exceptions import StepRewindError
from llmflow.runner import _load_resume_output


def test_a_step_that_only_outputs_resumes(tmp_path):
    """The ordinary case stays ordinary: the artifact becomes the step's output."""
    artifact = tmp_path / "summary.md"
    artifact.write_text("a summary", encoding="utf-8")
    context: dict = {}

    _load_resume_output({"name": "summarise", "output": "summary"}, artifact, context)

    assert context["summary"] == "a summary"


def test_a_step_that_appends_is_refused(tmp_path):
    """Loading the artifact would set `output` and leave the accumulator empty, silently."""
    artifact = tmp_path / "pericope.json"
    artifact.write_text('{"id": "one"}', encoding="utf-8")
    context: dict = {"pericope_results": []}

    with pytest.raises(StepRewindError, match="appends to"):
        _load_resume_output(
            {"name": "package_pericope", "output": "packaged", "append_to": "pericope_results"},
            artifact,
            context,
        )


def test_the_refusal_names_the_step_and_what_to_do(tmp_path):
    artifact = tmp_path / "x.json"
    artifact.write_text("{}", encoding="utf-8")

    with pytest.raises(StepRewindError) as raised:
        _load_resume_output(
            {"name": "package_pericope", "output": "packaged", "append_to": "results"},
            artifact,
            {},
        )

    message = str(raised.value)
    assert "package_pericope" in message
    assert "results" in message, "the accumulator that would have been left empty"


def test_nothing_is_written_to_context_when_it_is_refused(tmp_path):
    """A half-applied resume is the defect; refusing must leave the context untouched."""
    artifact = tmp_path / "x.json"
    artifact.write_text("{}", encoding="utf-8")
    context: dict = {"results": []}

    with pytest.raises(StepRewindError):
        _load_resume_output(
            {"name": "s", "output": "packaged", "append_to": "results"}, artifact, context
        )

    assert "packaged" not in context
    assert context["results"] == []
