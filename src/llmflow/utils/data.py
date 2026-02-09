"""Data manipulation and transformation utilities"""

import json
from pathlib import Path

import yaml

from llmflow.modules.logger import Logger

# Use unified logger - Logger() returns the logger instance directly
logger = Logger()


def create_json_dictionary(**kwargs):
    """
    Create a JSON dictionary from keyword arguments.
    Used to combine multiple pipeline variables into a single JSON structure.
    """
    logger.debug(f"create_json_dictionary called with {len(kwargs)} arguments")
    for key, value in kwargs.items():
        logger.debug(
            f"  {key}: {type(value)} with {len(value) if hasattr(value, '__len__') else 'unknown'} items"
        )
        if hasattr(value, "__len__") and len(value) > 0:
            logger.debug(
                f"    First item: {value[0][:100] if isinstance(value[0], str) else value[0]}"
            )

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
        {key: value for key, value in zip(keys, values)} for values in zip(*arrays)
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
        "step4": "Connections (What's at the Heart for Us?)",
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
            'book_code': str,           # "PSA", "LUK", "JHN" (USFM 3.0 book code)
            'chapter': int,             # 23, 12, 3
            'chapter_padded': str,      # "023", "012", "003"
            'start_verse': int,         # 1, 5, 16
            'end_verse': int,           # last_verse, 19, 16
            'is_whole_chapter': bool,   # True, False, False
            'filename_prefix': str,     # "019023001-019023176", "042012005-042012019", "043003016-043003016"
            'display_name': str,        # "Psalm-23", "Luke-12-5-19", "John-3-16"
            'canonical_reference': str  # "Psalm 23:1-176", "Luke 12:5-19", "John 3:16"
        }
    """

    # Bible book mapping with disambiguation (number, display_name, USFM_code)
    book_numbers = {
        # Old Testament
        "genesis": ("01", "Genesis", "GEN"),
        "gen": ("01", "Genesis", "GEN"),
        "ge": ("01", "Genesis", "GEN"),
        "gn": ("01", "Genesis", "GEN"),
        "exodus": ("02", "Exodus", "EXO"),
        "exod": ("02", "Exodus", "EXO"),
        "exo": ("02", "Exodus", "EXO"),
        "ex": ("02", "Exodus", "EXO"),
        "leviticus": ("03", "Leviticus", "LEV"),
        "lev": ("03", "Leviticus", "LEV"),
        "le": ("03", "Leviticus", "LEV"),
        "lv": ("03", "Leviticus", "LEV"),
        "numbers": ("04", "Numbers", "NUM"),
        "num": ("04", "Numbers", "NUM"),
        "nu": ("04", "Numbers", "NUM"),
        "nm": ("04", "Numbers", "NUM"),
        "deuteronomy": ("05", "Deuteronomy", "DEU"),
        "deut": ("05", "Deuteronomy", "DEU"),
        "dt": ("05", "Deuteronomy", "DEU"),
        "de": ("05", "Deuteronomy", "DEU"),
        "joshua": ("06", "Joshua", "JOS"),
        "josh": ("06", "Joshua", "JOS"),
        "jos": ("06", "Joshua", "JOS"),
        "jsh": ("06", "Joshua", "JOS"),
        "judges": ("07", "Judges", "JDG"),
        "judg": ("07", "Judges", "JDG"),
        "jdg": ("07", "Judges", "JDG"),
        "jg": ("07", "Judges", "JDG"),
        "ruth": ("08", "Ruth", "RUT"),
        "rut": ("08", "Ruth", "RUT"),
        "ru": ("08", "Ruth", "RUT"),
        "rt": ("08", "Ruth", "RUT"),
        "1 samuel": ("09", "1 Samuel", "1SA"),
        "1sam": ("09", "1 Samuel", "1SA"),
        "1sa": ("09", "1 Samuel", "1SA"),
        "1s": ("09", "1 Samuel", "1SA"),
        "1 sam": ("09", "1 Samuel", "1SA"),
        "2 samuel": ("10", "2 Samuel", "2SA"),
        "2sam": ("10", "2 Samuel", "2SA"),
        "2sa": ("10", "2 Samuel", "2SA"),
        "2s": ("10", "2 Samuel", "2SA"),
        "2 sam": ("10", "2 Samuel", "2SA"),
        "1 kings": ("11", "1 Kings", "1KI"),
        "1kgs": ("11", "1 Kings", "1KI"),
        "1ki": ("11", "1 Kings", "1KI"),
        "1k": ("11", "1 Kings", "1KI"),
        "1 kgs": ("11", "1 Kings", "1KI"),
        "2 kings": ("12", "2 Kings", "2KI"),
        "2kgs": ("12", "2 Kings", "2KI"),
        "2ki": ("12", "2 Kings", "2KI"),
        "2k": ("12", "2 Kings", "2KI"),
        "2 kgs": ("12", "2 Kings", "2KI"),
        "1 chronicles": ("13", "1 Chronicles", "1CH"),
        "1chron": ("13", "1 Chronicles", "1CH"),
        "1chr": ("13", "1 Chronicles", "1CH"),
        "1ch": ("13", "1 Chronicles", "1CH"),
        "1 chr": ("13", "1 Chronicles", "1CH"),
        "2 chronicles": ("14", "2 Chronicles", "2CH"),
        "2chron": ("14", "2 Chronicles", "2CH"),
        "2chr": ("14", "2 Chronicles", "2CH"),
        "2ch": ("14", "2 Chronicles", "2CH"),
        "2 chr": ("14", "2 Chronicles", "2CH"),
        "ezra": ("15", "Ezra", "EZR"),
        "ezr": ("15", "Ezra", "EZR"),
        "nehemiah": ("16", "Nehemiah", "NEH"),
        "neh": ("16", "Nehemiah", "NEH"),
        "ne": ("16", "Nehemiah", "NEH"),
        "esther": ("17", "Esther", "EST"),
        "esth": ("17", "Esther", "EST"),
        "est": ("17", "Esther", "EST"),
        "es": ("17", "Esther", "EST"),
        "job": ("18", "Job", "JOB"),
        "jb": ("18", "Job", "JOB"),
        "psalms": ("19", "Psalms", "PSA"),
        "psalm": ("19", "Psalms", "PSA"),
        "ps": ("19", "Psalms", "PSA"),
        "psa": ("19", "Psalms", "PSA"),
        "pss": ("19", "Psalms", "PSA"),
        "proverbs": ("20", "Proverbs", "PRO"),
        "prov": ("20", "Proverbs", "PRO"),
        "pro": ("20", "Proverbs", "PRO"),
        "pr": ("20", "Proverbs", "PRO"),
        "ecclesiastes": ("21", "Ecclesiastes", "ECC"),
        "eccl": ("21", "Ecclesiastes", "ECC"),
        "ecc": ("21", "Ecclesiastes", "ECC"),
        "ec": ("21", "Ecclesiastes", "ECC"),
        "song of songs": ("22", "Song of Songs", "SNG"),
        "song": ("22", "Song of Songs", "SNG"),
        "sos": ("22", "Song of Songs", "SNG"),
        "so": ("22", "Song of Songs", "SNG"),
        "canticles": ("22", "Song of Songs", "SNG"),
        "cant": ("22", "Song of Songs", "SNG"),
        "isaiah": ("23", "Isaiah", "ISA"),
        "isa": ("23", "Isaiah", "ISA"),
        "is": ("23", "Isaiah", "ISA"),
        "jeremiah": ("24", "Jeremiah", "JER"),
        "jer": ("24", "Jeremiah", "JER"),
        "je": ("24", "Jeremiah", "JER"),
        "jr": ("24", "Jeremiah", "JER"),
        "lamentations": ("25", "Lamentations", "LAM"),
        "lam": ("25", "Lamentations", "LAM"),
        "la": ("25", "Lamentations", "LAM"),
        "ezekiel": ("26", "Ezekiel", "EZK"),
        "ezek": ("26", "Ezekiel", "EZK"),
        "eze": ("26", "Ezekiel", "EZK"),
        "daniel": ("27", "Daniel", "DAN"),
        "dan": ("27", "Daniel", "DAN"),
        "da": ("27", "Daniel", "DAN"),
        "dn": ("27", "Daniel", "DAN"),
        "hosea": ("28", "Hosea", "HOS"),
        "hos": ("28", "Hosea", "HOS"),
        "ho": ("28", "Hosea", "HOS"),
        "joel": ("29", "Joel", "JOL"),
        "joe": ("29", "Joel", "JOL"),
        "jl": ("29", "Joel", "JOL"),
        "amos": ("30", "Amos", "AMO"),
        "amo": ("30", "Amos", "AMO"),
        "am": ("30", "Amos", "AMO"),
        "obadiah": ("31", "Obadiah", "OBA"),
        "obad": ("31", "Obadiah", "OBA"),
        "ob": ("31", "Obadiah", "OBA"),
        "jonah": ("32", "Jonah", "JON"),
        "jon": ("32", "Jonah", "JON"),
        "jnh": ("32", "Jonah", "JON"),
        "micah": ("33", "Micah", "MIC"),
        "mic": ("33", "Micah", "MIC"),
        "mi": ("33", "Micah", "MIC"),
        "nahum": ("34", "Nahum", "NAM"),
        "nah": ("34", "Nahum", "NAM"),
        "na": ("34", "Nahum", "NAM"),
        "habakkuk": ("35", "Habakkuk", "HAB"),
        "hab": ("35", "Habakkuk", "HAB"),
        "hb": ("35", "Habakkuk", "HAB"),
        "zephaniah": ("36", "Zephaniah", "ZEP"),
        "zeph": ("36", "Zephaniah", "ZEP"),
        "zep": ("36", "Zephaniah", "ZEP"),
        "zp": ("36", "Zephaniah", "ZEP"),
        "haggai": ("37", "Haggai", "HAG"),
        "hag": ("37", "Haggai", "HAG"),
        "hg": ("37", "Haggai", "HAG"),
        "zechariah": ("38", "Zechariah", "ZEC"),
        "zech": ("38", "Zechariah", "ZEC"),
        "zec": ("38", "Zechariah", "ZEC"),
        "zc": ("38", "Zechariah", "ZEC"),
        "malachi": ("39", "Malachi", "MAL"),
        "mal": ("39", "Malachi", "MAL"),
        "ml": ("39", "Malachi", "MAL"),
        # New Testament
        "matthew": ("40", "Matthew", "MAT"),
        "matt": ("40", "Matthew", "MAT"),
        "mt": ("40", "Matthew", "MAT"),
        "mat": ("40", "Matthew", "MAT"),
        "mark": ("41", "Mark", "MRK"),
        "mar": ("41", "Mark", "MRK"),
        "mk": ("41", "Mark", "MRK"),
        "mr": ("41", "Mark", "MRK"),
        "luke": ("42", "Luke", "LUK"),
        "luk": ("42", "Luke", "LUK"),
        "lk": ("42", "Luke", "LUK"),
        "lu": ("42", "Luke", "LUK"),
        "john": ("43", "John", "JHN"),
        "joh": ("43", "John", "JHN"),
        "jn": ("43", "John", "JHN"),
        "jhn": ("43", "John", "JHN"),
        "acts": ("44", "Acts", "ACT"),
        "act": ("44", "Acts", "ACT"),
        "ac": ("44", "Acts", "ACT"),
        "romans": ("45", "Romans", "ROM"),
        "rom": ("45", "Romans", "ROM"),
        "ro": ("45", "Romans", "ROM"),
        "rm": ("45", "Romans", "ROM"),
        "1 corinthians": ("46", "1 Corinthians", "1CO"),
        "1cor": ("46", "1 Corinthians", "1CO"),
        "1co": ("46", "1 Corinthians", "1CO"),
        "1c": ("46", "1 Corinthians", "1CO"),
        "1 cor": ("46", "1 Corinthians", "1CO"),
        "2 corinthians": ("47", "2 Corinthians", "2CO"),
        "2cor": ("47", "2 Corinthians", "2CO"),
        "2co": ("47", "2 Corinthians", "2CO"),
        "2c": ("47", "2 Corinthians", "2CO"),
        "2 cor": ("47", "2 Corinthians", "2CO"),
        "galatians": ("48", "Galatians", "GAL"),
        "gal": ("48", "Galatians", "GAL"),
        "ga": ("48", "Galatians", "GAL"),
        "ephesians": ("49", "Ephesians", "EPH"),
        "eph": ("49", "Ephesians", "EPH"),
        "ep": ("49", "Ephesians", "EPH"),
        "philippians": ("50", "Philippians", "PHP"),
        "phil": ("50", "Philippians", "PHP"),
        "php": ("50", "Philippians", "PHP"),
        "phi": ("50", "Philippians", "PHP"),
        "colossians": ("51", "Colossians", "COL"),
        "col": ("51", "Colossians", "COL"),
        "co": ("51", "Colossians", "COL"),
        "1 thessalonians": ("52", "1 Thessalonians", "1TH"),
        "1thess": ("52", "1 Thessalonians", "1TH"),
        "1th": ("52", "1 Thessalonians", "1TH"),
        "1 thess": ("52", "1 Thessalonians", "1TH"),
        "1 th": ("52", "1 Thessalonians", "1TH"),
        "2 thessalonians": ("53", "2 Thessalonians", "2TH"),
        "2thess": ("53", "2 Thessalonians", "2TH"),
        "2th": ("53", "2 Thessalonians", "2TH"),
        "2 thess": ("53", "2 Thessalonians", "2TH"),
        "2 th": ("53", "2 Thessalonians", "2TH"),
        "1 timothy": ("54", "1 Timothy", "1TI"),
        "1tim": ("54", "1 Timothy", "1TI"),
        "1ti": ("54", "1 Timothy", "1TI"),
        "1 tim": ("54", "1 Timothy", "1TI"),
        "1 ti": ("54", "1 Timothy", "1TI"),
        "2 timothy": ("55", "2 Timothy", "2TI"),
        "2tim": ("55", "2 Timothy", "2TI"),
        "2ti": ("55", "2 Timothy", "2TI"),
        "2 tim": ("55", "2 Timothy", "2TI"),
        "2 ti": ("55", "2 Timothy", "2TI"),
        "titus": ("56", "Titus", "TIT"),
        "tit": ("56", "Titus", "TIT"),
        "ti": ("56", "Titus", "TIT"),
        "philemon": ("57", "Philemon", "PHM"),
        "philem": ("57", "Philemon", "PHM"),
        "phm": ("57", "Philemon", "PHM"),
        "phlm": ("57", "Philemon", "PHM"),
        "hebrews": ("58", "Hebrews", "HEB"),
        "heb": ("58", "Hebrews", "HEB"),
        "he": ("58", "Hebrews", "HEB"),
        "james": ("59", "James", "JAS"),
        "jas": ("59", "James", "JAS"),
        "jm": ("59", "James", "JAS"),
        "ja": ("59", "James", "JAS"),
        "1 peter": ("60", "1 Peter", "1PE"),
        "1pet": ("60", "1 Peter", "1PE"),
        "1pe": ("60", "1 Peter", "1PE"),
        "1pt": ("60", "1 Peter", "1PE"),
        "1p": ("60", "1 Peter", "1PE"),
        "1 pet": ("60", "1 Peter", "1PE"),
        "2 peter": ("61", "2 Peter", "2PE"),
        "2pet": ("61", "2 Peter", "2PE"),
        "2pe": ("61", "2 Peter", "2PE"),
        "2pt": ("61", "2 Peter", "2PE"),
        "2p": ("61", "2 Peter", "2PE"),
        "2 pet": ("61", "2 Peter", "2PE"),
        "1 john": ("62", "1 John", "1JN"),
        "1joh": ("62", "1 John", "1JN"),
        "1jn": ("62", "1 John", "1JN"),
        "1j": ("62", "1 John", "1JN"),
        "1 joh": ("62", "1 John", "1JN"),
        "1john": ("62", "1 John", "1JN"),
        "2 john": ("63", "2 John", "2JN"),
        "2joh": ("63", "2 John", "2JN"),
        "2jn": ("63", "2 John", "2JN"),
        "2j": ("63", "2 John", "2JN"),
        "2 joh": ("63", "2 John", "2JN"),
        "2john": ("63", "2 John", "2JN"),
        "3 john": ("64", "3 John", "3JN"),
        "3joh": ("64", "3 John", "3JN"),
        "3jn": ("64", "3 John", "3JN"),
        "3j": ("64", "3 John", "3JN"),
        "3 joh": ("64", "3 John", "3JN"),
        "3john": ("64", "3 John", "3JN"),
        "jude": ("65", "Jude", "JUD"),
        "jud": ("65", "Jude", "JUD"),
        "jd": ("65", "Jude", "JUD"),
        "revelation": ("66", "Revelation", "REV"),
        "rev": ("66", "Revelation", "REV"),
        "re": ("66", "Revelation", "REV"),
        "rv": ("66", "Revelation", "REV"),
    }

    # Approximate verse counts for whole chapters (you may want to make this more precise)
    chapter_verse_counts = {
        # This is a simplified mapping - you'd want a complete Bible verse count database
        "19": {  # Psalms
            1: 6,
            2: 12,
            3: 8,
            4: 8,
            5: 12,
            23: 6,  # Psalm 23 has 6 verses
            119: 176,  # Psalm 119 is the longest
            # Add more as needed, or use an external Bible API
        },
        "42": {  # Luke
            12: 59,  # Luke 12 has 59 verses
            # Add more as needed
        },
        "43": {  # John
            3: 36,  # John 3 has 36 verses
            # Add more as needed
        },
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

    # Validate input is not empty
    if not passage:
        raise ValueError("Bible reference cannot be empty")

    # Parse different formats
    patterns = [
        # "Luke 12:5-19", "John 3:16-20", "Song of Songs 1:1-5"
        # Accept both hyphen (-) and en-dash (–) for verse ranges
        r"([\w\s]+?)\s+(\d+):(\d+)[-–](\d+)",
        # "Luke 12:5", "John 3:16", "Song of Songs 1:1"
        r"([\w\s]+?)\s+(\d+):(\d+)",
        # "Psalm 23", "Luke 12", "Song of Songs 1" (whole chapter)
        r"([\w\s]+?)\s+(\d+)$",
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
                raise ValueError(
                    f"Unrecognized Bible book '{book_name_raw}' in passage '{original_passage}'"
                )

            book_number, book_display_name, book_code = book_info

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
                display_name = (
                    f"{book_display_name.replace(' ', '-')}-{chapter}-{start_verse}"
                )
                canonical_reference = f"{book_display_name} {chapter}:{start_verse}"
            else:
                display_name = f"{book_display_name.replace(' ', '-')}-{chapter}-{start_verse}-{end_verse}"
                canonical_reference = (
                    f"{book_display_name} {chapter}:{start_verse}-{end_verse}"
                )

            return {
                "book_name": book_display_name,
                "book_number": book_number,
                "book_code": book_code,
                "chapter": chapter,
                "chapter_padded": f"{chapter:03d}",
                "start_verse": start_verse,
                "end_verse": end_verse,
                "is_whole_chapter": is_whole_chapter,
                "filename_prefix": filename_prefix,
                "display_name": display_name,
                "canonical_reference": canonical_reference,
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
            "actual_type": type(actual).__name__,
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
            "summary": f"JSON comparison failed: {str(e)}",
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


def load_json(file_path):
    """Load JSON data from file with error handling and logging"""
    logger.debug(f"📖 Loading JSON from: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"✅ Successfully loaded JSON ({len(str(data))} chars)")
        return data
    except FileNotFoundError:
        logger.error(f"❌ JSON file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error loading JSON from {file_path}: {e}")
        raise


def load_yaml(file_path):
    """Load YAML data from file with error handling and logging"""
    logger.debug(f"📖 Loading YAML from: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logger.debug("✅ Successfully loaded YAML")
        return data
    except FileNotFoundError:
        logger.error(f"❌ YAML file not found: {file_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"❌ Invalid YAML in {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error loading YAML from {file_path}: {e}")
        raise


def save_yaml(data, file_path):
    """Save data as YAML file with error handling and logging"""
    logger.debug(f"💾 Saving YAML to: {file_path}")

    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
        logger.debug("✅ Successfully saved YAML")
    except Exception as e:
        logger.error(f"❌ Error saving YAML to {file_path}: {e}")
        raise


def merge_dicts(dict1, dict2, deep=True):
    """Merge two dictionaries with optional deep merging"""
    logger.debug(f"🔗 Merging dictionaries (deep={deep})")

    if not deep:
        result = dict1.copy()
        result.update(dict2)
        return result

    # Deep merge
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value, deep=True)
        else:
            result[key] = value

    logger.debug("✅ Dictionaries merged successfully")
    return result


def flatten_dict(nested_dict, separator="."):
    """Flatten a nested dictionary using dot notation"""
    logger.debug(f"📏 Flattening dictionary with separator '{separator}'")

    def _flatten(obj, parent_key=""):
        items = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                items.extend(_flatten(value, new_key).items())
        else:
            return {parent_key: obj}
        return dict(items)

    result = _flatten(nested_dict)
    logger.debug(f"✅ Dictionary flattened to {len(result)} keys")
    return result


def validate_data_structure(data, required_keys, optional_keys=None):
    """Validate that data contains required keys and log validation results"""
    logger.debug("🔍 Validating data structure")
    logger.debug(f"Required keys: {required_keys}")

    if optional_keys:
        logger.debug(f"Optional keys: {optional_keys}")

    errors = []
    warnings = []

    if not isinstance(data, dict):
        errors.append("Data must be a dictionary")
        logger.error("❌ Data is not a dictionary")
        return False, errors, warnings

    # Check required keys
    missing_required = [key for key in required_keys if key not in data]
    if missing_required:
        errors.extend([f"Missing required key: {key}" for key in missing_required])
        for key in missing_required:
            logger.error(f"❌ Missing required key: {key}")

    # Check for unexpected keys
    all_valid_keys = set(required_keys)
    if optional_keys:
        all_valid_keys.update(optional_keys)

    unexpected_keys = [key for key in data.keys() if key not in all_valid_keys]
    if unexpected_keys:
        warnings.extend([f"Unexpected key: {key}" for key in unexpected_keys])
        for key in unexpected_keys:
            logger.warning(f"⚠️  Unexpected key: {key}")

    is_valid = len(errors) == 0

    if is_valid:
        logger.debug("✅ Data structure validation passed")
    else:
        logger.error(f"❌ Data structure validation failed with {len(errors)} errors")

    return is_valid, errors, warnings


def identity(value):
    """
    Return the input value unchanged.

    Useful for testing, debugging, and passthrough operations where you need
    to pass data through a step without modification.

    Args:
        value: Any value to return unchanged

    Returns:
        The same value that was input
    """
    return value


def load_json_file(file_path):
    """
    Load and parse a JSON file.
    Used to read JSON data from files in pipeline steps.

    Args:
        file_path: Path to the JSON file to load

    Returns:
        Parsed JSON data (dict or list)
    """
    logger.debug(f"Loading JSON file: {file_path}")
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.debug(f"Loaded JSON data with {len(data) if hasattr(data, '__len__') else 'unknown'} items")
    return data


def echo_file_path(message):
    """
    Print a message to stdout for user visibility.
    Useful for echoing file paths so they can be command+clicked in terminal.

    Args:
        message (str): Message to print

    Returns:
        str: The same message (for pipeline chaining)
    """
    print(message)
    return message
