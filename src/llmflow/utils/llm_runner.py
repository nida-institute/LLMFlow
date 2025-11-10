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
        "temperature",
        "max_tokens",
        "top_p",
        "top_k",
        "stop",
        "frequency_penalty",
        "presence_penalty",
        "seed",
    }

    # Filter config to only include valid parameters
    options = {
        k: v for k, v in config.items() if k != "model" and k in valid_llm_params
    }

    logger.debug(f"Filtered options for model: {options}")

    response = model.prompt(prompt, **options)
    raw_response = response.text()

    # Clean the response to remove outer markdown fences BEFORE any processing
    cleaned_response = clean_llm_response_text(raw_response)

    return cleaned_response


# ============================================================================
# MCP Tool Calling Support
# ============================================================================

def run_llm_with_mcp_tools(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text"
) -> str:
    """
    Execute LLM call with MCP tool support.
    This is a sync wrapper around the async implementation.
    """
    import asyncio
    return asyncio.run(_run_llm_with_mcp_tools_async(prompt, config, mcp_client, output_type))


async def _run_llm_with_mcp_tools_async(
    prompt: str,
    config: Dict[str, Any],
    mcp_client,
    output_type: str = "text"
) -> str:
    """
    Execute LLM with MCP tools using OpenAI API.

    Handles iterative tool calling:
    1. Send prompt to LLM
    2. If LLM requests tools, execute them via MCP
    3. Send results back to LLM
    4. Repeat until LLM gives final answer
    """
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

        logger.info(f"🛠️  {len(openai_tools)} MCP tools available")
        logger.debug(f"   Tools: {[t['function']['name'] for t in openai_tools]}")

        # Build initial messages
        messages = [{"role": "user", "content": prompt}]

        # Iterative tool calling loop
        max_iterations = 10
        for iteration in range(max_iterations):
            logger.debug(f"🔄 MCP iteration {iteration + 1}/{max_iterations}")

            try:
                response = await client.chat.completions.create(
                    model=config.get("model", "gpt-4o"),
                    messages=messages,
                    tools=openai_tools,
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens"),
                )
            except Exception as e:
                logger.error(f"❌ OpenAI API call failed: {e}")
                raise

            message = response.choices[0].message

            # Check if LLM is done (no tool calls)
            if not message.tool_calls:
                logger.info(f"✅ MCP conversation complete after {iteration + 1} iteration(s)")
                final_response = message.content or ""

                # Handle output type
                if output_type.lower() == "json":
                    return parse_llm_json_response(final_response)
                return final_response

            # LLM wants to call tools - add its message to history
            logger.info(f"🛠️  LLM requesting {len(message.tool_calls)} tool call(s)")
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

            # Execute each tool call via MCP
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                logger.info(f"   🔧 Executing: {tool_name}")

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
        logger.warning(f"⚠️  Max MCP iterations ({max_iterations}) reached")
        return message.content or "Error: Maximum tool calling iterations exceeded"
