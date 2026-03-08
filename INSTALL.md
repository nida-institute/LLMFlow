# Installing LLMFlow (Prebuilt Executables)

LLMFlow publishes single-file executables for Windows, macOS, and Linux via Nuitka. Follow the steps below to install the CLI without cloning the repo or managing Python environments manually.

> **Prerequisites**
> - An OpenAI-compatible API key exported as `OPENAI_API_KEY` (or provider-specific equivalents).
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
1. Move the binary into a directory on your PATH, e.g.:
   ```bash
   mv ~/Downloads/llmflow-macos /usr/local/bin/llmflow
   chmod +x /usr/local/bin/llmflow
   ```
2. On first launch, macOS Gatekeeper will likely block the unsigned binary:
   - Open *System Settings → Privacy & Security*.
   - Scroll to *Security* and click **Allow Anyway** next to `llmflow` (screenshot recommended here for docs/website).
   - Re-run `llmflow` from the terminal; when the "This app is from an unidentified developer" dialog appears, choose **Open**.

### Windows
1. Place `llmflow-windows.exe` somewhere convenient (e.g., `C:\Tools\llmflow.exe`).
2. Add that folder to the *System PATH* (System Properties → Environment Variables).
3. The first launch triggers Microsoft Defender SmartScreen:
   - Double-click the executable; when the *Windows protected your PC* dialog shows, click **More info**.
   - Press **Run anyway** to proceed (capture this dialog in a screenshot for user docs if possible).
4. Re-open PowerShell or Command Prompt and confirm `llmflow` runs.

### Linux
1. Move the binary into `~/.local/bin` or `/usr/local/bin`:
   ```bash
   mv ~/Downloads/llmflow-linux ~/.local/bin/llmflow
   chmod +x ~/.local/bin/llmflow
   ```
2. Ensure `~/.local/bin` is on your PATH (`echo $PATH`).

---

## 3. Validate the Installation

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
| Windows SmartScreen warning | App unsigned | Choose “More info → Run anyway” (or unblock in properties) |
| Missing API credentials | Environment variable not set | `export OPENAI_API_KEY=...` (macOS/Linux) / `setx OPENAI_API_KEY ...` (Windows) |

Once the CLI is on your PATH, continue with the [Quickstart Tutorial](docs/tutorial.md) to scaffold and run your first pipeline.

---

## Developing LLMFlow While Using It Elsewhere

If you are hacking on LLMFlow itself **and** maintaining other repositories that depend on it, keep the environments isolated:

1. In the LLMFlow repo, enter the Hatch-managed environment (`hatch shell`) before running tests or scripts. Install the package editable-only inside that shell (`pip install -e .`) so downstream repos can consume your live copy.
2. For each project that uses LLMFlow, create its own virtual environment (Hatch, venv, Poetry, etc.) and install the dependency there—either from PyPI (`pip install llmflow`) or via `pip install -e /path/to/LLMFlow` when you need local changes.
3. When you update the core repo, reinstall it in whichever consumer environment you’re working in so they stay in sync. This keeps dependency graphs clean and avoids “works on my machine” drift.

