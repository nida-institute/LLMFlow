def eval_condition(condition: str, context: dict) -> bool:
    """Evaluate a condition string against the context.

    Args:
        condition: Python expression as string
        context: Variables to make available during evaluation

    Returns:
        Boolean result of the expression
    """
    try:
        # Create a safe evaluation environment with context variables
        return bool(eval(condition, {"__builtins__": {}}, context))
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Condition evaluation failed: {condition} - {e}")
        return False