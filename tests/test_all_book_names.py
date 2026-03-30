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

from llmflow.utils.data import parse_bible_reference


class TestAllBookNamesValid:
    """Test that every book name/abbreviation is a valid parseable reference"""

    # This is the complete list of book names from parse_bible_reference
    # Each tuple is (abbreviation/name, expected_book_number, expected_book_name, expected_book_code)
    BOOK_ENTRIES = [
        # Old Testament
        ("Genesis", "01", "Genesis", "GEN"),
        ("Gen", "01", "Genesis", "GEN"),
        ("Ge", "01", "Genesis", "GEN"),
        ("Gn", "01", "Genesis", "GEN"),
        ("Exodus", "02", "Exodus", "EXO"),
        ("Exod", "02", "Exodus", "EXO"),
        ("Exo", "02", "Exodus", "EXO"),
        ("Ex", "02", "Exodus", "EXO"),
        ("Leviticus", "03", "Leviticus", "LEV"),
        ("Lev", "03", "Leviticus", "LEV"),
        ("Le", "03", "Leviticus", "LEV"),
        ("Lv", "03", "Leviticus", "LEV"),
        ("Numbers", "04", "Numbers", "NUM"),
        ("Num", "04", "Numbers", "NUM"),
        ("Nu", "04", "Numbers", "NUM"),
        ("Nm", "04", "Numbers", "NUM"),
        ("Deuteronomy", "05", "Deuteronomy", "DEU"),
        ("Deut", "05", "Deuteronomy", "DEU"),
        ("Dt", "05", "Deuteronomy", "DEU"),
        ("De", "05", "Deuteronomy", "DEU"),
        ("Joshua", "06", "Joshua", "JOS"),
        ("Josh", "06", "Joshua", "JOS"),
        ("Jos", "06", "Joshua", "JOS"),
        ("Jsh", "06", "Joshua", "JOS"),
        ("Judges", "07", "Judges", "JDG"),
        ("Judg", "07", "Judges", "JDG"),
        ("Jdg", "07", "Judges", "JDG"),
        ("Jg", "07", "Judges", "JDG"),
        ("Ruth", "08", "Ruth", "RUT"),
        ("Rut", "08", "Ruth", "RUT"),
        ("Ru", "08", "Ruth", "RUT"),
        ("Rt", "08", "Ruth", "RUT"),
        ("1 Samuel", "09", "1 Samuel", "1SA"),
        ("1Sam", "09", "1 Samuel", "1SA"),
        ("1Sa", "09", "1 Samuel", "1SA"),
        ("1S", "09", "1 Samuel", "1SA"),
        ("1 Sam", "09", "1 Samuel", "1SA"),
        ("2 Samuel", "10", "2 Samuel", "2SA"),
        ("2Sam", "10", "2 Samuel", "2SA"),
        ("2Sa", "10", "2 Samuel", "2SA"),
        ("2S", "10", "2 Samuel", "2SA"),
        ("2 Sam", "10", "2 Samuel", "2SA"),
        ("1 Kings", "11", "1 Kings", "1KI"),
        ("1Kgs", "11", "1 Kings", "1KI"),
        ("1Ki", "11", "1 Kings", "1KI"),
        ("1K", "11", "1 Kings", "1KI"),
        ("1 Kgs", "11", "1 Kings", "1KI"),
        ("2 Kings", "12", "2 Kings", "2KI"),
        ("2Kgs", "12", "2 Kings", "2KI"),
        ("2Ki", "12", "2 Kings", "2KI"),
        ("2K", "12", "2 Kings", "2KI"),
        ("2 Kgs", "12", "2 Kings", "2KI"),
        ("1 Chronicles", "13", "1 Chronicles", "1CH"),
        ("1Chron", "13", "1 Chronicles", "1CH"),
        ("1Chr", "13", "1 Chronicles", "1CH"),
        ("1Ch", "13", "1 Chronicles", "1CH"),
        ("1 Chr", "13", "1 Chronicles", "1CH"),
        ("2 Chronicles", "14", "2 Chronicles", "2CH"),
        ("2Chron", "14", "2 Chronicles", "2CH"),
        ("2Chr", "14", "2 Chronicles", "2CH"),
        ("2Ch", "14", "2 Chronicles", "2CH"),
        ("2 Chr", "14", "2 Chronicles", "2CH"),
        ("Ezra", "15", "Ezra", "EZR"),
        ("Ezr", "15", "Ezra", "EZR"),
        ("Nehemiah", "16", "Nehemiah", "NEH"),
        ("Neh", "16", "Nehemiah", "NEH"),
        ("Ne", "16", "Nehemiah", "NEH"),
        ("Esther", "17", "Esther", "EST"),
        ("Esth", "17", "Esther", "EST"),
        ("Est", "17", "Esther", "EST"),
        ("Es", "17", "Esther", "EST"),
        ("Job", "18", "Job", "JOB"),
        ("Jb", "18", "Job", "JOB"),
        ("Psalms", "19", "Psalms", "PSA"),
        ("Psalm", "19", "Psalms", "PSA"),
        ("Ps", "19", "Psalms", "PSA"),
        ("Psa", "19", "Psalms", "PSA"),
        ("Pss", "19", "Psalms", "PSA"),
        ("Proverbs", "20", "Proverbs", "PRO"),
        ("Prov", "20", "Proverbs", "PRO"),
        ("Pro", "20", "Proverbs", "PRO"),
        ("Pr", "20", "Proverbs", "PRO"),
        ("Ecclesiastes", "21", "Ecclesiastes", "ECC"),
        ("Eccl", "21", "Ecclesiastes", "ECC"),
        ("Ecc", "21", "Ecclesiastes", "ECC"),
        ("Ec", "21", "Ecclesiastes", "ECC"),
        ("Song of Songs", "22", "Song of Songs", "SNG"),
        ("Song", "22", "Song of Songs", "SNG"),
        ("Sos", "22", "Song of Songs", "SNG"),
        ("So", "22", "Song of Songs", "SNG"),
        ("Canticles", "22", "Song of Songs", "SNG"),
        ("Cant", "22", "Song of Songs", "SNG"),
        ("Isaiah", "23", "Isaiah", "ISA"),
        ("Isa", "23", "Isaiah", "ISA"),
        ("Is", "23", "Isaiah", "ISA"),
        ("Jeremiah", "24", "Jeremiah", "JER"),
        ("Jer", "24", "Jeremiah", "JER"),
        ("Je", "24", "Jeremiah", "JER"),
        ("Jr", "24", "Jeremiah", "JER"),
        ("Lamentations", "25", "Lamentations", "LAM"),
        ("Lam", "25", "Lamentations", "LAM"),
        ("La", "25", "Lamentations", "LAM"),
        ("Ezekiel", "26", "Ezekiel", "EZK"),
        ("Ezek", "26", "Ezekiel", "EZK"),
        ("Eze", "26", "Ezekiel", "EZK"),
        ("Daniel", "27", "Daniel", "DAN"),
        ("Dan", "27", "Daniel", "DAN"),
        ("Da", "27", "Daniel", "DAN"),
        ("Dn", "27", "Daniel", "DAN"),
        ("Hosea", "28", "Hosea", "HOS"),
        ("Hos", "28", "Hosea", "HOS"),
        ("Ho", "28", "Hosea", "HOS"),
        ("Joel", "29", "Joel", "JOL"),
        ("Joe", "29", "Joel", "JOL"),
        ("Jl", "29", "Joel", "JOL"),
        ("Amos", "30", "Amos", "AMO"),
        ("Amo", "30", "Amos", "AMO"),
        ("Am", "30", "Amos", "AMO"),
        ("Obadiah", "31", "Obadiah", "OBA"),
        ("Obad", "31", "Obadiah", "OBA"),
        ("Ob", "31", "Obadiah", "OBA"),
        ("Jonah", "32", "Jonah", "JON"),
        ("Jon", "32", "Jonah", "JON"),
        ("Jnh", "32", "Jonah", "JON"),
        ("Micah", "33", "Micah", "MIC"),
        ("Mic", "33", "Micah", "MIC"),
        ("Mi", "33", "Micah", "MIC"),
        ("Nahum", "34", "Nahum", "NAM"),
        ("Nah", "34", "Nahum", "NAM"),
        ("Na", "34", "Nahum", "NAM"),
        ("Habakkuk", "35", "Habakkuk", "HAB"),
        ("Hab", "35", "Habakkuk", "HAB"),
        ("Hb", "35", "Habakkuk", "HAB"),
        ("Zephaniah", "36", "Zephaniah", "ZEP"),
        ("Zeph", "36", "Zephaniah", "ZEP"),
        ("Zep", "36", "Zephaniah", "ZEP"),
        ("Zp", "36", "Zephaniah", "ZEP"),
        ("Haggai", "37", "Haggai", "HAG"),
        ("Hag", "37", "Haggai", "HAG"),
        ("Hg", "37", "Haggai", "HAG"),
        ("Zechariah", "38", "Zechariah", "ZEC"),
        ("Zech", "38", "Zechariah", "ZEC"),
        ("Zec", "38", "Zechariah", "ZEC"),
        ("Zc", "38", "Zechariah", "ZEC"),
        ("Malachi", "39", "Malachi", "MAL"),
        ("Mal", "39", "Malachi", "MAL"),
        ("Ml", "39", "Malachi", "MAL"),
        # New Testament
        ("Matthew", "40", "Matthew", "MAT"),
        ("Matt", "40", "Matthew", "MAT"),
        ("Mt", "40", "Matthew", "MAT"),
        ("Mat", "40", "Matthew", "MAT"),
        ("Mark", "41", "Mark", "MRK"),
        ("Mar", "41", "Mark", "MRK"),
        ("Mk", "41", "Mark", "MRK"),
        ("Mr", "41", "Mark", "MRK"),
        ("Luke", "42", "Luke", "LUK"),
        ("Luk", "42", "Luke", "LUK"),
        ("Lk", "42", "Luke", "LUK"),
        ("Lu", "42", "Luke", "LUK"),
        ("John", "43", "John", "JHN"),
        ("Joh", "43", "John", "JHN"),
        ("Jn", "43", "John", "JHN"),
        ("Jhn", "43", "John", "JHN"),
        ("Acts", "44", "Acts", "ACT"),
        ("Act", "44", "Acts", "ACT"),
        ("Ac", "44", "Acts", "ACT"),
        ("Romans", "45", "Romans", "ROM"),
        ("Rom", "45", "Romans", "ROM"),
        ("Ro", "45", "Romans", "ROM"),
        ("Rm", "45", "Romans", "ROM"),
        ("1 Corinthians", "46", "1 Corinthians", "1CO"),
        ("1Cor", "46", "1 Corinthians", "1CO"),
        ("1Co", "46", "1 Corinthians", "1CO"),
        ("1C", "46", "1 Corinthians", "1CO"),
        ("1 Cor", "46", "1 Corinthians", "1CO"),
        ("2 Corinthians", "47", "2 Corinthians", "2CO"),
        ("2Cor", "47", "2 Corinthians", "2CO"),
        ("2Co", "47", "2 Corinthians", "2CO"),
        ("2C", "47", "2 Corinthians", "2CO"),
        ("2 Cor", "47", "2 Corinthians", "2CO"),
        ("Galatians", "48", "Galatians", "GAL"),
        ("Gal", "48", "Galatians", "GAL"),
        ("Ga", "48", "Galatians", "GAL"),
        ("Ephesians", "49", "Ephesians", "EPH"),
        ("Eph", "49", "Ephesians", "EPH"),
        ("Ep", "49", "Ephesians", "EPH"),
        ("Philippians", "50", "Philippians", "PHP"),
        ("Phil", "50", "Philippians", "PHP"),
        ("Php", "50", "Philippians", "PHP"),
        ("Phi", "50", "Philippians", "PHP"),
        ("Colossians", "51", "Colossians", "COL"),
        ("Col", "51", "Colossians", "COL"),
        ("Co", "51", "Colossians", "COL"),
        ("1 Thessalonians", "52", "1 Thessalonians", "1TH"),
        ("1Thess", "52", "1 Thessalonians", "1TH"),
        ("1Th", "52", "1 Thessalonians", "1TH"),
        ("1 Thess", "52", "1 Thessalonians", "1TH"),
        ("1 Th", "52", "1 Thessalonians", "1TH"),
        ("2 Thessalonians", "53", "2 Thessalonians", "2TH"),
        ("2Thess", "53", "2 Thessalonians", "2TH"),
        ("2Th", "53", "2 Thessalonians", "2TH"),
        ("2 Thess", "53", "2 Thessalonians", "2TH"),
        ("2 Th", "53", "2 Thessalonians", "2TH"),
        ("1 Timothy", "54", "1 Timothy", "1TI"),
        ("1Tim", "54", "1 Timothy", "1TI"),
        ("1Ti", "54", "1 Timothy", "1TI"),
        ("1 Tim", "54", "1 Timothy", "1TI"),
        ("1 Ti", "54", "1 Timothy", "1TI"),
        ("2 Timothy", "55", "2 Timothy", "2TI"),
        ("2Tim", "55", "2 Timothy", "2TI"),
        ("2Ti", "55", "2 Timothy", "2TI"),
        ("2 Tim", "55", "2 Timothy", "2TI"),
        ("2 Ti", "55", "2 Timothy", "2TI"),
        ("Titus", "56", "Titus", "TIT"),
        ("Tit", "56", "Titus", "TIT"),
        ("Ti", "56", "Titus", "TIT"),
        ("Philemon", "57", "Philemon", "PHM"),
        ("Philem", "57", "Philemon", "PHM"),
        ("Phm", "57", "Philemon", "PHM"),
        ("Phlm", "57", "Philemon", "PHM"),
        ("Hebrews", "58", "Hebrews", "HEB"),
        ("Heb", "58", "Hebrews", "HEB"),
        ("He", "58", "Hebrews", "HEB"),
        ("James", "59", "James", "JAS"),
        ("Jas", "59", "James", "JAS"),
        ("Jm", "59", "James", "JAS"),
        ("Ja", "59", "James", "JAS"),
        ("1 Peter", "60", "1 Peter", "1PE"),
        ("1Pet", "60", "1 Peter", "1PE"),
        ("1Pe", "60", "1 Peter", "1PE"),
        ("1Pt", "60", "1 Peter", "1PE"),
        ("1P", "60", "1 Peter", "1PE"),
        ("1 Pet", "60", "1 Peter", "1PE"),
        ("2 Peter", "61", "2 Peter", "2PE"),
        ("2Pet", "61", "2 Peter", "2PE"),
        ("2Pe", "61", "2 Peter", "2PE"),
        ("2Pt", "61", "2 Peter", "2PE"),
        ("2P", "61", "2 Peter", "2PE"),
        ("2 Pet", "61", "2 Peter", "2PE"),
        ("1 John", "62", "1 John", "1JN"),
        ("1Joh", "62", "1 John", "1JN"),
        ("1Jn", "62", "1 John", "1JN"),
        ("1J", "62", "1 John", "1JN"),
        ("1 Joh", "62", "1 John", "1JN"),
        ("1John", "62", "1 John", "1JN"),
        ("2 John", "63", "2 John", "2JN"),
        ("2Joh", "63", "2 John", "2JN"),
        ("2Jn", "63", "2 John", "2JN"),
        ("2J", "63", "2 John", "2JN"),
        ("2 Joh", "63", "2 John", "2JN"),
        ("2John", "63", "2 John", "2JN"),
        ("3 John", "64", "3 John", "3JN"),
        ("3Joh", "64", "3 John", "3JN"),
        ("3Jn", "64", "3 John", "3JN"),
        ("3J", "64", "3 John", "3JN"),
        ("3 Joh", "64", "3 John", "3JN"),
        ("3John", "64", "3 John", "3JN"),
        ("Jude", "65", "Jude", "JUD"),
        ("Jud", "65", "Jude", "JUD"),
        ("Jd", "65", "Jude", "JUD"),
        ("Revelation", "66", "Revelation", "REV"),
        ("Rev", "66", "Revelation", "REV"),
        ("Re", "66", "Revelation", "REV"),
        ("Rv", "66", "Revelation", "REV"),
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
