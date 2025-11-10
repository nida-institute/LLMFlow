# LLMFlow — Project TL;DR

LLMFlow is a framework for orchestrating reasoning and transformation pipelines with language models.  
It treats code, data, and prompts as one flow of interpretation — bridging developer logic and narrative design.

## Essence
- **Purpose:** Compose and execute structured LLM pipelines defined in YAML or Python.
- **Philosophy:** Code as conversation — declarative pipelines mirror how humans layer thought, memory, and context.
- **Core idea:** “Flow” is a graph of steps (tasks, transforms, or evaluators), each defined declaratively with input/output bindings.

## Key Components
- **`llmflow-language.md`** — The grammar of LLMFlow YAML: steps, vars, inputs, outputs, and evaluation.
- **`architecture.md`** — Module structure, execution engine, and lifecycle.
- **`GPT_CONTEXT.md`** — The canonical “mindset” file for GPTs and Claude; defines design tone and vocabulary.
- **`tutorial.md`** — Hands-on intro showing a working pipeline.
- **`why-LLMFlow.md`** — Explains the philosophy: why flows instead of raw prompt chaining.

## Developer View
- Runs on Python 3.10+ with Pydantic for schema validation.
- Compatible with Pyright for static typing.
- Extendable via custom step types and adapters.
- Typical run: `python -m llmflow <flow.yaml>`

## Design Ethos
- Embodied clarity: pipeline YAML is a human-readable record of thought.
- Separation of *description* (YAML) and *execution* (Python runtime).
- Every flow can be narrated, inspected, and versioned as a living document.

This project sits where engineering meets hermeneutics — it codes the way we think.
