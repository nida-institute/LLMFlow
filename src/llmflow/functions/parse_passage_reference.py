def parse_passage_reference(passage_ref):
    """Parse passage reference and determine source text (WLC or SBLGNT)"""

    # Initialize variables
    citation = passage_ref
    book = None
    start_chapter = None
    start_verse = None
    end_chapter = None
    end_verse = None
    passage_text = None

    # Determine testament and source
    if any(
        book in passage_ref
        for book in [
            "Matthew",
            "Mark",
            "Luke",
            "John",
            "Acts",
            "Romans",
            "Corinthians",
            "Galatians",
            "Ephesians",
            "Philippians",
            "Colossians",
            "Thessalonians",
            "Timothy",
            "Titus",
            "Philemon",
            "Hebrews",
            "James",
            "Peter",
            "Jude",
            "Revelation",
        ]
    ):
        testament = "NT"
        source_text = "SBLGNT"
    else:
        testament = "OT"
        source_text = "WLC"

    # Parse the reference (existing logic)
    # TODO: Add actual parsing logic here
    passage_text = f"Text for {passage_ref}"

    return {
        "citation": citation,
        "book": book,
        "start_chapter": start_chapter,
        "start_verse": start_verse,
        "end_chapter": end_chapter,
        "end_verse": end_verse,
        "testament": testament,
        "source_text": source_text,
        "passage_text": passage_text,
    }
