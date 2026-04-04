"""Test suite for llmflow.utils.bible_data module.

Tests cover:
- BibleDataRegistry path resolution
- ACAI entity loading and querying
- Macula data access
- DuckDB integration
- Error handling and edge cases
"""

import importlib.util
import json
import pytest
from pathlib import Path

from llmflow.utils.bible_data import (
    BibleDataRegistry,
    registry,
    get_acai_path,
    get_macula_hebrew_path,
    get_macula_greek_path,
    load_acai_entity,
    get_acai_entities_for_passage,
    get_acai_entity_detail,
    _parse_reference_to_verse_range,
    _verse_id_to_reference,
)


#  =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def check_acai_available():
    """Skip test if ACAI data is not available."""
    if get_acai_path() is None:
        pytest.skip("ACAI not found on this system")


# =============================================================================
# Registry Tests
# =============================================================================

class TestBibleDataRegistry:
    """Test the BibleDataRegistry class."""

    def test_registry_singleton_exists(self):
        """Test that global registry instance is available."""
        assert registry is not None
        assert isinstance(registry, BibleDataRegistry)

    def test_get_acai_path(self, check_acai_available):
        """Test ACAI path resolution."""
        path = registry.get_path('acai')
        assert path is not None
        assert path.exists()
        assert path.name == 'ACAI'

        # Verify it has the expected structure
        assert (path / 'people' / 'json').exists()
        assert (path / 'places' / 'json').exists()
        assert (path / 'deities' / 'json').exists()

    def test_get_macula_hebrew_path(self):
        """Test Macula Hebrew path resolution."""
        path = registry.get_path('macula-hebrew')

        if path is None:
            pytest.skip("Macula Hebrew not found on this system")

        # Type assertion for pyright
        assert path is not None
        assert path.exists()
        assert path.name == 'macula-hebrew'

    def test_get_macula_greek_path(self):
        """Test Macula Greek path resolution."""
        path = registry.get_path('macula-greek')

        if path is None:
            pytest.skip("Macula Greek not found on this system")

        # Type assertion for pyright
        assert path is not None
        assert path.exists()
        assert path.name == 'macula-greek'

    def test_get_path_unknown_resource(self):
        """Test that unknown resources return None."""
        path = registry.get_path('nonexistent-resource')
        assert path is None

    def test_get_format(self):
        """Test format listing for resources."""
        formats = registry.get_format('acai')
        assert 'JSON' in formats
        assert 'Markdown' in formats

        macula_formats = registry.get_format('macula-hebrew')
        assert 'TSV' in macula_formats
        assert 'XML' in macula_formats

    def test_custom_base_path(self):
        """Test registry with custom base path."""
        custom_registry = BibleDataRegistry(base_path='/tmp')
        # Should return None for non-existent paths
        path = custom_registry.get_path('acai')
        assert path is None


# =============================================================================
# Helper Function Tests
# =============================================================================

class TestHelperFunctions:
    """Test helper functions for convenience access."""

    def test_get_acai_path(self, check_acai_available):
        """Test get_acai_path() convenience function."""
        path = get_acai_path()
        assert path is not None
        assert path.exists()
        assert path.name == 'ACAI'

    def test_get_macula_hebrew_path(self):
        """Test get_macula_hebrew_path() function."""
        path = get_macula_hebrew_path()
        # May be None if not installed
        if path is not None:
            assert path.exists()

    def test_get_macula_greek_path(self):
        """Test get_macula_greek_path() function."""
        path = get_macula_greek_path()
        # May be None if not installed
        if path is not None:
            assert path.exists()


# =============================================================================
# ACAI Entity Loading Tests
# =============================================================================

class TestACAIEntityLoading:
    """Test ACAI entity loading functionality."""

    def test_load_acai_entity_deity(self, check_acai_available):
        """Test loading a deity entity."""
        entity = load_acai_entity('deity:Angel')

        assert entity is not None
        assert entity['id'] == 'deity:Angel'
        assert entity['type'] == 'deity'
        assert 'localizations' in entity
        assert 'eng' in entity['localizations']
        assert entity['localizations']['eng']['preferred_label'] == 'An Angel'

    def test_load_acai_entity_person(self, check_acai_available):
        """Test loading a person entity (if Jesus exists)."""
        entity = load_acai_entity('person:Jesus')

        if entity is None:
            pytest.skip("Jesus entity not found in ACAI")

        assert entity['id'] == 'person:Jesus'
        assert entity['type'] == 'person'
        assert 'Jesus' in entity['localizations']['eng']['preferred_label']

    def test_load_acai_entity_invalid_id(self, check_acai_available):
        """Test loading with invalid entity ID."""
        entity = load_acai_entity('invalid')
        assert entity is None

        entity = load_acai_entity('person:NonExistentPerson9999')
        assert entity is None

    def test_load_acai_entity_all_types(self, check_acai_available):
        """Test that we can load at least one entity from each type."""
        acai_path = get_acai_path()
        entity_types = ['people', 'places', 'deities', 'groups',
                       'fauna', 'flora', 'realia', 'keyterms']

        for entity_type in entity_types:
            json_dir = acai_path / entity_type / 'json'
            if not json_dir.exists():
                continue

            # Get first JSON file
            json_files = list(json_dir.glob('*.json'))
            if not json_files:
                continue

            # Extract entity name from filename
            entity_name = json_files[0].stem

            # Normalize type name (people -> person, places -> place)
            type_singular = entity_type.rstrip('s') if entity_type not in ['fauna', 'flora', 'realia'] else entity_type
            if entity_type == 'people':
                type_singular = 'person'
            elif entity_type == 'deities':
                type_singular = 'deity'

            entity_id = f"{type_singular}:{entity_name}"
            entity = load_acai_entity(entity_id)

            assert entity is not None, f"Failed to load {entity_id}"
            assert entity['id'] == entity_id


# =============================================================================
# ACAI Entity Detail Tests
# =============================================================================

class TestACAIEntityDetail:
    """Test detailed entity information retrieval."""

    def test_get_acai_entity_detail(self, check_acai_available):
        """Test getting detailed entity information."""
        detail = get_acai_entity_detail('deity:Angel')

        assert detail is not None
        assert detail['id'] == 'deity:Angel'
        assert detail['type'] == 'deity'
        assert detail['label'] == 'An Angel'
        assert 'description' in detail
        assert 'reference_count' in detail
        assert detail['reference_count'] > 0
        assert 'references' in detail
        assert isinstance(detail['references'], list)

    def test_get_acai_entity_detail_invalid(self, check_acai_available):
        """Test getting detail for non-existent entity."""
        detail = get_acai_entity_detail('person:NonExistent999')
        assert detail is None


# =============================================================================
# ACAI Passage Query Tests
# =============================================================================

class TestACAIPassageQueries:
    """Test querying ACAI entities by Bible passage."""

    def test_get_entities_for_passage_basic(self, check_acai_available):
        """Test getting entities for a passage."""
        # Note: This test depends on the reference parser working
        # May need to mock if parser not available
        entities = get_acai_entities_for_passage('Genesis 1:1')

        # Genesis 1:1 should have some entities
        assert isinstance(entities, list)
        # Can't assert specific count without knowing data

    def test_get_entities_with_max_limit(self, check_acai_available):
        """Test limiting number of entities returned."""
        entities = get_acai_entities_for_passage('Genesis 1:1', max_entities=3)

        assert isinstance(entities, list)
        assert len(entities) <= 3

    def test_entities_sorted_by_frequency(self, check_acai_available):
        """Test that entities are sorted by reference count."""
        entities = get_acai_entities_for_passage('Genesis 1:1', max_entities=5)

        if len(entities) > 1:
            # Check that reference counts are descending
            for i in range(len(entities) - 1):
                assert entities[i]['reference_count'] >= entities[i+1]['reference_count']


# =============================================================================
# Reference Parsing Tests
# =============================================================================

class TestReferenceParsing:
    """Test Bible reference parsing helpers."""

    def test_parse_reference_to_verse_range(self):
        """Test parsing references to ACAI verse ID ranges."""
        start, end = _parse_reference_to_verse_range('Genesis 1:1')

        if start is not None:
            assert start == '01001001'  # Genesis (01), chapter 1 (001), verse 1 (001)
            assert end == '01001001'

    def test_verse_id_to_reference(self):
        """Test converting verse IDs to readable references."""
        ref = _verse_id_to_reference('01001001')
        assert ref == 'Genesis 1:1'

        ref = _verse_id_to_reference('41001001')
        assert ref == 'Mark 1:1'

        ref = _verse_id_to_reference('43003016')
        assert ref == 'John 3:16'

    def test_verse_id_to_reference_invalid(self):
        """Test handling of invalid verse IDs."""
        ref = _verse_id_to_reference('invalid')
        assert ref == 'invalid'  # Returns input if can't parse

        ref = _verse_id_to_reference('123')
        assert ref == '123'


# =============================================================================
# DuckDB Integration Tests
# =============================================================================

@pytest.mark.skipif(importlib.util.find_spec("duckdb") is None, reason="duckdb package not installed")
class TestDuckDBIntegration:
    """Test DuckDB database integration."""

    pytestmark = pytest.mark.duckdb

    def test_create_duckdb_connection(self):
        """Test creating a DuckDB connection."""
        from llmflow.utils.bible_data import create_duckdb_connection

        con = create_duckdb_connection(':memory:')
        assert con is not None

        # Test that ICU is loaded
        result = con.execute("SELECT current_setting('extension_directory')").fetchone()
        assert result is not None

    def test_query_macula_hebrew(self):
        """Test querying Macula Hebrew data."""
        from llmflow.utils.bible_data import query_macula_hebrew

        macula_path = get_macula_hebrew_path()
        if macula_path is None:
            pytest.skip("Macula Hebrew not available")

        # Check if Genesis TSV exists
        gen_tsv = macula_path / 'tsv' / 'Genesis.tsv'
        if not gen_tsv.exists():
            pytest.skip("Genesis.tsv not found")

        result = query_macula_hebrew('Genesis')
        assert result is not None

        # Get as dataframe
        df = result.df()
        assert len(df) > 0

    def test_load_acai_to_duckdb(self):
        """Test loading ACAI entities into DuckDB."""
        from llmflow.utils.bible_data import load_acai_to_duckdb, get_acai_path

        if get_acai_path() is None:
            pytest.skip("ACAI data not available")

        con = load_acai_to_duckdb(entity_types=['deities'])
        assert con is not None

        # Query the loaded data
        result = con.execute("""
            SELECT COUNT(*) as count
            FROM acai_entities
            WHERE type = 'deity'
        """).fetchone()

        assert result[0] > 0

    def test_hebrew_icu_sort_aleph_bet_order_with_niqquud(self):
        """Hebrew words with niqquud sort in aleph-bet order under ICU 'he' collation.

        This is a hard test: niqquud (vowel points) are Unicode combining characters
        that immediately follow the base consonant. A naive byte sort could be disrupted
        by them, but ICU collation must produce correct aleph-bet ordering.
        """
        from llmflow.utils.bible_data import create_duckdb_connection

        con = create_duckdb_connection(':memory:')
        # Three words with full niqquud, starting with aleph (א), bet (ב), gimel (ג)
        # Deliberately inserted in gimel→aleph→bet order to prove sorting works
        result = con.execute("""
            SELECT word FROM (VALUES
                ('גָּדוֹל'),
                ('אֱלֹהִים'),
                ('בָּרָא')
            ) t(word)
            ORDER BY word COLLATE he
        """).fetchall()
        words = [r[0] for r in result]
        assert words[0][0] == 'א', f"Aleph (א) should sort first, got: {words}"
        assert words[1][0] == 'ב', f"Bet (ב) should sort second, got: {words}"
        assert words[2][0] == 'ג', f"Gimel (ג) should sort third, got: {words}"

    def test_hebrew_niqquud_does_not_override_consonant_order(self):
        """Niqquud must not displace a word from its consonant-based sort position.

        שָׁלוֹם (shin+niqquud) and שלום (shin bare) both start with shin (ש).
        תּוֹרָה (tav+niqquud) starts with tav (ת), which follows shin in the aleph-bet.
        Under ICU Hebrew collation, both shin-words must sort before the tav-word.
        """
        from llmflow.utils.bible_data import create_duckdb_connection

        con = create_duckdb_connection(':memory:')
        result = con.execute("""
            SELECT label FROM (VALUES
                ('שָׁלוֹם', 'shalom_niqquud'),
                ('שלום',    'shalom_bare'),
                ('תּוֹרָה',  'torah_niqquud')
            ) t(word, label)
            ORDER BY word COLLATE he
        """).fetchall()
        labels = [r[0] for r in result]
        # Both shin-words (שׁ) come before the tav-word (ת)
        assert labels[2] == 'torah_niqquud', f"Torah (tav) should sort last: {labels}"
        assert set(labels[:2]) == {'shalom_niqquud', 'shalom_bare'}, \
            f"Both shalom variants should sort first: {labels}"


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_load_entity_with_custom_path(self, check_acai_available):
        """Test loading entity with custom ACAI path."""
        acai_path = get_acai_path()
        entity = load_acai_entity('deity:Angel', acai_path=str(acai_path))

        assert entity is not None
        assert entity['id'] == 'deity:Angel'

    def test_load_entity_with_invalid_path(self):
        """Test loading entity with invalid ACAI path."""
        entity = load_acai_entity('deity:Angel', acai_path='/nonexistent/path')
        assert entity is None

    def test_entity_has_required_fields(self, check_acai_available):
        """Test that loaded entities have all required fields."""
        entity = load_acai_entity('deity:Angel')

        assert entity is not None

        # Check required top-level fields
        required_fields = ['id', 'primary_id', 'type', 'localizations']
        for field in required_fields:
            assert field in entity, f"Missing required field: {field}"

        # Check localization structure
        assert 'eng' in entity['localizations']
        assert 'preferred_label' in entity['localizations']['eng']


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow_acai_lookup(self, check_acai_available):
        """Test complete workflow: passage -> entities -> details."""
        # Step 1: Get entities for a passage
        entities = get_acai_entities_for_passage('Genesis 16:7', max_entities=1)

        if not entities:
            pytest.skip("No entities found for Genesis 16:7")

        # Step 2: Get first entity ID
        entity_id = entities[0]['id']

        # Step 3: Get detailed information
        detail = get_acai_entity_detail(entity_id)

        assert detail is not None
        assert detail['id'] == entity_id
        assert 'description' in detail

    def test_verify_all_entity_types_loadable(self, check_acai_available):
        """Verify that we can access all entity type directories."""
        acai_path = get_acai_path()
        entity_dirs = ['people', 'places', 'deities', 'groups',
                      'fauna', 'flora', 'realia', 'keyterms']

        for entity_dir in entity_dirs:
            dir_path = acai_path / entity_dir / 'json'

            # Not all types may exist, so just check structure
            if dir_path.exists():
                json_files = list(dir_path.glob('*.json'))
                assert len(json_files) > 0, f"No JSON files in {entity_dir}"


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
