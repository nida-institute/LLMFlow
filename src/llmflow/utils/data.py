"""Data manipulation and transformation utilities"""

def create_json_dictionary(**kwargs):
    """
    Create a JSON dictionary from keyword arguments.
    Used to combine multiple pipeline variables into a single JSON structure.
    """
    import logging
    logger = logging.getLogger('llmflow.data')

    logger.debug(f"create_json_dictionary called with {len(kwargs)} arguments")
    for key, value in kwargs.items():
        logger.debug(f"  {key}: {type(value)} with {len(value) if hasattr(value, '__len__') else 'unknown'} items")
        if hasattr(value, '__len__') and len(value) > 0:
            logger.debug(f"    First item: {value[0][:100] if isinstance(value[0], str) else value[0]}")

    result = dict(kwargs)
    logger.debug(f"Returning dictionary with {len(result)} keys")

    return result

def interleave(json_structure, output_format=None):
    """
    Interleave arrays from a JSON structure using zip.

    Args:
        json_structure (dict): Dictionary with arrays as values
        output_format (str, optional): Output format ('json', 'markdown', etc.)

    Returns:
        list or str: Interleaved data as JSON structure or formatted string

    Example:
        interleave({"step1": ["a", "b"], "step2": ["c", "d"]})
        # Returns: [{"step1": "a", "step2": "c"}, {"step1": "b", "step2": "d"}]

        interleave({"step1": ["a", "b"], "step2": ["c", "d"]}, output_format="markdown")
        # Returns: Formatted Markdown string
    """
    if not json_structure:
        return [] if output_format != "markdown" else ""

    keys = list(json_structure.keys())
    arrays = list(json_structure.values())

    # Create the interleaved data structure
    interleaved_data = [
        {key: value for key, value in zip(keys, values)}
        for values in zip(*arrays)
    ]

    # Return based on output format
    if output_format == "markdown":
        return _format_as_markdown(interleaved_data)
    else:
        return interleaved_data

def _format_as_markdown(interleaved_data):
    """Convert interleaved data to Markdown format"""
    step_names = {
        "step1": "Senses (What's Happening?)",
        "step2": "Context (What's the Background?)",
        "step3": "Spiritual and Emotional Journey (What's at the Heart for Them?)",
        "step4": "Connections (What's at the Heart for Us?)"
    }

    markdown_sections = []

    for i, scene_data in enumerate(interleaved_data, 1):
        section_parts = [f"## Scene {i}\n"]

        for j, (step_key, content) in enumerate(scene_data.items(), 1):
            step_name = step_names.get(step_key, f"Step {j}")
            section_parts.append(f"### Step {j}: {step_name}")
            section_parts.append(content)
            section_parts.append("---\n")

        markdown_sections.append("\n\n".join(section_parts))

    return "\n\n".join(markdown_sections)

def flatten_structure(nested_dict, separator="_"):
    """Flatten nested dictionaries for pipeline processing"""
    # Implementation for complex data flattening
    pass

def validate_array_lengths(json_structure):
    """Ensure all arrays in structure have the same length"""
    # Implementation for data validation
    pass

def parse_bible_reference(passage):
    """
    Parse a Bible reference and return comprehensive range information.

    Args:
        passage (str): Bible reference like "Psalm 23", "Luke 12:5-19", "John 3:16"

    Returns:
        dict: {
            'book_name': str,           # "Psalm", "Luke", "John"
            'book_number': str,         # "19", "42", "43"
            'chapter': int,             # 23, 12, 3
            'start_verse': int,         # 1, 5, 16
            'end_verse': int,           # last_verse, 19, 16
            'is_whole_chapter': bool,   # True, False, False
            'filename_prefix': str,     # "019023001-019023176", "042012005-042012019", "043003016-043003016"
            'display_name': str,        # "Psalm-23", "Luke-12-5-19", "John-3-16"
            'canonical_reference': str  # "Psalm 23:1-176", "Luke 12:5-19", "John 3:16"
        }
    """

    # Bible book mapping with disambiguation
    book_numbers = {
        # Old Testament
        "genesis": ("01", "Genesis"), "gen": ("01", "Genesis"), "ge": ("01", "Genesis"), "gn": ("01", "Genesis"),
        "exodus": ("02", "Exodus"), "exod": ("02", "Exodus"), "exo": ("02", "Exodus"), "ex": ("02", "Exodus"),
        "leviticus": ("03", "Leviticus"), "lev": ("03", "Leviticus"), "le": ("03", "Leviticus"), "lv": ("03", "Leviticus"),
        "numbers": ("04", "Numbers"), "num": ("04", "Numbers"), "nu": ("04", "Numbers"), "nm": ("04", "Numbers"),
        "deuteronomy": ("05", "Deuteronomy"), "deut": ("05", "Deuteronomy"), "dt": ("05", "Deuteronomy"), "de": ("05", "Deuteronomy"),
        "joshua": ("06", "Joshua"), "josh": ("06", "Joshua"), "jos": ("06", "Joshua"), "jsh": ("06", "Joshua"),
        "judges": ("07", "Judges"), "judg": ("07", "Judges"), "jdg": ("07", "Judges"), "jg": ("07", "Judges"),
        "ruth": ("08", "Ruth"), "rut": ("08", "Ruth"), "ru": ("08", "Ruth"), "rt": ("08", "Ruth"),
        "1 samuel": ("09", "1 Samuel"), "1sam": ("09", "1 Samuel"), "1sa": ("09", "1 Samuel"), "1s": ("09", "1 Samuel"), "1 sam": ("09", "1 Samuel"),
        "2 samuel": ("10", "2 Samuel"), "2sam": ("10", "2 Samuel"), "2sa": ("10", "2 Samuel"), "2s": ("10", "2 Samuel"), "2 sam": ("10", "2 Samuel"),
        "1 kings": ("11", "1 Kings"), "1kgs": ("11", "1 Kings"), "1ki": ("11", "1 Kings"), "1k": ("11", "1 Kings"), "1 kgs": ("11", "1 Kings"),
        "2 kings": ("12", "2 Kings"), "2kgs": ("12", "2 Kings"), "2ki": ("12", "2 Kings"), "2k": ("12", "2 Kings"), "2 kgs": ("12", "2 Kings"),
        "1 chronicles": ("13", "1 Chronicles"), "1chron": ("13", "1 Chronicles"), "1chr": ("13", "1 Chronicles"), "1ch": ("13", "1 Chronicles"), "1 chr": ("13", "1 Chronicles"),
        "2 chronicles": ("14", "2 Chronicles"), "2chron": ("14", "2 Chronicles"), "2chr": ("14", "2 Chronicles"), "2ch": ("14", "2 Chronicles"), "2 chr": ("14", "2 Chronicles"),
        "ezra": ("15", "Ezra"), "ezr": ("15", "Ezra"),
        "nehemiah": ("16", "Nehemiah"), "neh": ("16", "Nehemiah"), "ne": ("16", "Nehemiah"),
        "esther": ("17", "Esther"), "esth": ("17", "Esther"), "est": ("17", "Esther"), "es": ("17", "Esther"),
        "job": ("18", "Job"), "jb": ("18", "Job"),
        "psalms": ("19", "Psalms"), "psalm": ("19", "Psalms"), "ps": ("19", "Psalms"), "psa": ("19", "Psalms"), "pss": ("19", "Psalms"),
        "proverbs": ("20", "Proverbs"), "prov": ("20", "Proverbs"), "pro": ("20", "Proverbs"), "pr": ("20", "Proverbs"),
        "ecclesiastes": ("21", "Ecclesiastes"), "eccl": ("21", "Ecclesiastes"), "ecc": ("21", "Ecclesiastes"), "ec": ("21", "Ecclesiastes"),
        "song of songs": ("22", "Song of Songs"), "song": ("22", "Song of Songs"), "sos": ("22", "Song of Songs"), "so": ("22", "Song of Songs"), "canticles": ("22", "Song of Songs"), "cant": ("22", "Song of Songs"),
        "isaiah": ("23", "Isaiah"), "isa": ("23", "Isaiah"), "is": ("23", "Isaiah"),
        "jeremiah": ("24", "Jeremiah"), "jer": ("24", "Jeremiah"), "je": ("24", "Jeremiah"), "jr": ("24", "Jeremiah"),
        "lamentations": ("25", "Lamentations"), "lam": ("25", "Lamentations"), "la": ("25", "Lamentations"),
        "ezekiel": ("26", "Ezekiel"), "ezek": ("26", "Ezekiel"), "eze": ("26", "Ezekiel"),
        "daniel": ("27", "Daniel"), "dan": ("27", "Daniel"), "da": ("27", "Daniel"), "dn": ("27", "Daniel"),
        "hosea": ("28", "Hosea"), "hos": ("28", "Hosea"), "ho": ("28", "Hosea"),
        "joel": ("29", "Joel"), "joe": ("29", "Joel"), "jl": ("29", "Joel"),
        "amos": ("30", "Amos"), "amo": ("30", "Amos"), "am": ("30", "Amos"),
        "obadiah": ("31", "Obadiah"), "obad": ("31", "Obadiah"), "ob": ("31", "Obadiah"),
        "jonah": ("32", "Jonah"), "jon": ("32", "Jonah"), "jnh": ("32", "Jonah"),
        "micah": ("33", "Micah"), "mic": ("33", "Micah"), "mi": ("33", "Micah"),
        "nahum": ("34", "Nahum"), "nah": ("34", "Nahum"), "na": ("34", "Nahum"),
        "habakkuk": ("35", "Habakkuk"), "hab": ("35", "Habakkuk"), "hb": ("35", "Habakkuk"),
        "zephaniah": ("36", "Zephaniah"), "zeph": ("36", "Zephaniah"), "zep": ("36", "Zephaniah"), "zp": ("36", "Zephaniah"),
        "haggai": ("37", "Haggai"), "hag": ("37", "Haggai"), "hg": ("37", "Haggai"),
        "zechariah": ("38", "Zechariah"), "zech": ("38", "Zechariah"), "zec": ("38", "Zechariah"), "zc": ("38", "Zechariah"),
        "malachi": ("39", "Malachi"), "mal": ("39", "Malachi"), "ml": ("39", "Malachi"),

        # New Testament
        "matthew": ("40", "Matthew"), "matt": ("40", "Matthew"), "mt": ("40", "Matthew"), "mat": ("40", "Matthew"),
        "mark": ("41", "Mark"), "mar": ("41", "Mark"), "mk": ("41", "Mark"), "mr": ("41", "Mark"),
        "luke": ("42", "Luke"), "luk": ("42", "Luke"), "lk": ("42", "Luke"), "lu": ("42", "Luke"),
        "john": ("43", "John"), "joh": ("43", "John"), "jn": ("43", "John"), "jhn": ("43", "John"),
        "acts": ("44", "Acts"), "act": ("44", "Acts"), "ac": ("44", "Acts"),
        "romans": ("45", "Romans"), "rom": ("45", "Romans"), "ro": ("45", "Romans"), "rm": ("45", "Romans"),
        "1 corinthians": ("46", "1 Corinthians"), "1cor": ("46", "1 Corinthians"), "1co": ("46", "1 Corinthians"), "1c": ("46", "1 Corinthians"), "1 cor": ("46", "1 Corinthians"),
        "2 corinthians": ("47", "2 Corinthians"), "2cor": ("47", "2 Corinthians"), "2co": ("47", "2 Corinthians"), "2c": ("47", "2 Corinthians"), "2 cor": ("47", "2 Corinthians"),
        "galatians": ("48", "Galatians"), "gal": ("48", "Galatians"), "ga": ("48", "Galatians"),
        "ephesians": ("49", "Ephesians"), "eph": ("49", "Ephesians"), "ep": ("49", "Ephesians"),
        "philippians": ("50", "Philippians"), "phil": ("50", "Philippians"), "php": ("50", "Philippians"), "phi": ("50", "Philippians"),
        "colossians": ("51", "Colossians"), "col": ("51", "Colossians"), "co": ("51", "Colossians"),
        "1 thessalonians": ("52", "1 Thessalonians"), "1thess": ("52", "1 Thessalonians"), "1th": ("52", "1 Thessalonians"), "1 thess": ("52", "1 Thessalonians"), "1 th": ("52", "1 Thessalonians"),
        "2 thessalonians": ("53", "2 Thessalonians"), "2thess": ("53", "2 Thessalonians"), "2th": ("53", "2 Thessalonians"), "2 thess": ("53", "2 Thessalonians"), "2 th": ("53", "2 Thessalonians"),
        "1 timothy": ("54", "1 Timothy"), "1tim": ("54", "1 Timothy"), "1ti": ("54", "1 Timothy"), "1 tim": ("54", "1 Timothy"), "1 ti": ("54", "1 Timothy"),
        "2 timothy": ("55", "2 Timothy"), "2tim": ("55", "2 Timothy"), "2ti": ("55", "2 Timothy"), "2 tim": ("55", "2 Timothy"), "2 ti": ("55", "2 Timothy"),
        "titus": ("56", "Titus"), "tit": ("56", "Titus"), "ti": ("56", "Titus"),
        "philemon": ("57", "Philemon"), "philem": ("57", "Philemon"), "phm": ("57", "Philemon"), "phlm": ("57", "Philemon"),
        "hebrews": ("58", "Hebrews"), "heb": ("58", "Hebrews"), "he": ("58", "Hebrews"),
        "james": ("59", "James"), "jas": ("59", "James"), "jm": ("59", "James"), "ja": ("59", "James"),
        "1 peter": ("60", "1 Peter"), "1pet": ("60", "1 Peter"), "1pe": ("60", "1 Peter"), "1pt": ("60", "1 Peter"), "1p": ("60", "1 Peter"), "1 pet": ("60", "1 Peter"),
        "2 peter": ("61", "2 Peter"), "2pet": ("61", "2 Peter"), "2pe": ("61", "2 Peter"), "2pt": ("61", "2 Peter"), "2p": ("61", "2 Peter"), "2 pet": ("61", "2 Peter"),
        "1 john": ("62", "1 John"), "1joh": ("62", "1 John"), "1jn": ("62", "1 John"), "1j": ("62", "1 John"), "1 joh": ("62", "1 John"), "1john": ("62", "1 John"),
        "2 john": ("63", "2 John"), "2joh": ("63", "2 John"), "2jn": ("63", "2 John"), "2j": ("63", "2 John"), "2 joh": ("63", "2 John"), "2john": ("63", "2 John"),
        "3 john": ("64", "3 John"), "3joh": ("64", "3 John"), "3jn": ("64", "3 John"), "3j": ("64", "3 John"), "3 joh": ("64", "3 John"), "3john": ("64", "3 John"),
        "jude": ("65", "Jude"), "jud": ("65", "Jude"), "jd": ("65", "Jude"),
        "revelation": ("66", "Revelation"), "rev": ("66", "Revelation"), "re": ("66", "Revelation"), "rv": ("66", "Revelation")
    }

    # Approximate verse counts for whole chapters (you may want to make this more precise)
    chapter_verse_counts = {
        # This is a simplified mapping - you'd want a complete Bible verse count database
        "19": {  # Psalms
            23: 176,  # Psalm 23 has 176 verses (it's the longest)
            1: 6, 2: 12, 3: 8, 4: 8, 5: 12,
            # Add more as needed, or use an external Bible API
        },
        "42": {  # Luke
            12: 59,  # Luke 12 has 59 verses
            # Add more as needed
        },
        "43": {  # John
            3: 36,   # John 3 has 36 verses
            # Add more as needed
        }
    }

    # Check for ambiguous abbreviations
    ambiguous_abbreviations = {
        "ph": ["Philippians", "Philemon"],
        "p": ["Psalms", "Proverbs", "1 Peter", "2 Peter", "Philippians", "Philemon"],
    }

    import re

    # Normalize input
    original_passage = passage
    passage = passage.lower().strip()

    # Parse different formats
    patterns = [
        # "Luke 12:5-19", "John 3:16-20"
        r"(\w+(?:\s+\w+)?)\s+(\d+):(\d+)-(\d+)",
        # "Luke 12:5", "John 3:16"
        r"(\w+(?:\s+\w+)?)\s+(\d+):(\d+)",
        # "Psalm 23", "Luke 12" (whole chapter)
        r"(\w+(?:\s+\w+)?)\s+(\d+)",
    ]

    for i, pattern in enumerate(patterns):
        match = re.match(pattern, passage)
        if match:
            book_name_raw = match.group(1).strip()
            chapter = int(match.group(2))

            # Check for ambiguous abbreviations
            if book_name_raw in ambiguous_abbreviations:
                possible_books = ambiguous_abbreviations[book_name_raw]
                if len(possible_books) > 1:
                    raise ValueError(
                        f"Ambiguous book abbreviation '{book_name_raw}' in passage '{original_passage}'. "
                        f"Could match: {', '.join(possible_books)}. "
                        f"Please use a more specific abbreviation."
                    )

            # Look up book
            book_info = book_numbers.get(book_name_raw)
            if not book_info:
                book_info = book_numbers.get(book_name_raw.replace(" ", ""))

            if not book_info:
                raise ValueError(f"Unrecognized Bible book '{book_name_raw}' in passage '{original_passage}'")

            book_number, book_display_name = book_info

            if i == 0:  # Range format "Luke 12:5-19"
                start_verse = int(match.group(3))
                end_verse = int(match.group(4))
                is_whole_chapter = False

            elif i == 1:  # Single verse "John 3:16"
                start_verse = int(match.group(3))
                end_verse = start_verse
                is_whole_chapter = False

            else:  # Whole chapter "Psalm 23"
                start_verse = 1
                # Look up or estimate end verse
                end_verse = chapter_verse_counts.get(book_number, {}).get(chapter, 999)
                is_whole_chapter = True

            # Build result
            start_code = f"{book_number}{chapter:03d}{start_verse:03d}"
            end_code = f"{book_number}{chapter:03d}{end_verse:03d}"
            filename_prefix = f"{start_code}-{end_code}"

            # Create display name
            if is_whole_chapter:
                display_name = f"{book_display_name.replace(' ', '-')}-{chapter}"
                canonical_reference = f"{book_display_name} {chapter}:1-{end_verse}"
            elif start_verse == end_verse:
                display_name = f"{book_display_name.replace(' ', '-')}-{chapter}-{start_verse}"
                canonical_reference = f"{book_display_name} {chapter}:{start_verse}"
            else:
                display_name = f"{book_display_name.replace(' ', '-')}-{chapter}-{start_verse}-{end_verse}"
                canonical_reference = f"{book_display_name} {chapter}:{start_verse}-{end_verse}"

            return {
                'book_name': book_display_name,
                'book_number': book_number,
                'chapter': chapter,
                'start_verse': start_verse,
                'end_verse': end_verse,
                'is_whole_chapter': is_whole_chapter,
                'filename_prefix': filename_prefix,
                'display_name': display_name,
                'canonical_reference': canonical_reference
            }

    # If we get here, the passage wasn't recognized
    raise ValueError(f"Could not parse Bible reference '{original_passage}'")

def simple_json_compare(expected, actual, test_name="comparison"):
    """
    Simple comparison using JSON serialization - works with standard library only.
    """
    import json

    try:
        # Serialize both to JSON strings for comparison
        expected_json = json.dumps(expected, sort_keys=True, indent=2)
        actual_json = json.dumps(actual, sort_keys=True, indent=2)

        is_identical = expected_json == actual_json

        result = {
            "test_name": test_name,
            "passed": is_identical,
            "structures_identical": is_identical,
            "expected_type": type(expected).__name__,
            "actual_type": type(actual).__name__
        }

        if is_identical:
            result["summary"] = "Structures are identical ✅"
        else:
            result["summary"] = "Structures differ ❌"
            # Show first difference if strings are short enough
            if len(expected_json) < 1000 and len(actual_json) < 1000:
                result["expected_json"] = expected_json
                result["actual_json"] = actual_json
            else:
                result["note"] = "Structures too large to display in full"

        return result

    except Exception as e:
        return {
            "test_name": test_name,
            "passed": False,
            "error": str(e),
            "summary": f"JSON comparison failed: {str(e)}"
        }

def flatten_json_to_markdown(data):
    """
    Recursively flatten any dict or list to Markdown by concatenating all values in document order.
    No headings, bullets, or formatting are added.
    """
    result = []

    def walk(val):
        if isinstance(val, dict):
            for v in val.values():
                walk(v)
        elif isinstance(val, list):
            for item in val:
                walk(item)
        else:
            result.append(str(val))

    walk(data)
    return "\n".join(result)
