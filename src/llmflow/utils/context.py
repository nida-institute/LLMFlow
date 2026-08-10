"""Variable resolution utilities — ${var} substitution and context traversal."""

import re
from typing import Any, Dict, Optional

# Sentinel for "key not found" — distinguishes missing keys from None values.
_MISSING = object()


def build_run_context(pipeline_config: Dict[str, Any], vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build the flat variable context a pipeline run uses.

    Precedence, low to high: root-level directory keys (base) -> the ``variables:``
    block -> caller ``vars`` (e.g. ``--var``, which win). This is the single source of
    the run context — both the runner and the public ``resolve_pipeline_paths`` accessor
    call it, so run-time and inspection-time behavior cannot drift. See LLMFlow#186.
    """
    pipeline_root = pipeline_config.get("pipeline", pipeline_config)
    pipeline_vars = pipeline_root.get("variables", {}) or {}
    dir_ctx = {
        k: pipeline_root[k]
        for k in ("intermediate_file_directory", "output_file_directory")
        if pipeline_root.get(k)
    }
    return {**dir_ctx, **pipeline_vars, **(vars or {})}


def _apply_slice(result: Any, bracket_content: str) -> Any:
    """Apply slice notation to result."""
    slice_parts = bracket_content.split(":")

    start = None
    stop = None
    step = None

    if len(slice_parts) >= 1 and slice_parts[0].strip():
        try:
            start = int(slice_parts[0].strip())
        except ValueError:
            return _MISSING

    if len(slice_parts) >= 2 and slice_parts[1].strip():
        try:
            stop = int(slice_parts[1].strip())
        except ValueError:
            return _MISSING

    if len(slice_parts) >= 3 and slice_parts[2].strip():
        try:
            step = int(slice_parts[2].strip())
        except ValueError:
            return _MISSING

    if isinstance(result, (list, str)):
        try:
            return result[slice(start, stop, step)]
        except (IndexError, TypeError):
            return _MISSING
    else:
        return _MISSING


def _apply_index_or_key(result: Any, bracket_content: str) -> Any:
    """Apply numeric index or dict/object key access."""
    try:
        idx = int(bracket_content)
        if isinstance(result, list):
            if len(result) == 0 or idx >= len(result) or (idx < 0 and abs(idx) > len(result)):
                return _MISSING
            return result[idx]
        else:
            return _MISSING
    except ValueError:
        bracket_key = bracket_content.strip().strip("'\"")

        if isinstance(result, dict):
            return result.get(bracket_key, _MISSING)
        elif hasattr(result, '__getitem__'):
            try:
                return result[bracket_key]  # type: ignore[index]
            except (KeyError, TypeError):
                return _MISSING
        elif hasattr(result, bracket_key):
            return getattr(result, bracket_key)
        else:
            return _MISSING


def _apply_single_bracket(result: Any, bracket_content: str, part_idx: int, parts: list, bracket_idx: int) -> Any:
    """Helper to apply a single bracket operation (for wildcard processing)."""
    if ":" in bracket_content:
        return _apply_slice(result, bracket_content)
    else:
        return _apply_index_or_key(result, bracket_content)


def get_from_context(expr: str, ctx: Dict[str, Any]) -> Any:
    """
    Resolve dot notation and list indices from context.
    Supports: foo.bar, foo[0], foo[key], foo['key'], foo[-3:], foo[:5][*].field
    """
    parts = re.split(r"\.(?![^\[]*\])", expr)  # split on dots not inside brackets
    result = ctx

    for i, part in enumerate(parts):
        m = re.match(r"^([a-zA-Z0-9_]+)(.*)$", part)
        if not m:
            return _MISSING

        key = m.group(1)
        bracket_section = m.group(2)

        if isinstance(result, dict):
            result = result.get(key, _MISSING)
            if result is _MISSING:
                return _MISSING
        elif hasattr(result, key):
            try:
                result = getattr(result, key)
            except AttributeError:
                return _MISSING
        else:
            return _MISSING

        if bracket_section:
            bracket_matches = re.findall(r"\[([^\]]+)\]", bracket_section)

            for bracket_idx, bracket_content in enumerate(bracket_matches):
                if bracket_content == "*":
                    if not isinstance(result, list):
                        return _MISSING

                    remaining_brackets = bracket_matches[bracket_idx + 1:]
                    remaining_parts = parts[i + 1:]

                    if remaining_brackets or remaining_parts:
                        results = []
                        for item in result:
                            temp_result = item
                            for rb in remaining_brackets:
                                temp_result = _apply_single_bracket(
                                    temp_result, rb, i, parts, bracket_idx
                                )
                                if temp_result is _MISSING:
                                    results.append(None)
                                    break
                            else:
                                if remaining_parts:
                                    sub_expr = ".".join(remaining_parts)
                                    temp_result = (
                                        get_from_context(sub_expr, temp_result)
                                        if temp_result is not _MISSING
                                        else None
                                    )
                                    if temp_result is _MISSING:
                                        temp_result = None
                                results.append(temp_result)
                        return results
                    else:
                        return list(result)

                elif ":" in bracket_content:
                    result = _apply_slice(result, bracket_content)
                    if result is _MISSING:
                        return _MISSING

                else:
                    result = _apply_index_or_key(result, bracket_content)
                    if result is _MISSING:
                        return _MISSING

    return result


def resolve(value: Any, context: Dict[str, Any], max_depth: int = 5) -> Any:
    """
    Resolves variables within a value using the provided context.
    Supports both {curly} and ${dollar} notation with dot notation and list indexing.
    Returns native Python objects for exact variable references.
    """
    if isinstance(value, str):
        match = re.match(r"^\$\{([^\}]+)\}$", value)
        if match:
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            if resolved is not _MISSING:
                if isinstance(resolved, str) and ("${" in resolved or "{" in resolved):
                    if max_depth > 0:
                        return resolve(resolved, context, max_depth - 1)
                return resolved
            return value

        match = re.match(r"^\{([^\}]+)\}$", value)
        if match:
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            if resolved is not _MISSING:
                if isinstance(resolved, str) and ("${" in resolved or "{" in resolved):
                    if max_depth > 0:
                        return resolve(resolved, context, max_depth - 1)
                return resolved
            return value

        def replace_var(match: re.Match) -> str:
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            if resolved is _MISSING:
                return match.group(0)
            if isinstance(resolved, str) and ("${" in resolved or "{" in resolved) and max_depth > 0:
                resolved = resolve(resolved, context, max_depth - 1)
            return str(resolved)

        value = re.sub(r"\$\{([^\}]+)\}", replace_var, value)
        value = re.sub(r"(?<!\$)\{([^\}]+)\}", replace_var, value)
        return value

    elif isinstance(value, dict):
        return {k: resolve(v, context, max_depth) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve(item, context, max_depth) for item in value]

    return value
