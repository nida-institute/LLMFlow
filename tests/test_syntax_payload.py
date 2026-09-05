"""`include: [syntax]` — the constituency tree, standoff, one entry per sentence.

Ruled in `design-scripture-representations.md` §4.5. The two orders cannot be reconciled: a
constituent whose words are interrupted by words from elsewhere is discontinuous, and no ordering
of a tree's children makes traversal emit sentence order while the tree keeps its shape. Greek has
discontinuous constituents because hyperbaton is a live device — 276 of Mark's 726 sentences have
an inversion somewhere in traversal. So each fact is stated once in the order native to it: text
in the USJ document in textual order, tree in the container in tree order, carrying no text.

**The payload is a list, one entry per sentence.** Lowfat wraps each sentence's tree in
`<sentence>`, whose two children are the running text and the tree, and those elements are in
canonical order in the file even though the tree inside each is not. A list makes "which subtree is
a sentence" structural rather than a word the engine invents — which is what `discourse-flow` asked
for, needing it because a point of departure is defined as sentence-initial and Mark has 726
sentences against 4,021 clause groups.

Nodes and leaves both carry `class` — the node's syntactic category — and `role`, its role with
respect to the governing verb. `rule` is not carried: it names the parser's derivation rather than
a fact about the constituent.

A leaf also carries a word-level `token`, and nothing further. No text, because the text is in the
USJ document; no `ref`, because a word's book, chapter and verse follow from where it sits there,
so carrying it would be a third encoding of identity beside the id and the position.
"""

import pytest
from lxml import etree

from llmflow.utils.syntax import sentences_from_lowfat

#: One sentence, with a discontinuous noun phrase: its words are 1 and 3, interrupted by 2.
DISCONTINUOUS = """
<sentence>
  <p>text in surface order</p>
  <wg class="cl" role="s" rule="ClCl">
    <wg class="np" role="adv">
      <w xml:id="n41001001001" ref="MRK 1:1!1" class="noun">Ἀρχὴ</w>
      <w xml:id="n41001001003" ref="MRK 1:1!3" class="noun">εὐαγγελίου</w>
    </wg>
    <w xml:id="n41001001002" ref="MRK 1:1!2" class="det">τοῦ</w>
  </wg>
</sentence>
"""

#: Two sentences in canonical order, as a chapter holds them.
TWO = """
<chapter>
  <sentence><p>a</p><wg class="cl"><w xml:id="n41001001001" ref="MRK 1:1!1">Ἀρχὴ</w></wg></sentence>
  <sentence><p>b</p><wg class="cl"><w xml:id="n41001002001" ref="MRK 1:2!1">Καθὼς</w></wg></sentence>
</chapter>
"""

#: Hebrew leaves are morphemes: word 4 of Ruth 1:1 is two `<m>` nodes.
HEBREW = """
<sentence>
  <p>a</p>
  <wg class="cl">
    <m xml:id="o080010010041" ref="RUT 1:1!4" class="art">הַ</m>
    <m xml:id="o080010010042" ref="RUT 1:1!4" class="noun">שֹּׁפְטִ֔ים</m>
  </wg>
</sentence>
"""


def parse(text):
    return etree.fromstring(text.strip())


def test_a_sentence_becomes_one_entry():
    payload = sentences_from_lowfat(parse(TWO))

    assert isinstance(payload, list)
    assert len(payload) == 2, "one entry per sentence, so the boundary is structural"


def test_sentences_keep_the_order_of_the_file():
    """Lowfat's `<sentence>` elements are canonically ordered even where the trees are not."""
    payload = sentences_from_lowfat(parse(TWO))

    assert payload[0]["children"][0]["token"] == "n41001001001"
    assert payload[1]["children"][0]["token"] == "n41001002001"


def test_a_node_carries_class_and_role_and_not_rule():
    payload = sentences_from_lowfat(parse(DISCONTINUOUS))
    top = payload[0]

    assert top["class"] == "cl"
    assert top["role"] == "s"
    assert "rule" not in top, "`rule` is the parser's derivation, not a fact about the constituent"


def test_a_node_without_a_role_carries_none():
    """Absent because the source says nothing, not because the engine dropped it."""
    payload = sentences_from_lowfat(parse(TWO))

    assert "role" not in payload[0]


def test_a_leaf_carries_its_token_and_its_analysis_and_nothing_else():
    """No text and no `ref`: the text is in the USJ document, and a word's book, chapter and verse
    follow from where it sits there, so carrying `ref` would be a third encoding of identity.

    `class` and `role` are carried, because the terminals are where the analysis sits. A leaf of
    only a token would make a Hebrew word's two morphemes indistinguishable — see
    `test_two_morphemes_of_one_word_stay_distinguishable`.
    """
    payload = sentences_from_lowfat(parse(DISCONTINUOUS))
    leaf = payload[0]["children"][0]["children"][0]

    assert leaf == {"token": "n41001001001", "class": "noun"}
    assert "ref" not in leaf and "text" not in leaf


def test_two_morphemes_of_one_word_stay_distinguishable():
    """Hebrew Lowfat is morpheme-based and the morphemes differ: 171 of Ruth 1's 172
    multi-morpheme words have morphemes of differing class or role. `וַ` is a conjunction and
    `יְהִ֗י` a verb; `הַ` is an article and `שֹּׁפְטִ֔ים` a noun.

    Both name the same **word**, which is the join a consumer keys on, and they remain two
    terminals because that is what the source states.
    """
    payload = sentences_from_lowfat(parse(HEBREW))
    article, noun = payload[0]["children"]

    assert article == {"token": "o08001001004", "class": "art"}
    assert noun == {"token": "o08001001004", "class": "noun"}


def test_the_tree_keeps_its_own_order_and_the_discontinuity_stays_visible():
    """The `np` reaches words 1 and 3 across word 2, which is the shape that cannot be flattened."""
    payload = sentences_from_lowfat(parse(DISCONTINUOUS))
    phrase, interrupter = payload[0]["children"]

    assert [leaf["token"] for leaf in phrase["children"]] == [
        "n41001001001",
        "n41001001003",
    ]
    assert interrupter["token"] == "n41001001002"


def test_a_hebrew_leaf_addresses_the_word_not_the_morpheme():
    """Word 4 is two morphemes; both leaves name the word, which is what a consumer can key on."""
    payload = sentences_from_lowfat(parse(HEBREW))
    tokens = [leaf["token"] for leaf in payload[0]["children"]]

    assert tokens == ["o08001001004", "o08001001004"], (
        f"expected the word-level id for both morphemes of word 4, got {tokens}"
    )


#: A compound word: `<c>` groups the two words of `בֵּית לֶחֶם` into one terminal node.
COMPOUND = """
<sentence>
  <p>a</p>
  <wg class="cl">
    <c class="noun" role="adv">
      <m xml:id="o080010010102" ref="RUT 1:1!10" class="noun">בֵּ֧ית</m>
      <m xml:id="o080010010111" ref="RUT 1:1!11" class="noun">לֶ֣חֶם</m>
    </c>
  </wg>
</sentence>
"""


def test_a_compound_word_is_carried_and_keeps_both_words():
    """`<c>` was dropped entirely at first, taking ten morphemes of Ruth 1 with it.

    *"c elements group such morphemes into one terminal node in the tree"* (*MACULA Hebrew
    Treebank for OSHB* §2.1). It is carried as a node rather than a leaf because it spans two
    **words** — `RUT 1:1!10` and `!11` — so no single token can name it, and flattening it would
    lose a compound the source states.

    Every `<c>` in Ruth 1 is `בֵּית לֶחֶם`, which is the same compound that makes a citation's word
    index run one behind Macula's from that point in the verse: the discourse corpus counts the
    place name as one word and the edition counts two.
    """
    payload = sentences_from_lowfat(parse(COMPOUND))
    compound = payload[0]["children"][0]

    assert compound["class"] == "noun"
    assert compound["role"] == "adv"
    assert [leaf["token"] for leaf in compound["children"]] == [
        "o08001001010",
        "o08001001011",
    ], "both words stay addressable"


def test_no_word_is_dropped_from_a_tree():
    """The guard for the defect above: a leaf missing from the payload is silent otherwise."""
    for source in (DISCONTINUOUS, TWO, HEBREW, COMPOUND):
        root = parse(source)
        payload = sentences_from_lowfat(root)

        def leaves(node):
            if "token" in node:
                return [node["token"]]
            return [t for child in node.get("children", []) for t in leaves(child)]

        emitted = [t for entry in payload for t in leaves(entry)]
        in_source = len(root.findall(".//w")) + len(root.findall(".//m"))
        assert len(emitted) == in_source, (
            f"{in_source} leaves in the source, {len(emitted)} in the payload"
        )


def test_an_empty_document_yields_an_empty_list():
    """Asked and found none, which is not the same as never asked."""
    assert sentences_from_lowfat(parse("<chapter/>")) == []


# --- the family, as a pipeline reaches it --------------------------------------------------


def test_syntax_needs_ids_beside_it():
    """§4.5: the leaves are `xml:id` values, which reach the document as `srcloc` through `ids`.

    A stronger condition than `check_include` enforces for the per-word families, and deliberately
    so: `syntax` is a tree *over* words rather than an annotation *on* one, so `per_word: true`
    would be the wrong way to arrive at the same requirement. Without `ids` the payload names
    words the document does not identify — unusable rather than merely thinner.
    """
    from llmflow.utils.scripture import check_include

    with pytest.raises(ValueError, match="needs `ids` beside it"):
        check_include(["syntax"], "usj")

    assert check_include(["ids", "syntax"], "usj") == ("ids", "syntax")


def test_an_edition_naming_no_lowfat_warns_rather_than_failing(caplog):
    """The same shape as a missing discourse source: a warning, and `None` rather than `[]`.

    `null` says the question could not be asked — this edition supplies no tree — as against
    asked and answered with nothing.
    """
    from llmflow.utils.syntax import syntax_payload

    rows = [{"ref": "MRK 1:1!1", "xml:id": "n41001001001", "text": "Ἀρχὴ"}]
    with caplog.at_level("WARNING"):
        assert syntax_payload({"kind": "tsv"}, rows, "SBLGNT") is None

    assert any("lowfat_path" in record.message for record in caplog.records)


def test_a_file_is_matched_by_what_it_declares_not_by_its_name(tmp_path):
    """Greek names files `02-mark.xml` and Hebrew `08-Rut-001-lowfat.xml`.

    Neither corpus declares a filename convention, so the book is read from the first `ref` in
    each file — which is a fact the file states.
    """
    from llmflow.utils.syntax import lowfat_files_for

    (tmp_path / "anything-at-all.xml").write_text(
        '<book><sentence><p>a</p><wg class="cl">'
        '<w xml:id="n41001001001" ref="MRK 1:1!1">Ἀρχὴ</w></wg></sentence></book>',
        encoding="utf-8",
    )
    (tmp_path / "02-mark.xml").write_text(
        '<book><sentence><p>a</p><wg class="cl">'
        '<w xml:id="n42001001001" ref="LUK 1:1!1">Ἐπειδήπερ</w></wg></sentence></book>',
        encoding="utf-8",
    )

    found = [p.name for p in lowfat_files_for(tmp_path, "MRK")]
    assert found == ["anything-at-all.xml"], (
        "matched on the declared `ref`, not on a filename that happens to say `mark`"
    )


def test_a_sentence_is_carried_whole_where_it_meets_the_passage():
    """Pruning a sentence's leaves to the requested rows would hand back a tree that is not the
    tree: the constituency of half a sentence is not a fact about the text. So some tokens may
    name words outside the rows returned, and the payload states the sentence the passage falls
    in.
    """
    from llmflow.utils.syntax import sentence_covers

    sentence = parse(
        '<sentence><p>a</p><wg class="cl">'
        '<w xml:id="n41001001001" ref="MRK 1:1!1">a</w>'
        '<w xml:id="n41001002001" ref="MRK 1:2!1">b</w></wg></sentence>'
    )

    assert sentence_covers(sentence, {"n41001001001"}), "one word of it is in the passage"
    assert not sentence_covers(sentence, {"n41001009001"})
