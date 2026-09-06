"""Every book spelling the published schemes use resolves to the right USFM code.

Three schemes name the books, and a citation may arrive in any of them:

- **USFM** codes are this table's keys.
- **OSIS** ids, transcribed from CrossWire's `OSIS_Book_Abbreviations`.
- **SBL** abbreviations, transcribed from SBL Press, *The SBL Handbook of Style*, Second
  Edition (Atlanta: SBL Press, 2014), 124-125, §§8.3.1-8.3.2. Rows the Handbook writes as
  "1-2 X" are expanded here into the two abbreviations a citation actually uses.

Both lists are transcribed from a source rather than recalled, because a wrong abbreviation in
the one table every reference passes through is a silent wrong answer, not an error.

Most of this passes without any alias being added: `normalise()` lowercases and strips dots and
spaces, so `1 Sam.`, `1Sam` and `1SA` collapse to one key. That is a property worth holding —
it is what makes commentary-style citations work at all — and nothing asserted it before, so a
tidy-up of `normalise()` could have broken every SBL and OSIS spelling with a green suite.

Convention: rule `check-the-source-not-the-rendering` — the subject is taken from the published
schemes, and the count is asserted so the check cannot quietly shrink to nothing.
"""
from __future__ import annotations

import pytest

from llmflow import books

#: CrossWire's OSIS ids for the 66 canonical books, in canonical order.
OSIS = {
    "Gen": "GEN", "Exod": "EXO", "Lev": "LEV", "Num": "NUM", "Deut": "DEU",
    "Josh": "JOS", "Judg": "JDG", "Ruth": "RUT", "1Sam": "1SA", "2Sam": "2SA",
    "1Kgs": "1KI", "2Kgs": "2KI", "1Chr": "1CH", "2Chr": "2CH", "Ezra": "EZR",
    "Neh": "NEH", "Esth": "EST", "Job": "JOB", "Ps": "PSA", "Prov": "PRO",
    "Eccl": "ECC", "Song": "SNG", "Isa": "ISA", "Jer": "JER", "Lam": "LAM",
    "Ezek": "EZK", "Dan": "DAN", "Hos": "HOS", "Joel": "JOL", "Amos": "AMO",
    "Obad": "OBA", "Jonah": "JON", "Mic": "MIC", "Nah": "NAM", "Hab": "HAB",
    "Zeph": "ZEP", "Hag": "HAG", "Zech": "ZEC", "Mal": "MAL",
    "Matt": "MAT", "Mark": "MRK", "Luke": "LUK", "John": "JHN", "Acts": "ACT",
    "Rom": "ROM", "1Cor": "1CO", "2Cor": "2CO", "Gal": "GAL", "Eph": "EPH",
    "Phil": "PHP", "Col": "COL", "1Thess": "1TH", "2Thess": "2TH", "1Tim": "1TI",
    "2Tim": "2TI", "Titus": "TIT", "Phlm": "PHM", "Heb": "HEB", "Jas": "JAS",
    "1Pet": "1PE", "2Pet": "2PE", "1John": "1JN", "2John": "2JN", "3John": "3JN",
    "Jude": "JUD", "Rev": "REV",
}

#: The Handbook's abbreviations for the canonical books, including the synonyms it offers.
SBL = {
    "Gen": "GEN", "Exod": "EXO", "Lev": "LEV", "Num": "NUM", "Deut": "DEU",
    "Josh": "JOS", "Judg": "JDG", "Ruth": "RUT", "1 Sam": "1SA", "2 Sam": "2SA",
    "1 Kgs": "1KI", "2 Kgs": "2KI", "1 Chr": "1CH", "2 Chr": "2CH", "Ezra": "EZR",
    "Neh": "NEH", "Esth": "EST", "Job": "JOB", "Ps": "PSA",
    "Prov": "PRO", "Eccl": "ECC", "Qoh": "ECC", "Song": "SNG", "Cant": "SNG",
    "Isa": "ISA", "Jer": "JER", "Lam": "LAM", "Ezek": "EZK", "Dan": "DAN",
    "Hos": "HOS", "Joel": "JOL", "Amos": "AMO", "Obad": "OBA", "Jonah": "JON",
    "Mic": "MIC", "Nah": "NAM", "Hab": "HAB", "Zeph": "ZEP", "Hag": "HAG",
    "Zech": "ZEC", "Mal": "MAL",
    "Matt": "MAT", "Mark": "MRK", "Luke": "LUK", "John": "JHN", "Acts": "ACT",
    "Rom": "ROM", "1 Cor": "1CO", "2 Cor": "2CO", "Gal": "GAL", "Eph": "EPH",
    "Phil": "PHP", "Col": "COL", "1 Thess": "1TH", "2 Thess": "2TH",
    "1 Tim": "1TI", "2 Tim": "2TI", "Titus": "TIT", "Phlm": "PHM", "Heb": "HEB",
    "Jas": "JAS", "1 Pet": "1PE", "2 Pet": "2PE", "1 John": "1JN",
    "2 John": "2JN", "3 John": "3JN", "Jude": "JUD", "Rev": "REV",
}

#: §8.3.1 also gives the Septuagint's names for the four books it splits differently. `Kgdms`
#: is a distinct token from `Kgs`, so which book each names is unambiguous. Resolving the name
#: says which book; it says nothing about versification, which a Kingdoms citation also implies
#: — the Handbook's own example is `3 Kgdms 2:46h LXX`, a verse with no Hebrew counterpart.
#: That belongs to the scheme machinery (#203), not to this table.
LXX_KINGDOMS = {"1 Kgdms": "1SA", "2 Kgdms": "2SA", "3 Kgdms": "1KI", "4 Kgdms": "2KI"}

#: There is no third or fourth book of Kings in any scheme, so these name nothing. Asserted
#: because `3 Kgdms` resolving must not drag a plausible-looking neighbour along with it.
NOT_BOOKS = ("3 Kgs", "4 Kgs", "5 Kgdms")

#: The Handbook's plural for Psalms, which USFM spends on Psalms of Solomon. Held out of `SBL`
#: above because it is the one abbreviation two published standards both claim, and this engine
#: reads both: the schemes it ships carry Psalms of Solomon as a book in its own right.
CLAIMED_BY_TWO_CANONS = "Pss"


def test_both_scheme_lists_cover_the_canon():
    """Without this, a truncated list would make every check below pass on less."""
    assert len(OSIS) == 66, f"the OSIS list names {len(OSIS)} books, not 66"
    assert len(set(SBL.values())) == 66, "the SBL list does not reach all 66 books"


@pytest.mark.parametrize("osis,expected", sorted(OSIS.items()))
def test_every_osis_id_resolves(osis, expected):
    assert books.resolve(osis) == expected
    assert books.resolve(osis + ".") == expected, "a trailing dot must not matter"


@pytest.mark.parametrize("sbl,expected", sorted(SBL.items()))
def test_every_sbl_abbreviation_resolves(sbl, expected):
    assert books.resolve(sbl) == expected
    assert books.resolve(sbl + ".") == expected, "the Handbook prints these with a period"


def test_the_one_abbreviation_two_canons_both_claim_is_refused():
    """The Handbook's `Pss` is Psalms; USFM's `PSS` is Psalms of Solomon, which the shipped
    schemes carry as a book of its own — 18 chapters in `org` and `lxx`.

    Both claims are sourced, so neither can be dropped, and the token is refused instead. It used
    to resolve to Psalms because `_index()` adds `other_codes` with `setdefault` and the alias got
    there first: a pipeline asking for Psalms of Solomon silently received Psalms.

    **Psalms of Solomon is now unreachable rather than wrong.** It has no display name here, and
    `other_codes` deliberately invents none, so the refusal's advice to write the book out cannot
    be followed for it. Refusing beats returning the wrong text; naming it is separate work.
    """
    with pytest.raises(books.AmbiguousBook) as raised:
        books.resolve(CLAIMED_BY_TWO_CANONS)

    message = str(raised.value)
    assert "Psalms" in message and "Psalms of Solomon" in message

    assert books.resolve("Ps") == "PSA", "the singular is untouched"
    assert books.resolve("Psalms") == "PSA"


@pytest.mark.parametrize("written,expected", sorted(LXX_KINGDOMS.items()))
def test_the_septuagint_kingdoms_names_resolve(written, expected):
    assert books.resolve(written) == expected
    assert books.resolve(written + ".") == expected


@pytest.mark.parametrize("written", NOT_BOOKS)
def test_a_book_that_does_not_exist_resolves_to_nothing(written):
    """`None` means "no such book", which is what a caller needs to hear.

    Adding the Kingdoms names must not make a neighbouring non-book resolve by accident — an
    invented book is worse than an unrecognised one, because the caller acts on it.
    """
    assert books.resolve(written) is None
