"""JSON Schema validator plugin.

Validates a pipeline payload against a JSON Schema file.

Handles both live Python objects (fresh LLM run) and raw JSON strings/bytes
(payloads loaded from disk via --rewind-to), so validation succeeds in both
cases without requiring changes to the rewind infrastructure.
"""

import json
from pathlib import Path
from typing import Any, Dict

from llmflow.modules.logger import Logger

logger = Logger()

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The json_schema_validator plugin requires the 'jsonschema' package. "
        "Add it to your project dependencies: pip install jsonschema"
    ) from exc


def execute(step_config: Dict) -> Any:
    """Validate a payload against a JSON Schema.

    Returns the (possibly coerced) payload unchanged on success so downstream
    steps can use it normally.

    Args:
        step_config: Resolved step config dict containing:
            inputs.payload    – the data to validate (dict/list *or* a JSON
                                string/bytes loaded from a saveas artifact)
            inputs.schema_path – path to the ``.schema.json`` file, resolved
                                 relative to the pipeline working directory

    Raises:
        jsonschema.ValidationError: if the payload does not match the schema.
        FileNotFoundError: if the schema file cannot be found.
        json.JSONDecodeError: if a string payload is not valid JSON.
    """
    inputs = step_config.get("inputs", {})

    payload = inputs.get("payload")
    schema_path = inputs.get("schema_path")

    if payload is None:
        raise ValueError("json_schema_validator requires 'payload' in inputs")
    if not schema_path:
        raise ValueError("json_schema_validator requires 'schema_path' in inputs")

    # --- Rewind compatibility fix -----------------------------------------
    # When a step is replayed via --rewind-to, LLMFlow loads the saved artifact
    # from disk and passes it as a raw string.  jsonschema.validate() expects a
    # native Python object, so we coerce before validation here rather than
    # requiring the rewind infrastructure to parse the file.
    if isinstance(payload, (str, bytes)):
        logger.debug("json_schema_validator: coercing string payload via json.loads")
        payload = json.loads(payload)
    # ----------------------------------------------------------------------

    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with schema_file.open(encoding="utf-8") as fh:
        schema = json.load(fh)

    logger.info(f"🔍 Validating payload against {schema_file.name}")
    jsonschema.validate(instance=payload, schema=schema)
    logger.info("✅ Schema validation passed")

    return payload


def register() -> Dict[str, Any]:
    """Register the json_schema_validator plugin."""
    return {"json_schema_validator": execute}
