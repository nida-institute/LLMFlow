"""For-each step handler — sequential and parallel iteration over a list."""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from typing import Any, Callable, Dict, Optional

from llmflow.modules.logger import Logger
from llmflow.utils.context import _MISSING, get_from_context, resolve
from llmflow.utils.io import sanitize_filename

logger = Logger()


def _format_iteration_fragment(value: Any, max_length: int = 48) -> str:
    """Create a filesystem-safe fragment representing an iteration value."""
    try:
        if isinstance(value, str):
            text = value
        elif isinstance(value, (int, float)):
            text = str(value)
        else:
            text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    except Exception:
        text = "item"

    text = text.strip() or "item"
    if len(text) > max_length:
        text = text[:max_length]

    sanitized = sanitize_filename(text)
    return sanitized or "item"


def resolve_template(template: str, context: Dict[str, Any]) -> str:
    """Resolve template variables in a string using context. Used for conditions."""
    resolved = resolve(template, context)
    if not isinstance(resolved, str):
        return str(resolved)
    return resolved


def _collect_loop_outputs(steps_list: list) -> tuple[set, set]:
    """Recursively collect append_to targets and output variable names from a steps list."""
    append_targets: set = set()
    output_vars: set = set()
    for s in steps_list:
        if "append_to" in s:
            append_targets.add(s["append_to"])
        if "outputs" in s:
            ov = s["outputs"]
            if isinstance(ov, str):
                output_vars.add(ov)
            elif isinstance(ov, list):
                output_vars.update(ov)
        if "steps" in s:
            na, no = _collect_loop_outputs(s["steps"])
            append_targets.update(na)
            output_vars.update(no)
    return append_targets, output_vars


class _AttrNamespace:
    """Wrap a dict for attribute-style access inside eval() sort-key expressions."""

    def __init__(self, d: dict) -> None:
        object.__setattr__(self, "_d", d)

    def __getattr__(self, name: str) -> Any:
        d = object.__getattribute__(self, "_d")
        if name in d:
            v = d[name]
            return _AttrNamespace(v) if isinstance(v, dict) else v
        raise AttributeError(name)


def _eval_key_expr(expr_str: str, ctx: Dict[str, Any]) -> Any:
    """Evaluate a ${...} sort/group key expression against a context dict."""
    m = re.match(r"^\$\{([^\}]+)\}$", expr_str)
    if not m:
        return resolve(expr_str, ctx)
    inner = m.group(1)
    result = get_from_context(inner, ctx)
    if result is not _MISSING:
        return result
    safe_builtins = {"len": len, "str": str, "int": int, "float": float, "bool": bool}
    eval_ns = {k: (_AttrNamespace(v) if isinstance(v, dict) else v) for k, v in ctx.items()}
    try:
        return eval(inner, {"__builtins__": safe_builtins}, eval_ns)  # noqa: S307
    except Exception:
        return expr_str


def _parse_order_by(order_by: Any) -> tuple[str, str]:
    """Parse an order-by value to (key_expr, direction)."""
    if isinstance(order_by, str):
        return order_by, "ascending"
    if isinstance(order_by, dict):
        return order_by.get("key", "${item}"), order_by.get("direction", "ascending")
    if isinstance(order_by, list) and order_by:
        first = order_by[0]
        return first.get("key", "${item}"), first.get("direction", "ascending")
    return "${item}", "ascending"


def _group_items(items: list, key_expr: str, context: Dict[str, Any]) -> list:
    """Group items by evaluating key_expr for each item. Returns [{key, items}] dicts."""
    groups: dict = {}
    order: list = []
    for item in items:
        key = _eval_key_expr(key_expr, {**context, "item": item})
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(item)
    return [{"key": k, "items": groups[k]} for k in order]


def _sort_groups(groups: list, order_expr: str, context: Dict[str, Any], direction: str = "ascending") -> list:
    """Sort groups by evaluating order_expr for each group."""
    def sort_key(group: dict) -> Any:
        return _eval_key_expr(order_expr, {**context, "group": group})
    return sorted(groups, key=sort_key, reverse=(direction == "descending"))


def _setup_iteration_context(
    index: int,
    item: Any,
    context: Dict[str, Any],
    item_var: str,
    step_name: str,
    debug_label_template: Optional[str],
    total: int = 0,
) -> Dict[str, Any]:
    """Build the isolated context for one for-each iteration."""
    iteration_context = deepcopy(context)
    iteration_context[item_var] = item
    iteration_context["_for_each_index"] = index
    iteration_context["loop"] = {
        "index": index,
        "total": total,
        "first": index == 1,
        "last": index == total,
    }

    parent_stack = iteration_context.get("_for_each_stack") or []
    stack = [dict(frame) for frame in parent_stack] if parent_stack else []

    label_fragment = None
    if debug_label_template:
        try:
            resolved_label = resolve(debug_label_template, iteration_context)
            if resolved_label is not None:
                label_fragment = _format_iteration_fragment(resolved_label)
        except Exception as exc:
            logger.debug(f"debug_label resolution failed in for-each '{step_name}': {exc}")

    value_fragment = _format_iteration_fragment(item)
    new_frame = {
        "level": len(stack) + 1,
        "variable": item_var,
        "value": value_fragment,
        "label": label_fragment or "",
        "index": index,
    }
    stack.append(new_frame)
    iteration_context["_for_each_stack"] = stack
    iteration_context["_for_each_meta"] = new_frame
    return iteration_context


def _run_iteration_steps(
    iteration_context: Dict[str, Any],
    steps: list,
    pipeline_config: Dict[str, Any],
    run_step_fn: Callable,
) -> Optional[str]:
    """Execute the nested steps for one iteration. Returns after_action or None."""
    for nested_step in steps:
        after_action = run_step_fn(nested_step, iteration_context, pipeline_config)
        if after_action in ("exit", "continue"):
            return after_action
    return None


def _propagate_iteration_results(
    iteration_context: Dict[str, Any],
    context: Dict[str, Any],
    append_targets: set,
    output_vars: set,
    baseline_lengths: Dict[str, int],
) -> None:
    """Propagate one iteration's results back to the parent context."""
    for target in append_targets:
        if target in iteration_context and isinstance(iteration_context[target], list):
            baseline = baseline_lengths.get(target, 0)
            new_items = iteration_context[target][baseline:]
            if target not in context:
                context[target] = list(new_items)
            else:
                context[target].extend(new_items)

    for var in output_vars:
        if var in iteration_context:
            context[var] = iteration_context[var]


def _run_for_each_parallel(
    input_data: list,
    item_var: str,
    steps: list,
    debug_label_template: Optional[str],
    step_name: str,
    parallel: int,
    append_to_targets: set,
    output_vars: set,
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any],
    run_step_fn: Callable,
) -> Optional[str]:
    """Parallel execution of for-each iterations with ordered result propagation."""
    baseline_lengths = {t: len(context[t]) for t in append_to_targets if t in context}

    def run_one(index: int, item: Any) -> tuple[int, Dict[str, Any], Optional[str]]:
        iter_ctx = _setup_iteration_context(
            index, item, context, item_var, step_name, debug_label_template,
            total=len(input_data),
        )
        after_action = _run_iteration_steps(iter_ctx, steps, pipeline_config, run_step_fn)
        return index, iter_ctx, after_action

    results: Dict[int, tuple[Dict[str, Any], Optional[str]]] = {}

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {
            executor.submit(run_one, i, item): i
            for i, item in enumerate(input_data, start=1)
        }
        for future in as_completed(futures):
            index, iter_ctx, after_action = future.result()
            results[index] = (iter_ctx, after_action)

    for index in sorted(results):
        iter_ctx, after_action = results[index]
        _propagate_iteration_results(
            iter_ctx, context, append_to_targets, output_vars, baseline_lengths
        )
        if after_action == "exit":
            logger.info(f"🛑 'after: exit' in parallel for-each iteration {index} - exiting pipeline")
            return "exit"

    return None


def run_for_each_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any],
    run_step_fn: Optional[Callable] = None,
) -> Optional[str]:
    """Execute a for-each loop step, sequentially or in parallel."""
    if run_step_fn is None:
        from llmflow.runner import run_step
        run_step_fn = run_step
    step_name = step.get("name", "unnamed")
    if "in" not in step:
        raise ValueError(
            f"for-each step '{step_name}': missing required 'in' key (the list to iterate "
            f"over). The legacy 'input' key was removed — use 'in'."
        )
    if "for" not in step:
        raise ValueError(
            f"for-each step '{step_name}': missing required 'for' key (the loop variable "
            f"name). The legacy 'item_var' key was removed — use 'for'."
        )
    _input_raw = resolve(step.get("in"), context)
    input_data: list = _input_raw if isinstance(_input_raw, list) else list(_input_raw)
    item_var: str = str(step["for"])
    steps = step.get("steps", [])
    debug_label_template = step.get("debug_label")
    parallel = step.get("parallel", 1)
    group_by_expr = step.get("group-by")
    order_by = step.get("order-by")

    if group_by_expr:
        input_data = _group_items(input_data, group_by_expr, context)
        if order_by:
            order_expr, direction = _parse_order_by(order_by)
            input_data = _sort_groups(input_data, order_expr, context, direction)
    elif order_by:
        order_expr, direction = _parse_order_by(order_by)
        input_data = sorted(
            input_data,
            key=lambda item: _eval_key_expr(order_expr, {**context, "item": item}),
            reverse=(direction == "descending"),
        )

    append_to_targets, output_vars = _collect_loop_outputs(steps)

    if parallel and isinstance(parallel, int) and parallel > 1:
        return _run_for_each_parallel(
            input_data, item_var, steps, debug_label_template, step_name,
            parallel, append_to_targets, output_vars, context, pipeline_config,
            run_step_fn,
        )

    for index, item in enumerate(input_data, start=1):
        baseline_lengths = {t: len(context[t]) for t in append_to_targets if t in context}

        iteration_context = _setup_iteration_context(
            index, item, context, item_var, step_name, debug_label_template,
            total=len(input_data),
        )
        after_action = _run_iteration_steps(iteration_context, steps, pipeline_config, run_step_fn)

        if after_action == "exit":
            logger.info("🛑 'after: exit' in for-each iteration - exiting pipeline")
            _propagate_iteration_results(
                iteration_context, context, append_to_targets, output_vars, baseline_lengths
            )
            return "exit"

        _propagate_iteration_results(
            iteration_context, context, append_to_targets, output_vars, baseline_lengths
        )

        if after_action == "continue":
            continue

    return None
