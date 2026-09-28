#!/usr/bin/env python3
"""Write `docs/cli-api.json` — this repository's copy of the public surface.

    hatch run python tools/index_cli_api.py > docs/cli-api.json

A thin wrapper. The rendering lives in `llmflow.cli_api`, inside the package, because `tools/`
is not in the wheel and `sp init` has to render the same map into a project. One implementation,
two callers — this one for the pre-commit hook here, and the file catalog for a project.

The companion to `tools/index_signatures.py`, which maps the implementation and declares in its
own `about` that it is not an API.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from llmflow.cli_api import render_cli_api  # noqa: E402

if __name__ == "__main__":
    sys.stdout.write(render_cli_api())
