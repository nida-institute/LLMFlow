"""The one-line installers find the latest release without GitHub's API (#270).

The API allows 60 unauthenticated requests an hour per address, and a shared address — a CI
runner, an office, a VPN — can be over it before the script starts. The web routes are not limited
the same way: `releases/latest` redirects to the newest tag, and `releases/download/<tag>/<asset>`
is the binary. When a request fails, the script prints the status and the response, so a failure
says why.

`install.sh` is run here against a stand-in `curl`, first on `PATH`, that answers by URL and logs
every call, so nothing reaches the network. `install.ps1` cannot be run without PowerShell, so it
is read. Neither replaces `release.yml`'s `verify-install`, which runs both against a real release.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "install.sh"
INSTALL_PS1 = REPO_ROOT / "install.ps1"
RELEASES = "https://github.com/nida-institute/LLMFlow/releases"
TAG = "v9.9.9"
RATE_LIMITED = "API rate limit exceeded for 203.0.113.7"

#: Answers `curl -sS [-L] -o FILE -w FORMAT URL` the way GitHub would, by URL. `STUB_FAIL` names a
#: URL fragment to answer with 403 and a body instead.
STUB = """import os, sys
args = sys.argv[1:]
with open(os.environ["STUB_LOG"], "a", encoding="utf-8") as log:
    log.write(" ".join(args) + "\\n")
url = args[-1]
out = args[args.index("-o") + 1] if "-o" in args else None
fail = os.environ.get("STUB_FAIL")
def body(text):
    if out and out != "/dev/null":
        with open(out, "w", encoding="utf-8") as handle:
            handle.write(text)
if fail and fail in url:
    body('{{"message": "{rate_limited}"}}')
    sys.stdout.write("403 ")
elif url.endswith("/releases/latest"):
    body("")
    sys.stdout.write("302 {releases}/tag/{tag}")
elif "/releases/download/{tag}/" in url:
    body("#!/bin/sh\\necho 'sp 9.9.9'\\n")
    sys.stdout.write("200 ")
else:
    body("Not Found")
    sys.stdout.write("404 ")
"""

needs_bash = pytest.mark.skipif(shutil.which("bash") is None, reason="install.sh needs bash")


def run_install(tmp_path: Path, fail: str | None = None) -> tuple:
    """`(completed process, logged curl calls)` for one run of install.sh against the stand-in."""
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    answers = stubs / "curl_answers.py"
    answers.write_text(
        STUB.format(releases=RELEASES, tag=TAG, rate_limited=RATE_LIMITED), encoding="utf-8"
    )
    # A wrapper, not a `#!` naming Python: the interpreter's path may hold a space, which a `#!`
    # line cannot.
    curl = stubs / "curl"
    curl.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{answers}" "$@"\n', encoding="utf-8")
    curl.chmod(0o755)
    log = tmp_path / "curl.log"
    log.write_text("", encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    env = {
        **os.environ,
        "PATH": f"{stubs}{os.pathsep}{os.environ['PATH']}",
        "HOME": str(home),
        "STUB_LOG": str(log),
    }
    if fail:
        env["STUB_FAIL"] = fail
    done = subprocess.run(
        ["bash", str(INSTALL_SH)], env=env, capture_output=True, text=True, timeout=60
    )
    return done, log.read_text(encoding="utf-8").splitlines()


@needs_bash
class TestInstallSh:
    def test_installs_the_binary_and_reports_the_redirect_s_version(self, tmp_path):
        done, _ = run_install(tmp_path)
        assert done.returncode == 0, done.stderr
        assert (tmp_path / "home" / "bin" / "sp").is_file()
        assert TAG in done.stdout

    def test_never_asks_the_api(self, tmp_path):
        _, calls = run_install(tmp_path)
        assert calls, "the stand-in curl was never called"
        assert not [call for call in calls if "api.github.com" in call]

    def test_downloads_the_tag_it_reported(self, tmp_path):
        """Pinned to the tag, so a release published mid-install cannot change what is fetched."""
        _, calls = run_install(tmp_path)
        assert any(f"{RELEASES}/download/{TAG}/sp-" in call for call in calls), calls

    @pytest.mark.parametrize("fail", ["/releases/latest", f"/releases/download/{TAG}/"])
    def test_a_refused_request_prints_its_status_and_response(self, tmp_path, fail):
        done, _ = run_install(tmp_path, fail=fail)
        assert done.returncode != 0
        assert "403" in done.stderr
        assert RATE_LIMITED in done.stderr


class TestInstallPs1:
    """Read, not run: PowerShell is not on every machine the suite runs on."""

    def test_never_asks_the_api(self):
        assert "api.github.com" not in INSTALL_PS1.read_text(encoding="utf-8")

    def test_finds_the_tag_by_the_latest_release_redirect(self):
        """The redirect is read, not followed, and the download is pinned to the tag it names."""
        text = INSTALL_PS1.read_text(encoding="utf-8")
        assert "AllowAutoRedirect = $false" in text
        assert '"$Releases/latest"' in text
        assert "/releases/tag/" in text
        assert '"$Releases/download/$Version/$AssetName"' in text

    def test_a_refused_request_prints_its_status_and_response(self):
        text = INSTALL_PS1.read_text(encoding="utf-8")
        assert "StatusCode" in text and "Response body" in text
