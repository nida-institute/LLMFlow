from llmflow.modules.telemetry import get_pricing_family


def test_pricing_family_gpt5_variants():
    # Variants should map to gpt-5 family for pricing
    assert get_pricing_family("gpt-5") == "gpt-5"
    assert get_pricing_family("gpt-5-preview") == "gpt-5"
    assert get_pricing_family("gpt-5o") == "gpt-5"
    assert get_pricing_family("o3-mini") == "gpt-5"
    assert get_pricing_family("o4") == "gpt-5"


def test_pricing_family_known_models():
    assert get_pricing_family("gpt-4o") == "gpt-4o"
    assert get_pricing_family("gpt-4o-mini") == "gpt-4o-mini"
    assert get_pricing_family("gpt-4-turbo") == "gpt-4-turbo"
    assert get_pricing_family("gpt-4") == "gpt-4"
    assert get_pricing_family("gpt-3.5-turbo") == "gpt-3.5-turbo"


def test_pricing_family_unknown():
    assert get_pricing_family("nonexistent-model-xyz") is None


def test_pricing_family_gpt41():
    """gpt-4.1 family should map to its own pricing, not gpt-4 ($30/1M)."""
    assert get_pricing_family("gpt-4.1") == "gpt-4.1"
    assert get_pricing_family("gpt-4.1-mini") == "gpt-4.1-mini"
    assert get_pricing_family("gpt-4.1-nano") == "gpt-4.1-nano"


def test_gpt41_not_mapped_to_gpt4():
    """gpt-4.1 must not fall through to 'gpt-4' family (wrong pricing)."""
    assert get_pricing_family("gpt-4.1") != "gpt-4"
    assert get_pricing_family("gpt-4.1-mini") != "gpt-4"
