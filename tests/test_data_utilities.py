"""Comprehensive unit tests for data utilities module.

Tests cover:
- parse_bible_reference(): All reference formats, abbreviations, edge cases
- interleave(): Array handling, markdown output, empty cases
- flatten_dict(): Nested structure handling, separators, edge cases
"""

import pytest
from llmflow.utils.data import (
    parse_bible_reference,
    interleave,
    flatten_dict,
)


# ============================================================================
# Test parse_bible_reference()
# ============================================================================

class TestParseBibleReference:
    """Test Bible reference parsing for all formats."""

    def test_whole_chapter_psalm(self):
        """Whole chapter reference like 'Psalm 23' should parse correctly."""
        result = parse_bible_reference("Psalm 23")
        assert result["book_name"] == "Psalms"
        assert result["book_number"] == "19"
        assert result["book_code"] == "PSA"
        assert result["chapter"] == 23
        assert result["chapter_padded"] == "023"
        assert result["start_verse"] == 1
        assert result["end_verse"] == 6
        assert result["is_whole_chapter"] is True
        assert result["display_name"] == "Psalms-23"
        assert result["canonical_reference"] == "Psalms 23:1-6"
        assert result["filename_prefix"] == "19023001-19023006"

    def test_single_verse_john(self):
        """Single verse like 'John 3:16' should parse correctly."""
        result = parse_bible_reference("John 3:16")
        assert result["book_name"] == "John"
        assert result["book_number"] == "43"
        assert result["book_code"] == "JHN"
        assert result["chapter"] == 3
        assert result["chapter_padded"] == "003"
        assert result["start_verse"] == 16
        assert result["end_verse"] == 16
        assert result["is_whole_chapter"] is False
        assert result["display_name"] == "John-3-16"
        assert result["canonical_reference"] == "John 3:16"
        assert result["filename_prefix"] == "43003016-43003016"

    def test_verse_range_luke(self):
        """Verse range like 'Luke 12:5-19' should parse correctly."""
        result = parse_bible_reference("Luke 12:5-19")
        assert result["book_name"] == "Luke"
        assert result["book_number"] == "42"
        assert result["book_code"] == "LUK"
        assert result["chapter"] == 12
        assert result["chapter_padded"] == "012"
        assert result["start_verse"] == 5
        assert result["end_verse"] == 19
        assert result["is_whole_chapter"] is False
        assert result["display_name"] == "Luke-12-5-19"
        assert result["canonical_reference"] == "Luke 12:5-19"
        assert result["filename_prefix"] == "42012005-42012019"

    def test_abbreviation_gen(self):
        """Book abbreviation 'Gen' should map to Genesis."""
        result = parse_bible_reference("Gen 1:1")
        assert result["book_name"] == "Genesis"
        assert result["book_number"] == "01"
        assert result["book_code"] == "GEN"
        assert result["chapter"] == 1
        assert result["start_verse"] == 1

    def test_abbreviation_matt(self):
        """Book abbreviation 'Matt' should map to Matthew."""
        result = parse_bible_reference("Matt 5:3-12")
        assert result["book_name"] == "Matthew"
        assert result["book_number"] == "40"
        assert result["book_code"] == "MAT"
        assert result["chapter"] == 5
        assert result["start_verse"] == 3
        assert result["end_verse"] == 12

    def test_abbreviation_rom(self):
        """Book abbreviation 'Rom' should map to Romans."""
        result = parse_bible_reference("Rom 8:28")
        assert result["book_name"] == "Romans"
        assert result["book_number"] == "45"
        assert result["book_code"] == "ROM"
        assert result["chapter"] == 8
        assert result["start_verse"] == 28

    def test_case_insensitive(self):
        """Reference parsing should be case insensitive."""
        result1 = parse_bible_reference("JOHN 3:16")
        result2 = parse_bible_reference("john 3:16")
        result3 = parse_bible_reference("John 3:16")
        assert result1["book_name"] == result2["book_name"] == result3["book_name"]
        assert result1["chapter"] == result2["chapter"] == result3["chapter"]

    def test_numbered_books_1_samuel(self):
        """Numbered book '1 Samuel' should parse correctly."""
        result = parse_bible_reference("1 Samuel 17:45")
        assert result["book_name"] == "1 Samuel"
        assert result["book_number"] == "09"
        assert result["book_code"] == "1SA"
        assert result["chapter"] == 17
        assert result["start_verse"] == 45

    def test_numbered_books_2_corinthians(self):
        """Numbered book '2 Corinthians' should parse correctly."""
        result = parse_bible_reference("2 Corinthians 5:17")
        assert result["book_name"] == "2 Corinthians"
        assert result["book_number"] == "47"
        assert result["book_code"] == "2CO"
        assert result["chapter"] == 5
        assert result["start_verse"] == 17

    def test_numbered_books_abbreviation_1cor(self):
        """Numbered book abbreviation '1Cor' should work."""
        result = parse_bible_reference("1Cor 13:4-8")
        assert result["book_name"] == "1 Corinthians"
        assert result["book_number"] == "46"
        assert result["book_code"] == "1CO"
        assert result["chapter"] == 13
        assert result["start_verse"] == 4
        assert result["end_verse"] == 8

    def test_song_of_songs(self):
        """Multi-word book 'Song of Songs' should parse correctly."""
        result = parse_bible_reference("Song of Songs 2:1")
        assert result["book_name"] == "Song of Songs"
        assert result["book_number"] == "22"
        assert result["chapter"] == 2
        assert result["start_verse"] == 1

    def test_revelation_chapter_padded(self):
        """Revelation 6:12-17 should have correct chapter_padded for directory paths."""
        result = parse_bible_reference("Revelation 6:12-17")
        assert result["book_name"] == "Revelation"
        assert result["book_number"] == "66"
        assert result["book_code"] == "REV"
        assert result["chapter"] == 6
        assert result["chapter_padded"] == "006"
        assert result["start_verse"] == 12
        assert result["end_verse"] == 17
        assert result["filename_prefix"] == "66006012-66006017"

    def test_revelation_abbreviation(self):
        """Revelation abbreviation 'Rev' should work."""
        result = parse_bible_reference("Rev 21:4")
        assert result["book_name"] == "Revelation"
        assert result["book_number"] == "66"
        assert result["book_code"] == "REV"
        assert result["chapter"] == 21
        assert result["start_verse"] == 4

    def test_usfm_book_codes_all_books(self):
        """All 66 books should have valid USFM 3.0 book codes."""
        test_cases = [
            ("Genesis 1:1", "GEN"), ("Exodus 1:1", "EXO"), ("Leviticus 1:1", "LEV"),
            ("Numbers 1:1", "NUM"), ("Deuteronomy 1:1", "DEU"), ("Joshua 1:1", "JOS"),
            ("Judges 1:1", "JDG"), ("Ruth 1:1", "RUT"), ("1 Samuel 1:1", "1SA"),
            ("2 Samuel 1:1", "2SA"), ("1 Kings 1:1", "1KI"), ("2 Kings 1:1", "2KI"),
            ("1 Chronicles 1:1", "1CH"), ("2 Chronicles 1:1", "2CH"), ("Ezra 1:1", "EZR"),
            ("Nehemiah 1:1", "NEH"), ("Esther 1:1", "EST"), ("Job 1:1", "JOB"),
            ("Psalms 1:1", "PSA"), ("Proverbs 1:1", "PRO"), ("Ecclesiastes 1:1", "ECC"),
            ("Song of Songs 1:1", "SNG"), ("Isaiah 1:1", "ISA"), ("Jeremiah 1:1", "JER"),
            ("Lamentations 1:1", "LAM"), ("Ezekiel 1:1", "EZK"), ("Daniel 1:1", "DAN"),
            ("Hosea 1:1", "HOS"), ("Joel 1:1", "JOL"), ("Amos 1:1", "AMO"),
            ("Obadiah 1:1", "OBA"), ("Jonah 1:1", "JON"), ("Micah 1:1", "MIC"),
            ("Nahum 1:1", "NAM"), ("Habakkuk 1:1", "HAB"), ("Zephaniah 1:1", "ZEP"),
            ("Haggai 1:1", "HAG"), ("Zechariah 1:1", "ZEC"), ("Malachi 1:1", "MAL"),
            ("Matthew 1:1", "MAT"), ("Mark 1:1", "MRK"), ("Luke 1:1", "LUK"),
            ("John 1:1", "JHN"), ("Acts 1:1", "ACT"), ("Romans 1:1", "ROM"),
            ("1 Corinthians 1:1", "1CO"), ("2 Corinthians 1:1", "2CO"), ("Galatians 1:1", "GAL"),
            ("Ephesians 1:1", "EPH"), ("Philippians 1:1", "PHP"), ("Colossians 1:1", "COL"),
            ("1 Thessalonians 1:1", "1TH"), ("2 Thessalonians 1:1", "2TH"), ("1 Timothy 1:1", "1TI"),
            ("2 Timothy 1:1", "2TI"), ("Titus 1:1", "TIT"), ("Philemon 1:1", "PHM"),
            ("Hebrews 1:1", "HEB"), ("James 1:1", "JAS"), ("1 Peter 1:1", "1PE"),
            ("2 Peter 1:1", "2PE"), ("1 John 1:1", "1JN"), ("2 John 1:1", "2JN"),
            ("3 John 1:1", "3JN"), ("Jude 1:1", "JUD"), ("Revelation 1:1", "REV"),
        ]
        for passage, expected_code in test_cases:
            result = parse_bible_reference(passage)
            assert result["book_code"] == expected_code, f"{passage} should have code {expected_code}"

    def test_psalms_plural(self):
        """'Psalms' (plural) should work."""
        result = parse_bible_reference("Psalms 119")
        assert result["book_name"] == "Psalms"
        assert result["book_number"] == "19"
        assert result["chapter"] == 119
        assert result["end_verse"] == 176  # Longest chapter

    def test_empty_reference_raises(self):
        """Empty reference should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_bible_reference("")

    def test_whitespace_only_raises(self):
        """Whitespace-only reference should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_bible_reference("   ")

    def test_invalid_book_raises(self):
        """Invalid book name should raise ValueError."""
        with pytest.raises(ValueError, match="Unrecognized Bible book"):
            parse_bible_reference("NotABook 1:1")

    def test_unparseable_format_raises(self):
        """Unparseable format should raise ValueError."""
        with pytest.raises(ValueError, match="Could not parse"):
            parse_bible_reference("something random")

    def test_ambiguous_abbreviation_raises(self):
        """Ambiguous abbreviation should raise ValueError."""
        with pytest.raises(ValueError, match="Ambiguous book abbreviation"):
            parse_bible_reference("ph 1:1")

    def test_filename_prefix_format(self):
        """Filename prefix format: 2-char USFM book code + 3-digit chapter + 3-digit verse."""
        result = parse_bible_reference("Genesis 1:1")
        assert result["filename_prefix"] == "01001001-01001001"

        result = parse_bible_reference("Revelation 22:21")
        assert result["filename_prefix"] == "66022021-66022021"
# Test interleave()
# ============================================================================

class TestInterleave:
    """Test array interleaving functionality."""

    def test_basic_interleave(self):
        """Basic interleave of two arrays should work."""
        data = {
            "step1": ["a", "b", "c"],
            "step2": ["x", "y", "z"]
        }
        result = interleave(data)
        assert len(result) == 3
        assert result[0] == {"step1": "a", "step2": "x"}
        assert result[1] == {"step1": "b", "step2": "y"}
        assert result[2] == {"step1": "c", "step2": "z"}

    def test_three_arrays(self):
        """Interleave of three arrays should work."""
        data = {
            "step1": [1, 2],
            "step2": [3, 4],
            "step3": [5, 6]
        }
        result = interleave(data)
        assert len(result) == 2
        assert result[0] == {"step1": 1, "step2": 3, "step3": 5}
        assert result[1] == {"step1": 2, "step2": 4, "step3": 6}

    def test_single_item_arrays(self):
        """Interleave of single-item arrays should work."""
        data = {
            "step1": ["only"],
            "step2": ["one"]
        }
        result = interleave(data)
        assert len(result) == 1
        assert result[0] == {"step1": "only", "step2": "one"}

    def test_empty_dict_returns_empty_list(self):
        """Empty dict should return empty list."""
        result = interleave({})
        assert result == []

    def test_empty_dict_markdown_returns_empty_string(self):
        """Empty dict with markdown format should return empty string."""
        result = interleave({}, output_format="markdown")
        assert result == ""

    def test_interleave_preserves_types(self):
        """Interleave should preserve value types."""
        data = {
            "numbers": [1, 2, 3],
            "strings": ["a", "b", "c"],
            "bools": [True, False, True]
        }
        result = interleave(data)
        assert result[0]["numbers"] == 1
        assert result[0]["strings"] == "a"
        assert result[0]["bools"] is True
        assert isinstance(result[0]["numbers"], int)
        assert isinstance(result[0]["strings"], str)
        assert isinstance(result[0]["bools"], bool)

    def test_markdown_output_format(self):
        """Markdown output should be formatted as string."""
        data = {
            "step1": ["Content A"],
            "step2": ["Content B"]
        }
        result = interleave(data, output_format="markdown")
        assert isinstance(result, str)
        assert "Scene 1" in result
        assert "Content A" in result
        assert "Content B" in result

    def test_markdown_output_multiple_scenes(self):
        """Markdown with multiple scenes should number them."""
        data = {
            "step1": ["Scene 1 Content", "Scene 2 Content"],
            "step2": ["More A", "More B"]
        }
        result = interleave(data, output_format="markdown")
        assert "Scene 1" in result
        assert "Scene 2" in result
        assert "Scene 1 Content" in result
        assert "Scene 2 Content" in result

    def test_json_output_default(self):
        """Default output (no format) should return list."""
        data = {
            "step1": ["a"],
            "step2": ["b"]
        }
        result = interleave(data)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_none_output_format_returns_list(self):
        """Explicit None output format should return list."""
        data = {
            "step1": ["a"],
            "step2": ["b"]
        }
        result = interleave(data, output_format=None)
        assert isinstance(result, list)


# ============================================================================
# Test flatten_dict()
# ============================================================================

class TestFlattenDict:
    """Test nested dictionary flattening."""

    def test_simple_nested_dict(self):
        """Simple nested dict should flatten with dots."""
        nested = {
            "user": {
                "name": "John",
                "age": 30
            }
        }
        result = flatten_dict(nested)
        assert result == {
            "user.name": "John",
            "user.age": 30
        }

    def test_deeply_nested_dict(self):
        """Deeply nested dict should flatten all levels."""
        nested = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            }
        }
        result = flatten_dict(nested)
        assert result == {"level1.level2.level3.value": "deep"}

    def test_mixed_nesting(self):
        """Mixed nesting levels should all flatten correctly."""
        nested = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3
                }
            },
            "f": 4
        }
        result = flatten_dict(nested)
        assert result == {
            "a": 1,
            "b.c": 2,
            "b.d.e": 3,
            "f": 4
        }

    def test_custom_separator(self):
        """Custom separator should be used instead of dot."""
        nested = {
            "user": {
                "name": "John"
            }
        }
        result = flatten_dict(nested, separator="_")
        assert result == {"user_name": "John"}

    def test_underscore_separator(self):
        """Underscore separator should work."""
        nested = {
            "config": {
                "database": {
                    "host": "localhost"
                }
            }
        }
        result = flatten_dict(nested, separator="_")
        assert result == {"config_database_host": "localhost"}

    def test_slash_separator(self):
        """Slash separator should work."""
        nested = {
            "path": {
                "to": {
                    "file": "test.txt"
                }
            }
        }
        result = flatten_dict(nested, separator="/")
        assert result == {"path/to/file": "test.txt"}

    def test_empty_dict(self):
        """Empty dict should return empty dict."""
        result = flatten_dict({})
        assert result == {}

    def test_already_flat_dict(self):
        """Already flat dict should remain unchanged."""
        flat = {"a": 1, "b": 2, "c": 3}
        result = flatten_dict(flat)
        assert result == flat

    def test_preserves_value_types(self):
        """Flattening should preserve value types."""
        nested = {
            "data": {
                "string": "text",
                "number": 42,
                "float": 3.14,
                "bool": True,
                "none": None
            }
        }
        result = flatten_dict(nested)
        assert result["data.string"] == "text"
        assert result["data.number"] == 42
        assert result["data.float"] == 3.14
        assert result["data.bool"] is True
        assert result["data.none"] is None
        assert isinstance(result["data.string"], str)
        assert isinstance(result["data.number"], int)
        assert isinstance(result["data.float"], float)
        assert isinstance(result["data.bool"], bool)

    def test_list_values_not_flattened(self):
        """Lists should remain as values, not be flattened."""
        nested = {
            "user": {
                "tags": ["admin", "user"]
            }
        }
        result = flatten_dict(nested)
        assert result == {"user.tags": ["admin", "user"]}
        assert isinstance(result["user.tags"], list)

    def test_multiple_branches(self):
        """Multiple branches should all flatten correctly."""
        nested = {
            "branch1": {
                "leaf1": "A",
                "leaf2": "B"
            },
            "branch2": {
                "leaf3": "C",
                "leaf4": "D"
            }
        }
        result = flatten_dict(nested)
        assert result == {
            "branch1.leaf1": "A",
            "branch1.leaf2": "B",
            "branch2.leaf3": "C",
            "branch2.leaf4": "D"
        }

    def test_numeric_keys_converted_to_strings(self):
        """Numeric dict keys should be converted to strings."""
        nested = {
            "data": {
                1: "one",
                2: "two"
            }
        }
        result = flatten_dict(nested)
        # Keys should be stringified
        assert "data.1" in result
        assert "data.2" in result

    def test_complex_real_world_example(self):
        """Complex real-world example should flatten correctly."""
        nested = {
            "pipeline": {
                "name": "test",
                "config": {
                    "llm": {
                        "model": "gpt-4o",
                        "temperature": 0.7
                    },
                    "output": {
                        "format": "json",
                        "path": "/tmp/output"
                    }
                }
            }
        }
        result = flatten_dict(nested)
        assert result["pipeline.name"] == "test"
        assert result["pipeline.config.llm.model"] == "gpt-4o"
        assert result["pipeline.config.llm.temperature"] == 0.7
        assert result["pipeline.config.output.format"] == "json"
        assert result["pipeline.config.output.path"] == "/tmp/output"


# ============================================================================
# Integration and Edge Cases
# ============================================================================

class TestDataUtilitiesIntegration:
    """Test integration scenarios and edge cases."""

    def test_parse_and_flatten_together(self):
        """Parse Bible reference and flatten result."""
        parsed = parse_bible_reference("John 3:16")
        flattened = flatten_dict({"reference": parsed})

        assert flattened["reference.book_name"] == "John"
        assert flattened["reference.chapter"] == 3
        assert flattened["reference.start_verse"] == 16

    def test_interleave_and_flatten_together(self):
        """Interleave data and flatten results."""
        data = {
            "step1": [{"a": 1}],
            "step2": [{"b": 2}]
        }
        interleaved = interleave(data)
        # interleaved[0] = {"step1": {"a": 1}, "step2": {"b": 2}}
        flattened = flatten_dict(interleaved[0])

        assert flattened["step1.a"] == 1
        assert flattened["step2.b"] == 2

    def test_all_66_books_parseable(self):
        """Verify all 66 books are recognized by name."""
        books = [
            "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
            "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
            "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
            "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
            "Ecclesiastes", "Song of Songs", "Isaiah", "Jeremiah", "Lamentations",
            "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
            "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
            "Zephaniah", "Haggai", "Zechariah", "Malachi",
            "Matthew", "Mark", "Luke", "John", "Acts",
            "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
            "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
            "1 Timothy", "2 Timothy", "Titus", "Philemon",
            "Hebrews", "James", "1 Peter", "2 Peter",
            "1 John", "2 John", "3 John", "Jude", "Revelation"
        ]

        for book in books:
            result = parse_bible_reference(f"{book} 1:1")
            assert result["book_name"] == book
            assert result["chapter"] == 1
            assert result["start_verse"] == 1
