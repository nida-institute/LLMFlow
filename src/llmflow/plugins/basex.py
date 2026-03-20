"""BaseX plugin — run XQuery against a local BaseX database."""

import os
import subprocess
import tempfile

from llmflow.modules.logger import Logger

logger = Logger()


def run_basex(query: str, params: dict | None = None, timeout: int = 120) -> str:
    """
    Execute an XQuery string against BaseX and return stripped stdout.

    If *params* is given, each key is substituted into the query wherever
    ``{key}`` appears (Python str.format_map style).

    Raises:
        RuntimeError: basex not found on PATH, non-zero exit, or timeout.
    """
    if params:
        query = query.format_map(params)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xq", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(query)
        qfile = fh.name

    try:
        try:
            result = subprocess.run(
                ["basex", qfile],
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
    finally:
        os.unlink(qfile)
