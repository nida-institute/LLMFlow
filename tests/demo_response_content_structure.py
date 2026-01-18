#!/usr/bin/env python3
"""Test to understand Response API message content structure."""

import json
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
print("CALL 1: Initial request with tools")
print("=" * 80)

response1 = client.responses.create(
    model="gpt-5",
    input=[
        {"type": "message", "role": "user", "content": "What's the weather in Seattle?"}
    ],
    tools=tools
)

print(f"Status: {response1.status}")
print(f"Output items: {len(response1.output)}")

# Extract function call
function_call_item = None
reasoning_item = None

for item in response1.output:
    print(f"\nItem type: {item.type}")
    print(f"Item id: {item.id}")

    if item.type == "function_call":
        function_call_item = item
        print(f"  call_id: {item.call_id}")
        print(f"  name: {item.name}")
        print(f"  arguments: {item.arguments}")
    elif item.type == "reasoning":
        reasoning_item = item
        print(f"  summary type: {type(item.summary)}")
        print(f"  summary value: {repr(item.summary)}")

if not function_call_item:
    print("\n❌ No function call found!")
    exit(1)

print("\n" + "=" * 80)
print("CALL 2: With function result")
print("=" * 80)

# Build input with conversation history
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
    input_items.append(reasoning_dict)

# Add function_call item
input_items.append({
    "type": "function_call",
    "id": function_call_item.id,
    "call_id": function_call_item.call_id,
    "name": function_call_item.name,
    "arguments": function_call_item.arguments
})

# Add function result
input_items.append({
    "type": "function_call_output",
    "call_id": function_call_item.call_id,
    "output": json.dumps({"temperature": 72, "condition": "sunny"})
})

print("Input to send:")
for i, item in enumerate(input_items):
    print(f"  {i}: {item['type']}")

try:
    response2 = client.responses.create(
        model="gpt-5",
        input=input_items,
        tools=tools
    )

    print(f"\n✅ SUCCESS!")
    print(f"Status: {response2.status}")
    print(f"Output items: {len(response2.output)}")

    for i, item in enumerate(response2.output):
        print(f"\n--- Output item {i} ---")
        print(f"Type: {item.type}")
        print(f"All attributes: {[attr for attr in dir(item) if not attr.startswith('_')]}")

        if item.type == "message":
            print(f"  content TYPE: {type(item.content)}")
            print(f"  content VALUE: {repr(item.content)}")

            # Check if content is an array
            if isinstance(item.content, list):
                print(f"  content is LIST with {len(item.content)} items")
                for j, content_item in enumerate(item.content):
                    print(f"    [{j}] type: {type(content_item)}")
                    if hasattr(content_item, 'type'):
                        print(f"    [{j}] item.type: {content_item.type}")
                    if hasattr(content_item, 'text'):
                        print(f"    [{j}] item.text: {repr(content_item.text[:100])}")
            else:
                print(f"  content is STRING: {repr(item.content[:100])}")

        elif item.type == "text":
            print(f"  text TYPE: {type(item.text)}")
            print(f"  text VALUE: {repr(item.text[:100])}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
