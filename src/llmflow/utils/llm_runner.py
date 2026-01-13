from typing import Any, Dict

import llm

from llmflow.modules.json_parser import parse_llm_json_response
from llmflow.modules.llm_response_clean import clean_llm_response_text
from llmflow.modules.logger import Logger

logger = Logger()

# Model cache - simpler than singleton pattern
_model_cache: Dict[str, Any] = {}


def get_model(model_name: str):
    """Get LLM model with caching."""
    if model_name not in _model_cache:
        _model_cache[model_name] = llm.get_model(model_name)
    return _model_cache[model_name]


# ============================================================================
# Model Family Detection and Parameter Sets
# ============================================================================

# Model family patterns for detection
MODEL_FAMILIES = {
    "gpt-5": ["gpt-5", "o3-mini", "o3", "o4"],
    "o1": ["o1"],
    "gpt-4": ["gpt-4", "gpt-3.5"],  # ← gpt-3.5 uses same params as gpt-4
    "claude": ["claude-3", "claude-4"],
    "gemini": ["gemini-"],
}

# Family-specific valid parameters
FAMILY_PARAMETERS = {
    "gpt-5": {
        "max_completion_tokens",  # GPT-5 uses Responses API with reasoning.effort
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
    return cleaned_response


# ============================================================================
# MCP Tool Calling Support
# ============================================================================

def run_llm_with_mcp_tools(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text",
    step_name: str = "unknown"  # ← Add parameter
) -> str:
    """Execute LLM call with MCP tool support."""
    import asyncio
    return asyncio.run(_run_llm_with_mcp_tools_async(
        prompt, config, mcp_client, output_type, step_name  # ← Pass through
    ))


async def _run_llm_with_mcp_tools_async(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text",
    step_name: str = "unknown"
) -> str:
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
    step_name: str = "unknown"
) -> str:
    """Execute LLM using Responses API (for GPT-5, o1)."""
    import json
    from openai import AsyncOpenAI

    client = AsyncOpenAI()

    # Initialize MCP session and get tools
    async with mcp_client as mcp:
        tools = await mcp._async_get_tool_definitions()

        if not tools:
            logger.warning("⚠️  No MCP tools available, falling back to simple call")
            return call_llm(prompt, config=config, output_type=output_type)

        # Convert MCP schema to OpenAI tool format
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

        if max_iterations == 1 and len(tools) > 1:
            logger.warning(
                f"⚠️  Step '{step_name}' has {len(tools)} tools but max_iterations=1. "
                f"Set 'mcp.max_iterations' explicitly if multi-step reasoning needed."
            )

        for iteration in range(max_iterations):
            logger.debug(f"🔄 MCP iteration {iteration + 1}/{max_iterations}")

            try:
                response = await client.responses.create(**api_params)
            except Exception as e:
                logger.error(f"❌ OpenAI Responses API call failed: {e}")
                raise

            # Check response status
            if response.status == "completed":
                # Extract output text from response
                output_text = ""
                for item in response.output:
                    if hasattr(item, 'type') and item.type == "message":
                        for content in item.content:
                            if hasattr(content, 'type') and content.type == "output_text":
                                output_text += content.text

                logger.debug("✅ LLM completed without requesting tools")

                if output_type.lower() == "json":
                    return parse_llm_json_response(output_text)
                return output_text

            # Check for tool calls
            tool_calls_found = False
            for item in response.output:
                if hasattr(item, 'type') and item.type == "function_call":
                    tool_calls_found = True
                    break

            if not tool_calls_found:
                # No tool calls but also not completed - shouldn't happen
                logger.warning(f"⚠️  Unexpected response status: {response.status}")
                output_text = ""
                for item in response.output:
                    if hasattr(item, 'type') and item.type == "message":
                        for content in item.content:
                            if hasattr(content, 'type') and content.type == "output_text":
                                output_text += content.text
                return output_text or "Error: Unexpected response format"

            # Execute tool calls and add results to input
            logger.debug(f"🛠️  LLM requesting tool calls")

            new_input_items = list(api_params["input"])  # Copy existing input

            for item in response.output:
                if hasattr(item, 'type'):
                    if item.type == "function_call":
                        tool_name = item.name
                        tool_args = json.loads(item.arguments) if isinstance(item.arguments, str) else item.arguments

                        logger.info(f"   🔧 {tool_name}")
                        logger.debug(f"      Args: {tool_args}")

                        try:
                            result = await mcp._async_call_tool(tool_name, tool_args)
                            result_preview = result[:200] + "..." if len(result) > 200 else result
                            logger.debug(f"      ✅ Result: {result_preview}")

                            # Add function call result to input
                            new_input_items.append({
                                "type": "function_call_output",
                                "call_id": item.id,
                                "name": tool_name,
                                "content": str(result)
                            })
                        except Exception as e:
                            logger.error(f"      ❌ Tool execution failed: {e}")
                            new_input_items.append({
                                "type": "function_call_output",
                                "call_id": item.id,
                                "name": tool_name,
                                "content": f"Error: {e}"
                            })

            # Update input for next iteration
            api_params["input"] = new_input_items

        # Max iterations reached
        logger.warning(f"⚠️  Max MCP iterations ({max_iterations}) reached")
        return "Error: Maximum tool calling iterations exceeded"


async def _run_with_chat_completions(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text",
    step_name: str = "unknown"
) -> str:
    """Execute LLM using Chat Completions API (for GPT-4, GPT-3.5)."""
    import json
    from openai import AsyncOpenAI

    client = AsyncOpenAI()

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
        messages = [{"role": "user", "content": prompt}]

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

        if max_iterations == 1 and len(tools) > 1:
            logger.warning(
                f"⚠️  Step '{step_name}' has {len(tools)} tools but max_iterations=1. "
                f"Set 'mcp.max_iterations' explicitly if multi-step reasoning needed."
            )
        elif "max_iterations" not in mcp_config:
            logger.debug(f"Using default max_iterations=1 for step '{step_name}'")

        for iteration in range(max_iterations):
            logger.debug(f"🔄 MCP iteration {iteration + 1}/{max_iterations}")

            try:
                response = await client.chat.completions.create(**api_params)
            except Exception as e:
                logger.error(f"❌ OpenAI API call failed: {e}")
                raise

            message = response.choices[0].message

            # Check if LLM is done (no tool calls)
            if not message.tool_calls:
                logger.debug("✅ LLM completed without requesting tools")
                final_content = message.content or ""

                # Parse JSON if requested
                if output_type.lower() == "json":
                    return parse_llm_json_response(final_content)

                return final_content

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
                    result_preview = result[:200] + "..." if len(result) > 200 else result
                    logger.debug(f"      ✅ Result: {result_preview}")

                except json.JSONDecodeError as e:
                    logger.error(f"      ❌ Invalid JSON arguments: {e}")
                    result = f"Error: Invalid arguments format - {e}"
                except Exception as e:
                    logger.error(f"      ❌ Tool execution failed: {e}")
                    result = f"Error: {e}"

                # Add tool result to message history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(result)
                })

        # If we hit max iterations without finishing
        logger.debug(f"⚠️  Max MCP iterations ({max_iterations}) reached")
        final_content = message.content or "Error: Maximum tool calling iterations exceeded"

        # Parse JSON if requested
        if output_type.lower() == "json":
            return parse_llm_json_response(final_content)

        return final_content
