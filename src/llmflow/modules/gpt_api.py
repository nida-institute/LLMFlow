import json
import re
import typer
import llm
from llmflow.modules.json_parser import parse_llm_json_response
from llmflow.modules.logging import log_section
from llmflow.utils.io import normalize_nfc
from llmflow.modules.llm_response_clean import clean_llm_response_text

# --- Singleton Model Holder ---
_model_singleton = {}

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

def call_gpt_with_retry(config, prompt, max_attempts=3):
    import httpx
    import logging
    logger = logging.getLogger('llmflow.gpt')

    model_obj = get_gpt_model(config["model"])

    for attempt in range(max_attempts):
        try:
            prompt_kwargs = {}

            for key, value in config.items():
                # Only send max_tokens for models that support it
                if key == "max_tokens":
                    if "gpt-5" in config["model"]:
                        # Do NOT send max_completion_tokens unless you confirm it's supported
                        continue  # Skip sending any token parameter for GPT-5
                    else:
                        prompt_kwargs["max_tokens"] = value
                elif key != "model":
                    prompt_kwargs[key] = value

            # Log what we're actually sending
            logger.debug(f"Sending parameters: {prompt_kwargs}")
            logger.debug(f"Model: {config['model']}")

            response = model_obj.prompt(prompt, **prompt_kwargs)

            if hasattr(response, "text"):
                response_text = clean_llm_response_text(response.text())
            else:
                response_text = clean_llm_response_text(str(response))
            return response_text
        except httpx.RemoteProtocolError as e:
            logger.warning(f"RemoteProtocolError (attempt {attempt + 1}): {e}")
        except httpx.RequestError as e:
            logger.warning(f"HTTP request error (attempt {attempt + 1}): {e}")
        except Exception as e:
            logger.warning(f"GPT call failed due to an unexpected error (attempt {attempt + 1}): {e}")

    logger.error("GPT call failed after maximum retries.")
    raise Exception("GPT call failed after maximum retries")

def call_gpt_get_json(config, prompt, retries):
    """
    Calls GPT model with the given prompt and parses the JSON response.
    Handles retries and structure verification. If the input is empty, returns an empty list.
    """
    for attempt in range(retries):
        try:
            response = call_gpt_with_retry(config, prompt, max_attempts=1)
            response_text = clean_llm_response_text(response if isinstance(response, str) else response.text())

            if not response_text:
                typer.secho(f"🔄 Received empty or invalid response from GPT (attempt {attempt + 1}/{retries}). Retrying this chunk.", fg=typer.colors.YELLOW)
                continue

            try:
                parsed_response = parse_llm_json_response(response_text)
                log_section("Parsed GPT Response", json.dumps(parsed_response, ensure_ascii=False, indent=2), False)
                return parsed_response

            except (json.JSONDecodeError, ValueError) as e:
                typer.secho(f"🔄 JSON parsing failed (attempt {attempt + 1}/{retries}): {e}", fg=typer.colors.YELLOW)
                continue

        except Exception as e:
            typer.secho(f"🔄 GPT call failed (attempt {attempt + 1}/{retries}): {e}", fg=typer.colors.YELLOW)
            continue

    typer.secho(f"❌ Failed to generate valid response after {retries} attempts.", fg=typer.colors.RED)
    return []
