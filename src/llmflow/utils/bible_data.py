"""Bible data registry and access utilities.

This module provides both:
1. High-level APIs for common operations (entity lookup, reference parsing)
2. Direct access to raw data paths for exploration with XPath, JSONPath, SQL, etc.

All data sources come from https://github.com/nida-institute/awesome-biblical-data
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# DATA REGISTRY - Paths to all awesome-biblical-data resources
# =============================================================================

class BibleDataRegistry:
    """Registry of Bible data sources from awesome-biblical-data.

    Provides paths to datasets for both:
    - High-level API access (via methods below)
    - Direct file/database access (via get_path())
    """

    def __init__(self, base_path: Optional[str] = None):
        """Initialize registry with base path to BibleAquifer repos.

        Args:
            base_path: Path to directory containing BibleAquifer repos.
                      Defaults to /Users/jonathan/github/BibleAquifer
        """
        self._custom_base_path = base_path is not None
        if base_path is None:
            # Default: assume BibleAquifer is a sibling of nida-institute
            self.base_path = Path.home() / "github" / "BibleAquifer"
        else:
            self.base_path = Path(base_path)

    def get_path(self, resource_id: str) -> Optional[Path]:
        """Get filesystem path to a data source.

        Args:
            resource_id: ID from awesome-biblical-data (e.g., 'acai', 'macula-hebrew')

        Returns:
            Path to the resource directory, or None if not found

        Examples:
            >>> registry = BibleDataRegistry()
            >>> registry.get_path('acai')
            PosixPath('/Users/jonathan/github/BibleAquifer/ACAI')
        """
        # Map resource IDs to (directory_name, org) tuples
        # org can be 'BibleAquifer', 'Clear', or None to check multiple
        resource_map = {
            'acai': ('ACAI', 'BibleAquifer'),
            'macula-hebrew': ('macula-hebrew', 'Clear'),
            'macula-greek': ('macula-greek', 'Clear'),
            'sblgnt': ('SBLGNT', 'BibleAquifer'),
            'bibleaquifer-sblgnt': ('SBLGNT', 'BibleAquifer'),
            'bibleaquifer-wlc': ('WLC', 'BibleAquifer'),
            'clear-bible-alignments': ('Alignments', 'Clear'),
        }

        mapping = resource_map.get(resource_id)
        if not mapping:
            return None

        dir_name, org = mapping

        # If custom base_path was provided, only check that location
        if self._custom_base_path:
            path = self.base_path / dir_name
            return path if path.exists() else None

        # Default behavior: try specific organization first
        if org:
            path = Path.home() / "github" / org / dir_name
            if path.exists():
                return path

        # Fallback: try base_path
        path = self.base_path / dir_name
        return path if path.exists() else None

    def get_format(self, resource_id: str) -> List[str]:
        """Get available formats for a resource.

        Returns:
            List of formats like ['JSON', 'XML', 'TSV']
        """
        # From awesome-biblical-data/resources.json
        formats = {
            'acai': ['JSON', 'Markdown'],
            'macula-hebrew': ['TSV', 'XML'],
            'macula-greek': ['TSV', 'XML'],
            'sblgnt': ['XML', 'OSIS', 'text'],
        }
        return formats.get(resource_id, [])


# Global registry instance
registry = BibleDataRegistry()


# =============================================================================
# ACAI - Entity Annotation (People, Places, Deities, etc.)
# =============================================================================

def get_acai_path() -> Path:
    """Get path to ACAI repository for direct data access.

    Returns:
        Path to ACAI root directory

    Use this to:
    - Load JSON entities directly
    - Query with JSONPath
    - Build custom indexes
    - Load into a database
    """
    return registry.get_path('acai')


def load_acai_entity(entity_id: str, acai_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load a single ACAI entity by ID.

    Args:
        entity_id: Full entity ID like 'person:Jesus', 'place:Jerusalem', 'deity:Angel'
        acai_path: Optional path to ACAI repo (uses registry default if not provided)

    Returns:
        Entity data dictionary or None if not found

    Examples:
        >>> entity = load_acai_entity('person:Jesus')
        >>> entity['localizations']['eng']['preferred_label']
        'Jesus'
    """
    if ':' not in entity_id:
        return None

    entity_type, entity_name = entity_id.split(':', 1)

    # Map singular to plural directory names
    type_dirs = {
        'person': 'people',
        'people': 'people',
        'place': 'places',
        'deity': 'deities',
        'group': 'groups',
        'fauna': 'fauna',
        'flora': 'flora',
        'realia': 'realia',
        'keyterm': 'keyterms',
    }

    entity_dir = type_dirs.get(entity_type)
    if not entity_dir:
        return None

    if acai_path is None:
        acai_path = get_acai_path()
    else:
        acai_path = Path(acai_path)

    json_path = acai_path / entity_dir / 'json' / f'{entity_name}.json'

    if not json_path.exists():
        return None

    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_acai_entities_for_passage(
    reference: str,
    acai_path: Optional[str] = None,
    max_entities: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get all ACAI entities appearing in a Bible passage.

    Args:
        reference: Bible reference (e.g., 'Mark 11:12-25', 'John 3:16')
        acai_path: Optional path to ACAI repo
        max_entities: Limit number of results (most frequent first)

    Returns:
        List of entity summaries with id, type, label, reference_count

    Examples:
        >>> entities = get_acai_entities_for_passage('Mark 11:12-25')
        >>> [e['label'] for e in entities[:3]]
        ['Jesus', 'Jerusalem', 'Temple']
    """
    if acai_path is None:
        acai_path = get_acai_path()
    else:
        acai_path = Path(acai_path)

    # Parse reference to verse range
    start_verse, end_verse = _parse_reference_to_verse_range(reference)
    if not start_verse:
        return []

    entities_found = []

    # Scan all entity types
    for entity_dir in ['people', 'places', 'deities', 'groups', 'fauna', 'flora', 'realia', 'keyterms']:
        json_dir = acai_path / entity_dir / 'json'
        if not json_dir.exists():
            continue

        for json_file in json_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    entity = json.load(f)

                # Check if entity has references in our passage
                refs = entity.get('references', [])
                matching_refs = [r for r in refs if start_verse <= r <= end_verse]

                if matching_refs:
                    entities_found.append({
                        'id': entity.get('id'),
                        'type': entity.get('type'),
                        'label': entity.get('localizations', {}).get('eng', {}).get('preferred_label'),
                        'reference_count': len(matching_refs),
                        'first_reference': matching_refs[0]
                    })
            except (json.JSONDecodeError, IOError):
                continue

    # Sort by frequency (most common first)
    entities_found.sort(key=lambda x: x['reference_count'], reverse=True)

    if max_entities:
        entities_found = entities_found[:max_entities]

    return entities_found


def get_acai_entity_detail(entity_id: str, acai_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get detailed information about an ACAI entity.

    Args:
        entity_id: Full entity ID (e.g., 'person:Jesus')
        acai_path: Optional path to ACAI repo

    Returns:
        Detailed entity info with description, references, relationships
    """
    entity = load_acai_entity(entity_id, acai_path)
    if not entity:
        return None

    localization = entity.get('localizations', {}).get('eng', {})
    descriptions = localization.get('descriptions', [])

    return {
        'id': entity.get('id'),
        'primary_id': entity.get('primary_id'),
        'type': entity.get('type'),
        'label': localization.get('preferred_label'),
        'description': descriptions[0].get('description') if descriptions else '',
        'gloss': descriptions[0].get('gloss') if descriptions else '',
        'reference_count': len(entity.get('references', [])),
        'references': entity.get('references', [])[:100],  # First 100 refs
        'referred_to_as': entity.get('referred_to_as', []),
        'related_entities': entity.get('related_entities', []),
    }


# =============================================================================
# MACULA HEBREW - Morphology & Syntax
# =============================================================================

def get_macula_hebrew_path() -> Path:
    """Get path to Macula Hebrew for direct TSV/XML access."""
    return registry.get_path('macula-hebrew')


def get_macula_greek_path() -> Path:
    """Get path to Macula Greek for direct TSV/XML access."""
    return registry.get_path('macula-greek')


# =============================================================================
# DATABASE OPTIONS - SQL queries with proper Unicode collation
# =============================================================================
#
# Two approaches for Unicode-aware sorting:
#
# 1. DuckDB (recommended for analytics)
#    - Built-in ICU collation support
#    - Direct TSV file querying
#    - Fast columnar storage
#    - Functions below use this approach
#
# 2. PyICU + SQLite (alternative)
#    - Use PyICU to generate sort keys
#    - Store keys alongside text in SQLite
#    - Example:
#        import icu
#        collator = icu.Collator.createInstance(icu.Locale('he'))
#        sort_key = collator.getSortKey(hebrew_text)
#        # Store sort_key in SQLite, ORDER BY sort_key
#    - Pros: Single dependency (SQLite), lighter weight
#    - Cons: Manual sort key generation, more setup
#
# =============================================================================

def query_macula_hebrew(book: str, query: Optional[str] = None):
    """Query Macula Hebrew TSV data with DuckDB.

    Args:
        book: Bible book name (e.g., 'Genesis', 'Ruth')
        query: Optional SQL WHERE clause. If None, returns all rows.

    Returns:
        DuckDB query result

    Examples:
        >>> # Get all verbs in Genesis
        >>> result = query_macula_hebrew('Genesis', "pos = 'verb'")
        >>> df = result.df()  # Convert to pandas DataFrame

        >>> # Get frequency of lemmas
        >>> con = duckdb.connect()
        >>> macula_path = get_macula_hebrew_path()
        >>> result = con.execute(f'''
        ...     SELECT lemma, gloss, COUNT(*) as freq
        ...     FROM '{macula_path}/tsv/Genesis.tsv'
        ...     WHERE pos = 'verb'
        ...     GROUP BY lemma, gloss
        ...     ORDER BY freq DESC
        ... ''')
    """
    try:
        import duckdb
    except ImportError:
        raise ImportError("DuckDB not installed. Run: pip install duckdb")

    macula_path = get_macula_hebrew_path()
    tsv_file = macula_path / 'tsv' / f'{book}.tsv'

    if not tsv_file.exists():
        raise FileNotFoundError(f"TSV file not found: {tsv_file}")

    con = duckdb.connect()

    if query:
        sql = f"SELECT * FROM '{tsv_file}' WHERE {query}"
    else:
        sql = f"SELECT * FROM '{tsv_file}'"

    return con.execute(sql)


def query_macula_greek(book: str, query: Optional[str] = None):
    """Query Macula Greek TSV data with DuckDB.

    Args:
        book: NT book name (e.g., 'Mark', 'John', 'Romans')
        query: Optional SQL WHERE clause

    Returns:
        DuckDB query result
    """
    try:
        import duckdb
    except ImportError:
        raise ImportError("DuckDB not installed. Run: pip install duckdb")

    macula_path = get_macula_greek_path()
    tsv_file = macula_path / 'tsv' / f'{book}.tsv'

    if not tsv_file.exists():
        raise FileNotFoundError(f"TSV file not found: {tsv_file}")

    con = duckdb.connect()

    if query:
        sql = f"SELECT * FROM '{tsv_file}' WHERE {query}"
    else:
        sql = f"SELECT * FROM '{tsv_file}'"

    return con.execute(sql)


def create_duckdb_connection(db_path: Optional[str] = ':memory:'):
    """Create a DuckDB connection with proper ICU collation.

    Args:
        db_path: Path to DuckDB file, or ':memory:' for in-memory database

    Returns:
        DuckDB connection object

    Examples:
        >>> con = create_duckdb_connection()
        >>> con.execute("SELECT 'א', 'ב', 'ג' ORDER BY 1 COLLATE 'he'")
        >>> # Properly sorts Hebrew with ICU collation
    """
    try:
        import duckdb
    except ImportError:
        raise ImportError("DuckDB not installed. Run: pip install duckdb")

    con = duckdb.connect(db_path)
    # Enable ICU extension for proper Unicode collation
    con.execute("INSTALL icu")
    con.execute("LOAD icu")
    return con


def load_acai_to_duckdb(con=None, entity_types: Optional[List[str]] = None):
    """Load ACAI entities into DuckDB for relational queries.

    Args:
        con: DuckDB connection (creates in-memory if None)
        entity_types: List of entity types to load (None = all)
                     Options: ['people', 'places', 'deities', 'groups',
                              'fauna', 'flora', 'realia', 'keyterms']

    Returns:
        DuckDB connection with ACAI data loaded

    Examples:
        >>> con = load_acai_to_duckdb()
        >>> con.execute('''
        ...     SELECT type, COUNT(*) as count
        ...     FROM acai_entities
        ...     GROUP BY type
        ... ''').fetchall()
    """
    try:
        import duckdb
    except ImportError:
        raise ImportError("DuckDB not installed. Run: pip install duckdb")

    if con is None:
        con = create_duckdb_connection(':memory:')

    if entity_types is None:
        entity_types = ['people', 'places', 'deities', 'groups',
                       'fauna', 'flora', 'realia', 'keyterms']

    acai_path = get_acai_path()

    # Create table schema
    con.execute("""
        CREATE TABLE IF NOT EXISTS acai_entities (
            id VARCHAR,
            primary_id VARCHAR,
            type VARCHAR,
            entity_name VARCHAR,
            preferred_label VARCHAR,
            description VARCHAR,
            reference_count INTEGER,
            references VARCHAR[]
        )
    """)

    # Load entities from each type
    for entity_type in entity_types:
        json_dir = acai_path / entity_type / 'json'
        if not json_dir.exists():
            continue

        for json_file in json_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    entity = json.load(f)

                localization = entity.get('localizations', {}).get('eng', {})
                descriptions = localization.get('descriptions', [])

                con.execute("""
                    INSERT INTO acai_entities VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    entity.get('id'),
                    entity.get('primary_id'),
                    entity.get('type'),
                    entity['id'].split(':')[1] if ':' in entity.get('id', '') else '',
                    localization.get('preferred_label'),
                    descriptions[0].get('description') if descriptions else '',
                    len(entity.get('references', [])),
                    entity.get('references', [])
                ])
            except (json.JSONDecodeError, IOError):
                continue

    return con


# =============================================================================
# ALTERNATIVE: PyICU + SQLite for Unicode Collation
# =============================================================================

def create_icu_collator(locale: str = 'en'):
    """Create an ICU collator for generating sort keys.

    Alternative to DuckDB: Use PyICU with SQLite for Unicode-aware sorting.

    Args:
        locale: ICU locale code (e.g., 'he' for Hebrew, 'el' for Greek, 'en' for English)

    Returns:
        ICU Collator instance

    Examples:
        >>> # Install PyICU: pip install pyicu
        >>> collator = create_icu_collator('he')
        >>> sort_key = collator.getSortKey('אברהם')  # Abraham in Hebrew
        >>>
        >>> # Store in SQLite with sort key
        >>> import sqlite3
        >>> conn = sqlite3.connect(':memory:')
        >>> conn.execute('CREATE TABLE words (text TEXT, sort_key BLOB)')
        >>> conn.execute('INSERT INTO words VALUES (?, ?)', ('אברהם', sort_key))
        >>> # Query: SELECT * FROM words ORDER BY sort_key
    """
    try:
        import icu
    except ImportError:
        raise ImportError("PyICU not installed. Run: pip install pyicu")

    return icu.Collator.createInstance(icu.Locale(locale))


def generate_sort_keys_for_texts(texts: List[str], locale: str = 'en') -> List[bytes]:
    """Generate ICU sort keys for a list of texts.

    Use this when loading data into SQLite if you need proper Unicode sorting.

    Args:
        texts: List of text strings to generate keys for
        locale: ICU locale for collation rules

    Returns:
        List of sort keys (bytes) in same order as input texts

    Examples:
        >>> hebrew_words = ['אברהם', 'אדם', 'אהרן']
        >>> sort_keys = generate_sort_keys_for_texts(hebrew_words, 'he')
        >>> # Now can store both text and sort_key in SQLite
    """
    collator = create_icu_collator(locale)
    return [collator.getSortKey(text) for text in texts]


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _parse_reference_to_verse_range(reference: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse Bible reference to ACAI verse ID range.

    ACAI uses 8-digit verse IDs: BBCCCVVV (book, chapter, verse)
    Example: Genesis 1:1 = "01001001"

    Args:
        reference: Reference like 'Mark 11:12-25' or 'John 3:16'

    Returns:
        Tuple of (start_verse_id, end_verse_id) or (None, None)
    """
    from llmflow.utils.data import parse_bible_reference

    try:
        parsed = parse_bible_reference(reference)
        book_num = parsed['book_number']
        chapter = str(parsed['chapter']).zfill(3)
        start_v = str(parsed['start_verse']).zfill(3)
        end_v = str(parsed['end_verse']).zfill(3)

        start_id = f"{book_num}{chapter}{start_v}"
        end_id = f"{book_num}{chapter}{end_v}"

        return (start_id, end_id)
    except (KeyError, ValueError, AttributeError):
        return (None, None)


def _verse_id_to_reference(verse_id: str) -> str:
    """Convert ACAI verse ID to human-readable reference.

    Args:
        verse_id: 8-digit verse ID like '01001001'

    Returns:
        Reference string like 'Genesis 1:1'
    """
    if len(verse_id) != 8:
        return verse_id

    book_names = [
        '', 'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
        '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra',
        'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
        'Ecclesiastes', 'Song of Songs', 'Isaiah', 'Jeremiah', 'Lamentations',
        'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
        'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
        'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
        'Matthew', 'Mark', 'Luke', 'John', 'Acts',
        'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
        'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy',
        '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James',
        '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
        'Jude', 'Revelation'
    ]

    book_num = int(verse_id[:2])
    chapter = int(verse_id[2:5])
    verse = int(verse_id[5:8])

    if 1 <= book_num < len(book_names):
        return f"{book_names[book_num]} {chapter}:{verse}"
    return verse_id


# =============================================================================
# EXAMPLE: Direct Data Access Patterns
# =============================================================================

def example_usage():
    """Examples of how to use this module."""

    # =============================================================================
    # Example 1: High-level API - Get ACAI entities for a passage
    # =============================================================================
    entities = get_acai_entities_for_passage('Mark 11:12-25')
    for entity in entities[:5]:
        print(f"{entity['label']} ({entity['type']}): {entity['reference_count']} occurrences")

    # Get detailed info about a specific entity
    jesus = get_acai_entity_detail('person:Jesus')
    print(f"{jesus['label']}: {jesus['description']}")


    # =============================================================================
    # Example 2: Direct file access - Load and explore JSON
    # =============================================================================
    acai_path = get_acai_path()

    # Load any entity directly
    angel_file = acai_path / 'deities' / 'json' / 'Angel.json'
    with open(angel_file) as f:
        angel = json.load(f)
        print(angel['localizations']['eng']['preferred_label'])

    # Iterate through all people
    people_dir = acai_path / 'people' / 'json'
    for json_file in people_dir.glob('*.json'):
        with open(json_file) as f:
            entity = json.load(f)
            # Analyze, transform, or export as needed


    # =============================================================================
    # Example 3: DuckDB - Query Macula morphology with proper Unicode sorting
    # =============================================================================
    import duckdb

    # Query Hebrew verbs in Genesis
    result = query_macula_hebrew('Genesis', "pos = 'verb'")
    df = result.df()  # Convert to pandas DataFrame
    print(f"Found {len(df)} verbs in Genesis")

    # Direct SQL with DuckDB - no import needed!
    con = create_duckdb_connection()
    macula_path = get_macula_hebrew_path()

    verb_freq = con.execute(f"""
        SELECT lemma, gloss, COUNT(*) as freq
        FROM '{macula_path}/tsv/Genesis.tsv'
        WHERE pos = 'verb'
        GROUP BY lemma, gloss
        ORDER BY freq DESC COLLATE 'he'
        LIMIT 10
    """).fetchall()

    print("Most frequent Hebrew verbs in Genesis:")
    for lemma, gloss, freq in verb_freq:
        print(f"  {lemma} ({gloss}): {freq}x")


    # =============================================================================
    # Example 4: Load ACAI into DuckDB for relational queries
    # =============================================================================
    con = load_acai_to_duckdb()

    # Query entities by type
    type_counts = con.execute("""
        SELECT type, COUNT(*) as count
        FROM acai_entities
        GROUP BY type
        ORDER BY count DESC
    """).fetchall()

    # Find most frequently mentioned people
    top_people = con.execute("""
        SELECT preferred_label, reference_count
        FROM acai_entities
        WHERE type = 'person'
        ORDER BY reference_count DESC
        LIMIT 10
    """).fetchall()


    # =============================================================================
    # Example 5: Cross-reference ACAI and Macula data
    # =============================================================================
    # Load both into same DuckDB connection
    con = create_duckdb_connection()

    # Load ACAI
    load_acai_to_duckdb(con)

    # Now can join ACAI entities with Macula morphology!
    # (requires mapping entity references to Macula node IDs)
