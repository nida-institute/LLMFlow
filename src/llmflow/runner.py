import yaml
import importlib
import inspect
import logging
from pathlib import Path
import re
import mistune
import json
import click

from llmflow.utils.llm_runner import call_llm
from llmflow.utils.io import normalize_nfc, validate_all_templates
from llmflow.utils.linter import lint_pipeline_contracts, lint_pipeline_full
from llmflow.modules.json_parser import parse_llm_json_response
from llmflow.modules.gpt_api import call_gpt_with_retry, call_gpt_get_json

from llmflow.plugins import plugin_registry
from llmflow.plugins.loader import load_plugins
load_plugins()

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
            resolved_inputs = {}
            for key, value in inputs.items():
                resolved_value = resolve(value, context)
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

# Clear the log file at the start of a new run
open('llmflow.log', 'w').close()

def log_and_screen(msg, level="info"):
    """Helper to log to both screen and file"""
    print(msg)
    getattr(pipeline_logger.logger, level)(msg)

def resolve(value, context):
    """
    Resolves variables within a value using the provided context.
    Supports dot notation and list indexing like ${foo.bar[0].baz}.
    Returns native Python objects for exact variable references.
    """
    import re
    logger = logging.getLogger('llmflow.resolve')

    logger.debug(f"Resolving value: {value}")
    logger.debug(f"Context keys: {list(context.keys())}")

    def get_from_context(expr, ctx):
        """Resolve dot notation and list indices from context."""
        logger.debug(f"get_from_context called with: {expr}")
        parts = re.split(r'\.(?![^\[]*\])', expr)  # split on dots not inside brackets
        result = ctx
        for part in parts:
            # Handle list index: foo[0]
            m = re.match(r'^([a-zA-Z0-9_]+)(\[(\-?\d+)\])?$', part)
            if not m:
                return None
            key = m.group(1)
            idx = m.group(3)
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
            if idx is not None:
                if isinstance(result, list):
                    try:
                        result = result[int(idx)]
                    except (IndexError, ValueError):
                        return None
                else:
                    return None
            if result is None:
                return None
        logger.debug(f"Resolved {expr} to: {result}")
        return result

    if isinstance(value, str):
        # If the value is exactly a variable reference, return the object itself
        pattern_exact = r'^\$\{([^\}]+)\}$'
        match_exact = re.match(pattern_exact, value)
        if match_exact:
            expr = match_exact.group(1)
            resolved = get_from_context(expr, context)
            if resolved is not None:
                return resolved
            else:
                return value  # fallback to original string if not found

        # Otherwise, do the usual string substitution
        pattern = r'\$\{([^\}]+)\}'
        def replace_var(match):
            expr = match.group(1)
            resolved = get_from_context(expr, context)
            return str(resolved) if resolved is not None else match.group(0)
        return re.sub(pattern, replace_var, value)
    elif isinstance(value, dict):
        return {k: resolve(v, context) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve(item, context) for item in value]
    return value

def render_prompt(prompt_config, context):
    """Renders a prompt from a file with variable substitution."""
    logger = logging.getLogger('llmflow.prompt')

    resolved_prompt = resolve(prompt_config, context)
    prompt_path = Path(resolved_prompt["file"])
    inputs = resolved_prompt.get("inputs", {})

    prompts_dir = Path(context.get("prompts_dir", "prompts"))
    full_prompt_path = prompt_path if prompt_path.is_absolute() else prompts_dir / prompt_path

    logger.debug(f"Loading prompt from: {full_prompt_path}")
    rendered_prompt = full_prompt_path.read_text()

    # Simple template substitution
    for key, val in context.items():
        rendered_prompt = rendered_prompt.replace(f"{{{key}}}", str(val))

    return rendered_prompt

def run_step(rule, context, pipeline_config):
    """Step dispatcher"""
    step_type = rule.get("type", "unknown")
    if step_type == "function":
        run_function_step(rule, context)
    elif step_type == "for-each":
        run_for_each_step(rule, context, pipeline_config)
    elif step_type == "llm":
        run_llm_step(rule, context, pipeline_config)
    else:
        raise ValueError(f"Unknown step type: {step_type}")

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

        logger.debug(f"For-each processing: input={input_spec}, item_var={item_var}")

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
            logger.debug(f"Input is a string, attempting to parse as JSON: {loop_input[:100]}...")
            import json
            import re

            # First check if it's a JSON string with code fences
            code_fence_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            fence_matches = re.findall(code_fence_pattern, loop_input)
            if fence_matches:
                logger.debug("Found code fence in input, extracting content")
                # Take the last code fence block (most likely to be the JSON)
                potential_json = fence_matches[-1].strip()
            else:
                potential_json = loop_input.strip()

            # Try to parse the JSON directly
            try:
                parsed_json = json.loads(potential_json)
                loop_input = parsed_json
            except json.JSONDecodeError:
                # Fallback: extract first valid JSON array using regex
                import re
                array_match = re.search(r'(\[[^\]]*\])', potential_json, re.DOTALL)
                if array_match:
                    try:
                        parsed_json = json.loads(array_match.group(1))
                        loop_input = parsed_json
                    except json.JSONDecodeError:
                        loop_input = [potential_json]
                else:
                    loop_input = [potential_json]

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
                run_step(substep, item_context, pipeline_config)

                if "append_to" in substep:
                    target_list_name = substep["append_to"]
                    if target_list_name not in context:
                        context[target_list_name] = []

                    # Get result from the substep
                    result = None
                    outputs = substep.get("outputs")
                    if outputs:  # Handle ANY step type with outputs
                        if isinstance(outputs, str):
                            result = item_context.get(outputs)
                        elif isinstance(outputs, list) and len(outputs) > 0:
                            result = item_context.get(outputs[0])

                    if result is not None:
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

        # Check for templates
        if "template" in rule or "format_with" in rule:
            template_path = rule.get("template") or rule.get("format_with")
            result = apply_output_template(result, template_path, context)

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
            logger = logging.getLogger('llmflow.resolve')
            logger.info(f"Resolving input '{key}': {value}")
            resolved_value = resolve(value, context)
            logger.info(f"Resolved to: {resolved_value}")

            # Temporary debug print to console
            if "list[-1]" in str(value):
                print(f"DEBUG: Resolving {key}: {value} -> {resolved_value}")

            resolved_inputs[key] = resolved_value

        import inspect

        # Get function signature
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        # Call function with context if it accepts it
        if 'context' in params:
            result = func(**resolved_inputs, context=context)
        else:
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

        # Handle append_to if specified
        if "append_to" in rule and result is not None:
            list_name = rule["append_to"]
            if list_name not in context:
                context[list_name] = []
            context[list_name].append(result)
            pipeline_logger.log_step_outputs(name, {list_name: f"Appended: {result}"})

        pipeline_logger.log_step_complete(name)
        handle_step_output(rule, context)

    except Exception as e:
        pipeline_logger.log_step_error(name, e)
        raise

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
                        content = resolve(content_spec, context)
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

def validate_pipeline_expressions(step_inputs, context):
    """
    Raise an error if any input value contains an unresolvable ${...} expression.
    """
    if isinstance(step_inputs, str):
        resolved = resolve(step_inputs, context)
        # If unresolved, it will still contain ${...}
        if isinstance(resolved, str) and "${" in resolved:
            # Instead of regex, just raise error for any remaining ${...}
            unresolved_vars = []
            idx = 0
            while idx < len(resolved):
                start = resolved.find("${", idx)
                if start == -1:
                    break
                end = resolved.find("}", start)
                if end == -1:
                    break
                unresolved_vars.append(resolved[start:end+1])
                idx = end + 1
            for expr in unresolved_vars:
                raise ValueError(f"Unresolved pipeline expression: {expr} in value '{step_inputs}'")
    elif isinstance(step_inputs, dict):
        for v in step_inputs.values():
            validate_pipeline_expressions(v, context)
    elif isinstance(step_inputs, list):
        for item in step_inputs:
            validate_pipeline_expressions(item, context)

def collect_all_templates(steps):
    """
    Recursively collect all template paths from pipeline steps, including:
    - Direct template_path references in function steps
    - Templates referenced in .gpt prompt files
    - Nested steps in for-each loops
    """
    templates = []

    for step in steps:
        step_name = step.get("name", "unnamed")

        # Check for direct template_path in inputs
        inputs = step.get("inputs", {})
        template_path = inputs.get("template_path")
        if template_path:
            templates.append((template_path, step_name))

        # Check for prompt files that might contain templates
        if step.get("type") == "llm":
            prompt_config = step.get("prompt", {})
            prompt_file = prompt_config.get("file")
            if prompt_file:
                # We need to scan the .gpt file for template references
                # Add this to templates list for validation
                templates.append((f"prompts/{prompt_file}", f"{step_name} (prompt file)"))

        # Recursively check nested steps (for-each, etc.)
        if step.get("type") == "for-each":
            nested_steps = step.get("steps", [])
            templates.extend(collect_all_templates(nested_steps))

    return templates

def run_pipeline(pipeline_path, vars=None, dry_run=False):
    """Execute a YAML-defined pipeline with template validation"""
    variables = vars or {}

    # Load pipeline FIRST before using any variables from it
    pipeline = yaml.safe_load(Path(pipeline_path).read_text())
    pipeline_root = pipeline.get("pipeline", pipeline)

    # Get steps EARLY so we can use rules
    rules = pipeline_root.get("steps", pipeline_root.get("rules", []))

    # Now we can use pipeline_logger with rules defined
    # Log and display the run mode
    if dry_run:
        pipeline_logger.logger.info("[DRY RUN] Simulating: %s", pipeline_path)
    else:
        pipeline_logger.logger.info("[LIVE RUN] Running: %s", pipeline_path)

    pipeline_logger.logger.debug(f"Variables: {variables}")  # This goes to file only now
    total_steps = len(rules)
    pipeline_logger.logger.info("Found %d steps to execute", total_steps)

    # Initialize context first for template validation
    context = dict(pipeline_root.get("variables", {}))
    context.update(variables)

    # Template validation - happens for BOTH dry run and live run
    pipeline_logger.logger.info("🔍 Validating pipeline templates...")

    # Use the existing validate_all_templates function - pass the pipeline dict, not the path
    try:
        validate_all_templates(pipeline_root)  # Changed from pipeline_path to pipeline_root
        pipeline_logger.logger.info("✅ All templates validated successfully")
    except Exception as e:
        pipeline_logger.logger.error(f"Template validation failed: {e}")
        raise

    # Pipeline structure validation - also happens for BOTH dry run and live run
    lint_pipeline_contracts(pipeline_path)
    lint_pipeline_full(pipeline_path, pipeline_logger)

    # For each step execution
    for rule in rules:
        name = rule.get("name", "unnamed")

        if dry_run:
            pipeline_logger.logger.info(f"Would run: {name}")
            continue

        try:
            run_step(rule, context, pipeline_root)
        except Exception as e:
            pipeline_logger.logger.error(f"Step '{name}' failed: {e}")
            raise

        pipeline_logger.logger.debug(f"Context after step {name}: {list(context.keys())}")

    pipeline_logger.logger.info("Pipeline complete.")

def apply_output_template(result, template_path, context):
    """Apply a template to format step output"""
    from llmflow.utils.io import render_markdown_template

    # Create template variables with the result
    template_vars = context.copy()
    template_vars['result'] = result

    # Render the template WITH CONTEXT
    formatted = render_markdown_template(
        template_path=template_path,
        variables=template_vars,
        context=context  # ADD THIS LINE - pass the full context for resolution
    )
    return formatted
