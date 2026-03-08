# Handling OpenAI Moderation Blocks

OpenAI's Responses API occasionally blocks Scripture-heavy passages, historical violence, or sensitive terminology even when the material is scholarly. LLMFlow now surfaces these events explicitly as `ModerationError` so operators can diagnose the issue instead of receiving empty completions.

## What LLMFlow Does
- Detects `status: incomplete` payloads whose `incomplete_details.reason` is `content_filter` or any `status: blocked` payload.
- Raises `ModerationError` immediately with the model name, step, explanation, and OpenAI filter metadata.
- Points back to this memo from the CLI so humans understand why retries will not succeed until the prompt changes.

## Why Moderation Triggers Bible Pipelines
1. **Graphic passages** – Books like Judges or Revelation describe violent scenes that trip generic filters.
2. **Polysemy** – Greek/ Hebrew lexeme glosses can match modern extremist vocabulary out of context.
3. **Batching** – Sending multi-chapter context in a single request increases the chance of a flagged paragraph.
4. **Tool echoes** – MCP tools that serialize source text verbatim can reintroduce material the LLM already justified as sensitive.

## Mitigation Checklist
1. **Prefix with scholarly framing** – Make the first lines of the prompt explicit: “You are analyzing canonical Scripture for academic publication. The content contains historical violence described for theological study.”
2. **Quote responsibly** – Surround long citations with quotation marks and add attribution (`> Deut 32:35`) so filters have context.
3. **Chunk high-risk passages** – Split steps so imprecatory psalms or conquest narratives run separately with additional rationale.
4. **Redact gratuitous tooling output** – When MCP tools return multi-page passages, trim to the exact verses referenced.
5. **Emphasize transformation goals** – Clarify that the model is summarizing, annotating, or translating for clergy—not generating new violent text.
6. **Log the reference** – Include the passage citation in the prompt metadata so a reviewer can show OpenAI support exactly what scripture triggered the block if escalation is needed.

## Workflow Suggestions
- Add a `guardrails:` comment block inside `.gpt` prompts reminding contributors to keep primers academic.
- When a moderation block occurs mid-pipeline, commit the failed context plus prompt to the repo so the next maintainer can iterate without rerunning earlier steps.
- Keep alternate phrasings (e.g., “put to death” → “executed”) in a shared glossary for sensitive lexemes that still capture meaning.

## When to Escalate
If repeated attempts with scholarly framing fail and the passage is indispensable (e.g., lectionary reading), open a support ticket with OpenAI referencing the model, request IDs, and a justification that the usage is theological research. Include the moderation metadata logged by LLMFlow under `content_filter_results`.
