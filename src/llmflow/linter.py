ALLOWED_STEP_KEYS = {
    "name",
    "type",
    "description",
    "input",
    "inputs",
    "output",
    "outputs",
    "item_var",
    "steps",
    "after",
    "append_to",
    "condition",
    "format",
    "function",
    "log",
    "max_tokens",
    "model",
    "output_type",
    "plugin",
    "prompt",
    "saveas",
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

def validate_step(step, location, errors):
    if "description" in step and not isinstance(step["description"], str):
        errors.append(
            f"{location}: step description must be a string if provided"
        )