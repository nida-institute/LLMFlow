from dataclasses import dataclass
from typing import List
import re
from difflib import unified_diff
from pathlib import Path

import click
import yaml
from pydantic import ValidationError
from llmflow.pipeline_schema import PipelineConfig

from llmflow.modules.logger import Logger

# Use unified logger
logger = Logger()


def log_and_screen(msg, color="white", level="info"):
    """Log to file and display once on screen with color"""
    # Log to unified logger (goes to both file and screen)
    if level == "error":
        logger.error(msg)
    elif level == "warning":
        logger.warning(msg)
    else:
        logger.info(msg)

    # Additional colored screen output (optional, since logger already handles screen output)
    if color != "white":  # Only add color if specifically requested
        click.secho(msg, fg=color, err=True)


def parse_prompt_header(prompt_path):
    text = Path(prompt_path).read_text(encoding="utf-8")
    match = re.search(r"<!--(.*?)-->", text, re.DOTALL)
    if not match:
        return None

    block = match.group(1).strip()
    try:
        data = yaml.safe_load(block)
        return data.get("prompt", {})
    except Exception:
        return None


def extract_template_variables(template_content):
    """Extract variables from templates that use {{ variable }} syntax"""
    # Find all {{ variable }} patterns, allowing spaces
    variable_pattern = r"\{\{\s*([^}]+?)\s*\}\}"
    variables = set()

    for match in re.finditer(variable_pattern, template_content):
        var_name = match.group(1).strip()
        # Skip template logic like {{#if}} or {{/endif}}
        if (
            not var_name.startswith("#")
            and not var_name.startswith("/")
            and not var_name.startswith("%")
        ):
            variables.add(var_name)

    return variables


def format_diff_box(step, file, declared, passed):
    declared_sorted = sorted(declared)
    passed_sorted = sorted(passed)
    diff = list(
        unified_diff(
            declared_sorted,
            passed_sorted,
            fromfile="prompt requires",
            tofile="pipeline inputs",
            lineterm="",
        )
    )
    if not diff:
        return ""
    border = "─" * 76
    lines = [
        f"╭─🔍 Contract Mismatch: {file} ─{border[len(' Contract Mismatch: ─') - len(file):]}",
        f"│ Step: {step}".ljust(78) + "│",
        "│ ❌ Inputs passed to this step do not match the prompt contract.".ljust(78)
        + "│",
        "│".ljust(78) + "│",
    ]
    lines += [f"│ {line}".ljust(78) + "│" for line in diff]
    lines.append("╰" + "─" * 78 + "╯")
    return "\n".join(lines)


def collect_all_steps(items):
    """Recursively collect all steps, including nested for-each and substeps."""
    all_steps = []

    # Handle both list of steps and individual step
    if isinstance(items, list):
        for step in items:
            all_steps.extend(collect_all_steps(step))
    elif isinstance(items, dict):
        all_steps.append(items)

        # Check for nested steps in for-each
        if items.get("type") == "for-each" and "steps" in items:
            nested_steps = items["steps"]
            all_steps.extend(collect_all_steps(nested_steps))

    return all_steps


def validate_all_step_contracts(all_steps, log_func, pipeline_root=None):
    """Validate all LLM steps against their prompt contracts"""
    errors = []
    validated_count = 0

    for step in all_steps:
        step_name = step.get("name", "unnamed")
        step_type = step.get("type", "")

        # Check append_to without outputs
        if "append_to" in step:
            append_to_value = step["append_to"]
            if not step.get("outputs"):
                if isinstance(append_to_value, str) and append_to_value.strip():
                    errors.append(
                        f"❌ Step '{step_name}': append_to: {append_to_value} requires 'outputs' to be specified"
                    )
                continue

        # Only validate contracts for LLM steps
        if step_type == "llm":
            log_func(
                f"🔍 Validating step '{step_name}' contract: {step.get('prompt', {}).get('file', 'NO_FILE')}"
            )

            prompt_config = step.get("prompt", {})
            prompt_file = prompt_config.get("file")

            if not prompt_file:
                errors.append(f"❌ Step '{step_name}': No prompt file specified")
                continue

            # Get prompts_dir from pipeline variables
            prompts_dir = "prompts"
            if pipeline_root:
                variables = pipeline_root.get("variables", {})
                prompts_dir = variables.get("prompts_dir", "prompts")

            # Try multiple paths
            prompt_path = None
            possible_paths = [
                f"{prompts_dir}/{prompt_file}",  # Use pipeline's prompts_dir
                f"prompts/{prompt_file}",  # Fallback to standard
                prompt_file,  # Raw filename (last resort)
            ]

            for possible_path in possible_paths:
                if Path(possible_path).exists():
                    prompt_path = possible_path
                    break

            if not prompt_path:
                errors.append(
                    f"❌ Step '{step_name}': Prompt file not found: {prompt_file}"
                )
                log_func(f"❌ Step '{step_name}' contract validation failed")
                continue

            try:
                # FIXED: Just pass the path to parse_prompt_header, don't read content separately
                prompt_data = parse_prompt_header(prompt_path)

                if not prompt_data:
                    errors.append(
                        f"❌ Step '{step_name}': Invalid prompt header in {prompt_path}"
                    )
                    continue

                # Validate step inputs match prompt requirements
                step_inputs = prompt_config.get("inputs", {})
                required_inputs = prompt_data.get("requires", [])

                missing_inputs = [
                    inp for inp in required_inputs if inp not in step_inputs
                ]
                if missing_inputs:
                    errors.append(
                        f"❌ Step '{step_name}': Missing required inputs: {missing_inputs}"
                    )
                    log_func(f"❌ Step '{step_name}' contract validation failed")
                else:
                    log_func(f"✅ Step '{step_name}' contract validation passed")
                    validated_count += 1

            except Exception as e:
                errors.append(
                    f"❌ Step '{step_name}': Error validating prompt {prompt_path}: {str(e)}"
                )
                log_func(f"❌ Step '{step_name}' contract validation failed")

    return errors, validated_count


def lint_pipeline_contracts(pipeline_path):
    """Validate that all pipeline steps match their prompt contracts"""
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    pipeline_root = pipeline.get("pipeline", pipeline)

    # ✅ CHECK IF LINTER IS DISABLED
    linter_config = pipeline_root.get("linter_config", {})
    if not linter_config.get("enabled", True):  # Default to enabled if not specified
        logger.info("ℹ️  Linter disabled by configuration, skipping validation")
        return

    all_steps = collect_all_steps(pipeline_root.get("steps", []))

    # Use the unified logger for output
    def unified_logger(msg, color="white", level="info"):
        log_and_screen(msg, color, level)

    errors, validated_count = validate_all_step_contracts(all_steps, unified_logger, pipeline_root)

    # Report final results
    if errors:
        logger.error(f"\n❌ Contract validation failed with {len(errors)} errors:")
        for error in errors:
            logger.error(f"  {error}")
        raise SystemExit("Pipeline contract validation failed")
    else:
        logger.info(f"\n✅ All {validated_count} step contracts valid")


def validate_template_step(step, errors, warnings):
    """Validate a template rendering step"""
    if step.get("type") != "function":
        return

    inputs = step.get("inputs", {})
    template_path = inputs.get("template_path")

    # Only validate if template_path is present
    if not template_path:
        return  # Skip if no template_path

    if not Path(template_path).exists():
        errors.append(
            f"❌ Step '{step['name']}': Template file not found: {template_path}"
        )
        return

    try:
        # Read template and extract {{variable}} patterns
        template_content = Path(template_path).read_text()
        template_vars = extract_template_variables(template_content)

        # Get variables provided to the template
        provided_vars = set()
        template_inputs = inputs.get("variables", {})
        if isinstance(template_inputs, dict):
            provided_vars = set(template_inputs.keys())

        # Check for missing variables - CHANGED: Make these errors, not warnings
        missing_vars = template_vars - provided_vars
        if missing_vars:
            for var in missing_vars:
                errors.append(
                    f"❌ Template '{template_path}' uses variable '{var}' but step '{step['name']}' doesn't provide it"
                )

    except Exception as e:
        errors.append(
            f"❌ Step '{step['name']}': Error reading template {template_path}: {e}"
        )


def validate_pipeline(pipeline_config):
    """Main pipeline validation function"""
    errors = []
    warnings = []

    steps = pipeline_config.get("steps", [])

    for step in steps:
        # Existing validations...

        # Add template validation
        validate_template_step(step, errors, warnings)

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def validate_pipeline_structure(pipeline_config):
    try:
        PipelineConfig(**pipeline_config)
        return []
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " → ".join(str(p) for p in err["loc"])
            errors.append(f"❌ Pipeline structure error: {err['msg']} (at [{loc}])")
        return errors


@dataclass
class LintResult:
    """Result of pipeline linting"""

    valid: bool
    errors: List[str]
    warnings: List[str]


def lint_pipeline_full(pipeline_path):
    """Lint pipeline and return result object instead of raising SystemExit"""
    all_errors = []
    all_warnings = []

    # Load pipeline first
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    pipeline_config = pipeline.get("pipeline", pipeline)

    # ✅ CHECK IF LINTER IS DISABLED
    linter_config = pipeline_config.get("linter_config", {})
    if not linter_config.get("enabled", True):  # Default to enabled if not specified
        logger.info("ℹ️  Linter disabled by configuration, skipping validation")
        return LintResult(valid=True, errors=[], warnings=[])

    # Print this once
    logger.info(f"Starting full pipeline lint for: {pipeline_path}")

    # 1. Structure validation
    logger.info("🔍 Validating pipeline structure...")
    structure_errors = validate_pipeline_structure(pipeline_config)
    if structure_errors:
        all_errors.extend(structure_errors)
        for error in structure_errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ Pipeline structure is valid")

    # 2. Contract validation
    all_steps = collect_all_steps(pipeline_config.get("steps", []))
    errors, validated_count = validate_all_step_contracts(all_steps, log_and_screen, pipeline_config)

    if errors:
        all_errors.extend(errors)
        for error in errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    else:
        logger.info(f"✅ All {validated_count} step contracts valid")

    # 3. Template validation
    logger.info("🔍 Validating pipeline templates...")
    template_errors = []
    template_warnings = []

    template_steps = [
        step for step in all_steps if step.get("inputs", {}).get("template_path")
    ]

    for step in template_steps:
        template_path = step.get("inputs", {}).get("template_path", "")
        logger.info(
            f"🔍 Validating template: {template_path} (step: {step.get('name')})"
        )

        validate_template_step(step, template_errors, template_warnings)

        if not template_errors:
            logger.info(f"✅ Template {template_path} is valid")

    if template_errors:
        all_errors.extend(template_errors)
        logger.error(
            f"\n❌ Template validation failed with {len(template_errors)} errors:"
        )
        for error in template_errors:
            logger.error(f"  {error}")
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    else:
        logger.info("✅ All templates validated successfully")

    # Show any warnings
    all_warnings.extend(template_warnings)
    for warning in all_warnings:
        logger.warning(f"⚠️  {warning}")

    logger.info("✅ Pipeline validation completed successfully")

    # Return success result
    return LintResult(valid=True, errors=[], warnings=all_warnings)


def check_step_outputs(step):
    """Warn if a step generates data but doesn't store it"""
    warnings = []

    # Check if step has append_to but no outputs
    if "append_to" in step and "outputs" not in step:
        warnings.append(
            f"Step '{step.get('name', 'unnamed')}' has append_to but no outputs"
        )

    # Check if LLM step has neither outputs nor append_to
    if step.get("type") == "llm" and "outputs" not in step and "append_to" not in step:
        warnings.append(
            f"LLM step '{step.get('name', 'unnamed')}' generates content but doesn't store it"
        )

    return warnings


def validate_step_prompt_contract(step, prompt_file, step_name):
    """Validate that a step's inputs match its prompt contract"""
    errors = []

    # Try to find the prompt file in common locations
    prompt_path = None
    for possible_path in [
        f"prompts/{prompt_file}",
        f"prompts/storyflow/{prompt_file}",
        prompt_file,
    ]:
        if Path(possible_path).exists():
            prompt_path = possible_path
            break

    if not prompt_path:
        errors.append(f"❌ Step '{step_name}': Prompt file not found: {prompt_file}")
        return errors

    # Parse the prompt header
    header = parse_prompt_header(prompt_path)
    if not header:
        errors.append(
            f"❌ Step '{step_name}': Missing or invalid YAML header in {prompt_path}"
        )
        return errors

    # Get required inputs from prompt
    required_inputs = set(header.get("requires", []))
    optional_inputs = set(header.get("optional", []))

    # Get inputs provided by the step
    step_inputs = set(step.get("prompt", {}).get("inputs", {}).keys())

    # Check for missing required inputs
    missing_required = required_inputs - step_inputs
    if missing_required:
        for missing in missing_required:
            errors.append(
                f"❌ Step '{step_name}': Missing required input '{missing}' for prompt '{prompt_file}'"
            )

    # Check for unexpected inputs (not required or optional)
    all_valid_inputs = required_inputs | optional_inputs
    unexpected_inputs = step_inputs - all_valid_inputs
    if unexpected_inputs:
        for unexpected in unexpected_inputs:
            errors.append(
                f"⚠️  Step '{step_name}': Unexpected input '{unexpected}' for prompt '{prompt_file}' (not in requires or optional)"
            )

    return errors
