# Lessons Learned: Building a Semantic Lexicon Pipeline with LLMs

**SBL 2025 Presentation Notes**
Jonathan Robie, R&D Fellow, Biblica

**Nida Institute Context**: The Nida Institute exists to produce high‑value, freely licensed linguistic and biblical resources across silos—linking translation practice, exegesis, digital humanities, and computational linguistics—and to release them as open data for unrestricted reuse in multiple ecosystems.

---

## Original Proposal (Context for Audience Expectation)

> **The Kairos Semantic Lexicon of Biblical Greek (SemLex Greek)** is a freely licensed, synchronic dictionary drawing examples from New Testament, Septuagint, Hellenistic literature, papyri, and inscriptions. GPT helps identify root meanings and derived senses, compare sources, refine definitions, and assign semantic domains (SIL SemDom + Louw & Nida). Early results are promising; this session reports what works, what does not, and projected completion timeline.

Key promised elements:
- Freely licensed (CC BY-SA 4.0)
- Multi-corpus (NT, LXX, papyri, inscriptions)
- Semantic domains (SemDom + Louw & Nida)
- GPT-assisted first drafts + human editing
- Accessibility across education levels
- Workflow: Obsidian + GitHub versioning
- Focus groups (planned) for usability and multilingual release

---

## The Vision

Create a **modern, accessible Greek lexicon** that serves working pastors, students, translators.

### Alignment With Proposal
| Proposal Claim | Current State |
|----------------|---------------|
| Freely licensed | Implemented (CC BY-SA 4.0) |
| Multi-corpus sourcing | NT + LXX stable; papyri/inscriptions planned |
| GPT-assisted drafting | Working (single-pass enrichment) |
| Semantic domains | POC promising; scaling design underway |
| Focus groups | Planned Q1 next year |
| Multilingual output | Pipeline scaffolded; translation prompts pending |
| Obsidian + GitHub workflow | Active |
| Human editorial review | Manual spot checks; audit tooling in progress |

---

### What's Different from Traditional Lexicons
1. **Freely Licensed and Open Access** (core differentiator): anyone can use, integrate, translate, redistribute—just attribute and share alike.
2. **Complete Inline Examples**: no lookup friction; Greek + translation + context visible.
3. **Modern Terminology & Functional Definitions**: interpretive, not cryptic abbreviations.
4. **Discourse Awareness**: particles, articles, cohesion, participant tracking.
5. **Semantic Domains** (in design): cross-language conceptual mapping.
6. **Structured Entries**: machine-parseable + human-friendly.
7. **Expandable Corpus Layers**: core (NT/LXX) upfront; papyri/inscriptions collapsible.

---

## What Worked vs. Proposal Expectations

Worked:
- Direct XML → enhanced XML → single LLM pass.
- MCP inline enrichment for missing Greek phrases.
- Structured Markdown output with contextual explanation.
- Early semantic domain POC (high agreement in test set).

Did Not (Yet):
- Full semantic domain rollout (scaling beyond POC).
- Automated papyri & inscription harvesting.
- Reliable multi-pass improvement (was net-negative).
- Full multilingual workflow & focus group feedback.

---

## Pivot: From Multi-Pass Ambition to Single-Pass Preservation

Original intent: staged refinement (extract → evidence → verify → sense analysis → render).
Reality: each added LLM pass produced loss (examples, sense granularity, patterns).
Decision: collapse to single synthesis pass leveraging pre-parsed enhanced XML + precise MCP usage.

---

## Key Lessons (Mapped to Proposal Themes)

1. Preservation first, enrichment second.
2. Tool use (MCP) requires algorithmic guidance (not generic instructions).
3. Semantic domain tagging: POC strong; scale requires stable sense segmentation + confidence metrics.
4. Human review focuses best on flagged anomalies ([@review]) not full entries.
5. Accessibility improves adoption more than maximal scholarly density.
6. Freely licensed distribution multiplies downstream innovation (apps, translations).
7. Structured output enables future NLP (alignment, domain classification, cross-references).

---

## Status Toward Deliverables

| Component | Phase | Next Action |
|-----------|-------|-------------|
| NT + LXX examples | Stable | Increase phrase extraction precision for patterns |
| Papyri & inscriptions | Prototype | Build corpus connector & citation normalizer |
| Semantic domains | POC success | Pilot 50 lemma scaling + confidence scoring |
| Editorial audit | Partial | Implement automated citation verification |
| Multilingual output | Scaffolded | Add i18n key map & translator prompt |
| Focus groups | Pending | Define user tasks & evaluation rubric |
| Discourse notes | Emerging | Add particle and article function templates |
| License messaging | Active | Add attribution footer generator |

---

## Remaining Gaps (Expectation Management)

- Scaling semantic domain assignment from successful POC; need confidence metrics + reviewer workflow.
- Papyri / inscription coverage will be selective (used only for difficult or low-frequency lexemes).
- Rare / obscure lexemes need external cross-lexicon triangulation (LSJ, BDAG references—not copied text).
- Hebrew (WLC) correspondence usage still needs consistent extraction rules (MCP access is available).

---

## Roadmap (High-Level)

Phase 1 (Now): Solidify single-pass enrichment + audit tooling
Phase 2: Scale semantic domain classifier (SemDom → Louw & Nida mapping) using POC patterns
Phase 3: Integrate selective papyri / inscription examples (still strictly synchronic)
Phase 4: Focus group evaluation (English baseline); limited pilot translations (e.g., Spanish, French) only where qualified reviewers available

---

## Risks

| Risk | Mitigation |
|------|------------|
| Hallucinated Greek fragments | Strict MCP extraction algorithm + verification |
| Sense flattening | Preserve source hierarchy; forbid merging in prompt |
| Over-expansion for novices | Collapsible advanced sections |
| Domain misalignment | Confidence scoring + human validation |
| Misuse of papyri for diachronic claims | Clear labeling: synchronic illustrative only |

---

## Example (Proposal Goal Realization)

```markdown
### ἀνά (Preposition, G303)

Core Meaning: Distribution or upward movement extended to abstract ratio functions.

Sense 1: Distributive ("each, apiece")
NT: ἀνὰ δηνάριον τῆς ἡμέρας — “a denarius for the day” (Matt 20:9)
Papyri: ἀνὰ δραχμὰς δέκα — “at ten drachmas each” (P.Oxy. 1273) [@doc]
Function: Marks per-unit allocation in commercial or narrative distributions.
Domain (target): Quantity / Measurement (SemDom 57.xx)
```

---

## From Proposal Claim to Operational Reality

Proposal: “GPT dramatically simplifies our work.”
Reality: GPT helps only when:
- Given structured XML (not raw mixed content).
- Used for synthesis—not parsing or deterministic routing.
- Guided with explicit algorithms for tool usage.

Proposal: “Assign semantic domains.”
Reality: Requires stable sense segmentation first; delayed until enrichment reliable.

---

## Next Steps (Reframed)

We are refining scope; shipment depends on meeting clarity and reliability thresholds rather than completing every ambitious feature.

### Short-Term (Foundational)
- Stabilize single-pass enrichment (enhanced XML + MCP phrase extraction).
- Tighten pattern heuristics (e.g., distributive μέν/δέ, article + participle).
- Implement minimal citation audit (presence + basic validation; NT/LXX/WLC).
- Pilot semantic domain extension on additional high‑frequency lemmas (retain confidence scores).
- Define focus group task set (find a sense, compare two entries, judge usefulness).
- Establish release criteria (entry completeness, example accuracy, absence of hallucinated Greek).
- Prepare first data dump format (Markdown + JSON schema).

### Medium-Term (Team & Workflow)
- Form small editorial team (sense review + domain confirmation).
- Introduce selective papyri / inscription examples for ambiguous or low-frequency senses (clear synchronic labeling).
- Formalize Hebrew correspondence extraction rules using existing MCP access to WLC.
- Run initial focus group; apply feedback to formatting & explanation depth.
- Pilot one translation (e.g., Spanish) with reviewer loop; evaluate localization workflow.
- Add lightweight CI checks (missing fields, malformed references, confidence threshold flags).
- Document contributor guidelines (what to edit vs. what is generated).

### Long-Term (Expansion & Hardening)
- Scale semantic domain tagging beyond pilot (retain confidence + override mechanism).
- Broaden selective external corpora coverage while remaining synchronic.
- Add optional discourse function annotations for high-impact function words.
- Introduce automated anomaly detection (pattern mismatch, unexpected lemma absence).
- Package periodic versioned data releases; produce integration guide for downstream tools.
- Evaluate feasibility of limited multilingual set (only where review capacity exists).
- Continue reducing manual workload via targeted LLM assistance (not additional opaque pipeline stages).

### Guiding Principles
- Ship usefulness over exhaustive scholarly completeness.
- Preserve source structure; avoid sense flattening.
- Keep human editorial judgment for edge cases.
- Remain synchronic; diachronic notes only when clarifying present usage.
- License and publish everything openly on GitHub; no hosted service layer.

(Previous linear “Next Steps” list superseded by this phased outline.)

---

## Availability & Distribution

- Public GitHub repo: source TEI, XSLT transform, prompts, and final outputs (Markdown + JSON).
- Upstream authoritative source: Abbott-Smith TEI (base text).
- Correction policy: minimal, documented errata fixes (scribe errors, wrong references, malformed Greek) applied as patch layer (we keep ORIGINAL + PATCH diff; no silent changes).
- Not publishing every transient intermediate file (avoid clutter).
- Retained artifacts:
  - Original licensed source (Abbott-Smith TEI, untouched snapshot).
  - Errata patch file (machine-readable list of corrections with rationale).
  - Enhanced XML (stable, pre-parsed form derived after applying approved patches).
  - Final entries (Markdown + structured JSON).
  - Domain assignment file (when stable).
- Ephemeral processing stages (scratch, debug, experimental merges) excluded from releases.
- Optional debug bundles may be tagged separately (opt-in for researchers).
- License: CC BY-SA 4.0.
- Distribution approach: incremental tagged releases once enrichment + audit pass thresholds.
- Clear, minimal file taxonomy for easy downstream integration (no noise).

### Incremental Publishing
Small audited batches:
- Pass baseline checks (no hallucinated Greek, sense hierarchy intact).
- Changelog includes: new entries, modified entries, errata applied (ID + description).
- Immediately reusable.

Focus: useful core data, transparent corrections, not pipeline exhaust.

---

## Scope and Intent

We are not attempting to revolutionize lexicography. We ship a useful, freely licensed resource. We do apply documented corrections to Abbott-Smith where clear errors surface (wrong verse, truncated Greek, mis-keyed form). Each fix is logged (original value, corrected value, evidence source).

Parallel aim: explore where LLMs can measurably reduce lexicographer workload (drafting, pattern spotting, semantic domain preclassification, example retrieval) while keeping humans in control of:
- Final sense segmentation
- Example selection for edge cases
- Functional/discourse notes
- Quality and attribution integrity

LLMs supply structured candidate data; humans validate, prune, and finalize. Efficiency target: shift effort from repetitive extraction to higher‑value editorial judgment.
