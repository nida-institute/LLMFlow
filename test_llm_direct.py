#!/usr/bin/env python3
"""Test llm library directly to see if it's hanging"""

import sys
sys.path.insert(0, '.')

import llm

# Get the model
model = llm.get_model("gpt-4o")

print("Testing direct llm call...", file=sys.stderr)

try:
    # Try a simple prompt with stream=False
    response = model.prompt("Say hello", stream=False)
    print(f"Response type: {type(response)}", file=sys.stderr)
    print(f"Response attributes: {dir(response)}", file=sys.stderr)

    # Try to get the text
    print("Calling response.text()...", file=sys.stderr)
    text = response.text()
    print(f"Got text: {text}", file=sys.stderr)

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()