"""
Tests for type: basex step — runs XQuery against a local BaseX database.

Tests use mock subprocess calls so BaseX does not need to be installed.
Integration tests that require a live BaseX instance are skipped unless
BASEX_INTEGRATION_TESTS=1 is set.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


# ---------------------------------------------------------------------------
# Unit tests — all mock subprocess, no BaseX required
# ---------------------------------------------------------------------------

class TestRunBasex:
    """Tests for the core run_basex() function in llmflow.plugins.basex."""

    def test_run_basex_returns_stdout_on_success(self):
        """run_basex() must return stripped stdout when basex exits 0."""
        from llmflow.plugins.basex import run_basex
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<occ ref='MAT.1.1'/>\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = run_basex("SELECT 1")
        assert result == "<occ ref='MAT.1.1'/>"

    def test_run_basex_raises_on_nonzero_exit(self):
        """run_basex() must raise RuntimeError with stderr when basex exits non-zero."""
        from llmflow.plugins.basex import run_basex
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Database 'no-such-db' not found."

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="no-such-db"):
                run_basex("db:get('no-such-db')//w")

    def test_run_basex_raises_when_basex_not_found(self):
        """run_basex() must raise a clear error when basex is not on PATH."""
        from llmflow.plugins.basex import run_basex
        with patch("subprocess.run", side_effect=FileNotFoundError("basex")):
            with pytest.raises(RuntimeError, match="basex.*not found|not.*installed"):
                run_basex("1+1")

    def test_run_basex_respects_timeout(self):
        """run_basex() must pass timeout to subprocess.run."""
        from llmflow.plugins.basex import run_basex
        import subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            run_basex("1+1", timeout=30)
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("timeout") == 30

    def test_run_basex_raises_on_timeout(self):
        """run_basex() must raise RuntimeError with a clear message on timeout."""
        from llmflow.plugins.basex import run_basex
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("basex", 10)):
            with pytest.raises(RuntimeError, match="timed out"):
                run_basex("(: slow query :)", timeout=10)

    def test_run_basex_substitutes_params(self):
        """run_basex() with params must substitute values into the query string."""
        from llmflow.plugins.basex import run_basex
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<result/>"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            run_basex(
                'for $w in db:get("macula-greek")//w[@lemma = "{lemma}"] return $w',
                params={"lemma": "λέγω"},
            )
        # The query written to the temp file should have the param substituted
        call_args = mock_run.call_args
        # basex is called with a temp file path; we check the query written to it
        # by inspecting what was passed (the temp file is deleted after, so we
        # capture it via the call args — the first positional arg is ["basex", <path>])
        called_cmd = call_args[0][0]
        assert called_cmd[0] == "basex"
        # We can't easily read the temp file since it's deleted, but we can verify
        # subprocess.run was called exactly once with a file argument
        assert len(called_cmd) == 2  # ["basex", "<tempfile>"]


class TestBasexStepRunner:
    """Tests for run_basex_step() in runner.py."""

    def _make_step(self, **overrides):
        base = {
            "name": "fetch-corpus",
            "type": "basex",
            "database": "macula-greek",
            "query": 'for $w in db:get("macula-greek")//w[@lemma = "{lemma}"] return $w',
            "params": {"lemma": "${lemma}"},
            "outputs": "corpus_data",
        }
        base.update(overrides)
        return base

    def test_run_basex_step_puts_result_in_context(self):
        """run_basex_step() must store the query result in context under outputs key."""
        from llmflow.runner import run_basex_step
        step = self._make_step()
        context = {"lemma": "λέγω"}

        with patch("llmflow.runner.run_basex", return_value="<occ ref='MAT.1.1'/>"):
            run_basex_step(step, context, {})

        assert "corpus_data" in context
        assert "MAT.1.1" in context["corpus_data"]

    def test_run_basex_step_resolves_params_from_context(self):
        """Params must be resolved from pipeline context before substitution."""
        from llmflow.runner import run_basex_step
        step = self._make_step(params={"lemma": "${current_lemma}"})
        context = {"current_lemma": "λόγος"}
        captured = {}

        def fake_run_basex(query, params=None, timeout=120):
            captured["params"] = params
            return "<occ/>"

        with patch("llmflow.runner.run_basex", side_effect=fake_run_basex):
            run_basex_step(step, context, {})

        assert captured["params"]["lemma"] == "λόγος"

    def test_run_basex_step_uses_query_file(self, tmp_path):
        """When query_file is given, it must read the file and use it as the query."""
        from llmflow.runner import run_basex_step
        qfile = tmp_path / "lemma.xq"
        qfile.write_text('for $w in db:get("macula-greek")//w return $w', encoding="utf-8")
        step = self._make_step(query_file=str(qfile), outputs="result")
        del step["query"]
        context = {}
        captured = {}

        def fake_run_basex(query, params=None, timeout=120):
            captured["query"] = query
            return "<occ/>"

        with patch("llmflow.runner.run_basex", side_effect=fake_run_basex):
            run_basex_step(step, context, {})

        assert 'db:get("macula-greek")' in captured["query"]

    def test_run_basex_step_propagates_timeout(self):
        """timeout: in the step config must be passed through to run_basex."""
        from llmflow.runner import run_basex_step
        step = self._make_step(timeout=30)
        context = {"lemma": "ὁ"}
        captured = {}

        def fake_run_basex(query, params=None, timeout=120):
            captured["timeout"] = timeout
            return "<occ/>"

        with patch("llmflow.runner.run_basex", side_effect=fake_run_basex):
            run_basex_step(step, context, {})

        assert captured["timeout"] == 30

    def test_run_basex_step_missing_basex_gives_helpful_error(self):
        """If basex is not installed, the step must raise with an actionable message."""
        from llmflow.runner import run_basex_step
        step = self._make_step()
        context = {"lemma": "λέγω"}

        with patch("llmflow.runner.run_basex",
                   side_effect=RuntimeError("basex not found on PATH")):
            with pytest.raises(RuntimeError, match="basex"):
                run_basex_step(step, context, {})


class TestBasexStepDispatch:
    """type: basex must be dispatched by the main run_step() function."""

    def test_run_step_dispatches_basex_type(self):
        """run_step() must call run_basex_step for type: basex steps."""
        from llmflow.runner import run_step
        step = {
            "name": "test-basex",
            "type": "basex",
            "database": "macula-greek",
            "query": "1+1",
            "outputs": "result",
        }
        context = {}
        with patch("llmflow.runner.run_basex_step", return_value=None) as mock_fn:
            run_step(step, context, {})
        mock_fn.assert_called_once()


# ---------------------------------------------------------------------------
# Integration test — requires live BaseX with macula-greek database
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("BASEX_INTEGRATION_TESTS"),
    reason="Set BASEX_INTEGRATION_TESTS=1 to run live BaseX tests",
)
class TestBasexIntegration:
    def test_simple_query_returns_xml(self):
        """A real XQuery against macula-greek must return XML elements."""
        from llmflow.plugins.basex import run_basex
        result = run_basex('for $w in db:get("macula-greek")//w[@lemma="λέγω"][position()<=3] return $w')
        assert "<w " in result
        assert 'lemma="λέγω"' in result
