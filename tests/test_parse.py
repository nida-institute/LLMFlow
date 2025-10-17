#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')

from llmflow.utils.data import parse_bible_reference

# Test the function directly
print("Testing parse_bible_reference...")
try:
    result = parse_bible_reference("Psalm 1")
    print(f"Success! Result: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()