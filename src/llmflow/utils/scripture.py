"""Named scripture editions: a reference range in, running text out.

An edition names a source in the registry and a backend that can read it. Text is assembled
by concatenating each word with its own trailing string, so whitespace and punctuation are
read from the source rather than inferred per language.

Why running text rather than a verse-keyed mapping, what each serialization costs, and which
one to reach for: `project/plans/design-scripture-representations.md`, and §3 of
`project/plans/plan-scripture-step.md` for the backends.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from lxml import etree  # type: ignore[attr-defined]

from llmflow.modules.logger import Logger
from llmflow.utils import versification as _versification

logger = Logger()

#: An edition definition's field naming the versification scheme its references are in.
SCHEME_KEY = "versification_scheme"

#: Editions whose scheme we know, and Paratext's versification numbers.
EDITION_TABLE_FILENAME = "versification-editions.json"

_EDITION_TABLE: Optional[Mapping[str, Any]] = None

#: Marks where a verse begins in `fmt="milestones"` output.
MILESTONE_TEMPLATE = "⌊{chapter}:{verse}⌋"

FORMATS = ("plain", "milestones", "usj")

#: The scheme assumed for an edition that declares none. Much of the translation world uses
#: English versification without meeting the issue, so a project may have no versification file
#: and assume it. Assuming is supported; assuming silently is not — the caller gets a warning
#: and the payload reports the guess under its own key, never as a declaration.
ASSUMED_SCHEME = "eng"

USJ_VERSION = "3.1"

#: `\p`, an ordinary paragraph. The source carries no paragraphing, and USX requires text to
#: sit inside a paragraph, so one plain `para` per chapter is the least the grammar allows.
USJ_PARA_MARKER = "p"

#: What each family delivers, declared in data rather than here: a family is edition-shaped, so
#: the same declaration serves Greek and Hebrew without any code knowing about either.
FAMILY_TABLE_FILENAME = "include-families.json"

_FAMILY_TABLE: Optional[Mapping[str, Any]] = None


def _family_table() -> Mapping[str, Any]:
    global _FAMILY_TABLE
    table = _FAMILY_TABLE
    if table is None:
        table = json.loads(_data_path(FAMILY_TABLE_FILENAME).read_text(encoding="utf-8"))
        _FAMILY_TABLE = table
    return table


def _family(name: str) -> Mapping[str, Any]:
    return _family_table().get("families", {}).get(name, {})


def family_columns(name: str) -> tuple:
    """The source columns *name* carries, across every edition it serves."""
    return tuple(_family(name).get("columns", ()))


def family_is_per_word(name: str) -> bool:
    """Whether *name* annotates individual words, and so needs `ids` to be joinable."""
    return bool(_family(name).get("per_word"))


def family_usx_attributes(name: str) -> Mapping[str, Sequence[str]]:
    """Fields USX already defines on a word node, and the source columns that fill each."""
    return _family(name).get("usx_attributes", {})


#: The annotation families `include` can ask for. See §3.0a of plan-scripture-step.md.
INCLUDE_FAMILIES = ("ids", "morphology", "senses", "glosses", "referents", "discourse", "syntax")

#: Families with a working implementation. The rest are named vocabulary, and asking for one
#: raises rather than returning a document with the payload quietly missing.
IMPLEMENTED_FAMILIES = frozenset(
    {"ids", "discourse", "morphology", "senses", "glosses", "referents"}
)

#: The one key holding everything USJ has no place for. A consumer wanting standard USJ
#: removes this key and is done; an extension anywhere else is one nobody could find.
CONTAINER_KEY = "scripture_pipelines"

#: An edition definition's field naming the directory of LGNTDF feature files.
DISCOURSE_KEY = "discourse_path"

#: `\w`, the USX character marker for a word. `ids` is spec-defined — it becomes the `srcloc`
#: attribute here — so it does not belong in the container.
USJ_WORD_MARKER = "w"
USJ_SRCLOC = "srcloc"

#: An `after` value that joins its word to the next, so no space follows it: the Hebrew maqqef
#: (`עַל־פְּנֵי`). Every other non-empty, non-space `after` ends a word and takes a space after it. An
#: empty `after` also joins and adds nothing — Macula Hebrew splits a word into morphemes and
#: marks the continuations that way.
#:
#: The Greek elision apostrophe is deliberately absent. It reads like a joining mark, and we had
#: it here, which spaced `κατ’οἶκόν` against the printed edition's `κατʼ οἶκόν` in 1,221 places.
#: Macula Greek's convention is uniform — a space follows every non-space `after`, and a mark
#: falling word-final is carried in `text` instead, which is why `ἀλλ’` appears there with `·` in
#: `after`. Reconstructing 7,330 verses under that rule matches a printed SBLGNT in 7,197 of them,
#: with no spacing difference among the rest.
JOINING_MARKS = frozenset({"־"})

#: An `after` value that stands *between* two words rather than ending one, so a space precedes it
#: as well as following it: the Hebrew paseq (`אֱלֹהִים ׀ בֵּין`), and a bare setuma or petucha letter
#: marking a section break mid-verse. The source carries these in the preceding word's `after`,
#: where nothing else can supply the leading space.
#:
#: The compound values `׃ס` and `׃פ` are deliberately absent: there the sof pasuq ends the word and
#: the letter follows it tight, which is how a WLC-derived text writes all 3,066 of them.
STANDALONE_MARKS = frozenset({"׀", "ס", "פ"})

#: USJ element types holding apparatus rather than the text being read. Their content is
#: dropped. Inline `char` elements outside a note are part of the reading and are kept.
SKIP_USJ_TYPES = frozenset({"note", "figure", "sidebar", "ref"})


class ResourceNotRegistered(KeyError):
    """Raised when a resource has no registration, listing what is available.

    Named for resources rather than editions since #217: a text is one kind of resource among
    several the catalog describes, and the command that fixes this is `sp resource add`.
    """

    def __str__(self) -> str:  # KeyError repr would quote the message
        return self.args[0] if self.args else ""


#: The lean parser and its result live in `versification`, which is the lower layer: the mapper
#: needs them and cannot import this module. Re-exported here because the read path is their
#: other caller and imports from `scripture`.
PassageRef = _versification.PassageRef
parse_passage_ref = _versification.parse_passage_ref


def _split_ref(ref: str) -> tuple[str, Optional[int], Optional[int]]:
    """``"GEN 1:1!3"`` -> ``("GEN", 1, 1)``. The ``!n`` word index is discarded."""
    head = (ref or "").split("!", 1)[0].strip()
    if " " not in head:
        return head.upper(), None, None
    book, _, cv = head.partition(" ")
    if ":" not in cv:
        return book.upper(), (int(cv) if cv.isdigit() else None), None
    c, _, v = cv.partition(":")
    try:
        return book.upper(), int(c), int(v)
    except ValueError:
        return book.upper(), None, None


def filter_rows(rows: Iterable[Mapping[str, Any]], ref: PassageRef) -> list[dict]:
    """Keep the rows inside *ref*, in source order."""
    kept = []
    for row in rows:
        book, chapter, verse = _split_ref(row.get("ref", ""))
        if book != ref.book:
            continue
        if chapter is None:
            continue
        if ref.covers(chapter, verse if verse is not None else 1):
            kept.append(dict(row))
    return kept


def join_rows(rows: Iterable[Mapping[str, Any]]) -> str:
    """Concatenate ``text + after``, adding a space only where ``after`` does not carry one.

    ``after`` plays four roles: a space; a mark that joins (``JOINING_MARKS``, or empty); a mark
    that ends a word, which needs a space added because the source carries it without one; and a
    mark that stands between two words (``STANDALONE_MARKS``), which needs one on each side. The
    joining and standalone roles are Hebrew-only. The single place this rule lives.
    """
    parts: list[str] = []
    for row in rows:
        parts.append(str(row.get("text") or ""))
        after = str(row.get("after") or "")
        if after in STANDALONE_MARKS:
            parts.append(" ")
        parts.append(after)
        if after and not after.isspace() and after not in JOINING_MARKS:
            parts.append(" ")
    return "".join(parts)


def group_by_verse(rows: Iterable[Mapping[str, Any]]) -> list:
    """Rows as ``((chapter, verse), rows)`` runs, in source order.

    A row whose ``ref`` names no verse joins the run before it, so text outside any verse is
    not silently dropped.
    """
    groups: list = []
    for row in rows:
        _, chapter, verse = _split_ref(row.get("ref", ""))
        key = (chapter, verse) if chapter is not None and verse is not None else None
        if groups and (key is None or key == groups[-1][0]):
            groups[-1][1].append(row)
        else:
            groups.append((key, [row]))
    return groups


def rows_to_text(rows: Sequence[Mapping[str, Any]], fmt: str = "milestones") -> str:
    """Running text for *rows*.

    With ``fmt="milestones"`` a ``⌊chapter:verse⌋`` marker precedes each verse, separated from
    the preceding text when that does not already end in whitespace.
    """
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r}; expected one of {', '.join(FORMATS)}")
    if fmt == "plain":
        return join_rows(rows).strip()

    parts: list[str] = []
    for key, group in group_by_verse(rows):
        if key is not None:
            if parts and not parts[-1][-1:].isspace():
                parts.append(" ")
            parts.append(MILESTONE_TEMPLATE.format(chapter=key[0], verse=key[1]))
            parts.append(" ")
        parts.append(join_rows(group))
    return "".join(parts).strip()


def edition_scheme(definition: Any, edition: Optional[str] = None) -> Optional[str]:
    """The versification scheme an edition's references are in, or None when unknown.

    Three sources, in order: the edition's own ``versification_scheme``; a Paratext project's
    ``Settings.xml``; the table of editions we construct. There is no global default — a
    Byzantine Greek text and a critical text are numbered differently, so a guess would be
    wrong exactly where it mattered.
    """
    if isinstance(definition, Mapping):
        declared = definition.get(SCHEME_KEY)
        if declared:
            return str(declared)
        from_paratext = _paratext_scheme(definition)
        if from_paratext:
            return from_paratext

    for name in (edition, definition.get("id") if isinstance(definition, Mapping) else None):
        if name and str(name).upper() in _known_editions():
            return _known_editions()[str(name).upper()]["scheme"]
    return None


def _edition_table() -> Mapping[str, Any]:
    global _EDITION_TABLE
    table = _EDITION_TABLE
    if table is None:
        import json

        table = json.loads(_edition_table_path().read_text(encoding="utf-8"))
        _EDITION_TABLE = table
    return table


def _data_path(filename: str) -> Path:
    """Locate a shipped data file whether running from an installed wheel or a dev checkout.

    The same two locations `file_catalog.catalog_path()` resolves.
    """
    import importlib.resources

    try:
        ref = importlib.resources.files("llmflow").joinpath(f"data/{filename}")
        path = Path(str(ref))
        if path.exists():
            return path
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / filename


def _edition_table_path() -> Path:
    return _data_path(EDITION_TABLE_FILENAME)


def _known_editions() -> dict:
    """Editions whose scheme can be answered from a name alone, catalog first.

    The catalog's answer is anchored to a repository and a file inside it; the hand-written
    table's is keyed on the id string, which two people can choose independently. So a catalog
    entry wins, and the table carries only what the catalog does not describe.
    """
    from llmflow import resources as _resources

    known: dict = {}
    try:
        for identifier, item in _resources.readable().items():
            if item.get("versification"):
                known[identifier.upper()] = {
                    "scheme": item["versification"],
                    "why": item.get("versification_why", ""),
                    "source": "catalog",
                }
    except Exception:  # a missing or malformed catalog must not break scheme resolution
        pass

    for key, value in _edition_table().get("known_editions", {}).items():
        if isinstance(value, Mapping) and value.get("scheme"):
            known.setdefault(key.upper(), dict(value))
    return known


def _paratext_scheme(definition: Mapping[str, Any]) -> Optional[str]:
    """The scheme a Paratext project's `Settings.xml` declares, by its number."""
    base_dir, project = definition.get("base_dir"), definition.get("project")
    if not base_dir or not project:
        return None
    settings = Path(base_dir) / str(project) / "Settings.xml"
    if not settings.is_file():
        return None

    number = re.search(
        r"<Versification>\s*([^<\s]*)\s*</Versification>",
        settings.read_text(encoding="utf-8", errors="replace"),
    )
    if not number:
        return None
    entry = _edition_table().get("paratext_versification_numbers", {}).get(number.group(1))
    if not isinstance(entry, Mapping) or not entry.get("scheme"):
        return None

    # A custom.vrs overlays the numbered scheme; this engine reads only the numbered one.
    if any((settings.parent / name).is_file() for name in ("custom.vrs", "Custom.vrs")):
        logger.warning(
            f"Paratext project {project!r} declares versification "
            f"{entry.get('paratext_name', number.group(1))!r} and also carries a custom.vrs, "
            f"which this engine does not read. References its overlay changes will be wrong."
        )
    return str(entry["scheme"])


def resolve_passage(
    passage: str,
    edition_scheme_name: Optional[str],
    requested_scheme: Optional[str],
    edition: Optional[str] = None,
    mappings_dir: Optional[Path] = None,
) -> str:
    """*passage*, named in *requested_scheme*, rewritten as the edition numbers it.

    A reference naming no verse — a whole chapter or book — has nothing to move. A range maps
    at both ends; an end the target scheme reaches from more than one place raises rather than
    being chosen, because choosing would put the passage somewhere the data does not say.
    """
    if not requested_scheme:
        return passage
    if edition_scheme_name is None:
        # Much of the translation world uses English versification without meeting the issue,
        # so an edition may simply have no versification file. Refusing left those projects
        # unable to read their own text; assuming is supported, and warned about every time,
        # because where the assumption is wrong it is wrong by whole verses.
        logger.warning(
            f"{edition or '(unnamed)'} does not say which versification its references are "
            f"in, so `{ASSUMED_SCHEME}` is assumed while reading {passage!r} as "
            f"{requested_scheme!r}. Add `{SCHEME_KEY}: <scheme>` to its registry entry: where "
            f"the assumption is wrong, the verses returned are the wrong ones."
        )
        edition_scheme_name = ASSUMED_SCHEME
    if requested_scheme == edition_scheme_name:
        return passage

    ref = parse_passage_ref(passage)
    if ref.start_chapter is None or ref.start_verse is None:
        return passage

    def moved(chapter: Optional[int], verse: Optional[int]) -> tuple[int, int]:
        mapped = _versification.map_reference(
            _versification.format_reference(ref.book, chapter or 0, verse or 0),
            requested_scheme,
            edition_scheme_name,
            mappings_dir,
        )
        _, new_chapter, new_verse, _ = _versification.as_single_verse(mapped)
        return new_chapter, new_verse

    start_chapter, start_verse = moved(ref.start_chapter, ref.start_verse)
    end_chapter, end_verse = moved(ref.end_chapter, ref.end_verse)

    if (start_chapter, start_verse) == (end_chapter, end_verse):
        return f"{ref.book} {start_chapter}:{start_verse}"
    if start_chapter == end_chapter:
        return f"{ref.book} {start_chapter}:{start_verse}-{end_verse}"
    return f"{ref.book} {start_chapter}:{start_verse}-{end_chapter}:{end_verse}"


def check_include(include: Any, fmt: str) -> tuple:
    """Validate `include` against `fmt` and return it as a tuple. See §4's lint rules."""
    if not include:
        return ()
    if isinstance(include, str):
        raise ValueError(
            f"include must be a list of families, not the string {include!r} — write "
            f"`include: [{include}]`."
        )
    families = tuple(include)

    if fmt != "usj":
        raise ValueError(
            f"include {list(families)} needs `format: usj`; `{fmt}` has nowhere to put a "
            f"payload."
        )
    unknown = [f for f in families if f not in INCLUDE_FAMILIES]
    if unknown:
        raise ValueError(
            f"unknown include {'family' if len(unknown) == 1 else 'families'} "
            f"{unknown}; expected from {', '.join(INCLUDE_FAMILIES)}."
        )
    unbuilt = [f for f in families if f not in IMPLEMENTED_FAMILIES]
    if unbuilt:
        raise NotImplementedError(
            f"include {unbuilt} is not implemented yet; available: "
            f"{', '.join(sorted(IMPLEMENTED_FAMILIES))}."
        )
    return families


def rows_to_output(
    rows: Sequence[Mapping[str, Any]],
    fmt: str,
    book: str,
    include: Sequence[str] = (),
    versification: Optional[str] = None,
    discourse: Optional[list] = None,
) -> str | dict:
    """The requested representation of *rows*: a string, or a USJ document for ``fmt="usj"``."""
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r}; expected one of {', '.join(FORMATS)}")
    if fmt == "usj":
        return rows_to_usj(
            rows, book=book, include=include, versification=versification, discourse=discourse
        )
    return rows_to_text(rows, fmt=fmt)


def rows_to_usj(
    rows: Sequence[Mapping[str, Any]],
    book: str,
    include: Sequence[str] = (),
    versification: Optional[str] = None,
    discourse: Optional[list] = None,
) -> dict:
    """*rows* as a USJ document: the book, a chapter node per chapter, one `para` inside each.

    One `para` per chapter because the source has no paragraph structure to carry, and the USX
    grammar requires text to sit inside one. A caller wanting editorial structure asks for
    `format: print`. Nothing is added outside the USJ node types.
    """
    want_ids = "ids" in include
    per_word = [f for f in include if family_is_per_word(f)]
    if per_word and not want_ids:
        raise ValueError(
            f"include {per_word} annotates individual words, and the container keys them by word "
            f"id — add `ids` so the document carries a {USJ_SRCLOC} to match them against."
        )

    #: `{field: (columns, in order of preference)}` for the USX attributes the asked-for families
    #: deliver. Only `lemma` and `strong` are here; everything else stays in the container.
    attributes: dict = {}
    for family in include:
        for field, columns in family_usx_attributes(family).items():
            attributes.setdefault(field, tuple(columns))

    annotation: dict = {family: {} for family in per_word}

    def annotate(row: Mapping[str, Any]) -> None:
        """Collect a word's declared columns, verbatim, skipping the ones it leaves empty."""
        identifier = row.get("xml:id")
        if not identifier:
            return
        for family in per_word:
            fields = {
                column: str(row[column])
                for column in family_columns(family)
                if str(row.get(column) or "").strip()
            }
            if fields:
                annotation[family][str(identifier)] = fields

    content: list = [{"type": "book", "marker": "id", "code": book}]
    chapter_open: Optional[int] = None
    para: Optional[dict] = None

    def emit(target: list, group: Sequence[Mapping[str, Any]]) -> None:
        """Append a verse's material: one string, or a `w` node per word when ids are asked.

        Text nodes carry their own spacing, as USJ text nodes do, so a consumer rebuilds the
        running text by concatenation. Space-joining the nodes instead would put a space
        before every comma.
        """
        if not want_ids:
            text = join_rows(group)
            if text:
                target.append(text)
            return
        for row in group:
            word = str(row.get("text") or "")
            if word:
                node = {"type": "char", "marker": USJ_WORD_MARKER, "content": [word]}
                identifier = row.get("xml:id")
                if identifier:
                    node[USJ_SRCLOC] = str(identifier)
                for field, columns in attributes.items():
                    value = next(
                        (str(row[c]) for c in columns if str(row.get(c) or "").strip()), None
                    )
                    if value:
                        node[field] = value
                target.append(node)
            annotate(row)
            # What follows the word — a space, a joining mark, punctuation and the space the
            # engine adds after it — is text. Dropping it would make the document
            # unflattenable back to running text.
            trailing = join_rows([{"text": "", "after": row.get("after")}])
            if trailing:
                target.append(trailing)

    # `sid` only, and deliberately: USX pairs a start milestone with a closing `<verse eid=…/>`,
    # but USJ does not — `usfmtc`, the USFM Technical Committee's reference implementation,
    # discards verse and chapter ends when it converts USX to USJ. Emitting them anyway would put
    # non-standard content in the standard node space, which is what CONTAINER_KEY exists to
    # avoid, and any round-trip through a conformant tool would drop them again.
    for key, group in group_by_verse(rows):
        if key is None:
            if para is not None:
                emit(para["content"], group)
            continue

        chapter, verse = key
        if chapter != chapter_open:
            chapter_open = chapter
            content.append(
                {
                    "type": "chapter",
                    "marker": "c",
                    "number": str(chapter),
                    "sid": f"{book} {chapter}",
                }
            )
            para = {"type": "para", "marker": USJ_PARA_MARKER, "content": []}
            content.append(para)

        assert para is not None  # a chapter node always opens one
        para["content"].append(
            {
                "type": "verse",
                "marker": "v",
                "number": str(verse),
                "sid": f"{book} {chapter}:{verse}",
            }
        )
        emit(para["content"], group)

    document = {"type": "USJ", "version": USJ_VERSION, "content": content}
    if include:
        # A key carries which kind of nothing it means: an empty collection is "asked, and the
        # answer is nothing"; `None` is "could not ask". Omitting the key says neither, and a
        # log warning does not travel with the payload to whoever reads it later — so a
        # consumer could not tell an edition with no discourse source from a passage where
        # discourse was never requested. A family the caller did not request stays absent,
        # because `include:` declares why. Rule `say-which-kind-of-nothing`.
        # `versification` names the scheme the labels in *this document* are in, which is the
        # edition's own: the verse markers come from its rows. It is never the scheme a caller
        # requested — a request maps the caller's reference inward to fetch the right verses,
        # and does not relabel the result. Reporting the request made the container assert
        # labels the document did not have, off by exactly the difference between the schemes,
        # and a consumer had nothing else to check it against.
        container: dict = {"versification": versification or None}
        if not versification:
            container["versification_guessed"] = ASSUMED_SCHEME
            logger.warning(
                f"{book}: the edition does not say which versification its references are in, "
                f"so `{ASSUMED_SCHEME}` is assumed; the {CONTAINER_KEY} container states "
                f"`versification: null` with `versification_guessed: {ASSUMED_SCHEME}` beside "
                f"it. Add `{SCHEME_KEY}: <scheme>` to the edition's registry entry to declare "
                f"it properly."
            )
        if "discourse" in include:
            container["discourse"] = discourse
        container.update(annotation)
        document[CONTAINER_KEY] = container
    return document


def resolve_edition(
    edition: str,
    registry_editions: Optional[Mapping[str, Any]] = None,
) -> Any:
    """Return the definition for a named edition: a TSV path string, or a mapping carrying a
    `kind` and what that backend needs."""
    available = dict(registry_editions or {})
    if edition in available:
        return available[edition]

    from llmflow import resources as _resources

    known = ", ".join(sorted(available)) or "(none registered)"
    try:
        in_catalog = edition in _resources.readable()
    except Exception:
        in_catalog = False

    remedy = (
        f"  Register it with `sp resource add {edition}` so the path is not written into a "
        f"pipeline."
        if in_catalog
        else "  `sp resource list` shows what the catalog knows; `sp resource add <ID>` "
        "registers one, and a resource of your own is registered from its path."
    )
    raise ResourceNotRegistered(
        f"Scripture resource {edition!r} is not registered.\n"
        f"  Registered: {known}\n" + remedy
    )


def usj_to_text(usj: Mapping[str, Any], fmt: str = "milestones") -> str:
    """Flatten a USJ document into running text.

    The USFM backend's counterpart to ``rows_to_text``. USJ nests strings inside ``para``
    elements with ``verse`` markers interleaved, so a verse boundary is a marker in a stream
    rather than a column on a row — but the output contract is identical: running text, verse
    positions marked, never a per-verse container.

    Chapter number is tracked from ``chapter`` elements, because a ``verse`` element carries
    only its own number.
    """
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r}; expected one of {', '.join(FORMATS)}")

    parts: list[str] = []
    chapter = {"n": None}  # boxed so the closure can assign

    def walk(node: Any) -> None:
        if isinstance(node, str):
            text = node.strip()
            if not text:
                return
            if parts and not parts[-1][-1:].isspace():
                parts.append(" ")
            parts.append(text)
            return
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, Mapping):
            return
        kind = node.get("type")
        if kind in SKIP_USJ_TYPES:
            return  # apparatus, not text — see SKIP_USJ_TYPES
        if kind == "chapter":
            if node.get("eid"):
                return  # a closing milestone, which names no new chapter
            chapter["n"] = node.get("number")
            return
        if kind == "verse":
            if node.get("eid"):
                return  # ends a verse rather than starting one
            if fmt == "milestones":
                if parts and not parts[-1][-1:].isspace():
                    parts.append(" ")
                parts.append(
                    MILESTONE_TEMPLATE.format(
                        chapter=chapter["n"] or "?", verse=node.get("number", "?")
                    )
                )
                parts.append(" ")
            return
        walk(node.get("content"))

    walk(usj.get("content"))
    return "".join(parts).strip()


#: A TEI word carries its reference in `ref` and its identity in `xml:id`.
TEI_REF = "ref"
TEI_ID = "{http://www.w3.org/XML/1998/namespace}id"

#: Separates two words that have no `pc` between them.
WORD_SEPARATOR = " "

#: Apparatus reference marks. Not text: they point from a word to an apparatus entry, and a
#: `pc` can hold a mark and real punctuation together. Excluded from `plain` and `milestones`
#: per plan-scripture-step.md §3.6.
APPARATUS_MARKS = frozenset("⸀⸁⸂⸃⸄⸅⸆⸇⸈⸉⸊")



def tei_book_files(tei_dir: str | Path) -> dict[str, Path]:
    """Map book code to file, taking the code from each file's first `w`."""
    directory = Path(tei_dir)
    if not directory.is_dir():
        return {}

    books: dict[str, Path] = {}
    for path in sorted(directory.glob("*.xml")):
        code = _first_book_code(path)
        if code:
            books.setdefault(code, path)
    return books


def _first_book_code(path: Path) -> Optional[str]:
    """The book code from the first `w` in *path*, without parsing the whole file."""
    for _, element in etree.iterparse(str(path), events=("start",)):
        if etree.QName(element).localname == "w":
            book, _, _ = _split_ref(element.get(TEI_REF) or "")
            return book or None
    return None


def read_tei_rows(tei_path: str | Path, ref: PassageRef) -> list[dict]:
    """Rows for *ref* from one TEI book file, in the shape `rows_to_text` consumes."""
    rows: list[dict] = []
    for element in etree.parse(str(tei_path)).getroot().iter():
        tag = etree.QName(element).localname
        if tag == "w":
            word = element.text or ""
            rows.append({
                "ref": element.get(TEI_REF) or "",
                "xml:id": element.get(TEI_ID) or "",
                "text": word,
                "after": "" if word[-1:] in JOINING_MARKS else WORD_SEPARATOR,
            })
        elif tag == "pc" and rows:
            punctuation = _without_apparatus_marks(element.text or "")
            if punctuation:
                # Several `pc` can follow one word: replace the separator, then accumulate.
                previous = rows[-1]["after"]
                rows[-1]["after"] = punctuation if previous == WORD_SEPARATOR else previous + punctuation
    return filter_rows(rows, ref)


def _without_apparatus_marks(text: str) -> str:
    return "".join(c for c in text if c not in APPARATUS_MARKS)


def read_rows(tsv_path: str | Path) -> list[dict]:
    """Read a Macula-style TSV. Only ``ref``, ``text`` and ``after`` are required here."""
    path = Path(tsv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Scripture data file not found: {path}")
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def passage_text(
    edition: str,
    passage: str,
    fmt: str = "milestones",
    registry_editions: Optional[Mapping[str, str]] = None,
) -> str | dict:
    """Running text for *passage* in *edition* — the whole job in one call."""
    path = resolve_edition(edition, registry_editions)
    ref = parse_passage_ref(passage)
    rows = filter_rows(read_rows(path), ref)
    if not rows:
        raise ValueError(
            f"No text found for {passage!r} in edition {edition!r}. "
            f"Check the book code and that the edition covers it "
            f"(WLC is Old Testament only; SBLGNT is New Testament only)."
        )
    return rows_to_output(rows, fmt=fmt, book=ref.book)


# --------------------------------------------------------------------------------------
# Edition registry
#
# One YAML file per edition under ``~/.sp/registrations/``:
#
#   id: SBLGNT
#   name: SBL Greek New Testament
#   kind: tsv                 # tsv | usfm
#   path: /path/to/macula-greek-SBLGNT.tsv
#
# For ``kind: usfm`` the fields are ``base_dir`` and ``project`` instead of ``path``, matching
# what load_usfm_passage() takes.
# --------------------------------------------------------------------------------------

def load_registry_editions(editions_dir: Any = None) -> dict:
    """Every registration this machine holds, with dataset-relative paths resolved.

    The store and its reader belong to `llmflow.resources`, which owns the whole question of
    what is registered and where it lives; this is the read path's door onto it. A registration
    recording `dataset` plus a relative `path` is resolved here, so a backend downstream always
    receives a definition it can open without knowing the store exists.
    """
    from llmflow import resources as _resources

    out: dict = {}
    for name, definition in _resources.load_registered(editions_dir).items():
        entry = dict(definition)
        if entry.get("path"):
            try:
                resolved = _resources.resolve_path(entry)
            except ValueError:
                out[name] = entry
                continue
            entry["path"] = str(resolved)
            # A USFM project is a directory, and `load_usfm_passage` wants it as a parent plus
            # a name. The catalog states one path because it describes where a thing is, not
            # what one reader's signature happens to be, so the split belongs here.
            if str(entry.get("kind", "")).lower() == "usfm" and not entry.get("base_dir"):
                entry["base_dir"] = str(resolved.parent)
                entry["project"] = resolved.name
        out[name] = entry
    return out


def _usfm_passage_text(definition: Mapping[str, Any], passage: str, fmt: str) -> str:
    """BSB and other USFM editions: passage -> USJ -> running text."""
    from llmflow.utils.data import load_usfm_passage

    base_dir = definition.get("base_dir")
    project = definition.get("project")
    if not base_dir or not project:
        raise ValueError(
            f"USFM edition {definition.get('id')!r} needs 'base_dir' and 'project' in its "
            f"registry entry."
        )
    usj = load_usfm_passage(str(base_dir), str(project), passage, "usj")
    if not isinstance(usj, Mapping):
        raise ValueError(f"USFM loader returned {type(usj).__name__}, expected a USJ mapping")
    return usj_to_text(usj, fmt=fmt)


def _no_text_found(passage: str, edition: str) -> str:
    return (
        f"No text found for {passage!r} in edition {edition!r}. Check the book code and "
        f"that the edition covers it (WLC is Old Testament only; SBLGNT New Testament only)."
    )


def _tei_passage_text(
    definition: Mapping[str, Any],
    passage: str,
    fmt: str,
    edition: str,
    include: Sequence[str] = (),
    versification: Optional[str] = None,
) -> str | dict:
    """Running text for *passage* from a directory of per-book TEI files."""
    tei_dir = definition.get("path")
    if not tei_dir:
        raise ValueError(f"TEI edition {edition!r} needs a 'path' in its registry entry.")

    ref = parse_passage_ref(passage)
    book_file = tei_book_files(tei_dir).get(ref.book)
    rows = read_tei_rows(book_file, ref) if book_file else []
    if not rows:
        raise ValueError(_no_text_found(passage, edition))
    return rows_to_output(
        rows,
        fmt=fmt,
        book=ref.book,
        include=include,
        versification=versification,
        discourse=(
            discourse_payload(definition, rows, edition) if "discourse" in include else None
        ),
    )


def edition_text(
    edition: str,
    passage: str,
    fmt: str = "milestones",
    editions: Optional[Mapping[str, Any]] = None,
    versification: Optional[str] = None,
    mappings_dir: Optional[Path] = None,
    include: Any = (),
) -> str | dict:
    """Running text for *passage* in *edition*, dispatched on the edition's `kind`.

    *versification* names the scheme *passage* is written in. When it differs from the
    edition's own, the reference is mapped before any text is read — a reference is not a
    location until a scheme is named, and fetching first would fetch the wrong verses.
    """
    # Before any filesystem work: an unusable format is a mistake in the pipeline, and
    # reporting it should not depend on the edition's data being present.
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r}; expected one of {', '.join(FORMATS)}")
    families = check_include(include, fmt)

    definition = resolve_edition(edition, editions)
    scheme = edition_scheme(definition, edition)
    passage = resolve_passage(
        passage,
        scheme,
        versification,
        edition=edition,
        mappings_dir=mappings_dir,
    )
    if isinstance(definition, str):  # bare path == a TSV, the common case
        definition = {"id": edition, "kind": "tsv", "path": definition}
    kind = str(definition.get("kind", "tsv")).lower()

    # The scheme the returned labels are in, which is the edition's — reading a passage does
    # not renumber the text. `versification` said which scheme the caller's reference was
    # written in, and was wrongly used here as though it described the result.
    result_scheme = scheme
    if kind == "usfm":
        return _usfm_passage_text(definition, passage, fmt)
    if kind == "tei":
        return _tei_passage_text(definition, passage, fmt, edition, families, result_scheme)
    if kind not in ("tsv",):
        raise ValueError(
            f"Edition {edition!r} has unknown kind {kind!r}; expected 'tsv', 'tei' or 'usfm'."
        )

    path = definition.get("path")
    if not path:
        raise ValueError(f"TSV edition {edition!r} needs a 'path' in its registry entry.")
    ref = parse_passage_ref(passage)
    rows = filter_rows(read_rows(path), ref)
    if not rows:
        raise ValueError(_no_text_found(passage, edition))
    return rows_to_output(
        rows,
        fmt=fmt,
        book=ref.book,
        include=families,
        versification=result_scheme,
        discourse=(
            discourse_payload(definition, rows, edition) if "discourse" in families else None
        ),
    )


def discourse_payload(
    definition: Any,
    rows: Sequence[Mapping[str, Any]],
    edition: str,
) -> Optional[list]:
    """Discourse items for *rows*, or None when this edition has no discourse source.

    Which corpus applies follows from the edition, not from the language: an edition names its
    own with `discourse_path`, and the loader reads either Levinsohn's Greek features or the
    Hebrew ones. An edition naming none is a warning rather than a failure (§4).
    """
    from llmflow.utils import discourse as _discourse

    path = definition.get(DISCOURSE_KEY) if isinstance(definition, Mapping) else None
    if not path:
        logger.warning(
            f"include: [discourse] was requested but edition {edition!r} names no "
            f"`{DISCOURSE_KEY}`, so no discourse features are attached. Add one to the "
            f"edition's registry entry, pointing at the corpus for its language."
        )
        return None

    citations = _discourse.load_citations(path)
    if not citations:
        logger.warning(
            f"include: [discourse]: no citations were read from {path!r} for edition "
            f"{edition!r}."
        )
        return None

    items: list = []
    for key, group in group_by_verse(rows):
        if key is None:
            continue
        book, _, _ = _split_ref(group[0].get("ref", ""))
        for_verse = citations.get(f"{book} {key[0]}:{key[1]}")
        if for_verse:
            items.extend(_discourse.resolve_verse(for_verse, group))
    return items
