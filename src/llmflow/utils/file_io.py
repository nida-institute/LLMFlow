"""File writing utilities — save content and track written paths."""

import json
import traceback
from pathlib import Path
from typing import Any, Optional

from llmflow.modules.logger import Logger

logger = Logger()

WRITTEN_FILES: list[str] = []


def _record_written_file(path: str) -> None:
    p = Path(path).resolve()
    pstr = str(p)
    if pstr not in WRITTEN_FILES:
        WRITTEN_FILES.append(pstr)
    logger.info(f"Wrote file: {p}")
    logger.debug(
        "Called from:\n" + "".join(traceback.format_stack()[-4:-1])
    )


def save_content_to_file(content: Any, path: str, format: Optional[str] = None) -> str:
    """Save content to file with optional format specification."""
    if format is None or format == 'auto':
        if path.endswith('.json'):
            format = 'json'
        elif path.endswith('.usx'):
            format = 'usx'
        elif path.endswith('.usj'):
            format = 'json'
        elif path.endswith('.usfm'):
            format = 'usfm'
        else:
            format = 'text'

    if format == 'json':
        if isinstance(content, (dict, list)):
            formatted_content = json.dumps(content, ensure_ascii=False, indent=2)
        elif isinstance(content, str):
            try:
                parsed = json.loads(content)
                while isinstance(parsed, str):
                    try:
                        parsed = json.loads(parsed)
                    except (json.JSONDecodeError, ValueError):
                        break
                formatted_content = json.dumps(parsed, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, ValueError):
                formatted_content = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            formatted_content = json.dumps(content, ensure_ascii=False, indent=2)
    else:
        raw = content if isinstance(content, str) else str(content)
        if path.endswith('.md'):
            from llmflow.utils.markdown_cleaner import clean_markdown
            formatted_content = clean_markdown(raw) + "\n"
        else:
            formatted_content = raw

    if format == 'usx':
        from llmflow.utils.data import serialize_usx
        formatted_content = serialize_usx(content)
    elif format == 'usfm':
        from llmflow.utils.data import serialize_usfm
        formatted_content = serialize_usfm(content)
    elif format == 'text':
        try:
            from lxml.etree import _Element, tostring
            if isinstance(content, _Element):
                formatted_content = tostring(content, encoding="unicode", pretty_print=True)
        except ImportError:
            pass

    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(str(formatted_content))

    return str(path_obj.absolute())
