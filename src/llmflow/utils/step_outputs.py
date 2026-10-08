"""Step output handling — store results in context, write saveas files."""

from pathlib import Path
from typing import Any, Dict, List

from llmflow.defects import DEFECT_LOG_KEY, RESERVED_KEY
from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.file_io import _record_written_file, save_content_to_file
from llmflow.utils.get_prefix_directory import get_prefix_directory

logger = Logger()


def parse_output_entry(entry: str) -> tuple[str, str]:
    """Split one `output:` list entry into `(variable, member)`.

    `"reference"` binds the member under its own name; `"passage_info=reference"` renames it.
    The left side is the pipeline's variable and the right is the step's member, which reads as
    the assignment it is (#263).
    """
    variable, sep, member = entry.partition("=")
    if not sep:
        return entry.strip(), entry.strip()
    return variable.strip(), member.strip()


def _bound_variables(step: Dict[str, Any], members: Dict[str, Any], primary: str) -> Dict[str, Any]:
    """Map each variable this step binds to its value, for a step type declaring members.

    A bare `output:` name binds the **primary** member — today's behaviour for every step type
    that has one, which is what keeps existing pipelines working. A list names members, each
    optionally renamed. Naming a member is how it is requested, so one nobody names is absent
    rather than empty: `say-which-kind-of-nothing`, whose stated exemption is a request list.
    """
    outputs = step.get("output")
    if isinstance(outputs, str):
        return {outputs: members.get(primary)}
    if isinstance(outputs, (list, tuple)):
        bound = {}
        for entry in outputs:
            variable, member = parse_output_entry(str(entry))
            bound[variable] = members.get(member)
        return bound
    return {}


def handle_step_outputs(
    step: Dict[str, Any],
    result: Any,
    context: Dict[str, Any],
    base_dir: str = ".",
    defects: Any = None,
    members: Dict[str, Any] | None = None,
    primary: str = "",
) -> None:
    """Store step result in context and handle saveas.

    Every step handler passes through here, which is why the defect log is drained here: a step
    of any type — function, basex, duckdb, llm under a schema — reports a defect by returning it
    under `defects`, and needs to know nothing about the log to do so.

    `members` is passed by a step type that declares them (#263). Its `output:` then names members
    rather than binding positionally, and `saveas` writes the first one named. Every other step
    type passes `result` alone and behaves exactly as it always has — `function` chief among them,
    since it returns arbitrary Python and cannot declare what it will produce.
    """
    context.pop("_last_saved_files", None)
    saved_paths: List[str] = []

    # The log travels in the context, which is the channel every step already has — passing it
    # down every handler signature would be the side channel this feature exists to avoid.
    log = defects if defects is not None else context.get(DEFECT_LOG_KEY)
    # Copied out, never removed: a step's output is its own, and a `saveas` should write what the
    # step actually returned.
    if log is not None and isinstance(result, dict) and RESERVED_KEY in result:
        log.extend(str(step.get("name", "unnamed")), result[RESERVED_KEY])

    # A member-producing step binds by name, and `saveas` is handed a step whose `output:` is the
    # plain variable names — so `handle_step_saveas` never has to know about `variable=member`.
    if members is not None:
        bound = _bound_variables(step, members, primary)
        context.update(bound)
        for variable, value in bound.items():
            logger.debug(f"📦 Stored in context['{variable}']: {type(value).__name__}")
        step = {**step, "output": list(bound)} if bound else step
        result = next(iter(bound.values()), members.get(primary))

    outputs = step.get("output")
    if members is None and outputs is not None:
        if isinstance(outputs, str):
            context[outputs] = result
            logger.debug(
                f"📦 Stored in context['{outputs}']: {type(result).__name__}, "
                f"length={len(str(result)) if result else 0}"
            )
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
            step_with_output = {**step, "output": temp_output}
            context[temp_output] = result
            saved_paths = handle_step_saveas(step_with_output, context)
            del context[temp_output]
        else:
            saved_paths = handle_step_saveas(step, context)

    context["_last_saved_files"] = saved_paths


def handle_step_saveas(step: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    """Handle saveas output for pipeline steps and return written paths."""
    saveas_config = step["saveas"]
    outputs = step.get("output")
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
        saved_path = save_content_to_file(content, str(path), "auto")
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
        fmt = saveas_config.get("format", "auto")

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
