"""Tests: searching the resource catalog with XPath.

`sp resource list` shows only entries with a `provides` block — 3 of 70 — under a legend that
reads as a full inventory, and nothing listed the rest. A downstream session concluded the engine
did not know Levinsohn's corpus and proposed hand-writing an absolute path to a manual clone.

The catalog is JSON, but the query language is real XPath: the entries are built into an
in-memory tree and `lxml` evaluates against it, so there is no query language of ours to write,
document, or let drift. `contains(., "…")` is free-text because XPath concatenates element text.

`lower-case()` and `matches()` are XPath 2.0 and lxml implements 1.0, so both are registered as
extension functions with their real semantics — `matches()` is regex with a flags argument, not
containment. They are scoped to the query rather than registered globally, so they cannot leak
into the XPath and XSLT plugins.
"""

import pytest

from llmflow import resources


def _ids(hits):
    return sorted(entry["id"] for entry in hits)


# ---------------------------------------------------------------------------
# The keyword shorthand
# ---------------------------------------------------------------------------

class TestKeywordShorthand:

    def test_a_bare_word_searches_every_field(self):
        assert "levinsohn-lgntdf" in _ids(resources.search("discourse"))

    def test_a_bare_word_is_case_insensitive(self):
        assert _ids(resources.search("DISCOURSE")) == _ids(resources.search("discourse"))

    def test_a_bare_word_matches_an_id(self):
        assert "gbi-lowfat" in _ids(resources.search("lowfat"))

    def test_a_hyphenated_word_is_still_a_keyword(self):
        assert "levinsohn-lgntdf" in _ids(resources.search("levinsohn-lgntdf"))

    def test_no_match_is_an_empty_list(self):
        assert resources.search("zzzznotathing") == []


# ---------------------------------------------------------------------------
# Real XPath
# ---------------------------------------------------------------------------

class TestXPathQueries:

    def test_free_text_contains(self):
        assert "levinsohn-lgntdf" in _ids(resources.search('contains(., "discourse")'))

    def test_a_field_scoped_contains(self):
        hits = _ids(resources.search('contains(category, "Treebank")'))
        assert "gbi-lowfat" in hits
        assert "levinsohn-lgntdf" not in hits

    def test_starts_with(self):
        hits = _ids(resources.search('starts-with(id, "morphgnt")'))
        assert hits and all(h.startswith("morphgnt") for h in hits)

    def test_boolean_composition(self):
        hits = _ids(resources.search('contains(., "greek") and not(contains(category, "Lexicon"))'))
        assert hits
        assert all("lexicon" not in h for h in hits)

    def test_an_attribute_selects_readable_entries(self):
        # A search returns *catalog entries*, and one entry may provide several readable
        # resources: `macula-greek-nt` provides `SBLGNT`. So these are the entry ids, not the
        # resource ids `readable()` is keyed by — a distinction the listing command blurs.
        hits = _ids(resources.search('@readable = "true"'))
        assert hits == ["bsb", "macula-greek-nt", "macula-hebrew"]
        assert all(entry.get("provides") for entry in resources.search('@readable = "true"'))

    def test_lower_case_is_available(self):
        assert "levinsohn-lgntdf" in _ids(
            resources.search('contains(lower-case(name), "levinsohn")')
        )

    def test_matches_is_a_regex_not_a_containment(self):
        assert "levinsohn-lgntdf" in _ids(resources.search('matches(id, "^levinsohn-")'))

    def test_matches_takes_a_flags_argument(self):
        assert "levinsohn-lgntdf" in _ids(resources.search('matches(name, "LEVINSOHN", "i")'))

    def test_a_regex_that_matches_nothing(self):
        assert resources.search('matches(id, "^zzz")') == []


# ---------------------------------------------------------------------------
# What a search covers, and what it returns
# ---------------------------------------------------------------------------

class TestScopeAndShape:

    def test_the_whole_catalog_is_searched_not_only_readable_entries(self):
        # The defect this exists to fix: `levinsohn-lgntdf` has no `provides` block, so it never
        # appeared in `sp resource list`.
        assert "levinsohn-lgntdf" not in resources.readable()
        assert "levinsohn-lgntdf" in _ids(resources.search("levinsohn"))

    def test_a_hit_is_the_catalog_entry_itself(self):
        hit = resources.search("levinsohn-lgntdf")[0]
        assert hit["id"] == "levinsohn-lgntdf"
        assert hit["github"].startswith("https://")
        assert "acquire" in hit

    def test_an_empty_query_is_refused(self):
        with pytest.raises(ValueError):
            resources.search("")

    def test_a_malformed_query_is_refused_with_the_query_in_the_message(self):
        with pytest.raises(ValueError) as raised:
            resources.search('contains(name, "unclosed')
        assert "contains(name" in str(raised.value)

    def test_an_unknown_function_is_refused_rather_than_raised_through(self):
        with pytest.raises(ValueError):
            resources.search('no-such-function(name)')


# ---------------------------------------------------------------------------
# The extensions stay scoped to the query
# ---------------------------------------------------------------------------

class TestExtensionsDoNotLeak:

    def test_lower_case_is_not_registered_globally(self):
        from lxml import etree

        resources.search('contains(lower-case(id), "levinsohn")')
        tree = etree.fromstring("<a><b>X</b></a>")
        with pytest.raises(etree.XPathEvalError):
            tree.xpath("//b[lower-case(.)]")
