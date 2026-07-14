# XQuery Analytics for Greek Lowfat Trees
## Use Cases Document

**Version:** 1.0
**Date:** March 27, 2026
**Status:** Proposed

---

## Executive Summary

This document proposes XQuery-based analytics for the Macula Greek Lowfat tree corpus, the XML representation of the SBLGNT/Nestle1904 with full syntactic annotation. XQuery enables analytical queries across morphological data, syntactic structures, and discourse features without the overhead of import operations. The hierarchical tree structure makes XQuery the natural fit for syntactic queries, clause-level analysis, and discourse segmentation.

**Key Benefits:**
- Native tree traversal (parent/ancestor/descendant axes)
- GROUP BY for aggregations across syntactic units
- Window functions for clause sequencing and participant tracking
- Direct XML access (no preprocessing)
- XQuery 3.1 higher-order functions for complex patterns
- Integration with BaseX database for sub-second queries

---

## Table of Contents

1. [Data Structure](#data-structure)
2. [Use Cases](#use-cases)
3. [Architecture](#architecture)
4. [XQuery Examples](#xquery-examples)
5. [Integration with LLMFlow](#integration-with-llmflow)
6. [Performance Considerations](#performance-considerations)

---

## Data Structure

### Lowfat XML Format

Macula Greek Lowfat is a flattened tree representation designed for XQuery:

```xml
<sentence>
  <wg class="cl" type="VerbElided" role="s">
    <w ref="MAT 1:1!1" lemma="βίβλος" normalized="βίβλος"
       unicode="Βίβλος" gloss="book" pos="noun"
       case="nominative" gender="feminine" number="singular"
       morph="N-NSF" role="s">Βίβλος</w>
    <w ref="MAT 1:1!2" lemma="γένεσις" normalized="γενέσεως"
       unicode="γενέσεως" gloss="origin" pos="noun"
       case="genitive" gender="feminine" number="singular"
       morph="N-GSF" role="o">γενέσεως</w>
    <!-- more words -->
  </wg>
</sentence>
```

**Key Elements:**
- `<sentence>` — Sentence boundary
- `<wg>` — Word group (phrase/clause)
  - `@class` — Syntactic category: `cl` (clause), `np` (noun phrase), `vp` (verb phrase), `pp` (prepositional phrase)
  - `@type` — Clause type: `VerbElided`, `Verbless`, `Minor`
  - `@role` — Syntactic role: `s` (subject), `p` (predicate), `o` (object), `io` (indirect object), `vc` (verbal complement), `adv` (adverbial)
- `<w>` — Word token with full morphology

**Attributes on `<w>`:**
- `@ref` — Verse reference (e.g., `MAT 1:1!1`)
- `@lemma` — Dictionary form
- `@normalized` — Normalized form (with accents)
- `@unicode` — Surface form as it appears in text
- `@gloss` — English gloss
- `@pos` — Part of speech
- `@case`, `@gender`, `@number`, `@person`, `@tense`, `@voice`, `@mood` — Morphological features
- `@morph` — Full morphology code
- `@ln` — Louw-Nida semantic domain (e.g., `33.260`)
- `@domain` — Semantic domain description
- `@role` — Syntactic role within clause

---

## Use Cases

### UC-1: Verb Frequency by Tense/Voice
**Goal:** Generate frequency distributions of verb forms for grammar instruction

**User Story:**
*"As a Greek instructor, I want to see how often each tense-voice combination appears in the Gospels vs Epistles, to prioritize teaching paradigms."*

**Query Pattern:**
```xquery
(: Verb frequency by tense, voice, and corpus section :)
declare variable $books external := ("MAT", "MRK", "LUK", "JHN");

let $verbs := db:get("macula-greek")//w[@pos="verb"]
                [starts-with(@ref, $books)]

return
  <results>{
    for $v in $verbs
    let $tense := string($v/@tense)
    let $voice := string($v/@voice)
    group by $tense, $voice
    order by count($v) descending
    return <combination tense="{$tense}" voice="{$voice}"
                        count="{count($v)}"
                        pct="{round-half-to-even(100 * count($v) div count($verbs), 2)}"/>
  }</results>
```

**Output:** XML with frequency counts, ready for LLM processing or CSV export

---

### UC-2: Clause Type Distribution
**Goal:** Identify discourse patterns via clause classification

**User Story:**
*"As a discourse analyst, I want to see the distribution of clause types (verbal, verbless, verb-elided) across narrative vs teaching sections."*

**Query Pattern:**
```xquery
(: Clause type distribution by book :)
let $clauses := db:get("macula-greek")//wg[@class="cl"]

return
  <clause-types>{
    for $cl in $clauses
    let $book := substring-before(($cl//w/@ref)[1], " ")
    let $type := string($cl/@type)
    group by $book, $type
    order by $book, count($cl) descending
    return <entry book="{$book}" type="{$type}" count="{count($cl)}"/>
  }</clause-types>
```

---

### UC-3: Participant Tracking with Window Functions
**Goal:** Detect subject continuity and topic shifts

**User Story:**
*"As a narrative analyst, I want to track when the grammatical subject changes across clauses, to identify episode boundaries."*

**Query Pattern:**
```xquery
(: Participant tracking — subject continuity across clauses :)
declare variable $passage external := "MRK 1";

let $clauses := db:get("macula-greek")//wg[@class="cl"]
                  [starts-with((descendant::w/@ref)[1], $passage)]

for $cl at $pos in $clauses
let $ref := (($cl//w/@ref)[1])
let $subject_words := $cl//w[@role="s"]
let $subject_lemmas := string-join($subject_words/@lemma, "+")
let $prev_lemmas :=
  if ($pos > 1) then
    string-join($clauses[$pos - 1]//w[@role="s"]/@lemma, "+")
  else ""
let $switch := if ($subject_lemmas ne $prev_lemmas) then "SWITCH" else "CONTINUE"

return <clause ref="{$ref}"
               subject="{$subject_lemmas}"
               signal="{$switch}"
               position="{$pos}"/>
```

**Output:** Episode boundary hints for discourse-flow pipeline

---

### UC-4: Collocation Discovery (Verb + Preposition)
**Goal:** Find idiomatic verb-preposition combinations

**User Story:**
*"As a lexicographer, I want to find Greek verbs that frequently occur with specific prepositions, to document phrasal semantics."*

**Query Pattern:**
```xquery
(: Verb-preposition collocations with statistical ranking :)
let $collocations :=
  for $vp in db:get("macula-greek")//wg[@class="vp"]
  let $verb := $vp/w[@pos="verb"]
  let $prep_phrase := $vp//wg[@class="pp"]
  let $prep := $prep_phrase/w[@pos="prep"]
  where exists($verb) and exists($prep)
  return <pair>
    <verb lemma="{$verb/@lemma}" gloss="{$verb/@gloss}"/>
    <prep lemma="{$prep/@lemma}" gloss="{$prep/@gloss}"/>
  </pair>

return
  <collocations>{
    for $p in $collocations
    let $verb_lemma := string($p/verb/@lemma)
    let $prep_lemma := string($p/prep/@lemma)
    group by $verb_lemma, $prep_lemma
    let $freq := count($p)
    where $freq >= 5
    order by $freq descending
    return <entry verb="{$verb_lemma}"
                  prep="{$prep_lemma}"
                  frequency="{$freq}"
                  gloss="{$p[1]/verb/@gloss} + {$p[1]/prep/@gloss}"/>
  }</collocations>
```

---

### UC-5: Syntactic Pattern Mining (Clause Structure)
**Goal:** Extract recurring syntactic structures for grammar teaching

**User Story:**
*"As a syntax teacher, I want to find common clause patterns (e.g., verb-subject-object, subject-verb-complement) with authentic examples."*

**Query Pattern:**
```xquery
(: Extract clause role patterns :)
let $clauses := db:get("macula-greek")//wg[@class="cl"]

return
  <clause-patterns>{
    for $cl in $clauses
    let $pattern := string-join($cl//w/@role, "-")
    let $example := string-join($cl//w/@unicode, " ")
    let $ref := ($cl//w/@ref)[1]
    group by $pattern
    let $freq := count($cl)
    where $freq >= 10 and string-length($pattern) > 0
    order by $freq descending
    return <pattern structure="{$pattern}"
                    frequency="{$freq}"
                    example="{($cl[1]//w/@unicode => string-join(' '))[1]}"
                    example-ref="{($cl[1]//w/@ref)[1]}"/>
  }</clause-patterns>
```

---

### UC-6: Semantic Domain Analysis (Louw-Nida)
**Goal:** Map semantic field distribution across books

**User Story:**
*"As a biblical theologian, I want to see which semantic domains (Louw-Nida) dominate in different NT books, to understand thematic emphasis."*

**Query Pattern:**
```xquery
(: Semantic domain frequency by book :)
let $words := db:get("macula-greek")//w[@ln]

return
  <semantic-domains>{
    for $w in $words
    let $book := substring-before($w/@ref, " ")
    let $domain := string($w/@ln)
    group by $book, $domain
    order by $book, count($w) descending
    return <entry book="{$book}"
                  domain="{$domain}"
                  description="{$w[1]/@domain}"
                  count="{count($w)}"/>
  }</semantic-domains>
```

---

### UC-7: Discourse Connective Analysis
**Goal:** Track conjunctions and their clause-linking patterns

**User Story:**
*"As a discourse linguist, I want to analyze how conjunctions (καί, δέ, γάρ, οὖν) pattern across clause boundaries in narrative."*

**Query Pattern:**
```xquery
(: Discourse connectives with following clause type :)
let $connectives := ("καί", "δέ", "γάρ", "οὖν", "ἀλλά")

for $w in db:get("macula-greek")//w[@lemma = $connectives]
let $clause := $w/ancestor::wg[@class="cl"][1]
let $clause_type := string($clause/@type)
let $connective := string($w/@lemma)
group by $connective, $clause_type
order by count($w) descending
return <connective lemma="{$connective}"
                   clause-type="{$clause_type}"
                   count="{count($w)}"
                   pct="{round(100 * count($w) div count(db:get('macula-greek')//w[@lemma = $connectives]), 2)}"/>
```

---

### UC-8: Nested Phrase Depth Analysis
**Goal:** Measure syntactic complexity via embedding depth

**User Story:**
*"As a readability researcher, I want to measure phrase nesting depth to identify structurally complex passages."*

**Query Pattern:**
```xquery
(: Calculate maximum nesting depth per clause :)
declare function local:depth($node) {
  if ($node/wg) then
    1 + max($node/wg ! local:depth(.))
  else
    0
};

let $clauses := db:get("macula-greek")//wg[@class="cl"]

for $cl in $clauses
let $ref := ($cl//w/@ref)[1]
let $depth := local:depth($cl)
where $depth > 3
order by $depth descending
return <complex-clause ref="{$ref}"
                       depth="{$depth}"
                       text="{string-join($cl//w/@unicode, ' ')}"/>
```

---

### UC-9: Genitive Chain Analysis
**Goal:** Identify and analyze genitive noun chains

**User Story:**
*"As a Greek grammarian, I want to find long genitive chains (e.g., 'the word of the truth of the gospel') to teach the genitive case."*

**Query Pattern:**
```xquery
(: Find genitive chains of length >= 3 :)
for $np in db:get("macula-greek")//wg[@class="np"]
let $genitives := $np/w[@case="genitive"]
where count($genitives) >= 3
return <genitive-chain ref="{($np//w/@ref)[1]}"
                       length="{count($genitives)}"
                       lemmas="{string-join($genitives/@lemma, ' + ')}"
                       text="{string-join($np//w/@unicode, ' ')}"/>
```

---

### UC-10: Imperative Clustering (Ethical Teaching Sections)
**Goal:** Detect concentrations of imperative verbs in parenetic passages

**User Story:**
*"As an ethics scholar, I want to find passages with high imperative density, indicating ethical instruction sections."*

**Query Pattern:**
```xquery
(: Imperative density by chapter :)
let $words := db:get("macula-greek")//w

for $w in $words
let $chapter_ref := substring-before($w/@ref, ":")
let $is_imperative := $w[@pos="verb" and @mood="imperative"]
group by $chapter_ref
let $total_words := count($w)
let $imperative_count := count($is_imperative)
let $density := if ($total_words > 0) then
                  round-half-to-even(100 * $imperative_count div $total_words, 2)
                else 0
where $density > 5.0
order by $density descending
return <chapter ref="{$chapter_ref}"
                imperatives="{$imperative_count}"
                total-words="{$total_words}"
                density-pct="{$density}"/>
```

---

## Integration with LLMFlow

### BaseX Step Type

LLMFlow already supports `type: basex` for running XQuery:

```yaml
steps:
  - name: extract_clause_patterns
    type: basex
    database: macula-greek
    query_file: queries/clause-patterns.xq
    params:
      book: "${book}"
      min_frequency: 10
    outputs: clause_data
    timeout: 60
```

**Query file** (`queries/clause-patterns.xq`):
```xquery
declare variable $book external;
declare variable $min_frequency external;

let $clauses := db:get("macula-greek")//wg[@class="cl"]
                  [starts-with((descendant::w/@ref)[1], $book)]
(: ... rest of query ... :)
```

### Pipeline Example: Syntax → Pedagogy

```yaml
name: greek-syntax-guide
description: Generate pedagogical syntax descriptions from corpus patterns

variables:
  book: "${book}"
  output_dir: output/syntax

steps:
  # 1. Extract clause patterns via XQuery
  - name: extract_patterns
    type: basex
    database: macula-greek
    query_file: queries/clause-patterns.xq
    params:
      book: "${book}"
      min_frequency: 5
    outputs: patterns_xml

  # 2. Parse XML result to structured data
  - name: parse_patterns
    type: function
    function: llmflow.utils.data.parse_xml_to_dict
    inputs:
      xml_string: "${patterns_xml}"
    outputs: patterns_data

  # 3. Generate pedagogical descriptions
  - name: explain_patterns
    type: llm
    prompt:
      file: prompts/explain_syntax_patterns.gpt
      inputs:
        patterns: "${patterns_data}"
        book: "${book}"
    outputs: syntax_guide

  # 4. Save output
  - name: save_guide
    type: save
    content: "${syntax_guide}"
    path: "${output_dir}/${book}_syntax_guide.md"
```

---

## Performance Considerations

### BaseX Indexing

For optimal query performance, create appropriate indexes:

```bash
basex -c "OPEN macula-greek; CREATE INDEX @ref; CREATE INDEX @lemma; CREATE INDEX @pos"
```

**Index types:**
- **Attribute index** — Fast lookups on `@ref`, `@lemma`, `@pos`, `@role`
- **Full-text index** — Text search on `@unicode`, `@gloss`
- **Path index** — Faster XPath evaluation for complex queries

### Query Optimization

**Best practices:**
1. **Filter early:** Use predicates close to the axis step
   ```xquery
   (: Good :)
   db:get("macula-greek")//wg[@class="cl" and starts-with((w/@ref)[1], "MAT")]

   (: Bad — filters too late :)
   db:get("macula-greek")//wg[@class="cl"][starts-with((descendant::w/@ref)[1], "MAT")]
   ```

2. **Use `let` for reused values:**
   ```xquery
   let $clauses := db:get("macula-greek")//wg[@class="cl"]
   return count($clauses) (: reuse binding :)
   ```

3. **Leverage GROUP BY:** More efficient than nested loops
   ```xquery
   (: Good — O(n) :)
   for $w in $words
   group by $lemma := $w/@lemma
   return <entry lemma="{$lemma}" count="{count($w)}"/>

   (: Bad — O(n²) :)
   for $lemma in distinct-values($words/@lemma)
   return <entry lemma="{$lemma}" count="{count($words[@lemma=$lemma])}"/>
   ```

### Benchmark Estimates

| Query Type | BaseX (indexed) | BaseX (no index) | File Scan |
|------------|-----------------|------------------|-----------|
| Simple word lookup | 0.05s | 2.1s | 8.5s |
| Clause aggregation | 0.3s | 4.2s | 15s |
| Nested GROUP BY | 0.8s | 12s | N/A |
| Window function (participant tracking) | 1.5s | 18s | N/A |

---

## Advantages Over TSV/CSV + DuckDB

1. **Native tree traversal:** `ancestor::`, `descendant::`, `following-sibling::` — impossible in flat tables
2. **Syntactic queries:** "Find all verbs inside prepositional phrases" — natural in XQuery, awkward in SQL
3. **No impedance mismatch:** XML → XQuery vs. XML → flatten → SQL
4. **Hierarchical grouping:** Group by clause, then by phrase type
5. **XPath abbreviations:** `//w[@pos='verb']` vs. messy LIKE patterns

## When to Use DuckDB Instead

- **Morphology-only queries:** If not using syntax tree structure, TSV + DuckDB is faster
- **Cross-dataset joins:** Combining Hebrew + Greek + English alignments
- **Window functions over flat sequences:** Running totals without tree context
- **Large-scale aggregations:** Millions of rows across multiple corpora

---

## Future Enhancements

### Planned XQuery Extensions

1. **Discourse annotation integration:** Connect Levinsohn-style markers to lowfat clauses
2. **Cross-reference resolution:** Track anaphora and pronoun resolution
3. **Parallel corpus queries:** Compare SBLGNT and Nestle1904 syntactic differences
4. **Semantic network generation:** Build word co-occurrence graphs from clause data

### LLMFlow Pipeline Features

1. **XQuery step result caching:** Cache expensive queries between runs
2. **Incremental XQuery updates:** Re-run only for changed verses
3. **XQuery → JSON converter:** Auto-convert XML results to JSON for LLM consumption
4. **Query visualization:** Generate syntax tree diagrams from XQuery results

---

## References

1. [BaseX Documentation](https://docs.basex.org/)
2. [XQuery 3.1 Specification](https://www.w3.org/TR/xquery-31/)
3. [Macula Greek Schema](https://github.com/Clear-Bible/macula-greek/tree/main/Nestle1904/lowfat)
4. [GBI Treebank Documentation](https://github.com/Clear-Bible/macula-greek/tree/main/docs)

---

**Contributors:** Jonathan Robie
**Status:** Draft for Implementation
