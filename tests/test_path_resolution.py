import os
import yaml
from pathlib import Path

def test_pipeline_path_resolution():
    """Test that pipeline can find its prompt files"""
    # Check current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")

    # Check if prompts exist
    prompts_dir = Path("prompts/storyflow")
    assert prompts_dir.exists(), f"Prompts directory not found: {prompts_dir}"

    # List available prompt files
    prompt_files = list(prompts_dir.glob("*.gpt"))
    assert len(prompt_files) > 0, "No .gpt files found in prompts/storyflow"

    print("Available prompt files:")
    for file in prompt_files:
        print(f"  - {file.name}")

    # Check pipeline configuration
    pipeline_path = Path("pipelines/storyflow-psalms-editing.yaml")
    assert pipeline_path.exists(), f"Pipeline file not found: {pipeline_path}"

    with open(pipeline_path) as f:
        pipeline = yaml.safe_load(f)

    # Handle both wrapped and unwrapped pipeline configs
    pipeline_config = pipeline.get("pipeline", pipeline)
    variables = pipeline_config.get("variables", {})

    print(f"\nPipeline variables:")
    for key, value in variables.items():
        print(f"  {key}: {value}")

    # Test prompts_dir variable
    prompts_dir_var = variables.get("prompts_dir")
    assert prompts_dir_var is not None, "prompts_dir variable not set in pipeline"

    resolved_path = Path(prompts_dir_var)
    assert resolved_path.exists(), f"Prompts directory from variable doesn't exist: {resolved_path}"

    # Test that required prompt files exist
    required_files = [
        "exegetical-pericope-psalms-e1.gpt",
        "exegetical-pericope-psalms-e2.gpt",
        "exegetical-pericope-psalms-e3.gpt",
        "leadersguide-intro.gpt",
        "leadersguide-scenes.gpt",
        "joshfrost-emotional.gpt"
    ]

    missing_files = []
    for filename in required_files:
        file_path = resolved_path / filename
        if not file_path.exists():
            missing_files.append(filename)
        else:
            print(f"✅ Found: {filename}")

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        assert False, f"Missing required prompt files: {missing_files}"

    print("✅ All required prompt files found!")