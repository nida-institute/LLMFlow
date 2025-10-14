#!/usr/bin/env python3
"""Direct test of the runner to find where it hangs"""

import sys
import logging
sys.path.insert(0, 'src')

# Set up logging to see everything
logging.basicConfig(level=logging.DEBUG)

from pathlib import Path
import yaml
from llmflow.runner import run_pipeline

# Load and run the pipeline with extra debugging
pipeline_path = "pipelines/storyflow-psalms.yaml"
print(f"Loading pipeline: {pipeline_path}")

# Load the pipeline manually to check it
pipeline_yaml = Path(pipeline_path).read_text()
pipeline_data = yaml.safe_load(pipeline_yaml)
print(f"Pipeline loaded: {pipeline_data.get('name', 'unnamed')}")
print(f"Number of steps: {len(pipeline_data.get('steps', []))}")

# Try running with extra debug
print("\nAttempting to run pipeline...")
try:
    result = run_pipeline(pipeline_path, vars={"passage": "Psalm 1"}, skip_lint=True)
    print(f"Pipeline completed! Result keys: {list(result.keys()) if result else 'None'}")
except KeyboardInterrupt:
    print("\nInterrupted!")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()