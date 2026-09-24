"""`sp setup` — interactive provider configuration."""
import getpass
import json
import sys

from llmflow.modules.logger import Logger

logger = Logger()


def provider_models() -> dict:
    """Model names grouped by provider, read from `data/models.json`.

    Derived rather than listed, because the listed version drifted badly: `data/models.json` was
    kept current while a literal dict here still offered `gpt-4o` as the newest OpenAI model and
    named two models the data file has never contained. A reader picking from `sp models` was
    being steered to a two-generation-old model.

    The provider keys come from the data too. The hardcoded set said `gemini` where the data says
    `google`, which is exactly the mismatch that turns a derived list into a silently empty one.
    """
    from llmflow.modules.telemetry import _load_models_data

    grouped: dict = {}
    for name, entry in (_load_models_data().get("models") or {}).items():
        grouped.setdefault(entry.get("provider", "other"), []).append(name)
    return {provider: sorted(names) for provider, names in sorted(grouped.items())}

#: Providers this command can store a key for.
#:
#: Two names, deliberately, because two systems name the same provider differently and neither
#: is ours to change. `key` is the `llm` keystore's identity and the same mapping the resolver
#: uses (`PROVIDER_ENV_VARS`, asserted equal in `test_api_key_resolution.py`) — Google's is
#: `gemini` there. `catalog` is the `provider` field in `data/models.json`, where it is `google`.
#: Collapsing them into one field looks tidy and silently empties a provider's model list.
#:
#: Names carry no generation: "Anthropic (Claude 3.5, ...)" is a claim about what is current,
#: and it was three generations stale before anyone noticed.
PROVIDERS = [
    {
        "name": "OpenAI",
        "key": "openai",
        "catalog": "openai",
        "env": "OPENAI_API_KEY",
        "prompt": "OpenAI API key",
        "url": "https://platform.openai.com/api-keys",
    },
    {
        "name": "Anthropic",
        "key": "anthropic",
        "catalog": "anthropic",
        "env": "ANTHROPIC_API_KEY",
        "prompt": "Anthropic API key",
        "url": "https://console.anthropic.com/settings/keys",
    },
    {
        "name": "Google Gemini",
        "key": "gemini",
        "catalog": "google",
        "env": "GEMINI_API_KEY",
        "prompt": "Gemini API key",
        "url": "https://aistudio.google.com/app/apikey",
    },
]


def _load_keys(keys_path):
    if keys_path.exists():
        try:
            return json.loads(keys_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_keys(keys_path, data):
    keys_path.parent.mkdir(parents=True, exist_ok=True)
    keys_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _set_windows_user_env(name, value):
    """Persist a user-scoped environment variable in the Windows registry.

    `winreg` ships only on Windows, so type checkers running on other platforms cannot
    resolve its attributes — hence the ignores. Guarded by the caller.
    """
    import winreg  # type: ignore[import-not-found]

    with winreg.OpenKey(  # type: ignore[attr-defined]
        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE  # type: ignore[attr-defined]
    ) as key:
        winreg.SetValueEx(  # type: ignore[attr-defined]
            key, name, 0, winreg.REG_EXPAND_SZ, value  # type: ignore[attr-defined]
        )


def _persist_env_var(name, value):
    """Persist *name* for future shells. Returns True if it was written.

    Windows only, and deliberately so: a process cannot change its parent shell's
    environment, so on macOS/Linux there is nothing setup can honestly do — it would have
    to edit the user's shell profile. It does not need to, because the engine resolves keys
    through the `llm` keystore as well as the environment (see
    llmflow.utils.llm_runner.resolve_provider_key, LLMFlow#195).

    Never raises: a registry write failing must not turn a successful key save into an
    error.
    """
    if sys.platform != "win32":
        return False
    try:
        _set_windows_user_env(name, value)
        return True
    except Exception:
        return False


def run_setup(update=False):
    try:
        import llm
    except ImportError:
        print("❌ The 'llm' package is not installed. Run: pip install llm")
        sys.exit(1)

    keys_path = llm.user_dir() / "keys.json"
    data = _load_keys(keys_path)

    print("\nsp setup — Configure your AI provider\n")
    print("Choose a provider to configure (Ctrl-C to exit):\n")

    for i, p in enumerate(PROVIDERS, 1):
        current = data.get(p["key"])
        status = "  ✅ key set" if current else "  (not configured)"
        print(f"  {i}. {p['name']}{status}")
    print(f"  {len(PROVIDERS) + 1}. Done\n")

    while True:
        try:
            choice = input("Enter number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

        if not choice.isdigit():
            print("Please enter a number.")
            continue

        idx = int(choice)
        if idx == len(PROVIDERS) + 1:
            print("\n✅ Setup complete.")
            break
        if idx < 1 or idx > len(PROVIDERS):
            print(f"Please enter 1–{len(PROVIDERS) + 1}.")
            continue

        provider = PROVIDERS[idx - 1]
        print(f"\n{provider['name']}")
        print(f"Get your key at: {provider['url']}")

        try:
            key_value = getpass.getpass(f"{provider['prompt']}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

        if not key_value:
            print("No key entered — skipping.")
        else:
            data[provider["key"]] = key_value
            _save_keys(keys_path, data)
            print(f"✅ {provider['name']} key saved.")
            # The engine reads this keystore, so the key is already usable. On Windows we
            # can also persist the environment variable for anything that expects it.
            if _persist_env_var(provider["env"], key_value):
                print(f"   Also set {provider['env']} for your user account "
                      "(open a new terminal to pick it up).")
            print()

        print("Configure another provider?\n")
        for i, p in enumerate(PROVIDERS, 1):
            current = data.get(p["key"])
            status = "  ✅ key set" if current else "  (not configured)"
            print(f"  {i}. {p['name']}{status}")
        print(f"  {len(PROVIDERS) + 1}. Done\n")


def run_models():
    """Print available models grouped by provider, showing which have API keys configured."""
    try:
        import llm
    except ImportError:
        print("❌ The 'llm' package is not installed. Run: pip install llm")
        sys.exit(1)

    keys_path = llm.user_dir() / "keys.json"
    data = _load_keys(keys_path)

    roster = provider_models()
    print("\nAvailable models by provider\n")

    for provider in PROVIDERS:
        key = provider["key"]
        models = roster.get(provider.get("catalog", key), [])
        has_key = bool(data.get(key))
        status = "✅" if has_key else "(no key — run `sp setup`)"
        print(f"{provider['name']}  {status}")
        for model in models:
            print(f"  {model}")
        print()

    print("💡 Using pip install? Any llm plugin works — use the model name directly")
    print("   in your pipeline YAML: model: ollama/llama3")
    print("   Plugin directory: https://llm.datasette.io/en/stable/plugins/directory.html\n")

    from llmflow.modules.telemetry import models_data_age_days
    age = models_data_age_days()
    if age is not None and age > 60:
        print(f"⚠️  Model pricing data is {age} days old. Run `sp models --update` to refresh.\n")


def run_models_update() -> bool:
    """Interactively update models.json from installed llm plugins.

    Discovers model IDs not covered by any pricing pattern, prompts the user
    to assign each to an existing family or define a new one, then saves the
    file with today's date stamped as last_updated.
    """
    from llmflow.modules.telemetry import (
        discover_new_models,
        get_models_data,
        save_models_json,
    )

    print("🔍 Querying installed llm plugins for available models...")
    new_ids = discover_new_models()

    data = get_models_data()
    families = list(data.get("models", {}).keys())

    if not new_ids:
        print("✅ All available models are already covered in models.json.")
    else:
        print(f"\n📋 Found {len(new_ids)} model(s) not covered by any pricing pattern:")
        for mid in new_ids:
            print(f"   {mid}")

        added = 0
        for model_id in new_ids:
            print(f"\n--- {model_id} ---")
            print("Assign to existing family:")
            for i, fam in enumerate(families, 1):
                print(f"  {i:2}. {fam}")
            print("   n. New family")
            print("   s. Skip")

            try:
                choice = input("Choice: ").strip().lower()
            except EOFError:
                break

            if choice == "s":
                continue

            if choice == "n":
                try:
                    family_key = input("  Family key (e.g. gpt-5.4): ").strip()
                    if not family_key:
                        continue
                    provider = input("  Provider (openai/anthropic/google): ").strip()
                    family_label = input(f"  Family label [{family_key}]: ").strip() or family_key
                    inp = float(input("  Input price per 1M tokens: ").strip() or "0")
                    out = float(input("  Output price per 1M tokens: ").strip() or "0")
                    ctx = int(input("  Max context tokens: ").strip() or "0")
                    max_out = int(input("  Max output tokens: ").strip() or "0")
                    json_schema_raw = input("  Supports JSON schema? (y/n) [n]: ").strip().lower()
                    json_schema = json_schema_raw == "y"
                except (EOFError, ValueError) as e:
                    print(f"  Skipping — {e}")
                    continue

                data["models"][family_key] = {
                    "provider": provider,
                    "family": family_label,
                    "input_price_per_1m": inp,
                    "output_price_per_1m": out,
                    "max_context_tokens": ctx,
                    "max_output_tokens": max_out,
                    "supports_json_schema": json_schema,
                }
                data["model_patterns"][family_key] = [model_id]
                families.append(family_key)
                print(f"  ✅ Added new family '{family_key}' with pattern '{model_id}'")
                added += 1

            else:
                try:
                    idx = int(choice) - 1
                    if not (0 <= idx < len(families)):
                        print("  Invalid number, skipping.")
                        continue
                    family_key = families[idx]
                except ValueError:
                    print("  Invalid choice, skipping.")
                    continue

                patterns = data["model_patterns"].setdefault(family_key, [])
                if model_id not in patterns:
                    patterns.append(model_id)
                print(f"  ✅ Added '{model_id}' to patterns for '{family_key}'")
                added += 1

        print(f"\n{added} new pattern(s) added.")

    if save_models_json(data):
        print("✅ models.json saved with today's date.")
        return True
    return False
