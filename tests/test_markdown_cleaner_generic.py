import pytest
from llmflow.utils.markdown_cleaner import clean_markdown


def test_basic_headings_and_paragraphs():
    raw = "# Title\n\nParagraph text."
    out = clean_markdown(raw)
    assert out == raw  # canonical already; should remain unchanged


def test_trailing_newline_is_removed_only_if_added():
    raw = "# Title\n\nParagraph."
    out = clean_markdown(raw)
    assert not out.endswith("\n")
    # If input already had trailing newline, mdformat may keep it; cleaner rstrip removes it
    raw2 = "# Title\n\nParagraph.\n"
    out2 = clean_markdown(raw2)
    assert not out2.endswith("\n")


def test_lists_bulleted_and_numbered():
    raw = "- item1\n-  item2\n\n1. one\n2.two"
    out = clean_markdown(raw)
    # Bulleted list normalized spacing
    assert "- item1" in out
    assert "- item2" in out
    # Ordered list may be canonicalized or indented
    assert "one" in out
    assert "two" in out
    assert ("1. one" in out) or ("1.  one" in out)
    # Accept possible leading spaces before the second item
    assert ("2. two" in out) or (" 2.two" in out) or ("   2.two" in out) or ("1. two" in out) or ("1.  two" in out)


def test_code_fence_preservation():
    raw = "```python\nprint('hello')\n```\n\nText after."
    out = clean_markdown(raw)
    assert "```python" in out
    assert "print('hello')" in out
    assert "```" in out
    assert "Text after." in out


def test_inline_code_and_emphasis():
    raw = "Use `code` and *emphasis* and **strong**."
    out = clean_markdown(raw)
    assert "Use `code`" in out
    assert "*emphasis*" in out
    assert "**strong**" in out


def test_blockquote_formatting():
    raw = "> Quote line\n> continuation"
    out = clean_markdown(raw)
    assert out.startswith("> Quote line")
    assert "\n> continuation" in out


def test_table_preservation():
    raw = (
        "| Col A | Col B |\n"
        "|-------|-------|\n"
        "|  1    |  2    |\n"
    )
    out = clean_markdown(raw)
    # mdformat may normalize spacing, but table structure must remain
    assert "| Col A | Col B |" in out
    assert "|---" in out  # alignment row normalized
    assert "| 1 | 2 |" in out or "| 1    |  2    |" in out


def test_html_block_preservation():
    raw = "<div>\n  <span>Inline HTML</span>\n</div>\n\nParagraph."
    out = clean_markdown(raw)
    assert "<div>" in out and "</div>" in out
    assert "<span>Inline HTML</span>" in out
    assert "Paragraph." in out


def test_mixed_content_complex():
    raw = (
        "# Title\n\n"
        "Intro paragraph.\n\n"
        "## Subheading\n\n"
        "- item A\n"
        "- item B\n\n"
        "1. first\n"
        "2. second\n\n"
        "```js\nconsole.log(1)\n```\n\n"
        "> Callout\n>\n> More\n"
    )
    out = clean_markdown(raw)
    # Headings
    assert "# Title" in out and "## Subheading" in out
    # Lists
    assert "- item A" in out and "- item B" in out
    # Ordered list items content preserved; numbering may be canonicalized
    assert "first" in out and "second" in out
    assert ("1. first" in out) or ("1.  first" in out)
    assert ("2. second" in out) or ("1. second" in out) or ("1.  second" in out)
    # Code
    assert "```js" in out and "console.log(1)" in out
    # Blockquote
    assert "> Callout" in out


def test_non_string_input_is_stringified():
    raw = {"key": "value", "n": 1}
    out = clean_markdown(raw)
    # mdformat will serialize as a code block or text; ensure it returns a string
    assert isinstance(out, str)
    assert "key" in out and "value" in out


def test_preserves_multiple_scenes_and_repeated_headings():
    raw = (
        "# Scene: A\n\n"
        "### Step 1: Enter\n\n"
        "# Scene: B\n\n"
        "### Step 1: Enter\n"
    )
    out = clean_markdown(raw)
    # Repeated headings are allowed; ensure both remain
    assert out.count("### Step 1: Enter") == 2
    assert out.count("# Scene:") == 2