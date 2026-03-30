# Implement Paratext Project Metadata Access

## Summary

Add support for loading Paratext project metadata files (Settings.xml, metadata.json, etc.) to enable language-aware pipelines and multi-project workflows.

## Motivation

Back-translation and multi-project comparison workflows need access to project metadata:
- Language name and ISO code
- Project identification (name, abbreviation)
- Versification scheme, encoding
- Biblical Terms renderings (future)

**Design document:** `project/plans/usfm-support.md` (Paratext Project Metadata Access section)

## Implementation Tasks

### 1. Core function: `load_project_file()`

Add to `src/llmflow/utils/data.py`:

```python
def load_project_file(base_dir: str, project_name: str, file: str) -> dict | lxml.etree._Element:
    """
    Load a metadata file from a Paratext project directory.

    Auto-detects format by extension:
    - .json → returns dict (parsed JSON)
    - .xml → returns lxml.etree._Element (parsed XML)

    Args:
        base_dir: Paratext projects directory
        project_name: Project subdirectory name
        file: Filename (e.g., "Settings.xml", "metadata.json")

    Returns:
        dict for JSON files, lxml.etree._Element for XML files

    Raises:
        FileNotFoundError: If project dir or file doesn't exist
        ValueError: If file extension is not .json or .xml
    """
```

**Supported files:**
- `metadata.json` (Scripture Burrito manifest)
- `Settings.xml` (Paratext settings)
- `BiblicalTerms.xml` (key term renderings)
- `CommentTags.xml`, `BookNames.xml`, etc.

### 2. XPath text extraction helper

Add utility function for extracting text values from XML:

```python
def xpath_text(element: lxml.etree._Element, path: str) -> str | None:
    """
    Extract text content from XML element using XPath.

    Args:
        element: lxml Element to query
        path: XPath query (e.g., ".//LanguageName/text()")

    Returns:
        Text content or None if not found
    """
```

### 3. Tests

Add `tests/test_paratext_metadata.py`:

- `test_load_project_file_json()` - loads metadata.json, returns dict
- `test_load_project_file_xml()` - loads Settings.xml, returns Element
- `test_load_project_file_not_found()` - raises FileNotFoundError
- `test_load_project_file_invalid_extension()` - raises ValueError for .txt
- `test_xpath_text_extraction()` - extracts language name from Settings.xml
- `test_xpath_text_not_found()` - returns None for missing path

**Test fixtures:** Create minimal synthetic files in `tests/fixtures/paratext/TestProject/`

### 4. Integration with existing USFM functions

Update back-translation example in `tmp/` to use metadata loading.

### 5. Documentation

Update `docs/llmflow-language.md` with:
- `load_project_file()` function reference
- `xpath_text()` helper function
- Examples of Scripture Burrito vs Paratext XML access patterns

## Key Design Decisions (from design doc)

✅ **Generic loader** - One function handles all file types (auto-detect by extension)
✅ **No pre-parsing** - Return raw formats (dict for JSON, Element for XML) for maximum flexibility
✅ **Extract in pipeline** - Don't pass lxml Elements to LLM templates; extract values first
✅ **Complementary formats** - Projects may have both Scripture Burrito and Paratext XML; load both

## Access Pattern Examples

**Scripture Burrito (dict access):**
```yaml
language: "${burrito.languages[0].name.en}"
iso: "${burrito.languages[0].tag}"
```

**Paratext Settings.xml (extract first):**
```yaml
- name: extract_language
  function: xpath_text
  inputs:
    xml: "${settings}"
    path: ".//LanguageName/text()"
  outputs: [language_name]
```

## Out of Scope (Future Work)

- Biblical Terms parsing/querying
- Notes and comment extraction
- Project progress tracking
- xml_to_dict() conversion helper

## Acceptance Criteria

- [ ] `load_project_file()` implemented in `data.py`
- [ ] `xpath_text()` helper implemented
- [ ] All 6 tests passing
- [ ] Test fixtures created
- [ ] Example pipeline in `tmp/` uses metadata loading
- [ ] Documentation updated

## Reference

See full design with 6 alternative approaches evaluated and 4 detailed usage examples in `project/plans/usfm-support.md` (Paratext Project Metadata Access section).
