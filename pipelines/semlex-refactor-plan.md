# SemLex Multi-Pass Pipeline Rebuild Plan

## Current Situation
We have a working but overly complex 9-pass pipeline that uses alphabetic naming (Pass A, Pass B, etc.). This creates maintenance problems:
- Adding/removing steps requires renaming everything
- Purpose of each step is unclear from names
- No audit trail to understand what happened in processing
- **Most critically:** The XML→JSON transformation may be lossy or incorrect

## Goal
Replace with a clean 4-phase pipeline that:
1. **Starts with accurate data** (XML enhancement + JSON transformation)
2. Uses purpose-based naming (stable regardless of ordering)
3. Includes comprehensive audit trails in intermediate JSON
4. Consolidates related tasks into coherent phases
5. Reduces token usage and API calls

---

## PHASE 0: Data Foundation (Non-LLM)

**This must be perfect before any LLM work begins.**

### Step 0.1: Enhance Abbott-Smith XML
**Tool:** XSLT transformation
**Input:** Raw Abbott-Smith XML entries
**Output:** Enhanced XML with explicit structure

**Enhancements needed:**
- [ ] Make sense hierarchy explicit (I, I.1, I.2, II, etc.)
- [ ] Mark up citations consistently (biblical, classical, grammatical)
- [ ] Distinguish prose from glosses from Greek text
- [ ] Add structural metadata (entry type, part of speech)
- [ ] Validate against schema (if we have one)

**Validation:**
- [ ] Pick 10 diverse entries (article, noun, verb, particle, preposition)
- [ ] Manually verify XML structure is accurate
- [ ] Check no information lost from original
- [ ] Verify sense paths are unambiguous

**Deliverable:** `{lemma}.enhanced.xml` for each entry

### Step 0.2: Transform XML to LLM-Friendly JSON
**Tool:** XSLT transformation
**Input:** Enhanced XML from Step 0.1
**Output:** Structured JSON suitable for LLM processing

**JSON structure requirements:**
```json
{
  "lemma": "ὁ",
  "pos": "art.",
  "etymology": "...",
  "segments": [
    {
      "text": "As prepositive article",
      "type": "senseProse|gloss|foreign|ref",
      "lang": "grc|eng",
      "sensePath": "I.|I.1|I.2",
      "index": 0,
      "osisRef": "Matt.8.20"  // if type=ref
    }
  ]
}
```

**Requirements:**
- [ ] Every piece of information from XML appears in JSON
- [ ] Sense hierarchy preserved in `sensePath`
- [ ] Citations marked with OSIS references
- [ ] Greek text marked with `lang: "grc"`
- [ ] Glosses distinguished from definitions
- [ ] Order preserved (index field)

**Validation:**
- [ ] Round-trip test: XML → JSON → XML should be lossless
- [ ] Compare JSON to your existing `ὁ.base.fixed.json`
- [ ] Verify biblical references are valid OSIS format
- [ ] Check for duplicates (you had some in the attachment)
- [ ] Validate sense paths are consistent

**Deliverable:** `{lemma}.base.json` for each entry

### Step 0.3: Quality Assurance on Base Data
Before proceeding to LLM phases:
- [ ] Run XML enhancement on ALL Abbott-Smith entries
- [ ] Run JSON transformation on all enhanced XML
- [ ] Generate statistics:
  - Entries with parsing errors
  - Entries with invalid OSIS references
  - Entries with duplicate segments (like your ὁ example)
  - Entries with missing sense paths
- [ ] Fix systematic issues in XSLT
- [ ] Manual review of 20 random entries

**Gate:** Do NOT proceed to Phase 1 until base JSON is verified accurate for 95% of entries.

---

## PHASE 1: Evidence Gathering (LLM)

**Now we can use LLMs, working from clean base data.**

### Step 1.1: Define Test Cases
- [ ] Select 3 lemmas with perfect base JSON:
  - Simple: `ἀγάπη` (concrete noun)
  - Medium: `εἰμί` (verb)
  - Complex: `ὁ` (article)

### Step 1.2: Write `gather-evidence.gpt` Prompt
**Input:** `{lemma}.base.json` (from Phase 0)
**Output:** `{lemma}.evidence.json`

**Prompt instructions:**
- [ ] Load base JSON as foundation
- [ ] Consult external sources (BDAG, LSJ, Thayer, Smyth, BDF, Wallace, Runge, Levinsohn, Dik)
- [ ] Add segments from external sources
- [ ] Mark each segment with `source` field
- [ ] Generate audit trail
- [ ] DO NOT modify base segments (only add)

**JSON output:**
```json
{
  "lemma": "ὁ",
  "pos": "art.",
  "audit": {
    "phase": "evidence_gathering",
    "timestamp": "2025-11-13T14:23:45Z",
    "model": "gpt-4o",
    "temperature": 0.3,
    "tokens_used": 12453,
    "sources_consulted": ["Abbott-Smith", "BDAG", "LSJ", ...],
    "warnings": ["Levinsohn: no examples found"],
    "base_segments": 156,  // from base.json
    "added_segments": 47   // from external sources
  },
  "segments": [
    // All segments from base.json (unchanged)
    // Plus new segments from external sources
  ]
}
```

### Step 1.3: Run Phase 1 Only
- [ ] Configure pipeline to stop after `gather-evidence`
- [ ] Run on 3 test cases
- [ ] Compare segment counts to base JSON

### Step 1.4: Validate Phase 1 Output
For EACH test case:
- [ ] **Preservation:** All base.json segments present and unchanged
- [ ] **Attribution:** New segments marked with source
- [ ] **Completeness:** External sources consulted
- [ ] **No Duplicates:** No segments repeated
- [ ] **Audit Trail:** Token usage, sources, warnings logged
- [ ] **Token Limit:** Within 16,000 tokens

**Gate:** Do NOT proceed until all 3 test cases pass validation.

---

## PHASE 2: Verification (LLM + MCP)

### Step 2.1: Test MCP Integration
- [ ] Verify MCP server is running
- [ ] Test each tool manually:
  - `get_passage_text("John.3.16")`
  - `get_word_info("θεός", "G2316")`
  - `get_passages_for_word_sense("G2316", "1")`
- [ ] Document response formats

### Step 2.2: Write `verify-citations.gpt` Prompt
**Input:** `{lemma}.evidence.json`
**Output:** `{lemma}.verified.json`

**Verification logic:**
- [ ] For `type: "ref"`: Verify via MCP
- [ ] For grammar citations: Validate format (e.g., "Smyth §1234")
- [ ] Flag segments that can't be verified
- [ ] Enrich verified citations with Greek context
- [ ] Generate detailed audit trail

### Step 2.3: Run Phase 2
- [ ] Run on 3 test cases
- [ ] Review `audit.failed_citations`
- [ ] Review `audit.enrichments`

### Step 2.4: Validate Phase 2 Output
- [ ] **Accuracy:** Manually verify 10 random citations per entry
- [ ] **No False Positives:** Valid citations not rejected
- [ ] **No False Negatives:** Invalid citations not passed
- [ ] **Enrichment Quality:** Added context is helpful
- [ ] **Audit Trail:** MCP calls, failures, reasons logged

**Gate:** >95% verification accuracy on test cases.

---

## PHASE 3: Sense Analysis (LLM)

### Step 3.1: Define Quality Criteria
- [ ] Document "good sense structure" rules
- [ ] Create "bad examples" list (e.g., ὁ as demonstrative)
- [ ] Define minimum evidence per sense (>3 examples)

### Step 3.2: Write `analyze-senses.gpt` Prompt
**Input:** `{lemma}.verified.json`
**Output:** `{lemma}.senses.json`

**Analysis tasks:**
- [ ] Cluster by usage patterns (not etymology)
- [ ] Distinguish semantic/grammatical/discourse
- [ ] Exclude archaic senses for NT Greek
- [ ] Generate audit trail with decisions

### Step 3.3: Run Phase 3
- [ ] Run on 3 test cases
- [ ] Review `audit.decisions`

### Step 3.4: Validate Phase 3 Output
- [ ] **No Forbidden Senses:** Check bad examples list
- [ ] **Evidence:** Each sense has sufficient examples
- [ ] **Mutual Exclusivity:** No overlap between senses
- [ ] **NT Focus:** Senses ordered by NT frequency
- [ ] **Audit Trail:** Decisions logged with reasons

**Gate:** Sense structures are defensible for all 3 test cases.

---

## PHASE 4: Final Rendering (LLM)

### Step 4.1: Define Markdown Format
- [ ] Document exact formatting rules
- [ ] Create example target output

### Step 4.2: Write `render-entry.gpt` Prompt
**Input:** `{lemma}.senses.json` + `{lemma}.verified.json`
**Output:** `{lemma}.md`

### Step 4.3: Run Full Pipeline
- [ ] Run all phases on 3 test cases
- [ ] Generate final Markdown

### Step 4.4: Validate Phase 4 Output
- [ ] **Format:** Matches specification
- [ ] **Completeness:** All verified citations present
- [ ] **Allocation:** Each citation in exactly one sense
- [ ] **Readability:** Human-understandable

**Gate:** All 3 test cases are publication-quality.

---

## Batch Testing & Production

[Same as previous checklist, starting from "5.1 Expand Test Set"]

---

## Critical Success Factors

1. **Phase 0 is non-negotiable** - Bad input data = bad LLM output
2. **XSLT must be perfect** - Test exhaustively before LLM work
3. **Validate each phase** - Never proceed with failing test cases
4. **Audit trails everywhere** - Track what happened, not just results
5. **Manual review at gates** - LLMs are tools, humans decide quality

## Revised Timeline

- **Phase 0:** 8-12 hours (XSLT development + validation)
- **Phase 1:** 4-6 hours (prompt + validation)
- **Phase 2:** 4-6 hours (MCP integration + validation)
- **Phase 3:** 4-6 hours (prompt + validation)
- **Phase 4:** 2-4 hours (prompt + validation)
- **Batch testing:** 4-6 hours
- **Production:** 2 hours + runtime

**Total:** 28-42 hours (doubled to account for data foundation)

## Next Action
**Start with Phase 0.1:** Review/enhance the XSLT that transforms Abbott-Smith XML. This is the foundation of everything.