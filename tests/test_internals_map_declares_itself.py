"""`docs/index.json` says what it is, inside itself.

It lists every module and function in `src/` — 93 modules and 881 functions when this was
written. Nothing in it said what it was for, so a reader who finds a catalogue that size
concludes it is an API listing, because nothing contradicts that reading. `project/index.md`
calls it *"Every module and function this engine has"*, which reinforces it.

**The boundary belongs in the artifact, not beside it.** A note in a document is one a reader
may not have open; a note in the file is one they cannot miss. It is also the only form that
survives the file being read by a tool, copied, or handed to a model that was given the path and
nothing else.

**This does not restate `the-language-is-the-whole-surface`** — that rule governs what a project
is told. This is about a file that ships to nobody and is read constantly *here*, by sessions
working on the engine, where the temptation is to treat it as an API for tests.

Held by a test rather than a convention because it is generated: `tools/index_signatures.py`
rebuilds it on every commit touching `src/`, so anything hand-added to the artifact is gone by
the next commit.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX = REPO_ROOT / "docs" / "index.json"


def index() -> dict:
    return json.loads(INDEX.read_text(encoding="utf-8"))


def test_the_map_exists_and_is_not_empty():
    """A guard that can quietly reduce to nothing is worse than an absent one."""
    data = index()
    assert data.get("modules"), "docs/index.json lists no modules"


def test_the_map_declares_what_it_is():
    """The first thing a reader meets must say what this file is for."""
    about = index().get("about")
    assert about, (
        "docs/index.json carries no `about` field. It lists every module and function in the "
        "engine, and a catalogue that size reads as an API unless it says otherwise. "
        "Add it in tools/index_signatures.py, which generates this file."
    )


def test_the_map_says_it_is_not_an_api():
    """The two readings to forestall: a surface for projects, and a surface for tests."""
    about = " ".join(str(v) for v in index().get("about", {}).values()).lower()

    assert "not an api" in about or "not a public api" in about, (
        "`about` must say plainly that this is not an API — the inference a reader makes by "
        "default, and the one that costs most to undo."
    )
    assert "test" in about, (
        "`about` must speak to tests. A test written against a function found here couples the "
        "suite to an internal that carries no compatibility promise; "
        "docs/ai-context/project/rules.md rule 1 says a step is exercised through the object "
        "model or the CLI."
    )
    assert "sp" in about, (
        "`about` must name the surface that *is* supported, or it only says what not to do."
    )
