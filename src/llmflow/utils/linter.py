from pathlib import Path
import yaml
import click
import re
from difflib import unified_diff
from llmflow.modules.logger import Logger
import jsonschema

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
    except Exception as e:
        return None

def extract_template_variables(template_content):
    """Extract variables from templates that use {{ variable }} syntax"""
    # Find all {{ variable }} patterns, allowing spaces
    variable_pattern = r'\{\{\s*([^}]+?)\s*\}\}'
    variables = set()

    for match in re.finditer(variable_pattern, template_content):
        var_name = match.group(1).strip()
        # Skip template logic like {{#if}} or {{/endif}}
        if not var_name.startswith('#') and not var_name.startswith('/') and not var_name.startswith('%'):
            variables.add(var_name)

    return variables

def format_diff_box(step, file, declared, passed):
    declared_sorted = sorted(declared)
    passed_sorted = sorted(passed)
    diff = list(unified_diff(declared_sorted, passed_sorted, fromfile="prompt requires", tofile="pipeline inputs", lineterm=""))
    if not diff:
        return ""
    border = "─" * 76
    lines = [
        f"╭─🔍 Contract Mismatch: {file} ─{border[len(' Contract Mismatch: ─') - len(file):]}",
        f"│ Step: {step}".ljust(78) + "│",
        f"│ ❌ Inputs passed to this step do not match the prompt contract.".ljust(78) + "│",
        f"│".ljust(78) + "│",
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

def validate_all_step_contracts(all_steps, log_func):
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
                    errors.append(f"❌ Step '{step_name}': append_to: {append_to_value} requires 'outputs' to be specified")
                continue

        # Only validate contracts for LLM steps
        if step_type == "llm":
            log_func(f"🔍 Validating step '{step_name}' contract: {step.get('prompt', {}).get('file', 'NO_FILE')}")

            prompt_config = step.get("prompt", {})
            prompt_file = prompt_config.get("file")

            if not prompt_file:
                errors.append(f"❌ Step '{step_name}': No prompt file specified")
                continue

            # FIXED: Use the same multi-path resolution logic as validate_step_prompt_contract
            prompt_path = None
            possible_paths = [
                f"prompts/{prompt_file}",           # Standard prompts directory
                f"prompts/storyflow/{prompt_file}", # Storyflow specific directory
                prompt_file                         # Raw filename (fallback)
            ]

            for possible_path in possible_paths:
                if Path(possible_path).exists():
                    prompt_path = possible_path
                    break

            if not prompt_path:
                errors.append(f"❌ Step '{step_name}': Prompt file not found: {prompt_file}")
                log_func(f"❌ Step '{step_name}' contract validation failed")
                continue

            try:
                # FIXED: Just pass the path to parse_prompt_header, don't read content separately
                prompt_data = parse_prompt_header(prompt_path)

                if not prompt_data:
                    errors.append(f"❌ Step '{step_name}': Invalid prompt header in {prompt_path}")
                    continue

                # Validate step inputs match prompt requirements
                step_inputs = prompt_config.get("inputs", {})
                required_inputs = prompt_data.get("requires", [])

                missing_inputs = [inp for inp in required_inputs if inp not in step_inputs]
                if missing_inputs:
                    errors.append(f"❌ Step '{step_name}': Missing required inputs: {missing_inputs}")
                    log_func(f"❌ Step '{step_name}' contract validation failed")
                else:
                    log_func(f"✅ Step '{step_name}' contract validation passed")
                    validated_count += 1

            except Exception as e:
                errors.append(f"❌ Step '{step_name}': Error validating prompt {prompt_path}: {str(e)}")
                log_func(f"❌ Step '{step_name}' contract validation failed")

    return errors, validated_count

def lint_pipeline_contracts(pipeline_path):
    """Validate that all pipeline steps match their prompt contracts"""
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    pipeline_root = pipeline.get("pipeline", pipeline)

    all_steps = collect_all_steps(pipeline_root.get("steps", []))

    # Use the unified logger for output
    def unified_logger(msg, color="white", level="info"):
        log_and_screen(msg, color, level)

    errors, validated_count = validate_all_step_contracts(all_steps, unified_logger)

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
        errors.append(f"❌ Step '{step['name']}': Template file not found: {template_path}")
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
                errors.append(f"❌ Template '{template_path}' uses variable '{var}' but step '{step['name']}' doesn't provide it")

    except Exception as e:
        errors.append(f"❌ Step '{step['name']}': Error reading template {template_path}: {e}")

def validate_pipeline(pipeline_config):
    """Main pipeline validation function"""
    errors = []
    warnings = []

    steps = pipeline_config.get("steps", [])

    for step in steps:
        # Existing validations...

        # Add template validation
        validate_template_step(step, errors, warnings)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

pipeline_schema = {
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "variables": { "type": "object" },
    "llm_config": {
      "type": "object",
      "properties": {
        "model": { "type": "string" },
        "max_tokens": { "type": "number" },
        "temperature": { "type": "number" }
      },
      "required": ["model", "max_tokens", "temperature"]
    },
    "linter_config": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean" },
        "treat_warnings_as_errors": { "type": "boolean" }
      }
    },
    "steps": {
      "type": "array",
      "items": { "$ref": "#/definitions/step" }
    }
  },
  "required": ["name", "steps"],
  "definitions": {
    "step": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "type": { "type": "string" },
        "function": { "type": "string" },
        "inputs": { "type": "object" },
        "outputs": {
          "anyOf": [
            { "type": "string" },
            { "type": "array", "items": { "type": "string" } }
          ]
        },
        "output_type": { "type": "string" },
        "saveas": { "type": "string" },
        "append_to": { "type": "string" },
        "log": { "type": "string" },
        "prompt": {
          "type": "object",
          "properties": {
            "file": { "type": "string" },
            "inputs": { "type": "object" }
          },
          "required": ["file", "inputs"]
        },
        "input": { "type": "string" },
        "item_var": { "type": "string" },
        "steps": {
          "type": "array",
          "items": { "$ref": "#/definitions/step" }
        }
      },
      "required": ["name", "type"]
    }
  }
}

def validate_pipeline_structure(pipeline_config):
    try:
        jsonschema.validate(instance=pipeline_config, schema=pipeline_schema)
        return []
    except jsonschema.ValidationError as e:
        return [f"❌ Pipeline structure error: {e.message} (at {list(e.path)})"]

def lint_pipeline_full(pipeline_path):
    # Load pipeline first
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    pipeline_config = pipeline.get("pipeline", pipeline)

    # Print this once
    logger.info(f"Starting full pipeline lint for: {pipeline_path}")

    logger.info("🔍 Validating pipeline structure...")
    structure_errors = validate_pipeline_structure(pipeline_config)
    if structure_errors:
        for error in structure_errors:
            logger.error(error)
        raise SystemExit("❌ Pipeline structure validation failed.")
    logger.info("✅ Pipeline structure is valid")

    all_steps = collect_all_steps(pipeline_config.get("steps", []))
    errors, validated_count = validate_all_step_contracts(all_steps, log_and_screen)

    if errors:
        for error in errors:
            logger.error(error)
        raise SystemExit("❌ Contract validation failed.")
    else:
        logger.info(f"✅ All {validated_count} step contracts valid")

    # 3. Template validation - FIXED: Proper error handling
    logger.info("🔍 Validating pipeline templates...")
    template_errors = []
    template_warnings = []

    # Collect template validation steps
    template_steps = [step for step in all_steps if step.get("inputs", {}).get("template_path")]

    for step in template_steps:
        template_path = step.get("inputs", {}).get("template_path", "")
        logger.info(f"🔍 Validating template: {template_path} (step: {step.get('name')})")

        validate_template_step(step, template_errors, template_warnings)

        if not template_errors:  # If no errors for this template
            logger.info(f"✅ Template {template_path} is valid")

    # Report template validation results
    if template_errors:
        logger.error(f"\n❌ Template validation failed with {len(template_errors)} errors:")
        for error in template_errors:
            logger.error(f"  {error}")
        raise SystemExit("❌ Template validation failed.")
    else:
        logger.info("✅ All templates validated successfully")

    # Show any warnings (but don't fail)
    for warning in template_warnings:
        logger.warning(f"⚠️  {warning}")

    logger.info("✅ Pipeline validation completed successfully")

def check_step_outputs(step):
    """Warn if a step generates data but doesn't store it"""
    warnings = []

    # Check if step has append_to but no outputs
    if "append_to" in step and "outputs" not in step:
        warnings.append(f"Step '{step.get('name', 'unnamed')}' has append_to but no outputs")

    # Check if LLM step has neither outputs nor append_to
    if step.get("type") == "llm" and "outputs" not in step and "append_to" not in step:
        warnings.append(f"LLM step '{step.get('name', 'unnamed')}' generates content but doesn't store it")

    return warnings

def validate_step_prompt_contract(step, prompt_file, step_name):
    """Validate that a step's inputs match its prompt contract"""
    errors = []

    # Try to find the prompt file in common locations
    prompt_path = None
    for possible_path in [f"prompts/{prompt_file}", f"prompts/storyflow/{prompt_file}", prompt_file]:
        if Path(possible_path).exists():
            prompt_path = possible_path
            break

    if not prompt_path:
        errors.append(f"❌ Step '{step_name}': Prompt file not found: {prompt_file}")
        return errors

    # Parse the prompt header
    header = parse_prompt_header(prompt_path)
    if not header:
        errors.append(f"❌ Step '{step_name}': Missing or invalid YAML header in {prompt_path}")
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
            errors.append(f"❌ Step '{step_name}': Missing required input '{missing}' for prompt '{prompt_file}'")

    # Check for unexpected inputs (not required or optional)
    all_valid_inputs = required_inputs | optional_inputs
    unexpected_inputs = step_inputs - all_valid_inputs
    if unexpected_inputs:
        for unexpected in unexpected_inputs:
            errors.append(f"⚠️  Step '{step_name}': Unexpected input '{unexpected}' for prompt '{prompt_file}' (not in requires or optional)")

    return errors
