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
        # Provide safe built-ins like len, str, int, etc.
        safe_builtins = {
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
        # Create a safe evaluation environment with context variables
        return bool(eval(condition, {"__builtins__": safe_builtins}, context))
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
    return resolve(template, context)