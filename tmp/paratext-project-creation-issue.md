# Paratext Project Creation & Management Operations

## Summary

Add high-level functions for creating and managing Paratext projects from LLMFlow pipelines, enabling workflows like automated back-translation project creation, multi-language translation generation, and project scaffolding.

## Motivation

Current LLMFlow Paratext support is **read-only**:
- ✅ Load Scripture text (`load_usfm_book`, `load_usfm_passage`)
- ✅ Load metadata (`load_project_file`)
- ❌ Cannot create new projects
- ❌ Cannot write Scripture back to projects
- ❌ Cannot generate project metadata files

**Use cases that require write operations:**

1. **Back-translation project creation** — After generating back-translation with LLM, create a new Paratext project with:
   - Settings.xml (target language: English, source language reference)
   - Scripture Burrito metadata.json
   - Back-translated USFM files (one per book)
   - Appropriate versification, encoding, etc.

2. **Multi-language translation generation** — Use discourse analysis + semantic domain data to generate draft translations into top N languages, each as a separate Paratext project

3. **Project scaffolding** — Create empty project structure that translators can import into Paratext

4. **Bulk Scripture editing** — Load, transform (e.g., apply consistent formatting), and write back

## Proposed Functions

### `create_project()`

```python
def create_project(
    base_dir: str,
    project_name: str,
    language_name: str,
    language_iso: str,
    project_type: str = "backTranslation",  # or "translation", "resource"
    source_project: str = None,  # for back-translations
    versification: str = "4",  # English versification
    **kwargs  # Other Settings.xml fields
) -> str:
    """
    Create a new Paratext project with metadata files.

    Creates:
    - Project directory: <base_dir>/<project_name>/
    - Settings.xml (Paratext 9 format)
    - metadata.json (Scripture Burrito manifest)
    - Empty USFM book stubs (optional)

    Returns:
        Project directory path
    """
```

### `write_usfm_book()`

```python
def write_usfm_book(
    base_dir: str,
    project_name: str,
    book: str,
    content: dict | str,  # USJ dict or USFM string
    format: str = "usfm"  # or "usj" to auto-convert
) -> None:
    """
    Write Scripture content to a project book file.

    - Auto-detects existing book number prefix (e.g., 41LUKPRJ.usfm)
    - Creates file if it doesn't exist
    - Preserves line endings and encoding
    """
```

### `update_project_metadata()`

```python
def update_project_metadata(
    base_dir: str,
    project_name: str,
    file: str,  # "Settings.xml" or "metadata.json"
    updates: dict  # Fields to update
) -> None:
    """
    Update specific fields in project metadata files.

    For XML: XPath-based updates
    For JSON: dict merge
    """
```

## Example Pipeline: Create Back-Translation Project

```yaml
variables:
  paratext_dir: "${PARATEXT_DIR}"
  source_project: "cebAPDv4"
  book: "LUK"

steps:
  # Load source metadata
  - name: load_source_metadata
    function: load_project_file
    inputs: {base_dir: "${paratext_dir}", project_name: "${source_project}", file: "metadata.json"}
    outputs: [source_metadata]

  # Load source Scripture
  - name: load_source
    function: load_usfm_book
    inputs: {base_dir: "${paratext_dir}", project_name: "${source_project}", book: "${book}", format: "usj"}
    outputs: [source_text]

  # Generate back-translation
  - name: backtranslate
    type: llm
    model: gpt-4o
    prompt: prompts/backtranslation.gpt
    inputs:
      source_language: "${source_metadata.languages[0].name.en}"
      text: "${source_text}"
    outputs: [backtrans_text]

  # Create back-translation project
  - name: create_bt_project
    function: create_project
    inputs:
      base_dir: "${paratext_dir}"
      project_name: "${source_project}_BT"
      language_name: "English"
      language_iso: "eng"
      project_type: "backTranslation"
      source_project: "${source_project}"
    outputs: [bt_project_dir]

  # Write back-translated book
  - name: write_book
    function: write_usfm_book
    inputs:
      base_dir: "${paratext_dir}"
      project_name: "${source_project}_BT"
      book: "${book}"
      content: "${backtrans_text}"
      format: "usfm"
```

## Example Pipeline: Multi-Language Translation

```yaml
# Generate draft translations into top 10 languages
# with semantic domain glosses and discourse markers

variables:
  target_languages:
    - {name: "Spanish", iso: "spa"}
    - {name: "French", iso: "fra"}
    - {name: "Swahili", iso: "swa"}
    # ... etc

steps:
  - name: for_each_language
    type: for-each
    items: "${target_languages}"
    steps:
      - name: create_project
        function: create_project
        inputs:
          base_dir: "${PARATEXT_DIR}"
          project_name: "AI_Draft_${item.iso}"
          language_name: "${item.name}"
          language_iso: "${item.iso}"
          project_type: "translation"

      - name: translate_books
        # ... load discourse data, semdom, translate, write ...
```

## Design Considerations

### 1. Settings.xml vs Scripture Burrito

**Recommended:** Generate both formats for maximum compatibility
- Modern tools (Paratext 9+, Translators' Workplace) prefer Scripture Burrito
- Legacy tools require Settings.xml
- Fields overlap significantly; maintain consistency

**Approach:** Template-based generation with variable substitution

### 2. Book Numbering

Paratext uses numeric prefixes (e.g., `41LUK.usfm`, `01GEN.usfm`)
- **Read existing:** Auto-detect from existing files
- **Create new:** Use canonical USFM order (GEN=01, EXO=02, ..., MAT=41, ..., REV=66)
- **Preserve:** Keep project's numbering scheme when reading/writing

### 3. Versification

- Default to versification 4 (English/NRSV) for back-translations
- Allow override for other project types
- Consider: helper function to copy versification from source project

### 4. Line Endings & Encoding

- Paratext standard: UTF-8 with BOM, CRLF line endings (Windows)
- Detect existing project conventions
- Allow override via kwargs

### 5. Validation

- Validate language ISO codes (639-3)
- Validate book codes (3-letter USFM)
- Validate project name (Paratext naming rules: no spaces, special chars)

## Out of Scope (Future Work)

- Full Paratext XML schemas (BiblicalTerms, Notes, ProjectProgress) — start with essential files only
- Paratext interoperability (Send/Receive, conflict resolution) — pipelines create local projects
- LDML generation — start with basic language info
- Custom stylesheets

## Implementation Tasks

- [ ] `create_project()` function with Settings.xml + metadata.json templates
- [ ] `write_usfm_book()` function with USJ→USFM conversion
- [ ] `update_project_metadata()` for field updates
- [ ] Templates for Settings.xml and metadata.json (embedded in data.py or separate files)
- [ ] Book number lookup table (canonical USFM order)
- [ ] Tests: create project, write books, verify files
- [ ] Documentation: function reference, pipeline examples

## Acceptance Criteria

- [ ] Create new project with Settings.xml + metadata.json
- [ ] Write USFM books to project directory
- [ ] Back-translation example pipeline works end-to-end
- [ ] Tests cover project creation, book writing, metadata updates
- [ ] Documentation updated

## Related

- Depends on: #73 (Paratext metadata loading — already implemented)
- Enables: Multi-language translation workflows, back-translation projects, project scaffolding
- Future: Integration with Paratext Send/Receive API (if/when available)

## Reference

- Scripture Burrito spec: https://docs.burrito.bible/
- Paratext 9 project structure: See existing projects in PARATEXT_DIR
- USFM 3.0 spec: https://ubsicap.github.io/usfm/
