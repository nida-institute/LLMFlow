from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from llmflow.utils.scripture import FORMATS as SCRIPTURE_FORMATS
from llmflow.utils.scripture import INCLUDE_FAMILIES as SCRIPTURE_INCLUDE_FAMILIES


class LLMConfig(BaseModel):
    provider: Optional[str] = "openai"  # FIX: Make optional with default
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model_config = ConfigDict(extra="allow")


class GroupByPrefixConfig(BaseModel):
    prefix_length: Optional[int] = None
    prefix_delimiter: Optional[str] = None

    def model_post_init(self, __context):
        if not (self.prefix_length or self.prefix_delimiter):
            raise ValidationError(
                [
                    {
                        "loc": ("group_by_prefix",),
                        "msg": "Provide prefix_length or prefix_delimiter",
                        "type": "value_error",
                    }
                ],
                type(self),
            )


class SaveAsConfig(BaseModel):
    path: str
    group_by_prefix: Optional[Union[int, GroupByPrefixConfig]] = None


class StepConfig(BaseModel):
    """Configuration for a pipeline step

    For plugin steps (type: xpath, tsv, etc.), parameters go in the 'inputs' dict.
    For other steps, 'inputs' is optional.
    """

    model_config = ConfigDict(extra="allow")

    name: str
    type: Optional[str] = None
    function: Optional[str] = None
    inputs: Optional[dict] = None
    outputs: Optional[Union[str, List[str]]] = None
    prompt: Optional[dict] = None
    steps: Optional[List["StepConfig"]] = None
    append_to: Optional[str] = None
    log: Optional[str] = None
    saveas: Optional[Union[str, SaveAsConfig, List[Dict[str, Any]]]] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    timeout_seconds: Optional[int] = None
    # NEW: guards
    require: Optional[List[Dict[str, Any]]] = None
    warn: Optional[List[Dict[str, Any]]] = None
    retry: Optional[Dict[str, Any]] = None


class PipelineConfig(BaseModel):
    """Root pipeline configuration"""

    model_config = ConfigDict(extra="allow")

    name: str
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    llm_config: Optional[LLMConfig] = None
    linter_config: Optional[Dict[str, Any]] = None
    intermediate_file_directory: Optional[str] = None
    output_file_directory: Optional[str] = None
    steps: List[StepConfig]
    vars: Optional[Dict[str, Any]] = None
    prompts_dir: Optional[str] = None


# Enable forward references
StepConfig.model_rebuild()

# ======================================================================================
# Step vocabulary — the single source (project/plans/design-schema-single-source.md)
#
# The pipeline language is a tagged union: which keys a step may carry depends on its
# ``type``. The step schema states that grammar directly — universal keys in
# ``properties``, per-type keys in ``allOf`` branches discriminated on ``type``.
# Everything downstream derives from it: the linter's per-type allowed set
# (:func:`allowed_step_keys`), the object model's attribute set (:func:`step_keys`),
# and the schema-vs-runner guard test. There is no second list of step keys.
# ======================================================================================

_OUTPUT_TARGET = {
    "oneOf": [
        {"type": "string"},
        {"type": "array", "items": {"type": "string"}},
    ]
}

_GUARD_RULES = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "if": {"type": "string"},
            "message": {"type": "string"},
        },
        "required": ["if"],
        "additionalProperties": False,
    },
}

_SAVEAS = {
    "oneOf": [
        {"type": "string"},
        {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "group_by_prefix": {
                    "oneOf": [
                        {"type": "integer"},
                        {
                            "type": "object",
                            "properties": {
                                "prefix_length": {"type": "integer"},
                                "prefix_delimiter": {"type": "string"},
                            },
                            "additionalProperties": False,
                            "anyOf": [
                                {"required": ["prefix_length"]},
                                {"required": ["prefix_delimiter"]},
                            ],
                        },
                    ]
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        {"type": "array", "items": {"type": "object"}},
    ]
}

# Keys read on a step of any type: the generic runner path (name, type, condition, log,
# after, require, warn, retry, and the `plugin:` dispatch) plus the shared output helper
# in utils/step_outputs.py (output/append_to/saveas/format).
_COMMON_STEP_PROPERTIES = {
    "name": {"type": "string"},
    "type": {"type": "string"},
    "description": {"type": "string"},  # documentation; read by no handler
    "condition": {"type": "string"},
    "log": {"type": "string"},
    "after": {"type": "string"},
    "plugin": {"type": "string"},
    # Read on any step type by the guard context builder (utils/guards.py reads
    # inputs.variables when evaluating require/warn), as well as by the handlers below.
    "inputs": {"type": "object"},
    "output": _OUTPUT_TARGET,
    "append_to": {"type": "string"},
    "saveas": _SAVEAS,
    "format": {"type": "string"},
    "require": _GUARD_RULES,
    "warn": _GUARD_RULES,
    "retry": {
        "type": "object",
        "properties": {
            "max_attempts": {"type": "integer", "minimum": 1},
            "delay_seconds": {"type": "number", "minimum": 0},
            "condition": {"type": "string"},
        },
        "additionalProperties": True,
    },
}

_LOADER_TYPES = (
    "load_json",
    "load_yaml",
    "load_xml",
    "load_csv",
    "load_tsv",
    "load_text",
    "load_directory",
)

# Per-type keys, in addition to the common ones above. Each entry becomes an ``allOf``
# branch keyed on ``type``. A step type absent from this list is *permissive*: plugin and
# registered types receive the whole step dict as a flat config, so their keys cannot be
# enumerated here.
_STEP_TYPE_PROPERTIES = [
    (
        ("llm",),
        {
            # `prompt` is either a path or {file, inputs} — exactly what render_prompt()
            # in steps/llm.py reads. Closed deliberately (LLMFlow#197): while this was
            # open, `prompt.template` validated and was then ignored, and the step died
            # with "Prompt 'file' must be a string, got NoneType". Adding a key here
            # without teaching render_prompt() to read it recreates that hole.
            "prompt": {
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string"},
                            "inputs": {"type": "object", "additionalProperties": True},
                        },
                        "required": ["file"],
                        "additionalProperties": False,
                    },
                ]
            },
            "llm_options": {"type": "object", "additionalProperties": True},
            "model": {"type": "string"},
            "temperature": {"type": "number"},
            "max_tokens": {"type": "integer"},
            "max_completion_tokens": {"type": "integer"},
            "timeout_seconds": {"type": "number"},
            "response_format": {"type": "object", "additionalProperties": True},
            "reasoning_effort": {"type": "string"},
            "mcp": {"type": "object", "additionalProperties": True},
            "output_type": {"type": "string"},
            "template": {"type": "string"},
        },
    ),
    (
        ("function",),
        {
            "function": {"type": "string"},
        },
    ),
    (
        ("duckdb",),
        {
            "query_file": {"type": "string"},
        },
    ),
    (
        ("scripture",),
        {
            # A named edition, resolved through the registry — never a path here. See
            # project/plans/design-scripture-editions.md (LLMFlow#200).
            "edition": {"type": "string"},
            "passage": {"type": "string"},
            # The enum is the implemented set, read from the one place that defines it, so a
            # format cannot be accepted by lint before it exists or outlive its removal.
            "format": {"type": "string", "enum": list(SCRIPTURE_FORMATS)},
            # The scheme `passage` is written in. Not an enum: a Paratext project brings its
            # own, and a custom mapping is a file the human puts in the store.
            "versification": {"type": "string"},
            # The annotation families, read from the one place that names them. A list
            # always — a bare string is rejected with the corrected form.
            "include": {
                "type": "array",
                "items": {"type": "string", "enum": list(SCRIPTURE_INCLUDE_FAMILIES)},
            },
        },
    ),
    (
        ("basex",),
        {
            "database": {"type": "string"},
            "query": {"type": "string"},
            "query_file": {"type": "string"},
            "timeout_seconds": {"type": "number"},
        },
    ),
    (
        ("for-each",),
        {
            "in": {},
            "for": {"type": "string"},
            "steps": {"type": "array"},
            "debug_label": {"type": "string"},
            "parallel": {"type": "integer", "minimum": 1},
            "group_by": {"type": "string"},
            "order_by": {
                "oneOf": [
                    {"type": "object", "additionalProperties": True},
                    {"type": "array", "items": {"type": "object"}},
                ]
            },
        },
    ),
    (
        ("window",),
        {
            "in": {},
            "for": {"type": "string"},
            "steps": {"type": "array"},
            "size": {"type": "integer"},
            "stride": {"type": "integer"},
            "include_partial": {"type": "boolean"},
            "start_when": {"type": "string"},
            "end_when": {"type": "string"},
            "size_by_tokens": {"type": "integer"},
            "stride_by_tokens": {"type": "integer"},
            "model": {"type": "string"},
            "merge": {"type": "object", "additionalProperties": True},
        },
    ),
    (
        ("if",),
        {"steps": {"type": "array"}},
    ),
    (
        ("json",),
        {"value": {}},
    ),
    (
        _LOADER_TYPES,
        {
            "path": {"type": "string"},
            "pattern": {"type": "string"},
            "delimiter": {"type": "string"},
            # Post-load filters applied by utils/data.py to the loaded payload.
            "key": {"type": "string"},
            "xpath": {"type": "string"},
            "namespaces": {"type": "object", "additionalProperties": True},
            "output_format": {"type": "string"},
            "where": {"type": "string"},
            "limit": {"type": "integer"},
            "offset": {"type": "integer"},
            "columns": {"type": "array", "items": {"type": "string"}},
        },
    ),
    (
        ("save",),
        {
            "path": {"type": "string"},
            "content": {},
        },
    ),
]


def _type_branch(types, properties):
    """Build one ``if type == …  then <keys>`` branch of the step schema."""
    match = {"const": types[0]} if len(types) == 1 else {"enum": list(types)}
    return {
        "if": {"properties": {"type": match}, "required": ["type"]},
        "then": {"properties": properties},
    }


_STEP_SCHEMA = {
    "type": "object",
    "properties": _COMMON_STEP_PROPERTIES,
    "required": ["name", "type"],
    "allOf": [_type_branch(types, props) for types, props in _STEP_TYPE_PROPERTIES],
}

PIPELINE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "variables": {"type": "object", "additionalProperties": True},
        "llm_config": {
            "type": "object",
            "properties": {
                "provider": {"type": "string"},
                "model": {"type": "string"},
                "max_tokens": {"type": "integer"},
                "temperature": {"type": "number"},
            },
            "required": ["provider", "model"],
        },
        "linter_config": {"type": "object", "additionalProperties": True},
        "intermediate_file_directory": {"type": "string"},
        "output_file_directory": {"type": "string"},
        "steps": {"type": "array", "items": _STEP_SCHEMA},
    },
    "required": ["name", "steps"],
}


# --- derived views of the step vocabulary ---------------------------------------------
#
# These read PIPELINE_SCHEMA, so the schema stays the only declaration. Consumers (the
# linter, the object model, the guard tests) call these rather than keeping their own list.


def _step_items() -> dict:
    return PIPELINE_SCHEMA["properties"]["steps"]["items"]


def _branch_types(branch: dict) -> set:
    """The step types a schema branch applies to."""
    match = branch.get("if", {}).get("properties", {}).get("type", {})
    if "const" in match:
        return {match["const"]}
    return set(match.get("enum", ()))


def common_step_keys() -> set:
    """Step keys valid regardless of ``type``."""
    return set(_step_items().get("properties", {}))


def declared_step_types() -> set:
    """Step types with a declared per-type key set (i.e. not permissive)."""
    types: set = set()
    for branch in _step_items().get("allOf", []):
        types |= _branch_types(branch)
    return types


def allowed_step_keys(step_type):
    """Keys a step of *step_type* may carry, or ``None`` when the type is permissive.

    ``None`` means "cannot be enumerated": plugin and registered step types receive the
    whole step dict as a flat config, so any key may be meaningful to the plugin.
    """
    if step_type not in declared_step_types():
        return None
    keys = common_step_keys()
    for branch in _step_items().get("allOf", []):
        if step_type in _branch_types(branch):
            keys |= set(branch.get("then", {}).get("properties", {}))
    return keys


def step_value_enums(step_type) -> dict:
    """`{key: allowed values}` for every per-type key the schema constrains to an enum.

    An array-valued key reports its *item* enum, so `include: [ids]` and `format: usj` are
    checked the same way. Read by the linter so the enum lives only in the schema.
    """
    if step_type not in declared_step_types():
        return {}
    enums: dict = {}
    for branch in _step_items().get("allOf", []):
        if step_type not in _branch_types(branch):
            continue
        for key, spec in branch.get("then", {}).get("properties", {}).items():
            if not isinstance(spec, dict):
                continue
            if isinstance(spec.get("enum"), list):
                enums[key] = list(spec["enum"])
            else:
                items = spec.get("items")
                if isinstance(items, dict) and isinstance(items.get("enum"), list):
                    enums[key] = list(items["enum"])
    return enums


def step_keys() -> set:
    """Every declared step key — the union across all types.

    This is the object model's attribute set: ``Step`` is flat and generic, exposing the
    union, while *validation* is per-type (see :func:`allowed_step_keys`).
    """
    keys = common_step_keys()
    for branch in _step_items().get("allOf", []):
        keys |= set(branch.get("then", {}).get("properties", {}))
    return keys
