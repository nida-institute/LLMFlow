import json
import time
import unicodedata
from llmflow.modules.logger import Logger
from llmflow.modules.json_parser import parse_llm_json_response

# Use unified logger
logger = Logger()

def call_llm(prompt_text, config=None, output_type="text", from_file=False, max_retries=3, retry_backoff=2):
    """
    Calls any LLM using existing gpt_api functions with flexible configuration support.
    """
    # Default config
    if config is None:
        config = {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2500}

    logger.debug(f"🤖 Calling LLM with config: {config}, output_type: {output_type}")

    if from_file:
        with open(prompt_text, encoding="utf-8") as f:
            prompt = f.read()
    else:
        prompt = prompt_text

    prompt = unicodedata.normalize("NFC", prompt)
    logger.debug(f"Prompt length: {len(prompt)} characters")

    # Get the model once
    from llmflow.modules.gpt_api import get_gpt_model
    model_name = config.get("model", "gpt-4o")
    model = get_gpt_model(model_name)

    if output_type == "json":
        # Handle JSON with retry logic
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"JSON attempt {attempt}/{max_retries}")

                # Call LLM directly
                response = _call_model(model, prompt, config)

                # Try to parse JSON
                json_result = parse_llm_json_response(response, fallback_on_error=False)

                if json_result is not None:
                    logger.debug(f"✅ Valid JSON received on attempt {attempt}")
                    return json_result

                if attempt < max_retries:
                    logger.warning(f"⚠️  Invalid JSON on attempt {attempt}, retrying...")
                    time.sleep(retry_backoff)
                else:
                    logger.error(f"❌ No valid JSON found after {max_retries} attempts")
                    raise ValueError(f"Could not extract valid JSON after {max_retries} attempts")

            except Exception as e:
                if attempt >= max_retries:
                    raise
                logger.warning(f"⚠️  Error on JSON attempt {attempt}: {e}")
                time.sleep(retry_backoff)
    else:
        # Regular text with retry logic
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt}/{max_retries}")
                response = _call_model(model, prompt, config)
                logger.debug(f"✅ LLM call successful")
                return response
            except Exception as e:
                if attempt >= max_retries:
                    raise
                logger.warning(f"⚠️  Attempt {attempt} failed: {e}")
                time.sleep(retry_backoff)

def _call_model(model, prompt, config):
    """Internal helper to call the model"""
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
    return response.text()
