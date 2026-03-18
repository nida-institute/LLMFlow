# Project TODO

> **Convention:** Active work lives here. Bugs and permanent decisions go to
> [GitHub Issues](https://github.com/nida-institute/LLMFlow/issues).
> Link issues with `→ #N` so this file doesn't duplicate GitHub.
> Board: https://github.com/orgs/nida-institute/projects/13

## 🔥 Active

### 🎓 Workshop readiness (main next goal)
- [ ] Build Mac + Windows installers via GitHub Actions CI → #32
  - PyInstaller spec already exists (`llmflow.spec`)
  - Trigger: push a version tag `v*` → auto-publish to GitHub Releases
  - Install script renames binary to `llmflow` (no manual rename needed):
    ```bash
    curl -fsSL .../llmflow-macos -o ~/bin/llmflow && chmod +x ~/bin/llmflow
    ```
- [ ] Implement `llmflow setup` command (per-machine, run once after install) → #32
  - Silently installs `llm` plugins (e.g. `llm install llm-gpt4all`)
  - Prompts user for OpenAI API key (`llm keys set openai`)
  - `llmflow setup --update` re-runs (update plugins, change key)
- [ ] **Naming convention locked:** `--update` is always a flag on its parent command, never a standalone subcommand
  - `llmflow init --update` — refresh generated project docs
  - `llmflow setup --update` — update plugins / change API key
  - No bare `llmflow update` command (use install script or `brew upgrade` to update binary)

## 📋 Backlog

### 🎓 Workshop readiness
- [ ] Replace hello-world example with a domain-relevant pipeline
      (e.g. translation notes for a Bible passage, or back-translation check)
- [ ] Polish error messages — every ❌ should say what to fix, not just what went wrong
- [ ] Workshop handout: 1-page "what is this and why do I care"
- [ ] API key story for workshop: shared org key so participants don't each need one

### 🚀 Publishing
- [ ] Clean up repo for public release (remove private data, audit history)
- [ ] Publish to PyPI as `llmflow` (name is currently available)

### 🔧 Open issues on board
- [ ] Bootstrap New Project UX improvements → #28
- [ ] Conditionals and switches → #11
- [ ] Checkpointing support → #8

## ✅ Done

---
_Audit notes and QA reports → project/audits/_
_Pipeline decisions → project/decisions.md (create when needed)_
_Project board → https://github.com/orgs/nida-institute/projects/13_
