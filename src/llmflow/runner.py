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
    """
    Resolves variables within a value using the provided context.

    This function recursively replaces placeholders in the given value with corresponding values from the context dictionary. Placeholders are denoted by the syntax `${key}`.

    Args:
        value (Any): The value to resolve. Can be a string, dictionary, list, or any other type.
        context (dict): A dictionary containing key-value pairs for variable substitution.

    Returns:
        Any: The resolved value with variables substituted from the context. If the value is a string, all occurrences of `${key}` are replaced with the corresponding value from the context. If the value is a dictionary or list, the function is applied recursively. Other types are returned unchanged.

    Examples:
        >>> resolve("${name}", {"name": "Alice"})
        'Alice'
        >>> resolve("Hello, ${name}!", {"name": "Bob"})
        'Hello, Bob!'
        >>> resolve({"greet": "Hi, ${user}"}, {"user": "Eve"})
        {'greet': 'Hi, Eve'}
        >>> resolve(["${a}", "${b}"], {"a": 1, "b": 2})
        [1, 2]
    """
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


def run_for_each_step(rule, context, pipeline_config):
    """
    Executes a sequence of steps for each item in a resolved input list, supporting both variable-based and plugin-sourced iteration.
    Args:
    rule (dict): A dictionary specifying the for-each rule. Expected keys:
    - "input": The input specification, either a variable reference (e.g., "${scene_list}") or a plugin dict with a "type" key.
    - "item_var": The name of the variable to bind each item to in the context.
    - "steps": A list of step dictionaries to execute for each item.
    context (dict): The current execution context, used for variable resolution and storing results.
    pipeline_config (dict): The pipeline configuration, passed to steps as needed.
    Raises:
    ValueError: If the input specification cannot be resolved to a list, or if a specified plugin is not found.
    Behavior:
    - Resolves the input specification to a list of items, either via variable resolution or by invoking a registered plugin.
    - Iterates over each item, binding it to the specified variable in the context.
    - For each item, executes the provided steps, which may include function steps or LLM prompt steps.
    - Supports appending LLM results to a list in the context if specified in the step.
    Note:
    - Plugins must be registered in the global `plugin_registry`.
    - Steps of type "function" and "llm" are supported.
    """
    input_spec = rule["input"]
    item_var = rule["item_var"]
    steps = rule["steps"]

    # 🔍 Support plugin-sourced iteration
    if isinstance(input_spec, dict) and "type" in input_spec:
        plugin_type = input_spec["type"]
        if plugin_type not in plugin_registry:
            raise ValueError(f"Plugin '{plugin_type}' not found.")
        plugin_func = plugin_registry[plugin_type]
        loop_input = list(plugin_func(input_spec)) # convert generator to list
    else:
        # Original behavior: resolve variable like "${scene_list}"
        loop_input = resolve(input_spec, context)

    if not isinstance(loop_input, list):
        raise ValueError(f"For-each input {input_spec} must resolve to a list.")

    for item in loop_input:
        # Create an item-specific context - this fixes the undefined item_context issue
        item_context = context.copy()
        item_context[item_var] = item # bind the variable like 'scene'

        for substep in steps:
            if substep["type"] == "function":
                run_function_step(substep, item_context)
            elif substep["type"] == "llm":
                rendered_prompt = render_prompt(substep["prompt"], item_context)  # Use item_context here
                result = normalize_nfc(call_llm(rendered_prompt, from_file=False))
                if "append_to" in substep:
                    target_list_name = substep["append_to"]
                    if target_list_name not in context:
                        context[target_list_name] = []
                    context[target_list_name].append(result)

def run_for_each_step(rule, context, pipeline_config):
    """
    Executes a sequence of steps for each item in a resolved input list, supporting both variable-based and plugin-sourced iteration.
    Args:
    rule (dict): A dictionary specifying the for-each rule. Expected keys:
    - "input": The input specification, either a variable reference (e.g., "${scene_list}") or a plugin dict with a "type" key.
    - "item_var": The name of the variable to bind each item to in the context.
    - "steps": A list of step dictionaries to execute for each item.
    context (dict): The current execution context, used for variable resolution and storing results.
    pipeline_config (dict): The pipeline configuration, passed to steps as needed.
    Raises:
    ValueError: If the input specification cannot be resolved to a list, or if a specified plugin is not found.
    Behavior:
    - Resolves the input specification to a list of items, either via variable resolution or by invoking a registered plugin.
    - Iterates over each item, binding it to the specified variable in the context.
    - For each item, executes the provided steps, which may include function steps or LLM prompt steps.
    - Supports appending LLM results to a list in the context if specified in the step.
    Note:
    - Plugins must be registered in the global `plugin_registry`.
    - Steps of type "function" and "llm" are supported.
    """
    input_spec = rule["input"]
    item_var = rule["item_var"]
    steps = rule["steps"]

    print(f"For-each processing: input={input_spec}, item_var={item_var}")

    # 🔍 Support plugin-sourced iteration
    if isinstance(input_spec, dict) and "type" in input_spec:
        plugin_type = input_spec["type"]
        if plugin_type not in plugin_registry:
            raise ValueError(f"Plugin '{plugin_type}' not found.")
        plugin_func = plugin_registry[plugin_type]
        loop_input = list(plugin_func(input_spec)) # convert generator to list
    else:
        # Original behavior: resolve variable like "${scene_list}"
        loop_input = resolve(input_spec, context)

    # Handle potential JSON string that needs to be parsed
    if isinstance(loop_input, str):
        print(f"Input is a string, attempting to parse as JSON: {loop_input[:100]}...")
        import json
        import re

        # First check if it's a JSON string with code fences
        code_fence_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        fence_matches = re.findall(code_fence_pattern, loop_input)
        if fence_matches:
            print(f"Found code fence in input, extracting content")
            # Take the last code fence block (most likely to be the JSON)
            potential_json = fence_matches[-1].strip()
        else:
            potential_json = loop_input.strip()

        # Try to parse the JSON directly
        try:
            parsed_json = json.loads(potential_json)
            print(f"Successfully parsed JSON with {len(parsed_json)} items")
            loop_input = parsed_json
        except json.JSONDecodeError:
            # Look for array pattern within the text
            json_array_pattern = r'\[\s*{.*}\s*\]'
            array_match = re.search(json_array_pattern, potential_json, re.DOTALL)

            if array_match:
                try:
                    array_text = array_match.group(0)
                    parsed_json = json.loads(array_text)
                    print(f"Found and parsed JSON array with {len(parsed_json)} items")
                    loop_input = parsed_json
                except json.JSONDecodeError:
                    print(f"Found JSON-like array but couldn't parse it, treating as single item")
                    loop_input = [potential_json]  # Treat as single item
            else:
                print(f"No valid JSON found, treating as single item")
                loop_input = [potential_json]  # Treat as single item

    # Ensure loop_input is a list (or at least iterable)
    if not isinstance(loop_input, list) and not hasattr(loop_input, '__iter__'):
        print(f"Input is not iterable, wrapping as single item")
        loop_input = [loop_input]

    print(f"Iterating over {len(list(loop_input)) if hasattr(loop_input, '__len__') else 'unknown number of'} items")

    for i, item in enumerate(loop_input):
        print(f"Processing item {i+1}")
        # Create a nested context with the item
        item_context = context.copy()
        item_context[item_var] = item  # bind the variable

        for substep in steps:
            if substep["type"] == "function":
                run_function_step(substep, item_context)
            elif substep["type"] == "llm":
                rendered_prompt = render_prompt(substep["prompt"], item_context)  # Use item_context
                result = normalize_nfc(call_llm(
                    rendered_prompt,
                    model=pipeline_config.get("llm_config", {}).get("model", "gpt-4o"),
                    max_tokens=pipeline_config.get("llm_config", {}).get("max_tokens", 1000),
                    temperature=pipeline_config.get("llm_config", {}).get("temperature", 0.7),
                    from_file=False
                ))

                if "append_to" in substep:
                    target_list_name = substep["append_to"]
                    if target_list_name not in context:
                        context[target_list_name] = []
                    context[target_list_name].append(result)
                    print(f"Appended result to {target_list_name}, list now has {len(context[target_list_name])} items")



def run_llm_step(rule, context, pipeline_config):
    """
    Executes a single LLM (Large Language Model) step as defined by a rule within a pipeline.

    This function renders a prompt using the provided rule and context, merges LLM configuration options
    from both the pipeline and the rule, calls the LLM with the resulting configuration, normalizes the output,
    and writes the result to the specified output variables in the context.

    Args:
        rule (dict): A dictionary defining the LLM step, including the prompt template, LLM options, and output variables.
        context (dict): A dictionary representing the current execution context, used for rendering the prompt and storing outputs.
        pipeline_config (dict): The overall pipeline configuration, which may include default LLM settings.

    Returns:
        str: The result generated by the LLM after processing the rendered prompt.

    Side Effects:
        Updates the `context` dictionary with the LLM result for each output variable specified in `rule["outputs"]`.
    """
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
    """
    Executes a function specified by a rule, resolving its inputs from the provided context,
    and updates the context with the function's outputs.

    Args:
        rule (dict): A dictionary specifying the function to run, its inputs, and outputs.
            Expected keys:
                - "function" (str): The full dotted path to the function (e.g., "module.submodule.func").
                - "inputs" (dict): A mapping of parameter names to values or context keys to resolve.
                - "outputs" (list): A list of context keys to assign the function's outputs to.
        context (dict): The current execution context, used to resolve input values and store outputs.

    Raises:
        ModuleNotFoundError: If the specified module cannot be imported. Provides a suggestion if the module
            path starts with "utils.".
        AttributeError: If the specified function does not exist in the imported module.

    Notes:
        - Only parameters matching the function's signature are passed.
        - If the function returns a dictionary, output keys are mapped accordingly.
        - If the function returns a single value, it is assigned to the first output key.
    """
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

    # Debug: Show context["expanded_entry"] before resolving inputs
    if "expanded_entry" in context:
        print(f"[DEBUG] context['expanded_entry'] before resolve: {context['expanded_entry']}")

    resolved_inputs = {k: resolve(v, context) for k, v in rule["inputs"].items()}

    if "expanded_entry" in context:
        print(f"[DEBUG] context['expanded_entry'] after resolve: {context['expanded_entry']}")

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
    """
    Executes a YAML-defined pipeline, supporting variable injection, dry runs, and multiple step types.
    """
    variables = variables or {}
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())

    # Debug pipeline structure
    print(f"Debug - Pipeline structure keys: {list(pipeline.keys())}")

    # Handle both structures: pipeline:{} wrapper or direct keys
    if "pipeline" in pipeline:
        # New format with pipeline wrapper
        pipeline_root = pipeline["pipeline"]
    else:
        # Old format with direct keys at top level
        pipeline_root = pipeline

    print(f"Debug - Using pipeline_root with keys: {list(pipeline_root.keys())}")

    # Initialize context with pipeline variables
    context = dict(pipeline_root.get("variables", {}))

    # Then update with CLI variables (these take precedence)
    context.update(variables)

    # Run contract linter before anything else
    lint_pipeline_contracts(pipeline_path)

    # Get steps array - handle both naming conventions
    rules = []
    if "steps" in pipeline_root:
        rules = pipeline_root["steps"]
        print(f"Debug - Found {len(rules)} steps")
    elif "rules" in pipeline_root:
        rules = pipeline_root["rules"]
        print(f"Debug - Found {len(rules)} rules")

    print(f"{'[DRY RUN]' if dry_run else '[LIVE RUN]'} Running: {pipeline_path}")
    print(f"Variables: {context}")
    print(f"Found {len(rules)} steps to execute")

    for rule in rules:
        name = rule.get("name", "unnamed")
        print(f"Executing step: {name} (type: {rule.get('type', 'unknown')})")

        if dry_run:
            print(f"Would run: {name}")
            continue

        if rule["type"] == "function":
            run_function_step(rule, context)
        elif rule["type"] == "for-each":
            # Pass the appropriate config - either top level or pipeline section
            config = pipeline_root if "pipeline" not in pipeline else pipeline["pipeline"]
            run_for_each_step(rule, context, config)
        elif rule["type"] == "llm":
            # Pass the appropriate config - either top level or pipeline section
            config = pipeline_root if "pipeline" not in pipeline else pipeline["pipeline"]
            run_llm_step(rule, context, config)
        else:
            raise ValueError(f"Unknown step type: {rule['type']}")

        print(f"  Context after step {name}: {list(context.keys())}")

    print("Pipeline complete.")
