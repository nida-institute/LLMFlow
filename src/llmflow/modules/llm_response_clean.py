# filepath: llmflow/modules/llm_response_clean.py
import re


def clean_llm_response_text(text: str) -> str:
    """
    Clean LLM response text by extracting JSON from markdown fences or surrounding text.
    """
    # Try to extract content from markdown code fences first
    fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    match = re.search(fence_pattern, text, re.DOTALL | re.IGNORECASE)

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


_OUTER_FENCE = re.compile(r"\A```([\w-]*)[ \t]*\r?\n(.*)\r?\n```[ \t]*\Z", re.DOTALL)
_FENCE_LINE = re.compile(r"^[ \t]*```", re.MULTILINE)


def strip_outer_fence(text: str) -> str:
    """*text* without a code fence that wraps the whole of it, and nothing else removed.

    A text answer is the answer: a review whose checklist reads `[x]`, an analysis with a
    diagram in a fenced block, must reach the pipeline whole. Only when the model has wrapped
    its entire answer in one fence is the fence taken off: a fence with nothing fenced inside
    it, or a ```` ```markdown ```` (or ```` ```md ````) fence whose inner fences pair up — a
    document with a diagram in it, wrapped as a whole. Two separate blocks that happen to open
    and close the answer are left alone. JSON is dug out of surrounding prose later, by the JSON
    parser, for JSON steps only.
    """
    stripped = text.strip()
    match = _OUTER_FENCE.match(stripped)
    if match:
        info, inner = match.group(1).lower(), match.group(2)
        fences = len(_FENCE_LINE.findall(inner))
        if fences == 0 or (info in ("markdown", "md") and fences % 2 == 0):
            return inner.strip()
    return stripped
