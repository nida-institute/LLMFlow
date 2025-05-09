from pathlib import Path
import re
import yaml

def parse_prompt_header(prompt_path):
    text = Path(prompt_path).read_text(encoding="utf-8")
    match = re.search(r"<!--\s*@prompt\s*(.*?)-->", text, re.DOTALL)
    if not match:
        return None

    block = match.group(1)
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    result = {"requires": [], "optional": [], "format": None}

    for line in lines:
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip()
        if key == "requires":
            result["requires"] = [v.strip() for v in val.split(",") if v.strip()]
        elif key == "optional":
            result["optional"] = [v.strip() for v in val.split(",") if v.strip()]
        elif key == "format":
            result["format"] = val

    return result

def lint_pipeline_contracts(pipeline_path):
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    steps = pipeline.get("pipeline", {}).get("steps", pipeline.get("pipeline", {}).get("rules", []))
    variables = set(pipeline.get("pipeline", {}).get("variables", {}).keys())
    errors = []

    valid_formats = {"json", "markdown", "html", "text"}

    for step in steps:
        if step.get("type") != "llm":
            continue

        file = step.get("prompt", {}).get("file")
        if not file:
            continue

        prompt_path = Path(pipeline["pipeline"]["variables"].get("prompts_dir", "prompts")) / file
        if not prompt_path.exists():
            errors.append(f"❌ Prompt file not found: {prompt_path}")
            continue

        header = parse_prompt_header(prompt_path)
        if not header:
            errors.append(f"❌ Missing @prompt header in {prompt_path}")
            continue

        passed_inputs = set(step.get("prompt", {}).get("inputs", {}).keys())
        visible_vars = variables.union(passed_inputs)

        for req in header["requires"]:
            if req not in visible_vars:
                errors.append(f"❌ Missing required input '{req}' in step '{step['name']}' for prompt '{file}'")

        if header["format"] and header["format"].lower() not in valid_formats:
            errors.append(f"❌ Invalid format '{header['format']}' in @prompt header of {prompt_path}. Must be one of: {', '.join(valid_formats)}")

    return sorted(set(errors))
