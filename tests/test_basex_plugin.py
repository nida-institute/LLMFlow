"""Tests for basex plugin — inputs: block → -b flag binding (issue #71)."""
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


def _make_completed(returncode=0, stdout="<results/>", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


# ---------------------------------------------------------------------------
# run_basex — -b flag binding via inputs dict
# ---------------------------------------------------------------------------

def test_no_inputs_no_b_flags(tmp_path):
    """With no inputs, basex is called with just the query file."""
    qfile = tmp_path / "q.xq"
    qfile.write_text("count(//verse)")

    ok = _make_completed(stdout="42")
    with patch("llmflow.plugins.basex.subprocess.run", return_value=ok) as mock_run:
        from llmflow.plugins.basex import run_basex
        result = run_basex(str(qfile))

    cmd = mock_run.call_args[0][0]
    assert cmd == ["basex", str(qfile)]
    assert result == "42"


def test_inputs_become_b_flags(tmp_path):
    """Each inputs key becomes a -b<key>=<value> argument before the file."""
    qfile = tmp_path / "q.xq"
    qfile.write_text("declare variable $lemma external; $lemma")

    ok = _make_completed(stdout="הָיָה")
    with patch("llmflow.plugins.basex.subprocess.run", return_value=ok) as mock_run:
        from llmflow.plugins.basex import run_basex
        result = run_basex(str(qfile), inputs={"lemma": "הָיָה"})

    cmd = mock_run.call_args[0][0]
    assert "-blemma=הָיָה" in cmd
    assert cmd[-1] == str(qfile)   # file always last
    assert result == "הָיָה"


def test_multiple_inputs_all_become_b_flags(tmp_path):
    """Multiple inputs all appear as -b flags."""
    qfile = tmp_path / "q.xq"
    qfile.write_text(".")

    ok = _make_completed(stdout="ok")
    with patch("llmflow.plugins.basex.subprocess.run", return_value=ok) as mock_run:
        from llmflow.plugins.basex import run_basex
        run_basex(str(qfile), inputs={"book": "MAT", "chapter": "5"})

    cmd = mock_run.call_args[0][0]
    assert "-bbook=MAT" in cmd
    assert "-bchapter=5" in cmd
    assert cmd[-1] == str(qfile)


def test_inputs_values_are_coerced_to_str(tmp_path):
    """Integer / other non-string values are coerced to str for -b binding."""
    qfile = tmp_path / "q.xq"
    qfile.write_text(".")

    ok = _make_completed(stdout="ok")
    with patch("llmflow.plugins.basex.subprocess.run", return_value=ok) as mock_run:
        from llmflow.plugins.basex import run_basex
        run_basex(str(qfile), inputs={"chapter": 5, "limit": 10})

    cmd = mock_run.call_args[0][0]
    assert "-bchapter=5" in cmd
    assert "-blimit=10" in cmd


def test_query_content_not_modified_when_inputs_used(tmp_path):
    """With inputs:, the XQuery file is passed as-is — no str.format_map."""
    xquery = "declare variable $x external; <r>{$x}</r>"
    qfile = tmp_path / "q.xq"
    qfile.write_text(xquery)

    ok = _make_completed(stdout="<r>hello</r>")
    with patch("llmflow.plugins.basex.subprocess.run", return_value=ok) as mock_run:
        from llmflow.plugins.basex import run_basex
        run_basex(str(qfile), inputs={"x": "hello"})

    # The file passed to basex should still contain the original curly braces
    passed_file = mock_run.call_args[0][0][-1]
    assert Path(passed_file).read_text() == xquery


def test_basex_not_found_raises(tmp_path):
    """FileNotFoundError from subprocess → RuntimeError."""
    qfile = tmp_path / "q.xq"
    qfile.write_text("1")

    with patch("llmflow.plugins.basex.subprocess.run", side_effect=FileNotFoundError):
        from llmflow.plugins.basex import run_basex
        with pytest.raises(RuntimeError, match="basex not found"):
            run_basex(str(qfile))


def test_timeout_raises(tmp_path):
    """TimeoutExpired → RuntimeError."""
    qfile = tmp_path / "q.xq"
    qfile.write_text("1")

    with patch(
        "llmflow.plugins.basex.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["basex"], 1),
    ):
        from llmflow.plugins.basex import run_basex
        with pytest.raises(RuntimeError, match="timed out"):
            run_basex(str(qfile), timeout=1)


def test_nonzero_exit_raises(tmp_path):
    """Non-zero basex exit → RuntimeError with stderr text."""
    qfile = tmp_path / "q.xq"
    qfile.write_text("1")

    err = _make_completed(returncode=1, stderr="XPDY0002: database not found")
    with patch("llmflow.plugins.basex.subprocess.run", return_value=err):
        from llmflow.plugins.basex import run_basex
        with pytest.raises(RuntimeError, match="XPDY0002"):
            run_basex(str(qfile))


# ---------------------------------------------------------------------------
# run_basex_step — inputs: resolved from pipeline context
# ---------------------------------------------------------------------------

def test_run_basex_step_passes_inputs_to_run_basex(tmp_path):
    """run_basex_step resolves inputs: and forwards them to run_basex."""
    qfile = tmp_path / "q.xq"
    qfile.write_text("declare variable $lemma external; $lemma")

    step = {
        "name": "test-step",
        "type": "basex",
        "query_file": str(qfile),
        "inputs": {"lemma": "${lemma}"},
        "output": "result",
    }
    context = {"lemma": "הָיָה"}

    with patch("llmflow.steps.basex.run_basex") as mock_run_basex:
        mock_run_basex.return_value = "הָיָה"
        from llmflow.runner import run_basex_step
        run_basex_step(step, context, {})

    mock_run_basex.assert_called_once()
    _, kwargs = mock_run_basex.call_args
    assert kwargs.get("inputs") == {"lemma": "הָיָה"}


def test_run_basex_step_no_inputs_passes_none(tmp_path):
    """run_basex_step with no inputs: passes inputs=None."""
    qfile = tmp_path / "q.xq"
    qfile.write_text("count(//v)")

    step = {
        "name": "test-step",
        "type": "basex",
        "query_file": str(qfile),
        "output": "result",
    }

    with patch("llmflow.steps.basex.run_basex") as mock_run_basex:
        mock_run_basex.return_value = "3"
        from llmflow.runner import run_basex_step
        run_basex_step(step, {}, {})

    _, kwargs = mock_run_basex.call_args
    assert kwargs.get("inputs") is None
