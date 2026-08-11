"""Slice 1 of the public Python API (LLMFlow#187).

- `load_pipeline_config` is the ONE place that parses a pipeline YAML (custom `!tags`,
  empty files) — replacing the copy inlined in runner.py, linter.py, pipeline_paths.py.
- `PIPELINE_SCHEMA` / `PipelineConfig` know the directory keys (previously only allowed
  as `additionalProperties`), so the schema is the complete vocabulary the object model
  will mirror.
"""
import textwrap
from pathlib import Path

import pytest

from llmflow.pipeline_schema import PIPELINE_SCHEMA, PipelineConfig
from llmflow.yaml_loader import load_pipeline_config


# --- the single loader ---

def test_load_pipeline_config_parses_yaml(tmp_path):
    p = tmp_path / "p.yaml"
    p.write_text("name: p\nsteps: []\n", encoding="utf-8")
    cfg = load_pipeline_config(p)
    assert cfg["name"] == "p"
    assert cfg["steps"] == []


def test_load_pipeline_config_supports_llmflow_tags(tmp_path):
    p = tmp_path / "p.yaml"
    p.write_text(textwrap.dedent("""
        name: p
        steps:
          - !window_advance
            name: advance
            cursor: next_pos
    """), encoding="utf-8")
    cfg = load_pipeline_config(p)
    assert cfg["steps"][0]["_tag"] == "window_advance"
    assert cfg["steps"][0]["name"] == "advance"


def test_load_pipeline_config_empty_file_is_empty_dict(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    assert load_pipeline_config(p) == {}


def test_load_pipeline_config_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_pipeline_config(tmp_path / "nope.yaml")


def test_load_pipeline_config_accepts_str_path(tmp_path):
    p = tmp_path / "p.yaml"
    p.write_text("name: p\nsteps: []\n", encoding="utf-8")
    assert load_pipeline_config(str(p))["name"] == "p"


# --- schema knows the directory keys (gap closed) ---

def test_schema_declares_directory_keys():
    props = PIPELINE_SCHEMA["properties"]
    assert props["intermediate_file_directory"]["type"] == "string"
    assert props["output_file_directory"]["type"] == "string"


def test_pipeline_config_accepts_directory_keys():
    cfg = PipelineConfig(
        name="p",
        steps=[],
        intermediate_file_directory="outputs/intermediate",
        output_file_directory="outputs/out",
    )
    assert cfg.intermediate_file_directory == "outputs/intermediate"
    assert cfg.output_file_directory == "outputs/out"
