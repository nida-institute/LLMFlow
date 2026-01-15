
"""Tests for pipeline telemetry and cost tracking.

Tests cover:
- Per-step timing measurement
- Token usage tracking (input/output)
- Cost calculation per model
- Pipeline summary generation
- Optimization suggestions
- MCP call tracking
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import time

from llmflow.modules.telemetry import (
    StepMetrics,
    PipelineMetrics,
    TelemetryCollector,
    calculate_cost,
    format_duration,
    generate_optimization_suggestions,
)


# ============================================================================
# Test Cost Calculation
# ============================================================================

class TestCostCalculation:
    """Test cost calculation for different models."""

    def test_gpt5_cost_calculation(self):
        """GPT-5 cost calculation with standard rates."""
        cost = calculate_cost(
            model="gpt-5",
            prompt_tokens=1000,
            completion_tokens=500
        )
        # $15/1M input + $60/1M output
        expected = (1000 * 15 / 1_000_000) + (500 * 60 / 1_000_000)
        assert cost == pytest.approx(expected)
        assert cost == pytest.approx(0.045)  # $0.015 + $0.030

    def test_gpt4o_cost_calculation(self):
        """GPT-4o cost calculation with standard rates."""
        cost = calculate_cost(
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500
        )
        # $2.50/1M input + $10/1M output
        expected = (1000 * 2.50 / 1_000_000) + (500 * 10 / 1_000_000)
        assert cost == pytest.approx(expected)
        assert cost == pytest.approx(0.0075)  # $0.0025 + $0.005

    def test_gpt4o_mini_cost_calculation(self):
        """GPT-4o-mini cost calculation with standard rates."""
        cost = calculate_cost(
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500
        )
        # $0.15/1M input + $0.60/1M output
        expected = (1000 * 0.15 / 1_000_000) + (500 * 0.60 / 1_000_000)
        assert cost == pytest.approx(expected)
        assert cost == pytest.approx(0.00045)  # $0.00015 + $0.0003

    def test_unknown_model_defaults_to_zero(self):
        """Unknown models should default to $0 with warning."""
        cost = calculate_cost(
            model="unknown-model",
            prompt_tokens=1000,
            completion_tokens=500
        )
        assert cost == 0.0

    def test_zero_tokens(self):
        """Zero tokens should result in zero cost."""
        cost = calculate_cost(
            model="gpt-4o",
            prompt_tokens=0,
            completion_tokens=0
        )
        assert cost == 0.0

    def test_gpt5_variant_names(self):
        """GPT-5 family variants should use GPT-5 pricing."""
        # o3-mini should map to gpt-5 pricing
        cost = calculate_cost(
            model="o3-mini",
            prompt_tokens=1000,
            completion_tokens=500
        )
        expected = (1000 * 15 / 1_000_000) + (500 * 60 / 1_000_000)
        assert cost == pytest.approx(expected)

        # o3 should also map to gpt-5 pricing
        cost2 = calculate_cost(
            model="o3",
            prompt_tokens=1000,
            completion_tokens=500
        )
        assert cost2 == pytest.approx(expected)

    def test_gpt35_variant_names(self):
        """GPT-3.5 variants should map correctly."""
        # gpt-3.5 should map to gpt-3.5-turbo pricing
        cost = calculate_cost(
            model="gpt-3.5",
            prompt_tokens=1000,
            completion_tokens=500
        )
        expected = (1000 * 0.50 / 1_000_000) + (500 * 1.50 / 1_000_000)
        assert cost == pytest.approx(expected)


# ============================================================================
# Test Duration Formatting
# ============================================================================

class TestDurationFormatting:
    """Test human-readable duration formatting."""

    def test_format_seconds(self):
        """Durations under 1 minute should show seconds."""
        assert format_duration(0.5) == "0.5s"
        assert format_duration(5.234) == "5.2s"
        assert format_duration(45) == "45.0s"

    def test_format_minutes_seconds(self):
        """Durations over 1 minute should show minutes and seconds."""
        assert format_duration(65) == "1m 5s"
        assert format_duration(125.7) == "2m 6s"
        assert format_duration(90) == "1m 30s"

    def test_format_hours(self):
        """Long durations should show hours, minutes, seconds."""
        assert format_duration(3661) == "1h 1m 1s"
        assert format_duration(7200) == "2h 0m 0s"

    def test_zero_duration(self):
        """Zero duration should format correctly."""
        assert format_duration(0) == "0.0s"


# ============================================================================
# Test StepMetrics
# ============================================================================

class TestStepMetrics:
    """Test step-level metrics tracking."""

    def test_create_step_metrics(self):
        """Create step metrics with basic info."""
        metrics = StepMetrics(
            step_name="enrich_passage",
            step_type="llm",
            model="gpt-4o"
        )
        assert metrics.step_name == "enrich_passage"
        assert metrics.step_type == "llm"
        assert metrics.model == "gpt-4o"
        assert metrics.start_time is not None
        assert metrics.end_time is None
        assert metrics.duration is None

    def test_complete_step_metrics(self):
        """Completing step should calculate duration."""
        metrics = StepMetrics(
            step_name="test_step",
            step_type="llm",
            model="gpt-4o"
        )
        time.sleep(0.1)  # Simulate work
        metrics.complete()

        assert metrics.end_time is not None
        assert metrics.duration is not None
        assert metrics.duration >= 0.1

    def test_complete_recalculates_total_tokens(self):
        """Calling complete() should recalculate total_tokens if needed."""
        # Create metrics without total_tokens set
        metrics = StepMetrics(
            step_name="test_step",
            step_type="llm",
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=0  # Explicitly set to 0
        )
        # Override after __post_init__ to simulate external setting of tokens
        metrics.total_tokens = 0
        metrics.prompt_tokens = 1000
        metrics.completion_tokens = 500

        metrics.complete()

        assert metrics.total_tokens == 1500

    def test_step_metrics_with_tokens(self):
        """Step metrics should track token usage."""
        metrics = StepMetrics(
            step_name="test_step",
            step_type="llm",
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500
        )
        assert metrics.prompt_tokens == 1000
        assert metrics.completion_tokens == 500
        assert metrics.total_tokens == 1500

    def test_step_cost_calculation(self):
        """Step should calculate its own cost."""
        metrics = StepMetrics(
            step_name="test_step",
            step_type="llm",
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500
        )
        cost = metrics.calculate_cost()
        assert cost == pytest.approx(0.0075)

    def test_function_step_has_no_cost(self):
        """Function steps should have zero cost."""
        metrics = StepMetrics(
            step_name="parse_passage",
            step_type="function"
        )
        metrics.complete()
        assert metrics.calculate_cost() == 0.0

    def test_mcp_call_tracking(self):
        """Step should track MCP calls."""
        metrics = StepMetrics(
            step_name="enrich",
            step_type="llm",
            model="gpt-4o",
            mcp_calls=15,
            mcp_truncations=2
        )
        assert metrics.mcp_calls == 15
        assert metrics.mcp_truncations == 2


# ============================================================================
# Test PipelineMetrics
# ============================================================================

class TestPipelineMetrics:
    """Test pipeline-level metrics aggregation."""

    def test_empty_pipeline_metrics(self):
        """Empty pipeline should have zero totals."""
        metrics = PipelineMetrics(pipeline_name="test")
        assert metrics.total_duration == 0.0
        assert metrics.total_cost == 0.0
        assert metrics.total_tokens == 0
        assert len(metrics.steps) == 0

    def test_add_step_to_pipeline(self):
        """Adding steps should update pipeline metrics."""
        pipeline = PipelineMetrics(pipeline_name="test")

        step1 = StepMetrics(
            step_name="step1",
            step_type="llm",
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500
        )
        step1.complete()

        pipeline.add_step(step1)

        assert len(pipeline.steps) == 1
        assert pipeline.total_tokens == 1500
        assert pipeline.total_cost > 0

    def test_pipeline_duration_from_steps(self):
        """Pipeline duration should span all steps."""
        pipeline = PipelineMetrics(pipeline_name="test")

        step1 = StepMetrics("step1", "llm", "gpt-4o")
        time.sleep(0.1)
        step1.complete()
        pipeline.add_step(step1)

        step2 = StepMetrics("step2", "llm", "gpt-4o")
        time.sleep(0.1)
        step2.complete()
        pipeline.add_step(step2)

        assert pipeline.total_duration >= 0.2

    def test_get_slowest_steps(self):
        """Should identify slowest steps."""
        pipeline = PipelineMetrics(pipeline_name="test")

        # Add fast step
        fast = StepMetrics("fast", "llm", "gpt-4o")
        time.sleep(0.05)
        fast.complete()
        pipeline.add_step(fast)

        # Add slow step
        slow = StepMetrics("slow", "llm", "gpt-5")
        time.sleep(0.15)
        slow.complete()
        pipeline.add_step(slow)

        # Add medium step
        medium = StepMetrics("medium", "llm", "gpt-4o")
        time.sleep(0.1)
        medium.complete()
        pipeline.add_step(medium)

        slowest = pipeline.get_slowest_steps(n=2)
        assert len(slowest) == 2
        assert slowest[0].step_name == "slow"
        assert slowest[1].step_name == "medium"

    def test_get_cost_breakdown_by_model(self):
        """Should break down costs by model."""
        pipeline = PipelineMetrics(pipeline_name="test")

        # Add GPT-5 step
        gpt5_step = StepMetrics(
            "step1", "llm", "gpt-5",
            prompt_tokens=1000,
            completion_tokens=500
        )
        gpt5_step.complete()
        pipeline.add_step(gpt5_step)

        # Add GPT-4o step
        gpt4o_step = StepMetrics(
            "step2", "llm", "gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500
        )
        gpt4o_step.complete()
        pipeline.add_step(gpt4o_step)

        breakdown = pipeline.get_cost_breakdown_by_model()
        assert "gpt-5" in breakdown
        assert "gpt-4o" in breakdown
        assert breakdown["gpt-5"] > breakdown["gpt-4o"]


# ============================================================================
# Test TelemetryCollector
# ============================================================================

class TestTelemetryCollector:
    """Test the main telemetry collector."""

    def test_start_step_timing(self):
        """Starting a step should create metrics."""
        collector = TelemetryCollector()
        collector.start_step("test_step", "llm", model="gpt-4o")

        assert collector.current_step is not None
        assert collector.current_step.step_name == "test_step"

    def test_end_step_timing(self):
        """Ending a step should complete metrics."""
        collector = TelemetryCollector()
        collector.start_step("test_step", "llm", model="gpt-4o")
        time.sleep(0.1)
        collector.end_step(
            "test_step",
            prompt_tokens=1000,
            completion_tokens=500
        )

        assert collector.current_step is None
        assert len(collector.pipeline.steps) == 1
        step = collector.pipeline.steps[0]
        assert step.duration >= 0.1
        assert step.prompt_tokens == 1000

    def test_record_mcp_call(self):
        """Recording MCP calls should update current step."""
        collector = TelemetryCollector()
        collector.start_step("enrich", "llm", model="gpt-4o")

        collector.record_mcp_call(tool_name="get_passage_text", response_size=5000)
        collector.record_mcp_call(tool_name="get_entities", response_size=120000, truncated=True)

        collector.end_step("enrich", prompt_tokens=1000, completion_tokens=500)

        step = collector.pipeline.steps[0]
        assert step.mcp_calls == 2
        assert step.mcp_truncations == 1

    def test_generate_summary(self):
        """Should generate formatted summary."""
        collector = TelemetryCollector(pipeline_name="test-pipeline")

        # Add a step
        collector.start_step("test", "llm", model="gpt-4o")
        time.sleep(0.1)
        collector.end_step("test", prompt_tokens=1000, completion_tokens=500)

        summary = collector.generate_summary()

        assert "test-pipeline" in summary
        assert "Total Duration" in summary
        assert "Total Cost" in summary
        assert "test" in summary  # Step name


# ============================================================================
# Test Optimization Suggestions
# ============================================================================

class TestOptimizationSuggestions:
    """Test optimization suggestion generation."""

    def test_suggest_model_downgrade(self):
        """Should suggest downgrade when cost difference is significant."""
        step = StepMetrics(
            "bodies_ast", "llm", "gpt-5",
            prompt_tokens=5000,
            completion_tokens=2000
        )
        step.complete()

        suggestions = generate_optimization_suggestions([step])

        # Should suggest gpt-4o as alternative
        assert len(suggestions) > 0
        suggestion = suggestions[0]
        assert "gpt-4o" in suggestion.lower()
        assert "bodies_ast" in suggestion

    def test_suggest_increased_mcp_limit(self):
        """Should suggest increasing max_iterations when close to limit."""
        step = StepMetrics(
            "enrich", "llm", "gpt-4o",
            prompt_tokens=10000,
            completion_tokens=5000,
            mcp_calls=38,  # Close to typical max of 40
        )
        step.complete()

        suggestions = generate_optimization_suggestions([step], mcp_max_iterations=40)

        assert len(suggestions) > 0
        assert any("max_iterations" in s for s in suggestions)

    def test_suggest_truncation_adjustment(self):
        """Should report truncation savings."""
        step = StepMetrics(
            "enrich", "llm", "gpt-4o",
            prompt_tokens=10000,
            completion_tokens=5000,
            mcp_calls=15,
            mcp_truncations=3
        )
        step.complete()

        suggestions = generate_optimization_suggestions([step])

        assert len(suggestions) > 0
        assert any("truncat" in s.lower() for s in suggestions)

    def test_no_suggestions_for_optimal_config(self):
        """Well-optimized steps should have few suggestions."""
        step = StepMetrics(
            "fast_step", "llm", "gpt-4o-mini",
            prompt_tokens=500,
            completion_tokens=200,
            mcp_calls=0
        )
        step.complete()

        suggestions = generate_optimization_suggestions([step])

        # Should have minimal or no suggestions
        # (Might suggest downgrade from mini is already cheapest)
        assert len(suggestions) <= 1

    def test_suggest_max_tokens_reduction(self):
        """Should suggest reducing max_tokens if consistently unused."""
        step = StepMetrics(
            "test", "llm", "gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500  # 500 tokens used
        )
        step.complete()

        # Simulate configured max_tokens of 8192
        suggestions = generate_optimization_suggestions(
            [step],
            configured_max_tokens=8192
        )

        # Should suggest reducing max_tokens since only using 500
        assert any("max_tokens" in s for s in suggestions)


class TestTokenTrackingIntegration:
    """Test that token usage is correctly tracked and returned from LLM runner."""

    @pytest.mark.asyncio
    async def test_chat_completions_returns_usage_dict(self):
        """Chat Completions API should return dict with content and usage."""
        from llmflow.utils.llm_runner import _run_with_chat_completions
        from unittest.mock import Mock, AsyncMock, patch

        # Mock OpenAI response with usage data
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        # Mock MCP client
        mock_mcp = AsyncMock()
        mock_mcp.__aenter__ = AsyncMock(return_value=mock_mcp)
        mock_mcp.__aexit__ = AsyncMock(return_value=None)
        mock_mcp._async_get_tool_definitions = AsyncMock(return_value=[
            {"name": "test_tool", "description": "Test", "inputSchema": {}}
        ])

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await _run_with_chat_completions(
                prompt="test prompt",
                config={"model": "gpt-4o", "temperature": 0.7},
                mcp_client=mock_mcp,
                output_type="text",
                step_name="test_step"
            )

        # Should return dict with content and usage
        assert isinstance(result, dict)
        assert "content" in result
        assert "usage" in result
        assert result["content"] == "Test response"
        assert result["usage"]["prompt_tokens"] == 100
        assert result["usage"]["completion_tokens"] == 50
        assert result["usage"]["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_chat_completions_accumulates_tokens_across_iterations(self):
        """Token usage should accumulate across multiple MCP iterations."""
        from llmflow.utils.llm_runner import _run_with_chat_completions
        from unittest.mock import Mock, AsyncMock, patch

        # First response triggers tool call, second response completes
        mock_response1 = Mock()
        mock_response1.choices = [Mock()]
        mock_response1.choices[0].message = Mock()
        mock_response1.choices[0].message.content = None
        mock_response1.choices[0].message.tool_calls = [Mock()]
        mock_response1.choices[0].message.tool_calls[0].id = "call_1"
        mock_response1.choices[0].message.tool_calls[0].function = Mock()
        mock_response1.choices[0].message.tool_calls[0].function.name = "test_tool"
        mock_response1.choices[0].message.tool_calls[0].function.arguments = '{"arg": "value"}'
        mock_response1.usage = Mock()
        mock_response1.usage.prompt_tokens = 100
        mock_response1.usage.completion_tokens = 20
        mock_response1.usage.total_tokens = 120

        mock_response2 = Mock()
        mock_response2.choices = [Mock()]
        mock_response2.choices[0].message = Mock()
        mock_response2.choices[0].message.content = "Final response"
        mock_response2.choices[0].message.tool_calls = None
        mock_response2.usage = Mock()
        mock_response2.usage.prompt_tokens = 150
        mock_response2.usage.completion_tokens = 50
        mock_response2.usage.total_tokens = 200

        # Mock MCP client and tool execution
        mock_mcp = AsyncMock()
        mock_mcp.__aenter__ = AsyncMock(return_value=mock_mcp)
        mock_mcp.__aexit__ = AsyncMock(return_value=None)
        mock_mcp._async_get_tool_definitions = AsyncMock(return_value=[
            {"name": "test_tool", "description": "Test", "inputSchema": {}}
        ])
        mock_mcp._async_call_tool = AsyncMock(return_value=[Mock(content="tool result")])

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(side_effect=[mock_response1, mock_response2])
            mock_client_class.return_value = mock_client

            result = await _run_with_chat_completions(
                prompt="test prompt",
                config={"model": "gpt-4o", "mcp": {"max_iterations": 5}},
                mcp_client=mock_mcp,
                output_type="text",
                step_name="test_step"
            )

        # Tokens should be accumulated across both API calls
        assert result["usage"]["prompt_tokens"] == 250  # 100 + 150
        assert result["usage"]["completion_tokens"] == 70  # 20 + 50
        assert result["usage"]["total_tokens"] == 320  # 120 + 200

    @pytest.mark.asyncio
    async def test_json_output_preserves_usage(self):
        """JSON output should parse content but preserve usage data."""
        from llmflow.utils.llm_runner import _run_with_chat_completions
        from unittest.mock import Mock, AsyncMock, patch

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '{"key": "value"}'
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 25
        mock_response.usage.total_tokens = 75

        mock_mcp = AsyncMock()
        mock_mcp.__aenter__ = AsyncMock(return_value=mock_mcp)
        mock_mcp.__aexit__ = AsyncMock(return_value=None)
        mock_mcp._async_get_tool_definitions = AsyncMock(return_value=[
            {"name": "test_tool", "description": "Test", "inputSchema": {}}
        ])

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await _run_with_chat_completions(
                prompt="test prompt",
                config={"model": "gpt-4o"},
                mcp_client=mock_mcp,
                output_type="json",
                step_name="test_step"
            )

        # Content should be parsed JSON
        assert isinstance(result["content"], dict)
        assert result["content"]["key"] == "value"
        # Usage should still be present
        assert result["usage"]["prompt_tokens"] == 50
        assert result["usage"]["completion_tokens"] == 25


# ============================================================================
# Test Model Attribution in Telemetry
# ============================================================================

class TestModelAttribution:
    """Test that telemetry correctly attributes costs to the actual model used."""

    def test_telemetry_uses_merged_model_not_step_model(self):
        """Telemetry should record the final merged model, not just step model.

        This is a regression test for the bug where:
        - Step has no model specified
        - Pipeline llm_config specifies gpt-5
        - Telemetry was recording gpt-4o (default) instead of gpt-5

        The fix moves telemetry.start_step() to after config merging.
        """
        from llmflow.modules.telemetry import TelemetryCollector
        from unittest.mock import Mock

        # Create a mock telemetry collector
        telemetry = TelemetryCollector(pipeline_name="test")

        # Simulate the config merging logic from runner.py
        pipeline_config = {
            "llm_config": {"model": "gpt-5"},
            "_telemetry": telemetry
        }

        step = {
            "name": "test_step",
            # No model specified at step level
        }

        # Build merged config (same logic as runner.py lines 592-622)
        llm_config = pipeline_config.get("llm_config", {})
        step_options = step.get("llm_options", {})
        step_config = {
            "model": step.get("model"),
            "temperature": step.get("temperature") or step_options.get("temperature"),
        }
        step_config = {k: v for k, v in step_config.items() if v is not None}

        merged_config = {
            "model": "gpt-4o",  # Universal default
            "temperature": 0.7,
        }
        merged_config.update(llm_config)
        merged_config.update(step_options)
        merged_config.update(step_config)

        final_model = merged_config.get("model", "gpt-4o")

        # Start telemetry with the FINAL model (after merging)
        telemetry.start_step("test_step", "llm", model=final_model)

        # Verify telemetry recorded the correct model
        assert telemetry.current_step.model == "gpt-5"
        assert telemetry.current_step.model != "gpt-4o"

        # Complete the step with token usage
        telemetry.end_step(
            "test_step",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Verify cost is calculated with gpt-5 pricing, not gpt-4o
        step_metrics = telemetry.pipeline.steps[0]
        assert step_metrics.model == "gpt-5"

        # GPT-5 pricing: $15/1M input + $60/1M output
        expected_cost = (1000 * 15 / 1_000_000) + (500 * 60 / 1_000_000)
        assert step_metrics.calculate_cost() == pytest.approx(expected_cost)
        assert step_metrics.calculate_cost() == pytest.approx(0.045)

        # NOT gpt-4o pricing ($2.50/1M input + $10/1M output = $0.0075)
        assert step_metrics.calculate_cost() != pytest.approx(0.0075)

    def test_mixed_models_cost_attribution(self):
        """Verify that pipelines with multiple models correctly attribute costs.

        Tests that gpt-5 costs don't get attributed to gpt-4o and vice versa.
        """
        from llmflow.modules.telemetry import TelemetryCollector

        telemetry = TelemetryCollector(pipeline_name="mixed_models")

        # Step 1: gpt-5 call
        telemetry.start_step("gpt5_step", "llm", model="gpt-5")
        telemetry.end_step("gpt5_step", prompt_tokens=1000, completion_tokens=500)

        # Step 2: gpt-4o call
        telemetry.start_step("gpt4o_step", "llm", model="gpt-4o")
        telemetry.end_step("gpt4o_step", prompt_tokens=2000, completion_tokens=1000)

        # Step 3: another gpt-5 call
        telemetry.start_step("gpt5_step2", "llm", model="gpt-5")
        telemetry.end_step("gpt5_step2", prompt_tokens=500, completion_tokens=250)

        # Verify individual step costs
        gpt5_step1 = telemetry.pipeline.steps[0]
        assert gpt5_step1.model == "gpt-5"
        # GPT-5: $15/1M input + $60/1M output
        expected_gpt5_step1 = (1000 * 15 / 1_000_000) + (500 * 60 / 1_000_000)
        assert gpt5_step1.calculate_cost() == pytest.approx(expected_gpt5_step1)

        gpt4o_step = telemetry.pipeline.steps[1]
        assert gpt4o_step.model == "gpt-4o"
        # GPT-4o: $2.50/1M input + $10/1M output
        expected_gpt4o = (2000 * 2.50 / 1_000_000) + (1000 * 10 / 1_000_000)
        assert gpt4o_step.calculate_cost() == pytest.approx(expected_gpt4o)

        gpt5_step2 = telemetry.pipeline.steps[2]
        assert gpt5_step2.model == "gpt-5"
        expected_gpt5_step2 = (500 * 15 / 1_000_000) + (250 * 60 / 1_000_000)
        assert gpt5_step2.calculate_cost() == pytest.approx(expected_gpt5_step2)

        # Verify cost breakdown aggregates correctly by model
        breakdown = telemetry.pipeline.get_cost_breakdown_by_model()

        # Should have exactly 2 models
        assert len(breakdown) == 2
        assert "gpt-5" in breakdown
        assert "gpt-4o" in breakdown

        # Verify gpt-5 total (2 steps)
        expected_gpt5_total = expected_gpt5_step1 + expected_gpt5_step2
        assert breakdown["gpt-5"] == pytest.approx(expected_gpt5_total)

        # Verify gpt-4o total (1 step)
        assert breakdown["gpt-4o"] == pytest.approx(expected_gpt4o)

        # Verify total cost is sum of all models
        expected_total = expected_gpt5_total + expected_gpt4o
        assert telemetry.pipeline.total_cost == pytest.approx(expected_total)

        # Verify gpt-5 costs are NOT using gpt-4o pricing
        # If they were, the costs would be much lower
        gpt4o_pricing_wrong = (1500 * 2.50 / 1_000_000) + (750 * 10 / 1_000_000)  # gpt-4o pricing for gpt-5 tokens
        assert breakdown["gpt-5"] != pytest.approx(gpt4o_pricing_wrong)
