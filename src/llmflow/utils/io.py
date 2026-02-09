import json
import re
import unicodedata
from pathlib import Path

import markdown

from llmflow.modules.logger import Logger
from llmflow.plugins.echo import echo

# Use unified logger
logger = Logger()

# --- Basic utilities ---


def normalize_nfc(text):
    """Normalize text to NFC (Canonical Decomposition, followed by Canonical Composition)"""
    return unicodedata.normalize("NFC", text)


def write_nfc(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(normalize_nfc(content))


def sanitize_filename(text):
    if not isinstance(text, str):
        return "unnamed"
    return re.sub(r"[^\w]+", "_", text.strip())


def read_text(path):
    """
    Read text content from a file and return it as a string.
    Handles Unicode normalization for consistency.

    Args:
        path (str): Path to the text file to read

    Returns:
        str: The content of the file as a normalized string

    Raises:
        FileNotFoundError: If the file doesn't exist
        UnicodeDecodeError: If the file can't be decoded as UTF-8
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return normalize_nfc(content)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(f"Could not decode file as UTF-8: {path}") from e


# --- Template rendering ---


def eval_template_expr(expr, variables):
    """Safely evaluate dot notation and subscript expressions using variables dict."""
    variables = to_attrdict(variables)  # Convert to AttrDict for dot notation support
    try:
        return str(eval(expr, {"__builtins__": {}}, variables))
    except Exception:
        return f"{{{{{expr}}}}}"  # Leave as-is if evaluation fails


def render_template(template_content, variables):
    """Enhanced template rendering supporting dot notation and subscripts."""
    variables = to_attrdict(variables)  # <--- Add this line

    def replacer(match):
        expr = match.group(1).strip()
        return eval_template_expr(expr, variables)

    # Replace all {{ ... }} patterns
    return re.sub(r"\{\{\s*([^\}]+?)\s*\}\}", replacer, template_content)


def render_markdown_template(template_path, variables, context=None):
    """
    Render a markdown template with variable substitution.
    Supports both {{variable}} and ${variable} syntax.
    """
    logger.debug(f"📄 Rendering template: {template_path}")
    logger.debug(f"Template variables: {list(variables.keys())}")

    try:
        template_content = Path(template_path).read_text(encoding="utf-8")

        # First pass: {{variable}} syntax
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in template_content:
                template_content = template_content.replace(placeholder, str(value))
                logger.debug(f"Replaced {{{{ {key} }}}} with value")

        # Second pass: ${variable} syntax with context resolution if available
        if context:
            from llmflow.runner import resolve

            # Find all ${...} patterns
            dollar_pattern = r"\$\{([^}]+)\}"
            matches = re.findall(dollar_pattern, template_content)

            for match in matches:
                try:
                    resolved_value = resolve(f"${{{match}}}", context)
                    if resolved_value != f"${{{match}}}":  # If it was actually resolved
                        template_content = template_content.replace(
                            f"${{{match}}}", str(resolved_value)
                        )
                        logger.debug(f"Resolved ${{ {match} }} from context")
                except Exception as e:
                    logger.warning(f"Could not resolve ${{ {match} }}: {e}")

        logger.debug("✅ Template rendered successfully")
        return template_content

    except FileNotFoundError:
        logger.error(f"❌ Template file not found: {template_path}")
        raise
    except Exception as e:
        logger.error(f"❌ Error rendering template {template_path}: {e}")
        raise


def extract_template_variables(template_content):
    """Extract variables from templates that use {{variable}} or ${variable} syntax"""
    variables = set()

    # Find {{variable}} patterns
    curly_pattern = r"\{\{\s*([^}]+?)\s*\}\}"
    for match in re.finditer(curly_pattern, template_content):
        var_name = match.group(1).strip()
        if not var_name.startswith("#") and not var_name.startswith("/"):
            variables.add(var_name)

    # Find ${variable} patterns
    dollar_pattern = r"\$\{\s*([^}]+?)\s*\}"
    for match in re.finditer(dollar_pattern, template_content):
        var_name = match.group(1).strip()
        variables.add(var_name)

    return variables


def validate_template(template_path, required_variables=None):
    """
    Validate that a template file exists and contains expected variables.
    Returns (is_valid, missing_vars, extra_vars)
    """
    logger.debug(f"🔍 Validating template: {template_path}")

    try:
        if not Path(template_path).exists():
            logger.error(f"❌ Template file not found: {template_path}")
            return False, [], []

        template_content = Path(template_path).read_text(encoding="utf-8")
        template_vars = extract_template_variables(template_content)

        if required_variables is None:
            logger.debug(f"✅ Template exists and contains {len(template_vars)} variables")
            return True, [], []

        required_set = set(required_variables)
        missing_vars = required_set - template_vars
        extra_vars = template_vars - required_set

        if missing_vars:
            logger.warning(f"⚠️  Template missing required variables: {missing_vars}")
        if extra_vars:
            logger.debug(f"Template has extra variables: {extra_vars}")

        is_valid = len(missing_vars) == 0
        logger.debug(f"✅ Template validation {'passed' if is_valid else 'failed'}")

        return is_valid, list(missing_vars), list(extra_vars)

    except Exception as e:
        logger.error(f"❌ Error validating template {template_path}: {e}")
        return False, [], []


def validate_all_templates(pipeline_config):
    """
    Validate all templates referenced in a pipeline configuration.
    Raises an exception if any templates are invalid.
    """
    logger.info("🔍 Validating all pipeline templates...")

    errors = []
    template_count = 0

    def check_step_templates(steps):
        nonlocal template_count, errors

        for step in steps:
            step_name = step.get("name", "unnamed")

            # Check for template_path in function step inputs
            if step.get("type") == "function":
                inputs = step.get("inputs", {})

                # Handle both dict and list inputs
                if isinstance(inputs, dict):
                    template_path = inputs.get("template_path")
                elif isinstance(inputs, list):
                    # For list inputs, skip template path checking
                    template_path = None
                else:
                    template_path = None

                if template_path:
                    logger.debug(
                        f"Checking template for step '{step_name}': {template_path}"
                    )
                    template_count += 1

                    is_valid, missing_vars, extra_vars = validate_template(
                        template_path
                    )
                    if not is_valid:
                        errors.append(
                            f"Step '{step_name}': Invalid template {template_path}"
                        )

                    # Check if step provides required variables
                    template_vars = inputs.get("variables", {})
                    if isinstance(template_vars, dict) and missing_vars:
                        provided_vars = set(template_vars.keys())
                        still_missing = set(missing_vars) - provided_vars
                        if still_missing:
                            errors.append(
                                f"Step '{step_name}': Template {template_path} "
                                f"missing variables: {still_missing}"
                            )

            # Check for templates in LLM step output formatting
            if step.get("type") == "llm":
                template_path = step.get("template") or step.get("format_with")
                if template_path:
                    logger.debug(
                        f"Checking output template for step '{step_name}': {template_path}"
                    )
                    template_count += 1

                    is_valid, missing_vars, extra_vars = validate_template(
                        template_path
                    )
                    if not is_valid:
                        errors.append(
                            f"Step '{step_name}': Invalid output template {template_path}"
                        )

            # Recursively check nested steps (for-each, etc.)
            if step.get("type") == "for-each":
                nested_steps = step.get("steps", [])
                check_step_templates(nested_steps)

    # Start validation
    steps = pipeline_config.get("steps", [])
    check_step_templates(steps)

    # Report results
    if errors:
        logger.error(f"❌ Template validation failed with {len(errors)} errors:")
        for error in errors:
            logger.error(f"  {error}")
        raise ValueError(f"Template validation failed: {len(errors)} errors found")
    else:
        logger.info(f"✅ All {template_count} templates validated successfully")


def save_markdown_as(text, passage, format="md", output_dir="outputs"):
    """
    Save text content as a file with custom naming and directory.
    Supports both markdown and HTML output.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    safe_passage = sanitize_filename(passage)

    if format == "md":
        path = Path(output_dir) / f"{safe_passage}.md"
        write_nfc(path, text)
        return str(path)
    elif format == "html":
        html_text = markdown.markdown(text, output_format="xhtml")
        path = Path(output_dir) / f"{safe_passage}.html"
        write_nfc(path, html_text)
        return str(path)
    else:
        raise ValueError(f"Unsupported format: {format}")


def save_xml(xml_string, basename, output_dir="outputs/xml"):
    """Save an XML string to a file, using a sanitized version of the entry_id."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(basename)
    path = Path(output_dir) / f"{safe_name}.xml"

    write_nfc(path, xml_string.strip())
    return str(path)


def save_text(content, output_path, format="md"):
    """Save text content to a file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    write_nfc(output_path, content)
    return str(output_path)


def load_json(file_path):
    """Load JSON content from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(content, output_path):
    """Save JSON content to a file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    return str(output_path)


def extract_pipeline_variables(pipeline):
    """Extract all variables that will be available in context"""
    available = set()

    # Add variables from variables section
    if "variables" in pipeline:
        available.update(pipeline["variables"].keys())

    # Add outputs from all steps
    for step in pipeline.get("steps", []):
        if "outputs" in step:
            available.update(step["outputs"])

    # Add special variables that are always available
    available.update(["passage", "source"])  # Add other globals as needed

    return available


def extract_interleave_fields(pipeline):
    """Extract field names from interleave operations"""
    interleave_fields = {}

    for step in pipeline.get("steps", []):
        if "inputs" in step and "variables" in step["inputs"]:
            variables = step["inputs"]["variables"]
            for var_name, var_config in variables.items():
                if isinstance(var_config, dict) and "interleave" in var_config:
                    interleave_fields[var_name] = list(var_config["interleave"].keys())

    return interleave_fields


def extract_pipeline_variables_at_step(pipeline, target_step_name):
    """Extract variables available when a specific step runs"""
    available = set()

    # Add global variables
    if "variables" in pipeline:
        available.update(pipeline["variables"].keys())

    # Add outputs from steps that run BEFORE the target step
    for step in pipeline.get("steps", []):
        if step.get("name") == target_step_name:
            break  # Stop when we reach the target step

        if "outputs" in step:
            available.update(step["outputs"])

    return available


def validate_template_structure(template_path, pipeline, step_name):
    """Check template against variables available when that step runs"""
    template_vars = extract_template_variables(template_path)
    available_vars = extract_pipeline_variables_at_step(pipeline, step_name)

    # Also check the specific inputs to this template step
    for step in pipeline.get("steps", []):
        if step.get("name") == step_name and "inputs" in step:
            if "variables" in step["inputs"]:
                # Template gets these specific variables
                step_vars = set(step["inputs"]["variables"].keys())
                missing = template_vars - step_vars
                return {
                    "valid": len(missing) == 0,
                    "missing_vars": missing,
                    "unused_vars": step_vars - template_vars,
                    "interleave_issues": [],  # ✅ Add this
                }

    missing = template_vars - available_vars
    return {
        "valid": len(missing) == 0,
        "missing_vars": missing,
        "unused_vars": available_vars - template_vars,
        "interleave_issues": [],  # ✅ Add this
    }

class AttrDict(dict):
    """A dict that supports attribute access (dot notation)."""

    def __getattr__(self, item):
        value = self.get(item)
        if isinstance(value, dict):
            return AttrDict(value)
        return value

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def to_attrdict(obj):
    """Recursively convert dicts in obj to AttrDict."""
    if isinstance(obj, dict):
        return AttrDict({k: to_attrdict(v) for k, v in obj.items()})
    elif isinstance(obj, list):
        return [to_attrdict(i) for i in obj]
    return obj
