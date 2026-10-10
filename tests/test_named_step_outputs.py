"""A step's outputs are named, not positional (#263).

`output:` takes a list whose entries name the step type's **members**, each optionally renamed:

    output: [text, reference]                    # each lands under its own name
    output: [subject=text, passage_info=reference]   # variable=member

The rename form is what makes two steps of one type expressible
in a pipeline — two `scripture` steps both offering `text` would otherwise collide on one context
variable, which the starter example needs.

**A bare output name binds the step's primary member**, which for `type: scripture` is `text` —
exactly what it binds today, so no existing pipeline changes. That was ruled as option A against
binding the whole object, which would have turned `${subject}` from a string into a dict in every
pipeline in every project.

**Named binding applies only to step types that declare members.** `function` steps return
arbitrary Python and cannot declare any, so positional stays there and is the honest form — the
stated boundary in the design, not an oversight.

Exercised through `load_pipeline(...)` per rule 1 in `docs/ai-context/project/rules.md`.

Design: `project/plans/design-named-step-outputs.md`.

**`output:` is the one key (#263).** `returns:` is
retired from the language, and `alignment` and `parallel-passages` migrate to naming their members
in `output:` in the same change. Naming a member requests it, so there is no second key to ask
with.
"""
from pathlib import Path

import pytest

from llmflow import load_pipeline

SHIPPED_SCHEMES = Path(__file__).resolve().parent.parent / "src/llmflow/templates/sp/versification"

HEBREW_TSV = (
    "ref\ttext\tafter\n"
    "GEN 1:1!1\tבְּרֵאשִׁית\t \n"
    "GEN 1:1!2\tבָּרָא\t\n"
    "GEN 1:2!1\tוְהָאָרֶץ\t\n"
)


@pytest.fixture
def store(tmp_path, monkeypatch) -> Path:
    """A throwaway `$SP_HOME` holding one registered resource and the shipped schemes."""
    home = tmp_path / "sp"
    resources = home / "resources"
    resources.mkdir(parents=True)

    tsv = tmp_path / "wlc.tsv"
    tsv.write_text(HEBREW_TSV, encoding="utf-8")
    (resources / "WLC.yaml").write_text(
        f"id: WLC\nname: Westminster Leningrad Codex\nkind: tsv\npath: {tsv}\n"
        f"versification_scheme: org\n",
        encoding="utf-8",
    )

    versification = home / "versification"
    versification.mkdir()
    for scheme in SHIPPED_SCHEMES.glob("*.json"):
        (versification / scheme.name).write_text(scheme.read_text(encoding="utf-8"), "utf-8")

    monkeypatch.setenv("SP_HOME", str(home))
    return home


def pipeline_file(tmp_path: Path, steps: str) -> Path:
    path = tmp_path / "pipeline.yaml"
    path.write_text(f"name: named-outputs\nsteps:\n{steps}", encoding="utf-8")
    return path


def run(path: Path) -> dict:
    pipeline = load_pipeline(path)
    result = pipeline.lint()
    assert result.valid, f"pipeline did not lint: {getattr(result, 'errors', result)}"
    return pipeline.run(log_file=str(path.parent / "llmflow.log"))


def scripture_step(output: str, name: str = "subject") -> str:
    return (
        f"  - name: {name}\n"
        "    type: scripture\n"
        "    resource: WLC\n"
        '    passage: "GEN 1:1"\n'
        "    format: milestones\n"
        f"    output: {output}\n"
    )


# --- members bind by name ---------------------------------------------------------------


def test_members_bind_under_their_own_names(tmp_path, store):
    """`output: [text, reference]` — each member lands in a variable of the same name."""
    context = run(pipeline_file(tmp_path, scripture_step("[text, reference]")))

    assert isinstance(context["text"], str), "the `text` member is the passage itself"
    assert "בְּרֵאשִׁית" in context["text"]

    assert isinstance(context["reference"], dict), "the `reference` member is the parsed reference"
    assert context["reference"]["book_code"] == "GEN"
    assert context["reference"]["filename_prefix"] == "01001001-01001001"


def test_a_member_can_be_renamed(tmp_path, store):
    """`variable=member` — the left side is the pipeline's name, the right the step's."""
    context = run(
        pipeline_file(tmp_path, scripture_step("[subject=text, passage_info=reference]"))
    )

    assert "בְּרֵאשִׁית" in context["subject"]
    assert context["passage_info"]["book_code"] == "GEN"
    assert "text" not in context, "a renamed member does not also bind under its own name"
    assert "reference" not in context


def test_renaming_is_what_lets_two_steps_of_one_type_coexist(tmp_path, store):
    """The case the starter example needs: a Greek passage and an English one, both `text`."""
    steps = scripture_step("[greek=text, passage_info=reference]", name="subject") + scripture_step(
        "[english=text]", name="english"
    )
    context = run(pipeline_file(tmp_path, steps))

    assert "בְּרֵאשִׁית" in context["greek"]
    assert "בְּרֵאשִׁית" in context["english"]
    assert context["passage_info"]["book_code"] == "GEN"


def test_a_subset_may_be_requested(tmp_path, store):
    """Naming a member requests it; a caller need not name them all."""
    context = run(pipeline_file(tmp_path, scripture_step("[reference]")))

    assert context["reference"]["book_code"] == "GEN"
    assert "text" not in context, "an unrequested member is absent, not empty"


# --- the bare form is unchanged, which is the whole compatibility contract -------------


def test_a_bare_name_binds_the_primary_member(tmp_path, store):
    """Ruled A: `output: subject` binds `text`, exactly as it does today.

    This is the regression that matters. Binding the whole object instead would turn
    `${subject}` from a string into a dict in every pipeline in every project.
    """
    context = run(pipeline_file(tmp_path, scripture_step("subject")))

    assert isinstance(context["subject"], str), (
        f"a bare output name must bind the primary member, got "
        f"{type(context['subject']).__name__}"
    )
    assert "בְּרֵאשִׁית" in context["subject"]


# --- what lint catches, which is the point of declaring members at all ----------------


def test_an_unknown_member_is_a_lint_error(tmp_path, store):
    """A member the step type does not declare is caught before the run."""
    pipeline = load_pipeline(pipeline_file(tmp_path, scripture_step("[refrence]")))
    result = pipeline.lint()

    assert not result.valid, "a misspelled member name should not lint"
    message = str(getattr(result, "errors", result))
    assert "refrence" in message, f"the error should name the offending member: {message}"
    assert "reference" in message, f"the error should name the legal members: {message}"


def test_naming_the_same_member_twice_is_a_lint_error(tmp_path, store):
    """Two variables from one member is a request nobody means to make."""
    pipeline = load_pipeline(pipeline_file(tmp_path, scripture_step("[a=text, b=text]")))
    result = pipeline.lint()

    assert not result.valid, "the same member bound twice should not lint"
