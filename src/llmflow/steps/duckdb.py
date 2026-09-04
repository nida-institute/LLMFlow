"""DuckDB step handler."""

import time
from pathlib import Path
from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def run_duckdb_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> Any:
    """Execute a DuckDB query step and return its result."""
    try:
        import duckdb

        # Imported to check availability, not to use here: duckdb converts results via pandas,
        # so a missing pandas must fail with the message below rather than mid-query.
        import pandas as pd  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "DuckDB step requires 'duckdb' package. "
            "Install with: pip install duckdb>=1.0.0"
        ) from e

    name = step.get("name", "unnamed_duckdb_step")
    query_file_path = step.get("query_file")
    inputs = step.get("inputs", {})
    output_format = step.get("format", "records")

    if not query_file_path:
        raise ValueError(f"DuckDB step '{name}' missing required 'query_file' parameter")

    logger.info(f"🦆 Starting DuckDB step: {name}")
    logger.debug(f"Query file: {query_file_path}")

    telemetry = pipeline_config.get("_telemetry") if pipeline_config else None
    if telemetry:
        telemetry.start_step(name, "duckdb")

    query_path = Path(query_file_path)
    if not query_path.is_absolute():
        queries_dir = Path(context.get("queries_dir", "queries"))
        query_path = queries_dir / query_path

    if not query_path.exists():
        raise FileNotFoundError(
            f"DuckDB query file not found: {query_path}\n"
            f"Looked in: {query_path.absolute()}"
        )

    logger.debug(f"Loading query from: {query_path}")
    query_template = query_path.read_text(encoding="utf-8")

    resolved_inputs = {}
    if isinstance(inputs, dict):
        for key, value in inputs.items():
            resolved_inputs[key] = resolve(value, context)
            logger.debug(f"Resolved input '{key}': {resolved_inputs[key]}")

    extended_context = {**context, **resolved_inputs}
    resolved_query = resolve(query_template, extended_context)
    logger.debug(f"Resolved query preview: {resolved_query[:200]}...")

    try:
        start_time = time.time()
        conn = duckdb.connect(":memory:")
        result_df = conn.execute(str(resolved_query)).fetchdf()
        conn.close()
        execution_time = time.time() - start_time
        row_count = len(result_df)
        logger.info(f"📊 Query returned {row_count} rows in {execution_time:.2f}s")
        if telemetry:
            telemetry.record_metric("query_execution_time", execution_time)
            telemetry.record_metric("rows_returned", row_count)
    except Exception as e:
        logger.error(f"DuckDB query execution failed: {e}")
        logger.debug(f"Query that failed:\n{resolved_query}")
        if telemetry:
            telemetry.end_step(error=str(e))
        raise

    if output_format == "records":
        result = result_df.to_dict("records")
    elif output_format == "dict":
        result = result_df.to_dict("list")
    elif output_format == "json":
        result = result_df.to_json(orient="records")
    elif output_format == "dataframe":
        result = result_df
    else:
        logger.warning(f"Unknown format '{output_format}', defaulting to 'records'")
        result = result_df.to_dict("records")

    handle_step_outputs(step, result, context)

    if telemetry:
        telemetry.end_step()

    logger.info(f"✅ Completed DuckDB step: {name}")
    return result
