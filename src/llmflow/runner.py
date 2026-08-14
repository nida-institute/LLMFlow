import importlib
import inspect
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from llmflow.plugins.basex import run_basex
from llmflow.plugins.loader import discover_plugins
from llmflow.utils.io import validate_all_templates
from llmflow.utils.linter import lint_pipeline_full
from llmflow.utils.llm_runner import call_llm, run_llm_with_mcp_tools
from llmflow.utils.context import _MISSING, get_from_context, resolve
from llmflow.utils.file_io import WRITTEN_FILES, _record_written_file, save_content_to_file
from llmflow.utils.step_outputs import handle_step_outputs, handle_step_saveas
from llmflow.utils.debug import _get_debug_dir, _clear_debug_dir
from llmflow.steps.plugin import run_plugin_step
from llmflow.steps.basex import run_basex_step
from llmflow.steps.function import run_function_step
from llmflow.steps.duckdb import run_duckdb_step
from llmflow.steps.json_step import run_json_step
from llmflow.steps.load import run_load_step
from llmflow.steps.save import run_save_step
from llmflow.steps.llm import render_prompt, build_debug_filename, apply_output_template, run_llm_step
from llmflow.steps.for_each import run_for_each_step
from llmflow.steps.window import run_window_step, run_window_advance_step
from llmflow.steps.if_step import run_if_step
from llmflow.exceptions import (
    StepExecutionError,
    ForEachIterationError,
    VariableResolutionError,
    LLMProviderError,
    PluginError,
    StepRetryError,
    StepRewindError,
)
from llmflow.modules.mcp import init_mcp_client
from llmflow.utils.guards import build_eval_locals, build_step_eval_ctx, enforce_require, collect_warnings, _safe_eval
from llmflow.utils.io import sanitize_filename
from llmflow.utils.rewind import StepRewindManager
from datetime import datetime

# Single unified logger instance
logger = Logger()

# Shared YAML loader that recognises LLMFlow tags such as !window_advance.
# Defined in yaml_loader.py to avoid circular imports with linter.py.
from llmflow.yaml_loader import load_pipeline_config  # noqa: E402


_RETRY_MISSING = object()


def _snapshot_retry_targets(step, context):
    snapshot = {"outputs": {}, "append_to": None}

    outputs = step.get("output")
    if isinstance(outputs, str):
        output_names = [outputs]
    elif isinstance(outputs, list):
        output_names = outputs
    else:
        output_names = []

    for name in output_names:
        if name in context:
            snapshot["outputs"][name] = deepcopy(context[name])
        else:
            snapshot["outputs"][name] = _RETRY_MISSING

    append_to = step.get("append_to")
    if append_to:
        exists = append_to in context
        value = deepcopy(context[append_to]) if exists else None
        snapshot["append_to"] = (append_to, exists, value)

    return snapshot


def _restore_retry_targets(context, snapshot):
    for name, value in snapshot.get("outputs", {}).items():
        if value is _RETRY_MISSING:
            context.pop(name, None)
        else:
            context[name] = deepcopy(value)

    append_snapshot = snapshot.get("append_to")
    if append_snapshot:
        name, existed_before, value = append_snapshot
        if existed_before:
            context[name] = deepcopy(value)
        else:
            context.pop(name, None)


def _evaluate_condition_expression(condition_expr, context, *, label="condition"):
    if condition_expr is None:
        return False

    if isinstance(condition_expr, bool):
        return condition_expr
    if isinstance(condition_expr, (int, float)):
        return bool(condition_expr)

    if isinstance(condition_expr, str):
        stripped = condition_expr.strip()
        # ${...} — evaluate the inner expression via AST, bypassing resolve().
        # resolve() looks up the leading identifier in context and discards any
        # trailing operators (e.g. "is None", "is not None"), so
        # "${x is None}" would silently return the raw value of x rather than
        # the result of the comparison.  _safe_eval handles the full expression
        # correctly because it puts all context variables in scope as locals.
        if stripped.startswith("${") and stripped.endswith("}"):
            expr_str = stripped[2:-1]
            try:
                return _safe_eval(expr_str, build_eval_locals(context))
            except Exception as exc:
                logger.warning(f"{label} eval failed: {expr_str} - {exc}")
                return False

        # Plain (non-${}) string — try resolve() first, then eval.
        try:
            resolved = resolve(condition_expr, context)
        except Exception as exc:
            logger.warning(f"{label} resolution failed: {condition_expr} - {exc}")
            resolved = condition_expr

        if isinstance(resolved, bool):
            return resolved
        if isinstance(resolved, (int, float)):
            return bool(resolved)
        expr_str = resolved if isinstance(resolved, str) else str(resolved)
        if not expr_str:
            return False
        try:
            return _safe_eval(expr_str, build_eval_locals(context))
        except Exception as exc:
            logger.warning(f"{label} eval failed: {expr_str} - {exc}")
            return False

    return bool(condition_expr)


def _evaluate_retry_condition(condition_expr, context):
    return _evaluate_condition_expression(condition_expr, context, label="retry condition")


def _coerce_retry_number(value, default, context, cast_type: type = int):
    if value is None:
        return default

    try:
        resolved = resolve(value, context)
    except Exception:
        resolved = value

    try:
        return cast_type(resolved)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _execute_step_with_retry(step, context, retry_cfg, execute_once):
    if not isinstance(retry_cfg, dict):
        return execute_once()

    step_name = step.get("name", "unnamed")
    max_attempts = _coerce_retry_number(retry_cfg.get("max_attempts", 3), 3, context, int)
    if max_attempts < 1:
        max_attempts = 1
    delay_seconds = _coerce_retry_number(retry_cfg.get("delay_seconds", 2), 2.0, context, float)
    if delay_seconds < 0:
        delay_seconds = 0
    condition_expr = retry_cfg.get("condition")

    snapshot = _snapshot_retry_targets(step, context)
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        context["_retry_attempt"] = attempt
        try:
            after_action = execute_once()
            last_exception = None
        except KeyboardInterrupt:
            context.pop("_retry_attempt", None)
            raise
        except Exception as exc:
            last_exception = exc
            retry_needed = True
            reason = f"exception {type(exc).__name__}: {exc}"
        else:
            if after_action:
                context.pop("_retry_attempt", None)
                return after_action

            retry_needed = _evaluate_retry_condition(condition_expr, context)
            if not retry_needed:
                context.pop("_retry_attempt", None)
                return None

            reason = f"condition '{condition_expr}' still true"

        if attempt == max_attempts:
            _restore_retry_targets(context, snapshot)
            context.pop("_retry_attempt", None)
            message = (
                f"Step '{step_name}' failed after {max_attempts} attempts"
                if last_exception
                else f"Step '{step_name}' did not meet retry condition after {max_attempts} attempts"
            )
            raise StepRetryError(
                message,
                step_name=step_name,
                attempts=max_attempts,
                condition=condition_expr,
                context=context,
                original_error=last_exception,
            )

        logger.warning(
            f"🔁 Retry {attempt}/{max_attempts} for step '{step_name}' ({reason}). Next attempt in {delay_seconds}s"
        )
        _restore_retry_targets(context, snapshot)
        if delay_seconds:
            time.sleep(delay_seconds)

    context.pop("_retry_attempt", None)
    return None


def _resolve_saveas_path_for_resume(step: dict, context: dict) -> "Path | None":
    """Return the resolved saveas Path for resume checking, or None if not resolvable."""
    saveas = step.get("saveas")
    try:
        if isinstance(saveas, str):
            return Path(str(resolve(saveas, context)))
        if isinstance(saveas, dict):
            return Path(str(resolve(saveas.get("path", ""), context)))
    except Exception:
        pass
    return None


def _load_resume_output(step: dict, path: "Path", context: dict) -> None:
    """Load file content into the step's declared output variable in context."""
    content = path.read_text(encoding="utf-8")
    outputs = step.get("output")
    if isinstance(outputs, str):
        context[outputs] = content
    elif isinstance(outputs, list) and outputs:
        context[outputs[0]] = content


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

    step_completed = False

    try:
        # Check condition BEFORE executing any step type
        condition = step.get("condition")
        if condition:
            logger.debug(f"🔍 Evaluating condition: {condition}")
            condition_result = _evaluate_condition_expression(condition, context)
            logger.debug(f"   Condition result: {condition_result}")
            if not condition_result:
                logger.info(f"⏭️  Skipping step '{step.get('name')}' (condition false)")
                return None

        # Resume: skip step if its saveas file already exists on disk. See GH #166.
        if pipeline_config and pipeline_config.get("_resume") and "saveas" in step:
            _resume_path = _resolve_saveas_path_for_resume(step, context)
            if _resume_path and _resume_path.exists():
                _load_resume_output(step, _resume_path, context)
                logger.info(f"⏭️  Resume: skipping '{step.get('name')}' ({_resume_path.name} exists)")
                return None

        def _execute_once():
            local_after_action = None

            if step.get("_tag") == "window_advance":
                run_window_advance_step(step, context, pipeline_config or {}, run_step)
            elif step_type == "for-each":
                local_after_action = run_for_each_step(step, context, pipeline_config or {}, run_step)
            elif step_type == "window":
                local_after_action = run_window_step(step, context, pipeline_config or {}, run_step)
            elif step_type == "llm":
                result = run_llm_step(step, context, pipeline_config or {})
                handle_step_outputs(step, result, context)
            elif step_type == "function":
                result = run_function_step(step, context, pipeline_config)
            elif step_type == "duckdb":
                result = run_duckdb_step(step, context, pipeline_config)
            elif step_type == "if":
                local_after_action = run_if_step(step, context, pipeline_config, run_step)
            elif step_type == "basex":
                run_basex_step(step, context, pipeline_config)
            elif step_type == "json":
                run_json_step(step, context)
            elif step_type in ("load_json", "load_yaml", "load_xml", "load_csv",
                               "load_tsv", "load_text", "load_directory"):
                run_load_step(step, context)
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

            return local_after_action

        retry_cfg = step.get("retry")
        if retry_cfg:
            after_action = _execute_step_with_retry(step, context, retry_cfg, _execute_once)
        else:
            after_action = _execute_once()

        step_completed = True

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
                outputs = step.get("output")
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
                enforce_require(eval_ctx, step.get("require") or [], step_name=step.get("name"), context_info=context_info)

            # Non-blocking warnings: collect and attach to context
            if "warn" in step and step.get("warn"):
                msgs = collect_warnings(eval_ctx, step.get("warn") or [])
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

        # Persist rewind checkpoints when enabled
        manager = pipeline_config.get("_rewind_manager") if pipeline_config else None
        if manager:
            if step_completed:
                manager.record_step(step, context)
            else:
                context.pop("_last_saved_files", None)
        else:
            context.pop("_last_saved_files", None)


_LOADER_FORMATS = {"json", "yaml", "xml", "csv", "tsv", "text"}


def run_pipeline(
    pipeline_file,
    vars=None,
    dry_run=False,
    verbose=False,
    skip_lint=False,
    log_file='llmflow.log',
    rewind_to: str | None = None,
    stop_after: str | None = None,
    resume: bool = False,
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
        rewind_to: Optional step name to replay from saved artifacts instead of executing
        stop_after: Optional step name after which to halt execution
    """
    # Plugins are needed only to execute a pipeline (LLMFlow#178).
    discover_plugins()

    from pathlib import Path
    from pydantic import ValidationError
    from llmflow.pipeline_schema import PipelineConfig  # FIX: Correct module name

    # Reset per-run state
    global WRITTEN_FILES
    WRITTEN_FILES = []

    # Debug dir clear is deferred until after pipeline load so we can resolve
    # intermediate_file_directory. See _clear_debug_dir() call below.

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
            pipeline_config = load_pipeline_config(pipeline_path)
        except yaml.YAMLError as e:
            logger.error(f"❌ YAML syntax error in {pipeline_file}:")
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark  # type: ignore[attr-defined]
                logger.error(f"   Line {mark.line + 1}, Column {mark.column + 1}")
                logger.error(f"   {e.problem}")  # type: ignore[attr-defined]
                if hasattr(e, 'context'):
                    logger.error(f"   Context: {e.context}")  # type: ignore[attr-defined]
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
        lint_result = lint_pipeline_full(
            str(pipeline_path),
            vars=vars,
            rewind_to=rewind_to,
        )
        if lint_result and not lint_result.valid:
            logger.error("❌ Pipeline validation failed:")
            for error in lint_result.errors:
                logger.error(f"  - {error}")
            raise SystemExit(1)

    # Resolve the pipeline block (root, or nested under a top-level `pipeline:` key)
    pipeline_root = pipeline_config.get("pipeline", pipeline_config)

    # Initialize rewind manager (always record checkpoints; replay only when requested)
    rewind_manager = StepRewindManager(rewind_to=rewind_to)

    # Store telemetry, rewind manager, and resume flag in pipeline config for step access
    pipeline_config["_telemetry"] = telemetry
    pipeline_config["_rewind_manager"] = rewind_manager
    pipeline_config["_resume"] = resume

    # Derive pipeline name for debug subdirectory organisation
    if pipeline_path is not None:
        pipeline_name = pipeline_path.stem
    else:
        raw_name = str(pipeline_config.get("name", "pipeline"))
        pipeline_name = re.sub(r'[^a-zA-Z0-9-]', '-', raw_name).strip('-').lower()
    pipeline_config["_pipeline_name"] = pipeline_name

    # Initialize context: dir declarations are base, pipeline vars override, CLI vars win.
    # Shared with the public Pipeline.resolve() accessor so the two can't drift (LLMFlow#187).
    from llmflow.utils.context import build_run_context
    context = build_run_context(pipeline_config, vars)
    logger.debug(f"Variables: {vars}")

    # Clear this pipeline's debug subdirectory now that we can resolve intermediate_file_directory
    _clear_debug_dir(pipeline_config, context, dry_run, pipeline_name)

    # Redirect llmflow.log into debug/{pipeline_name}/ when intermediate_file_directory is declared
    if pipeline_config.get("intermediate_file_directory") and not dry_run:
        _debug_log = str(Path(_get_debug_dir(pipeline_config, context, pipeline_name)) / "llmflow.log")
        Logger.reset(log_file=_debug_log)
        _ = Logger()
        linter_cfg = pipeline_config.get("linter_config", {}) or {}
        if isinstance(linter_cfg, dict) and linter_cfg.get("log_level", "").upper() == "DEBUG":
            logger.set_level("DEBUG")
        if verbose:
            logger.set_level("DEBUG")

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
            step_name = step.get("name", "unnamed")

            if rewind_manager and rewind_manager.should_replay(step_name, step=step):
                try:
                    rewind_manager.replay_step(step, context)
                except StepRewindError as exc:
                    logger.error(f"❌ {exc}")
                    raise

                if stop_after and step_name == stop_after:
                    logger.info(f"🛑 Stop-after '{step_name}' reached (rewind).")
                    break
                continue

            after_action = run_step(step, context, pipeline_config)

            # If we are still in the rewind phase and just executed a step normally
            # (because it had no saveas), check whether it was the rewind target so
            # we can mark the phase complete and let subsequent steps run normally.
            if rewind_manager and rewind_manager.in_rewind_phase:
                rewind_manager.mark_target_reached(step_name)

            if stop_after and step_name == stop_after:
                logger.info(f"🛑 Stop-after '{step_name}' reached.")
                break

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
    telemetry.complete_pipeline()

    # Generate and log telemetry summary
    summary = telemetry.generate_summary()
    logger.info("\n" + "="*80)
    logger.info("📊 Pipeline Telemetry Summary")
    logger.info("="*80)
    logger.info(summary)

    # NOTE: Optimization suggestions table suppressed in favor of detailed cost breakdown
    # Detailed per-model/per-prompt breakdown is included in the telemetry summary above.

    return context
