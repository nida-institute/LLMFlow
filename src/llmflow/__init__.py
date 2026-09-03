"""LLMFlow / Scripture Pipelines.

Public Python API. These names are the supported surface for programs that embed the
engine — kept stable and backed by the same code the runner uses, so callers never
re-derive what the engine already resolves (see LLMFlow public-API epic).
"""
from typing import TYPE_CHECKING, Any

from llmflow.catalog import api_catalog
from llmflow.model import Pipeline, ResolvedPipeline, Step, load_pipeline
from llmflow.pipeline_schema import PIPELINE_SCHEMA

if TYPE_CHECKING:  # lazy at runtime (see __getattr__), to keep `import llmflow` light
    from llmflow.books import resolve as resolve_book  # noqa: F401
    from llmflow.modules.telemetry import get_model_metadata as model_metadata  # noqa: F401
    from llmflow.utils.data import parse_bible_reference  # noqa: F401
    from llmflow.utils.llm_runner import call_llm  # noqa: F401

__all__ = [
    # object model
    "load_pipeline",
    "Pipeline",
    "ResolvedPipeline",
    "Step",
    # direct model access (#175) — imported lazily
    "call_llm",
    # utilities — imported lazily
    "parse_bible_reference",
    "resolve_book",
    "model_metadata",
    # published machine-readable mapping (Decision 2)
    "PIPELINE_SCHEMA",
    "api_catalog",
]


def __getattr__(name: str) -> Any:
    # Lazy exports keep `import llmflow` from pulling heavy deps (the `llm` package, etc.).
    if name == "call_llm":
        from llmflow.utils.llm_runner import call_llm

        return call_llm
    if name == "parse_bible_reference":
        from llmflow.utils.data import parse_bible_reference

        return parse_bible_reference
    if name == "resolve_book":
        from llmflow.books import resolve as resolve_book

        return resolve_book
    if name == "model_metadata":
        from llmflow.modules.telemetry import get_model_metadata

        return get_model_metadata
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
