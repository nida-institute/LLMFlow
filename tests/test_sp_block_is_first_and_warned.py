"""sp's delimited block carries a warning and sits at the top of the file.

Ruled 2026-08-25. Scope, cause and wording: `project/plans/design-one-source-for-shipped-files.md`.
"""
from __future__ import annotations

from llmflow.cli_utils import (
    ASSISTANT_RULES_POINTER,
    CLAUDE_MD_LLMFLOW_BLOCK,
    CURSORRULES_LLMFLOW_BLOCK,
    LLMFLOW_BLOCK_BEGIN,
    LLMFLOW_BLOCK_END,
    SP_BLOCK_WARNING,
    WINDSURFRULES_LLMFLOW_BLOCK,
    _upsert_delimited_block,
    read_delimited_block,
)

BLOCKS = {
    "CLAUDE_MD_LLMFLOW_BLOCK": CLAUDE_MD_LLMFLOW_BLOCK,
    "CURSORRULES_LLMFLOW_BLOCK": CURSORRULES_LLMFLOW_BLOCK,
    "WINDSURFRULES_LLMFLOW_BLOCK": WINDSURFRULES_LLMFLOW_BLOCK,
    "ASSISTANT_RULES_POINTER": ASSISTANT_RULES_POINTER,
}


def test_every_block_carries_the_warning():
    for name, content in BLOCKS.items():
        assert SP_BLOCK_WARNING in content, f"{name} ships without the warning"


def test_the_warning_says_what_it_must_say():
    """Three claims, because a warning that omits any of them is not the one ruled."""
    w = SP_BLOCK_WARNING
    assert "ONLY `sp` MAY WRITE HERE" in w          # who owns it
    assert "lost" in w                               # edits are destroyed
    assert "breaks how the system behaves" in w      # and the system misbehaves
    assert "below" in w                              # where the project's content goes


def test_the_warning_is_written_once():
    """One copy of the text, composed into the four, so they cannot drift apart."""
    for name, content in BLOCKS.items():
        assert content.count("ONLY `sp` MAY WRITE HERE") == 1, f"{name} repeats the warning"


def _begin() -> str:
    return LLMFLOW_BLOCK_BEGIN.format(name="workflow")


def test_the_block_is_prepended_to_a_file_that_already_has_content(tmp_path):
    f = tmp_path / ".cursorrules"
    f.write_text("# the project's own rules\nkeep me\n", encoding="utf-8")

    _upsert_delimited_block(f, "workflow", "SP CONTENT")

    text = f.read_text(encoding="utf-8")
    assert text.startswith(_begin()), "sp's block must be the first thing in the file"
    assert "# the project's own rules" in text and "keep me" in text
    assert text.index(_begin()) < text.index("# the project's own rules")


def test_a_block_at_the_bottom_is_relocated_to_the_top(tmp_path):
    """*"relocate on next run"* — including files sp itself appended to earlier."""
    f = tmp_path / "CLAUDE.md"
    f.write_text(
        "# the human's file\ntheir content\n\n"
        + _begin() + "\nOLD SP CONTENT\n" + LLMFLOW_BLOCK_END.format(name="workflow") + "\n",
        encoding="utf-8",
    )

    _upsert_delimited_block(f, "workflow", "NEW SP CONTENT")

    text = f.read_text(encoding="utf-8")
    assert text.startswith(_begin())
    assert read_delimited_block(f, "workflow") == "NEW SP CONTENT"
    assert "OLD SP CONTENT" not in text, "the old region must be moved, not duplicated"
    assert text.count(_begin()) == 1, "exactly one block"
    assert "# the human's file" in text and "their content" in text


def test_an_unchanged_block_already_in_place_is_left_alone(tmp_path):
    f = tmp_path / ".windsurfrules"
    _upsert_delimited_block(f, "workflow", "SP CONTENT")
    before = f.read_text(encoding="utf-8")

    action = _upsert_delimited_block(f, "workflow", "SP CONTENT")

    assert action == "unchanged"
    assert f.read_text(encoding="utf-8") == before


def test_a_new_file_gets_only_the_block(tmp_path):
    f = tmp_path / ".cursorrules"
    assert _upsert_delimited_block(f, "workflow", "SP CONTENT") == "created"
    assert f.read_text(encoding="utf-8").startswith(_begin())
