import json
import re
import os
import unicodedata
import logging  # ← Add this missing import
from pathlib import Path
import markdown  # You forgot this earlier!

# --- Basic utilities ---

def normalize_nfc(text):
    if isinstance(text, str):
        return unicodedata.normalize("NFC", text)
    elif isinstance(text, list):
        return [normalize_nfc(item) for item in text]
    else:
        return text

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

# --- Markdown rendering and saving ---

def render_markdown_template(template_path, variables):
    """
    Render template using only Jinja2.
    Supports interleave operations for complex data structures.
    """
    import jinja2
    from pathlib import Path

    template_content = read_text(template_path)

    # Process special operations like interleave
    processed_vars = process_interleave_operations(variables)

    # Use Jinja2 for all templates
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(Path(template_path).parent),
        trim_blocks=True,
        lstrip_blocks=True
    )

    template = env.get_template(Path(template_path).name)
    return normalize_nfc(template.render(**processed_vars))

def process_interleave_operations(variables):
    """Handle interleave operations - create arrays of objects for Jinja2."""
    processed_vars = {}
    for key, value in variables.items():
        if isinstance(value, dict) and "interleave" in value:
            step_arrays = value["interleave"]

            # Get all the arrays dynamically
            array_names = list(step_arrays.keys())
            arrays = [step_arrays[name] for name in array_names]

            # Create array of objects with dynamic field names
            scene_objects = []
            for items in zip(*arrays):
                scene_obj = {}
                for i, field_name in enumerate(array_names):
                    scene_obj[field_name] = items[i]
                scene_objects.append(scene_obj)

            processed_vars[key] = scene_objects
        else:
            processed_vars[key] = value

    return processed_vars

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

# --- XML saving ---

def save_xml(xml_string, basename, output_dir="outputs/xml"):
    """
    Save an XML string to a file, using a sanitized version of the entry_id.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(basename)
    path = Path(output_dir) / f"{safe_name}.xml"

    write_nfc(path, xml_string.strip())
    return str(path)


# --- JSON saving ---

def save_json(passage, content, output_dir="outputs/scenes"):
    """Save JSON content with debug logging"""
    logger = logging.getLogger('llmflow.io')

    logger.debug("=== DEBUG save_json ===")
    logger.debug(f"passage: {passage}")
    logger.debug(f"content type: {type(content)}")
    logger.debug(f"content value: {content}")
    logger.debug(f"output_dir: {output_dir}")

    # Create the directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate filename
    safe_passage = sanitize_filename(passage)
    output_path = Path(output_dir) / f"{safe_passage}.json"

    logger.debug(f"Writing to: {output_path}")

    # Write the content
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    logger.debug("File written successfully")
    logger.debug("=== END DEBUG save_json ===")

    return str(output_path)

# --- Existing save_leaders_guide (good enough for now) ---

def save_leaders_guide(passage, intro, scenes, step1, step2, step3, step4, summary):
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    safe_passage = sanitize_filename(passage)
    output_path = os.path.join(output_dir, f"leaders_guide_{safe_passage}.md")

    lines = [intro.strip(), ""]
    for i, scene in enumerate(scenes):
        title = scene.get("Title", f"Scene {i+1}")
        citation = scene.get("Citation", "")
        text = scene.get("Berean Standard Bible", "")
        lines.append(f"## {title} ({citation})")
        if text:
            lines.append(f"*{text}*")
        lines.append("")
        lines.append(step1[i])
        lines.append("")
        lines.append(step2[i])
        lines.append("")
        lines.append(step3[i])
        lines.append("")
        lines.append(step4[i])
        lines.append("")
    lines.append(summary.strip())
    lines.append("")

    full_markdown = "\n".join(lines)
    write_nfc(output_path, full_markdown)

    result = copy.deepcopy(structure)
    return result

def extract_template_variables(template_path):
    """Extract all variables used in a Jinja2 template"""
    import jinja2
    import re

    template_content = read_text(template_path)

    # Find all Jinja2 variables: {{ variable }}, {{ object.property }}, {{ array[index] }}
    jinja_vars = set()

    # Simple variables: {{ variable }}
    simple_vars = re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}', template_content)
    jinja_vars.update(simple_vars)

    # Object properties: {{ object.property }}
    obj_props = re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\.[a-zA-Z0-9_.]*\s*\}\}', template_content)
    jinja_vars.update(obj_props)

    # Array access: {{ array[0] }} or {{ array[loop.index0] }}
    array_vars = re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\[[^\]]*\]\s*\}\}', template_content)
    jinja_vars.update(array_vars)

    # For loops: {% for item in collection %}
    for_loops = re.findall(r'\{\%\s*for\s+\w+\s+in\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\%\}', template_content)
    jinja_vars.update(for_loops)

    # ✅ Remove Jinja2 built-ins that are automatically available
    jinja_builtins = {
        'loop',        # Available in {% for %} loops
        'scene_data',  # Loop variable from {% for scene_data in scene_steps %}
        'scene',       # Loop variable from {% for scene in scenes %}
        'item',        # Common loop variable
        'forloop',     # Alternative loop object
        'range',       # Jinja2 range function
        'super',       # Template inheritance
        'self',        # Template self-reference
        'varargs',     # Function arguments
        'kwargs'       # Keyword arguments
    }

    # Also remove any variables that are defined as loop variables in the template
    # Look for {% for variable_name in ... %} patterns
    loop_vars = re.findall(r'\{\%\s*for\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+in\s+', template_content)
    jinja_builtins.update(loop_vars)

    jinja_vars = jinja_vars - jinja_builtins

    return jinja_vars

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
                    "interleave_issues": []  # ✅ Add this
                }

    missing = template_vars - available_vars
    return {
        "valid": len(missing) == 0,
        "missing_vars": missing,
        "unused_vars": available_vars - template_vars,
        "interleave_issues": []  # ✅ Add this
    }

def validate_all_templates(pipeline):
    """Validate all templates used in the pipeline"""
    validation_results = {}

    for step in pipeline.get("steps", []):
        if step.get("type") == "function" and step.get("function") == "llmflow.utils.io.render_markdown_template":
            inputs = step.get("inputs", {})
            if "template_path" in inputs:
                template_path = inputs["template_path"]
                step_name = step.get("name", "unnamed")

                print(f"🔍 Validating template: {template_path} (step: {step_name})")

                try:
                    result = validate_template_structure(template_path, pipeline, step_name)
                    validation_results[template_path] = result

                    if result["valid"]:
                        print(f"✅ Template {template_path} is valid")
                    else:
                        print(f"❌ Template {template_path} has issues:")
                        if result["missing_vars"]:
                            print(f"   Missing variables: {result['missing_vars']}")
                        if result["interleave_issues"]:
                            for issue in result["interleave_issues"]:
                                print(f"   {issue}")

                    if result["unused_vars"]:
                        print(f"ℹ️  Unused variables: {result['unused_vars']}")

                except Exception as e:
                    print(f"⚠️  Error validating {template_path}: {e}")
                    validation_results[template_path] = {"valid": False, "error": str(e)}

    return validation_results
