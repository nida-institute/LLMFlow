"""API keys resolve from one place (LLMFlow#195).

The engine reaches models two ways: through the `llm` package, and — for structured-output
steps — through the provider's client directly. Those used to read the key from *different*
stores: `llm`'s keystore vs `OPENAI_API_KEY` in the environment. So `sp setup`, which writes
only the keystore, reported success and left every `response_format` step unauthenticated.

`resolve_provider_key` gives both routes one source by delegating to `llm.get_key`, whose
order is: explicit argument -> `llm` keystore entry for the alias -> environment variable.

**Every test here patches `llm.get_key`.** That is deliberate, not laziness: this machine's
real keystore holds live keys, so a test that asserted on a *resolved* value would print a
real secret into the log the moment it failed. These tests assert the delegation instead —
which alias and env var are passed through, and that the return value is handed back
untouched. No real key is ever read or compared.
"""
import pytest

from llmflow.utils.llm_runner import PROVIDER_ENV_VARS, resolve_provider_key

SENTINEL = "test-key-not-a-real-secret"


@pytest.fixture
def captured_get_key(monkeypatch):
    """Patch llm.get_key, recording its kwargs and returning a sentinel."""
    calls = {}

    def fake_get_key(explicit_key=None, key_alias=None, env_var=None, **kw):
        calls.update(explicit_key=explicit_key, key_alias=key_alias, env_var=env_var)
        return calls.get("_return", SENTINEL)

    monkeypatch.setattr("llm.get_key", fake_get_key)
    return calls


class TestResolveProviderKey:
    @pytest.mark.parametrize("provider,env_var", sorted(PROVIDER_ENV_VARS.items()))
    def test_passes_the_provider_alias_and_its_env_var(self, provider, env_var,
                                                      captured_get_key):
        """Both key sources are offered for every provider: the keystore entry (by
        alias) and the environment variable."""
        assert resolve_provider_key(provider) == SENTINEL
        assert captured_get_key["key_alias"] == provider
        assert captured_get_key["env_var"] == env_var

    def test_forwards_an_explicit_key(self, captured_get_key):
        resolve_provider_key("openai", explicit="from-caller")
        assert captured_get_key["explicit_key"] == "from-caller"

    def test_returns_none_when_nothing_is_configured(self, monkeypatch):
        monkeypatch.setattr("llm.get_key", lambda *a, **k: None)
        assert resolve_provider_key("openai") is None

    def test_unknown_provider_is_an_error_not_a_silent_none(self):
        """A typo'd provider must not look indistinguishable from 'no key configured'."""
        with pytest.raises(ValueError, match="nosuchprovider"):
            resolve_provider_key("nosuchprovider")

    def test_error_names_the_known_providers(self):
        with pytest.raises(ValueError, match="openai"):
            resolve_provider_key("openai-typo")

    def test_covers_the_three_providers_setup_offers(self):
        assert set(PROVIDER_ENV_VARS) == {"openai", "anthropic", "gemini"}


class TestProviderTableIsTheSingleMapping:
    """`setup_command.PROVIDERS` declared an `"env"` field that nothing read (#195).
    It is now the same mapping the resolver uses, asserted here so they cannot drift."""

    def test_setup_providers_and_resolver_agree(self):
        from llmflow.setup_command import PROVIDERS

        declared = {p["key"]: p["env"] for p in PROVIDERS}
        assert declared == PROVIDER_ENV_VARS, (
            "setup_command.PROVIDERS and PROVIDER_ENV_VARS disagree — "
            "the provider -> env-var mapping must be declared once"
        )


class TestWindowsEnvVarPersistence:
    """On Windows a CLI *can* persist a user environment variable, so `sp setup` finishes
    the job there (LLMFlow#195, option A). On macOS/Linux a process cannot change its
    parent shell's environment, so setup does not try — option D makes the env var
    unnecessary anyway.
    """

    def test_persists_on_windows(self, monkeypatch):
        from llmflow import setup_command

        monkeypatch.setattr(setup_command.sys, "platform", "win32")
        calls = []
        monkeypatch.setattr(setup_command, "_set_windows_user_env",
                            lambda name, value: calls.append((name, value)))
        setup_command._persist_env_var("OPENAI_API_KEY", "k")
        assert calls == [("OPENAI_API_KEY", "k")]

    def test_does_nothing_on_macos(self, monkeypatch):
        from llmflow import setup_command

        monkeypatch.setattr(setup_command.sys, "platform", "darwin")
        calls = []
        monkeypatch.setattr(setup_command, "_set_windows_user_env",
                            lambda name, value: calls.append((name, value)))
        assert setup_command._persist_env_var("OPENAI_API_KEY", "k") is False
        assert calls == []

    def test_reports_failure_rather_than_raising(self, monkeypatch):
        """A registry write can fail; setup must not abort a successful key save over it."""
        from llmflow import setup_command

        monkeypatch.setattr(setup_command.sys, "platform", "win32")

        def boom(name, value):
            raise OSError("registry unavailable")

        monkeypatch.setattr(setup_command, "_set_windows_user_env", boom)
        assert setup_command._persist_env_var("OPENAI_API_KEY", "k") is False
