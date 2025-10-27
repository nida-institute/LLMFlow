from pathlib import Path

import yaml


def test_linter_path_fix():
    """Test the correct path resolution logic"""

    # Use correct pipeline path
    pipeline_path = "pipelines/storyflow-test.yaml"

    # Load pipeline
    with open(pipeline_path) as f:
        pipeline_data = yaml.safe_load(f)

    variables = pipeline_data.get("variables", {})
    prompts_dir = variables.get("prompts_dir", "")

    # Get first LLM step
    steps = pipeline_data.get("steps", [])
    llm_steps = [s for s in steps if s.get("type") == "llm"]
    step = llm_steps[0] if len(llm_steps) > 0 else None
    prompt_file = step.get("prompt", {}).get("file", "") if step is not None else ""

    print("=== PATH RESOLUTION COMPARISON ===")

    # WRONG: What linter currently does
    pipeline_root = Path(pipeline_path).parent  # pipelines/
    wrong_path = pipeline_root / prompts_dir / prompt_file
    print(f"❌ WRONG (current linter): {wrong_path}")
    print(f"   Exists: {wrong_path.exists()}")

    # CORRECT: What it should do
    project_root = Path.cwd()  # /Users/jonathan/github/nida-institute/LLMFlow/
    correct_path = project_root / prompts_dir / prompt_file
    print(f"✅ CORRECT (should be):    {correct_path}")
    print(f"   Exists: {correct_path.exists()}")

    # Alternative: Relative to where the command is run
    relative_path = Path(prompts_dir) / prompt_file
    print(f"📁 RELATIVE (simplest):    {relative_path}")
    print(f"   Exists: {relative_path.exists()}")

    # Test the fix logic
    print("\n=== TESTING FIX LOGIC ===")
    possible_paths = [
        f"prompts/{prompt_file}",
        f"prompts/storyflow/{prompt_file}",
        prompt_file,
    ]

    found_path = None
    for possible_path in possible_paths:
        path_exists = Path(possible_path).exists()
        print(f"Testing: {possible_path} - Exists: {path_exists}")
        if path_exists and not found_path:
            found_path = possible_path

    print(f"\n🎯 FIX RESULT: Found prompt at '{found_path}'")

    assert found_path is not None, "Fix should find the prompt file"
    assert Path(found_path).exists(), "Found path should exist"


def test_simulate_fixed_linter():
    """Simulate how the linter should work after the fix"""

    def find_prompt_file(prompt_file):
        """Simulate the fixed prompt file resolution"""
        possible_paths = [
            f"prompts/{prompt_file}",
            f"prompts/storyflow/{prompt_file}",
            prompt_file,
        ]

        for possible_path in possible_paths:
            if Path(possible_path).exists():
                return possible_path
        return None

    # Test with the actual failing file
    prompt_file = "exegetical-pericope-psalms-e1.gpt"
    found_path = find_prompt_file(prompt_file)

    print(f"Prompt file: {prompt_file}")
    print(f"Found at: {found_path}")
    print(f"File exists: {Path(found_path).exists() if found_path else False}")

    assert found_path is not None, f"Should find {prompt_file}"
    assert found_path == "prompts/storyflow/exegetical-pericope-psalms-e1.gpt"
