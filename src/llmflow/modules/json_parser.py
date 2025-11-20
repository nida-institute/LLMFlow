import json
import re

from llmflow.modules.logger import Logger

# Use unified logger
logger = Logger()


def parse_llm_json_response(response_text, fallback_on_error=True):
    """
    Parse JSON from LLM response with error handling and logging.
    """
    logger.debug(f"🔍 Parsing JSON response ({len(response_text)} chars)")

    try:
        # First, try to parse the entire response as JSON
        try:
            result = json.loads(response_text.strip())
            logger.debug("✅ Successfully parsed entire response as JSON")
            return result
        except json.JSONDecodeError:
            pass

        # Look for JSON in code blocks
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        code_blocks = re.findall(code_block_pattern, response_text, re.IGNORECASE)

        for i, block in enumerate(code_blocks):
            try:
                result = json.loads(block.strip())
                logger.debug(f"✅ Successfully parsed JSON from code block {i+1}")
                return result
            except json.JSONDecodeError:
                logger.debug(f"Failed to parse code block {i+1} as JSON")
                continue

        # Look for JSON-like structures without code blocks
        # FIX: Use GREEDY matching to capture the full JSON structure
        # Try to find the largest valid JSON object or array
        json_pattern = r"(\{[\s\S]*\}|\[[\s\S]*\])"  # ← Changed from *? to * (greedy)
        potential_json = re.findall(json_pattern, response_text)

        # Sort by length descending - try longest matches first
        potential_json = sorted(potential_json, key=len, reverse=True)

        for i, candidate in enumerate(potential_json):
            try:
                result = json.loads(candidate.strip())
                logger.debug(f"✅ Successfully parsed JSON from pattern match {i+1} (length: {len(candidate)})")
                return result
            except json.JSONDecodeError:
                logger.debug(f"Failed to parse pattern match {i+1} as JSON")
                continue

        if fallback_on_error:
            logger.warning("⚠️  No valid JSON found, returning raw text")
            return response_text
        else:
            logger.error("❌ No valid JSON found in response")
            raise ValueError("Could not parse JSON from LLM response")

    except Exception as e:
        logger.error(f"❌ Error parsing JSON response: {e}")
        if fallback_on_error:
            return response_text
        else:
            raise


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
