## Problem

Biblical reference data (Macula Greek, Macula Hebrew, Berean Bible) is too large to bundle in the distribution binary (~150–600MB working tree). Pipelines that need this data currently have no standard way to obtain it.

## Proposed solution

Add `sp download-data` CLI subcommand that fetches datasets on demand to a local directory.

## Usage

```bash
sp download-data                          # no args → show catalog + usage hint
sp download-data --list                   # enumerate available datasets with size/license
sp download-data macula-greek             # download to default location (~/.sp/data)
sp download-data macula-greek --dest ./data/macula
```

## Catalog (initial)

| Dataset | Source | License | Approx size |
|---|---|---|---|
| macula-greek | Clear-Bible/macula-greek | CC BY 4.0 | ~150MB |
| macula-hebrew | Clear-Bible/macula-hebrew | CC BY 4.0 | ~400MB |
| berean-usx | Berean Bible | CC BY-SA 4.0 | ~15MB |

For the full catalog, `--list` will point to https://github.com/nida-institute/awesome-biblical-data

## Details

- Default dest: `~/.sp/data/<dataset-name>/`
- `LLMFLOW_DATA_DIR` env var overrides the base path
- Downloads a zipball (no git history)
- Macula formats: Lowfat XML, Node XML, TSV morphology
- Berean: USX format
- Pipelines reference data via `${LLMFLOW_DATA_DIR}/macula-greek/...`
