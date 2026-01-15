import importlib
import inspect
import json
import os
import re
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import argparse
import logging
import sys

import httpx
import yaml
from openai import APIError as OpenAIAPIError, APITimeoutError, RateLimitError

from llmflow.modules.logger import Logger
from llmflow.modules.telemetry import TelemetryCollector, generate_optimization_suggestions
from llmflow.plugins import plugin_registry
from llmflow.plugins.loader import discover_plugins
from llmflow.utils.io import validate_all_templates
from llmflow.utils.linter import lint_pipeline_full
from llmflow.utils.llm_runner import call_llm, run_llm_with_mcp_tools
from llmflow.utils.get_prefix_directory import get_prefix_directory  # ← ADD THIS LINE
from llmflow.exceptions import (
    StepExecutionError,
    ForEachIterationError,
    VariableResolutionError,
    LLMProviderError,
    PluginError
)
from llmflow.modules.mcp import init_mcp_client
from llmflow.utils.guards import build_step_eval_ctx, enforce_require, collect_warnings
from llmflow.utils.io import sanitize_filename
from datetime import datetime

discover_plugins()

# Single unified logger instance
logger = Logger()

def build_debug_filename(step: Dict[str, Any], context: Dict[str, Any], request_or_response: str) -> str:
    """Build a debug filename from passage (or timestamp), prompt file, and request/response type.

    Format with passage: {passage}_{prompt_file}_{request_or_response}.txt
    Format without passage: {timestamp}_{prompt_file}_{request_or_response}.txt

    Example: Mark-1-1-12_leadersguide-naming-ast_request.txt
    Example: 2026-01-13-143045_lexicon-step_request.txt
    """
    parts = []

    # Get passage from context (try multiple possible keys)
    passage = context.get("passage") or context.get("Citation") or context.get("scene", {}).get("Citation")
    if passage:
        parts.append(sanitize_filename(str(passage)))
    else:
        # Fallback to timestamp when no passage available
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        parts.append(timestamp)

    # Get prompt filename from step config
    prompt_config = step.get("prompt", {})
    if isinstance(prompt_config, dict):
        prompt_file = prompt_config.get("file", "")
    elif isinstance(prompt_config, str):
        prompt_file = prompt_config
    else:
        prompt_file = ""

    if prompt_file:
        # Extract just the filename without extension
        prompt_name = Path(prompt_file).stem
        parts.append(sanitize_filename(prompt_name))
    else:
        # Fallback to step name
        step_name = step.get("name", "llm_step")
        parts.append(sanitize_filename(step_name))

    # Add request/response indicator
    parts.append(request_or_response)

    return "_".join(parts) + ".txt"

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
    Supports: foo.bar, foo[0], foo[key], foo['key'], Row objects with attributes/getitem.
    """
    import re

    parts = re.split(r"\.(?![^\[]*\])", expr)  # split on dots not inside brackets
    result = ctx

    for part in parts:
        # Handle list index: foo[0] OR dict key: foo[key] OR foo['key']
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
            # Try numeric index first
            try:
                idx = int(bracket_content)
                if isinstance(result, list):
                    if len(result) == 0 or idx >= len(result):
                        return None
                    result = result[idx]
                else:
                    return None
            except ValueError:
                # Not a number - treat as dict/object key
                # Remove quotes if present: 'key' or "key" -> key
                bracket_key = bracket_content.strip().strip("'\"")

                # Try dict access
                if isinstance(result, dict):
                    result = result.get(bracket_key)
                # Try Row object __getitem__
                elif hasattr(result, '__getitem__'):
                    try:
                        result = result[bracket_key]
                    except (KeyError, TypeError):
                        return None
                # Try attribute access as fallback
                elif hasattr(result, bracket_key):
                    result = getattr(result, bracket_key)
                else:
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
    rendered_prompt = full_prompt_path.read_text(encoding="utf-8")

    # FIRST: Handle {{variable}} syntax (double braces) - your existing prompts
    for key, val in context.items():
        rendered_prompt = rendered_prompt.replace(f"{{{{{key}}}}}", str(val))

    # THEN: Use resolve() for ${var} and {var} syntax (handles dot notation)
    rendered_prompt = resolve(rendered_prompt, context)

    logger.debug(f"Rendered prompt length: {len(rendered_prompt)} chars")
    logger.debug(f"Rendered prompt preview (after substitution): {rendered_prompt[:300]}...")

    return rendered_prompt


def handle_step_outputs(step, result, context, base_dir="."):
    """Handle step outputs, including saveas."""
    # 1. Handle outputs - store results in context
    outputs = step.get("outputs")
    if outputs is not None:
        if isinstance(outputs, str):
            context[outputs] = result
            logger.info(f"📦 Stored in context['{outputs}']: {type(result).__name__}, length={len(str(result)) if result else 0}")
            if step.get("name") == "bodies":
                logger.debug(f"   First 100 chars: {repr(str(result)[:100]) if result else 'NONE'}")
        elif isinstance(outputs, list):
            if len(outputs) == 1:
                context[outputs[0]] = result
                logger.debug(f"Stored result in context['{outputs[0]}']")
            else:
                for i, output_name in enumerate(outputs):
                    value = result[i] if isinstance(result, (list, tuple)) and i < len(result) else result
                    context[output_name] = value
                    logger.debug(f"Stored result in context['{output_name}']")

    # 2. Handle append_to
    append_to = step.get("append_to")
    if append_to:
        if append_to not in context:
            context[append_to] = []
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

    # 3. Handle saveas - delegate to handle_step_saveas for proper group_by_prefix support
    if "saveas" in step:
        # Store result in context temporarily if not already there
        if outputs is None:
            # Need a temporary output name for saveas to work
            temp_output = f"_temp_output_{id(result)}"
            step_with_output = {**step, "outputs": temp_output}
            context[temp_output] = result
            handle_step_saveas(step_with_output, context)
            del context[temp_output]
        else:
            handle_step_saveas(step, context)


def handle_step_saveas(step: Dict[str, Any], context: Dict[str, Any]) -> None:  # ← Changed parameter name from 'rule' to 'step'
    """Handle saveas output for pipeline steps."""
    saveas_config = step["saveas"]  # ← Changed from 'rule' to 'step'
    outputs = step.get("outputs")  # ← Changed from 'rule' to 'step'

    def get_content():
        if isinstance(outputs, list):
            return context[outputs[0]]
        if isinstance(outputs, str):
            return context[outputs]
        raise ValueError("No outputs specified for saveas")

    if isinstance(saveas_config, str):
        path = resolve(saveas_config, context)
        content = get_content()
        fmt = step.get("format", "auto")
        saved_path = save_content_to_file(content, path, fmt)
        _record_written_file(saved_path)
        return

    if isinstance(saveas_config, dict):
        raw_path = saveas_config["path"]
        logger.debug(f"Resolving saveas path: {raw_path}")
        logger.debug(f"Context keys: {list(context.keys())}")
        path = resolve(raw_path, context)
        logger.debug(f"Resolved path: {path}")
        group_cfg = saveas_config.get("group_by_prefix")
        content = get_content()
        fmt = step.get("format", "auto")

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

        saved_path = save_content_to_file(content, path, fmt)
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


def run_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None
) -> Any:
    """Execute a step based on its type"""
    step_type = step.get("type")

    # Handle step-level log configuration
    step_log_level = step.get("log", "").upper()
    original_level = None
    if step_log_level == "DEBUG":
        original_level = logger.level
        logger.set_level("DEBUG")
        logger.debug(f"🔍 Enabled DEBUG logging for step: {step.get('name')}")

    try:
        # Check condition BEFORE executing any step type
        condition = step.get("condition")
        if condition:
            # Resolve variables in condition before evaluation
            resolved_condition = resolve(condition, context)
            logger.debug(f"🔍 Evaluating condition: {condition}")
            logger.debug(f"   Resolved to: {resolved_condition}")

            try:
                if isinstance(resolved_condition, bool):
                    condition_result = resolved_condition
                elif isinstance(resolved_condition, (int, float)):
                    condition_result = bool(resolved_condition)
                else:
                    condition_result = bool(eval(str(resolved_condition)))
            except Exception as e:
                logger.warning(f"Condition evaluation failed: {condition} - {e}")
                condition_result = False

            if not condition_result:
                logger.info(f"⏭️  Skipping step '{step.get('name')}' (condition false)")
                return None

        # Execute step based on type
        after_action = None

        if step_type == "for-each":
            after_action = run_for_each_step(step, context, pipeline_config)
        elif step_type == "llm":
            result = run_llm_step(step, context, pipeline_config)
            handle_step_outputs(step, result, context)
        elif step_type == "function":
            result = run_function_step(step, context, pipeline_config)
        elif step_type == "if":
            after_action = run_if_step(step, context, pipeline_config)
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

        # ✅ CENTRALIZED: Handle 'after' directive for ALL steps
        # Priority: nested step's after_action > step's own after directive
        if after_action:
            return after_action  # Propagate from nested steps

        # Handle this step's own after directive
        after_directive = step.get("after")
        if after_directive:
            logger.debug(f"Step '{step.get('name')}' has after: {after_directive}")
            return after_directive  # Return "exit", "continue", or "skip"

        # NEW: enforce 'require' and 'warn' after outputs have been stored
        try:
            eval_ctx = build_step_eval_ctx(step, context)

            # Debug logging for guards
            if step.get("name") == "bodies" and "require" in step:
                outputs = step.get("outputs")
                if outputs:
                    logger.debug(f"🔍 Bodies guard check - outputs key: {outputs}")
                    logger.debug(f"🔍 Value in context: {repr(context.get(outputs, 'NOT_FOUND'))[:200]}")
                    logger.debug(f"🔍 Value in eval_ctx: {repr(eval_ctx.get(outputs, 'NOT_FOUND'))[:200]}")
                    logger.debug(f"🔍 Variable '{outputs}' in eval_ctx keys: {outputs in eval_ctx}")
                    logger.debug(f"🔍 Type of eval_ctx['{outputs}']: {type(eval_ctx.get(outputs))}")

            # Fail-hard requires (raises ValueError)
            if "require" in step and step.get("require"):
                # Build context info for better error messages
                context_info = {}
                if "scene" in context:
                    scene = context.get("scene")
                    if isinstance(scene, dict):
                        context_info["scene_citation"] = scene.get("Citation", "unknown")
                enforce_require(eval_ctx, step.get("require"), step_name=step.get("name"), context_info=context_info)

            # Non-blocking warnings: collect and attach to context
            if "warn" in step and step.get("warn"):
                msgs = collect_warnings(eval_ctx, step.get("warn"))
                if msgs:
                    # initialize warnings sink once
                    if "_warnings" not in context or context["_warnings"] is None:
                        context["_warnings"] = []
                    context["_warnings"].extend(msgs)
                    for m in msgs:
                        logger.warning(f"⚠️  {m}")
        except Exception:
            # propagate require failures and eval errors
            raise

        return None

    finally:
        # Restore original logger level if it was changed
        if original_level is not None:
            logger.level = original_level
            logger.debug(f"🔍 Restored logger level after step: {step.get('name')}")


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


def run_llm_step(step: Dict[str, Any], context: Dict[str, Any], pipeline_config: Dict[str, Any]) -> str:
    """Execute an LLM step and return its result"""
    name = step.get("name", "unnamed_llm_step")

    logger.info(f"🤖 Starting LLM step: {name}")
    logger.debug(f"Step details: {step}")
    logger.debug(f"Context keys available: {list(context.keys())}")

    # Get telemetry reference (but don't start tracking yet - we need merged config first)
    telemetry = pipeline_config.get("_telemetry")

    rendered_prompt = render_prompt(step["prompt"], context)

    # Debug: save rendered prompt (request) when log_level=debug
    try:
        if (pipeline_config.get("linter_config", {}) or {}).get("log_level", "").lower() == "debug":
            filename = build_debug_filename(step, context, "request")
            prompt_path = f"outputs/debug/{filename}"
            save_content_to_file(rendered_prompt, prompt_path, format="text")
            logger.debug(f"📝 Saved request to {prompt_path}")
    except Exception as e:
        logger.debug(f"(request debug save skipped: {e})")

    # Build merged config
    llm_config = pipeline_config.get("llm_config", {})
    step_options = step.get("llm_options", {})
    step_config = {
        "model": step.get("model"),
        "temperature": step.get("temperature") or step_options.get("temperature"),
        "max_tokens": step.get("max_tokens") or step_options.get("max_tokens"),
        "max_completion_tokens": step.get("max_completion_tokens") or step_options.get("max_completion_tokens"),
        "timeout_seconds": step.get("timeout_seconds") or step_options.get("timeout_seconds"),
        "response_format": step.get("response_format"),
        "reasoning_effort": step.get("reasoning_effort") or step_options.get("reasoning_effort"),
    }
    step_config = {k: v for k, v in step_config.items() if v is not None}

    # Start with universal defaults only
    merged_config = {
        "model": "gpt-4o",
        "temperature": 0.7,
        "timeout_seconds": 30,
    }
    merged_config.update(llm_config)
    merged_config.update(step_options)
    merged_config.update(step_config)

    # Add model-specific defaults only if not already set
    from llmflow.utils.llm_runner import get_model_family
    final_model = merged_config.get("model", "gpt-4o")
    model_family = get_model_family(final_model)

    # Now start telemetry tracking with the ACTUAL model that will be used
    if telemetry:
        telemetry.start_step(name, "llm", model=final_model)

    if "max_tokens" not in merged_config and "max_completion_tokens" not in merged_config:
        # Apply appropriate token limit default based on model family
        if model_family in ("gpt-5", "o1"):
            merged_config["max_completion_tokens"] = 2500
        else:
            merged_config["max_tokens"] = 2500

    # Include MCP config if present
    if "mcp" in step:
        merged_config["mcp"] = step["mcp"]

    # Determine output type
    output_type = step.get("output_type", "text")

    if output_type == "text":
        saveas_config = step.get("saveas")
        if saveas_config:
            path = saveas_config if isinstance(saveas_config, str) else saveas_config.get("path", "")
            if path.endswith(".json"):
                output_type = "json"
                logger.debug(f"    🔍 Auto-detected JSON output from saveas path: {path}")

    # Initialize MCP client if enabled
    mcp_client = init_mcp_client(step, pipeline_config)

    try:
        # Retry configuration
        max_retries = 3
        retry_delay = 2

        response = None
        for attempt in range(max_retries):
            try:
                if mcp_client:
                    logger.info(f"    ⏳ Calling {merged_config.get('model')} with MCP tools for step '{name}'...")
                    response = run_llm_with_mcp_tools(
                        rendered_prompt,
                        merged_config,  # ← Changed from 'config' to 'merged_config'
                        mcp_client,
                        output_type,
                        step_name=step.get("name", "unknown"),
                        step=step,
                        context=context,
                        pipeline_config=pipeline_config
                    )
                else:
                    logger.info(f"    ⏳ Calling {merged_config.get('model')} for step '{name}'...")
                    response = call_llm(
                        rendered_prompt,
                        config=merged_config,
                        output_type=output_type
                    )

                # Success! Break out of retry loop
                break

            except KeyboardInterrupt:
                # Don't retry on Ctrl+C
                logger.info("⚠️  User interrupted - exiting")
                raise

            except Exception as e:
                # Catch ANY exception from LLM call
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # 2s, 4s, 8s
                    logger.warning(f"⚠️  LLM error (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {str(e)[:100]}")
                    logger.warning(f"    Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ LLM call failed after {max_retries} attempts")
                    logger.error(f"    Final error: {type(e).__name__}: {e}")
                    raise  # Re-raise after all retries exhausted

        # Extract content and token usage from response
        # LLM functions now return dict with 'content' and 'usage' keys
        usage = {}
        response_content = response

        if isinstance(response, dict):
            if "content" in response:
                response_content = response["content"]
                usage = response.get("usage", {})
            # else: backward compatibility - dict is the actual content

        # Debug: save raw response text
        try:
            if response_content is not None and (pipeline_config.get("linter_config", {}) or {}).get("log_level", "").lower() == "debug":
                filename = build_debug_filename(step, context, "response")
                resp_path = f"outputs/debug/{filename}"
                save_content_to_file(response_content if isinstance(response_content, str) else str(response_content), resp_path, format="text")
                logger.debug(f"🗒️ Saved response to {resp_path}")
        except Exception as e:
            logger.debug(f"(response debug save skipped: {e})")

        # Check for templates (only runs if we got a response)
        if response_content and ("template" in step or "format_with" in step):
            template_path = step.get("template") or step.get("format_with")
            response_content = apply_output_template(response_content, template_path, context)

        logger.info(f"✅ Completed LLM step: {name}")

        # End telemetry tracking with token counts
        if telemetry:
            telemetry.end_step(
                name,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0)
            )

        return response_content

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


def save_content_to_file(content: Any, path: str, format: str = None) -> str:
    """Save content to file with optional format specification."""
    import json
    from pathlib import Path

    # Auto-detect format from extension if not specified OR if format='auto'
    if format is None or format == 'auto':
        if path.endswith('.json'):
            format = 'json'
        else:
            format = 'text'

    # Apply format
    if format == 'json':
        # Case 1: Python dict/list - serialize directly
        if isinstance(content, (dict, list)):
            formatted_content = json.dumps(content, ensure_ascii=False, indent=2)

        # Case 2: String that might be JSON
        elif isinstance(content, str):
            try:
                parsed = json.loads(content)

                # Handle double/triple encoding - keep parsing strings
                while isinstance(parsed, str):
                    try:
                        parsed = json.loads(parsed)
                    except (json.JSONDecodeError, ValueError):
                        break  # Can't parse further

                # Now re-serialize with proper formatting
                formatted_content = json.dumps(parsed, ensure_ascii=False, indent=2)

            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, serialize the string itself
                formatted_content = json.dumps(content, ensure_ascii=False, indent=2)

        # Case 3: Other Python objects
        else:
            formatted_content = json.dumps(content, ensure_ascii=False, indent=2)
    else:
        # Text mode - preserve exact content
        formatted_content = content if isinstance(content, str) else str(content)

    # Create parent directories and write
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(formatted_content)

    return str(path_obj.absolute())


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


def run_for_each_step(step: Dict[str, Any], context: Dict[str, Any], pipeline_config: Dict[str, Any]) -> str | None:
    """Execute a for-each loop step"""
    input_data = resolve(step.get("input", []), context)
    item_var = step.get("item_var", "item")
    steps = step.get("steps", [])

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
    """Execute an if step - evaluate condition and run nested steps"""
    nested_steps = step.get("steps", [])
    name = step.get("name", "unnamed")

    # Condition already evaluated in run_step(), we only get here if TRUE
    logger.debug(f"✅ Condition true for '{name}', running nested steps")

    # Run nested steps
    if nested_steps:
        logger.debug(f"   Running {len(nested_steps)} nested steps")
        for nested_step in nested_steps:
            after_action = run_step(nested_step, context, pipeline_config)
            if after_action in ["exit", "continue"]:
                logger.debug(f"   Propagating after action: {after_action}")
                return after_action  # Propagate up

    return None  # Normal completion


def run_pipeline(
    pipeline_file, vars=None, dry_run=False, verbose=False, skip_lint=False, log_file='llmflow.log'
):
    """
    Run a pipeline from a YAML file.

    Args:
        pipeline_file: Path to the pipeline YAML file
        vars: Optional dictionary of variables to override
        dry_run: If True, only validate and show what would run
        verbose: Enable verbose logging
        skip_lint: Skip linting validation
        log_file: Path to log file (default: llmflow.log in cwd)
    """
    from pathlib import Path
    from pydantic import ValidationError
    from llmflow.pipeline_schema import PipelineConfig  # FIX: Correct module name

    # Reset logger singleton for new run - ensures log file is overwritten, not appended
    Logger.reset(log_file=log_file)
    # Force recreation of singleton by calling Logger() again
    _ = Logger()

    # Set up logging
    if verbose:
        logger.set_level("DEBUG")

    # Initialize telemetry collector
    telemetry = TelemetryCollector(pipeline_name=str(pipeline_file) if not isinstance(pipeline_file, dict) else "inline")

    # Add current working directory to sys.path for local plugin imports
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    # Accept dict pipelines directly
    if isinstance(pipeline_file, dict):
        pipeline_path = None
        pipeline_config = pipeline_file

        # Check for pipeline-level log_level configuration
        linter_config = pipeline_config.get('linter_config', {})
        if isinstance(linter_config, dict):
            pipeline_log_level = linter_config.get('log_level', '').upper()
            if pipeline_log_level == 'DEBUG':
                logger.set_level("DEBUG")
    else:
        pipeline_path = Path(pipeline_file)
        if not pipeline_path.exists():
            logger.error(f"❌ Pipeline file not found: {pipeline_file}")
            logger.error(f"   Current directory: {os.getcwd()}")
            logger.error("   💡 Tip: Make sure you're running from the correct directory")
            raise SystemExit(1)

        # Load and parse YAML with error handling
        try:
            with open(pipeline_path, "r") as f:
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
    if not skip_lint and pipeline_path is not None:
        logger.info("🔍 Validating pipeline...")
        lint_result = lint_pipeline_full(str(pipeline_path))
        if lint_result and not lint_result.valid:
            logger.error("❌ Pipeline validation failed:")
            for error in lint_result.errors:
                logger.error(f"  - {error}")
            raise SystemExit(1)

    # Get variables from pipeline
    pipeline_root = pipeline_config.get("pipeline", pipeline_config)
    pipeline_vars = pipeline_root.get("variables", {})

    # Store telemetry in pipeline config for step access
    pipeline_config["_telemetry"] = telemetry

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
    try:
        for step in steps:
            after_action = run_step(step, context, pipeline_config)
            if after_action == "exit":
                logger.info(f"🛑 'after: exit' - exiting pipeline early after step '{step.get('name')}'.")
                break
            elif after_action == "continue":
                continue  # Default behavior
    except KeyboardInterrupt:
        logger.info("\n⚠️  Execution interrupted by user (Ctrl+C)")
        logger.info("   Pipeline stopped. Partial results may be available.")
        raise  # Re-raise to be caught by CLI handler

    logger.info("Pipeline complete.")

    # Generate and log telemetry summary
    summary = telemetry.generate_summary()
    logger.info("\n" + "="*80)
    logger.info("📊 Pipeline Telemetry Summary")
    logger.info("="*80)
    logger.info(summary)

    # Generate optimization suggestions
    mcp_config = pipeline_config.get("mcp", {})
    mcp_max_iterations = mcp_config.get("max_iterations", 10)
    suggestions = generate_optimization_suggestions(
        telemetry.pipeline.steps,
        mcp_max_iterations=mcp_max_iterations
    )
    if suggestions:
        logger.info("\n" + "="*80)
        logger.info("💡 Optimization Suggestions")
        logger.info("="*80)
        for suggestion in suggestions:
            logger.info(f"  • {suggestion}")
        logger.info("="*80)

    return context
