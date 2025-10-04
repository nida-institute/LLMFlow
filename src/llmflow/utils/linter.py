from pathlib import Path
import yaml
import click
import re
from difflib import unified_diff
import jsonschema

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

def lint_pipeline_contracts(pipeline_path):
    """Validate that all pipeline steps match their prompt contracts"""
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    pipeline_root = pipeline.get("pipeline", pipeline)

    # Use the recursive collector to get ALL steps including for-each nested ones
    all_steps = collect_all_steps(pipeline_root.get("steps", []))

    errors = []
    validated_count = 0

    # Now validate ALL steps (including nested ones)
    for step in all_steps:
        step_name = step.get("name", "unnamed")

        if step.get("type") == "llm":
            prompt_config = step.get("prompt", {})
            prompt_file = prompt_config.get("file")

            if prompt_file:
                # Show what we're validating
                click.secho(f"🔍 Validating step '{step_name}' contract: {prompt_file}", fg="cyan")

                # Validate this step's prompt contract
                step_errors = validate_step_prompt_contract(step, prompt_file, step_name)

                if step_errors:
                    errors.extend(step_errors)
                    click.secho(f"❌ Step '{step_name}' contract validation failed", fg="red")
                else:
                    click.secho(f"✅ Step '{step_name}' contract valid", fg="green")
                    validated_count += 1

    # Report final results
    if errors:
        click.secho(f"\n❌ Contract validation failed with {len(errors)} errors:", fg="red")
        for error in errors:
            click.secho(f"  {error}", fg="red")
        raise ValueError("Pipeline contract validation failed")
    else:
        click.secho(f"\n✅ All {validated_count} step contracts valid", fg="green")

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
        errors.append(f"Step '{step['name']}': Template file not found: {template_path}")
        return

    try:
        # Read template and extract {variable} patterns
        template_content = Path(template_path).read_text()
        template_vars = extract_template_variables(template_content)

        # Get variables provided to the template
        provided_vars = set()
        template_inputs = inputs.get("variables", {})
        if isinstance(template_inputs, dict):
            provided_vars = set(template_inputs.keys())

        # Check for missing variables
        missing_vars = template_vars - provided_vars
        if missing_vars:
            for var in missing_vars:
                warnings.append(f"Template '{template_path}' uses variable '{var}' but step '{step['name']}' doesn't provide it")

    except Exception as e:
        errors.append(f"Step '{step['name']}': Error reading template {template_path}: {e}")

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

def lint_pipeline_full(pipeline_path, pipeline_logger=None):
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    pipeline_config = pipeline.get("pipeline", pipeline)

    # Configure linter logging
    linter_config = pipeline_config.get("linter_config", {})
    logger = configure_linter_logging(linter_config)
    logger.info(f"Starting full pipeline lint for: {pipeline_path}")

    def log_and_screen(msg, color="white", level="info"):
        click.secho(msg, fg=color)
        if pipeline_logger:
            getattr(pipeline_logger.logger, level)(msg)

    # 1. Structure validation
    log_and_screen("🔍 Validating pipeline structure...", color="cyan")
    structure_errors = validate_pipeline_structure(pipeline_config)
    if structure_errors:
        for error in structure_errors:
            log_and_screen(error, color="red", level="error")
        raise SystemExit("❌ Pipeline structure validation failed.")
    log_and_screen("✅ Pipeline structure is valid", color="green")

    # 2. Contract validation - CALL DIRECTLY, don't duplicate
    errors = []
    validated_count = 0
    all_steps = collect_all_steps(pipeline_config.get("steps", []))

    for step in all_steps:
        step_name = step.get("name", "unnamed")
        if step.get("type") == "llm":
            prompt_config = step.get("prompt", {})
            prompt_file = prompt_config.get("file")
            if prompt_file:
                log_and_screen(f"🔍 Validating step '{step_name}' contract: {prompt_file}", color="cyan")
                step_errors = validate_step_prompt_contract(step, prompt_file, step_name)
                if step_errors:
                    errors.extend(step_errors)
                    log_and_screen(f"❌ Step '{step_name}' contract validation failed", color="red")
                else:
                    log_and_screen(f"✅ Step '{step_name}' contract valid", color="green")
                    validated_count += 1

    if errors:
        for error in errors:
            log_and_screen(error, color="red", level="error")
        raise SystemExit("❌ Contract validation failed.")
    else:
        log_and_screen(f"✅ All {validated_count} step contracts valid", color="green")

    # 3. Template validation
    template_errors = []
    template_warnings = []
    for step in all_steps:
        validate_template_step(step, template_errors, template_warnings)

    for warning in template_warnings:
        log_and_screen(warning, color="yellow", level="warning")
    if template_errors:
        for error in template_errors:
            log_and_screen(error, color="red", level="error")
        raise SystemExit("❌ Template validation failed.")

    if template_warnings:
        log_and_screen("✅ Template validation completed", color="green")

def configure_linter_logging(linter_config):
    """Configure logging level for the linter based on pipeline config"""
    import logging
    logger = logging.getLogger('llmflow.linter')

    # Get log level from config, default to INFO
    log_level = linter_config.get('log_level', 'info').upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Set the logger level
    logger.setLevel(numeric_level)

    # Check if handler already exists to avoid duplicates
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(numeric_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        # Update existing handler's level
        for handler in logger.handlers:
            handler.setLevel(numeric_level)

    return logger

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
