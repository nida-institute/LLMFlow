"""Tests: a Paratext project's own versification, when it carries a `custom.vrs`.

The reported name answers which versification is in force. A project using a standard scheme
reports that scheme's name; a project using a standard scheme with its own `custom.vrs` on top
is not using the standard scheme any more, so it reports the project's name — the only name
that numbering has.

A registry-declared `versification_scheme` chooses which standard scheme the overlay is based
on. It does not suppress the overlay: the project's own file always applies.
"""

from pathlib import Path

import pytest

from llmflow.utils.scripture import resource_scheme
from llmflow.utils.versification import Scheme, packaged_mappings_dir, scheme_name

MAPPINGS = packaged_mappings_dir()

OVERLAY = """\
# a project's own numbering
3JN 1:14
-MAT 17:21
PSA 47:10
"""


def _project(tmp_path: Path, number: str = "4", overlay: str | None = None) -> dict:
    """A Paratext project directory, and the registry definition naming it."""
    project = tmp_path / "projects" / "myProject"
    project.mkdir(parents=True)
    (project / "Settings.xml").write_text(
        f"<ScriptureText><Versification>{number}</Versification></ScriptureText>"
    )
    if overlay is not None:
        (project / "custom.vrs").write_text(overlay)
    return {"kind": "usfm", "base_dir": str(project.parent), "project": project.name}


# ---------------------------------------------------------------------------
# A project with no custom.vrs is unchanged
# ---------------------------------------------------------------------------

class TestStandardProject:

    def test_reports_the_standard_scheme_name(self, tmp_path):
        scheme = resource_scheme(_project(tmp_path), mappings_dir=MAPPINGS)
        assert scheme == "eng"

    def test_the_name_is_a_string_not_a_scheme(self, tmp_path):
        scheme = resource_scheme(_project(tmp_path), mappings_dir=MAPPINGS)
        assert not isinstance(scheme, Scheme)

    def test_the_original_scheme_number(self, tmp_path):
        scheme = resource_scheme(_project(tmp_path, number="1"), mappings_dir=MAPPINGS)
        assert scheme == "org"


# ---------------------------------------------------------------------------
# A project carrying a custom.vrs reports its own name
# ---------------------------------------------------------------------------

class TestProjectWithOverlay:

    def test_reports_the_project_name(self, tmp_path):
        scheme = resource_scheme(_project(tmp_path, overlay=OVERLAY), mappings_dir=MAPPINGS)
        assert scheme_name(scheme) == "myProject"

    def test_the_scheme_travels_as_an_object(self, tmp_path):
        scheme = resource_scheme(_project(tmp_path, overlay=OVERLAY), mappings_dir=MAPPINGS)
        assert isinstance(scheme, Scheme)

    def test_the_overlay_is_applied(self, tmp_path):
        scheme = resource_scheme(_project(tmp_path, overlay=OVERLAY), mappings_dir=MAPPINGS)
        assert int(scheme.max_verses["3JN"][0]) == 14
        assert int(scheme.max_verses["PSA"][46]) == 10

    def test_the_base_supplies_what_the_overlay_does_not_state(self, tmp_path):
        scheme = resource_scheme(_project(tmp_path, overlay=OVERLAY), mappings_dir=MAPPINGS)
        assert int(scheme.max_verses["GEN"][0]) == 31

    def test_excluded_verses_come_through(self, tmp_path):
        scheme = resource_scheme(_project(tmp_path, overlay=OVERLAY), mappings_dir=MAPPINGS)
        assert "MAT 17:21" in scheme.excluded_verses

    def test_the_capitalised_spelling_is_found(self, tmp_path):
        definition = _project(tmp_path)
        project_dir = Path(definition["base_dir"]) / definition["project"]
        (project_dir / "Custom.vrs").write_text(OVERLAY)
        scheme = resource_scheme(definition, mappings_dir=MAPPINGS)
        assert scheme_name(scheme) == "myProject"

    def test_an_overlay_stating_nothing_leaves_the_base_name_in_force(self, tmp_path):
        # One real project ships a comments-only custom.vrs. Its numbering is its base's, so
        # it is not a numbering of its own and does not take the project's name.
        scheme = resource_scheme(
            _project(tmp_path, overlay="# nothing stated here\n"), mappings_dir=MAPPINGS
        )
        assert scheme == "eng"

    def test_no_longer_warns_that_the_overlay_is_unread(self, tmp_path, caplog):
        resource_scheme(_project(tmp_path, overlay=OVERLAY), mappings_dir=MAPPINGS)
        assert "does not read" not in caplog.text


# ---------------------------------------------------------------------------
# A declared scheme chooses the base, and never suppresses the overlay
# ---------------------------------------------------------------------------

class TestDeclaredSchemeChoosesTheBase:

    def test_a_declared_scheme_alone_is_reported_as_itself(self, tmp_path):
        definition = _project(tmp_path)
        definition["versification_scheme"] = "org"
        assert resource_scheme(definition, mappings_dir=MAPPINGS) == "org"

    def test_a_declared_scheme_does_not_suppress_the_overlay(self, tmp_path):
        definition = _project(tmp_path, overlay=OVERLAY)
        definition["versification_scheme"] = "org"
        scheme = resource_scheme(definition, mappings_dir=MAPPINGS)
        assert scheme_name(scheme) == "myProject"

    def test_the_declared_scheme_is_the_base_that_is_folded_onto(self, tmp_path):
        from llmflow.utils.versification import load_scheme

        definition = _project(tmp_path, overlay=OVERLAY)
        definition["versification_scheme"] = "org"
        scheme = resource_scheme(definition, mappings_dir=MAPPINGS)
        # PSA 47 is stated by the overlay; PSA 48 is not, so it must come from org, which
        # numbers the Psalms differently from eng.
        org = load_scheme("org", MAPPINGS)
        assert int(scheme.max_verses["PSA"][46]) == 10
        assert scheme.max_verses["PSA"][47] == org.max_verses["PSA"][47]


# ---------------------------------------------------------------------------
# Definitions that are not Paratext projects
# ---------------------------------------------------------------------------

class TestNonParatextDefinitions:

    def test_a_definition_without_a_project_is_untouched(self, tmp_path):
        assert resource_scheme({"kind": "tsv", "path": "x.tsv"}, mappings_dir=MAPPINGS) is None

    def test_a_declared_scheme_on_a_plain_edition(self, tmp_path):
        definition = {"kind": "tsv", "path": "x.tsv", "versification_scheme": "lxx"}
        assert resource_scheme(definition, mappings_dir=MAPPINGS) == "lxx"

    def test_a_project_whose_number_is_unknown(self, tmp_path):
        assert resource_scheme(_project(tmp_path, number="99"), mappings_dir=MAPPINGS) is None
