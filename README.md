# LLMFlow

**LLMFlow** is a declarative pipeline system for building workflows powered by large language models (LLMs). It allows you to structure and automate prompts, responses, and output generation across a series of steps — with optional scene-based iteration, variable injection, and file generation.

## 🔧 Installation

LLMFlow is a Python project that uses [Hatch](https://hatch.pypa.io/) for packaging and environment management.

```bash
git clone https://github.com/nida-institute/LLMFlow.git
cd LLMFlow
hatch env create
```

## 🚀 Running a Pipeline

To run a pipeline:

```bash
hatch run llmflow run --pipeline pipelines/storyflow.yaml --var passage="Psalm 23"
```

### Options

- `--pipeline`: Path to an LLMFlow YAML file (default: `pipelines/storyflow.yaml`)
- `--var`: Inject variables (e.g. `--var passage="John 15"`). Repeatable.
- `--dry_run`: Show the steps without executing them.

## 🧠 What Is an LLMFlow?

An **LLMFlow** is a YAML file that defines:
- The pipeline name
- Input variables
- A series of declarative steps (`rules`) including LLM calls, iteration, and output saving

See [`llmflow-language.md`](llmflow-language.md) for full reference.
