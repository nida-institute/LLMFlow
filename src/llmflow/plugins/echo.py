"""Echo plugin - returns a static message or value."""

from typing import Any, Dict
from llmflow.modules.logger import Logger

logger = Logger()


def echo(
    inputs: Dict[str, Any] | None = None,
    *,
    context: Dict[str, Any] | None = None,
    **kwargs: Any,
) -> Any:
    """
    Simple echo plugin that returns the provided value unchanged.

    Supports both plugin-driven invocation (passing a full inputs dict) and
    function-step invocation (passing keyword arguments like ``value=...``).
    """
    if inputs is None:
        inputs = {}
    if not isinstance(inputs, dict):
        raise ValueError("Echo plugin expects inputs to be a dict.")

    if kwargs:
        inputs = {**inputs, **kwargs}

    if "value" not in inputs:
        raise ValueError("Echo plugin requires a 'value' argument.")
    return inputs["value"]


# Plugin metadata
PLUGIN_NAME = "echo"
PLUGIN_FUNCTION = echo