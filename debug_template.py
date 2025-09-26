"""Standalone Jinja2 template debugger for LLMFlow"""

import json
import sys
from pathlib import Path

def debug_template(template_path, variables_dict):
    """Debug a Jinja2 template with given variables"""

    # Set up Jinja2 with debug mode
    template_dir = Path(template_path).parent
    template_name = Path(template_path).name

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=DebugUndefined  # This gives better error messages
    )

    template = env.get_template(template_name)

    print("🔍 Template Debugging")
    print("=" * 50)
    print(f"Template: {template_path}")
    print(f"Variables provided:")

    # Pretty print all variables and their types
    for key, value in variables_dict.items():
        print(f"  {key}: {type(value).__name__}")
        if isinstance(value, (list, dict)):
            if isinstance(value, list) and len(value) > 0:
                print(f"    Length: {len(value)}")
                print(f"    First item: {type(value[0]).__name__}")
                if hasattr(value[0], 'keys'):
                    print(f"    Keys: {list(value[0].keys())}")
            elif isinstance(value, dict):
                print(f"    Keys: {list(value.keys())}")
        elif isinstance(value, str):
            print(f"    Length: {len(value)} chars")
            if len(value) > 100:
                print(f"    Preview: {value[:100]}...")
            else:
                print(f"    Value: {value}")
        print()

    print("🚀 Attempting template render...")
    print("=" * 50)

    try:
        result = template.render(**variables_dict)
        print("✅ Template rendered successfully!")
        print(f"Output length: {len(result)} characters")
        print("\n📄 Rendered output:")
        print("-" * 30)
        print(result)
        return result
    except Exception as e:
        print(f"❌ Template render failed: {e}")
        print(f"Error type: {type(e).__name__}")

        # Try to give more specific debugging info
        if "str object has no element" in str(e):
            print("\n🔍 String indexing error detected!")
            print("This usually means you're treating a string like a list/dict.")
            print("Check your variable types above.")

        raise

if __name__ == "__main__":
    # Example usage with your actual data structure

    # Mock your pipeline data
    mock_scenes = [
        {
            'Scene number': 'Scene 1',
            'Citation': 'Psalm 23:1–3',
            'Title': 'The Shepherd Provides and Guides'
        },
        {
            'Scene number': 'Scene 2',
            'Citation': 'Psalm 23:4',
            'Title': 'Comfort in the Valley'
        },
        {
            'Scene number': 'Scene 3',
            'Citation': 'Psalm 23:5–6',
            'Title': 'Abundance and Eternal Presence'
        }
    ]

    mock_scene_steps = [
        {"step1": "Body content 1", "step2": "Heart content 1", "step3": "Connect content 1", "step4": "Name content 1"},
        {"step1": "Body content 2", "step2": "Heart content 2", "step3": "Connect content 2", "step4": "Name content 2"},
        {"step1": "Body content 3", "step2": "Heart content 3", "step3": "Connect content 3", "step4": "Name content 3"}
    ]

    variables = {
        "passage": "Psalm 23",
        "intro": "This is the intro content...",
        "scenes": mock_scenes,
        "scene_steps": mock_scene_steps,
        "summary": "This is the summary content..."
    }

    # Debug the template
    debug_template("templates/leadersguide_template.md", variables)