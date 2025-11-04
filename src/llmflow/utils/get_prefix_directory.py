import unicodedata
from pathlib import Path


def strip_diacritics(text: str) -> str:
    """
    Remove diacritics/accents from Unicode text.
    """
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')


def get_prefix_directory(
    filename: str,
    prefix_length: int | None = 2,
    prefix_delimiter: str | None = None,
) -> str:
    """
    Derive grouping directory name from filename (without extension).

    If prefix_delimiter provided, split on it and take first segment.
    Else take first prefix_length characters (default 2).
    Diacritics removed, lowercased.

    Examples:
        get_prefix_directory("σύ.md") -> "συ"
        get_prefix_directory("Ἀβαδδών.md", prefix_length=3) -> "αβα"
        get_prefix_directory("G1234_ἀγάπη.md", prefix_delimiter="_") -> "g1234"
        get_prefix_directory("H5921_עַל.md", prefix_delimiter="_") -> "h5921"
    """
    stem = Path(filename).stem
    normalized = strip_diacritics(stem)

    if prefix_delimiter:
        prefix = normalized.split(prefix_delimiter, 1)[0]
    else:
        length = prefix_length if prefix_length is not None else 2
        prefix = normalized[:length]

    return prefix.lower()