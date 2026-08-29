# Biblical Data Sources & Access Patterns

> **Use this file for:** `sp resource`, resource locations (`~/sp/resources/`), USFM/USX/Macula/Berean access patterns, `load_usfm_book`/`load_usfm_passage`/`list_usfm_books`/`export_usx`/`load_project_file`, `load_xml_file`/`load_csv_file`/`xpath_text`, Paratext project layout, Paratext metadata (Settings.xml, metadata.json), multi-project comparison, deuterocanonical split-text.
> **Budget: 200 lines / 8KB.** If adding content would push past this, split into a new file and add a row to `index.md`.

Reference for AI assistants working with Scripture Pipelines. Covers how to obtain datasets, where they live on disk, and how pipelines reference them.

---

## Getting a resource onto this machine

`sp resource` is the whole surface (#217). `sp download-data` is gone — it carried its own
four-entry catalog beside the public one, which drifted.

```bash
sp resource list                     # what the catalog knows, and what this machine has
sp resource add WLC                  # fetch if needed, then register
sp resource add WLC --no-download    # register now, fetch later
sp resource download acai            # fetch something no reader can yet open
```

Something of your own goes by path — `--path ~/paratext/MYPROJ` (a Paratext project identifies
itself) or `--path x.tsv --kind tsv --versification org` (anything else must say its `kind`).

**Downloading and registering are different acts.** Downloading puts data on disk; registering
tells the engine a pipeline may name it. `add` does both, because asking for a resource is
asking to use it.

**Corpora:** `~/sp/resources/<owner>/<repo>/` — visible rather than hidden, because a library of
texts is not configuration, and named for the source so two contributors cannot collide. Not in
git: `https-<host>/<file>`. Each carries `.sp-resource.json` recording what was fetched.

**Registrations:** `~/.sp/registrations/`, one file each, path *relative* to the download so it
means the same thing on every machine. Absolute paths are honoured, which is what a maintainer
working against their own clone needs. `sp doctor` warns when one points at nothing.

**The catalog** is `resources.json` in `nida-institute/awesome-biblical-data`, vendored at
`data/resources.json`. It carries **shape, never state** — which file holds a text, which
backend reads it, its versification and canon. What changes as a maintainer works stays in that
resource's own repository. A `provides` block means the engine can open it; without one (ACAI,
CNTR) `sp resource download` fetches it for direct use.

| Provides | From | License | |
|---|---|---|---|
| `WLC` | Clear-Bible/macula-hebrew | CC BY 4.0 | OT, `tsv`, `org` |
| `SBLGNT` | Clear-Bible/macula-greek | CC BY 4.0 | NT, `tsv`, `org` |
| `BSB` | bereanbible.com `bsb_usfm.zip` | Public domain | OT+NT, `usfm`, `eng` |

BSB uses the official USFM release, not the `usfm-bible/examples.bsb` mirror, which omits `\id`
in Ecclesiastes and so silently loses that book. Fuller detail: `docs/llmflow-language.md`.

---

## Access Patterns by Dataset

### Macula Greek (NT Morphology)

Lowfat XML tree structure. XPath is the primary access method.

```yaml
- name: get_verse_words
  type: xpath
  inputs:
    path: "${LLMFLOW_DATA_DIR}/Clear-Bible/macula-greek/lowfat/61-MAT.xml"
    xpath: "//w[@ref='MAT 1:1']"
    output_format: xml_string
  output: verse_words
```

Available sub-paths under `~/sp/resources/Clear-Bible/macula-greek/`:
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
    path: "${LLMFLOW_DATA_DIR}/Clear-Bible/macula-hebrew/WLC/01GEN.xml"
    xpath: "//w[@gloss]"
    output_format: xml_string
  output: words
```

### BSB (English Bible) — name it, do not path to it

The old `berean-usx` dataset is gone: it pointed at `Freely-Given-org/OpenEnglishBible`, which
404s, and it is not in the catalog (#201). BSB now comes from the official USFM release and is a
registered resource, so a pipeline names it and never carries a path:

```yaml
- name: load_passage
  type: scripture
  edition: BSB
  passage: "${passage}"
  format: milestones
  output: english_text
```

This is the preferred shape for **any** registered text — WLC and SBLGNT included. An absolute
path in a pipeline is why several repositories only ran on one laptop.

Reach for `type: xpath` over raw files only when you need the markup itself rather than the
text, and then against a resource this machine actually has — `sp resource list` says which.

---

## Pipeline Variable Pattern

Set `LLMFLOW_DATA_DIR` once (in shell profile or `.env`) and reference it uniformly:

```yaml
variables:
  data_dir: "${LLMFLOW_DATA_DIR}"
  greek_lowfat: "${LLMFLOW_DATA_DIR}/Clear-Bible/macula-greek/lowfat"
  hebrew_root: "${LLMFLOW_DATA_DIR}/Clear-Bible/macula-hebrew/WLC"
```

This pattern is for the *annotation* trees, which no step type reads yet. For scripture text,
name a registered resource with `type: scripture` instead — a path in a pipeline is the thing
`sp resource` exists to remove.

If `LLMFLOW_DATA_DIR` is not set, the default is `~/sp/resources` — or `$SP_HOME/resources`
when `SP_HOME` is set, which is for test runs and containers. `sp doctor` warns when either
is redirected, because that is how one machine ends up holding several copies of a text.

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
    file_path: "${LLMFLOW_DATA_DIR}/Clear-Bible/macula-greek/tsv/61-MAT.tsv"
    delimiter: "\t"
  output: words_tsv
```

---

## Versification

Scripture Pipelines uses the Copenhagen Alliance versification system. See `parse_bible_reference()` in `llmflow.utils.data` for canonical book codes, chapter/verse padding, and cross-versification helpers.

Full spec: https://github.com/Copenhagen-Alliance/versification-specification
