# Design Cycle Examples for Balisage Paper

Document showing the iterative design cycle for Paratext metadata access feature (issue #73).

---

## Stage 1: Initial Problem Recognition

**User (March 24, 2026):**
> "I think we have a GitHub issue on Paratext" [context: working on back-translation pipeline]
>
> The pipeline needs to know what language the source text is in to generate proper prompts.

**AI Response:**
Identified need for metadata access. Proposed quick solution: add a `get_paratext_metadata()` function that returns a dict with language info.

**User Pushback:**
> "We're going to need ALL the XML metadata eventually. I'm thinking we should load it into ETree."

---

## Stage 2: Design Exploration & Documentation

**AI:** "Let me write up the design options in a document so we can evaluate them properly."

Created `project/plans/usfm-support.md` section "Paratext Project Metadata Access" with 6 design options evaluated:

### Option 1: Specialized function per metadata type
```python
get_language_name(base_dir, project_name) -> str
get_language_iso(base_dir, project_name) -> str
get_versification(base_dir, project_name) -> int
```
**Pros:** Simple for common cases
**Cons:** Proliferation of functions, not extensible

### Option 2: Generic key-based getter
```python
get_project_metadata(base_dir, project_name, key: str) -> str
# Usage: get_project_metadata(dir, proj, "LanguageName")
```
**Pros:** Single function
**Cons:** No type safety, unclear what keys exist

### Option 3: Return structured dict
```python
get_project_metadata(base_dir, project_name) -> dict
# Returns: {"language_name": "Cebuano", "language_iso": "ceb", ...}
```
**Pros:** One call gets everything
**Cons:** Key names are arbitrary, no schema

### Option 4: Parse to dataclass
```python
@dataclass
class ProjectMetadata:
    language_name: str
    language_iso: str
    versification: int
```
**Pros:** Type safety, IDE autocomplete
**Cons:** Rigid schema, can't handle optional fields well

### Option 5: Return lxml Element (AI's initial preference)
```python
load_project_settings(base_dir, project_name) -> lxml.etree._Element
# User does: settings.find(".//LanguageName").text
```
**Pros:** Maximum flexibility, no data loss
**Cons:** User must know XML structure and XPath

### Option 6: **Generic file loader with format detection** ✅
```python
load_project_file(base_dir, project_name, file: str) -> dict | Element
# Auto-detects: .json → dict, .xml → Element
```
**Pros:** Handles both Scripture Burrito and Paratext XML, no opinionated parsing
**Cons:** Returns different types based on file extension

---

## Stage 3: Design Discussion & Pushback

**AI Recommendation (in design doc):**
Return lxml Element (Option 5) - gives maximum flexibility.

**User Response:**
> "I like Option 6 better. Generic loader. Load `metadata.json` → dict. Load `Settings.xml` → Element. Let the pipeline decide what to extract."

**AI Pushback:**
"But that means the return type varies. Should we have two functions instead? `load_project_json()` and `load_project_xml()`?"

**User:**
> "No - one function is fine. The auto-detection is a feature. Projects have different metadata depending on their vintage. Some have Scripture Burrito, some just have Paratext XML. The pipeline needs to handle both."

**AI:**
"Fair point. But we need to add a helper for XML text extraction then, since you can't pass `_Element` objects to LLM templates."

**User:**
> "Yes - add `xpath_text(element, path)` helper."

---

## Stage 4: API Design Details

**AI Proposal:**
```python
def load_project_file(
    base_dir: str,
    project_name: str,
    file: str
) -> dict | lxml.etree._Element
```

**User Refinement:**
> "Good. Examples in docstring please - show both Scripture Burrito dict access and Paratext XML extraction patterns."

**AI:** Added 4 detailed examples to design doc:

### Example 1: Scripture Burrito language (dict access)
```yaml
- name: load_metadata
  function: load_project_file
  inputs:
    base_dir: "${PARATEXT_DIR}"
    project_name: "cebAPDv4"
    file: "metadata.json"
  outputs: [burrito]

- name: backtranslate
  type: llm
  inputs:
    source_language: "${burrito.languages[0].name.en}"
    language_iso: "${burrito.languages[0].tag}"
```

### Example 2: Paratext Settings (extract first)
```yaml
- name: load_settings
  function: load_project_file
  inputs: {base_dir: "${PT_DIR}", project_name: "cebAPDv4", file: "Settings.xml"}
  outputs: [settings]

- name: extract_language
  function: xpath_text
  inputs: {element: "${settings}", path: ".//LanguageName/text()"}
  outputs: [language_name]
```

**User:** "Perfect. That shows the two different access patterns clearly."

---

## Stage 5: Test-Driven Development

**AI:** "Before implementing, let me write the tests first."

Created `tests/test_paratext_metadata.py` with 9 tests (all initially failing):

```python
def test_load_project_file_json(tmp_path):
    """Returns dict for .json files"""
    # Setup: create minimal metadata.json
    # Test: result should be dict with expected structure
    # Assert: isinstance(result, dict)

def test_load_project_file_xml(tmp_path):
    """Returns Element for .xml files"""
    # Test: result should be lxml Element
    # Assert: isinstance(result, lxml.etree._Element)

def test_load_project_file_not_found(tmp_path):
    """Raises FileNotFoundError for missing files"""
    # Assert: with pytest.raises(FileNotFoundError)

def test_xpath_text_extraction(tmp_path):
    """Extract text content via XPath"""
    # Test: xpath_text(element, ".//LanguageName/text()") == "Test Language"

def test_xpath_text_not_found(tmp_path):
    """Returns None for missing XPath"""
    # Test: xpath_text(element, ".//Missing/text()") is None
```

**User:** "Run them - we expect them all to fail."

**AI:**
```bash
$ pytest tests/test_paratext_metadata.py -v
FAILED (9 failures) - load_project_file not found, xpath_text not found
```

"Good - now we implement to make them pass."

---

## Stage 6: Implementation

**AI:** Implemented in `src/llmflow/utils/data.py`:

```python
def load_project_file(
    base_dir: str, project_name: str, file: str
) -> dict | lxml.etree._Element:
    """Load metadata file from Paratext project.

    Auto-detects format:
    - .json → returns dict (Scripture Burrito)
    - .xml → returns lxml Element (Paratext XML)
    """
    project_path = Path(base_dir) / project_name
    file_path = project_path / file

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}\n"
            f"Project directory: {project_path}"
        )

    if file.endswith('.json'):
        return load_json_file(str(file_path))
    elif file.endswith('.xml'):
        return load_xml_file(str(file_path))
    else:
        raise ValueError(f"Unsupported file type: {file}")


def xpath_text(element: lxml.etree._Element, path: str) -> str | None:
    """Extract text content from XML element via XPath."""
    results = element.xpath(path)
    if results and isinstance(results, list) and len(results) > 0:
        return str(results[0]) if results[0] is not None else None
    return None
```

---

## Stage 7: Test Verification

**AI:**
```bash
$ pytest tests/test_paratext_metadata.py -v
===== 9 passed =====

$ pytest -v  # All tests
===== 1225 passed, 8 skipped =====
```

"All tests passing, no regressions."

**User:** "Good. Push to dev."

---

## Stage 8: Documentation & Examples

**AI:** Updated three documentation files:

1. **`docs/llmflow-language.md`** - added function reference
2. **`docs/ai-context/data-sources.md`** - added usage patterns
3. **`docs/ai-context/paratext-schemas.md`** - NEW: schema reference showing what fields exist

**User Feedback on Documentation:**
> "Wait - we have the HOW (functions to load files) but not the WHAT (what data is inside them). An AI needs to know what fields exist in Scripture Burrito and Settings.xml."

**AI:** "You're right. Creating schema reference file..."

Added comprehensive schema documentation showing:
- Scripture Burrito structure: `languages[0].name.en`, `identification.name.en`
- Paratext Settings.xml elements: `LanguageName`, `LanguageIsoCode`, `Versification`
- XPath query examples for each field
- Guidance on choosing between formats

**User:** "Perfect - now AI assistants know both mechanics AND schema."

---

## Stage 9: Real-World Testing

**User:** "Let's test this on an actual Paratext project."

Created example pipeline in `tmp/backtranslation.yaml`:

```yaml
steps:
  - name: load_metadata
    type: function
    function: load_project_file
    inputs:
      base_dir: "${PARATEXT_DIR}"
      project_name: "${project_name}"
      file: "metadata.json"
    outputs: [burrito]

  - name: load_source
    type: function
    function: load_usfm_book
    inputs:
      base_dir: "${PARATEXT_DIR}"
      project_name: "${project_name}"
      book: "${book}"
      format: "usj"
    outputs: [source_text]

  - name: backtranslate
    type: llm
    model: gpt-4o
    prompt: prompts/backtranslation.gpt
    inputs:
      source_text: "${source_text}"
      source_language: "${burrito.languages[0].name.en}"
      language_iso: "${burrito.languages[0].tag}"
```

**Issue Found During Testing:**
Pipeline failed - missing `name` and `description` fields (required by linter).

**User:** "Add them and run again."

Fixed pipeline, ran successfully. User noted critical design insight:

> "Parsing files upfront protects against VM/mount disconnects. If Paratext projects are on network drives, the mount could disconnect during a long-running LLM step (which can take minutes). By parsing USFM to USJ dict upfront, the pipeline becomes independent of file I/O after initial load."

**AI:** "That's an important rationale - I'll document it in the issue."

Added comment to issue #73 explaining eager evaluation design choice.

---

## Stage 10: Public Repository Creation

**User:** "Create a public example repository with working Paratext pipelines."

**AI:** Created `paratext-pipelines` repository structure with:
- `backtranslation.yaml` - working pipeline
- `multi-project-comparison.yaml` - compare passages across 3+ projects
- Full `sp init` scaffold (prompts/, docs/audits/, project/)
- Comprehensive README with examples

**Process:**
1. Created files locally
2. Initialized git
3. Committed 22 files (1333 lines)
4. Used `gh repo create` to make public repo
5. Pushed successfully

Repository live at: https://github.com/nida-institute/paratext-pipelines

---

## Stage 11: Issue Closure

**AI:** Added completion comment to issue #73:

```markdown
## Implementation Complete

All acceptance criteria met:
- ✅ load_project_file() implemented
- ✅ xpath_text() helper implemented
- ✅ 9 tests passing (1225 total)
- ✅ Documentation updated
- ✅ Example pipeline working
- ✅ Design rationale documented (eager evaluation)
- ✅ paratext-pipelines repo created

Closing.
```

---

## Key Design Principles Demonstrated

### 1. Design Before Implementation
- **Don't guess** - when multiple approaches exist, write them all down
- **Document trade-offs** - pros/cons for each option
- **Let user decide** - they understand domain constraints you don't

### 2. Test-Driven Development
- **Write failing tests first** - forces specification before implementation
- **Run full suite** - catch regressions (1225 tests must pass)
- **Tests document behavior** - clearer than prose

### 3. Iterative Refinement
- **AI proposes** → **User refines** → **AI pushes back** → **User justifies**
- Each cycle improves the design
- Disagreement is productive when it surfaces assumptions

### 4. Real-World Validation
- **Theory → Practice** - test on actual Paratext projects
- **Find edge cases** - network mounts, timing issues
- **Document rationale** - why eager evaluation matters

### 5. Communication Infrastructure
- **Design documents** - shared understanding
- **GitHub issues** - track decisions and rationale
- **Example repositories** - show working implementations
- **Schema documentation** - bridge knowledge gaps

---

## Timeline

- **March 24:** Initial problem recognition
- **March 24:** Design document with 6 options
- **March 24:** Design discussion, chose Option 6
- **March 24:** Wrote 9 failing tests
- **March 24:** Implementation, all tests passing
- **March 24:** Documentation updated (3 files)
- **March 25:** Schema documentation added
- **March 25:** Example pipeline tested
- **March 25:** paratext-pipelines repo created and published
- **March 25:** Issue #73 closed

**Total elapsed:** ~24 hours from problem to public working examples.

---

## Excerpts from Key Documents

### From `project/plans/usfm-support.md`

> **Design Question:** How should pipelines access Paratext project metadata?
>
> A back-translation workflow needs the source language name. A multi-project comparison needs to identify which projects to compare. Both require reading project metadata files.
>
> Paratext projects have two metadata formats:
> 1. **Scripture Burrito** (`metadata.json`) - modern, JSON-based
> 2. **Paratext XML** (`Settings.xml`) - legacy, XML-based
>
> Some projects have both. Some have only Paratext XML. Pipelines must handle both.
>
> [Six options evaluated with pros/cons...]
>
> **Recommendation:** Option 6 - Generic loader with auto-detection.
> - Returns dict for JSON, Element for XML
> - Requires helper function for XPath text extraction
> - Handles both formats without opinionated parsing
> - Maximizes flexibility for different metadata needs

### From Issue #73

> **Design rationale (eager evaluation):**
>
> Paratext projects may be on network drives, VMs, or mounted volumes that can disconnect. If we passed file paths to LLM steps and tried to access them during prompt rendering, the mount could go out of scope mid-run. LLM steps can take minutes (especially for full books).
>
> By parsing everything upfront:
> 1. `load_usfm_book(format="usj")` returns dict in memory
> 2. LLM step runs with the dict (no file I/O)
> 3. Pipeline becomes independent of filesystem after initial load
>
> This makes long-running pipelines resilient to transient I/O issues.

### From `paratext-pipelines/README.md`

> ## How it Works
>
> Pipelines use LLMFlow's Paratext support:
>
> - **`load_project_file()`** — Loads metadata files (Scripture Burrito `metadata.json`, Paratext `Settings.xml`)
> - **`load_usfm_book()`** / **`load_usfm_passage()`** — Loads Scripture text in USJ (JSON) or USX (XML) format
> - **`list_usfm_books()`** — Lists all books in a project
>
> All metadata and text is loaded into memory before LLM steps run, protecting against network mount disconnects during long-running operations.
