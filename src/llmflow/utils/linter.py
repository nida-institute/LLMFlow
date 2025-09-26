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
    import logging
    logger = logging.getLogger('llmflow.linter')

    all_steps = []

    # Handle both list of steps and individual step
    if isinstance(items, list):
        logger.debug(f"collect_all_steps: Processing list with {len(items)} items")
        for i, step in enumerate(items):
            logger.debug(f"  Item {i}: {step.get('name', 'unnamed')} (type: {step.get('type', 'unknown')})")
            all_steps.extend(collect_all_steps(step))
    elif isinstance(items, dict):
        step_name = items.get('name', 'unnamed')
        step_type = items.get('type', 'unknown')
        logger.debug(f"collect_all_steps: Processing step '{step_name}' (type: {step_type})")

        all_steps.append(items)

        # Check for nested steps in for-each
        if items.get("type") == "for-each" and "steps" in items:
            nested_steps = items["steps"]
            logger.debug(f"  Found for-each with {len(nested_steps)} nested steps")
            all_steps.extend(collect_all_steps(nested_steps))
        else:
            logger.debug(f"  No nested steps found")

    logger.debug(f"collect_all_steps: Returning {len(all_steps)} total steps")
    return all_steps

def lint_pipeline_contracts(pipeline_path):
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    pipeline_config = pipeline.get("pipeline", pipeline)  # Handle both formats
    steps = pipeline_config.get("steps", [])
    variables = set(pipeline_config.get("variables", {}).keys())
    prompts_dir = pipeline_config.get("variables", {}).get("prompts_dir", "prompts")

    linter_config = pipeline_config.get("linter_config", {})
    if not linter_config.get("enabled", True):
        return

    # Configure logging
    logger = configure_linter_logging(linter_config)
    logger.info(f"Starting contract lint for: {pipeline_path}")

    treat_warnings_as_errors = linter_config.get("treat_warnings_as_errors", False)

    errors = []
    warnings = []

    valid_formats = {"json", "markdown", "html", "text", "yaml", "xml"}  # Add more as needed

    # Use all steps, including nested
    all_steps = collect_all_steps(steps)

    for step in all_steps:
        step_name = step.get("name", "[unnamed step]")

        # Check for append_to without outputs
        if 'append_to' in step:
            outputs = step.get('outputs')
            if not outputs or (isinstance(outputs, list) and len(outputs) == 0):
                errors.append(
                    f"❌ Step '{step_name}' uses 'append_to: {step['append_to']}' "
                    f"but has no valid 'outputs' field - the result will not be captured!"
                )

        # Continue with existing LLM validation...
        if step.get("type") != "llm":
            continue

        file = step.get("prompt", {}).get("file")
        if not file:
            continue

        prompt_path = Path(prompts_dir) / file
        if not prompt_path.exists():
            errors.append(f"❌ Prompt file not found: {prompt_path}")
            continue

        # Try to parse the prompt header
        text = Path(prompt_path).read_text(encoding="utf-8")
        match = re.search(r"<!--(.*?)-->", text, re.DOTALL)
        header_yaml = match.group(1).strip() if match else None
        header = None
        if header_yaml:
            try:
                header = yaml.safe_load(header_yaml).get("prompt", {})
            except Exception:
                header = None

        if not header:
            # Build a suggested header based on the pipeline
            pipeline_inputs = step.get("prompt", {}).get("inputs", {})
            required_inputs = sorted(pipeline_inputs.keys())
            suggested_header = yaml.dump({
                "prompt": {
                    "requires": required_inputs,
                    "optional": [],
                    "format": "Markdown",
                    "description": "TODO: Describe what this prompt does."
                }
            }, sort_keys=False)
            inputs_yaml = yaml.dump(pipeline_inputs, sort_keys=False)
            errors.append(
                f"❌ Missing or unreadable YAML @prompt header in {prompt_path}\n\n"
                f"🔢 Pipeline Step Inputs:\n{inputs_yaml}\n\n"
                f"📄 Found header in prompt file:\n{header_yaml[:500] if header_yaml else '[No header found]'}\n\n"
                f"✅ Suggested YAML header:\n{suggested_header}"
            )
            continue

        passed_inputs = set(step.get("prompt", {}).get("inputs", {}).keys())
        visible_vars = variables.union(passed_inputs)
        declared = set(header.get("requires", []))

        for req in declared:
            if req not in visible_vars:
                errors.append(f"❌ Step '{step_name}' is missing required input '{req}' for prompt '{file}'")

        diff_block = format_diff_box(step_name, file, declared, passed_inputs)
        if diff_block:
            warnings.append(diff_block)

        format = header.get("format", "markdown").lower()  # Add .lower() here
        allowed_formats = ["json", "yaml", "markdown", "xml", "text", "html"]
        if format not in allowed_formats:
            errors.append(f"❌ Invalid format '{contract.get('format', 'markdown')}' in prompt '{prompt_file}'. Allowed: {', '.join(allowed_formats)}")

        pipeline_output_type = step.get("output_type", "").lower()
        header_output_type = header.get("output_type", "").lower()

        if pipeline_output_type and header_output_type and pipeline_output_type != header_output_type:
            warnings.append(f"⚠️  Output type mismatch in '{step_name}': pipeline declares '{pipeline_output_type}', prompt declares '{header_output_type}'")

    for msg in warnings:
        click.secho(msg, fg="yellow")

    if errors or (treat_warnings_as_errors and warnings):
        for msg in errors:
            click.secho(msg, fg="red")
        raise SystemExit("❌ Prompt contract validation failed. See above for details.")

def extract_template_variables(template_content):
    """Extract all variables used in a Jinja2 template using AST parsing"""
    env = Environment()
    ast = env.parse(template_content)

    # Get all undeclared variables (variables that need to be provided)
    undeclared_variables = meta.find_undeclared_variables(ast)

    return undeclared_variables

def validate_template_step(step, errors, warnings):
    """Validate a template rendering step (only checks for file existence)"""
    if step.get("type") != "function":
        return

    inputs = step.get("inputs", {})
    template_path = inputs.get("template_path")

    # Only validate if template_path is present
    if not template_path:
        return  # <-- Do not add an error, just skip

    if not Path(template_path).exists():
        errors.append(f"Step '{step['name']}': Template file not found: {template_path}")
        return

    try:
        Path(template_path).read_text()
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
    pipeline_config = pipeline.get("pipeline", pipeline)  # Handle both formats

    # Configure linter logging
    linter_config = pipeline_config.get("linter_config", {})
    logger = configure_linter_logging(linter_config)
    logger.info(f"Starting full pipeline lint for: {pipeline_path}")

    def log_and_screen(msg, color="white", level="info"):
        click.secho(msg, fg=color)
        if pipeline_logger:
            getattr(pipeline_logger.logger, level)(msg)

    log_and_screen("🔍 Validating pipeline structure...", color="cyan")
    structure_errors = validate_pipeline_structure(pipeline_config)
    if structure_errors:
        for error in structure_errors:
            log_and_screen(error, color="red", level="error")
        raise SystemExit("❌ Pipeline structure validation failed. See above for details.")
    log_and_screen("✅ Pipeline structure is valid", color="green")

    # 2. Prompt contract validation
    lint_pipeline_contracts(pipeline_path)

    # 3. Template validation
    errors = []
    warnings = []
    steps = pipeline_config.get("steps", [])
    all_steps = collect_all_steps(steps)
    for step in all_steps:
        validate_template_step(step, errors, warnings)

    for warning in warnings:
        log_and_screen(warning, color="yellow", level="warning")
    if errors:
        for error in errors:
            log_and_screen(error, color="red", level="error")
        raise SystemExit("❌ Template validation failed. See above for details.")
    if warnings or errors:
        click.secho("✅ Template validation completed", fg="green")

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
