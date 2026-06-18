# Why Scripture Pipelines

The global church still has far too few high-quality biblical resources. The work of
producing them — exegetical guides, translation helps, community Bible study materials,
orality-adapted content — is hard, slow, and dependent on a small number of people with
the right combination of linguistic expertise, biblical scholarship, and cultural knowledge.
Those people are overextended. The need far exceeds what they can produce.

The people doing this work come from varied contexts: Western scholars and linguists,
field workers living and serving overseas, and a growing number of traditional and
untraditional scholars from the global church itself. What they share is the challenge
of producing resources that actually fit the communities they serve. Western resources
exist in abundance, but they often aren't the right fit — and producing something
better requires the ability to prototype new kinds of resources, try them, and iterate.
The experts who could do this don't have time to experiment.

Scripture Pipelines exists to make those experts more productive — and to help
scholarly communities innovate rather than just consume.

---

## A Rich Ecosystem of Biblical Data

Biblical scholarship now has access to an extraordinary set of structured data resources:
Greek and Hebrew source texts, verse-level discourse analysis, morphological annotation,
semantic domain tagging, entity identification across the entire canon, lexical data,
alignment data, translation corpora. These are the products of decades of careful
scholarship by linguists, text critics, and computational humanists.

The problem is that these resources are hard to use together. They come from different
projects, use different identifiers, have different structures. A scholar who wants to
ask "what are the discourse features, morphological signals, entity relationships, and
semantic patterns all saying about this passage simultaneously?" faces an integration
problem that can consume most of a research day before any analysis begins.

Scripture Pipelines addresses this with text-based pipelines (written in YAML) that a
developer — working alongside domain experts and with the help of an AI assistant — can
read, write, and modify. Building a pipeline typically requires three kinds of knowledge:
someone who understands the data sources, someone who understands the audience and what
the resource needs to accomplish, and a developer comfortable collaborating with both and
working with AI tools to write and debug the pipeline code. Mentoring developers who can
fill that third role is part of what this project is about. Each step in a pipeline can
query a database (using XQuery against BaseX), extract data from XML documents (using
XPath), load spreadsheet-style data files, call an LLM, or run custom functions. Steps
pass their output forward; every intermediate result is saved to disk and open for
inspection. A scholar or an AI assistant can read the pipeline YAML and understand
exactly what data is being fetched, what is being asked of the model, and what the model
produced at each stage.

For contributors who aren't developers, `sp gui` provides a lightweight document
management interface — a way to review outputs, track status, and work with generated
materials without touching the pipeline code. It's in early stages, but the intent is
that the whole team can participate, not just the developer.

---

## Data Integration in Practice

Pipelines can draw from a wide range of sources:

**Biblical data resources** — the datasets catalogued in [Awesome Biblical Resources](https://github.com/nida-institute/awesome-biblical-resources): Greek and Hebrew source texts, Levinsohn discourse features, Macula morphology, ACAI entity data (people, places, groups, and deities identified across the entire canon), word senses and semantic domains, alignment data, translation corpora. These are the primary scholarly inputs Scripture Pipelines is designed to connect.

**Translation projects** — USFM and USJ files from Paratext projects: draft translations, back translations, consultant notes.

**Databases and files** — BaseX XML databases (via XQuery), XML and USFM documents (via XPath), CSV/TSV spreadsheet files, JSON, Markdown, plain text.

**Live data services** — external tools callable via MCP (Model Context Protocol), including the Bible Resource MCP, which provides exact passage text, word senses, morphological analysis, and entity data directly within a pipeline step.

**Previous steps** — every step can receive output from any earlier step in the pipeline. Structured JSON works best for most purposes — it's inspectable, schema-validatable, and easy to pass forward — but steps can pass any data format. They can write outputs to disk,
update Obsidian vault notes, or pass structured JSON forward to the next step. The format
doesn't matter — what matters is that every step declares what it needs and produces
something the next step can use.

One concrete example of why this matters: the Bible Resource MCP provides exact passage
text, word senses, morphological analysis, and entity data as live tools callable from
within a pipeline step. When a step receives the actual Greek text via MCP, the LLM
reasons from what the text says. Without it, the LLM draws on its training memory of
what the Greek probably says — and that produces plausible-sounding errors that are
hard to catch.

This is what enables rapid prototyping: you can assemble a pipeline from existing data
sources, run it on a few passages, inspect every intermediate output, and find out quickly
whether the approach works — before investing in a full run or relying on the results.

---

## What AI Enables — and Where It Falls Short

AI can be extremely helpful for this work and significantly increase efficiency. It
excels at integrating complex, heterogeneous datasets — holding many structured sources
together simultaneously and surfacing connections across them. It gives a coherent
high-level picture of what the data says and can find specific fine-grained details on
demand. It is excellent for brainstorming, exploring what a new kind of resource could
look like, and generating first drafts that the scholar then shapes.

But AI also hallucinates. It drifts — confidently pursuing what seems like a plausible
continuation rather than what was actually asked. It fails to understand what is really
being asked, produces fluent output that misses the point, and then defends that output
rather than reconsidering it.

Compounding this: AI has no reliable way to evaluate the quality of its own output,
because quality is ultimately a human judgment. Whether an analysis is accurate,
whether a resource serves the community it was made for, whether an explanation fits
the cultural context — these are questions only humans can answer. Confident and
accurate look the same to the model generating the text.

In biblical and linguistic work, this makes failures especially hard to detect. The
output uses the right vocabulary. It reads like careful analysis. It may be grounded
in nothing at all — the model has recalled what scholarship sounds like and produced
more of it, drawing on training rather than text.

The first specific concern is quality. In domains like biblical discourse analysis,
scholars have spent decades carefully annotating the Greek New Testament and Hebrew
Bible — paragraph boundaries, thematic transitions, prominence markers, clause
connectives — building datasets that represent irreplaceable expertise. That expertise
belongs to the scholarly community; AI is not a substitute for it. Scripture Pipelines
treats those datasets as authoritative inputs. The AI's job is to reason from them,
not to replace them.

The second concern is formation. If the AI surfaces the discourse structure, traces
the character arcs, and identifies the thematic breaks — and the scholar's job is to
approve or reject the output — the scholar gradually stops doing the analytical work
that builds genuine understanding. Approving output that looks good is easy. Catching
what's wrong with it requires doing the work yourself, and the pull toward "looks good,
move on" is strong. In most AI systems, there's no good way to verify what the model
actually did — no record of what it received, no trace of where a claim came from — so
the scholar has no foothold for resistance. The AI gets faster; the scholar gets lazier.
The dependency is invisible until the expertise is gone.

This is not only a risk for biblical scholarship. AI is only as good as the data it
reasons from. When that data is itself AI-generated — and when humans have lost the
capacity to check it against primary sources — quality degrades in ways that compound
and accelerate. The careful human scholarship that grounds AI output is not a legacy
artifact to be replaced; it is what keeps AI output grounded in something real. This is a threat to every field where AI is displacing rather than augmenting
human expertise.

The design intention is the opposite. Scripture Pipelines is built to be used not just
for producing outputs, but for building capacity. That means using AI to help scholars
reason through difficult texts, not just summarize them. It means producing mentoring
materials — resources that help scholars teach one another, that make expertise
transferable across the community. It means using AI in ways that build judgment, not replace it.

---

## Aligning AI with the Scholar's Goals

The central design problem in Scripture Pipelines is alignment: how do you keep the
AI working toward the scholar's actual goals, rather than producing output that sounds
like it answered the question but didn't?

The design principle is simple: the scholar is in charge. The AI follows direction,
accepts correction, and does not assert its own judgment over the scholar's. This is
harder to achieve than it sounds — AI systems tend to pursue their own interpretation
of a task even when it diverges from what was asked. The [Human at the Helm](https://github.com/nida-institute/human-at-the-helm)
methodology is a practical framework for keeping that from happening: the scholar
commands, the AI executes.

In practice, this means four things:

**Prompt contracts.** Every LLM step declares exactly what data it requires — verified
by `sp lint` before any LLM calls are made. When a step requires source text, it must
have it. The AI cannot substitute training knowledge for a required input; the pipeline
stops if the data is absent.

**Structured outputs.** Every LLM step produces structured JSON output that follows a
defined schema — the model cannot give you freeform prose where the pipeline expects a
specific field. Output is inspectable, comparable, and testable in ways that prose is not.

**Persistent intermediate artifacts.** Every step's output is saved to disk. If the
final result is wrong or thin, you can trace backward step by step to find exactly
where the analysis went off. Every decision about what is worth analyzing, and what
counts as a good result, belongs to the scholar.

**Debug request and response files.** Every LLM step can produce a record of what
the model actually received — the literal prompt at inference time — and what it
returned before any post-processing. Together these are the primary tool for detecting
**freelancing**: output that sounds grounded in the text but was generated from
training knowledge. Open the request file; search for the specific claim; if the
source is not there, the model invented it. The response file shows exactly what the
model said, independent of how the pipeline processed or structured it afterward.

These mechanisms are also a curriculum: working with them teaches you to ask better
questions about what the AI actually received, what it did with it, and whether the
output reflects the text.

---

## Auditing and Debugging

Auditing is itself a collaboration between human and AI. The human brings domain
judgment — the ability to recognize whether an analysis is sound, whether a claim
fits the text, whether an output serves the community it was made for. The AI brings
the ability to read large files quickly, trace specific claims back to their sources,
and surface patterns across many steps. What makes this collaboration possible is
transparency: every artifact in the pipeline is readable by both.

Intermediate outputs are plain JSON. Debug request files are plain text. There are
no hidden framework states, no opaque embeddings, no internals that only the system
can see. A scholar can open any file and read what the model received and produced.
An AI assistant can do the same — and can help trace whether specific output claims
are grounded in the input data, flag step boundaries where grounding breaks, or
identify patterns of drift across a run.

`sp lint` checks the pipeline for problems before any LLM calls are made: missing
inputs, schema mismatches, prompt contract violations.

The `/audit-output` skill provides a systematic protocol for output quality. The
core technique is a five-claim spot-check: pick five specific claims from the output —
a sensory detail, a cultural observation, a character's inner state, a tension thread
reference — and trace each one to the debug request file. Every grounded claim has a
source. Every freelanced claim does not. Working backward: if the final output is thin, check each step boundary until you find
where the model stopped using what it was given.

---

## When to Use Scripture Pipelines

Use it when you need:

- Traceable scholarly or linguistic workflows where the provenance of every claim matters
- Integration across multiple structured biblical data sources in a single pipeline
- Mixed deterministic and generative steps — database queries, XPath extraction,
  spreadsheet loading, LLM calls — each described in plain YAML
- Rapid prototyping of new resource types with structured, reviewable output
- Multi-language and orality-focused tasks
- Human editorial cycles with outputs tracked in version control, where every change
  is visible

Scripture Pipelines is a batch pipeline tool — it runs a defined sequence of steps
from start to finish, producing structured artifacts at each stage.

---

## Feature Comparison

| Area | Scripture Pipelines | LangChain / LlamaIndex | Haystack | Custom Scripts |
|------|---------------------|------------------------|----------|----------------|
| Pipeline Model | Declarative YAML | Imperative chains | YAML + code | Manual |
| Prompt Contracts | First-class (`.gpt` headers) | No native | No native | Manual |
| Intermediate Artifacts | Saved + testable | Hidden | Partial | Depends |
| Schema-Enforced Output | Built-in (`json_schema`) | Optional | Optional | Manual |
| Domain Extension | Pluggable functions/plugins | Possible but ad hoc | Possible | Manual |
| Multi-Repo Strategy | Built-in pattern | Not opinionated | Not opinionated | DIY |
| Human Editorial Loop | Designed-in | Not primary | Limited | DIY |
| Biblical / Linguistic Tasks | Native focus | Generic NLP | Generic QA | Custom |
| MCP Integration | Implemented | Partial | No | N/A |
| Obsidian Vault Use | Supported pattern | Not addressed | Not addressed | DIY |
| Testing Strategy | Extensive unit tests | Limited | Limited | Manual |

---

## Further Reading

- Stuart Russell, *Human Compatible: Artificial Intelligence and the Problem of Control* (2019) — a readable book by a leading AI researcher arguing that AI systems behave better when they are designed to assume they do not know what the human's goals are — and therefore keep asking rather than assuming they know. This is the theoretical foundation for why Scripture Pipelines builds correction and oversight into every step.
- [Human at the Helm](https://github.com/nida-institute/human-at-the-helm) — practical guidelines for working with AI in scholarly settings: how to keep the human in authority, how to detect when the AI has gone off track, and how to maintain the accountability that scholarship requires.
- [Awesome Biblical Resources](https://github.com/nida-institute/awesome-biblical-resources) — a curated catalog of high-quality structured datasets for biblical scholarship: Greek and Hebrew texts, discourse analysis, morphological data, entity databases, lexicons, and more. These are the data sources Scripture Pipelines is designed to connect.
