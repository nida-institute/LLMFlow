import os
import pytest


def test_openai_credentials_present_and_plausible():
    """
    Ensures LLM credentials are available for live runs.
    Accepts either:
      - OpenAI: OPENAI_API_KEY starting with 'sk-' and reasonable length
      - Azure OpenAI: AZURE_OPENAI_API_KEY plus AZURE_OPENAI_ENDPOINT
    The test avoids any network calls; it only validates environment presence/shape.
    """
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()

    if not openai_key and not azure_key:
        pytest.fail(
            "Missing OpenAI credentials. Set OPENAI_API_KEY (OpenAI) or "
            "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT (Azure OpenAI)."
        )

    if openai_key:
        assert openai_key.startswith("sk-"), (
            "OPENAI_API_KEY should start with 'sk-'. If you're using Azure OpenAI, "
            "unset OPENAI_API_KEY and set AZURE_OPENAI_API_KEY/AZURE_OPENAI_ENDPOINT instead."
        )
        assert len(openai_key) > 20, "OPENAI_API_KEY looks too short to be valid."

    if azure_key:
        # Azure keys are opaque; just require non-trivial length and a plausible endpoint
        assert len(azure_key) > 20, "AZURE_OPENAI_API_KEY looks too short to be valid."
        assert azure_endpoint.startswith("http"), (
            "AZURE_OPENAI_ENDPOINT must be set and start with http(s) when using Azure OpenAI."
        )
