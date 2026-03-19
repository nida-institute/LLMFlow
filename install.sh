#!/usr/bin/env bash
# install.sh — LLMFlow one-line installer for macOS and Linux
#
# Acceptance criteria:
#   1. Detects OS and arch; selects correct binary from GitHub releases
#   2. Downloads to ~/bin/llmflow (no admin rights required)
#   3. Makes binary executable
#   4. Warns clearly if ~/bin is not on PATH, with exact shell fix to run
#   5. Prints post-install message pointing to `llmflow setup`
#   6. Fails loudly with a helpful message if download fails
#   7. Runs `llmflow --version` after install and confirms it exits 0
#      (catches download corruption, wrong arch, missing Gatekeeper allow, etc.)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.sh | bash
# Or:
#   wget -qO- https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.sh | bash

set -euo pipefail

REPO="nida-institute/LLMFlow"
INSTALL_DIR="$HOME/bin"
BINARY_NAME="llmflow"
API_URL="https://api.github.com/repos/${REPO}/releases/latest"

# ── Detect OS and architecture ────────────────────────────────────────────────

OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
  Darwin)
    case "$ARCH" in
      arm64)  ASSET="llmflow-macos" ;;
      x86_64) ASSET="llmflow-macos" ;;
      *)      echo "❌ Unsupported macOS architecture: $ARCH" >&2; exit 1 ;;
    esac
    ;;
  Linux)
    case "$ARCH" in
      x86_64)  ASSET="llmflow-linux"  ;;
      aarch64) ASSET="llmflow-linux" ;;
      *)        echo "❌ Unsupported Linux architecture: $ARCH" >&2; exit 1 ;;
    esac
    ;;
  *)
    echo "❌ Unsupported OS: $OS" >&2
    echo "   For Windows, run: irm https://raw.githubusercontent.com/${REPO}/main/install.ps1 | iex" >&2
    exit 1
    ;;
esac

# ── Resolve download URL from latest release ──────────────────────────────────

echo "ℹ️  Fetching latest LLMFlow release..."

if command -v curl &>/dev/null; then
  RELEASE_JSON="$(curl -fsSL "$API_URL")"
elif command -v wget &>/dev/null; then
  RELEASE_JSON="$(wget -qO- "$API_URL")"
else
  echo "❌ Neither curl nor wget is available. Please install one and retry." >&2
  exit 1
fi

# Extract download URL for our asset using grep/sed (no jq required)
DOWNLOAD_URL="$(echo "$RELEASE_JSON" \
  | grep -o '"browser_download_url": *"[^"]*'"$ASSET"'[^"]*"' \
  | head -1 \
  | sed 's/.*"browser_download_url": *"\([^"]*\)".*/\1/')"

if [[ -z "$DOWNLOAD_URL" ]]; then
  echo "❌ Could not find asset '${ASSET}' in the latest release." >&2
  echo "   Check https://github.com/${REPO}/releases/latest for available assets." >&2
  exit 1
fi

VERSION="$(echo "$RELEASE_JSON" \
  | grep -o '"tag_name": *"[^"]*"' \
  | head -1 \
  | sed 's/.*"tag_name": *"\([^"]*\)".*/\1/')"

echo "⬇️  Downloading LLMFlow ${VERSION} (${ASSET})..."

# ── Download ──────────────────────────────────────────────────────────────────

mkdir -p "$INSTALL_DIR"
DEST="${INSTALL_DIR}/${BINARY_NAME}"

if command -v curl &>/dev/null; then
  curl -fsSL --progress-bar -o "$DEST" "$DOWNLOAD_URL"
else
  wget -q --show-progress -O "$DEST" "$DOWNLOAD_URL"
fi

chmod +x "$DEST"

echo "✅ Installed to ${DEST}"

# ── PATH check ────────────────────────────────────────────────────────────────

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
  echo ""
  echo "⚠️  ${INSTALL_DIR} is not on your PATH."
  echo "   Add this line to your shell config (~/.zshrc or ~/.bashrc):"
  echo ""
  echo "     export PATH=\"\$HOME/bin:\$PATH\""
  echo ""
  echo "   Then reload: source ~/.zshrc   (or open a new terminal)"
else
  echo ""
fi

# ── macOS Gatekeeper notice ───────────────────────────────────────────────────

if [[ "$OS" == "Darwin" ]]; then
  echo "ℹ️  macOS Gatekeeper: on first run you may see a security warning."
  echo "   If so: System Settings → Privacy & Security → Allow Anyway, then run again."
  echo ""
fi

# ── Done ──────────────────────────────────────────────────────────────────────

# ── Verify the binary runs ───────────────────────────────────────────────────

if "$DEST" --version &>/dev/null; then
  VERSION_OUT="$("$DEST" --version 2>&1)"
  echo "✅ Verified: ${VERSION_OUT}"
else
  echo "⚠️  The binary was installed but 'llmflow --version' failed."
  if [[ "$OS" == "Darwin" ]]; then
    echo "   This is usually a macOS Gatekeeper block."
    echo "   Go to System Settings → Privacy & Security → Allow Anyway, then re-run."
  else
    echo "   Check that the file is not corrupted: file ${DEST}"
  fi
  echo ""
fi

echo "🎉 LLMFlow is installed! Next step:"
echo ""
echo "   llmflow setup"
echo ""
echo "   This will walk you through configuring your API key for OpenAI,"
echo "   Anthropic, or Google Gemini."
