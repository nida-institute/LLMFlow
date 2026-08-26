"""The `database:` keyword binds $database in the query (LLMFlow#189).

`database:` was required by the linter and then thrown away — nothing passed it to
BaseX. Queries therefore hardcoded the database name inside the XQuery, or smuggled it
through an ad-hoc `inputs: db:` entry, so changing `database:` in the pipeline changed
nothing at all.

The convention: the keyword and the XQuery variable are the same word.

    - name: q
      type: basex
      database: macula-sblgnt-lowfat     # -> -bdatabase=macula-sblgnt-lowfat
      query_file: queries/leitwort.xq

    declare variable $database external;
    collection($database)//w

Why a *collision* with `inputs: database:` must be an error rather than a precedence
rule: BaseX accepts duplicate -b flags for one variable, takes the last silently, and
exits 0. Verified against BaseX 12.3:

    basex -bdatabase=FIRST -bdatabase=SECOND q.xq   ->  exit 0, "SECOND"

So the YAML can say `database: acai` on its own line while the query runs against
something else, with the step reporting success. BaseX will never tell us; the linter
has to.

Tests mock subprocess — no BaseX required.
"""
from unittest.mock import MagicMock, patch

import pytest


def _ok(stdout="<r/>"):
    m = MagicMock()
    m.returncode, m.stdout, m.stderr = 0, stdout, ""
    return m


def _run_step(step, context=None):
    """Run a basex step, returning the argv basex would have been called with."""
    from llmflow.steps.basex import run_basex_step
    with patch("llmflow.plugins.basex.subprocess.run", return_value=_ok()) as mock:
        run_basex_step(step, context if context is not None else {}, {})
    return mock.call_args[0][0]


class TestDatabaseIsBound:
    def test_database_becomes_a_binding(self, tmp_path):
        q = tmp_path / "q.xq"
        q.write_text("declare variable $database external; collection($database)")
        argv = _run_step({
            "name": "q", "type": "basex",
            "database": "macula-sblgnt-lowfat",
            "query_file": str(q),
        })
        assert "-bdatabase=macula-sblgnt-lowfat" in argv, (
            f"database: was not passed to BaseX — argv was {argv}"
        )

    def test_database_resolves_variables(self, tmp_path):
        """`database:` must go through resolve(), like every other step value."""
        q = tmp_path / "q.xq"
        q.write_text("declare variable $database external; 1")
        argv = _run_step(
            {"name": "q", "type": "basex",
             "database": "${corpus_name}", "query_file": str(q)},
            {"corpus_name": "macula-hebrew-lowfat"},
        )
        assert "-bdatabase=macula-hebrew-lowfat" in argv, argv

    def test_database_coexists_with_other_inputs(self, tmp_path):
        q = tmp_path / "q.xq"
        q.write_text("declare variable $database external; 1")
        argv = _run_step({
            "name": "q", "type": "basex",
            "database": "acai",
            "query_file": str(q),
            "inputs": {"book_id": "MAT", "chapter": "3"},
        })
        for expected in ("-bdatabase=acai", "-bbook_id=MAT", "-bchapter=3"):
            assert expected in argv, f"missing {expected} in {argv}"

    def test_only_one_database_binding_is_emitted(self, tmp_path):
        """Two -bdatabase flags would let BaseX silently pick the last one."""
        q = tmp_path / "q.xq"
        q.write_text("declare variable $database external; 1")
        argv = _run_step({
            "name": "q", "type": "basex",
            "database": "acai", "query_file": str(q),
        })
        assert len([a for a in argv if a.startswith("-bdatabase=")]) == 1, argv


class TestCollisionIsRejected:
    """`database:` and `inputs: database:` both write $database — refuse to guess."""

    def test_runtime_raises_on_collision(self, tmp_path):
        q = tmp_path / "q.xq"
        q.write_text("declare variable $database external; 1")
        from llmflow.steps.basex import run_basex_step
        with pytest.raises(ValueError, match="database"):
            with patch("llmflow.plugins.basex.subprocess.run", return_value=_ok()):
                run_basex_step({
                    "name": "q", "type": "basex",
                    "database": "acai",
                    "query_file": str(q),
                    "inputs": {"database": "sdbh"},
                }, {}, {})

    def test_lint_rejects_collision(self, tmp_path):
        """Caught before the run, which is the point — `sp run` can skip linting."""
        from llmflow.utils.linter import lint_pipeline_full
        (tmp_path / "q.xq").write_text("declare variable $database external; 1")
        p = tmp_path / "p.yaml"
        p.write_text(
            "name: p\n"
            "steps:\n"
            "  - name: q\n"
            "    type: basex\n"
            "    database: acai\n"
            "    query_file: q.xq\n"
            "    inputs:\n"
            "      database: sdbh\n"
        )
        result = lint_pipeline_full(str(p))
        assert not result.valid
        assert any("database" in e for e in result.errors), result.errors


class TestRetiredSpelling:
    def test_db_is_a_known_typo_for_database(self):
        """`$db` was the old ad-hoc spelling; guide rather than silently ignore.

        BaseX drops bindings for variables a query never declares — exit 0, no warning
        (verified on 12.3) — so a stale `db:` would fail silently forever.
        """
        from llmflow.utils.linter import COMMON_TYPOS
        assert COMMON_TYPOS.get("db") == "database"
