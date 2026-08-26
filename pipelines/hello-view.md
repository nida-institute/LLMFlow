# hello.yaml

```yaml
name: "Hello Scripture Pipelines"
description: |
  Minimal starter pipeline for Scripture Pipelines.
  Run with: llmflow run --pipeline pipelines/hello.yaml
variables:
  output_dir: "outputs"

output_file_directory: "outputs"

llm_config:
  model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 500

steps:
  - name: "multilingual-greeting"
    type: "llm"
    prompt:
      file: "hello.gpt"
      inputs:
        language_count: 5
    output: greeting
    saveas:
      path: "${output_dir}/greeting.md"
```
