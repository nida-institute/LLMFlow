"""A shipped skill must not send a session to a path that does not exist in a project.

Every skill and discipline here is installed into projects that are not this one. This repository
has files those projects never receive — `docs/architecture.md`, `docs/audits/` — so a reference
that resolves while writing the skill resolves nowhere for its actual audience, and nothing says
so. The session simply finds nothing and works around it.

Found the hard way: a consumer's audit skill routed to `docs/audits/INDEX.md`, which `sp init` has
never created in any project. Two more pointed at the pre-split layout — `docs/ai-context/rules.md`
and `docs/ai-context/github-workflow.md` — which moved into `sp/` and `project/` halves and were
never swept. The worst of them told a session to add a project rule to what is now a *generated*
file, where `sp doctor` reverts it without a word.

The catalogue is the authority on what a project actually gets, so that is what this checks
against. Two things are deliberately not failures: a path presented as an optional override a
project *may* supply, and a path inside an illustrative example. Both are named below rather than
pattern-matched, because a rule that guesses at intent is one nobody can predict.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "src" / "llmflow" / "templates"

#: Paths a project may supply to override a shipped default. Absent is the normal case.
OPTIONAL_OVERRIDES = frozenset({
    "docs/prompt-organization-convention.md",
})

#: Referenced inside an example of what someone *said* or a sample checklist line, not as a
#: location to open. Each is quoted prose rather than an instruction.
ILLUSTRATIVE = frozenset({
    "docs/Y",
    "docs/language.md",
    "docs/architecture.md",
    "docs/architecture/debugging.md",   # a provenance note: "generalized from ears-to-hear ..."
})

#: Created by a skill's own run rather than by `sp init`, so absence before the run is correct.
WRITTEN_BY_A_SKILL = frozenset({
    "project/HANDOFF.md",
    "project/plans/tmp-context.md",
})

#: Open questions, listed so a reader can find them. An unresolved case recorded here is visible;
#: a quietly widened pattern is not. Empty is the goal, not the assumption — the previous entry,
#: `docs/audits/`, was resolved by fixing the document that referenced it rather than by shipping
#: the directory, since the directory's absence turned out to be a decision and not an oversight.
AWAITING_A_RULING: frozenset = frozenset()

#: Correct in an ecosystem whose ai-context is not split into halves. A shared skill names both
#: spellings so it serves either, and the flat one resolves nowhere here by design.
UNSPLIT_EQUIVALENT = frozenset({
    "docs/ai-context/rules.md",
})

EXEMPT = (OPTIONAL_OVERRIDES | ILLUSTRATIVE | WRITTEN_BY_A_SKILL
          | AWAITING_A_RULING | UNSPLIT_EQUIVALENT)

#: A repo-relative path inside backticks. Only the trees a project actually has.
PATH = re.compile(r"`((?:docs|project|prompts|pipelines|schemas)/[\w./-]+)`")

SHIPPED = sorted(
    list((TEMPLATES / "sp" / "skills").rglob("SKILL.md"))
    + list((TEMPLATES / "sp" / "disciplines").glob("*.md"))
)


def _catalogued() -> set:
    catalog = yaml.safe_load((REPO_ROOT / "data" / "file-catalog.yaml").read_text(encoding="utf-8"))
    entries = catalog["files"] if isinstance(catalog, dict) and "files" in catalog else catalog
    paths = {e["path"] for e in entries if isinstance(e, dict) and e.get("path")}
    return paths | {str(Path(p).parent) for p in paths}


def test_there_are_shipped_skills_to_check():
    """Guard the guard: a bad glob here would pass by having nothing to inspect."""
    assert len(SHIPPED) > 10, f"only found {len(SHIPPED)} shipped documents"


@pytest.mark.parametrize("path", SHIPPED, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_referenced_paths_exist_in_a_project(path: Path):
    known = _catalogued()
    offences = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for match in PATH.finditer(line):
            target = match.group(1).rstrip("/")
            if target in EXEMPT or target in known:
                continue
            # An example filename under a directory that exists — `project/audits/audit-thing.md`
            # — illustrates naming rather than naming a file. The directory must be real; the file
            # need not be. A directory that is itself unresolved counts here too, so one open
            # question does not also fail every example written under it.
            if str(Path(target).parent) in known or str(Path(target).parent) in AWAITING_A_RULING:
                continue
            offences.append(f"{path.relative_to(TEMPLATES)}:{number}: {target}")

    assert not offences, (
        "shipped documents pointing at paths `sp init` does not create:\n  "
        + "\n  ".join(offences)
        + "\n\nEither ship the file through data/file-catalog.yaml, correct the reference, or "
          "add it to one of the named exemptions with a reason."
    )
