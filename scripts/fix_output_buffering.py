#!/usr/bin/env python3
"""Fix the output buffering issue"""

import os
import sys

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", buffering=1)

# Set environment variable for Python unbuffered output
os.environ["PYTHONUNBUFFERED"] = "1"

# Now run the CLI
sys.path.insert(0, ".")
from src.llmflow.cli import cli

sys.argv = [
    "llmflow",
    "run",
    "--pipeline",
    "pipelines/storyflow-psalms.yaml",
    "--var",
    "passage=Psalm 88",
    "--verbose",
]

cli()
