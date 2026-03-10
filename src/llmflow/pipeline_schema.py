from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


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
    input: Optional[str] = None  # For for-each steps
    outputs: Optional[Union[str, List[str]]] = None
    prompt: Optional[dict] = None
    item_var: Optional[str] = None
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
    steps: List[StepConfig]
    vars: Optional[Dict[str, Any]] = None
    prompts_dir: Optional[str] = None


# Enable forward references
StepConfig.model_rebuild()

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
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "function": {"type": "string"},
                    "prompt": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "object", "additionalProperties": True},
                        ]
                    },
                    "model": {"type": "string"},
                    "max_tokens": {"type": "integer"},
                    "temperature": {"type": "number"},
                    "timeout_seconds": {"type": "number"},
                    "input": {},
                    "inputs": {"type": "object"},
                    "outputs": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ]
                    },
                    "append_to": {"type": "string"},
                    "steps": {"type": "array"},
                    "item_var": {"type": "string"},
                    "condition": {"type": "string"},
                    "saveas": {
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
                        ]
                    },
                    # NEW: guards in schema
                    "require": {
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
                    },
                    "warn": {
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
                    },
                    "retry": {
                        "type": "object",
                        "properties": {
                            "max_attempts": {"type": "integer", "minimum": 1},
                            "delay_seconds": {"type": "number", "minimum": 0},
                            "condition": {"type": "string"},
                        },
                        "additionalProperties": True,
                    },
                },
                "required": ["name", "type"],
            },
        },
    },
    "required": ["name", "steps"],
}
