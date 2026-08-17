# DRAFT — Authorized Vocabulary for Scripture Pipelines / LLMFlow

**Status:** Draft, but in force. The "use X, not Y" list is authoritative for user-facing text
and commit messages; the Captain bans off-list abstract nouns (e.g. "governance").

> **Status:** Draft for the Captain to review and place at
> `docs/ai-context/vocabulary.md` (AI must not write ai-context directly).
> **Purpose:** the canonical terms for this project's core concepts, so AI
> collaborators use the project's own words instead of drifting into generic-AI
> vocabulary. Grounded in `overview.md`, `collaboration-principles.md`,
> `CLAUDE.md`, and `llmflow-language.md` — not invented here.
> Items marked **(confirm)** need the Captain's ruling.

## How to use this list
- Prefer the **canonical term** for each concept.
- Do not substitute the **avoid** synonyms; use the replacement instead.
- If a needed concept is missing, propose an addition rather than coining a term.

## Names
| Term | Use |
|------|-----|
| **Scripture Pipelines** | The product / project name — use in prose. |
| **sp** | The CLI command and binary. |
| **llmflow** | The Python package and import namespace *only* (e.g. `function: llmflow.utils.data.parse_bible_reference`). Not a product name. |
| **LLMFlow** | **Deprecated** as a product name; superseded by Scripture Pipelines. |

## Roles and the command model
| Term | Meaning |
|------|---------|
| **Captain** / **the human** / **the architect** | The human who directs the project: decides goals, design, and scope, commands the work, and holds final authority. (Called *architect* in `collaboration-principles.md`.) |
| **the model** / **the AI** / **the implementer** | The AI collaborator that proposes and implements work under the Captain's direction; it is corrigible and accountable and holds no authority of its own. |
| **authority** | The Captain's right to decide goals, design, and scope; the model holds none of it and acts only within the Captain's decisions. |
| **authorization / sign-off** | The Captain's explicit approval of a specific change, given before the model edits any file (obtained through the `/authorize` workflow). |
| **drift** | The gradual shift from human-commanded execution to AI-led decisions, in which the model redirects goals, expands scope, or steers choices the Captain did not authorize; encompasses scope creep and architecture drift. |
| **stand-down** | A mid-session correction in which the Captain reasserts authority after the model has begun to drive; invoked with `/stand-down`. |
| **human review** | The Captain's verification of AI-produced output before it is accepted or used, since that output is probabilistically correct and can fail in ways that resemble success. |

## Collaboration failure modes (the project's own taxonomy)
`cognitive overload`, `scope creep`, `architecture drift`, `session amnesia`,
`error compounding`. Use these; do **not** relabel them.

## Core engine concepts
| Canonical term | Meaning |
|----------------|---------|
| **pipeline** | An ordered list of steps in YAML. |
| **step** | A single unit with `type`, inputs, and outputs. Step types: `llm`, `function`, `for-each`, `if`, `window`, `save`, `json`, `load_*`, `basex`, `duckdb`, `xpath`, `xslt`, `plugin`. |
| **context** | The map of variables produced/consumed by steps. |
| **prompt contract** | The `requires`/`optional` header a `.gpt` prompt declares to state which variables it needs; the linter enforces it. |
| **guardrails** | The `# GUARDRAILS` section of a prompt, holding the MANDATORY/MUST constraints and quality controls that keep the model within required behavior; part of the prompt-organization convention. |
| **variable resolution** | `${var}` in YAML; `{{var}}` in prompt/template files. |
| **loop variable** / **list** | `for:` (the bound element) and `in:` (the list) — XQuery style. **Never** `item_var`/`input`/`over`. |
| **linter / lint** | Static validation before a run. |
| **saveas** | Persisting a step's output to disk. |
| **telemetry** | Per-step cost/time tracking. |
| **plugin** | A registered step type living in a project's `plugins/`. |
| **registry** | The global resource registry in `~/.sp/`. |
| **resource repo** | The consumer repo (often an Obsidian vault) holding generated outputs. |
| **deterministic function** | A `type: function` step — mechanical, non-LLM work. |

## Use X, not Y
| Avoid | Use | Note |
|-------|-----|------|
| frame, framing, reframe | design, goals, scope, decision, direction | Captain's ruling; primary target of this pass |
| flow (as a common noun) | pipeline | no separate "flow" concept is needed |
| LLMFlow (as a product name) | Scripture Pipelines | `llmflow` remains only as the Python package / import namespace |
| countermeasure | safeguard, discipline | |
| orchestrate (of Scripture Pipelines' own behavior) | coordinate, run, drive | Fine when naming the external tool category (Prefect/Airflow "workflow orchestration") |
| ecosystem | name the specific thing meant | Vague; replace with what it denotes — e.g. document format, publishing workflows, distribution tools, tools-and-data-sources |
| governance | human command, human authority | Off-list; recurring AI insertion — the concept is the Captain commanding the tool (James Kirk model), not committee/policy governance |

## Confirmed-native (do NOT flag these as insertions)
`leverage`, `hallucinate` / `hallucination`, `safeguard`, `at scale`,
`architect` / `implementer`, `drift`, `scope creep`, `architecture drift`,
`framework` (as in "analytical framework" / "drift-patterns framework").

## "framing" — resolution (Captain, this session)
"framing / interpretation drift" is a legitimate taxonomy term in the
drift-patterns framework and stays there; it is not banned in the framework
docs. It is **too abstract for the Balisage paper's audience**, so the paper
describes the behaviors concretely (redirecting goals, expanding scope, claiming
false authority, misreporting status) and cites the framework rather than
reciting the abstract category names. The `frame/framing` ban therefore applies
to the paper's prose, not to the framework's own taxonomy.
