import mdformat


def clean_markdown(content: str) -> str:
    """
    Normalize / clean markdown by parsing and re-serializing it.

    This uses mdformat, which parses the markdown and then
    pretty-prints it back to a canonical Markdown form.

    Args:
        content: Raw markdown string

    Returns:
        Normalized markdown string
    """
    # mdformat parses to an AST and then serializes back to markdown
    return mdformat.text(content).strip()
