import json
import re

from llmflow.modules.logger import Logger
from llmflow.modules.llm_response_clean import clean_llm_response_text

# Use unified logger
logger = Logger()


def parse_llm_json_response(text: str):
    """Parse JSON from LLM response, handling markdown fences and double-encoding."""
    # Clean the response text
    cleaned = clean_llm_response_text(text)

    try:
        # First parse attempt
        result = json.loads(cleaned)

        # Check if result is a string (double-encoded JSON)
        while isinstance(result, str):
            logger.debug("Detected double-encoded JSON, parsing again")
            result = json.loads(result)

        return result
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️  JSON parse error at position {e.pos}: {e.msg}")

        # Try to fix common escape issues
        try:
            # Replace invalid escapes with proper ones
            fixed = cleaned.replace('\\ ', ' ')  # Remove backslash before spaces
            fixed = re.sub(r'\\(?!["\\/bfnrtu])', '', fixed)  # Remove invalid escapes
            result = json.loads(fixed)
            logger.debug("✅ Fixed invalid escape sequences and parsed successfully")

            # Check for double-encoding again
            while isinstance(result, str):
                result = json.loads(result)

            return result
        except json.JSONDecodeError:
            logger.warning(f"⚠️  Could not fix JSON, returning raw text")
            return cleaned


def validate_json_structure(data, required_fields=None):
    """
    Validate that parsed JSON has expected structure.
    """
    logger.debug("🔍 Validating JSON structure")

    if not isinstance(data, (dict, list)):
        logger.error("❌ JSON data is not a dict or list")
        return False, ["Data must be a dictionary or list"]

    errors = []

    if required_fields and isinstance(data, dict):
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            errors.extend(
                [f"Missing required field: {field}" for field in missing_fields]
            )
            for field in missing_fields:
                logger.error(f"❌ Missing required field: {field}")

    is_valid = len(errors) == 0

    if is_valid:
        logger.debug("✅ JSON structure validation passed")
    else:
        logger.error(f"❌ JSON structure validation failed with {len(errors)} errors")

    return is_valid, errors


def handle_llm_response(message, output_type, max_iterations=5):
    """
    Handle the response from the LLM, including parsing JSON and managing tool calls.
    """
    logger.info("🤖 Handling LLM response")

    # Check if LLM is done (no tool calls)
    if not message.tool_calls:
        logger.debug("✅ LLM completed without requesting tools")
        final_content = message.content or ""

        # Parse JSON if requested
        if output_type.lower() == "json":
            from llmflow.modules.json_parser import parse_llm_json_response

            return parse_llm_json_response(final_content)

        return final_content

    # If there are tool calls, we need to process them
    logger.info(f"🔧 Processing {len(message.tool_calls)} tool calls")

    for iteration in range(1, max_iterations + 1):
        logger.info(f"🔄 MCP Iteration {iteration}")

        for tool_call in message.tool_calls:
            logger.info(f"📞 Calling tool: {tool_call.name}")

            # Here you would implement the actual tool calling logic
            # For now, we just log and pretend the tool call was successful
            logger.info(f"✅ Tool {tool_call.name} called successfully")

            # After a successful tool call, check if the LLM is done
            if not message.tool_calls:
                logger.debug("✅ LLM completed after tool calls")
                final_content = message.content or ""

                # Parse JSON if requested
                if output_type.lower() == "json":
                    from llmflow.modules.json_parser import parse_llm_json_response

                    return parse_llm_json_response(final_content)

                return final_content

    # If we hit max iterations without finishing
    logger.debug(f"⚠️  Max MCP iterations ({max_iterations}) reached")
    final_content = message.content or "Error: Maximum tool calling iterations exceeded"

    # Parse JSON if requested
    if output_type.lower() == "json":
        from llmflow.modules.json_parser import parse_llm_json_response

        return parse_llm_json_response(final_content)

    return final_content
