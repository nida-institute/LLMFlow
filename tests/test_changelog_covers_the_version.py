"""The version in `pyproject.toml` must have a section in the CHANGELOG.

The recurring failure this catches: bump the version, open the PR, and discover afterwards that
the CHANGELOG still says `## Unreleased` — so the release describes itself as unreleased and the
notes for it exist nowhere. It has happened often enough to be a process defect rather than an
oversight, and a checklist item does not fix a step that gets skipped. This runs in CI on every
pull request, which is before the merge that would ship it.

It stays green during ordinary development: `pyproject.toml` holds the *last released* version
while new entries accumulate under `## Unreleased`, so the released heading is present and the
check passes. It goes red at exactly one moment — the version is bumped and the heading is not
written — which is the moment worth catching.
"""

from __future__ import annotations

import re
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"

#: A version heading: `##`, the version, a dash, then an ISO date. The CHANGELOG uses an em dash;
#: a hyphen is accepted so a heading is not rejected over punctuation.
VERSION_HEADING = re.compile(r"^##\s+(\d[\w.]*)\s*[—-]\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)


def declared_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def changelog_versions() -> list:
    return VERSION_HEADING.findall(CHANGELOG.read_text(encoding="utf-8"))


def test_the_changelog_has_versioned_sections_at_all():
    """Absent, every check below would pass by having nothing to read."""
    assert changelog_versions(), "no `## <version> — <date>` headings found"


def test_the_declared_version_has_a_changelog_section():
    version = declared_version()
    documented = [v for v, _ in changelog_versions()]
    assert version in documented, (
        f"pyproject declares {version} and the CHANGELOG has no `## {version} — <date>` "
        f"heading. Rename `## Unreleased` to it before the PR, or the release ships describing "
        f"itself as unreleased. Documented: {documented[:5]}"
    )


def test_the_declared_version_is_documented_once():
    """Scoped to the release being made, deliberately.

    Older sections are the record and are not this guard's business. One historical version
    carries two headings from a mis-merge; merging them would edit the record to satisfy a test.
    """
    documented = [v for v, _ in changelog_versions()]
    version = declared_version()
    assert documented.count(version) == 1, (
        f"{documented.count(version)} sections claim version {version}"
    )


def test_the_newest_section_is_the_declared_version():
    """A section added below an older one reads as history rather than as this release."""
    documented = [v for v, _ in changelog_versions()]
    assert documented[0] == declared_version(), (
        f"the topmost CHANGELOG section is {documented[0]}, but pyproject declares "
        f"{declared_version()}. The newest section belongs at the top, under `## Unreleased`."
    )
