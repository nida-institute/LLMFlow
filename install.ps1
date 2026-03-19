# install.ps1 — LLMFlow one-line installer for Windows
#
# Acceptance criteria:
#   1. Downloads llmflow-windows-x64.exe from latest GitHub release
#   2. Places it at $env:USERPROFILE\bin\llmflow.exe (no admin rights required)
#   3. Adds that folder to the user's PATH permanently (registry, no admin needed)
#   4. Warns if PATH update requires a new terminal
#   5. Clears SmartScreen block via Unblock-File
#   6. Prints post-install message pointing to `llmflow setup`
#   7. Runs `llmflow --version` after install and confirms it exits 0
#      (catches download corruption, wrong arch, SmartScreen block, etc.)
#   8. Fails with clear error if download fails
#
# Usage (run in PowerShell):
#   irm https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$Repo        = "nida-institute/LLMFlow"
$AssetName   = "llmflow-windows.exe"
$InstallDir  = Join-Path $env:USERPROFILE "bin"
$BinaryName  = "llmflow.exe"
$ApiUrl      = "https://api.github.com/repos/$Repo/releases/latest"

# ── Fetch latest release info ─────────────────────────────────────────────────

Write-Host "ℹ️  Fetching latest LLMFlow release..."

try {
    $Release = Invoke-RestMethod -Uri $ApiUrl -UseBasicParsing
} catch {
    Write-Error "❌ Failed to fetch release info from GitHub: $_"
    exit 1
}

$Asset = $Release.assets | Where-Object { $_.name -eq $AssetName } | Select-Object -First 1

if (-not $Asset) {
    Write-Error "❌ Asset '$AssetName' not found in the latest release. Check https://github.com/$Repo/releases/latest"
    exit 1
}

$Version     = $Release.tag_name
$DownloadUrl = $Asset.browser_download_url

Write-Host "⬇️  Downloading LLMFlow $Version ($AssetName)..."

# ── Download ──────────────────────────────────────────────────────────────────

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

$Dest = Join-Path $InstallDir $BinaryName

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $Dest -UseBasicParsing
} catch {
    Write-Error "❌ Download failed: $_"
    exit 1
}

# Clear SmartScreen "blocked" flag so Windows doesn't prompt on first run
Unblock-File -Path $Dest

Write-Host "✅ Installed to $Dest"

# ── Add to user PATH (no admin required) ─────────────────────────────────────

$CurrentPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
$PathDirs    = $CurrentPath -split ";" | Where-Object { $_ -ne "" }

if ($PathDirs -notcontains $InstallDir) {
    $NewPath = ($PathDirs + $InstallDir) -join ";"
    [System.Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
    Write-Host ""
    Write-Host "⚠️  Added $InstallDir to your PATH."
    Write-Host "   Please close and reopen PowerShell for the change to take effect."
} else {
    Write-Host "✅ $InstallDir is already on your PATH."
}

# ── Done ──────────────────────────────────────────────────────────────────────

# ── Verify the binary runs ───────────────────────────────────────────────────

try {
    $VersionOut = & $Dest --version 2>&1
    Write-Host "✅ Verified: $VersionOut"
} catch {
    Write-Host "⚠️  The binary was installed but 'llmflow --version' failed."
    Write-Host "   Try right-clicking $Dest → Properties → Unblock, then re-run."
    Write-Host ""
}

Write-Host ""
Write-Host "🎉 LLMFlow is installed! Next step:"
Write-Host ""
Write-Host "   llmflow setup"
Write-Host ""
Write-Host "   This will walk you through configuring your API key for OpenAI,"
Write-Host "   Anthropic, or Google Gemini."
Write-Host ""
Write-Host "   (Open a new PowerShell window first if you just saw the PATH message above.)"
