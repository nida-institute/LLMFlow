#!/usr/bin/env python3
"""Test direct OpenAI API call to verify it works"""

import os
from openai import OpenAI
import time

# Simple direct test
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

print("Testing direct OpenAI API call...")
start_time = time.time()

try:
    # Non-streaming call
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say 'Hello, World!' and nothing else."}],
        max_tokens=50,
        temperature=0.4,
        stream=False  # Explicitly disable streaming
    )

    print(f"Response received in {time.time() - start_time:.2f} seconds")
    print(f"Response: {response.choices[0].message.content}")

    # Now test with streaming
    print("\nTesting with streaming=True...")
    start_time = time.time()

    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Count from 1 to 5."}],
        max_tokens=50,
        temperature=0.4,
        stream=True
    )

    print("Streaming response:")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end='', flush=True)

    print(f"\nStreaming completed in {time.time() - start_time:.2f} seconds")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()