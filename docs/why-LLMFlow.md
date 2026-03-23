# ❓ Why Scripture Pipelines

Scripture Pipelines is a declarative, testable pipeline engine for LLM + rule/data hybrid workflows with a focus on Bible translation, exegesis, lexicons, and multi‑language / orality tasks. It separates:
- Core orchestration (this repo)
- Domain artifact repositories (leaders’ guides, lexicons, exegetical notes)
- Human‑edited outputs (Git + Obsidian vaults)

## 🔑 Core Advantages
- Declarative YAML pipelines (llm | function | for-each)
- Prompt contracts (`requires` / `optional` in `.gpt` headers)
- Deterministic variable resolution (`${var}`) + template substitution (`{{var}}`)
- Full unit test coverage for data flow and resolution
- Multi-repo content generation with persistent intermediate artifacts
- Human-in-the-loop: outputs checked into resource repos, edited, diffed, regenerated
- Planned MCP integration for selective regeneration, contract inspection, diff tooling
- Obsidian vault alignment (links, indexes, status front-matter)

## 🧩 Feature Comparison (Updated)

| Area | Scripture Pipelines | LangChain / LlamaIndex | Haystack | Custom Scripts |
|------|---------|------------------------|----------|----------------|
| Pipeline Model | Declarative YAML | Imperative chains | YAML + code | Manual |
| Domain Extension | Pluggable functions/plugins | Possible but ad hoc | Possible | Manual |
| Prompt Contracts | First-class (`.gpt` headers) | No native | No native | Manual |
| Intermediate Artifacts | Saved + testable | Hidden | Partial | Depends |
| Multi-Repo Strategy | Built-in pattern | Not opinionated | Not opinionated | DIY |
| Human Editorial Loop | Designed-in | Not primary | Limited | DIY |
| Obsidian Vault Use | Supported pattern | Not addressed | Not addressed | DIY |
| MCP (Planned) | Yes (context/tools) | No | No | N/A |
| Biblical / Linguistic Tasks | Native focus | Generic NLP | Generic QA | Custom |
| Testing Strategy | Extensive unit tests | Limited | Limited | Manual |

## 🧠 Domain Fit
- Handles structured scripture references, lexicon entries, scene segmentation.
- Mixes LLM steps with deterministic parsing and enrichment.
- Encourages review of each transformation (scholar + developer collaboration).

## 🛠 Hybrid Workflow
- Rule-based extraction (XML, regex, mapping tables).
- LLM contextual synthesis (scene guides, emotional arcs, semantic domains).
- Aggregation via `append_to` lists in iteration loops.
- Markdown + JSON outputs for downstream tooling.

## 🗂 Multi-Repository Output
Resource-specific repositories:
- pipelines/ (domain YAML)
- prompts/ (contracted `.gpt`)
- outputs/ (generated + human-edited)
- Obsidian vault structure (link indices, status flags)

Core engine remains clean/public; domain repos stay private or semi-open.

## 📄 Prompt & Template Model
- `.gpt` prompt: HTML comment header with `requires`, `optional`, `description`.
- Body uses `{{variable}}`; current runner single-brace substitution slated for refactor.
- Templates (`.md`) support `{{var}}` and `${var}` for late context resolution.

## 🧭 Obsidian Vault Integration
- Generated files become notes.
- Cross-links added by future link-resolution function step.
- Status front-matter maintained manually (e.g. `status: review-needed`).
- MCP (planned) to surface vault metadata as live context.

## 🔌 Plugins & Extensions
- XPath example plugin.
- Add functions: reference via `function: your.module.fn`.
- Future MCP adapter: tools (`rerun_step`, `validate_contract`, `diff_output`).

## 🚀 MCP Roadmap (Planned)
1. Adapter layer exposing pipeline context as MCP resources.
2. Tools for selective regeneration and contract introspection.
3. Diffing edited vs generated content to flag stale prompts.

## ✅ When To Use Scripture Pipelines
Use if you need:
- Traceable scholarly or linguistic workflows.
- Mixed deterministic + generative steps.
- Multi-language or non-chat LLM tasks.
- Human editorial cycles with versioned outputs.
- Clear test assertions over transformation chains.

## 🚫 When Not Ideal
- Pure chat application scaffolding.
- High-throughput concurrent inference (no parallel runner yet).
- Turnkey RAG pipelines (no built-in vector store layer).

## 🔄 Editing & Regeneration Loop
1. Generate initial artifacts.
2. Human edits in vault/repo.
3. Flag divergence (future diff tool).
4. Regenerate selectively with MCP tools (planned).

## 🎯 Summary
Scripture Pipelines provides a disciplined, inspectable framework for complex Bible / linguistics workflows, balancing automation with human editorial control, and preparing for richer interactive tooling via MCP and vault-aware metadata.

### Linting
First-class validation via `sp lint` (schema, prompt contracts, path checks).
