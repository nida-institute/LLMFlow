# DuckDB Analytics Platform for Bible Data
## Design Document

**Version:** 1.0
**Date:** March 27, 2026
**Status:** Proposed

---

## Executive Summary

This document proposes a DuckDB-based analytics platform for biblical data from the awesome-biblical-data registry. DuckDB enables advanced analytical queries across morphological data, entity annotations, syntactic structures, and translations without requiring expensive data import operations. This platform will power new features in discourse-flow, paratext-pipelines, and enable entirely new analytical tools.

**Key Benefits:**
- Query TSV/CSV files directly without import
- 10-100x faster than SQLite for analytical queries
- Built-in ICU collation for all 7,000+ languages
- Window functions for discourse analysis
- Array/JSON support for complex structures
- Columnar storage for efficient aggregations

---

## Table of Contents

1. [Data Sources](#data-sources)
2. [Use Cases](#use-cases)
3. [Architecture](#architecture)
4. [SQL Examples](#sql-examples)
5. [Integration Points](#integration-points)
6. [Performance Considerations](#performance-considerations)
7. [Implementation Roadmap](#implementation-roadmap)

---

## Data Sources

From [awesome-biblical-data](https://github.com/nida-institute/awesome-biblical-data), these datasets are prime candidates for DuckDB analytics:

### 1. Macula Hebrew (TSV, 1.2M tokens)
- **Path:** `/Users/jonathan/github/Clear/macula-hebrew/tsv/`
- **Fields:** verse_id, word_id, text, lemma, gloss, pos, gender, number, person, tense, stem, state, pronominal_suffix, node_id
- **Size:** ~39 books × ~30K tokens each
- **Use Cases:** Morphological frequency, syntactic patterns, vocabulary analysis

### 2. Macula Greek (TSV, 138K tokens)
- **Path:** `/Users/jonathan/github/Clear/macula-greek/tsv/`
- **Fields:** verse_id, word_id, text, lemma, gloss, pos, case, gender, number, person, tense, voice, mood, node_id
- **Size:** 27 NT books
- **Use Cases:** NT syntax, translation comparison, Greek-Hebrew parallels

### 3. ACAI Entity Annotations (JSON, ~15K entities)
- **Path:** `/Users/jonathan/github/BibleAquifer/ACAI/*/json/`
- **Types:** people, places, deities, groups, fauna, flora, realia, keyterms
- **Fields:** id, type, label, description, references (verse IDs), relationships
- **Use Cases:** Character networks, geographic analysis, theme tracking

### 4. Clear Bible Alignments (TSV/JSON)
- **Description:** Word-level alignment between Hebrew/Greek and English translations
- **Use Cases:** Translation memory, consistency checking, semantic mapping

### 5. Levinsohn Hebrew Discourse Features
- **Path:** `/Users/jonathan/github/nida-institute/levinsohn-samuel-hebrew/`
- **Fields:** Discourse markers, participant tracking, clause boundaries
- **Use Cases:** Discourse boundary detection, rhetorical structure

---

## Use Cases

### UC-1: Morphological Frequency Analysis
**Goal:** Generate frequency lists for translation training materials

**User Story:**
*"As a translation trainer, I want to see the 1000 most frequent Hebrew verbs in narrative vs. poetry vs. wisdom literature, so I can prioritize vocabulary instruction."*

**Query Pattern:**
```sql
-- Top 100 verbs by genre (simplified)
SELECT
    genre,
    lemma,
    gloss,
    COUNT(*) as frequency,
    COUNT(DISTINCT verse_id) as verse_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY genre), 2) as pct_of_genre
FROM read_csv_auto('macula-hebrew/tsv/*.tsv')
WHERE pos = 'verb'
  AND book IN (CASE
      WHEN genre = 'narrative' THEN ('Genesis', 'Exodus', '1Samuel', '2Samuel')
      WHEN genre = 'poetry' THEN ('Psalms', 'Proverbs', 'Job')
      WHEN genre = 'wisdom' THEN ('Proverbs', 'Ecclesiastes', 'Song of Songs')
  END)
GROUP BY genre, lemma, gloss
QUALIFY ROW_NUMBER() OVER (PARTITION BY genre ORDER BY frequency DESC) <= 100
ORDER BY genre, frequency DESC
```

**Output:** CSV/JSON for curriculum development, prioritized word lists

**Existing Alternative:** Manual aggregation with pandas, ~100x slower

---

### UC-2: Participant Reference Tracking
**Goal:** Automatically detect when narrative focus shifts between characters

**User Story:**
*"As a discourse analyst, I want to track subject continuity across clauses to identify episode boundaries and participant prominence."*

**Query Pattern:**
```sql
WITH subjects AS (
    SELECT
        verse_id,
        word_id,
        lemma,
        gloss,
        ROW_NUMBER() OVER (PARTITION BY verse_id ORDER BY word_id) as word_position
    FROM macula_hebrew
    WHERE grammatical_role = 'subject'
),
subject_switches AS (
    SELECT
        verse_id,
        lemma as current_subject,
        gloss as current_label,
        LAG(lemma, 1) OVER (ORDER BY verse_id) as prev_subject,
        LAG(gloss, 1) OVER (ORDER BY verse_id) as prev_label,
        CASE
            WHEN lemma != LAG(lemma, 1) OVER (ORDER BY verse_id)
            THEN 'SWITCH'
            ELSE 'CONTINUE'
        END as discourse_signal
    FROM subjects
    WHERE word_position = 1  -- First subject in verse
)
SELECT
    verse_id,
    discourse_signal,
    current_subject,
    current_label,
    COUNT(*) OVER (
        ORDER BY verse_id
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as local_switch_density
FROM subject_switches
WHERE discourse_signal = 'SWITCH'
ORDER BY verse_id
```

**Output:** Episode boundary suggestions for discourse-flow pipeline

**Integration:** Feed results to LLM for refined segmentation

---

### UC-3: Collocation Discovery (Lexical Semantics)
**Goal:** Find words that frequently co-occur to identify idioms and semantic fields

**User Story:**
*"As a lexicographer, I want to find Hebrew noun-verb pairs that occur together frequently, to understand conventional expressions and build a collocation lexicon."*

**Query Pattern:**
```sql
-- Find noun-verb pairs that co-occur in same verse
WITH word_pairs AS (
    SELECT
        a.verse_id,
        a.lemma as noun_lemma,
        a.gloss as noun_gloss,
        b.lemma as verb_lemma,
        b.gloss as verb_gloss
    FROM macula_hebrew a
    JOIN macula_hebrew b
        ON a.verse_id = b.verse_id
        AND a.word_id < b.word_id
    WHERE a.pos = 'noun'
      AND b.pos = 'verb'
)
SELECT
    noun_lemma || ' + ' || verb_lemma as collocation,
    noun_gloss || ' + ' || verb_gloss as gloss,
    COUNT(*) as cooccurrence_count,
    COUNT(DISTINCT verse_id) as verse_count,
    -- PMI (Pointwise Mutual Information) for significance
    LOG2(
        (COUNT(*)::FLOAT / (SELECT COUNT(*) FROM word_pairs)) /
        ((SELECT COUNT(*) FROM macula_hebrew WHERE lemma = noun_lemma AND pos = 'noun')::FLOAT /
         (SELECT COUNT(*) FROM macula_hebrew)::FLOAT *
         (SELECT COUNT(*) FROM macula_hebrew WHERE lemma = verb_lemma AND pos = 'verb')::FLOAT /
         (SELECT COUNT(*) FROM macula_hebrew)::FLOAT)
    ) as pmi_score
FROM word_pairs
GROUP BY noun_lemma, noun_gloss, verb_lemma, verb_gloss
HAVING cooccurrence_count >= 5
ORDER BY pmi_score DESC
LIMIT 200
```

**Output:** Collocation dictionary with statistical significance

**Novel Capability:** PMI scoring impossible in simple pandas aggregation

---

### UC-4: Cross-Testament Translation Patterns
**Goal:** Map how Hebrew OT concepts are translated in the Greek NT

**User Story:**
*"As a biblical theologian, I want to see how key Hebrew theological terms (ברית covenant, חסד mercy, etc.) are rendered in LXX and NT citations, to track semantic development."*

**Query Pattern:**
```sql
-- Requires Clear Bible alignments data
WITH hebrew_occurrences AS (
    SELECT
        verse_id,
        lemma as hebrew_lemma,
        gloss as hebrew_gloss
    FROM macula_hebrew
    WHERE lemma IN ('ברית', 'חסד', 'אמת', 'צדקה')  -- Key theological terms
),
greek_translations AS (
    SELECT
        h.hebrew_lemma,
        h.hebrew_gloss,
        g.lemma as greek_lemma,
        g.gloss as greek_gloss,
        a.translation_type,  -- From alignment: literal, dynamic, paraphrase
        COUNT(*) as translation_count
    FROM hebrew_occurrences h
    JOIN alignments a ON h.verse_id = a.hebrew_verse
    JOIN macula_greek g ON a.greek_verse = g.verse_id
                        AND a.greek_word_id = g.word_id
    GROUP BY h.hebrew_lemma, h.hebrew_gloss, g.greek_lemma, g.greek_gloss, a.translation_type
)
SELECT
    hebrew_lemma,
    hebrew_gloss,
    greek_lemma,
    greek_gloss,
    translation_type,
    translation_count,
    ROUND(100.0 * translation_count / SUM(translation_count) OVER (PARTITION BY hebrew_lemma), 2) as pct_of_total
FROM greek_translations
ORDER BY hebrew_lemma, translation_count DESC
```

**Output:** Translation equivalence tables for lexicons, semantic shift analysis

---

### UC-5: Character Network Analysis
**Goal:** Map relationships between biblical characters across narrative

**User Story:**
*"As a Bible curriculum developer, I want to visualize which characters appear together in stories, to create relational study guides."*

**Query Pattern:**
```sql
-- Load ACAI data into DuckDB first (using load_acai_to_duckdb)
WITH verse_participants AS (
    SELECT
        verse_id,
        entity_name as person
    FROM acai_entities
    CROSS JOIN UNNEST(references) as t(verse_id)
    WHERE type = 'person'
),
co_occurrences AS (
    SELECT
        a.person as person1,
        b.person as person2,
        COUNT(DISTINCT a.verse_id) as shared_verses,
        LIST(DISTINCT a.verse_id ORDER BY a.verse_id) as verse_list
    FROM verse_participants a
    JOIN verse_participants b
        ON a.verse_id = b.verse_id
        AND a.person < b.person  -- Avoid duplicates
    GROUP BY a.person, b.person
    HAVING shared_verses >= 5
)
SELECT
    person1,
    person2,
    shared_verses,
    verse_list[1:5] as sample_verses  -- First 5 verses
FROM co_occurrences
ORDER BY shared_verses DESC
LIMIT 100
```

**Output:** Network graph data (nodes = people, edges = co-occurrences) for Gephi, D3.js, etc.

**Visualization:** Interactive character relationship explorer for nida-institute-website

---

### UC-6: Syntactic Pattern Mining
**Goal:** Find recurring syntactic structures for grammar instruction

**User Story:**
*"As a Hebrew teacher, I want to find common clause patterns (e.g., verb-subject-object, subject-verb-prepositional-phrase) with real examples."*

**Query Pattern:**
```sql
-- Extract clause patterns from Macula syntax trees
WITH clause_structures AS (
    SELECT
        verse_id,
        clause_id,
        STRING_AGG(pos || ':' || text, ' → ' ORDER BY word_id) as clause_pattern,
        STRING_AGG(pos, '-' ORDER BY word_id) as pos_pattern,
        STRING_AGG(gloss, ' ' ORDER BY word_id) as english_gloss
    FROM macula_hebrew
    WHERE clause_id IS NOT NULL
    GROUP BY verse_id, clause_id
)
SELECT
    pos_pattern,
    COUNT(*) as frequency,
    LIST(DISTINCT clause_pattern ORDER BY clause_pattern LIMIT 10) as example_clauses,
    LIST(DISTINCT english_gloss LIMIT 5) as sample_glosses
FROM clause_structures
WHERE LENGTH(pos_pattern) - LENGTH(REPLACE(pos_pattern, '-', '')) + 1 BETWEEN 3 AND 8  -- 3-8 words
GROUP BY pos_pattern
HAVING frequency >= 20
ORDER BY frequency DESC
LIMIT 50
```

**Output:** Grammar pattern catalog with authentic examples

---

### UC-7: Translation Difficulty Scoring
**Goal:** Identify verses that need expert attention based on vocabulary rarity

**User Story:**
*"As a translation consultant, I want to prioritize verse review based on lexical difficulty (rare words, hapax legomena) rather than reviewing linearly."*

**Query Pattern:**
```sql
WITH word_frequencies AS (
    SELECT
        lemma,
        COUNT(*) as corpus_frequency,
        COUNT(*) FILTER (WHERE corpus_frequency = 1) as is_hapax
    FROM macula_hebrew
    GROUP BY lemma
),
verse_difficulty AS (
    SELECT
        h.verse_id,
        COUNT(*) as word_count,
        SUM(CASE WHEN wf.corpus_frequency = 1 THEN 1 ELSE 0 END) as hapax_count,
        AVG(LOG(wf.corpus_frequency + 1)) as avg_log_frequency,
        MIN(wf.corpus_frequency) as rarest_word_freq
    FROM macula_hebrew h
    JOIN word_frequencies wf ON h.lemma = wf.lemma
    GROUP BY h.verse_id
)
SELECT
    verse_id,
    word_count,
    hapax_count,
    ROUND(avg_log_frequency, 2) as difficulty_score,
    rarest_word_freq,
    PERCENT_RANK() OVER (ORDER BY avg_log_frequency) as difficulty_percentile
FROM verse_difficulty
WHERE difficulty_percentile < 0.10  -- Hardest 10% of verses
ORDER BY difficulty_score ASC
LIMIT 100
```

**Output:** Priority translation review list for paratext-pipelines

---

### UC-8: Thematic Density Mapping
**Goal:** Track how themes develop across narrative arc

**User Story:**
*"As a biblical theology student, I want to see how covenant language intensifies or diminishes across the Pentateuch to understand literary structure."*

**Query Pattern:**
```sql
WITH covenant_vocabulary AS (
    SELECT unnest(['ברית', 'חסד', 'אמונה', 'שמר', 'קום']) as covenant_lemma
),
theme_density AS (
    SELECT
        h.book,
        h.chapter,
        COUNT(*) FILTER (WHERE h.lemma IN (SELECT covenant_lemma FROM covenant_vocabulary)) as covenant_words,
        COUNT(*) as total_words,
        ROUND(100.0 * covenant_words / NULLIF(total_words, 0), 2) as covenant_density
    FROM macula_hebrew h
    WHERE h.book IN ('Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy')
    GROUP BY h.book, h.chapter
    ORDER BY CASE h.book
        WHEN 'Genesis' THEN 1
        WHEN 'Exodus' THEN 2
        WHEN 'Leviticus' THEN 3
        WHEN 'Numbers' THEN 4
        WHEN 'Deuteronomy' THEN 5
    END, h.chapter
)
SELECT
    book,
    chapter,
    covenant_density,
    AVG(covenant_density) OVER (
        ORDER BY CASE book
            WHEN 'Genesis' THEN 1
            WHEN 'Exodus' THEN 2
            WHEN 'Leviticus' THEN 3
            WHEN 'Numbers' THEN 4
            WHEN 'Deuteronomy' THEN 5
        END, chapter
        ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
    ) as rolling_avg_density
FROM theme_density
ORDER BY CASE book
    WHEN 'Genesis' THEN 1
    WHEN 'Exodus' THEN 2
    WHEN 'Leviticus' THEN 3
    WHEN 'Numbers' THEN 4
    WHEN 'Deuteronomy' THEN 5
END, chapter
```

**Output:** Time-series data for theme intensity visualization

**Visualization:** Heatmap showing thematic peaks/troughs across books

---

### UC-9: Semantic Field Generation
**Goal:** Automatically cluster words into semantic domains

**User Story:**
*"As a lexicographer, I want to find words that share similar distributional patterns (appear in similar contexts) to generate semantic field candidates."*

**Query Pattern:**
```sql
-- Simplified: Find words that co-occur with same verbs (distributional similarity)
WITH word_verb_cooccurrence AS (
    SELECT
        n.lemma as noun,
        v.lemma as verb,
        COUNT(*) as cooccur_count
    FROM macula_hebrew n
    JOIN macula_hebrew v
        ON n.verse_id = v.verse_id
        AND n.pos = 'noun'
        AND v.pos = 'verb'
    GROUP BY n.lemma, v.lemma
),
similarity_matrix AS (
    SELECT
        a.noun as noun1,
        b.noun as noun2,
        SUM(LEAST(a.cooccur_count, b.cooccur_count)) as similarity_score
    FROM word_verb_cooccurrence a
    JOIN word_verb_cooccurrence b
        ON a.verb = b.verb
        AND a.noun < b.noun
    GROUP BY a.noun, b.noun
    HAVING similarity_score >= 3
)
SELECT
    noun1,
    noun2,
    similarity_score,
    RANK() OVER (PARTITION BY noun1 ORDER BY similarity_score DESC) as similarity_rank
FROM similarity_matrix
WHERE similarity_rank <= 10  -- Top 10 similar words for each noun
ORDER BY noun1, similarity_score DESC
```

**Output:** Word similarity graph for semantic domain construction

**Application:** Seed data for AI-assisted lexicon development

---

### UC-10: Multi-Version Alignment Analysis
**Goal:** Compare translation choices across versions (ESV, NIV, NASB, etc.)

**User Story:**
*"As a translation committee, we want to see where major English versions diverge in translating difficult passages, to understand interpretive options."*

**Query Pattern:**
```sql
-- Assumes alignment data for multiple English versions
WITH translation_divergence AS (
    SELECT
        h.verse_id,
        h.lemma as hebrew_lemma,
        h.gloss as hebrew_gloss,
        COUNT(DISTINCT e.english_gloss) as translation_variants,
        LIST(DISTINCT e.version || ':' || e.english_gloss ORDER BY e.version) as version_translations
    FROM macula_hebrew h
    JOIN alignments_english e ON h.verse_id = e.verse_id AND h.word_id = e.hebrew_word_id
    WHERE e.version IN ('ESV', 'NIV', 'NASB', 'CSB', 'NLT')
    GROUP BY h.verse_id, h.lemma, h.gloss
    HAVING translation_variants >= 3  -- At least 3 different translations
)
SELECT
    verse_id,
    hebrew_lemma,
    hebrew_gloss,
    translation_variants,
    version_translations
FROM translation_divergence
ORDER BY translation_variants DESC, verse_id
LIMIT 200
```

**Output:** Translation divergence report for exegetical review

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────┐
│         Awesome Biblical Data Registry          │
│  (ACAI, Macula Hebrew/Greek, Alignments, etc.)  │
└───────────────────┬─────────────────────────────┘
                    │
                    │ Direct file access (no import)
                    │
┌───────────────────▼─────────────────────────────┐
│              DuckDB Analytics Layer              │
│                                                  │
│  ┌──────────────┐  ┌─────────────┐             │
│  │ Query Engine │  │ ICU Collation│             │
│  │ (Columnar)   │  │ Support      │             │
│  └──────────────┘  └─────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌─────────────┐             │
│  │ Window Funcs │  │ Array/JSON  │             │
│  │ (Analytics)  │  │ Operations  │             │
│  └──────────────┘  └─────────────┘             │
└───────────────────┬─────────────────────────────┘
                    │
                    │ Python API (llmflow.utils.bible_data)
                    │
        ┌───────────┴───────────┬──────────────────┐
        │                       │                  │
┌───────▼────────┐   ┌──────────▼────────┐   ┌────▼─────────┐
│ discourse-flow │   │ paratext-pipelines│   │ New Analytics│
│   Pipeline     │   │                   │   │    Tools     │
└────────────────┘   └───────────────────┘   └──────────────┘
```

### Data Flow

1. **No Import Step:** DuckDB reads TSV/CSV/JSON directly
2. **Query Execution:** SQL sent to DuckDB engine
3. **Results:** Returned as Python objects (list, dict, DataFrame)
4. **Caching:** Optional per-session caching for repeated queries

---

## SQL Examples

### Example 1: Basic Morphology Query
```sql
-- Top 20 Hebrew nouns in Genesis
SELECT lemma, gloss, COUNT(*) as freq
FROM 'macula-hebrew/tsv/Genesis.tsv'
WHERE pos = 'noun'
GROUP BY lemma, gloss
ORDER BY freq DESC COLLATE 'he'
LIMIT 20
```

### Example 2: Multi-File Aggregation
```sql
-- Verb distribution across Pentateuch
SELECT
    filename,
    COUNT(*) FILTER (WHERE pos = 'verb') as verb_count,
    COUNT(*) as total_words,
    ROUND(100.0 * verb_count / total_words, 2) as verb_percentage
FROM read_csv_auto([
    'macula-hebrew/tsv/Genesis.tsv',
    'macula-hebrew/tsv/Exodus.tsv',
    'macula-hebrew/tsv/Leviticus.tsv',
    'macula-hebrew/tsv/Numbers.tsv',
    'macula-hebrew/tsv/Deuteronomy.tsv'
], filename=true)
GROUP BY filename
ORDER BY filename
```

### Example 3: Window Function (Running Total)
```sql
-- Cumulative vocabulary growth
WITH unique_lemmas AS (
    SELECT DISTINCT
        verse_id,
        lemma
    FROM macula_hebrew
    ORDER BY verse_id
)
SELECT
    verse_id,
    lemma,
    ROW_NUMBER() OVER (ORDER BY verse_id) as cumulative_words,
    COUNT(DISTINCT lemma) OVER (ORDER BY verse_id) as unique_vocabulary
FROM unique_lemmas
```

---

## DuckDB Step Type for LLMFlow Pipelines

### Overview

Add a new `duckdb` step type to LLMFlow that executes SQL queries stored in `.sql` files with variable substitution, similar to how `llm` steps use `.gpt` prompt files. This enables analytical data processing as a first-class pipeline step alongside LLM calls and function invocations.

### Step Configuration

```yaml
steps:
  - name: analyze_verb_frequency
    type: duckdb
    query_file: queries/verb_frequency.sql
    inputs:
      book: "${book}"
      genre: "narrative"
      macula_path: "/Users/jonathan/github/Clear/macula-hebrew/tsv/"
      min_frequency: 5
    output: verb_stats
    format: records  # Optional: records (default), dataframe, json
```

### Query File Format

Query files (`.sql`) support variable substitution using `${variable}` syntax:

**File:** `queries/verb_frequency.sql`
```sql
-- Parameterized DuckDB query
-- Description: Extract verb frequency statistics for a book
-- Inputs: book, macula_path, min_frequency

SELECT
    lemma,
    gloss,
    COUNT(*) as frequency,
    COUNT(DISTINCT verse_id) as verse_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*) OVER ()), 2) as pct_of_total
FROM read_csv_auto('${macula_path}/*.tsv')
WHERE pos = 'verb'
  AND book = '${book}'
GROUP BY lemma, gloss
HAVING frequency >= ${min_frequency}
ORDER BY frequency DESC
LIMIT 100
```

### Output Formats

- **`records`** (default): List of dictionaries `[{col1: val1, col2: val2}, ...]`
- **`dataframe`**: Returns pandas DataFrame object
- **`json`**: JSON string representation
- **`dict`**: Dictionary with columns as keys `{col1: [vals], col2: [vals]}`

### Integration with LLM Steps

DuckDB query results flow naturally into LLM prompts:

```yaml
steps:
  # 1. Query morphological data
  - name: extract_verbs
    type: duckdb
    query_file: queries/verb_frequency.sql
    inputs:
      book: "${book}"
      macula_path: "/data/macula-hebrew/tsv/"
    output: verb_data

  # 2. Generate pedagogical descriptions
  - name: explain_verbs
    type: llm
    prompt:
      file: prompts/explain_verbs.gpt
      inputs:
        verbs: "${verb_data}"
        level: "intermediate"
    output: vocab_list
```

**Prompt file** (`prompts/explain_verbs.gpt`):
```
You are a Hebrew language instructor creating vocabulary materials.

Given this verb frequency data:
{{verbs}}

Create pedagogical descriptions for intermediate students, focusing on:
- Most frequent verbs (prioritize these)
- Common usage patterns
- Memorable examples from scripture
```

### Implementation Details

**Function signature:**
```python
def run_duckdb_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None
) -> Any:
    """Execute a DuckDB query step and return results"""
```

**Behavior:**
1. Read query file from `query_file` path (relative to `queries/` directory)
2. Resolve all `${variable}` references using step `inputs` and pipeline context
3. Execute query using DuckDB in-memory connection
4. Format results according to `format` parameter
5. Store result in context using `outputs` key
6. Log query execution time for telemetry

**Error Handling:**
- Missing query file → `FileNotFoundError` with helpful message
- SQL syntax error → `DuckDBError` with query context
- Missing variable → `VariableResolutionError` with variable name
- Empty results → Return empty list/DataFrame based on format

**Telemetry:**
- Track query execution time
- Record number of rows returned
- Log query file path and resolved variables

### Example: Full End-to-End Pipeline

```yaml
name: verb-vocabulary-generator
description: Generate ranked vocabulary lists with pedagogical context

variables:
  book: "${book}"
  level: "intermediate"
  macula_path: "/Users/jonathan/github/Clear/macula-hebrew/tsv/"

steps:
  # 1. Extract verb frequencies
  - name: extract_verbs
    type: duckdb
    query_file: queries/verb_frequency.sql
    inputs:
      book: "${book}"
      macula_path: "${macula_path}"
      min_frequency: 5
    output: verb_data

  # 2. Find common collocations for top verbs
  - name: find_collocations
    type: duckdb
    query_file: queries/verb_collocations.sql
    inputs:
      book: "${book}"
      macula_path: "${macula_path}"
      top_n_verbs: 20
    output: collocation_data

  # 3. Generate pedagogical descriptions
  - name: explain_verbs
    type: llm
    prompt:
      file: prompts/explain_verbs.gpt
      inputs:
        verbs: "${verb_data}"
        collocations: "${collocation_data}"
        level: "${level}"
    output: vocab_list

  # 4. Save to markdown
  - name: save_output
    type: save
    content: "${vocab_list}"
    path: "outputs/${book}_vocab_${level}.md"
```

### Benefits

1. **Declarative Data Processing:** SQL queries as pipeline steps, versioned alongside prompts
2. **No Code Required:** Analysts write SQL, not Python
3. **Performance:** DuckDB's columnar engine 10-100x faster than pandas for these queries
4. **Composability:** Chain DuckDB queries with LLM steps naturally
5. **Reproducibility:** Query files and variable values logged for every run
6. **Reusability:** Share query files across pipelines
7. **Type Safety:** DuckDB validates SQL at execution time

### Migration Path

**Before** (Python function step):
```yaml
- name: analyze_data
  type: function
  function: my_module.analyze_with_pandas
  inputs:
    book: "${book}"
```

**After** (DuckDB step):
```yaml
- name: analyze_data
  type: duckdb
  query_file: queries/analyze.sql
  inputs:
    book: "${book}"
```

Existing Python functions can be migrated to SQL queries where appropriate, with significant performance gains.

---

## Integration Points

### 1. LLMFlow Pipelines
**File:** `llmflow/utils/bible_data.py`

**Add new functions:**
```python
def analyze_vocabulary_difficulty(book: str) -> Dict:
    """Return difficulty metrics for a book."""

def find_discourse_boundaries(book: str, chapter: int) -> List[Dict]:
    """Detect participant switches, theme changes."""

def generate_frequency_list(books: List[str], pos: str = 'all') -> pd.DataFrame:
    """Create frequency-ranked word list."""
```

### 2. Discourse-Flow Pipeline
**Enhancement:** Add pre-processing step using DuckDB

```yaml
# In discourse-flow.yaml
- name: analyze_passage_difficulty
  type: function
  function: llmflow.utils.bible_data.analyze_difficulty
  inputs:
    passage: "${passage}"
  output: difficulty_metrics

- name: identify_discourse_signals
  type: function
  function: llmflow.utils.bible_data.find_discourse_boundaries
  inputs:
    passage_info: "${passage_info}"
  output: discourse_signals
```

### 3. Paratext Pipelines
**New capability:** Translation difficulty pre-check

```python
# Before translation review
difficulty_scores = bible_data.analyze_verse_difficulty(book="Ruth")
high_priority = difficulty_scores[difficulty_scores['percentile'] < 0.2]
```

### 4. Interactive Query Tool
**New tool:** `biblical-analytics` CLI

```bash
# Command-line tool
biblical-analytics query "
  SELECT lemma, COUNT(*) as freq
  FROM macula_hebrew
  WHERE book = 'Ruth' AND pos = 'verb'
  GROUP BY lemma ORDER BY freq DESC
"

# Export results
biblical-analytics frequency-list --book Ruth --format json > ruth_vocab.json
```

---

## Performance Considerations

### Benchmarks (Estimated)

| Operation | SQLite (with import) | pandas | DuckDB |
|-----------|---------------------|--------|--------|
| Load Genesis TSV | 2.5s | 1.8s | 0.15s |
| Count verbs | 0.8s | 2.1s | 0.05s |
| Complex aggregation | 12s | 15s | 0.6s |
| Pentateuch frequency list | 45s | 60s | 2.1s |
| Window function (participant tracking) | N/A* | 30s | 1.2s |

*SQLite doesn't support window functions without extension

### Optimization Strategies

1. **Query Planning:** Push filters down to file scan
2. **Columnar Reads:** Only read needed columns
3. **Parallel Execution:** Multi-threaded query execution
4. **Result Caching:** Cache common queries in session
5. **Partition Awareness:** Query only needed files

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [x] Add DuckDB support to `bible_data.py`
- [x] Create basic query functions
- [ ] Write test suite for DuckDB functionality
- [ ] Document SQL patterns in examples

### Phase 2: Core Analytics (Week 3-4)
- [ ] Implement frequency analysis functions
- [ ] Add participant tracking queries
- [ ] Create collocation discovery functions
- [ ] Build difficulty scoring system

### Phase 3: Integration (Week 5-6)
- [ ] Integrate with discourse-flow pipeline
- [ ] Add analytics step to paratext-pipelines
- [ ] Create Jupyter notebook examples
- [ ] Performance testing and optimization

### Phase 4: Advanced Features (Week 7-8)
- [ ] Character network analysis
- [ ] Thematic density mapping
- [ ] Cross-testament translation patterns
- [ ] Semantic field generation

### Phase 5: Tooling (Week 9-10)
- [ ] Build CLI tool (`biblical-analytics`)
- [ ] Create web dashboard (optional)
- [ ] Generate documentation site
- [ ] User training materials

---

## Success Metrics

1. **Performance:** 10x faster than current pandas-based analysis
2. **Adoption:** 50% of pipeline runs use DuckDB analytics
3. **New Capabilities:** 5+ features impossible with previous tools
4. **User Satisfaction:** Positive feedback from researchers
5. **Code Reuse:** DuckDB queries shared across 3+ projects

---

## Future Enhancements

### Machine Learning Integration
- Export feature vectors for word embeddings
- Generate training data for NLP models
- Similarity scoring for semantic analysis

### Real-Time Analysis
- Web API serving DuckDB queries
- Interactive dashboards (Streamlit/Gradio)
- Collaborative analysis platform

### Extended Data Sources
- Add NT syntax treebanks
- Integrate Dead Sea Scrolls data
- Include Septuagint morphology

---

## Appendix A: DuckDB vs Alternatives

| Feature | DuckDB | SQLite | pandas | Polars |
|---------|--------|--------|--------|--------|
| Direct CSV/TSV read | ✅ | ❌ | ✅ | ✅ |
| Window functions | ✅ | Limited | ✅ | ✅ |
| ICU collation | ✅ | Extension | ❌ | ❌ |
| Array operations | ✅ | JSON ext | ✅ | ✅ |
| Performance | Excellent | Good | Fair | Excellent |
| SQL standard | SQL:2016 | SQL-92 | N/A | Limited |
| Setup complexity | Low | None | None | Low |

**Verdict:** DuckDB best for analytical queries on file-based data with complex SQL needs.

---

## Appendix B: Sample Queries Library

See [`examples/duckdb_queries.sql`](examples/duckdb_queries.sql) for:
- 50+ pre-written analytical queries
- Commented explanations
- Performance tips
- Common patterns

---

## References

1. [DuckDB Documentation](https://duckdb.org/docs/)
2. [Macula Hebrew Schema](https://github.com/Clear-Bible/macula-hebrew)
3. [ACAI Format Specification](https://github.com/BibleAquifer/ACAI)
4. [awesome-biblical-data Registry](https://github.com/nida-institute/awesome-biblical-data)

---

**Contributors:** Jonathan
**Reviewers:** [Add reviewers]
**Status:** Draft for Review
