import unicodedata
import llm
import json
import xml.etree.ElementTree as ET
import time

def call_llm(prompt_text, model="gpt-4o", tags=None,
             temperature=0.7, max_tokens=2500, from_file=False,
             max_retries=3, retry_backoff=2):
    """
    Calls the `llm` Python API with retries and output normalization.
    """

    if from_file:
        with open(prompt_text, encoding="utf-8") as f:
            prompt = f.read()
    else:
        prompt = prompt_text

    prompt = unicodedata.normalize("NFC", prompt)
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            model_obj = llm.get_model(model)
            # Call with only allowed options
            response = model_obj.prompt(
                prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            output = response.text()
            output = unicodedata.normalize("NFC", output)

            # Try to return structured content
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                try:
                    return ET.fromstring(output)
                except ET.ParseError:
                    return output  # fallback to plain text

        except Exception as e:
            print(f"⚠️ LLM call failed on attempt {attempt}: {e}")
            last_exception = e
            if attempt < max_retries:
                wait_time = retry_backoff ** (attempt - 1)
                print(f"🔁 Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    raise RuntimeError(f"LLM call failed after {max_retries} attempts") from last_exception
