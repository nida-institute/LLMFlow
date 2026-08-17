# Plan: Scripture Pipelines Documentation for Scholars

**Status:** Proposed — not built. A documentation plan; no articles from it have been written.

**Goal:** Replace or supplement existing docs to explain why Scripture Pipelines are useful to scholars and translators — hands-on, methodology-focused, oriented toward content creation rather than software development.

**Primary audience:** Scholars and translators who may not be developers. They understand their domain deeply; they are learning to work with AI tools for content creation at scale.

**Secondary audience (Option D):** Developers whose job is to support those scholars — setting up pipelines, writing prompt files, debugging runs, extending the engine with new function steps or plugins.

---

## The Problem with the Current why-LLMFlow.md

The existing document leads with a feature comparison table and bullet points aimed at developers choosing a framework. A scholar reading it sees "Declarative YAML," "Pydantic schema validation," and "MCP roadmap" — none of which explains why they should use this rather than just chatting with GPT-4.

It can be replaced or kept as a technical reference for developers; the options below differ in how much they lean on it.

---

## The Two-Part System: Pipeline + GUI

The documentation needs to explain both parts and how they fit together. They address different problems:

**`sp run` (the pipeline)** handles generation: declarative, reproducible steps at scale with full intermediate artifacts. The scholar specifies what the LLM is asked; the pipeline executes it consistently.

**`sp gui` (the content lifecycle manager)** handles what happens after generation: moving content through stages (generated → editing → approved), enforcing permissions at each stage, allowing scholars to compare generated vs. edited versions side by side, and integrating with git. This is what makes the human editorial role structurally secure — the pipeline writes to the generated stage; when a scholar promotes a file to editing, it moves to a location the pipeline cannot touch. Running the pipeline again regenerates without affecting the edited version.

Any documentation that describes the scholar's workflow needs to explain both parts. An article that only covers the pipeline leaves out the most important part of the scholar-facing experience.

---

## What Belongs in "Why Scripture Pipelines" vs. the Methodology Document

This distinction matters for every option below.

**A "Why" document** answers: what fundamental problems does this solve, and why does this approach address them better than alternatives? Its job is not to describe individual features but to make the case for the overall approach. A reader who finishes it should understand the philosophy and be convinced — or at least intellectually engaged. They should not yet know how to use `--resume`.

Major reasons that belong here:
- **Reproducibility and accountability** — the pipeline is a complete, durable specification of what was done; colleagues can understand, audit, and reproduce the work months later
- **Consistent application at scale** — a framework that produces one leaders' guide section also produces two hundred, with the same structure and the same analytical approach throughout
- **Human authority over content** — the scholar specifies what the LLM is asked; the pipeline executes that specification; the content lifecycle manager ensures human editorial work is never overwritten by regeneration; the scholar's judgment governs what becomes authoritative
- **Structured collaboration** — a shared pipeline means a scholar and developer are working from the same specification; the scholar's domain expertise shapes what is generated; the developer's technical knowledge shapes how the pipeline runs
- **Auditability** — every intermediate output is saved to disk; a scholar can inspect exactly what the LLM received and what it produced at every step, making verification tractable rather than impossible

**Operational details that do not belong in a "Why" document:**
- Individual CLI flags (`--resume`, `--rewind-to`, `--stop-after`, `--dry-run`)
- YAML syntax and pipeline structure
- Prompt contract syntax
- Debugging workflows
- Step types and configuration

These belong in the methodology document, the language reference, or getting-started. Including them in a "Why" document buries the argument in implementation detail and signals to scholars that this is a tool for developers, not for them.

---

## Where Scholars Actually Are

The reader is probably already using AI — ChatGPT or Claude — to draft content: leaders' guides, lexicon entries, storytelling definitions. It's producing something. But they have experienced at least one of these:

- A run produced good results; they can't reproduce it because they don't remember exactly what they typed
- The LLM gave confident, plausible output that turned out to have errors only a domain expert would catch
- They want to apply the same framework to 200 passages, not just 3
- They edited the output carefully; someone re-ran the pipeline and overwrote their edits
- A colleague asked "how was this generated?" and they couldn't give a clear answer
- Output looks good on the surface but is systematically wrong in ways that only become visible when a domain expert reads it carefully

These are the problems a "Why" document should address — at the level of the problem, not at the level of the flag that helps.

---

## Structural Options

### Option A: Replace why-LLMFlow.md with one narrative article

One document covering the full arc: problem → approach → why not alternatives. Roughly 1200–1500 words. Replaces `why-LLMFlow.md`. No operational detail.

**Where it works well:** One document is easy to share, easy to discover, and easy to maintain. A reader who asks "why should I use this?" gets a complete answer in one place. The narrative can build an argument properly — the opening problem earns the reader's attention, the approach section answers it, the comparison with alternatives confirms the case.

**Where it breaks down:** Even without operational detail, a document covering reproducibility, scale, human authority, the GUI content lifecycle, structured collaboration, and auditability is doing a lot. The risk is that each section is too brief to actually land — the argument is gestured at rather than made. A scholar who has never thought about pipeline-based content creation needs more than a paragraph per major idea to come away convinced.

There is also a structural gap: a "Why" document that never tells the reader what to do next leaves them motivated but stranded. Either it ends with a pointer to the methodology document (requiring readers to follow a link) or it includes a brief "what this looks like in practice" section — which risks blurring the line into operational detail.

---

### Option B: Replace why-LLMFlow.md + add a methodology companion

Two documents:

1. **`why-scripture-pipelines.md`** (replaces `why-LLMFlow.md`) — The case for the approach. Problem-first narrative. Major reasons only, no operational detail. Ends with a clear picture of what the workflow looks like at a high level. ~1000 words.

2. **`content-creation-methodology.md`** — Hands-on. How to actually work well with the pipeline and the GUI. Operational detail lives here: the debugging workflow, prompt contracts, how to use the content lifecycle stages, how to audit intermediate outputs. ~1500–2000 words.

**Where it works well:** Each document has one job and can be written in the mode that job requires. The "why" document makes an argument; the methodology document is a reference. They can evolve independently — a new CLI flag means updating the methodology doc; the core argument in the "why" document stays stable. The split also matches how different readers will encounter the documentation: a new reader needs the "why" first; an experienced user who wants to know how to diff across stages goes directly to the methodology.

**Where it breaks down:** Two documents require the reader to find both. More importantly, the "why" document's argument depends partly on what the system actually does — and a reader who doesn't know that `sp gui` provides side-by-side diff across lifecycle stages won't fully grasp why "human authority over content" is a real guarantee rather than a claim. The "why" document has to invoke capabilities without explaining them, which requires precise language to avoid being either too vague (loses the reader) or too concrete (slides into operational detail).

---

### Option C: Three articles mirroring human-at-the-helm

1. **`why-scripture-pipelines.md`** — The case. Mirrors the human-at-the-helm README.
2. **`content-creation-methodology.md`** — How to work well. Hands-on.
3. **`content-creation-drift-patterns.md`** — What goes wrong. Mirrors drift-patterns.md but specific to content creation: the LLM claiming to have faithfully represented sources when it hallucinated, outputs that are plausible but theologically wrong in ways only a domain expert catches, the erosion of the scholar's judgment when iteration happens too fast without verification.

**Where it works well:** The drift patterns document addresses something that doesn't exist anywhere targeted at content creators. The domain-specific failure modes for scripture content creation are meaningfully different from the general drift patterns in human-at-the-helm, and writing them down is independently valuable. This option gives the documentation a complete shape: why to use it, how to use it well, and what to watch for when things go wrong.

**Where it breaks down:** Three documents is a maintenance commitment. The drift patterns document requires careful writing — concrete enough to be recognizable, general enough to transfer across projects. There is also a placement question: if the drift patterns piece is general enough to apply beyond scripture pipelines, it may belong in human-at-the-helm rather than here. If it's too specific to scripture pipelines, it may feel narrow. Cross-linking between the two repositories solves this partly but fragments the reading experience.

---

### Option D: Two audiences, one shared narrative

**Primary audience: scholars.** Secondary audience: developers whose job is to support those scholars.

The design insight is that scholars and supporting developers share the same concepts but approach them from different positions. A scholar needs to understand why the pipeline produces trustworthy content and how the content lifecycle protects their editorial work. A developer needs to understand how to build and debug the pipeline that implements the scholar's specifications. The methodology is shared; the vantage point differs.

**Structure:**

1. **`why-scripture-pipelines.md`** (replaces `why-LLMFlow.md`) — Written for scholars. The case for the approach at the level of problems and principles. ~1200 words.

2. **`content-creation-methodology.md`** — Two-track document with **Scholar's Track** and **Developer's Track**, clearly labeled within each section. The scholar track explains the concept and workflow; the developer track (in a callout block) gives the implementation perspective.

   Example section — using a major concept, not an operational detail:

   > **The content lifecycle: how your edits are protected**
   >
   > *For scholars:* When the pipeline generates content, it writes to the generated stage. When you're ready to work with a piece, you promote it to the editing stage — at which point it moves to a location the pipeline cannot touch. If the pipeline runs again (because you extended the corpus, or a prompt was improved), your edited version is unchanged. You review the new generated version, decide what if anything to incorporate, and the GUI lets you compare the two side by side. Your judgment governs what becomes authoritative.
   >
   > *For developers:* The content lifecycle is enforced by `sp gui`'s stage/permission model. Each stage has a directory and file permissions set by `.sp-permissions` sentinel files that survive git clone. Transition logic (`content_transition.py`) moves files between stages and updates metadata. The pipeline's `saveas` paths write only to the generated stage directory; they have no knowledge of other stages. This structural separation — not any CLI flag — is what makes the guarantee hold.

   This structure works because the major concepts — reproducibility, scale, content lifecycle, human authority — are the same for both audiences. The two tracks answer "what does this mean for me?" from each position.

3. **`content-creation-drift-patterns.md`** — Same as Option C. Written for both audiences.

**Where it works well:** Scholars and developers who work together benefit from reading the same document. The developer who has read the scholar track understands the mental model they're building for — and builds pipelines accordingly. The scholar who has skimmed the developer track understands what the developer is doing when they configure stage permissions and why it matters. This shared vocabulary reduces the most common failure mode in scholar-developer collaboration: the developer builds something technically correct that doesn't match how the scholar thinks about their work.

The format also makes an implicit claim explicit: Scripture Pipelines is designed for a specific division of labor. The scholar specifies and reviews; the developer implements and maintains. The two-track structure embodies this claim rather than just stating it.

**Where it breaks down:** The two-track format is harder to write and maintain than it looks. Both tracks must be genuinely complete — a gesture toward the developer audience is worse than not addressing them at all, because it signals "this document isn't really for you" and developers will go to the code instead. Keeping both tracks substantive while maintaining a readable whole requires discipline. 

The visual convention also matters more here than in other options. Blockquotes with italic labels work in GitHub Markdown but are not visually distinct enough to make audience-switching feel natural. More robust formatting (collapsible sections, distinct callout styling) may be needed but is not standard in GitHub-rendered Markdown.

Finally: the benefit of shared vocabulary only materializes if both parties actually read both tracks. In practice, a developer onboarding may go directly to the code; a scholar encountering developer callouts may skip them. The format creates the opportunity for shared reading but does not guarantee it.

---

## Comparing the Options

| | One document (A) | Two documents (B) | Three documents (C) | Two tracks (D) |
|---|---|---|---|---|
| Writing complexity | Medium | Low per document | High total | High |
| Maintenance burden | Medium | Low (independent) | High | Medium-high |
| Argument depth | Compressed | Full | Full | Full |
| Reader experience — new scholar | Good if concise | Requires following link | Requires following links | Good if tracks are clear |
| Reader experience — developer | Not the audience | Not the audience | Not the audience | Yes, if tracks are real |
| Shared vocabulary for scholar-developer teams | None | None | None | Yes, if both read it |
| Drift patterns coverage | No | No | Yes | Yes (with 3rd doc) |
| Mirrors human-at-the-helm | No | Partially | Yes | Yes (with 3rd doc) |

**Key tensions:**

*Argument depth vs. single document.* The five major reasons to use Scripture Pipelines (reproducibility, scale, human authority, content lifecycle, auditability) each need real development to land. A single document that covers all five without operational detail can do this — but only if each section is given enough space. A document that gestures at these ideas without developing them is worse than the feature comparison table it replaces, because at least the table is honest about what it is.

*Audience purity vs. shared vocabulary.* Writing purely for scholars produces a cleaner "Why" document. Writing for both scholars and developers in the methodology document is harder but produces something a team can read together. The question is whether the people using this documentation are working in isolation or in collaboration.

*Completeness vs. tractability.* Options C and D are more complete but require substantially more writing and discipline. Options A and B can be written and published quickly. The drift patterns document in particular — if done well — is independently valuable; if done hastily, it's just a list of things that can go wrong.

---

## Content Outline: why-scripture-pipelines.md

The outline below is at the level of problems and principles — no CLI flags, no YAML, no operational detail.

**Opening: informal AI use doesn't produce accountable content**

Scholars working with AI tend to begin informally: describe what you want, read what comes out, adjust, repeat. This produces content. It does not produce accountable content. When a colleague asks "how was this generated?" or "is this consistent with how we defined this term in Mark?" there is no answer — only a vague memory of what was typed into a chat window three months ago.

**Reproducibility and accountability**

A pipeline is a complete, durable specification of what was done. Every step is named, every input declared, every output saved to a known location. The pipeline file is the record. A scholar can return to it six months later and understand exactly what happened. A team member can read it and reproduce the run. An auditor can verify which sources the LLM received and at which step.

**Consistent application at scale**

A chat session produces one output. A pipeline produces as many as the corpus requires, with the same analytical framework applied consistently throughout. This is not just efficiency — it is what makes aggregate analysis possible. To know whether a particular framework works, you have to apply it to the whole corpus and examine the result. A pipeline makes this tractable; a chat session does not.

**Human authority over the content**

The scholar specifies what the LLM is asked — not in the moment of a chat exchange, but in a durable prompt file that can be read, revised, and reviewed. The pipeline executes that specification. The content lifecycle manager ensures that when a scholar edits generated content, their editorial work is structurally protected: the pipeline writes to a generated stage; the scholar promotes files to an editing stage the pipeline cannot touch; the scholar's judgment governs what becomes authoritative.

**Auditability**

Every intermediate output is saved to disk. A scholar reviewing a lexicon entry can inspect exactly what the LLM received at each step and what it produced. This makes verification tractable — not by trusting the LLM's self-report, but by examining the evidence directly. Without intermediate artifacts, verification is impossible at scale; with them, it is demanding but achievable.

**Why not a chat UI**

Chat interfaces produce output. They do not produce accountable output. Every run is ephemeral; collaboration requires copying text between sessions; applying the same framework to 200 passages requires 200 separate interactions; there is no record of what the LLM received, no mechanism for protecting editorial work, no way to know whether a change improved the result.

**Why not custom scripts or general-purpose frameworks**

Custom scripts work until the second person tries to run them, or the original author returns six months later. Without shared conventions for saving intermediate results, logging, and error handling, every project reinvents the same infrastructure. General-purpose frameworks like LangChain are built for developers building applications, not for scholars running content generation at corpus scale.

---

## Content Outline: content-creation-methodology.md

**Part 1: Generating content with `sp run`**

1. **Design the pipeline before running it** — think through steps; lint early; use `--dry-run` to verify structure before spending on API calls
2. **Prompt contracts** — `requires:` declares what the LLM needs; prevents silent failures from missing context; how to write and validate them
3. **Intermediate outputs** — why `saveas` matters; inspecting step outputs; using the log and verbose mode
4. **Iterating on prompts** — how `--rewind-to` allows improving a step without rerunning the whole pipeline
5. **Running at scale** — `for-each` for corpus-wide generation; monitoring partial runs; resuming interrupted runs with `--resume`

**Part 2: Working with generated content in `sp gui`**

6. **The content lifecycle** — what stages mean (generated, editing, approved); why the separation exists; how permissions are enforced
7. **Promoting a file to editing** — how a file moves from the generated stage to a protected editing stage
8. **Diffing generated vs. edited** — comparing the pipeline's latest output against your edited version; deciding what to keep
9. **Approving and committing** — transitioning to approved; git integration for team workflows
10. **When the pipeline regenerates** — running the pipeline again updates the generated stage only; the edited version is untouched; the scholar decides when and whether to incorporate changes

**Part 3: The verification loop**

11. **Auditing intermediate outputs** — what to look for; when to fix a prompt vs. accept and edit
12. **The collaboration loop** — pipeline generates, scholar reviews in the GUI, pipeline never touches the editing or approved stages

---

## Files to Create/Change

| File | Action |
|------|--------|
| `docs/why-LLMFlow.md` | Replace with `why-scripture-pipelines.md` (rename + rewrite) |
| `docs/content-creation-methodology.md` | New file |
| `docs/content-creation-drift-patterns.md` | New file (Option C/D only) |

The rename matches the CLI name (`sp`) and audience framing. Internal links to the old filename should be updated.

---

## Open Questions

1. Should the drift patterns piece go here or in human-at-the-helm? The general framework is there; the scripture-specific examples would be here or there.
2. Should `content-creation-methodology.md` live in `docs/` or be a top-level `METHODOLOGY.md`?
3. The tutorial.md is currently a bare "hello world." Should it be expanded into a real walkthrough of a scripture pipeline (e.g., the storytelling-dictionary pattern), or kept minimal and let the methodology doc do the work?
