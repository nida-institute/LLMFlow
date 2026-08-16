"""LLM step handler — prompt rendering, debug filename building, LLM call."""

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from llmflow.modules.logger import Logger
from llmflow.modules.mcp import init_mcp_client
from llmflow.utils.context import resolve
from llmflow.utils.debug import _get_debug_dir
from llmflow.utils.file_io import save_content_to_file
from llmflow.utils.io import sanitize_filename
from llmflow.utils.llm_runner import call_llm, run_llm_with_mcp_tools
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def build_debug_filename(step: Dict[str, Any], context: Dict[str, Any], request_or_response: str) -> str:
    """Build a debug filename from passage (or timestamp), prompt file, and request/response type.

    Format with passage: {passage}_{prompt_file}_{request_or_response}.txt
    Format without passage: {timestamp}_{prompt_file}_{request_or_response}.txt
    """
    parts = []

    passage = context.get("passage") or context.get("Citation") or context.get("scene", {}).get("Citation")
    if passage:
        parts.append(sanitize_filename(str(passage)))
    else:
        parts.append(datetime.now().strftime("%Y-%m-%d-%H%M%S"))

    prompt_config = step.get("prompt", {})
    if isinstance(prompt_config, dict):
        prompt_file = prompt_config.get("file", "")
    elif isinstance(prompt_config, str):
        prompt_file = prompt_config
    else:
        prompt_file = ""

    if prompt_file:
        parts.append(sanitize_filename(Path(prompt_file).stem))
    else:
        parts.append(sanitize_filename(step.get("name", "llm_step")))

    iteration_meta = None
    stack = context.get("_for_each_stack")
    if isinstance(stack, list) and stack:
        iteration_meta = stack[-1]
    if iteration_meta is None:
        iteration_meta = context.get("_for_each_meta")

    if iteration_meta:
        level = iteration_meta.get("level")
        if level:
            parts.append(f"lvl{level}")
        var_name = iteration_meta.get("variable")
        label_value = iteration_meta.get("label") or iteration_meta.get("value")
        if var_name and label_value:
            var_token = sanitize_filename(str(var_name)) or "item"
            label_token = sanitize_filename(str(label_value)) or "value"
            parts.append(f"{var_token}-{label_token}")

    parts.append(request_or_response)
    return "_".join(parts) + ".txt"


def render_prompt(prompt_config: Union[str, Dict[str, Any]], context: Dict[str, Any]) -> str:
    """Render a prompt from a file with variable substitution."""
    resolved_prompt = resolve(prompt_config, context)

    if isinstance(resolved_prompt, dict):
        prompt_file = resolved_prompt.get("file")
        if not isinstance(prompt_file, str):
            raise ValueError(f"Prompt 'file' must be a string, got {type(prompt_file)}")
        prompt_path = Path(prompt_file)

        prompt_inputs = resolved_prompt.get("inputs", {})
        if prompt_inputs:
            extended_context = {**context}
            for key, value in prompt_inputs.items():
                extended_context[key] = resolve(value, context)
            logger.debug(f"Extended context with prompt inputs: {list(extended_context.keys())}")
            context = extended_context

    elif isinstance(resolved_prompt, str):
        prompt_path = Path(resolved_prompt)
    else:
        raise ValueError(f"Prompt config must be string or dict, got {type(resolved_prompt)}")

    from llmflow.utils.io import resolve_prompt_path, expand_mixins
    prompts_dir = str(context.get("prompts_dir", "prompts"))
    full_prompt_path = resolve_prompt_path(str(prompt_path), prompts_dir)

    logger.debug(f"Loading prompt from: {full_prompt_path}")
    rendered_prompt = full_prompt_path.read_text(encoding="utf-8")

    rendered_prompt = expand_mixins(rendered_prompt, full_prompt_path)

    from llmflow.utils.linter import parse_prompt_header, extract_template_variables

    header = parse_prompt_header(str(full_prompt_path))
    if header is not None:
        declared = set()
        requires = header.get("requires") or []
        optional = header.get("optional") or []
        if isinstance(requires, list):
            declared.update(requires)
        if isinstance(optional, list):
            declared.update(optional)

        frontmatter_match = re.search(
            r"^---[ \t]*\n.*?\n---[ \t]*\n?", rendered_prompt, re.DOTALL | re.MULTILINE
        )
        if not frontmatter_match:
            frontmatter_match = re.search(r"<!--(.*?)-->", rendered_prompt, re.DOTALL)

        body = rendered_prompt[frontmatter_match.end():] if frontmatter_match else rendered_prompt
        body_vars = extract_template_variables(body)

        undeclared = body_vars - declared
        if undeclared:
            raise ValueError(
                f"❌ Prompt contract violation in {full_prompt_path.name}:\n"
                f"   Variables used in prompt body but not declared in header:\n"
                f"   {', '.join(sorted(undeclared))}\n\n"
                f"   Add these to 'requires:' or 'optional:' in the prompt header."
            )

        missing_required = [var for var in requires if var not in context]
        if missing_required:
            raise ValueError(
                f"❌ Prompt contract violation in {full_prompt_path.name}:\n"
                f"   Required variables missing from context:\n"
                f"   {', '.join(sorted(missing_required))}\n\n"
                f"   These must be provided via prompt.inputs or earlier pipeline steps."
            )

    if header is not None:
        declared = set()
        requires = header.get("requires") or []
        optional = header.get("optional") or []
        if isinstance(requires, list):
            declared.update(requires)
        if isinstance(optional, list):
            declared.update(optional)
        for key in declared:
            if key in context:
                rendered_prompt = rendered_prompt.replace(f"{{{{{key}}}}}", str(context[key]))
    else:
        for key, val in context.items():
            rendered_prompt = rendered_prompt.replace(f"{{{{{key}}}}}", str(val))

    rendered_prompt = resolve(rendered_prompt, context)

    logger.debug(f"Rendered prompt length: {len(rendered_prompt)} chars")
    logger.debug(f"Rendered prompt preview (after substitution): {rendered_prompt[:300]}...")

    return str(rendered_prompt)


def apply_output_template(content: Any, template_path: Optional[str], context: Dict[str, Any]) -> str:
    """Apply an output template to format LLM response content."""
    if not template_path:
        return str(content) if content is not None else ""
    from llmflow.utils.io import render_markdown_template
    return render_markdown_template(template_path, {**context, "content": content}, context)


def run_llm_step(step: Dict[str, Any], context: Dict[str, Any], pipeline_config: Dict[str, Any]) -> Any:
    """Execute an LLM step and return its result."""
    name = step.get("name", "unnamed_llm_step")

    logger.info(f"🤖 Starting LLM step: {name}")
    logger.debug(f"Step details: {step}")
    logger.debug(f"Context keys available: {list(context.keys())}")

    telemetry = pipeline_config.get("_telemetry")

    rendered_prompt = render_prompt(step["prompt"], context)

    try:
        if (pipeline_config.get("linter_config", {}) or {}).get("log_level", "").lower() == "debug":
            filename = build_debug_filename(step, context, "request")
            prompt_path = str(
                Path(_get_debug_dir(
                    pipeline_config,
                    context,
                    pipeline_config.get("_pipeline_name", "pipeline"),
                    pipeline_config.get("_debug_run_key"),
                ))
                / filename
            )
            save_content_to_file(rendered_prompt, prompt_path, format="text")
            logger.debug(f"📝 Saved request to {prompt_path}")
    except Exception as e:
        logger.debug(f"(request debug save skipped: {e})")

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

    merged_config = {
        "model": "gpt-4o",
        "temperature": 0.7,
        "timeout_seconds": 30,
    }
    merged_config.update(llm_config)
    merged_config.update(step_options)
    merged_config.update(step_config)

    from llmflow.utils.llm_runner import get_model_family
    final_model = merged_config.get("model", "gpt-4o")
    model_family = get_model_family(final_model)

    if telemetry:
        telemetry.start_step(name, "llm", model=final_model)

    if "max_tokens" not in merged_config and "max_completion_tokens" not in merged_config:
        if model_family == "o1":
            merged_config["max_completion_tokens"] = 2500
        elif model_family != "gpt-5":
            merged_config["max_tokens"] = 2500

    if "mcp" in step:
        merged_config["mcp"] = step["mcp"]

    output_type = step.get("output_type", "text")

    if output_type == "text":
        saveas_config = step.get("saveas")
        if saveas_config:
            path = saveas_config if isinstance(saveas_config, str) else saveas_config.get("path", "")
            if path.endswith(".json"):
                output_type = "json"
                logger.debug(f"    🔍 Auto-detected JSON output from saveas path: {path}")

    mcp_client = init_mcp_client(step, pipeline_config)

    try:
        _llm_retry_cfg = step.get("retry", {}) if isinstance(step.get("retry"), dict) else {}
        max_retries = _llm_retry_cfg.get("max_attempts", 3)
        retry_delay = _llm_retry_cfg.get("delay_seconds", 2)

        response = None
        for attempt in range(max_retries):
            try:
                if mcp_client:
                    logger.info(f"    ⏳ Calling {merged_config.get('model')} with MCP tools for step '{name}'...")
                    response = run_llm_with_mcp_tools(
                        rendered_prompt,
                        merged_config,
                        mcp_client,
                        output_type,
                        step_name=step.get("name", "unknown"),
                        step=step,
                        context=context,
                        pipeline_config=pipeline_config,
                    )
                else:
                    logger.info(f"    ⏳ Calling {merged_config.get('model')} for step '{name}'...")
                    response = call_llm(rendered_prompt, config=merged_config, output_type=output_type)

                break

            except KeyboardInterrupt:
                logger.info("⚠️  User interrupted - exiting")
                raise

            except Exception as e:
                err_type = type(e).__name__
                err_msg = str(e)[:200]
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"⚠️  LLM error (attempt {attempt + 1}/{max_retries}): {err_type}: {err_msg}")
                    logger.warning(f"    Step: '{name}', model: {merged_config.get('model')}")
                    logger.warning(f"    Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ LLM call failed after {max_retries} attempts")
                    logger.error(f"    Step: '{name}', model: {merged_config.get('model')}")
                    logger.error(f"    Final error ({err_type}): {err_msg}")
                    raise

        usage = {}
        response_content = response

        if isinstance(response, dict):
            if "content" in response:
                response_content = response["content"]
                usage = response.get("usage", {})

        try:
            pt = int(usage.get("prompt_tokens", 0) or 0)
            ct = int(usage.get("completion_tokens", 0) or 0)
        except Exception:
            pt, ct = 0, 0

        if model_family in ("gpt-5", "o1") and pt == 0 and ct == 0:
            def _estimate_tokens(text: Any) -> int:
                try:
                    s = text if isinstance(text, str) else str(text or "")
                    return max(1, int(len(s) / 4))
                except Exception:
                    return 0

            est_prompt = _estimate_tokens(rendered_prompt)
            est_completion = _estimate_tokens(response_content)
            usage = {
                "prompt_tokens": est_prompt,
                "completion_tokens": est_completion,
                "total_tokens": est_prompt + est_completion,
            }
            logger.warning(
                f"⚠️  No usage data from Responses API; estimated tokens for cost "
                f"(prompt≈{est_prompt}, completion≈{est_completion})."
            )

        try:
            if response_content is not None and (pipeline_config.get("linter_config", {}) or {}).get("log_level", "").lower() == "debug":
                filename = build_debug_filename(step, context, "response")
                resp_path = str(
                    Path(_get_debug_dir(
                    pipeline_config,
                    context,
                    pipeline_config.get("_pipeline_name", "pipeline"),
                    pipeline_config.get("_debug_run_key"),
                ))
                    / filename
                )
                save_content_to_file(
                    response_content if isinstance(response_content, str) else str(response_content),
                    resp_path,
                    format="text",
                )
                logger.debug(f"🗒️ Saved response to {resp_path}")
        except Exception as e:
            logger.debug(f"(response debug save skipped: {e})")

        if response_content and "template" in step:
            template_path = step.get("template")
            response_content = apply_output_template(response_content, template_path, context)

        logger.info(f"✅ Completed LLM step: {name}")

        if telemetry:
            telemetry.end_step(
                name,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )

        return response_content

    finally:
        if mcp_client:
            import asyncio
            asyncio.run(mcp_client._async_close())
