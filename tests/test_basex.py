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

    def test_run_basex_returns_stdout_on_success(self, tmp_path):
        """run_basex() must return stripped stdout when basex exits 0."""
        from llmflow.plugins.basex import run_basex
        qfile = tmp_path / "q.xq"
        qfile.write_text("1+1")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<occ ref='MAT.1.1'/>\n"
        mock_result.stderr = ""

        with patch("llmflow.plugins.basex.subprocess.run", return_value=mock_result):
            result = run_basex(str(qfile))
        assert result == "<occ ref='MAT.1.1'/>"

    def test_run_basex_raises_on_nonzero_exit(self, tmp_path):
        """run_basex() must raise RuntimeError with stderr when basex exits non-zero."""
        from llmflow.plugins.basex import run_basex
        qfile = tmp_path / "q.xq"
        qfile.write_text("db:get('no-such-db')//w")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Database 'no-such-db' not found."

        with patch("llmflow.plugins.basex.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="no-such-db"):
                run_basex(str(qfile))

    def test_run_basex_raises_when_basex_not_found(self, tmp_path):
        """run_basex() must raise a clear error when basex is not on PATH."""
        from llmflow.plugins.basex import run_basex
        qfile = tmp_path / "q.xq"
        qfile.write_text("1+1")
        with patch("llmflow.plugins.basex.subprocess.run", side_effect=FileNotFoundError("basex")):
            with pytest.raises(RuntimeError, match="basex.*not found|not.*installed"):
                run_basex(str(qfile))

    def test_run_basex_respects_timeout(self, tmp_path):
        """run_basex() must pass timeout to subprocess.run."""
        from llmflow.plugins.basex import run_basex
        qfile = tmp_path / "q.xq"
        qfile.write_text("1+1")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""

        with patch("llmflow.plugins.basex.subprocess.run", return_value=mock_result) as mock_run:
            run_basex(str(qfile), timeout=30)
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("timeout") == 30

    def test_run_basex_raises_on_timeout(self, tmp_path):
        """run_basex() must raise RuntimeError with a clear message on timeout."""
        import subprocess
        from llmflow.plugins.basex import run_basex
        qfile = tmp_path / "q.xq"
        qfile.write_text("(: slow query :)")
        with patch("llmflow.plugins.basex.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("basex", 10)):
            with pytest.raises(RuntimeError, match="timed out"):
                run_basex(str(qfile), timeout=10)

    def test_run_basex_inputs_become_b_flags(self, tmp_path):
        """run_basex() with inputs must pass -b<key>=<value> flags to basex."""
        from llmflow.plugins.basex import run_basex
        qfile = tmp_path / "q.xq"
        qfile.write_text("declare variable $lemma external; $lemma")
        mock_result = MagicMock(returncode=0, stdout="λέγω", stderr="")

        with patch("llmflow.plugins.basex.subprocess.run", return_value=mock_result) as mock_run:
            run_basex(str(qfile), inputs={"lemma": "λέγω"})

        cmd = mock_run.call_args[0][0]
        assert "-blemma=λέγω" in cmd
        assert cmd[-1] == str(qfile)


class TestBasexStepRunner:
    """Tests for run_basex_step() in runner.py."""

    def _make_step(self, tmp_path, **overrides):
        qfile = tmp_path / "q.xq"
        qfile.write_text("declare variable $lemma external; $lemma")
        base = {
            "name": "fetch-corpus",
            "type": "basex",
            "query_file": str(qfile),
            "inputs": {"lemma": "${lemma}"},
            "output": "corpus_data",
        }
        base.update(overrides)
        return base

    def test_run_basex_step_puts_result_in_context(self, tmp_path):
        """run_basex_step() must store the query result in context under outputs key."""
        from llmflow.runner import run_basex_step
        step = self._make_step(tmp_path)
        context = {"lemma": "λέγω"}

        with patch("llmflow.steps.basex.run_basex", return_value="<occ ref='MAT.1.1'/>"):
            run_basex_step(step, context, {})

        assert "corpus_data" in context
        assert "MAT.1.1" in context["corpus_data"]

    def test_run_basex_step_resolves_inputs_from_context(self, tmp_path):
        """inputs: values are resolved from pipeline context and forwarded."""
        from llmflow.runner import run_basex_step
        step = self._make_step(tmp_path, inputs={"lemma": "${current_lemma}"})
        context = {"current_lemma": "λόγος"}
        captured = {}

        def fake_run_basex(query_file, inputs=None, timeout=120):
            captured["inputs"] = inputs
            return "<occ/>"

        with patch("llmflow.steps.basex.run_basex", side_effect=fake_run_basex):
            run_basex_step(step, context, {})

        assert captured["inputs"]["lemma"] == "λόγος"

    def test_run_basex_step_uses_query_file(self, tmp_path):
        """query_file path is resolved and passed directly to run_basex."""
        from llmflow.runner import run_basex_step
        qfile = tmp_path / "lemma.xq"
        qfile.write_text("declare variable $lemma external; $lemma", encoding="utf-8")
        step = self._make_step(tmp_path, query_file=str(qfile), outputs="result")
        context = {}
        captured = {}

        def fake_run_basex(query_file, inputs=None, timeout=120):
            captured["query_file"] = query_file
            return "<occ/>"

        with patch("llmflow.steps.basex.run_basex", side_effect=fake_run_basex):
            run_basex_step(step, context, {})

        assert captured["query_file"] == str(qfile)

    def test_run_basex_step_propagates_timeout(self, tmp_path):
        """timeout_seconds: in the step config must be passed through to run_basex.

        The step key is `timeout_seconds` (one spelling across step types); the
        `run_basex` *function* parameter is still named `timeout`.
        """
        from llmflow.runner import run_basex_step
        step = self._make_step(tmp_path, timeout_seconds=30)
        context = {"lemma": "ὁ"}
        captured = {}

        def fake_run_basex(query_file, inputs=None, timeout=120):
            captured["timeout"] = timeout
            return "<occ/>"

        with patch("llmflow.steps.basex.run_basex", side_effect=fake_run_basex):
            run_basex_step(step, context, {})

        assert captured["timeout"] == 30

    def test_run_basex_step_missing_basex_gives_helpful_error(self, tmp_path):
        """If basex is not installed, the step must raise with an actionable message."""
        from llmflow.runner import run_basex_step
        step = self._make_step(tmp_path)
        context = {"lemma": "λέγω"}

        with patch("llmflow.steps.basex.run_basex",
                   side_effect=RuntimeError("basex not found on PATH")):
            with pytest.raises(RuntimeError, match="basex"):
                run_basex_step(step, context, {})


class TestBasexStepDispatch:
    """type: basex must be dispatched by the main run_step() function."""

    def test_run_step_dispatches_basex_type(self, tmp_path):
        """run_step() must call run_basex_step for type: basex steps."""
        from llmflow.runner import run_step
        qfile = tmp_path / "q.xq"
        qfile.write_text("1+1")
        step = {
            "name": "test-basex",
            "type": "basex",
            "query_file": str(qfile),
            "output": "result",
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
    def test_simple_query_returns_xml(self, tmp_path):
        """A real XQuery against macula-greek must return XML elements."""
        from llmflow.plugins.basex import run_basex
        qfile = tmp_path / "q.xq"
        qfile.write_text('for $w in db:get("macula-greek")//w[@lemma="λέγω"][position()<=3] return $w')
        result = run_basex(str(qfile))
        assert "<w " in result
        assert 'lemma="λέγω"' in result

    def test_hebrew_uca_sort_aleph_bet_order_with_niqquud(self, tmp_path):
        """XQuery fn:sort with UCA Hebrew collation must produce aleph-bet order for words with niqquud.

        This is a hard test: niqquud (vowel points) are Unicode combining characters.
        The UCA collation must treat the base consonant as the primary sort key so that
        אֱלֹהִים (aleph) < בָּרָא (bet) < גָּדוֹל (gimel) regardless of attached niqquud.
        Words are inserted in gimel→aleph→bet order to prove sorting is active.
        """
        from llmflow.plugins.basex import run_basex
        qfile = tmp_path / "hebrew_sort.xq"
        qfile.write_text(
            'let $words := ("גָּדוֹל", "אֱלֹהִים", "בָּרָא")\n'
            'let $sorted := fn:sort($words, "http://www.w3.org/2013/collation/UCA?lang=he")\n'
            'return string-join($sorted, ",")',
            encoding='utf-8'
        )
        result = run_basex(str(qfile))
        words = result.split(',')
        assert len(words) == 3, f"Expected 3 words, got: {words}"
        assert words[0][0] == 'א', f"Aleph (א) should sort first, got: {words}"
        assert words[1][0] == 'ב', f"Bet (ב) should sort second, got: {words}"
        assert words[2][0] == 'ג', f"Gimel (ג) should sort third, got: {words}"

    def test_hebrew_niqquud_transparent_at_primary_strength(self, tmp_path):
        """UCA primary strength must treat שָׁלוֹם (with niqquud) equal to שלום (bare consonants).

        Niqquud are secondary-weight differences in ICU/UCA. At primary strength only
        base consonants are compared, so a fully-pointed word must compare equal (0)
        to its unpointed form. This is the key requirement for searching Hebrew text
        without knowing whether niqquud are present in a source.
        """
        from llmflow.plugins.basex import run_basex
        qfile = tmp_path / "niqquud_compare.xq"
        qfile.write_text(
            'fn:compare(\n'
            '  "שָׁלוֹם",\n'
            '  "שלום",\n'
            '  "http://www.w3.org/2013/collation/UCA?lang=he;strength=primary"\n'
            ')',
            encoding='utf-8'
        )
        result = run_basex(str(qfile))
        assert result.strip() == '0', (
            f"שָׁלוֹם and שלום should compare equal at primary strength (got {result!r}). "
            "Niqquud must be transparent at primary collation weight."
        )
