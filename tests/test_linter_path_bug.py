import os
from pathlib import Path

def test_linter_path_resolution_bug():
    """Test to isolate the linter path resolution issue"""

    pipeline_path = "pipelines/storyflow-psalms-editing.yaml"

    try:
        # Use the correct function name from the available list
        from llmflow.utils.linter import lint_pipeline_full

        print(f"Current directory: {os.getcwd()}")
        print(f"Pipeline path: {pipeline_path}")
        print(f"Pipeline exists: {Path(pipeline_path).exists()}")

        # Run the full linter and catch the specific error
        try:
            result = lint_pipeline_full(pipeline_path)
            print(f"Linter result: {result}")
        except Exception as lint_error:
            print(f"Linter error: {lint_error}")

            # Let's manually check what the linter is trying to do
            try:
                from llmflow.utils.linter import validate_step_prompt_contract

                # Test the specific function that's failing
                import yaml
                with open(pipeline_path) as f:
                    pipeline = yaml.safe_load(f)

                # Get the first failing step
                steps = pipeline.get("steps", [])
                llm_steps = [s for s in steps if s.get("type") == "llm"]

                if llm_steps:
                    step = llm_steps[0]
                    print(f"\nTesting step: {step.get('name')}")

                    # Try to validate this step's contract manually
                    try:
                        validate_step_prompt_contract(step, pipeline.get("variables", {}), Path(pipeline_path).parent)
                        print("Step validation succeeded!")
                    except Exception as step_error:
                        print(f"Step validation error: {step_error}")
                        print(f"Error type: {type(step_error)}")

                        # Debug what paths it's trying
                        variables = pipeline.get("variables", {})
                        prompts_dir = variables.get("prompts_dir", "")
                        prompt_file = step.get("prompt", {}).get("file", "")

                        print(f"Variables: {variables}")
                        print(f"Prompts dir: '{prompts_dir}'")
                        print(f"Prompt file: '{prompt_file}'")
                        print(f"Pipeline parent: {Path(pipeline_path).parent}")

                        # Test different base paths
                        test_bases = [
                            Path.cwd(),
                            Path(pipeline_path).parent,
                            Path(pipeline_path).parent.parent
                        ]

                        for base in test_bases:
                            test_path = base / prompts_dir / prompt_file
                            print(f"Testing: {test_path} - Exists: {test_path.exists()}")

            except ImportError as validate_error:
                print(f"Could not import validate_step_prompt_contract: {validate_error}")

    except ImportError as e:
        print(f"Could not import lint_pipeline_full: {e}")

def test_manual_contract_validation():
    """Manually test what the contract validation is doing"""

    # Let's manually check how the linter validates contracts
    pipeline_path = "pipelines/storyflow-psalms-editing.yaml"

    import yaml
    with open(pipeline_path) as f:
        pipeline = yaml.safe_load(f)

    variables = pipeline.get("variables", {})
    prompts_dir = variables.get("prompts_dir", "")

    print(f"Manual check:")
    print(f"  prompts_dir from YAML: '{prompts_dir}'")

    # Get a failing step
    steps = pipeline.get("steps", [])
    llm_steps = [s for s in steps if s.get("type") == "llm"]

    if llm_steps:
        step = llm_steps[0]  # First LLM step
        print(f"  First LLM step: {step.get('name')}")

        prompt_config = step.get("prompt", {})
        if isinstance(prompt_config, dict) and "file" in prompt_config:
            prompt_file = prompt_config["file"]
            print(f"  Prompt file: '{prompt_file}'")

            # Try to construct the full path like the linter should
            full_path = Path(prompts_dir) / prompt_file
            print(f"  Constructed path: {full_path}")
            print(f"  Path exists: {full_path.exists()}")

            # Try relative to pipeline directory
            pipeline_dir = Path(pipeline_path).parent
            alt_path = pipeline_dir / prompts_dir / prompt_file
            print(f"  Alternative path: {alt_path}")
            print(f"  Alt path exists: {alt_path.exists()}")

def test_direct_linter_call():
    """Test calling the linter functions directly to see exact error"""

    try:
        from llmflow.utils.linter import validate_all_step_contracts

        pipeline_path = "pipelines/storyflow-psalms-editing.yaml"

        import yaml
        with open(pipeline_path) as f:
            pipeline_data = yaml.safe_load(f)

        print(f"Testing validate_all_step_contracts directly...")
        print(f"Pipeline data type: {type(pipeline_data)}")
        print(f"Pipeline data keys: {list(pipeline_data.keys())}")

        # The error suggests we're passing the wrong structure
        # Let's try different approaches

        try:
            # Approach 1: Pass the steps directly
            steps = pipeline_data.get("steps", [])
            print(f"Number of steps: {len(steps)}")
            print(f"First step type: {type(steps[0]) if steps else 'No steps'}")

            result = validate_all_step_contracts(steps, Path(pipeline_path).parent)
            print(f"Validation result (steps): {result}")

        except Exception as e1:
            print(f"Error with steps approach: {e1}")

            try:
                # Approach 2: Maybe it needs variables too?
                variables = pipeline_data.get("variables", {})
                result = validate_all_step_contracts(steps, Path(pipeline_path).parent, variables)
                print(f"Validation result (with variables): {result}")

            except Exception as e2:
                print(f"Error with variables approach: {e2}")

                # Let's look at the function signature
                import inspect
                sig = inspect.signature(validate_all_step_contracts)
                print(f"Function signature: {sig}")

                # Try to call it with minimal args
                try:
                    # Maybe it just needs the individual step?
                    if steps:
                        step = steps[0]  # First LLM step
                        print(f"Testing single step: {step.get('name')}")
                        print(f"Step type: {step.get('type')}")

                        # Look for a single step validation function
                        from llmflow.utils.linter import validate_step_prompt_contract

                        try:
                            result = validate_step_prompt_contract(step, variables, Path(pipeline_path).parent)
                            print(f"Single step validation succeeded!")
                        except Exception as step_error:
                            print(f"Single step validation error: {step_error}")
                            print(f"Step error type: {type(step_error)}")

                            # This should be the actual path resolution error
                            if "not found" in str(step_error).lower() or "no such file" in str(step_error).lower():
                                print(f"🎯 FOUND THE PATH ISSUE: {step_error}")

                                # Let's see what exact path it's looking for
                                error_msg = str(step_error)
                                print(f"Full error message: {error_msg}")

                except ImportError as import_err:
                    print(f"Could not import validate_step_prompt_contract: {import_err}")

    except ImportError as e:
        print(f"Could not import validate_all_step_contracts: {e}")

        # Let's just see what functions are actually available and try them
        try:
            import llmflow.utils.linter as linter_mod
            available = [name for name in dir(linter_mod)
                        if not name.startswith('_') and callable(getattr(linter_mod, name))]
            print(f"Available callable functions: {available}")

            # Try each function that might be related to validation
            validation_funcs = [name for name in available if 'validate' in name.lower()]
            print(f"Validation functions: {validation_funcs}")

            for func_name in validation_funcs:
                try:
                    func = getattr(linter_mod, func_name)
                    sig = inspect.signature(func)
                    print(f"{func_name}: {sig}")
                except Exception as sig_error:
                    print(f"Could not get signature for {func_name}: {sig_error}")

        except Exception as explore_error:
            print(f"Could not explore linter module: {explore_error}")

def test_find_actual_validation_error():
    """Try to trigger the exact same error that the CLI is showing"""

    try:
        # Let's try to replicate the exact same call that the CLI makes
        from llmflow.utils.linter import lint_pipeline_contracts

        pipeline_path = "pipelines/storyflow-psalms-editing.yaml"

        print(f"Testing lint_pipeline_contracts (the function CLI probably uses)...")

        try:
            result = lint_pipeline_contracts(pipeline_path)
            print(f"lint_pipeline_contracts result: {result}")
        except Exception as e:
            print(f"lint_pipeline_contracts error: {e}")
            print(f"Error type: {type(e)}")

            # This should be the exact same error as the CLI
            error_msg = str(e)
            if "not found" in error_msg.lower():
                print(f"🎯 FOUND THE EXACT CLI ERROR: {e}")

                # Parse the error to see what path it's looking for
                print(f"Full error: {error_msg}")

    except ImportError as e:
        print(f"Could not import lint_pipeline_contracts: {e}")

        # Let's try the other functions we know exist
        try:
            from llmflow.utils.linter import lint_pipeline_full

            result = lint_pipeline_full(pipeline_path)
            print(f"lint_pipeline_full succeeded: {result}")

        except Exception as full_error:
            print(f"lint_pipeline_full error: {full_error}")
            print(f"This is probably the real issue: {full_error}")

def test_debug_validate_step_prompt_contract():
    """Debug exactly what validate_step_prompt_contract is doing"""
    
    try:
        from llmflow.utils.linter import validate_step_prompt_contract
        import inspect
        
        # Look at the source code of this function
        print("Function signature:")
        sig = inspect.signature(validate_step_prompt_contract)
        print(f"  {sig}")
        
        # Get source if possible
        try:
            source = inspect.getsource(validate_step_prompt_contract)
            print("Function source (first 20 lines):")
            lines = source.split('\n')[:20]
            for i, line in enumerate(lines, 1):
                print(f"  {i:2d}: {line}")
        except:
            print("Could not get source code")
            
        # Now let's test it manually with correct parameters
        pipeline_path = "pipelines/storyflow-psalms-editing.yaml"
        
        import yaml
        with open(pipeline_path) as f:
            pipeline_data = yaml.safe_load(f)
        
        # Get the first LLM step
        steps = pipeline_data.get("steps", [])
        llm_steps = [s for s in steps if s.get("type") == "llm"]
        
        if llm_steps:
            step = llm_steps[0]
            print(f"\nTesting step: {step.get('name')}")
            
            # Try different approaches to call the function
            approaches = [
                ("Just step", [step]),
                ("Step + empty vars", [step, {}]),
                ("Step + vars + pipeline_root", [step, pipeline_data.get("variables", {}), Path(pipeline_path).parent]),
                ("Step + vars + pipeline_path", [step, pipeline_data.get("variables", {}), pipeline_path]),
                ("Step + vars + str_path", [step, pipeline_data.get("variables", {}), str(Path(pipeline_path).parent)]),
            ]
            
            for name, args in approaches:
                try:
                    print(f"\nTrying {name} with args: {[type(arg).__name__ for arg in args]}")
                    result = validate_step_prompt_contract(*args)
                    print(f"  ✅ Success: {result}")
                    break  # If one works, we found the right signature
                except Exception as e:
                    print(f"  ❌ Failed: {e}")
                    
    except ImportError as e:
        print(f"Could not import validate_step_prompt_contract: {e}")

def test_trace_exact_path_resolution():
    """Trace exactly how the linter resolves prompt file paths"""
    
    # Let's manually walk through what the linter should be doing
    pipeline_path = "pipelines/storyflow-psalms-editing.yaml"
    
    import yaml
    with open(pipeline_path) as f:
        pipeline_data = yaml.safe_load(f)
    
    variables = pipeline_data.get("variables", {})
    steps = pipeline_data.get("steps", [])
    
    print("=== MANUAL PATH RESOLUTION TRACE ===")
    print(f"Pipeline file: {pipeline_path}")
    print(f"Pipeline directory: {Path(pipeline_path).parent}")
    print(f"Variables: {variables}")
    
    # Find the first LLM step
    llm_steps = [s for s in steps if s.get("type") == "llm"]
    if llm_steps:
        step = llm_steps[0]
        step_name = step.get("name")
        prompt_config = step.get("prompt", {})
        
        print(f"\nStep: {step_name}")
        print(f"Prompt config: {prompt_config}")
        
        if isinstance(prompt_config, dict) and "file" in prompt_config:
            prompt_file = prompt_config["file"]
            print(f"Prompt file (raw): '{prompt_file}'")
            
            # The linter should be doing this:
            # 1. Get the prompts_dir variable
            prompts_dir = variables.get("prompts_dir", "")
            print(f"prompts_dir variable: '{prompts_dir}'")
            
            # 2. Construct the full path
            if prompts_dir:
                # What the linter SHOULD do:
                pipeline_root = Path(pipeline_path).parent
                full_path = pipeline_root / prompts_dir / prompt_file
                print(f"Expected full path: {full_path}")
                print(f"File exists: {full_path.exists()}")
                
                # What the linter might actually be doing (incorrectly):
                wrong_paths = [
                    Path(prompt_file),  # Just the filename
                    Path(pipeline_path).parent / prompt_file,  # No prompts_dir
                    Path(prompts_dir) / prompt_file,  # No pipeline_root
                ]
                
                print(f"\nPossible incorrect paths the linter might be checking:")
                for i, wrong_path in enumerate(wrong_paths, 1):
                    print(f"  {i}. {wrong_path} - Exists: {wrong_path.exists()}")
                
                # The error message shows it's looking for just the filename
                # This suggests the linter is NOT using prompts_dir at all
                print(f"\n🎯 LIKELY ISSUE: Linter is looking for '{prompt_file}' instead of '{full_path}'")
                print("This means the linter is not resolving the prompts_dir variable!")