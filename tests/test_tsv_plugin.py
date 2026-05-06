"""Tests for TSV/CSV reader plugin."""

import csv
from pathlib import Path

import pytest

import llmflow.plugins
from llmflow.plugins.loader import discover_plugins
from llmflow.runner import resolve
from llmflow.plugins.tsv_reader import Row

# Ensure plugins are loaded
discover_plugins()


class TestTsvReader:
    """Test the TSV reader plugin."""

    @pytest.fixture
    def sample_tsv(self, tmp_path):
        """Create a sample TSV file."""
        tsv_file = tmp_path / "test.tsv"
        with open(tsv_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['lemma', 'status', 'count'])
            writer.writerow(['α', 'done', '10'])
            writer.writerow(['Ἀαρών', 'pending', '5'])
            writer.writerow(['Ἀβαδδών', 'done', '3'])
        return tsv_file

    def test_row_dot_notation(self, sample_tsv):
        """Test Row object allows dot notation access."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(sample_tsv)}))  # Convert to list

        row = rows[0]
        assert row.lemma == 'α'
        assert row.status == 'done'
        assert row.count == '10'

    def test_row_bracket_notation(self, sample_tsv):
        """Test Row object allows bracket notation access."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(sample_tsv)}))  # Convert to list

        row = rows[0]
        assert row['lemma'] == 'α'
        assert row['status'] == 'done'

    def test_row_to_dict(self, sample_tsv):
        """Test Row object can convert back to dict."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(sample_tsv)}))  # Convert to list

        row = rows[0]
        data = row.to_dict()
        assert data == {'lemma': 'α', 'status': 'done', 'count': '10'}

    def test_execute_reads_tsv(self, sample_tsv):
        """Test plugin reads TSV file correctly."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(sample_tsv)}))  # Convert to list

        assert len(rows) == 3
        assert rows[0].lemma == 'α'
        assert rows[0].status == 'done'
        assert rows[0].count == '10'
        assert rows[1].lemma == 'Ἀαρών'
        assert rows[2].lemma == 'Ἀβαδδών'

    def test_execute_with_limit(self, sample_tsv):
        """Test plugin respects limit parameter."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({  # Convert to list
            "path": str(sample_tsv),
            "limit": 2
        }))

        assert len(rows) == 2
        assert rows[0].lemma == 'α'
        assert rows[1].lemma == 'Ἀαρών'

    def test_execute_with_from_keyword(self, sample_tsv):
        """Test plugin accepts 'from' as alternative to 'path'."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"from": str(sample_tsv)}))  # Convert to list

        assert len(rows) == 3

    def test_execute_csv_delimiter(self, tmp_path):
        """Test plugin can read CSV with comma delimiter."""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'value'])
            writer.writerow(['alpha', '1'])
            writer.writerow(['beta', '2'])

        # Use tsv plugin with delimiter parameter for CSV
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({
            "path": str(csv_file),
            "delimiter": ","
        }))

        assert len(rows) == 2
        assert rows[0].name == 'alpha'
        assert rows[0].value == '1'
        assert rows[1].name == 'beta'
        assert rows[1].value == '2'

    def test_execute_file_not_found(self):
        """Test plugin raises error for missing file."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]

        with pytest.raises(FileNotFoundError):
            list(plugin_func({"path": "/nonexistent/file.tsv"}))  # Force evaluation

    def test_execute_missing_path(self):
        """Test plugin raises error when path is missing."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]

        with pytest.raises(ValueError, match="requires 'path' or 'from'"):
            list(plugin_func({}))  # Force evaluation


class TestRowResolution:
    """Test that Row objects resolve correctly in variable substitution."""

    def test_resolve_row_dot_notation(self):
        """Test that ${row.lemma} resolves to the actual value."""
        row = Row({'lemma': 'λόγος', 'status': 'done', 'count': '42'})
        context = {'row': row}

        # Test dot notation
        result = resolve('${row.lemma}', context)
        assert result == 'λόγος'

        result = resolve('${row.status}', context)
        assert result == 'done'

        result = resolve('${row.count}', context)
        assert result == '42'

    def test_resolve_row_in_string(self):
        """Test that Row values resolve within strings."""
        row = Row({'lemma': 'λόγος', 'key': 'G3056'})
        context = {'row': row}

        # Test string interpolation
        result = resolve('outputs/markdown/${row.lemma}.md', context)
        assert result == 'outputs/markdown/λόγος.md'

        result = resolve('Entry ${row.key}: ${row.lemma}', context)
        assert result == 'Entry G3056: λόγος'

    def test_resolve_row_in_xpath(self):
        """Test that Row values work in XPath expressions."""
        row = Row({'lemma': 'α', 'id': '123'})
        context = {'row': row}

        result = resolve("//tei:entry[@key='${row.lemma}']", context)
        assert result == "//tei:entry[@key='α']"


class TestTsvFiltering:
    """Test row filtering (where) and column selection (columns)."""

    @pytest.fixture
    def macula_tsv(self, tmp_path):
        """Create a macula-style TSV with book/chapter/verse/text/lemma/morph columns."""
        tsv_file = tmp_path / "macula.tsv"
        with open(tsv_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['book', 'chapter', 'verse', 'text', 'lemma', 'morph'])
            writer.writerow(['GEN', '1', '1', 'בְּרֵאשִׁ֖ית', 'רֵאשִׁית', 'HR/Ncfsa'])
            writer.writerow(['GEN', '1', '2', 'וְהָאָ֗רֶץ', 'אֶרֶץ', 'HC/Ncfsa'])
            writer.writerow(['GEN', '2', '1', 'וַיְכֻלּ֛וּ', 'כָּלָה', 'HVaw/Vqw3mp'])
            writer.writerow(['EXO', '1', '1', 'וְאֵ֗לֶּה', 'אֵלֶּה', 'HC/Pd3cp'])
        return tsv_file

    def test_where_single_condition(self, macula_tsv):
        """Filter rows by a single column equality."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_tsv), "where": "book == 'GEN'"}))
        assert len(rows) == 3
        assert all(r.book == 'GEN' for r in rows)

    def test_where_two_conditions(self, macula_tsv):
        """Filter rows by two AND-joined conditions."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_tsv), "where": "book == 'GEN' and chapter == '1'"}))
        assert len(rows) == 2
        assert all(r.book == 'GEN' and r.chapter == '1' for r in rows)

    def test_columns_projection(self, macula_tsv):
        """Returned Row objects contain only requested columns."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_tsv), "columns": ["text", "lemma", "morph"]}))
        assert len(rows) == 4
        assert rows[0].text == 'בְּרֵאשִׁ֖ית'
        assert rows[0].lemma == 'רֵאשִׁית'
        assert rows[0].morph == 'HR/Ncfsa'
        assert not hasattr(rows[0], 'book')
        assert not hasattr(rows[0], 'chapter')

    def test_where_and_columns_together(self, macula_tsv):
        """where filters rows, then columns projects the result."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({
            "path": str(macula_tsv),
            "where": "book == 'GEN' and chapter == '1'",
            "columns": ["text", "lemma", "morph"],
        }))
        assert len(rows) == 2
        assert not hasattr(rows[0], 'book')
        assert rows[0].text == 'בְּרֵאשִׁ֖ית'

    def test_limit_applied_after_where(self, macula_tsv):
        """limit counts post-filter rows, not raw rows."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({
            "path": str(macula_tsv),
            "where": "book == 'GEN'",
            "limit": 2,
        }))
        assert len(rows) == 2
        assert all(r.book == 'GEN' for r in rows)

    def test_unknown_column_in_columns_raises(self, macula_tsv):
        """Requesting a column not in the file raises ValueError."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        with pytest.raises(ValueError, match="nosuchcol"):
            list(plugin_func({"path": str(macula_tsv), "columns": ["text", "nosuchcol"]}))

    def test_where_unknown_column_yields_nothing(self, macula_tsv):
        """A where condition on a non-existent column matches no rows."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_tsv), "where": "nosuchcol == 'GEN'"}))
        assert rows == []

    def test_where_variable_already_resolved(self, macula_tsv):
        """Runner resolves ${vars} before calling plugin; show the pattern works."""
        context = {'book': 'EXO'}
        where = resolve("book == '${book}'", context)
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_tsv), "where": where}))
        assert len(rows) == 1
        assert rows[0].book == 'EXO'


class TestTsvStartswith:
    """Test startswith operator for prefix-encoded columns (e.g. Macula ref)."""

    @pytest.fixture
    def macula_ref_tsv(self, tmp_path):
        """Macula-style TSV where book/chapter/verse are encoded in ref."""
        tsv_file = tmp_path / "macula-greek.tsv"
        with open(tsv_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['ref', 'text', 'lemma', 'morph'])
            writer.writerow(['PHM 1:1!1', 'Παῦλος', 'Παῦλος', 'N-NMS'])
            writer.writerow(['PHM 1:1!2', 'δέσμιος', 'δέσμιος', 'N-NMS'])
            writer.writerow(['PHM 1:10!1', 'παρακαλῶ', 'παρακαλέω', 'V-PAI-1S'])
            writer.writerow(['COL 1:1!1', 'Παῦλος', 'Παῦλος', 'N-NMS'])
            writer.writerow(['COL 1:2!1', 'Τιμόθεος', 'Τιμόθεος', 'N-NMS'])
        return tsv_file

    def test_startswith_filters_by_book(self, macula_ref_tsv):
        """startswith filters Macula rows by book prefix."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_ref_tsv), "where": "ref startswith 'PHM '"}))
        assert len(rows) == 3
        assert all(r.ref.startswith('PHM ') for r in rows)

    def test_startswith_filters_by_verse(self, macula_ref_tsv):
        """startswith filters Macula rows to a specific verse."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_ref_tsv), "where": "ref startswith 'PHM 1:10'"}))
        assert len(rows) == 1
        assert rows[0].ref == 'PHM 1:10!1'

    def test_startswith_and_columns(self, macula_ref_tsv):
        """startswith combined with column projection."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({
            "path": str(macula_ref_tsv),
            "where": "ref startswith 'PHM '",
            "columns": ["ref", "lemma"],
        }))
        assert len(rows) == 3
        assert not hasattr(rows[0], 'morph')
        assert rows[0].lemma == 'Παῦλος'

    def test_startswith_with_resolved_variable(self, macula_ref_tsv):
        """startswith works with a pre-resolved book code variable."""
        context = {'book_code': 'COL'}
        where = resolve("ref startswith '${book_code} '", context)
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_ref_tsv), "where": where}))
        assert len(rows) == 2
        assert all(r.ref.startswith('COL ') for r in rows)

    def test_invalid_operator_raises(self, macula_ref_tsv):
        """Unsupported operator in where raises ValueError."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        with pytest.raises(ValueError, match="cannot parse"):
            list(plugin_func({"path": str(macula_ref_tsv), "where": "ref contains 'PHM'"}))


class TestTsvUsfmExtractors:
    """Test book(col)/chapter(col)/verse(col) USFM ref extractors in where."""

    @pytest.fixture
    def macula_ref_tsv(self, tmp_path):
        """Macula-style TSV: ref encodes BOOK chapter:verse!word."""
        tsv_file = tmp_path / "macula-greek.tsv"
        with open(tsv_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['ref', 'text', 'lemma', 'morph'])
            writer.writerow(['PHM 1:1!1',  'Παῦλος',   'Παῦλος',   'N-NMS'])
            writer.writerow(['PHM 1:1!2',  'δέσμιος',  'δέσμιος',  'N-NMS'])
            writer.writerow(['PHM 1:10!1', 'παρακαλῶ', 'παρακαλέω', 'V-PAI-1S'])
            writer.writerow(['COL 1:1!1',  'Παῦλος',   'Παῦλος',   'N-NMS'])
            writer.writerow(['COL 2:3!1',  'Χριστοῦ',  'Χριστός',   'N-GMS'])
        return tsv_file

    def test_book_extractor(self, macula_ref_tsv):
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_ref_tsv), "where": "book(ref) == 'PHM'"}))
        assert len(rows) == 3
        assert all(r.ref.startswith('PHM ') for r in rows)

    def test_chapter_extractor(self, macula_ref_tsv):
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_ref_tsv), "where": "chapter(ref) == '1'"}))
        assert len(rows) == 4  # PHM 1:1!1, PHM 1:1!2, PHM 1:10!1, COL 1:1!1

    def test_verse_extractor(self, macula_ref_tsv):
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_ref_tsv), "where": "verse(ref) == '10'"}))
        assert len(rows) == 1
        assert rows[0].ref == 'PHM 1:10!1'

    def test_book_and_chapter(self, macula_ref_tsv):
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({
            "path": str(macula_ref_tsv),
            "where": "book(ref) == 'COL' and chapter(ref) == '2'",
        }))
        assert len(rows) == 1
        assert rows[0].ref == 'COL 2:3!1'

    def test_book_extractor_with_columns(self, macula_ref_tsv):
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({
            "path": str(macula_ref_tsv),
            "where": "book(ref) == 'PHM'",
            "columns": ["ref", "lemma"],
        }))
        assert len(rows) == 3
        assert not hasattr(rows[0], 'morph')

    def test_book_extractor_with_resolved_variable(self, macula_ref_tsv):
        context = {'book_code': 'COL'}
        where = resolve("book(ref) == '${book_code}'", context)
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_ref_tsv), "where": where}))
        assert len(rows) == 2
        assert all(r.ref.startswith('COL ') for r in rows)

    def test_word_extractor(self, macula_ref_tsv):
        """word(ref) extracts the word index from BOOK chapter:verse!word."""
        plugin_func = llmflow.plugins.plugin_registry["tsv"]
        rows = list(plugin_func({"path": str(macula_ref_tsv), "where": "word(ref) == '2'"}))
        assert len(rows) == 1
        assert rows[0].ref == 'PHM 1:1!2'
