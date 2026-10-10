"""`type: parallel-passages` — the step that asks which groups a passage takes part in.

The reader is tested in `test_parallel_passages.py`; this file is about the step: that the
language accepts it, that a group reaches the context whole, and that a passage in no group is
an empty list (#258).

Every expected value here comes from `SAMPLE` below, which is written for these tests. No
assertion names a figure read off the real UBS database: a count taken from that file is a
measurement of the data rather than a statement about the code, so a defect in the reader
would be frozen into the suite as the expected answer, and a UBS release would turn a
correct engine red. Measurements belong in #258, beside the command that re-derives them.
"""

from __future__ import annotations

import json

import pytest

from llmflow import load_pipeline
from llmflow import paths as _paths
from tests.parallel_passages_fixture import build_dataset

#: Four groups, written to state the shapes the step has to get right:
#:
#:   1. an OT source quoted by two NT verses
#:   2. the same two NT verses without the OT source — a subset of (1)
#:   3. a row naming a range
#:   4. a row naming a comma list
#:
#: (1) and (2) together are the case where one group's members are contained in another's:
#: both are returned, because the database states them separately and collapsing one into the
#: other would assert a judgment the source never makes (#258).
SAMPLE = """<?xml version="1.0" encoding="utf-8"?>
<Passages>
  <Passage>
    <Verse HEB="2222">JOL 2:1</Verse>
    <Verse GRK="22222">MRK 1:2</Verse>
    <Verse GRK="22222">LUK 7:27</Verse>
  </Passage>
  <Passage>
    <Verse GRK="22222">MRK 1:2</Verse>
    <Verse GRK="22222">LUK 7:27</Verse>
  </Passage>
  <Passage>
    <Verse GRK="2222">MAT 3:1-2</Verse>
    <Verse GRK="2222">MRK 1:4-5</Verse>
  </Passage>
  <Passage>
    <Verse GRK="2222">MAT 8:16</Verse>
    <Verse GRK="2222">MRK 1:32,34</Verse>
  </Passage>
  <Passage>
    <Verse HEB="2222">PSA 51:3</Verse>
    <Verse GRK="2222">ROM 3:4</Verse>
  </Passage>
</Passages>
"""


@pytest.fixture
def registered(tmp_path, monkeypatch):
    """A resource with no parallel-passages field, and the engine reading the fixture dataset.

    The dataset ships with the engine, so a registration names nothing about it. The tests
    point the reader at a dataset converted from `SAMPLE` rather than at the shipped one.
    `$SP_HOME` is already redirected for every test by `conftest`.
    """
    from llmflow.utils import parallel_passages

    dataset = build_dataset(tmp_path, SAMPLE)
    monkeypatch.setattr(parallel_passages, "dataset_path", lambda: dataset)

    store = tmp_path / "store"
    (store / "registrations").mkdir(parents=True)
    monkeypatch.setenv(_paths.SP_HOME_ENV, str(store))
    (store / "registrations" / "TESTGRK.yaml").write_text(
        "id: TESTGRK\nkind: tsv\nversification_scheme: org\n", encoding="utf-8"
    )
    return "TESTGRK"


def build(tmp_path, resource, passage, extra="", output="parallels"):
    """A one-step pipeline that saves the step's result as JSON.

    `output` names the members wanted (#263). A bare name binds the primary member,
    `references`, which is what every test here reads.
    """
    out = tmp_path / "parallels.json"
    pipeline = tmp_path / "parallels.yaml"
    pipeline.write_text(
        "name: parallels-under-test\n"
        "steps:\n"
        "  - name: parallels\n"
        "    type: parallel-passages\n"
        f"    resource: {resource}\n"
        f'    passage: "{passage}"\n'
        f"{extra}"
        f"    output: {output}\n"
        f"    saveas: {out}\n",
        encoding="utf-8",
    )
    return load_pipeline(pipeline), out


def run(tmp_path, resource, passage, extra="", output="parallels"):
    """Run it and return what reached disk."""
    pipeline, out = build(tmp_path, resource, passage, extra, output)
    pipeline.run()
    return json.loads(out.read_text(encoding="utf-8"))


def references(group):
    """The references a returned group names, in the order it names them."""
    return group["references"]


class TestTheStepIsInTheLanguage:
    def test_the_schema_declares_the_type_and_its_keys(self):
        """The type is declared, not permissive.

        Asserted against the schema rather than against a clean lint, because lint alone
        cannot tell the difference: an unrecognised type is treated as a plugin, whose keys
        cannot be enumerated, so a pipeline using this step lints clean today — before
        anything implements it. A test resting on that would pass whether or not the branch
        was ever written.
        """
        from llmflow.pipeline_schema import allowed_step_keys, common_step_keys

        allowed = allowed_step_keys("parallel-passages")
        assert allowed is not None, "the type is permissive — no schema branch declares it"
        # `returns:` was retired (#263): members are named in `output:`, which is a
        # common key, and naming one is how it is requested.
        assert {"resource", "passage", "versification"} <= allowed
        assert "returns" not in allowed, "returns: is retired; members are named in output:"
        # `include:` belongs to `type: scripture`. Not `format:`, which is common to every
        # step — it names how `saveas` serialises — so it is legal here and proves nothing.
        assert "include" not in allowed - common_step_keys()

    def test_a_well_formed_step_lints_clean(self, tmp_path, registered):
        pipeline, _ = build(tmp_path, registered, "MRK 1:2")
        result = pipeline.lint()
        assert result.valid, result.errors

    def test_a_key_belonging_to_another_step_type_is_refused(self, tmp_path, registered):
        """The schema is type-discriminated, so a `type: scripture` key here is an error.

        This is the step's half of the silent-ignore hole: `include:` is real, no handler on
        this step reads it, and a global allowed-set would have accepted it with no effect.
        """
        pipeline, _ = build(tmp_path, registered, "MRK 1:2", extra="    include: [ids]\n")
        result = pipeline.lint()
        assert not result.valid
        assert any("include" in str(error) for error in result.errors)


class TestAGroupIsReturnedWhole:
    def test_every_member_reaches_the_context(self, tmp_path, registered):
        """Asking about one verse returns the group's other members too, never an intersection."""
        groups = run(tmp_path, registered, "JOL 2:1")
        assert [references(group) for group in groups] == [["JOL 2:1", "MRK 1:2", "LUK 7:27"]]

    def test_a_verse_inside_a_range_row_finds_that_row(self, tmp_path, registered):
        """String equality would miss it: the row names `MRK 1:4-5` and the request names 1:5."""
        groups = run(tmp_path, registered, "MRK 1:5")
        assert [references(group) for group in groups] == [["MAT 3:1-2", "MRK 1:4-5"]]

    def test_a_verse_the_comma_row_omits_does_not_match(self, tmp_path, registered):
        """`MRK 1:32,34` names two verses, not the one between them."""
        assert run(tmp_path, registered, "MRK 1:33") == []

    def test_a_group_carries_its_references_and_nothing_else(self, tmp_path, registered):
        """`references` is the reference list, not the raw input (#258).

        The per-word digits index UBSGNT5 rather than the resource asked about, so nothing
        can read them until the identifier join exists. They belong under `words`, beside
        that join — as `syntax` leaves out `rule` and `nodeId` for the same reason.
        """
        group = run(tmp_path, registered, "JOL 2:1")[0]
        assert set(group) == {"references"}


class TestASubsetGroupIsStillItsOwnGroup:
    def test_both_groups_come_back(self, tmp_path, registered):
        """A group is returned whole, and groups are not collapsed (#258).

        The fixture states the quotation and the bare parallel as two groups. Returning one
        would merge two relations the source keeps apart — that Mark quotes Joel, and that
        Mark and Luke run parallel — and no later reader could recover the difference.
        """
        groups = run(tmp_path, registered, "MRK 1:2")
        assert [references(group) for group in groups] == [
            ["JOL 2:1", "MRK 1:2", "LUK 7:27"],
            ["MRK 1:2", "LUK 7:27"],
        ]

    def test_a_range_request_repeats_no_group(self, tmp_path, registered):
        groups = run(tmp_path, registered, "MRK 1:1-5")
        signatures = [tuple(references(group)) for group in groups]
        assert len(signatures) == len(set(signatures))


class TestTheRequestIsMappedBeforeLookup:
    def test_a_reference_in_another_scheme_finds_the_row(self, tmp_path, registered):
        """`versification:` names the scheme the request is written in, not the database's.

        The database is numbered `org`, where the psalm's superscription is counted, so the
        verse an English reader calls `PSA 51:1` is `PSA 51:3` there. Unmapped, this finds
        nothing and the run still reports success — which is the failure the key prevents.
        """
        groups = run(
            tmp_path, registered, "PSA 51:1", extra="    versification: eng\n"
        )
        assert [references(group) for group in groups] == [["PSA 51:3", "ROM 3:4"]]


class TestTwoKindsOfNothing:
    def test_a_passage_in_no_group_is_an_empty_list(self, tmp_path, registered):
        """Consulted, and this passage takes part in nothing."""
        assert run(tmp_path, registered, "JHN 1:1") == []

    def test_a_resource_needs_no_registration_field(self, tmp_path, registered):
        """The dataset ships with the engine, so the registration names nothing about it."""
        assert run(tmp_path, registered, "MRK 1:2") != []


class TestTheRegistrationOptionIsGone:
    def test_resource_set_refuses_the_retired_option(self, capsys):
        """`--parallel-passages-path` pointed a registration at the XML; there is nothing left
        for it to point at, so it is refused rather than accepted and ignored."""
        from llmflow.cli import main

        with pytest.raises(SystemExit):
            main(["resource", "set", "SBLGNT", "--parallel-passages-path", "anything"])
        assert "--parallel-passages-path" in capsys.readouterr().err


class TestThroughTheCommandLine:
    """`sp run` is the surface a pipeline author actually has.

    The cases above drive `load_pipeline(...).run()`, which is cheaper and more focused but
    skips argument parsing and `--var` plumbing. This is the path an application takes end to
    end: a reference arrives as a `--var`, reaches the step, and the answer lands on disk.
    """

    def test_a_var_reaches_the_step_and_the_answer_lands_on_disk(
        self, tmp_path, monkeypatch, registered
    ):
        from llmflow.cli import main

        out = tmp_path / "parallels.json"
        pipeline = tmp_path / "parallels.yaml"
        pipeline.write_text(
            "name: parallels-through-the-cli\n"
            "steps:\n"
            "  - name: parallels\n"
            "    type: parallel-passages\n"
            f"    resource: {registered}\n"
            '    passage: "${passage}"\n'
            "    output: parallels\n"
            f"    saveas: {out}\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        main(["run", "--pipeline", str(pipeline), "--var", "passage=JOL 2:1"])

        assert json.loads(out.read_text(encoding="utf-8")) == [
            {"references": ["JOL 2:1", "MRK 1:2", "LUK 7:27"]}
        ]


class TestTheWordLevelHalfIsNotBuilt:
    def test_returns_words_is_refused_and_names_what_is_missing(self, tmp_path, registered):
        """It must not quietly fall back to counting positions.

        The digits index UBSGNT5 and the resource is numbered otherwise, so position alone
        answers against the wrong words some of the time — and silently, which is worse than
        refusing. The join goes through MARBLE identifiers or it does not happen.
        """
        with pytest.raises(Exception) as caught:
            run(tmp_path, registered, "MRK 1:2", output="[words]")
        assert "words" in str(caught.value)
