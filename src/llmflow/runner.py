
import yaml
import importlib
from pathlib import Path

from llmflow.utils.llm_runner import call_llm
from llmflow.utils.io import normalize_nfc

def resolve(value, context):
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        key = value[2:-1]
        return context.get(key, value)
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

def run_pipeline(pipeline_path, variables=None, dry_run=False):

    variables = variables or {}
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    rules = pipeline["pipeline"].get("rules", [])
    context = dict(pipeline["pipeline"].get("variables", {}))
    context.update(variables)

    print(f"{'[DRY RUN]' if dry_run else '[LIVE RUN]'} Running: {pipeline_path}")
    print(f"Variables: {context}")

    for rule in rules:
        name = rule["name"]
        if dry_run:
            print(f"Would run: {name}")
            continue

        if rule["type"] == "function":
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

            resolved_inputs = {k: resolve(v, context) for k, v in rule["inputs"].items()}
            result = func(**resolved_inputs)

            if isinstance(result, dict):
                for k in rule["outputs"]:
                    context[k] = result.get(k)
            else:
                for k, v in zip(rule["outputs"], [result]):
                    context[k] = v
        elif rule["type"] == "for-each":
            loop_input = resolve(rule["input"], context)
            item_var = rule["item_var"]
            steps = rule["steps"]

            if not isinstance(loop_input, list):
                raise ValueError(f"For-each input {rule['input']} must resolve to a list.")

            for item in loop_input:
                context[item_var] = item  # temporarily bind scene, etc.

                for substep in steps:
                    if substep["type"] == "llm":
                        resolved_prompt = resolve_dict(substep["prompt"], context)
                        prompt_path = resolved_prompt["file"]
                        inputs = resolved_prompt.get("inputs", {})

                        prompt_path = Path(prompt_path)
                        prompts_dir = Path(context.get("prompts_dir", "prompts"))

                        if prompt_path.is_absolute():
                            full_prompt_path = prompt_path
                        else:
                            full_prompt_path = prompts_dir / prompt_path

                        print(f"Loading prompt from: {full_prompt_path}")
                        rendered_prompt = full_prompt_path.read_text()
                        for key, val in inputs.items():
                            rendered_prompt = rendered_prompt.replace(f"{{{key}}}", str(val))

                        result = normalize_nfc(call_llm(rendered_prompt, from_file=False))

                        if "append_to" in substep:
                            target_list_name = substep["append_to"]
                            if target_list_name not in context:
                                context[target_list_name] = []
                            context[target_list_name].append(result)

                    elif substep["type"] == "function":
                        raise NotImplementedError("Functions inside for-each not implemented yet.")

        elif rule["type"] == "llm":
            resolved_prompt = resolve_dict(rule["prompt"], context)
            prompt_path = resolved_prompt["file"]
            inputs = resolved_prompt.get("inputs", {})
            # Make the prompt path relative to the prompts directory, not the pipeline location
            prompt_path = Path(prompt_path)
            prompts_dir = Path(context.get("prompts_dir", "prompts"))

            if prompt_path.is_absolute():
                full_prompt_path = prompt_path
            else:
                full_prompt_path = prompts_dir / prompt_path

            print(f"Loading prompt from: {full_prompt_path}")
            rendered_prompt = full_prompt_path.read_text()
            for key, val in inputs.items():
                rendered_prompt = rendered_prompt.replace(f"{{{key}}}", str(val))
            result = normalize_nfc(call_llm(rendered_prompt, from_file=False))
            for out in rule["outputs"]:
                context[out] = result

    print("Pipeline complete.")
