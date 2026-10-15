#!/usr/bin/env bash
# install.sh — Scripture Pipelines one-line installer for macOS and Linux
#
# Acceptance criteria:
#   1. Detects OS and arch; selects correct binary from GitHub releases
#   2. Downloads to ~/bin/sp (no admin rights required)
#   3. Makes binary executable
#   4. Warns clearly if ~/bin is not on PATH, with exact shell fix to run
#   5. Prints post-install message pointing to `sp setup`
#   6. Fails loudly with a helpful message if download fails
#   7. Runs `sp --version` after install and confirms it exits 0
#      (catches download corruption, wrong arch, missing Gatekeeper allow, etc.)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.sh | bash
# Or:
#   wget -qO- https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.sh | bash

set -euo pipefail

REPO="nida-institute/LLMFlow"
INSTALL_DIR="$HOME/bin"
BINARY_NAME="sp"
# The web routes, not GitHub's API: the API allows 60 unauthenticated requests an hour per
# address, and a shared address — a CI runner, an office, a VPN — can be over it already (#270).
RELEASES_URL="https://github.com/${REPO}/releases"

# ── Detect OS and architecture ────────────────────────────────────────────────

OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
  Darwin)
    case "$ARCH" in
      arm64)  ASSET="sp-macos" ;;
      x86_64) ASSET="sp-macos" ;;
      *)      echo "❌ Unsupported macOS architecture: $ARCH" >&2; exit 1 ;;
    esac
    ;;
  Linux)
    case "$ARCH" in
      x86_64)  ASSET="sp-linux"  ;;
      aarch64) ASSET="sp-linux" ;;
      *)        echo "❌ Unsupported Linux architecture: $ARCH" >&2; exit 1 ;;
    esac
    ;;
  *)
    echo "❌ Unsupported OS: $OS" >&2
    echo "   For Windows, run: irm https://raw.githubusercontent.com/${REPO}/main/install.ps1 | iex" >&2
    exit 1
    ;;
esac

# ── Requests ──────────────────────────────────────────────────────────────────

if ! command -v curl &>/dev/null && ! command -v wget &>/dev/null; then
  echo "❌ Neither curl nor wget is available. Please install one and retry." >&2
  exit 1
fi

RESPONSE="$(mktemp)"
trap 'rm -f "$RESPONSE"' EXIT

# request URL OUTFILE FOLLOW — prints "STATUS LOCATION". FOLLOW is "yes" to follow redirects.
# The response body is written to OUTFILE whatever the status, so a failure can be shown.
request() {
  local url="$1" out="$2" follow="$3"
  if command -v curl &>/dev/null; then
    if [[ "$follow" == "yes" ]]; then
      curl -sS -L -o "$out" -w '%{http_code} %{redirect_url}' "$url" || true
    else
      curl -sS -o "$out" -w '%{http_code} %{redirect_url}' "$url" || true
    fi
  else
    local headers status location
    if [[ "$follow" == "yes" ]]; then
      headers="$(wget -S -O "$out" "$url" 2>&1 || true)"
    else
      headers="$(wget -S --max-redirect=0 -O "$out" "$url" 2>&1 || true)"
    fi
    status="$(printf '%s\n' "$headers" | grep -o 'HTTP/[0-9.]* [0-9]*' | tail -1 | awk '{print $2}')"
    location="$(printf '%s\n' "$headers" | grep -i '^ *Location:' | tail -1 | awk '{print $2}' | tr -d '\r')"
    printf '%s %s' "${status:-000}" "$location"
  fi
}

# refused WHAT STATUS FILE — says what was refused, with GitHub's own answer, and stops.
refused() {
  echo "❌ $1 failed: HTTP $2." >&2
  if [[ -s "$3" ]]; then
    echo "   GitHub answered:" >&2
    head -c 2000 "$3" >&2
    echo "" >&2
  fi
  echo "   Check https://github.com/${REPO}/releases/latest, or retry in a few minutes." >&2
  exit 1
}

# ── The latest release's tag, from where /releases/latest redirects ───────────

echo "ℹ️  Fetching latest Scripture Pipelines release..."

read -r STATUS LOCATION <<< "$(request "${RELEASES_URL}/latest" "$RESPONSE" no)"
if [[ "$STATUS" != 3* || "$LOCATION" != */releases/tag/* ]]; then
  refused "Finding the latest release" "${STATUS:-000}" "$RESPONSE"
fi
VERSION="${LOCATION##*/releases/tag/}"

# ── Download that tag's binary ────────────────────────────────────────────────

echo "⬇️  Downloading Scripture Pipelines ${VERSION} (${ASSET})..."

mkdir -p "$INSTALL_DIR"
DEST="${INSTALL_DIR}/${BINARY_NAME}"
DOWNLOAD_URL="${RELEASES_URL}/download/${VERSION}/${ASSET}"

read -r STATUS _ <<< "$(request "$DOWNLOAD_URL" "$DEST" yes)"
if [[ "$STATUS" != 2* ]]; then
  cp "$DEST" "$RESPONSE" 2>/dev/null || true
  rm -f "$DEST"
  refused "Downloading ${DOWNLOAD_URL}" "${STATUS:-000}" "$RESPONSE"
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
  echo "⚠️  The binary was installed but 'sp --version' failed."
  if [[ "$OS" == "Darwin" ]]; then
    echo "   This is usually a macOS Gatekeeper block."
    echo "   Go to System Settings → Privacy & Security → Allow Anyway, then re-run."
  else
    echo "   Check that the file is not corrupted: file ${DEST}"
  fi
  echo ""
fi

echo "🎉 Scripture Pipelines is installed! Next step:"
echo ""
echo "   sp setup"
echo ""
echo "   This will walk you through configuring your API key for OpenAI,"
echo "   Anthropic, or Google Gemini."
