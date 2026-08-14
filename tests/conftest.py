import pytest
from pathlib import Path


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
