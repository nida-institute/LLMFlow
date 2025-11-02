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