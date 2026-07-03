"""Step output handling — store results in context, write saveas files."""

from pathlib import Path
from typing import Any, Dict, List

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.file_io import _record_written_file, save_content_to_file
from llmflow.utils.get_prefix_directory import get_prefix_directory

logger = Logger()


def handle_step_outputs(step: Dict[str, Any], result: Any, context: Dict[str, Any], base_dir: str = ".") -> None:
    """Store step result in context and handle saveas."""
    context.pop("_last_saved_files", None)
    saved_paths: List[str] = []

    outputs = step.get("outputs") or step.get("output")
    if outputs is not None:
        if isinstance(outputs, str):
            context[outputs] = result
            logger.info(f"📦 Stored in context['{outputs}']: {type(result).__name__}, length={len(str(result)) if result else 0}")
            if step.get("name") == "bodies":
                logger.debug(f"   First 100 chars: {repr(str(result)[:100]) if result else 'NONE'}")
        elif isinstance(outputs, list):
            if len(outputs) == 1:
                context[outputs[0]] = result
                logger.debug(f"Stored result in context['{outputs[0]}']")
            else:
                for i, output_name in enumerate(outputs):
                    value = result[i] if isinstance(result, (list, tuple)) and i < len(result) else result
                    context[output_name] = value
                    logger.debug(f"Stored result in context['{output_name}']")

    append_to = step.get("append_to")
    if append_to:
        if append_to not in context:
            context[append_to] = []
        if outputs:
            if isinstance(outputs, str):
                value_to_append = context.get(outputs)
            elif isinstance(outputs, list):
                value_to_append = context.get(outputs[0])
            else:
                value_to_append = result
        else:
            value_to_append = result
        context[append_to].append(value_to_append)
        logger.debug(f"Appended to {append_to}: now has {len(context[append_to])} items")

    if "saveas" in step:
        if outputs is None:
            temp_output = f"_temp_output_{id(result)}"
            step_with_output = {**step, "outputs": temp_output}
            context[temp_output] = result
            saved_paths = handle_step_saveas(step_with_output, context)
            del context[temp_output]
        else:
            saved_paths = handle_step_saveas(step, context)

    context["_last_saved_files"] = saved_paths


def handle_step_saveas(step: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    """Handle saveas output for pipeline steps and return written paths."""
    saveas_config = step["saveas"]
    outputs = step.get("outputs") or step.get("output")
    saved_paths: List[str] = []

    def get_content() -> Any:
        if isinstance(outputs, list):
            return context[outputs[0]]
        if isinstance(outputs, str):
            return context[outputs]
        raise ValueError("No output specified for saveas")

    if isinstance(saveas_config, str):
        path = resolve(saveas_config, context)
        content = get_content()
        fmt = step.get("format", "auto")
        saved_path = save_content_to_file(content, str(path), fmt)
        _record_written_file(saved_path)
        saved_paths.append(saved_path)
        return saved_paths

    if isinstance(saveas_config, dict):
        raw_path = saveas_config["path"]
        logger.debug(f"Resolving saveas path: {raw_path}")
        logger.debug(f"Context keys: {list(context.keys())}")
        path = resolve(raw_path, context)
        logger.debug(f"Resolved path: {path}")
        group_cfg = saveas_config.get("group_by_prefix")
        content = get_content()
        fmt = step.get("format", "auto")

        if group_cfg:
            fname = Path(str(path)).name
            if isinstance(group_cfg, int):
                prefix_dir = get_prefix_directory(fname, prefix_length=group_cfg)
            else:
                prefix_dir = get_prefix_directory(
                    fname,
                    prefix_length=group_cfg.get("prefix_length"),
                    prefix_delimiter=group_cfg.get("prefix_delimiter"),
                )
            path = str(Path(str(path)).parent / prefix_dir / fname)

        saved_path = save_content_to_file(content, str(path), fmt)
        _record_written_file(saved_path)
        saved_paths.append(saved_path)
        return saved_paths

    if isinstance(saveas_config, list):
        for item in saveas_config:
            if isinstance(item, dict):
                path = resolve(item["path"], context)
                content_spec = item.get("content")
                content = resolve(content_spec, context) if content_spec else get_content()
                fmt = item.get("format", "auto")
                saved_path = save_content_to_file(content, str(path), fmt)
                _record_written_file(saved_path)
                saved_paths.append(saved_path)
        return saved_paths

    raise ValueError("Invalid saveas configuration type")
