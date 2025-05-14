# ⚙️ Installing and Running LLMFlow

This document provides step-by-step instructions for installing and running your custom `LLMFlow` pipeline environment using Hatch.

---

## 🐍 1. Prerequisites

Before installing, ensure you have the following:

* **Python 3.10 or later**
* **[Hatch](https://hatch.pypa.io/latest/install/)** (for environment and packaging management)
* An OpenAI API key or other model access token depending on your backend

---

## 📦 2. Clone the Project

```bash
git clone https://your-git-host/your-llmflow-repo.git
cd your-llmflow-repo
```

---

## 🛠 3. Install the Environment

Install dependencies using Hatch:

```bash
hatch env create
```

To activate the environment for use with `llmflow` commands:

```bash
hatch shell
```

Or run commands directly via Hatch:

```bash
hatch run llmflow --help
```

---

## 🔐 4. Set Up Environment Variables

Create a `.env` file (or export variables manually) with your model credentials:

```env
OPENAI_API_KEY=your-key-here
```

You can also pass these via `--env` or shell export.

---

## 🚀 5. Run a Pipeline

To run a pipeline:

```bash
hatch run llmflow run --pipeline pipelines/simple-table.yaml --var passage="Genesis 1:1"
```

To lint (validate) the pipeline:

```bash
hatch run llmflow lint --pipeline pipelines/simple-table.yaml
```

---

## 🧪 6. Troubleshooting

* **Missing dependencies?** Run `hatch env create` again.
* **Linting errors?** Make sure `.gpt` files contain required YAML headers.
* **Model not responding?** Check API key and internet connection.

