# filepath: llmflow/modules/llm_response_clean.py
import re

from llmflow.utils.io import normalize_nfc


def clean_llm_response_text(text: str) -> str:
    """
    Clean LLM response text by extracting JSON from markdown fences.
    If fences are present, extract only the content between them.
    Otherwise, just strip whitespace.
    """
    # Try to extract content from markdown code fences
    # Match ```json or ``` followed by content, then closing ```
    fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    match = re.search(fence_pattern, text, re.DOTALL)

    if match:
        # Return only the content inside the fences
        return match.group(1).strip()

    # No fences found, just strip whitespace
    return text.strip()
