"""Data manipulation and transformation utilities"""

import json
from pathlib import Path

import yaml

from llmflow import books as _books
from llmflow.modules.logger import Logger
from llmflow.utils import versification as _versification

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
            first = next(iter(value.values())) if isinstance(value, dict) else value[0]
            logger.debug(
                f"    First item: {first[:100] if isinstance(first, str) else first}"
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


#: The scheme a reference is assumed to be written in when the caller names none. This is the
#: request side — a fact about the person who typed it — and is deliberately unlike the source
#: side, where an edition's scheme is a property of the text and has no default at all.
DEFAULT_REQUEST_VERSIFICATION = "eng"


def _measuring_scheme(book_code, requested, passage, *, extent_needed):
    """The scheme to measure *book_code* with, and whether *requested* itself defines it.

    A scheme that does not list the book cannot answer. Where nothing needs measuring the gap is
    recorded and parsing continues; where an extent is needed, one other scheme defining the book
    is used and more than one is refused, because choosing between them would be a guess.

    The returned scheme is always usable for `.name`; the flag says whether it actually defines
    the book, and a caller must not range-check against it when the flag is False.
    """
    scheme = _versification.packaged_scheme(requested)
    if book_code in scheme.max_verses:
        return scheme, True

    others = [
        name
        for name in _versification.packaged_scheme_names()
        if book_code in _versification.packaged_scheme(name).max_verses
    ]
    logger.warning(
        f"{book_code} is not defined in versification {requested!r}"
        + (f"; it is defined in {', '.join(others)}." if others else " or in any shipped scheme.")
    )
    if extent_needed and len(others) == 1:
        return _versification.packaged_scheme(others[0]), False
    if not extent_needed:
        # Nothing to measure, so the requested scheme is returned as it stands; the caller reads
        # the False and skips a range check the scheme has no data to make.
        return scheme, False
    raise ValueError(
        f"{passage!r}: {book_code} is not defined in versification {requested!r}, so the extent "
        f"of a whole chapter cannot be resolved. "
        + (
            f"It is defined in {', '.join(others)} — name one with `versification=`."
            if others
            else "No shipped scheme defines it."
        )
    )


def _check_reference(scheme, book_code, pairs, passage):
    """Refuse a chapter or verse the scheme does not have. Verse 0 is a superscription."""
    chapters = scheme.max_verses.get(book_code) or []
    for chapter, verse in pairs:
        if not 1 <= chapter <= len(chapters):
            raise ValueError(
                f"{passage!r}: {book_code} has {len(chapters)} chapters in versification "
                f"{scheme.name!r}, so there is no chapter {chapter}."
            )
        if verse is None:
            continue
        last = int(chapters[chapter - 1])
        if not 0 <= verse <= last:
            raise ValueError(
                f"{passage!r}: {book_code} {chapter} has {last} verses in versification "
                f"{scheme.name!r}, so there is no verse {verse}."
            )


def parse_bible_reference(
    passage,
    versification=DEFAULT_REQUEST_VERSIFICATION,
    source_versification=None,
):
    """
    Parse a Bible reference and return comprehensive range information.

    Args:
        passage (str): Bible reference like "Psalm 23", "Luke 12:5-19", "John 3:16"

    Args:
        passage (str): "Psalm 23", "Luke 12:5-19", "John 3:16", "MRK 3:14", "Romans"
        versification (str): the scheme the *request* is written in. Defaults to `eng`.
        source_versification (str): the scheme an edition's text is numbered in, recorded on the
            result and never resolved against — this function has no edition to read.

    Returns:
        dict: {
            'book_name': str,                 # "Psalms", "Luke", "John"
            'book_number': str,               # "19", "42", "43"
            'book_code': str,                 # "PSA", "LUK", "JHN" (USFM 3.0 book code)
            'chapter': int,                   # 23, 12, 3
            'chapter_padded': str,            # "023", "012", "003"
            'start_verse': int,               # 1, 5, 16
            'end_verse': int,                 # resolved from maxVerses for a whole chapter
            'end_chapter': int,
            'is_whole_chapter': bool,
            'filename_prefix': str,           # "19023001-19023006"
            'display_name': str,              # "Psalms-23", "Luke-12-5-19", "John-3-16"
            'canonical_reference': str,       # "Psalms 23:1-6", "Luke 12:5-19", "John 3:16"
            'testament': str,                 # "OT" | "NT"
            'original_language': str,         # "Hebrew" | "Greek"
            'requested_versification': str,   # the scheme the reference was read in
            'source_versification': str|None, # echoed from the argument
            'extent_versification': str|None, # where end_verse came from; None if not resolved
            'book_in_versification': bool,    # False when the scheme does not define the book
        }

    Raises:
        ValueError: for an unrecognised book, an ambiguous abbreviation, a chapter or verse the
            scheme does not have, or a whole chapter in a scheme that does not define the book.
    """

    # Book names, codes, numbers and testaments live in `data/book-names.json`, read through
    # `llmflow.books`. They used to be 271 lines of dict literal here — unreachable to the read
    # path, which grew its own shape-matching parser and turned `Mark` into book `MARK`.
    import re

    # Normalize input
    original_passage = passage
    passage = passage.lower().strip()

    # Validate input is not empty
    if not passage:
        raise ValueError("Bible reference cannot be empty")

    # Parse different formats
    patterns = [
        # Cross-chapter range: "Genesis 1:1-2:3", "Matthew 5:1-7:29"
        # Accept both hyphen (-) and en-dash (–) for verse ranges
        r"([\w\s]+?)\s+(\d+):(\d+)[-–](\d+):(\d+)",
        # Same-chapter range: "Luke 12:5-19", "John 3:16-20", "Song of Songs 1:1-5"
        r"([\w\s]+?)\s+(\d+):(\d+)[-–](\d+)",
        # Single verse: "Luke 12:5", "John 3:16", "Song of Songs 1:1"
        r"([\w\s]+?)\s+(\d+):(\d+)",
        # Whole chapter: "Psalm 23", "Luke 12", "Song of Songs 1"
        r"([\w\s]+?)\s+(\d+)$",
    ]

    for i, pattern in enumerate(patterns):
        match = re.match(pattern, passage)
        if match:
            book_name_raw = match.group(1).strip()
            chapter = int(match.group(2))

            try:
                book_code = _books.resolve(book_name_raw)
            except _books.AmbiguousBook as ambiguous:
                raise ValueError(
                    f"Ambiguous book abbreviation '{book_name_raw}' in passage "
                    f"'{original_passage}'. {ambiguous}"
                )

            if not book_code:
                raise ValueError(
                    f"Unrecognized Bible book '{book_name_raw}' in passage '{original_passage}'"
                )

            book_number = _books.number(book_code)
            book_display_name = _books.name(book_code)
            if not book_number or not book_display_name:
                raise ValueError(
                    f"Bible book {book_code!r} in passage '{original_passage}' has no name or "
                    f"number declared, so a filename and a canonical reference cannot be built."
                )

            if i == 0:  # Cross-chapter range "Genesis 1:1-2:3"
                start_verse = int(match.group(3))
                end_chapter = int(match.group(4))
                end_verse = int(match.group(5))
                is_whole_chapter = False

            elif i == 1:  # Same-chapter range "Luke 12:5-19"
                start_verse = int(match.group(3))
                end_verse = int(match.group(4))
                end_chapter = chapter  # Same as start chapter
                is_whole_chapter = False

            elif i == 2:  # Single verse "John 3:16"
                start_verse = int(match.group(3))
                end_verse = start_verse
                end_chapter = chapter
                is_whole_chapter = False

            else:  # Whole chapter "Psalm 23"
                start_verse = 1
                end_verse = None  # resolved from the scheme below
                end_chapter = chapter
                is_whole_chapter = True

            scheme, book_known = _measuring_scheme(
                book_code, versification, original_passage, extent_needed=is_whole_chapter
            )
            extent_from = None
            if is_whole_chapter:
                _check_reference(scheme, book_code, [(chapter, None)], original_passage)
                end_verse = int(scheme.max_verses[book_code][chapter - 1])
                extent_from = scheme.name
            elif book_known:
                _check_reference(
                    scheme,
                    book_code,
                    [(chapter, start_verse), (end_chapter, end_verse)],
                    original_passage,
                )

            # Build result
            start_code = f"{book_number}{chapter:03d}{start_verse:03d}"
            end_code = f"{book_number}{end_chapter:03d}{end_verse:03d}"
            filename_prefix = f"{start_code}-{end_code}"

            # Create display name and canonical reference
            if is_whole_chapter:
                display_name = f"{book_display_name.replace(' ', '-')}-{chapter}"
                canonical_reference = f"{book_display_name} {chapter}:1-{end_verse}"
            elif end_chapter != chapter:  # Cross-chapter
                display_name = f"{book_display_name.replace(' ', '-')}-{chapter}-{start_verse}-{end_chapter}-{end_verse}"
                canonical_reference = f"{book_display_name} {chapter}:{start_verse}-{end_chapter}:{end_verse}"
            elif start_verse == end_verse:  # Single verse
                display_name = (
                    f"{book_display_name.replace(' ', '-')}-{chapter}-{start_verse}"
                )
                canonical_reference = f"{book_display_name} {chapter}:{start_verse}"
            else:  # Same-chapter range
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
                "end_chapter": end_chapter,
                "is_whole_chapter": is_whole_chapter,
                "filename_prefix": filename_prefix,
                "display_name": display_name,
                "canonical_reference": canonical_reference,
                "testament": _books.testament(book_code),
                "original_language": _books.original_language(book_code),
                "requested_versification": versification,
                "source_versification": source_versification,
                "extent_versification": extent_from,
                "book_in_versification": book_known,
            }

    # Last resort: try matching the entire input as a book name (whole-book reference)
    # e.g. "1 John", "Romans", "Revelation"
    try:
        book_code = _books.resolve(passage)
    except _books.AmbiguousBook:
        book_code = None
    entry = _books.entry(book_code) if book_code else None
    if book_code and entry and entry.get("number") and entry.get("name"):
        book_number = entry["number"]
        book_display_name = entry["name"]
        filename_prefix = f"{book_number}_book"
        _, book_known = _measuring_scheme(
            book_code, versification, original_passage, extent_needed=False
        )
        return {
            "book_name": book_display_name,
            "book_number": book_number,
            "book_code": book_code,
            "chapter": None,
            "chapter_padded": None,
            "start_verse": 1,
            "end_verse": None,
            "end_chapter": None,
            "is_whole_chapter": False,
            "is_whole_book": True,
            "filename_prefix": filename_prefix,
            "display_name": book_display_name.replace(" ", "-"),
            "canonical_reference": book_display_name,
            "testament": _books.testament(book_code),
            "original_language": _books.original_language(book_code),
            "requested_versification": versification,
            "source_versification": source_versification,
            "extent_versification": None,
            "book_in_versification": book_known,
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


def load_text_file(file_path):
    """
    Load a plain-text or Markdown file and return its contents as a string.

    Useful for injecting static context (e.g. a Markdown prompt fragment,
    a template, or a reference document) into a pipeline step.

    Args:
        file_path: Path to the text file (.txt, .md, or any plain-text format)

    Returns:
        str: Full file contents as a Unicode string
    """
    logger.debug(f"Loading text file: {file_path}")
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    logger.debug(f"Loaded text file ({len(content)} chars)")
    return content


def load_csv_file(file_path, delimiter=","):
    """
    Load a CSV (or TSV) file and return the rows as a list of dicts.

    Each row is a dict keyed by the header row. Values are always strings —
    convert them downstream if you need numbers. Compatible with `for-each`.

    Args:
        file_path: Path to the CSV/TSV file
        delimiter: Field delimiter (default: ','; use '\\t' for TSV)

    Returns:
        list[dict]: One dict per data row; empty list if the file has no data rows
    """
    import csv as _csv

    logger.debug(f"Loading CSV file: {file_path} (delimiter={repr(delimiter)})")
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = _csv.DictReader(f, delimiter=delimiter)
        rows = list(reader)

    logger.debug(f"Loaded {len(rows)} rows from CSV")
    return rows


def load_xml_file(file_path):
    """
    Load and parse an XML or USX file using lxml, returning the root element.

    The returned lxml _Element supports XPath, attribute access, and full
    tree traversal. Use with llmflow.utils.xml.xpath_get() or directly in
    plugin steps.

    Raises lxml.etree.XMLSyntaxError for malformed XML (not caught — let it
    surface so pipeline authors see the real parse error).

    Args:
        file_path: Path to the XML/USX/TEI file

    Returns:
        lxml.etree._Element: Parsed root element
    """
    from lxml import etree  # type: ignore[attr-defined]

    logger.debug(f"Loading XML file: {file_path}")
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"XML file not found: {file_path}")

    tree = etree.parse(str(path))
    root = tree.getroot()
    logger.debug(f"Loaded XML: root tag <{root.tag}>")
    return root


# ---------------------------------------------------------------------------
# USFM / USX / USJ loaders (Paratext project support)
# ---------------------------------------------------------------------------

# Canonical USFM book order keyed by 3-letter code.
# Numbers are LLMFlow-internal sort keys only — never exposed to callers.
# Source: USFM 3.x canonical book list (Protestant + deuterocanonical).
_USFM_BOOK_ORDER = {
    "GEN": 1, "EXO": 2, "LEV": 3, "NUM": 4, "DEU": 5,
    "JOS": 6, "JDG": 7, "RUT": 8, "1SA": 9, "2SA": 10,
    "1KI": 11, "2KI": 12, "1CH": 13, "2CH": 14, "EZR": 15,
    "NEH": 16, "EST": 17, "JOB": 18, "PSA": 19, "PRO": 20,
    "ECC": 21, "SNG": 22, "ISA": 23, "JER": 24, "LAM": 25,
    "EZK": 26, "DAN": 27, "HOS": 28, "JOL": 29, "AMO": 30,
    "OBA": 31, "JON": 32, "MIC": 33, "NAM": 34, "HAB": 35,
    "ZEP": 36, "HAG": 37, "ZEC": 38, "MAL": 39,
    # Deuterocanonical / apocryphal
    "TOB": 40, "JDT": 41, "ESG": 42, "WIS": 43, "SIR": 44,
    "BAR": 45, "LJE": 46, "S3Y": 47, "SUS": 48, "BEL": 49,
    "1MA": 50, "2MA": 51, "3MA": 52, "4MA": 53, "1ES": 54,
    "2ES": 55, "MAN": 56, "PS2": 57, "ODA": 58, "PSS": 59,
    "EZA": 60,
    # NT
    "MAT": 61, "MRK": 62, "LUK": 63, "JHN": 64, "ACT": 65,
    "ROM": 66, "1CO": 67, "2CO": 68, "GAL": 69, "EPH": 70,
    "PHP": 71, "COL": 72, "1TH": 73, "2TH": 74, "1TI": 75,
    "2TI": 76, "TIT": 77, "PHM": 78, "HEB": 79, "JAS": 80,
    "1PE": 81, "2PE": 82, "1JN": 83, "2JN": 84, "3JN": 85,
    "JUD": 86, "REV": 87,
}


def _usfm_book_sort_key(code: str) -> int:
    return _USFM_BOOK_ORDER.get(code.upper(), 9999)


def _scan_usfm_project(base_dir: str, project_name: str):
    """
    Scan a Paratext project directory for USFM files.

    Returns list of (book_code, file_path) tuples.
    Raises FileNotFoundError if the project directory does not exist.
    """
    project_dir = Path(base_dir) / project_name
    if not project_dir.exists():
        raise FileNotFoundError(
            f"Paratext project directory not found: {project_dir}"
        )

    from usfmtc import readFile

    results = []
    for f in sorted(project_dir.iterdir()):
        if f.suffix.lower() in (".sfm", ".usfm"):
            try:
                usx = readFile(str(f))
                if usx is None:
                    continue
                code = usx.book
                if code:
                    results.append((code.upper(), f, usx))
            except Exception as exc:
                logger.warning(f"⚠️  Skipping {f.name}: {exc}")
    return results


def _usx_to_element(usx_obj):
    """Convert a usfmtc USX object to an lxml _Element."""
    from lxml import etree  # type: ignore[attr-defined]
    xml_str = usx_obj.outUsx()
    if xml_str is None:
        raise ValueError("usfmtc returned no USX output")
    if isinstance(xml_str, str):
        xml_str = xml_str.encode("utf-8")
    return etree.fromstring(xml_str)


def _usx_to_usj(usx_obj) -> dict:
    """Convert a usfmtc USX object to a USJ dict."""
    return usx_obj.outUsj()


def _format_result(usx_obj, format: str):
    fmt = format.lower()
    if fmt == "usx":
        return _usx_to_element(usx_obj)
    elif fmt == "usj":
        return _usx_to_usj(usx_obj)
    else:
        raise ValueError(
            f"Invalid format '{format}': must be 'usx' or 'usj'"
        )


def list_usfm_books(base_dir: str, project_name: str) -> list:
    """
    List book codes found in a Paratext project directory.

    Returns book codes sorted in canonical USFM order (GEN → REV,
    deuterocanonicals after MAL, unknown codes at the end).
    Book codes are always 3-letter uppercase strings (e.g. "LUK", "GEN").

    Args:
        base_dir: Parent directory containing Paratext projects.
        project_name: Name of the Paratext project subdirectory.

    Returns:
        Sorted list of 3-letter USFM book codes present in the project.

    Raises:
        FileNotFoundError: If the project directory does not exist.
    """
    entries = _scan_usfm_project(base_dir, project_name)
    codes = [code for code, _, _ in entries]
    return sorted(codes, key=_usfm_book_sort_key)


def load_usfm_book(base_dir: str, project_name: str, book: str, format: str):
    """
    Load a single book from a Paratext project.

    Args:
        base_dir: Parent directory containing Paratext projects.
        project_name: Name of the Paratext project subdirectory.
        book: 3-letter USFM book code (e.g. "LUK").
        format: "usx" returns lxml _Element; "usj" returns dict.

    Returns:
        lxml _Element (usx) or dict (usj).

    Raises:
        FileNotFoundError: If the project directory does not exist.
        ValueError: If the book is not found in the project, or format is invalid.
    """
    entries = _scan_usfm_project(base_dir, project_name)
    book_upper = book.upper()
    for code, _, usx_obj in entries:
        if code == book_upper:
            logger.debug(f"Loading USFM book {book_upper} as {format}")
            return _format_result(usx_obj, format)
    raise ValueError(
        f"Book '{book_upper}' not found in project '{project_name}' "
        f"under '{base_dir}'"
    )


def _parse_passage(passage: str):
    """
    Parse a passage string into (book, chapter, start_verse, end_verse).

    Supported formats:
        "LUK"        → ("LUK", None, None, None)   whole book
        "LUK 1"      → ("LUK", 1,    None, None)   whole chapter
        "LUK 1:3"    → ("LUK", 1,    3,    3)       single verse
        "LUK 1:1-10" → ("LUK", 1,    1,    10)      verse range (inclusive)

    Returns (book_code, chapter_or_None, start_verse_or_None, end_verse_or_None).
    """
    parts = passage.strip().split()
    if not parts:
        raise ValueError("Empty passage string")

    book = parts[0].upper()

    if len(parts) == 1:
        return book, None, None, None

    chapter_part = parts[1]
    if ":" not in chapter_part:
        try:
            chapter = int(chapter_part)
        except ValueError:
            raise ValueError(f"Cannot parse chapter from passage: '{passage}'")
        return book, chapter, None, None

    # Verse reference: "1:3" or "1:1-10"
    ch_str, verse_str = chapter_part.split(":", 1)
    try:
        chapter = int(ch_str)
    except ValueError:
        raise ValueError(f"Cannot parse chapter from passage: '{passage}'")

    if "-" in verse_str:
        v_start_str, v_end_str = verse_str.split("-", 1)
    else:
        v_start_str = v_end_str = verse_str

    try:
        start_verse = int(v_start_str)
        end_verse = int(v_end_str)
    except ValueError:
        raise ValueError(f"Cannot parse verse range from passage: '{passage}'")

    if start_verse > end_verse:
        raise ValueError(
            f"Start verse {start_verse} is greater than end verse {end_verse} "
            f"in passage: '{passage}'"
        )

    return book, chapter, start_verse, end_verse


def _extract_chapter_usj(usj: dict, chapter: int) -> dict:
    """
    Extract a single chapter from a USJ dict by chapter number.

    Returns a new USJ dict whose content contains only the nodes
    belonging to the requested chapter.
    """
    content = usj.get("content", [])
    in_chapter = False
    chapter_content = []

    for item in content:
        if not isinstance(item, dict):
            if in_chapter:
                chapter_content.append(item)
            continue

        marker = item.get("type") or item.get("marker")

        if marker == "chapter":
            num = item.get("number") or item.get("sid", "").split(" ")[-1]
            try:
                this_chapter = int(str(num).split(":")[0])
            except (ValueError, TypeError):
                this_chapter = None

            if this_chapter == chapter:
                in_chapter = True
                chapter_content.append(item)
            elif in_chapter:
                # Hit the next chapter — stop
                break
        else:
            if in_chapter:
                chapter_content.append(item)

    return {
        "type": "USJ",
        "version": usj.get("version", "3.1"),
        "content": chapter_content,
    }


def _verse_number(item) -> int | None:
    """Extract a verse number from a USJ verse marker dict, or None."""
    if not isinstance(item, dict):
        return None
    if item.get("type") == "verse" or item.get("marker") == "v":
        raw = item.get("number") or item.get("sid", "").split(":")[-1].split("-")[0]
        try:
            return int(str(raw).split("-")[0])
        except (ValueError, TypeError):
            return None
    return None


def _filter_para_content(content: list, start_verse: int, end_verse: int) -> list:
    """
    Filter a para's content list to items belonging to verses [start_verse, end_verse].

    Verse markers reset the current verse number; text/inline nodes following a
    verse marker belong to that verse.  Items before any verse marker (e.g. a
    leading section-head) are excluded.
    """
    current_verse = None
    result = []
    for item in content:
        v = _verse_number(item)
        if v is not None:
            current_verse = v
        if current_verse is not None and start_verse <= current_verse <= end_verse:
            result.append(item)
        elif current_verse is not None and current_verse > end_verse:
            break
    return result


def _extract_verse_range_usj(chapter_usj: dict, start_verse: int, end_verse: int) -> dict:
    """
    Extract verses [start_verse, end_verse] (inclusive) from a single-chapter USJ dict.

    The chapter marker and any pre-verse paragraph-level nodes (headings, etc.) that
    appear before the first requested verse are preserved.  Para nodes whose filtered
    content is empty are dropped.
    """
    content = chapter_usj.get("content", [])
    result_content = []
    found_any_verse = False

    for item in content:
        if not isinstance(item, dict):
            # Raw string at chapter level — keep if before verses start
            if not found_any_verse:
                result_content.append(item)
            continue

        marker = item.get("type") or item.get("marker")

        if marker == "chapter":
            result_content.append(item)
            continue

        # Para-level node: filter its content array
        if "content" in item:
            filtered = _filter_para_content(item["content"], start_verse, end_verse)
            if filtered:
                found_any_verse = True
                result_content.append({**item, "content": filtered})
        else:
            # Para node with no content (empty para marker): keep if before verses
            if not found_any_verse:
                result_content.append(item)

    return {
        "type": "USJ",
        "version": chapter_usj.get("version", "3.1"),
        "content": result_content,
    }


def load_usfm_passage(base_dir: str, project_name: str, passage: str, format: str):
    """
    Load a passage from a Paratext project by reference string.

    Supported formats:
        "LUK"        — whole book
        "LUK 1"      — whole chapter 1
        "LUK 1:3"    — single verse
        "LUK 1:1-10" — verse range (inclusive)

    Args:
        base_dir: Parent directory containing Paratext projects.
        project_name: Name of the Paratext project subdirectory.
        passage: Passage reference string.
        format: "usx" returns lxml _Element; "usj" returns dict.

    Returns:
        lxml _Element (usx) or dict (usj) containing the requested content.

    Raises:
        FileNotFoundError: If the project directory does not exist.
        ValueError: If the book is not found or the passage string is invalid.
    """
    book, chapter, start_verse, end_verse = _parse_passage(passage)

    if chapter is None:
        return load_usfm_book(base_dir, project_name, book, format)

    # Load the full book as USJ, extract the chapter
    usj = load_usfm_book(base_dir, project_name, book, format="usj")
    chapter_usj = _extract_chapter_usj(usj, chapter)

    # Further filter to verse range if requested
    if start_verse is not None and end_verse is not None:
        chapter_usj = _extract_verse_range_usj(chapter_usj, start_verse, end_verse)

    if format.lower() == "usj":
        return chapter_usj

    # Convert extracted USJ back to USX element
    import json
    from usfmtc import USX as _USX
    usx_obj = _USX.fromUsj(json.dumps(chapter_usj))
    return _usx_to_element(usx_obj)


def export_usx(base_dir: str, project_name: str, output_dir: str) -> str:
    """
    Export all books in a Paratext project to USX 3.1 files.

    Output filenames preserve the project's original numeric prefix
    (e.g. "42LUK.sfm" → "42LUK.usx") for round-trip compatibility.

    Args:
        base_dir: Parent directory containing Paratext projects.
        project_name: Name of the Paratext project subdirectory.
        output_dir: Directory to write .usx files into (created if needed).

    Returns:
        output_dir as a string.

    Raises:
        FileNotFoundError: If the project directory does not exist.
    """
    entries = _scan_usfm_project(base_dir, project_name)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for code, src_path, usx_obj in entries:
        # Preserve the project's original filename prefix, change extension to .usx
        stem = src_path.stem  # e.g. "42LUK"
        out_path = out / f"{stem}.usx"
        logger.debug(f"Exporting {code} → {out_path}")
        xml_str = usx_obj.outUsx()
        if xml_str is not None:
            if isinstance(xml_str, str):
                xml_str = xml_str.encode("utf-8")
            out_path.write_bytes(xml_str)

    logger.info(f"✅ Exported {len(entries)} book(s) to {output_dir}")
    return output_dir


def load_usfm_project(base_dir: str, project_name: str, format: str = "usx") -> dict:
    """
    Load all books from a Paratext project eagerly.

    Args:
        base_dir: Parent directory containing Paratext projects.
        project_name: Name of the Paratext project subdirectory.
        format: "usx" returns lxml _Element values; "usj" returns dict values.

    Returns:
        Dict mapping 3-letter USFM book codes to parsed content
        (lxml _Element for "usx", dict for "usj").

    Raises:
        FileNotFoundError: If the project directory does not exist.
        ValueError: If format is invalid.
    """
    entries = _scan_usfm_project(base_dir, project_name)
    return {code: _format_result(usx_obj, format) for code, _, usx_obj in entries}


def serialize_usx(content) -> str | bool | None:
    """
    Serialize scripture content to USX XML string.

    Args:
        content: lxml _Element (USX) or dict (USJ).

    Returns:
        USX XML as a unicode string.
    """
    from lxml.etree import _Element, tostring
    if isinstance(content, _Element):
        return tostring(content, encoding="unicode", pretty_print=True)
    # USJ dict path
    import json
    from usfmtc import USX as _USX
    usx_obj = _USX.fromUsj(json.dumps(content))
    return usx_obj.outUsx()


def serialize_usfm(content) -> str | bool | None:
    """
    Serialize scripture content to USFM text.

    Args:
        content: lxml _Element (USX) or dict (USJ).

    Returns:
        USFM as a unicode string.
    """
    from usfmtc import USX as _USX
    from lxml.etree import _Element, tostring
    if isinstance(content, _Element):
        xml_str = tostring(content, encoding="unicode")
        usx_obj = _USX.fromUsx(xml_str)
        if usx_obj is None:
            return None
        return usx_obj.outUsfm()
    # USJ dict path
    import json
    usx_obj = _USX.fromUsj(json.dumps(content))
    return usx_obj.outUsfm()


def get_paratext_metadata(base_dir: str, project_name: str) -> dict:
    """
    Read Paratext project metadata from Settings.xml.

    Extracts key project information including language name, ISO code,
    full project name, and other metadata useful for translation workflows.

    Args:
        base_dir: Parent directory containing Paratext projects.
        project_name: Name of the Paratext project subdirectory.

    Returns:
        Dict with metadata fields:
            - language_name: Full language name (e.g. "Cebuano")
            - language_iso: ISO 639-3 code (e.g. "ceb")
            - full_name: Full project name
            - Additional fields as found in Settings.xml

        Returns empty dict if Settings.xml not found or cannot be parsed.

    Example:
        >>> meta = get_paratext_metadata("/path/to/paratext", "cebAPDv4")
        >>> meta['language_name']
        'Cebuano'
        >>> meta['language_iso']
        'ceb'
    """
    from lxml import etree  # type: ignore[attr-defined]

    project_dir = Path(base_dir) / project_name
    settings_path = project_dir / "Settings.xml"

    if not settings_path.exists():
        logger.warning(f"⚠️  Settings.xml not found in {project_dir}")
        return {}

    try:
        tree = etree.parse(str(settings_path))
        root = tree.getroot()

        metadata = {}

        # Map Paratext XML elements to metadata keys
        field_mappings = {
            'LanguageName': 'language_name',
            'LanguageIsoCode': 'language_iso',
            'FullName': 'full_name',
            'Abbreviation': 'abbreviation',
            'Versification': 'versification',
            'Copyright': 'copyright',
        }

        for xml_field, key in field_mappings.items():
            elem = root.find(xml_field)
            if elem is not None and elem.text:
                metadata[key] = elem.text.strip()

        logger.debug(f"Loaded metadata for {project_name}: {metadata.get('language_name', 'unknown')}")
        return metadata

    except Exception as exc:
        logger.warning(f"⚠️  Could not parse Settings.xml for {project_name}: {exc}")
        return {}


def load_project_file(base_dir: str, project_name: str, file: str, required: bool = True):
    """
    Load a metadata file from a Paratext project directory.

    Auto-detects format by file extension:
    - .json → returns dict (parsed JSON)
    - .xml → returns lxml.etree._Element (parsed XML)

    Args:
        base_dir: Paratext projects base directory
        project_name: Project subdirectory name
        file: Filename to load (e.g., "Settings.xml", "metadata.json")
        required: If False, return None when the file is absent instead of raising.
                  The project directory itself must still exist.

    Returns:
        dict for JSON files, lxml.etree._Element for XML files, or None if
        required=False and the file does not exist.

    Raises:
        FileNotFoundError: If project directory doesn't exist, or file doesn't
                           exist when required=True (default).
        ValueError: If file extension is not .json or .xml

    Example:
        >>> settings = load_project_file("/paratext", "cebAPDv4", "Settings.xml")
        >>> lang = settings.find('.//LanguageName').text

        >>> burrito = load_project_file("/paratext", "cebAPDv4", "metadata.json")
        >>> lang = burrito['languages'][0]['name']['en']

        >>> meta = load_project_file("/paratext", "proj", "metadata.json", required=False)
        >>> lang_tag = meta['languages'][0]['tag'] if meta else None
    """
    import json
    from lxml import etree  # type: ignore[attr-defined]

    project_dir = Path(base_dir) / project_name
    file_path = project_dir / file

    # Check project directory exists
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    # Check file exists
    if not file_path.exists():
        if not required:
            return None
        raise FileNotFoundError(f"File not found: {file_path}")

    # Auto-detect format by extension
    ext = file_path.suffix.lower()

    if ext == '.json':
        # Parse and return JSON as dict
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    elif ext == '.xml':
        # Parse and return XML as lxml Element
        tree = etree.parse(str(file_path))
        return tree.getroot()

    else:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            f"Only .json and .xml files are supported."
        )


def xpath_text(element, path: str):
    """
    Extract text content from an XML element using XPath.

    Args:
        element: lxml.etree._Element to query
        path: XPath query string (e.g., ".//LanguageName/text()")

    Returns:
        str: Text content of first matching node, or None if not found

    Example:
        >>> settings = load_project_file("/paratext", "project", "Settings.xml")
        >>> lang = xpath_text(settings, ".//LanguageName/text()")
        'Cebuano'
        >>> iso = xpath_text(settings, ".//LanguageIsoCode/text()")
        'ceb'
    """
    result = element.xpath(path)

    if result:
        # XPath with /text() returns list of strings
        # Return first match
        return result[0] if isinstance(result, list) else result

    return None


# ---------------------------------------------------------------------------
# Tabular filtering — shared by load_tsv, load_csv, and the tsv plugin
# ---------------------------------------------------------------------------

import re as _re

_EQ_RE = _re.compile(r'^(\w+)\s*==\s*[\'"]([^\'"]*)[\'"]$')
_STARTSWITH_RE = _re.compile(r'^(\w+)\s+startswith\s+[\'"]([^\'"]*)[\'"]$')
_USFM_RE = _re.compile(r'^(book|chapter|verse|word)\((\w+)\)\s*==\s*[\'"]([^\'"]*)[\'"]$')


def _extract_usfm_part(cell: str, part: str) -> str:
    """Extract book/chapter/verse/word component from a USFM ref like 'PHM 1:10!3'."""
    try:
        book, cv = cell.split(" ", 1)
        if part == "book":
            return book
        cv_part, word = (cv.split("!", 1) if "!" in cv else (cv, ""))
        chapter, verse = cv_part.split(":", 1)
        if part == "chapter":
            return chapter
        if part == "verse":
            return verse
        if part == "word":
            return word
    except (ValueError, AttributeError):
        pass
    return ""


def _parse_tabular_where(where_expr: str) -> list[tuple[str, str, str, str]]:
    """Parse a where expression into (extractor, column, operator, value) tuples.

    Supported forms (joined by 'and'):
        column == 'value'
        column startswith 'prefix'
        book(column) == 'value'
        chapter(column) == 'value'
        verse(column) == 'value'
        word(column) == 'value'
    """
    conditions = []
    for atom in (a.strip() for a in where_expr.split(" and ")):
        m = _USFM_RE.match(atom)
        if m:
            conditions.append((m.group(1), m.group(2), "==", m.group(3)))
            continue
        m = _EQ_RE.match(atom)
        if m:
            conditions.append(("", m.group(1), "==", m.group(2)))
            continue
        m = _STARTSWITH_RE.match(atom)
        if m:
            conditions.append(("", m.group(1), "startswith", m.group(2)))
            continue
        raise ValueError(
            f"cannot parse where condition: {atom!r}. "
            "Supported: column == 'value'  |  column startswith 'prefix'  |  "
            "book/chapter/verse/word(column) == 'value'  (joined by 'and')"
        )
    return conditions


def _matches_tabular_row(row: dict, extractor: str, col: str, op: str, val: str) -> bool:
    """Test one parsed condition against a row dict."""
    cell = row.get(col, "")
    if extractor:
        cell = _extract_usfm_part(cell, extractor)
    if op == "==":
        return cell == val
    if op == "startswith":
        return cell.startswith(val)
    return False


def apply_tabular_filters(rows: list[dict], step: dict) -> list[dict]:
    """Apply where/limit/offset/columns filtering to a list of row dicts.

    Args:
        rows:  Loaded tabular data as list of dicts (one dict per row).
        step:  Step config dict. Recognized keys:
                 where   — filter expression string
                 limit   — max rows to return (applied after where)
                 offset  — rows to skip (applied after where)
                 columns — list of column names to project

    Returns:
        Filtered list of dicts.
    """
    from llmflow.modules.logger import Logger
    logger = Logger()

    where = step.get("where")
    limit = step.get("limit")
    offset = int(step.get("offset", 0))
    columns = step.get("columns")

    if columns and rows:
        fieldnames = list(rows[0].keys())
        unknown = [c for c in columns if c not in fieldnames]
        if unknown:
            raise ValueError(
                f"unknown columns: {unknown}. Available: {fieldnames}"
            )

    if where:
        conditions = _parse_tabular_where(where)
        # Warn once per condition if the column is missing from the data
        if rows:
            fieldnames = list(rows[0].keys())
            for _ext, col, _op, _val in conditions:
                if col not in fieldnames:
                    logger.warning(
                        f"where condition references unknown column {col!r} — no rows will match"
                    )
                    return []
        rows = [r for r in rows if all(
            _matches_tabular_row(r, ext, col, op, val)
            for ext, col, op, val in conditions
        )]

    if offset:
        rows = rows[offset:]

    if limit is not None:
        rows = rows[:int(limit)]

    if columns:
        rows = [{k: r[k] for k in columns} for r in rows]

    return rows


# ---------------------------------------------------------------------------
# XML XPath filtering — used by load_xml step
# ---------------------------------------------------------------------------

def apply_xml_xpath(element, step: dict):
    """Apply an optional xpath: filter to a loaded lxml element.

    Args:
        element:  Root lxml _Element returned by load_xml_file.
        step:     Step config dict. Recognized keys:
                    xpath         — XPath expression (optional)
                    namespaces    — prefix→URI mapping for namespace-aware XPath
                    output_format — "element" (default), "xml-string", or "text"

    Returns:
        If xpath is absent: the element unchanged.
        If xpath is present: a list of results in the requested output_format.
    """
    xpath_expr = step.get("xpath")
    if not xpath_expr:
        return element

    from lxml import etree  # type: ignore[attr-defined]

    namespaces = step.get("namespaces") or {}
    output_format = step.get("output_format", "element")

    results = element.xpath(xpath_expr, namespaces=namespaces)

    if output_format == "text":
        out = []
        for item in results:
            if isinstance(item, str):
                out.append(item)
            elif hasattr(item, "text"):
                out.append(item.text or "")
            else:
                out.append(str(item))
        return out

    if output_format == "xml-string":
        return [etree.tostring(item, encoding="unicode") for item in results]

    # Default: "element" — return lxml elements as-is
    return list(results)


# ---------------------------------------------------------------------------
# JSON/YAML key extraction — used by load_json and load_yaml steps
# ---------------------------------------------------------------------------

def apply_key_extract(data, step: dict):
    """Extract a nested value from loaded JSON/YAML data by dot-path key.

    Args:
        data:  Loaded data (dict or list).
        step:  Step config dict. Recognized key:
                 key — dot-separated path, e.g. "pericopes" or "book.chapters"

    Returns:
        If key is absent: data unchanged.
        If key is present: the value at that dot-path.

    Raises:
        KeyError if any part of the path does not exist.
    """
    key = step.get("key")
    if not key:
        return data

    result = data
    for part in key.split("."):
        if isinstance(result, dict):
            if part not in result:
                raise KeyError(f"key '{key}': '{part}' not found in {list(result.keys())}")
            result = result[part]
        else:
            raise KeyError(f"key '{key}': cannot traverse '{part}' — not a dict")
    return result
