"""
Test that all book names and abbreviations in parse_bible_reference are valid.

This test ensures every entry in the book_numbers dictionary can be successfully
parsed as a valid Bible reference in both SBL and USFM conventions.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llmflow import books as _books
from llmflow.utils.data import parse_bible_reference


class TestAllBookNamesValid:
    """Test that every book name/abbreviation is a valid parseable reference"""

    # This is the complete list of book names from parse_bible_reference
    # Each tuple is (abbreviation/name, expected_book_number, expected_book_name, expected_book_code)
    # Derived from `data/book-names.json`, not copied from it. This list was a second
    # encoding of that file: 71 spellings were removed from the data and this list still
    # named them, so the suite failed on entries the engine had deliberately stopped
    # accepting. One declaration, read here. Rule `check-the-source-not-the-rendering`.
    BOOK_ENTRIES = [
        (spelling, entry["number"], entry["name"], code)
        for code, entry in _books.table().items()
        for spelling in (code, entry["name"], *entry["aliases"])
    ]

    @pytest.mark.parametrize("book_input,expected_number,expected_name,expected_code", BOOK_ENTRIES)
    def test_book_name_parses_successfully(
        self, book_input, expected_number, expected_name, expected_code
    ):
        """Test that each book name/abbreviation can be successfully parsed"""
        result = parse_bible_reference(book_input)

        assert result["book_name"] == expected_name, f"Book name mismatch for '{book_input}'"
        assert result["book_number"] == expected_number, f"Book number mismatch for '{book_input}'"
        assert result["book_code"] == expected_code, f"Book code mismatch for '{book_input}'"
        assert result.get("is_whole_book") is True, f"Should be whole book for '{book_input}'"
        assert result["filename_prefix"] == f"{expected_number}_book", f"Filename prefix mismatch for '{book_input}'"

    def test_all_66_books_covered(self):
        """Verify we have entries for all 66 canonical books"""
        unique_book_numbers = set(entry[1] for entry in self.BOOK_ENTRIES)

        # Should have all books from 01 (Genesis) to 66 (Revelation)
        expected_numbers = {f"{i:02d}" for i in range(1, 67)}

        assert unique_book_numbers == expected_numbers, (
            f"Missing book numbers: {expected_numbers - unique_book_numbers}\n"
            f"Extra book numbers: {unique_book_numbers - expected_numbers}"
        )

    def test_case_insensitive_parsing(self):
        """Test that book names work regardless of case"""
        test_cases = [
            "john",
            "JOHN",
            "John",
            "JoHn",
            "genesis",
            "GENESIS",
            "Genesis",
        ]

        for book_name in test_cases:
            result = parse_bible_reference(book_name)
            assert result["book_name"] in ["John", "Genesis"], f"Failed to parse '{book_name}'"

    def test_book_with_chapter_still_works(self):
        """Ensure adding chapter references still works after book-only parsing"""
        result = parse_bible_reference("John 3:16")
        assert result["book_name"] == "John"
        assert result["chapter"] == 3
        assert result["start_verse"] == 16
        assert result.get("is_whole_book") is not True

    def test_sbl_abbreviations(self):
        """Test common SBL-style abbreviations"""
        sbl_tests = [
            ("Gen", "Genesis"),
            ("Exod", "Exodus"),
            ("Deut", "Deuteronomy"),
            ("Josh", "Joshua"),
            ("1 Sam", "1 Samuel"),
            ("2 Kgs", "2 Kings"),
            ("Ps", "Psalms"),
            ("Prov", "Proverbs"),
            ("Isa", "Isaiah"),
            ("Jer", "Jeremiah"),
            ("Matt", "Matthew"),
            ("Rom", "Romans"),
            ("1 Cor", "1 Corinthians"),
            ("Gal", "Galatians"),
            ("Eph", "Ephesians"),
            ("Phil", "Philippians"),
            ("Rev", "Revelation"),
        ]

        for abbrev, expected_name in sbl_tests:
            result = parse_bible_reference(abbrev)
            assert result["book_name"] == expected_name, f"SBL abbreviation '{abbrev}' failed"

    def test_usfm_codes_present(self):
        """Verify USFM codes are present and valid"""
        # Sample USFM codes to verify
        usfm_tests = [
            ("Genesis", "GEN"),
            ("Matthew", "MAT"),
            ("Mark", "MRK"),
            ("Luke", "LUK"),
            ("John", "JHN"),
            ("Acts", "ACT"),
            ("Romans", "ROM"),
            ("1 Corinthians", "1CO"),
            ("Galatians", "GAL"),
            ("Ephesians", "EPH"),
            ("Revelation", "REV"),
        ]

        for book_name, expected_code in usfm_tests:
            result = parse_bible_reference(book_name)
            assert result["book_code"] == expected_code, f"USFM code mismatch for '{book_name}'"
