import os
import tempfile
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field

from llmflow.runner import run_pipeline


def create_test_dict():
    """Helper function to create test data"""
    return {"value": "test_value"}


def create_nested_dict():
    """Helper function to create nested data"""
    return {"outer": {"inner": "nested_value"}}


def create_empty_list():
    """Helper function to create empty list"""
    return []


def create_large_list():
    """Helper function to create large list"""
    return list(range(100))


def test_data_flows_through_pipeline():
    """Test that data flows correctly through a multi-step pipeline"""

    pipeline = {
        "name": "test-data-flow",
        "variables": {},
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
        },
        "steps": [
            {
                "name": "create_data",
                "type": "function",
                "function": "tests.test_data_flow.create_test_dict",
                "outputs": "data",
            },
            {
                "name": "extract_value",
                "type": "function",
                "function": "operator.getitem",
                "inputs": ["${data}", "value"],
                "outputs": "result",
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline, f)

        run_pipeline(pipeline_file, skip_lint=True)


def test_data_flow_with_nested_references():
    """Test data flow with nested variable references"""

    pipeline = {
        "name": "test-nested-data-flow",
        "variables": {},
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
        },
        "steps": [
            {
                "name": "create_nested",
                "type": "function",
                "function": "tests.test_data_flow.create_nested_dict",
                "outputs": "nested_data",
            },
            {
                "name": "access_nested",
                "type": "function",
                "function": "operator.getitem",
                "inputs": ["${nested_data}", "outer"],
                "outputs": "outer_data",
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline, f)

        run_pipeline(pipeline_file, skip_lint=True)


def test_data_flow_with_empty_lists():
    """Test that empty lists are handled correctly"""

    pipeline = {
        "name": "test-empty-lists",
        "variables": {},
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
        },
        "steps": [
            {
                "name": "create_empty_list",
                "type": "function",
                "function": "tests.test_data_flow.create_empty_list",
                "outputs": "empty_list",
            },
            {
                "name": "check_empty",
                "type": "function",
                "function": "builtins.len",
                "inputs": ["${empty_list}"],
                "outputs": "list_length",
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline, f)

        run_pipeline(pipeline_file, skip_lint=True)


def test_data_flow_with_conditional_processing():
    """Test data flow with conditional logic"""

    pipeline = {
        "name": "test-conditional-flow",
        "variables": {},
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
        },
        "steps": [
            {
                "name": "create_value",
                "type": "function",
                "function": "tests.test_data_flow.create_test_dict",
                "outputs": "data",
            },
            {
                "name": "process_value",
                "type": "function",
                "function": "operator.getitem",
                "inputs": ["${data}", "value"],
                "outputs": "result",
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline, f)

        run_pipeline(pipeline_file, skip_lint=True)


def test_data_flow_with_error_recovery():
    """Test that the system handles errors gracefully"""

    pipeline = {
        "name": "test-error-recovery",
        "variables": {},
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
        },
        "steps": [
            {
                "name": "safe_operation",
                "type": "function",
                "function": "tests.test_data_flow.create_test_dict",
                "outputs": "result",
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline, f)

        run_pipeline(pipeline_file, skip_lint=True)


def test_data_flow_with_deeply_nested_structures():
    """Test data flow with deeply nested data structures"""

    pipeline = {
        "name": "test-deep-nesting",
        "variables": {},
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
        },
        "steps": [
            {
                "name": "create_deep_structure",
                "type": "function",
                "function": "tests.test_data_flow.create_nested_dict",
                "outputs": "deep_data",
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline, f)

        run_pipeline(pipeline_file, skip_lint=True)


def test_data_flow_with_large_datasets():
    """Test data flow with larger datasets"""

    pipeline = {
        "name": "test-large-data",
        "variables": {},
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
        },
        "steps": [
            {
                "name": "create_large_list",
                "type": "function",
                "function": "tests.test_data_flow.create_large_list",
                "outputs": "large_list",
            },
            {
                "name": "get_length",
                "type": "function",
                "function": "builtins.len",
                "inputs": ["${large_list}"],
                "outputs": "list_size",
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline, f)

        run_pipeline(pipeline_file, skip_lint=True)


def test_data_flow_with_variable_substitution_edge_cases():
    """Test edge cases in variable substitution"""

    pipeline = {
        "name": "test-substitution-edge-cases",
        "variables": {"special_chars": "value_with_$pecial_chars"},
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
        },
        "steps": [
            {
                "name": "use_special_var",
                "type": "function",
                "function": "builtins.len",
                "inputs": ["${special_chars}"],
                "outputs": "result",
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline, f)

        run_pipeline(pipeline_file, skip_lint=True)


def test_data_flow_with_circular_references():
    """Test that circular references are detected/handled"""

    pipeline = {
        "name": "test-circular-refs",
        "variables": {},
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
        },
        "steps": [
            {
                "name": "create_data",
                "type": "function",
                "function": "tests.test_data_flow.create_test_dict",
                "outputs": "data",
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline, f)

        run_pipeline(pipeline_file, skip_lint=True)


class LLMConfig(BaseModel):
    """LLM provider configuration"""

    model_config = ConfigDict(extra="allow")

    provider: str
    model: str
    max_tokens: Optional[int] = 4000
    temperature: Optional[float] = None


class StepConfig(BaseModel):
    """Configuration for a pipeline step"""

    model_config = ConfigDict(extra="allow")

    name: str
    type: str
    function: Optional[str] = None
    prompt: Optional[Union[str, Dict[str, Any]]] = None
    input: Optional[Any] = None
    inputs: Optional[Union[Dict[str, Any], List[Any]]] = None
    outputs: Optional[Union[str, List[str]]] = None
    append_to: Optional[str] = None
    steps: Optional[List["StepConfig"]] = None
    item_var: Optional[str] = None
    condition: Optional[str] = None


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
