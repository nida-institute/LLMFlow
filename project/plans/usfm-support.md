# USFM/USX/USJ Support Design

**Status:** Implemented in part — historical record. USFM/USJ handling exists in `utils/data.py`,
`utils/file_io.py` and the loader steps (`tests/test_usfm_loaders.py`). Not everything sketched here
was built; check the code before relying on any specific capability.

Contains `output_dir`, a retired spelling — the declarations are now
`intermediate_file_directory` / `output_file_directory`, and the directory is plural `outputs/`.

_Status: Draft — under discussion_
_Created: 2026-03-24_

---

## Goal

Give Scripture Pipelines pipelines first-class access to USFM/USX/USJ Scripture data — specifically Paratext-sourced projects — at any granularity: whole project, single book, or passage (chapter initially, verse range later).

A common use case is **multi-project comparison**: set `base_dir` once as a pipeline global variable, then load the same passage from several translation projects for comparison (e.g. a 3-way semantic comparison among translations).

```yaml
variables:
  paratext_dir: "${PARATEXT_DIR}"   # set once
  book: "LUK"
  chapter: "1"

steps:
  - name: load_proj_a
    type: function
    function: load_usfm_passage
    inputs:
      base_dir: "${paratext_dir}"
      project_name: "ProjectA"
      passage: "${book} ${chapter}"
    outputs:
      - text_a

  - name: load_proj_b
    type: function
    function: load_usfm_passage
    inputs:
      base_dir: "${paratext_dir}"
      project_name: "ProjectB"
      passage: "${book} ${chapter}"
    outputs:
      - text_b

  - name: load_proj_c
    type: function
    function: load_usfm_passage
    inputs:
      base_dir: "${paratext_dir}"
      project_name: "ProjectC"
      passage: "${book} ${chapter}"
    outputs:
      - text_c

  - name: compare
    type: llm
    prompt: prompts/semantic-compare.gpt
    inputs:
      text_a: "${text_a}"
      text_b: "${text_b}"
      text_c: "${text_c}"
```

This pattern also supports iterating a list of project names driven by a variable, once Scripture Pipelines loop support is available.

---

## Constraints

- **Version:** US? 3.1 only. We do not support earlier formats.
- **Library:** `usfmtc` (Martin Hosken / SIL), `>=0.4.5`. Already installed in hatch env.
  - `usfmtc.readFile(path)` → `USX` object; auto-detects format from extension (`.sfm`, `.usfm`, `.usx`, `.usj`)
  - `USX.outUsj()` → `dict` (USJ 3.1 structure)
  - `USX.outUsx()` / `USX.saveAs(path, outputformat=...)` → round-trip to USX, USJ, or USFM
  - `USX.book` → book code string (e.g. `"LUK"`)
- **Do not use `usfm-grammar`** (already installed but inferior; will be removed from dependencies)
- **Paratext project layout:** `<base_dir>/<project_name>/*.sfm` or `*.usfm`

---

## Return format contract

Two formats are supported, selected by `format=` parameter:

| `format=` | Returns | Use case |
|---|---|---|
| `"usx"` | `lxml.etree._Element` | XPath, BaseX, `type: basex` pipeline steps |
| `"usj"` | `dict` | JSON-serializable, best for LLM prompt injection |

**The pipeline must specify `format:` explicitly.** There is no magic default that varies by function — the pipeline author decides what they need. If `format` is omitted, a fallback default of `"usx"` is used, but pipelines should always state it clearly.

**Reading:** `usfmtc` handles older USFM/USX versions gracefully — encountering them in real Paratext projects is common and expected. No version validation on input.

**Writing:** Scripture Pipelines always outputs USX/USJ **3.1**. Older versions are never written.

---

## Proposed functions (in `src/llmflow/utils/data.py`)

### `list_usfm_books(base_dir, project_name) → list[str]`

Returns book codes found in `<base_dir>/<project_name>/`, sorted in **canonical USFM order** (Genesis → Revelation, deuterocanonicals after Malachi, unknown codes at the end).

Scans for `*.sfm` / `*.usfm`. Fast — reads only enough of each file to extract the book code.

**Sort key:** a hardcoded lookup table keyed on the 3-letter USFM book code (e.g. `GEN=1, EXO=2, ... MAL=39, TOB=40 ... MAT=61...`). The project's own numeric book numbers are preserved in filenames (see below), but they are **not used for sorting** — the canonical code-based order is stable across all projects regardless of how their numbers are assigned.

**Resolved design decisions:**

1. **Preserve project book numbers in output filenames.** When writing processed results (e.g. `export_usx`), the output filename keeps the same numeric prefix the project uses (e.g. `41LUKPRJ.usx` not `LUK.usx`). This ensures round-trip compatibility and avoids breaking Paratext's own tooling.

2. **Always use 3-letter book codes to identify books in Scripture Pipelines.** All function parameters, pipeline YAML, and API surfaces use codes (`"LUK"`, `"GEN"`) not numbers. Numbers are treated as opaque file-naming artifacts belonging to the source project.

```yaml
- name: books
  type: function
  function: list_usfm_books
  inputs:
    base_dir: "${PARATEXT_DIR}"
    project_name: "MyProject"
  outputs:
    - book_list   # e.g. ["GEN", "LUK", "MAT", "ACT"]  (canonical order)
```

---

### `load_usfm_book(base_dir, project_name, book, format) → _Element | dict`

Loads a single book. Scans project dir, finds the file whose book code matches `book`, parses with `usfmtc`, returns in requested format.

Raises `ValueError` if book not found. Raises `FileNotFoundError` if project dir missing.

```yaml
- name: load_luke
  type: function
  function: load_usfm_book
  inputs:
    base_dir: "${PARATEXT_DIR}"
    project_name: "MyProject"
    book: "LUK"
    format: "usj"      # or "usx" for XPath/BaseX use
  outputs:
    - scripture
```

---

### `load_usfm_passage(base_dir, project_name, passage, format) → dict | _Element`

Loads a passage by reference string. Phase 1: whole book or whole chapter. Phase 2: verse range.

Passage string formats:
- `"LUK"` — whole book
- `"LUK 1"` — chapter 1
- `"LUK 1:1-10"` — verse range _(Phase 2 only)_

Returns only the relevant content: for chapter, a USJ/USX subtree containing paragraphs from that chapter.

```yaml
- name: load_passage
  type: function
  function: load_usfm_passage
  inputs:
    base_dir: "${PARATEXT_DIR}"
    project_name: "MyProject"
    passage: "LUK 1"
    format: "usj"
  outputs:
    - passage_content
```

---

### `export_usx(base_dir, project_name, output_dir) → str`

Converts all books in the project to USX 3.1 and writes them as `<BOOK>.usx` into `output_dir`. Returns `output_dir` as a string so it can be piped into a `type: basex` step or `sp load-db basex`.

```yaml
- name: export
  type: function
  function: export_usx
  inputs:
    base_dir: "${PARATEXT_DIR}"
    project_name: "MyProject"
    output_dir: "/tmp/myproject-usx"
  outputs:
    - usx_dir

- name: query
  type: basex
  db: "myproject"
  # user first ran: sp load-db basex MyProject --source /tmp/myproject-usx
```

---

## Format conversion helpers (stretch — maybe not needed as pipeline functions)

These are thin wrappers that could be useful as standalone utilities or in tests:

```python
usfm_to_usj(usfm_text: str) -> dict
usfm_to_usx_element(usfm_text: str) -> lxml.etree._Element
usj_to_usx_element(usj: dict) -> lxml.etree._Element
usx_element_to_usj(element: lxml.etree._Element) -> dict
```

`usfmtc` already handles all of these round-trips. Worth exposing in `data.py` for pipeline authors? Or keep internal?

---

## BaseX integration path

Existing `sp load-db basex` accepts a source directory of XML files. The simplest path:

```
Paratext project dir (*.sfm)
    → export_usx() → /tmp/myproject-usx/*.usx
        → sp load-db basex MyProject --source /tmp/myproject-usx
            → BaseX DB "MyProject"
```

Alternatively, add a `usfm` driver to `load_db.py`:

```
sp load-db usfm MyProject --source <base_dir>/<project_name>
```

...which internally calls `export_usx()` to a temp dir, then runs the BaseX `CREATE DB` command. Fewer steps for the user. But it couples `load_db.py` to `usfmtc`.

---

## `pyproject.toml` changes

- Add: `usfmtc>=0.4.5`
- Remove (or keep but mark optional): `usfm-grammar`

---

## Test fixtures

- Minimal synthetic USFM written inline in test (no file dependency)
- Or copy one chapter of the Patani Malay LUK USFM fixture already available at `local/patanimalay/LUK_2025-07-10T19-25-53-965Z.usfm` (in the backtranslation repo — we'd need to copy or recreate a minimal version)
- Fixture file lives at `tests/fixtures/usfm/TestProject/LUK.sfm`

---

## Deuterocanonical book identity: a known ambiguity

Some deuterocanonical texts appear as **separate books** in some traditions/projects and as **chapters within a canonical book** in others:

- Bel and the Dragon → separate book (`BEL`) in some projects; Daniel 14 in others
- Susanna → separate book (`SUS`) in some projects; Daniel 13 in others
- 1 Esdras, Prayer of Manasseh, etc. similarly vary

This means the same underlying text can live in more than one USFM book code depending on the project's tradition. **AI pipelines that search for a passage should be reminded to check multiple locations** (e.g. look in `DAN` _and_ `BEL` / `SUS` if you need the full Theodotion Daniel).

This is worth surfacing in the AI context docs so LLMs are not misled into assuming a unique one-to-one mapping between text and book code.

---

## Passage extraction: honest scope

Verse-level slicing from USX/USJ is non-trivial. In USFM, `\v 1` is a milestone, not a container — verse text runs as paragraph content until the next milestone. This means:

- **Chapter boundary** is clean (paragraphs inside `<chapter>` in USX, or `marker: "c"` in USJ)
- **Verse boundary** requires walking content nodes and splitting mid-paragraph

Phase 1 scope: support `"BOOK"` and `"BOOK C"` only.
Phase 2: verse ranges — requires a dedicated passage extractor.

---

## Paratext Project Metadata Access

### Problem Statement

When working with multiple Paratext projects in a pipeline (e.g., 3-way comparison), users need access to project-level metadata and resources beyond just the Scripture text:

- **Settings.xml** — language name, ISO code, versification, copyright, encoding
- **Biblical Terms lists** — BiblicalTerms.xml (project-specific renderings)
- **Notes** — checking notes, consultant notes
- **Back references** — cross-references, parallel passages
- **Project structure** — book presence, completion status

**Use case:** Back-translation pipeline needs to know the source language name and ISO code to generate context-aware prompts.

**Challenge:** If a pipeline loads 3 projects (`ProjectA`, `ProjectB`, `ProjectC`), how do I access each project's metadata distinctly? Do I need 3 separate function calls? Or does metadata get bundled with the Scripture data?

### Paratext Project File Inventory

A typical Paratext project directory contains:

**XML metadata files (Paratext 8/9):**
- `Settings.xml` — language, ISO code, versification, copyright, encoding, project type
- `BiblicalTerms.xml` — project-specific renderings of key biblical terms
- `CommentTags.xml` — tags for categorizing consultant/translator notes
- `BookNames.xml` — localized book names in the target language
- `ProjectProgress.xml` — completion status by book and stage

**JSON metadata files (Scripture Burrito):**
- `metadata.json` — Scripture Burrito manifest with comprehensive project metadata
  - System/identification (project name, ID, revision)
  - Type/format (translation, audio, video, etc.)
  - Languages (ISO codes, scripts, writing systems)
  - Agencies (copyright, contributors, publishers)
  - Ingredients (list of books/resources with their locations)
  - More structured and extensible than Settings.xml

**Other files:**
- `*.sfm` / `*.usfm` — Scripture text files (one per book)
- `*.ldml` — LDML language/writing system definitions
- `Notes/*.xml` — checking notes, consultant notes (separate files per note type/book)
- `*.license` — Paratext license/registration info

For Scripture Pipelines, the most useful are:
1. **Settings.xml / metadata.json** (language info, versification)
2. **BiblicalTerms.xml** (key term renderings)
3. **Scripture files** (already handled by `load_usfm_*` functions)

Notes and progress files are less commonly needed in automated workflows.

**Format strategy:** Projects may have **both** Scripture Burrito (`metadata.json`) and Paratext XML (`Settings.xml`). They are **complementary**, not alternatives:
- **Scripture Burrito** provides structured, standardized metadata (languages, agencies, ingredients)
- **Paratext XML** provides implementation-specific settings (encoding, custom fields, project-internal state)
- Some metadata appears in both but with different structures
- **Load both when available** — let pipeline decide which to use for each field

### Design Alternatives

#### Option 1: Explicit metadata function (current implementation)

```yaml
- name: load_metadata_a
  type: function
  function: get_paratext_metadata
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "ProjectA"
  outputs:
    - metadata_a

- name: load_text_a
  type: function
  function: load_usfm_book
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "ProjectA"
    book: "LUK"
    format: "usj"
  outputs:
    - text_a
```

**Pros:**
- Explicit — user controls when metadata is loaded
- Lazy — metadata only loaded if needed
- Compositional — metadata step independent of text loading

**Cons:**
- Verbose — need separate step for each project's metadata
- Variable naming burden — `metadata_a`, `metadata_b`, `metadata_c`
- Metadata and text are separate — no automatic association

#### Option 2: Settings.xml returned as XML element (XPath access)

```yaml
- name: load_settings_a
  type: function
  function: load_paratext_settings
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "ProjectA"
  outputs:
    - settings_xml_a  # lxml _Element

- name: extract_language
  type: xpath
  xml: "${settings_xml_a}"
  query: "/ScriptureText/LanguageName/text()"
  outputs:
    - language_a
```

**Pros:**
- Full XPath power — query anything in Settings.xml
- Flexible — user chooses what to extract
- Format consistency with USX (also XML)

**Cons:**
- More steps required for simple field access
- Requires XPath knowledge
- Verbose for common fields (language, ISO code)

#### Option 3: Metadata as dict with explicit field extraction in template

```yaml
- name: load_metadata_a
  type: function
  function: get_paratext_metadata
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "ProjectA"
  outputs:
    - metadata_a  # dict with keys: language_name, language_iso, full_name, etc.

- name: llm_step
  type: llm
  prompt: prompts/backtranslation.gpt
  inputs:
    source_language: "${metadata_a.language_name}"  # dot notation
    language_iso: "${metadata_a.language_iso}"
```

**Pros:**
- Clean template syntax with dot notation
- Common fields pre-extracted
- JSON-serializable (works with LLM context injection)

**Cons:**
- Limited to pre-extracted fields
- Cannot query arbitrary Settings.xml content
- Dict vs XML choice must be made upfront

#### Option 4: Dual-format metadata function

```yaml
- name: load_metadata
  type: function
  function: get_paratext_metadata
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "ProjectA"
    format: "dict"  # or "xml"
  outputs:
    - metadata_a
```

**Pros:**
- User chooses format based on need
- `dict` for simple field access, `xml` for XPath queries
- Consistent with `load_usfm_book(format=...)` pattern

**Cons:**
- Two code paths to maintain
- Format choice may not be obvious to pipeline authors

#### Option 5: Bundled metadata with Scripture load

```yaml
- name: load_text_a
  type: function
  function: load_usfm_book
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "ProjectA"
    book: "LUK"
    format: "usj"
    include_metadata: true
  outputs:
    - text_a  # USJ dict
    - metadata_a  # auto-generated: metadata dict
```

**Pros:**
- One function call gets both text + metadata
- Metadata automatically associated with its project
- No separate metadata step needed

**Cons:**
- Overhead if metadata not needed
- Multiple outputs from single step (uncommon in Scripture Pipelines)
- Unclear what `include_metadata` scope is (Settings.xml only? or also Biblical Terms?)

### Open Design Questions

1. **What metadata scope?** Settings.xml only? Or also Biblical Terms, notes, back references? (Suggest: Settings.xml only for Phase 1)

2. **Return format?** Dict (JSON-serializable) vs XML element (XPath-queryable)? Or both with `format=` param?

3. **When to load?** Explicit function call (current) vs bundled with text load vs automatic on first project access?

4. **Caching?** If a pipeline loads multiple books from the same project, should metadata be cached? (Scripture Pipelines runner doesn't currently cache function results across steps)

5. **Biblical Terms access pattern?** Separate function `load_biblical_terms(base_dir, project_name, format=...)` returning XML or parsed dict?

6. **Multi-project pattern?** Is there a cleaner way to handle "load metadata + text from 3 projects" without 6 separate steps?

#### Option 6: Load XML files directly as lxml Elements (RECOMMENDED)

```yaml
- name: load_settings_a
  type: function
  function: load_paratext_file
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "ProjectA"
    file: "Settings.xml"
  outputs:
    - settings_a  # lxml _Element

- name: load_biblical_terms_a
  type: function
  function: load_paratext_file
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "ProjectA"
    file: "BiblicalTerms.xml"
  outputs:
    - terms_a  # lxml _Element
```

Then access via XPath or convert to dict:

```yaml
- name: extract_language
  type: xpath
  xml: "${settings_a}"
  query: "/ScriptureText/LanguageName/text()"
  outputs:
    - language_a

# Or in template using xpath_query helper or dict conversion
```

**Pros:**
- **Complete access** — all fields available, nothing pre-filtered
- **Future-proof** — any new Paratext fields automatically accessible
- **Consistent** — same pattern as USX/USX (XML elements)
- **Less code** — no field mapping, just load XML
- **Flexible** — user chooses what to extract
- **Extensible** — works for Settings.xml, BiblicalTerms.xml, CommentTags.xml, etc.

**Cons:**
- Requires XPath knowledge (but so does BaseX/USX querying)
- Slightly more verbose for simple field access

### Recommended Approach

**Phase 1: Generic project file loader**

- `load_project_file(base_dir, project_name, file) → dict | lxml.etree._Element`
- Loads any metadata file from the project directory
- **Auto-detects format by extension:**
  - `.json` → returns `dict` (parsed JSON)
  - `.xml` → returns `lxml.etree._Element` (parsed XML)
- Files supported:
  - `metadata.json` (Scripture Burrito manifest)
  - `Settings.xml` (Paratext settings)
  - `BiblicalTerms.xml` (key term renderings)
  - `CommentTags.xml`, `BookNames.xml`, etc.

**Access patterns:**
- **JSON files**: Native dict access with dot notation: `${metadata.languages[0].iso}`
- **XML files**: Must extract values in pipeline steps, then use simple variables in templates
  - **Python (in pipeline code)**: `element.find('.//LanguageName').text` — `.text` is an attribute
  - **XPath**: `element.xpath('.//LanguageName/text()')[0]` — `text()` is XPath function
  - **Scripture Pipelines templates**: Cannot call methods — extract in pipeline, pass simple vars
  - **Passing to LLM**: lxml Elements must be serialized first (e.g., `lxml.etree.tostring(element)` or convert to dict)

**Phase 2: Helper for XML→dict conversion (optional)**

For XML files where dict access is preferred:

```yaml
- name: settings_to_dict
  type: function
  function: xml_to_dict
  inputs:
    xml: "${settings_xml}"
  outputs:
    - settings_dict  # can now use ${settings_dict.LanguageName}
```

**Not recommended:** Pre-parsing specific fields — loses flexibility and requires maintenance as formats evolve.

### Usage Examples

**Important:** Scripture Pipelines uses custom template substitution (not Jinja2). Templates support simple variable access but **cannot call methods**. When working with XML:
- **lxml Elements cannot be passed to LLM directly** — they must be serialized or values extracted first
- Extract values in pipeline steps (using XPath or Python helpers)
- Pass simple string/dict variables to templates
- In Python: `element.find('.//Tag').text` (`.text` is attribute; correct)
- In XPath: `element.xpath('.//Tag/text()')[0]` (`text()` is XPath function)
- To serialize: `lxml.etree.tostring(element, encoding='unicode')` or convert to dict

---

#### Scripture Burrito metadata.json structure (for reference)

```json
{
  "meta": {
    "version": "0.3.0",
    "category": "source",
    "generator": {...}
  },
  "identification": {
    "name": {"en": "Cebuano New Testament"},
    "abbreviation": {"en": "cebAPD"}
  },
  "languages": [
    {
      "tag": "ceb",
      "name": {"en": "Cebuano"},
      "scriptDirection": "ltr"
    }
  ],
  "type": {
    "flavorType": {
      "name": "scripture",
      "flavor": {
        "name": "textTranslation",
        "currentScope": {...}
      }
    }
  },
  "agencies": [{...}],
  "ingredients": {...}
}
```

Common access paths:
- Language name: `metadata["languages"][0]["name"]["en"]`
- ISO code: `metadata["languages"][0]["tag"]`
- Project name: `metadata["identification"]["name"]["en"]`
- Abbreviation: `metadata["identification"]["abbreviation"]["en"]`

#### Settings.xml structure (for reference)

```xml
<ScriptureText>
  <LanguageName>Cebuano</LanguageName>
  <LanguageIsoCode>ceb</LanguageIsoCode>
  <FullName>Cebuano Ang Bag-ong Dipta</FullName>
  <Abbreviation>cebAPD</Abbreviation>
  <Versification>4</Versification>
  <Copyright>...</Copyright>
  <Encoding>65001</Encoding>
  <!-- many other fields... -->
</ScriptureText>
```

Common XPath queries:
- Language name: `/ScriptureText/LanguageName/text()`
- ISO code: `/ScriptureText/LanguageIsoCode/text()`
- Full project name: `/ScriptureText/FullName/text()`
- Abbreviation: `/ScriptureText/Abbreviation/text()`
- Versification: `/ScriptureText/Versification/text()`

#### Loading project metadata (recommended pattern):

**Best practice:** Extract values in pipeline steps, pass simple variables to templates.

See Example 1 below for the recommended pattern.

#### Loading both Scripture Burrito and Paratext metadata:

If project has both formats (common for modern projects), load both:

```yaml
- name: load_burrito
  type: function
  function: load_project_file
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "cebAPDv4"
    file: "metadata.json"
  outputs:
    - burrito  # dict - structured metadata

- name: load_settings
  type: function
  function: load_project_file
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "cebAPDv4"
    file: "Settings.xml"
  outputs:
    - settings  # lxml Element - Paratext-specific settings

- name: extract_settings_fields
  type: function
  function: xpath_multiple  # Extract multiple fields at once
  inputs:
    xml: "${settings}"
    paths:
      versification: ".//Versification"
      encoding: ".//Encoding"
  outputs:
    - settings_fields  # Dict with extracted values

- name: process
  type: llm
  prompt: prompts/process.gpt
  inputs:
    # Use Burrito for standardized fields (better structure)
    language: "${burrito.languages[0].name.en}"
    iso: "${burrito.languages[0].tag}"
    # Use extracted Settings fields
    versification: "${settings_fields.versification}"
    encoding: "${settings_fields.encoding}"
```

**When to use which:**
- **Scripture Burrito** (`metadata.json`): Language info, project identification, agencies, structured ingredients list
- **Paratext Settings** (`Settings.xml`): Versification scheme, encoding, Paratext-specific project state, legacy fields

#### Example 1: Extracting language from Paratext Settings.xml

```yaml
steps:
  - name: load_settings
    type: function
    function: load_project_file
    inputs:
      base_dir: "${PARATEXT_DIR}"
      project_name: "cebAPDv4"
      file: "Settings.xml"
    outputs:
      - settings  # Returns: lxml.etree._Element

  # Extract language info in pipeline, then pass to template
  - name: extract_language
    type: function
    function: xpath_text  # Helper that extracts text from XPath result
    inputs:
      xml: "${settings}"
      path: ".//LanguageName/text()"  # /text() extracts the text value
    outputs:
      - language_name

  - name: extract_iso
    type: function
    function: xpath_text
    inputs:
      xml: "${settings}"
      path: ".//LanguageIsoCode/text()"  # /text() extracts the text value
    outputs:
      - language_iso

  - name: backtranslate
    type: llm
    model: gpt-4o
    prompt: prompts/backtranslation.gpt
    inputs:
      language: "${language_name}"  # Simple string variable
      iso: "${language_iso}"
      source_text: "${scripture}"
```

In the template file (`backtranslation.gpt`):
```
Source Language: {{language}}
ISO Code: {{iso}}

Please back-translate the following {{language}} text...
```

**Note:** Scripture Pipelines templates use custom substitution, not full Python. Extract values in pipeline steps first, then pass simple variables to templates.

```yaml
  - name: extract_language_python
    type: function
    function: python_eval  # if Scripture Pipelines supports inline Python
    code: "settings.find('.//LanguageName').text"
    inputs:
      settings: "${settings}"
    outputs:
      - language_name
```

**In Python code:** The syntax `element.find('.//LanguageName').text` is correct. The `.text` attribute gets the text content (not XPath `text()`). For XPath queries, use: `element.xpath('.//LanguageName/text()')[0]`.

#### Example 2: Extracting language from Scripture Burrito metadata.json

```yaml
steps:
  - name: load_burrito
    type: function
    function: load_project_file
    inputs:
      base_dir: "${PARATEXT_DIR}"
      project_name: "cebAPDv4"
      file: "metadata.json"
    outputs:
      - burrito  # Returns: dict (parsed JSON)

  - name: backtranslate
    type: llm
    model: gpt-4o
    prompt: prompts/backtranslation.gpt
    inputs:
      # Direct dict access - cleaner than XML
      language: "${burrito.languages[0].name.en}"
      iso: "${burrito.languages[0].tag}"
      project_name: "${burrito.identification.name.en}"
      abbreviation: "${burrito.identification.abbreviation.en}"
      source_text: "${scripture}"
```

In the template file (`backtranslation.gpt`):
```
Source Language: {{language}}
ISO Code: {{iso}}
Project: {{project_name}} ({{abbreviation}})
```

**Why Burrito is simpler for language info:**
- No XPath needed — just dict access
- Multi-language support built-in: `burrito.languages[0]`, `burrito.languages[1]`, etc.
- Standardized structure across all projects

#### Example 3: Fallback pattern (check Burrito first, fall back to Paratext)

For maximum compatibility with both old and new projects:

```yaml
steps:
  # Try to load Scripture Burrito first
  - name: try_load_burrito
    type: function
    function: load_project_file
    inputs:
      base_dir: "${PARATEXT_DIR}"
      project_name: "${project_name}"
      file: "metadata.json"
    outputs:
      - burrito
    # Note: This will raise FileNotFoundError if metadata.json doesn't exist
    # In practice, you'd need error handling here (future enhancement)

  - name: load_settings
    type: function
    function: load_project_file
    inputs:
      base_dir: "${PARATEXT_DIR}"
      project_name: "${project_name}"
      file: "Settings.xml"
    outputs:
      - settings

  # Extract language - try Burrito first (dict access works), fall back to Settings
  - name: extract_language
    type: function
    function: get_language  # Helper that tries burrito.languages[0].name.en, falls back to Settings XPath
    inputs:
      burrito: "${burrito}"
      settings: "${settings}"
    outputs:
      - source_language
      - language_iso

  - name: process
    type: llm
    prompt: prompts/process.gpt
    inputs:
      language: "${source_language}"  # Already extracted as string
      iso: "${language_iso}"
```

**Note:** Since Scripture Pipelines uses custom template resolution (not Jinja2), prefer **extracting values in pipeline steps** rather than calling methods or using conditionals in templates. Templates should receive simple string/dict variables.

#### Example 4: Multi-project comparison with language metadata

```yaml
variables:
  paratext_dir: "${PARATEXT_DIR}"
  book: "LUK"

steps:
  # Load metadata for all three projects
  - name: load_burrito_a
    function: load_project_file
    inputs: {base_dir: "${paratext_dir}", project_name: "ProjectA", file: "metadata.json"}
    outputs: [burrito_a]

  - name: load_burrito_b
    function: load_project_file
    inputs: {base_dir: "${paratext_dir}", project_name: "ProjectB", file: "metadata.json"}
    outputs: [burrito_b]

  - name: load_burrito_c
    function: load_project_file
    inputs: {base_dir: "${paratext_dir}", project_name: "ProjectC", file: "metadata.json"}
    outputs: [burrito_c]

  # Load Scripture text
  - name: load_text_a
    function: load_usfm_book
    inputs: {base_dir: "${paratext_dir}", project_name: "ProjectA", book: "${book}", format: "usj"}
    outputs: [text_a]

  - name: load_text_b
    function: load_usfm_book
    inputs: {base_dir: "${paratext_dir}", project_name: "ProjectB", book: "${book}", format: "usj"}
    outputs: [text_b]

  - name: load_text_c
    function: load_usfm_book
    inputs: {base_dir: "${paratext_dir}", project_name: "ProjectC", book: "${book}", format: "usj"}
    outputs: [text_c]

  # Compare with language context
  - name: compare
    type: llm
    model: gpt-4o
    prompt: prompts/semantic-compare.gpt
    inputs:
      # Project A metadata
      lang_a: "${burrito_a.languages[0].name.en}"
      iso_a: "${burrito_a.languages[0].tag}"
      text_a: "${text_a}"
      # Project B metadata
      lang_b: "${burrito_b.languages[0].name.en}"
      iso_b: "${burrito_b.languages[0].tag}"
      text_b: "${text_b}"
      # Project C metadata
      lang_c: "${burrito_c.languages[0].name.en}"
      iso_c: "${burrito_c.languages[0].tag}"
      text_c: "${text_c}"
```

In the template (`semantic-compare.gpt`):
```
Compare these three translations:

1. {{lang_a}} ({{iso_a}}): {{text_a | json}}
2. {{lang_b}} ({{iso_b}}): {{text_b | json}}
3. {{lang_c}} ({{iso_c}}): {{text_c | json}}

Analyze semantic differences...
```

---

## Common Access Patterns Summary

**Note:** XML values must be extracted in pipeline steps first. The table shows final variable access after extraction.

| Data | Scripture Burrito (dict) | Paratext Settings (after XPath extraction) |
|------|-------------------|----------------------|
| Language name | `${burrito.languages[0].name.en}` | `${language_name}` (extracted via XPath `.//LanguageName/text()`) |
| ISO code | `${burrito.languages[0].tag}` | `${language_iso}` (extracted via XPath `.//LanguageIsoCode/text()`) |
| Project name | `${burrito.identification.name.en}` | `${full_name}` (extracted via XPath `.//FullName/text()`) |
| Abbreviation | `${burrito.identification.abbreviation.en}` | `${abbreviation}` (extracted via XPath `.//Abbreviation/text()`) |
| Versification | `${burrito.type.flavorType.flavor.versification}` (if present) | `${versification}` (extracted via XPath `.//Versification/text()`) |
| Encoding | N/A (Unicode assumed) | `${encoding}` (extracted via XPath `.//Encoding/text()`) |

**Recommendation:**
- **JSON (Scripture Burrito)**: Can access nested structures directly with `${...}`
- **XML (Settings.xml)**: Requires extraction step using XPath or Python helpers, then simple variable access

---

#### Alternative: Convert XML to dict for dot notation

If you want `${metadata_a.settings.language}` style access:

```yaml
- name: load_settings_a
  type: function
  function: load_paratext_file
  inputs:
    base_dir: "${paratext_dir}"
    project_name: "cebAPDv4"
    file: "Settings.xml"
  outputs:
    - settings_xml_a

- name: settings_to_dict
  type: function
  function: xml_to_dict
  inputs:
    xml: "${settings_xml_a}"
  outputs:
    - settings_a  # now a dict

- name: backtranslate
  type: llm
  prompt: tmp/backtranslation.gpt
  inputs:
    language: "${settings_a.LanguageName}"  # dot notation
    iso: "${settings_a.LanguageIsoCode}"
```

The `xml_to_dict` function would recursively convert XML elements to nested dicts, preserving the structure.

---

## Open Questions

1. ~~**Default format for `load_usfm_book`**~~ — resolved: pipeline always specifies `format:` explicitly. Fallback default `"usx"` if omitted, but pipelines should not rely on it.

2. **`load_usfm_project`** — loads the entire project as `dict[book_code, element_or_dict]`. This could be large (full NT = 27 books). Should it:
   - (a) Load all books eagerly and return a dict? Simple but potentially expensive.
   - (b) Return a lazy index (book_code → file path) and only load on demand?
   - (c) Skip this function entirely — pipeline authors iterate over `list_usfm_books` and call `load_usfm_book` in a loop step?

3. **`export_usx` placement**: Pipeline-callable function in `data.py`, OR a new `sp load-db usfm` driver in `load_db.py`? The driver approach is cleaner for the CLI user ("one command does it all") but couples two modules. The function approach keeps the pipeline more composable.

4. **Format conversion helpers**: Expose `usfm_to_usj()`, `usx_element_to_usj()` etc. as pipeline-callable functions? Or keep them internal/test-only?

5. ~~**Version validation**~~ — resolved: no validation needed; `usfmtc` handles older versions gracefully.

6. **USX output and whitespace/namespace**: `lxml` USX elements may carry `xmlns` attributes from the original file. When `usfmtc` writes USX XML, does it produce clean 3.1 namespace? Needs a quick smoke test.

7. ~~**Passage format default**~~ — resolved: pipeline specifies format explicitly on every step.

8. **Verse range Phase 2**: Is it acceptable to raise `NotImplementedError("Verse range selection not yet supported — use 'BOOK C' for whole chapter")` when a verse range is detected in Phase 1?

---

## Implementation order (TDD)

1. Write failing tests: `tests/test_usfm_loaders.py`
   - `test_list_usfm_books_returns_sorted_list`
   - `test_list_usfm_books_empty_dir_returns_empty_list`
   - `test_load_usfm_book_returns_usx_element`
   - `test_load_usfm_book_returns_usj_dict`
   - `test_load_usfm_book_not_found_raises_value_error`
   - `test_load_usfm_book_missing_dir_raises_file_not_found`
   - `test_load_usfm_passage_whole_book`
   - `test_load_usfm_passage_chapter`
   - `test_load_usfm_passage_verse_range_raises_not_implemented`
   - `test_export_usx_writes_files`
2. Implement functions in `data.py`
3. Update `pyproject.toml`
4. Update `docs/llmflow-language.md` (Common functions section)
5. Update `docs/ai-context/data-sources.md`
