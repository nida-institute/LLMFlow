# filepath: llmflow/modules/llm_response_clean.py
import re
from llmflow.utils.io import normalize_nfc

def clean_llm_response_text(text):
    """
    Strips LLM hedges, code fences, and normalizes to NFC.
    """
    hedge_patterns = [
        r'^Here\'s the (JSON )?response:?\s*',
        r'^The (JSON )?output is:?\s*',
        r'^```json\s*',
        r'^```markdown\s*',
        r'^```xml\s*',
        r'^```html\s*',
        r'^```csv\s*',
        r'^```tsv\s*',
        r'^```txt\s*',
        r'^```\s*',
        r'\s*```\s*$',
        r'^Here is the.*?:\s*',
        r'^Based on.*?:\s*',
        r'^The result is:?\s*',
        r'^Output:\s*',
        r'^Answer:\s*',
        r'^Sure, here.*?:\s*',
        r'^Certainly!.*?:\s*',
        r'^Of course!.*?:\s*',
        r'^As requested.*?:\s*',
        r'^Below is.*?:\s*',
    ]
    cleaned = text.strip()
    for pattern in hedge_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = cleaned.strip()
    return normalize_nfc(cleaned)