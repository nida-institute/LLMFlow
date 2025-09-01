import json
import re
import typer
from llmflow.modules.logging import log_section
from llmflow.modules.llm_response_clean import clean_llm_response_text

def parse_llm_json_response(response_text, debug=False):
    """
    Robust parser for JSON responses from LLMs.

    Handles common issues:
    - Markdown code blocks (```json ... ```)
    - Leading/trailing text hedges
    - Empty responses
    - Malformed JSON
    - Unicode issues

    Args:
        response_text (str): Raw response from LLM
        debug (bool): Show debug output

    Returns:
        dict/list: Parsed JSON object

    Raises:
        json.JSONDecodeError: If JSON cannot be parsed after cleanup
        ValueError: If response is empty or invalid
    """

    if debug:
        typer.secho(f"📝 Raw LLM response ({len(response_text)} chars):", fg=typer.colors.BLUE)
        typer.secho(f"'{response_text[:200]}...'", fg=typer.colors.BLUE)

    # Check for empty response
    if not response_text or not response_text.strip():
        raise ValueError("Empty response from LLM")

    # Clean up the response and strip hedges, normalize NFC
    cleaned = clean_llm_response_text(response_text)

    # Find JSON content between code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(1)

    # Look for JSON-like content (starts with { or [)
    json_content_match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    if json_content_match:
        cleaned = json_content_match.group(1)

    if debug:
        typer.secho(f"🧹 Cleaned response ({len(cleaned)} chars):", fg=typer.colors.GREEN)
        typer.secho(f"'{cleaned[:200]}...'", fg=typer.colors.GREEN)

    # Try to parse JSON
    try:
        parsed = json.loads(cleaned)

        if debug:
            typer.secho(f"✅ JSON parsed successfully: {type(parsed)}", fg=typer.colors.GREEN, bold=True)
            if isinstance(parsed, (dict, list)):
                typer.secho(f"📊 Contains {len(parsed)} items", fg=typer.colors.GREEN)

        return parsed

    except json.JSONDecodeError as e:
        # Try some common fixes

        # Fix: Remove trailing commas
        fixed = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        try:
            parsed = json.loads(fixed)
            if debug:
                typer.secho(f"✅ JSON parsed after removing trailing commas", fg=typer.colors.YELLOW)
            return parsed
        except json.JSONDecodeError:
            pass

        # Fix: Handle unescaped quotes in strings
        try:
            # Simple attempt - replace unescaped quotes in likely string values
            fixed = re.sub(r'(?<!\\)"(?=[^,}\]]*[,}\]])', '\\"', cleaned)
            parsed = json.loads(fixed)
            if debug:
                typer.secho(f"✅ JSON parsed after fixing quotes", fg=typer.colors.YELLOW)
            return parsed
        except json.JSONDecodeError:
            pass

        # Fix: Try parsing line by line for array responses
        if cleaned.strip().startswith('[') and cleaned.strip().endswith(']'):
            try:
                # Remove outer brackets and try to parse each object
                inner = cleaned.strip()[1:-1].strip()
                if inner:
                    # Split by likely object boundaries
                    objects = re.split(r'\},\s*\{', inner)
                    if len(objects) > 1:
                        # Reconstruct with proper brackets
                        fixed_objects = []
                        for i, obj in enumerate(objects):
                            if i == 0 and not obj.strip().startswith('{'):
                                obj = '{' + obj
                            if i == len(objects) - 1 and not obj.strip().endswith('}'):
                                obj = obj + '}'
                            if not obj.strip().startswith('{'):
                                obj = '{' + obj
                            if not obj.strip().endswith('}'):
                                obj = obj + '}'
                            fixed_objects.append(obj.strip())

                        # Try parsing each object
                        parsed_objects = []
                        for obj_str in fixed_objects:
                            parsed_objects.append(json.loads(obj_str))

                        if debug:
                            typer.secho(f"✅ JSON parsed as array of {len(parsed_objects)} objects", fg=typer.colors.YELLOW)
                        return parsed_objects
            except:
                pass

        # If all fixes failed, raise the original error with context

        log_section("Could not parse JSON")
        log_section(f"Original error: {e}")
        log_section(f"Cleaned JSON text: '{cleaned}'", True)

        raise json.JSONDecodeError(f"Could not parse LLM JSON response: {e}", cleaned, e.pos)