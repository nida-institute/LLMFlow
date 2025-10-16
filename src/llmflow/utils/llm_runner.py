import json
import time
import unicodedata
import llm
from typing import Dict, Any, Optional

from llmflow.modules.logger import Logger
from llmflow.modules.json_parser import parse_llm_json_response
from llmflow.modules.llm_response_clean import clean_llm_response_text

logger = Logger()

# Model cache - simpler than singleton pattern
_model_cache: Dict[str, Any] = {}

def get_model(model_name: str):
    """Get LLM model with caching."""
    if model_name not in _model_cache:
        _model_cache[model_name] = llm.get_model(model_name)
    return _model_cache[model_name]

# Generic parameter schema
PARAMETER_SCHEMAS = {
    "temperature": {"type": float, "min": 0, "max": 2},
    "max_tokens": {"type": int, "min": 1},
    "top_p": {"type": float, "min": 0, "max": 1},
    "top_k": {"type": int, "min": 1},
    "frequency_penalty": {"type": float, "min": -2, "max": 2},
    "presence_penalty": {"type": float, "min": -2, "max": 2},
    "timeout_seconds": {"type": int, "min": 1},
    "seed": {"type": int},
}

def validate_parameter(name: str, value: Any) -> list[str]:
    """Validate a single parameter generically."""
    if name not in PARAMETER_SCHEMAS:
        return []  # Unknown params are passed through

    schema = PARAMETER_SCHEMAS[name]
    errors = []

    # Type validation
    if not isinstance(value, schema["type"]):
        errors.append(f"{name} must be of type {schema['type'].__name__}")
        return errors

    # Range validation
    if "min" in schema and value < schema["min"]:
        errors.append(f"{name} must be >= {schema['min']}")
    if "max" in schema and value > schema["max"]:
        errors.append(f"{name} must be <= {schema['max']}")

    return errors

def validate_llm_config(config: Dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    """Validate LLM configuration parameters."""
    errors = []
    warnings = []

    # Temperature validation (universal)
    temperature = config.get("temperature")
    if temperature is not None and not (0 <= temperature <= 2):
        errors.append("temperature must be between 0 and 2")

    # Max tokens validation (universal)
    max_tokens = config.get("max_tokens")
    if max_tokens is not None and (not isinstance(max_tokens, int) or max_tokens <= 0):
        errors.append("max_tokens must be a positive integer")

    # Top-p validation (universal)
    top_p = config.get("top_p")
    if top_p is not None and not (0 <= top_p <= 1):
        errors.append("top_p must be between 0 and 1")

    # Frequency/presence penalty validation (common across providers)
    for penalty in ["frequency_penalty", "presence_penalty"]:
        value = config.get(penalty)
        if value is not None and not (-2 <= value <= 2):
            errors.append(f"{penalty} must be between -2 and 2")

    # Model name validation (generic - just check it exists)
    model = config.get("model")
    if not model:
        errors.append("model name is required")

    # Timeout validation
    timeout = config.get("timeout_seconds")
    if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
        errors.append("timeout_seconds must be a positive integer")

    return len(errors) == 0, errors, warnings

def call_llm(prompt: str, config: Dict[str, Any], output_type: str = "text"):
    """Main LLM calling function with validation and caching."""
    logger.debug(f"🤖 Calling LLM with config: {config}, output_type: {output_type}")

    # Validate config
    is_valid, errors, warnings = validate_llm_config(config)
    if not is_valid:
        raise ValueError(f"Invalid LLM config: {errors}")

    # Get model
    model_name = config.get("model", "gpt-4o")
    model = get_model(model_name)

    # Call model
    response = _call_model(model, prompt, config)

    # Handle response type
    if output_type.lower() == "json":
        return parse_llm_json_response(response)
    return response

def _call_model(model, prompt: str, config: Dict[str, Any]) -> str:
    """Internal helper to call the model."""
    # Only pass known valid LLM parameters
    valid_llm_params = {
        'temperature', 'max_tokens', 'top_p', 'top_k', 'stop',
        'frequency_penalty', 'presence_penalty', 'seed'
    }

    # Filter config to only include valid parameters
    options = {k: v for k, v in config.items()
               if k != "model" and k in valid_llm_params}

    logger.debug(f"Filtered options for model: {options}")

    response = model.prompt(prompt, **options)
    raw_response = response.text()

    # Clean the response to remove outer markdown fences BEFORE any processing
    cleaned_response = clean_llm_response_text(raw_response)

    return cleaned_response
