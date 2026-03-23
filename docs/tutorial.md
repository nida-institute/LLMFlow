# LLMFlow Project Tutorial

This repository was initialized with `sp init`.
It includes a minimal, working example that shows how to declare variables,
pass them between steps, and write results to files using `saveas`.

## 1. Project layout

After running `sp init` in an empty directory, you should see:

```
./
├── output/
├── pipelines/
│   └── hello-llmflow.yaml
└── prompts/
    ├── hello.gpt
    └── reply.gpt
```

Pipelines live under `pipelines/`, prompt templates live under `prompts/`,
and generated content is written into `output/`.

## 2. Tutorial pipeline

The tutorial pipeline is defined in `pipelines/hello-llmflow.yaml`:

```yaml
name: "Hello Multilingual Pipeline"
variables:
  prompts_dir: "prompts"
  output_dir: "output"

llm_config:
  model: "gpt-4o-mini"
  temperature: 0.2

steps:
  - name: "multilingual-greeting"
    type: "llm"
    prompt:
      file: "hello.gpt"
      inputs:
        language_count: 5
    outputs: greeting
    saveas:
      path: "${output_dir}/hello.md"

  - name: "respond-to-greetings"
    type: "llm"
    prompt:
      file: "reply.gpt"
      inputs:
        greeting_markdown: "${greeting}"
    outputs: reply_block
    saveas:
      path: "${output_dir}/responses.md"
```

Highlights:

- The `variables` block declares `output_dir`, which is referenced later
  in the `saveas.path` fields using `${output_dir}`.
- The first step saves its LLM output into a pipeline variable called
  `greeting` and also writes that markdown to `output/hello.md`.
- The second step reads `${greeting}` and passes it into the `reply.gpt`
  prompt as `greeting_markdown`, then writes its result to
  `output/responses.md`.

## 3. Running the tutorial

From the project root (where `pipelines/` and `prompts/` live):

```bash
sp run --pipeline pipelines/hello-llmflow.yaml
```

On success, you should see two files:

- `output/hello.md` – the original multilingual greetings
- `output/responses.md` – replies to each greeting

Open them in your editor or viewer of choice and iterate on the prompts
as needed.

## 4. Next steps

- Change `language_count` in the first step to explore larger lists.
- Edit `prompts/hello.gpt` or `prompts/reply.gpt` to adjust tone,
  structure, or formatting.
- Add a third step that summarizes all replies into a short report and
  saves it to another file using `saveas`.
