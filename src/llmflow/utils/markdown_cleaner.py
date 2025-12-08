from typing import Optional
from markdown_it import MarkdownIt
import mdformat


def clean_markdown(content: str, style: Optional[str] = None) -> str:
    """
    Normalize Markdown by parsing and re-serializing.

    - Parses with markdown-it-py to validate tokenization for any Markdown.
    - Formats with mdformat to produce canonical, consistent Markdown.
    - Preserves content semantics; does not apply domain-specific heuristics.
    - Only trims trailing newlines to avoid altering meaningful whitespace.

    Args:
        content: Raw markdown string
        style: Optional mdformat style (None uses default)

    Returns:
        Normalized markdown string
    """
    if not isinstance(content, str):
        content = str(content)

    # Validate tokenization for arbitrary Markdown
    md = MarkdownIt()
    md.parse(content)

    # Serialize to canonical Markdown
    formatted = mdformat.text(content, options={} if style is None else {"style": style})

    # Preserve content; only remove trailing newline mdformat adds by default
    return formatted.rstrip("\n")
