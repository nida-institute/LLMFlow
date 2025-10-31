import importlib
import inspect
import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml

from llmflow.modules.logger import Logger
from llmflow.plugins import plugin_registry
from llmflow.plugins.loader import discover_plugins
from llmflow.utils.io import validate_all_templates
from llmflow.utils.linter import lint_pipeline_full
from llmflow.utils.llm_runner import call_llm

discover_plugins()

# Single unified logger instance
logger = Logger()

# Track files written during a run and emit to both llmflow.log and stdout
WRITTEN_FILES = []


def _record_written_file(path):
    import traceback

    p = Path(path).resolve()
    pstr = str(p)
    if pstr not in WRITTEN_FILES:
        WRITTEN_FILES.append(pstr)
    logger.info(f"Wrote file: {p}")
    logger.debug(
        "Called from:\n" + "".join(traceback.format_stack()[-4:-1])
    )


def resolve(value, context, max_depth=5):
    """
    Resolves variables within a value using the provided context.
    Supports both {curly} and ${dollar} notation with dot notation and list indexing.
    Returns native Python objects for exact variable references.
    Handles Row objects from TSV plugin.
    """
    import re

    logger.debug(f"Resolving value: {value}")
    logger.debug(f"Context keys: {list(context.keys())}")

    def get_from_context(expr, ctx):
        """Resolve dot notation and list indices from context."""
        logger.debug(f"get_from_context called with: {expr}")
        parts = re.split(r"\.(?![^\[]*\])", expr)  # split on dots not inside brackets
        result = ctx
        for part in parts:
            # Handle list index: foo[0]
            m = re.match(r"^([a-zA-Z0-9_]+)(\[(\-?\d+)\])?$", part)
            if not m:
                return None
            key = m.group(1)
            idx = m.group(3)

            if isinstance(result, dict):
                result = result.get(key)
            elif hasattr(result, key):  # FIX: Check hasattr instead of __getattr__
                # Handle Row objects and similar objects with attributes
                try:
                    result = getattr(result, key)
                except AttributeError:
                    return None
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
        pattern_dollar_exact = r"^\$\{([^\}]+)\}$"
        match_dollar_exact = re.match(pattern_dollar_exact, value)
        if match_dollar_exact:
            expr = match_dollar_exact.group(1)
            resolved = get_from_context(expr, context)
            if resolved is not None:
                # RECURSIVE RESOLUTION: If result is still a template, resolve it
                if isinstance(resolved, str) and (
                    resolved.startswith("${") or resolved.startswith("{")
                ):
                    if max_depth > 0:
                        return resolve(resolved, context, max_depth - 1)
                return resolved
            else:
                return value  # fallback to original string if not found

        # Handle {curly} syntax (original syntax) - with recursive resolution
        pattern_curly_exact = r"^\{([^\}]+)\}$"
        match_curly_exact = re.match(pattern_curly_exact, value)
        if match_curly_exact:
            expr = match_curly_exact.group(1)
            resolved = get_from_context(expr, context)
            if resolved is not None:
                # RECURSIVE RESOLUTION: If result is still a template, resolve it
                if isinstance(resolved, str) and (
                    resolved.startswith("${") or resolved.startswith("{")
                ):
                    if max_depth > 0:
                        return resolve(resolved, context, max_depth - 1)
                return resolved
            else:
                return value  # fallback to original string if not found

        # Handle string substitution for both syntaxes
        # First handle ${...} syntax
        pattern_dollar = r"\$\{([^\}]+)\}"

        def replace_dollar_var(match):
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            return str(resolved) if resolved is not None else match.group(0)

        value = re.sub(pattern_dollar, replace_dollar_var, value)

        # Then handle {curly} syntax
        pattern_curly = r"\{([^\}]+)\}"

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


def render_prompt(
    prompt_config: Union[str, Dict[str, Any]], context: Dict[str, Any]
) -> str:
    """Renders a prompt from a file with variable substitution."""
    resolved_prompt = resolve(prompt_config, context)

    # Handle the case where prompt is a dict with 'file' key
    if isinstance(resolved_prompt, dict):
        prompt_file = resolved_prompt.get("file")
        if not isinstance(prompt_file, str):
            raise ValueError(f"Prompt 'file' must be a string, got {type(prompt_file)}")
        prompt_path = Path(prompt_file)
        resolved_prompt.get("inputs", {})
    elif isinstance(resolved_prompt, str):
        # Handle the case where prompt is just a string path
        prompt_path = Path(resolved_prompt)
    else:
        raise ValueError(
            f"Prompt config must be string or dict, got {type(resolved_prompt)}"
        )

    prompts_dir = Path(context.get("prompts_dir", "prompts"))
    full_prompt_path = (
        prompt_path if prompt_path.is_absolute() else prompts_dir / prompt_path
    )

    logger.debug(f"Loading prompt from: {full_prompt_path}")
    rendered_prompt = full_prompt_path.read_text()

    # Simple template substitution
    for key, val in context.items():
        rendered_prompt = rendered_prompt.replace(f"{{{key}}}", str(val))

    return rendered_prompt


def handle_step_outputs(rule: Dict[str, Any], result: Any, context: Dict[str, Any]) -> None:
    """
    Common handler for step outputs, append_to, and saveas.
    Works for all step types: function, llm, plugin, etc.

    Args:
        rule: The step configuration dict
        result: The result value(s) from the step execution
        context: The execution context to update
    """
    step_name = rule.get("name", "unnamed")

    # 1. Handle outputs - store results in context
    outputs = rule.get("outputs")
    if outputs is not None:
        if isinstance(outputs, str):
            context[outputs] = result
            logger.debug(f"Stored result in context['{outputs}']")
        elif isinstance(outputs, list):
            if isinstance(result, (list, tuple)) and len(result) == len(outputs):
                # Multiple results matching multiple output names
                for output_name, result_value in zip(outputs, result):
                    context[output_name] = result_value
                    logger.debug(f"Stored result in context['{output_name}']")
            else:
                # Single result or mismatch - store in first output
                context[outputs[0]] = result
                logger.debug(f"Stored result in context['{outputs[0]}']")

    # 2. Handle append_to - append result to a list
    append_to = rule.get("append_to")
    if append_to:
        if append_to not in context:
            context[append_to] = []

        # Get the value to append (use output variable if specified, otherwise raw result)
        if outputs:
            if isinstance(outputs, str):
                value_to_append = context.get(outputs)
            elif isinstance(outputs, list):
                value_to_append = context.get(outputs[0])
            else:
                value_to_append = result
        else:
            value_to_append = result

        context[append_to].append(value_to_append)
        logger.debug(f"Appended to {append_to}: now has {len(context[append_to])} items")

    # 3. Handle saveas - save result to file(s)
    if "saveas" in rule:
        handle_step_saveas(rule, context)


def handle_step_saveas(rule: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Handle saveas output for pipeline steps."""
    saveas_config = rule["saveas"]
    outputs = rule.get("outputs")

    if isinstance(saveas_config, str):
        # Simple syntax: saveas: "path/to/file.txt"
        resolved_path = resolve(saveas_config, context)

        # Get content from outputs
        if isinstance(outputs, list):
            content = context[outputs[0]]
        elif isinstance(outputs, str):
            content = context[outputs]
        else:
            raise ValueError(
                "Cannot determine content to save - no outputs specified"
            )

        saved_path = save_content_to_file(content, resolved_path)
        _record_written_file(saved_path)

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
                    content = context[outputs[0]]
                elif isinstance(outputs, str):
                    content = context[outputs]
                else:
                    raise ValueError("Cannot determine content to save")

                format_type = save_item.get("format", "auto")
                saved_path = save_content_to_file(content, path, format_type)
                _record_written_file(saved_path)


def run_step(rule, context, pipeline_config):
    """Step dispatcher with unified output handling"""
    step_type = rule.get("type", "unknown")
    step_name = rule.get("name", "unnamed")

    result = None

    try:
        # Execute the appropriate step type
        if step_type == "function":
            result = run_function_step(rule, context)
            # FIX: Don't call handle_step_outputs here - run_function_step already does it
        elif step_type == "for-each":
            run_for_each_step(rule, context, pipeline_config)
            return
        elif step_type == "llm":
            result = run_llm_step(rule, context, pipeline_config)
            # Handle outputs for LLM steps
            handle_step_outputs(rule, result, context)
        elif step_type == "save":
            run_save_step(rule, context)
            return
        elif step_type in plugin_registry:
            result = run_plugin_step(rule, context)
            # Handle outputs for plugin steps
            handle_step_outputs(rule, result, context)
        else:
            raise ValueError(f"Unknown step type: {step_type}")

    except Exception as e:
        logger.error(f"❌ Error in {step_type} step '{step_name}': {e}")
        raise


def run_plugin_step(rule: Dict[str, Any], context: Dict[str, Any]) -> Any:
    """Execute a plugin step and return its result"""
    step_type = rule["type"]
    step_name = rule.get("name", "unnamed")

    logger.info(f"🔌 Starting plugin step: {step_name}")
    plugin_func = plugin_registry[step_type]

    # Resolve all variables in the rule before passing to plugin
    resolved_rule = {}
    for key, value in rule.items():
        if key in ['name', 'type', 'outputs', 'append_to', 'saveas']:
            resolved_rule[key] = value
        else:
            resolved_rule[key] = resolve(value, context)

    # Execute plugin
    results = plugin_func(resolved_rule)

    # Convert generators to lists
    if hasattr(results, '__iter__') and not isinstance(results, (str, dict)):
        try:
            results = list(results)
        except TypeError:
            pass

    logger.info(f"✅ Completed plugin step: {step_name}")
    return results


def run_function_step(rule: Dict[str, Any], context: Dict[str, Any]) -> Any:
    """Execute a function step and return its result"""
    name: str = rule.get("name", "unnamed")
    function_name: str = rule["function"]
    inputs: Union[Dict[str, Any], List[Any]] = rule.get("inputs", {})

    logger.info(f"🔧 Starting function step: {name}")
    logger.debug(f"Function: {function_name}")

    # Import and get the function
    module_name, func_name = function_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    func: Callable[..., Any] = getattr(module, func_name)

    # Resolve all input variables
    sig = inspect.signature(func)
    result: Any

    if isinstance(inputs, dict):
        resolved_inputs: Dict[str, Any] = {
            key: resolve(value, context) for key, value in inputs.items()
        }
        if "context" in sig.parameters:
            result = func(**resolved_inputs, context=context)
        else:
            result = func(**resolved_inputs)

    elif isinstance(inputs, list):
        resolved_args: List[Any] = [resolve(value, context) for value in inputs]
        if "context" in sig.parameters:
            result = func(*resolved_args, context=context)
        else:
            result = func(*resolved_args)
    else:
        resolved_inputs = {}
        if "context" in sig.parameters:
            result = func(**resolved_inputs, context=context)
        else:
            result = func(**resolved_inputs)

    # Handle outputs - this will process outputs, append_to, and saveas
    handle_step_outputs(rule, result, context)

    logger.info(f"✅ Completed function step: {name}")
    return result


def run_llm_step(rule: Dict[str, Any], context: Dict[str, Any], pipeline_config: Dict[str, Any]) -> str:
    """Execute an LLM step and return its result"""
    name = rule.get("name", "unnamed_llm_step")

    logger.info(f"🤖 Starting LLM step: {name}")
    logger.debug(f"Step details: {rule}")

    rendered_prompt = render_prompt(rule["prompt"], context)

    # Build merged config
    llm_config = pipeline_config.get("llm_config", {})
    step_config = rule.get("llm_options", {})
    merged_config = {
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 2500,
        "timeout_seconds": 30,
    }
    merged_config.update(llm_config)
    merged_config.update(step_config)

    output_type = rule.get("output_type", "text")
    logger.info(f"    ⏳ Calling {merged_config.get('model')} for step '{name}'...")

    result = call_llm(
        rendered_prompt, config=merged_config, output_type=output_type
    )

    # Check for templates
    if "template" in rule or "format_with" in rule:
        template_path = rule.get("template") or rule.get("format_with")
        result = apply_output_template(result, template_path, context)

    logger.info(f"✅ Completed LLM step: {name}")
    return result


def _value_to_string(value: Any) -> str:
    """Convert a value to string for text output"""
    if isinstance(value, str):
        return value
    elif isinstance(value, list):
        return "\n".join(str(item) for item in value)
    elif isinstance(value, dict):
        return yaml.dump(value, default_flow_style=False, allow_unicode=True)
    else:
        return str(value)


def run_save_step(rule: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Execute a save step to write content to a file"""
    name = rule.get("name", "unnamed")
    logger.info(f"💾 Starting save step: {name}")
    logger.debug(f"Step details: {rule}")
    
    # Get the raw path from rule
    path = rule.get("path")
    logger.debug(f"Raw path from rule: {path}")
    logger.debug(f"Context keys: {list(context.keys())}")

    if path:
        # Resolve variables in path
        resolved_path = resolve(path, context)
        logger.debug(f"Resolved path: {resolved_path}")
    else:
        resolved_path = "output.txt"  # Default fallback
        logger.debug(f"No path specified, using default: {resolved_path}")

    # Get content - it can be specified directly or referenced from context
    content_value = rule.get("content")
    logger.debug(f"Raw content from rule: {content_value}")
    
    if content_value:
        # Resolve the content variable
        content = resolve(content_value, context)
        logger.debug(f"Resolved content: {content}")
    else:
        # Fallback: might be in context under a default key
        content = context.get("content", "")
        logger.debug(f"Using content from context['content']: {content}")

    # Ensure parent directory exists
    from pathlib import Path
    output_path = Path(resolved_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(content))

    filename = str(output_path.absolute())
    logger.info(f"Wrote file: {filename}")

    # Track written files
    _record_written_file(filename)

    logger.info(f"✅ Completed save step: {name}")


def apply_output_template(result, template_path, context):
    """Apply a template to format step output"""
    from llmflow.utils.io import render_markdown_template

    # Create template variables with the resultz
    template_vars = context.copy()
    template_vars["result"] = result

    # Render the template WITH CONTEXT
    formatted = render_markdown_template(
        template_path=template_path,
        variables=template_vars,
        context=context,  # ADD THIS LINE - pass the full context for resolution
    )
    return formatted


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
                unresolved_vars.append(resolved[start : end + 1])
                idx = end + 1
            for expr in unresolved_vars:
                raise ValueError(
                    f"Unresolved pipeline expression: {expr} in value '{step_inputs}'"
                )
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
                templates.append(
                    (f"prompts/{prompt_file}", f"{step_name} (prompt file)")
                )

        # Recursively check nested steps (for-each, etc.)
        if step.get("type") == "for-each":
            nested_steps = step.get("steps", [])
            templates.extend(collect_all_templates(nested_steps))

    return templates


def run_pipeline(
    pipeline_path, vars=None, dry_run=False, skip_lint=False, verbose=False
):
    """Execute a YAML-defined pipeline with template validation"""
    variables = vars or {}

    # Clear the log file at the start of a new run
    open("llmflow.log", "w").close()

    # Load pipeline FIRST before using any variables from it - with friendly error handling
    # Strict YAML linting before validation
    try:
        from ruamel.yaml import YAML

        yaml_linter = YAML(typ="safe")
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
            logger.info("\n[ERROR] Pipeline config validation failed:")
            logger.info(e)
            raise SystemExit(1)
        # Validate each step strictly
        for idx, step in enumerate(pipeline_root.get("steps", [])):
            try:
                StepConfig(**step)
            except ValidationError as e:
                logger.info(
                    f"\n[ERROR] Step {idx+1} ('{step.get('name','unnamed')}') validation failed:"
                )
                logger.info(e)
                raise SystemExit(1)

    except FileNotFoundError:
        # Get both relative and absolute paths for helpful error message
        pipeline_file = Path(pipeline_path)
        current_dir = Path.cwd()
        abs_path = pipeline_file.resolve()

        logger.error("❌ Pipeline file not found:")
        logger.error(f"   Looking for: {pipeline_path}")
        logger.error(f"   Absolute path: {abs_path}")
        logger.error(f"   Current directory: {current_dir}")
        logger.error("   Are you running from the correct directory?")

        # List available pipeline files if pipelines directory exists
        pipelines_dir = current_dir / "pipelines"
        if pipelines_dir.exists() and pipelines_dir.is_dir():
            available = list(pipelines_dir.glob("*.yaml"))
            if available:
                logger.error("\n   Available pipelines:")
                for p in available:
                    logger.error(f"   - {p.name}")

        raise SystemExit(1)

    # Extract pipeline root and steps
    pipeline_root = pipeline.get("pipeline", pipeline)
    rules = pipeline_root.get("steps", [])

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


def run_for_each_step(rule: Dict[str, Any], context: Dict[str, Any], pipeline_config: Dict[str, Any]) -> None:
    """Execute a for-each step"""
    name = rule.get("name", "unnamed")
    input_var = rule.get("input")
    item_var = rule.get("item_var", "item")
    steps = rule.get("steps", [])

    logger.info(f"🔁 Starting for-each step: {name}")
    logger.debug(f"Step details: {rule}")

    # Resolve the input to get the list
    resolved_input = resolve(input_var, context)
    if not isinstance(resolved_input, (list, tuple)):
        raise ValueError(
            f"for-each input must resolve to a list, got {type(resolved_input)}"
        )

    total_items = len(resolved_input)
    logger.info(f"   Processing {total_items} items")

    # Track which lists are append_to targets across all nested steps
    append_to_lists = set()

    def collect_append_to_targets(steps_list):
        """Recursively collect all append_to target list names"""
        for step in steps_list:
            if "append_to" in step:
                append_to_lists.add(step["append_to"])
            if step.get("type") == "for-each" and "steps" in step:
                collect_append_to_targets(step["steps"])

    collect_append_to_targets(steps)

    for idx, item in enumerate(resolved_input, start=1):
        logger.debug(f"Processing item {idx}/{total_items}")

        # Create isolated context for this iteration using deepcopy
        item_context = deepcopy(context)
        item_context[item_var] = item

        # Run nested steps with the item context
        for nested_step in steps:
            run_step(nested_step, item_context, pipeline_config)

        # After iteration, ONLY merge append_to lists back to parent context
        # Do NOT merge other variables that were modified in the iteration
        for list_name in append_to_lists:
            if list_name in item_context:
                # Ensure parent context has the list
                if list_name not in context:
                    context[list_name] = []
                # Merge only if it's actually a list
                if isinstance(item_context[list_name], list):
                    # Extend parent list with new items from iteration
                    for item_val in item_context[list_name]:
                        if item_val not in context[list_name]:
                            context[list_name].append(item_val)

    logger.info(f"✅ Completed for-each step: {name}")


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
