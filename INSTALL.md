# Installing Scripture Pipelines

Scripture Pipelines publishes single-file executables for Windows, macOS, and Linux. No Python or package managers required.

## Quick Install (recommended)

### macOS / Linux
```bash
curl -fsSL https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.sh | bash
```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.ps1 | iex
```

After installing, run `sp --version` to confirm it worked.

Then set your API key — see [Set your API key](#set-your-api-key) below. On 0.2.1.23 and earlier this must be an **environment variable**; `sp setup` alone is not enough, because several code paths read the key straight from the environment. From 0.2.1.24 either method works.

Once the key is set, see the [Quickstart Tutorial](docs/tutorial.md) to run your first pipeline.

---

## Manual Install

**⬇️ [Download the latest release](https://github.com/nida-institute/LLMFlow/releases/latest)** — click Assets and pick the file for your platform.

> **Prerequisites**
> - An OpenAI, Anthropic, or Google Gemini API key, set as an environment variable — see [Set your API key](#set-your-api-key).
> - macOS 13+/Windows 11+/Ubuntu 22.04+ are the tested targets (other recent versions typically work, but aren’t guaranteed).

---

## 1. Download the Latest Release

1. Visit the [GitHub Releases page](https://github.com/nida-institute/LLMFlow/releases).
2. Pick the newest release tagged `Scripture Pipelines vx.y.z`.
3. Download the artifact for your platform:
   - **macOS (Universal)**: `sp-macos` (single binary)
   - **Windows (x64)**: `sp-windows.exe`
   - **Linux (x86_64)**: `sp-linux`
4. (Optional) Verify checksums listed in the release notes.

---

## 2. Install per Operating System

### macOS
1. Create a personal `bin` folder (if it doesn't exist) and move the binary there — no admin rights needed:
   ```bash
   mkdir -p ~/bin
   mv ~/Downloads/sp-macos ~/bin/sp
   chmod +x ~/bin/sp
   ```
2. Make sure `~/bin` is on your PATH. Add this line to `~/.zshrc` (or `~/.bash_profile` for older Macs) if it isn't already:
   ```bash
   export PATH="$HOME/bin:$PATH"
   ```
   Then reload your shell: `source ~/.zshrc`
3. On first launch, macOS Gatekeeper will likely block the unsigned binary:
   - Open *System Settings → Privacy & Security*.
   - Scroll to *Security* and click **Allow Anyway** next to `sp`.
   - Re-run `sp` from the terminal; when the "This app is from an unidentified developer" dialog appears, choose **Open**.

### Windows

#### Step 1 — Download

1. Go to [github.com/nida-institute/LLMFlow/releases/latest](https://github.com/nida-institute/LLMFlow/releases/latest).
2. Under **Assets**, click `sp-windows.exe` to download it.

#### Step 2 — Create a permanent home for the executable

1. Create the folder `C:\Tools\` (or any folder you prefer — just be consistent).
2. Move `sp-windows.exe` from your Downloads folder into `C:\Tools\`.
3. Rename it to `sp.exe` so the command is `sp` rather than `sp-windows`. (In PowerShell
   you will need to type `sp.exe` — see Step 6 for why.)

#### Step 3 — Add `C:\Tools\` to your PATH

This lets you run `sp` from any folder in any terminal window.

1. Press **Win + S**, type **"environment variables"**, and click **"Edit the system environment variables"**.
2. Click the **Environment Variables…** button at the bottom of the dialog.
3. In the **User variables** section (top half), find **Path** and double-click it.
4. Click **New**, type `C:\Tools\`, then click **OK** on all three dialogs.
5. **Close and reopen** any PowerShell or Command Prompt windows — existing ones won't pick up the change.

#### Step 4 — Clear the SmartScreen warning (first run only)

Because the binary is unsigned, Windows will block it on first launch:

1. Open PowerShell and run `sp --version`.
2. If you see a SmartScreen dialog saying **"Windows protected your PC"**:
   - Click **More info**.
   - Click **Run anyway**.
3. After this one-time step, `sp` runs without any dialogs.

**Alternative (no dialog):** Right-click `sp.exe` in File Explorer → **Properties** → check **Unblock** at the bottom → **OK**. Then run normally.

#### Step 5 — Set your API key

In PowerShell (persists for your user account):
```powershell
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-...", "User")
```
Close and reopen PowerShell, then confirm: `echo $env:OPENAI_API_KEY`

On 0.2.1.23 and earlier this environment variable is **required** — see
[Set your API key](#set-your-api-key) for why `sp setup` alone is not sufficient on those
versions.

#### Step 6 — Know about the `sp` name clash in PowerShell

> ⚠️ **In PowerShell, `sp` is already a built-in alias for `Set-ItemProperty`.** PowerShell
> resolves aliases before programs, so typing `sp` runs *that*, not Scripture Pipelines — usually
> producing a confusing parameter error rather than an obvious "wrong command" message.

Three ways round it, in increasing order of convenience:

1. **Use the full filename** — always works, nothing to configure:
   ```powershell
   sp.exe --version
   ```
   Aliases have no `.exe`, so the suffix reaches the real program.
2. **Use Command Prompt (`cmd`) instead of PowerShell** — it has no aliases, so plain `sp` works.
3. **Point `sp` at Scripture Pipelines in your PowerShell profile.** Run `notepad $PROFILE`
   (creating the file if prompted) and add:
   ```powershell
   Remove-Item Alias:sp -Force -ErrorAction SilentlyContinue
   Set-Alias sp "$env:USERPROFILE\bin\sp.exe"
   ```
   Open a new PowerShell window afterwards. Plain `sp` then behaves as the documentation
   elsewhere assumes. Note this removes the `Set-ItemProperty` shorthand for your sessions; the
   full cmdlet name keeps working.

This affects macOS and Linux users not at all — only PowerShell defines that alias.

#### Verify

```powershell
sp.exe --version
```

You should see the version printed, e.g. `sp 0.2.1.24`. You're ready — continue with the
[Quickstart Tutorial](docs/tutorial.md).

### Linux
1. Move the binary into `~/.local/bin` or `/usr/local/bin`:
   ```bash
   mv ~/Downloads/sp-linux ~/.local/bin/sp
   chmod +x ~/.local/bin/sp
   ```
2. Ensure `~/.local/bin` is on your PATH (`echo $PATH`).

---

## 3. Install the `llm` Package and Models

Scripture Pipelines uses the [`llm`](https://llm.datasette.io/) package to call language models. The prebuilt binary ships with `llm` bundled, but you need to configure your API key and (optionally) install additional model plugins.

### Set your API key

**Set an environment variable.** On **0.2.1.23 and earlier this is required**; from **0.2.1.24**
either method works and you can use `sp setup` instead.

Scripture Pipelines calls models two ways: through the `llm` package, and — for steps using
`response_format` (structured outputs) — through the provider's own client.

- **0.2.1.23 and earlier:** that second path reads the key **straight from the environment**, so
  `llm keys set` / `sp setup` alone is not enough — those write `llm`'s own keystore, and a
  structured-output step will still fail to authenticate.
- **0.2.1.24 onwards:** both paths resolve keys the same way — explicit key, then `llm`'s
  keystore, then the environment variable — so `sp setup` on its own is sufficient. The
  environment variable continues to work.

If you are unsure which you have, run `sp --version`. Setting the environment variable is correct
on every version, so the instructions below are always safe.

**macOS / Linux** — add to `~/.zshrc` (or `~/.bashrc`), then open a new terminal:

```bash
export OPENAI_API_KEY="sk-..."
```

**Windows (PowerShell)** — persists for your user account; close and reopen PowerShell after:

```powershell
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-...", "User")
```

Confirm it is set:

```bash
# macOS / Linux
[ -n "$OPENAI_API_KEY" ] && echo "key is set"
```
```powershell
# Windows
echo $env:OPENAI_API_KEY
```

Use `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` in place of `OPENAI_API_KEY` for those providers.

> **Keeping the key out of a plaintext config file (macOS)** — store it in the login Keychain
> once and have your shell read it, so it is not sitting in cleartext in `~/.zshrc`:
> ```bash
> security add-generic-password -a "$USER" -s OPENAI_API_KEY -w   # prompts for the value
> ```
> then in `~/.zshrc`:
> ```bash
> export OPENAI_API_KEY="$(security find-generic-password -s OPENAI_API_KEY -w 2>/dev/null)"
> ```

**About `sp setup`.** It writes the key into `llm`'s keystore (`llm keys set` under the hood).

- On **0.2.1.23 and earlier** it does **not** set the environment variable, so it does not replace
  the step above.
- From **0.2.1.24** it is sufficient on its own, and on Windows it also persists the environment
  variable for your user account.

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
sp --version
```

You should see output similar to:

```
llmflow 0.2.1.23
```

If the command is not found, double-check that the binary is executable and that the containing directory is on your PATH.

---

## 4. Upgrading

1. Download the latest release artifact for your OS.
2. Replace the existing binary with the new one (overwriting the file in your PATH directory).
3. Re-run `sp --version` to confirm the update.

---

## 5. Troubleshooting

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `zsh: permission denied` (macOS/Linux) | File not marked executable | `chmod +x /path/to/sp` |
| `command not found` | PATH not updated | Add directory to PATH and reopen terminal |
| Windows SmartScreen warning | App unsigned | Click "More info → Run anyway", or right-click exe → Properties → Unblock |
| `sp` not found after PATH change (Windows) | Old terminal still open | Close and reopen PowerShell/Command Prompt |
| `sp` gives an odd parameter error in PowerShell, e.g. about `-Path` or `-Name` | PowerShell's built-in `sp` alias for `Set-ItemProperty` ran instead | Use `sp.exe`, or override the alias — see [the `sp` name clash in PowerShell](#step-6--know-about-the-sp-name-clash-in-powershell) |
| Plugin loading message appears twice | Fixed in 0.2.1.24 | Upgrade |
| Missing API credentials | Environment variable not set | `export OPENAI_API_KEY=...` (macOS/Linux) / `[System.Environment]::SetEnvironmentVariable(...)` (Windows) |

Once the CLI is on your PATH, continue with the [Quickstart Tutorial](docs/tutorial.md) to scaffold and run your first pipeline.

---

## Developing Scripture Pipelines While Using It Elsewhere

If you are hacking on Scripture Pipelines itself **and** maintaining other repositories that depend on it, keep the environments isolated:

1. In the Scripture Pipelines repo, enter the Hatch-managed environment (`hatch shell`) before running tests or scripts. Install the package editable-only inside that shell (`pip install -e .`) so downstream repos can consume your live copy.
2. For each project that uses Scripture Pipelines, create its own virtual environment (Hatch, venv, Poetry, etc.) and install the dependency there—either from PyPI (`pip install scripture-pipelines`) or via `pip install -e /path/to/LLMFlow` when you need local changes.
3. When you update the core repo, reinstall it in whichever consumer environment you’re working in so they stay in sync. This keeps dependency graphs clean and avoids “works on my machine” drift.

