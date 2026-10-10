"""`info` as a third severity, and the handler that was silently promoting it.

Asked for by `nida-institute/discourse-flow`, whose note is in `collab/discourse-flow/`. They had
added `info` to their own defect plugin and would rather not keep a severity vocabulary the engine
does not share — a published defect file then carries a level its reader does not know.

**What `info` is for: a condition that is rare and unlikely, but not wrong.** Their two live
cases: a window that returns a single pericope, which is not an error and not a warning — the run
keeps the pericope and records the fact; and derived children with no analysis, which is by
design and which they measure at 56 of 119 leaf pericopes in Mark. Reporting either at `warning`
spends a reader's attention on deciding they are not problems, which is the cost the severity
distinction exists to avoid.

**The handler is a defect whichever way that goes.** It maps anything below ERROR to `warning`,
so a deliberate INFO on the `llmflow.defects` logger became a warning with nothing saying so.

**One trap they hit and we do not.** Their `report` derived its warning count as
`len(defects) - errors`, so a third severity folded silently into the warning total. Ours counts
each severity from `SEVERITIES`, so it was already right — `test_counts_are_per_severity` pins
that, because it is the thing that would break quietly if someone ever optimised it.
"""

from __future__ import annotations

import logging

from llmflow.defects import SEVERITIES, DefectLog, defect_logging_handler


def test_info_is_a_known_severity():
    assert "info" in SEVERITIES


def test_the_three_severities_are_ordered_least_to_most_serious():
    """The order is what a reader of the vocabulary learns; it should not be arbitrary."""
    assert SEVERITIES == ("info", "warning", "error")


def test_an_info_defect_is_recorded_and_kept_distinct():
    log = DefectLog("p")
    log.record("windows", "one pericope in this window", severity="info")
    log.record("windows", "something to look at", severity="warning")

    assert log.counts() == {"info": 1, "warning": 1, "error": 0}


def test_counts_are_per_severity_rather_than_derived_by_subtraction():
    """The trap discourse-flow hit locally: a third severity folded into the warning total.

    Ours counts each severity from `SEVERITIES`. This pins it, because the subtraction form is
    the tempting simplification and it fails silently — the total stays right while the split
    goes wrong.
    """
    log = DefectLog("p")
    log.record("s", "a", severity="info")
    log.record("s", "b", severity="info")
    log.record("s", "c", severity="error")

    counts = log.counts()
    assert counts["info"] == 2, "info must be counted as itself"
    assert counts["warning"] == 0, "no warning was recorded, so the warning count is zero"
    assert counts["error"] == 1
    assert sum(counts.values()) == 3


def test_the_summary_names_each_severity_present():
    log = DefectLog("p")
    log.record("s", "a", severity="info")
    log.record("s", "b", severity="error")

    summary = log.summary()
    assert "info" in summary and "error" in summary
    assert "warning" not in summary, "a severity with no entries is not listed"


def test_an_unknown_severity_is_still_refused():
    """Widening the vocabulary must not turn it into an open set."""
    import pytest

    log = DefectLog("p")
    with pytest.raises(ValueError) as caught:
        log.record("s", "m", severity="notice")
    assert "notice" in str(caught.value)


# --- the handler, which was promoting INFO to warning -------------------------------------


def _emit(level: int, message: str) -> DefectLog:
    log = DefectLog("p")
    handler = defect_logging_handler(log)
    record = logging.LogRecord("llmflow.defects", level, __file__, 0, message, (), None)
    handler.emit(record)
    return log


def test_an_info_record_becomes_an_info_defect():
    """It became a `warning`, silently, and there was no level to promote it to."""
    assert _emit(logging.INFO, "expected, and worth recording").counts()["info"] == 1


def test_a_debug_record_becomes_an_info_defect():
    """Below INFO is still not a warning. The run said something quiet; keep it quiet."""
    assert _emit(logging.DEBUG, "quiet").counts()["info"] == 1


def test_a_warning_record_is_still_a_warning():
    assert _emit(logging.WARNING, "look at this").counts()["warning"] == 1


def test_an_error_record_is_still_an_error():
    assert _emit(logging.ERROR, "nothing downstream to inspect").counts()["error"] == 1


def test_a_critical_record_is_an_error():
    """Above ERROR has no separate defect severity, and should not silently become one."""
    assert _emit(logging.CRITICAL, "worse").counts()["error"] == 1
