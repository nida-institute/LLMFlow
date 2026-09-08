"""Tests: the scripture step names a `resource`, and `edition` is retired.

`edition` claimed a distinction the data does not make — `SBLGNT` is a TSV inside
`Clear-Bible/macula-greek`, not a critical edition of the Greek New Testament, and the same
edition could be registered twice in two encodings. A dataset provides resources.

Driven from the schema, which is where the language is declared: `step_keys()` unions the common
keys with every per-type branch, and `model._STEP_ATTRS` builds the object model's attributes from
that union. So the API follows the declaration rather than being kept in step with it by hand, and
these tests go through the API a consumer uses.

One syntax, no aliases. The retired key fails loud and names its replacement, as the `for`/`in`
migration established.

**This file names the retired key deliberately.** A search-and-replace across the suite once
turned every `edition` here into `resource`, leaving `assert "resource" not in step_keys()` beside
`assert "resource" in step_keys()` and three retirement tests that linted a valid pipeline while
asserting it failed. A test whose subject is the old word cannot be migrated by renaming it.
"""

from pathlib import Path

import pytest

from llmflow import load_pipeline
from llmflow.pipeline_schema import step_keys

RETIRED = "edition"
CURRENT = "resource"


def _pipeline(tmp_path: Path, key: str) -> Path:
    path = tmp_path / "pipeline.yaml"
    path.write_text(
        "name: test\n"
        "steps:\n"
        "  - name: fetch\n"
        "    type: scripture\n"
        f"    {key}: SBLGNT\n"
        '    passage: "MRK 1:14"\n'
        "    output: source\n"
    )
    return path


# ---------------------------------------------------------------------------
# The declaration
# ---------------------------------------------------------------------------

class TestTheSchemaDeclaresResource:

    def test_the_current_key_is_declared(self):
        assert CURRENT in step_keys()

    def test_the_retired_key_is_not(self):
        assert RETIRED not in step_keys()


# ---------------------------------------------------------------------------
# The API, which is generated from it
# ---------------------------------------------------------------------------

class TestTheObjectModelFollows:

    def test_a_step_exposes_the_current_key(self, tmp_path):
        pipeline = load_pipeline(str(_pipeline(tmp_path, CURRENT)))
        assert pipeline.steps[0].resource == "SBLGNT"

    def test_a_step_no_longer_exposes_the_retired_one(self, tmp_path):
        pipeline = load_pipeline(str(_pipeline(tmp_path, CURRENT)))
        with pytest.raises(AttributeError):
            getattr(pipeline.steps[0], RETIRED)


# ---------------------------------------------------------------------------
# The retired key fails loud
# ---------------------------------------------------------------------------

class TestTheRetiredKeyIsRefused:

    def test_a_pipeline_using_it_does_not_lint(self, tmp_path):
        result = load_pipeline(str(_pipeline(tmp_path, RETIRED))).lint()
        assert not result.valid

    def test_the_failure_names_the_replacement(self, tmp_path):
        result = load_pipeline(str(_pipeline(tmp_path, RETIRED))).lint()
        joined = " ".join(result.errors)
        assert RETIRED in joined
        assert CURRENT in joined

    def test_the_current_key_lints_clean(self, tmp_path):
        result = load_pipeline(str(_pipeline(tmp_path, CURRENT))).lint()
        assert result.valid, result.errors
