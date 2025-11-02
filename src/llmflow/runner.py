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
            elif hasattr(result, key):
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

        # FIX: Extract and resolve inputs from prompt config
        prompt_inputs = resolved_prompt.get("inputs", {})
        if prompt_inputs:
            # Create extended context with resolved inputs
            extended_context = {**context}
            for key, value in prompt_inputs.items():
                extended_context[key] = resolve(value, context)
            logger.debug(f"Extended context with prompt inputs: {list(extended_context.keys())}")
            context = extended_context

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

    # FIRST: Handle {{variable}} syntax (double braces) - your existing prompts
    for key, val in context.items():
        rendered_prompt = rendered_prompt.replace(f"{{{{{key}}}}}", str(val))

    # THEN: Use resolve() for ${var} and {var} syntax (handles dot notation)
    rendered_prompt = resolve(rendered_prompt, context)

    logger.debug(f"Rendered prompt length: {len(rendered_prompt)} chars")
    logger.debug(f"Rendered prompt preview (after substitution): {rendered_prompt[:300]}...")

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
            # Don't call handle_step_outputs here - run_function_step already does it
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
    """Execute a plugin step"""
    name = rule.get("name", "unnamed")
    step_type = rule.get("type")

    logger.info(f"🔌 Starting plugin step: {name}")

    try:
        plugin_func = plugin_registry[step_type]
        plugin_config = {k: resolve(v, context) for k, v in rule.items()}
        logger.debug(f"Plugin config being passed: {plugin_config}")

        # Execute plugin - returns generator
        results = plugin_func(plugin_config)

        # FIX: Only convert generators to list, not strings/primitives
        if hasattr(results, '__iter__') and not isinstance(results, (str, dict, bytes)):
            # Check if it's actually a generator, not just iterable
            import types
            if isinstance(results, types.GeneratorType):
                results = list(results)

        logger.info(f"✅ Completed plugin step: {name}")
        return results

    except Exception as e:
        logger.error(f"❌ Error in {step_type} step '{name}': {e}")
        raise


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
    logger.debug(f"Context keys available: {list(context.keys())}")
    logger.debug(f"Context values preview: {[(k, str(v)[:100]) for k, v in context.items()]}")

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


def apply_output_template(llm_output: str, template_path: str, context: Dict[str, Any]) -> str:
    """Apply a template to LLM output"""
    from jinja2 import Template

    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = Path("templates") / template_file

    template_content = template_file.read_text()
    template = Template(template_content)

    # Make both llm_output and all context variables available
    template_context = {**context, "llm_output": llm_output, "output": llm_output}

    return template.render(**template_context)


def run_save_step(rule: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Execute a save step to write content to a file"""
    name = rule.get("name", "unnamed")
    logger.info(f"💾 Starting save step: {name}")
    logger.debug(f"Step details: {rule}")

    # Get and resolve the path
    path = rule.get("path")
    if path:
        resolved_path = resolve(path, context)
        logger.debug(f"Resolved path: {resolved_path}")
    else:
        resolved_path = "output.txt"
        logger.debug(f"No path specified, using default: {resolved_path}")

    # Get content
    content_value = rule.get("content")
    if content_value:
        content = resolve(content_value, context)
    else:
        content = context.get("content", "")

    # Write file
    from pathlib import Path
    output_path = Path(resolved_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(content))

    filename = str(output_path.absolute())
    _record_written_file(filename)

    logger.info(f"✅ Completed save step: {name}")


def save_content_to_file(content: Any, path: str, format_type: str = "auto") -> str:
    """Save content to a file with format detection"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "auto":
        ext = output_path.suffix.lower()
        if ext in [".json"]:
            format_type = "json"
        elif ext in [".yaml", ".yml"]:
            format_type = "yaml"
        else:
            format_type = "text"

    _save_file_by_format(content, str(output_path), format_type)
    return str(output_path.absolute())


def _save_file_by_format(content: Any, path: str, format_type: str) -> None:
    """Internal helper to save files by format"""
    if format_type == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    elif format_type == "yaml":
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content))


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

    # Track which lists are append_to targets
    append_to_lists = set()

    def collect_append_to_targets(steps_list):
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

        # ONLY merge append_to lists back to parent context
        for list_name in append_to_lists:
            if list_name in item_context:
                if list_name not in context:
                    context[list_name] = []
                if isinstance(item_context[list_name], list):
                    for item_val in item_context[list_name]:
                        if item_val not in context[list_name]:
                            context[list_name].append(item_val)

    logger.debug(f"Context after step {name}: {list(context.keys())}")
    logger.info(f"✅ Completed for-each step: {name}")


def run_pipeline(
    pipeline_file, vars=None, dry_run=False, verbose=False, skip_lint=False
):
    """
    Run a pipeline from a YAML file.

    Args:
        pipeline_file: Path to the pipeline YAML file
        vars: Optional dictionary of variables to override
        dry_run: If True, only validate and show what would run
        verbose: Enable verbose logging
        skip_lint: Skip linting validation
    """
    from pathlib import Path
    from pydantic import ValidationError
    from llmflow.pipeline_schema import PipelineConfig  # FIX: Correct module name

    # Set up logging
    if verbose:
        logger.set_level("DEBUG")

    pipeline_path = Path(pipeline_file)

    # Check if file exists
    if not pipeline_path.exists():
        logger.error(f"❌ Pipeline file not found: {pipeline_file}")
        raise SystemExit(1)  # Change from FileNotFoundError

    # Load and parse YAML with error handling
    try:
        with open(pipeline_path, 'r') as f:
            pipeline_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"❌ YAML syntax error in {pipeline_file}:")
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            logger.error(f"   Line {mark.line + 1}, Column {mark.column + 1}")
            logger.error(f"   {e.problem}")
            if hasattr(e, 'context'):
                logger.error(f"   Context: {e.context}")
        else:
            logger.error(f"   {str(e)}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"❌ Error reading pipeline file {pipeline_file}: {e}")
        raise SystemExit(1)

    if not pipeline_config:
        logger.error(f"❌ Pipeline file is empty or invalid: {pipeline_file}")
        raise SystemExit(1)

    # Validate pipeline structure with Pydantic
    try:
        PipelineConfig(**pipeline_config)
    except ValidationError as e:
        logger.error(f"❌ Pipeline validation error in {pipeline_file}:")
        for error in e.errors():
            field = " → ".join(str(loc) for loc in error['loc'])
            logger.error(f"   {field}: {error['msg']}")
            if 'input' in error:
                logger.error(f"   Got: {error['input']}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"❌ Pipeline structure error: {e}")
        raise SystemExit(1)

    # Lint if requested
    if not skip_lint:
        logger.info("🔍 Validating pipeline...")
        lint_result = lint_pipeline_full(str(pipeline_path))
        # Handle None return (for mocked tests)
        if lint_result and not lint_result.valid:
            logger.error("❌ Pipeline validation failed:")
            for error in lint_result.errors:
                logger.error(f"  - {error}")
            raise SystemExit(1)

    # Get variables from pipeline
    pipeline_root = pipeline_config.get("pipeline", pipeline_config)
    pipeline_vars = pipeline_root.get("variables", {})

    # Initialize context with merged variables (CLI vars override pipeline vars)
    context = {**pipeline_vars, **(vars or {})}
    logger.debug(f"Variables: {vars}")

    # Get steps to execute
    steps = pipeline_root.get("steps", [])
    logger.info(f"Found {len(steps)} steps to execute")

    # Validate templates - ONLY pass pipeline_root
    logger.info("🔍 Validating pipeline templates...")
    validate_all_templates(pipeline_root)
    logger.info("✅ All templates validated successfully")

    if dry_run:
        logger.info("\n🎯 Dry run mode - showing steps that would execute:")
        for step in pipeline_config.get("steps", []):
            logger.info(f"Would run: {step['name']} (type: {step['type']})")
        logger.info("Dry run complete. Exiting.")
        return context  # Return context immediately, don't execute

    logger.info("\n🎯 Starting pipeline execution...")

    # Execute each step
    for rule in steps:
        run_step(rule, context, pipeline_root)

    logger.info("Pipeline complete.")
    return context
