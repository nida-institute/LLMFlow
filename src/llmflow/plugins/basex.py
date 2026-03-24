"""BaseX plugin — run XQuery against a local BaseX database."""

import os
import subprocess

from llmflow.modules.logger import Logger

logger = Logger()


def run_basex(query_file: str, inputs: dict | None = None, timeout: int = 120) -> str:
    """
    Execute an XQuery file against BaseX and return stripped stdout.

    If *inputs* is given, each key/value pair is passed to BaseX as an
    external variable binding via the ``-b<key>=<value>`` CLI flag.  The
    XQuery must declare the variable as external::

        declare variable $lemma external;

    The query file is **never** modified — no Python string substitution is
    performed, so XQuery curly braces (computed constructors, maps, arrays)
    are safe.

    Raises:
        RuntimeError: basex not found on PATH, non-zero exit, or timeout.
    """
    cmd = ["basex"]
    if inputs:
        for key, value in inputs.items():
            cmd.append(f"-b{key}={value}")
    cmd.append(query_file)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "basex not found on PATH — install BaseX and ensure 'basex' is executable"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"BaseX query timed out after {timeout}s"
        )

    if result.returncode != 0:
        raise RuntimeError(f"BaseX error: {result.stderr.strip()}")

    return result.stdout.strip()
