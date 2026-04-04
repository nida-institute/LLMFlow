"""Tests for model metadata freshness and completeness.

These tests ensure model pricing, token limits, and capabilities are current
before shipping a release. Run automatically in CI.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from llmflow.modules.telemetry import (
    get_model_data_version,
    get_model_metadata,
    supports_json_schema,
    get_model_max_tokens,
    MODEL_METADATA,
    MODEL_FAMILIES,
)


def test_model_metadata_is_fresh():
    """Model metadata must be updated at least quarterly (90 days).

    This test enforces regular reviews of pricing and token limits.
    Run before shipping to ensure users have current data.
    """
    version, last_updated_str = get_model_data_version()

    # Parse date
    last_updated = None
    try:
        last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d")
    except ValueError:
        pytest.fail(
            f"Invalid last_updated format in data/models.json: '{last_updated_str}'. "
            "Expected format: YYYY-MM-DD"
        )

    # Type assertion: pytest.fail() raises exception, so last_updated is always set here
    assert last_updated is not None

    # Check age
    age_days = (datetime.now() - last_updated).days

    assert age_days < 90, (
        f"⚠️  data/models.json is {age_days} days old (last updated {last_updated_str}).\n"
        "   ACTION REQUIRED: Review and update model pricing/limits in data/models.json.\n"
        "   1. Check OpenAI pricing: https://openai.com/api/pricing/\n"
        "   2. Check Anthropic pricing: https://www.anthropic.com/pricing\n"
        "   3. Check Google Gemini pricing: https://ai.google.dev/pricing\n"
        "   4. Update data/models.json with current values\n"
        "   5. Update 'last_updated' field to today's date"
    )


def test_model_metadata_has_required_fields():
    """Each model in metadata must have complete information."""

    # Load raw JSON to check structure
    models_file = Path(__file__).parent.parent / "data" / "models.json"
    with open(models_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    required_fields = {
        "provider",
        "input_price_per_1m",
        "output_price_per_1m",
        "max_context_tokens",
        "max_output_tokens",
        "supports_json_schema",
    }

    models = data.get("models", {})

    for model_key, model_data in models.items():
        missing = required_fields - set(model_data.keys())
        assert not missing, (
            f"Model '{model_key}' missing required fields: {missing}\n"
            f"All models must have: {required_fields}"
        )


def test_gpt_models_have_pricing():
    """All GPT model families must have pricing data."""
    gpt_families = ["gpt-5", "o1", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
                    "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

    for family in gpt_families:
        assert family in MODEL_METADATA, f"Missing pricing for {family}"

        metadata = MODEL_METADATA[family]
        assert metadata["input"] > 0, f"{family} input price must be > 0"
        assert metadata["output"] > 0, f"{family} output price must be > 0"
        assert metadata["max_context"] > 0, f"{family} max_context must be > 0"
        assert metadata["max_output"] > 0, f"{family} max_output must be > 0"


def test_claude_models_have_pricing():
    """All Claude model families must have pricing data."""
    claude_families = [
        "claude-4-opus", "claude-4-sonnet", "claude-4-haiku",
        "claude-3.5-opus", "claude-3.5-sonnet", "claude-3.5-haiku",
        "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
    ]

    for family in claude_families:
        assert family in MODEL_METADATA, f"Missing pricing for {family}"

        metadata = MODEL_METADATA[family]
        assert metadata["input"] > 0, f"{family} input price must be > 0"
        assert metadata["output"] > 0, f"{family} output price must be > 0"
        assert metadata["max_context"] > 0, f"{family} max_context must be > 0"


def test_gemini_models_have_pricing():
    """All Gemini model families must have pricing data."""
    gemini_families = [
        "gemini-2.5-pro", "gemini-2.5-flash",
        "gemini-1.5-pro", "gemini-1.5-flash",
    ]

    for family in gemini_families:
        assert family in MODEL_METADATA, f"Missing pricing for {family}"

        metadata = MODEL_METADATA[family]
        assert metadata["input"] >= 0, f"{family} input price must be >= 0"
        assert metadata["output"] >= 0, f"{family} output price must be >= 0"
        assert metadata["max_context"] > 0, f"{family} max_context must be > 0"


def test_json_schema_support_flags():
    """Verify JSON schema support flags match known capabilities."""

    # OpenAI models with JSON schema (response_format)
    assert supports_json_schema("gpt-5") is True
    assert supports_json_schema("gpt-4.1") is True
    assert supports_json_schema("gpt-4o") is True
    assert supports_json_schema("gpt-4o-mini") is True

    # OpenAI models WITHOUT JSON schema
    assert supports_json_schema("o1") is False  # o1 series doesn't support structured output
    assert supports_json_schema("gpt-4") is False  # Legacy gpt-4

    # Claude models (use prompt engineering, not strict schema)
    assert supports_json_schema("claude-3.5-sonnet") is False
    assert supports_json_schema("claude-4-opus") is False

    # Gemini models (use response_schema parameter)
    assert supports_json_schema("gemini-2.5-pro") is True
    assert supports_json_schema("gemini-1.5-flash") is True


def test_model_patterns_complete():
    """All models in metadata must have pattern mappings."""

    # Every model key in MODEL_METADATA should appear in MODEL_FAMILIES
    for model_key in MODEL_METADATA.keys():
        assert model_key in MODEL_FAMILIES, (
            f"Model '{model_key}' exists in MODEL_METADATA but missing from MODEL_FAMILIES.\n"
            "Add pattern mapping in data/models.json 'model_patterns' section."
        )


def test_max_tokens_are_reasonable():
    """Sanity check that token limits are in reasonable ranges."""

    for model_key, metadata in MODEL_METADATA.items():
        max_context = metadata["max_context"]
        max_output = metadata["max_output"]

        # Context window should be at least 4k
        assert max_context >= 4096, (
            f"{model_key} max_context ({max_context}) seems too low. Check data/models.json."
        )

        # Output should be at least 1k
        assert max_output >= 1024, (
            f"{model_key} max_output ({max_output}) seems too low. Check data/models.json."
        )

        # Output shouldn't exceed context
        assert max_output <= max_context, (
            f"{model_key} max_output ({max_output}) exceeds max_context ({max_context})."
        )


def test_pricing_is_reasonable():
    """Sanity check that pricing is in reasonable ranges."""

    for model_key, metadata in MODEL_METADATA.items():
        input_price = metadata["input"]
        output_price = metadata["output"]

        # Prices should be positive
        assert input_price >= 0, f"{model_key} input price cannot be negative"
        assert output_price >= 0, f"{model_key} output price cannot be negative"

        # Output price should generally be >= input price (or equal for some models)
        # Relaxed check: output shouldn't be < 50% of input (catches obvious errors)
        if input_price > 0:
            ratio = output_price / input_price
            assert ratio >= 0.5, (
                f"{model_key} pricing ratio seems wrong: "
                f"input=${input_price}, output=${output_price} (ratio={ratio:.2f})"
            )

        # Prices shouldn't be absurdly high (>$200 per 1M tokens)
        assert input_price < 200, f"{model_key} input price (${input_price}) seems too high"
        assert output_price < 200, f"{model_key} output price (${output_price}) seems too high"


def test_get_model_metadata_returns_data():
    """get_model_metadata() should return data for known models."""

    # Test a few known models
    gpt4o_meta = get_model_metadata("gpt-4o")
    assert gpt4o_meta is not None
    assert gpt4o_meta["input"] == MODEL_METADATA["gpt-4o"]["input"]

    claude_meta = get_model_metadata("claude-3.5-sonnet")
    assert claude_meta is not None

    gemini_meta = get_model_metadata("gemini-2.5-pro")
    assert gemini_meta is not None

    # Unknown model
    unknown_meta = get_model_metadata("totally-fake-model-9000")
    assert unknown_meta is None


def test_get_model_max_tokens_returns_limits():
    """get_model_max_tokens() should return context limits."""

    # GPT-4o has 128k context
    assert get_model_max_tokens("gpt-4o") == 128000

    # Gemini 2.5 Pro has 2M context
    assert get_model_max_tokens("gemini-2.5-pro") == 2000000

    # Claude 3.5 has 200k context
    assert get_model_max_tokens("claude-3.5-sonnet") == 200000

    # Unknown model
    assert get_model_max_tokens("fake-model") is None
