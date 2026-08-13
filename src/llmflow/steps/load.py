"""Loader step handlers — load_json, load_yaml, load_xml, load_csv, load_tsv, load_text, load_directory."""

from pathlib import Path
from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve

logger = Logger()

_LOADER_FORMATS = {"json", "yaml", "xml", "csv", "tsv", "text"}


def _load_one(path, fmt, load_json_file, load_yaml, load_xml_file,
              load_csv_file, load_text_file, step):
    """Load a single file according to fmt."""
    path = Path(path)
    if fmt == "json":
        from llmflow.utils.data import apply_key_extract
        return apply_key_extract(load_json_file(str(path)), step)
    if fmt == "yaml":
        from llmflow.utils.data import apply_key_extract
        return apply_key_extract(load_yaml(str(path)), step)
    if fmt == "xml":
        from llmflow.utils.data import apply_xml_xpath
        return apply_xml_xpath(load_xml_file(str(path)), step)
    if fmt in ("csv", "tsv"):
        from llmflow.utils.data import apply_tabular_filters
        delimiter = step.get("delimiter", "\t" if fmt == "tsv" else ",")
        rows = load_csv_file(str(path), delimiter=delimiter)
        return apply_tabular_filters(rows, step)
    if fmt == "text":
        return load_text_file(str(path))


def run_load_step(step: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Execute a load_* step — resolve path, load file(s), store in context."""
    from llmflow.utils.data import (
        load_json_file,
        load_yaml,
        load_xml_file,
        load_csv_file,
        load_text_file,
    )

    name = step.get("name", "unnamed")
    step_type = step.get("type", "")
    output_var = step.get("output")
    if not output_var:
        raise ValueError(f"loader step '{name}' requires an 'outputs' key")
    if isinstance(output_var, list):
        output_var = output_var[0]

    path = str(resolve(step.get("path", ""), context))

    if step_type == "load_directory":
        pattern = step.get("pattern")
        fmt = step.get("format")
        if not pattern:
            raise ValueError(f"load_directory step '{name}' requires a 'pattern' key")
        if not fmt:
            raise ValueError(f"load_directory step '{name}' requires a 'format' key")
        if fmt not in _LOADER_FORMATS:
            raise ValueError(
                f"load_directory step '{name}': invalid format '{fmt}'. "
                f"Must be one of: {sorted(_LOADER_FORMATS)}"
            )
        files = sorted(Path(path).glob(pattern))
        result = [_load_one(f, fmt, load_json_file, load_yaml, load_xml_file,
                            load_csv_file, load_text_file, step) for f in files]
    else:
        fmt = {
            "load_json": "json",
            "load_yaml": "yaml",
            "load_xml": "xml",
            "load_csv": "csv",
            "load_tsv": "tsv",
            "load_text": "text",
        }[step_type]
        result = _load_one(Path(path), fmt, load_json_file, load_yaml, load_xml_file,
                           load_csv_file, load_text_file, step)

    context[output_var] = result
    logger.info(f"✅ {step_type} '{name}': stored in context['{output_var}']")
