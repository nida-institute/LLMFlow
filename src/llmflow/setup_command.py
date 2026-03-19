"""llmflow setup — interactive provider configuration."""
import getpass
import json
import sys

from llmflow.modules.logger import Logger

logger = Logger()

PROVIDER_MODELS = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "o3-mini",
        "o3",
    ],
    "anthropic": [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ],
    "gemini": [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
    ],
}

PROVIDERS = [
    {
        "name": "OpenAI (GPT-4o, o3, ...)",
        "key": "openai",
        "env": "OPENAI_API_KEY",
        "prompt": "OpenAI API key",
        "url": "https://platform.openai.com/api-keys",
    },
    {
        "name": "Anthropic (Claude 3.5, ...)",
        "key": "anthropic",
        "env": "ANTHROPIC_API_KEY",
        "prompt": "Anthropic API key",
        "url": "https://console.anthropic.com/settings/keys",
    },
    {
        "name": "Google Gemini",
        "key": "gemini",
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


def run_setup(update=False):
    try:
        import llm
    except ImportError:
        print("❌ The 'llm' package is not installed. Run: pip install llm")
        sys.exit(1)

    keys_path = llm.user_dir() / "keys.json"
    data = _load_keys(keys_path)

    print("\nllmflow setup — Configure your AI provider\n")
    print("Choose a provider to configure (Ctrl-C to exit):\n")

    for i, p in enumerate(PROVIDERS, 1):
        current = data.get(p["key"])
        status = f"  ✅ key set" if current else "  (not configured)"
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
            print(f"✅ {provider['name']} key saved.\n")

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

    print("\nAvailable models by provider\n")

    for provider in PROVIDERS:
        key = provider["key"]
        models = PROVIDER_MODELS.get(key, [])
        has_key = bool(data.get(key))
        status = "✅" if has_key else "(no key — run `llmflow setup`)"
        print(f"{provider['name']}  {status}")
        for model in models:
            print(f"  {model}")
        print()

    print("💡 Using pip install? Any llm plugin works — use the model name directly")
    print("   in your pipeline YAML: model: ollama/llama3")
    print("   Plugin directory: https://llm.datasette.io/en/stable/plugins/directory.html\n")
