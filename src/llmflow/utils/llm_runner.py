
import subprocess
import json
import unicodedata
import io
import mimetypes
from magic import Magic

import subprocess
import json
import unicodedata
import xml.etree.ElementTree as ET
from magic import Magic

def call_llm(prompt_path_or_text, model="gpt-4o", tags=None, from_file=True, max_tokens=None, temperature=None):
    """
    Use the `llm` CLI to call a registered model with a prompt.
    If `from_file` is True, `prompt_path_or_text` is a path to a .gpt file.
    Otherwise it's a raw string prompt.

    Parameters:
        prompt_path_or_text: Path to .gpt file or raw prompt text
        model: Model to use for generation
        tags: List of tags to add to the prompt
        from_file: Whether prompt_path_or_text is a file path
        max_tokens: (optional) Maximum output tokens
        temperature: (optional) Creativity of response

    Returns:
        JSON, XML, or normalized string output
    """

    command = ["llm", "prompt", "-m", model]

    if max_tokens is not None:
        command.extend(["-n", str(max_tokens)])
    if temperature is not None:
        command.extend(["--temperature", str(temperature)])
    if tags:
        for tag in tags:
            command.extend(["--tag", tag])

    if from_file:
        command.extend(["-f", prompt_path_or_text])
    else:
        command.append(prompt_path_or_text)

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"LLM call failed: {result.stderr}")

    output = result.stdout.strip()
    output = unicodedata.normalize('NFC', output)

    try:
        mime = Magic(mime=True).from_buffer(output)

        if mime == 'application/json':
            return json.loads(output)
        elif mime in ('application/xml', 'text/xml'):
            return ET.fromstring(output)
        elif mime == 'text/plain':
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                try:
                    return ET.fromstring(output)
                except Exception:
                    return output
    except ImportError:
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            try:
                return ET.fromstring(output)
            except Exception:
                return output

    return output
