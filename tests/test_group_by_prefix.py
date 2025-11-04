import pytest
from pathlib import Path
from llmflow.utils.get_prefix_directory import strip_diacritics, get_prefix_directory


class TestGroupByPrefix:
    """Test the group_by_prefix feature for saveas."""

    def test_strip_diacritics(self):
        """Test diacritic removal."""
        assert strip_diacritics("σύ") == "συ"
        assert strip_diacritics("Ἀβαδδών") == "Αβαδδων"
        assert strip_diacritics("café") == "cafe"
        assert strip_diacritics("naïve") == "naive"

    def test_get_prefix_directory_two_chars(self):
        """Test default 2-character prefix."""
        assert get_prefix_directory("σύ.md") == "συ"
        assert get_prefix_directory("Ἀβαδδών.md") == "αβ"
        assert get_prefix_directory("hello.txt") == "he"

    def test_get_prefix_directory_lowercase(self):
        """Test that output is always lowercase."""
        assert get_prefix_directory("HELLO.md") == "he"
        assert get_prefix_directory("Hello.md") == "he"
        assert get_prefix_directory("Ἀβαδδών.md") == "αβ"
        assert get_prefix_directory("ΣΎ.md") == "συ"

    def test_get_prefix_directory_hebrew(self):
        """Test Hebrew filenames."""
        assert get_prefix_directory("אָדָם.md") == "אד"
        assert get_prefix_directory("שָׁלוֹם.md") == "של"
        assert get_prefix_directory("תּוֹרָה.md") == "תו"
        assert get_prefix_directory("א.md") == "א"

    def test_get_prefix_directory_mandarin(self):
        """Test Mandarin (Chinese) filenames."""
        assert get_prefix_directory("你好.md") == "你好"
        assert get_prefix_directory("中国.md") == "中国"
        assert get_prefix_directory("道德经.md") == "道德"
        assert get_prefix_directory("爱.md") == "爱"

    def test_get_prefix_directory_one_char(self):
        """Test single character filename."""
        assert get_prefix_directory("σ.md") == "σ"
        assert get_prefix_directory("A.md") == "a"
        assert get_prefix_directory("Σ.md") == "σ"

    def test_get_prefix_directory_custom_length(self):
        """Test custom prefix length."""
        assert get_prefix_directory("hello.md", prefix_length=3) == "hel"
        assert get_prefix_directory("HELLO.md", prefix_length=3) == "hel"
        assert get_prefix_directory("hi.md", prefix_length=3) == "hi"
        assert get_prefix_directory("a.md", prefix_length=3) == "a"
        # Hebrew with custom length - שלום has 4 chars after stripping
        assert get_prefix_directory("שָׁלוֹם.md", prefix_length=3) == "שלו"