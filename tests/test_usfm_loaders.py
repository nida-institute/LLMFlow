"""Tests for USFM/USX/USJ loader functions.

Uses a small synthetic Paratext-style project in tests/fixtures/usfm/TestProject/.
All tests use book codes (not numbers) to identify books.
"""
import os
import pytest
from pathlib import Path
from lxml import etree

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "usfm"
PROJECT = "TestProject"


# ---------------------------------------------------------------------------
# list_usfm_books
# ---------------------------------------------------------------------------

def test_list_usfm_books_returns_canonical_order():
    from llmflow.utils.data import list_usfm_books
    books = list_usfm_books(str(FIXTURES_DIR), PROJECT)
    assert books == ["MAT", "LUK"]  # canonical order: Matthew before Luke


def test_list_usfm_books_returns_list_of_strings():
    from llmflow.utils.data import list_usfm_books
    books = list_usfm_books(str(FIXTURES_DIR), PROJECT)
    assert isinstance(books, list)
    assert all(isinstance(b, str) for b in books)


def test_list_usfm_books_empty_dir_returns_empty_list(tmp_path):
    from llmflow.utils.data import list_usfm_books
    proj = tmp_path / "EmptyProject"
    proj.mkdir()
    assert list_usfm_books(str(tmp_path), "EmptyProject") == []


def test_list_usfm_books_missing_dir_raises():
    from llmflow.utils.data import list_usfm_books
    with pytest.raises(FileNotFoundError):
        list_usfm_books("/nonexistent/path", "NoProject")


# ---------------------------------------------------------------------------
# load_usfm_book
# ---------------------------------------------------------------------------

def test_load_usfm_book_returns_usx_element():
    from llmflow.utils.data import load_usfm_book
    result = load_usfm_book(str(FIXTURES_DIR), PROJECT, "LUK", format="usx")
    assert isinstance(result, etree._Element)


def test_load_usfm_book_returns_usj_dict():
    from llmflow.utils.data import load_usfm_book
    result = load_usfm_book(str(FIXTURES_DIR), PROJECT, "LUK", format="usj")
    assert isinstance(result, dict)
    assert result.get("type") == "USJ"
    assert isinstance(result.get("content"), list)


def test_load_usfm_book_usx_contains_expected_content():
    from llmflow.utils.data import load_usfm_book
    result = load_usfm_book(str(FIXTURES_DIR), PROJECT, "LUK", format="usx")
    # Root element should be usx
    assert result.tag.lower() in ("usx", "{http://www.w3.org/XML/1998/namespace}usx") or "usx" in result.tag.lower()


def test_load_usfm_book_not_found_raises_value_error():
    from llmflow.utils.data import load_usfm_book
    with pytest.raises(ValueError, match="GEN"):
        load_usfm_book(str(FIXTURES_DIR), PROJECT, "GEN", format="usx")


def test_load_usfm_book_missing_dir_raises_file_not_found():
    from llmflow.utils.data import load_usfm_book
    with pytest.raises(FileNotFoundError):
        load_usfm_book("/nonexistent/path", "NoProject", "LUK", format="usx")


def test_load_usfm_book_invalid_format_raises():
    from llmflow.utils.data import load_usfm_book
    with pytest.raises(ValueError, match="format"):
        load_usfm_book(str(FIXTURES_DIR), PROJECT, "LUK", format="xml")


# ---------------------------------------------------------------------------
# load_usfm_passage
# ---------------------------------------------------------------------------

def test_load_usfm_passage_whole_book_usj():
    from llmflow.utils.data import load_usfm_passage
    result = load_usfm_passage(str(FIXTURES_DIR), PROJECT, "LUK", format="usj")
    assert isinstance(result, dict)
    assert result.get("type") == "USJ"


def test_load_usfm_passage_whole_book_usx():
    from llmflow.utils.data import load_usfm_passage
    result = load_usfm_passage(str(FIXTURES_DIR), PROJECT, "LUK", format="usx")
    assert isinstance(result, etree._Element)


def test_load_usfm_passage_chapter_usj():
    from llmflow.utils.data import load_usfm_passage
    result = load_usfm_passage(str(FIXTURES_DIR), PROJECT, "LUK 1", format="usj")
    assert isinstance(result, dict)
    # Should contain content from chapter 1
    content = result.get("content", [])
    assert len(content) > 0


def test_load_usfm_passage_chapter_excludes_other_chapters():
    from llmflow.utils.data import load_usfm_passage
    result = load_usfm_passage(str(FIXTURES_DIR), PROJECT, "LUK 1", format="usj")
    content = result.get("content", [])
    chapter_markers = [
        item.get("number") for item in content
        if isinstance(item, dict) and item.get("type") == "chapter"
    ]
    # Should only contain chapter 1, not chapter 2
    assert chapter_markers == [] or all(int(n) == 1 for n in chapter_markers if n)


def test_load_usfm_passage_verse_range_raises_not_implemented():
    from llmflow.utils.data import load_usfm_passage
    with pytest.raises(NotImplementedError):
        load_usfm_passage(str(FIXTURES_DIR), PROJECT, "LUK 1:1-3", format="usj")


def test_load_usfm_passage_bad_book_raises_value_error():
    from llmflow.utils.data import load_usfm_passage
    with pytest.raises(ValueError):
        load_usfm_passage(str(FIXTURES_DIR), PROJECT, "GEN", format="usj")


# ---------------------------------------------------------------------------
# export_usx
# ---------------------------------------------------------------------------

def test_export_usx_writes_files(tmp_path):
    from llmflow.utils.data import export_usx
    out = export_usx(str(FIXTURES_DIR), PROJECT, str(tmp_path))
    assert out == str(tmp_path)
    files = list(tmp_path.iterdir())
    assert len(files) == 2  # LUK and MAT
    names = {f.name for f in files}
    assert any("LUK" in n for n in names)
    assert any("MAT" in n for n in names)


def test_export_usx_files_are_valid_xml(tmp_path):
    from llmflow.utils.data import export_usx
    export_usx(str(FIXTURES_DIR), PROJECT, str(tmp_path))
    for f in tmp_path.iterdir():
        tree = etree.parse(str(f))
        assert tree.getroot() is not None


def test_export_usx_preserves_project_filename_prefix(tmp_path):
    from llmflow.utils.data import export_usx
    export_usx(str(FIXTURES_DIR), PROJECT, str(tmp_path))
    names = {f.name for f in tmp_path.iterdir()}
    # Original files are 42LUK.sfm and 40MAT.sfm — output should keep the prefix
    assert any(n.startswith("42") for n in names)
    assert any(n.startswith("40") for n in names)


# ---------------------------------------------------------------------------
# load_usfm_project
# ---------------------------------------------------------------------------

def test_load_usfm_project_returns_dict():
    from llmflow.utils.data import load_usfm_project
    result = load_usfm_project(str(FIXTURES_DIR), PROJECT, format="usx")
    assert isinstance(result, dict)
    assert set(result.keys()) == {"MAT", "LUK"}


def test_load_usfm_project_usx_values_are_elements():
    from llmflow.utils.data import load_usfm_project
    from lxml.etree import _Element
    result = load_usfm_project(str(FIXTURES_DIR), PROJECT, format="usx")
    for v in result.values():
        assert isinstance(v, _Element)


def test_load_usfm_project_usj_values_are_dicts():
    from llmflow.utils.data import load_usfm_project
    result = load_usfm_project(str(FIXTURES_DIR), PROJECT, format="usj")
    for v in result.values():
        assert isinstance(v, dict)
