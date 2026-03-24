# Biblical Data Sources & Access Patterns

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
  outputs: verse_words
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
  outputs: words
```

### Berean USX (English Bible)

USX 3.0 XML, one file per canonical book. Reference via `parse_bible_reference` output.

```yaml
- name: load_passage
  type: xpath
  inputs:
    path: "${LLMFLOW_DATA_DIR}/berean-usx/${passage_info.book_code}.usx"
    xpath: "//verse[@number='${passage_info.chapter}:${passage_info.start_verse}']"
  outputs: verse_usx
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

```yaml
- name: load_morphology
  type: function
  function: llmflow.utils.data.load_csv_file
  inputs:
    file_path: "${LLMFLOW_DATA_DIR}/macula-greek/tsv/61-MAT.tsv"
    delimiter: "\t"
  outputs: words_tsv
```

---

## Versification

LLMFlow uses the Copenhagen Alliance versification system. See `parse_bible_reference()` in `llmflow.utils.data` for canonical book codes, chapter/verse padding, and cross-versification helpers.

Full spec: https://github.com/Copenhagen-Alliance/versification-specification
