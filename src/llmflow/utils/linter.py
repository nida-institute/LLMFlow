from dataclasses import dataclass
from typing import List, Set
import re
from difflib import unified_diff
from pathlib import Path

import click
import yaml
from pydantic import ValidationError
from llmflow.pipeline_schema import PipelineConfig, PIPELINE_SCHEMA
from llmflow.utils.llm_runner import validate_model_parameter, get_model_family


def extract_variable_references(text: str) -> Set[str]:
    """Extract all variable references from a string (${var} or {{var}} syntax)"""
    variables = set()

    # Extract ${...} patterns
    for match in re.finditer(r'\$\{([^\}]+)\}', text):
        var = match.group(1).strip()
        # Extract root variable (before . or [)
        root = re.split(r'[.\[]', var)[0]
        variables.add(root)

    # Extract {{...}} patterns
    for match in re.finditer(r'\{\{([^\}]+)\}\}', text):
        var = match.group(1).strip()
        # Extract root variable (before . or [)
        root = re.split(r'[.\[]', var)[0]
        variables.add(root)

    return variables

def _allowed_step_keys_from_schema() -> set:
    props = (
        PIPELINE_SCHEMA.get("properties", {})
        .get("steps", {})
        .get("items", {})
        .get("properties", {})
    )
    return set(props.keys())


# Keep schema-driven keys authoritative so new keywords (like "retry") are picked up
# automatically, then union the plugin-specific extras that live outside the schema.
_SCHEMA_STEP_KEYS = _allowed_step_keys_from_schema()
_EXTRA_STEP_KEYS = {
    "description",
    "output",
    "after",
    "format",
    "log",
    "max_tokens",
    "output_type",
    "plugin",
    "response_format",
    "temperature",
    "timeout_seconds",
    "mcp",
    "llm_options",
    "tools",
    "path",
    "xpath",
    "namespaces",
    "output_format",
    "stylesheet_path",
    "xml_string",
    "group_by_prefix",
    "limit",
    "variables",
}

ALLOWED_STEP_KEYS = _SCHEMA_STEP_KEYS | _EXTRA_STEP_KEYS
COMMON_TYPOS = {
    "saveaas": "saveas",
    "ouput": "outputs",
    "ouptuts": "outputs",
    "intputs": "inputs",
    "inputss": "inputs",
    "apend_to": "append_to",
}

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
    """Parse header from a .gpt prompt file (supports both YAML frontmatter and HTML comments)"""
    text = Path(prompt_path).read_text(encoding="utf-8")

    # Try YAML frontmatter first (--- ... ---)
    yaml_match = re.search(r"^---\s*\n(.*?)\n---\s*$", text, re.DOTALL | re.MULTILINE)
    if yaml_match:
        block = yaml_match.group(1).strip()
        try:
            data = yaml.safe_load(block)
            # Unwrap 'prompt' key if present (same as HTML comment format)
            return data.get("prompt", data)
        except Exception as e:
            logger.error(f"Failed to parse YAML frontmatter in {prompt_path}: {e}")
            return None

    # Fallback: Try HTML comment style (<!-- ... -->)
    html_match = re.search(r"<!--(.*?)-->", text, re.DOTALL)
    if html_match:
        block = html_match.group(1).strip()
        try:
            data = yaml.safe_load(block)
            # Old format may wrap in 'prompt' key
            return data.get("prompt", data)
        except Exception as e:
            logger.error(f"Failed to parse HTML comment header in {prompt_path}: {e}")
            return None

    # No header found
    logger.error(f"No valid header found in {prompt_path} (tried both --- and <!-- formats)")
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
                f"{prompts_dir}/{prompt_file}",
                f"prompts/{prompt_file}",
                prompt_file,
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
                prompt_data = parse_prompt_header(prompt_path)

                if not prompt_data:
                    errors.append(
                        f"❌ Step '{step_name}': Invalid prompt header in {prompt_path}"
                    )
                    continue

                # NEW: Handle both old and new header formats
                # Old format: { prompt: { requires: [...], optional: [...] } }
                # New format: { inputs: {...}, outputs: {...} }

                step_inputs = prompt_config.get("inputs", {})

                # Check if using new format (inputs/outputs) or old format (requires/optional)
                if "inputs" in prompt_data:
                    # New format: all keys in 'inputs' are required by default
                    required_inputs = list(prompt_data.get("inputs", {}).keys())
                else:
                    # Old format: explicit 'requires' list
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


def _collect_declared_outputs(all_steps):
    declared = set()
    for step in all_steps:
        outs = step.get("outputs")
        if isinstance(outs, dict):
            declared.update(outs.keys())
        elif isinstance(outs, list):
            declared.update(outs)
        elif isinstance(outs, str):
            declared.add(outs)
    return declared


def _validate_template_var_provenance(all_steps, errors):
    declared = _collect_declared_outputs(all_steps)
    for step in all_steps:
        if step.get("function") != "llmflow.utils.io.render_markdown_template":
            continue
        vars_map = step.get("inputs", {}).get("variables", {})
        if not isinstance(vars_map, dict):
            continue
        for k, v in vars_map.items():
            s = (v or "").strip()
            if s.startswith("${") and s.endswith("}"):
                ref = s[2:-1]
                if ref not in declared:
                    errors.append(
                        f"❌ Template var '{k}' references '{v}' but no prior step declared '{ref}' in outputs"
                    )


def _extract_all_variables_from_value(value, path=""):
    """Recursively extract all variable references from any value (string, dict, list)"""
    variables = set()

    if isinstance(value, str):
        variables.update(extract_variable_references(value))
    elif isinstance(value, dict):
        for k, v in value.items():
            variables.update(_extract_all_variables_from_value(v, f"{path}.{k}" if path else k))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            variables.update(_extract_all_variables_from_value(item, f"{path}[{i}]"))

    return variables


def _build_available_context(pipeline_vars, declared_outputs, item_var=None, for_each_var=None):
    """Build set of variables available at a given step"""
    available = set()

    # Pipeline-level variables
    if pipeline_vars:
        available.update(pipeline_vars.keys())

    # Outputs from previous steps
    available.update(declared_outputs)

    # For-each context
    if item_var:
        available.add(item_var)
    if for_each_var:
        available.add(for_each_var)

    return available


def _validate_variable_references_recursive(steps, pipeline_vars, parent_outputs, errors, parent_item_vars=None):
    """Recursively validate variable references with proper scoping for nested steps

    Args:
        steps: List of steps to validate
        pipeline_vars: Pipeline-level variables
        parent_outputs: Set of outputs declared by parent/previous steps (mutable, shared across recursion)
        errors: List to append error messages to
        parent_item_vars: Set of item_var names from parent for-each loops
    """
    if parent_item_vars is None:
        parent_item_vars = set()

    # Use parent_outputs directly (don't copy) so nested steps can add outputs visible to parent
    declared_outputs = parent_outputs

    for step in steps:
        step_name = step.get("name", "unnamed")
        step_type = step.get("type", "")

        # Build available context for this step
        item_var = step.get("item_var")
        for_each_input = step.get("input")  # for-each uses "input" not "for-each"

        # Combine parent item_vars with current item_var
        current_item_vars = parent_item_vars.copy()
        if item_var:
            current_item_vars.add(item_var)

        available = _build_available_context(
            pipeline_vars,
            declared_outputs,
            None,  # Don't pass item_var here
            for_each_input
        )
        # Add all parent and current item_vars
        available.update(current_item_vars)

        # Extract all variable references from step configuration
        # Check: inputs, outputs, condition, saveas, format, input (for-each)
        # NOTE: append_to is NOT checked - it declares a new variable, doesn't reference one
        fields_to_check = ["inputs", "condition", "saveas", "format", "input"]

        for field in fields_to_check:
            if field in step:
                field_value = step[field]
                referenced_vars = _extract_all_variables_from_value(field_value)

                # Check each referenced variable
                for var in referenced_vars:
                    # Extract root variable (before . or [)
                    root_var = re.split(r'[.\[]', var)[0]

                    if root_var not in available:
                        # Show helpful error message with available variables
                        available_list = sorted(available)
                        errors.append(
                            f"❌ Step '{step_name}' field '{field}': Variable '${{{var}}}' not available. "
                            f"Available: {available_list if available_list else '(none)'}"
                        )

        # Handle nested steps (for-each loops)
        if "steps" in step and isinstance(step["steps"], list):
            # Recursively validate nested steps with current context plus item_var
            _validate_variable_references_recursive(
                step["steps"],
                pipeline_vars,
                declared_outputs,
                errors,
                current_item_vars
            )

        # After processing step (including nested steps), add its outputs to declared_outputs
        outs = step.get("outputs")
        if isinstance(outs, dict):
            declared_outputs.update(outs.keys())
        elif isinstance(outs, list):
            declared_outputs.update(outs)
        elif isinstance(outs, str):
            declared_outputs.add(outs)

        # Handle append_to - these create implicit lists
        append_to = step.get("append_to")
        if append_to:
            declared_outputs.add(append_to)


def _validate_all_variable_references(all_steps, pipeline_vars, errors):
    """Validate that all variable references in step configurations can be resolved

    This is the top-level entry point that starts recursive validation.
    """
    _validate_variable_references_recursive(all_steps, pipeline_vars, set(), errors)


def validate_model_parameters(all_steps, pipeline_config):
    """Validate that LLM parameters are compatible with the model being used.

    Checks parameters from all sources:
    - Pipeline-level llm_config
    - Step-level llm_options
    - Step-level direct parameters

    Returns list of error messages.
    """
    errors = []
    llm_config = pipeline_config.get("llm_config", {})

    # Parameters that can be specified and should be validated
    VALIDATED_PARAMS = {
        "max_tokens",
        "max_completion_tokens",
        "temperature",
        "top_p",
        "top_k",
        "frequency_penalty",
        "presence_penalty",
    }

    for step in all_steps:
        if step.get("type") != "llm":
            continue

        step_name = step.get("name", "unnamed")

        # Build merged config following same logic as runner.py
        step_options = step.get("llm_options", {})

        # Determine the model for this step
        model = step.get("model") or llm_config.get("model") or "gpt-4o"

        # Collect all parameters from all sources
        all_params = {}

        # 1. Pipeline-level defaults
        for param in VALIDATED_PARAMS:
            if param in llm_config:
                all_params[param] = ("pipeline.llm_config", llm_config[param])

        # 2. Step-level llm_options (override pipeline defaults)
        for param in VALIDATED_PARAMS:
            if param in step_options:
                all_params[param] = (f"step '{step_name}' llm_options", step_options[param])

        # 3. Step-level direct parameters (override everything)
        for param in VALIDATED_PARAMS:
            if param in step:
                all_params[param] = (f"step '{step_name}'", step[param])

        # Validate each parameter against the model
        for param, (source, value) in all_params.items():
            param_errors = validate_model_parameter(model, param, value)
            if param_errors:
                # Add context about where the invalid parameter came from
                for error in param_errors:
                    errors.append(f"❌ In {source}: {error}")

    return errors


def lint_pipeline_full(pipeline_path):
    """Lint pipeline and return result object instead of raising SystemExit"""
    all_errors = []
    all_warnings = []

    # Load pipeline first
    try:
        pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    except FileNotFoundError:
        # Re-raise to let cli.py handle with better error message
        raise

    pipeline_config = pipeline.get("pipeline", pipeline)

    # ✅ CHECK IF LINTER IS DISABLED
    linter_config = pipeline_config.get("linter_config", {})
    if not linter_config.get("enabled", True):
        logger.info("ℹ️  Linter disabled by configuration, skipping validation")
        return LintResult(valid=True, errors=[], warnings=[])

    logger.info(f"Starting full pipeline lint for: {pipeline_path}")

    # 1) Structure validation
    logger.info("🔍 Validating pipeline structure...")
    structure_errors = validate_pipeline_structure(pipeline_config)
    if structure_errors:
        all_errors.extend(structure_errors)
        for error in structure_errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ Pipeline structure is valid")

    # 1.5) Step keyword validation
    logger.info("🔍 Validating step keywords...")
    all_steps = collect_all_steps(pipeline_config.get("steps", []))
    keyword_errors = lint_pipeline_steps(all_steps)
    if keyword_errors:
        all_errors.extend(keyword_errors)
        for error in keyword_errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ All step keywords are valid")

    # 1.6) Model-parameter compatibility validation
    logger.info("🔍 Validating model-parameter compatibility...")
    parameter_errors = validate_model_parameters(all_steps, pipeline_config)
    if parameter_errors:
        all_errors.extend(parameter_errors)
        for error in parameter_errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ All model parameters are compatible")

    # 2) Prompt contract validation
    errors, validated_count = validate_all_step_contracts(all_steps, log_and_screen, pipeline_config)
    if errors:
        all_errors.extend(errors)
        for error in errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    else:
        logger.info(f"✅ All {validated_count} step contracts valid")

    # 2.5) Variable reference validation (NEW: ensure all variable references can be resolved)
    logger.info("🔍 Validating variable references...")
    variable_errors = []
    pipeline_vars = pipeline_config.get("variables", {})
    # Use pipeline_config.get("steps", []) instead of all_steps to preserve hierarchy
    _validate_all_variable_references(pipeline_config.get("steps", []), pipeline_vars, variable_errors)

    if variable_errors:
        all_errors.extend(variable_errors)
        logger.error(f"\n❌ Variable validation failed with {len(variable_errors)} errors:")
        for error in variable_errors:
            logger.error(f"  {error}")
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    else:
        logger.info("✅ All variable references can be resolved")

    # 3) Template variables validation (NEW: ensure templates and variables match)
    logger.info("🔍 Validating template variables...")
    template_errors = []
    template_warnings = []

    template_steps = [step for step in all_steps if step.get("inputs", {}).get("template_path")]
    for step in template_steps:
        template_path = step.get("inputs", {}).get("template_path", "")
        logger.info(f"🔍 Validating template: {template_path} (step: {step.get('name')})")
        validate_template_step(step, template_errors, template_warnings)

    if template_errors:
        all_errors.extend(template_errors)
        logger.error(f"\n❌ Template validation failed with {len(template_errors)} errors:")
        for error in template_errors:
            logger.error(f"  {error}")
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ Template variables match pipeline-provided variables")

    if all_errors:
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)

    # Show any warnings
    all_warnings.extend(template_warnings)
    for warning in all_warnings:
        logger.warning(f"⚠️  {warning}")

    logger.info("✅ Pipeline validation completed successfully")
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

    header = parse_prompt_header(prompt_path)
    if not header:
        errors.append(f"❌ Step '{step_name}': Missing or invalid YAML header in {prompt_path}")
        return errors

    step_inputs = set(step.get("prompt", {}).get("inputs", {}).keys())

    # Support both formats
    if "inputs" in header and isinstance(header["inputs"], dict):
        required_inputs = set(header["inputs"].keys())
        optional_inputs = set()
    else:
        required_inputs = set(header.get("requires", []))
        optional_inputs = set(header.get("optional", []))

    missing_required = required_inputs - step_inputs
    if missing_required:
        for missing in sorted(missing_required):
            errors.append(f"❌ Step '{step_name}': Missing required input '{missing}' for prompt '{prompt_file}'")

    unexpected_inputs = step_inputs - (required_inputs | optional_inputs)
    if unexpected_inputs:
        for unexpected in sorted(unexpected_inputs):
            errors.append(f"⚠️  Step '{step_name}': Unexpected input '{unexpected}' for prompt '{prompt_file}' (not declared)")

    return errors


# Add to your linter (e.g. llmflow/utils/linter.py)

def _lint_conditional_rules(step, errors, key: str):
    rules = step.get(key, [])
    if rules and not isinstance(rules, list):
        errors.append(f"Step '{step.get('name','unnamed')}': '{key}' must be a list")
        return
    for r in rules or []:
        if not isinstance(r, dict):
            errors.append(f"Step '{step.get('name','unnamed')}': each '{key}' rule must be an object")
            continue
        if "if" not in r or not isinstance(r.get("if"), str) or not r.get("if").strip():
            errors.append(f"Step '{step.get('name','unnamed')}': '{key}' rule must include non-empty 'if' expression")
        for k in r.keys():
            if k not in {"if", "message"}:
                errors.append(f"Step '{step.get('name','unnamed')}': unknown '{key}' key '{k}'")

def lint_pipeline_steps(steps):
    errors = []
    for step in steps:
        step_name = step.get('name', '<unnamed>')
        for key in step.keys():
            if key not in ALLOWED_STEP_KEYS:
                suggestion = COMMON_TYPOS.get(key)
                message = f"Step '{step_name}' has unknown keyword '{key}'"
                if suggestion:
                    message += f" (Did you mean '{suggestion}'?)"
                errors.append(message)
        _lint_conditional_rules(step, errors, "require")
        _lint_conditional_rules(step, errors, "warn")
    return errors
