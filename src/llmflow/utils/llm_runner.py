
import subprocess
import json
import unicodedata
import io
import mimetypes
from magic import Magic
def call_llm(prompt_path_or_text, model="gpt-4o", tags=None, from_file=True):
    """
    Use the `llm` CLI to call a registered model with a prompt.
    If `from_file` is True, `prompt_path_or_text` is a path to a .gpt file.
    Otherwise it's a raw string prompt.

    Parameters:
        prompt_path_or_text: Path to .gpt file or raw prompt text
        model: Model to use for generation
        tags: List of tags to add to the prompt
        from_file: Whether prompt_path_or_text is a file path

    Returns:
        For JSON: Returns a Python dictionary of the parsed JSON
        For XML: Returns an XML ElementTree object
        For others: Returns the normalized string output
    """

    command = ["llm", "prompt", "-m", model]
    if tags:
        for tag in tags:
            command.extend(["--tag", tag])

    if from_file:
        command.extend(["-f", prompt_path_or_text])
    else:
        # For raw text, pass it as an argument after all options
        command.append(prompt_path_or_text)

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"LLM call failed: {result.stderr}")

    output = result.stdout.strip()

    # Normalize output to Unicode NFC form
    output = unicodedata.normalize('NFC', output)

    import xml.etree.ElementTree as ET

    # Try to detect content type from the output
    try:
        mime = Magic(mime=True)
        content_type = mime.from_buffer(output)

        if content_type == 'application/json':
            return json.loads(output)
        elif content_type in ('application/xml', 'text/xml'):
            return ET.fromstring(output)
        elif content_type == 'text/plain':
            # Try JSON first as it might still be valid JSON with text/plain mime type
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # Try XML as fallback
                try:
                    return ET.fromstring(output)
                except Exception:
                    # Return as plain text
                    return output
    except ImportError:
        # Fall back to manual detection if python-magic isn't available
        # Try JSON first
        try:
            parsed_json = json.loads(output)
            return parsed_json
        except json.JSONDecodeError:
            # Not XML either, try XML
            try:
                xml_root = ET.fromstring(output)
                return xml_root
            except Exception:
                # Not XML either, return as string
                return output

    return output
