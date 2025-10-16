import json
import re
import typer
import llm
import openai
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from llmflow.modules.json_parser import parse_llm_json_response
from llmflow.modules.logger import Logger
from llmflow.utils.io import normalize_nfc
from llmflow.modules.llm_response_clean import clean_llm_response_text

# --- Singleton Model Holder ---
_model_singleton = {}

logger = Logger()

def get_gpt_model(model_name):
    """
    Retrieves the GPT model object based on the provided model name.
    Uses a singleton pattern to ensure only one instance per model name.
    """
    if not model_name:
        typer.secho("Error: Model name cannot be empty.", fg=typer.colors.RED)
        raise typer.Exit(1)

    if model_name in _model_singleton:
        return _model_singleton[model_name]

    try:
        model = llm.get_model(model_name)
        if not model:
            typer.secho(f"Error: Model '{model_name}' not found.", fg=typer.colors.RED)
            raise typer.Exit(1)
        _model_singleton[model_name] = model
        return model
    except Exception as e:
        typer.secho(f"Error retrieving model '{model_name}': {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

def validate_openai_config(config):
    """
    Validate OpenAI-specific configuration parameters.
    """
    logger.debug("🔍 Validating OpenAI configuration")

    errors = []
    warnings = []

    # Check API key
    api_key = config.get("api_key") or openai.api_key
    if not api_key:
        errors.append("OpenAI API key not found in config or environment")

    # Validate model
    model = config.get("model", "")
    openai_models = [
        "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
    ]
    if model and model not in openai_models:
        warnings.append(f"Unknown OpenAI model '{model}', supported: {openai_models}")

    # Validate parameters
    temperature = config.get("temperature")
    if temperature is not None:
        if not 0 <= temperature <= 2:
            errors.append("temperature must be between 0 and 2")

    max_tokens = config.get("max_tokens")
    if max_tokens is not None:
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            errors.append("max_tokens must be a positive integer")

    top_p = config.get("top_p")
    if top_p is not None:
        if not 0 <= top_p <= 1:
            errors.append("top_p must be between 0 and 1")

    frequency_penalty = config.get("frequency_penalty")
    if frequency_penalty is not None:
        if not -2 <= frequency_penalty <= 2:
            errors.append("frequency_penalty must be between -2 and 2")

    presence_penalty = config.get("presence_penalty")
    if presence_penalty is not None:
        if not -2 <= presence_penalty <= 2:
            errors.append("presence_penalty must be between -2 and 2")

    # Log results
    if errors:
        for error in errors:
            logger.error(f"❌ Config error: {error}")

    if warnings:
        for warning in warnings:
            logger.warning(f"⚠️  Config warning: {warning}")

    if not errors and not warnings:
        logger.debug("✅ OpenAI configuration is valid")

    return len(errors) == 0, errors, warnings
