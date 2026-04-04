"""Pipeline telemetry and cost tracking.

Provides per-step and pipeline-level metrics including:
- Timing (start/end/duration)
- Token usage (input/output)
- Cost calculation per model
- MCP call tracking
- Optimization suggestions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

from llmflow.modules.logger import Logger

logger = Logger()


# ============================================================================
# Model Metadata Loading
# ============================================================================

_models_cache: Optional[Dict[str, Any]] = None


def _load_models_data() -> Dict[str, Any]:
    """Load model metadata from data/models.json.

    Returns:
        Dict with keys: metadata_version, last_updated, models, model_patterns
    """
    global _models_cache

    if _models_cache is not None:
        return _models_cache

    # Find models.json relative to this file
    # __file__ = src/llmflow/modules/telemetry.py
    # .parent.parent.parent.parent = repo root
    models_file = Path(__file__).parent.parent.parent.parent / "data" / "models.json"

    if not models_file.exists():
        logger.warning(f"⚠️  Model metadata file not found: {models_file}")
        logger.warning("    Falling back to empty model data. Cost calculation unavailable.")
        _models_cache = {
            "metadata_version": "0.0",
            "last_updated": "unknown",
            "models": {},
            "model_patterns": {},
        }
        return _models_cache

    try:
        with open(models_file, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
            _models_cache = data
        return _models_cache
    except Exception as e:
        logger.warning(f"⚠️  Failed to load model metadata from {models_file}: {e}")
        logger.warning("    Falling back to empty model data. Cost calculation unavailable.")
        _models_cache = {
            "metadata_version": "0.0",
            "last_updated": "unknown",
            "models": {},
            "model_patterns": {},
        }
        return _models_cache


def _get_model_metadata_dict() -> Dict[str, Dict[str, Any]]:
    """Get MODEL_METADATA dict from models.json.

    Converts from JSON format (input_price_per_1m, max_context_tokens, supports_json_schema)
    to internal format (input, max_context, json_schema).

    Returns:
        Dict mapping model family keys to metadata dicts
    """
    data = _load_models_data()
    models = data.get("models", {})

    # Convert JSON format to internal format
    metadata = {}
    for key, model in models.items():
        metadata[key] = {
            "input": model.get("input_price_per_1m", 0.0),
            "output": model.get("output_price_per_1m", 0.0),
            "max_context": model.get("max_context_tokens", 0),
            "max_output": model.get("max_output_tokens", 0),
            "json_schema": model.get("supports_json_schema", False),
        }

    return metadata


def _get_model_pricing_dict() -> Dict[str, Dict[str, float]]:
    """Get MODEL_PRICING dict (legacy format)."""
    metadata = _get_model_metadata_dict()
    return {k: {"input": v["input"], "output": v["output"]} for k, v in metadata.items()}


def _get_model_families_dict() -> Dict[str, List[str]]:
    """Get MODEL_FAMILIES dict from models.json."""
    data = _load_models_data()
    return data.get("model_patterns", {})


# Lazy-loaded module-level variables for backward compatibility
MODEL_METADATA = _get_model_metadata_dict()
MODEL_PRICING = _get_model_pricing_dict()
MODEL_FAMILIES = _get_model_families_dict()


def get_model_data_version() -> tuple[str, str]:
    """Get model data version and last updated date.

    Returns:
        Tuple of (version, last_updated_date) e.g. ("1.0", "2026-04-02")
    """
    data = _load_models_data()
    return (
        data.get("metadata_version", "unknown"),
        data.get("last_updated", "unknown"),
    )


def get_pricing_family(model: str) -> Optional[str]:
    """Map a model name to its pricing family.

    Args:
        model: Model name (e.g., "o3-mini", "gpt-4o")

    Returns:
        Pricing family key or None if unknown
    """
    # Try exact match first
    if model in MODEL_PRICING:
        return model

    # Try pattern matching
    for family, patterns in MODEL_FAMILIES.items():
        if any(pattern in model for pattern in patterns):
            return family

    return None


def get_model_metadata(model: str) -> Optional[Dict[str, Any]]:
    """Get comprehensive metadata for a model.

    Args:
        model: Model name (e.g., "gpt-4o", "claude-3.5-sonnet", "gemini-2.5-pro")

    Returns:
        Dict with keys: input, output, max_context, max_output, json_schema
        Returns None if model is unknown
    """
    family = get_pricing_family(model)
    if family and family in MODEL_METADATA:
        return MODEL_METADATA[family]
    return None


def get_model_max_tokens(model: str) -> Optional[int]:
    """Get max context window for a model.

    Args:
        model: Model name

    Returns:
        Max context tokens or None if unknown
    """
    metadata = get_model_metadata(model)
    return metadata["max_context"] if metadata else None


def supports_json_schema(model: str) -> bool:
    """Check if a model supports JSON schema / structured output.

    Args:
        model: Model name

    Returns:
        True if model supports JSON schema (response_format or response_schema)
    """
    metadata = get_model_metadata(model)
    return metadata["json_schema"] if metadata else False


def update_models_from_github(target_path: Optional[Path] = None) -> bool:
    """Update models.json from GitHub main branch.

    Args:
        target_path: Path to save models.json (default: data/models.json in package)

    Returns:
        True if update successful, False otherwise
    """
    url = "https://raw.githubusercontent.com/nida-institute/LLMFlow/main/data/models.json"

    if target_path is None:
        # __file__ = src/llmflow/modules/telemetry.py
        # .parent.parent.parent.parent = repo root
        target_path = Path(__file__).parent.parent.parent.parent / "data" / "models.json"

    try:
        logger.info(f"📡 Fetching latest model metadata from GitHub...")
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Validate basic structure
        required_keys = {"metadata_version", "last_updated", "models", "model_patterns"}
        if not all(k in data for k in required_keys):
            logger.error("❌ Invalid model metadata format from GitHub")
            return False

        # Write to file
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline

        logger.info(f"✅ Updated model metadata to version {data['metadata_version']}")
        logger.info(f"   Last updated: {data['last_updated']}")
        logger.info(f"   Models: {len(data['models'])}")

        # Clear cache to force reload
        global _models_cache
        _models_cache = None

        return True

    except urllib.error.URLError as e:
        logger.error(f"❌ Failed to fetch from GitHub: {e}")
        logger.error("   Check your internet connection or try again later.")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to update model metadata: {e}")
        return False


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost for a model call based on token usage.

    Args:
        model: Model name (e.g., "gpt-4o", "gpt-5", "o3-mini")
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    pricing_family = get_pricing_family(model)

    if not pricing_family:
        logger.warning(f"⚠️  Unknown model '{model}' - cannot calculate cost. Defaulting to $0.")
        return 0.0

    pricing = MODEL_PRICING[pricing_family]
    input_cost = (prompt_tokens * pricing["input"]) / 1_000_000
    output_cost = (completion_tokens * pricing["output"]) / 1_000_000

    return input_cost + output_cost


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1m 30s", "45.2s", "1h 5m 10s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    remaining_seconds = round(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"

    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {remaining_seconds}s"


@dataclass
class StepMetrics:
    """Metrics for a single pipeline step."""

    step_name: str
    step_type: str  # "llm", "function", "template"
    model: Optional[str] = None

    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    start_perf: float = field(default_factory=time.perf_counter)
    end_perf: Optional[float] = None
    duration: Optional[float] = None  # seconds

    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # MCP metrics
    mcp_calls: int = 0
    mcp_truncations: int = 0

    def __post_init__(self):
        """Auto-calculate total_tokens if not provided."""
        if self.total_tokens == 0 and (self.prompt_tokens or self.completion_tokens):
            self.total_tokens = int(self.prompt_tokens) + int(self.completion_tokens)

    def complete(self):
        """Mark step as complete and calculate duration."""
        self.end_time = datetime.now()
        self.end_perf = time.perf_counter()
        # perf_counter yields monotonic durations, avoiding clock skew in ordering
        self.duration = max(0.0, (self.end_perf - self.start_perf))

        # Calculate total tokens if not already set
        if self.total_tokens == 0 and (self.prompt_tokens or self.completion_tokens):
            self.total_tokens = int(self.prompt_tokens) + int(self.completion_tokens)

    def calculate_cost(self) -> float:
        """Calculate cost for this step.

        Returns:
            Cost in USD, or 0.0 for non-LLM steps or unknown models
        """
        if self.step_type != "llm" or not self.model:
            return 0.0

        return calculate_cost(self.model, self.prompt_tokens, self.completion_tokens)


@dataclass
class PipelineMetrics:
    """Aggregated metrics for entire pipeline."""

    pipeline_name: str
    steps: List[StepMetrics] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    @property
    def total_duration(self) -> float:
        """Total pipeline duration in seconds."""
        if not self.steps:
            return 0.0

        # Use actual step timings
        return sum(step.duration or 0.0 for step in self.steps)

    @property
    def wall_clock_duration(self) -> float:
        """Actual wall-clock time from start to end."""
        if self.end_time is None:
            return 0.0
        return max(0.0, (self.end_time - self.start_time).total_seconds())

    @property
    def total_cost(self) -> float:
        """Total cost across all steps."""
        return sum(step.calculate_cost() for step in self.steps)

    @property
    def total_tokens(self) -> int:
        """Total tokens across all steps."""
        return sum(step.total_tokens for step in self.steps)

    def add_step(self, step: StepMetrics):
        """Add a completed step to pipeline metrics."""
        self.steps.append(step)

    def get_slowest_steps(self, n: int = 3) -> List[StepMetrics]:
        """Get the N slowest steps.

        Args:
            n: Number of steps to return

        Returns:
            List of slowest steps, sorted by duration (descending)
        """
        return sorted(
            [s for s in self.steps if s.duration],
            key=lambda s: s.duration or 0,
            reverse=True
        )[:n]

    def get_cost_breakdown_by_model(self) -> Dict[str, float]:
        """Get cost breakdown by model.

        Returns:
            Dictionary mapping model name to total cost
        """
        breakdown = {}
        for step in self.steps:
            if step.model:
                cost = step.calculate_cost()
                breakdown[step.model] = breakdown.get(step.model, 0.0) + cost
        return breakdown


class TelemetryCollector:
    """Collect and report telemetry for pipeline execution."""

    def __init__(self, pipeline_name: str = "pipeline"):
        self.pipeline = PipelineMetrics(pipeline_name=pipeline_name)
        self.current_step: Optional[StepMetrics] = None

    def start_step(
        self,
        step_name: str,
        step_type: str,
        model: Optional[str] = None
    ):
        """Start timing a pipeline step.

        Args:
            step_name: Name of the step
            step_type: Type of step ("llm", "function", "template")
            model: Model name for LLM steps
        """
        self.current_step = StepMetrics(
            step_name=step_name,
            step_type=step_type,
            model=model
        )

    def end_step(
        self,
        step_name: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0
    ):
        """End timing for current step and record metrics.

        Args:
            step_name: Name of the step (for validation)
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            total_tokens: Total tokens (if provided directly)
        """
        if not self.current_step:
            return

        # Validate step name matches
        if self.current_step.step_name != step_name:
            raise ValueError(
                f"Step name mismatch: expected '{self.current_step.step_name}', got '{step_name}'"
            )

        # Update token counts
        self.current_step.prompt_tokens = prompt_tokens
        self.current_step.completion_tokens = completion_tokens
        if total_tokens:
            self.current_step.total_tokens = total_tokens

        # Complete and add to pipeline
        self.current_step.complete()
        self.pipeline.add_step(self.current_step)
        self.current_step = None

    def complete_pipeline(self):
        """Mark the overall pipeline end time."""
        self.pipeline.end_time = datetime.now()

    def record_mcp_call(
        self,
        tool_name: str,
        response_size: int,
        truncated: bool = False
    ):
        """Record an MCP tool call.

        Args:
            tool_name: Name of the tool called
            response_size: Size of response in characters
            truncated: Whether response was truncated
        """
        if not self.current_step:
            return

        self.current_step.mcp_calls += 1
        if truncated:
            self.current_step.mcp_truncations += 1

    def generate_summary(self) -> str:
        """Generate formatted summary of pipeline execution.

        Returns:
            Multi-line summary string
        """
        lines = []
        lines.append("")
        lines.append("📋 Pipeline Summary")
        lines.append("━" * 60)
        lines.append(f"Pipeline: {self.pipeline.pipeline_name}")
        lines.append(f"Total Duration: {format_duration(self.pipeline.total_duration)}")
        lines.append(f"Wall Clock: {format_duration(self.pipeline.wall_clock_duration)}")
        lines.append(f"Total Cost: ${self.pipeline.total_cost:.4f}")
        lines.append(f"Total Tokens: {self.pipeline.total_tokens:,}")
        lines.append("")

        if self.pipeline.steps:
            lines.append("⏱️ Step Timeline:")
            cumulative = 0.0
            for step in self.pipeline.steps:
                step_duration = step.duration or 0.0
                cumulative += step_duration
                model_info = f" ({step.model})" if step.model else ""
                lines.append(
                    f"  • {step.step_name}: {format_duration(step_duration)} | Cumulative {format_duration(cumulative)}{model_info}"
                )
            lines.append("")

        # Slowest steps
        slowest = self.pipeline.get_slowest_steps(n=5)
        if slowest:
            lines.append("🐌 Slowest Steps:")
            for i, step in enumerate(slowest, 1):
                model_info = f" ({step.model})" if step.model else ""
                lines.append(f"  {i}. {step.step_name}: {format_duration(step.duration or 0)}{model_info}")
            lines.append("")

        # Cost breakdown (nested by model → step/prompt)
        breakdown = self.pipeline.get_cost_breakdown_by_model()
        if breakdown:
            lines.append("💰 Cost Breakdown by Model:")
            total = self.pipeline.total_cost
            for model, model_cost in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
                model_pct = (model_cost / total * 100) if total > 0 else 0
                lines.append(f"  • {model}: ${model_cost:.4f} ({model_pct:.0f}%)")

                # Per-step breakdown for this model
                step_costs = []
                for step in self.pipeline.steps:
                    if step.model == model:
                        cost = step.calculate_cost()
                        if cost > 0:
                            step_costs.append((step.step_name, cost))

                # Sort steps by cost descending and print
                for step_name, cost in sorted(step_costs, key=lambda x: x[1], reverse=True):
                    step_pct = (cost / model_cost * 100) if model_cost > 0 else 0
                    lines.append(f"     - {step_name}: ${cost:.4f} ({step_pct:.0f}%)")

            lines.append("")

        # MCP stats
        total_mcp_calls = sum(s.mcp_calls for s in self.pipeline.steps)
        total_truncations = sum(s.mcp_truncations for s in self.pipeline.steps)
        if total_mcp_calls > 0:
            lines.append("🔧 MCP Tool Calls:")
            lines.append(f"  Total calls: {total_mcp_calls}")
            if total_truncations > 0:
                lines.append(f"  Truncations: {total_truncations} (saved tokens)")
            lines.append("")

        # Add footer note about updating model metadata
        version, last_updated = get_model_data_version()
        lines.append(f"ℹ️  Model data version {version} (updated {last_updated})")
        lines.append("   To ensure pricing/limits are current: sp registry update-models")
        lines.append("")

        return "\n".join(lines)


def generate_optimization_suggestions(
    steps: List[StepMetrics],
    mcp_max_iterations: Optional[int] = None,
    configured_max_tokens: Optional[int] = None
) -> List[str]:
    """Generate optimization suggestions based on step metrics.

    Args:
        steps: List of step metrics
        mcp_max_iterations: Configured max MCP iterations
        configured_max_tokens: Configured max_tokens limit

    Returns:
        List of suggestion strings
    """
    suggestions = []

    for step in steps:
        if step.step_type != "llm" or not step.model:
            continue

        # Suggest model downgrade if cost savings > 50%
        if step.model in ["gpt-5", "o1", "o1-preview"]:
            current_cost = step.calculate_cost()

            # Calculate alternative with gpt-4o
            alt_cost = calculate_cost("gpt-4o", step.prompt_tokens, step.completion_tokens)
            savings = current_cost - alt_cost
            savings_pct = (savings / current_cost * 100) if current_cost > 0 else 0

            if savings_pct > 50:
                suggestions.append(
                    f"💡 {step.step_name}: Consider gpt-4o instead of {step.model} "
                    f"(-${savings:.2f}, -{savings_pct:.0f}%) - test quality first"
                )

        # Suggest increasing MCP max_iterations if close to limit
        if mcp_max_iterations and step.mcp_calls > 0:
            utilization = step.mcp_calls / mcp_max_iterations
            if utilization > 0.9:
                suggestions.append(
                    f"⚠️  {step.step_name}: Using {step.mcp_calls}/{mcp_max_iterations} MCP iterations "
                    f"({utilization*100:.0f}%) - consider increasing max_iterations"
                )

        # Report truncation savings
        if step.mcp_truncations > 0:
            suggestions.append(
                f"✂️  {step.step_name}: {step.mcp_truncations} MCP responses truncated "
                f"(saved tokens and cost)"
            )

        # Suggest max_tokens reduction if consistently under-utilized
        if configured_max_tokens and step.completion_tokens > 0:
            utilization = step.completion_tokens / configured_max_tokens
            if utilization < 0.25:  # Using less than 25% of limit
                recommended = step.completion_tokens * 2  # 2x actual usage
                suggestions.append(
                    f"📉 {step.step_name}: Only using {step.completion_tokens}/{configured_max_tokens} "
                    f"tokens ({utilization*100:.0f}%) - could reduce max_tokens to {recommended}"
                )

    return suggestions
