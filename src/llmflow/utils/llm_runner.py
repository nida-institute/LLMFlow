
import subprocess
import json
import unicodedata
import io
import mimetypes
from magic import Magic

import llm

import subprocess
import json
import unicodedata
import xml.etree.ElementTree as ET
from magic import Magic

def call_llm(prompt_path_or_text, model="gpt-4o", tags=None, from_file=True, max_tokens=None, temperature=None):
    """
        Use the `llm` library to call a registered model with a prompt.
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
    # Configure model options
    model_instance = llm.get_model(model)
    options = {}
    model_kwargs = {}

    if temperature is not None:
        model_kwargs["temperature"] = temperature

    if max_tokens is not None:
        model_kwargs["max_tokens"] = max_tokens

    # Set up prompt
    if from_file:
        with open(prompt_path_or_text, 'r') as f:
            prompt_text = f.read()
    else:
        prompt_text = prompt_path_or_text
    # Execute prompt with model
    response = model_instance.prompt(prompt_text, **model_kwargs)
    if tags:
        for tag in tags:
            response.add_tag(tag)

    # Capture output as string
    output = response.text().strip()
    result = type('obj', (object,), {
        'stdout': output,
        'stderr': '',
        'returncode': 0
    })

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
