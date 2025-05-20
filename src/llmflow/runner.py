import yaml
import importlib
import inspect
from pathlib import Path

from llmflow.utils.llm_runner import call_llm
from llmflow.utils.io import normalize_nfc
from llmflow.utils.linter import lint_pipeline_contracts

from llmflow.plugins import plugin_registry
from llmflow.plugins.loader import load_plugins
load_plugins()

def resolve(value, context):
    if isinstance(value, str):
        if value.startswith("${") and value.endswith("}"):
            key = value[2:-1]
            return context.get(key, value)
        else:
            # Handle embedded variables like "text with ${var} inside"
            for k, v in context.items():
                value = value.replace(f"${{{k}}}", str(v))
            return value
    elif isinstance(value, dict):
        return resolve_dict(value, context)
    elif isinstance(value, list):
        return [resolve(item, context) for item in value]
    return value

def resolve_dict(obj, context):
    """
    Recursively resolves variables in dictionaries, lists, and strings.

    Args:
        obj: The object to resolve variables in
        context: The context dictionary containing variable values

    Returns:
        The object with all variables resolved
    """
    if isinstance(obj, dict):
        return {k: resolve_dict(v, context) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_dict(v, context) for v in obj]
    elif isinstance(obj, str):
        for k, v in context.items():
            obj = obj.replace(f"${{{k}}}", str(v))
        return obj
    return obj

def render_prompt(prompt_config, context):
    """
    Renders a prompt from a file with variable substitution.

    Args:
        prompt_config: Dictionary with 'file' and optional 'inputs' keys
        context: Context dictionary with variables

    Returns:
        The rendered prompt text
    """
    resolved_prompt = resolve_dict(prompt_config, context)
    prompt_path = Path(resolved_prompt["file"])
    inputs = resolved_prompt.get("inputs", {})

    # Resolve prompt location
    prompts_dir = Path(context.get("prompts_dir", "prompts"))
    full_prompt_path = prompt_path if prompt_path.is_absolute() else prompts_dir / prompt_path

    print(f"Loading prompt from: {full_prompt_path}")
    rendered_prompt = full_prompt_path.read_text()
    for key, val in context.items():
        rendered_prompt = rendered_prompt.replace(f"{{{key}}}", str(val))

    return rendered_prompt


def run_for_each_step(rule, context):
    input_spec = rule["input"]
    item_var = rule["item_var"]
    steps = rule["steps"]

    # 🔍 Support plugin-sourced iteration
    if isinstance(input_spec, dict) and "type" in input_spec:
        plugin_type = input_spec["type"]
        if plugin_type not in plugin_registry:
            raise ValueError(f"Plugin '{plugin_type}' not found.")
        plugin_func = plugin_registry[plugin_type]
        loop_input = list(plugin_func(input_spec))  # convert generator to list
    else:
        # Original behavior: resolve variable like "${scene_list}"
        loop_input = resolve(input_spec, context)

    if not isinstance(loop_input, list):
        raise ValueError(f"For-each input {input_spec} must resolve to a list.")

    for item in loop_input:
        context[item_var] = item  # bind the variable like 'scene'

        for substep in steps:
            if substep["type"] == "function":
                raise NotImplementedError("Functions inside for-each not implemented yet.")

            elif substep["type"] == "llm":
                rendered_prompt = render_prompt(substep["prompt"], context)
                result = normalize_nfc(call_llm(rendered_prompt, from_file=False))

                if "append_to" in substep:
                    target_list_name = substep["append_to"]
                    if target_list_name not in context:
                        context[target_list_name] = []
                    context[target_list_name].append(result)

def run_llm_step(rule, context, pipeline_config):
    rendered_prompt = render_prompt(rule["prompt"], context)

    # Read model config
    llm_config = pipeline_config.get("llm_config", {})
    step_config = rule.get("llm_options", {})

    merged_config = {
        "model": step_config.get("model", llm_config.get("model", "gpt-4o")),
        "max_tokens": step_config.get("max_tokens", llm_config.get("max_tokens", 1000)),
        "temperature": step_config.get("temperature", llm_config.get("temperature", 0.7)),
    }

    result = normalize_nfc(call_llm(
        rendered_prompt,
        model=merged_config["model"],
        max_tokens=merged_config["max_tokens"],
        temperature=merged_config["temperature"],
        from_file=False
    ))

    # Write result to output variables
    for out in rule.get("outputs", []):
        context[out] = result

    return result

def run_function_step(rule, context):
    module_path, func_name = rule["function"].rsplit(".", 1)

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        if module_path.startswith("utils."):
            suggestion = "llmflow." + module_path
            raise ModuleNotFoundError(f"✖️ Module '{module_path}' not found. Did you mean '{suggestion}'?") from e
        else:
            raise

    func = getattr(module, func_name)

    # Resolve inputs from context
    resolved_inputs = {k: resolve(v, context) for k, v in rule["inputs"].items()}

    # Filter to match function signature
    valid_params = inspect.signature(func).parameters.keys()
    filtered_inputs = {k: v for k, v in resolved_inputs.items() if k in valid_params}

    result = func(**filtered_inputs)

    # Assign result(s) to context
    if isinstance(result, dict):
        for k in rule["outputs"]:
            context[k] = result.get(k)
    else:
        for k, v in zip(rule["outputs"], [result]):
            context[k] = v


def run_pipeline(pipeline_path, variables=None, dry_run=False):

    variables = variables or {}
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())

    # Run contract linter before anything else
    lint_pipeline_contracts(pipeline_path)

    # Transitioning to "steps" instead of "rules" in YAML
    pipeline_root = pipeline.get("pipeline", {})
    if "steps" in pipeline_root and "rules" not in pipeline_root:
        pipeline_root["rules"] = pipeline_root.pop("steps")

    rules = pipeline_root.get("rules", [])

    context = dict(pipeline_root.get("variables", {}))
    context.update(variables)

    print(f"{'[DRY RUN]' if dry_run else '[LIVE RUN]'} Running: {pipeline_path}")
    print(f"Variables: {context}")

    for rule in rules:
        name = rule["name"]
        if dry_run:
            print(f"Would run: {name}")
            continue

        if rule["type"] == "function":
            run_function_step(rule, context)
        elif rule["type"] == "for-each":
            run_for_each_step(rule, context)
        elif rule["type"] == "llm":
            run_llm_step(rule, context, pipeline["pipeline"])
        else:
            raise ValueError(f"Unknown step type: {rule['type']}")


    print("Pipeline complete.")
