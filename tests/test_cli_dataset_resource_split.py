"""Tests: `sp dataset` and `sp resource` name the two layers separately.

One command noun covered both, and the help text showed the conflation without noticing:
`sp resource add WLC` took an inner id while `sp resource download acai` took an outer one, and
both were described as "Catalog id". A downstream session read `sp resource list`, saw only inner
items, and concluded the catalog did not know an outer one.

  dataset   an obtainable body of data — a repository or a download. The catalog lists these.
  resource  a readable text inside one, carrying a reader and a versification.

Searching is a question about the catalog, so it belongs to `dataset`.
"""

import subprocess
import sys

import pytest


def _sp(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "llmflow.cli", *args], capture_output=True, text=True
    )


class TestDatasetCommand:

    def test_search_lives_under_dataset(self):
        result = _sp("dataset", "search", "discourse")
        assert result.returncode == 0, result.stderr
        assert "levinsohn-lgntdf" in result.stdout

    def test_search_takes_an_xpath_predicate(self):
        result = _sp("dataset", "search", 'contains(category, "Treebank")')
        assert result.returncode == 0, result.stderr
        assert "gbi-lowfat" in result.stdout

    def test_a_malformed_query_fails_without_a_traceback(self):
        result = _sp("dataset", "search", 'contains(name, "unclosed')
        assert result.returncode != 0
        assert "Traceback" not in result.stderr

    def test_dataset_list_shows_what_the_machine_has(self):
        result = _sp("dataset", "list")
        assert result.returncode == 0, result.stderr


class TestResourceCommand:

    def test_resource_list_still_lists_readable_texts(self):
        result = _sp("resource", "list")
        assert result.returncode == 0, result.stderr
        assert "SBLGNT" in result.stdout

    def test_the_legend_points_at_dataset_search(self):
        result = _sp("resource", "list")
        assert "sp dataset search" in result.stdout

    def test_search_is_no_longer_under_resource(self):
        result = _sp("resource", "search", "discourse")
        assert result.returncode != 0
