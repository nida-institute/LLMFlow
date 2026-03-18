# Installing LLMFlow (Prebuilt Executables)

LLMFlow publishes single-file executables for Windows, macOS, and Linux. No Python or package managers required.

## Quick Install (recommended)

### macOS / Linux
```bash
curl -fsSL https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.sh | bash
```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.ps1 | iex
```

After installing, run `llmflow setup` to configure your API key for OpenAI, Anthropic, or Google Gemini.

---

## Manual Install

**⬇️ [Download the latest release](https://github.com/nida-institute/LLMFlow/releases/latest)** — click Assets and pick the file for your platform.

> **Prerequisites**
> - An OpenAI, Anthropic, or Google Gemini API key (configured via `llmflow setup` after install).
> - macOS 13+/Windows 11+/Ubuntu 22.04+ are the tested targets (other recent versions typically work, but aren’t guaranteed).

---

## 1. Download the Latest Release

1. Visit the [GitHub Releases page](https://github.com/nida-institute/LLMFlow/releases).
2. Pick the newest release tagged `LLMFlow vx.y.z`.
3. Download the artifact for your platform:
   - **macOS (Universal)**: `llmflow-macos` (single binary)
   - **Windows (x64)**: `llmflow-windows.exe`
   - **Linux (x86_64)**: `llmflow-linux`
4. (Optional) Verify checksums listed in the release notes.

---

## 2. Install per Operating System

### macOS
1. Create a personal `bin` folder (if it doesn't exist) and move the binary there — no admin rights needed:
   ```bash
   mkdir -p ~/bin
   mv ~/Downloads/llmflow-macos ~/bin/llmflow
   chmod +x ~/bin/llmflow
   ```
2. Make sure `~/bin` is on your PATH. Add this line to `~/.zshrc` (or `~/.bash_profile` for older Macs) if it isn't already:
   ```bash
   export PATH="$HOME/bin:$PATH"
   ```
   Then reload your shell: `source ~/.zshrc`
3. On first launch, macOS Gatekeeper will likely block the unsigned binary:
   - Open *System Settings → Privacy & Security*.
   - Scroll to *Security* and click **Allow Anyway** next to `llmflow` (screenshot recommended here for docs/website).
   - Re-run `llmflow` from the terminal; when the "This app is from an unidentified developer" dialog appears, choose **Open**.

### Windows

#### Step 1 — Download

1. Go to [github.com/nida-institute/LLMFlow/releases/latest](https://github.com/nida-institute/LLMFlow/releases/latest).
2. Under **Assets**, click `llmflow-windows.exe` to download it.

#### Step 2 — Create a permanent home for the executable

1. Create the folder `C:\Tools\` (or any folder you prefer — just be consistent).
2. Move `llmflow-windows.exe` from your Downloads folder into `C:\Tools\`.
3. Rename it to `llmflow.exe` so you can type `llmflow` instead of `llmflow-windows`.

#### Step 3 — Add `C:\Tools\` to your PATH

This lets you run `llmflow` from any folder in any terminal window.

1. Press **Win + S**, type **"environment variables"**, and click **"Edit the system environment variables"**.
2. Click the **Environment Variables…** button at the bottom of the dialog.
3. In the **User variables** section (top half), find **Path** and double-click it.
4. Click **New**, type `C:\Tools\`, then click **OK** on all three dialogs.
5. **Close and reopen** any PowerShell or Command Prompt windows — existing ones won't pick up the change.

#### Step 4 — Clear the SmartScreen warning (first run only)

Because the binary is unsigned, Windows will block it on first launch:

1. Open PowerShell and run `llmflow --version`.
2. If you see a SmartScreen dialog saying **"Windows protected your PC"**:
   - Click **More info**.
   - Click **Run anyway**.
3. After this one-time step, `llmflow` runs without any dialogs.

**Alternative (no dialog):** Right-click `llmflow.exe` in File Explorer → **Properties** → check **Unblock** at the bottom → **OK**. Then run normally.

#### Step 5 — Set your API key

In PowerShell (persists for your user account):
```powershell
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-...", "User")
```
Close and reopen PowerShell, then confirm: `echo $env:OPENAI_API_KEY`

#### Verify

```powershell
llmflow --version
```

You should see something like `llmflow 0.1.5.04`. You're ready — continue with the [Quickstart Tutorial](docs/tutorial.md).

### Linux
1. Move the binary into `~/.local/bin` or `/usr/local/bin`:
   ```bash
   mv ~/Downloads/llmflow-linux ~/.local/bin/llmflow
   chmod +x ~/.local/bin/llmflow
   ```
2. Ensure `~/.local/bin` is on your PATH (`echo $PATH`).

---

## 3. Install the `llm` Package and Models

LLMFlow uses the [`llm`](https://llm.datasette.io/) package to call language models. The prebuilt binary ships with `llm` bundled, but you need to configure your API key and (optionally) install additional model plugins.

### Set your OpenAI API key

The simplest approach — store it once so `llm` uses it automatically:

```bash
llm keys set openai
# Paste key here
```

Or use an environment variable (see platform-specific steps above for how to set it permanently).

### Install additional model plugins (optional)

To use Anthropic Claude, Google Gemini, or other providers, install the corresponding plugin:

```bash
# Anthropic Claude
llm install llm-anthropic
llm keys set anthropic

# Google Gemini
llm install llm-gemini
llm keys set gemini
```

For a full list of available plugins see [llm.datasette.io/en/stable/plugins/directory.html](https://llm.datasette.io/en/stable/plugins/directory.html).

### Verify available models

```bash
llm models
```

You should see `gpt-4o`, `gpt-4o-mini`, and any plugins you installed.

---

## 4. Validate the Installation

Run the CLI from any terminal:

```bash
llmflow --version
```

You should see output similar to:

```
llmflow 0.9.0 (nuitka build 2026-02-18)
```

If the command is not found, double-check that the binary is executable and that the containing directory is on your PATH.

---

## 4. Upgrading

1. Download the latest release artifact for your OS.
2. Replace the existing binary with the new one (overwriting the file in your PATH directory).
3. Re-run `llmflow --version` to confirm the update.

---

## 5. Troubleshooting

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `zsh: permission denied` (macOS/Linux) | File not marked executable | `chmod +x /path/to/llmflow` |
| `command not found` | PATH not updated | Add directory to PATH and reopen terminal |
| Windows SmartScreen warning | App unsigned | Click "More info → Run anyway", or right-click exe → Properties → Unblock |
| `llmflow` not found after PATH change (Windows) | Old terminal still open | Close and reopen PowerShell/Command Prompt |
| Missing API credentials | Environment variable not set | `export OPENAI_API_KEY=...` (macOS/Linux) / `[System.Environment]::SetEnvironmentVariable(...)` (Windows) |

Once the CLI is on your PATH, continue with the [Quickstart Tutorial](docs/tutorial.md) to scaffold and run your first pipeline.

---

## Developing LLMFlow While Using It Elsewhere

If you are hacking on LLMFlow itself **and** maintaining other repositories that depend on it, keep the environments isolated:

1. In the LLMFlow repo, enter the Hatch-managed environment (`hatch shell`) before running tests or scripts. Install the package editable-only inside that shell (`pip install -e .`) so downstream repos can consume your live copy.
2. For each project that uses LLMFlow, create its own virtual environment (Hatch, venv, Poetry, etc.) and install the dependency there—either from PyPI (`pip install llmflow`) or via `pip install -e /path/to/LLMFlow` when you need local changes.
3. When you update the core repo, reinstall it in whichever consumer environment you’re working in so they stay in sync. This keeps dependency graphs clean and avoids “works on my machine” drift.

