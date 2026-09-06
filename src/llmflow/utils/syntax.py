"""The constituency tree as standoff structure, one entry per sentence.

Ruled in `project/plans/design-scripture-representations.md` §4.5. Text and tree are two orders
that cannot be reconciled: a constituent whose words are interrupted by words from elsewhere is
discontinuous, and no arrangement of a tree's children makes traversal emit sentence order while
the tree keeps its shape. Greek has such constituents because hyperbaton is a live rhetorical
device — 276 of Mark's 726 sentences carry an inversion somewhere in traversal. So each fact is
stated once, in the order native to it: the reading text stays in the USJ document in textual
order, and the tree sits in the container in tree order, carrying no text at all.

**A list, one entry per sentence.** Lowfat wraps each sentence in `<sentence>`, whose two children
are the running text and the tree, and those elements are in canonical order in the file even
where the tree inside one is not. A list therefore makes "which subtree is a sentence" structural
rather than a class the engine invents — which matters because a point of departure is defined as
sentence-initial, and Mark has 726 sentences against 4,021 clause groups, so answering that
question against clauses would be wrong roughly five times in six.

**What a node carries.** `class`, the syntactic category, and `role`, its role with respect to the
governing verb; then `articular`, `head`, `type`, `clauseType`, `junction` and `predication` where
the source states them, and `children` in tree order.

Those six are carried because they are properties of a *constituent* and none of them has a route
through the TSV, which is one row per word. `articular` is the clearest case: in
`τῇ κατ᾽ οἶκόν σου ἐκκλησίᾳ` the article governs a phrase containing a prepositional phrase, not
the word beside it, so articularity cannot ride in a per-word family however the families are
arranged.

`rule` and `nodeId` are not carried: they name how the parser derived the node rather than a fact
about the constituent.

**What a leaf carries.** One `token`, the word-level id, plus `class`, `role`, `junction` and
`discontinuous`. No text, because the text is in the USJ document; no `ref`, because a word's book,
chapter and verse follow from where it sits there, and carrying it would be a third encoding of
identity beside the id and the position. Nothing the per-word families already deliver, because a
second encoding of `lemma` or `morph` is one that can disagree with the first.

`discontinuous` earns its place: this family is standoff *because* text order and tree order cannot
be reconciled, and it is the source's own marking of exactly that — 6,038 Greek words, in 4,404 of
the corpus's 8,010 sentences, and never on a group node.

Hebrew leaves are `<m>` morpheme nodes, so a word written in several pieces appears as several
leaves. Each names the **word**, through `_word_identifier` — a consumer keying on a leaf gets an
address it can join against, rather than one piece of a word.
"""

from __future__ import annotations

from typing import Any, Optional

from llmflow.utils.discourse import _word_identifier, _word_index

#: Elements that are words or morphemes — the leaves of a Lowfat tree.
LEAF_TAGS = ("w", "m")

#: Elements that group other elements: the tree's internal nodes.
#:
#: `c` is Hebrew-only and holds a compound word — *"Elements that contain multiple morphemes that
#: make up a compound word… c elements group such morphemes into one terminal node in the tree"*
#: (*MACULA Hebrew Treebank for OSHB* §2.1). Every one in Ruth 1 is `בֵּית לֶחֶם`. It is carried as
#: a node rather than a leaf because it spans two *words* — `RUT 1:1!10` and `!11` — so a single
#: token cannot name it, and flattening it would lose the compound the source states. Its `class`
#: and `role` come across like any other node's.
GROUP_TAGS = ("wg", "c")

#: Carried onto a group node, in this order.
#:
#: `rule` and `nodeId` are deliberately absent. `rule` names how the parser derived the node rather
#: than a fact about the constituent, and it comes in two conventions — a capitalised `Rule`, paired
#: with `nodeId`, runs through all 27 Greek books alongside the lower-case one. Both are the tool's
#: bookkeeping.
#:
#: `articular` is the reason this list is longer than `class` and `role`. It has no route through
#: the TSV, and articularity is a property of a *phrase*: in `τῇ κατ᾽ οἶκόν σου ἐκκλησίᾳ` the
#: article governs a phrase containing a prepositional phrase, not the word beside it. So no
#: per-word family could carry it, and it is `syntax` or nowhere.
GROUP_ATTRIBUTES = (
    "class",
    "role",
    "articular",
    "head",
    "type",
    "clauseType",
    "junction",
    "predication",
)

#: Carried onto a leaf. Everything else Macula puts on a `w` or `m` — `lemma`, `strong`, `morph`,
#: `gloss`, the parsing fields, `frame`, `subjref`, `referent` — is a TSV column that arrives
#: through a per-word family, and a second encoding here could disagree with the first.
#:
#: `discontinuous` is on leaves only, never on `wg`, and has no TSV route. It marks the very
#: phenomenon this family is standoff *for*: 6,038 Greek words carry it, in 4,404 of the corpus's
#: 8,010 sentences.
#:
#: `role` is carried on leaves for a reason beyond symmetry: the **Hebrew** TSV has no `role`
#: column, so for Hebrew this is its only route.
LEAF_ATTRIBUTES = ("class", "role", "junction", "discontinuous")

#: Greek writes `clauseType`, Hebrew `clausetype`, for one fact. The payload states it once, under
#: the Greek spelling — **the one place a field name is not the source's verbatim.** Emitting both
#: would present an inconsistency between the sources as though it were a distinction in the
#: grammar, and make a consumer know which corpus it was reading in order to find the value.
SPELLINGS = {"clauseType": ("clauseType", "clausetype")}

XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

#: The edition registry key naming a Lowfat directory, parallel to `discourse_path`.
LOWFAT_KEY = "lowfat_path"


def _localname(element: Any) -> str:
    from lxml import etree  # type: ignore[attr-defined]

    return etree.QName(element).localname


def _leaf(element: Any) -> Optional[dict]:
    """One terminal — a Greek word or a Hebrew morpheme — or None where it names no id.

    Carries `class` and `role` like any node, because the terminals are where the analysis
    actually sits. Hebrew Lowfat is morpheme-based: 171 of Ruth 1's 172 multi-morpheme words have
    morphemes of differing class or role — `וַ` is a conjunction and `יְהִ֗י` a verb with role `v`
    — so a shape carrying only the token would render them indistinguishable and make a word's two
    terminals look like one thing repeated. Greek carries the same: 11,286 of Mark's words declare
    a class and 4,426 a role.

    `token` is the **word-level** id in both languages, so two morphemes of one Hebrew word name
    the same word while remaining separate terminals. That is the join a consumer keys on; the
    morpheme's own id is in the edition's rows for anyone who needs it.
    """
    from llmflow.utils.discourse import _word_identifier, _word_index

    identifier = element.get(XML_ID)
    if not identifier:
        return None

    # `_word_index` and `_word_identifier` read the declared Macula id format, so a Hebrew
    # morpheme resolves to its word and a Greek word is already one. Passing `ref` through a
    # mapping keeps that logic in one place rather than repeating the format here.
    row = {"ref": element.get("ref") or "", "xml:id": identifier}
    index = _word_index(row)

    leaf: dict = {"token": _word_identifier(row, index or "")}
    _carry(element, LEAF_ATTRIBUTES, leaf)
    return leaf


def _carry(element: Any, names: tuple, into: dict) -> None:
    """Copy the attributes the source states, in declared order, skipping those it omits.

    An attribute Macula writes only when true — `articular`, `discontinuous`, `head` — is absent
    rather than false, so the payload says nothing where the source says nothing.
    """
    for name in names:
        for spelling in SPELLINGS.get(name, (name,)):
            value = (element.get(spelling) or "").strip()
            if value:
                into[name] = value
                break


def _node(element: Any) -> Optional[dict]:
    """A group as a node with its children, or a leaf as a token. None where neither."""
    tag = _localname(element)

    if tag in LEAF_TAGS:
        return _leaf(element)

    if tag not in GROUP_TAGS:
        return None

    node: dict = {}
    _carry(element, GROUP_ATTRIBUTES, node)

    children = [child for child in (_node(c) for c in element) if child is not None]
    if children:
        node["children"] = children

    return node or None


def _first_ref(path: Any) -> Optional[str]:
    """The first `ref` a file declares, read without parsing the rest of it.

    Which book a Lowfat file holds is read from its content rather than its name: the Greek
    corpus names files `02-mark.xml` and the Hebrew one `08-Rut-001-lowfat.xml`, and a filename
    convention is a shape to infer from rather than something either corpus declares. Peeking at
    the first `ref` costs 0.33s across all 930 Hebrew files.
    """
    from lxml import etree  # type: ignore[attr-defined]

    try:
        for _, element in etree.iterparse(str(path), events=("start",)):
            ref = element.get("ref")
            if ref:
                element.clear()
                return ref
    except (OSError, etree.XMLSyntaxError):
        return None
    return None


def lowfat_files_for(directory: Any, book: str) -> list:
    """Every Lowfat file in *directory* whose content is *book*, in name order.

    A Greek book is one file and a Hebrew book is one file per chapter, so this returns however
    many the corpus uses without either shape being named here.
    """
    from pathlib import Path

    root = Path(directory)
    if not root.is_dir():
        return []

    wanted = str(book).strip().upper()
    found = []
    for path in sorted(root.rglob("*.xml")):
        ref = _first_ref(path)
        if not ref:
            continue
        declared = ref.split()[0].strip().upper() if ref.split() else ""
        if declared == wanted:
            found.append(path)
    return found


def sentence_covers(sentence: Any, word_ids: Any) -> bool:
    """Whether any terminal of *sentence* is one of *word_ids*.

    A sentence is carried whole where it meets the passage at all, even where it runs past both
    ends. Pruning its leaves to the passage would hand back a tree that is not the tree — the
    constituency of a half sentence is not a fact about the text — so the payload states the
    sentence the passage falls in, and some tokens may name words outside the rows returned.
    """
    for element in sentence.iter():
        if _localname(element) in LEAF_TAGS:
            identifier = element.get(XML_ID)
            if not identifier:
                continue
            row = {"ref": element.get("ref") or "", "xml:id": identifier}
            if _word_identifier(row, _word_index(row) or "") in word_ids:
                return True
    return False


def sentences_from_lowfat(root: Any) -> list:
    """Every `<sentence>` under *root* as a payload entry, in the order the file states them.

    A `<sentence>` holds the running text and the tree; only the tree is read here, the text
    coming from the edition's own rows. Where *root* is itself a `<sentence>`, it is the only one.
    """
    if _localname(root) == "sentence":
        found = [root]
    else:
        found = list(root.iter("{*}sentence")) or list(root.iter("sentence"))

    payload = []
    for sentence in found:
        for child in sentence:
            if _localname(child) not in GROUP_TAGS:
                continue
            node = _node(child)
            if node is not None:
                payload.append(node)
    return payload


def syntax_payload(definition: Any, rows: Any, edition: str) -> Optional[list]:
    """The trees covering *rows*, or None where this edition names no Lowfat source.

    Sentence-ordered, because Lowfat's `<sentence>` elements are in canonical order in the file
    even where the tree inside one is not — 276 of Mark's 726 have an inversion somewhere in
    traversal, which is the whole reason text and tree are carried separately.

    `None` rather than an empty list where the edition declares no `lowfat_path`: the question
    could not be asked, as against asked and answered with nothing.
    """
    from llmflow.modules.logger import Logger

    logger = Logger()

    path = definition.get(LOWFAT_KEY) if isinstance(definition, dict) else None
    if not path:
        logger.warning(
            f"include: [syntax] was requested but edition {edition!r} names no `{LOWFAT_KEY}`, "
            f"so no syntax is attached. Add one to the edition's registry entry, pointing at the "
            f"Lowfat directory for its text."
        )
        return None

    # The book comes from `ref`, which every Macula row carries as `MRK 1:1!1`. There is no
    # `book` column in either corpus's TSV.
    books = {
        str(row.get("ref") or "").split()[0].strip().upper()
        for row in rows
        if str(row.get("ref") or "").strip()
    }
    books.discard("")
    if not books:
        return []

    wanted = {
        _word_identifier({"ref": r.get("ref") or "", "xml:id": r.get("xml:id") or ""},
                         _word_index({"ref": r.get("ref") or ""}) or "")
        for r in rows if r.get("xml:id")
    }

    from lxml import etree  # type: ignore[attr-defined]

    payload: list = []
    for book in sorted(books):
        for file in lowfat_files_for(path, book):
            try:
                root = etree.parse(str(file)).getroot()
            except (OSError, etree.XMLSyntaxError) as error:
                logger.warning(f"syntax: {file} could not be read and was skipped: {error}")
                continue
            for sentence in root.iter("{*}sentence") if root.nsmap else root.iter("sentence"):
                if sentence_covers(sentence, wanted):
                    payload.extend(sentences_from_lowfat(sentence))
    return payload
