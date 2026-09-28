"""What a run noticed but did not fail on.

A step that finds a discrepancy in the data — a citation that did not resolve, a unit needing
review, an assumption it had to make — records it here and carries on. Distinct from three things
that already existed and answer different questions: `Logger` writes prose nobody can count,
telemetry describes the run rather than the data, and `require:` fails the step, which is the
opposite of what this is for.

Two channels reach it, and neither is a side channel:

- **the reserved key.** A step returns `defects` alongside its data, so a defect is ordinary step
  output — visible to the pipeline, replayable by `--rewind-to`, and writable by an XQuery, a SQL
  query or an LLM under a schema, not only by Python. That is what keeps this inside
  `context-is-the-only-channel` rather than needing an exemption from it.
- **the logger.** Python code writes to `llmflow.defects` and is captured, so a plugin author
  needs no new import and no new habit.

`[]` and absence differ. An empty log means the run looked and found nothing; no file at all means
nothing looked.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

#: The key a step returns its defects under. Reserved: a step's data must not use the name for
#: anything else, because the runner drains it wherever a step result is a mapping.
RESERVED_KEY = "defects"

#: Where the run's log sits in the pipeline context. Engine-owned, so it is prefixed like the
#: other keys the runner sets — the log rides the channel every step already has rather than
#: being threaded through each handler's signature.
DEFECT_LOG_KEY = "_defects"

#: Least serious first, so the order is itself part of the vocabulary.
#:
#: `info` is a condition that is rare and unlikely but **not wrong** — nothing went amiss, and
#: the record exists so that someone examining the run can see it happened. `warning` is the
#: normal case: the run produced something and this is evidence worth having. `error` is a
#: condition that leaves nothing downstream to inspect.
#:
#: This was two values, on the reasoning that a third invites a debate about which one applies.
#: It was asked for by a consumer with two cases that are neither wrong nor worth a reader's
#: attention as problems — a window returning a single pericope, and derived children that carry
#: no analysis by design, 56 of 119 in one book. Reporting those at `warning` spends attention on
#: deciding they are not problems, which is the cost the distinction exists to avoid. The debate
#: the third value invites is cheaper than the attention the missing one was costing.
SEVERITIES = ("info", "warning", "error")


class DefectLog:
    """Everything a run noticed, in the order it noticed it.

    A list rather than a set or a queue: the order defects were found in is the order a reader
    wants them, and two identical messages from different units are two facts rather than one.
    """

    def __init__(self, pipeline: str = "") -> None:
        self.pipeline = pipeline
        self._entries: list[dict] = []
        # `for-each` with `parallel:` runs steps concurrently, so appends race without this. A
        # lost defect is a silent one, which is the failure this whole module exists to end.
        self._lock = threading.Lock()

    def __deepcopy__(self, memo: dict) -> "DefectLog":
        """A copied context shares the one log, rather than getting a copy of it.

        `for-each` deep-copies the context for each iteration so the iterations cannot see one
        another's variables. The log is the exception: a copy would collect an iteration's
        defects into an object that is then discarded, which is the silent loss this module
        exists to end. There is one log per run, and every iteration writes to it.

        It is also the only workable answer — a `threading.Lock` cannot be copied at all.
        """
        memo[id(self)] = self
        return self

    def record(
        self,
        step: str,
        message: str,
        *,
        severity: str = "warning",
        location: Optional[str] = None,
        **detail: Any,
    ) -> None:
        """Record and return; the caller carries on with a flagged unit."""
        if severity not in SEVERITIES:
            raise ValueError(
                f"{severity!r} is not a known severity; expected one of {SEVERITIES}"
            )
        entry = {
            "step": step,
            "message": message,
            "severity": severity,
            "location": location,
            "detail": dict(detail),
        }
        with self._lock:
            self._entries.append(entry)

    def extend(self, step: str, payload: Any) -> None:
        """Drain what a step returned under `defects`.

        Tolerant about shape on purpose: a step may return a mapping per defect, or a bare string
        where the message is all there is to say. A step reporting a defect is already having a
        bad day, and refusing its report over its shape would lose the report.
        """
        if not isinstance(payload, Iterable) or isinstance(payload, (str, bytes, Mapping)):
            return
        for item in payload:
            if isinstance(item, Mapping):
                fields = dict(item)
                self.record(
                    str(fields.pop("step", None) or step),
                    str(fields.pop("message", "")),
                    severity=str(fields.pop("severity", "warning")),
                    location=fields.pop("location", None),
                    **fields,
                )
            elif item is not None:
                self.record(step, str(item))

    def entries(self) -> list[dict]:
        with self._lock:
            return list(self._entries)

    def counts(self) -> dict:
        found = self.entries()
        return {severity: sum(1 for e in found if e["severity"] == severity)
                for severity in SEVERITIES}

    def summary(self) -> str:
        """One line for the end of a run. Says so when there is nothing, rather than nothing."""
        counts = self.counts()
        total = sum(counts.values())
        if not total:
            return "🔍 No defects recorded — the run looked and found nothing."
        parts = [f"{n} {name}{'s' if n != 1 else ''}" for name, n in counts.items() if n]
        return f"🔍 {total} defect{'s' if total != 1 else ''} recorded: {', '.join(parts)}"

    def write(self, path: Any) -> Path:
        """Write the log, entries and counts together.

        Written even when empty: `[]` is the run saying it looked, which a reader cannot infer
        from a missing file.
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pipeline": self.pipeline,
            "counts": self.counts(),
            "defects": self.entries(),
        }
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return target


class _DefectHandler(logging.Handler):
    """Turns a record on the `llmflow.defects` logger into an entry."""

    def __init__(self, log: DefectLog) -> None:
        super().__init__()
        self._log = log

    def emit(self, record: logging.LogRecord) -> None:
        # The logger's levels map onto the defect vocabulary rather than collapsing into it.
        # This read `"error" if levelno >= ERROR else "warning"`, so a deliberate INFO became a
        # warning and nothing said so — and until `info` existed there was no level to promote
        # it to. Reported by a consumer who had hit it.
        if record.levelno >= logging.ERROR:
            severity = "error"
        elif record.levelno >= logging.WARNING:
            severity = "warning"
        else:
            severity = "info"
        # Anything the caller passed as `extra` that is not a standard LogRecord attribute.
        standard = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
            "message", "asctime", "taskName"
        }
        detail = {k: v for k, v in record.__dict__.items() if k not in standard}
        self._log.record(
            detail.pop("step", None) or record.name,
            record.getMessage(),
            severity=severity,
            location=detail.pop("location", None),
            **detail,
        )


def defect_logging_handler(log: DefectLog) -> logging.Handler:
    """A handler that files `llmflow.defects` records into *log*."""
    return _DefectHandler(log)
