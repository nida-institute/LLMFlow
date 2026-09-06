"""Verse ranges — #169, designed in `design-verse-regions.md`.

#169 reports that four plugins each implement verse-range overlap. Reading them, the duplication is
worse and lower down: **five reference parsers** across the four files, three incompatible return
types, and **not one of them returns the book**. So `division_lookup.py:31` compares `Mark 1:1-5`
against `John 1:1-5` as overlapping — a defect that is structural rather than careless, because the
parsed type has nowhere to put a book.

The engine already parses references two ways, and this module adds no third: `parse_passage_ref`
gives the syntax as a `PassageRef`, and a scheme turns that into concrete verses. What was missing
is only the comparison layer.

**Books are distinct documents.** No range spans books, so ordinals are book-local:
`max_verses[book]` is all that is needed, and the schemes disagreeing on book inventory — 95 books
in `org` against 66 in `rsc` — stops mattering. Chapter-boundary adjacency, which the superseded
design treated as the hard case, becomes `a.end + 1 == b.start`.

**`overlaps` means the colloquial thing** — shares at least one verse, containment and equality
included. Allen's interval algebra reserves the word for the strictly partial case; every one of the
four plugins, and any pipeline author, means the other. The strict case is a configuration the
implementation handles and does not name.
"""

import pytest

from llmflow.utils.verse_ranges import (
    Range,
    contains,
    equals,
    overlaps,
    select,
    touches,
    verse_count,
)

ORG = "org"


def r(reference, scheme=ORG):
    return Range.parse(reference, scheme=scheme)


# --- the type, built once at the boundary ---------------------------------------------------


def test_a_range_carries_its_book():
    """The one thing all five plugin parsers threw away."""
    assert r("Mark 1:1-5").book == "MRK"


def test_a_single_verse_starts_and_ends_at_the_same_place():
    one = r("MRK 1:1")
    assert one.start == one.end


def test_a_whole_chapter_resolves_to_its_verses():
    """`Mark 1` is 45 verses in `org`, and the scheme is what says so."""
    assert verse_count(r("Mark 1")) == 45


def test_a_whole_book_resolves_to_its_chapters():
    """The existing parser leaves a bare book unresolved — `chapter=None`. A range with no
    concrete endpoints cannot be compared, so the constructor resolves it or there is nothing
    to build on."""
    mark = r("Mark")
    assert mark.start == 1
    assert verse_count(mark) == sum(int(n) for n in _chapters("MRK"))


def test_end_before_start_is_refused():
    """`parse_bible_reference("Mark 1:5-1:2")` returns it happily. An unconstructible illegal
    state is the whole point of parsing at the boundary — otherwise every downstream function
    needs a guard, and `division_lookup.py:40` shows what those guards turn into."""
    with pytest.raises(ValueError, match="Mark 1:5-1:2"):
        r("Mark 1:5-1:2")


def test_an_unknown_book_is_refused():
    with pytest.raises(ValueError, match="[Bb]lah"):
        r("Blah 1:1")


def test_a_verse_the_scheme_does_not_have_is_refused():
    with pytest.raises(ValueError, match="99"):
        r("Mark 1:99")


def test_a_book_the_scheme_does_not_carry_names_both():
    """`org` has 95 books, `rsc` 66. Failing at construction beats comparing `False` against
    everything, which reads as a legitimate answer."""
    assert r("1MA 1:1", scheme="org").book == "1MA"
    with pytest.raises(ValueError, match="rsc"):
        r("1MA 1:1", scheme="rsc")


def test_there_is_no_default_scheme():
    """A reference is not a location until a scheme is named, so there is nothing to default to."""
    with pytest.raises(TypeError):
        Range.parse("Mark 1:1")


# --- ordinals are book-local ----------------------------------------------------------------


def test_the_same_chapter_and_verse_in_two_books_share_an_ordinal():
    """Which is only sound because books are distinct documents: an ordinal is never compared
    across books, so it needs no canon order and no book sequence."""
    assert r("MRK 1:1").start == r("LUK 1:1").start


def test_a_chapter_boundary_is_one_step():
    """Mark 1 has 45 verses in `org`, so 1:45 and 2:1 are adjacent. This is the case the
    superseded design called the hardest; with ordinals it is `+ 1`."""
    assert r("MRK 1:45").end + 1 == r("MRK 2:1").start


# --- overlaps: the colloquial sense ----------------------------------------------------------


def test_overlaps_when_they_share_a_verse():
    assert overlaps(r("Mark 1:1-5"), r("Mark 1:5-10"))


def test_overlaps_is_symmetric():
    a, b = r("Mark 1:1-5"), r("Mark 1:3-8")
    assert overlaps(a, b) == overlaps(b, a)


def test_overlaps_includes_containment_and_equality():
    """The ruling that let the partition stay internal. Allen's `overlaps` excludes both; nobody
    reading a pipeline means Allen's."""
    assert overlaps(r("Mark 1:1-10"), r("Mark 1:3-5"))
    assert overlaps(r("Mark 1:1-5"), r("Mark 1:1-5"))


def test_adjacent_ranges_do_not_overlap():
    assert not overlaps(r("Mark 1:1-5"), r("Mark 1:6-10"))


def test_a_gap_is_not_an_overlap():
    assert not overlaps(r("Mark 1:1-5"), r("Mark 1:8-10"))


# --- contains, touches, equals ---------------------------------------------------------------


def test_contains_covers_every_verse():
    assert contains(r("Mark 1:1-10"), r("Mark 1:3-5"))
    assert not contains(r("Mark 1:1-5"), r("Mark 1:3-8"))


def test_a_range_contains_itself():
    assert contains(r("Mark 1:1-5"), r("Mark 1:1-5"))


def test_touches_is_adjacency_with_no_shared_verse():
    """Ruled `touches`, not Allen's `meets`. The docstring says adjacency because GIS uses the
    word for shared boundaries, and a reader may expect overlapping ranges to qualify."""
    assert touches(r("Mark 1:1-5"), r("Mark 1:6-10"))
    assert not touches(r("Mark 1:1-5"), r("Mark 1:5-10")), "they share verse 5"
    assert not touches(r("Mark 1:1-5"), r("Mark 1:8-10")), "there is a gap"


def test_touches_across_a_chapter_boundary():
    """Needs `max_verses` to know Mark 1 ends at 45 — and gets it from the constructor."""
    assert touches(r("MRK 1:45"), r("MRK 2:1"))


def test_touches_is_symmetric():
    a, b = r("Mark 1:1-5"), r("Mark 1:6-10")
    assert touches(a, b) == touches(b, a)


def test_equals():
    assert equals(r("Mark 1:1-5"), r("Mark 1:1-5"))
    assert not equals(r("Mark 1:1-5"), r("Mark 1:1-6"))


# --- books are distinct documents -------------------------------------------------------------


@pytest.mark.parametrize("relation", [overlaps, contains, touches, equals])
def test_nothing_relates_across_books(relation):
    """Cross-book answers rather than raising, because callers filtering a mixed-book set should
    not have to catch errors. `False` is true here — they share no verse and are not adjacent."""
    assert not relation(r("Mark 1:1-5"), r("John 1:1-5"))


def test_the_shipped_cross_book_defect_does_not_reproduce():
    """`division_lookup.py:31` regexes out `1:1-5` and drops the book, so these compare as
    overlapping. Reported to `ears-to-hear`; this is the guard on our side."""
    assert not overlaps(r("Mark 1:1-5"), r("John 1:1-5"))


# --- verse_count -------------------------------------------------------------------------------


def test_verse_count_of_a_simple_range():
    assert verse_count(r("Mark 1:1-5")) == 5


def test_verse_count_of_a_single_verse():
    assert verse_count(r("MRK 1:1")) == 1


def test_verse_count_across_a_chapter_boundary():
    """Mark 1:45 is the last verse of the chapter, so 1:45-2:3 is four verses."""
    assert verse_count(r("MRK 1:45-2:3")) == 4


# --- select ------------------------------------------------------------------------------------

DIVISIONS = [
    {"title": "prologue", "verse_range": "Mark 1:1-8"},
    {"title": "baptism", "verse_range": "Mark 1:9-13"},
    {"title": "galilee", "verse_range": "Mark 1:14-20"},
]


def test_select_returns_the_members_not_booleans():
    """`division_lookup` wants the division, not an interval — identity is the answer."""
    got = select(DIVISIONS, "Mark 1:10", "overlaps", ref="verse_range", scheme=ORG)
    assert [d["title"] for d in got] == ["baptism"]


def test_select_returns_every_match_not_the_first():
    """The defect at `division_lookup.py:56`: `return` on first match gives a passage spanning two
    divisions whichever comes first in the list, and reports nothing. A list makes the straddle
    visible, and taking the first becomes something the caller writes."""
    got = select(DIVISIONS, "Mark 1:7-10", "overlaps", ref="verse_range", scheme=ORG)
    assert [d["title"] for d in got] == ["prologue", "baptism"]


def test_select_returns_an_empty_list_never_none():
    """`say-which-kind-of-nothing`: the lookup ran and found nothing."""
    got = select(DIVISIONS, "Mark 2:1", "overlaps", ref="verse_range", scheme=ORG)
    assert got == []


def test_select_refuses_without_a_ref():
    """`ref` is the pipeline declaring where its ranges live — `declared-not-inferred`. Guessing a
    key is how a payload nobody checked gets built."""
    with pytest.raises(TypeError):
        select(DIVISIONS, "Mark 1:10", "overlaps", scheme=ORG)


def test_select_resolves_a_nested_ref():
    """`ref` uses the engine's own path resolution, so it behaves like every other path in sp."""
    nested = [{"title": "prologue", "meta": {"range": "Mark 1:1-8"}}]
    got = select(nested, "Mark 1:3", "overlaps", ref="meta.range", scheme=ORG)
    assert [d["title"] for d in got] == ["prologue"]


def test_select_names_an_unknown_relation():
    with pytest.raises(ValueError, match="overlaps"):
        select(DIVISIONS, "Mark 1:10", "encloses", ref="verse_range", scheme=ORG)


def test_select_warns_when_no_member_shares_the_probes_book(caplog):
    """With the partition internal, an empty result means both "nothing overlaps" and "you compared
    a Mark passage against John's divisions". The second is a pipeline bug, and silence is the
    wrong-with-no-symptom pattern. A warning fires exactly on that mistake."""
    with caplog.at_level("WARNING"):
        got = select(DIVISIONS, "John 1:1", "overlaps", ref="verse_range", scheme=ORG)

    assert got == []
    assert any("JHN" in record.message for record in caplog.records)


def test_select_reports_a_member_whose_reference_will_not_parse(caplog):
    """`division_lookup.py:40` catches `ValueError` and returns `False`, so an unreadable reference
    reports as overlapping nothing. The member is skipped, but it is said out loud."""
    broken = DIVISIONS + [{"title": "broken", "verse_range": "not a reference"}]
    with caplog.at_level("WARNING"):
        got = select(broken, "Mark 1:10", "overlaps", ref="verse_range", scheme=ORG)

    assert [d["title"] for d in got] == ["baptism"]
    assert any("broken" in record.message or "not a reference" in record.message
               for record in caplog.records)


# --- the two parsers this module did not add a third to ------------------------------------------


@pytest.mark.parametrize(
    "reference",
    ["Mark 1:1-5", "Mark 1:45-2:3", "MRK 1:1", "Genesis 1:1-2:3", "Luke 12:5-19", "John 3:16"],
)
def test_the_engines_two_parsers_agree_on_the_syntax_they_share(reference):
    """`parse_passage_ref` is syntax only; `parse_bible_reference` is syntax plus scheme plus
    presentation. They are layered rather than duplicated — but each carries its own pattern set,
    so nothing holds them together. This is the pin: if it fires, unify them.

    Recorded in `design-verse-regions.md` §1 as the engine having the duplication it reports in the
    plugins.
    """
    from llmflow.utils.data import parse_bible_reference
    from llmflow.utils.versification import parse_passage_ref

    syntax = parse_passage_ref(reference)
    full = parse_bible_reference(reference, versification=ORG)

    assert syntax.book == full["book_code"]
    assert syntax.start_chapter == full["chapter"]
    assert syntax.start_verse == full["start_verse"]
    assert syntax.end_chapter == full["end_chapter"]
    assert syntax.end_verse == full["end_verse"]


# --- laws, checked against every book of every scheme --------------------------------------------


@pytest.mark.parametrize("scheme", ["org", "eng", "lxx", "rsc", "rso", "vul"])
def test_the_relations_hold_for_every_book_and_chapter(scheme):
    """Laws rather than examples, over real data: 95 books and 1,584 chapters in `org` alone.

    Two implementations of overlap "agreed today for no stated reason" in the plugins this replaces.
    A law is the stated reason. Without `hypothesis` in the project, the corpus of every chapter in
    every packaged scheme is the closest thing to generated input — and it is real, which generated
    input is not.

    The four laws:
      - a chapter's verse count is what the scheme says it is
      - a whole book contains each of its chapters
      - consecutive chapters touch, which is the `max_verses`-dependent case
      - consecutive chapters do not overlap
    """
    from llmflow.utils.versification import packaged_scheme

    books = packaged_scheme(scheme).max_verses
    assert books, f"{scheme} carries no books"

    for book, chapters in books.items():
        if book == "PSS":
            continue  # refused: two published canons claim the token — see the test below

        whole = Range.parse(book, scheme=scheme)
        assert verse_count(whole) == sum(int(n) for n in chapters), f"{scheme} {book} whole book"

        previous = None
        for number in range(1, len(chapters) + 1):
            chapter = Range.parse(f"{book} {number}", scheme=scheme)

            assert verse_count(chapter) == int(chapters[number - 1]), f"{scheme} {book} {number}"
            assert contains(whole, chapter), f"{scheme} {book} excludes chapter {number}"
            if previous is not None:
                assert touches(previous, chapter), f"{scheme} {book} {number - 1}/{number}"
                assert not overlaps(previous, chapter), f"{scheme} {book} {number - 1}/{number}"
            previous = chapter


def test_a_book_two_canons_both_claim_is_refused_rather_than_guessed():
    """`PSS` is Psalms of Solomon in USFM and `Pss` is Psalms in the SBL Handbook. It used to
    resolve to Psalms, so a range written for Psalms of Solomon silently described Psalms — the
    sweep above is what caught it, since `PSS`'s verse counts did not match the book it returned.

    Refused now, which is why the sweep skips it: an unbuildable range is the correct outcome, and
    the alternative was a wrong one.
    """
    from llmflow.books import AmbiguousBook

    with pytest.raises(AmbiguousBook):
        Range.parse("PSS 1", scheme=ORG)

    assert Range.parse("PSA 1", scheme=ORG).book == "PSA", "Psalms itself is untouched"


def _chapters(book):
    from llmflow.utils.versification import packaged_scheme

    return packaged_scheme(ORG).max_verses[book]
