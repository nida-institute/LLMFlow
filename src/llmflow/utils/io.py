import json
import re
import os
import unicodedata
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

# --- Markdown rendering and saving ---

def render_markdown_template(template_path, variables):
    """
    Load a Markdown template and substitute variables into it.
    Returns the final rendered Markdown string.
    """
    template_text = Path(template_path).read_text(encoding="utf-8")

    def substitute_var(match):
        var_name = match.group(1)
        return variables.get(var_name, f"{{MISSING:{var_name}}}")

    rendered = re.sub(r"\$\{(\w+)\}", substitute_var, template_text)
    return rendered

def save_markdown_as(text, passage, format="md", output_dir="outputs"):
    """
    Save a Markdown string into the specified format (md, html, etc.).
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    safe_passage = sanitize_filename(passage)

    if format == "md":
        path = Path(output_dir) / f"{safe_passage}.md"
        write_nfc(path, text.strip())
        return str(path)

    elif format == "html":
        html_text = markdown.markdown(text, output_format="html5")
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
    """
    Save a JSON object or string to a file.

    Args:
        passage (str): Identifier used for the filename
        content (Union[str, dict, list]): Content to save - can be:
            - JSON string
            - Python dict or list
            - String with embedded JSON
        output_dir (str): Directory to save the file

    Returns:
        str: Path to the saved file
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    safe_passage = sanitize_filename(passage)
    path = Path(output_dir) / f"{safe_passage}.json"

    # Handle string input - attempt to parse as JSON
    if isinstance(content, str):
        try:
            # Try direct JSON parsing
            parsed_content = json.loads(content)
            content = parsed_content
        except json.JSONDecodeError:
            # Look for JSON in code blocks or other formats
            import re

            # Try to find JSON in code blocks
            json_code_block = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_code_block:
                try:
                    parsed_content = json.loads(json_code_block.group(1).strip())
                    content = parsed_content
                except json.JSONDecodeError:
                    # If we can't parse it, keep it as a string
                    print(f"Warning: Could not parse JSON from code block in: {content[:100]}...")
            else:
                # Keep the original string if no JSON found
                print(f"Warning: Content could not be parsed as JSON, saving as string: {content[:100]}...")
                # Wrap the string in a simple object to make it valid JSON
                content = {"text": content}

    # Normalize content recursively
    content = normalize_nfc(content)

    # Write to file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    return str(path)

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
    return output_path
