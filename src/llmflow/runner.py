import yaml
import importlib
import inspect
from llmflow.modules.logger import Logger
from pathlib import Path
import re
import mistune
import json
import click
from copy import deepcopy
import os
import sys

from llmflow.utils.llm_runner import call_llm

from llmflow.utils.io import normalize_nfc, validate_all_templates
from llmflow.utils.linter import lint_pipeline_contracts, lint_pipeline_full
from llmflow.modules.json_parser import parse_llm_json_response

from llmflow.plugins import plugin_registry
from llmflow.plugins.loader import load_plugins
load_plugins()

# Single unified logger instance
logger = Logger()

def resolve(value, context, max_depth=5):
    """
    Resolves variables within a value using the provided context.
    Supports both {curly} and ${dollar} notation with dot notation and list indexing.
    Returns native Python objects for exact variable references.
    """
    import re

    logger.debug(f"Resolving value: {value}")
    logger.debug(f"Context keys: {list(context.keys())}")

    def get_from_context(expr, ctx):
        """Resolve dot notation and list indices from context."""
        logger.debug(f"get_from_context called with: {expr}")
        parts = re.split(r'\.(?![^\[]*\])', expr)  # split on dots not inside brackets
        result = ctx
        for part in parts:
            # Handle list index: foo[0]
            m = re.match(r'^([a-zA-Z0-9_]+)(\[(\-?\d+)\])?$', part)
            if not m:
                return None
            key = m.group(1)
            idx = m.group(3)
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
            if idx is not None:
                if isinstance(result, list):
                    try:
                        result = result[int(idx)]
                    except (IndexError, ValueError):
                        return None
                else:
                    return None
            if result is None:
                return None
        logger.debug(f"Resolved {expr} to: {result}")
        return result

    if isinstance(value, str):
        # Handle ${...} syntax (dollar syntax) - with recursive resolution
        pattern_dollar_exact = r'^\$\{([^\}]+)\}$'
        match_dollar_exact = re.match(pattern_dollar_exact, value)
        if match_dollar_exact:
            expr = match_dollar_exact.group(1)
            resolved = get_from_context(expr, context)
            if resolved is not None:
                # RECURSIVE RESOLUTION: If result is still a template, resolve it
                if isinstance(resolved, str) and (resolved.startswith("${") or resolved.startswith("{")):
                    if max_depth > 0:
                        return resolve(resolved, context, max_depth - 1)
                return resolved
            else:
                return value  # fallback to original string if not found

        # Handle {curly} syntax (original syntax) - with recursive resolution
        pattern_curly_exact = r'^\{([^\}]+)\}$'
        match_curly_exact = re.match(pattern_curly_exact, value)
        if match_curly_exact:
            expr = match_curly_exact.group(1)
            resolved = get_from_context(expr, context)
            if resolved is not None:
                # RECURSIVE RESOLUTION: If result is still a template, resolve it
                if isinstance(resolved, str) and (resolved.startswith("${") or resolved.startswith("{")):
                    if max_depth > 0:
                        return resolve(resolved, context, max_depth - 1)
                return resolved
            else:
                return value  # fallback to original string if not found

        # Handle string substitution for both syntaxes
        # First handle ${...} syntax
        pattern_dollar = r'\$\{([^\}]+)\}'
        def replace_dollar_var(match):
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            return str(resolved) if resolved is not None else match.group(0)
        value = re.sub(pattern_dollar, replace_dollar_var, value)

        # Then handle {curly} syntax
        pattern_curly = r'\{([^\}]+)\}'
        def replace_curly_var(match):
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            return str(resolved) if resolved is not None else match.group(0)
        value = re.sub(pattern_curly, replace_curly_var, value)

        return value

    elif isinstance(value, dict):
        return {k: resolve(v, context, max_depth) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve(item, context, max_depth) for item in value]
    return value

def render_prompt(prompt_config, context):
    """Renders a prompt from a file with variable substitution."""
    resolved_prompt = resolve(prompt_config, context)
    prompt_path = Path(resolved_prompt["file"])
    inputs = resolved_prompt.get("inputs", {})

    prompts_dir = Path(context.get("prompts_dir", "prompts"))
    full_prompt_path = prompt_path if prompt_path.is_absolute() else prompts_dir / prompt_path

    logger.debug(f"Loading prompt from: {full_prompt_path}")
    rendered_prompt = full_prompt_path.read_text()

    # Simple template substitution
    for key, val in context.items():
        rendered_prompt = rendered_prompt.replace(f"{{{key}}}", str(val))

    return rendered_prompt

def run_step(rule, context, pipeline_config):
    """Step dispatcher"""
    step_type = rule.get("type", "unknown")
    if step_type == "function":
        run_function_step(rule, context)
    elif step_type == "for-each":
        run_for_each_step(rule, context, pipeline_config)
    elif step_type == "llm":
        run_llm_step(rule, context, pipeline_config)
    elif step_type == "save":
        run_save_step(rule, context)
    else:
        raise ValueError(f"Unknown step type: {step_type}")

def run_for_each_step(rule, context, pipeline_config):
    """Executes a sequence of steps for each item in a resolved input list"""
    step_name = rule.get('name', 'unnamed_for_each_step')
    log_level = rule.get('log', 'debug')

    # Log step start
    logger.info(f"🔄 Starting for-each step: {step_name}")
    logger.debug(f"Step details: {rule}")

    try:
        input_spec = rule["input"]
        item_var = rule["item_var"]
        steps = rule["steps"]

        logger.debug(f"For-each processing: input={input_spec}, item_var={item_var}")

        # Get the list to iterate over
        loop_input = _get_loop_input(input_spec, context, logger)

        logger.debug(f"Iterating over {len(loop_input)} items")

        # Process each item in the list
        for i, item in enumerate(loop_input):
            logger.debug(f"Processing item {i+1}/{len(loop_input)}")

            # Create isolated context for this iteration using deepcopy
            item_context = deepcopy(context)
            item_context[item_var] = item

            # Run all substeps with the isolated context
            for substep in steps:
                run_step(substep, item_context, pipeline_config)

            # Handle append_to operations after all substeps complete
            _handle_append_operations(steps, item_context, context, logger)

        logger.info(f"✅ Completed for-each step: {step_name}")

    except Exception as e:
        logger.error(f"❌ Error in for-each step '{step_name}': {e}")
        raise

def _get_loop_input(input_spec, context, logger):
    """Extract and normalize the input list for iteration"""
    # Support plugin-sourced iteration
    if isinstance(input_spec, dict) and "type" in input_spec:
        plugin_type = input_spec["type"]
        if plugin_type not in plugin_registry:
            raise ValueError(f"Plugin '{plugin_type}' not found.")
        plugin_func = plugin_registry[plugin_type]
        return list(plugin_func(input_spec))

    # Resolve variable reference like "${scene_list}"
    loop_input = resolve(input_spec, context)

    # Handle JSON strings
    if isinstance(loop_input, str):
        loop_input = _parse_json_string(loop_input, logger)

    # Ensure we have a list
    if not isinstance(loop_input, list):
        logger.debug(f"Input is not a list, wrapping as single item")
        loop_input = [loop_input]

    return loop_input

def _parse_json_string(json_str, logger):
    """Parse a JSON string, handling code fences and fallbacks"""
    logger.debug(f"Parsing JSON string: {json_str[:100]}...")

    # Extract from code fences if present
    code_fence_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    fence_matches = re.findall(code_fence_pattern, json_str)

    if fence_matches:
        logger.debug("Found code fence, extracting content")
        json_str = fence_matches[-1].strip()

    # Try direct JSON parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Fallback: extract first JSON array
        array_match = re.search(r'(\[[^\]]*\])', json_str, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group(1))
            except json.JSONDecodeError:
                pass

    # Last resort: wrap as single item
    return [json_str]

def _handle_append_operations(steps, item_context, main_context, logger):
    """Handle append_to operations from substeps, avoiding duplicates"""
    for substep in steps:
        if "append_to" not in substep:
            continue

        target_list = substep["append_to"]
        result = _get_substep_result(substep, item_context)

        if result is None:
            continue

        # Initialize list in main context if needed
        if target_list not in main_context:
            main_context[target_list] = []

        # Append only the new result from this iteration
        main_context[target_list].append(result)
        logger.debug(f"Appended to {target_list}: now has {len(main_context[target_list])} items")

def _get_substep_result(substep, context):
    """Extract the result value from a substep's outputs"""
    outputs = substep.get("outputs")
    if not outputs:
        return None

    if isinstance(outputs, str):
        return context.get(outputs)
    elif isinstance(outputs, list) and outputs:
        return context.get(outputs[0])

    return None

def run_function_step(rule, context):
    """Execute a function step with proper variable resolution"""
    name = rule.get("name", "unnamed")
    function_name = rule["function"]
    inputs = rule.get("inputs", {})
    outputs = rule.get("outputs")

    logger.info(f"🔧 Starting function step: {name}")
    logger.debug(f"Function: {function_name}")

    try:
        # Import and get the function
        module_name, func_name = function_name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)

        # Resolve all input variables
        resolved_inputs = {key: resolve(value, context) for key, value in inputs.items()}

        # Call function with context if it accepts it
        sig = inspect.signature(func)
        if 'context' in sig.parameters:
            result = func(**resolved_inputs, context=context)
        else:
            result = func(**resolved_inputs)

        # Handle outputs
        if outputs is not None:
            if isinstance(outputs, str):
                context[outputs] = result
            elif isinstance(outputs, list):
                if len(outputs) == 1:
                    context[outputs[0]] = result
                else:
                    # Multiple outputs - unpack result
                    for i, output_name in enumerate(outputs):
                        if isinstance(result, (tuple, list)) and i < len(result):
                            context[output_name] = result[i]
                        else:
                            context[output_name] = result

        # Handle append_to if specified
        if "append_to" in rule and result is not None:
            list_name = rule["append_to"]
            if list_name not in context:
                context[list_name] = []
            context[list_name].append(result)

        logger.info(f"✅ Completed function step: {name}")

        # Handle saveas output
        handle_step_output(rule, context)

    except Exception as e:
        logger.error(f"❌ Error in function step '{name}': {e}")
        raise

def run_llm_step(rule, context, pipeline_config):
    """Executes a single LLM step with logging"""
    name = rule.get('name', 'unnamed_llm_step')

    logger.info(f"🤖 Starting LLM step: {name}")
    logger.debug(f"Step details: {rule}")

    try:
        rendered_prompt = render_prompt(rule["prompt"], context)

        # Build merged config
        llm_config = pipeline_config.get("llm_config", {})
        step_config = rule.get("llm_options", {})
        merged_config = {
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 2500,
            "timeout_seconds": 30
        }
        merged_config.update(llm_config)
        merged_config.update(step_config)

        output_type = rule.get("output_type", "text")
        logger.info(f"    ⏳ Calling {merged_config.get('model')} for step '{name}'...")

        # Single unified call
        result = call_llm(rendered_prompt, config=merged_config, output_type=output_type)

        # Check for templates
        if "template" in rule or "format_with" in rule:
            template_path = rule.get("template") or rule.get("format_with")
            result = apply_output_template(result, template_path, context)

        # Handle outputs
        outputs = rule.get("outputs")
        if outputs is not None:
            if isinstance(outputs, str):
                context[outputs] = result
            elif isinstance(outputs, list):
                if len(outputs) == 1:
                    context[outputs[0]] = result
                else:
                    for i, output_name in enumerate(outputs):
                        if isinstance(result, (tuple, list)) and i < len(result):
                            context[output_name] = result[i]
                        else:
                            context[output_name] = result

        # Handle append_to if specified
        if "append_to" in rule and result is not None:
            list_name = rule["append_to"]
            if list_name not in context:
                context[list_name] = []
            context[list_name].append(result)

        logger.info(f"✅ Completed LLM step: {name}")

        # Log outputs
        if outputs:
            result_dict = {}
            if isinstance(outputs, str):
                result_dict[outputs] = context[outputs]
            elif isinstance(outputs, list):
                for output_name in outputs:
                    if output_name in context:
                        result_dict[output_name] = context[output_name]
            logger.debug(f"Step outputs: {result_dict}")

        # Handle saveas output
        handle_step_output(rule, context)

    except Exception as e:
        logger.error(f"❌ Error in LLM step '{name}': {e}")
        raise

def run_save_step(rule, context):
    """Save data from context to file"""
    name = rule.get('name', 'unnamed_save_step')
    log_level = rule.get('log', 'debug')

    logger.info(f"💾 Starting save step: {name}")
    logger.debug(f"Step details: {rule}")

    try:
        # Resolve the input expression
        input_expr = rule.get("input", "")
        if not input_expr:
            raise ValueError(f"Save step '{name}' missing 'input' field")

        value = resolve(input_expr, context)

        # Get filename and format
        filename = rule.get("filename", "")
        if not filename:
            raise ValueError(f"Save step '{name}' missing 'filename' field")

        fmt = rule.get("format", "text").lower()
        _save_file_by_format(value, filename, fmt)

        logger.info(f"✅ Completed save step: {name}")

        return f"Saved to {filename}"

    except Exception as e:
        logger.error(f"❌ Error in save step '{name}': {e}")
        raise

def handle_step_output(rule, context):
    """Handle saveas output for pipeline steps."""
    if "saveas" in rule:
        saveas_config = rule["saveas"]
        outputs = rule.get("outputs")

        if isinstance(saveas_config, str):
            # Simple syntax
            resolved_path = resolve(saveas_config, context)
            if isinstance(outputs, list):
                content = context[outputs[0]]
            elif isinstance(outputs, str):
                content = context[outputs]
            else:
                raise ValueError("Cannot determine content to save - no outputs specified")
            save_content_to_file(content, resolved_path)

        elif isinstance(saveas_config, list):
            # Array syntax: multiple destinations
            for save_item in saveas_config:
                if isinstance(save_item, dict):
                    path = resolve(save_item["path"], context)

                    # Get content and RESOLVE dot notation
                    if "content" in save_item:
                        content_spec = save_item["content"]
                        content = resolve(content_spec, context)
                    elif isinstance(outputs, list):
                        content_var = outputs[0]
                        content = context[content_var]
                    elif isinstance(outputs, str):
                        content_var = outputs
                        content = context[content_var]
                    else:
                        raise ValueError("Cannot determine content to save")

                    format_type = save_item.get("format", "auto")
                    save_content_to_file(content, path, format_type)

def save_content_to_file(content, path, format_type="auto"):
    """Save content to file with format detection"""
    file_path = Path(path)

    # Auto-detect format from extension
    if format_type == "auto":
        ext = file_path.suffix.lower()
        if ext == ".json":
            format_type = "json"
        elif ext in [".md", ".txt"]:
            format_type = "text"

    _save_file_by_format(content, str(file_path), format_type)
    return str(file_path)

def validate_pipeline_expressions(step_inputs, context):
    """
    Raise an error if any input value contains an unresolvable ${...} expression.
    """
    if isinstance(step_inputs, str):
        resolved = resolve(step_inputs, context)
        # If unresolved, it will still contain ${...}
        if isinstance(resolved, str) and "${" in resolved:
            # Instead of regex, just raise error for any remaining ${...}
            unresolved_vars = []
            idx = 0
            while idx < len(resolved):
                start = resolved.find("${", idx)
                if start == -1:
                    break
                end = resolved.find("}", start)
                if end == -1:
                    break
                unresolved_vars.append(resolved[start:end+1])
                idx = end + 1
            for expr in unresolved_vars:
                raise ValueError(f"Unresolved pipeline expression: {expr} in value '{step_inputs}'")
    elif isinstance(step_inputs, dict):
        for v in step_inputs.values():
            validate_pipeline_expressions(v, context)
    elif isinstance(step_inputs, list):
        for item in step_inputs:
            validate_pipeline_expressions(item, context)

def collect_all_templates(steps):
    """
    Recursively collect all template paths from pipeline steps, including:
    - Direct template_path references in function steps
    - Templates referenced in .gpt prompt files
    - Nested steps in for-each loops
    """
    templates = []

    for step in steps:
        step_name = step.get("name", "unnamed")

        # Check for direct template_path in inputs
        inputs = step.get("inputs", {})
        template_path = inputs.get("template_path")
        if template_path:
            templates.append((template_path, step_name))

        # Check for prompt files that might contain templates
        if step.get("type") == "llm":
            prompt_config = step.get("prompt", {})
            prompt_file = prompt_config.get("file")
            if prompt_file:
                # We need to scan the .gpt file for template references
                # Add this to templates list for validation
                templates.append((f"prompts/{prompt_file}", f"{step_name} (prompt file)"))

        # Recursively check nested steps (for-each, etc.)
        if step.get("type") == "for-each":
            nested_steps = step.get("steps", [])
            templates.extend(collect_all_templates(nested_steps))

    return templates

def run_pipeline(pipeline_path, vars=None, dry_run=False, skip_lint=False, verbose=False):
    """Execute a YAML-defined pipeline with template validation"""
    variables = vars or {}

    # Clear the log file at the start of a new run
    open('llmflow.log', 'w').close()

    # Load pipeline FIRST before using any variables from it - with friendly error handling
    # Strict YAML linting before validation
    try:
        from ruamel.yaml import YAML
        yaml_linter = YAML(typ='safe')
        with open(pipeline_path, encoding="utf-8") as f:
            pipeline = yaml_linter.load(f)
        # Minimal Pydantic validation
        from pydantic import ValidationError
        from llmflow.pipeline_schema import PipelineConfig, StepConfig
        pipeline_root = pipeline.get("pipeline", pipeline)
        # Validate top-level pipeline config
        try:
            PipelineConfig(**pipeline_root)
        except ValidationError as e:
            print("\n[ERROR] Pipeline config validation failed:")
            print(e)
            raise SystemExit(1)
        # Validate each step strictly
        for idx, step in enumerate(pipeline_root.get("steps", [])):
            try:
                StepConfig(**step)
            except ValidationError as e:
                print(f"\n[ERROR] Step {idx+1} ('{step.get('name','unnamed')}') validation failed:")
                print(e)
                raise SystemExit(1)

    except FileNotFoundError:
        # Get both relative and absolute paths for helpful error message
        pipeline_file = Path(pipeline_path)
        current_dir = Path.cwd()
        abs_path = pipeline_file.resolve()

        logger.error(f"❌ Pipeline file not found:")
        logger.error(f"   Looking for: {pipeline_path}")
        logger.error(f"   Absolute path: {abs_path}")
        logger.error(f"   Current directory: {current_dir}")
        logger.error(f"   Are you running from the correct directory?")

        # List available pipeline files if pipelines directory exists
        pipelines_dir = current_dir / "pipelines"
        if pipelines_dir.exists() and pipelines_dir.is_dir():
            yaml_files = list(pipelines_dir.glob("*.yaml")) + list(pipelines_dir.glob("*.yml"))
            if yaml_files:
                logger.error(f"   Available pipelines in {pipelines_dir}:")
                for yaml_file in sorted(yaml_files):
                    logger.error(f"     - {yaml_file.name}")

        raise SystemExit(1)
    except Exception as e:
        logger.error(f"❌ Error reading pipeline file '{pipeline_path}': {e}")
        raise SystemExit(1)

    pipeline_root = pipeline.get("pipeline", pipeline)

    # Get steps EARLY so we can use rules
    rules = pipeline_root.get("steps", pipeline_root.get("rules", []))

    # Log and display the run mode
    if dry_run:
        logger.info(f"[DRY RUN] Simulating: {pipeline_path}")
    else:
        logger.info(f"[LIVE RUN] Running: {pipeline_path}")

    logger.debug(f"Variables: {variables}")
    total_steps = len(rules)
    logger.info(f"Found {total_steps} steps to execute")

    # Initialize context first for template validation
    context = dict(pipeline_root.get("variables", {}))
    context.update(variables)

    # Preflight validation
    if not skip_lint:
        # Run full pipeline validation (includes template validation)
        try:
            lint_pipeline_full(pipeline_path)
        except Exception as e:
            logger.error(f"ERROR in lint_pipeline_full: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    else:
        # Just validate templates if linting is skipped
        logger.info("🔍 Validating pipeline templates...")
        try:
            validate_all_templates(pipeline_root)
            logger.info("✅ All templates validated successfully")
        except Exception as e:
            logger.error(f"Template validation failed: {e}")
            raise

    # Show execution is starting
    if not dry_run:
        logger.info("\n🎯 Starting pipeline execution...")
        import sys
        sys.stdout.flush()
        # Flush all logger handlers too
        for handler in logger.logger.handlers:
            handler.flush()
    else:
        logger.info("\n[DRY RUN] Skipping execution")

    # For each step execution
    for rule in rules:
        name = rule.get("name", "unnamed")

        if dry_run:
            logger.info(f"Would run: {name}")
            continue

        try:
            # Step logging is handled within each step function
            run_step(rule, context, pipeline_root)
        except Exception as e:
            logger.error(f"Step '{name}' failed: {e}")
            raise

        logger.debug(f"Context after step {name}: {list(context.keys())}")

    logger.info("Pipeline complete.")

    return context  # Return the final context instead of None

def apply_output_template(result, template_path, context):
    """Apply a template to format step output"""
    from llmflow.utils.io import render_markdown_template

    # Create template variables with the resultz
    template_vars = context.copy()
    template_vars['result'] = result

    # Render the template WITH CONTEXT
    formatted = render_markdown_template(
        template_path=template_path,
        variables=template_vars,
        context=context  # ADD THIS LINE - pass the full context for resolution
    )
    return formatted

def _save_file_by_format(value, filename, fmt):
    """Save value to file in specified format"""
    import json
    import yaml

    # Ensure output directory exists
    output_dir = os.path.dirname(filename)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if fmt == "json":
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
    elif fmt == "yaml":
        with open(filename, "w", encoding="utf-8") as f:
            yaml.dump(value, f, default_flow_style=False, allow_unicode=True)
    else:  # text, markdown, or any other format
        content = _value_to_string(value)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

def _value_to_string(value):
    """Convert any value to string representation"""
    if isinstance(value, str):
        return value
    elif isinstance(value, (list, tuple)):
        return "\n".join(str(item) for item in value)
    else:
        return str(value)
