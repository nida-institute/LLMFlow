# filepath: llmflow/modules/llm_response_clean.py
import re


def clean_llm_response_text(text: str) -> str:
    """
    Clean LLM response text by extracting JSON from markdown fences or surrounding text.
    """
    # Try to extract content from markdown code fences first
    fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    match = re.search(fence_pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()

    # If no fences, try to find JSON objects or arrays embedded in text
    # Look for balanced braces/brackets with proper nesting
    json_start = -1
    brace_count = 0
    bracket_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char in '{[':
                if json_start == -1:
                    json_start = i
                if char == '{':
                    brace_count += 1
                else:
                    bracket_count += 1
            elif char in '}]':
                if char == '}':
                    brace_count -= 1
                else:
                    bracket_count -= 1

                # Found complete JSON structure
                if brace_count == 0 and bracket_count == 0 and json_start != -1:
                    return text[json_start:i+1].strip()

    # No JSON found, return as-is
    return text.strip()
