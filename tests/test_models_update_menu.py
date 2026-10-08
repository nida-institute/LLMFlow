"""`sp models --update` asks which entry prices a new model, with the entries grouped by family.

Measured before this was written: the menu listed the keys of `models` in `models.json` — 23
individual price entries, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano` and so on — under the heading
"Assign to existing family", and never read the `family` field each entry carries. A model
assigned from it took that entry's prices and limits without the question saying so. Prices
differ inside a family, so the real question is which entry to price the model like.
"""
import pytest

from llmflow import setup_command
from llmflow.modules import telemetry

DATA = {
    "metadata_version": "1.0",
    "last_updated": "2026-09-06",
    "models": {
        "gpt-5": {"provider": "openai", "family": "gpt-5-reasoning", "input_price_per_1m": 1.25,
                  "output_price_per_1m": 10.0, "max_context_tokens": 400000,
                  "max_output_tokens": 128000, "supports_json_schema": True},
        "gpt-4.1": {"provider": "openai", "family": "gpt-4.1", "input_price_per_1m": 2.0,
                    "output_price_per_1m": 8.0, "max_context_tokens": 1047576,
                    "max_output_tokens": 32768, "supports_json_schema": True},
        "gpt-4.1-mini": {"provider": "openai", "family": "gpt-4.1", "input_price_per_1m": 0.4,
                         "output_price_per_1m": 1.6, "max_context_tokens": 1047576,
                         "max_output_tokens": 32768, "supports_json_schema": True},
    },
    "model_patterns": {"gpt-5": ["gpt-5"], "gpt-4.1": ["gpt-4.1"], "gpt-4.1-mini": ["gpt-4.1-mini"]},
}


@pytest.fixture
def menu(monkeypatch):
    """Run the update with *answers* typed in; return what was saved."""
    import copy

    saved = {}

    def run(answers, new=("gpt-6-astra",)):
        data = copy.deepcopy(DATA)
        replies = iter(answers)
        monkeypatch.setattr(telemetry, "discover_new_models", lambda: list(new))
        monkeypatch.setattr(telemetry, "get_models_data", lambda: data)
        monkeypatch.setattr(telemetry, "save_models_json", lambda d, *a: saved.update(d) or True)
        def typed(prompt=""):
            print(prompt, end="")  # as `input` does, so the prompt reaches the captured output
            return next(replies)

        monkeypatch.setattr("builtins.input", typed)
        setup_command.run_models_update()
        return saved

    return run


def _numbered(out, entry):
    """The number the menu gave *entry*."""
    for line in out.splitlines():
        stripped = line.strip()
        if stripped.endswith(f". {entry}") or f". {entry} " in stripped:
            return stripped.split(".")[0].strip()
    raise AssertionError(f"{entry} is not offered:\n{out}")


def test_entries_are_shown_under_their_family(menu, capsys):
    menu(["s"])
    out = capsys.readouterr().out
    assert "gpt-4.1" in out and "gpt-5-reasoning" in out
    header = next(i for i, line in enumerate(out.splitlines()) if line.strip() == "gpt-4.1:")
    below = out.splitlines()[header + 1: header + 3]
    assert any(line.strip().endswith(". gpt-4.1") for line in below)
    assert any(line.strip().endswith(". gpt-4.1-mini") for line in below)


def test_the_question_is_which_entry_prices_it(menu, capsys):
    menu(["s"])
    out = capsys.readouterr().out
    assert "Price gpt-6-astra like" in out
    assert "Assign to existing family" not in out


def test_choosing_an_entry_adds_the_model_to_its_patterns(menu, capsys):
    saved = {}

    def answers():
        out = capsys.readouterr().out
        return _numbered(out, "gpt-4.1-mini")

    # The number depends on the menu's order, so read it from a dry run first.
    menu(["s"])
    number = answers()
    saved = menu([number])
    assert "gpt-6-astra" in saved["model_patterns"]["gpt-4.1-mini"]


def test_a_new_entry_joins_an_existing_family(menu, capsys):
    menu(["s"])
    capsys.readouterr()
    saved = menu([
        "n",            # a new entry
        "",             # its key: the model's own id
        "openai",       # provider
        "1",            # family: the first offered
        "3", "12",      # prices
        "500000", "64000",
        "y",
    ])
    entry = saved["models"]["gpt-6-astra"]
    assert entry["family"] == "gpt-5-reasoning"
    assert (entry["input_price_per_1m"], entry["output_price_per_1m"]) == (3.0, 12.0)
    assert (entry["max_context_tokens"], entry["max_output_tokens"]) == (500000, 64000)
    assert saved["model_patterns"]["gpt-6-astra"] == ["gpt-6-astra"]


def test_a_new_entry_can_start_a_new_family(menu):
    saved = menu(["n", "", "openai", "gpt-6", "3", "12", "500000", "64000", "n"])
    assert saved["models"]["gpt-6-astra"]["family"] == "gpt-6"


def test_the_new_entry_question_offers_the_families(menu, capsys):
    menu(["n", "", "openai", "gpt-6", "0", "0", "0", "0", "n"])
    out = capsys.readouterr().out
    assert "gpt-4.1" in out and "gpt-5-reasoning" in out and "or type a new family" in out
