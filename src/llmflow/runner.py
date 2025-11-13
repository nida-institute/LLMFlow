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
from llmflow.utils.get_prefix_directory import get_prefix_directory
from llmflow.utils.io import validate_all_templates
from llmflow.utils.linter import lint_pipeline_full
from llmflow.utils.llm_runner import call_llm, run_llm_with_mcp_tools
from llmflow.exceptions import (
    StepExecutionError,
    ForEachIterationError,
    VariableResolutionError,
    LLMProviderError,  # Add this
    PluginError
)
from llmflow.modules.mcp import init_mcp_client

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


def get_from_context(expr: str, ctx: Dict[str, Any]) -> Any:
    """
    Resolve dot notation and list indices from context.
    Supports: foo.bar, foo[0], foo.bar[key], Row objects with attributes/getitem.
    """
    import re

    parts = re.split(r"\.(?![^\[]*\])", expr)  # split on dots not inside brackets
    result = ctx

    for part in parts:
        # Handle list index: foo[0] OR dict key: foo[key]
        m = re.match(r"^([a-zA-Z0-9_]+)(\[([^\]]+)\])?$", part)
        if not m:
            return None

        key = m.group(1)
        bracket_content = m.group(3)

        # Get key from dict or object attribute
        if isinstance(result, dict):
            result = result.get(key)
        elif hasattr(result, key):
            try:
                result = getattr(result, key)
            except AttributeError:
                return None
        else:
            return None

        # Handle bracket access
        if bracket_content is not None:
            try:
                idx = int(bracket_content)
                if isinstance(result, list):
                    if len(result) == 0 or idx >= len(result):
                        return None
                    result = result[idx]
                else:
                    return None
            except ValueError:
                # Not an integer - treat as string key
                if isinstance(result, dict):
                    result = result.get(bracket_content)
                elif hasattr(result, '__getitem__'):
                    try:
                        result = result[bracket_content]
                    except (KeyError, TypeError):
                        return None
                else:
                    return None

        if result is None:
            return None

    return result


def resolve(value, context, max_depth=5):
    """
    Resolves variables within a value using the provided context.
    Supports both {curly} and ${dollar} notation with dot notation and list indexing.
    Returns native Python objects for exact variable references.
    """
    import re

    if isinstance(value, str):
        # Handle ${...} syntax (exact match returns native object)
        match = re.match(r"^\$\{([^\}]+)\}$", value)
        if match:
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            if resolved is not None:
                # Recursive resolution if still templated
                if isinstance(resolved, str) and (resolved.startswith("${") or resolved.startswith("{")):
                    if max_depth > 0:
                        return resolve(resolved, context, max_depth - 1)
                return resolved
            return value

        # Handle {curly} syntax (exact match returns native object)
        match = re.match(r"^\{([^\}]+)\}$", value)
        if match:
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            if resolved is not None:
                # Recursive resolution if still templated
                if isinstance(resolved, str) and (resolved.startswith("${") or resolved.startswith("{")):
                    if max_depth > 0:
                        return resolve(resolved, context, max_depth - 1)
                return resolved
            return value

        # String substitution for both syntaxes
        def replace_var(match):
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            return str(resolved) if resolved is not None else match.group(0)

        value = re.sub(r"\$\{([^\}]+)\}", replace_var, value)
        value = re.sub(r"\{([^\}]+)\}", replace_var, value)
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


def handle_step_outputs(rule: Dict[str, Any], result: Any, context: Dict[str, Any]):
    """Store step results in context based on outputs configuration."""

    # 1. Handle outputs - store results in context
    outputs = rule.get("outputs")
    if outputs is not None:
        if isinstance(outputs, str):
            context[outputs] = result
            logger.debug(f"Stored result in context['{outputs}']")
        elif isinstance(outputs, list):
            # Store the entire result under the first output name
            # This allows both ${entries} and ${entries[0]} to work
            if len(outputs) == 1:
                context[outputs[0]] = result  # Store the list, not result[0]
                logger.debug(f"Stored result in context['{outputs[0]}']")
            else:
                # Multiple outputs - unpack the result
                for i, output_name in enumerate(outputs):
                    value = result[i] if isinstance(result, (list, tuple)) and i < len(result) else result
                    context[output_name] = value
                    logger.debug(f"Stored result in context['{output_name}']")

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

    def get_content():
        if isinstance(outputs, list):
            return context[outputs[0]]
        if isinstance(outputs, str):
            return context[outputs]
        raise ValueError("No outputs specified for saveas")

    if isinstance(saveas_config, str):
        path = resolve(saveas_config, context)
        content = get_content()
        saved_path = save_content_to_file(content, path)
        _record_written_file(saved_path)
        return

    if isinstance(saveas_config, dict):
        path = resolve(saveas_config["path"], context)
        group_cfg = saveas_config.get("group_by_prefix")
        content = get_content()

        if group_cfg:
            from pathlib import Path as _P
            fname = _P(path).name
            if isinstance(group_cfg, int):
                prefix_dir = get_prefix_directory(fname, prefix_length=group_cfg)
            else:
                prefix_dir = get_prefix_directory(
                    fname,
                    prefix_length=group_cfg.get("prefix_length"),
                    prefix_delimiter=group_cfg.get("prefix_delimiter"),
                )
            path = str(_P(path).parent / prefix_dir / fname)

        saved_path = save_content_to_file(content, path)
        _record_written_file(saved_path)
        return

    if isinstance(saveas_config, list):
        for item in saveas_config:
            if isinstance(item, dict):
                path = resolve(item["path"], context)
                content_spec = item.get("content")
                content = resolve(content_spec, context) if content_spec else get_content()
                fmt = item.get("format", "auto")
                saved_path = save_content_to_file(content, path, fmt)
                _record_written_file(saved_path)
        return

    raise ValueError("Invalid saveas configuration type")


def run_step(step: Dict[str, Any], context: Dict[str, Any], pipeline_config: Dict[str, Any] | None = None) -> str | None:
    """
    Execute a single step based on its type.
    Returns 'exit' if step has 'after: exit', 'continue' if 'after: continue', else None.
    """
    step_type = step.get("type")

    if step_type == "for-each":
        after_action = run_for_each_step(step, context, pipeline_config)
        # Check if nested step returned exit
        if after_action == "exit":
            return "exit"
    elif step_type == "llm":
        result = run_llm_step(step, context, pipeline_config)
        handle_step_outputs(step, result, context)
    elif step_type == "function":
        result = run_function_step(step, context, pipeline_config)
        # handle_step_outputs is called inside run_function_step
    elif step_type == "if":
        after_action = run_if_step(step, context, pipeline_config)
        # Check if nested step returned exit
        if after_action == "exit":
            return "exit"
    elif step_type == "save":
        run_save_step(step, context, pipeline_config)
    elif step.get("plugin"):
        result = run_plugin_step(step, context, pipeline_config)
        handle_step_outputs(step, result, context)
    elif step_type in plugin_registry:
        result = run_plugin_step(step, context, pipeline_config)
        handle_step_outputs(step, result, context)
    else:
        raise ValueError(f"Unknown step type: {step_type}")

    # Return the after action to propagate it up
    return step.get("after")


def run_plugin_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None
) -> Any:
    """Execute a plugin step"""
    name = step.get("name", "unnamed")
    step_type = step.get("type")

    logger.info(f"🔌 Starting plugin step: {name}")

    try:
        plugin_func = plugin_registry[step_type]
        plugin_config = {k: resolve(v, context) for k, v in step.items()}

        # Execute plugin
        results = plugin_func(plugin_config)

        # Convert generators to list
        import types
        if isinstance(results, types.GeneratorType):
            results = list(results)

        logger.info(f"✅ Completed plugin step: {name}")
        return results

    except Exception as e:
        logger.error(f"❌ Error in {step_type} step '{name}': {e}")
        raise


def run_function_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None
) -> Any:
    """Execute a function step and return its result"""
    name = step.get("name", "unnamed")
    function_name = step["function"]
    inputs = step.get("inputs", {})

    logger.info(f"🔧 Starting function step: {name}")

    # Import and get the function
    module_name, func_name = function_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)

    # Resolve all input variables
    sig = inspect.signature(func)

    if isinstance(inputs, dict):
        resolved_inputs = {key: resolve(value, context) for key, value in inputs.items()}
        result = func(**resolved_inputs, context=context) if "context" in sig.parameters else func(**resolved_inputs)
    elif isinstance(inputs, list):
        resolved_args = [resolve(value, context) for value in inputs]
        result = func(*resolved_args, context=context) if "context" in sig.parameters else func(*resolved_args)
    else:
        result = func(context=context) if "context" in sig.parameters else func()

    # Handle outputs
    handle_step_outputs(step, result, context)

    logger.info(f"✅ Completed function step: {name}")
    return result


def run_llm_step(rule: Dict[str, Any], context: Dict[str, Any], pipeline_config: Dict[str, Any]) -> str:
    """Execute an LLM step and return its result"""
    name = rule.get("name", "unnamed_llm_step")

    logger.info(f"🤖 Starting LLM step: {name}")
    logger.debug(f"Step details: {rule}")
    logger.debug(f"Context keys available: {list(context.keys())}")

    rendered_prompt = render_prompt(rule["prompt"], context)

    # Build merged config - FIX: Use llm_options if present
    llm_config = pipeline_config.get("llm_config", {})

    # FIX: Check for llm_options in step
    step_options = rule.get("llm_options", {})
    step_config = {
        "model": rule.get("model"),
        "temperature": rule.get("temperature") or step_options.get("temperature"),
        "max_tokens": rule.get("max_tokens") or step_options.get("max_tokens"),
        "timeout_seconds": rule.get("timeout_seconds") or step_options.get("timeout_seconds"),
    }
    # Remove None values
    step_config = {k: v for k, v in step_config.items() if v is not None}

    # Merge configs: defaults < pipeline < step-level
    merged_config = {
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 2500,
        "timeout_seconds": 30,
    }
    merged_config.update(llm_config)
    merged_config.update(step_options)  # FIX: Merge llm_options
    merged_config.update(step_config)    # Then override with direct step attrs

    output_type = rule.get("output_type", "text")

    # Initialize MCP client if enabled
    mcp_client = init_mcp_client(rule, pipeline_config)

    try:
        if mcp_client:
            # Use tool-calling flow with iterative calls
            logger.info(f"    ⏳ Calling {merged_config.get('model')} with MCP tools for step '{name}'...")
            response = run_llm_with_mcp_tools(
                rendered_prompt,
                merged_config,
                mcp_client,
                output_type
            )
        else:
            # Use simple flow without tools
            logger.info(f"    ⏳ Calling {merged_config.get('model')} for step '{name}'...")
            response = call_llm(
                rendered_prompt,
                config=merged_config,
                output_type=output_type
            )

        # Check for templates
        if "template" in rule or "format_with" in rule:
            template_path = rule.get("template") or rule.get("format_with")
            response = apply_output_template(response, template_path, context)

        logger.info(f"✅ Completed LLM step: {name}")
        return response

    finally:
        # Always close MCP client if it was created
        if mcp_client:
            import asyncio
            asyncio.run(mcp_client._async_close())


def run_save_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None
) -> None:
    """Execute a save step to write content to a file"""
    name = step.get("name", "unnamed")
    logger.info(f"💾 Starting save step: {name}")

    path = resolve(step.get("path", "output.txt"), context)
    content_value = step.get("content")
    content = resolve(content_value, context) if content_value else context.get("content", "")

    saved_path = save_content_to_file(content, path)
    _record_written_file(saved_path)

    logger.info(f"✅ Completed save step: {name}")


def save_content_to_file(content: Any, path: str, format_type: str = "auto") -> str:
    """Save content to a file with format detection"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Auto-detect format from extension
    if format_type == "auto":
        ext = output_path.suffix.lower()
        if ext in [".json"]:
            format_type = "json"
        elif ext in [".yaml", ".yml"]:
            format_type = "yaml"
        else:
            format_type = "text"

    # Write file by format (inline the logic)
    if format_type == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    elif format_type == "yaml":
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(str(content))

    return str(output_path.absolute())


def resolve_template(template: str, context: Dict[str, Any]) -> str:
    """
    Resolve template variables in a string using context.
    Used for conditions in if statements.
    Returns a string suitable for eval().
    """
    resolved = resolve(template, context)
    # If resolved value is already a bool, int, etc., convert to string for eval
    if not isinstance(resolved, str):
        return str(resolved)
    return resolved


def run_for_each_step(rule: Dict[str, Any], context: Dict[str, Any], pipeline_config: Dict[str, Any]) -> str | None:
    """Execute a for-each loop step"""
    input_data = resolve(rule.get("input", []), context)
    item_var = rule.get("item_var", "item")
    steps = rule.get("steps", [])

    # Collect all append_to targets AND regular outputs
    def collect_outputs(steps_list):
        append_targets = set()
        output_vars = set()
        for step in steps_list:
            if "append_to" in step:
                append_targets.add(step["append_to"])
            if "outputs" in step:
                outputs = step["outputs"]
                if isinstance(outputs, str):
                    output_vars.add(outputs)
                elif isinstance(outputs, list):
                    output_vars.update(outputs)
            if "steps" in step:
                nested_append, nested_output = collect_outputs(step["steps"])
                append_targets.update(nested_append)
                output_vars.update(nested_output)
        return append_targets, output_vars

    append_to_targets, output_vars = collect_outputs(steps)

    for item in input_data:
        iteration_context = deepcopy(context)
        iteration_context[item_var] = item

        for step in steps:
            after_action = run_step(step, iteration_context, pipeline_config)

            if after_action == "exit":
                logger.info("🛑 'after: exit' in for-each iteration - exiting entire pipeline")

                # Propagate BOTH append_to AND regular outputs before exiting
                for target in append_to_targets:
                    if target in iteration_context and isinstance(iteration_context[target], list):
                        if target not in context:
                            context[target] = iteration_context[target][:]
                        else:
                            original_length = len(context[target])
                            new_items = iteration_context[target][original_length:]
                            context[target].extend(new_items)

                # FIX: Also propagate regular outputs before exiting
                for output_var in output_vars:
                    if output_var in iteration_context:
                        context[output_var] = iteration_context[output_var]
                        logger.debug(f"Propagated output '{output_var}' before exit")

                return "exit"  # Propagate exit to parent

            elif after_action == "continue":
                logger.info("⏭️  'after: continue' in for-each iteration - skipping to next iteration")
                break  # Break out of steps loop, continue with next item

        # Normal propagation (no exit)
        for target in append_to_targets:
            if target in iteration_context and isinstance(iteration_context[target], list):
                if target not in context:
                    context[target] = iteration_context[target][:]
                else:
                    original_length = len(context[target])
                    new_items = iteration_context[target][original_length:]
                    context[target].extend(new_items)

    return None  # No exit, normal completion


def run_if_step(step: Dict[str, Any], context: Dict[str, Any], pipeline_config: Dict[str, Any] | None = None) -> str | None:
    """Execute an if step conditionally. Returns 'exit' if any nested step has 'after: exit'."""
    condition_expr = step.get("condition")
    nested_steps = step.get("steps", [])

    if not condition_expr:
        raise ValueError("if step missing 'condition'")
    if not nested_steps:
        return None

    name = step.get("name", "unnamed")
    logger.info(f"❓ Starting if step: {name}")

    try:
        resolved = resolve(condition_expr, context)
        # If resolve returns a boolean/int directly, use it as-is
        # Otherwise evaluate it as a Python expression
        if isinstance(resolved, bool):
            condition_result = resolved
        elif isinstance(resolved, (int, float)):
            condition_result = bool(resolved)
        else:
            # It's a string expression, evaluate it
            condition_result = bool(eval(resolved))

        if condition_result:
            logger.info(f"   Condition is true, executing {len(nested_steps)} steps")
            for nested in nested_steps:
                after_action = run_step(nested, context, pipeline_config)
                if after_action == "exit":
                    logger.info("🛑 'after: exit' in nested step - propagating exit signal")
                    return "exit"
                elif after_action == "continue":
                    logger.info("⏭️  'after: continue' in nested step - breaking out of if block")
                    # CHANGE: For now, only break from if block
                    # In the future, this should propagate to enclosing for-each loop
                    return None  # Don't propagate continue from if to for-each
        else:
            logger.info("   Condition is false, skipping steps")

    except Exception as e:
        logger.error(f"Error evaluating condition '{condition_expr}': {e}")

    logger.info(f"✅ Completed if step: {step.get('name', 'unnamed')}")
    return None


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
        after_action = run_step(rule, context, pipeline_config)
        if after_action == "exit":
            logger.info(f"🛑 'after: exit' - exiting pipeline early after step '{rule.get('name')}'.")
            break
        elif after_action == "continue":
            continue  # Default behavior

    logger.info("Pipeline complete.")
    return context
