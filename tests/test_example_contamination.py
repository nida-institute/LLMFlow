"""Tests: a prompt's example must not be the passage under test.

If the example in a prompt *is* the passage being run, the model reproduces the example rather
than performing the task. The run looks like a success and measures nothing, and nothing in the
output says so.

The check reads the **template**, not the rendered prompt: a `.gpt` file holds the examples, while
the data arrives through `{{var}}`, so the passage under test always appears in a rendered prompt
and its presence there means nothing. In the template it means contamination.

Overlap rather than equality, because a template citing `MRK 1:1-8` contaminates a run on
`MRK 1:5`. `verse_ranges.overlaps` already answers that, so this adds no second implementation of
reference comparison.

What it cannot catch: an example that paraphrases the passage without citing it. No pattern finds
"the wilderness preacher in camel hair". It makes the careless case loud, which is where this
failure actually lives.
"""

from __future__ import annotations

from llmflow.defects import DEFECT_LOG_KEY, DefectLog
from llmflow.utils.prompt_hygiene import contaminating_references
from llmflow.utils.versification import references_in


class TestReferencesIn:

    def test_it_finds_a_usfm_reference(self):
        assert "MRK 1:1-8" in references_in("For example, MRK 1:1-8 shows the pattern.")

    def test_it_finds_a_written_book_name(self):
        assert references_in("See Mark 1:1-8 for the shape.")

    def test_it_finds_a_bare_chapter(self):
        assert references_in("Consider PHM 1 as a whole.")

    def test_ordinary_prose_yields_nothing(self):
        assert references_in("Return valid JSON only. No commentary.") == []

    def test_a_version_number_is_not_a_reference(self):
        assert references_in("Requires version 3:1 of the schema") == []

    def test_a_placeholder_is_not_scanned(self):
        """`{{passage}}` is where the data arrives; it is not an example."""
        assert references_in("Analyse {{passage}} carefully.") == []

    def test_the_same_reference_twice_is_reported_once(self):
        found = references_in("MRK 1:1-8 ... and again MRK 1:1-8")
        assert found.count("MRK 1:1-8") == 1


class TestContaminatingReferences:

    def test_the_run_s_own_passage_in_the_template_is_contamination(self):
        template = "Example: in MRK 1:1-8 the herald appears.\n\nNow analyse {{passage}}."
        assert contaminating_references(template, "MRK 1:1-8") == ["MRK 1:1-8"]

    def test_an_overlapping_reference_is_contamination_too(self):
        """A template citing MRK 1:1-8 contaminates a run on MRK 1:5."""
        assert contaminating_references("Example: MRK 1:1-8", "MRK 1:5") == ["MRK 1:1-8"]

    def test_a_different_passage_is_fine(self):
        assert contaminating_references("Example: MRK 12:13-17", "MRK 1:1-8") == []

    def test_a_different_book_is_fine(self):
        assert contaminating_references("Example: JHN 1:1-8", "MRK 1:1-8") == []

    def test_no_passage_means_no_check(self):
        assert contaminating_references("Example: MRK 1:1-8", "") == []

    def test_an_unparseable_passage_is_not_an_error(self):
        """A pipeline may name something this cannot parse; that is not this check's business."""
        assert contaminating_references("Example: MRK 1:1-8", "not a reference") == []


class TestItRecordsADefect:

    def test_contamination_is_recorded_rather_than_raised(self):
        from llmflow.utils.prompt_hygiene import warn_about_contamination

        log = DefectLog()
        context = {DEFECT_LOG_KEY: log, "passage": "MRK 1:1-8"}
        warn_about_contamination("Example: MRK 1:1-8 shows it.", "prompts/p.gpt", context)

        assert len(log.entries()) == 1
        entry = log.entries()[0]
        assert entry["severity"] == "warning"
        assert "MRK 1:1-8" in entry["message"]
        assert "p.gpt" in entry["message"]

    def test_a_clean_template_records_nothing(self):
        from llmflow.utils.prompt_hygiene import warn_about_contamination

        log = DefectLog()
        context = {DEFECT_LOG_KEY: log, "passage": "MRK 1:1-8"}
        warn_about_contamination("Example: MRK 12:13-17.", "prompts/p.gpt", context)
        assert log.entries() == []

    def test_it_works_without_a_defect_log(self):
        from llmflow.utils.prompt_hygiene import warn_about_contamination

        warn_about_contamination("Example: MRK 1:1-8", "p.gpt", {"passage": "MRK 1:1-8"})
