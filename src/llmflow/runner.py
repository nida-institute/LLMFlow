import yaml
import importlib
import inspect
import logging
from pathlib import Path

from llmflow.utils.llm_runner import call_llm
from llmflow.utils.io import normalize_nfc
from llmflow.utils.linter import lint_pipeline_contracts
from llmflow.modules.json_parser import parse_llm_json_response

from llmflow.plugins import plugin_registry
from llmflow.plugins.loader import load_plugins
load_plugins()

from llmflow.modules.gpt_api import call_gpt_with_retry, call_gpt_get_json

class PipelineLogger:
    def __init__(self):
        # Set up logging with both file and console handlers
        self.logger = logging.getLogger('llmflow')
        self.logger.setLevel(logging.DEBUG)

        # Clear existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Prevent propagation to root logger to avoid duplicate console output
        self.logger.propagate = False

        # File handler for detailed logs
        file_handler = logging.FileHandler('llmflow.log')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler ONLY for step execution (INFO level and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_step_start(self, step_name, step_type):
        """Show step execution on screen"""
        self.logger.info(f"🚀 Executing: {step_name} ({step_type})")

    def log_step_complete(self, step_name):
        """Show step completion on screen"""
        self.logger.info(f"✅ Completed: {step_name}")

    def log_step_error(self, step_name, error):
        """Show step error on screen"""
        self.logger.error(f"❌ Failed: {step_name} - {str(error)}")

    def log_step_details(self, step_name, step_config, context, log_level='debug'):
        """Log detailed step information to file ONLY"""
        level = self._get_log_level(log_level)

        # These go to file only (DEBUG level)
        self.logger.log(level, f"Step '{step_name}' configuration: {step_config}")

        inputs = step_config.get('inputs', {})
        if inputs:
            # Fix circular import - resolve is defined in this same file
            resolved_inputs = {}
            for key, value in inputs.items():
                resolved_value = resolve(value, context)  # Remove the import line
                resolved_inputs[key] = self._summarize_value(resolved_value)

            self.logger.log(level, f"Step '{step_name}' inputs: {resolved_inputs}")

    def log_step_outputs(self, step_name, outputs, log_level='debug'):
        """Log step outputs to file"""
        level = self._get_log_level(log_level)

        summarized_outputs = {}
        for key, value in outputs.items():
            summarized_outputs[key] = self._summarize_value(value)

        self.logger.log(level, f"Step '{step_name}' outputs: {summarized_outputs}")

    def _get_log_level(self, log_level):
        """Convert string log level to logging constant"""
        return getattr(logging, log_level.upper(), logging.DEBUG)

    def _summarize_value(self, value):
        """Summarize values for logging"""
        if isinstance(value, str):
            if len(value) > 100:
                return f"<string: {len(value)} chars>"
            return f'"{value}"'
        elif isinstance(value, list):
            if len(value) == 0:
                return "[]"
            item_type = type(value[0]).__name__ if value else "unknown"
            return f"<array: {len(value)} {item_type} items>"
        elif isinstance(value, dict):
            return f"<dict: {len(value)} keys>"
        else:
            return str(value)

# Initialize logger at module level
pipeline_logger = PipelineLogger()

def resolve(value, context):
    """
    Resolves variables within a value using the provided context.
    Now supports dot notation for nested objects like ${object.property}

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

            # Handle dot notation for nested properties
            if '.' in key:
                parts = key.split('.')
                result = context
                for part in parts:
                    if isinstance(result, dict):
                        result = result.get(part)
                    else:
                        return value  # Return original if can't resolve
                    if result is None:
                        return value  # Return original if not found
                return result
            else:
                # Handle simple variables
                return context.get(key, value)
        else:
            # Handle embedded variables like "text with ${var} inside"
            import re
            def replace_var(match):
                var_key = match.group(1)
                if '.' in var_key:
                    # Handle nested properties in embedded variables too
                    parts = var_key.split('.')
                    result = context
                    for part in parts:
                        if isinstance(result, dict):
                            result = result.get(part)
                        else:
                            return match.group(0)  # Return original
                        if result is None:
                            return match.group(0)
                    return str(result)
                else:
                    return str(context.get(var_key, match.group(0)))

            pattern = r'\$\{([^}]+)\}'
            return re.sub(pattern, replace_var, value)
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
    """Renders a prompt from a file with variable substitution."""
    logger = logging.getLogger('llmflow.prompt')

    resolved_prompt = resolve_dict(prompt_config, context)
    prompt_path = Path(resolved_prompt["file"])
    inputs = resolved_prompt.get("inputs", {})

    prompts_dir = Path(context.get("prompts_dir", "prompts"))
    full_prompt_path = prompt_path if prompt_path.is_absolute() else prompts_dir / prompt_path

    logger.debug(f"Loading prompt from: {full_prompt_path}")  # Changed from print
    rendered_prompt = full_prompt_path.read_text()
    for key, val in context.items():
        rendered_prompt = rendered_prompt.replace(f"{{{key}}}", str(val))

    return rendered_prompt


def run_for_each_step(rule, context, pipeline_config):
    """Executes a sequence of steps for each item in a resolved input list"""
    logger = logging.getLogger('llmflow.foreach')

    step_name = rule.get('name', 'unnamed_for_each_step')
    log_level = rule.get('log', 'debug')

    # Log step start
    pipeline_logger.log_step_start(step_name, 'for-each')
    pipeline_logger.log_step_details(step_name, rule, context, log_level)

    try:
        input_spec = rule["input"]
        item_var = rule["item_var"]
        steps = rule["steps"]

        logger.debug(f"For-each processing: input={input_spec}, item_var={item_var}")  # Changed from print

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
            logger.debug(f"Input is a string, attempting to parse as JSON: {loop_input[:100]}...")  # Changed from print
            import json
            import re

            # First check if it's a JSON string with code fences
            code_fence_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            fence_matches = re.findall(code_fence_pattern, loop_input)
            if fence_matches:
                logger.debug("Found code fence in input, extracting content")  # Changed from print
                # Take the last code fence block (most likely to be the JSON)
                potential_json = fence_matches[-1].strip()
            else:
                potential_json = loop_input.strip()

            # Try to parse the JSON directly
            try:
                parsed_json = json.loads(potential_json)
                logger.debug(f"Successfully parsed JSON with {len(parsed_json)} items")
                loop_input = parsed_json
            except json.JSONDecodeError:
                # Look for array pattern within the text
                json_array_pattern = r'\[\s*{.*}\s*\]'
                array_match = re.search(json_array_pattern, potential_json, re.DOTALL)

                if array_match:
                    try:
                        array_text = array_match.group(0)
                        parsed_json = json.loads(array_text)
                        logger.debug(f"Found and parsed JSON array with {len(parsed_json)} items")
                        loop_input = parsed_json
                    except json.JSONDecodeError:
                        logger.debug(f"Found JSON-like array but couldn't parse it, treating as single item")
                        loop_input = [potential_json]  # Treat as single item
                else:
                    logger.debug(f"No valid JSON found, treating as single item")
                    loop_input = [potential_json]  # Treat as single item

        # Ensure loop_input is a list (or at least iterable)
        if not isinstance(loop_input, list) and not hasattr(loop_input, '__iter__'):
            logger.debug(f"Input is not iterable, wrapping as single item")
            loop_input = [loop_input]

        logger.debug(f"Iterating over {len(list(loop_input)) if hasattr(loop_input, '__len__') else 'unknown number of'} items")

        for i, item in enumerate(loop_input):
            logger.debug(f"Processing item {i+1}")
            # Create a nested context with the item
            item_context = context.copy()
            item_context[item_var] = item  # bind the variable

            for substep in steps:
                if substep["type"] == "function":
                    run_function_step(substep, item_context)
                elif substep["type"] == "llm":
                    result = run_llm_step(
                        substep,
                        item_context,
                        pipeline_config
                    )

                    if "append_to" in substep:
                        target_list_name = substep["append_to"]
                        if target_list_name not in context:
                            context[target_list_name] = []
                        context[target_list_name].append(result)
                        logger.debug(f"Appended result to {target_list_name}, list now has {len(context[target_list_name])} items")

        pipeline_logger.log_step_complete(step_name)

    except Exception as e:
        pipeline_logger.log_step_error(step_name, e)
        raise

def run_llm_step(rule, context, pipeline_config):
    """Executes a single LLM step with logging"""
    step_name = rule.get('name', 'unnamed_llm_step')
    log_level = rule.get('log', 'debug')

    # Log step start
    pipeline_logger.log_step_start(step_name, 'llm')
    pipeline_logger.log_step_details(step_name, rule, context, log_level)

    try:
        rendered_prompt = render_prompt(rule["prompt"], context)
        llm_config = pipeline_config.get("llm_config", {})
        step_config = rule.get("llm_options", {})

        merged_config = llm_config.copy()
        merged_config.update(step_config)

        if "model" not in merged_config:
            merged_config["model"] = "gpt-4o"

        output_type = rule.get("output_type")

        if output_type == "json":
            result = call_gpt_get_json(merged_config, rendered_prompt, retries=3)
        else:
            result = call_gpt_with_retry(merged_config, rendered_prompt, max_attempts=3)

        # Handle outputs (existing logic)
        outputs = rule.get("outputs")
        result_dict = {}

        if outputs is None:
            pass
        elif isinstance(outputs, list):
            if len(outputs) == 1:
                context[outputs[0]] = result
                result_dict[outputs[0]] = result
            else:
                for out in outputs:
                    context[out] = result
                    result_dict[out] = result
        elif isinstance(outputs, str):
            context[outputs] = result
            result_dict[outputs] = result

        # Log completion and outputs
        pipeline_logger.log_step_complete(step_name)
        pipeline_logger.log_step_outputs(step_name, result_dict, log_level)

        # Handle print/log output
        handle_step_output(rule, context)

        return result

    except Exception as e:
        pipeline_logger.log_step_error(step_name, e)
        raise

def run_function_step(rule, context):
    """Execute a function step with proper variable resolution"""
    name = rule.get("name", "unnamed")
    function_name = rule["function"]
    inputs = rule.get("inputs", {})
    outputs = rule.get("outputs")

    pipeline_logger.log_step_start(name, "function")
    pipeline_logger.log_step_details(name, rule, context, rule.get('log', 'debug'))

    try:
        # Import and get the function
        module_name, func_name = function_name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)

        # RECURSIVELY resolve all input variables
        resolved_inputs = {}
        for key, value in inputs.items():
            resolved_inputs[key] = resolve_deep(value, context)  # ← Change this

        # Call the function with resolved inputs
        result = func(**resolved_inputs)

        # Store outputs in context
        if isinstance(outputs, str):
            context[outputs] = result
        elif isinstance(outputs, list):
            if len(outputs) == 1:
                context[outputs[0]] = result
            else:
                for i, output_name in enumerate(outputs):
                    context[output_name] = result[i] if isinstance(result, (tuple, list)) else result

        pipeline_logger.log_step_complete(name)
        handle_step_output(rule, context)

    except Exception as e:
        pipeline_logger.log_step_error(name, e)
        raise

def resolve_deep(value, context):
    """Recursively resolve variables in nested structures"""
    if isinstance(value, str):
        return resolve(value, context)
    elif isinstance(value, dict):
        return {k: resolve_deep(v, context) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_deep(item, context) for item in value]
    else:
        return value

def handle_step_output(rule, context):
    """Handle saveas output for pipeline steps."""
    if "saveas" in rule:
        saveas_config = rule["saveas"]
        outputs = rule.get("outputs")

        if isinstance(saveas_config, str):
            # Simple syntax
            resolved_path = resolve(saveas_config, context)
            if isinstance(outputs, list):
                content = context[outputs[0]]
            elif isinstance(outputs, str):
                content = context[outputs]
            else:
                raise ValueError("Cannot determine content to save - no outputs specified")
            save_content_to_file(content, resolved_path)

        elif isinstance(saveas_config, list):
            # Array syntax: multiple destinations
            for save_item in saveas_config:
                if isinstance(save_item, dict):
                    path = resolve(save_item["path"], context)

                    # Get content and RESOLVE dot notation
                    if "content" in save_item:
                        content_spec = save_item["content"]
                        content = resolve(content_spec, context)  # ← This was missing!
                    elif isinstance(outputs, list):
                        content_var = outputs[0]
                        content = context[content_var]
                    elif isinstance(outputs, str):
                        content_var = outputs
                        content = context[content_var]
                    else:
                        raise ValueError("Cannot determine content to save")

                    format_type = save_item.get("format", "auto")
                    save_content_to_file(content, path, format_type)


def save_content_to_file(content, path, format_type="auto"):
    """Save content to file with format detection"""
    from pathlib import Path
    import json

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Auto-detect format from extension
    if format_type == "auto":
        ext = file_path.suffix.lower()
        if ext == ".json":
            format_type = "json"
        elif ext in [".md", ".txt"]:
            format_type = "text"

    # Save based on format
    if format_type == "json":
        with open(file_path, "w", encoding="utf-8") as f:
            if isinstance(content, str):
                # If content is already JSON string, parse it first
                try:
                    content = json.loads(content)
                except:
                    pass
            json.dump(content, f, indent=2, ensure_ascii=False)
    else:
        # Default to text/markdown
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(content))

    return str(file_path)


def run_pipeline(pipeline_path, variables=None, dry_run=False):
    """Execute a YAML-defined pipeline with template validation"""
    variables = variables or {}

    # Load pipeline FIRST before using any variables from it
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    pipeline_root = pipeline.get("pipeline", pipeline)

    # Get steps EARLY so we can use rules
    rules = pipeline_root.get("steps", pipeline_root.get("rules", []))

    # Now we can use pipeline_logger with rules defined
    pipeline_logger.logger.info(f"{'[DRY RUN]' if dry_run else '[LIVE RUN]'} Running: {pipeline_path}")
    pipeline_logger.logger.debug(f"Variables: {variables}")  # This goes to file only now
    pipeline_logger.logger.info(f"Found {len(rules)} steps to execute")

    # Add template validation
    from llmflow.utils.io import validate_all_templates
    print("🔍 Validating pipeline templates...")
    validation_results = validate_all_templates(pipeline_root)

    # Check if any templates failed validation
    failed_templates = [
        template for template, result in validation_results.items()
        if not result.get("valid", False)
    ]

    if failed_templates:
        print(f"❌ Template validation failed for: {failed_templates}")
        if not dry_run:
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return
    else:
        print("✅ All templates validated successfully")

    # Initialize context
    context = dict(pipeline_root.get("variables", {}))
    context.update(variables)

    # Run contract linter
    lint_pipeline_contracts(pipeline_path)

    for rule in rules:
        name = rule.get("name", "unnamed")
        step_type = rule.get("type", "unknown")

        if dry_run:
            pipeline_logger.logger.info(f"Would run: {name}")
            continue

        try:
            if step_type == "function":
                run_function_step(rule, context)
            elif step_type == "for-each":
                run_for_each_step(rule, context, pipeline_root)
            elif step_type == "llm":
                run_llm_step(rule, context, pipeline_root)
            else:
                raise ValueError(f"Unknown step type: {step_type}")
        except Exception as e:
            pipeline_logger.logger.error(f"Step '{name}' failed: {e}")
            raise

        pipeline_logger.logger.debug(f"Context after step {name}: {list(context.keys())}")

    pipeline_logger.logger.info("Pipeline complete.")
