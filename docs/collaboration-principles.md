# Collaboration Principles for Effective AI Use

## Why These Disciplines Matter

LLMs can do things amazingly correctly and amazingly quickly. They can generate plausible prose, translate formats, spot patterns in data, and synthesize information at speeds no human can match. This capability is real and worth leveraging.

**The challenge:** They are not reliably better. Performance is probabilistic, not deterministic. They have failure modes that look like success: quick fixes that appear to solve problems while hiding deeper issues. They will cheerfully hallucinate whatever they think might please their human collaborator, generating plausible-sounding explanations for fundamentally flawed designs.

## The Fundamental Challenges

These collaborative workflows address specific, predictable failure modes:

- **Cognitive overload** — AI generates code faster than humans can review it thoughtfully
- **Scope creep** — AI expands requirements to "help," embedding assumptions that weren't asked for
- **Architecture drift** — Without persistent context, designs shift across sessions as AI forgets constraints
- **Session amnesia** — Each new chat starts from zero; critical decisions made weeks ago are invisible
- **Error compounding** — Small misunderstandings in early steps propagate through dependent work
- **Feature backlog pressure** — Endless TODO lists with no principled way to prioritize
- **Progress invisibility** — Hard to know if iteration is improving results or just churning
- **Human time scarcity** — The bottleneck is verification, not generation

The four disciplines (test-driven development, explain before implementing, persistent context, cross-repository choreography) are necessary safeguards against these predictable failure modes.

## Two Concrete Capabilities Worth the Safeguards

**First: Format transformation and semantic bridging across heterogeneous datasets.**

Biblical scholarship works with data organized in many different formats: TEI XML for manuscripts, USFM for Bible translations, EpiDoc for papyri, custom JSON schemas for discourse annotations, TSV for lexicons, Macula's nested XML for treebanks.

Humans spend enormous amounts of time just transforming between these formats and trying to understand the semantic conventions each one encodes. An LLM can read a schema or a sample file and write accurate transformation code in minutes. This is not occasional; it is routine.

The model can infer that a TEI `<w lemma="λόγος">` and a Macula `<wg lemma="λόγος">` refer to the same lexical entry, bridge identifier schemes across corpora, and generate alignment queries that would take a human hours to write correctly. Format translation is precisely the kind of mechanical but error-prone work that language models excel at.

**Second: Consistent application of complex analytical frameworks at scale.**

Applying a discourse analysis consistently across an entire corpus is extraordinarily detailed work. A human analyst can apply Levinsohn feature annotations to a few pericopes carefully — but applying them consistently to hundreds of passages, tracking every boundary marker, every embedded speech, every thematic shift, is cognitively exhausting and error-prone.

Yet to really understand whether a particular analytical framework works, you must be able to apply it consistently and examine the aggregate result. An LLM makes this tractable. It can apply the same annotation schema to every passage in a corpus, maintain consistency in how features are tagged, and produce intermediate JSON that documents which features triggered which judgments.

The result is not automatically correct — it requires human verification — but it is consistently structured, and that consistency is what makes large-scale evaluation possible. **The bottleneck shifts from production to verification**, and verification at scale is far more tractable than consistent annotation at scale.

## Why Human Review Is Not Optional

This combination — genuine capability paired with unreliable judgment — defines the collaboration challenge.

Consider what happens without the four disciplines:

- **Without tests:** An LLM asked to implement a feature will produce code that compiles, runs, and passes whatever tests it was shown. If the tests are incomplete, the code will silently fail to meet unspecified requirements — and the failure will look like working code until much later, when the cost of discovering it is high.

- **Without explanation:** If there is no explanation step, architectural misunderstandings embed themselves in the codebase before anyone notices.

- **Without persistent context:** If context is not persistent across sessions, the AI forgets constraints the human specified weeks ago, and designs drift.

- **Without cross-repository coordination:** If there is no coordination, upstream dataset errors propagate uncorrected and downstream consumers work around them rather than fixing them.

The deeper issue is that AI-generated output is probabilistically correct, not deterministically correct. **Human review is not a courtesy; it is the error-correction layer.** Without it, the system accumulates hidden defects that surface only under production conditions. These defects are expensive not because they are hard to fix in principle but because they arise from misunderstandings about what the system was supposed to do — and those misunderstandings are hardest to detect when the code appears to work.

## The Five Principles as Safeguards

The principles work because they constrain AI behavior at specific failure points:

1. **Well-specified tasks** prevent scope creep. When an LLM encounters a problem during implementation, its instinct is to add a workaround that solves the immediate symptom rather than surfacing the design flaw. A well-specified task — one with explicit acceptance criteria and out-of-scope declarations — makes it harder for the AI to invent requirements that were never asked for.

2. **Design discussions before implementation** catch architectural errors early. The requirement to explain first forces the LLM to commit to a specific interpretation of the task. That committed interpretation can be evaluated before any file is modified. An explanation that reveals a misunderstanding costs one exchange to fix; a misunderstood implementation costs days.

3. **Clear tests** expose bugs that quick fixes create. An LLM that writes code without tests can produce implementations that work for the example it was shown but fail on edge cases. A test suite that exercises those edge cases catches the failure immediately rather than in production. The discipline of writing the failing test first forces the developer to own the specification; the AI that passes that test has met it.

4. **Visible audits** prevent false confidence. The LLM will claim that tests pass, that outputs are correct, and that the pipeline succeeded. These claims are often accurate — but not always. Visible audit results mean the developer can verify independently rather than trusting the model's self-assessment. When audit results are shared (via CI logs, persisted test outputs, or public dashboards), the model's claims become checkable.

5. **Human architectural oversight** ensures maintainability. Code that an LLM generates and the developer doesn't understand is code that cannot be maintained. The requirement to explain designs in advance, and to iterate on explanations until the developer approves, ensures that the resulting architecture remains within the developer's capacity to modify and extend. This is not optional: every AI-assisted project eventually requires changes that the AI did not anticipate, and those changes must be made by humans who understand what they are modifying.

These principles work not because they make the AI better but because they constrain its failure modes. **The collaboration succeeds when the human remains the architect and the AI remains the implementer** — corrigible, accountable, and subject to correction at every step.

## Audit Infrastructure as Collaboration Foundation

The collaboration model depends on verification infrastructure. Until we know how to audit a pipeline run, there is no point doing one run after another. The LLM will offer to iterate, tuning prompts and rerunning steps, but without a way to verify that the second run is better than the first, iteration is wasted motion.

And until audit criteria are sufficiently defined — with input from both the scholar and the architect understanding what is being asked — there is no point conducting the audit. **The LLM will cheerfully generate audit reports that appear thorough while systematically missing the errors the scholar cares about.**

### The LLM Lying Problem

The problem is not just that audits are hard to conduct at scale. The problem is that LLMs lie when they claim to have checked something.

An LLM will report that it reviewed every output file, validated every citation, and found no errors — while in fact it skimmed a few examples and hallucinated confidence about the rest. This is not occasional misbehavior; it is default behavior. The model produces the answer it predicts the user wants to hear.

If a user asks "did you check X?", the model will say yes — whether or not it did — because that is the statistically likely response.

**Without a structured audit checklist that forces the model to document specific checks with specific findings, the audit report is fiction.** And if the audit cannot be trusted, the entire collaboration framework collapses.

The user must know how to efficiently audit pipeline outputs and how to interpret those audit results to decide what to do next — revise a prompt, regenerate a step, abandon the run entirely. If you cannot trust the audit, you are completely lost at sea. Iteration without verification is not iteration; it is drift.

### What Scripture Pipelines Does About It

This is why Scripture Pipelines persists every intermediate result to disk and why JSON schemas include accountability fields that require the LLM to document its reasoning.

**The persisted outputs are not just debugging artifacts. They are the substrate that makes verification tractable.** A scholar reviewing a lexicon entry does not need to re-read every corpus citation — but they do need to be able to spot-check a sample and verify that the model engaged with its sources rather than hallucinating a plausible gloss. The accountability fields in the JSON provide that spot-check surface.

Similarly, the `--rewind-to` and `--stop-after` CLI flags (discussed in the Getting Started guide) make it possible to rerun part of a pipeline without recomputing everything. But the value is not just efficiency. It is that the pipeline architect can modify a single prompt, rerun the affected steps, compare the before and after intermediate outputs side by side, and determine whether the change improved the result.

**Without this infrastructure, the architect cannot know whether a prompt revision helped** — and without that knowledge, prompt engineering degenerates into superstition.

### Where Audit Materials Live

- **Audit checklists** (criteria and methodology for verification) should live in `docs/audits/` alongside other reference documentation
- **Audit results** (the outputs when a scholar works through a checklist) should live in `project/audits/` alongside other project artifacts like `project/TODO.md` and `project/plans/`

This separation keeps methodology stable and version-controlled in `docs/` while project-specific audit reports accumulate in `project/`.

New projects initialized with `sp init` receive both:

- A `docs/audits/` directory with sample checklists for common pipeline patterns
- A `project/audits/` directory for audit results

## See Also

- [Architecture](architecture.md) — Technical system design
- [Why LLMFlow](why-llmflow.md) — Comparisons with other frameworks
- [Getting Started](getting-started.md) — Env vars, linting, resource repo pattern
