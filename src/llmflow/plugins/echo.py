"""Echo plugin - returns a static message or value."""

from typing import Any, Dict
from llmflow.modules.logger import Logger

logger = Logger()


def echo(inputs: Dict[str, Any]) -> str:
    """
    Echo a message or value.

    Args:
        inputs: Dict with 'message' key

    Returns:
        The message string
    """
    message = inputs.get("message", "")
    logger.debug(f"Echo: {message}")
    return str(message)


# Plugin metadata
PLUGIN_NAME = "echo"
PLUGIN_FUNCTION = echo