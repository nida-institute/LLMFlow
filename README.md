# Scripture Pipelines

**Scripture Pipelines** is a declarative pipeline system for AI-assisted biblical and linguistic scholarship. Workflows are declared in YAML pipelines that specify information flow, prompt contracts, and output structure. The engine handles execution, validation, and persistence — every intermediate result is saved to disk, every LLM step can be required to account for its sources, and the same pipeline can be rerun with a revised prompt without re-querying earlier steps.

Biblical and linguistic scholarship now has more open data than it can use: word-level morphological annotations for the entire Hebrew Bible and Greek New Testament, syntactic treebanks, discourse feature datasets, lexicographic databases, documentary papyri and inscriptions. The bottleneck is not data — it is the human capacity to bring rigorous scholarly attention to bear on that data at scale. Scripture Pipelines is designed for that problem.

## An Opinionated Framework: The Human Commands

Scripture Pipelines is not neutral about who is in charge. The framework is built on a specific conviction: **Bible translation and biblical scholarship are best done by human beings**. This is not a modest claim about current AI limitations; it is a claim about the nature of the work. Translation creates community ownership. Biblical scholarship is the work of scholars whose training, judgment, and accountability to the academy and the church are not transferable to a language model. And beyond these specific domains: doing meaningful work together matters. The collaboration of a translation team, the exchange between a scholar and a dataset — these are not inefficiencies to be automated away.

The operating model is the **James Kirk model**: Captain Kirk commands the Enterprise; the crew and the ship's computer execute. The contrasting model is HAL 9000 — the AI that locks the crew out because it has concluded that the mission matters more than the people. HAL is not a villain; it is doing exactly what it was designed to do. Stuart Russell (*Human Compatible*, 2019) calls the distinguishing property **corrigibility**: an AI that remains genuinely uncertain about human preferences and therefore defers to humans for correction. The James Kirk model is corrigibility in practice.

Scripture Pipelines operationalizes this through four interlocking disciplines:

1. **Test-driven development** — approximately 2:1 test-to-production ratio. Writing the failing test first forces the human to own the specification before the AI touches it. Without a precise test, a model that ignores an inconvenient requirement produces code that compiles while silently failing.

2. **Explain before implementing** — every non-trivial change begins with the AI describing what it plans to do and which files it will modify, before any file is touched. Explanation commits the model to a specific interpretation that can be evaluated before any file is modified.

3. **Persistent context infrastructure** — each project carries `.github/copilot-instructions.md` (the AI's constitution: architecture patterns, pitfalls, what not to change) and `docs/ai-context/` (which data sources to trust, what the pipeline language supports, what work is in progress). These are active working constraints in every session, not documentation artifacts.

4. **Cross-repository choreography** — when a pipeline run reveals an error in an upstream dataset, the AI drafts a well-formed upstream issue, files it via the GitHub CLI, and records the issue number in `project/TODO.md`. The issue tracker is the communication bus. The AI is the correspondent. The human remains the architect.

## The Kairos Project

Scripture Pipelines is at the heart of the **[Kairos Project](https://nida.org)**, a NIDA Institute initiative to build a global community of scholars — spanning the Western academy and far beyond it — who want to serve Bible translation and the global church.

Part of what that means is providing information in the most useful form for communities that traditional scholarly resources were not built for: non-Western communities, oral cultures, and people who engage Scripture outside the academy. Most of these texts were written by and for oral storytelling cultures. Today's oral storytelling communities do not need PhDs from Western academia to read them. What they need is orientation to settings and cultures that are foreign to any world we live in now — and that orientation rarely looks like a journal article.

The Kairos Project takes a more inclusive approach: it trusts that readers in community can encounter the text directly and make genuine discoveries. The scholar's role is to equip that encounter, not to conduct it on the reader's behalf. It also builds resources for people who want to learn Greek or Hebrew, who want to understand what discourse analysis reveals about text structure, who want to climb into technical scholarship because the text draws them deeper. The goal is scaffolding at every level, with the ladder running in both directions: scholarly insight flows out and community questions flow back in. Everything produced is freely licensed.

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
sp setup        # choose OpenAI, Anthropic, or Google Gemini
sp models       # see available models and which keys are configured
```

See [INSTALL.md](INSTALL.md) for manual install steps and Gatekeeper/SmartScreen notes.

---

### Install via pip (for developers and power users)

```bash
pip install llmflow
```

Scripture Pipelines uses the [`llm`](https://llm.datasette.io/) package to call language models. By default it supports OpenAI. To use other providers, install the corresponding plugin:

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

Run `sp models` to see all available models and which keys you have configured.

### Install Scripture Pipelines as a Command-Line Tool

Scripture Pipelines is designed to work across multiple independent projects. Install it once, use it everywhere.

#### Development Installation (Recommended)

```bash
# Clone the Scripture Pipelines repository
git clone https://github.com/nida-institute/LLMFlow.git
cd LLMFlow

# Install in editable mode
pip install -e .

# Verify installation
sp --version
sp --help
```

#### Using Hatch (For Contributors)

```bash
# Install hatch if you haven't already
pip install hatch

# Enter the development environment
hatch shell

# Scripture Pipelines is now available
sp --version
```

### Working with Multiple Projects

Once installed, `sp` works seamlessly across different project repositories:

```bash
# Lexicon project
cd ~/github/biblical-lexicon
sp run --pipeline pipelines/lexicon-generation.yaml

# Exegetical guides project
cd ~/github/exegetical-guides
sp run --pipeline pipelines/storyflow.yaml

# Translation notes project
cd ~/github/translation-notes
sp run --pipeline pipelines/note-generation.yaml
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
mkdir ~/github/my-new-sp-project
cd ~/github/my-new-sp-project
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
sp.log
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
sp run --pipeline pipelines/example.yaml
```

### Available Commands

```bash
# Run a pipeline
sp run --pipeline pipelines/your-pipeline.yaml

# Dry run (preview without execution)
sp run --pipeline pipelines/your-pipeline.yaml --dry-run

# Validate a pipeline
sp lint pipelines/your-pipeline.yaml

# Set variables from command line
sp run --pipeline pipelines/your-pipeline.yaml --var key=value

# Show version
sp --version

# Get help
sp --help
```

### Global Conventions & Skills

LLMFlow provides globally-shared resources that improve prompt engineering quality and AI assistant effectiveness:

**Prompt Organization Convention** (`~/.sp/conventions/`)
- Standard structure for `.gpt` prompt files
- Enforces verifiable input → output transformations
- Co-locates rules, examples, and data sources
- Provides length guidelines and complexity categories

**Audit Prompts Skill** (`~/.sp/skills/audit-prompts/`)
- VS Code Copilot skill for auditing `.gpt` files
- Checks convention compliance, sprawl detection
- **Critical:** Verifies input data grounding (prevents hallucination)
- **Critical:** Flags AI-generated examples (biggest source of drift)

These are automatically installed when you run `sp init`. See [Global Conventions & Skills](docs/global-conventions.md) for complete documentation.

**Quick usage:**
```bash
# Initialize a project (installs global resources)
sp init

# Audit a prompt file (in VS Code with Copilot)
@audit-prompts Check prompts/my-prompt.gpt
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

1. **Keep Scripture Pipelines Updated**: Periodically update your Scripture Pipelines installation:
   ```bash
   cd ~/github/scripture-pipelines
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

**Important:** When asking for help with Scripture Pipelines pipelines, reference [`docs/GPT_CONTEXT.md`](docs/GPT_CONTEXT.md)

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
