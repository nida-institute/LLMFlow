"""Window step handler — fixed, condition-based, and token-based windowing."""

import json
from copy import deepcopy
from typing import Any, Callable, Dict, Optional

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.guards import build_eval_locals, _safe_eval
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def _eval_window_condition(expr: str, item: Any, context: dict) -> bool:
    """Evaluate a window start_when/end_when condition with item in scope."""
    stripped = expr.strip()
    if stripped.startswith("${") and stripped.endswith("}"):
        stripped = stripped[2:-1]
    eval_locals = build_eval_locals({**context, "item": item})
    try:
        return bool(_safe_eval(stripped, eval_locals))
    except Exception as exc:
        logger.warning(f"window condition eval failed: {stripped} - {exc}")
        return False


def _build_windows_fixed(items: list, size: int, stride: int, include_partial: bool) -> list[list]:
    """Generate fixed-size windows (tumbling when stride==size, sliding when stride<size)."""
    windows = []
    i = 0
    while i < len(items):
        window = items[i:i + size]
        if len(window) == size or include_partial:
            windows.append(window)
        i += stride
    return windows


def _build_windows_condition(items: list, start_when: str, end_when: Optional[str], context: dict) -> list[list]:
    """Generate condition-based tumbling windows."""
    windows = []
    current: Optional[list] = None

    for item in items:
        is_start = _eval_window_condition(start_when, item, context)

        if end_when:
            is_end = _eval_window_condition(end_when, item, context)
            if is_start and current is not None:
                windows.append(current)
                current = None
            if is_start:
                current = [item]
            elif current is not None:
                current.append(item)
            if is_end and current is not None:
                windows.append(current)
                current = None
        else:
            if is_start:
                if current is not None:
                    windows.append(current)
                current = [item]
            elif current is not None:
                current.append(item)

    if current is not None and end_when is None:
        windows.append(current)
    return windows


def _build_windows_token(
    items: list,
    size_by_tokens: int,
    stride_by_tokens: int,
    model: str,
    include_partial: bool,
) -> list[list]:
    """Token-aware sliding windows using tiktoken."""
    try:
        import tiktoken
    except ImportError:
        raise ImportError(
            "tiktoken is required for token-based windowing. "
            "Install with: pip install tiktoken"
        ) from None

    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(item: Any) -> int:
        text = json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list)) else str(item)
        return len(enc.encode(text))

    counts = [count_tokens(item) for item in items]
    n = len(items)
    windows: list[list] = []
    start = 0

    while start < n:
        total = 0
        end = start
        while end < n:
            if total + counts[end] > size_by_tokens and end > start:
                break
            total += counts[end]
            end += 1

        is_partial = end == n
        if not is_partial or include_partial:
            windows.append(items[start:end])

        if stride_by_tokens <= 0:
            start = end
        else:
            overlap_tokens = 0
            k = end
            while k > start:
                if overlap_tokens + counts[k - 1] <= stride_by_tokens:
                    overlap_tokens += counts[k - 1]
                    k -= 1
                else:
                    break
            start = max(k, start + 1)

    return windows


def _slice_window_from_pos(items: list, start: int, size_by_tokens: int, model: str) -> list:
    """Slice items[start:] accumulating up to size_by_tokens tokens."""
    try:
        import tiktoken
    except ImportError:
        raise ImportError(
            "tiktoken is required for token-based windowing. "
            "Install with: pip install tiktoken"
        ) from None

    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(item: Any) -> int:
        text = json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list)) else str(item)
        return len(enc.encode(text))

    total = 0
    end = start
    n = len(items)
    while end < n:
        tok = count_tokens(items[end])
        if total + tok > size_by_tokens and end > start:
            break
        total += tok
        end += 1

    return items[start:end] if end > start else []


def _propagate_window_outputs(
    context: Dict[str, Any],
    iteration_context: Dict[str, Any],
    append_to_targets: set,
    output_vars: set,
) -> None:
    """Copy per-iteration results back to the parent context."""
    for target in append_to_targets:
        if target in iteration_context and isinstance(iteration_context[target], list):
            if target not in context:
                context[target] = iteration_context[target][:]
            else:
                orig = len(context[target])
                context[target].extend(iteration_context[target][orig:])
    for output_var in output_vars:
        if output_var in iteration_context:
            context[output_var] = iteration_context[output_var]


def run_window_advance_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any],
    run_step_fn: Callable,
) -> None:
    """Execute a !window_advance step inside a window step."""
    step_name = step.get("name", "unnamed")
    inner_step = step.get("step")
    cursor_var = step.get("cursor")

    if not inner_step:
        raise ValueError(f"!window_advance step '{step_name}': requires a 'step' key")
    if not cursor_var:
        raise ValueError(f"!window_advance step '{step_name}': requires a 'cursor' key")

    run_step_fn(inner_step, context, pipeline_config)

    cursor_value = context.get(cursor_var)
    context["_window_cursor"] = cursor_value
    logger.info(f"🪟  window_advance '{step_name}': cursor → {cursor_value!r}")


def _run_window_dynamic(
    step: Dict[str, Any],
    input_data: list,
    steps: list,
    item_var: str,
    size_by_tokens: Optional[int],
    size: Any,
    model: str,
    include_partial: bool,
    append_to_targets: set,
    output_vars: set,
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any],
    run_step_fn: Callable,
) -> Optional[str]:
    """Dynamic windowing: cursor is determined each iteration by a !window_advance step."""
    step_name = step.get("name", "unnamed")
    start = 0
    index = 0
    n = len(input_data)

    while start < n:
        index += 1

        if size_by_tokens is not None:
            window = _slice_window_from_pos(input_data, start, size_by_tokens, model)
        else:
            window = input_data[start:start + size]

        if not window:
            break

        iteration_context = deepcopy(context)
        iteration_context[item_var] = window
        iteration_context["_window_index"] = index
        iteration_context["window_num"] = index
        iteration_context["_window_first"] = window[0] if window else None
        iteration_context["_window_last"] = window[-1] if window else None
        iteration_context["_window_cursor"] = None

        parent_stack = iteration_context.get("_for_each_stack") or []
        stack = [dict(frame) for frame in parent_stack] if parent_stack else []
        new_frame = {
            "level": len(stack) + 1,
            "variable": item_var,
            "value": f"window_{index}",
            "label": f"window_{index}",
            "index": index,
        }
        stack.append(new_frame)
        iteration_context["_for_each_stack"] = stack
        iteration_context["_for_each_meta"] = new_frame

        logger.info(f"🪟  Window step '{step_name}': dynamic window {index}, start={start}")

        for nested_step in steps:
            after_action = run_step_fn(nested_step, iteration_context, pipeline_config)
            if after_action == "exit":
                _propagate_window_outputs(context, iteration_context, append_to_targets, output_vars)
                return "exit"
            elif after_action == "continue":
                break

        _propagate_window_outputs(context, iteration_context, append_to_targets, output_vars)

        cursor = iteration_context.get("_window_cursor")
        if cursor is None:
            logger.info(f"🪟  Window step '{step_name}': cursor is null — stopping after window {index}")
            break

        if not isinstance(cursor, int) or cursor < 0:
            raise ValueError(
                f"Window step '{step_name}': !window_advance cursor must be a "
                f"non-negative integer or null, got {cursor!r}"
            )
        if cursor <= start:
            raise ValueError(
                f"Window step '{step_name}': !window_advance cursor {cursor} does not "
                f"advance beyond current start {start} — infinite loop prevented"
            )

        start = cursor

    return None


def run_window_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any],
    run_step_fn: Optional[Callable] = None,
) -> Optional[str]:
    """Execute a window step — iterate over windows of the input list."""
    if run_step_fn is None:
        from llmflow.runner import run_step
        run_step_fn = run_step
    from llmflow.steps.function import run_function_step

    step_name = step.get("name", "unnamed")
    if "in" not in step:
        raise ValueError(
            f"Window step '{step_name}': missing required 'in' key (the list to window "
            f"over). The legacy 'input'/'over' keys were removed — use 'in'."
        )
    if "for" not in step:
        raise ValueError(
            f"Window step '{step_name}': missing required 'for' key (the window variable "
            f"name). The legacy 'item_var' key was removed — use 'for'."
        )
    input_data = resolve(step.get("in"), context)
    if not isinstance(input_data, list):
        raise ValueError(
            f"Window step '{step_name}': 'in' must resolve to a list, "
            f"got {type(input_data).__name__}"
        )

    item_var: str = str(step["for"])
    steps = step.get("steps", [])
    size = step.get("size")
    stride = step.get("stride", size)
    include_partial = step.get("include_partial", True)
    start_when = step.get("start_when")
    end_when = step.get("end_when")
    size_by_tokens = step.get("size_by_tokens")
    stride_by_tokens = step.get("stride_by_tokens", 0)
    _model_raw = resolve(step.get("model", "gpt-4o"), context)
    model: str = str(_model_raw) if not isinstance(_model_raw, str) else _model_raw

    if start_when:
        windows = _build_windows_condition(input_data, start_when, end_when, context)
    elif size_by_tokens is not None:
        if not isinstance(size_by_tokens, int) or size_by_tokens < 1:
            raise ValueError(f"Window step '{step_name}': 'size_by_tokens' must be a positive integer")
        if not isinstance(stride_by_tokens, int) or stride_by_tokens < 0:
            raise ValueError(f"Window step '{step_name}': 'stride_by_tokens' must be a non-negative integer")
        windows = _build_windows_token(input_data, size_by_tokens, stride_by_tokens, model, include_partial)
    else:
        if not isinstance(size, int):
            raise ValueError(f"Window step '{step_name}': 'size' must be a positive integer")
        if not isinstance(stride, int):
            raise ValueError(f"Window step '{step_name}': 'stride' must be a positive integer")
        windows = _build_windows_fixed(input_data, size, stride, include_partial)

    if not windows:
        logger.info(f"⏭️  Window step '{step.get('name', 'unnamed')}': no windows generated, skipping")
        return None

    def collect_outputs(steps_list):
        append_targets = set()
        output_vars = set()
        for s in steps_list:
            if "append_to" in s:
                append_targets.add(s["append_to"])
            if "output" in s:
                ov = s["output"]
                if isinstance(ov, str):
                    output_vars.add(ov)
                elif isinstance(ov, list):
                    output_vars.update(ov)
            if "steps" in s:
                na, no = collect_outputs(s["steps"])
                append_targets.update(na)
                output_vars.update(no)
            if s.get("_tag") == "window_advance" and "step" in s:
                na, no = collect_outputs([s["step"]])
                append_targets.update(na)
                output_vars.update(no)
        return append_targets, output_vars

    append_to_targets, output_vars = collect_outputs(steps)

    has_advance = any(s.get("_tag") == "window_advance" for s in steps)
    if has_advance:
        return _run_window_dynamic(
            step, input_data, steps, item_var,
            size_by_tokens, size, model, include_partial,
            append_to_targets, output_vars, context, pipeline_config,
            run_step_fn,
        )

    for index, window in enumerate(windows, start=1):
        iteration_context = deepcopy(context)
        iteration_context[item_var] = window
        iteration_context["_window_index"] = index
        iteration_context["window_num"] = index
        iteration_context["_window_first"] = window[0] if window else None
        iteration_context["_window_last"] = window[-1] if window else None

        parent_stack = iteration_context.get("_for_each_stack") or []
        stack = [dict(frame) for frame in parent_stack] if parent_stack else []
        new_frame = {
            "level": len(stack) + 1,
            "variable": item_var,
            "value": f"window_{index}",
            "label": f"window_{index}",
            "index": index,
        }
        stack.append(new_frame)
        iteration_context["_for_each_stack"] = stack
        iteration_context["_for_each_meta"] = new_frame

        for nested_step in steps:
            after_action = run_step_fn(nested_step, iteration_context, pipeline_config)

            if after_action == "exit":
                logger.info("🛑 'after: exit' in window iteration - exiting pipeline")
                for target in append_to_targets:
                    if target in iteration_context and isinstance(iteration_context[target], list):
                        if target not in context:
                            context[target] = iteration_context[target][:]
                        else:
                            orig = len(context[target])
                            context[target].extend(iteration_context[target][orig:])
                for output_var in output_vars:
                    if output_var in iteration_context:
                        context[output_var] = iteration_context[output_var]
                return "exit"

            elif after_action == "continue":
                logger.info("⏭️  'after: continue' in window iteration - next window")
                break

        for target in append_to_targets:
            if target in iteration_context and isinstance(iteration_context[target], list):
                if target not in context:
                    context[target] = iteration_context[target][:]
                else:
                    orig = len(context[target])
                    context[target].extend(iteration_context[target][orig:])

        for output_var in output_vars:
            if output_var in iteration_context:
                context[output_var] = iteration_context[output_var]

    merge_config = step.get("merge")
    if merge_config:
        logger.info(f"🔀 Window step '{step_name}': running merge")
        merge_result = run_function_step(merge_config, context, pipeline_config)
        handle_step_outputs(merge_config, merge_result, context)

    return None
