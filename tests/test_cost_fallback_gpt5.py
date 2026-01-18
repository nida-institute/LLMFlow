import pytest

from llmflow.modules.telemetry import TelemetryCollector
import llmflow.runner as runner_module


def test_gpt5_cost_estimation_when_usage_missing(monkeypatch, tmp_path):
    # Arrange: fake LLM call returning content without usage
    def fake_call_llm(prompt, config, output_type="text"):
        return {"content": "Short output text for testing.", "usage": {}}

    monkeypatch.setattr(runner_module, "call_llm", fake_call_llm)

    telemetry = TelemetryCollector(pipeline_name="test_pipeline")
    pipeline_config = {
        "_telemetry": telemetry,
        "llm_config": {},
        "linter_config": {"log_level": "info"},
    }

    # Prepare a temporary prompt file and point runner to it
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Hello, this is a prompt for estimation.")

    step = {
        "name": "gpt5_step",
        "prompt": prompt_file.name,
        "model": "gpt-5",
        "output_type": "text",
    }

    context = {"prompts_dir": str(tmp_path)}

    # Act
    result = runner_module.run_llm_step(step, context, pipeline_config)

    # Assert: telemetry recorded non-zero tokens and non-zero cost
    assert isinstance(result, str)
    assert telemetry.pipeline.total_tokens > 0
    assert telemetry.pipeline.total_cost > 0.0

    # Cost breakdown contains the model used
    breakdown = telemetry.pipeline.get_cost_breakdown_by_model()
    assert "gpt-5" in breakdown
    assert breakdown["gpt-5"] > 0.0
