import os
import shutil
import tempfile
from pathlib import Path

import pytest

from llmflow.cli_utils import _unlock_sp_dir

REPO_ROOT = Path(__file__).resolve().parent.parent


#: The engine's own unlock, aliased rather than reimplemented — the inverse of `_lock_sp_dir`.
_unlock_tree = _unlock_sp_dir


def _empty_tree(path: Path) -> None:
    """Remove entries named with `tempfile`'s prefix from `path`; leave everything else (#207)."""
    if not path.is_dir():
        return
    prefix = tempfile.gettempprefix()
    for child in path.iterdir():
        if not child.name.startswith(prefix):
            continue  # a third-party cache lives here too; not this suite's to delete
        _unlock_tree(child)
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child, ignore_errors=True)
        else:
            try:
                child.unlink()
            except OSError:
                pass


def pytest_configure(config) -> None:
    """Anchor pytest's basetemp and `tempfile` inside the repository, and print where (#207)."""
    given = config.option.basetemp
    basetemp = Path(given) if given else REPO_ROOT / "tmp" / "pytest"
    if not basetemp.is_absolute():
        basetemp = REPO_ROOT / basetemp
    config.option.basetemp = str(basetemp)
    _unlock_tree(basetemp)

    loose = basetemp.parent / f"{basetemp.name}-tempfile"
    loose.mkdir(parents=True, exist_ok=True)
    _empty_tree(loose)
    tempfile.tempdir = str(loose)
    for var in ("TMPDIR", "TEMP", "TMP"):
        os.environ[var] = str(loose)

    rel = basetemp.parent.relative_to(REPO_ROOT)
    print(
        f"\npytest intermediates: {rel}/{basetemp.name}/ (per-test) and "
        f"{rel}/{loose.name}/ (tempfile) — inside the repo, git-ignored, "
        "failures kept until the next run."
    )


@pytest.fixture(autouse=True)
def _cwd_is_restored():
    """Fail the test that leaves the process somewhere else (#207).

    A test that changes directory and does not change back makes every later test write
    relative paths into that directory — which is how `llmflow.log` kept appearing in
    `/private/tmp`, outside the repository, on every run.
    """
    before = os.getcwd()
    yield
    after = os.getcwd()
    if after != before:
        os.chdir(before)
        raise AssertionError(
            f"this test left the working directory at {after}, not {before}. "
            "Use the `monkeypatch.chdir` fixture, or restore it in a finally block."
        )


@pytest.fixture(autouse=True)
def _tmp_path_can_be_removed(tmp_path):
    """Unlock a test's own directory so `tmp_path_retention_policy = failed` can delete it.

    Teardown ordering does the work: `tmp_path` is set up as this fixture's dependency, so its
    finalizer — the one that removes the directory when the test passed — runs *after* this one.
    Without the unlock, that removal hits the same read-only store and leaves the directory
    behind, which is the accumulation this change exists to stop.
    """
    yield
    _unlock_tree(tmp_path)


@pytest.fixture
def temp_prompt_file(tmp_path):
    """Create a temporary prompt file for testing"""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(exist_ok=True)

    prompt_file = prompts_dir / "test.gpt"
    prompt_file.write_text("Test prompt: ${item}")

    return str(prompts_dir)


@pytest.fixture(scope="session", autouse=True)
def _tidy_debug_dirs_left_by_tests():
    """Remove the `outputs/debug/tmp*` directories the suite creates in the repo.

    `utils/debug._get_debug_dir` falls back to `cwd/outputs/debug/<pipeline_name>`, and
    tests feed it pipelines written to `tempfile` paths — so each run leaves a dozen
    directories named after temp files (`tmp0_piyndf`, …). They are empty, they are never
    read again, and nothing else collects them: `sp clean` needs `--pipeline`, so it only
    cleans a named pipeline's output. Left alone they accumulate indefinitely; 976 of them
    had built up before this fixture existed.

    Deliberately conservative — it removes a directory only when **all** of these hold:
      * it sits directly under `outputs/debug/`
      * its name starts with `tmp` (the tempfile prefix)
      * it is empty
    So real debug output, which is named after a real pipeline and contains request and
    response dumps, is never touched.
    """
    yield

    debug_root = Path.cwd() / "outputs" / "debug"
    if not debug_root.is_dir():
        return
    for path in debug_root.iterdir():
        if not path.is_dir() or not path.name.startswith("tmp"):
            continue
        try:
            path.rmdir()  # only succeeds when empty — the safety check is the syscall
        except OSError:
            pass  # not empty, or vanished: leave it alone


# ---------------------------------------------------------------------------
# A dummy store for the whole suite (#207)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _dummy_sp_home(tmp_path_factory) -> Path:
    """One throwaway store for the session, not one per test.

    Per-test would be cleaner in principle and slow in practice: every `sp init` installs 12
    disciplines and 10 skills, so a fresh store per test re-copies all of it. Sharing is safe
    now that the installers compare content before writing — the second install is a no-op.
    """
    return tmp_path_factory.mktemp("home") / ".sp"


@pytest.fixture(autouse=True)
def _store_is_disposable(monkeypatch, _dummy_sp_home):
    """Point `$SP_HOME` at a throwaway directory for every test (#207).

    The suite wrote to the real `~/.sp`: `sp init` installs disciplines and skills over the
    store, and every init test registered its pytest temp directory as a permanent project. The
    Captain cleaned 18 junk registrations out of `~/.sp/projects/` on 2026-08-24 and test runs
    the same day recreated 16 of them. Idempotence cannot help — each temp directory is a
    genuinely new project, correctly registered — so the store has to move.

    **`$SP_HOME`, not `$HOME`.** Redirecting the home directory also works and reaches far past
    the store: `test_helm_sync` and `test_shortname_is_helm` locate the Human at the Helm clone
    under `~/github/` and *skip* when it is absent, so moving `HOME` beneath them would turn two
    real guards green while they checked nothing. Moving the store alone leaves them working and
    needs no opt-out.

    It moves inside the test process deliberately. `SP_HOME=... hatch run pytest` would work for
    the store too, but the `HOME` variant of this idea rebuilds the whole 511 MB hatch
    environment, because hatch keys its environment on `HOME`.
    """
    monkeypatch.setenv("SP_HOME", str(_dummy_sp_home))


@pytest.fixture(scope="session", autouse=True)
def _the_real_store_is_left_alone():
    """Fail the run if the suite wrote into the machine's real `~/.sp` (#207).

    `_store_is_disposable` redirects `$SP_HOME` so tests cannot reach the real store. This is
    the check that it worked, because the failure it guards against is silent: a test that
    slips past the fixture leaves a registration behind and nothing says so. Seventeen
    accumulated that way, each pointing at a pytest temp directory deleted seconds later, and
    they were found by reading the store rather than by anything failing.

    Deliberately not a user-facing cleanup command. The Captain: *"don't introduce a user
    command because our test suite is buggy."* The cost of a test-suite defect belongs in the
    test suite.

    Compares only the set of names. It never writes to the store, and it does not care what a
    real project's registration contains — only that the suite added nothing.
    """
    real = Path(os.path.expanduser("~")) / ".sp" / "projects"
    before = {p.name for p in real.glob("*.yaml")} if real.is_dir() else set()

    yield

    after = {p.name for p in real.glob("*.yaml")} if real.is_dir() else set()
    added = sorted(after - before)
    assert not added, (
        "The suite wrote these into the real ~/.sp/projects/:\n  "
        + "\n  ".join(added)
        + "\nA test reached past `$SP_HOME`. Set it, or use the `_dummy_sp_home` fixture."
    )
