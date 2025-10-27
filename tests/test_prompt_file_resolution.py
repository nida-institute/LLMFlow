import os
from pathlib import Path

import yaml


def test_prompt_file_resolution():
    """Test that the linter can resolve prompt file paths correctly"""

    # Update to use existing pipeline file
    pipeline_path = "pipelines/storyflow-test.yaml"

    # Check if the actual pipeline file exists and has correct structure
    pipeline_path = Path("pipelines/storyflow-test.yaml")
    assert pipeline_path.exists(), f"Pipeline file not found: {pipeline_path}"

    # Load the pipeline
    with open(pipeline_path) as f:
        pipeline_data = yaml.safe_load(f)

    print(f"Pipeline structure keys: {list(pipeline_data.keys())}")

    # Check variables
    variables = pipeline_data.get("variables", {})
    prompts_dir = variables.get("prompts_dir", "NOT SET")
    print(f"prompts_dir variable: {prompts_dir}")

    # Check if prompts directory exists
    prompts_path = Path(prompts_dir)
    print(f"Prompts directory exists: {prompts_path.exists()}")

    if prompts_path.exists():
        print("Available prompt files:")
        for file in prompts_path.glob("*.gpt"):
            print(f"  - {file.name}")

    # Check specific files that are failing
    required_files = [
        "exegetical-pericope-psalms-e1.gpt",
        "leadersguide-intro.gpt",
        "joshfrost-emotional.gpt",
    ]

    print("\nChecking required files:")
    for filename in required_files:
        file_path = prompts_path / filename
        exists = file_path.exists()
        print(f"  {filename}: {'✅' if exists else '❌'} ({file_path})")

        if exists:
            # Check file is readable and not empty
            try:
                with open(file_path, "r") as f:
                    content = f.read().strip()
                    print(f"    File size: {len(content)} chars")
                    if len(content) == 0:
                        print("    ⚠️  File is empty!")
            except Exception as e:
                print(f"    ❌ Error reading file: {e}")


def test_variable_resolution_in_context():
    """Test if variable resolution works for prompt file paths"""

    # Create a simple test case that mimics the failing scenario
    test_pipeline = {
        "name": "test-prompt-resolution",
        "variables": {"prompts_dir": "prompts/storyflow"},
        "steps": [
            {
                "name": "test_step",
                "type": "llm",
                "prompt": {"file": "exegetical-pericope-psalms-e1.gpt"},
            }
        ],
    }

    # Save to temp file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_pipeline, f)
        temp_pipeline_path = f.name

    print(f"Created test pipeline: {temp_pipeline_path}")

    # Try to validate this simple case
    try:
        # Import what's actually available in the linter
        from llmflow.utils.linter import LintContext

        # Create a lint context to see how it resolves paths
        lint_context = LintContext(temp_pipeline_path)

        print(f"Pipeline root: {lint_context.pipeline_root}")
        print(f"Variables: {lint_context.variables}")

        # Check how it resolves the prompts_dir
        resolved_prompts_dir = lint_context.resolve_variable("${prompts_dir}")
        print(f"Resolved prompts_dir: {resolved_prompts_dir}")

        # Check full file path resolution
        prompt_file = "exegetical-pericope-psalms-e1.gpt"
        full_path = (
            Path(lint_context.pipeline_root) / resolved_prompts_dir / prompt_file
        )
        print(f"Full resolved path: {full_path}")
        print(f"File exists at resolved path: {full_path.exists()}")

    except ImportError as e:
        print(f"Import error: {e}")
        print("Available linter functions:")
        try:
            import llmflow.utils.linter as linter

            print(
                f"  Available: {[name for name in dir(linter) if not name.startswith('_')]}"
            )
        except Exception:
            print("  Could not import linter module")
    except Exception as e:
        print(f"Error during resolution test: {e}")
        import traceback

        traceback.print_exc()

    # Clean up
    os.unlink(temp_pipeline_path)


def test_debug_linter_path_resolution():
    """Debug the exact linter path resolution logic"""

    pipeline_path = "pipelines/storyflow-test.yaml"

    try:
        # First, let's see what's actually in the linter module
        import llmflow.utils.linter as linter_module

        print(
            f"Linter module contents: {[name for name in dir(linter_module) if not name.startswith('_')]}"
        )

        # Try to create a lint context
        from llmflow.utils.linter import LintContext

        # Create lint context same way the real linter does
        lint_context = LintContext(pipeline_path)

        print("=== LINTER DEBUG ===")
        print(f"Pipeline file: {pipeline_path}")
        print(f"Pipeline root: {lint_context.pipeline_root}")
        print(f"Current working dir: {os.getcwd()}")

        # Check variables resolution
        print("\nVariables:")
        for key, value in lint_context.variables.items():
            print(f"  {key}: {value}")

        # Test specific prompt file resolution
        prompts_dir = lint_context.variables.get("prompts_dir", "")
        print(f"\nPrompts directory: '{prompts_dir}'")

        if prompts_dir:
            # Try different path resolution approaches
            approaches = [
                ("Relative to cwd", Path(prompts_dir)),
                (
                    "Relative to pipeline",
                    Path(lint_context.pipeline_root) / prompts_dir,
                ),
                ("Absolute path", Path(prompts_dir).resolve()),
            ]

            for name, path in approaches:
                print(f"\n{name}: {path}")
                print(f"  Exists: {path.exists()}")
                if path.exists():
                    gpt_files = list(path.glob("*.gpt"))
                    print(f"  GPT files found: {len(gpt_files)}")
                    if gpt_files:
                        print(f"  First few: {[f.name for f in gpt_files[:3]]}")

    except ImportError as e:
        print(f"Import error: {e}")
        # Let's try a different approach - check what the runner does
        try:
            from llmflow.runner import load_pipeline_config

            config = load_pipeline_config(pipeline_path)
            print("Pipeline config loaded successfully")
            print(f"Config keys: {list(config.keys())}")
            if "variables" in config:
                print(f"Variables: {config['variables']}")
        except Exception as runner_e:
            print(f"Runner approach failed: {runner_e}")

    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback

        traceback.print_exc()


def test_simple_file_check():
    """Simple test to verify the files actually exist"""

    print(f"Current working directory: {os.getcwd()}")

    # Check basic file structure
    pipeline_file = Path("pipelines/storyflow-test.yaml")
    prompts_dir = Path("prompts/storyflow")

    print(f"Pipeline file exists: {pipeline_file.exists()}")
    print(f"Prompts directory exists: {prompts_dir.exists()}")

    if prompts_dir.exists():
        gpt_files = list(prompts_dir.glob("*.gpt"))
        print(f"Found {len(gpt_files)} .gpt files")

        # Check the specific files that are failing
        failing_files = [
            "exegetical-pericope-psalms-e1.gpt",
            "leadersguide-intro.gpt",
            "joshfrost-emotional.gpt",
        ]

        print("\nSpecific file check:")
        for filename in failing_files:
            filepath = prompts_dir / filename
            exists = filepath.exists()
            print(f"  {filename}: {'✅' if exists else '❌'}")

            if exists:
                # Check if file is readable
                try:
                    with open(filepath, "r") as f:
                        content = f.read()
                        print(
                            f"    Size: {len(content)} chars, First 50: {repr(content[:50])}"
                        )
                except Exception as e:
                    print(f"    Error reading: {e}")
