def parse_passage_reference(passage_ref):
    """Parse passage reference and determine source text (WLC or SBLGNT)"""

    # Determine testament and source
    if any(book in passage_ref for book in ['Matthew', 'Mark', 'Luke', 'John', 'Acts',
                                           'Romans', 'Corinthians', 'Galatians', 'Ephesians',
                                           'Philippians', 'Colossians', 'Thessalonians',
                                           'Timothy', 'Titus', 'Philemon', 'Hebrews',
                                           'James', 'Peter', 'John', 'Jude', 'Revelation']):
        testament = "NT"
        source_text = "SBLGNT"
    else:
        testament = "OT"
        source_text = "WLC"

    # Parse the reference (existing logic)
    # ... your existing parsing code ...

    return {
        "citation": citation,
        "book": book,
        "start_chapter": start_chapter,
        "start_verse": start_verse,
        "end_chapter": end_chapter,
        "end_verse": end_verse,
        "testament": testament,
        "source_text": source_text,
        "passage_text": passage_text  # Retrieved from appropriate source
    }