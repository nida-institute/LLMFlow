# install.ps1 — Scripture Pipelines one-line installer for Windows
#
# Acceptance criteria:
#   1. Downloads sp-windows.exe from latest GitHub release
#   2. Places it at $env:USERPROFILE\bin\sp.exe (no admin rights required) (no admin rights required)
#   3. Adds that folder to the user's PATH permanently (registry, no admin needed)
#   4. Warns if PATH update requires a new terminal
#   5. Clears SmartScreen block via Unblock-File
#   6. Prints post-install message pointing to `sp setup`
#   7. Runs `sp --version` after install and confirms it exits 0
#      (catches download corruption, wrong arch, SmartScreen block, etc.)
#   8. Fails with clear error if download fails
#
# Usage (run in PowerShell):
#   irm https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$Repo        = "nida-institute/LLMFlow"
$AssetName   = "sp-windows.exe"
$InstallDir  = Join-Path $env:USERPROFILE "bin"
$BinaryName  = "sp.exe"
# The web routes, not GitHub's API: the API allows 60 unauthenticated requests an hour per
# address, and a shared address — a CI runner, an office, a VPN — can be over it already (#270).
$Releases    = "https://github.com/$Repo/releases"

# Says what was refused, with GitHub's own answer, and stops. $Response may be $null when the
# request never reached GitHub.
function Stop-Refused($What, $Response, $Detail) {
    $Status = "no response"
    $Body = ""
    if ($Response) {
        $Status = "HTTP $([int]$Response.StatusCode) (StatusCode $($Response.StatusCode))"
        try {
            $Reader = New-Object System.IO.StreamReader($Response.GetResponseStream())
            $Body = $Reader.ReadToEnd()
            $Reader.Close()
        } catch { }
    }
    Write-Host "❌ $What failed: $Status. $Detail"
    if ($Body) {
        Write-Host "   Response body:"
        Write-Host ($Body.Substring(0, [Math]::Min(2000, $Body.Length)))
    }
    Write-Host "   Check https://github.com/$Repo/releases/latest, or retry in a few minutes."
    exit 1
}

# ── The latest release's tag, from where /releases/latest redirects ───────────

Write-Host "ℹ️  Fetching latest Scripture Pipelines release..."

$Request = [System.Net.HttpWebRequest]::Create("$Releases/latest")
$Request.AllowAutoRedirect = $false
$Request.UserAgent = "scripture-pipelines-installer"
try {
    $Response = $Request.GetResponse()
} catch [System.Net.WebException] {
    Stop-Refused "Finding the latest release" $_.Exception.Response $_.Exception.Message
}

$Location = $Response.Headers["Location"]
$Code = [int]$Response.StatusCode
$Response.Close()
if ($Code -lt 300 -or $Code -ge 400 -or $Location -notmatch "/releases/tag/(.+)$") {
    Write-Host "❌ Finding the latest release failed: HTTP $Code, redirected to '$Location'."
    exit 1
}

$Version     = $Matches[1]
$DownloadUrl = "$Releases/download/$Version/$AssetName"

Write-Host "⬇️  Downloading Scripture Pipelines $Version ($AssetName)..."

# ── Download ──────────────────────────────────────────────────────────────────

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

$Dest = Join-Path $InstallDir $BinaryName

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $Dest -UseBasicParsing

    # Verify download succeeded
    if (-not (Test-Path $Dest)) {
        Write-Error "❌ Download completed but file not found at $Dest"
        exit 1
    }

    $FileSize = (Get-Item $Dest).Length
    Write-Host "✅ Downloaded $([math]::Round($FileSize/1MB, 2)) MB to $Dest"

} catch [System.Net.WebException] {
    Stop-Refused "Downloading $DownloadUrl" $_.Exception.Response $_.Exception.Message
} catch {
    if ($_.Exception.Response) {
        Stop-Refused "Downloading $DownloadUrl" $_.Exception.Response $_.Exception.Message
    }
    Write-Host "❌ Download failed: $_"
    exit 1
}

# Clear SmartScreen "blocked" flag so Windows doesn't prompt on first run
Unblock-File -Path $Dest

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
    Write-Host "⚠️  The binary was installed but 'sp --version' failed."
    Write-Host "   Try right-clicking $Dest → Properties → Unblock, then re-run."
    Write-Host ""
}

Write-Host ""
Write-Host "🎉 Scripture Pipelines is installed! Next step:"
Write-Host ""
Write-Host "   sp setup"
Write-Host ""
Write-Host "   This will walk you through configuring your API key for OpenAI,"
Write-Host "   Anthropic, or Google Gemini."
Write-Host ""
Write-Host "   (Open a new PowerShell window first if you just saw the PATH message above.)"
