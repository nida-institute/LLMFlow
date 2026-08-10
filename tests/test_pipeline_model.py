"""Slice 2 of the public Python API (LLMFlow#187): the Pipeline/Step object model.

The object graph mirrors the pipeline YAML: attributes are the declared syntax keys
(raw, unresolved — resolution is slice 3), nesting mirrors nesting, and the model is
kept in lockstep with PIPELINE_SCHEMA by the drift tests at the bottom.
"""
import textwrap

import pytest

from llmflow import Pipeline, Step, load_pipeline
from llmflow.pipeline_schema import PIPELINE_SCHEMA

# Total, mechanical reserved-word rule: append "_" to Python keywords.
RESERVED = {"in": "in_", "for": "for_"}


def _api_name(key: str) -> str:
    return RESERVED.get(key, key)


PIPELINE_YAML = textwrap.dedent("""
    name: sample
    description: a sample
    intermediate_file_directory: outputs/intermediate
    output_file_directory: ${base}/out
    variables:
      base: outputs
    steps:
      - name: gen
        type: llm
        prompt: gen.gpt
        saveas: ${output_file_directory}/gen.txt
      - name: loop
        type: for-each
        for: ${items}
        steps:
          - name: inner
            type: llm
""")


def _write(tmp_path):
    p = tmp_path / "sample.yaml"
    p.write_text(PIPELINE_YAML, encoding="utf-8")
    return p


def test_load_pipeline_returns_pipeline(tmp_path):
    assert isinstance(load_pipeline(_write(tmp_path)), Pipeline)


def test_pipeline_attributes_mirror_yaml(tmp_path):
    p = load_pipeline(_write(tmp_path))
    assert p.name == "sample"
    assert p.description == "a sample"
    assert p.intermediate_file_directory == "outputs/intermediate"
    assert p.output_file_directory == "${base}/out"        # declared, raw (not resolved)
    assert p.variables == {"base": "outputs"}
    assert [s.name for s in p.steps] == ["gen", "loop"]


def test_step_attributes_mirror_yaml(tmp_path):
    gen = load_pipeline(_write(tmp_path)).steps[0]
    assert isinstance(gen, Step)
    assert gen.type == "llm"
    assert gen.prompt == "gen.gpt"
    assert gen.saveas == "${output_file_directory}/gen.txt"  # declared, raw


def test_nested_steps_and_reserved_words(tmp_path):
    loop = load_pipeline(_write(tmp_path)).steps[1]
    assert loop.for_ == "${items}"                    # 'for' -> 'for_'
    assert [s.name for s in loop.steps] == ["inner"]  # nested Steps mirror nesting


def test_missing_attributes_are_none(tmp_path):
    gen = load_pipeline(_write(tmp_path)).steps[0]
    assert gen.condition is None
    assert gen.append_to is None


def test_model_is_read_only(tmp_path):
    p = load_pipeline(_write(tmp_path))
    with pytest.raises(AttributeError):
        p.name = "changed"


# --- drift tests: the object model mirrors PIPELINE_SCHEMA (the single oracle) ---

# Computed methods (resolve/run/lint/schemas/render_prompt) land in later slices; they are
# not schema keys, so the reverse check excludes them.
_KNOWN_METHODS: set[str] = {"resolve", "lint", "run", "render_prompt"}


def _public_attrs(cls) -> set:
    # dir() so inherited attributes (from the shared _PipelineView base) are included.
    return {a for a in dir(cls) if not a.startswith("_")} - _KNOWN_METHODS


def test_pipeline_attributes_match_schema():
    schema_keys = {_api_name(k) for k in PIPELINE_SCHEMA["properties"]}
    api = _public_attrs(Pipeline)
    missing = schema_keys - api
    invented = api - schema_keys
    assert not missing, f"Pipeline missing attributes for schema keys: {missing}"
    assert not invented, f"Pipeline has non-schema (invented) attributes: {invented}"


def test_step_attributes_match_schema():
    step_props = PIPELINE_SCHEMA["properties"]["steps"]["items"]["properties"]
    schema_keys = {_api_name(k) for k in step_props}
    api = _public_attrs(Step)
    missing = schema_keys - api
    invented = api - schema_keys
    assert not missing, f"Step missing attributes for schema keys: {missing}"
    assert not invented, f"Step has non-schema (invented) attributes: {invented}"
