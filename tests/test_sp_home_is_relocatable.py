"""Guardrail: `$SP_HOME` decides where the store lives, and one function decides that.

Captain, 2026-08-25, on isolating the test suite from the real store: *"just a dummy ~/.sp is
sufficient, no?"* — yes, and narrower than the alternative. An earlier attempt redirected `HOME`
for the whole suite, which works but reaches far past the store: two test files locate the Human
at the Helm clone under `~/github/` and *skip* when it is absent, so redirecting `HOME` beneath
them would have turned two real guards green while they checked nothing.

`$SP_HOME` touches only the store. It also earns its keep outside the tests: a container, a CI
runner, or a machine where the store belongs somewhere other than the home directory.

Before this, eleven call sites across four modules each wrote `Path.home() / ".sp"` — eleven
encodings of one fact, which is the defect rule 29 names. Now they ask `sp_home()`.
"""
from pathlib import Path

from llmflow.paths import sp_home


def test_defaults_to_the_home_directory(monkeypatch):
    monkeypatch.delenv("SP_HOME", raising=False)
    assert sp_home() == Path.home() / ".sp"


def test_sp_home_overrides_it(monkeypatch, tmp_path):
    monkeypatch.setenv("SP_HOME", str(tmp_path / "elsewhere"))
    assert sp_home() == tmp_path / "elsewhere"


def test_it_expands_a_tilde(monkeypatch):
    monkeypatch.setenv("SP_HOME", "~/somewhere-else")
    assert sp_home() == Path.home() / "somewhere-else"


def test_no_module_resolves_the_store_on_its_own(monkeypatch, tmp_path):
    """The point of the resolver: nothing may compute the path independently, or `$SP_HOME`
    would move the store for some code and not others."""
    import subprocess

    src = Path(__file__).resolve().parent.parent / "src" / "llmflow"
    hits = subprocess.run(
        ["grep", "-rn", '--include=*.py', 'home() / "\\.sp"', str(src)],
        capture_output=True, text=True,
    ).stdout.strip()
    hits = [h for h in hits.splitlines() if "paths.py" not in h]
    assert not hits, (
        "These compute the store path directly instead of calling `sp_home()`:\n  "
        + "\n  ".join(hits)
    )
