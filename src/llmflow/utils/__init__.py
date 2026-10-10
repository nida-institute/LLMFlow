def condition_safe_builtins() -> dict:
    """The names a `condition:` expression may use besides the pipeline's own variables.

    One declaration, read twice: the evaluator builds its environment from it, and the linter's
    variable validator skips these names rather than reporting them undefined. They were a
    literal inside the evaluator, so `sp lint` refused `${len(...)}` while the evaluator ran it
    — the linter being the stricter of the two, which is the wrong way round, since it is the
    half that cannot execute the expression. Reported by a consumer who had to compute counts in
    a `function` step to work around it, at the cost of a step per branch.
    """
    return {
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "True": True,
        "False": False,
        "None": None,
    }


def eval_condition(condition: str, context: dict) -> bool:
    """Evaluate a condition string against the context.

    Args:
        condition: Python expression as string
        context: Variables to make available during evaluation

    Returns:
        Boolean result of the expression
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        return bool(eval(condition, {"__builtins__": condition_safe_builtins()}, context))
    except Exception as e:
        logger.warning(f"Condition evaluation failed: {condition} - {e}")
        return False


def interpolate_template(template: str, context: dict) -> str:
    """Interpolate variables in a template string.

    Args:
        template: Template string with ${var} or {var} placeholders
        context: Variables to substitute

    Returns:
        Interpolated string
    """
    from llmflow.runner import resolve  # Correct import path
    return str(resolve(template, context))
