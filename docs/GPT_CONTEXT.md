# LLMFlow System Context for AI Assistants

**For AI assistants helping with LLMFlow development and pipelines.**
This file provides comprehensive context about LLMFlow's architecture,
conventions, and common patterns.

## What is LLMFlow?

LLMFlow is a YAML-based pipeline orchestration tool designed for LLM-powered workflows. It enables users to chain together LLM calls, data processing, file operations, and custom functions into reproducible pipelines.

**Key Features:**

- YAML-based pipeline definitions
- Multiple LLM provider support (OpenAI, Anthropic, etc.)
- Plugin system for extensibility
- Template-based prompts with variable substitution
- Data processing (XML/XPath, TSV, JSON)
- Validation and linting

## For Users Getting Help

To get effective help from GPT when creating or debugging pipelines:

1. **Share your pipeline YAML file** (e.g., `pipelines/my-pipeline.yaml`)
2. **Share any error messages** from the terminal
3. **Share the log file** (`llmflow.log` in your project directory)
4. **Describe what you want to achieve** in plain language
5. **Share this context file** so GPT understands LLMFlow

**Quick Command:** Run `llmflow context` to generate this file automatically.

## Documentation Resources

- **This file (GPT_CONTEXT.md)**: Conceptual guide with pipeline patterns and examples
- **docs/index.json**: Complete function reference with 1052 functions across 118 modules
  - Auto-generated from source code
  - Shows function signatures, parameters, and locations
  - Use for quick lookup of available utilities and APIs
- **docs/index.signatures.json**: Detailed signature data for tooling integration

---

## Pipeline Structure Reference

### Complete Pipeline Template

```yaml
name: my-pipeline

description: |
  What this pipeline does and why.

  Examples:
    llmflow run --pipeline pipelines/my-pipeline.yaml --var input="value"
    llmflow run --pipeline pipelines/my-pipeline.yaml --var file="data.txt"

  Outputs:
    - Results are saved to outputs/
    - Logs are written to llmflow.log

variables:
  prompts_dir: prompts         # Where prompt templates live
  output_dir: outputs          # Where results are saved
  custom_var: "some value"     # Any custom variables

llm_config:                    # Optional: default LLM settings
  provider: openai
  model: gpt-4o
  max_tokens: 4000
  temperature: 0.7

linter_config:                 # Optional: validation settings
  enabled: true
  treat_warnings_as_errors: false

steps:
  - name: step-name
    type: step-type
    # ... step-specific configuration
```

### Required Fields

Every pipeline must have:
- `name`: Unique identifier for the pipeline
- `steps`: Array of at least one step

Every step must have:
- `name`: Unique identifier within the pipeline
- `type`: One of the available step types

---

## Step Types Reference

### 1. LLM Step

Calls a language model with a prompt template.

```yaml
- name: generate-content
  type: llm
  model: gpt-4o              # Optional if set in llm_config
  temperature: 0.7           # Optional (default: 0.7)
  max_tokens: 4000           # Optional (default: 4000)
  prompt:
    file: my-prompt.md       # Relative to prompts_dir
    inputs:                  # Variables to pass to template
      text: "${input_text}"
      context: "${background_info}"
  outputs:
    - result                 # Store response in ${result}
  saveas: outputs/result.txt # Optional: save to file
  log: info                  # Optional: debug, info, warning, error
```

**Prompt Template Format:**

```markdown
<!--
prompt:
  requires:
    - text
    - context
  format: markdown
  description: Brief description with {variables} in metadata
-->

# Task Description

Process this text: {{text}}

Background: {{context}}
```

**Template Syntax:**
- **YAML frontmatter**: Use `{variable}` in metadata fields (description, etc.)
- **Template body**: Use `{{variable}}` for substitution in the actual prompt text
- Both syntaxes are supported and will be replaced with actual values

### 2. Function Step

Calls a Python function from a module.

```yaml
- name: process-data
  type: function
  function: mymodule.process_text  # Import path
  inputs:
    - "${input_text}"              # Positional arguments as list
    - "${options}"
  outputs:
    - processed                    # Store return value
```

**Alternative dict syntax for named arguments:**

```yaml
inputs:
  text: "${input_text}"
  options: "${settings}"
```

### 3. For-Each Step

Loops over a list, executing nested steps for each item.

```yaml
- name: process-items
  type: for-each
  input: "${items}"           # List to iterate over
  item_var: item              # Variable name for current item
  steps:
    - name: process-one
      type: llm
      prompt:
        file: process-item.md
        inputs:
          content: "${item}"  # Access current item
      outputs:
        - result
      append_to: all_results  # Collect results across iterations
```

**Accessing item properties:**
- For objects: `${item.property}` or `${item[property]}`
- For TSV rows: `${item[column_name]}`
- For lists: `${item}` (the item itself)

### 4. XPath Step (Plugin)

Queries XML documents using XPath.

```yaml
- name: find-entries
  type: xpath
  inputs:                     # All params go in inputs dict
    path: data/file.xml
    xpath: //entry[@key='${search_term}']
    output_format: xml-string # xml-string, text, or count
    namespaces:               # Optional: XML namespaces
      tei: "http://www.tei-c.org/ns/1.0"
  outputs:
    - entries                 # List of matching elements
  log: debug
```

### 5. TSV Step (Plugin)

Reads TSV (tab-separated values) files.

```yaml
- name: load-data
  type: tsv
  inputs:
    path: data/input.tsv
    filter:                   # Optional: filter rows
      column: status
      value: active
  outputs:
    - rows                    # List of row dictionaries
```

**Accessing TSV data:**

```yaml
- name: process-rows
  type: for-each
  input: "${rows}"
  item_var: row
  steps:
    - name: use-row-data
      type: llm
      prompt:
        inputs:
          lemma: "${row[lemma]}"      # Use bracket notation
          gloss: "${row[gloss]}"
```

### 6. Echo Step

Prints messages to the console.

```yaml
- name: show-progress
  type: echo
  inputs:
    message: "Processing ${item.name}..."
```

### 7. Log Step

Writes messages to the log file.

```yaml
- name: log-status
  type: log
  inputs:
    message: "Completed ${step_name}"
    level: info              # debug, info, warning, error
```

---

## Variable Substitution

LLMFlow uses `${variable}` syntax for variable substitution:

### Basic Variables
```yaml
variables:
  name: "World"

steps:
  - name: greet
    type: echo
    inputs:
      message: "Hello, ${name}!"  # → "Hello, World!"
```

### Object Properties
```yaml
# Using dot notation
"${user.name}"           # → value of user['name']
"${config.api.key}"      # → nested property

# Using bracket notation
"${user[name]}"          # → same as user.name
"${row[column_name]}"    # → for TSV rows
```

### List Access
```yaml
"${items[0]}"            # → first item
"${results[-1]}"         # → last item
```

### Command-Line Variables
```bash
llmflow run --pipeline my-pipeline.yaml --var passage="Psalm 23"
```

```yaml
variables:
  passage: "${passage}"  # Set from command line
```

---

## Common Patterns

### Pattern 1: Chain LLM Calls

```yaml
steps:
  - name: analyze
    type: llm
    prompt:
      file: analyze.md
      inputs:
        text: "${input}"
    outputs:
      - analysis

  - name: summarize
    type: llm
    prompt:
      file: summarize.md
      inputs:
        analysis: "${analysis}"  # Use output from previous step
    outputs:
      - summary
```

### Pattern 2: Process List and Collect Results

```yaml
steps:
  - name: load-items
    type: tsv
    inputs:
      path: data.tsv
    outputs:
      - items

  - name: process-each
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: process-one
        type: llm
        prompt:
          file: process.md
          inputs:
            data: "${item[column]}"
        outputs:
          - result
        append_to: all_results  # Builds list across iterations
        saveas: "outputs/${item[id]}.txt"  # Dynamic filename
```

### Pattern 3: Conditional Processing

```yaml
steps:
  - name: check-status
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: process-if-active
        type: llm
        condition: "${item[status]} == 'active'"  # Only runs if true
        prompt:
          file: process.md
```

### Pattern 4: Multi-Step Data Pipeline

```yaml
steps:
  - name: load-xml
    type: xpath
    inputs:
      path: data.xml
      xpath: //entry
    outputs:
      - entries

  - name: process-entries
    type: for-each
    input: "${entries}"
    item_var: entry
    steps:
      - name: extract-data
        type: function
        function: mymodule.parse_entry
        inputs:
          - "${entry}"
        outputs:
          - parsed

      - name: generate-content
        type: llm
        prompt:
          file: expand.md
          inputs:
            data: "${parsed}"
        outputs:
          - expanded
        saveas: "outputs/${parsed[id]}.md"
```

---

## File Organization

```
my-project/
├── pipelines/
│   ├── pipeline1.yaml
│   └── pipeline2.yaml
├── prompts/
│   ├── analyze.md
│   └── summarize.md
├── inputs/
│   └── data.tsv
├── outputs/
│   └── (generated files)
├── llmflow.log
└── .env                 # API keys (not in git)
```

---

## Troubleshooting Guide

### Variable Not Resolving

**Problem:** `${variable}` appears as literal text instead of being replaced.

**Solutions:**
- **In YAML config**: Use `${var}` for pipeline variables
- **In prompt templates**: Use `{{var}}` in the template body
- **In prompt metadata**: Use `{var}` in YAML frontmatter descriptions
- Check syntax: Use `${var}`, not `$var`, `{var}`, or `{{var}}` in YAML
- For objects: Try both `${obj.prop}` and `${obj[prop]}`
- For TSV rows: Always use `${row[column]}`, not `${row.column}`
- Check variable is defined in `variables:` or created by previous step

**Example:**
```yaml
# ❌ Wrong in YAML
"$variable"
"{variable}"
"{{variable}}"

# ✅ Correct in YAML
"${variable}"

# ✅ Correct in prompt template body
"{{variable}}"

# ✅ Correct in prompt frontmatter description
description: "Processes {variable} from the input"
```

### LLM Step Failing

**Problem:** LLM step produces error or unexpected output.

**Check:**
1. Prompt file exists in `prompts_dir`
2. All required variables in prompt are provided in `inputs:`
3. Model name is valid (e.g., `gpt-4o`, `claude-sonnet-4.5`)
4. API key is set in environment (`.env` file or environment variable)
5. Variable values are correct type (string, list, dict)

**Example:**
```yaml
# Prompt requires 'text' and 'context'
prompt:
  file: analyze.md
  inputs:
    text: "${input_text}"      # ✅ Provided
    # ❌ Missing 'context'
```

### File Not Saving

**Problem:** `saveas:` doesn't create expected file.

**Solutions:**
- Ensure directory exists or create it in variables
- Check file path is valid and writable
- Use forward slashes `/` even on Windows
- For dynamic filenames, ensure variable exists

**Example:**
```yaml
# ✅ Static path
saveas: outputs/result.txt

# ✅ Dynamic path
saveas: "outputs/${item[id]}.txt"

# ❌ Directory doesn't exist
saveas: nonexistent/result.txt
```

### For-Each Loop Issues

**Problem:** Loop not iterating correctly or items not accessible.

**Solutions:**
- Verify `input:` is a list (check previous step output)
- Use correct syntax for item access (`${item}` or `${item[prop]}`)
- For TSV: Use `${item[column_name]}` with brackets
- Check `item_var:` doesn't conflict with existing variable

**Example:**
```yaml
# ✅ Correct TSV access
- name: process-rows
  type: for-each
  input: "${rows}"
  item_var: row
  steps:
    - name: use-data
      type: echo
      inputs:
        message: "${row[lemma]}"  # Use brackets

# ❌ Wrong - dot notation doesn't work for TSV
message: "${row.lemma}"
```

### XPath Not Finding Elements

**Problem:** XPath query returns empty list.

**Solutions:**
- Check XML file path is correct
- Verify namespaces are declared (required for namespaced XML)
- Test XPath in an XML editor first
- Use `output_format: count` to debug

**Example:**
```yaml
# ✅ With namespace
inputs:
  xpath: //tei:entry[@key='λόγος']
  namespaces:
    tei: "http://www.tei-c.org/ns/1.0"

# ❌ Missing namespace declaration
inputs:
  xpath: //tei:entry[@key='λόγος']
  # No namespaces defined
```

### Linter Errors

**Problem:** Pipeline fails validation before running.

**Common issues:**
- `append_to` without `outputs:` - add outputs field
- Missing `name` or `type` in step
- Invalid step type
- Prompt file doesn't exist
- Required prompt variables not provided

**Example:**
```yaml
# ❌ append_to without outputs
- name: collect
  type: llm
  append_to: results

# ✅ Fixed
- name: collect
  type: llm
  outputs: [result]
  append_to: results
```

---

## Environment Setup

### API Keys

Create `.env` file in project root:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Never commit `.env` to git!** Add to `.gitignore`:

```
.env
llmflow.log
outputs/
```

### Installation

```bash
# Install LLMFlow
pip install llmflow

# Or from source
cd LLMFlow
pip install -e .
```

---

## Running Pipelines

### Basic Usage

```bash
# Run a pipeline
llmflow run --pipeline pipelines/my-pipeline.yaml

# With custom variables
llmflow run --pipeline pipelines/my-pipeline.yaml --var input="text"

# Verbose output
llmflow run --pipeline pipelines/my-pipeline.yaml --verbose

# Dry run (validate without executing)
llmflow run --pipeline pipelines/my-pipeline.yaml --dry-run
```

### Validation

```bash
# Lint pipeline before running
llmflow lint pipelines/my-pipeline.yaml

# Show pipeline info
llmflow info pipelines/my-pipeline.yaml
```

---

## Example Pipelines

### Example 1: Simple Text Processing

```yaml
name: summarize-text

description: |
  Summarize input text using GPT-4.

  Usage:
    llmflow run --pipeline pipelines/summarize.yaml --var input="Long text..."

variables:
  prompts_dir: prompts

steps:
  - name: summarize
    type: llm
    model: gpt-4o
    prompt:
      file: summarize.md
      inputs:
        text: "${input}"
    outputs:
      - summary
    saveas: outputs/summary.txt
```

### Example 2: Multi-Step with Data

```yaml
name: process-lexicon

description: |
  Process lexicon entries from TSV and expand with LLM.

  Usage:
    llmflow run --pipeline pipelines/lexicon.yaml

variables:
  prompts_dir: prompts
  data_file: data/lexicon.tsv

steps:
  - name: load-entries
    type: tsv
    inputs:
      path: "${data_file}"
      filter:
        column: status
        value: ready
    outputs:
      - entries

  - name: process-entries
    type: for-each
    input: "${entries}"
    item_var: entry
    steps:
      - name: expand-entry
        type: llm
        model: gpt-4o
        prompt:
          file: expand-lexicon.md
          inputs:
            lemma: "${entry[lemma]}"
            gloss: "${entry[gloss]}"
        outputs:
          - expanded
        saveas: "outputs/${entry[lemma]}.md"
        append_to: all_entries
```

### Example 3: XML Processing Pipeline

```yaml
name: process-tei-xml

description: |
  Extract and process entries from TEI XML.

variables:
  prompts_dir: prompts

steps:
  - name: find-entries
    type: xpath
    inputs:
      path: data/dictionary.xml
      xpath: //tei:entry
      namespaces:
        tei: "http://www.tei-c.org/ns/1.0"
    outputs:
      - entries

  - name: process-each-entry
    type: for-each
    input: "${entries}"
    item_var: entry
    steps:
      - name: extract-lemma
        type: function
        function: mymodule.extract_lemma
        inputs:
          - "${entry}"
        outputs:
          - lemma

      - name: generate-content
        type: llm
        prompt:
          file: expand-entry.md
          inputs:
            xml: "${entry}"
            lemma: "${lemma}"
        outputs:
          - content
        saveas: "outputs/${lemma}.md"
```

---

## Plugin Development

### Creating a Plugin

```python
# myproject/plugins/my_plugin.py

def process_data(inputs, context):
    """
    Custom plugin function.

    Args:
        inputs: Dict with parameters from YAML 'inputs:'
        context: Pipeline context with variables

    Returns:
        Result that will be stored in step's 'outputs:'
    """
    param1 = inputs.get('param1')
    param2 = inputs.get('param2')

    # Your processing logic
    result = do_something(param1, param2)

    return result
```

### Using the Plugin

```yaml
steps:
  - name: use-plugin
    type: my_plugin
    inputs:
      param1: "value1"
      param2: "${variable}"
    outputs:
      - result
```

---

## Tips for GPT When Helping Users

1. **Always ask for the pipeline YAML** - Don't guess at structure
2. **Check variable substitution carefully** - Common source of errors
3. **Verify file paths exist** - Relative to where pipeline runs
4. **Explain the flow** - Help users understand how data moves through steps
5. **Show before/after examples** - Make changes clear
6. **Test XPath separately** - XML queries are tricky
7. **Check TSV column names** - Must match exactly, use brackets
8. **Validate outputs exist** - Before they're used as inputs
9. **Consider the loop context** - Variables inside for-each have different scope
10. **Suggest dry-run first** - `--dry-run` catches many issues

---

## Common Questions

**Q: How do I debug variable substitution?**
A: Add `log: debug` to steps and check `llmflow.log`. Also use `--verbose` flag.

**Q: Can I use multiple LLM providers?**
A: Yes, set `provider:` and `model:` per step, or use `llm_config:` for defaults.

**Q: How do I handle errors in loops?**
A: Currently, errors stop the pipeline. Use `condition:` to skip problematic items.

**Q: Can I call external APIs?**
A: Yes, create a function plugin that calls the API.

**Q: How do I process very large files?**
A: Use `for-each` with filtering, or create a plugin that streams data.

**Q: Can I use Jinja2 templates?**
A: Prompts use `{{variable}}` syntax similar to Jinja2, but it's a simpler system.

---

## Getting More Help

- Check the log file: `llmflow.log`
- Run with verbose: `llmflow run --pipeline ... --verbose`
- Validate first: `llmflow lint pipelines/my-pipeline.yaml`
- Share complete error messages and log with GPT
- Include your pipeline YAML when asking for help

---

**Last Updated:** November 2, 2025
**LLMFlow Version:** Current development version

---

## Advanced Topics

### Context Isolation in For-Each Loops

**Key Principle:** For-each loops create **isolated iteration contexts** with **selective sharing** for `append_to` targets.

#### How Context Sharing Works

```yaml
steps:
  - name: process-items
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: do-something
        type: llm
        inputs:
          data: "${shared_data}"  # Deep copied (isolated per iteration)
        outputs: [result]
        append_to: all_results    # Shared reference (accumulates across iterations)
```

**Behavior:**

1. **Regular variables** in iteration context are **deep copied** - changes don't leak between iterations
2. **`append_to` targets** are **shared references** - accumulate results across all iterations
3. **Nested for-each loops** also get isolated contexts, but their `append_to` targets are shared with parent loops

#### Why This Design?

**Problem:** Without isolation, one iteration's changes could affect the next:

```yaml
# Without deep copy (BAD):
context = {"shared_list": ["initial"]}

steps:
  - name: loop
    type: for-each
    input: [1, 2, 3]
    steps:
      - name: modify-input
        type: function
        function: append_to_list
        inputs:
          my_list: "${shared_list}"  # Would see ["initial", 1] on iteration 2!
          item: "${item}"

# With deep copy (GOOD):
# Each iteration gets its own copy: ["initial"]
# Result: context["shared_list"] is still ["initial"] (unchanged)
```

**Solution:** Deep copy everything EXCEPT `append_to` targets.

#### When to Use `append_to`

✅ **Use `append_to` when:**
- Collecting results across loop iterations
- Building a list of processed items
- Accumulating data from nested loops

```yaml
- name: collect-results
  type: for-each
  input: "${items}"
  steps:
    - name: process
      type: llm
      outputs: [result]
      append_to: all_results  # ✅ Accumulates across all iterations
```

❌ **DON'T rely on `append_to` when:**
- You want iteration isolation
- Passing lists as function parameters (they'll be deep copied)
- Modifying shared state (use function return values instead)

```yaml
# ❌ Wrong: Trying to modify parent context directly
- name: loop
  type: for-each
  steps:
    - name: modify-shared
      type: function
      inputs:
        shared_list: "${shared_list}"  # Gets deep copy, changes lost

# ✅ Correct: Use append_to to collect changes
- name: loop
  type: for-each
  steps:
    - name: process
      type: function
      outputs: [result]
      append_to: collected_results  # Changes accumulate
```

#### Nested For-Each Loops

**Important:** `append_to` targets are **recursively shared** across ALL nesting levels.

```yaml
- name: outer
  type: for-each
  input: ["a", "b"]
  item_var: outer_item
  steps:
    - name: inner
      type: for-each
      input: [1, 2]
      item_var: inner_item
      steps:
        - name: collect
          type: function
          function: mymodule.concat
          inputs:
            v1: "${outer_item}"
            v2: "${inner_item}"
          outputs: [result]
          append_to: all_results  # Accumulates across ALL iterations
```

**Result:** `context["all_results"]` contains: `["a1", "a2", "b1", "b2"]`

**How it works:**
1. System recursively finds ALL `append_to` targets in nested steps
2. All loops share the same list reference
3. Deep copying isolates everything EXCEPT `append_to` targets

### Troubleshooting For-Each Issues

**Problem:** Results not accumulating across iterations.

**Solution:** Use `append_to:` to share results:
```yaml
steps:
  - name: collect
    outputs: [result]
    append_to: all_results  # Shared across iterations
```

**Problem:** Parent context getting modified by iteration.

**Solution:** This should NOT happen - iterations are isolated. If you see this:
1. Check if you're using `append_to` (which IS shared)
2. File a bug - deep copy should prevent contamination

**Problem:** Nested loop results not visible in outer loop.

**Solution:** `append_to` targets are shared across ALL nesting levels:
```yaml
- name: outer
  type: for-each
  steps:
    - name: inner
      type: for-each
      steps:
        - name: collect
          append_to: results  # Visible in outer loop context
```