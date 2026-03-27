# Pipeline Localization for Multilingual Output

## Problem Statement

Users of Scripture Pipelines often want output in languages other than English—particularly for the **top N languages** that modern LLMs handle well (Spanish, French, Portuguese, Swahili, Mandarin, Hindi, etc.). Currently, pipelines produce English-only output, requiring manual post-translation.

**Key Questions:**
1. What's the best architecture for multilingual pipeline output?
2. Does translating prompts into the target language improve output quality?
3. How do we balance quality, cost, and maintainability across languages?

---

## Current State

**English-only pipeline:**
```yaml
- name: explain_passage
  type: llm
  prompt_file: prompts/explain_context.gpt
  inputs:
    passage: "${passage_text}"
    culture: "${exegetical_culture}"
  outputs: explanation
```

**Prompt file** (`prompts/explain_context.gpt`):
```
You are a biblical scholar explaining cultural context.

Passage: {{passage}}
Historical context: {{culture}}

Provide a clear explanation suitable for Bible translators.
```

**Problem:** Output is always in English, even when the target audience speaks Swahili, French, or Mandarin.

---

## Design Options

### Option 1: Post-Translation (Simplest)

**Architecture:** Generate English → translate final output

```yaml
steps:
  # 1. Generate content in English
  - name: explain_passage
    type: llm
    prompt_file: prompts/explain_context.gpt
    inputs:
      passage: "${passage_text}"
    outputs: explanation_english

  # 2. Translate to target language
  - name: translate_output
    type: llm
    prompt: |
      Translate the following text to ${target_language}.
      Preserve technical terms and Scripture references.

      Text to translate:
      ${explanation_english}
    outputs: explanation_localized
```

**Pros:**
- Simple — one prompt file per content type
- Existing English prompts work as-is
- Easy to test (verify English first, then translation)

**Cons:**
- Two LLM calls per string (doubles cost and latency)
- Translation quality may degrade technical accuracy
- "Translationese" artifacts (unnatural phrasing)
- No cultural adaptation, just linguistic translation

**When to use:** Quick prototypes, low-resource languages where LLM struggles with direct generation

---

### Option 2: Native Language Prompts

**Architecture:** Translate prompt templates → generate directly in target language

**Prompt file** (`prompts/explain_context.es.gpt`):
```
Eres un erudito bíblico explicando el contexto cultural.

Pasaje: {{passage}}
Contexto histórico: {{culture}}

Proporciona una explicación clara adecuada para traductores de la Biblia.
```

**Pipeline:**
```yaml
variables:
  target_language: "es"  # ISO 639-1 code
  prompt_suffix: "${target_language}"

steps:
  - name: explain_passage
    type: llm
    prompt_file: "prompts/explain_context.${prompt_suffix}.gpt"
    inputs:
      passage: "${passage_text}"
      culture: "${exegetical_culture}"
    outputs: explanation
```

**Pros:**
- Single LLM call (50% cost savings vs. post-translation)
- More natural phrasing in target language
- Can adapt cultural examples for target audience
- Better tone and register control

**Cons:**
- Requires maintaining N prompt files (one per language)
- Prompt translation quality affects output quality
- Harder to ensure consistency across language versions
- Testing effort multiplies by number of languages

**When to use:** Major languages with significant user base (Spanish, French, Portuguese, Swahili, Mandarin)

**Quality Evidence (2024-2026 LLMs):**
- **GPT-4o, Claude 3.5, Gemini 2.0:** Native language prompts generally produce better results than post-translation for Spanish, French, German, Portuguese, Mandarin, Japanese, Arabic, Hindi
- **Smaller models (Llama 3, Mistral):** More variable—depends on training data balance
- **Low-resource languages:** Post-translation may be more reliable

---

### Option 3: Hybrid Approach (Prompt Injection)

**Architecture:** Keep English prompts, inject target language instruction

**Prompt file** (`prompts/explain_context.gpt`) — **unchanged English version**

**Pipeline:**
```yaml
variables:
  target_language: "Swahili"
  language_instruction: "IMPORTANT: Respond ONLY in ${target_language}. Do not use English."

steps:
  - name: explain_passage
    type: llm
    prompt_file: prompts/explain_context.gpt
    inputs:
      passage: "${passage_text}"
      culture: "${exegetical_culture}"
      language_override: "${language_instruction}"  # Injected at runtime
    outputs: explanation
```

**Prompt modification (automatic):**
```
IMPORTANT: Respond ONLY in Swahili. Do not use English.

You are a biblical scholar explaining cultural context.

Passage: {{passage}}
Historical context: {{culture}}

Provide a clear explanation suitable for Bible translators.
```

**Pros:**
- One prompt file maintained (English)
- Works reasonably well for top 20-30 languages
- Easy to add new languages (just add variable)
- Falls back gracefully if model ignores instruction

**Cons:**
- Less control over cultural adaptation
- Instruction-following varies by model
- May get mixed-language output (English + target)
- Slightly lower quality than native prompts

**When to use:** Moderate-resource languages, rapid prototyping, cost-sensitive applications

---

### Option 4: Prompt Library with Fallback Chain

**Architecture:** Try native prompt → fallback to hybrid → fallback to post-translation

```yaml
variables:
  target_language: "sw"  # Swahili
  fallback_chain: [ "native", "hybrid", "translate" ]

steps:
  - name: explain_passage
    type: function
    function: llmflow.localization.smart_generate
    inputs:
      prompt_base: "prompts/explain_context"
      target_language: "${target_language}"
      fallback_chain: "${fallback_chain}"
      passage: "${passage_text}"
      culture: "${exegetical_culture}"
    outputs: explanation
```

**Function logic:**
1. Check if `prompts/explain_context.sw.gpt` exists → use native prompt
2. Else, check if Swahili is in "hybrid-supported" list → inject instruction
3. Else, generate English → translate

**Pros:**
- Best quality for well-supported languages
- Graceful degradation for lesser-supported languages
- Maintainers can add native prompts incrementally
- Users get consistent interface

**Cons:**
- More complex implementation
- Requires maintaining language support metadata
- Harder to debug (which path was taken?)

**When to use:** Production systems serving diverse language needs

---

## Critical Design Question: Automatic Prompt Translation

### Should We Build an Auto-Translation Flag?

**Proposal:** Add a `--translate-prompts` flag that automatically translates English prompt files to the target language at runtime using LLM.

```bash
sp run --pipeline discourse-flow.yaml \
       --var target_language="es" \
       --translate-prompts
# Auto-translates prompts/explain_context.gpt → Spanish → generates output
```

**Under the hood:**
1. Load `prompts/explain_context.gpt` (English)
2. If `--translate-prompts` set and target ≠ English:
   - Call LLM: "Translate this prompt template to Spanish, preserving {{variable}} syntax"
   - Cache translation (to avoid re-translating every run)
   - Use translated prompt for generation

**Pros:**
- ✅ Zero maintenance burden (no `.es.gpt`, `.fr.gpt` files to maintain)
- ✅ Works for any language instantly (no upfront translation needed)
- ✅ Prompt updates in English automatically propagate to all languages
- ✅ Easy to test: compare auto-translated vs. manually-crafted prompts

**Cons:**
- ❌ Translation quality varies (especially for nuanced instructions)
- ❌ Adds latency to first run (mitigated by caching)
- ❌ Cache invalidation complexity (when to re-translate?)
- ❌ No opportunity for cultural adaptation (literal translation only)
- ❌ Harder to debug (can't read the actual prompt used)

---

### Is This Best for Top N Languages?

**TL;DR: No — for high-impact languages, manually-translated prompts are worth the investment.**

**Reasoning:**

1. **Quality ceiling:** Auto-translated prompts are "good enough" but rarely excellent. For Spanish, French, Portuguese, Mandarin (billions of speakers), the extra quality from native prompts justifies the cost.

2. **Cultural adaptation:** A Spanish prompt isn't just English words in Spanish — it should use Spanish rhetorical conventions, examples that resonate with Latin American or European Spanish speakers, and culturally appropriate framing. Auto-translation can't do this.

3. **Cost vs. value:**
   - Auto-translation adds ~1 LLM call per prompt per pipeline run (even with caching, cache misses happen)
   - Manual translation: one-time cost of $50-200 per language for 10 core prompts
   - Break-even: if >100 runs in target language, manual beats auto

4. **Quality compounding:** Poor prompt → poor output. If the prompt translation is "good but slightly off," every output generated from it inherits that degradation. For production use cases (Bible translation guide, theological resources), this matters.

5. **Community trust:** Users in Top N languages expect first-class support, not "auto-translated from English." Native prompts signal commitment to quality.

**Recommended strategy:**

| Language Tier | Approach | Rationale |
|--------------|----------|-----------|
| **Tier 1** (Spanish, French, Portuguese, Mandarin, Swahili) | Manual translation | High-impact languages, quality matters, cost justified |
| **Tier 2** (Arabic, Hindi, Korean, Tagalog, Amharic) | Hybrid: manual for critical prompts, auto for rest | Balance quality and maintenance |
| **Tier 3** (All others) | Auto-translation | Enable broad coverage without overwhelming maintenance |

**Implementation:**
- Build the `--translate-prompts` flag for Tier 3 languages
- But invest in manual `.es.gpt`, `.fr.gpt`, etc. for Tier 1
- Use auto-translation as a **prototyping tool** to generate first drafts that native speakers then refine

**Analogy:** It's like software localization — you _could_ use Google Translate for your UI strings, but Stripe, Notion, and GitHub all hire professional translators for major languages because quality matters.

---

## Worked Use Cases

### Use Case 1: Discourse Flow Guide (Swahili)

**Scenario:** Generate discourse analysis guide for Swahili Bible translation team

**Current (English only):**
```bash
sp run --pipeline discourse-flow.yaml --var book="Mark 1:1-15"
# Output: output/discourse/Mark_1_1-15_guide.md (English)
```

**Desired (Swahili):**
```bash
sp run --pipeline discourse-flow.yaml \
       --var book="Mark 1:1-15" \
       --var target_language="sw"
# Output: output/discourse/Mark_1_1-15_guide_sw.md (Swahili)
```

**Implementation (Option 2 - Native Prompts):**

1. Translate prompt templates to Swahili:
   - `prompts/explain_discourse_structure.sw.gpt`
   - `prompts/explain_pericope_boundaries.sw.gpt`
   - `prompts/explain_participant_tracking.sw.gpt`

2. Update pipeline:
```yaml
variables:
  target_language: "${target_language:-en}"
  prompt_suffix: "${target_language}"

steps:
  - name: explain_structure
    type: llm
    prompt_file: "prompts/explain_discourse_structure.${prompt_suffix}.gpt"
    # ... rest of step
```

3. One-time translation of 3 prompts (300 words total) → enables infinite Swahili output

**Cost Analysis:**
- **Option 1 (post-translate):** 2 LLM calls per output = ~$0.03/guide
- **Option 2 (native):** 1 LLM call per output = ~$0.015/guide
- **Break-even:** After ~20 guides, native prompts are cheaper

---

### Use Case 2: Vocabulary Lists (Spanish, French, Portuguese)

**Scenario:** Generate vocabulary frequency lists for Romance-language Bible translation projects

**Current:**
```bash
sp run --pipeline vocab-generator.yaml --var book="Exodus"
# Output: output/vocab/Exodus_top_500_verbs.md (English glosses)
```

**Desired:**
```bash
sp run --pipeline vocab-generator.yaml \
       --var book="Exodus" \
       --var target_language="es"
# Output includes Spanish glosses and explanations
```

**Implementation (Option 3 - Hybrid):**

1. Keep English prompt unchanged
2. Add language override in pipeline:

```yaml
variables:
  target_language: "${target_language:-en}"
  language_names:
    en: "English"
    es: "Spanish"
    fr: "French"
    pt: "Portuguese"
  language_instruction: |
    IMPORTANT: Generate all explanations in ${language_names[target_language]}.
    Keep Hebrew lemmas unchanged. Translate glosses and descriptions.

steps:
  - name: extract_vocabulary
    type: duckdb
    query_file: queries/verb_frequency.sql
    # ... (language-agnostic query)

  - name: explain_vocabulary
    type: llm
    prompt_file: prompts/explain_verbs.gpt
    inputs:
      verbs: "${verb_data}"
      language_override: "${language_instruction}"
    outputs: vocab_guide
```

**Result:** Same prompt file works for Spanish, French, Portuguese (all well-supported by GPT-4o/Claude)

---

### Use Case 3: Exegetical Notes (Mandarin)

**Scenario:** Generate cultural background notes for Mandarin-speaking translators

**Challenge:** Mandarin requires different rhetorical structure and cultural examples

**Implementation (Option 4 - Smart Fallback):**

1. Create high-quality Mandarin prompt for critical content:
   - `prompts/cultural_background.zh.gpt` (professional translation)

2. Use hybrid approach for less critical content:
   - `prompts/technical_terms.gpt` (English + injection)

3. Pipeline configuration:
```yaml
variables:
  target_language: "zh"

steps:
  # Critical content - use native Mandarin prompt
  - name: cultural_background
    type: llm
    prompt_file: "prompts/cultural_background.${target_language}.gpt"
    outputs: background

  # Technical content - hybrid approach
  - name: explain_terms
    type: llm
    prompt_file: "prompts/technical_terms.gpt"
    inputs:
      language_override: "Respond in Mandarin Chinese (简体中文)"
    outputs: terms
```

**Quality tiers:**
- **Tier 1 (Mandarin, Spanish, French):** Native prompts for all content
- **Tier 2 (Portuguese, Arabic, Hindi):** Native prompts for critical content, hybrid for rest
- **Tier 3 (Swahili, Tagalog, Amharic):** Hybrid for all

---

## Recommended Approach

### Phase 1: Hybrid Infrastructure (Q2 2026)

**Rationale:** Enables immediate multilingual support without N× prompt maintenance

1. Add `target_language` variable to all pipelines
2. Implement automatic language instruction injection
3. Test with Spanish, French, Portuguese, Swahili
4. Document language quality tiers

**Implementation:**
```yaml
# Add to all pipeline templates
variables:
  target_language: "${target_language:-en}"
  language_instruction: |
    ${if(target_language != 'en',
         'IMPORTANT: Generate output in ' + language_names[target_language],
         '')}
```

### Phase 2: Native Prompts for Top Languages (Q3 2026)

**Rationale:** Invest in quality for high-impact languages

1. Spanish: ~500M speakers, major Bible translation market
2. French: ~300M speakers, Francophone Africa
3. Portuguese: ~250M speakers, Brazil + Africa
4. Swahili: ~200M speakers, East Africa
5. Mandarin: ~1B speakers, growing interest in biblical resources

**Process:**
- Professional translation of core prompts (~10 prompts × 5 languages = 50 files)
- A/B test vs. hybrid approach
- Measure quality improvement and user satisfaction

### Phase 3: Community-Contributed Prompts (Q4 2026)

**Rationale:** Leverage native speakers for less common languages

1. Create contribution guidelines for prompt translation
2. Set up review process (quality checks, test runs)
3. Publish language coverage matrix

---

## Open Questions

1. **Auto-translation flag priority:** Should we build `--translate-prompts` in Phase 1 (as a fallback) or Phase 3 (after manual translations prove valuable)?
2. **Model selection by language:** Should we recommend GPT-4o for Spanish/French but Claude for Mandarin?
3. **Quality metrics:** How do we measure localization quality? (BLEU? Human eval?)
4. **Cultural adaptation:** Should prompts include culture-specific examples? (e.g., African proverbs for Swahili output)
5. **Mixed-language input:** How to handle Hebrew/Greek text in non-English explanations?
6. **Terminology consistency:** Should we maintain glossaries across languages?
7. **Cache strategy:** If we implement auto-translation, how to cache? (Hash of English prompt + target language? Time-based expiry?)

---

## Implementation Checklist

- [ ] **Decide:** Build auto-translation flag now or defer until Phase 3?
- [ ] Add `target_language` variable support to pipeline engine
- [ ] Implement language instruction injection (hybrid approach)
- [ ] Create language support metadata file (`languages.yaml`)
- [ ] Write utility function: `smart_generate()` with fallback chain
- [ ] **If auto-translation:** Implement `--translate-prompts` flag with caching
- [ ] Translate 5 core prompts to Spanish (pilot)
- [ ] A/B test: native Spanish prompts vs. hybrid vs. auto-translation
- [ ] Document best practices for prompt localization
- [ ] Create community contribution guide for new languages
- [ ] Add language quality tier to `sp --help` output

---

## Success Metrics

- **Coverage:** Support ≥10 languages by end of 2026
- **Quality:** Native speaker rating ≥4.0/5.0 for Tier 1 languages
- **Adoption:** ≥30% of pipeline runs use non-English output
- **Cost:** Average cost/output within 20% of English baseline
- **Maintenance:** ≤2 hours/month per additional language

---

## Related Issues

- #38 — BaseX collections for multilingual data
- #43 — Greek papyri (multilingual examples)
- TBD — Translation memory integration

---

## References

1. [OpenAI Model Capabilities by Language](https://platform.openai.com/docs/guides/text-generation)
2. [Anthropic Claude Language Support](https://docs.anthropic.com/claude/docs/models-overview#language-support)
3. [Google I18N Best Practices](https://developers.google.com/international/)
4. Zhu et al. (2024). "Evaluating Multilingual Prompt Quality for Large Language Models"

---

**Labels:** `enhancement`, `i18n`, `user-experience`, `multilingual`
**Milestone:** v0.3.0
**Priority:** High (major user request)
