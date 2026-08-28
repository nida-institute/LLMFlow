"""File writing utilities — save content and track written paths."""

import csv
import io as _io
import json
import traceback
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import yaml

from llmflow.modules.logger import Logger

logger = Logger()

WRITTEN_FILES: list[str] = []

#: Every accepted `format` value, mapped to the writer it selects. A value containing `/` is a
#: mime type; an informal name is the spelling for the formats with no registered type — `usj`,
#: `usx` and `usfm` have none, so coining `application/x-usj` would mean owning a vocabulary
#: while appearing to borrow one. The yaml aliases predate RFC 9512 and are still widely written.
FORMAT_ALIASES = {
    "json": "json",
    "application/json": "json",
    "usj": "json",
    "yaml": "yaml",
    "application/yaml": "yaml",
    "text/yaml": "yaml",
    "application/x-yaml": "yaml",
    "text": "text",
    "text/plain": "text",
    "markdown": "markdown",
    "text/markdown": "markdown",
    "csv": "csv",
    "text/csv": "csv",
    "tsv": "tsv",
    "text/tab-separated-values": "tsv",
    "xml": "xml",
    "application/xml": "xml",
    "text/xml": "xml",
    "usx": "usx",
    "usfm": "usfm",
}

#: What `auto` reads from the path. A suffix absent here is not an error by itself — a string is
#: still written as text — but it cannot imply a serialisation for structured content.
EXTENSION_FORMATS = {
    ".json": "json",
    ".usj": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".markdown": "markdown",
    ".csv": "csv",
    ".tsv": "tsv",
    ".xml": "xml",
    ".usx": "usx",
    ".usfm": "usfm",
    ".txt": "text",
}

_ACCEPTED = ", ".join(sorted(FORMAT_ALIASES))


def _record_written_file(path: str) -> None:
    p = Path(path).resolve()
    pstr = str(p)
    if pstr not in WRITTEN_FILES:
        WRITTEN_FILES.append(pstr)
    logger.info(f"Wrote file: {p}")
    logger.debug(
        "Called from:\n" + "".join(traceback.format_stack()[-4:-1])
    )


def _element_or_none(content: Any):
    """*content* as an lxml element, or None."""
    try:
        from lxml.etree import _Element
    except ImportError:
        return None
    return content if isinstance(content, _Element) else None


def resolve_format(fmt: Optional[str], path: str, content: Any) -> str:
    """The writer to use, from an explicit format or from the path.

    An unrecognised explicit value is an error naming what is accepted. With `auto`, an
    unrecognised suffix falls back to text for a string, and is an error for anything else:
    ``str()`` on a mapping is a Python repr, never a serialisation.
    """
    if fmt is not None and fmt != "auto":
        try:
            return FORMAT_ALIASES[str(fmt).strip().lower()]
        except KeyError:
            raise ValueError(
                f"{fmt!r} is not a format `saveas` can write. Accepted: {_ACCEPTED}."
            ) from None

    suffix = Path(path).suffix.lower()
    if suffix in EXTENSION_FORMATS:
        return EXTENSION_FORMATS[suffix]
    if isinstance(content, str) or _element_or_none(content) is not None:
        return "text"
    raise ValueError(
        f"{path!r} has no extension naming a format, and {type(content).__name__} content "
        f"cannot be written as text. Give `saveas` a format. Accepted: {_ACCEPTED}."
    )


def _as_json(content: Any) -> str:
    """JSON, re-parsing a string that already holds JSON so it is not double-encoded."""
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            while isinstance(parsed, str):
                try:
                    parsed = json.loads(parsed)
                except (json.JSONDecodeError, ValueError):
                    break
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, ValueError):
            return json.dumps(content, ensure_ascii=False, indent=2)
    return json.dumps(content, ensure_ascii=False, indent=2)


def _as_yaml(content: Any) -> str:
    return yaml.safe_dump(content, allow_unicode=True, sort_keys=False, default_flow_style=False)


def _as_text(content: Any) -> str:
    element = _element_or_none(content)
    if element is not None:
        from lxml.etree import tostring

        return tostring(element, encoding="unicode", pretty_print=True)
    return content if isinstance(content, str) else str(content)


def _as_markdown(content: Any) -> str:
    from llmflow.utils.markdown_cleaner import clean_markdown

    return clean_markdown(_as_text(content)) + "\n"


def _as_delimited(content: Any, delimiter: str, name: str) -> str:
    """Rows as delimited text. A mapping per row takes its header from the first row's keys.

    `csv.writer` quotes a value containing the delimiter or a newline; joining by hand would
    write it raw and corrupt the file silently.
    """
    if not isinstance(content, Sequence) or isinstance(content, str):
        raise ValueError(
            f"{name} needs a sequence of rows, not {type(content).__name__}."
        )
    buffer = _io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    rows = list(content)
    if not rows:
        return ""
    if isinstance(rows[0], Mapping):
        header = list(rows[0].keys())
        for position, row in enumerate(rows):
            if not isinstance(row, Mapping) or list(row.keys()) != header:
                raise ValueError(
                    f"{name} row {position} has keys {sorted(getattr(row, 'keys', list)())} "
                    f"against the header's keys {sorted(header)}. Every row must carry the "
                    f"same keys in the same order."
                )
        writer.writerow(header)
        writer.writerows([[row[key] for key in header] for row in rows])
    else:
        writer.writerows([list(row) for row in rows])
    return buffer.getvalue()


def _as_xml(content: Any) -> str:
    """XML from an element, or a string checked for well-formedness.

    There is no defined mapping from a Python mapping to xml, so a dict is refused rather than
    guessed at. `usx` is the format for a USJ document.
    """
    from lxml.etree import XMLSyntaxError, fromstring, tostring

    element = _element_or_none(content)
    if element is not None:
        return tostring(element, encoding="unicode", pretty_print=True)
    if isinstance(content, str):
        try:
            fromstring(content.encode("utf-8"))
        except XMLSyntaxError as error:
            raise ValueError(f"xml content is not well-formed: {error}") from None
        return content
    # An xpath result set is a list of siblings, so it is written as a fragment: each item
    # well-formed on its own, the whole not single-rooted. Refusing it would leave those
    # pipelines writing `str(list)`.
    if isinstance(content, Sequence):
        return "\n".join(_as_xml(item) for item in content)
    raise ValueError(
        f"xml cannot be written from {type(content).__name__}. Give an lxml element, an "
        f"xml string, or a sequence of either; for a USJ document use `usx`."
    )


def _as_usx(content: Any) -> str:
    from llmflow.utils.data import serialize_usx

    return str(serialize_usx(content))


def _as_usfm(content: Any) -> str:
    from llmflow.utils.data import serialize_usfm

    return str(serialize_usfm(content))


WRITERS = {
    "json": _as_json,
    "yaml": _as_yaml,
    "text": _as_text,
    "markdown": _as_markdown,
    "csv": lambda content: _as_delimited(content, ",", "csv"),
    "tsv": lambda content: _as_delimited(content, "\t", "tsv"),
    "xml": _as_xml,
    "usx": _as_usx,
    "usfm": _as_usfm,
}


def save_content_to_file(content: Any, path: str, format: Optional[str] = None) -> str:
    """Serialise *content* to *path*, in NFC.

    *format* is an informal name or a mime type; `auto` or absent reads the path's extension.
    Every write is Unicode NFC.
    """
    resolved = resolve_format(format, path, content)
    formatted_content = WRITERS[resolved](content)

    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(unicodedata.normalize("NFC", str(formatted_content)))

    return str(path_obj.absolute())
