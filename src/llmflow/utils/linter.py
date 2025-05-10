from pathlib import Path
import yaml
import click
import re
from difflib import unified_diff

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

def lint_pipeline_contracts(pipeline_path):
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    steps = pipeline.get("pipeline", {}).get("steps", pipeline.get("pipeline", {}).get("rules", []))
    variables = set(pipeline.get("pipeline", {}).get("variables", {}).keys())
    prompts_dir = pipeline.get("pipeline", {}).get("variables", {}).get("prompts_dir", "prompts")

    linter_config = pipeline.get("pipeline", {}).get("linter_config", {})
    if not linter_config.get("enabled", True):
        return

    treat_warnings_as_errors = linter_config.get("treat_warnings_as_errors", False)

    errors = []
    warnings = []

    valid_formats = {"json", "markdown", "html", "text"}

    for step in steps:
        if step.get("type") != "llm":
            continue

        file = step.get("prompt", {}).get("file")
        if not file:
            continue

        step_name = step.get("name", "[unnamed step]")
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

        fmt = header.get("format", "").lower()
        if fmt and fmt not in valid_formats:
            errors.append(
                f"❌ Invalid format '{fmt}' in prompt '{file}'. Allowed: {', '.join(valid_formats)}"
            )

    for msg in warnings:
        click.secho(msg, fg="yellow")

    if errors or (treat_warnings_as_errors and warnings):
        for msg in errors:
            click.secho(msg, fg="red")
        raise SystemExit("❌ Prompt contract validation failed. See above for details.")
