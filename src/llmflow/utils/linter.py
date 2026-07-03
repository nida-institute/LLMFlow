import ast
from dataclasses import dataclass
from typing import Any, List, Set
import re
from difflib import unified_diff
from pathlib import Path

import click
import yaml
from pydantic import ValidationError
from llmflow.yaml_loader import LLMFlowLoader as _LLMFlowLoader
from llmflow.pipeline_schema import PipelineConfig, PIPELINE_SCHEMA
from llmflow.exceptions import StepRewindError
from llmflow.utils.llm_runner import validate_model_parameter, get_model_family
from llmflow.utils.get_prefix_directory import get_prefix_directory


def _identifiers_in_expr(expr: str) -> Set[str]:
    """Return all variable names in a Python expression, excluding keywords and builtins."""
    try:
        tree = ast.parse(expr, mode='eval')
        return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    except SyntaxError:
        return set()


def extract_variable_references(text: str) -> Set[str]:
    """Extract all variable references from a string (${var} or {{var}} syntax)"""
    variables = set()

    # Extract ${...} patterns
    for match in re.finditer(r'\$\{([^\}]+)\}', text):
        variables.update(_identifiers_in_expr(match.group(1).strip()))

    # Extract {{...}} patterns
    for match in re.finditer(r'\{\{([^\}]+)\}\}', text):
        variables.update(_identifiers_in_expr(match.group(1).strip()))

    return variables

def _allowed_step_keys_from_schema() -> set:
    props = (
        PIPELINE_SCHEMA.get("properties", {})
        .get("steps", {})
        .get("items", {})
        .get("properties", {})
    )
    return set(props.keys())


# Keep schema-driven keys authoritative so new keywords (like "retry") are picked up
# automatically, then union the plugin-specific extras that live outside the schema.
_SCHEMA_STEP_KEYS = _allowed_step_keys_from_schema()
_EXTRA_STEP_KEYS = {
    "description",
    "output",
    "after",
    "format",
    "log",
    "max_tokens",
    "output_type",
    "plugin",
    "response_format",
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
    # json step keys
    "value",
    # loader step keys
    "pattern",
    "delimiter",
    # basex step keys
    "database",
    "query",
    "query_file",
    "params",
    "timeout",
    # for-each keys
    "parallel",
    "group-by",
    "order-by",
    # window step keys
    "size",
    "stride",
    "include_partial",
    "start_when",
    "end_when",
    "size_by_tokens",
    "stride_by_tokens",
    "merge",
    "item_var",
    "over",
}

ALLOWED_STEP_KEYS = _SCHEMA_STEP_KEYS | _EXTRA_STEP_KEYS
COMMON_TYPOS = {
    "saveaas": "saveas",
    "ouput": "outputs",
    "ouptuts": "outputs",
    "intputs": "inputs",
    "inputss": "inputs",
    "apend_to": "append_to",
}

from llmflow.modules.logger import Logger

# Use unified logger
logger = Logger()


def log_and_screen(msg, color="white", level="info"):
    """Log to file and display once on screen with color"""
    # Log to unified logger (goes to both file and screen)
    if level == "error":
        logger.error(msg)
    elif level == "warning":
        logger.warning(msg)
    else:
        logger.info(msg)

    # Additional colored screen output (optional, since logger already handles screen output)
    if color != "white":  # Only add color if specifically requested
        click.secho(msg, fg=color, err=True)


def parse_prompt_header(prompt_path):
    """Parse header from a .gpt prompt file (supports both YAML frontmatter and HTML comments)"""
    text = Path(prompt_path).read_text(encoding="utf-8")

    # Try YAML frontmatter first (--- ... ---)
    yaml_match = re.search(r"^---\s*\n(.*?)\n---\s*$", text, re.DOTALL | re.MULTILINE)
    if yaml_match:
        block = yaml_match.group(1).strip()
        try:
            data = yaml.safe_load(block)
            # Unwrap 'prompt' key if present (same as HTML comment format)
            return data.get("prompt", data)
        except Exception as e:
            logger.error(f"Failed to parse YAML frontmatter in {prompt_path}: {e}")
            return None

    # Fallback: Try HTML comment style (<!-- ... -->)
    html_match = re.search(r"<!--(.*?)-->", text, re.DOTALL)
    if html_match:
        block = html_match.group(1).strip()
        try:
            data = yaml.safe_load(block)
            # Old format may wrap in 'prompt' key
            return data.get("prompt", data)
        except Exception as e:
            logger.error(f"Failed to parse HTML comment header in {prompt_path}: {e}")
            return None

    # No header found
    logger.error(f"No valid header found in {prompt_path} (tried both --- and <!-- formats)")
    return None


def extract_template_variables(template_content):
    """Extract variables from templates that use {{ variable }} syntax"""
    # Find all {{ variable }} patterns, allowing spaces
    variable_pattern = r"\{\{\s*([^}]+?)\s*\}\}"
    variables = set()

    for match in re.finditer(variable_pattern, template_content):
        var_name = match.group(1).strip()
        # Skip template logic and mixin directives
        if (
            not var_name.startswith("#")
            and not var_name.startswith("/")
            and not var_name.startswith("%")
            and not var_name.startswith("mixin:")
        ):
            variables.add(var_name)

    return variables


def validate_gpt_body_declares_all_vars(prompt_path: str) -> List[str]:
    """Check that every {{var}} used in a .gpt body is declared in requires: or optional:.

    Returns a list of error strings (empty list means the file is clean).
    """
    header = parse_prompt_header(prompt_path)
    if header is None:
        return [
            f"❌ {prompt_path}: No parseable frontmatter — cannot validate template variables"
        ]

    declared: Set[str] = set()
    requires = header.get("requires") or []
    optional = header.get("optional") or []
    if isinstance(requires, list):
        declared.update(requires)
    if isinstance(optional, list):
        declared.update(optional)

    # Extract body (everything after the closing --- of the frontmatter)
    text = Path(prompt_path).read_text(encoding="utf-8")
    frontmatter_match = re.search(
        r"^---[ \t]*\n.*?\n---[ \t]*\n?", text, re.DOTALL | re.MULTILINE
    )
    body = text[frontmatter_match.end():] if frontmatter_match else text

    body_vars = extract_template_variables(body)
    undeclared = body_vars - declared

    return [
        f"❌ {prompt_path}: uses '{{{{var}}}}' for '{var}' but '{var}' is not declared in requires: or optional:"
        for var in sorted(undeclared)
    ]


def format_diff_box(step, file, declared, passed):
    declared_sorted = sorted(declared)
    passed_sorted = sorted(passed)
    diff = list(
        unified_diff(
            declared_sorted,
            passed_sorted,
            fromfile="prompt requires",
            tofile="pipeline inputs",
            lineterm="",
        )
    )
    if not diff:
        return ""
    border = "─" * 76
    lines = [
        f"╭─🔍 Contract Mismatch: {file} ─{border[len(' Contract Mismatch: ─') - len(file):]}",
        f"│ Step: {step}".ljust(78) + "│",
        "│ ❌ Inputs passed to this step do not match the prompt contract.".ljust(78)
        + "│",
        "│".ljust(78) + "│",
    ]
    lines += [f"│ {line}".ljust(78) + "│" for line in diff]
    lines.append("╰" + "─" * 78 + "╯")
    return "\n".join(lines)


def collect_all_steps(items):
    """Recursively collect all steps, including nested for-each and substeps."""
    all_steps = []

    # Handle both list of steps and individual step
    if isinstance(items, list):
        for step in items:
            all_steps.extend(collect_all_steps(step))
    elif isinstance(items, dict):
        all_steps.append(items)

        # Check for nested steps in for-each
        if items.get("type") == "for-each" and "steps" in items:
            nested_steps = items["steps"]
            all_steps.extend(collect_all_steps(nested_steps))

    return all_steps


def validate_all_step_contracts(all_steps, log_func, pipeline_root=None):
    """Validate all LLM steps against their prompt contracts"""
    errors = []
    validated_count = 0

    for step in all_steps:
        step_name = step.get("name", "unnamed")
        step_type = step.get("type", "")

        # Check append_to without outputs
        if "append_to" in step:
            append_to_value = step["append_to"]
            if not step.get("outputs"):
                if isinstance(append_to_value, str) and append_to_value.strip():
                    errors.append(
                        f"❌ Step '{step_name}': append_to: {append_to_value} requires 'outputs' to be specified"
                    )
                continue

        # Validate basex step required fields
        if step_type == "basex":
            if not step.get("database"):
                errors.append(f"❌ Step '{step_name}': basex step requires 'database'")
            if not step.get("query") and not step.get("query_file"):
                errors.append(f"❌ Step '{step_name}': basex step requires 'query' or 'query_file'")

        # Only validate contracts for LLM steps
        if step_type == "llm":
            log_func(
                f"🔍 Validating step '{step_name}' contract: {step.get('prompt', {}).get('file', 'NO_FILE')}"
            )

            prompt_config = step.get("prompt", {})
            prompt_file = prompt_config.get("file")

            if not prompt_file:
                errors.append(f"❌ Step '{step_name}': No prompt file specified")
                continue

            # Get prompts_dir from pipeline variables
            prompts_dir = "prompts"
            if pipeline_root:
                variables = pipeline_root.get("variables", {})
                prompts_dir = variables.get("prompts_dir", "prompts")

            # Resolve prompt path using shared utility (same logic as runner)
            from llmflow.utils.io import resolve_prompt_path
            try:
                prompt_path = str(resolve_prompt_path(prompt_file, prompts_dir))
            except FileNotFoundError:
                errors.append(
                    f"❌ Step '{step_name}': Prompt file not found: {prompt_file}"
                )
                log_func(f"❌ Step '{step_name}' contract validation failed")
                continue

            try:
                prompt_data = parse_prompt_header(prompt_path)

                if not prompt_data:
                    errors.append(
                        f"❌ Step '{step_name}': Invalid prompt header in {prompt_path}"
                    )
                    continue

                # NEW: Handle both old and new header formats
                # Old format: { prompt: { requires: [...], optional: [...] } }
                # New format: { inputs: {...}, outputs: {...} }

                step_inputs = prompt_config.get("inputs", {})

                # Check if using new format (inputs/outputs) or old format (requires/optional)
                if "inputs" in prompt_data:
                    # New format: all keys in 'inputs' are required by default
                    required_inputs = list(prompt_data.get("inputs", {}).keys())
                else:
                    # Old format: explicit 'requires' list
                    required_inputs = prompt_data.get("requires", [])

                missing_inputs = [
                    inp for inp in required_inputs if inp not in step_inputs
                ]
                if missing_inputs:
                    errors.append(
                        f"❌ Step '{step_name}': Missing required inputs: {missing_inputs}"
                    )
                    log_func(f"❌ Step '{step_name}' contract validation failed")
                else:
                    log_func(f"✅ Step '{step_name}' contract validation passed")
                    validated_count += 1

            except Exception as e:
                errors.append(
                    f"❌ Step '{step_name}': Error validating prompt {prompt_path}: {str(e)}"
                )
                log_func(f"❌ Step '{step_name}' contract validation failed")

    return errors, validated_count


def lint_pipeline_contracts(pipeline_path):
    """Validate that all pipeline steps match their prompt contracts"""
    pipeline = yaml.load(Path(pipeline_path).read_text(), Loader=_LLMFlowLoader)
    pipeline_root = pipeline.get("pipeline", pipeline)

    # ✅ CHECK IF LINTER IS DISABLED
    linter_config = pipeline_root.get("linter_config", {})
    if not linter_config.get("enabled", True):  # Default to enabled if not specified
        logger.info("ℹ️  Linter disabled by configuration, skipping validation")
        return

    all_steps = collect_all_steps(pipeline_root.get("steps", []))

    # Use the unified logger for output
    def unified_logger(msg, color="white", level="info"):
        log_and_screen(msg, color, level)

    errors, validated_count = validate_all_step_contracts(all_steps, unified_logger, pipeline_root)

    # Report final results
    if errors:
        logger.error(f"\n❌ Contract validation failed with {len(errors)} errors:")
        for error in errors:
            logger.error(f"  {error}")
        raise SystemExit("Pipeline contract validation failed")
    else:
        logger.info(f"\n✅ All {validated_count} step contracts valid")


def validate_template_step(step, errors, warnings):
    """Validate a template rendering step"""
    if step.get("type") != "function":
        return

    inputs = step.get("inputs", {})
    template_path = inputs.get("template_path")

    # Only validate if template_path is present
    if not template_path:
        return  # Skip if no template_path

    if not Path(template_path).exists():
        errors.append(
            f"❌ Step '{step['name']}': Template file not found: {template_path}"
        )
        return

    try:
        # Read template and extract {{variable}} patterns
        template_content = Path(template_path).read_text()
        template_vars = extract_template_variables(template_content)

        # Get variables provided to the template
        provided_vars = set()
        template_inputs = inputs.get("variables", {})
        if isinstance(template_inputs, dict):
            provided_vars = set(template_inputs.keys())

        # Check for missing variables - CHANGED: Make these errors, not warnings
        missing_vars = template_vars - provided_vars
        if missing_vars:
            for var in missing_vars:
                errors.append(
                    f"❌ Template '{template_path}' uses variable '{var}' but step '{step['name']}' doesn't provide it"
                )

    except Exception as e:
        errors.append(
            f"❌ Step '{step['name']}': Error reading template {template_path}: {e}"
        )


def validate_pipeline(pipeline_config):
    """Main pipeline validation function"""
    errors = []
    warnings = []

    steps = pipeline_config.get("steps", [])

    for step in steps:
        # Existing validations...

        # Add template validation
        validate_template_step(step, errors, warnings)

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def validate_pipeline_structure(pipeline_config):
    try:
        PipelineConfig(**pipeline_config)
        return []
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " → ".join(str(p) for p in err["loc"])
            errors.append(f"❌ Pipeline structure error: {err['msg']} (at [{loc}])")
        return errors


@dataclass
class LintResult:
    """Result of pipeline linting"""

    valid: bool
    errors: List[str]
    warnings: List[str]


def _collect_declared_outputs(all_steps):
    declared = set()
    for step in all_steps:
        outs = step.get("outputs")
        if isinstance(outs, dict):
            declared.update(outs.keys())
        elif isinstance(outs, list):
            declared.update(outs)
        elif isinstance(outs, str):
            declared.add(outs)
    return declared


def _validate_template_var_provenance(all_steps, errors):
    declared = _collect_declared_outputs(all_steps)
    for step in all_steps:
        if step.get("function") != "llmflow.utils.io.render_markdown_template":
            continue
        vars_map = step.get("inputs", {}).get("variables", {})
        if not isinstance(vars_map, dict):
            continue
        for k, v in vars_map.items():
            s = (v or "").strip()
            if s.startswith("${") and s.endswith("}"):
                ref = s[2:-1]
                if ref not in declared:
                    errors.append(
                        f"❌ Template var '{k}' references '{v}' but no prior step declared '{ref}' in outputs"
                    )


def _extract_all_variables_from_value(value, path=""):
    """Recursively extract all variable references from any value (string, dict, list)"""
    variables = set()

    if isinstance(value, str):
        variables.update(extract_variable_references(value))
    elif isinstance(value, dict):
        for k, v in value.items():
            variables.update(_extract_all_variables_from_value(v, f"{path}.{k}" if path else k))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            variables.update(_extract_all_variables_from_value(item, f"{path}[{i}]"))

    return variables


def _build_available_context(pipeline_vars, declared_outputs, item_var=None, for_each_var=None):
    """Build set of variables available at a given step"""
    available = set()

    # Pipeline-level variables
    if pipeline_vars:
        available.update(pipeline_vars.keys())

    # Outputs from previous steps
    available.update(declared_outputs)

    # For-each context
    if item_var:
        available.add(item_var)
    if for_each_var:
        available.add(for_each_var)

    return available


def _validate_variable_references_recursive(steps, pipeline_vars, parent_outputs, errors, parent_item_vars=None):
    """Recursively validate variable references with proper scoping for nested steps

    Args:
        steps: List of steps to validate
        pipeline_vars: Pipeline-level variables
        parent_outputs: Set of outputs declared by parent/previous steps (mutable, shared across recursion)
        errors: List to append error messages to
        parent_item_vars: Set of item_var names from parent for-each loops
    """
    if parent_item_vars is None:
        parent_item_vars = set()

    # Use parent_outputs directly (don't copy) so nested steps can add outputs visible to parent
    declared_outputs = parent_outputs

    for step in steps:
        step_name = step.get("name", "unnamed")
        step_type = step.get("type", "")

        # Build available context for this step
        item_var = step.get("item_var")
        for_each_input = step.get("input")  # for-each uses "input" not "for-each"

        # Combine parent item_vars with current item_var
        current_item_vars = parent_item_vars.copy()
        if item_var:
            current_item_vars.add(item_var)

        # for-each injects loop context variables into nested steps
        if step_type == "for-each":
            current_item_vars.update({"_for_each_index", "_for_each_meta", "_for_each_stack", "loop"})

        available = _build_available_context(
            pipeline_vars,
            declared_outputs,
            None,  # Don't pass item_var here
            for_each_input
        )
        # Add all parent and current item_vars
        available.update(current_item_vars)

        # Extract all variable references from step configuration
        # Check: inputs, outputs, condition, saveas, format, input (for-each), value (json)
        # NOTE: append_to is NOT checked - it declares a new variable, doesn't reference one
        fields_to_check = ["inputs", "condition", "saveas", "format", "input", "value"]

        for field in fields_to_check:
            if field in step:
                field_value = step[field]
                referenced_vars = _extract_all_variables_from_value(field_value)

                # Check each referenced variable
                for var in referenced_vars:
                    root_var = var  # already a root identifier from _identifiers_in_expr

                    if root_var not in available:
                        # Show helpful error message with available variables
                        available_list = sorted(available)
                        errors.append(
                            f"❌ Step '{step_name}' field '{field}': Variable '${{{var}}}' not available. "
                            f"Available: {available_list if available_list else '(none)'}"
                        )

        # Handle nested steps (for-each loops)
        if "steps" in step and isinstance(step["steps"], list):
            # Recursively validate nested steps with current context plus item_var
            _validate_variable_references_recursive(
                step["steps"],
                pipeline_vars,
                declared_outputs,
                errors,
                current_item_vars
            )

        # After processing step (including nested steps), add its outputs to declared_outputs
        outs = step.get("outputs")
        if isinstance(outs, dict):
            declared_outputs.update(outs.keys())
        elif isinstance(outs, list):
            declared_outputs.update(outs)
        elif isinstance(outs, str):
            declared_outputs.add(outs)

        # json and loader steps use singular 'output' key
        if step.get("type") in {"json"} | _LOADER_STEP_TYPES:
            if step.get("output"):
                declared_outputs.add(step["output"])

        # Handle append_to - these create implicit lists
        append_to = step.get("append_to")
        if append_to:
            declared_outputs.add(append_to)

        # !window_advance: the inner step's outputs become available to subsequent
        # steps in the same window iteration (e.g. the cursor variable).
        if step.get("_tag") == "window_advance":
            inner = step.get("step", {})
            inner_outs = inner.get("outputs")
            if isinstance(inner_outs, str):
                declared_outputs.add(inner_outs)
            elif isinstance(inner_outs, list):
                declared_outputs.update(inner_outs)


def _validate_all_variable_references(all_steps, pipeline_vars, errors):
    """Validate that all variable references in step configurations can be resolved

    This is the top-level entry point that starts recursive validation.
    """
    _validate_variable_references_recursive(all_steps, pipeline_vars, set(), errors)


def validate_model_parameters(all_steps, pipeline_config):
    """Validate that LLM parameters are compatible with the model being used.

    Checks parameters from all sources:
    - Pipeline-level llm_config
    - Step-level llm_options
    - Step-level direct parameters

    Returns list of error messages.
    """
    errors = []
    llm_config = pipeline_config.get("llm_config", {})

    # Parameters that can be specified and should be validated
    VALIDATED_PARAMS = {
        "max_tokens",
        "max_completion_tokens",
        "temperature",
        "top_p",
        "top_k",
        "frequency_penalty",
        "presence_penalty",
    }

    for step in all_steps:
        if step.get("type") != "llm":
            continue

        step_name = step.get("name", "unnamed")

        # Build merged config following same logic as runner.py
        step_options = step.get("llm_options", {})

        # Determine the model for this step
        model = step.get("model") or llm_config.get("model") or "gpt-4o"

        # Collect all parameters from all sources
        all_params = {}

        # 1. Pipeline-level defaults
        for param in VALIDATED_PARAMS:
            if param in llm_config:
                all_params[param] = ("pipeline.llm_config", llm_config[param])

        # 2. Step-level llm_options (override pipeline defaults)
        for param in VALIDATED_PARAMS:
            if param in step_options:
                all_params[param] = (f"step '{step_name}' llm_options", step_options[param])

        # 3. Step-level direct parameters (override everything)
        for param in VALIDATED_PARAMS:
            if param in step:
                all_params[param] = (f"step '{step_name}'", step[param])

        # Validate each parameter against the model
        for param, (source, value) in all_params.items():
            param_errors = validate_model_parameter(model, param, value)
            if param_errors:
                # Add context about where the invalid parameter came from
                for error in param_errors:
                    errors.append(f"❌ In {source}: {error}")

    return errors


def _validate_rewind_requirements(
    pipeline_config: dict,
    cli_vars: dict | None,
    rewind_to: str | None,
):
    if not rewind_to:
        return []

    errors = []
    pipeline_root = pipeline_config.get("pipeline", pipeline_config)
    steps = pipeline_root.get("steps", []) or []
    variables = dict(pipeline_root.get("variables", {}))
    if cli_vars:
        variables.update(cli_vars)

    required_steps = []
    for step in steps:
        required_steps.append(step)
        if step.get("name") == rewind_to:
            break
    else:
        errors.append(f"❌ Rewind target '{rewind_to}' not found in pipeline steps")
        return errors

    for step in required_steps:
        step_name = step.get("name", "unnamed")
        if not step.get("saveas"):
            # No saveas — this step will be re-executed during rewind (cheap/deterministic).
            # Its outputs (e.g. passage_info) populate context so downstream saveas paths
            # can be resolved.  Not an error.
            continue

        try:
            candidate_paths = _resolve_save_paths_for_lint(step, variables)
        except StepRewindError:
            # saveas path contains variables that depend on runtime step outputs
            # (e.g. ${passage_info.filename_prefix}).  We cannot validate the artifact
            # at lint time; defer to execution.
            continue

        missing = []
        for candidate in candidate_paths:
            candidate_path = Path(candidate).expanduser()
            if not candidate_path.is_absolute():
                candidate_path = Path.cwd() / candidate_path
            if not candidate_path.exists():
                missing.append(candidate_path)

        if missing:
            errors.append(
                f"❌ Step '{step_name}': saved artifact missing for rewind ({missing[0]})"
            )

    return errors


def _resolve_save_paths_for_lint(step: dict, context: dict) -> List[str]:
    from llmflow.runner import resolve

    saveas_config = step.get("saveas")
    paths: List[str] = []

    if isinstance(saveas_config, str):
        path = resolve(saveas_config, context)
        _ensure_path_resolved_for_lint(path, saveas_config, step)
        return [str(path)]

    if isinstance(saveas_config, dict):
        raw_path = saveas_config.get("path")
        path = resolve(raw_path, context)
        _ensure_path_resolved_for_lint(path, raw_path, step)

        group_cfg = saveas_config.get("group_by_prefix")
        if group_cfg:
            filename = Path(str(path)).name
            if isinstance(group_cfg, int):
                prefix_dir = get_prefix_directory(filename, prefix_length=group_cfg)
            else:
                prefix_dir = get_prefix_directory(
                    filename,
                    prefix_length=group_cfg.get("prefix_length"),
                    prefix_delimiter=group_cfg.get("prefix_delimiter"),
                )
            parent = Path(str(path)).parent
            path = str(parent / prefix_dir / filename)

        return [str(path)]

    raise StepRewindError(
        f"Unsupported saveas configuration for step '{step.get('name', 'unnamed')}'",
        step_name=step.get("name") or "",
    )


def _ensure_path_resolved_for_lint(resolved_value: Any, original: Any, step: dict) -> None:
    path_str = str(resolved_value)
    if "${" in path_str or "{" in path_str:
        raise StepRewindError(
            f"Saveas path for step '{step.get('name', 'unnamed')}' contains unresolved variables: {original}",
            step_name=step.get("name") or "",
        )


def _build_module_func_map(module_ast: ast.Module) -> dict:
    return {
        node.name: node
        for node in ast.walk(module_ast)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _collect_transitive_funcs(
    func_name: str,
    func_map: dict,
    visited: set | None = None,
) -> list:
    if visited is None:
        visited = set()
    if func_name not in func_map or func_name in visited:
        return []
    visited.add(func_name)
    func_node = func_map[func_name]
    result = [func_node]
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            callee = node.func.id
            if callee in func_map and callee not in visited:
                result.extend(_collect_transitive_funcs(callee, func_map, visited))
    return result


def _output_path_violations(func_nodes: list) -> list[tuple[str, int]]:
    violations = []
    for func_node in func_nodes:
        for node in ast.walk(func_node):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "outputs/" in node.value:
                    violations.append((func_node.name, node.lineno))
    return violations


def check_function_step_no_internal_paths(all_steps: list) -> list[str]:
    """Warn when a function: step constructs hardcoded paths to outputs/ internally.

    Follows the same-module call graph transitively so helper-function violations
    are caught, not just violations in the directly-invoked function. See GH #165.
    """
    warnings: list[str] = []
    seen_modules: dict[str, tuple] = {}

    for step in all_steps:
        func_ref = step.get("function")
        if not func_ref or "." not in func_ref:
            continue

        module_dotted, func_name = func_ref.rsplit(".", 1)
        module_path = Path(module_dotted.replace(".", "/") + ".py")

        if not module_path.exists():
            continue

        module_key = str(module_path)
        if module_key not in seen_modules:
            try:
                module_ast = ast.parse(module_path.read_text())
                seen_modules[module_key] = (module_ast, _build_module_func_map(module_ast))
            except SyntaxError:
                continue

        _, func_map = seen_modules[module_key]
        func_nodes = _collect_transitive_funcs(func_name, func_map)
        if not func_nodes:
            continue

        step_name = step.get("name", "unnamed")
        for callee_name, lineno in _output_path_violations(func_nodes):
            if callee_name == func_name:
                warnings.append(
                    f"Step '{step_name}': {func_ref} constructs a path to outputs/ "
                    f"at line {lineno} — receive paths through pipeline inputs instead. (GH #165)"
                )
            else:
                warnings.append(
                    f"Step '{step_name}': {func_ref} calls {callee_name}() which constructs "
                    f"a path to outputs/ at line {lineno} — receive paths through pipeline "
                    f"inputs instead. (GH #165)"
                )

    return warnings


def lint_pipeline_full(
    pipeline_path,
    *,
    vars: dict | None = None,
    rewind_to: str | None = None,
):
    """Lint pipeline and return result object instead of raising SystemExit"""
    all_errors = []
    all_warnings = []

    # Load pipeline first
    try:
        pipeline = yaml.load(Path(pipeline_path).read_text(), Loader=_LLMFlowLoader)
    except FileNotFoundError:
        # Re-raise to let cli.py handle with better error message
        raise

    pipeline_config = pipeline.get("pipeline", pipeline)
    cli_vars = vars or {}

    # ✅ CHECK IF LINTER IS DISABLED
    linter_config = pipeline_config.get("linter_config", {})
    if not linter_config.get("enabled", True):
        logger.info("ℹ️  Linter disabled by configuration, skipping validation")
        return LintResult(valid=True, errors=[], warnings=[])

    logger.info(f"Starting full pipeline lint for: {pipeline_path}")

    # 1) Structure validation
    logger.info("🔍 Validating pipeline structure...")
    structure_errors = validate_pipeline_structure(pipeline_config)
    if structure_errors:
        all_errors.extend(structure_errors)
        for error in structure_errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ Pipeline structure is valid")

    # 1.5) Step keyword validation
    logger.info("🔍 Validating step keywords...")
    all_steps = collect_all_steps(pipeline_config.get("steps", []))
    keyword_errors = lint_pipeline_steps(all_steps)
    if keyword_errors:
        all_errors.extend(keyword_errors)
        for error in keyword_errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ All step keywords are valid")

    # 1.6) Model-parameter compatibility validation
    logger.info("🔍 Validating model-parameter compatibility...")
    parameter_errors = validate_model_parameters(all_steps, pipeline_config)
    if parameter_errors:
        all_errors.extend(parameter_errors)
        for error in parameter_errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ All model parameters are compatible")

    # 2) Prompt contract validation
    errors, validated_count = validate_all_step_contracts(all_steps, log_and_screen, pipeline_config)
    if errors:
        all_errors.extend(errors)
        for error in errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    else:
        logger.info(f"✅ All {validated_count} step contracts valid")

    # 2.1) .gpt body declaration validation: every {{var}} must be in requires:/optional:
    logger.info("🔍 Validating .gpt template variable declarations...")
    gpt_decl_errors: List[str] = []
    pipeline_vars_for_prompts = pipeline_config.get("variables", {})
    prompts_dir_for_decl = pipeline_vars_for_prompts.get("prompts_dir", "prompts")
    for step in all_steps:
        if step.get("type") != "llm":
            continue
        prompt_file = step.get("prompt", {}).get("file")
        if not prompt_file:
            continue
        from llmflow.utils.io import resolve_prompt_path
        try:
            resolved = resolve_prompt_path(prompt_file, prompts_dir_for_decl)
            gpt_decl_errors.extend(validate_gpt_body_declares_all_vars(str(resolved)))
        except FileNotFoundError:
            pass  # Already reported by contract validation above
    if gpt_decl_errors:
        all_errors.extend(gpt_decl_errors)
        for err in gpt_decl_errors:
            logger.error(err)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ All .gpt template variables are declared")

    # 2.5) Variable reference validation (NEW: ensure all variable references can be resolved)
    logger.info("🔍 Validating variable references...")
    variable_errors = []
    pipeline_vars = pipeline_config.get("variables", {})
    # Use pipeline_config.get("steps", []) instead of all_steps to preserve hierarchy
    _validate_all_variable_references(pipeline_config.get("steps", []), pipeline_vars, variable_errors)

    if variable_errors:
        all_errors.extend(variable_errors)
        logger.error(f"\n❌ Variable validation failed with {len(variable_errors)} errors:")
        for error in variable_errors:
            logger.error(f"  {error}")
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    else:
        logger.info("✅ All variable references can be resolved")

    # 3) Template variables validation (NEW: ensure templates and variables match)
    logger.info("🔍 Validating template variables...")
    template_errors = []
    template_warnings = []

    template_steps = [step for step in all_steps if step.get("inputs", {}).get("template_path")]
    for step in template_steps:
        template_path = step.get("inputs", {}).get("template_path", "")
        logger.info(f"🔍 Validating template: {template_path} (step: {step.get('name')})")
        validate_template_step(step, template_errors, template_warnings)

    if template_errors:
        all_errors.extend(template_errors)
        logger.error(f"\n❌ Template validation failed with {len(template_errors)} errors:")
        for error in template_errors:
            logger.error(f"  {error}")
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)
    logger.info("✅ Template variables match pipeline-provided variables")

    # 4) Rewind readiness validation (optional)
    rewind_errors = _validate_rewind_requirements(
        pipeline_config,
        cli_vars,
        rewind_to,
    )
    if rewind_errors:
        all_errors.extend(rewind_errors)
        for error in rewind_errors:
            logger.error(error)
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)

    if all_errors:
        return LintResult(valid=False, errors=all_errors, warnings=all_warnings)

    # 5) Function step internal path check (GH #165)
    func_io_warnings = check_function_step_no_internal_paths(all_steps)
    all_warnings.extend(func_io_warnings)

    # 6) Saveas directory declaration warnings
    _intermediate_raw = pipeline_config.get("intermediate_file_directory")
    _output_raw = pipeline_config.get("output_file_directory")
    if _intermediate_raw or _output_raw:
        from llmflow.runner import resolve as _resolve
        _vars = pipeline_config.get("variables", {}) or {}
        _ctx = {**_vars, **cli_vars}
        _intermediate_dir = Path(str(_resolve(str(_intermediate_raw), _ctx))) if _intermediate_raw else None
        _output_dir = Path(str(_resolve(str(_output_raw), _ctx))) if _output_raw else None
        for _step in all_steps:
            _saveas = _step.get("saveas")
            if not _saveas:
                continue
            _raw_path = _saveas if isinstance(_saveas, str) else _saveas.get("path", "")
            try:
                _saveas_path = Path(str(_resolve(str(_raw_path), _ctx)))
            except Exception:
                continue
            _under_intermediate = _intermediate_dir and _saveas_path.is_relative_to(_intermediate_dir)
            _under_output = _output_dir and _saveas_path.is_relative_to(_output_dir)
            if not _under_intermediate and not _under_output:
                all_warnings.append(
                    f"Step \"{_step.get('name', 'unnamed')}\" saveas path \"{_saveas_path}\" "
                    f"is not under intermediate_file_directory or output_file_directory."
                )

    # Show any warnings
    all_warnings.extend(template_warnings)
    for warning in all_warnings:
        logger.warning(f"⚠️  {warning}")

    logger.info("✅ Pipeline validation completed successfully")
    return LintResult(valid=True, errors=[], warnings=all_warnings)


def check_step_outputs(step):
    """Warn if a step generates data but doesn't store it"""
    warnings = []

    # Check if step has append_to but no outputs
    if "append_to" in step and "outputs" not in step:
        warnings.append(
            f"Step '{step.get('name', 'unnamed')}' has append_to but no outputs"
        )

    # Check if LLM step has neither outputs nor append_to
    if step.get("type") == "llm" and "outputs" not in step and "append_to" not in step:
        warnings.append(
            f"LLM step '{step.get('name', 'unnamed')}' generates content but doesn't store it"
        )

    return warnings


def validate_step_prompt_contract(step, prompt_file, step_name):
    """Validate that a step's inputs match its prompt contract"""
    errors = []
    prompt_path = None
    for possible_path in [
        f"prompts/{prompt_file}",
        f"prompts/storyflow/{prompt_file}",
        prompt_file,
    ]:
        if Path(possible_path).exists():
            prompt_path = possible_path
            break
    if not prompt_path:
        errors.append(f"❌ Step '{step_name}': Prompt file not found: {prompt_file}")
        return errors

    header = parse_prompt_header(prompt_path)
    if not header:
        errors.append(f"❌ Step '{step_name}': Missing or invalid YAML header in {prompt_path}")
        return errors

    step_inputs = set(step.get("prompt", {}).get("inputs", {}).keys())

    # Support both formats
    if "inputs" in header and isinstance(header["inputs"], dict):
        required_inputs = set(header["inputs"].keys())
        optional_inputs = set()
    else:
        # If step provides inputs but the header has no requires: key at all,
        # the contract is incomplete — treat as an error so lint catches it.
        if step_inputs and "requires" not in header:
            errors.append(
                f"❌ Step '{step_name}': Prompt '{prompt_file}' has no 'requires:' "
                f"declaration — cannot validate variable contract. "
                f"Add a 'requires:' list to the frontmatter."
            )
            return errors
        required_inputs = set(header.get("requires", []))
        optional_inputs = set(header.get("optional", []))

    missing_required = required_inputs - step_inputs
    if missing_required:
        for missing in sorted(missing_required):
            errors.append(f"❌ Step '{step_name}': Missing required input '{missing}' for prompt '{prompt_file}'")

    unexpected_inputs = step_inputs - (required_inputs | optional_inputs)
    if unexpected_inputs:
        for unexpected in sorted(unexpected_inputs):
            errors.append(f"⚠️  Step '{step_name}': Unexpected input '{unexpected}' for prompt '{prompt_file}' (not declared)")

    return errors


# Add to your linter (e.g. llmflow/utils/linter.py)

def _lint_conditional_rules(step, errors, key: str):
    rules = step.get(key, [])
    if rules and not isinstance(rules, list):
        errors.append(f"Step '{step.get('name','unnamed')}': '{key}' must be a list")
        return
    for r in rules or []:
        if not isinstance(r, dict):
            errors.append(f"Step '{step.get('name','unnamed')}': each '{key}' rule must be an object")
            continue
        if_val = r.get("if")
        if "if" not in r or not isinstance(if_val, str) or not if_val.strip():
            errors.append(f"Step '{step.get('name','unnamed')}': '{key}' rule must include non-empty 'if' expression")
        for k in r.keys():
            if k not in {"if", "message"}:
                errors.append(f"Step '{step.get('name','unnamed')}': unknown '{key}' key '{k}'")

def _lint_window_step(step: dict, errors: list) -> None:
    """Validate window step configuration."""
    name = step.get("name", "<unnamed>")
    has_size = "size" in step
    has_size_by_tokens = "size_by_tokens" in step
    has_start_when = "start_when" in step

    mode_count = sum([has_size, has_size_by_tokens, has_start_when])

    if mode_count == 0:
        errors.append(
            f"Window step '{name}': must specify one of 'size' (fixed), "
            f"'size_by_tokens' (token-aware), or 'start_when' (condition-based)"
        )
        return

    if mode_count > 1:
        errors.append(
            f"Window step '{name}': 'size', 'size_by_tokens', and 'start_when' are mutually exclusive"
        )
        return

    if has_size:
        size = step["size"]
        if not isinstance(size, int) or size < 1:
            errors.append(f"Window step '{name}': 'size' must be a positive integer")

        if "stride" in step:
            stride = step["stride"]
            if not isinstance(stride, int) or stride < 1:
                errors.append(f"Window step '{name}': 'stride' must be a positive integer")

        if "end_when" in step:
            errors.append(
                f"Window step '{name}': 'end_when' is only valid with 'start_when', not 'size'"
            )

        if "stride_by_tokens" in step:
            errors.append(
                f"Window step '{name}': 'stride_by_tokens' is only valid with 'size_by_tokens'"
            )

    if has_size_by_tokens:
        sbt = step["size_by_tokens"]
        if not isinstance(sbt, int) or sbt < 1:
            errors.append(f"Window step '{name}': 'size_by_tokens' must be a positive integer")

        if "stride_by_tokens" in step:
            s = step["stride_by_tokens"]
            if not isinstance(s, int) or s < 0:
                errors.append(
                    f"Window step '{name}': 'stride_by_tokens' must be a non-negative integer"
                )

        if "stride" in step:
            errors.append(
                f"Window step '{name}': use 'stride_by_tokens' (not 'stride') with 'size_by_tokens'"
            )

        if "end_when" in step or "start_when" in step:
            errors.append(
                f"Window step '{name}': 'start_when'/'end_when' cannot be used with 'size_by_tokens'"
            )

    if has_start_when:
        if "stride" in step:
            errors.append(
                f"Window step '{name}': 'stride' is only valid with 'size', not 'start_when'"
            )
        if "include_partial" in step:
            errors.append(
                f"Window step '{name}': 'include_partial' is only valid with 'size' or 'size_by_tokens', not 'start_when'"
            )
        if "stride_by_tokens" in step:
            errors.append(
                f"Window step '{name}': 'stride_by_tokens' is only valid with 'size_by_tokens'"
            )

    # Validate merge block
    if "merge" in step:
        merge = step["merge"]
        if not isinstance(merge, dict):
            errors.append(f"Window step '{name}': 'merge' must be a dict")
        elif "function" not in merge:
            errors.append(f"Window step '{name}': 'merge' must have a 'function' key")

    if "steps" not in step or not step["steps"]:
        errors.append(f"Window step '{name}': must have a non-empty 'steps' list")


def _collect_var_refs(obj, refs: set | None = None) -> set:
    """Recursively collect root variable names from all ${...} references in a config object."""
    if refs is None:
        refs = set()
    if isinstance(obj, str):
        refs.update(extract_variable_references(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_var_refs(v, refs)
    elif isinstance(obj, list):
        for item in obj:
            _collect_var_refs(item, refs)
    return refs


def _collect_loop_append_targets(steps_list: list) -> set:
    """Recursively collect all append_to targets declared in a steps list."""
    targets: set = set()
    for s in steps_list:
        if "append_to" in s:
            targets.add(s["append_to"])
        if "steps" in s and isinstance(s["steps"], list):
            targets.update(_collect_loop_append_targets(s["steps"]))
    return targets


def _lint_for_each_parallel(step: dict, errors: list) -> None:
    """Error when parallel: is set and a step reads an append_to target from the same loop.

    In parallel mode every iteration starts from the same parent context snapshot —
    append_to lists populated by other iterations are not visible during execution.
    Reading such a variable within the loop produces an empty list (or the pre-loop
    value) instead of the accumulated results, silently corrupting output.
    """
    parallel = step.get("parallel")
    if not isinstance(parallel, int) or parallel <= 1:
        return

    name = step.get("name", "<unnamed>")
    inner_steps = step.get("steps", [])
    append_targets = _collect_loop_append_targets(inner_steps)
    if not append_targets:
        return

    refs = _collect_var_refs(inner_steps)
    cross = append_targets & refs
    for target in sorted(cross):
        errors.append(
            f"Step '{name}': parallel: {parallel} is set but '${{{target}}}' is "
            f"referenced within the loop — in parallel mode, append_to results are "
            f"not visible to concurrent iterations (each iteration starts from the "
            f"parent context snapshot). Remove the cross-iteration reference or use "
            f"parallel: 1."
        )


def _lint_for_each_group_by(step: dict, errors: list) -> None:
    """Validate group-by and order-by on for-each steps."""
    group_by = step.get("group-by")
    order_by = step.get("order-by")
    name = step.get("name", "<unnamed>")

    if group_by is not None:
        # group-by expression must reference ${item.*} to be meaningful
        if isinstance(group_by, str) and not re.search(r"\$\{item\b", group_by):
            errors.append(
                f"Step '{name}': group-by expression '{group_by}' does not reference "
                f"'item' — use ${{item.field}} to group by an attribute of each item."
            )

    if order_by is not None:
        # Collect all direction values from dict and list forms
        directions: list = []
        if isinstance(order_by, dict):
            directions.append(order_by.get("direction", "ascending"))
        elif isinstance(order_by, list):
            for entry in order_by:
                if isinstance(entry, dict):
                    directions.append(entry.get("direction", "ascending"))
        valid = {"ascending", "descending"}
        for d in directions:
            if d not in valid:
                errors.append(
                    f"Step '{name}': order-by direction '{d}' is invalid — "
                    f"use 'ascending' or 'descending'."
                )


_LOADER_STEP_TYPES = {
    "load_json", "load_yaml", "load_xml", "load_csv", "load_tsv",
    "load_text", "load_directory",
}
_LOADER_FORMATS = {"json", "yaml", "xml", "csv", "tsv", "text"}


def _lint_loader_step(step, errors):
    name = step.get("name", "<unnamed>")
    step_type = step.get("type")
    has_output = step.get("output") or step.get("outputs")
    if not has_output:
        errors.append(f"Step '{name}' (type: {step_type}) is missing required key 'output'")
    if not step.get("path"):
        errors.append(f"Step '{name}' (type: {step_type}) is missing required key 'path'")
    elif "${" not in str(step.get("path", "")):
        path = Path(step["path"])
        if not path.exists():
            errors.append(
                f"Step '{name}' (type: {step_type}): path not found: {step['path']}"
            )
    if step_type == "load_directory":
        if not step.get("pattern"):
            errors.append(f"Step '{name}' (type: load_directory) is missing required key 'pattern'")
        fmt = step.get("format")
        if not fmt:
            errors.append(f"Step '{name}' (type: load_directory) is missing required key 'format'")
        elif fmt not in _LOADER_FORMATS:
            errors.append(
                f"Step '{name}' (type: load_directory): invalid format '{fmt}'. "
                f"Must be one of: {sorted(_LOADER_FORMATS)}"
            )


def _lint_json_step(step, errors):
    name = step.get("name", "<unnamed>")
    if not step.get("output"):
        errors.append(f"Step '{name}' (type: json) is missing required key 'output'")
    if "value" not in step:
        errors.append(f"Step '{name}' (type: json) is missing required key 'value'")


def lint_pipeline_steps(steps):
    errors = []
    for step in steps:
        step_name = step.get('name', '<unnamed>')
        for key in step.keys():
            if key not in ALLOWED_STEP_KEYS:
                suggestion = COMMON_TYPOS.get(key)
                message = f"Step '{step_name}' has unknown keyword '{key}'"
                if suggestion:
                    message += f" (Did you mean '{suggestion}'?)"
                errors.append(message)
        _lint_conditional_rules(step, errors, "require")
        _lint_conditional_rules(step, errors, "warn")
        if step.get("type") == "json":
            _lint_json_step(step, errors)
        if step.get("type") in _LOADER_STEP_TYPES:
            _lint_loader_step(step, errors)
        if step.get("type") == "window":
            _lint_window_step(step, errors)
        if step.get("type") == "for-each":
            _lint_for_each_parallel(step, errors)
            _lint_for_each_group_by(step, errors)
    return errors
