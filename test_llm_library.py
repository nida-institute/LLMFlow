#!/usr/bin/env python3
"""Test llm library to see if it's causing the hang"""

import llm
import time
import sys

print("Testing llm library...")
print(f"Available models: {[model.model_id for model in llm.get_models()]}")

# Test with the llm library
model = llm.get_model("gpt-4o")

print("\nTesting simple prompt...")
start_time = time.time()

try:
    # Try without streaming first
    response = model.prompt(
        "Say 'Hello from LLM library!' and nothing else.",
        max_tokens=50,
        temperature=0.4
    )

    print(f"Response received in {time.time() - start_time:.2f} seconds")
    print(f"Response text: {response.text()}")

    # Check if response object has streaming info
    print(f"\nResponse object type: {type(response)}")
    print(f"Response attributes: {dir(response)}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Try to understand if llm library uses streaming by default
print("\n\nChecking llm library configuration...")
try:
    import inspect
    # Check the prompt method signature
    sig = inspect.signature(model.prompt)
    print(f"Model.prompt signature: {sig}")

    # Check if there's a stream parameter
    params = sig.parameters
    if 'stream' in params:
        print(f"Stream parameter found: {params['stream']}")
    else:
        print("No explicit stream parameter in prompt method")

except Exception as e:
    print(f"Could not inspect method: {e}")