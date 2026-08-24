# Biblical Data Sources & Access Patterns

> **Use this file for:** `sp download-data`, dataset locations (`~/.sp/data/`), USFM/USX/Macula/Berean access patterns, `load_usfm_book`/`load_usfm_passage`/`list_usfm_books`/`export_usx`/`load_project_file`, `load_xml_file`/`load_csv_file`/`xpath_text`, Paratext project layout, Paratext metadata (Settings.xml, metadata.json), multi-project comparison, deuterocanonical split-text.
> **Budget: 200 lines / 8KB.** If adding content would push past this, split into a new file and add a row to `index.md`.

Reference for AI assistants working with Scripture Pipelines. Covers how to obtain datasets, where they live on disk, and how pipelines reference them.

---

## Downloading Datasets

Use `sp download-data` to fetch datasets on demand. No git clone — downloads a zipball (no history).

```bash
sp download-data --list                            # show catalog
sp download-data macula-greek                     # → ~/.sp/data/macula-greek/
sp download-data macula-greek --dest ./data       # custom dest
```

**Default location:** `~/.sp/data/<dataset-name>/`
**Override:** `export LLMFLOW_DATA_DIR=/path/to/data`
**Pipeline reference:** `${LLMFLOW_DATA_DIR}/macula-greek/...`

---

## Built-in Dataset Catalog

These are wired into `sp download-data`. Full catalog: https://github.com/nida-institute/awesome-biblical-data

| Dataset | GitHub Repo | License | Approx Size | Key Content |
|---|---|---|---|---|
| `macula-greek` | Clear-Bible/macula-greek | CC BY 4.0 | ~150MB | NT Lowfat XML, Node XML, TSV morphology. BHSA-compatible word IDs. |
| `macula-hebrew` | Clear-Bible/macula-hebrew | CC BY 4.0 | ~400MB | OT XML, TSV morphology. Aligned to BHS. |
| `berean-usx` | Freely-Given-org/OpenEnglishBible | CC BY-SA 4.0 | ~15MB | Berean Standard Bible in USX 3.0 format (one file per book). |

---

## Access Patterns by Dataset

### Macula Greek (NT Morphology)

Lowfat XML tree structure. XPath is the primary access method.

```yaml
- name: get_verse_words
  type: xpath
  inputs:
    path: "${LLMFLOW_DATA_DIR}/macula-greek/lowfat/61-MAT.xml"
    xpath: "//w[@ref='MAT 1:1']"
    output_format: xml_string
  output: verse_words
```

Available sub-paths under `~/.sp/data/macula-greek/`:
- `lowfat/` — Lowfat XML trees, one file per NT book (e.g. `61-MAT.xml`)
- `nodes/` — Node XML trees
- `tsv/` — TSV morphology files, one per book

Book filenames use a three-digit USFM number prefix: `61-MAT`, `62-MRK`, ..., `87-REV`.

### Macula Hebrew (OT Morphology)

Same structure as Macula Greek.

```yaml
- name: get_hebrew_words
  type: xpath
  inputs:
    path: "${LLMFLOW_DATA_DIR}/macula-hebrew/WLC/01GEN.xml"
    xpath: "//w[@gloss]"
    output_format: xml_string
  output: words
```

### Berean USX (English Bible)

USX 3.0 XML, one file per canonical book. Reference via `parse_bible_reference` output.

```yaml
- name: load_passage
  type: xpath
  inputs:
    path: "${LLMFLOW_DATA_DIR}/berean-usx/${passage_info.book_code}.usx"
    xpath: "//verse[@number='${passage_info.chapter}:${passage_info.start_verse}']"
  output: verse_usx
```

---

## Pipeline Variable Pattern

Set `LLMFLOW_DATA_DIR` once (in shell profile or `.env`) and reference it uniformly:

```yaml
variables:
  data_dir: "${LLMFLOW_DATA_DIR}"
  greek_lowfat: "${LLMFLOW_DATA_DIR}/macula-greek/lowfat"
  hebrew_root: "${LLMFLOW_DATA_DIR}/macula-hebrew/WLC"
  berean_usx: "${LLMFLOW_DATA_DIR}/berean-usx"
```

If `LLMFLOW_DATA_DIR` is not set, the default is `~/.sp/data`.

---

## Loading Data Files in Function Steps

Use the built-in data loaders (all in `llmflow.utils.data`):

| Function | Returns | Use for |
|---|---|---|
| `load_text_file(path)` | `str` | Plain text, Markdown, USFM |
| `load_json_file(path)` | `dict` or `list` | JSON checkpoints, catalog files |
| `load_csv_file(path, delimiter=",")` | `list[dict]` | Morphology TSV with `delimiter="\t"`, CSV word lists |
| `load_xml_file(path)` | `lxml.etree._Element` | USX, TEI, Lowfat XML (full lxml tree) |
| `list_usfm_books(base_dir, project_name)` | `list[str]` | Book codes in a Paratext project, canonical order |
| `load_usfm_book(base_dir, project_name, book, format)` | `_Element` or `dict` | Single book from Paratext project; `format="usx"` or `"usj"` |
| `load_usfm_passage(base_dir, project_name, passage, format)` | `_Element` or `dict` | Passage by reference (`"LUK"`, `"LUK 1"`); verse ranges Phase 2 |
| `export_usx(base_dir, project_name, output_dir)` | `str` | Convert whole project to USX 3.1 files (e.g. for BaseX ingestion) |
| `load_project_file(base_dir, project_name, file)` | `dict` or `_Element` | Load metadata files; auto-detects format (`.json`→dict, `.xml`→Element) |
| `xpath_text(element, path)` | `str` or `None` | Extract text from XML element using XPath query |

**Paratext project layout:** `<base_dir>/<project_name>/*.sfm` or `*.usfm`

**Paratext metadata files:**
- `metadata.json` (Scripture Burrito) — returns `dict`, direct access: `${burrito.languages[0].name.en}`
- `Settings.xml` (Paratext 8/9) — returns `lxml.etree._Element`, requires extraction via `xpath_text()`
- `BiblicalTerms.xml`, `BookNames.xml`, etc. — also return `_Element`

**Schema reference:** See [paratext-schemas.md](paratext-schemas.md) for complete field listings, XPath queries, and choosing between Burrito vs Settings.xml

**Metadata access pattern:**
```yaml
# Scripture Burrito (dict) — preferred for language info
- name: load_metadata
  function: load_project_file
  inputs: {base_dir: "${PARATEXT_DIR}", project_name: "cebAPDv4", file: "metadata.json"}
  output: [burrito]

# Direct dict access in templates
language: "${burrito.languages[0].name.en}"
iso: "${burrito.languages[0].tag}"
```

```yaml
# Paratext XML — requires extraction
- name: load_settings
  function: load_project_file
  inputs: {base_dir: "${PARATEXT_DIR}", project_name: "cebAPDv4", file: "Settings.xml"}
  output: [settings]

- name: extract_language
  function: xpath_text
  inputs: {xml: "${settings}", path: ".//LanguageName/text()"}
  output: [language_name]
```

**Book codes:** Always 3-letter uppercase (`"LUK"`, `"GEN"`). Project numeric prefixes are preserved in filenames but not used in API calls.

**Version note:** Input files can be any USFM/USX version — `usfmtc` handles older versions gracefully. Output is always USX/USJ 3.1.

**Deuterocanonical split-text warning:** Some texts appear as separate books in some traditions (e.g. `BEL`, `SUS`) and as chapters within a canonical book in others (Daniel 14, Daniel 13). Pipelines searching for deuterocanonical content should check multiple book codes. See `project/plans/usfm-support.md` for details.

**Multi-project comparison pattern:**
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
      format: "usj"
    output:
      - text_a
```

```yaml
- name: load_morphology
  type: function
  function: llmflow.utils.data.load_csv_file
  inputs:
    file_path: "${LLMFLOW_DATA_DIR}/macula-greek/tsv/61-MAT.tsv"
    delimiter: "\t"
  output: words_tsv
```

---

## Versification

Scripture Pipelines uses the Copenhagen Alliance versification system. See `parse_bible_reference()` in `llmflow.utils.data` for canonical book codes, chapter/verse padding, and cross-versification helpers.

Full spec: https://github.com/Copenhagen-Alliance/versification-specification
