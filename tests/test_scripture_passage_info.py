"""`type: scripture` can hand back what it already parsed about the reference (#244).

The starter example needs `filename_prefix` to name its output files, and the plan's original
shape got it from `function: llmflow.utils.data.parse_bible_reference`. Rule
`the-language-is-the-whole-surface` forbids a shipped example naming our Python, so the fact has
to arrive through the language instead.

**Why this step rather than a new one.** `type: scripture` already parses the passage in order to
fetch it, so surfacing the parse adds no second parser — `declared-not-inferred` and `one-design`.

**Why a second output name rather than a key in the result.** The step's result is sometimes a
bare string: `format: milestones` with an empty `include` returns text and nothing else. A
`passage_info` key would therefore force every result into a dict, which changes the output shape
of every `type: scripture` step in every project. The two-name form is additive instead —
`output: source` behaves exactly as it does today, and only `output: [source, info]` opts in — so
the non-regression test below is as much the point as the new behaviour is.

Exercised through `load_pipeline(...)` per rule 1 in `docs/ai-context/project/rules.md`: a raw
dict handed to `run_scripture_step` satisfies the runner and the object model by construction and
so cannot see a key the schema fails to declare.
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
    path.write_text(f"name: passage-info\nsteps:\n{steps}", encoding="utf-8")
    return path


def run(path: Path) -> dict:
    """Lint then run, failing with the linter's own message rather than a bare exception."""
    pipeline = load_pipeline(path)
    result = pipeline.lint()
    assert result.valid, f"pipeline did not lint: {getattr(result, 'errors', result)}"
    return pipeline.run(log_file=str(path.parent / "llmflow.log"))


def test_a_second_output_name_receives_the_parsed_reference(tmp_path, store):
    """`output: [text, info]` binds the passage text and what the engine parsed about it."""
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n"
        "    type: scripture\n"
        "    resource: WLC\n"
        '    passage: "GEN 1:1"\n'
        "    format: milestones\n"
        "    output: [source, passage_info]\n",
    )
    context = run(path)

    info = context["passage_info"]
    assert isinstance(info, dict), f"expected the parsed reference, got {type(info).__name__}"
    assert info["book_code"] == "GEN"
    assert info["canonical_reference"] == "Genesis 1:1"
    assert info["filename_prefix"] == "01001001-01001001"
    assert info["testament"] == "OT"
    assert info["original_language"] == "Hebrew"

    # The four versification fields travel with it, because which scheme answered is the thing a
    # reader cannot re-derive from the reference string alone (`project/data-shapes.md`).
    for field in (
        "requested_versification",
        "source_versification",
        "extent_versification",
        "book_in_versification",
    ):
        assert field in info, f"{field} missing from passage_info"

    # The first name still holds the passage itself, unchanged.
    assert "בְּרֵאשִׁית" in context["source"]


def test_a_single_output_name_is_unchanged(tmp_path, store):
    """The opt-in must not alter what every existing pipeline already gets.

    This is the regression that matters: if the handler returned a pair unconditionally, every
    `output: source` in every project would silently become a tuple.
    """
    path = pipeline_file(
        tmp_path,
        "  - name: fetch\n"
        "    type: scripture\n"
        "    resource: WLC\n"
        '    passage: "GEN 1:1"\n'
        "    format: milestones\n"
        "    output: source\n",
    )
    context = run(path)

    assert isinstance(context["source"], str), (
        f"a single output name must still bind the text itself, got "
        f"{type(context['source']).__name__}"
    )
    assert "בְּרֵאשִׁית" in context["source"]
    assert "passage_info" not in context


def test_a_later_step_names_its_file_from_the_parsed_reference(tmp_path, store):
    """`filename_prefix` is why the starter example wants this at all.

    A step's own `saveas` may not name its own output: the linter adds a step's outputs to the
    available set *after* checking that step, although `handle_step_outputs` binds them before
    writing. So the fact is declared by one step and consumed by the next — which is the shape
    the starter example uses, and the reason the first step is the one that declares it.
    """
    out = tmp_path / "out"
    path = pipeline_file(
        tmp_path,
        "  - name: subject\n"
        "    type: scripture\n"
        "    resource: WLC\n"
        '    passage: "GEN 1:1"\n'
        "    format: milestones\n"
        "    output: [subject, passage_info]\n"
        "  - name: context\n"
        "    type: scripture\n"
        "    resource: WLC\n"
        '    passage: "GEN 1:1"\n'
        "    format: milestones\n"
        "    output: context_text\n"
        f'    saveas: "{out}/${{passage_info.filename_prefix}}-context.txt"\n',
    )
    run(path)

    written = out / "01001001-01001001-context.txt"
    assert written.is_file(), (
        f"expected {written}, found "
        f"{list(out.iterdir()) if out.is_dir() else 'no directory'}"
    )
    assert "בְּרֵאשִׁית" in written.read_text(encoding="utf-8")
