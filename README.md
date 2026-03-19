# LLMFlow

**LLMFlow** is a declarative pipeline system for building workflows powered by large language models (LLMs). It allows you to structure and automate prompts, responses, and output generation across a series of steps — with optional scene-based iteration, variable injection, and file generation.

## Installation

### Quick Install (no Python required)

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/nida-institute/LLMFlow/main/install.ps1 | iex
```

Then configure your API key:

```bash
llmflow setup        # choose OpenAI, Anthropic, or Google Gemini
llmflow models       # see available models and which keys are configured
```

See [INSTALL.md](INSTALL.md) for manual install steps and Gatekeeper/SmartScreen notes.

---

### Install via pip (for developers and power users)

```bash
pip install llmflow
```

LLMFlow uses the [`llm`](https://llm.datasette.io/) package to call language models. By default it supports OpenAI. To use other providers, install the corresponding plugin:

```bash
pip install llm-anthropic   # Anthropic Claude
pip install llm-gemini      # Google Gemini
pip install llm-ollama      # Local models via Ollama
# Full plugin list: https://llm.datasette.io/en/stable/plugins/directory.html
```

Set your API key for each provider:

```bash
llm keys set openai
llm keys set anthropic
llm keys set gemini
```

Then use the model name directly in your pipeline YAML:

```yaml
steps:
  - name: generate
    type: llm
    model: claude-3-5-sonnet-20241022   # Anthropic
    # model: gemini-2.0-flash           # Gemini
    # model: ollama/llama3              # Local via Ollama
```

Run `llmflow models` to see all available models and which keys you have configured.

### Install LLMFlow as a Command-Line Tool

LLMFlow is designed to work across multiple independent projects. Install it once, use it everywhere.

#### Development Installation (Recommended)

```bash
# Clone the LLMFlow repository
git clone https://github.com/nida-institute/LLMFlow.git
cd LLMFlow

# Install in editable mode
pip install -e .

# Verify installation
llmflow --version
llmflow --help
```

#### Using Hatch (For Contributors)

```bash
# Install hatch if you haven't already
pip install hatch

# Enter the development environment
hatch shell

# LLMFlow is now available
llmflow --version
```

### Working with Multiple Projects

Once installed, `llmflow` works seamlessly across different project repositories:

```bash
# Lexicon project
cd ~/github/biblical-lexicon
llmflow run --pipeline pipelines/lexicon-generation.yaml

# Exegetical guides project
cd ~/github/exegetical-guides
llmflow run --pipeline pipelines/storyflow.yaml

# Translation notes project
cd ~/github/translation-notes
llmflow run --pipeline pipelines/note-generation.yaml
```

Each project repository maintains its own:
- **Pipeline configurations** (`pipelines/*.yaml`)
- **Templates** (`templates/*.md`)
- **Prompts** (`prompts/*.md`)
- **Outputs** (`outputs/*/`)
- **Git history and version control**

This keeps each project's artifacts separate and independently versioned.

### Recommended Project Structure

Each of your project repositories should follow this structure:

```
your-project-repo/
├── .gitignore                 # Ignore outputs/, .env, etc.
├── README.md                  # Project-specific documentation
├── pipelines/
│   └── your-pipeline.yaml    # Your pipeline definition
├── templates/
│   └── your-template.md      # Output templates
├── prompts/
│   └── step1.md              # LLM prompt files
├── outputs/                   # Generated artifacts (git-ignored)
│   └── leaders_guide/
│       └── *.md
└── .env                       # API keys (git-ignored, optional)
```

### Example: Setting Up a New Project

```bash
# Create a new project repository
mkdir ~/github/my-new-llmflow-project
cd ~/github/my-new-llmflow-project
git init

# Create the basic structure
mkdir -p pipelines templates prompts outputs

# Add .gitignore
cat > .gitignore << 'EOF'
# Outputs (generated artifacts)
outputs/

# Environment files
.env
*.env

# Python
__pycache__/
*.pyc
.pytest_cache/

# Logs
*.log
llmflow.log
EOF

# Create your first pipeline
cat > pipelines/example.yaml << 'EOF'
name: example-pipeline
vars:
  output_dir: outputs

steps:
  - name: generate_content
    type: llm
    # ... your step configuration
EOF

# Run your pipeline
llmflow run --pipeline pipelines/example.yaml
```

### Available Commands

```bash
# Run a pipeline
llmflow run --pipeline pipelines/your-pipeline.yaml

# Dry run (preview without execution)
llmflow run --pipeline pipelines/your-pipeline.yaml --dry-run

# Validate a pipeline
llmflow lint pipelines/your-pipeline.yaml

# Set variables from command line
llmflow run --pipeline pipelines/your-pipeline.yaml --var key=value

# Show version
llmflow --version

# Get help
llmflow --help
```

### Example Projects

Here are some example project types and their typical structures:

#### Exegetical Guides Project

```
~/github/exegetical-guides/
├── pipelines/
│   └── storyflow.yaml
├── templates/
│   └── leadersguide_scene_template.md
├── prompts/
│   ├── step1_body.md
│   ├── step2_heart.md
│   └── step3_speak.md
└── outputs/
    └── leaders_guide/
        └── 42001057-42001057_leaders_guide.md
```

#### Biblical Lexicon Project

```
~/github/biblical-lexicon/
├── pipelines/
│   └── lexicon-generation.yaml
├── templates/
│   └── lexicon_entry.md
├── prompts/
│   ├── define_word.md
│   └── find_usage.md
└── outputs/
    └── lexicon/
        └── greek_entries/
```

#### Translation Notes Project

```
~/github/translation-notes/
├── pipelines/
│   └── note-generation.yaml
├── templates/
│   └── translation_note.md
├── prompts/
│   └── create_note.md
└── outputs/
    └── notes/
        └── matthew/
```

### Tips for Multi-Project Workflow

1. **Keep LLMFlow Updated**: Periodically update your LLMFlow installation:
   ```bash
   cd ~/github/LLMFlow
   git pull
   pip install -e .
   ```

2. **Version Control**: Each project should have its own git repository:
   ```bash
   git add pipelines/ templates/ prompts/
   git commit -m "Add pipeline configuration"
   git push
   ```

3. **Ignore Outputs**: Add `outputs/` to `.gitignore` in each project to avoid committing generated files.

4. **Share Configurations**: If multiple projects use similar pipelines, consider:
   - Creating a shared template repository
   - Symlinking common templates
   - Using git submodules for shared resources

5. **Environment Variables**: Use `.env` files in each project for project-specific API keys or settings.

## 🤖 Working with AI Assistants (GitHub Copilot, Claude, ChatGPT)

**Important:** When asking for help with LLMFlow pipelines, reference [`docs/GPT_CONTEXT.md`](docs/GPT_CONTEXT.md)

This file contains comprehensive documentation about:
- Pipeline structure and syntax
- Variable substitution rules (`${var}` in YAML vs `{{var}}` in prompt templates)
- Step types (llm, plugin, function, for_each)
- Common patterns and examples
- Troubleshooting guide

**VSCode Users:** This project includes workspace settings that suggest referencing GPT_CONTEXT.md in Copilot Chat conversations.

**Syntax Quick Reference:**
```yaml
# In pipeline YAML - use ${var}
inputs:
  text: "${source_text}"

# In prompt templates - use {{var}}
Process this: {{text}}
```

### Prompt File Format (`.gpt`)

Variables use `{{variable}}` double curly brace syntax:

```
<!--
prompt:
  requires:
    - passage
    - scene
  optional: []
-->

Analyze {{passage}} using {{scene}}.
```

Variable substitution is handled by the `llm` package.

### Template File Format (`.md`)

Variables use `{{variable}}` or `${variable}` syntax:

```markdown
# {{passage}} Guide

Context: ${context.background}
```

Variable substitution is handled by `render_markdown_template()`.

## License

Copyright 2025 Biblica, Inc.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
