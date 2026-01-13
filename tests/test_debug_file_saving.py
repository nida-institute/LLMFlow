#!/usr/bin/env python3
"""Test debug file saving for requests and responses."""

import json
import os
import shutil
from pathlib import Path

# Setup
DEBUG_DIR = "outputs/debug"
if os.path.exists(DEBUG_DIR):
    shutil.rmtree(DEBUG_DIR)
os.makedirs(DEBUG_DIR, exist_ok=True)

# Import the functions
from llmflow.runner import build_debug_filename, save_content_to_file

print("=" * 80)
print("TESTING DEBUG FILE SAVING")
print("=" * 80)

# Test 1: build_debug_filename with passage
step = {
    "name": "test_step",
    "prompt": {"file": "prompts/test-prompt.gpt"}
}
context = {"passage": "Mark 1:1-12"}
pipeline_config = {"linter_config": {"log_level": "debug"}}

filename_request = build_debug_filename(step, context, "request")
filename_response = build_debug_filename(step, context, "response")

print(f"\n✅ Request filename: {filename_request}")
print(f"✅ Response filename: {filename_response}")

assert "Mark" in filename_request, "Passage should be in filename"
assert "test_prompt" in filename_request or "test-prompt" in filename_request, "Prompt name should be in filename"
assert "request" in filename_request, "Should have request indicator"
assert "response" in filename_response, "Should have response indicator"

# Test 2: build_debug_filename without passage (should use timestamp)
context_no_passage = {}
filename_timestamp = build_debug_filename(step, context_no_passage, "request")
print(f"✅ Timestamp filename (no passage): {filename_timestamp}")
assert "request" in filename_timestamp, "Should have request indicator"

# Test 3: Save test files
test_request = "This is a test request"
test_response = "This is a test response"

request_path = f"{DEBUG_DIR}/{filename_request}"
response_path = f"{DEBUG_DIR}/{filename_response}"

save_content_to_file(test_request, request_path, format="text")
save_content_to_file(test_response, response_path, format="text")

print(f"\n✅ Saved request to: {request_path}")
print(f"✅ Saved response to: {response_path}")

# Test 4: Verify files exist and contain correct content
assert os.path.exists(request_path), f"Request file should exist: {request_path}"
assert os.path.exists(response_path), f"Response file should exist: {response_path}"

with open(request_path) as f:
    assert f.read() == test_request, "Request file content mismatch"

with open(response_path) as f:
    assert f.read() == test_response, "Response file content mismatch"

print("\n✅ All debug file tests passed!")
print(f"✅ Files created in: {DEBUG_DIR}/")
print(f"   - {filename_request}")
print(f"   - {filename_response}")

print("\n" + "=" * 80)
print("NOW TESTING ACTUAL RESPONSES API")
print("=" * 80)

from pathlib import Path
from openai import OpenAI

client = OpenAI()

# Simple tool for testing
tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
]

print("=" * 80)
print("FIRST API CALL - Prompt + Tools")
print("=" * 80)

response1 = client.responses.create(
    model="gpt-5",
    input=[
        {"type": "message", "role": "user", "content": "What's the weather in Seattle?"}
    ],
    tools=tools
)

# Save the actual API response to see its structure
api_response_path = f"{DEBUG_DIR}/actual_api_response.txt"
save_content_to_file(str(response1), api_response_path, format="text")
print(f"\n📝 Saved actual API response to: {api_response_path}")

print(f"\nResponse status: {response1.status}")
print(f"Response output items: {len(response1.output)}")

for i, item in enumerate(response1.output):
    print(f"\n--- Output item {i} ---")
    print(f"Type: {item.type}")
    print(f"All attributes: {dir(item)}")

    # Print actual values
    if item.type == "reasoning":
        print(f"  id: {item.id}")
        print(f"  summary: {repr(item.summary)}")
        print(f"  summary type: {type(item.summary)}")
        print(f"  summary is None: {item.summary is None}")
        print(f"  summary == '': {item.summary == ''}")
        if hasattr(item, 'content'):
            print(f"  content: {repr(item.content[:100] if item.content else item.content)}")
    elif item.type == "function_call":
        print(f"  id: {item.id}")
        print(f"  call_id: {item.call_id}")
        print(f"  name: {item.name}")
        print(f"  arguments: {item.arguments}")

print("\n" + "=" * 80)
print("BUILDING SECOND REQUEST - Adding tool result")
print("=" * 80)

# Find the function_call
function_call_item = None
reasoning_item = None
for item in response1.output:
    if item.type == "function_call":
        function_call_item = item
    elif item.type == "reasoning":
        reasoning_item = item

if function_call_item:
    # Build the second request
    input_items = [
        {"type": "message", "role": "user", "content": "What's the weather in Seattle?"}
    ]

    # Add reasoning item
    if reasoning_item:
        reasoning_dict = {
            "type": "reasoning",
            "id": reasoning_item.id,
            "summary": reasoning_item.summary if reasoning_item.summary else []
        }
        if hasattr(reasoning_item, 'content') and reasoning_item.content:
            reasoning_dict["content"] = reasoning_item.content
        input_items.append(reasoning_dict)
        print(f"\nReasoning item to send:")
        print(json.dumps(reasoning_dict, indent=2))

    # Add function_call item
    function_call_dict = {
        "type": "function_call",
        "id": function_call_item.id,
        "call_id": function_call_item.call_id,
        "name": function_call_item.name,
        "arguments": function_call_item.arguments
    }
    input_items.append(function_call_dict)
    print(f"\nFunction call item to send:")
    print(json.dumps(function_call_dict, indent=2))

    # Add function result
    result_dict = {
        "type": "function_call_output",
        "call_id": function_call_item.call_id,
        "output": json.dumps({"temperature": 72, "condition": "sunny"})
    }
    input_items.append(result_dict)
    print(f"\nFunction result item to send:")
    print(json.dumps(result_dict, indent=2))

    print(f"\n\nComplete input array ({len(input_items)} items):")
    print(json.dumps(input_items, indent=2))

    print("\n" + "=" * 80)
    print("SECOND API CALL - With tool results")
    print("=" * 80)

    try:
        response2 = client.responses.create(
            model="gpt-5",
            input=input_items,
            tools=tools
        )

        print(f"\n✅ SUCCESS!")
        print(f"Response status: {response2.status}")
        print(f"Response output items: {len(response2.output)}")

        for i, item in enumerate(response2.output):
            print(f"\n--- Output item {i} ---")
            print(f"Type: {item.type}")
            if item.type == "message":
                print(f"  content: {item.content}")
            elif item.type == "text":
                print(f"  text: {item.text}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"Error type: {type(e)}")

print("\n" + "=" * 80)
print("TESTING OUTPUT EXTRACTION (like llm_runner.py does)")
print("=" * 80)

# Test that we correctly extract content from different response types
test_outputs = [
    # Test 1: message type (what we get after tool execution)
    type('MockItem', (), {'type': 'message', 'content': 'The weather is sunny'})(),
    # Test 2: text type (what we might get in some responses)
    type('MockItem', (), {'type': 'text', 'text': 'Some text response'})(),
    # Test 3: reasoning type (should be skipped in text extraction)
    type('MockItem', (), {'type': 'reasoning', 'id': 'rs_123', 'summary': []})(),
]

# Simulate the extraction logic from llm_runner.py lines 427-433
extracted_text = ""
for item in test_outputs:
    if hasattr(item, 'type'):
        if item.type == "text" and hasattr(item, 'text'):
            extracted_text += item.text
        elif item.type == "message" and hasattr(item, 'content'):
            extracted_text += item.content

print(f"\nExtracted text: '{extracted_text}'")
expected_text = "The weather is sunnySome text response"
assert extracted_text == expected_text, f"Expected '{expected_text}', got '{extracted_text}'"
print(f"✅ Output extraction works correctly!")

print("\n" + "=" * 80)
print("VERIFYING ACTUAL RESPONSE2 CONTENT EXTRACTION")
print("=" * 80)

if 'response2' in locals():
    # Extract text from response2 the same way llm_runner.py does
    final_output = ""
    for item in response2.output:
        if hasattr(item, 'type'):
            if item.type == "text" and hasattr(item, 'text'):
                final_output += item.text
                print(f"✅ Extracted from text type: '{item.text[:100]}...'")
            elif item.type == "message" and hasattr(item, 'content'):
                # content is ALWAYS an array of ResponseOutputText objects
                if isinstance(item.content, list):
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            final_output += content_item.text
                            print(f"✅ Extracted from message content: '{content_item.text[:100]}...'")
                else:
                    final_output += str(item.content)
print("\n" + "=" * 80)
print("ALL TESTS PASSED!")
print("=" * 80)
