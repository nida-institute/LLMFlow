"""A verse continues across paragraphs: poetry lines without a verse marker belong to it.

In USFM a verse of poetry spans several paragraphs — `\\q1 \\v 3 A voice …` then
`\\q2 'Prepare the way …'` — and only the first carries the verse marker. The verse-range
filter used to track the current verse per paragraph, so every continuation line was
dropped: the BSB of Mark 1:2-3 reached the model as "As it is written in Isaiah the prophet:"
and "A voice of one calling in the wilderness," with both quotations missing, and every verse
of Psalm 51 lost its second half. A section heading between verses is not verse text and stays
out.
"""

from llmflow.utils.data import load_usfm_passage
from llmflow.utils.scripture import usj_to_text

MARK = r"""\id MRK - Poetry Test
\c 1
\p \v 1 This is the beginning of the gospel.
\v 2 As it is written in Isaiah the prophet:
\b
\q1 "Behold, I will send My messenger ahead of You,
\q2 who will prepare Your way."
\q1 \v 3 "A voice of one calling in the wilderness,
\q2 'Prepare the way for the Lord,
\q2 make straight paths for Him.'"
\s1 The Baptism of Jesus
\p \v 4 John the Baptist appeared in the wilderness.
\q1 \v 5 First line of five,
\q2 second line of five.
"""


def _project(tmp_path):
    project = tmp_path / "Poetry"
    project.mkdir()
    (project / "41MRK.sfm").write_text(MARK, encoding="utf-8")
    return str(tmp_path), "Poetry"


def _text(tmp_path, passage):
    base, name = _project(tmp_path)
    return usj_to_text(load_usfm_passage(base, name, passage, "usj"), fmt="milestones")


def test_continuation_lines_belong_to_the_verse_before_them(tmp_path):
    text = _text(tmp_path, "MRK 1:2-3")
    assert "Behold, I will send My messenger" in text
    assert "who will prepare Your way" in text
    assert "Prepare the way for the Lord" in text
    assert "make straight paths for Him" in text


def test_a_heading_between_verses_is_not_verse_text(tmp_path):
    text = _text(tmp_path, "MRK 1:3-4")
    assert "make straight paths for Him" in text
    assert "The Baptism of Jesus" not in text
    assert "John the Baptist appeared" in text


def test_continuation_after_the_range_is_left_out(tmp_path):
    text = _text(tmp_path, "MRK 1:4")
    assert "John the Baptist appeared" in text
    assert "First line of five" not in text
    assert "second line of five" not in text


def test_continuation_of_the_last_verse_in_range_is_kept(tmp_path):
    text = _text(tmp_path, "MRK 1:5")
    assert "First line of five" in text
    assert "second line of five" in text
