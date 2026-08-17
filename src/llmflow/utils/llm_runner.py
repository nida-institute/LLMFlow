from typing import Any, Dict, Optional

import llm

from llmflow.exceptions import ModerationError
from llmflow.modules.json_parser import parse_llm_json_response
from llmflow.modules.llm_response_clean import clean_llm_response_text
from llmflow.modules.logger import Logger

logger = Logger()
MODERATION_GUIDE_PATH = "docs/moderation-handling.md"

# Model cache - simpler than singleton pattern
_model_cache: Dict[str, Any] = {}
def _extract_detail_value(details: Any, attr: str) -> Any:
    if details is None:
        return None
    if isinstance(details, dict):
        return details.get(attr)
    return getattr(details, attr, None)


def _raise_if_moderation_blocked(response: Any, model_name: str, step_name: str) -> None:
    """Inspect a Responses API payload for moderation blocks and raise immediately."""

    status = getattr(response, "status", "") or ""
    details = getattr(response, "incomplete_details", None)
    raw_reason = _extract_detail_value(details, "reason")
    normalized_reason = raw_reason.lower() if isinstance(raw_reason, str) else raw_reason
    explanation = _extract_detail_value(details, "explanation")
    filter_results = _extract_detail_value(details, "content_filter_results")
    status_details = getattr(response, "status_details", None)

    blocked = False

    if status.lower() == "blocked":
        blocked = True
        normalized_reason = normalized_reason or "blocked"
    elif status.lower() == "incomplete" and (normalized_reason in {"content_filter", "safety"}):
        blocked = True
    elif isinstance(normalized_reason, str) and normalized_reason in {"content_filter", "safety"}:
        blocked = True

    if not blocked:
        return

    details_payload = {
        "status": status,
        "reason": raw_reason or normalized_reason,
        "content_filter_results": filter_results,
        "status_details": status_details,
    }
    details_payload = {k: v for k, v in details_payload.items() if v is not None}

    message_parts = [
        f"OpenAI Responses API blocked step '{step_name}' for model {model_name}.",
        f"Reason: {raw_reason or normalized_reason or 'moderation'}.",
    ]

    if explanation:
        message_parts.append(f"Explanation: {explanation}.")
    if filter_results:
        message_parts.append(f"Filter results: {filter_results}.")
    if status_details:
        message_parts.append(f"Status details: {status_details}.")

    message_parts.append(f"See {MODERATION_GUIDE_PATH} for mitigation strategies.")

    # Following the Error Handling guideline: provide actionable tips without raw tracebacks
    raise ModerationError(
        " ".join(message_parts),
        provider="openai",
        model=model_name,
        step_name=step_name,
        reason=raw_reason or normalized_reason,
        explanation=explanation,
        details=details_payload,
    )


def get_model(model_name: str):
    """Get LLM model with caching."""
    if model_name not in _model_cache:
        _model_cache[model_name] = llm.get_model(model_name)
    return _model_cache[model_name]


# ============================================================================
# API key resolution — one path (LLMFlow#195)
# ============================================================================

# provider alias -> environment variable. Declared once; setup_command.PROVIDERS
# carries the same mapping and a test asserts the two agree.
PROVIDER_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def resolve_provider_key(provider: str, explicit: str | None = None) -> str | None:
    """Return the API key for *provider*, or None if none is configured.

    Resolution order (via ``llm.get_key``): explicit argument -> the ``llm`` keystore
    entry for this provider (what ``sp setup`` / ``llm keys set`` writes) -> the
    provider's environment variable.

    Steps that use ``response_format`` talk to the provider's client directly rather than
    through the ``llm`` package. Those call sites used to construct the client with no key,
    so it read the environment variable and nothing else — meaning ``sp setup`` could report
    success and leave every structured-output step unauthenticated. Going through here gives
    both routes one key source; the environment variable still works, it is just no longer
    the only thing that does. See LLMFlow#195.
    """
    env_var = PROVIDER_ENV_VARS.get(provider)
    if env_var is None:
        raise ValueError(
            f"Unknown provider {provider!r}. Known providers: "
            f"{', '.join(sorted(PROVIDER_ENV_VARS))}"
        )
    return llm.get_key(explicit_key=explicit, key_alias=provider, env_var=env_var)


# ============================================================================
# Model Family Detection and Parameter Sets
# ============================================================================

# Model family patterns for detection
MODEL_FAMILIES = {
    "gpt-5": ["gpt-5", "gpt-5.5", "o3-mini", "o3", "o4"],
    "o1": ["o1"],
    "gpt-4": ["gpt-4", "gpt-3.5"],  # ← gpt-3.5 uses same params as gpt-4
    "claude": ["claude-3", "claude-4"],
    "gemini": ["gemini-"],
}

# Family-specific valid parameters
FAMILY_PARAMETERS = {
    "gpt-5": {
        # GPT-5 reasoning models only accept reasoning_effort, no token limits
    },
    "o1": {
        "max_completion_tokens",  # o1 uses Responses API with reasoning.effort
    },
    "gpt-4": {
        "max_tokens",
        "temperature",
        "top_p",
        "top_k",
        "stop",
        "frequency_penalty",
        "presence_penalty",
        "seed",
        "response_format",
    },
    "claude": {
        "max_tokens",
        "temperature",
        "top_p",
        "top_k",
        "stop_sequences",
    },
    "gemini": {
        "maxOutputTokens",
        "temperature",
        "topP",
        "topK",
        "candidateCount",
        "response_mime_type",
        "response_schema",
    },
}


def get_model_family(model_name: str) -> str:
    """Detect model family from model name."""
    for family, patterns in MODEL_FAMILIES.items():
        if any(pattern in model_name for pattern in patterns):
            return family
    return "gpt-4"  # Default to gpt-4 instead of "unknown"


def get_valid_parameters(model_name: str) -> set:
    """Get valid parameters for a specific model."""
    family = get_model_family(model_name)
    return FAMILY_PARAMETERS.get(family, set())


def validate_model_parameter(model_name: str, param_name: str, value: Any) -> list[str]:
    """Validate a parameter for a specific model."""
    errors = []
    valid_params = get_valid_parameters(model_name)

    if param_name not in valid_params:
        # Helpful suggestions for common mistakes
        if param_name == "max_tokens" and "max_completion_tokens" in valid_params:
            errors.append(
                f"Parameter 'max_tokens' is not supported by {model_name}. "
                "Use 'max_completion_tokens' instead."
            )
            return errors
        elif param_name == "max_completion_tokens" and "max_tokens" in valid_params:
            errors.append(
                f"Parameter 'max_completion_tokens' is not supported by {model_name}. "
                "Use 'max_tokens' instead."
            )
            return errors
        elif param_name in PARAMETER_SCHEMAS:
            # Known parameter but not for this model
            errors.append(f"Parameter '{param_name}' is not supported by {model_name}")
            return errors
        # Unknown parameter - pass through (let API validate)
        return []

    # Type and range validation
    if param_name in PARAMETER_SCHEMAS:
        schema = PARAMETER_SCHEMAS[param_name]
        if not isinstance(value, schema["type"]):
            errors.append(f"{param_name} must be of type {schema['type'].__name__}")
            return errors
        if "min" in schema and value < schema["min"]:
            errors.append(f"{param_name} must be >= {schema['min']}")
        if "max" in schema and value > schema["max"]:
            errors.append(f"{param_name} must be <= {schema['max']}")

    return errors


# Generic parameter schema
PARAMETER_SCHEMAS = {
    "temperature": {"type": float, "min": 0, "max": 2},
    "max_tokens": {"type": int, "min": 1},
    "max_completion_tokens": {"type": int, "min": 1},
    "maxOutputTokens": {"type": int, "min": 1},
    "top_p": {"type": float, "min": 0, "max": 1},
    "topP": {"type": float, "min": 0, "max": 1},
    "top_k": {"type": int, "min": 1},
    "topK": {"type": int, "min": 1},
    "frequency_penalty": {"type": float, "min": -2, "max": 2},
    "presence_penalty": {"type": float, "min": -2, "max": 2},
    "timeout_seconds": {"type": int, "min": 1},
    "seed": {"type": int},
    "candidateCount": {"type": int, "min": 1},
    "response_format": {"type": dict},        # ← ADD: OpenAI JSON schema
    "response_schema": {"type": dict},        # ← ADD: Gemini JSON schema
    "response_mime_type": {"type": str},      # ← ADD: Gemini MIME type
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

    # CRITICAL: If response_format is present, use direct OpenAI client
    # The llm package may not pass this parameter through correctly
    if "response_format" in config:
        model_name = config.get("model", "gpt-4o")
        # Only use direct client for OpenAI models
        if any(pattern in model_name for pattern in MODEL_FAMILIES["gpt-4"] + MODEL_FAMILIES["gpt-5"]):
            logger.debug("Using direct OpenAI client for response_format support")
            return _call_openai_with_response_format(prompt, config, output_type)
        else:
            logger.warning(f"⚠️  response_format specified but model {model_name} may not support it")

    # Get model
    model_name = config.get("model", "gpt-4o")
    model = get_model(model_name)

    # Call model
    response = _call_model(model, prompt, config)

    # Handle response type
    if output_type.lower() == "json":
        content = response["content"] if isinstance(response, dict) else response
        parsed = parse_llm_json_response(content)
        if isinstance(response, dict):
            return {"content": parsed, "usage": response.get("usage", {})}
        return parsed
    return response


def _call_model(model, prompt: str, config: Dict[str, Any]) -> dict:
    """Internal helper to call the model."""
    model_name = config.get("model")

    if model_name:
        valid_llm_params = get_valid_parameters(model_name)
    else:
        # Fallback for backward compatibility
        valid_llm_params = {
            "temperature",
            "max_tokens",
            "max_completion_tokens",
            "top_p",
            "top_k",
            "stop",
            "frequency_penalty",
            "presence_penalty",
            "seed",
        }

    options = {
        k: v for k, v in config.items() if k != "model" and k in valid_llm_params
    }
    logger.debug(f"Filtered options for {model_name or 'model'}: {options}")

    response = model.prompt(prompt, **options)
    raw_response = response.text()
    cleaned_response = clean_llm_response_text(raw_response)

    # Capture token usage from the llm package Response object
    try:
        usage_obj = response.usage()
        prompt_tokens = int(usage_obj.input or 0)
        completion_tokens = int(usage_obj.output or 0)
    except Exception:
        prompt_tokens, completion_tokens = 0, 0

    return {
        "content": cleaned_response,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def _load_schema_from_file(schema_file: str) -> dict:
    """Load JSON schema from a file path.

    Args:
        schema_file: Path to JSON schema file (relative to current directory)

    Returns:
        Parsed JSON schema as dict

    Raises:
        FileNotFoundError: If schema file doesn't exist
        json.JSONDecodeError: If schema file is invalid JSON
    """
    import json
    from pathlib import Path

    schema_path = Path(schema_file)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _expand_response_format_schema(response_format: dict) -> dict:
    """Expand response_format config by loading schema from file if schema_file is present.

    Args:
        response_format: The response_format config dict (may be modified)

    Returns:
        Expanded response_format dict with schema loaded from file
    """
    # Make a copy to avoid modifying the original
    expanded = response_format.copy()

    # Check if json_schema.schema_file is present
    if "json_schema" in expanded:
        json_schema = expanded["json_schema"]
        if isinstance(json_schema, dict) and "schema_file" in json_schema:
            schema_file = json_schema["schema_file"]
            logger.debug(f"📄 Loading schema from file: {schema_file}")

            # Load schema from file
            schema = _load_schema_from_file(schema_file)

            # Replace schema_file with loaded schema
            json_schema = json_schema.copy()
            del json_schema["schema_file"]
            json_schema["schema"] = schema
            expanded["json_schema"] = json_schema

            logger.debug(f"✅ Schema loaded: {len(str(schema))} chars")

    return expanded


def _call_openai_with_response_format(prompt: str, config: Dict[str, Any], output_type: str = "text") -> dict:
    """Call OpenAI API directly when response_format is specified.

    The llm package may not pass response_format through correctly,
    so we use the OpenAI client directly to ensure structured outputs work.

    Supports both inline schemas and file-based schemas via schema_file.
    """
    from openai import OpenAI

    # One key source for both routes — keystore or env var (LLMFlow#195)
    client = OpenAI(api_key=resolve_provider_key("openai"))

    model_name = config.get("model", "gpt-4o-2024-08-06")

    # Build API parameters
    api_params = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
    }

    # Add temperature (default 0.7)
    api_params["temperature"] = config.get("temperature", 0.7)

    # Add token limit
    if "max_completion_tokens" in config:
        api_params["max_completion_tokens"] = config["max_completion_tokens"]
    elif "max_tokens" in config:
        api_params["max_tokens"] = config["max_tokens"]

    # Add other OpenAI-specific parameters
    for param in ["top_p", "frequency_penalty", "presence_penalty", "seed", "stop"]:
        if param in config:
            api_params[param] = config[param]

    # CRITICAL: Add response_format (expand schema_file if present)
    if "response_format" in config:
        response_format = _expand_response_format_schema(config["response_format"])
        api_params["response_format"] = response_format
        logger.debug(f"Using response_format: {response_format.get('type', 'unknown')}")

    # Call OpenAI API
    try:
        response = client.chat.completions.create(**api_params)
    except Exception as e:
        logger.error(f"❌ OpenAI API call failed: {e}")
        raise

    # Extract content
    content = response.choices[0].message.content or ""

    # Get token usage
    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        "total_tokens": response.usage.total_tokens if response.usage else 0,
    }

    # Parse JSON if requested
    if output_type.lower() == "json":
        try:
            parsed_content = parse_llm_json_response(content)
            return {"content": parsed_content, "usage": usage}
        except Exception as e:
            logger.error(f"❌ JSON parsing failed even with response_format: {e}")
            logger.error(f"   Content: {content[:500]}")
            raise

    return {"content": content, "usage": usage}


# ============================================================================
# MCP Tool Calling Support
# ============================================================================

def run_llm_with_mcp_tools(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text",
    step_name: str = "unknown",
    step: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    pipeline_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute LLM call with MCP tool support."""
    import asyncio
    return asyncio.run(_run_llm_with_mcp_tools_async(
        prompt, config, mcp_client, output_type, step_name, step, context, pipeline_config
    ))


async def _run_llm_with_mcp_tools_async(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text",
    step_name: str = "unknown",
    step: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    pipeline_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute LLM with MCP tools using OpenAI API.

    Routes to Responses API for GPT-5/o1 (better reasoning),
    or Chat Completions API for other models.
    """
    model_name = config.get("model", "gpt-4o")
    model_family = get_model_family(model_name)

    # Use Responses API for reasoning models (GPT-5, o1)
    if model_family in ("gpt-5", "o1"):
        return await _run_with_responses_api(
            prompt, config, mcp_client, output_type, step_name
        )
    else:
        return await _run_with_chat_completions(
            prompt, config, mcp_client, output_type, step_name
        )


async def _run_with_responses_api(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text",
    step_name: str = "unknown",
    step: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    pipeline_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute LLM using Responses API (for GPT-5, O1)."""
    from llmflow.runner import save_content_to_file
    import json
    from openai import OpenAI
    import asyncio
    from functools import partial

    # Responses API is only available in sync client, so we'll use it in a thread pool
    client = OpenAI(api_key=resolve_provider_key("openai"))

    # Initialize MCP session and get tools
    async with mcp_client as mcp:
        tools = await mcp._async_get_tool_definitions()

        if not tools:
            logger.warning("⚠️  No MCP tools available, falling back to simple call")
            return call_llm(prompt, config=config, output_type=output_type)

        # Convert MCP schema to Responses API tool format (flatter than Chat Completions)
        openai_tools = [
            {
                "type": "function",
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {})
            }
            for tool in tools
        ]

        logger.debug(f"🛠️  {len(openai_tools)} MCP tools available")
        logger.debug(f"   Tools: {[t['name'] for t in openai_tools]}")

        model_name = config.get("model", "gpt-5")

        # Build Responses API request
        api_params = {
            "model": model_name,
            "input": [{"role": "user", "content": prompt}],
            "tools": openai_tools,
            "reasoning": {
                "effort": config.get("reasoning_effort", "medium")
            }
        }

        # Add max_output_tokens if specified
        if "max_completion_tokens" in config:
            api_params["max_output_tokens"] = config["max_completion_tokens"]
        elif "max_tokens" in config:
            api_params["max_output_tokens"] = config["max_tokens"]

        mcp_config = config.get("mcp", {})
        max_iterations = mcp_config.get("max_iterations", 1)
        max_tool_response_size = mcp_config.get("max_tool_response_size", 100000)
        timeout_seconds = config.get("timeout_seconds", 60)

        if max_iterations == 1 and len(tools) > 1:
            logger.warning(
                f"⚠️  Step '{step_name}' has {len(tools)} tools but max_iterations=1. "
                f"Set 'mcp.max_iterations' explicitly if multi-step reasoning needed."
            )

        # Track cumulative token usage across all iterations
        # Note: Responses API doesn't expose usage data yet, so we track what we can
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0

        for iteration in range(max_iterations):
            logger.debug(f"🔄 MCP iteration {iteration + 1}/{max_iterations}")
            logger.info(f"📤 API params: model={api_params['model']}, tools={len(api_params.get('tools', []))}, input_messages={len(api_params.get('input', []))}")

            try:
                response = await asyncio.to_thread(
                    client.responses.create,
                    **api_params,
                    timeout=timeout_seconds
                )

                # Debug: save the provider's raw reply alongside the step's parsed response.
                #
                # This used to write to a hardcoded "outputs/debug/{filename}", ignoring
                # both intermediate_file_directory and the per-pipeline subdirectory, so it
                # landed outside the run's own audit trail entirely (LLMFlow#198). It is
                # supplementary evidence for a call the step handler already recorded, so
                # it takes no sequence number and no manifest line of its own.
                try:
                    recorder = (pipeline_config or {}).get("_debug_recorder")
                    if recorder is not None and step:
                        saved = recorder.save_artifact(
                            f"{step.get('name', 'llm_step')}-raw-response", response
                        )
                        if saved:
                            logger.debug(f"🗒️ Saved raw response to {saved}")
                except Exception as e:
                    logger.debug(f"(response debug save skipped: {e})")

            except Exception as e:
                logger.error(f"❌ OpenAI Responses API call failed: {e}")
                raise

            _raise_if_moderation_blocked(response, model_name, step_name)

            # Track token usage if available (Responses API may not expose this yet)
            if hasattr(response, 'usage') and response.usage:
                total_prompt_tokens += getattr(response.usage, 'prompt_tokens', 0) or 0
                total_completion_tokens += getattr(response.usage, 'completion_tokens', 0) or 0
                total_tokens += getattr(response.usage, 'total_tokens', 0) or 0

            # Debug: Log response structure
            logger.debug(f"📊 Response status: {response.status}")
            logger.debug(f"📊 Response output items: {len(response.output)}")
            for i, item in enumerate(response.output):
                logger.debug(f"📊 Output item {i}: type={getattr(item, 'type', 'NO TYPE')}, hasattr text={hasattr(item, 'text')}")
                if hasattr(item, '__dict__'):
                    logger.debug(f"📊 Output item {i} attributes: {list(item.__dict__.keys())}")

            # Check response status
            if response.status == "completed":
                # Check if there are function calls to handle
                has_function_calls = any(
                    hasattr(item, 'type') and item.type == "function_call"
                    for item in response.output
                )

                if not has_function_calls:
                    # No function calls, extract final text output
                    output_text = ""
                    for item in response.output:
                        if hasattr(item, 'type'):
                            # Handle both 'text' and 'message' types
                            if item.type == "text" and hasattr(item, 'text'):
                                output_text += item.text
                            elif item.type == "message" and hasattr(item, 'content'):
                                # After tool execution, GPT-5 returns 'message' type with 'content'
                                # content is ALWAYS an array of ResponseOutputText objects
                                if isinstance(item.content, list):
                                    for content_item in item.content:
                                        text = getattr(content_item, 'text', None)
                                        if text is not None:
                                            output_text += text
                                else:
                                    # Fallback for unexpected structure
                                    output_text += str(item.content)

                    logger.debug(f"✅ LLM completed without requesting tools. Output length: {len(output_text)}")

                    # Parse JSON if requested
                    if output_type.lower() == "json":
                        output_text = parse_llm_json_response(output_text)

                    # Return content with token usage
                    return {
                        "content": output_text,
                        "usage": {
                            "prompt_tokens": total_prompt_tokens,
                            "completion_tokens": total_completion_tokens,
                            "total_tokens": total_tokens
                        }
                    }

                # Has function calls - fall through to handle them
                logger.debug(f"🛠️  LLM requesting tool calls")

            # Check for tool calls (even if status is not "completed")
            tool_calls_found = False
            for item in response.output:
                if hasattr(item, 'type') and item.type == "function_call":
                    tool_calls_found = True
                    break

            if not tool_calls_found:
                # No tool calls and already handled completed status above
                logger.warning(f"⚠️  Unexpected response status: {response.status}")
                output_text = ""
                for item in response.output:
                    if hasattr(item, 'type'):
                        if item.type == "text" and hasattr(item, 'text'):
                            output_text += item.text
                        elif item.type == "message" and hasattr(item, 'content'):
                            # content is ALWAYS an array of ResponseOutputText objects
                            if isinstance(item.content, list):
                                for content_item in item.content:
                                    text = getattr(content_item, 'text', None)
                                    if text is not None:
                                        output_text += text
                            else:
                                output_text += str(item.content)

                # Return with usage data
                return {
                    "content": output_text or "Error: Unexpected response format",
                    "usage": {
                        "prompt_tokens": total_prompt_tokens,
                        "completion_tokens": total_completion_tokens,
                        "total_tokens": total_tokens
                    }
                }

            # Execute tool calls and add results to input
            logger.debug(f"🛠️  LLM requesting tool calls")

            new_input_items = list(api_params["input"])  # Copy existing input

            # First, add all response output items (includes function_call items)
            for item in response.output:
                if hasattr(item, 'type'):
                    # Convert the response item to dict for input
                    if item.type in ["reasoning", "function_call"]:
                        # Add these items to the conversation history
                        item_dict = {
                            "type": item.type,
                            "id": item.id,
                        }
                        if item.type == "function_call":
                            item_dict["call_id"] = item.call_id
                            item_dict["name"] = item.name
                            item_dict["arguments"] = item.arguments
                        elif item.type == "reasoning":
                            # summary is REQUIRED by API and must be an array
                            summary = getattr(item, 'summary', None)
                            if summary is None or not isinstance(summary, list):
                                summary = []
                            item_dict["summary"] = summary

                            content = getattr(item, 'content', None)
                            if content:
                                item_dict["content"] = content
                        new_input_items.append(item_dict)

            # Now execute tool calls and add their outputs
            for item in response.output:
                if hasattr(item, 'type'):
                    if item.type == "function_call":
                        tool_name = item.name
                        tool_args = json.loads(item.arguments) if isinstance(item.arguments, str) else item.arguments

                        logger.info(f"   🔧 {tool_name}")
                        logger.debug(f"      Args: {tool_args}")

                        try:
                            result = await mcp._async_call_tool(tool_name, tool_args)
                            result_str = str(result)

                            # Truncate if needed
                            if len(result_str) > max_tool_response_size:
                                truncated_chars = len(result_str) - max_tool_response_size
                                result_str = result_str[:max_tool_response_size] + f"\n\n[...truncated {truncated_chars:,} characters]"
                                logger.warning(f"      ⚠️  Tool response truncated from {len(str(result)):,} to {len(result_str):,} chars")
                            else:
                                logger.debug(f"      ℹ️  Tool response size: {len(result_str):,} chars (within {max_tool_response_size:,} limit)")

                            result_preview = result_str[:200] + "..." if len(result_str) > 200 else result_str
                            logger.debug(f"      ✅ Result: {result_preview}")

                            # Add function call result to input
                            new_input_items.append({
                                "type": "function_call_output",
                                "call_id": item.call_id,
                                "output": result_str
                            })
                        except Exception as e:
                            logger.error(f"      ❌ Tool execution failed: {e}")
                            new_input_items.append({
                                "type": "function_call_output",
                                "call_id": item.call_id,
                                "output": f"Error: {e}"
                            })

            # Update input for next iteration
            api_params["input"] = new_input_items

        # Max iterations reached
        logger.warning(f"⚠️  Max MCP iterations ({max_iterations}) reached")
        return {
            "content": "Error: Maximum tool calling iterations exceeded",
            "usage": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens
            }
        }


async def _run_with_chat_completions(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text",
    step_name: str = "unknown"
) -> Dict[str, Any]:
    """Execute LLM using Chat Completions API (for GPT-4, GPT-3.5)."""
    import json
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=resolve_provider_key("openai"))

    # Initialize MCP session and get tools
    async with mcp_client as mcp:
        tools = await mcp._async_get_tool_definitions()

        if not tools:
            logger.warning("⚠️  No MCP tools available, falling back to simple call")
            return call_llm(prompt, config=config, output_type=output_type)

        # Convert MCP schema to OpenAI function calling format
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {})
                }
            }
            for tool in tools
        ]

        logger.debug(f"🛠️  {len(openai_tools)} MCP tools available")
        logger.debug(f"   Tools: {[t['function']['name'] for t in openai_tools]}")

        # Build initial messages
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]

        # Build API call parameters with model-aware defaults
        model_name = config.get("model", "gpt-4o")

        api_params = {
            "model": model_name,
            "messages": messages,
            "tools": openai_tools,
        }

        # Add temperature (all models in Chat Completions support it)
        api_params["temperature"] = config.get("temperature", 0.7)

        # Add token limit parameter based on what's in config (don't pass None)
        if "max_completion_tokens" in config:
            api_params["max_completion_tokens"] = config["max_completion_tokens"]
        elif "max_tokens" in config:
            api_params["max_tokens"] = config["max_tokens"]

        # Add response_format if specified
        if "response_format" in config:
            api_params["response_format"] = config["response_format"]

        mcp_config = config.get("mcp", {})
        max_iterations = mcp_config.get("max_iterations", 1)  # Default to 1
        max_tool_response_size = mcp_config.get("max_tool_response_size", 100000)

        if max_iterations == 1 and len(tools) > 1:
            logger.warning(
                f"⚠️  Step '{step_name}' has {len(tools)} tools but max_iterations=1. "
                f"Set 'mcp.max_iterations' explicitly if multi-step reasoning needed."
            )
        elif "max_iterations" not in mcp_config:
            logger.debug(f"Using default max_iterations=1 for step '{step_name}'")

        # Track cumulative token usage across all iterations
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0

        message = None
        for iteration in range(max_iterations):
            logger.debug(f"🔄 MCP iteration {iteration + 1}/{max_iterations}")

            try:
                response = await client.chat.completions.create(**api_params)
            except Exception as e:
                logger.error(f"❌ OpenAI API call failed: {e}")
                raise

            # Accumulate token usage from this iteration
            if hasattr(response, 'usage') and response.usage:
                total_prompt_tokens += response.usage.prompt_tokens or 0
                total_completion_tokens += response.usage.completion_tokens or 0
                total_tokens += response.usage.total_tokens or 0

            message = response.choices[0].message

            # Check if LLM is done (no tool calls)
            if not message.tool_calls:
                logger.debug("✅ LLM completed without requesting tools")
                final_content = message.content or ""

                # Parse JSON if requested
                if output_type.lower() == "json":
                    final_content = parse_llm_json_response(final_content)

                # Return content with token usage
                return {
                    "content": final_content,
                    "usage": {
                        "prompt_tokens": total_prompt_tokens,
                        "completion_tokens": total_completion_tokens,
                        "total_tokens": total_tokens
                    }
                }

            # Log how many tool calls were requested
            logger.debug(f"🛠️  LLM requesting {len(message.tool_calls)} tool call(s)")

            # Build messages to send back to LLM
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # INFO log: Show tool name and key arguments on one line
                if "usfm_references" in tool_args:
                    refs = tool_args["usfm_references"]
                    ref_count = len(refs)
                    # Show first few references
                    preview_refs = refs[:5]
                    ref_preview = ", ".join(preview_refs)
                    if ref_count > 5:
                        ref_preview += f", ... ({ref_count} total)"
                    logger.info(f"   🔧 {tool_name}: {ref_preview}")
                else:
                    # Fallback for other tool types
                    logger.info(f"   🔧 {tool_name}")

                logger.debug(f"      Full args: {tool_args}")

                try:
                    # Parse arguments
                    args = json.loads(tool_call.function.arguments)
                    logger.debug(f"      Args: {args}")

                    # Call MCP server (async!)
                    result = await mcp._async_call_tool(tool_name, args)
                    result_str = str(result)

                    # Truncate if needed
                    if len(result_str) > max_tool_response_size:
                        truncated_chars = len(result_str) - max_tool_response_size
                        result_str = result_str[:max_tool_response_size] + f"\n\n[...truncated {truncated_chars:,} characters]"
                        logger.warning(f"      ⚠️  Tool response truncated from {len(str(result)):,} to {len(result_str):,} chars")
                    else:
                        logger.debug(f"      ℹ️  Tool response size: {len(result_str):,} chars (within {max_tool_response_size:,} limit)")

                    result_preview = result_str[:200] + "..." if len(result_str) > 200 else result_str
                    logger.debug(f"      ✅ Result: {result_preview}")

                except json.JSONDecodeError as e:
                    logger.error(f"      ❌ Invalid JSON arguments: {e}")
                    result_str = f"Error: Invalid arguments format - {e}"
                except Exception as e:
                    logger.error(f"      ❌ Tool execution failed: {e}")
                    result_str = f"Error: {e}"

                # Add tool result to message history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result_str
                })

        # If we hit max iterations without finishing
        logger.debug(f"⚠️  Max MCP iterations ({max_iterations}) reached")
        final_content = message.content if message is not None else "" or "Error: Maximum tool calling iterations exceeded"

        # Parse JSON if requested
        if output_type.lower() == "json":
            final_content = parse_llm_json_response(final_content)

        # Return content with token usage (even on max iterations)
        return {
            "content": final_content,
            "usage": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens
            }
        }
